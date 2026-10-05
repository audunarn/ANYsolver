"""One finite-law spatial discriminator using the retained radial reference.

Only the fixture factory is adapted; structural geometry, loads, boundary
traces and independent reference are reused. No production monkeypatch occurs.
This is development evidence and consumes no former D1 execution authority.
"""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
import sys

import numpy as np
import scipy
import anysolver
from anysolver import validate_general_contact
from docs.d1_review_support.d2_projected_penalty_shell_dev import fixture, file_identity
from scripts import general_contact_d1_interior_press_dev as retained


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    freeze = args.output.with_suffix(".inputs.json")
    snapshot = args.output.with_suffix(".runner.source.py")
    if any(p.exists() for p in (args.output, freeze, snapshot)):
        raise FileExistsError("exclusive output already exists")
    original_factory = retained.build_radial_guided_case
    source_paths = (Path(__file__), Path(retained.__file__),
        Path("docs/d1_review_support/d1_radial_two_body_reference.py"),
        Path("docs/d1_review_support/d2_projected_penalty_shell_dev.py"))
    record = {"accepted": False, "released": False,
        "purpose": "finite-law same-spatial-mechanics integrated response discriminator",
        "resource_caps": {"seconds": 900, "process_tree_bytes": 4000000000},
        "environment": {"python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
            "anysolver": str(Path(anysolver.__file__).resolve())},
        "source": {str(p): file_identity(p) for p in source_paths},
        "production": {p.name: file_identity(p) for p in
            (Path(anysolver.__file__).parent/"general_contact").glob("*.py")},
        "targets": {"integrated_response_relative": .02, "physical_gap_m": 5e-5,
            "force_and_moment_balance_relative": 1e-6},
        "limits": "guided flat elastic fixed-MIN3 spatial comparison; no boundary or uniform-stability admission"}
    snapshot.write_bytes(Path(__file__).read_bytes())

    def finite_factory(**kwargs):
        model, definition, old_settings, program, reference, inputs = original_factory(**kwargs)
        definition = replace(definition, interactions=tuple(replace(interaction,
            normal_law="projected_penalty", normal_stiffness=1e7)
            for interaction in definition.interactions))
        settings = fixture(1e7)[2]
        report = validate_general_contact(model, definition, settings)
        if not report.valid:
            raise ValueError(f"finite-law spatial preflight rejected: {report.issues}")
        record.update(geometry_and_reference=inputs, contact_definition=asdict(definition),
            contact_settings=asdict(settings), path_program=program.contract(),
            capability_profile=report.profile)
        freeze.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
        inputs.update(normal_law="projected_penalty", normal_regularization_pa_per_m=1e7,
            capability_profile=report.profile, d1_admission=False,
            development_inputs=file_identity(freeze))
        return model, definition, settings, program, reference, inputs

    retained.build_radial_guided_case = finite_factory
    try:
        retained.radial_solve(args.output, target_cells=12, target_right_x_m=1.297)
    finally:
        retained.build_radial_guided_case = original_factory
    result = json.loads(args.output.read_text(encoding="utf-8"))
    checks = {"completed_two_steps": result.get("status") == "completed" and result.get("accepted_steps") == 2}
    if checks["completed_two_steps"]:
        checks.update(force_response=result["force_relative_error"] <= .02,
            source_displacements=max(p["relative_error"] for p in result["source_displacement_samples"]) <= .02,
            target_displacements=max(p["relative_error"] for p in result["target_displacement_samples"]) <= .02,
            independent_gap=bool(result["independent_gap_lower_m"]["gap_tolerance_met"]))
    result.update(accepted=False, released=False, finite_law_development_checks=checks,
        finite_law_development_checks_met=all(checks.values()),
        adapter=file_identity(__file__))
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"finite_law_development_checks": checks}), flush=True)
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
