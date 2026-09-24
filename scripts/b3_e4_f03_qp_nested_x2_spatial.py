"""Preparatory Q6 X0/X1/X2 area, nodal and signed spatial work audit.

This consumes a saved unregistered Q6 state. It is not a scientific gate,
and its source-level timing is not installed-artifact qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import threading
from time import perf_counter

import numpy as np
import psutil

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_conforming_qp_energy import QpOperators
from scripts._b3_e4_f03_primal_ritz import E0, F0, YAW_LENGTH
from scripts._b3_e4_f03_qp_precise_functional import from_qp_recovery_precise
from scripts._b3_e4_f03_qp_precise_line_adjoint import PreciseLineAreaAdjoint
from scripts._b3_e4_f03_qp_nodal_recovery import (
    distributed_support_liftings, recover_nodal, support_liftings,
)
from scripts._b3_e4_f03_qp_spatial_recovery import SpatialQpRecovery
from scripts.b3_e4_f03_qp_nested_x_pilot import refined_x, refined_x2


def _sample_memory(stop, maximum):
    process = psutil.Process()
    while not stop.is_set():
        maximum[0] = max(maximum[0], process.memory_info().rss)
        stop.wait(.25)
    maximum[0] = max(maximum[0], process.memory_info().rss)


def run(path, *, operators: QpOperators | None = None):
    source_bytes = Path(path).read_bytes()
    row = json.loads(source_bytes)
    grid = row.get("grid")
    if grid not in ("x0", "x1", "x2"):
        raise ValueError("unsupported fixed-Q6 spatial grid")
    x = None if grid == "x0" else refined_x() if grid == "x1" else refined_x2()
    trace = FinitePadQpTrace(6, x=x)
    if operators is not None:
        if not isinstance(operators, QpOperators):
            raise ValueError("shared Q6 shell operator required")
        owned = operators.trace
        if (owned.p != trace.p or owned.x != trace.x or
                owned.y != trace.y or owned.offsets != trace.offsets or
                owned.a != trace.a or owned.j != trace.j or
                not np.array_equal(operators.free_columns,
                                   trace.free_columns)):
            raise ValueError("shared Q6 shell operator does not match spatial trace")
        trace = owned
    statuses = {"x0": "UNREGISTERED_NESTED_X0_PILOT",
                "x1": "UNREGISTERED_NESTED_X_PILOT",
                "x2": "UNREGISTERED_NESTED_X2_PILOT"}
    counts = {"x0": (3286, 3410), "x1": (4402, 4526),
              "x2": (5890, 6014)}
    if (row["status"] != statuses[grid] or
            row["degree"] != 6 or
            row["x_hex"] != [x.hex() for x in trace.x] or
            row["y_hex"] != [y.hex() for y in trace.y] or
            (row["dof_count"], row["physical_coordinates"]) != counts[grid]):
        raise ValueError("incompatible fixed-Q6 state")
    q = np.zeros(2*trace.n)
    q[trace.free_columns] = row["free_state"]
    eta = np.array(row["root_multiplier"])
    start_prepare = perf_counter()
    functional = from_qp_recovery_precise(trace, q, eta).functional
    adjoint = PreciseLineAreaAdjoint(trace, q, eta, functional)
    print(f"prepared coefficient-space line integrals in {perf_counter()-start_prepare:.3f} s", flush=True)
    stop = threading.Event()
    maximum = [psutil.Process().memory_info().rss]
    sampler = threading.Thread(target=_sample_memory,
        args=(stop, maximum), daemon=True)
    sampler.start()
    try:
        elapsed = {}
        start = perf_counter()
        nodal = recover_nodal(
            adjoint, free_shell_stiffness=(None if operators is None else
                                           operators.shell_stiffness))
        elapsed["nodal_recovery_s"] = perf_counter()-start
        print(f"nodal recovery: {elapsed['nodal_recovery_s']:.3f} s", flush=True)
        start = perf_counter()
        spatial = SpatialQpRecovery(adjoint)
        elapsed["area_11_13_and_spatial_setup_s"] = perf_counter()-start
        print(f"area 11/13 comparison: {elapsed['area_11_13_and_spatial_setup_s']:.3f} s", flush=True)
        start = perf_counter()
        lifts = support_liftings(trace)
        distributed = distributed_support_liftings(trace)
        works = [[spatial.work(z) for z in group] for group in
                 (lifts, distributed)]
        elapsed["twelve_spatial_works_s"] = perf_counter()-start
        print(f"twelve spatial works: {elapsed['twelve_spatial_works_s']:.3f} s", flush=True)
        residual = nodal.shell_nodal_force-nodal.area_nodal_load
        scale = max(F0, float(np.max(np.abs(nodal.line_nodal_load))))
        wrench_scale = np.array((F0, F0, F0*YAW_LENGTH))
        numerical = {
            "area_line_nodal_gap_scaled": float(np.max(np.abs(
                nodal.area_nodal_load-nodal.line_nodal_load))/scale),
            "free_equilibrium_scaled": float(np.max(np.abs(
                nodal.free_residual))/scale),
            "area_line_wrench_gap_scaled": float(np.max(np.abs(
                nodal.area_wrench-nodal.line_wrench)/wrench_scale)),
            "area_order_discrepancy": spatial.area_order_error,
            "lifting_invariance_scaled": float(np.max(np.abs(
                (distributed-lifts)@residual)/np.tile(wrench_scale, 2))),
            "global_shell_balance_scaled": float(np.max(np.abs(
                nodal.support_wrenches[:3]+nodal.support_wrenches[3:]+
                nodal.line_wrench)/wrench_scale)),
            "beam_root_reaction_defect_scaled": float(np.max(np.abs(
                nodal.beam_root_reaction+eta)/wrench_scale)),
            "maximum_spatial_work_defect_scaled": float(max(
                abs(work.reaction-residual@z)/max(E0, abs(work.reaction),
                    abs(residual@z))
                for group, fields in zip((lifts, distributed), works)
                for z, work in zip(group, fields))),
        }
        if (numerical["area_line_nodal_gap_scaled"] > 2e-10 or
                numerical["free_equilibrium_scaled"] > 2e-9 or
                numerical["area_line_wrench_gap_scaled"] > 2e-9 or
                numerical["area_order_discrepancy"] > 2e-10 or
                numerical["lifting_invariance_scaled"] > 2e-9 or
                numerical["global_shell_balance_scaled"] > 2e-9 or
                numerical["beam_root_reaction_defect_scaled"] > 2e-9 or
                numerical["maximum_spatial_work_defect_scaled"] > 2e-9):
            raise ArithmeticError("Q6 spatial or physical balance check failed")
    finally:
        stop.set()
        sampler.join(timeout=2.)
    return {"status": "UNREGISTERED_Q6_SPATIAL_AUDIT",
            "grid": grid,
            "input_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "numerical": numerical,
            "elapsed": elapsed,
            "sampled_peak_rss_bytes": maximum[0],
            "support_wrenches": nodal.support_wrenches.tolist(),
            "area_wrench": nodal.area_wrench.tolist(),
            "line_wrench": nodal.line_wrench.tolist(),
            "beam_root_reaction": nodal.beam_root_reaction.tolist(),
            "spatial_work": [[{
                "cell": work.cell, "support": work.support,
                "free": work.free, "interior": work.interior,
                "total": work.total, "reaction": work.reaction,
            } for work in group] for group in works],
            "qualification_status": "F03_G0B_OPEN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.state)
    args.output.write_text(json.dumps(result, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"numerical": result["numerical"],
                      "elapsed": result["elapsed"],
                      "sampled_peak_rss_bytes":
                          result["sampled_peak_rss_bytes"]}))


if __name__ == "__main__":
    main()
