"""Compare selected and fine pressure bases on one bounded coupled Q4/S3 press."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

import numpy as np

from anysolver import solve_static_nonlinear, validate_general_contact
from anysolver.general_contact.pressure_basis import (
    build_q4_source_selected_q1_basis,
)
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def _run(basis: str) -> dict:
    model, definition, settings, program = build_case(
        4, steps_per_segment=2, load_profile="distributed",
        total_force_n=0.3, target_right_x_m=1.3,
    )
    if basis == "selected_q1_knots_dev":
        settings = replace(
            settings, q4_source_pressure_basis=basis,
            q4_source_pressure_knot_columns=(0, 1, 2, 4),
        )
    report = validate_general_contact(model, definition, settings)
    if not report.valid:
        raise ValueError(f"{basis} admission: {report.issues}")
    start = time.perf_counter()
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    contact = result.info.get("general_contact") or {}
    record = {
        "basis": basis,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "elapsed_seconds": time.perf_counter()-start,
        "accepted_steps": len(result.steps),
        "final_displacements_m": result.displacements.tolist(),
        "contact": contact,
        "history": result.info.get("force_displacement_history"),
        "augmentation_attempts": result.info.get("contact_augmentation_attempts"),
        "contact_failure": result.info.get("contact_failure"),
        "profile": report.profile,
    }
    if result.status == "completed":
        mode_ids = tuple(contact["source_pressure_node_ids"])
        mode_pressures = np.asarray(contact["numerical_pressure_pa"], dtype=float)
        faces = tuple(tuple(model.mesh.elements[face].node_ids)
                      for face in definition.surfaces[0].element_ids)
        if basis == "selected_q1_knots_dev":
            transform = build_q4_source_selected_q1_basis(
                faces, settings.q4_source_pressure_knot_columns,
            )
            if mode_ids != transform.mode_ids:
                raise AssertionError("selected pressure mode IDs changed")
            fine_ids = transform.fine_source_node_ids
            fine_pressure = transform.as_array() @ mode_pressures
        else:
            fine_ids = mode_ids
            fine_pressure = mode_pressures
        record["fine_node_ids"] = fine_ids
        record["fine_pressure_pa"] = fine_pressure.tolist()
    return record


def main(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    fine = _run("fine_nodal_q1")
    selected = _run("selected_q1_knots_dev")
    comparison = None
    if fine["status"] == selected["status"] == "completed":
        if fine["fine_node_ids"] != selected["fine_node_ids"]:
            raise AssertionError("fine pressure node identities differ")
        fine_p = np.asarray(fine["fine_pressure_pa"])
        selected_p = np.asarray(selected["fine_pressure_pa"])
        fine_u = np.asarray(fine["final_displacements_m"])
        selected_u = np.asarray(selected["final_displacements_m"])
        fine_c, selected_c = fine["contact"], selected["contact"]
        comparison = {
            "pressure_nodal_relative_l2": float(
                np.linalg.norm(selected_p-fine_p)/np.linalg.norm(fine_p)
            ),
            "displacement_relative_l2": float(
                np.linalg.norm(selected_u-fine_u)/np.linalg.norm(fine_u)
            ),
            "normal_force_difference_n": float(
                np.asarray(selected_c["integration_force"])[2]
                - np.asarray(fine_c["integration_force"])[2]
            ),
            "minimum_gap_difference_m": float(
                selected_c["minimum_gap"]-fine_c["minimum_gap"]
            ),
        }
    record = {
        "candidate": "selected_vs_fine_4q4_two_s3_distributed_press_dev",
        "question": "Does selected pressure space preserve the fine-basis coupled field on this partial-contact fixture?",
        "same_mechanics": {
            "source_q4_faces": 4,
            "target_s3_faces": 2,
            "distributed_downward_force_n": 0.3,
            "target_right_x_m": 1.3,
            "steps_per_segment": 2,
            "selected_knot_columns": [0, 1, 2, 4],
        },
        "fine": fine,
        "selected": selected,
        "comparison": comparison,
    }
    output.write_text(json.dumps(record, indent=2, default=str)+"\n",
                      encoding="utf-8")
    print(json.dumps({
        "fine_status": fine["status"],
        "selected_status": selected["status"],
        "fine_seconds": fine["elapsed_seconds"],
        "selected_seconds": selected["elapsed_seconds"],
        "comparison": comparison,
    }, indent=2))
    if comparison is None:
        raise RuntimeError("coupled selected/fine press did not complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)
