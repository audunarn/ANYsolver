"""End-to-end elastic B2 graph checks for the experimental session."""

import numpy as np
import pytest
from scipy import sparse

from anysolver import stiffened_shell

from anysolver._stiffened_shell_b2_experimental import (
    ExperimentalB2Error, create_experimental_b2_analysis,
)
from anysolver.control import CancellationToken
from test_b2_physical_linear_oriented_graph import _members, _solve


def _analysis():
    members, _ = _members()
    transform = sparse.eye(18, format="csr")[:, 6:]
    offset = np.zeros(18)
    selected = np.arange(12, 18)
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2LinearDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            members, transform, offset, selected, 8))
    # The plan is captured; later caller mutation cannot change this session.
    transform.data[:] = 0.
    offset[:] = 1.
    selected[:] = 0
    return analysis, members


def _cases(count):
    cases = []
    for index in range(count):
        load = np.zeros(18)
        load[12:18] = (
            .4+.1*np.sin(index), -.9+.1*np.cos(index),
            .7+.05*np.sin(index+.3), -.2+.03*np.cos(index+.5),
            .3+.02*np.sin(index+.7), .1+.01*np.cos(index+.9),
        )
        cases.append((f"case-{index:03}", load))
    return cases


def test_connected_graph_solves_1_10_100_with_physical_recovery_and_one_factorization():
    analysis, members = _analysis()
    assert analysis.capabilities.status == "experimental"
    assert not analysis.capabilities.production_qualified
    assert not analysis.capabilities.shell_attachment_supported
    assert analysis.node_ids == (0, 1, 2)
    for count in (1, 10, 100):
        cases = _cases(count)
        result = analysis.solve_linear_many(
            cases, recover_members={"member-1": (0., .5, 1.)})
        assert result.status == "completed" and result.failure_reason is None
        assert len(result.cases) == count
        assert result.factorization_count == 1
        assert 1 <= result.maximum_rhs_chunk <= 8
        for observed, (case_id, load) in zip(result.cases, cases):
            expected, _, _ = _solve(members, load)
            assert observed.case_id == case_id
            np.testing.assert_allclose(observed.values, expected[12:18],
                                       rtol=1e-11, atol=1e-11)
            assert len(observed.members) == 1
            recovery = observed.members[0]
            assert recovery.member_id == "member-1"
            assert recovery.stations == (0., .5, 1.)
            assert np.isfinite(recovery.resultants_local).all()
            assert np.isfinite(recovery.strains_local).all()
    analysis.close()
    with pytest.raises(ExperimentalB2Error, match="closed"):
        analysis.solve_linear_many(_cases(1))


def test_cancellation_returns_only_complete_ordered_cases():
    analysis, _ = _analysis()
    token = CancellationToken()
    seen = []

    def cancel_after_three(case_id):
        seen.append(case_id)
        if len(seen) == 3:
            token.cancel("stop after complete case")

    result = analysis.solve_linear_many(
        _cases(100), cancellation_token=token, on_case=cancel_after_three,
        recover_members={"member-1": (0., .5, 1.)})
    assert result.status == "cancelled"
    assert [case.case_id for case in result.cases] == seen == [
        "case-000", "case-001", "case-002"]
    assert all(len(case.members) == 1 for case in result.cases)
    assert result.factorization_count == 1
    analysis.close()


def test_rejects_disconnected_graph_without_inventing_coupling():
    members, _ = _members()
    from dataclasses import replace
    separated = replace(
        members[1], node_ids=(4, 5),
        reference_points_m=((5., 0., 0.), (5., 1.5, 0.)))
    with pytest.raises(ValueError, match="connected"):
        create_experimental_b2_analysis(
            (members[0], separated), sparse.eye(24, format="csr")[:, 6:],
            np.zeros(24), np.arange(6, 12))


def test_failed_sparse_solve_publishes_no_plausible_case(monkeypatch):
    analysis, _ = _analysis()

    def failed_factorization_solve(_rhs):
        raise RuntimeError("Sparse solve produced NaN/Inf values")

    monkeypatch.setattr(analysis._batch._handle, "solve_many",
                        failed_factorization_solve)
    result = analysis.solve_linear_many(_cases(10))
    assert result.status == "failed"
    assert result.cases == ()
    assert "Sparse solve produced NaN/Inf values" in result.failure_reason
    assert result.factorization_count is None
    analysis.close()


def test_unexpected_callback_error_propagates():
    analysis, _ = _analysis()

    def broken_callback(_case_id):
        raise RuntimeError("physical B2 batch solve residual failed: callback programming error")

    with pytest.raises(RuntimeError, match="callback programming error"):
        analysis.solve_linear_many(_cases(1), on_case=broken_callback)
    analysis.close()
