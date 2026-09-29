"""One capped fine solve with coarse poses used solely as Newton initial guesses.

The fine structural/contact model, path, committed state, gates, and checkpoint
logic belong to the ordinary static driver. This fixture only substitutes the
disposable q/z iterate at each step after rechecking its actual swept path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from anysolver.general_contact import static_path
from docs.d1_review_support.d1_two_body_refined_target_route import (
    build_refined_case, run,
)
from docs.d1_review_support.d1_two_body_16x16_linearization_preflight import (
    interpolate_target,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-record", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--seed-trace", type=Path, required=True)
    parser.add_argument("--progress-trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.seed_trace, args.progress_trace, args.output):
        if path.exists():
            parser.error(f"output exists: {path}")
    saved_bytes = args.saved_record.read_bytes()
    saved = json.loads(saved_bytes)
    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    if (preflight["status"] != "seed_preflight_pass"
            or preflight["saved_source_sha256"] != hashlib.sha256(saved_bytes).hexdigest()
            or saved["status"] != "completed" or saved["accepted_steps"] != 2
            or len(saved["steps"]) != 2):
        raise ValueError("saved coarse path or preflight is incompatible")
    old_model, _old_definition, _old_settings, old_program, old_x, old_y = (
        build_refined_case(4, 8, 8)
    )
    _fine_model, _fine_definition, _fine_settings, fine_program, fine_x, fine_y = (
        build_refined_case(4, 16, 16)
    )
    if old_program.contract() != fine_program.contract():
        raise ValueError("path contracts differ")
    original = static_path.solve_semismooth_increment
    with args.seed_trace.open("w", encoding="utf-8", buffering=1) as trace:
        def event(**fields):
            trace.write(json.dumps(fields)+"\n")
            trace.flush()

        def seeded_increment(**kwargs):
            step = int(kwargs["step"])
            if step not in (1, 2):
                return original(**kwargs)
            manager = kwargs["manager"]
            model = kwargs["model"]
            transform = kwargs["transform"]
            offset = kwargs["offset"]
            old_step = saved["steps"][step-1]
            if (old_step["source_pressure_node_ids"]
                    != list(manager.law.pressure_mode_ids)):
                raise ValueError("source pressure identities changed")
            seed_u = interpolate_target(
                old_model, np.asarray(old_step["accepted_displacements"]),
                old_x, old_y, model, fine_x, fine_y,
            )
            seed_q = np.asarray(transform.T @ (seed_u-offset)).reshape(-1)
            seed_z = (np.asarray(old_step["numerical_pressure_pa"])
                      * np.asarray(old_step["reference_support_m2"]))
            prior_u = np.asarray(transform @ kwargs["q"] + offset).reshape(-1)
            reasons = []
            reconstruction = float(np.max(np.abs(
                transform @ seed_q + offset-seed_u)))
            control_error = float(np.max(np.abs(
                kwargs["control_rows"] @ seed_q-kwargs["target"])))
            if reconstruction > 1.0e-10:
                reasons.append("constraint_reconstruction")
            if control_error > 1.0e-10:
                reasons.append("control_target")
            if seed_z.shape != kwargs["nodal_forces"].shape or not np.all(
                    np.isfinite(seed_z)) or np.any(seed_z < 0):
                reasons.append("nodal_force")
            # Unlike the proxy preflight, this starts from the actual fine
            # accepted pose. The driver does not otherwise check this path
            # when a seeded q happens to satisfy Newton convergence at entry.
            swept = False
            if not reasons:
                swept = bool(manager._swept_admissible(prior_u, seed_u))
                if not swept:
                    reasons.append("previous_fine_to_seed_sweep")
            event(step=step, seed_used=not reasons, rejection_reasons=reasons,
                  reconstruction_error=reconstruction,
                  control_error=control_error,
                  actual_previous_fine_to_seed_swept=swept)
            if not reasons:
                kwargs = dict(kwargs, q=seed_q, nodal_forces=seed_z)
            return original(**kwargs)

        with patch.object(static_path, "solve_semismooth_increment",
                          seeded_increment):
            record = run(4, 16, 16, record_pressure=True,
                         trace_path=args.progress_trace)
    record["coarse_seed_source_sha256"] = hashlib.sha256(saved_bytes).hexdigest()
    record["seed_trace"] = str(args.seed_trace)
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "status", "failure_reason", "accepted_steps", "elapsed_seconds",
    )}, indent=2))
    raise SystemExit(0 if record["status"] == "completed" else 2)


if __name__ == "__main__":
    main()
