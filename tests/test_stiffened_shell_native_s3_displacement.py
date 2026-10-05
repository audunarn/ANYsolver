"""Native elastic mixed/all-S3 fixed displacement lifecycle."""
from dataclasses import replace
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_displacement_checkpoint import decode_snapshot
from test_stiffened_shell_native_point_displacement import (
    model, owner, compare, native_state, ACTIONS, DIRECTION, CONTROL, OPTIONS, HISTORICAL_POLICY)


@pytest.mark.parametrize('q4,s3', (
    (((1, 2, 5, 4),), ((2, 3, 6), (2, 6, 5))),
    ((), ((1, 2, 5), (1, 5, 4), (2, 3, 6), (2, 6, 5))),
))
def test_native_elastic_s3_displacement_cancel_restore_reject(request, monkeypatch, tmp_path, q4, s3):
    base = model('generalized')
    definition = replace(base, shell=replace(base.shell, q4_elements=q4, s3_elements=s3),
                         q4_pullback_policy=base.q4_pullback_policy if q4 else HISTORICAL_POLICY)
    analysis = owner(request, definition)
    resumed = owner(request, definition)
    assert analysis.capabilities['displacement_control'] == 'experimental_native_point_elastic_s3_fixed_translation_v1'
    analysis.solve(ACTIONS, (.5, 1.), **OPTIONS)
    dof = analysis._shell_count + 6*analysis._beam_index[105] + 2
    initial = analysis._finite_driver._state.q[dof]
    targets = (initial*.99, initial*1.01)
    token = CancellationToken()
    def accepted(result):
        assert result.free_equilibrium_ratio <= 1e-8 and result.constraint_max <= 1e-9
        token.cancel('accepted S3 displacement prefix')
    kwargs = dict(OPTIONS, displacement_control=CONTROL)
    with pytest.raises(SolveCancelled):
        analysis.solve(DIRECTION, targets, **kwargs, cancellation_token=token, on_accepted=accepted)
    saved = analysis.checkpoint()
    prefix = analysis.recover()
    metadata, arrays = decode_snapshot(analysis, saved)
    assert metadata['policy'] == 'B3_GE_NATIVE_POINT_ELASTIC_S3_DISPLACEMENT_V1_DEV'
    assert not any(name.startswith('shell_plastic') for name in arrays)
    restored = resumed.restore(saved)
    assert resumed.checkpoint() == saved
    compare(prefix, restored)
    (tmp_path/'s3-prefix.checkpoint').write_bytes(saved)
    import anysolver._stiffened_shell_displacement_corrector as corrector
    with monkeypatch.context() as patch:
        patch.setattr(corrector, 'bordered_correction', lambda matrix, *args: (np.zeros(matrix.shape[0]), 0.))
        with pytest.raises(ss.DisplacementCorrectorFailure):
            analysis.solve(DIRECTION, (targets[1],), **kwargs)
    assert analysis.checkpoint() == saved
    # Native displacement chart events are admitted by the current public
    # controller. Preserve the accepted load, physical frames and histories;
    # restart and continue the same rebased endpoint on both owners.
    history_before = native_state(analysis)
    rebased = analysis.rebase_rotations(prefix.generation)
    repeated_rebase = resumed.rebase_rotations(prefix.generation)
    compare(rebased, repeated_rebase)
    assert rebased.generation == prefix.generation+1
    assert rebased.history == prefix.history and rebased.amplitude == prefix.amplitude
    np.testing.assert_array_equal(rebased.shell_frames, prefix.shell_frames)
    for name, value in history_before.items():
        np.testing.assert_array_equal(value, native_state(analysis)[name])
    rebased_raw = analysis.checkpoint()
    assert resumed.checkpoint() == rebased_raw
    rebased_metadata, rebased_arrays = decode_snapshot(analysis, rebased_raw)
    assert rebased_metadata['chart_events'] == 1
    assert not np.any(rebased_arrays['q'][:analysis._shell_count].reshape(-1,6)[:,3:])
    np.testing.assert_array_equal(rebased_arrays['shell_anchors'], prefix.shell_frames)
    replayed = owner(request, definition)
    compare(rebased, replayed.restore(rebased_raw))
    assert replayed.checkpoint() == rebased_raw
    with pytest.raises(ValueError, match='stale or invalid'):
        analysis.rebase_rotations(prefix.generation)
    assert analysis.checkpoint() == rebased_raw
    final = analysis.solve(DIRECTION, (targets[1],), **kwargs)
    continued = resumed.solve(DIRECTION, (targets[1],), **kwargs)
    continued_replay = replayed.solve(DIRECTION, (targets[1],), **kwargs)
    compare(final, continued)
    compare(final, continued_replay)
    assert analysis.checkpoint() == resumed.checkpoint() == replayed.checkpoint()
    assert final.free_equilibrium_ratio <= 1e-8 and final.constraint_max <= 1e-9
    assert not final.production_qualified
    support = final.support_reactions[:analysis._shell_count].reshape(-1, 6)
    applied = final.applied_dead_load[:analysis._shell_count+6*len(analysis._beam_ids)].reshape(-1, 6)
    np.testing.assert_allclose(support[:, :3].sum(axis=0) + applied[:, :3].sum(axis=0), 0., atol=1e-5)
    (tmp_path/'s3-completed.checkpoint').write_bytes(analysis.checkpoint())
