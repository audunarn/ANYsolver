"""Bounded producer for the saved F03 trace-port evidence."""
from __future__ import annotations

from bisect import bisect_right

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_scientific_port_storage as storage
from scripts import _b3_e4_f03_sparse_trace_binding as trace


def _owned_vector(value: object, size: int) -> np.ndarray:
    if (
        type(value) is not np.ndarray
        or value.dtype != np.dtype(np.float64)
        or value.shape != (size,)
        or not value.flags.c_contiguous
        or not np.isfinite(value).all()
    ):
        raise ValueError("finite contiguous binary64 F03 physical state required")
    return np.frombuffer(value.tobytes(order="C"), dtype=np.float64)


def _preflight(
    grid: topology.CompiledGrid,
    budget: trace.TraceBindingBudget,
) -> None:
    if not isinstance(grid, topology.CompiledGrid) or type(budget) is not trace.TraceBindingBudget:
        raise ValueError("validated F03 grid and trace budget required")
    active = max((len(value) for value in grid.trace_incidence), default=0)
    input_nnz = len(trace.KEYS) * 3 * active
    workspace = input_nnz * (8 + 8 + 8) + len(trace.KEYS) * 3 * 8
    if (
        grid.free_dofs > budget.sparse_budget.max_order
        or input_nnz > budget.max_input_nnz
        or workspace > budget.max_work_bytes
    ):
        raise ValueError("F03 trace-port production exceeds declared resource budget")


def produce_port_evidence(
    grid: topology.CompiledGrid,
    q: np.ndarray,
    *,
    budget: trace.TraceBindingBudget,
) -> storage.PortEvidence:
    """Produce the ordered 27 ports without assembly, factorization, or solve."""
    _preflight(grid, budget)
    state = _owned_vector(q, grid.free_dofs)
    intervals = {}
    samples = []
    for station, order, side in trace.KEYS:
        index = min(
            bisect_right(grid.station_cuts, station) - 1,
            len(grid.station_cuts) - 2,
        )
        if side == "left" and index > 0 and station == grid.station_cuts[index]:
            index -= 1
        if index not in intervals:
            intervals[index] = assembly.trace_interval(
                grid, index, budget.trace_budget,
            )
        local = intervals[index]
        tau = (station - local.left) / (local.right - local.left)
        exact = local.evaluate_exact(tau, order)
        values = np.asarray(exact, dtype=np.float64)
        if values.shape != (3, len(local.indices)) or not np.isfinite(values).all():
            raise ArithmeticError("invalid F03 exact trace-port conversion")
        operator = sparse.coo_matrix(
            (
                values.ravel(),
                (
                    np.repeat(np.arange(3), len(local.indices)),
                    np.tile(local.indices, 3),
                ),
            ),
            shape=(3, grid.free_dofs),
            dtype=np.float64,
        ).tocsr()
        operator.eliminate_zeros()
        operator.sort_indices()
        action = np.ascontiguousarray(operator @ state, dtype=np.float64)
        if action.shape != (3,) or not np.isfinite(action).all():
            raise ArithmeticError("nonfinite F03 trace-port action")
        samples.append(trace.SavedPort(
            station, order, side, operator.copy(),
            np.frombuffer(action.tobytes(order="C"), dtype=np.float64),
        ))
    values = tuple(samples)
    if len(values) != len(trace.KEYS):
        raise ArithmeticError("incomplete F03 trace-port inventory")
    return storage.PortEvidence(
        values,
        values[0].operator.copy(),
        values[8].operator.copy(),
        values[9].operator[1:2].copy(),
    )
