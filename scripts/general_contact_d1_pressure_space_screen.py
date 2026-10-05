"""Separate structural Q4 and primal Q1 pressure resolution at a flat front.

This runs only the independent fixed-geometry linearized development model.
It screens pressure-space candidates without spending a coupled-solve or
qualification execution authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from scripts.general_contact_d1_linearized_front_reference import _linearized_case
from scripts.general_contact_d1_pressure_field_compare import _squared_norm


STRUCTURAL_COLUMNS = (16, 24, 32, 48, 64, 96, 128)


def _field(case: dict) -> tuple[int, np.ndarray, dict]:
    return case["pressure_columns"], case["pressure"], {}


def _comparison(first: dict, second: dict) -> dict:
    earlier, later = _field(first), _field(second)
    return {
        "structural_columns": [first["columns"], second["columns"]],
        "pressure_columns": [first["pressure_columns"],
                             second["pressure_columns"]],
        "relative_full_l2": float(np.sqrt(
            _squared_norm(earlier, later)/_squared_norm(later)
        )),
        "absolute_front_l2_pa_sqrt_m": float(np.sqrt(
            _squared_norm(earlier, later, x_min=0.625, x_max=0.75)
        )),
        "absolute_interior_l2_pa_sqrt_m": float(np.sqrt(
            _squared_norm(earlier, later, x_min=0.8, x_max=1.0)
        )),
        "integrated_force_change_n": (
            second["integrated_force_n"]-first["integrated_force_n"]
        ),
        "tip_displacement_change_m": (
            second["tip_vertical_displacement_m"]
            - first["tip_vertical_displacement_m"]
        ),
    }


def main(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    cache = {}
    policies = {
        "fixed_16_q1": lambda n: 16,
        "paired_q1": lambda n: n//2,
        "fine_q1": lambda n: n,
    }
    cases = {}
    for policy, pressure_columns in policies.items():
        cases[policy] = []
        for structural_columns in STRUCTURAL_COLUMNS:
            key = structural_columns, pressure_columns(structural_columns)
            if key not in cache:
                cache[key] = _linearized_case(*key)
            cases[policy].append(cache[key])

    # Equal-resolution common refinement must reproduce the earlier validated
    # fine-space trends. This is a replay comparison, not a second coupled run.
    finest = cases["fine_q1"]
    expected = (0.070395168, 0.13815739)
    observed = tuple(_comparison(a, b)["relative_full_l2"]
                     for a, b in zip(finest, finest[1:]))[:2]
    if any(abs(a-b) > 1.0e-5 for a, b in zip(observed, expected)):
        raise AssertionError("equal-mesh common refinement changed the saved trend")

    policy_reports = {}
    for name, sequence in cases.items():
        policy_reports[name] = {
            "cases": [{key: (value.tolist() if isinstance(value, np.ndarray)
                            else value) for key, value in case.items()}
                      for case in sequence],
            "adjacent": [_comparison(a, b)
                         for a, b in zip(sequence, sequence[1:])],
            "against_policy_finest": [_comparison(case, sequence[-1])
                                      for case in sequence[:-1]],
        }
    pressure_sweep_columns = (8, 16, 24, 32, 48, 64, 96, 128)
    for pressure_columns in pressure_sweep_columns:
        key = (128, pressure_columns)
        if key not in cache:
            cache[key] = _linearized_case(*key)
    sweep = [cache[(128, pressure_columns)]
             for pressure_columns in pressure_sweep_columns]
    sweep_report = {
        "structural_columns": 128,
        "pressure_columns": pressure_sweep_columns,
        "cases": [{key: (value.tolist() if isinstance(value, np.ndarray)
                        else value) for key, value in case.items()}
                  for case in sweep],
        "adjacent": [_comparison(a, b)
                     for a, b in zip(sweep, sweep[1:])],
        "against_finest_pressure": [_comparison(case, sweep[-1])
                                    for case in sweep[:-1]],
    }
    report = {
        "candidate": "linearized_q4_structural_vs_q1_pressure_resolution_screen_dev",
        "limits": "source-only Q4 tangent; independent flat Q1 contact work and QP; no nonlinear moving geometry or continuum mechanics reference",
        "structural_columns": STRUCTURAL_COLUMNS,
        "unique_structural_pressure_cases": len(cache),
        "elapsed_seconds": time.perf_counter()-started,
        "policies": policy_reports,
        "fixed_structural_pressure_sweep": sweep_report,
    }
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "unique_cases": len(cache),
        "elapsed_seconds": report["elapsed_seconds"],
        "policies": {
            name: {
                "adjacent_full_l2": [item["relative_full_l2"]
                                     for item in data["adjacent"]],
                "case_minimum_physical_gap_m": [
                    item["minimum_physical_overlap_gap_m"]
                    for item in data["cases"]
                ],
            } for name, data in policy_reports.items()
        },
        "fixed_structural_pressure_sweep": {
            "pressure_columns": pressure_sweep_columns,
            "relative_full_l2_to_fine": [
                item["relative_full_l2"]
                for item in sweep_report["against_finest_pressure"]
            ],
            "minimum_physical_gap_m": [
                item["minimum_physical_overlap_gap_m"]
                for item in sweep_report["cases"]
            ],
        },
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    main(args.output)
