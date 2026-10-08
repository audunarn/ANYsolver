"""Compare saved Q4/S3 cumulative contact reaction on the reference overlap.

The flat case has source y in [0.1,1.1] m and target y in [0,1] m. Q1
pressure therefore integrates over y in [0.1,1] with exact row weights
0.495 and 0.405 m. The source x span is one meter and lies inside the target.
This is a development weak-response diagnostic, not an acceptance oracle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.general_contact_d1_pressure_field_compare import _field


def _line_reaction(field: tuple[int, np.ndarray, dict]) -> np.ndarray:
    pressure = field[1]
    return 0.495*pressure[0] + 0.405*pressure[1]


def _cumulative(line: np.ndarray, x: float) -> float:
    columns = len(line)-1
    if not 0.0 <= x <= 1.0:
        raise ValueError("reference coordinate must lie in [0,1]")
    cell = min(columns-1, int(x*columns))
    width = 1.0/columns
    preceding = float(np.sum((line[:cell]+line[1:cell+1])*width/2.0))
    t = x*columns-cell
    return preceding + width*(line[cell]*t
                              + (line[cell+1]-line[cell])*t*t/2.0)


def _line_at(line: np.ndarray, x: float) -> float:
    return float(np.interp(x, np.linspace(0, 1, len(line)), line))


def _maximum_cumulative_difference(a: np.ndarray, b: np.ndarray):
    na, nb = len(a)-1, len(b)-1
    breaks = sorted({i/n for n in (na, nb) for i in range(n+1)})
    best = 0.0
    location = 0.0
    for left, right in zip(breaks, breaks[1:]):
        delta_left = _line_at(a, left)-_line_at(b, left)
        delta_right = _line_at(a, right)-_line_at(b, right)
        points = [left, right]
        if delta_left*delta_right < 0:
            points.append(left + (right-left)*(-delta_left)
                          /(delta_right-delta_left))
        for x in points:
            difference = abs(_cumulative(a, x)-_cumulative(b, x))
            if difference > best:
                best, location = difference, x
    return float(best), float(location)


def analyze(paths: list[Path]) -> dict:
    if len(paths) < 2:
        raise ValueError("provide at least two saved full-press reports")
    fields = [_field(path) for path in paths]
    if any(field[2].get("target_columns", 1) != 1
           or field[2].get("pressure_basis", "fine_nodal_q1")
           != "fine_nodal_q1" for field in fields):
        raise ValueError("requires one flat two-S3 target and fine Q1 pressure")
    lines = [_line_reaction(field) for field in fields]
    totals = [_cumulative(line, 1.0) for line in lines]
    rows = []
    for path, field, total in zip(paths, fields, totals):
        source_force = float(field[2]["history"][2]["contact"]["integration_force"][2])
        rows.append({
            "report": str(path), "columns": field[0],
            "cumulative_total_n": total,
            "reported_contact_force_n": source_force,
            "total_minus_reported_n": total-source_force,
        })
    adjacent = []
    for index in range(len(lines)-1):
        maximum, location = _maximum_cumulative_difference(
            lines[index], lines[index+1],
        )
        adjacent.append({
            "earlier_columns": fields[index][0],
            "later_columns": fields[index+1][0],
            "maximum_absolute_cumulative_difference_n": maximum,
            "location_reference_x": location,
            "relative_later_total": maximum/totals[index+1],
        })
    return {
        "purpose": "development cumulative normal reaction comparison",
        "measure": "exact reference-strip Q1 pressure integration over physical y overlap [0.1,1] m and source x [0,1] m",
        "cases": rows,
        "adjacent_comparisons": adjacent,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = analyze(args.reports)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
