"""Atomic finite-step checks for the experimental native point panel."""

import numpy as np
import pytest
from dataclasses import replace

from anysolver._stiffened_shell_ge_experimental import (
    ExperimentalGEAnalysis, NodalAction,
)
from anysolver import _stiffened_shell_ge_finite_experimental as finite_experimental
from anysolver._stiffened_shell_ge_checkpoint_binary import (
    MAGIC as BINARY_CHECKPOINT_MAGIC, encode as encode_binary_checkpoint,
)
from anysolver.control import CancellationToken, SolveCancelled
from test_stiffened_shell_ge_experimental import _panel


def _actions():
    return (NodalAction("beam", 105, (0., 0., 1000., 0., 0., 0.)),)


def test_finite_point_panel_accepts_two_complete_elastic_increments():
    analysis = ExperimentalGEAnalysis(_panel())
    result = analysis.solve(_actions(), (.5, 1.))
    assert result.status == "completed"
    assert result.generation == 2 and result.load_factor == 1.
    assert result.free_equilibrium_ratio <= 1e-8
    assert result.constraint_max <= 1e-9
    assert result.beam_positions[-1, 2] > 0.
    np.testing.assert_allclose(
        result.support_reactions[:analysis._shell_count].reshape(-1, 6)[:, 2].sum(),
        -1000., rtol=1e-7, atol=1e-5)
    assert not result.beam_frames.flags.writeable
    with pytest.raises(ValueError):
        result.beam_frames.setflags(write=True)
    assert analysis.recover() is result
    saved = analysis.checkpoint()
    resumed = ExperimentalGEAnalysis(_panel())
    restored = resumed.restore(saved)
    np.testing.assert_allclose(restored.shell_displacement,
                               result.shell_displacement, rtol=0., atol=0.)
    np.testing.assert_allclose(restored.beam_positions,
                               result.beam_positions, rtol=0., atol=0.)
    assert restored.accepted_factors == (.5, 1.)
    continued = resumed.solve(_actions(), (2.,))
    assert continued.generation == 3
    assert continued.accepted_factors == (.5, 1., 2.)
    assert continued.free_equilibrium_ratio <= 1e-8

    damaged = bytearray(saved)
    damaged[-20] = ord("9")
    fresh = ExperimentalGEAnalysis(_panel())
    with pytest.raises(ValueError):
        fresh.restore(bytes(damaged))
    assert fresh._generation == 0 and fresh._finite_driver is None


def test_binary_checkpoint_restores_finite_prefix_and_continues(monkeypatch):
    analysis = ExperimentalGEAnalysis(_panel())
    accepted = analysis.solve(_actions(), (.5, 1.))
    monkeypatch.setattr(finite_experimental, "MAX_JSON_CHECKPOINT_VALUES", 0)
    raw = analysis.checkpoint()
    assert raw.startswith(BINARY_CHECKPOINT_MAGIC)
    resumed = ExperimentalGEAnalysis(_panel())
    restored = resumed.restore(raw)
    assert restored.accepted_factors == accepted.accepted_factors
    np.testing.assert_array_equal(restored.shell_displacement,
                                  accepted.shell_displacement)
    np.testing.assert_array_equal(restored.cell_resultants,
                                  accepted.cell_resultants)
    continued = resumed.solve(_actions(), (2.,))
    assert continued.accepted_factors == (.5, 1., 2.)
    assert continued.free_equilibrium_ratio <= 1e-8
    damaged = bytearray(raw)
    damaged[-35] ^= 1
    fresh = ExperimentalGEAnalysis(_panel())
    with pytest.raises(ValueError, match="digest"):
        fresh.restore(bytes(damaged))
    assert fresh._generation == 0 and fresh._finite_driver is None
    driver = analysis._finite_driver
    extreme = driver._pattern.copy()
    extreme[analysis._free[0]] = 1.e308
    state = driver._state
    forged = encode_binary_checkpoint(
        "finite", analysis._identity, accepted.generation,
        (("q", state.q), ("frames", state.frames), ("cells", state.cells),
         ("resultants", state.resultants),
         ("multipliers", state.multipliers), ("pattern", extreme),
         ("accepted_factors", np.asarray(accepted.accepted_factors))))
    with pytest.raises(ValueError, match="mechanically inconsistent"):
        fresh.restore(forged)
    assert fresh._generation == 0 and fresh._finite_driver is None


def test_rejected_and_cancelled_finite_trials_keep_accepted_prefix():
    analysis = ExperimentalGEAnalysis(_panel())
    accepted = analysis.solve(_actions(), (.5,))
    with pytest.raises(RuntimeError, match="iteration limit"):
        analysis.solve(_actions(), (1.,), max_iterations=1)
    assert analysis.recover() is accepted
    assert analysis.recover().generation == 1
    token = CancellationToken()
    token.cancel("fixture cancellation")
    with pytest.raises(SolveCancelled, match="fixture cancellation"):
        analysis.solve(_actions(), (1.,), cancellation_token=token)
    assert analysis.recover() is accepted
    completed = analysis.solve(_actions(), (1.,))
    assert completed.generation == 2


def test_failed_first_finite_attempt_does_not_select_mode_or_load_pattern():
    analysis = ExperimentalGEAnalysis(_panel())
    other = (NodalAction("beam", 105, (1000., 0., 0., 0., 0., 0.)),)
    token = CancellationToken()
    token.cancel("fixture cancellation")
    with pytest.raises(SolveCancelled):
        analysis.solve(other, (1.,), cancellation_token=token)
    assert analysis._generation == 0 and analysis._finite_driver is None
    with pytest.raises(RuntimeError, match="iteration limit"):
        analysis.solve(other, (1.,), max_iterations=1)
    assert analysis._generation == 0 and analysis._finite_driver is None
    accepted = analysis.solve(_actions(), (.5, 1.))
    assert accepted.generation == 2


def test_rotation_chart_limit_uses_backtracking_before_exhaustion(monkeypatch):
    analysis = ExperimentalGEAnalysis(_panel())
    from anysolver._stiffened_shell_ge_finite_experimental import (
        FinitePointDriver, _RotationStepTooLarge,
    )
    original = FinitePointDriver._advance
    rejected = []

    def chart_limited(self, state, increment, amount):
        if not rejected and amount == 1.:
            rejected.append(True)
            raise _RotationStepTooLarge("finite beam rotation increment requires cutback")
        return original(self, state, increment, amount)

    monkeypatch.setattr(FinitePointDriver, "_advance", chart_limited)
    result = analysis.solve(_actions(), (.5, 1.))
    assert rejected and result.generation == 2
    assert result.free_equilibrium_ratio <= 1e-8


def test_partial_first_solve_keeps_accepted_prefix(monkeypatch):
    analysis = ExperimentalGEAnalysis(_panel())
    from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
    original = FinitePointDriver._assemble

    def fail_second(self, state, factor, *args, **kwargs):
        if factor == 1.:
            raise RuntimeError("fixture second-step failure")
        return original(self, state, factor, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(FinitePointDriver, "_assemble", fail_second)
        with pytest.raises(RuntimeError, match="second-step failure"):
            analysis.solve(_actions(), (.5, 1.))
    accepted = analysis.recover()
    assert accepted.generation == 1 and accepted.accepted_factors == (.5,)
    resumed = analysis.solve(_actions(), (1.,))
    assert resumed.generation == 2


@pytest.mark.parametrize("q4,s3", [
    (((1, 2, 5, 4),), ((2, 3, 6), (2, 6, 5))),
    ((), ((1, 2, 5), (1, 5, 4), (2, 3, 6), (2, 6, 5))),
])
def test_finite_mixed_and_s3_panels_restart_and_continue(q4, s3):
    base = _panel()
    definition = replace(base, shell=replace(
        base.shell, q4_elements=q4, s3_elements=s3))
    analysis = ExperimentalGEAnalysis(definition)
    first = analysis.solve(_actions(), (.5, 1.))
    assert first.generation == 2 and first.accepted_factors == (.5, 1.)
    assert first.free_equilibrium_ratio <= 1e-8
    assert first.constraint_max <= 1e-9
    support = first.support_reactions[:analysis._shell_count].reshape(-1, 6)
    np.testing.assert_allclose(support[:, 2].sum(), -1000., atol=1e-5)
    resumed = ExperimentalGEAnalysis(definition)
    restored = resumed.restore(analysis.checkpoint())
    np.testing.assert_array_equal(restored.shell_displacement,
                                  first.shell_displacement)
    np.testing.assert_array_equal(restored.beam_positions,
                                  first.beam_positions)
    continued = resumed.solve(_actions(), (2.,))
    assert continued.generation == 3
    assert continued.free_equilibrium_ratio <= 1e-8
