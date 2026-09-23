"""Preparatory Q1 classical-reference energy and bounded equilibrium candidate.

This is an unregistered finite-pad reference calculation, not F03 evidence or
the native shell/beam interface.  All essential values are eliminated at the
two supported x edges; the only beam conditions are the three pose rows.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import sparse
from scipy.sparse.linalg import MatrixRankWarning, spsolve

from scripts._b3_e4_f03_conforming_q1_trace import FinitePadQ1Trace
from scripts._b3_e4_f03_primal_ritz import (
    E0, F0, PLANE, SECTION, THICKNESS, U0, YAW_LENGTH,
)


@dataclass(frozen=True)
class Q1Operators:
    trace: FinitePadQ1Trace
    free_columns: np.ndarray
    shell_stiffness: sparse.csr_matrix
    beam_stiffness: sparse.csr_matrix
    load: np.ndarray
    root_constraint: np.ndarray
    tip_pose: np.ndarray
    load_discrepancy_scaled: float
    beam_discrepancy_relative: float
    station_intervals: int

    @property
    def dof_count(self) -> int:
        return len(self.free_columns)


def _station_rule(left: float, right: float, order: int):
    if not left < right:
        raise ValueError("nonpositive represented station interval")
    roots, weights = leggauss(order)
    # Distinct represented crossing events can be only one ulp apart.  There
    # is then no binary64 interior point for a Gauss node.  A and A' are
    # continuous at those events: retain the interval's full physical weight
    # and evaluate its limiting value at the representable midpoint.
    if np.nextafter(left, right) >= right:
        return (np.full(order, (left+right)/2), (right-left)*weights/2)
    return (left + (right-left)*(roots+1)/2,
            (right-left)*weights/2)


def _shell(trace: FinitePadQ1Trace, free: np.ndarray) -> sparse.csr_matrix:
    """Scatter exact Q1 cell strain products without a global dense matrix."""
    inverse = np.full(2*trace.n, -1, dtype=int)
    inverse[free] = np.arange(len(free))
    roots, weights = leggauss(2)
    rows, columns, values = [], [], []
    ny = len(trace.y)
    for i, (xl, xr) in enumerate(zip(trace.x, trace.x[1:])):
        hx = xr-xl
        for k, (yl, yr) in enumerate(zip(trace.y, trace.y[1:])):
            hy = yr-yl
            nodes = np.array((i*ny+k, (i+1)*ny+k,
                              i*ny+k+1, (i+1)*ny+k+1))
            local = np.r_[nodes, trace.n+nodes]
            stiffness = np.zeros((8, 8))
            for gx, wx in zip(roots, weights):
                tx = (gx+1)/2
                for gy, wy in zip(roots, weights):
                    ty = (gy+1)/2
                    dx = np.array((-(1-ty), 1-ty, -ty, ty))/hx
                    dy = np.array((-(1-tx), -tx, 1-tx, tx))/hy
                    b = np.zeros((3, 8))
                    b[0, :4], b[1, 4:] = dx, dy
                    b[2, :4], b[2, 4:] = dy, dx
                    stiffness += (wx*wy*hx*hy*THICKNESS/4)*b.T@PLANE@b
            for a, global_a in enumerate(local):
                ra = inverse[global_a]
                if ra < 0:
                    continue
                for b, global_b in enumerate(local):
                    cb = inverse[global_b]
                    if cb >= 0:
                        rows.append(ra)
                        columns.append(cb)
                        values.append(stiffness[a, b])
    shape = (len(free), len(free))
    return sparse.coo_matrix((values, (rows, columns)), shape=shape).tocsr()


def _beam_and_load(trace: FinitePadQ1Trace, free: np.ndarray,
                   beam_order: int, load_order: int):
    rows, columns, values = [], [], []
    load = np.zeros(len(free))
    for left, right in zip(trace.station_breakpoints(),
                           trace.station_breakpoints()[1:]):
        if right <= left:
            raise ValueError("nonpositive station interval")
        stations, weights = _station_rule(left, right, beam_order)
        for s, weight in zip(stations, weights):
            pose, derivative, _ = trace.matrices(float(s))
            pose, derivative = pose[:, free], derivative[:, free]
            strain = np.stack((derivative[0], derivative[2],
                               derivative[1]-pose[2]))
            active = np.flatnonzero(np.any(strain != 0, axis=0))
            local = weight*strain[:, active].T@SECTION@strain[:, active]
            rr, cc = np.meshgrid(active, active, indexing="ij")
            rows.extend(rr.ravel())
            columns.extend(cc.ravel())
            values.extend(local.ravel())
        stations, weights = _station_rule(left, right, load_order)
        for s, weight in zip(stations, weights):
            pose = trace.matrices(float(s))[0]
            load += weight*F0*(1+.25*math.cos(2*math.pi*s))*pose[1, free]
    matrix = sparse.coo_matrix((values, (rows, columns)),
                               shape=(len(free), len(free))).tocsr()
    return matrix, load


def assemble(trace: FinitePadQ1Trace | None = None, *,
             beam_order: int = 4, load_order: int = 48,
             compare_quadrature: bool = True) -> Q1Operators:
    """Assemble mapped Q1 energies and the smooth load interval by interval.

    Four points integrate Q1 beam energy exactly on each fixed-incidence
    interval.  Six points and the prescribed 48/64 load pair check that
    independently; neither discrepancy is an acceptance threshold.
    """
    if beam_order not in (4, 6) or load_order not in (48, 64):
        raise ValueError("unsupported bounded Q1 quadrature")
    trace = FinitePadQ1Trace() if trace is None else trace
    free = trace.free_columns
    shell = _shell(trace, free)
    beam, load = _beam_and_load(trace, free, beam_order, load_order)
    beam_difference = load_difference = float("nan")
    if compare_quadrature:
        comparison_beam, comparison_load = _beam_and_load(
            trace, free, 6 if beam_order == 4 else 4,
            64 if load_order == 48 else 48)
        beam_difference = float(sparse.linalg.norm(beam-comparison_beam) /
                                max(sparse.linalg.norm(beam),
                                    sparse.linalg.norm(comparison_beam)))
        load_difference = float(np.max(np.abs(load-comparison_load))/F0)
    root = trace.matrices(0.)[0][:, free]
    tip = trace.matrices(1., side="left")[0][:, free]
    if (not np.isfinite(shell.data).all() or
            not np.isfinite(beam.data).all() or
            not np.isfinite(load).all() or
            not np.isfinite(root).all() or not np.isfinite(tip).all()):
        raise ValueError("nonfinite Q1 reference operator")
    return Q1Operators(trace, free, shell, beam, load, root, tip,
                       load_difference, beam_difference,
                       len(trace.station_breakpoints())-1)


def scaled_root_singular_values(operators: Q1Operators) -> np.ndarray:
    """Dimensionless rank witness for the physical root rows."""
    diagonal = (operators.shell_stiffness+operators.beam_stiffness).diagonal()
    if np.any(diagonal <= 0):
        raise ValueError("nonpositive Q1 energy diagonal")
    displacement_scale = np.sqrt(E0/diagonal)
    root_scale = np.array((1/U0, 1/U0, YAW_LENGTH/U0))
    return np.linalg.svd(root_scale[:, None]*operators.root_constraint*
                         displacement_scale[None, :], compute_uv=False)


def solve(operators: Q1Operators):
    """One bounded candidate solve; caller must not interpret it as convergence."""
    stiffness = operators.shell_stiffness+operators.beam_stiffness
    diagonal = stiffness.diagonal()
    if np.any(diagonal <= 0) or not np.isfinite(diagonal).all():
        raise ValueError("nonpositive Q1 energy diagonal")
    d = np.sqrt(E0/diagonal)
    root_scale = np.diag((1/U0, 1/U0, YAW_LENGTH/U0))
    singulars = scaled_root_singular_values(operators)
    if singulars[-1] <= 1.e-10*singulars[0]:
        raise ValueError("Q1 root rows lack three independent conditions")
    scaled_stiffness = sparse.diags(d)@stiffness@sparse.diags(d)/E0
    scaled_root = root_scale@operators.root_constraint@np.diag(d)
    saddle = sparse.bmat(((scaled_stiffness, sparse.csr_matrix(scaled_root.T)),
                          (sparse.csr_matrix(scaled_root), sparse.csr_matrix((3, 3)))),
                         format="csc")
    rhs = np.r_[d*operators.load/E0, np.zeros(3)]
    with warnings.catch_warnings():
        warnings.simplefilter("error", MatrixRankWarning)
        try:
            result = spsolve(saddle, rhs)
        except MatrixRankWarning as exc:
            raise ValueError("singular Q1 saddle factorization") from exc
    if not np.isfinite(result).all():
        raise ValueError("nonfinite Q1 saddle solution")
    q = d*result[:-3]
    multiplier = E0*root_scale@result[-3:]
    residual = stiffness@q+operators.root_constraint.T@multiplier-operators.load
    return q, multiplier, {
        "shell_energy_j": float(q@operators.shell_stiffness@q/2),
        "beam_energy_j": float(q@operators.beam_stiffness@q/2),
        "external_work_j": float(operators.load@q),
        "root_compatibility_scaled": float(np.max(np.abs(root_scale@operators.root_constraint@q))),
        "equilibrium_scaled": float(np.max(np.abs(d*residual/E0))),
        "root_singular_values": singulars,
        "tip_pose": operators.tip_pose@q,
        "root_reaction_physical": -multiplier,
        "shell_nnz": operators.shell_stiffness.nnz,
        "beam_nnz": operators.beam_stiffness.nnz,
    }
