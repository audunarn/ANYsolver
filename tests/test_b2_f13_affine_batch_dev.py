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
from anysolver.linalg import FactorizationCache
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


def test_callback_cannot_change_submitted_case_inventory():
    members, _ = _members()
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        transform, offset, np.arange(12, 18), max_chunk=4)
    submitted = _cases(10)
    expected = tuple(submitted)

    def mutate_future_cases(identity):
        if identity == "case-000":
            submitted[5] = ("replacement", np.full(18, 42.))
            submitted.pop()

    result = batch.solve_many(submitted, on_case=mutate_future_cases)
    assert result.status == "completed"
    assert [case.case_id for case in result.cases] == [
        identity for identity, _ in expected]
    assert result.maximum_rhs_chunk == 4
    stiffness = batch.full_stiffness[6:, 6:]
    for (identity, load), selected in zip(expected, result.cases):
        oracle = spsolve(stiffness, load[6:])
        np.testing.assert_allclose(selected.values, oracle[6:12],
                                   rtol=3e-12, atol=3e-12)
        assert selected.case_id == identity
    batch.close()


def test_active_batch_cannot_be_closed_or_reentered_from_callback():
    members, _ = _members()
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        transform, offset, np.arange(12, 18), max_chunk=4)

    def check_active_owner(identity):
        if identity == "case-000":
            with pytest.raises(RuntimeError, match="operation is active"):
                batch.close()
            with pytest.raises(RuntimeError, match="operation is active"):
                batch.solve_many(_cases(1))

    result = batch.solve_many(_cases(10), on_case=check_active_owner)
    assert result.status == "completed" and len(result.cases) == 10
    assert result.factorization_count == 1

    def fail_callback(_identity):
        raise LookupError("caller callback failed")

    with pytest.raises(LookupError, match="caller callback failed"):
        batch.solve_many(_cases(1), on_case=fail_callback)
    assert batch.solve_many(_cases(1)).status == "completed"
    batch.close()
    with pytest.raises(RuntimeError, match="closed"):
        batch.solve_many(_cases(1))


def test_cancellation_publishes_only_ordered_complete_cases():
    members, _ = _members()
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        transform, offset, np.arange(12, 18), max_chunk=8)
    token = CancellationToken()
    stations = [.25]
    def stop_after_five(identity):
        stations[0] = .75
        if identity == "case-004":
            token.cancel("bounded prefix")
    result = batch.solve_many(_cases(100), cancellation_token=token,
                              on_case=stop_after_five,
                              recover_members={members[0].member_id: stations})
    assert result.status == "cancelled"
    assert [case.case_id for case in result.cases] == [
        f"case-{i:03}" for i in range(5)]
    assert result.factorization_count == 1
    assert result.maximum_rhs_chunk == 8
    assert all(case.members[0].stations == (.25,) for case in result.cases)
    batch.close()


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


def test_selected_member_recovery_matches_independent_physical_states():
    members, _ = _members()
    compiled = tuple(member.compile_local() for member in members)
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        compiled, transform, offset, np.arange(12, 18), max_chunk=8)
    requested = {member.definition.member_id: (.2, .8)
                 for member in compiled}
    cases = _cases(100)
    result = batch.solve_many(cases, recover_members=requested)
    assert result.status == "completed" and len(result.cases) == 100
    assert result.maximum_rhs_chunk == 8
    stiffness = batch.full_stiffness
    for (identity, load), selected in zip(cases, result.cases):
        state = np.zeros(18)
        state[6:] = spsolve(stiffness[6:, 6:], load[6:])
        assert selected.case_id == identity
        assert len(selected.members) == 2
        for recovery, member in zip(selected.members, compiled):
            dofs = [6*batch.node_ids.index(node)+j
                    for node in member.definition.node_ids for j in range(6)]
            oracle = member.operator.evaluate(
                member.local_dof_map()@state[dofs], stations=(.2, .8))
            assert recovery.member_id == member.definition.member_id
            np.testing.assert_allclose(recovery.resultants_local,
                                       oracle.resultants, rtol=1e-10, atol=1e-12)
            np.testing.assert_allclose(recovery.strains_local,
                                       oracle.strains, rtol=1e-10, atol=1e-12)
    assert all(len(case.members) == 2 for case in result.cases)
    batch.close()


def test_selected_recovery_rejects_invalid_requests_before_case_publication():
    members, _ = _members()
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        tuple(member.compile_local() for member in members),
        transform, offset, np.arange(12, 18))
    observed = []
    with pytest.raises(ValueError, match="not compiled"):
        batch.solve_many(_cases(1), recover_members={"unknown": (.5,)},
                         on_case=observed.append)
    with pytest.raises(ValueError, match="recovery mapping"):
        batch.solve_many(_cases(1), recover_members=(.5,),
                         on_case=observed.append)
    with pytest.raises(ValueError, match="recovery stations"):
        batch.solve_many(_cases(1),
                         recover_members={members[0].member_id: (1.1,)},
                         on_case=observed.append)
    assert observed == []
    batch.close()


def test_cancellation_during_selected_recovery_discards_incomplete_case(monkeypatch):
    members, _ = _members()
    compiled = tuple(member.compile_local() for member in members)
    transform, offset = _plan()
    batch = CompiledB2AffineBatch(
        compiled, transform, offset, np.arange(12, 18))
    token = CancellationToken()
    original = type(compiled[0].operator).recover_sections

    def cancel_during_recovery(operator, displacement, *, stations):
        response = original(operator, displacement, stations=stations)
        token.cancel("during selected recovery")
        return response

    monkeypatch.setattr(type(compiled[0].operator), "recover_sections",
                        cancel_during_recovery)
    observed = []
    result = batch.solve_many(
        _cases(10), cancellation_token=token,
        recover_members={compiled[0].definition.member_id: (.5,)},
        on_case=observed.append)
    assert result.status == "cancelled"
    assert result.cases == () and observed == []
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
    compiled = tuple(member.compile_local() for member in members)
    cache = FactorizationCache(name="bounded-b2-affine", max_entries=2)
    batch = CompiledB2AffineBatch(
        compiled, first_t, first_u0, np.arange(12, 18),
        max_chunk=8, factorization_cache=cache)
    assert (cache.hits, cache.misses) == (0, 1)
    selected = batch.solve_many((("audited", load),)).cases[0].values
    np.testing.assert_allclose(selected, state[12:18],
                               rtol=1e-11, atol=1e-11)
    first_handle = batch._handle
    batch.close()

    _, _, value_t, value_u0, value_independent, _ = equation(.25, .002)
    np.testing.assert_array_equal(value_t.toarray(), first_t.toarray())
    np.testing.assert_array_equal(value_independent, independent)
    assert value_u0[12] == .002 and first_u0[12] == .001
    value_batch = CompiledB2AffineBatch(
        compiled, value_t, value_u0, np.arange(12, 18),
        factorization_cache=cache)
    assert (cache.hits, cache.misses) == (1, 1)
    assert value_batch._handle is first_handle
    value_state = value_t@spsolve(
        (value_t.T@stiffness@value_t).tocsc(),
        value_t.T@(load-stiffness@value_u0))+value_u0
    value_u0[12] = 9.
    value_selected = value_batch.solve_many((("new-value", load),)).cases[0].values
    np.testing.assert_allclose(value_selected, value_state[12:18],
                               rtol=1e-11, atol=1e-11)
    assert not np.array_equal(value_selected, selected)
    value_batch.close()

    _, _, structural_t, structural_u0, _, _ = equation(.5, .002)
    assert not np.array_equal(structural_t.toarray(), first_t.toarray())
    structural_batch = CompiledB2AffineBatch(
        compiled, structural_t, structural_u0, np.arange(12, 18),
        factorization_cache=cache)
    assert (cache.hits, cache.misses) == (1, 2)
    assert structural_batch._handle is not first_handle
    structural_state = structural_t@spsolve(
        (structural_t.T@stiffness@structural_t).tocsc(),
        structural_t.T@(load-stiffness@structural_u0))+structural_u0
    np.testing.assert_allclose(
        structural_batch.solve_many((("new-structure", load),)).cases[0].values,
        structural_state[12:18], rtol=1e-11, atol=1e-11)
    structural_batch.close()

    model.add_boundary_condition(BoundaryCondition("conflict", [0],
                                                   {"ux": 1.}))
    with pytest.raises(ValueError, match="Invalid constraint system"):
        build_constraint_transformation(stiffness, np.zeros(18), model)
