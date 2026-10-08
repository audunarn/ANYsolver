"""Bounded x/y refinement of the independent D1 scalar obstacle reference."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from general_contact_d1_continuum_obstacle_reference import (
    PARTIAL_CONTACT_HEIGHT_M, _full_width_exact_check, solve, summarize,
)


def _x_force(solution, bins: int) -> np.ndarray:
    force = np.sum(solution.pressure_force, axis=0)
    if solution.nx % bins:
        raise ValueError("comparison bins must partition x grid")
    return force.reshape(bins, solution.nx // bins).sum(axis=1)


def _compare(first, second, bins: int) -> dict:
    left = _x_force(first, bins)
    right = _x_force(second, bins)
    difference = left-right
    return {
        "first_grid": [first.nx, first.ny],
        "second_grid": [second.nx, second.ny],
        "common_x_bins": bins,
        "force_difference_n": float(np.sum(difference)),
        "x_force_l1_relative": float(np.sum(np.abs(difference))
                                     / np.sum(np.abs(right))),
        "x_force_l2_relative": float(np.linalg.norm(difference)
                                     / np.linalg.norm(right)),
        "cumulative_force_max_relative": float(np.max(np.abs(
            np.cumsum(difference)
        )) / np.sum(np.abs(right))),
    }


def _fine_q1_x_force(report_path: Path) -> np.ndarray:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    case = next(item for item in report["cases"] if item["columns"] == 128)
    pressure = np.asarray(case["pressure"], dtype=float)
    if pressure.shape != (2, 129):
        raise ValueError("saved fine Q1 field has unexpected layout")
    # Source y is [0.1,1.1], represented contact y is [0.1,1.0].
    # Exact integrated source Q1 supports on that interval are .495/.405 m.
    integrated_line = 0.495 * pressure[0] + 0.405 * pressure[1]
    return (integrated_line[:-1] + integrated_line[1:]) / 256.0


def main() -> None:
    grids = ((128, 160), (128, 320), (256, 160), (256, 320))
    solutions = {
        grid: solve(*grid, PARTIAL_CONTACT_HEIGHT_M) for grid in grids
    }
    full = solve(256, 320, 1.0)
    source_path = Path(
        "reports/general_contact_d1_linearized_front_stationary_dev_20260928.json"
    )
    fine_q1 = _fine_q1_x_force(source_path)
    continuum_128 = _x_force(solutions[(256, 320)], 128)
    difference = fine_q1-continuum_128
    report = {
        "method": "independent_scalar_shear_obstacle_xy_refinement_dev",
        "source_pressure_report": str(source_path),
        "full_width_large_control": {
            **summarize(full), **_full_width_exact_check(full),
        },
        "partial_width": [summarize(solutions[grid]) for grid in grids],
        "comparisons": [
            _compare(solutions[a], solutions[b], bins)
            for a, b, bins in (
                ((128, 160), (128, 320), 128),
                ((128, 160), (256, 160), 128),
                ((128, 320), (256, 320), 128),
                ((256, 160), (256, 320), 256),
            )
        ],
        "fine_q1_vs_256x320_continuum": {
            "force_difference_n": float(np.sum(difference)),
            "x_force_l1_relative": float(np.sum(np.abs(difference))
                                         / np.sum(np.abs(continuum_128))),
            "x_force_l2_relative": float(np.linalg.norm(difference)
                                         / np.linalg.norm(continuum_128)),
            "cumulative_force_max_relative": float(np.max(np.abs(
                np.cumsum(difference)
            )) / np.sum(np.abs(continuum_128))),
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
