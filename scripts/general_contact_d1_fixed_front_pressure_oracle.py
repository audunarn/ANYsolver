"""Independent affine-front pressure oracle for saved fixed-pose probe reports.

Only the saved nodal pressures and supports enter this calculation. Basis
integrals are analytic and field errors use exact two-point product quadrature
for the squared piecewise bilinear difference from an affine positive part.
The reference is a local-plane approximation to the tilted shell projection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _hat_integrals(divisions: int, lower: float, upper: float):
    """Integrals of each piecewise linear hat and x times that hat."""
    mass = np.zeros(divisions + 1)
    first_moment = np.zeros(divisions + 1)
    for cell in range(divisions):
        x0, x1 = cell / divisions, (cell + 1) / divisions
        a, b = max(lower, x0), min(upper, x1)
        if a >= b:
            continue
        h = x1 - x0
        delta1 = b - a
        delta2 = (b*b - a*a) / 2.0
        delta3 = (b*b*b - a*a*a) / 3.0
        mass[cell] += (x1*delta1 - delta2) / h
        mass[cell + 1] += (delta2 - x0*delta1) / h
        first_moment[cell] += (x1*delta2 - delta3) / h
        first_moment[cell + 1] += (delta3 - x0*delta2) / h
    return mass, first_moment


def _field_squared_error(pressure: np.ndarray, left: float, right: float,
                         bottom: float, top: float, midpoint: float,
                         stiffness: float, slope: float) -> float:
    rows, columns = pressure.shape[0] - 1, pressure.shape[1] - 1
    gauss = (-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))
    squared = 0.0
    for row in range(rows):
        y0, y1 = row / rows, (row + 1) / rows
        a_y, b_y = max(bottom, y0), min(top, y1)
        if a_y >= b_y:
            continue
        for column in range(columns):
            x0, x1 = column / columns, (column + 1) / columns
            edges = sorted({max(left, x0), min(right, x1), midpoint})
            for a_x, b_x in zip(edges, edges[1:]):
                a_x, b_x = max(a_x, left, x0), min(b_x, right, x1)
                if a_x >= b_x:
                    continue
                for gx in gauss:
                    x = (a_x + b_x + (b_x - a_x)*gx) / 2.0
                    u = (x - x0) * columns
                    for gy in gauss:
                        y = (a_y + b_y + (b_y - a_y)*gy) / 2.0
                        v = (y - y0) * rows
                        numerical = (
                            (1-v)*((1-u)*pressure[row, column]
                                   + u*pressure[row, column+1])
                            + v*((1-u)*pressure[row+1, column]
                                 + u*pressure[row+1, column+1])
                        )
                        reference = stiffness*slope*max(midpoint-x, 0.0)
                        squared += ((b_x-a_x)*(b_y-a_y)/4.0
                                    * (numerical-reference)**2)
    return squared


def analyze(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("profile") != "fixed_affine_partial_pressure_central_q4_s3_dev":
        raise ValueError("unexpected fixed-pose probe profile")
    left, right = map(float, report["target_x_range_m"])
    bottom, top = map(float, report["target_y_range_m"])
    midpoint = (left + right) / 2.0
    stiffness = float(report["normal_stiffness_pa_per_m"])
    slope = float(report["gap_slope"])
    reference_squared = (stiffness*slope)**2 * (top-bottom) * (
        midpoint-left)**3 / 3.0
    if not (0 <= left < midpoint < right <= 1
            and 0 <= bottom < top <= 1
            and reference_squared > 0):
        raise ValueError("invalid analytic overlap or pressure scale")

    results = []
    for record in report["rows"]:
        columns, rows = int(record["divisions"]), int(record["rows"])
        count = (columns+1)*(rows+1)
        ids = record["source_pressure_node_ids"]
        if sorted(ids) != list(range(1, count+1)):
            raise ValueError("pressure-node topology does not match rectangular grid")
        pressure = np.zeros(count)
        support = np.zeros(count)
        pressure[np.asarray(ids)-1] = record["numerical_pressure_pa"]
        support[np.asarray(ids)-1] = record["reference_support_m2"]
        if not np.all(np.isfinite(pressure)) or not np.all(np.isfinite(support)):
            raise ValueError("nonfinite pressure or support")
        pressure = pressure.reshape(rows+1, columns+1)
        support = support.reshape(rows+1, columns+1)

        x_mass, x_moment = _hat_integrals(columns, left, right)
        y_mass, _ = _hat_integrals(rows, bottom, top)
        exact_support = np.outer(y_mass, x_mass)
        exact_pressure = np.zeros_like(pressure)
        supported = exact_support > 1.0e-15
        mean_x = np.zeros_like(x_mass)
        x_positive = x_mass > 1.0e-15
        mean_x[x_positive] = x_moment[x_positive] / x_mass[x_positive]
        exact_pressure[supported] = stiffness*slope*np.maximum(
            midpoint - np.broadcast_to(mean_x, exact_pressure.shape)[supported],
            0.0,
        )
        squared_error = _field_squared_error(
            pressure, left, right, bottom, top, midpoint, stiffness, slope,
        )
        results.append({
            "source_divisions": columns,
            "source_rows": rows,
            "exact_supported_modes": int(np.count_nonzero(supported)),
            "reported_supported_modes": int(record["supported_pressure_modes"]),
            "max_absolute_support_error_m2": float(np.max(np.abs(
                support - exact_support))),
            "max_absolute_nodal_pressure_error_pa": float(np.max(np.abs(
                pressure - exact_pressure))),
            "relative_continuous_pressure_l2_error": float(np.sqrt(
                squared_error / reference_squared)),
            "reported_integrated_force_n": float(record["reaction_z_n"]),
            "analytic_integrated_force_n": float(
                stiffness*slope*(top-bottom)*(midpoint-left)**2/2.0),
        })
    return {
        "purpose": "development fixed-pose contact-front pressure comparison",
        "source_report": str(path),
        "reference": "analytic local-plane Q1 support/affine-gap projection and continuous positive-part pressure",
        "continuum_reference_l2_pa_m": float(np.sqrt(reference_squared)),
        "rows": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = analyze(args.report)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
