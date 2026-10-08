"""Screen nonnegative front-clustered pressure knots at fixed 128-Q4 structure.

The observed front interval informs these developmental candidate knots. The
comparison is exact for piecewise bilinear Q1 pressure fields on the common
reference strip; the matched fine linearized field is a comparator, not an
accepted continuum reference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.general_contact_d1_linearized_front_reference import _linearized_case


def _cluster_knots(subdivisions: int) -> tuple[float, ...]:
    if subdivisions not in (2, 3, 4, 6, 8, 10):
        raise ValueError("bounded candidate subdivisions are 2, 3, 4, 6, 8 and 10")
    knots = [0.0]
    for cell in range(16):
        parts = subdivisions if 9 <= cell < 13 else 1
        knots.extend((cell+part/parts)/16.0
                     for part in range(1, parts+1))
    return tuple(knots)


def _field_value(case: dict, x: float, y: float) -> float:
    knots = np.asarray(case["pressure_knots"] if case["pressure_knots"] is not None
                       else np.linspace(0.0, 1.0, case["pressure_columns"]+1))
    cell = min(len(knots)-2, int(np.searchsorted(knots, x, side="right")-1))
    local = (x-knots[cell])/(knots[cell+1]-knots[cell])
    pressure = case["pressure"]
    return float((1-y)*((1-local)*pressure[0, cell]
                         + local*pressure[0, cell+1])
                 + y*((1-local)*pressure[1, cell]
                      + local*pressure[1, cell+1]))


def _squared_difference(first: dict, second: dict | None = None,
                        x_min: float = 0.0, x_max: float = 1.0) -> float:
    if not 0.0 <= x_min < x_max <= 1.0:
        raise ValueError("comparison interval must lie in [0,1]")
    candidates = (first,) if second is None else (first, second)
    breaks = {x_min, x_max}
    for case in candidates:
        knots = (case["pressure_knots"] if case["pressure_knots"] is not None
                 else np.linspace(0.0, 1.0, case["pressure_columns"]+1))
        breaks.update(float(knot) for knot in knots
                      if x_min < knot < x_max)
    gauss = (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0))
    result = 0.0
    for left, right in zip(sorted(breaks), sorted(breaks)[1:]):
        for gx in gauss:
            x = 0.5*(left+right+(right-left)*gx)
            for gy in gauss:
                y = 0.5*(1.0+gy)
                difference = _field_value(first, x, y)
                if second is not None:
                    difference -= _field_value(second, x, y)
                result += 0.25*(right-left)*difference*difference
    return result


def main(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    reference = _linearized_case(128, 128)
    uniform = [_linearized_case(128, pressure_columns)
               for pressure_columns in (16, 32, 48, 64)]
    clustered = [_linearized_case(128, pressure_knots=_cluster_knots(parts))
                 for parts in (4, 8, 10)]
    norm = _squared_difference(reference)
    if norm <= 0.0:
        raise ValueError("fine comparison pressure is zero")
    cases = []
    for label, case in ((f"uniform_{item['pressure_columns']}", item)
                        for item in uniform):
        cases.append((label, case))
    cases.extend((f"front_cluster_{parts}", case)
                 for parts, case in zip((4, 8, 10), clustered))
    comparisons = []
    for label, case in cases:
        comparisons.append({
            "candidate": label,
            "pressure_columns": case["pressure_columns"],
            "relative_full_l2_to_fine": float(np.sqrt(
                _squared_difference(case, reference)/norm
            )),
            "absolute_front_l2_pa_sqrt_m": float(np.sqrt(
                _squared_difference(case, reference, 0.625, 0.75)
            )),
            "absolute_interior_l2_pa_sqrt_m": float(np.sqrt(
                _squared_difference(case, reference, 0.8, 1.0)
            )),
            "integrated_force_difference_n": (
                case["integrated_force_n"]-reference["integrated_force_n"]
            ),
            "tip_displacement_difference_m": (
                case["tip_vertical_displacement_m"]
                -reference["tip_vertical_displacement_m"]
            ),
            "minimum_physical_overlap_gap_m": (
                case["minimum_physical_overlap_gap_m"]
            ),
            "first_active_reference_x": case["first_active_reference_x"],
            "maximum_pressure_pa": case["maximum_pressure_pa"],
            "active_modes": case["active_modes"],
            "active_work_rank": case["active_work_rank"],
            "active_compliance_scaled_condition": (
                case["active_compliance_scaled_condition"]
            ),
        })
    nested = []
    for structural_columns in (32, 48, 64, 96, 128):
        parts = structural_columns//16
        coarse = _linearized_case(
            structural_columns, pressure_knots=_cluster_knots(parts),
        )
        fine = _linearized_case(structural_columns, structural_columns)
        nested.append({
            "structural_columns": structural_columns,
            "cluster_subdivisions": parts,
            "cluster_pressure_modes": coarse["supported_modes"],
            "fine_pressure_modes": fine["supported_modes"],
            "relative_full_l2_to_fine": float(np.sqrt(
                _squared_difference(coarse, fine)
                /_squared_difference(fine)
            )),
            "integrated_force_difference_n": (
                coarse["integrated_force_n"]-fine["integrated_force_n"]
            ),
            "minimum_physical_gap_difference_m": (
                coarse["minimum_physical_overlap_gap_m"]
                -fine["minimum_physical_overlap_gap_m"]
            ),
            "cluster_active_condition": (
                coarse["active_compliance_scaled_condition"]
            ),
            "fine_active_condition": (
                fine["active_compliance_scaled_condition"]
            ),
        })
    report = {
        "candidate": "fixed_128q4_front_cluster_pressure_screen_dev",
        "reference": "uniform 128-column pressure on the same 128-Q4 linearized structure; not a continuum oracle",
        "clustered_interval": [9/16, 13/16],
        "comparisons": comparisons,
        "nested_structural_pressure_comparisons": nested,
        "clustered_pressure_knots": {
            f"front_cluster_{parts}": list(_cluster_knots(parts))
            for parts in (4, 8, 10)
        },
    }
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"fixed_128q4": comparisons,
                      "nested": nested}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    main(args.output)
