"""Predeclared, unregistered F03 classical Qp nested-x diagnostic.

Run one degree per process. This does not confer a qualification status.
The physical grid rule and complete holdout are documented in
docs/agent_plans/B3_GE_E4_PL_G0_F03_QP_NESTED_X_PILOT_20260923.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from scripts._b3_e4_f03_conforming_qp_energy import assemble, solve
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_precise_functional import from_qp_recovery_precise
from scripts._b3_e4_f03_qp_piecewise_functional import norm_squared


BANDS = tuple((i / 4, (i + 1) / 4) for i in range(4)) + (
    (0., 1 / 32), (1 / 32, 1 / 16),
    (15 / 16, 31 / 32), (31 / 32, 1.),
)


def refined_x() -> tuple[float, ...]:
    """Exactly bisect original cells wider than a beam quarter."""
    original = FinitePadQpTrace(1).x
    midpoints = ((left + right) / 2 for left, right in
                 zip(original, original[1:]) if right - left > .25)
    return tuple(sorted(set(original).union(midpoints)))


def refined_x2() -> tuple[float, ...]:
    """Bisect the remaining quarter-length X1 cells without rounding X0."""
    first = refined_x()
    midpoints = ((left + right) / 2 for left, right in
                 zip(first, first[1:]) if right - left >= .25)
    return tuple(sorted(set(first).union(midpoints)))


def run(degree: int, grid: str = "x1", *, candidate_state=None) -> dict:
    if degree not in (4, 5, 6):
        raise ValueError("pilot degree must be Q4, Q5 or Q6")
    if grid not in ("x0", "x1", "x2") or (grid in ("x0", "x2") and degree != 6):
        raise ValueError("X0 and X2 pilots require fixed Q6")
    x = None if grid == "x0" else refined_x() if grid == "x1" else refined_x2()
    trace = FinitePadQpTrace(degree, x=x)
    expected = {"x0": (10, 11), "x1": (13, 17), "x2": (17, 25)}[grid]
    if (len(trace.x), len(trace.station_intervals())) != expected:
        raise ArithmeticError("predeclared pilot grid or crossing count changed")
    elapsed = {}
    start = perf_counter()
    operators = assemble(trace)
    elapsed["assembly_s"] = perf_counter() - start
    start = perf_counter()
    free_q, eta, result = solve(operators, candidate_state=candidate_state)
    elapsed["solve_s"] = perf_counter() - start
    q = np.zeros(2 * trace.n)
    q[operators.free_columns] = free_q
    start = perf_counter()
    adjoint = FinitePadAreaAdjoint(trace, q, eta)
    endpoint = adjoint.atoms
    signed = {
        "tip_pose": result["tip_pose"].tolist(),
        "shell_energy_j": result["shell_energy_j"],
        "beam_energy_j": result["beam_energy_j"],
        "total_energy_j": result["shell_energy_j"] + result["beam_energy_j"],
        "external_work_j": result["external_work_j"],
        "eta": eta.tolist(),
        "root_section": (endpoint[0] + eta).tolist(),
        "tip_section": (-endpoint[1]).tolist(),
        "root_atom": endpoint[0].tolist(),
        "tip_atom": endpoint[1].tolist(),
        "line_wrench": adjoint.line_wrench().tolist(),
        "bands": [adjoint.band_wrench(a, b).tolist() for a, b in BANDS],
    }
    elapsed["signed_recovery_s"] = perf_counter() - start
    start = perf_counter()
    precise = from_qp_recovery_precise(trace, q, eta)
    norm = norm_squared(precise.functional)
    elapsed["functional_s"] = perf_counter() - start
    return {
        "status": {"x0": "UNREGISTERED_NESTED_X0_PILOT",
                   "x1": "UNREGISTERED_NESTED_X_PILOT",
                   "x2": "UNREGISTERED_NESTED_X2_PILOT"}[grid],
        "grid": grid,
        "degree": degree,
        "x": trace.x,
        "x_hex": [coordinate.hex() for coordinate in trace.x],
        "y": trace.y,
        "y_hex": [coordinate.hex() for coordinate in trace.y],
        "station_intervals": trace.station_intervals(),
        "dof_count": operators.dof_count,
        "physical_coordinates": 2 * trace.n,
        "free_state_sha256": hashlib.sha256(free_q.tobytes()).hexdigest(),
        "free_state": free_q.tolist(),
        "root_multiplier": eta.tolist(),
        "signed": signed,
        "functional": {
            "breaks": precise.functional.breaks.tolist(),
            "coefficients": precise.functional.coefficients.tolist(),
            "cosine": precise.functional.cosine.tolist(),
            "atoms": precise.functional.atoms.tolist(),
        },
        "functional_norm_n": float(np.sqrt(norm.squared_total)),
        "functional_squared_channels": norm.squared_channels.tolist(),
        "numerical": {
            "beam_discrepancy_relative": operators.beam_discrepancy_relative,
            "load_discrepancy_scaled": operators.load_discrepancy_scaled,
            "root_compatibility_scaled": result["root_compatibility_scaled"],
            "equilibrium_scaled": result["equilibrium_scaled"],
            "work_identity_scaled": result["work_identity_scaled"],
            "root_singular_values": result["root_singular_values"].tolist(),
            "root_pose_derivative_singular_values":
                result["root_pose_derivative_singular_values"].tolist(),
            "scaled_shell_min_eigenvalue": result["scaled_shell_min_eigenvalue"],
            "shell_nnz": result["shell_nnz"],
            "beam_nnz": result["beam_nnz"],
            "fallback_indices": precise.base.fallback_indices,
            "max_precision_defect": precise.max_precision_defect,
            "max_nodal_defect": precise.max_nodal_defect,
            "max_held_defect": precise.max_held_defect,
            "exact_interior_crossings": precise.exact_interior_crossings,
            "max_boundary_crossing_shift":
                precise.max_boundary_crossing_shift,
            "max_endpoint_defect": precise.max_endpoint_defect,
            "density_order_discrepancy":
                norm.density_order_discrepancy.tolist(),
            "cross_order_discrepancy":
                norm.cross_order_discrepancy.tolist(),
        },
        "elapsed": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("degree", type=int, choices=(4, 5, 6))
    parser.add_argument("output", type=Path)
    parser.add_argument("--grid", choices=("x0", "x1", "x2"), default="x1")
    arguments = parser.parse_args()
    record = run(arguments.degree, arguments.grid)
    arguments.output.write_text(json.dumps(record, indent=2) + "\n",
                                encoding="utf-8")
    print(json.dumps({"degree": arguments.degree,
                      "free": record["dof_count"],
                      "norm_n": record["functional_norm_n"],
                      "elapsed": record["elapsed"]}))


if __name__ == "__main__":
    main()
