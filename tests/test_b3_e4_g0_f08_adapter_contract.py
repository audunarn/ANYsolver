"""F08 typed native local adapter parity and accepted-predecessor ownership."""

from hashlib import sha256

import numpy as np
import pytest

from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._ge_beam3_retained_fibre_program import solve_force_program
from anysolver._ge_beam3_retained_fibre_state import Context as FibreContext
from anysolver._ge_beam3_seeded_load_program import ForceProgram
from anysolver._stiffened_shell_b3_local_adapter import (
    evaluate_local_trial, evaluate_sparse_trial,
)
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from test_b3_e4_g0_f08_local_operator_seam import _sparse_local_gather
from test_ge_beam3_retained_fibre import make_model


def _relative(a, b):
    return np.linalg.norm(a-b)/max(1., np.linalg.norm(b))


@pytest.mark.parametrize("family", ("generalized", "physical_fibre"))
@pytest.mark.parametrize("trial", (False, True))
def test_typed_adapter_matches_old_local_seam_and_dense_owner(
        family, trial, monkeypatch):
    if family == "generalized":
        context = build(4, z_offset=.0675,
                        torsion_constant=square_torsion_constant()).context
        origin = context.initial.origins
        state = context.initial.mechanical
        layout = context
    else:
        context = FibreContext(
            make_model(contrast=1.),
                ForceProgram((.25,), ((5, .4, -.005, 0.),),
                         max_iterations=24))
        origin = context.initial.origins
        state = context.initial.mechanical
        layout = context.layout
    if trial:
        delta = np.zeros(layout.count)
        delta[layout.nodal_count-6+1] = 1e-6
        delta[layout.nodal_count-6+3] = 2e-6
        delta[layout.nodal_count] = 1e-6
        state = layout.advance(state, delta)
    before = canonical(origin)
    old_r, old_k, old_histories = _sparse_local_gather(
        context, state, origin, .25, fibre=family == "physical_fibre")
    dense = context.assemble(state, .25, origin)
    local = evaluate_local_trial(context, state, origin, .25,
                                 family=family, element_index=0)
    local_again = evaluate_local_trial(context, state, origin, .25,
                                       family=family, element_index=0)
    assert local.residual.shape == (42,) and local.tangent.shape == (42, 42)
    assert local.slots.shape == (42,) and not local.production_qualified
    assert local.candidate_history is not origin[0]
    np.testing.assert_array_equal(local.residual, local_again.residual)
    local.residual[0] = np.nan
    assert np.isfinite(local_again.residual).all()
    with monkeypatch.context() as patch:
        patch.setattr(context, "assemble", lambda *_: (_ for _ in ()).throw(
            AssertionError("dense assembler called by local adapter")))
        result = evaluate_sparse_trial(context, state, origin, .25,
                                       family=family)
    assert result.family == family and not result.production_qualified
    assert len(result.candidate_histories) == 2
    assert all(candidate is not previous for candidate, previous
               in zip(result.candidate_histories, origin))
    assert _relative(result.residual, old_r) == 0.
    assert _relative(result.tangent.toarray(), old_k.toarray()) == 0.
    assert _relative(result.residual, dense[0]) <= 1e-12
    assert _relative(result.tangent.toarray(), dense[1]) <= 1e-12
    assert tuple(canonical(history) for history in result.candidate_histories) == old_histories
    assert tuple(canonical(history) for history in result.candidate_histories) == tuple(
        canonical(response.history) for response in dense[3])
    assert canonical(origin) == before


def test_typed_adapter_retains_yielded_accepted_predecessor():
    program = ForceProgram((.25, .5, 1., .5, 0., -.5, 0.),
                           ((5, .4, -.005, 0.),), max_iterations=24)
    accepted = solve_force_program(make_model(contrast=1.), program,
                                   stop_after=3)
    assert accepted.status == "paused" and accepted.completed_targets == 3
    checkpoint_hash = sha256(accepted.checkpoint).hexdigest()
    context = FibreContext(make_model(contrast=1.), program)
    restored, _ = context.restore(
        accepted.checkpoint, expected_sha256=checkpoint_hash)
    origin = restored.histories
    before = canonical(origin)
    state_before = canonical(restored.mechanical.descriptor())
    assert any(row[2] > 0 for cell in origin for station in cell.stations
               for row in station.rows)
    for trial in (False, True):
        state = restored.mechanical
        if trial:
            delta = np.zeros(context.layout.count)
            delta[context.layout.nodal_count-6+1] = 1e-6
            delta[context.layout.nodal_count-6+3] = 2e-6
            delta[context.layout.nodal_count] = 1e-6
            state = context.layout.advance(state, delta)
        result = evaluate_sparse_trial(context, state, origin, 1.,
                                       family="physical_fibre")
        assert all(candidate is not previous for candidate, previous
                   in zip(result.candidate_histories, origin))
        dense = context.assemble(state, 1., origin)
        assert _relative(result.residual, dense[0]) <= 1e-12
        assert _relative(result.tangent.toarray(), dense[1]) <= 1e-12
        assert tuple(canonical(history) for history in result.candidate_histories) == tuple(
            canonical(response.history) for response in dense[3])
        assert canonical(origin) == before
        assert canonical(restored.mechanical.descriptor()) == state_before
        assert sha256(accepted.checkpoint).hexdigest() == checkpoint_hash


def test_typed_adapter_rejects_bad_family_and_parameter():
    context = build(4, z_offset=.0675,
                    torsion_constant=square_torsion_constant()).context
    with pytest.raises(ValueError, match="family"):
        evaluate_sparse_trial(context, context.initial.mechanical,
                              context.initial.origins, .25, family="legacy")
    with pytest.raises(ValueError, match="finite"):
        evaluate_sparse_trial(context, context.initial.mechanical,
                              context.initial.origins, np.nan,
                              family="generalized")
