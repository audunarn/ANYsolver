"""Constitutive potential, mixed derivatives and station state research tests."""

from fractions import Fraction as F

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_section_probe import (
    DirectedHardeningSectionProbe, SectionHistory, SectionStationProbe,
    SectionTransactionError, _digest,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, T6
from test_ge_beam3_curved_p5_algebra_probe import section


DIRECTION = np.array([1., .2, -.1, .3, -.4, .5])


def model():
    return DirectedHardeningSectionProbe(section(), DIRECTION, .1, .4)


@pytest.mark.parametrize('amplitude', [0., .005, .3, -.3])
def test_full_section_potential_resultants_and_tangent(amplitude):
    law = model()
    strain = amplitude*DIRECTION
    made = law.strain_response(strain)
    direction = np.cos(np.arange(6)+.3)/4
    step = 1e-6
    plus, minus = law.strain_response(strain+step*direction), law.strain_response(strain-step*direction)
    assert abs((plus.incremental_potential-minus.incremental_potential)/(2*step)-made.resultants @ direction) <= 1e-7
    assert np.linalg.norm((plus.resultants-minus.resultants)/(2*step)-made.tangent @ direction) <= 1e-7
    assert np.linalg.norm(made.tangent-made.tangent.T) <= 1e-11
    assert np.linalg.eigvalsh(made.tangent).min() > 0
    assert made.dissipation_increment >= 0
    yield_value = abs(DIRECTION @ made.resultants)-(.1+.4*made.history.accumulated)
    assert yield_value <= 1e-11
    if made.plastic_active:
        assert abs(yield_value) <= 1e-11


def test_return_and_energy_agree_with_exact_rational_scalar_minimizer():
    elastic = np.diag([4., 8., 16., 2., 6., 10.])
    a = [F(1), F(1, 2), F(-1, 4), F(1, 2), F(1, 4), F(-1, 2)]
    e = [v/F(2) for v in a]
    diagonal = list(map(F, [4, 8, 16, 2, 6, 10]))
    drive = sum(x*c*y for x, c, y in zip(a, diagonal, e))
    metric = sum(x*c*x for x, c in zip(a, diagonal))
    delta = (drive-F(1, 8))/(metric+F(1, 2))
    stress = [c*(x-delta*y) for c, x, y in zip(diagonal, e, a)]
    potential = sum((x-delta*y)*s/F(2) for x, y, s in zip(e, a, stress))+delta**2/F(4)+delta/F(8)
    law = DirectedHardeningSectionProbe(elastic, list(map(float, a)), .125, .5)
    made = law.strain_response(list(map(float, e)))
    assert abs(made.history.plastic_coordinate-float(delta)) <= 1e-11
    assert np.linalg.norm(made.resultants-np.array(list(map(float, stress)))) <= 1e-11
    assert abs(made.incremental_potential-float(potential)) <= 1e-11


@pytest.mark.parametrize('scale', [.001, 1., -1.])
def test_partial_legendre_response_matches_full_return_and_directional_derivatives(scale):
    law = model()
    origin = SectionHistory(.02, .04)
    point = scale*np.array([.3, -.2, .1, .4, -.3, .2])
    made = law.mixed_response(point[:3], point[3:], origin)
    full = law.strain_response(made.section.strain, origin)
    assert abs(full.history.plastic_coordinate-made.section.history.plastic_coordinate) <= 1e-11
    assert abs(full.history.accumulated-made.section.history.accumulated) <= 1e-11
    assert np.linalg.norm(full.resultants[3:]-point[3:]) <= 1e-11
    assert np.linalg.norm(full.tangent-made.section.tangent) <= 1e-11
    direction = np.cos(np.arange(6)+.2)/5
    step = 1e-6
    plus_point, minus_point = point+step*direction, point-step*direction
    plus = law.mixed_response(plus_point[:3], plus_point[3:], origin)
    minus = law.mixed_response(minus_point[:3], minus_point[3:], origin)
    assert abs((plus.potential-minus.potential)/(2*step)-made.gradient @ direction) <= 1e-7
    assert np.linalg.norm((plus.gradient-minus.gradient)/(2*step)-made.hessian @ direction) <= 1e-7
    eigenvalues = np.linalg.eigvalsh(made.hessian)
    assert np.count_nonzero(eigenvalues > 0) == 3
    assert np.count_nonzero(eigenvalues < 0) == 3
    assert np.linalg.norm(made.hessian-made.hessian.T) <= 1e-11
    # At fixed moment the curvature is a minimizer of phi(gamma,kappa)-m.kappa.
    for perturbation in (np.array([.1, -.2, .3]), np.array([-.3, .2, -.1])):
        strain = made.section.strain.copy()
        strain[3:] += perturbation
        trial = law.strain_response(strain, origin)
        assert trial.incremental_potential-point[3:] @ strain[3:] >= made.potential


def test_pure_bending_plastic_flow_has_valid_moment_controlled_hardening():
    direction = np.array([0., 0., 0., 1., -.2, .3])
    law = DirectedHardeningSectionProbe(section(), direction, .1, .4)
    moment = np.array([.4, -.3, .2])
    made = law.mixed_response([.1, -.05, .02], moment)
    expected = (direction[3:] @ moment-.1)/.4
    assert made.section.plastic_active
    assert abs(made.section.history.plastic_coordinate-expected) <= 1e-11
    assert np.linalg.norm(made.section.resultants[3:]-moment) <= 1e-11
    full = law.strain_response(made.section.strain)
    assert abs(full.history.plastic_coordinate-expected) <= 1e-11


@pytest.mark.parametrize('transform', [T6, np.kron(np.eye(2), rotation([1.7, -1.4, 2.]))])
def test_physical_frame_reexpression_and_reversal_preserve_constitutive_work(transform):
    elastic = section()
    # Form the congruence as a Gram product to keep exact stored symmetry.
    factor = np.linalg.cholesky(elastic).T @ transform.T
    other = DirectedHardeningSectionProbe(factor.T @ factor, transform @ DIRECTION, .1, .4)
    origin = SectionHistory(.02, .04)
    strain = .3*DIRECTION
    made = model().strain_response(strain, origin)
    moved = other.strain_response(transform @ strain, origin)
    assert abs(moved.history.plastic_coordinate-made.history.plastic_coordinate) <= 1e-11
    assert abs(moved.incremental_potential-made.incremental_potential) <= 1e-11
    assert np.linalg.norm(moved.resultants-transform @ made.resultants) <= 1e-11
    assert np.linalg.norm(moved.tangent-transform @ made.tangent @ transform.T) <= 1e-11
    gamma, moment = np.array([.3, -.2, .1]), np.array([.4, -.3, .2])
    mixed = model().mixed_response(gamma, moment, origin)
    other_mixed = other.mixed_response(transform[:3, :3] @ gamma, transform[3:, 3:] @ moment, origin)
    assert abs(other_mixed.potential-mixed.potential) <= 1e-11
    assert np.linalg.norm(other_mixed.gradient-transform @ mixed.gradient) <= 1e-11
    assert np.linalg.norm(other_mixed.hessian-transform @ mixed.hessian @ transform.T) <= 1e-11


def test_load_unload_reversal_preserves_monotone_accumulation_and_dissipation():
    station = SectionStationProbe(model())
    previous = SectionHistory()
    responses = []
    for amplitude in (0., .05, .2, .195, .1, -.1, .1):
        before = station.committed
        response = station.trial(amplitude*DIRECTION)
        assert station.committed == before
        assert response.history.accumulated >= previous.accumulated
        assert response.dissipation_increment >= 0
        station.commit(response)
        assert _digest(station.replay()) == _digest(response)
        previous = response.history
        responses.append(response)
    assert responses[2].plastic_active
    assert not responses[3].plastic_active
    assert responses[5].history.plastic_coordinate < responses[2].history.plastic_coordinate
    assert station.committed[0] == 7


def test_replay_uses_accepted_origin_not_new_unloading_tangent():
    elastic = np.diag([4., 3., 2., 1., 2., 3.])
    law = DirectedHardeningSectionProbe(elastic, [1., 0., 0., 0., 0., 0.], .125, .5)
    station = SectionStationProbe(law)
    strain = np.array([.5, 0., 0., 0., 0., 0.])
    accepted = station.trial(strain)
    station.commit(accepted)
    replay = station.replay()
    new_trial = station.trial(strain)
    assert replay.plastic_active and not new_trial.plastic_active
    assert np.linalg.norm(replay.resultants-new_trial.resultants) <= 1e-11
    assert np.linalg.norm(replay.tangent-new_trial.tangent) > 1.
    station.discard(new_trial)
    assert _digest(station.replay()) == _digest(replay)


def test_station_ownership_discard_stale_commit_and_independent_histories():
    first, second = SectionStationProbe(model()), SectionStationProbe(model())
    trial = first.trial(.3*DIRECTION)
    with pytest.raises(SectionTransactionError):
        second.commit(trial)
    first.discard(trial)
    with pytest.raises(SectionTransactionError):
        first.commit(trial)
    stale = first.trial(.3*DIRECTION)
    current = first.trial(.2*DIRECTION)
    with pytest.raises(SectionTransactionError):
        first.commit(stale)
    first.commit(current)
    with pytest.raises(SectionTransactionError):
        first.commit(current)
    assert second.committed == (0, SectionHistory())
    with pytest.raises(SectionTransactionError):
        second.replay()


def test_mutation_and_invalid_trial_leave_history_and_replay_unchanged():
    station = SectionStationProbe(model())
    accepted = station.trial(.2*DIRECTION)
    station.commit(accepted)
    before, digest = station.committed, _digest(station.replay())
    accepted.strain.setflags(write=True)
    accepted.strain[:] = 99.
    assert _digest(station.replay()) == digest
    trial = station.trial(.3*DIRECTION)
    trial.tangent.setflags(write=True)
    trial.tangent[0, 0] += .1
    with pytest.raises(SectionTransactionError, match='altered'):
        station.commit(trial)
    station.discard(trial)
    pending = station.trial(.3*DIRECTION)
    with pytest.raises(ValueError):
        station.trial(np.full(6, np.nan))
    with pytest.raises(SectionTransactionError):
        station.commit(pending)
    assert station.committed == before
    assert _digest(station.replay()) == digest


def test_input_bounds_and_unadmitted_history_models_are_rejected():
    for hardening in (0., -1., np.nan, True):
        with pytest.raises(ValueError):
            DirectedHardeningSectionProbe(section(), DIRECTION, .1, hardening)
    for bad in (np.zeros(6), np.full(6, np.inf)):
        with pytest.raises(ValueError):
            DirectedHardeningSectionProbe(section(), bad, .1, .4)
    for history in (SectionHistory(.1, 0.), SectionHistory(np.nan, 1.), SectionHistory(True, 1.)):
        with pytest.raises(ValueError):
            model().strain_response(np.zeros(6), history)
    with pytest.raises(ValueError):
        model().mixed_response(np.zeros(6), np.zeros(3))
    with pytest.raises(ValueError):
        SectionStationProbe(object())
