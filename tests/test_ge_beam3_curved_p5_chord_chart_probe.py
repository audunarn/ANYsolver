"""Small local-chart development checks, not finite-element qualification."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import reduced_energy, rotation, T6
from docs.reference_cases.ge_beam3_curved_p5_chord_chart_probe import ChordChartLocalProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import CurvedFiniteProbe, LocalStationarityError
from test_ge_beam3_curved_p5_algebra_probe import assert_scaled_close, perturbed, reference, section


@pytest.mark.parametrize("rho", [1., 100., 10000., 1000000.])
def test_high_contrast_local_stationarity_preserves_absolute_tolerance(rho):
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    elastic = np.diag([rho*rho]*3+[1., 2., 3.])
    model = ChordChartLocalProbe(ref, elastic, x, q)
    result = model.solve()
    assert result.physical_residual_norm <= 1e-11
    assert result.iterations <= 25
    jet, rotations, maps = model.jet(result.parameters)
    assert model.physical_norm(jet, maps) <= 1e-11
    assert_scaled_close(rotations, result.rotations)
    assert_scaled_close(jet.hessian, jet.hessian.T)
    assert np.linalg.eigvalsh(jet.hessian).min() > 0
    energy, _ = reduced_energy(ref, elastic, x, q, result.rotations)
    assert_scaled_close(result.potential, energy)


@pytest.mark.parametrize("rho", [10000., 1000000.])
def test_nearly_inextensional_high_contrast_state_keeps_small_tilt_coordinates(rho):
    ref = reference(.6, .2, .15)
    _, q, _ = perturbed(ref)
    x = ref.coordinates.copy()
    for cell, vector in enumerate(([.12, -.08, .06], [-.06, .1, .08])):
        x[cell+1] = x[cell]+rotation(vector) @ (ref.coordinates[cell+1]-ref.coordinates[cell])
    elastic = np.diag([rho*rho]*3+[1., 2., 3.])
    model = ChordChartLocalProbe(ref, elastic, x, q)
    result = model.solve()
    assert result.physical_residual_norm <= 1e-11
    expected, _ = reduced_energy(ref, elastic, x, q, result.rotations)
    assert_scaled_close(result.potential, expected)
    assert max(abs(result.parameters[[0, 1, 3, 4]])) < 1e-6
    assert not result.parameters.flags.writeable


@pytest.mark.parametrize("loaded", [False, True])
def test_coupled_potential_and_stationary_rotations_match_original_probe(loaded):
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    force = [.1, -.2, .3] if loaded else None
    original = CurvedFiniteProbe(ref, section(), line_force=force).evaluate(x, q)
    chart = ChordChartLocalProbe(ref, section(), x, q, line_force=force).solve()
    assert_scaled_close(chart.potential, original.potential)
    assert_scaled_close(chart.rotations, original.local_rotations)


def test_same_potential_first_and_second_variations_and_physical_torque_map():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    model = ChordChartLocalProbe(ref, section(), x, q, line_force=[.1, -.2, .3])
    parameters = np.array([.08, -.04, .07, -.05, .03, -.06])
    jet, rotations, maps = model.jet(parameters)
    original = model.base._jet(x, q, rotations, external=False)
    assert_scaled_close(jet.value, original.value)
    for cell in (0, 1):
        local = slice(3*cell, 3*cell+3)
        assert_scaled_close(jet.gradient[local], maps[cell].T @ original.gradient[local])
    direction = np.sin(np.arange(6)+.7)/4
    step = 2e-5
    plus, _, _ = model.jet(parameters+step*direction)
    minus, _, _ = model.jet(parameters-step*direction)
    assert_scaled_close((plus.value-minus.value)/(2*step), jet.gradient @ direction, 1e-7)
    assert_scaled_close((plus.gradient-minus.gradient)/(2*step), jet.hessian @ direction, 1e-7)


def test_finite_rigid_superposition():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    base = ChordChartLocalProbe(ref, section(), x, q).solve()
    transform = rotation([2.1, -1.8, 2.5])
    moved_x = x @ transform.T+[2., -4., 7.]
    moved_q = np.einsum("ij,njk->nik", transform, q)
    spatial = ChordChartLocalProbe(ref, section(), moved_x, moved_q).solve()
    assert_scaled_close(spatial.potential, base.potential)
    assert_scaled_close(spatial.rotations, np.einsum("ij,njk->nik", transform, base.rotations))


def test_reference_coordinate_change_and_reversal():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    base = ChordChartLocalProbe(ref, section(), x, q).solve()
    transform = rotation([.6, -.8, 1.1])
    moved_ref = ref.rigidly_transformed(transform, np.array([3., -2., 1.]))
    moved = ChordChartLocalProbe(moved_ref, section(), x @ transform.T+[3., -2., 1.],
                                np.einsum("ij,njk->nik", transform, q)).solve()
    assert_scaled_close(moved.potential, base.potential)
    assert_scaled_close(moved.rotations, np.einsum("ij,njk,kl->nil", transform,
                                                 base.rotations, transform.T))
    flip = np.diag([-1., 1., -1.])
    reversed_result = ChordChartLocalProbe(ref.reversed(), T6 @ section() @ T6.T,
                                          x[::-1], q[::-1] @ flip).solve()
    assert_scaled_close(reversed_result.potential, base.potential)
    assert_scaled_close(reversed_result.rotations, base.rotations[::-1])


def test_bounded_failure_repeatability_and_input_preservation():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    x_before, q_before = x.copy(), q.copy()
    model = ChordChartLocalProbe(ref, section(), x, q)
    with pytest.raises(LocalStationarityError, match="budget"):
        model.solve(max_iterations=0)
    for bad in (-1, 26, True):
        with pytest.raises(ValueError, match="limit"):
            model.solve(max_iterations=bad)
    for bad in (np.zeros(5), np.full(6, np.nan)):
        with pytest.raises(ValueError, match="six-component"):
            model.solve(initial=bad)
    first, second = model.solve(), model.solve()
    assert first.potential == second.potential
    assert np.array_equal(first.parameters, second.parameters)
    assert np.array_equal(x, x_before) and np.array_equal(q, q_before)
    with pytest.raises(ValueError, match="tilt"):
        model.jet([3., 0., 0., 0., 0., 0.])
    x[1] = x[0]
    with pytest.raises(ValueError, match="chord"):
        ChordChartLocalProbe(ref, section(), x, q)
