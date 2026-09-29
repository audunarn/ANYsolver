"""Check an accepted D1 pose using the standalone independent gap oracle."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

from examples.general_contact_d1_interior_controls_dev import (
    build_model, _independent_projected_gap_bound,
)
from scripts.general_contact_d1_interior_press_dev import build_interior_press


def main(saved_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    if (saved.get("status") != "completed"
            or saved.get("source_columns") != 4
            or saved.get("source_rows") != 4
            or saved.get("target_s3_faces") != 2):
        raise ValueError("independent gap check needs accepted 16-Q4/two-S3 pose")
    model, definition, _ = build_model()
    lower = _independent_projected_gap_bound(
        model, definition, np.asarray(saved["displacements"], dtype=float),
        definition.interactions[0].gap_tolerance,
    )
    record = {
        "status": "development_independent_gap_pass",
        "saved_pose": str(saved_path),
        "independent_conservative_lower_gap_m": lower,
        "solver_conservative_lower_gap_m": saved["history"][-1]["contact"][
            "minimum_gap"],
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


def interior_press(saved_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    if (saved.get("status") != "completed"
            or saved.get("accepted_steps") != 2
            or saved.get("source_support") != "perimeter"
            or saved.get("target_rows") != 1
            or saved.get("load_shape") != "interior_distributed"
            or saved.get("slide_body") != "target"
            or saved.get("force_n") != 0.04
            or saved.get("reference_slope") != 1.0e-4):
        raise ValueError("saved pose differs from bounded interior press")
    model, definition, _settings, _program = build_interior_press(
        source_support="perimeter",
        source_columns=saved["source_columns"],
        source_rows=saved["source_rows"],
        source_y_profile=saved.get("source_y_profile"),
        offline_structural_reference_y16=saved.get(
            "offline_structural_reference_y16", False),
        target_columns=saved["target_s3_faces"]//2,
        target_rows=1, force_n=0.04, reference_slope=1.0e-4,
        load_shape="interior_distributed", slide_body="target",
    )
    lower = _independent_projected_gap_bound(
        model, definition, np.asarray(saved["displacements"], dtype=float),
        definition.interactions[0].gap_tolerance,
    )
    record = {
        "status": "development_independent_gap_pass",
        "saved_pose": str(saved_path),
        "independent_conservative_lower_gap_m": lower,
        "solver_conservative_lower_gap_m": saved["history"][-1]["contact"][
            "minimum_gap"],
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interior-press":
        interior_press(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        main(Path(sys.argv[1]), Path(sys.argv[2]))
