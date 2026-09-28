"""Integrated experimental Q4/native-B3 point-panel checks."""

import anysolver
import numpy as np
import pytest
from dataclasses import replace

from anysolver import b3_ge
from anysolver import _stiffened_shell_ge_experimental as ge_experimental
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_ge_experimental import (
    PROFILE, ExperimentalGEAnalysis, FixedCoordinate, LinearDefinition,
    NodalAction, PointConnection, ShellPanel,
)


def _panel():
    e = 210e9
    nu = .3
    g = e/(2*(1+nu))
    section = b3_ge.EllipsoidalGeneralizedSection(
        np.diag((e*.01, g*.008, g*.008, g*1.6666666666666667e-5,
                 e*8.333333333333333e-6, e*8.333333333333333e-6)),
        np.eye(6), 1e20, 1e9)
    beam_points = [(x, -.5, .1) for x in (0., .5, 1., 1.5, 2.)]
    beams = tuple(b3_ge.define_beam(
        "b3-ge", i+1, (101+2*i, 102+2*i, 103+2*i),
        np.array(beam_points[2*i:2*i+3]), np.tile(np.eye(3), (3, 1, 1)),
        section, np.eye(6)) for i in range(2))
    shell = ShellPanel(
        (1, 2, 3, 4, 5, 6),
        ((0., -.5, 0.), (1., -.5, 0.), (2., -.5, 0.),
         (0., .5, 0.), (1., .5, 0.), (2., .5, 0.)),
        ((1, 2, 5, 4), (2, 3, 6, 5)), .07, e, nu, 7850.)
    return LinearDefinition(
        PROFILE, shell, beams,
        (PointConnection(1, 101), PointConnection(2, 103),
         PointConnection(3, 105)),
        tuple(FixedCoordinate("shell", node, axis)
              for node in (1, 4) for axis in range(6)))


def test_sparse_mixed_panel_solve_recovery_and_restart():
    definition = _panel()
    analysis = anysolver.stiffened_shell.create_analysis(definition=definition)
    details = analysis.preflight()
    assert details["retained_dofs"] == 48
    assert details["constraints"] == 18
    assert details["production_qualified"] is False
    assert analysis._K.nnz < analysis._K.shape[0]**2
    actions = (NodalAction("beam", 105, (0., 0., 100., 0., 0., 0.)),)
    result = analysis.solve_linear(actions)
    assert result.status == "completed"
    assert result.free_equilibrium_ratio < 1e-8
    assert result.constraint_max < 1e-9
    assert result.beam_coordinates[6*4+2] > 0.
    assert np.linalg.norm(result.reactions[analysis._fixed]) > 0.
    support = result.reactions[:analysis._shell_count].reshape(-1, 6)
    support_force = support[:, :3].sum(axis=0)
    support_moment = (support[:, 3:].sum(axis=0) +
                      np.cross(np.asarray(definition.shell.coordinates_m),
                               support[:, :3]).sum(axis=0))
    np.testing.assert_allclose(support_force, (0., 0., -100.), atol=1e-6)
    np.testing.assert_allclose(support_moment, (50., 200., 0.), atol=1e-5)
    assert not result.shell_displacement.flags.writeable
    saved = analysis.checkpoint()
    with pytest.raises(ValueError):
        result.shell_displacement.setflags(write=True)
    assert analysis.checkpoint() == saved
    resumed = b3_ge.create_stiffened_shell_analysis(
        formulation="b3-ge", definition=definition)
    restored = resumed.restore(saved)
    np.testing.assert_allclose(restored.shell_displacement,
                               result.shell_displacement, rtol=0, atol=0)
    np.testing.assert_allclose(restored.beam_coordinates,
                               result.beam_coordinates, rtol=0, atol=0)
    second = resumed.solve_linear((NodalAction(
        "beam", 105, (0., 0., 200., 0., 0., 0.)),))
    np.testing.assert_allclose(second.beam_coordinates,
                               2*result.beam_coordinates, rtol=1e-7, atol=1e-12)
    assert second.generation == restored.generation+1
    corrupted = bytearray(saved)
    corrupted[-3] = ord('9')
    fresh = ExperimentalGEAnalysis(definition)
    with pytest.raises(ValueError):
        fresh.restore(bytes(corrupted))
    with pytest.raises(RuntimeError, match="fresh"):
        resumed.restore(saved)
    assert resumed.recover().generation == second.generation


def test_invalid_action_does_not_change_accepted_prefix():
    analysis = ExperimentalGEAnalysis(_panel())
    first = analysis.solve_linear((NodalAction(
        "beam", 105, (0., 0., 10., 0., 0., 0.)),))
    saved = analysis.checkpoint()
    with pytest.raises(ValueError, match="unknown"):
        analysis.solve_linear((NodalAction(
            "beam", 999, (0., 0., 1., 0., 0., 0.)),))
    assert analysis.recover().generation == first.generation
    assert analysis.checkpoint() == saved


def test_reference_linear_load_cases_reuse_one_factorization():
    analysis = ExperimentalGEAnalysis(_panel())
    assert analysis.preflight()["reference_linear_factorizations"] == 0
    first = analysis.solve_linear((NodalAction(
        "beam", 105, (0., 0., 100., 0., 0., 0.)),))
    second = analysis.solve_linear((NodalAction(
        "beam", 105, (0., 0., 200., 0., 0., 0.)),))
    np.testing.assert_allclose(second.beam_coordinates,
                               2*first.beam_coordinates, rtol=1e-10, atol=1e-12)
    assert analysis.preflight()["reference_linear_factorizations"] == 1
    assert second.generation == first.generation+1


def test_cancellation_after_linear_factorization_preserves_empty_prefix(monkeypatch):
    analysis = ExperimentalGEAnalysis(_panel())
    action = (NodalAction("beam", 105, (0., 0., 100., 0., 0., 0.)),)
    token = CancellationToken()
    safe_point = ge_experimental.cancellation_safe_point

    def cancel_after_solve(current_token, phase):
        if phase == "stiffened-shell.linear.solved":
            current_token.cancel("after sparse solve")
        return safe_point(current_token, phase)

    monkeypatch.setattr(ge_experimental, "cancellation_safe_point",
                        cancel_after_solve)
    with pytest.raises(SolveCancelled, match="after sparse solve"):
        analysis.solve_linear(action, cancellation_token=token)
    assert analysis._generation == 0 and analysis._accepted is None
    assert analysis.preflight()["reference_linear_factorizations"] == 1
    monkeypatch.setattr(ge_experimental, "cancellation_safe_point", safe_point)
    accepted = analysis.solve_linear(action)
    assert accepted.generation == 1
    assert analysis.preflight()["reference_linear_factorizations"] == 1


@pytest.mark.parametrize("q4,s3", [
    (((1, 2, 5, 4),), ((2, 3, 6), (2, 6, 5))),
    ((), ((1, 2, 5), (1, 5, 4), (2, 3, 6), (2, 6, 5))),
])
def test_mixed_and_s3_point_panel_sparse_recovery_restart(q4, s3):
    original = _panel()
    definition = replace(original, shell=replace(
        original.shell, q4_elements=q4, s3_elements=s3))
    analysis = ExperimentalGEAnalysis(definition)
    assert analysis.preflight()["retained_dofs"] == 48
    actions = (NodalAction("beam", 105, (0., 0., 100., 0., 0., 0.)),)
    first = analysis.solve_linear(actions)
    assert first.free_equilibrium_ratio < 1e-8
    assert first.constraint_max < 1e-9
    support = first.reactions.reshape(-1, 6)
    np.testing.assert_allclose(support[:, :3].sum(axis=0),
                               (0., 0., -100.), atol=1e-5)
    restored = ExperimentalGEAnalysis(definition).restore(analysis.checkpoint())
    np.testing.assert_array_equal(restored.shell_displacement,
                                  first.shell_displacement)
    np.testing.assert_array_equal(restored.beam_coordinates,
                                  first.beam_coordinates)


def test_disconnected_shell_cells_fail_before_sparse_solve():
    original = _panel()
    shell = replace(original.shell, q4_elements=((1, 2, 5, 4), (3, 7, 8, 6)),
                    node_ids=original.shell.node_ids+(7, 8),
                    coordinates_m=original.shell.coordinates_m+
                    ((3., -.5, 0.), (3., .5, 0.)))
    with pytest.raises(ValueError, match="connected"):
        ExperimentalGEAnalysis(replace(original, shell=shell))


def test_duplicate_point_equations_fail_during_preflight():
    definition = _panel()
    with pytest.raises(ValueError, match="duplicate experimental point"):
        ExperimentalGEAnalysis(replace(
            definition, points=definition.points+(definition.points[0],)))


def test_sparse_solution_matches_bounded_dense_kkt_and_cancel_keeps_prefix():
    analysis = ExperimentalGEAnalysis(_panel())
    action = (NodalAction("beam", 105, (0., 0., 100., 0., 0., 0.)),)
    observed = analysis.solve_linear(action)
    load = np.zeros(analysis._K.shape[0])
    load[analysis._shell_count+6*analysis._beam_index[105]+2] = 100.
    dense = np.linalg.solve(analysis._A.toarray(),
                            np.r_[load[analysis._free],
                                  np.zeros(analysis._C.shape[0])])
    np.testing.assert_allclose(
        np.r_[observed.shell_displacement, observed.beam_coordinates]
        [analysis._free], dense[:len(analysis._free)], rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(observed.multipliers,
                               dense[len(analysis._free):], rtol=1e-9, atol=1e-9)
    saved = analysis.checkpoint()
    token = CancellationToken()
    token.cancel("fixture cancellation")
    with pytest.raises(SolveCancelled, match="fixture cancellation"):
        analysis.solve_linear(action, cancellation_token=token)
    assert analysis.checkpoint() == saved
