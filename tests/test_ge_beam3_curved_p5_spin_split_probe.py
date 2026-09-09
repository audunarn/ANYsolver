"""Development checks for the bounded current-chord spin coordinate."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, T6
from docs.reference_cases.ge_beam3_curved_p5_spin_split_probe import CurrentChordSpinProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import CurvedFiniteProbe, LocalStationarityError
from test_ge_beam3_curved_p5_algebra_probe import reference, section, perturbed, assert_scaled_close


def coupled_state(ref, rho, amplitude):
    x = ref.coordinates+amplitude*np.array([[.01, -.02, .03], [.04, .03, -.02], [-.01, .04, .02]])
    q = np.array([rotation(amplitude*np.array(v)) @ frame for v, frame in zip(
        [[.04, -.02, .06], [-.03, .05, .02], [.02, .03, -.04]], ref.nodal_triads)])
    scaling = np.diag([rho]*3+[1.]*3)
    return scaling @ section() @ scaling, x, q


@pytest.mark.parametrize("rho", [1., 100., 10000., 1000000.])
def test_coupled_section_at_explicit_reciprocal_contrast_amplitude(rho):
    # These are additional load states, not replacements for the preserved
    # amplitude-one high-contrast failure and not an amplitude admission rule.
    ref = reference(.6, .2, .15)
    elastic, x, q = coupled_state(ref, rho, 1/rho)
    model = CurrentChordSpinProbe(ref, elastic, x, q)
    result = model.solve()
    assert result.physical_residual_norm <= 1e-11
    assert result.iterations <= 25
    jet, _, maps = model.jet(result.parameters)
    assert model.physical_norm(jet, maps) <= 1e-11
    assert np.linalg.eigvalsh(jet.hessian).min() > 0
    assert all(abs(result.parameters[[2, 5]]) < np.pi)


def test_force_component_is_exactly_independent_of_current_chord_spin():
    ref = reference(.6, .2, .15)
    elastic, x, q = coupled_state(ref, 1000000., 1.)
    model = CurrentChordSpinProbe(ref, elastic, x, q)
    # Explicit component ablation for this algebra unit test only. Never solve
    # or qualify the resulting degenerate functional; the real section and
    # all coupled moment terms remain present in every other test.
    model.base.h_inverse = (np.zeros((6, 6)), np.zeros((6, 6)))
    parameters = np.array([.07, -.04, .6, -.03, .02, -.8])
    jet, rotations, _ = model.jet(parameters)
    assert np.array_equal(jet.gradient[[2, 5]], np.zeros(2))
    assert np.array_equal(jet.hessian[[2, 5]], np.zeros((2, 6)))
    parameters[[2, 5]] = 0
    unspun, other_rotations, _ = model.jet(parameters)
    assert jet.value == unspun.value
    assert not np.array_equal(rotations, other_rotations)


@pytest.mark.parametrize("force", [None, [.1, -.2, .3]])
def test_moderate_coupled_solution_and_loaded_work_match_original(force):
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    original = CurvedFiniteProbe(ref, section(), line_force=force).evaluate(x, q)
    result = CurrentChordSpinProbe(ref, section(), x, q, line_force=force).solve()
    assert_scaled_close(result.potential, original.potential)
    assert_scaled_close(result.rotations, original.local_rotations)


def test_nonstationary_variations_and_physical_torque_use_same_potential():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    model = CurrentChordSpinProbe(ref, section(), x, q, line_force=[.1, -.2, .3])
    parameters = np.array([.08, -.04, .7, -.05, .03, -.6])
    jet, rotations, maps = model.jet(parameters)
    original = model.base._jet(x, q, rotations, external=False)
    assert_scaled_close(jet.value, original.value)
    for cell in (0, 1):
        selected = slice(3*cell, 3*cell+3)
        assert_scaled_close(jet.gradient[selected], maps[cell].T @ original.gradient[selected])
        # The spin column is the current chord direction, independent of tilt.
        direction = x[cell+1]-x[cell]
        assert_scaled_close(maps[cell, :, 2], direction/np.linalg.norm(direction))
    direction = np.cos(np.arange(6)+.4)/5
    step = 2e-5
    plus, _, _ = model.jet(parameters+step*direction)
    minus, _, _ = model.jet(parameters-step*direction)
    assert_scaled_close((plus.value-minus.value)/(2*step), jet.gradient @ direction, 1e-7)
    assert_scaled_close((plus.gradient-minus.gradient)/(2*step), jet.hessian @ direction, 1e-7)


def test_covariance_reversal_and_finite_superposed_motion():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    base = CurrentChordSpinProbe(ref, section(), x, q).solve()
    g = rotation([2.1, -1.8, 2.5])
    shifted = x @ g.T+[2., -4., 7.]
    frames = np.einsum("ij,njk->nik", g, q)
    spatial = CurrentChordSpinProbe(ref, section(), shifted, frames).solve()
    assert_scaled_close(spatial.potential, base.potential)
    assert_scaled_close(spatial.rotations, np.einsum("ij,njk->nik", g, base.rotations))
    moved_ref = ref.rigidly_transformed(g, np.array([2., -4., 7.]))
    moved = CurrentChordSpinProbe(moved_ref, section(), shifted, frames).solve()
    assert_scaled_close(moved.potential, base.potential)
    assert_scaled_close(moved.rotations, np.einsum("ij,njk,kl->nil", g, base.rotations, g.T))
    flip = np.diag([-1., 1., -1.])
    reversed_result = CurrentChordSpinProbe(ref.reversed(), T6 @ section() @ T6.T,
                                           x[::-1], q[::-1] @ flip).solve()
    assert_scaled_close(reversed_result.potential, base.potential)
    assert_scaled_close(reversed_result.rotations, base.rotations[::-1])


@pytest.mark.parametrize("spin", [np.pi, -np.pi, 2*np.pi, 100.])
def test_no_endpoint_only_acceptance_after_multiple_spin_turns(spin):
    ref = reference()
    x, q, _ = perturbed(ref)
    model = CurrentChordSpinProbe(ref, section(), x, q)
    with pytest.raises(ValueError, match="principal chart"):
        model.jet([0., 0., spin, 0., 0., 0.])


def test_original_extreme_coupled_case_fails_closed_without_mutating_inputs():
    ref = reference(.6, .2, .15)
    elastic, x, q = coupled_state(ref, 1000000., 1.)
    x_before, q_before = x.copy(), q.copy()
    model = CurrentChordSpinProbe(ref, elastic, x, q)
    # Preserve the unresolved case. This test proves rejection, not physics
    # qualification or proof that no admissible stationary solution exists.
    with pytest.raises(LocalStationarityError):
        model.solve()
    assert np.array_equal(x, x_before) and np.array_equal(q, q_before)
