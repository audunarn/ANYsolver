"""Focused algebraic checks for preparatory conforming Qp energy."""

from dataclasses import replace
import math

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss

import scripts._b3_e4_f03_conforming_qp_energy as qp_energy
from scripts._b3_e4_f03_conforming_q1_energy import (
    assemble as assemble_q1, solve as solve_q1,
)
from scripts._b3_e4_f03_conforming_qp_energy import (
    _require_solution_checks, _station_rule, assemble, solve,
)
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0, F0, PLANE, SECTION, THICKNESS


def _basis(p, t):
    values = []
    derivatives = []
    for a in range(p+1):
        factors = [(t-b/p)/(a/p-b/p) for b in range(p+1) if b != a]
        values.append(math.prod(factors))
        derivatives.append(sum(math.prod(factors[:j]+factors[j+1:]) /
                               (a/p-b/p) for j, b in enumerate(
                                   b for b in range(p+1) if b != a)))
    return np.array(values), np.array(derivatives)


def _direct_shell_energy(trace, q):
    full = np.zeros(2*trace.n)
    full[trace.free_columns] = q
    roots, weights = leggauss(trace.p+2)
    energy = 0.
    for i, (xl, xr) in enumerate(zip(trace.x, trace.x[1:])):
        hx = xr-xl
        for k, (yl, yr) in enumerate(zip(trace.y, trace.y[1:])):
            hy = yr-yl
            nodes = np.array([(i*trace.p+a)*trace.ny+k*trace.p+b
                              for a in range(trace.p+1) for b in range(trace.p+1)])
            ux, uy = full[nodes], full[trace.n+nodes]
            for gx, wx in zip(roots, weights):
                bx, dbx = _basis(trace.p, (gx+1)/2)
                for gy, wy in zip(roots, weights):
                    by, dby = _basis(trace.p, (gy+1)/2)
                    dx = np.outer(dbx/hx, by).ravel()
                    dy = np.outer(bx, dby/hy).ravel()
                    strain = np.array((dx@ux, dy@uy, dy@ux+dx@uy))
                    energy += wx*wy*hx*hy*THICKNESS/8*(strain@PLANE@strain)
    return energy


def _direct_beam_energy_and_load(trace, q):
    full = np.zeros(2*trace.n)
    full[trace.free_columns] = q
    energy = work = 0.
    for left, right in trace.station_intervals():
        stations, weights = _station_rule(left, right, trace.p+5)
        for station, weight in zip(stations, weights):
            pose, derivative, _ = trace.matrices(float(station))
            pose, derivative = pose@full, derivative@full
            strain = np.array((derivative[0], derivative[2],
                               derivative[1]-pose[2]))
            energy += weight*(strain@SECTION@strain)/2
        stations, weights = _station_rule(left, right, 64)
        for station, weight in zip(stations, weights):
            pose = trace.matrices(float(station))[0]@full
            work += weight*F0*(1+.25*math.cos(2*math.pi*station))*pose[1]
    return energy, work


def test_p1_separately_assembled_q1_matrix_load_and_solve():
    generic = assemble(FinitePadQpTrace(1))
    specific = assemble_q1()
    assert np.array_equal(generic.free_columns, specific.free_columns)
    assert np.allclose(generic.shell_stiffness.toarray(),
                       specific.shell_stiffness.toarray(), rtol=2e-13, atol=2e-4)
    assert np.allclose(generic.beam_stiffness.toarray(),
                       specific.beam_stiffness.toarray(), rtol=2e-11, atol=2e-4)
    assert np.allclose(generic.load, specific.load, rtol=2e-12, atol=2e-7)
    assert np.allclose(generic.root_constraint, specific.root_constraint, atol=5e-13)
    q, reaction, result = solve(generic)
    q1, reaction1, result1 = solve_q1(specific)
    assert np.allclose(q, q1, rtol=1e-9, atol=1e-12)
    assert np.allclose(reaction, reaction1, rtol=1e-9, atol=1e-6)
    assert np.allclose(result["tip_pose"], result1["tip_pose"], rtol=1e-9, atol=1e-12)
    assert result["root_compatibility_scaled"] < 1e-8
    assert result["equilibrium_scaled"] < 1e-8
    assert result["work_identity_scaled"] < 1e-10


@pytest.mark.parametrize("p", (2, 3, 4, 5, 6))
def test_piecewise_random_fields_against_independent_shell_and_dense_beam_oracles(p, monkeypatch):
    trace = FinitePadQpTrace(p, x=(-.5, 0., 1., 1.5), y=(-.5, 0., .5))
    operators = assemble(trace)
    assert operators.dof_count < 450
    assert operators.shell_stiffness.nnz < operators.dof_count**2
    assert operators.beam_stiffness.nnz < operators.dof_count**2
    assert operators.beam_discrepancy_relative < 1e-10
    assert operators.load_discrepancy_scaled < 1e-10
    rng = np.random.default_rng(710+p)
    for _ in range(2):
        q = rng.normal(size=operators.dof_count)*1e-5
        shell = _direct_shell_energy(trace, q)
        beam, work = _direct_beam_energy_and_load(trace, q)
        assert q@operators.shell_stiffness@q/2 == pytest.approx(shell, rel=2e-11)
        assert q@operators.beam_stiffness@q/2 == pytest.approx(beam, rel=2e-11)
        assert operators.load@q == pytest.approx(work, rel=2e-11, abs=2e-8)
    candidate, reaction, result = solve(operators)
    assert np.isfinite(candidate).all() and np.isfinite(reaction).all()
    assert result["scaled_shell_min_eigenvalue"] > 1e-10
    assert result["root_compatibility_scaled"] < 1e-8
    assert result["equilibrium_scaled"] < 1e-8
    assert result["work_identity_scaled"] < 1e-10
    if p == 2:
        duplicate = operators.root_constraint.copy()
        duplicate[2] = duplicate[1]
        with pytest.raises(ValueError, match="three independent"):
            solve(replace(operators, root_constraint=duplicate))
        # Finite but incorrect factor responses must never be reported as a
        # candidate. The two perturbations isolate equilibrium and root rows.
        with monkeypatch.context() as patch:
            patch.setattr(qp_energy, "spsolve", lambda matrix, rhs: np.zeros_like(rhs))
            with pytest.raises(ValueError, match="equilibrium numerical"):
                solve(operators)
        displacement_scale = np.sqrt(E0/(operators.shell_stiffness+
                                          operators.beam_stiffness).diagonal())
        index = int(np.argmax(np.abs(operators.root_constraint[0]*displacement_scale)))
        wrong = np.zeros(operators.dof_count+3)
        wrong[index] = 1.
        with monkeypatch.context() as patch:
            patch.setattr(qp_energy, "spsolve", lambda matrix, rhs: wrong.copy())
            with pytest.raises(ValueError, match="root compatibility numerical"):
                solve(operators)


@pytest.mark.parametrize("values,failed", [
    ((2e-10, 0., 0.), "root compatibility"),
    ((0., 2e-10, 0.), "equilibrium"),
    ((0., 0., 2e-10), "energy/work identity"),
])
def test_numerical_return_guards_reject_finite_wrong_metrics(values, failed):
    with pytest.raises(ValueError, match=failed):
        _require_solution_checks(*values)


def test_missing_comparison_rejected_before_factorization():
    trace = FinitePadQpTrace(2, x=(-.5, 0., 1., 1.5), y=(-.5, 0., .5))
    operators = assemble(trace, compare_quadrature=False)
    with pytest.raises(ValueError, match="quadrature comparison"):
        solve(operators)


def test_resource_inventory_rejects_oversized_grid_before_assembly():
    trace = FinitePadQpTrace(3, x=np.linspace(-.5, 1.5, 29),
                             y=np.linspace(-.5, .5, 13))
    with pytest.raises(ValueError, match="resource inventory"):
        assemble(trace)
