"""Separate cell-polynomial full-wrench check for failed nested-x bands."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0, SECTION, YAW_LENGTH
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle


BANDS = ((.25, .5, 1), (.5, .75, 2), (1 / 32, 1 / 16, 5))
SCALE = np.array((F0, F0, F0 * YAW_LENGTH))


def _density(oracle, coefficients, station):
    pose, first, second = oracle.evaluate(coefficients, float(station))
    ea, ei, ga = np.diag(SECTION)
    shear = ga * (first[1] - pose[2])
    return np.array((ea * second[0],
        ga * (second[1] - first[2]) +
        F0 * (1 + .25 * math.cos(2 * math.pi * station)),
        ei * second[2] + shear))


def _band(oracle, coefficients, trace, left, right, order):
    roots, weights = np.polynomial.legendre.leggauss(order)
    parts = sorted(set((left, right)).union(
        event for event in trace.station_breakpoints() if left < event < right))
    mean_x = sum(x for x, _ in trace.offsets) / len(trace.offsets)
    mean_y = sum(y for _, y in trace.offsets) / len(trace.offsets)
    geometric_j = sum(x*x + y*y + 2*trace.a**2/3 for x, y in
                      trace.offsets) / len(trace.offsets)
    gamma = geometric_j / trace.j
    total = np.zeros(3)
    for a, b in zip(parts, parts[1:]):
        if not a < b:
            raise ArithmeticError("nonpositive reference subinterval")
        stations = (a + b) / 2 + (b - a) * roots / 2
        density = np.array([_density(oracle, coefficients, s)
                            for s in stations])
        w = weights * (b - a) / 2
        total += np.array((w @ density[:, 0], w @ density[:, 1],
            w @ (stations * density[:, 1] + mean_x * density[:, 1] -
                 mean_y * density[:, 0] + gamma * density[:, 2])))
    return total


def run(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    p = record["degree"]
    trace = FinitePadQpTrace(p, x=record["x"], y=record["y"])
    q = np.zeros(2 * trace.n)
    q[trace.free_columns] = record["free_state"]
    oracle = PiecewisePadMomentOracle(p, x=trace.x, y=trace.y,
        offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
    coefficients = oracle.coefficients(q)
    rows = {}
    for left, right, index in BANDS:
        low = _band(oracle, coefficients, trace, left, right, 48)
        high = _band(oracle, coefficients, trace, left, right, 64)
        adjoint = np.array(record["signed"]["bands"][index])
        rows[f"{left:.8f}-{right:.8f}"] = {
            "piecewise_48": low.tolist(),
            "piecewise_64": high.tolist(),
            "adjoint": adjoint.tolist(),
            "max_48_64_scaled": float(np.max(np.abs(low-high)/SCALE)),
            "max_adjoint_64_scaled": float(np.max(np.abs(adjoint-high)/SCALE)),
        }
    return str(p), rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("q4", type=Path)
    parser.add_argument("q5", type=Path)
    parser.add_argument("q6", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = {"status": "UNREGISTERED_INDEPENDENT_BAND_CHECK",
              "cases": dict(run(path) for path in (args.q4, args.q5, args.q6))}
    args.output.write_text(json.dumps(result, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({p: {name: row["max_adjoint_64_scaled"]
                          for name, row in bands.items()}
                      for p, bands in result["cases"].items()}))


if __name__ == "__main__":
    main()
