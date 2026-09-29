"""Compare an accepted two-body D1 press with independent linear Q1 mortar."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

from docs.d1_review_support.d1_two_body_reference_oracle import solve_reference
from scripts.general_contact_d1_interior_press_dev import build_interior_press


def main(saved_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    expected = {
        "status": "completed", "accepted_steps": 2,
        "source_columns": 4, "source_rows": 4, "target_s3_faces": 2,
        "source_support": "perimeter", "load_shape": "interior_distributed",
        "force_n": 0.04, "reference_slope": 1.0e-4,
        "slide_body": "target", "four_phase": False,
    }
    if any(saved.get(key) != value for key, value in expected.items()):
        raise ValueError("saved nonlinear press differs from bounded oracle case")
    model, definition, _settings, program = build_interior_press(
        source_support="perimeter", source_columns=4, source_rows=4,
        target_columns=1, target_rows=1, force_n=0.04,
        reference_slope=1.0e-4, load_shape="interior_distributed",
        slide_body="target",
    )
    reference = solve_reference(
        model, definition, program, 2, physical_parallel_skin=True,
    )
    production = saved["history"][-1]["contact"]
    displacement = np.asarray(saved["displacements"], dtype=float)
    source_ids = tuple(production["source_pressure_node_ids"])
    if source_ids != reference["source_pressure_nodes"]:
        raise ValueError("oracle and solver source pressure order differ")
    pressure = np.asarray(production["numerical_pressure_pa"])
    active_production = [node for node, value in zip(source_ids, pressure)
                         if value > 0.0]
    active_reference = [node for node, value in zip(source_ids,
                                                    reference["pressure"])
                        if value > 0.0]
    force_prod = float(production["integration_force"][2])
    force_ref = float(reference["integrated_force"])
    norm_u = max(float(np.linalg.norm(reference["displacement"])), 1.0e-15)
    norm_p = max(float(np.linalg.norm(reference["pressure"])), 1.0e-15)
    normal_gap_at_production = (
        reference["initial_gap"]
        + reference["weighted_gap_work"] @ displacement/reference["support"]
    )
    result = {
        "status": "development_two_body_linear_oracle_comparison",
        "production_input": str(saved_path),
        "reference_scope": "frozen_xy_footprint_linear_two_body_q1_s3",
        "independent_initial_parallel_skin_gap_m": reference["initial_gap"],
        "independent_reference_overlap_area_m2": reference["integrated_area"],
        "oracle_active_set_iterations": reference["active_set_iterations"],
        "production_active_node_ids": active_production,
        "oracle_active_node_ids": active_reference,
        "production_integrated_normal_force_n": force_prod,
        "oracle_integrated_normal_force_n": force_ref,
        "integrated_force_relative_difference": abs(force_prod-force_ref)
                                              /max(abs(force_ref), 1.0e-15),
        "displacement_relative_l2_difference": float(np.linalg.norm(
            displacement-reference["displacement"])/norm_u),
        "pressure_relative_l2_difference": float(np.linalg.norm(
            pressure-reference["pressure"])/norm_p),
        "support_relative_l2_difference": float(np.linalg.norm(
            np.asarray(production["reference_support_m2"])
            -reference["support"])/np.linalg.norm(reference["support"])),
        "oracle_gap_at_production_minimum_m": float(np.min(
            normal_gap_at_production)),
        "production_normalized_gap_minimum_m": float(np.min(
            production["normalized_weighted_gap_m"])),
        "oracle_pressure_pa": reference["pressure"].tolist(),
        "oracle_displacements_m": reference["displacement"].tolist(),
    }
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items()
                      if not key.startswith("oracle_pressure")
                      and not key.startswith("oracle_displacements")}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
