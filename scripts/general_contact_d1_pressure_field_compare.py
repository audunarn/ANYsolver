"""Compare saved distributed Q4/S3 pressure fields on the reference strip.

This read-only development diagnostic uses exact tensor-product two-point
quadrature for the squared difference of piecewise bilinear fields. It does not
call ANYsolver contact geometry, constitutive code, or acceptance machinery.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _field(path: Path) -> tuple[int, np.ndarray, dict]:
    report = json.loads(path.read_text(encoding="utf-8"))
    columns = report["columns"]
    if (type(columns) is not int or columns < 2
            or report["status"] != "completed"
            or report["steps_per_segment"] != 3
            or report["load_profile"] != "distributed"
            or report["total_downward_force_n"] != 0.3
            or report["target_right_x_m"] != 1.3
            or len(report["history"]) < 3):
        raise ValueError(f"incompatible distributed full-press report: {path}")
    contact = report["history"][2]["contact"]
    stride = columns + 1
    fine_ids = list(range(1, 2*stride+1))
    ids = contact["source_pressure_node_ids"]
    pressure = np.asarray(contact["numerical_pressure_pa"], dtype=float)
    if len(ids) != len(pressure) or not np.all(np.isfinite(pressure)):
        raise ValueError(f"invalid pressure vector: {path}")
    if contact.get("pressure_basis_version") == "q4_source_macro_q1_pair_v1":
        if (columns % 2 or contact.get("source_geometry_node_ids") != fine_ids
                or ids != ([i for i in range(1, stride+1, 2)]
                           + [i for i in range(stride+1, 2*stride+1, 2)])):
            raise ValueError(f"unexpected macro strip topology: {path}")
        anchors = dict(zip(ids, pressure))
        pressure = np.asarray([
            anchors[node] if node in anchors
            else 0.5*(anchors[node-1]+anchors[node+1])
            for node in fine_ids
        ])
    elif ids != fine_ids:
        raise ValueError(f"unexpected fine strip topology: {path}")
    if np.min(pressure) < -1.0e-12:
        raise ValueError(f"negative reported pressure: {path}")
    return columns, pressure.reshape(2, stride), report


def _value(field: tuple[int, np.ndarray, dict], x: float, y: float) -> float:
    columns, pressure, _ = field
    cell = min(columns-1, int(x*columns))
    local_x = x*columns-cell
    return float((1-y)*((1-local_x)*pressure[0, cell]
                         + local_x*pressure[0, cell+1])
                 + y*((1-local_x)*pressure[1, cell]
                      + local_x*pressure[1, cell+1]))


def _squared_norm(a: tuple[int, np.ndarray, dict],
                  b: tuple[int, np.ndarray, dict] | None = None) -> float:
    columns = (a[0],) if b is None else (a[0], b[0])
    breaks = sorted({i/n for n in columns for i in range(n+1)})
    gauss = (-1/np.sqrt(3), 1/np.sqrt(3))
    result = 0.0
    for lower, upper in zip(breaks, breaks[1:]):
        for gx in gauss:
            x = 0.5*(lower+upper+(upper-lower)*gx)
            for gy in gauss:
                y = 0.5*(1+gy)
                difference = _value(a, x, y)
                if b is not None:
                    difference -= _value(b, x, y)
                result += 0.25*(upper-lower)*difference*difference
    return result


def main(paths: list[Path], output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    if len(paths) < 2:
        raise ValueError("provide at least two reports")
    fields = [_field(path) for path in paths]
    reference = fields[-1]
    comparisons = []
    for path, field in zip(paths[:-1], fields[:-1]):
        comparisons.append({
            "report": str(path),
            "columns": field[0],
            "pressure_basis": field[2].get("pressure_basis", "fine_nodal_q1"),
            "relative_reference_l2": float(np.sqrt(
                _squared_norm(field, reference)/_squared_norm(reference))),
        })
    result = {
        "purpose": "development reference-surface pressure-field comparison",
        "reference_report": str(paths[-1]),
        "reference_columns": reference[0],
        "measure": "exact squared piecewise-bilinear L2 over common-refined unit reference strip",
        "comparisons": comparisons,
    }
    if len(fields) >= 3 and fields[0][0] == fields[1][0]:
        result["first_two_same_mesh_relative_l2"] = float(np.sqrt(
            _squared_norm(fields[1], fields[0])/_squared_norm(fields[0])))
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="+",
                        help="comparison reports followed by the reference report")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.reports, args.output)
