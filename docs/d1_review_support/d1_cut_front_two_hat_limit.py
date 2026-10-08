"""Independent exact-polynomial target limit for two source x hats.

The 2-S3 target has two free normal nodes, but their leading work rows are
opposites for the corrected cut-row y pressure. This yields one signed
two-hat combination with zero leading target work. No ANYsolver contact
routines are used.
"""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path

import numpy as np


X_LEFT = -0.113
X_RIGHT = 2.127
Y_BOTTOM = -0.087
Y_TOP = 1.0
CENTERS = (1.0, 1.5)
X_GAUSS = ((-sqrt(3.0/5.0), 5.0/9.0),
           (0.0, 8.0/9.0), (sqrt(3.0/5.0), 5.0/9.0))
Y_GAUSS = ((-1.0/sqrt(3.0), 1.0), (1.0/sqrt(3.0), 1.0))


def shape(x, y):
    xi = (x-X_LEFT)/(X_RIGHT-X_LEFT)
    eta = (y-Y_BOTTOM)/(Y_TOP-Y_BOTTOM)
    if xi+eta <= 1.0:
        return np.asarray((xi, 0.0))
    return np.asarray((1.0-eta, xi+eta-1.0))


def x_hats(x):
    return np.asarray([max(0.0, 1.0-abs(x-c)/0.5) for c in CENTERS])


def limit_matrix():
    bulk = np.zeros((2, 2))
    rim = np.zeros((2, 2))
    crossing = X_LEFT+(X_RIGHT-X_LEFT)*Y_TOP/(Y_TOP-Y_BOTTOM)
    if not 1.5 < crossing < 2.0:
        raise AssertionError("unexpected diagonal crossing at the lower rim")
    for xa, xb in ((0.5, 1.0), (1.0, 1.5),
                   (1.5, crossing), (crossing, 2.0)):
        for xg, wx in X_GAUSS:
            x = (xa+xb)/2+(xb-xa)*xg/2
            x_weights = (xb-xa)*wx/2*x_hats(x)
            diagonal = Y_TOP-(Y_TOP-Y_BOTTOM)*(
                x-X_LEFT)/(X_RIGHT-X_LEFT)
            if diagonal >= 1.0:
                raise AssertionError("S3 diagonal reached the upper rim")
            y_intervals = (((0.0, diagonal), (diagonal, 1.0))
                           if diagonal > 0.0 else ((0.0, 1.0),))
            for ya, yb in y_intervals:
                for yg, wy in Y_GAUSS:
                    y = (ya+yb)/2+(yb-ya)*yg/2
                    bulk += np.outer(shape(x, y), x_weights)*(
                        (yb-ya)*wy/2*(1.0-3.0*y))
            rim += np.outer(shape(x, 1.0), x_weights)/2
    return bulk, rim


def null_coefficients(matrix):
    row = matrix[0]
    coefficients = np.asarray((row[1], -row[0]))
    coefficients /= np.linalg.norm(coefficients)
    if coefficients[0] < 0.0:
        coefficients = -coefficients
    return coefficients


def finite_target_work(theta, coefficients):
    """Integrate the same pressure against the two free S3 normal tests."""
    if not 0.0 < theta <= 0.1:
        raise ValueError("bounded cut fraction required")
    b = theta**2/2-theta**3/3
    d = 0.25+theta-theta**2+theta**3/3
    beta = -b/d
    alpha = -beta/2
    upper = 1.0+theta
    result = np.zeros(2)
    crossing = X_LEFT+(X_RIGHT-X_LEFT)*upper/(upper-Y_BOTTOM)
    if not 1.5 < crossing < 2.0:
        raise AssertionError("unexpected finite-cut diagonal crossing")
    for xa, xb in ((0.5, 1.0), (1.0, 1.5),
                   (1.5, crossing), (crossing, 2.0)):
        for xg, wx in X_GAUSS:
            x = (xa+xb)/2+(xb-xa)*xg/2
            x_weight = (xb-xa)*wx/2*float(x_hats(x)@coefficients)
            xi = (x-X_LEFT)/(X_RIGHT-X_LEFT)
            diagonal = upper-(upper-Y_BOTTOM)*xi
            if diagonal >= 1.0:
                raise AssertionError("S3 diagonal reached the upper rim")
            y_intervals = (((0.0, diagonal), (diagonal, 1.0))
                           if diagonal > 0.0 else ((0.0, 1.0),))
            for ya, yb in (*y_intervals, (1.0, upper)):
                for yg, wy in Y_GAUSS:
                    y = (ya+yb)/2+(yb-ya)*yg/2
                    eta = (y-Y_BOTTOM)/(upper-Y_BOTTOM)
                    if xi+eta <= 1.0:
                        test = np.asarray((xi, 0.0))
                    else:
                        test = np.asarray((1.0-eta, xi+eta-1.0))
                    pressure_y = ((alpha*(1-y)+beta*y) if y <= 1.0
                                  else beta*(2-y)+(y-1))
                    result += x_weight*(yb-ya)*wy/2*pressure_y*test
    return result


def main():
    bulk, rim = limit_matrix()
    full = bulk+rim
    coefficients = null_coefficients(full)
    residual = full@coefficients
    if np.linalg.norm(residual) > 1.0e-14:
        raise AssertionError("target-limit null was not resolved")
    finite = {}
    for theta in (0.1, 0.05, 0.025):
        force = finite_target_work(theta, coefficients)
        finite[str(theta)] = {
            "target_shape_work": force.tolist(),
            "normal_gap_gradient_work": (-force).tolist(),
            "free_norm": float(np.linalg.norm(force)),
            "free_norm_over_theta_cubed":
                float(np.linalg.norm(force)/theta**3),
        }
    output = Path(__file__).with_name(
        "d1_cut_front_two_hat_limit_v3_20260929.json")
    if output.exists():
        raise FileExistsError(output)
    result = {
        "status": "independent_two_hat_target_limit",
        "source_x_hat_centers": CENTERS,
        "target_free_node_order": "bottom_right_then_top_right",
        "bulk_matrix": bulk.tolist(),
        "rim_delta_matrix": rim.tolist(),
        "full_limit_matrix": full.tolist(),
        "unit_l2_null_coefficients": coefficients.tolist(),
        "null_residual_l2": float(np.linalg.norm(residual)),
        "limit_singular_values": np.linalg.svd(full,
                                               compute_uv=False).tolist(),
        "finite_cut_exact_polynomial_work": finite,
        "quadrature": "3-point x by 2-point y, split at Q1 knots and S3 diagonal",
    }
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"coefficients": result["unit_l2_null_coefficients"],
                      "null_residual_l2": result["null_residual_l2"],
                      "singular_values": result["limit_singular_values"]}))


if __name__ == "__main__":
    main()
