"""Compare saved nodal pressure diagnostics without rerunning coupled solves."""

import argparse
import json
from pathlib import Path

import numpy as np


def summarize(path: Path):
    record = json.loads(path.read_text(encoding="utf-8"))
    if (record["status"] != "completed"
            or record["geometry_profile"] != "central"
            or record["total_load_n"] != 2.0
            or record["normal_stiffness"] != 100_000.0
            or not record["supported_schur"]):
        raise ValueError("pressure comparison needs completed central 2 N cases")
    divisions = record["divisions"]
    contact = record["general_contact"]
    ids = np.asarray(contact["source_pressure_node_ids"], dtype=int)
    support = np.asarray(contact["reference_support_m2"], dtype=float)
    pressure = np.asarray(contact["numerical_pressure_pa"], dtype=float)
    if (len(ids) != (divisions+1)**2 or len(support) != len(ids)
            or len(pressure) != len(ids)):
        raise ValueError("pressure diagnostics and regular source mesh disagree")
    active = pressure > 0.0
    nodal_force = support*pressure
    force = np.asarray(contact["integration_force"], dtype=float)
    moment = np.asarray(contact["integration_moment"], dtype=float)
    x_index = (ids-1) % (divisions+1)
    y_index = (ids-1) // (divisions+1)
    return {
        "divisions": divisions,
        "integrated_normal_force_n": float(force[2]),
        "support_pressure_sum_n": float(np.sum(nodal_force)),
        "physical_resultant_center_xy_m": [
            float(-moment[1]/force[2]), float(moment[0]/force[2]),
        ],
        "active_nodes": int(np.count_nonzero(active)),
        "active_support_sum_m2": float(np.sum(support[active])),
        "maximum_nodal_pressure_pa": float(np.max(pressure)),
        "pressure_force_by_x_strip_n": np.bincount(
            x_index, weights=nodal_force, minlength=divisions+1,
        ).tolist(),
        "pressure_force_by_y_strip_n": np.bincount(
            y_index, weights=nodal_force, minlength=divisions+1,
        ).tolist(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("input", type=Path, nargs="+")
    args = parser.parse_args()
    if len(args.input) < 2:
        parser.error("compare at least two completed meshes")
    rows = [summarize(path) for path in args.input]
    args.output.write_text(json.dumps({
        "profile": "saved_coupled_q4_s3_pressure_distribution_dev",
        "rows": rows,
    }, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print({key: value for key, value in row.items()
               if not key.startswith("pressure_force_by_")})


if __name__ == "__main__":
    main()
