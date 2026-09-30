"""Compare one boundary predicate on the identical saved reporting candidate.

Development attribution only: the installed package is patched in memory with
one explicitly hashed function. No solve, acceptance or route speed claim.
"""
from __future__ import annotations
import argparse
import ast
from dataclasses import asdict
from functools import wraps
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import anysolver
from anysolver.general_contact import s3_patch_augmented as augmented
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from scripts.general_contact_d1_interior_press_dev import build_radial_guided_case


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--saved", type=Path, required=True)
    parser.add_argument("--patched-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    saved = json.loads(args.saved.read_text(encoding="utf-8"))
    assert saved["status"] == "completed" and saved["accepted_steps"] == len(saved["history"]) > 0
    pose = np.asarray(saved["displacements"], dtype=float)
    pressure = np.asarray(saved["history"][-1]["contact"]["numerical_pressure_pa"], dtype=float)
    assert np.all(np.isfinite(pose)) and np.all(np.isfinite(pressure))
    old = augmented._touching_projected_boundaries
    patch_raw = args.patched_source.read_bytes()
    node = next(n for n in ast.parse(patch_raw).body
                if isinstance(n, ast.FunctionDef) and n.name == old.__name__)
    namespace = dict(augmented.__dict__)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(args.patched_source), "exec"), namespace)
    new = namespace[old.__name__]
    record = dict(status="development_started", saved=str(args.saved.resolve()),
        saved_sha256=digest(args.saved), installed_module=str(Path(anysolver.__file__).resolve()),
        installed_augmented_sha256=digest(augmented.__file__), patched_source_sha256=hashlib.sha256(patch_raw).hexdigest(),
        helper_sha256=digest(__file__), scope="same saved-pose reporting; only named predicate patched in memory",
        evaluations=[])
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    start = time.perf_counter()
    model, definition, settings, *_ = build_radial_guided_case(
        target_cells=saved["target_cells"], target_y0_m=saved["target_y0_m"],
        target_right_x_m=saved["target_right_x_m"])
    manager = GeneralS3PatchManager(model, definition, settings)
    manager.set_normal_multipliers(pressure)
    record["preparation_seconds"] = time.perf_counter()-start
    record["numpy_error_policy"] = np.geterr()
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    outputs = []
    try:
        for label, predicate in (("original", old), ("padded_boxes", new)):
            stats = dict(predicate=label, touching_calls=0, true_calls=0, touching_seconds=0.)
            @wraps(predicate)
            def measured(*a, **kw):
                started = time.perf_counter()
                try:
                    value = predicate(*a, **kw)
                    stats["true_calls"] += int(value)
                    return value
                finally:
                    stats["touching_calls"] += 1
                    stats["touching_seconds"] += time.perf_counter()-started
            augmented._touching_projected_boundaries = measured
            start = time.perf_counter()
            force, tangent, certificate = manager.evaluate(pose, tangent=False)
            assert tangent is None
            fields = asdict(certificate)
            encoded = json.dumps(fields, sort_keys=True, allow_nan=False, default=json_scalar)
            stats.update(report_seconds=time.perf_counter()-start,
                force=force.tolist(), certificate=fields,
                certificate_sha256=hashlib.sha256(encoded.encode()).hexdigest())
            outputs.append((force.copy(), encoded))
            record["evaluations"].append(stats)
            args.output.write_text(json.dumps(record, indent=2, default=json_scalar), encoding="utf-8")
        record.update(status="development_complete",
            exact_force_parity=bool(np.array_equal(outputs[0][0], outputs[1][0])),
            maximum_force_difference_n=float(np.max(np.abs(outputs[0][0]-outputs[1][0]))),
            exact_certificate_parity=outputs[0][1] == outputs[1][1],
            exact_branch_counts=all(record["evaluations"][0][k] == record["evaluations"][1][k]
                                    for k in ("touching_calls", "true_calls")))
        args.output.write_text(json.dumps(record, indent=2, default=json_scalar), encoding="utf-8")
        assert record["exact_force_parity"] and record["exact_certificate_parity"] and record["exact_branch_counts"]
    finally:
        augmented._touching_projected_boundaries = old


if __name__ == "__main__":
    main()
