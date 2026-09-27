"""Private B2 1/10/100 RHS and complete-case cancellation feasibility."""

from dataclasses import replace
import math

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import spsolve

from anysolver.assembly import build_constraint_transformation
from anysolver.boundary import BoundaryCondition
from anysolver._b2_physical_linear_batch_dev import CompiledB2AffineBatch
from anysolver._b2_physical_flexibility_linear import LinearSection
from anysolver.control import CancellationToken
from anysolver.fe_core import FEModel
from test_b2_physical_linear_oriented_graph import (
    _exact_linear_solve, _force_method_energy, _members, _solve,
)


def _plan():
    transform = sparse.eye(18, format="csr")[:, 6:]
    offset = np.zeros(18)
    return transform, offset


def _cases(count):
    cases = []
    for i in range(count):
        load = np.zeros(18)
        load[12:18] = (.4+.1*np.sin(i), -.9+.1*np.cos(i),
                       .7+.05*np.sin(i+.3), -.2+.03*np.cos(i+.5),
                       .3+.02*np.sin(i+.7), .1+.01*np.cos(i+.9))
        cases.append((f"case-{i:03}", load))
    return cases


@pytest.mark.parametrize("count", (1, 10, 100))
def test_ordered_selected_batch_matches_independent_sparse_solves(count):
    members, _ = _members()
    compiled = tuple(member.compile_local() for member in members)
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(compiled, transform, offset,
                                  np.arange(12, 18), max_chunk=8)
    stiffness = batch.full_stiffness
    transform.data[:] = 0.
    offset[:] = 1.
    cases = _cases(count)
    result = batch.solve_many(cases)
    assert result.status == "completed"
    assert len(result.cases) == count
    assert result.factorization_count == 1
    assert result.maximum_rhs_chunk <= 8
    assert [case.case_id for case in result.cases] == [identity for identity, _ in cases]
    independent_k = stiffness[6:, 6:]
    for (identity, load), selected in zip(cases, result.cases):
        oracle = spsolve(independent_k, load[6:])
        np.testing.assert_allclose(selected.values, oracle[6:12],
                                   rtol=3e-12, atol=3e-12)
        assert selected.case_id == identity
    assert batch.full_stiffness is not stiffness
    batch.close()
    with pytest.raises(RuntimeError, match="closed"):
        batch.solve_many(cases[:1])


def test_cancellation_publishes_only_ordered_complete_cases():
    members, _ = _members()
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        transform, offset, np.arange(12, 18), max_chunk=8)
    token = CancellationToken()
    def stop_after_five(identity):
        if identity == "case-004":
            token.cancel("bounded prefix")
    result = batch.solve_many(_cases(100), cancellation_token=token,
                              on_case=stop_after_five)
    assert result.status == "cancelled"
    assert [case.case_id for case in result.cases] == [
        f"case-{i:03}" for i in range(5)]
    assert result.factorization_count == 1
    assert result.maximum_rhs_chunk == 8


def test_failed_factorization_does_not_return_offset_only_case():
    members, _ = _members()
    transform, offset = _plan()
    compiled = tuple(member.compile_local() for member in members)
    with pytest.raises(ValueError, match="selected DOFs"):
        CompiledB2AffineBatch(compiled, transform, offset,
                              np.array([12.5]))
    singular = transform.tolil()
    singular[:, 1] = 0.
    offset[12:18] = 42.
    with pytest.raises(RuntimeError, match="factorization failed"):
        CompiledB2AffineBatch(
            compiled,
            singular.tocsr(), offset, np.arange(12, 18), max_chunk=8)


def test_inaccurate_backend_solution_is_not_published(monkeypatch):
    members, _ = _members()
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        transform, offset, np.arange(12, 18), max_chunk=8)
    monkeypatch.setattr(batch._handle, "solve_many",
                        lambda rhs: np.zeros_like(rhs))
    observed = []
    with pytest.raises(RuntimeError, match="solve residual failed"):
        batch.solve_many(_cases(1), on_case=observed.append)
    assert observed == []
    batch.close()


@pytest.mark.parametrize("radius_m", (.005, .02, .08))
def test_scaled_batch_preserves_coherent_circular_elbow_work(radius_m):
    area = math.pi*radius_m**2
    inertia = math.pi*radius_m**4/4
    section = LinearSection.isotropic(
        E=210e9, nu=.3, area=area, Iy=inertia, Iz=inertia,
        J=2*inertia, ky=.9, kz=.9)
    members, _ = _members()
    physical = tuple(replace(member, section_id=f"circle-{radius_m}",
                             section=section) for member in members)
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in physical),
        transform, offset, np.arange(12, 18), max_chunk=8)
    tip = np.array((.1, -.08, .06, .01, -.012, .008))
    load = np.zeros(18)
    load[12:] = tip
    result = batch.solve_many((("mixed", load),))
    assert result.status == "completed" and result.factorization_count == 1
    selected = np.asarray(result.cases[0].values)
    reduced = batch.full_stiffness[6:, 6:].toarray()
    exact = np.asarray(_exact_linear_solve(reduced, load[6:]),
                       dtype=float)
    np.testing.assert_allclose(selected, exact[6:12], rtol=1e-9,
                               atol=1e-13)
    physical_work = float(_force_method_energy(physical, tip))
    assert abs(.5*tip@selected-physical_work)/physical_work <= 1e-9
    batch.close()


def test_existing_auditor_builds_b2_affine_map_and_tracks_its_dependencies():
    members, points = _members()
    _, _, stiffness = _solve(members, np.zeros(18))
    model = FEModel("bounded-B2-audited-affine")
    for node_id, point in enumerate(points):
        model.add_node(node_id, *point)
    model.add_boundary_condition(BoundaryCondition(
        "root", [0], {name: 0. for name in
                       ("ux", "uy", "uz", "rx", "ry", "rz")}))

    def equation(coefficient, value):
        model.constraint_equations.clear()
        model.add_constraint_equation(
            terms=((12, 1.), (7, -coefficient)), rhs=value,
            dependent_dof=12, source_id="tip-x-to-mid-y")
        return build_constraint_transformation(
            stiffness, np.zeros(18), model)

    _, _, first_t, first_u0, independent, _ = equation(.25, .001)
    assert first_t.shape == (18, 11) and independent.size == 11
    load = _cases(1)[0][1]
    first_k = (first_t.T@stiffness@first_t).tocsc()
    reduced_load = first_t.T@(load-stiffness@first_u0)
    state = first_t@spsolve(first_k, reduced_load)+first_u0
    assert abs(state[12]-.25*state[7]-.001) <= 1e-13
    np.testing.assert_allclose(first_t.T@(stiffness@state-load), 0.,
                               atol=1e-11)
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        first_t, first_u0, np.arange(12, 18), max_chunk=8)
    selected = batch.solve_many((("audited", load),)).cases[0].values
    np.testing.assert_allclose(selected, state[12:18],
                               rtol=1e-11, atol=1e-11)
    batch.close()

    _, _, value_t, value_u0, value_independent, _ = equation(.25, .002)
    np.testing.assert_array_equal(value_t.toarray(), first_t.toarray())
    np.testing.assert_array_equal(value_independent, independent)
    assert value_u0[12] == .002 and first_u0[12] == .001
    _, _, structural_t, _, _, _ = equation(.5, .002)
    assert not np.array_equal(structural_t.toarray(), first_t.toarray())

    model.add_boundary_condition(BoundaryCondition("conflict", [0],
                                                   {"ux": 1.}))
    with pytest.raises(ValueError, match="Invalid constraint system"):
        build_constraint_transformation(stiffness, np.zeros(18), model)
