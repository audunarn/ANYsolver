"""Compare two saved source-only pressure fields on one exact Q1 measure.

This postprocessor reads frozen development outputs; it does not call the
contact kernel or either source-only solver.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def _mass(knots: np.ndarray, right: float) -> np.ndarray:
    matrix = np.zeros((len(knots), len(knots)))
    for cell, (left, end) in enumerate(zip(knots[:-1], knots[1:])):
        upper = min(float(end), right)
        if upper <= left:
            continue
        # Exact degree-two integration, including the last clipped y cell.
        for point, weight in ((-1.0 / np.sqrt(3.0), 1.0),
                              (1.0 / np.sqrt(3.0), 1.0)):
            coordinate = (left + upper + (upper - left) * point) / 2.0
            fraction = (coordinate - left) / (end - left)
            shape = np.array((1.0 - fraction, fraction))
            matrix[cell:cell + 2, cell:cell + 2] += (
                (upper - left) * weight * np.outer(shape, shape) / 2.0
            )
    return matrix


def _read(path: Path) -> tuple[dict, dict]:
    data = path.read_bytes()
    record = json.loads(data)
    if len(record["cases"]) != 1:
        raise ValueError("expected one saved case per input")
    return record["cases"][0], {"path": str(path.resolve()),
                                 "sha256": hashlib.sha256(data).hexdigest()}


def compare(selected_path: Path, fine_path: Path) -> dict:
    selected, selected_source = _read(selected_path)
    fine, fine_source = _read(fine_path)
    if ((selected["nx"], selected["ny"]) != (fine["nx"], fine["ny"])
            or fine["pressure_nx"] != fine["nx"]
            or selected["pressure_knots"] is None):
        raise ValueError("fields must share structure with a matched fine basis")
    nx, ny = fine["nx"], fine["ny"]
    x = np.linspace(0.0, 1.0, nx + 1)
    y = np.linspace(0.0, 1.0, ny + 1)
    knots = np.asarray(selected["pressure_knots"], dtype=float)
    if (len(knots) != selected["pressure_nx"] + 1
            or knots[0] != 0.0 or knots[-1] != 1.0
            or not np.all(np.diff(knots) > 0.0)
            or not np.allclose(knots * nx, np.rint(knots * nx),
                               rtol=0.0, atol=1.0e-12)):
        raise ValueError("selected knots must be nested in the fine x grid")
    a = np.asarray(selected["pressure_grid_pa"], dtype=float)
    b = np.asarray(fine["pressure_grid_pa"], dtype=float)
    if (a.shape != (ny + 1, len(knots)) or b.shape != (ny + 1, nx + 1)
            or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b))):
        raise ValueError("invalid pressure grids")
    aligned = np.stack([np.interp(x, knots, row) for row in a])
    difference = aligned - b
    mx, my = _mass(x, 1.0), _mass(y, 0.9)
    def norm_sq(field: np.ndarray) -> float:
        return float(np.sum(field * (my @ field @ mx)))
    fine_norm = np.sqrt(norm_sq(b))
    difference_norm = np.sqrt(norm_sq(difference))
    if fine_norm <= 0.0:
        raise ValueError("fine field has zero norm")
    line_selected = np.asarray(selected["line_pressure_n_per_m"], dtype=float)
    line_fine = np.asarray(fine["line_pressure_n_per_m"], dtype=float)
    if line_selected.shape != (len(knots),) or line_fine.shape != (nx + 1,):
        raise ValueError("invalid line pressure shapes")
    line_difference = np.interp(x, knots, line_selected) - line_fine
    return {
        "method": "exact common-Q1 L2 over x=[0,1], y=[0,0.9]",
        "selected_source": selected_source,
        "fine_source": fine_source,
        "structural_cells": [nx, ny],
        "selected_pressure_modes": selected["pressure_modes"],
        "fine_pressure_modes": fine["pressure_modes"],
        "selected_active_scaled_compliance_minimum_eigenvalue":
            selected["active_scaled_compliance_minimum_eigenvalue"],
        "fine_active_scaled_compliance_minimum_eigenvalue":
            fine["active_scaled_compliance_minimum_eigenvalue"],
        "selected_active_scaled_compliance_condition":
            selected["active_scaled_compliance_condition"],
        "fine_active_scaled_compliance_condition":
            fine["active_scaled_compliance_condition"],
        "selected_pressure_l2_pa_m": np.sqrt(norm_sq(aligned)),
        "fine_pressure_l2_pa_m": fine_norm,
        "difference_pressure_l2_pa_m": difference_norm,
        "relative_pressure_l2": difference_norm / fine_norm,
        "maximum_node_pressure_difference_pa": float(np.max(np.abs(difference))),
        "maximum_node_pressure_difference_relative":
            float(np.max(np.abs(difference)) / np.max(b)),
        "relative_line_pressure_l2": float(np.sqrt(line_difference @ mx @ line_difference
                                                   / (line_fine @ mx @ line_fine))),
        "reaction_difference_n": (selected["integrated_reaction_n"]
                                   - fine["integrated_reaction_n"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selected", type=Path)
    parser.add_argument("fine", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(compare(args.selected, args.fine), indent=2) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
