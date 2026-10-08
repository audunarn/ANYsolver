"""Summarize active pressure and structural coordinates at full shell slide."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def summarize(path: Path):
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["status"] != "completed" or record["accepted_steps"] != 12:
        raise ValueError("expected a complete twelve-step development path")
    columns = record["columns"]
    model, _definition, _settings, _program = build_case(
        columns, four_phase=True, steps_per_segment=3,
        load_profile=record["load_profile"],
        total_force_n=record["total_downward_force_n"],
    )
    full_slide = record["history"][5]
    recontact = record["history"][11]
    contact = full_slide["contact"]
    displacements = np.asarray(record["final_displacements"])
    active = []
    for node_id, pressure, support, gap in zip(
            contact["source_pressure_node_ids"],
            contact["normal_multiplier_estimate_pa"],
            contact["reference_support_m2"],
            contact["normalized_weighted_gap_m"], strict=True):
        if pressure <= 0.0:
            continue
        node = model.mesh.nodes[node_id]
        dofs = model.mesh.dof_manager.get_node_dofs(node_id)
        active.append({
            "node_id": node_id,
            "reference_x_m": float(node.x),
            "current_x_m": float(node.x+displacements[dofs[0]]),
            "current_z_m": float(node.z+displacements[dofs[2]]),
            "pressure_pa": float(pressure),
            "support_m2": float(support),
            "pressure_times_support_n": float(pressure*support),
            "normalized_gap_m": float(gap),
        })
    return {
        "source": str(path),
        "columns": columns,
        "slide_force_n": contact["integration_force"][2],
        "recontact_force_n": recontact["contact"]["integration_force"][2],
        "slide_minimum_gap_m": contact["minimum_gap"],
        "slide_overlap_area_m2": contact["reference_overlap_area"],
        "active_pressure_nodes": active,
    }


def main(first: Path, second: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    rows = [summarize(path) for path in (first, second)]
    difference = abs(rows[1]["slide_force_n"]-rows[0]["slide_force_n"])
    record = {
        "comparison": rows,
        "absolute_slide_force_difference_n": difference,
        "relative_to_finer_slide_force": difference/abs(rows[1]["slide_force_n"]),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py EIGHT_JSON SIXTEEN_JSON OUTPUT")
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
