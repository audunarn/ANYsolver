"""Bounded, preparatory Qp finite-pad shell/beam energy and three-root solve.

This is an independent classical-reference candidate, not registered F03
evidence, a native interface law, or a convergence/qualification result.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import sparse
from scipy.sparse.linalg import MatrixRankWarning, eigsh, spsolve

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import (
    E0, F0, L0, PLANE, SECTION, THICKNESS, U0, YAW_LENGTH,
)


# Algebraic preparation limits only; these are not physical acceptance gates.
_QUADRATURE_RELATIVE_LIMIT = 1.e-10
_LOAD_SCALED_LIMIT = 1.e-10
_SHELL_EIGENVALUE_LIMIT = 1.e-10
_ROOT_RANK_RATIO_LIMIT = 1.e-10
_SOLUTION_NUMERICAL_LIMIT = 1.e-10
_MAX_FREE_DOFS = 5890
_MAX_STATION_INTERVALS = 128


@dataclass(frozen=True)
class QpOperators:
    trace: FinitePadQpTrace
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
    # One-ulp intervals have physical weight but no representable interior.
    if np.nextafter(left, right) >= right:
        return np.full(order, (left + right)/2), (right-left)*weights/2
    return left + (right-left)*(roots+1)/2, (right-left)*weights/2


def _shell(trace: FinitePadQpTrace, free: np.ndarray) -> sparse.csr_matrix:
    inverse = np.full(2*trace.n, -1, dtype=int)
    inverse[free] = np.arange(len(free))
    roots, weights = leggauss(trace.p+1)
    rows, columns, values = [], [], []
    m = (trace.p+1)**2
    for i, (xl, xr) in enumerate(zip(trace.x, trace.x[1:])):
        hx = xr-xl
        for k, (yl, yr) in enumerate(zip(trace.y, trace.y[1:])):
            hy = yr-yl
            nodes = np.array([(i*trace.p+a)*trace.ny+k*trace.p+b
                              for a in range(trace.p+1) for b in range(trace.p+1)])
            local = np.r_[nodes, trace.n+nodes]
            kept = np.flatnonzero(inverse[local] >= 0)
            stiffness = np.zeros((len(kept), len(kept)))
            for gx, wx in zip(roots, weights):
                tx = (gx+1)/2
                bx = np.array([basis(tx) for basis, _ in trace._basis])
                dbx = np.array([derivative(tx)/hx for _, derivative in trace._basis])
                for gy, wy in zip(roots, weights):
                    ty = (gy+1)/2
                    by = np.array([basis(ty) for basis, _ in trace._basis])
                    dby = np.array([derivative(ty)/hy for _, derivative in trace._basis])
                    dx, dy = np.outer(dbx, by).ravel(), np.outer(bx, dby).ravel()
                    bmat = np.zeros((3, 2*m))
                    bmat[0, :m], bmat[1, m:] = dx, dy
                    bmat[2, :m], bmat[2, m:] = dy, dx
                    bmat = bmat[:, kept]
                    stiffness += (wx*wy*hx*hy*THICKNESS/4)*(bmat.T@PLANE@bmat)
            active = inverse[local[kept]]
            rr, cc = np.meshgrid(active, active, indexing="ij")
            rows.extend(rr.ravel())
            columns.extend(cc.ravel())
            values.extend(stiffness.ravel())
    return sparse.coo_matrix((values, (rows, columns)),
                             shape=(len(free), len(free))).tocsr()


def _beam_and_load(trace: FinitePadQpTrace, free: np.ndarray,
                   beam_order: int, load_order: int):
    n = len(free)
    beam = sparse.csr_matrix((n, n))
    load = np.zeros(n)
    for left, right in trace.station_intervals():
        stations, weights = _station_rule(left, right, beam_order)
        interval_rows = []
        for station, weight in zip(stations, weights):
            pose, derivative, _ = trace.matrices(float(station))
            pose, derivative = pose[:, free], derivative[:, free]
            strain = np.stack((derivative[0], derivative[2],
                               derivative[1]-pose[2]))
            interval_rows.append((strain, weight))
        active = np.flatnonzero(np.any([np.any(row != 0, axis=0)
                                        for row, _ in interval_rows], axis=0))
        if len(active):
            local = np.zeros((len(active), len(active)))
            for strain, weight in interval_rows:
                bmat = strain[:, active]
                local += weight*(bmat.T@SECTION@bmat)
            rr, cc = np.meshgrid(active, active, indexing="ij")
            beam += sparse.coo_matrix((local.ravel(), (rr.ravel(), cc.ravel())),
                                       shape=(n, n)).tocsr()
        stations, weights = _station_rule(left, right, load_order)
        for station, weight in zip(stations, weights):
            pose = trace.matrices(float(station))[0]
            load += weight*F0*(1+.25*math.cos(2*math.pi*station))*pose[1, free]
    return beam, load


def assemble(trace: FinitePadQpTrace | None = None, *,
             beam_order: int | None = None, load_order: int = 48,
             compare_quadrature: bool = True) -> QpOperators:
    trace = FinitePadQpTrace(1) if trace is None else trace
    if not isinstance(trace, FinitePadQpTrace):
        raise TypeError("Qp finite-pad trace required")
    primary = trace.p+3
    comparison = trace.p+5
    beam_order = primary if beam_order is None else beam_order
    if beam_order not in (primary, comparison) or load_order not in (48, 64):
        raise ValueError("unsupported bounded Qp quadrature")
    free = trace.free_columns
    intervals = len(trace.station_intervals())
    if len(free) > _MAX_FREE_DOFS or intervals > _MAX_STATION_INTERVALS:
        raise ValueError("Qp preparation exceeds bounded resource inventory")
    shell = _shell(trace, free)
    beam, load = _beam_and_load(trace, free, beam_order, load_order)
    beam_difference = load_difference = float("nan")
    if compare_quadrature:
        comparison_beam, comparison_load = _beam_and_load(
            trace, free, comparison if beam_order == primary else primary,
            64 if load_order == 48 else 48)
        beam_difference = float(sparse.linalg.norm(beam-comparison_beam)/
                                max(sparse.linalg.norm(beam),
                                    sparse.linalg.norm(comparison_beam)))
        load_difference = float(np.max(np.abs(load-comparison_load))/F0)
    root = trace.matrices(0.)[0][:, free]
    tip = trace.matrices(1., side="left")[0][:, free]
    if any(not np.isfinite(item).all() for item in
           (shell.data, beam.data, load, root, tip)):
        raise ValueError("nonfinite Qp reference operator")
    return QpOperators(trace, free, shell, beam, load, root, tip,
                       load_difference, beam_difference, intervals)


def _scaled_root_singular_values(operators: QpOperators,
                                 displacement_scale: np.ndarray):
    root_scale = np.diag((1/U0, 1/U0, YAW_LENGTH/U0))
    root = root_scale@operators.root_constraint*displacement_scale[None, :]
    pose, derivative, _ = operators.trace.matrices(0.)
    columns = operators.free_columns
    stacked = np.vstack((root, L0*root_scale@derivative[:, columns]*
                         displacement_scale[None, :]))
    return np.linalg.svd(root, compute_uv=False), np.linalg.svd(stacked, compute_uv=False)


def _require_solution_checks(root_compatibility_scaled: float,
                             equilibrium_scaled: float,
                             work_identity_scaled: float) -> None:
    """Numerical return guards, not scientific physical acceptance limits."""
    for name, value in (("root compatibility", root_compatibility_scaled),
                        ("equilibrium", equilibrium_scaled),
                        ("energy/work identity", work_identity_scaled)):
        if (not math.isfinite(value) or value < 0 or
                value > _SOLUTION_NUMERICAL_LIMIT):
            raise ValueError(f"Qp {name} numerical check failed")


def solve(operators: QpOperators, *, candidate_state=None):
    """Solve or validate one candidate after quadrature, energy and rank gates."""
    if (not np.isfinite(operators.beam_discrepancy_relative) or
            not np.isfinite(operators.load_discrepancy_scaled) or
            operators.beam_discrepancy_relative < 0 or
            operators.load_discrepancy_scaled < 0 or
            operators.beam_discrepancy_relative > _QUADRATURE_RELATIVE_LIMIT or
            operators.load_discrepancy_scaled > _LOAD_SCALED_LIMIT):
        raise ValueError("Qp beam/load quadrature comparison missing or excessive")
    shell, beam = operators.shell_stiffness, operators.beam_stiffness
    stiffness = shell+beam
    diagonal = stiffness.diagonal()
    if np.any(diagonal <= 0) or not np.isfinite(diagonal).all():
        raise ValueError("nonpositive Qp energy diagonal")
    if any(not np.isfinite(item).all() for item in
           (shell.data, beam.data, operators.load, operators.root_constraint)):
        raise ValueError("nonfinite Qp solve input")
    d = np.sqrt(E0/diagonal)
    scaled_shell = sparse.diags(d)@shell@sparse.diags(d)/E0
    shell_norm = sparse.linalg.norm(scaled_shell)
    if sparse.linalg.norm(scaled_shell-scaled_shell.T) > 1.e-12*max(1., shell_norm):
        raise ValueError("asymmetric Qp shell energy")
    if sparse.linalg.norm(beam-beam.T) > 1.e-12*max(1., sparse.linalg.norm(beam)):
        raise ValueError("asymmetric Qp beam energy")
    # Sparse smallest-eigenvalue check avoids a global dense shell matrix.
    shell_minimum = float(eigsh(scaled_shell, k=1, which="SA",
                               return_eigenvectors=False, tol=1.e-9)[0])
    if shell_minimum <= _SHELL_EIGENVALUE_LIMIT:
        raise ValueError("Qp shell lacks positive energy on admitted fields")
    singulars, six_singulars = _scaled_root_singular_values(operators, d)
    if (not np.isfinite(singulars).all() or
            singulars[-1] <= _ROOT_RANK_RATIO_LIMIT*singulars[0]):
        raise ValueError("Qp root rows lack three independent conditions")
    if (not np.isfinite(six_singulars).all() or
            six_singulars[-1] <= _ROOT_RANK_RATIO_LIMIT*six_singulars[0]):
        raise ValueError("Qp root pose/derivative rows lack six independent channels")
    scaled_stiffness = sparse.diags(d)@stiffness@sparse.diags(d)/E0
    root_scale = np.diag((1/U0, 1/U0, YAW_LENGTH/U0))
    scaled_root = root_scale@operators.root_constraint@np.diag(d)
    saddle = sparse.bmat(((scaled_stiffness, sparse.csr_matrix(scaled_root.T)),
                          (sparse.csr_matrix(scaled_root), sparse.csr_matrix((3, 3)))),
                         format="csc")
    rhs = np.r_[d*operators.load/E0, np.zeros(3)]
    if candidate_state is None:
        with warnings.catch_warnings():
            warnings.simplefilter("error", MatrixRankWarning)
            try:
                result = spsolve(saddle, rhs)
            except MatrixRankWarning as exc:
                raise ValueError("singular Qp saddle factorization") from exc
    else:
        result = np.asarray(candidate_state, dtype=np.float64)
        if result.shape != (operators.dof_count + 3,):
            raise ValueError("Qp candidate state has wrong KKT dimension")
    if not np.isfinite(result).all():
        raise ValueError("nonfinite Qp saddle solution")
    q = d*result[:-3]
    multiplier = E0*root_scale@result[-3:]
    residual = stiffness@q+operators.root_constraint.T@multiplier-operators.load
    shell_energy = float(q@shell@q/2)
    beam_energy = float(q@beam@q/2)
    external_work = float(operators.load@q)
    root_compatibility = float(np.max(np.abs(root_scale@operators.root_constraint@q)))
    equilibrium = float(np.max(np.abs(d*residual/E0)))
    work_identity = abs(2*(shell_energy+beam_energy)-external_work)/E0
    _require_solution_checks(root_compatibility, equilibrium, work_identity)
    return q, multiplier, {
        "shell_energy_j": shell_energy,
        "beam_energy_j": beam_energy,
        "external_work_j": external_work,
        "root_compatibility_scaled": root_compatibility,
        "equilibrium_scaled": equilibrium,
        "work_identity_scaled": work_identity,
        "root_singular_values": singulars,
        "root_pose_derivative_singular_values": six_singulars,
        "scaled_shell_min_eigenvalue": shell_minimum,
        "tip_pose": operators.tip_pose@q,
        "root_reaction_physical": -multiplier,
        "shell_nnz": shell.nnz,
        "beam_nnz": beam.nnz,
    }
