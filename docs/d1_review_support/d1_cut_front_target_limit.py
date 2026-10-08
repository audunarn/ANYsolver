"""Independent exact-polynomial quadrature for the flat two-S3 rim limit.

No ANYsolver contact routines are used. The 3-point x and 2-point y Gauss
rules are exact for the piecewise polynomials after splitting at Q1 knots
and the S3 diagonal. The limiting pressure measure includes a rim delta.
"""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path


X_LEFT = -0.113
X_RIGHT = 2.127
Y_BOTTOM = -0.087
Y_TOP = 1.0
X_GAUSS = ((-sqrt(3.0/5.0), 5.0/9.0),
           (0.0, 8.0/9.0), (sqrt(3.0/5.0), 5.0/9.0))
Y_GAUSS = ((-1.0/sqrt(3.0), 1.0), (1.0/sqrt(3.0), 1.0))


def target_shape(x, y):
    xi = (x-X_LEFT)/(X_RIGHT-X_LEFT)
    eta = (y-Y_BOTTOM)/(Y_TOP-Y_BOTTOM)
    if xi+eta <= 1.0:
        return xi, 0.0  # free br and tr nodes, lower triangle
    return 1.0-eta, xi+eta-1.0  # upper triangle


def x_hat(x):
    return (x-0.5)/0.5 if x <= 1.0 else (1.5-x)/0.5


def main():
    bulk = [0.0, 0.0]
    delta = [0.0, 0.0]
    for xa, xb in ((0.5, 1.0), (1.0, 1.5)):
        for xg, wx in X_GAUSS:
            x = (xa+xb)/2+(xb-xa)*xg/2
            x_weight = (xb-xa)*wx/2*x_hat(x)
            diagonal = Y_TOP-(Y_TOP-Y_BOTTOM)*(
                x-X_LEFT)/(X_RIGHT-X_LEFT)
            if not 0.0 < diagonal < 1.0:
                raise AssertionError("the S3 diagonal left the analytic split")
            for ya, yb in ((0.0, diagonal), (diagonal, 1.0)):
                for yg, wy in Y_GAUSS:
                    y = (ya+yb)/2+(yb-ya)*yg/2
                    shape = target_shape(x, y)
                    for i in range(2):
                        bulk[i] += x_weight*(yb-ya)*wy/2*(1-3*y)*shape[i]
            shape_at_rim = target_shape(x, 1.0)
            for i in range(2):
                delta[i] += x_weight*shape_at_rim[i]/2
    result = {
        "status": "independent_flat_target_limit",
        "target_free_node_ids": [17, 18],
        "bulk_limit": bulk,
        "rim_delta_limit": delta,
        "total_limit": [a+b for a, b in zip(bulk, delta)],
        "l2_limit": sqrt(sum((a+b)**2 for a, b in zip(bulk, delta))),
        "quadrature": "3-point x by 2-point y, split at x-hat knot and S3 diagonal",
    }
    output = Path(__file__).with_name(
        "d1_cut_front_target_limit_20260929.json")
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
