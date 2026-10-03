"""Equation parity and bounded projected reference controls, not acceptance."""
import math

import numpy as np
import pytest
from scipy import linalg

from scripts.b3_e4_bl5_modal_reference_dev import p0_shell_bracket
from scripts.r8_bl5_projected_modal_envelope_dev import projected_modal_bracket


@pytest.mark.parametrize('count,nonuniform,units', ((4, False, 1.), (17, True, 1.),
                                                  (128, True, 1000.)))
def test_old_complete_gram_parity_including_signed_basis_and_units(count, nonuniform, units):
    knots = np.linspace(0., 1., count+1)
    if nonuniform:
        knots = knots**1.3
    projection = np.column_stack((np.ones(count), np.linspace(-1., 1., count),
                                  np.cos(np.arange(count))))
    # Density transforms inversely to length, including signed basis values.
    projection /= units
    knots *= units
    args = (units, .2*units, .4*units, 768)
    old_lower, old_upper, _ = p0_shell_bracket(knots, *args)
    lower, upper, info = projected_modal_bracket(knots, projection, *args)
    np.testing.assert_allclose(lower, projection.T@old_lower@projection, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(upper, projection.T@old_upper@projection, rtol=1e-12, atol=1e-12)
    expected = linalg.eigvalsh(projection.T@(old_upper-old_lower)@projection,
                              projection.T@old_lower@projection)[-1]
    assert info['relative_diagnostic_status'] == 'available'
    assert info['relative_loewner_tail_bound'] == pytest.approx(expected, rel=1e-8, abs=1e-13)
    assert info['tail_cell_count'] == count
    assert info['max_chunk_rows'] == 256


def test_equivalent_coordinate_and_density_basis_units():
    knots = np.array((0., .07, .21, .49, .76, 1.))
    projection = np.column_stack((np.ones(5), np.linspace(-2., 3., 5)))
    lower, upper, _ = projected_modal_bracket(knots, projection, 1., .2, .4, 512)
    scaled_lower, scaled_upper, _ = projected_modal_bracket(
        1000*knots, projection/1000, 1000., 200., 400., 512)
    np.testing.assert_allclose(scaled_lower, lower, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(scaled_upper, upper, rtol=1e-12, atol=1e-12)
    basis_units = np.diag((2., -.3))
    changed_lower, changed_upper, _ = projected_modal_bracket(
        knots, projection@basis_units, 1., .2, .4, 512)
    np.testing.assert_allclose(changed_lower, basis_units.T@lower@basis_units, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(changed_upper, basis_units.T@upper@basis_units, rtol=1e-12, atol=1e-12)


def test_three_sine_projection_refinements_keep_original_modal_controls():
    length, width, ell = 1., .2, .4
    k = np.pi/(2*length)
    alpha = np.sqrt(1+ell**2*k**2)/ell
    exact = length**2*width/(2*ell**2*alpha*np.tanh(alpha*width))
    errors = []
    for count in (8, 16, 32):
        knots = np.linspace(0., length, count+1)
        projection = ((np.cos(k*knots[:-1])-np.cos(k*knots[1:]))/
                      (k*np.diff(knots)))[:, None]
        lower, upper, _ = projected_modal_bracket(knots, projection, length, width, ell, 4096)
        old_lower, old_upper, _ = p0_shell_bracket(knots, length, width, ell, 4096)
        np.testing.assert_allclose(lower, projection.T@old_lower@projection, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(upper, projection.T@old_upper@projection, rtol=1e-12, atol=1e-12)
        errors.append(abs(lower[0, 0]/exact-1.))
    assert errors[1] < .3*errors[0]
    assert errors[2] < .3*errors[1]
    assert errors[2] < 1e-3


def test_three_modal_truncations_bracket_independent_finer_sum():
    knots = np.array((0., .07, .21, .49, .76, 1.))
    projection = np.column_stack((np.ones(5), np.array((1., -2., 3., -4., 5.))))
    old_finer, _, _ = p0_shell_bracket(knots, 1., .2, .4, 4096)
    finer = projection.T@old_finer@projection
    previous = None
    for modes in (256, 512, 1024):
        lower, upper, _ = projected_modal_bracket(knots, projection, 1., .2, .4, modes)
        assert linalg.eigvalsh(finer-lower)[0] > -1e-12
        assert linalg.eigvalsh(upper-finer)[0] > -1e-12
        if previous is not None:
            assert linalg.eigvalsh(lower-previous)[0] > -1e-12
        previous = lower


def _independent_scalar_sum(knots, density, length, width, ell, modes):
    terms = []
    for mode in range(modes):
        k = (mode+.5)*math.pi/length
        coefficient = 2/(length*k)*math.fsum(
            float(value)*(math.cos(k*float(left))-math.cos(k*float(right)))
            for left, right, value in zip(knots[:-1], knots[1:], density))
        alpha = math.sqrt(1+ell**2*k**2)/ell
        weight = length**2*width/(2*ell**2*alpha*math.tanh(alpha*width))
        terms.append(weight*coefficient**2)
    return math.fsum(terms)


def test_over_old_limit_against_independent_signed_scalar_sum_and_tail():
    count, modes = 257, 1024
    knots = np.linspace(0., 1., count+1)**1.2
    density = np.cos(np.arange(count)*.17)-.4
    lower, upper, info = projected_modal_bracket(knots, density[:, None], 1., .2, .4, modes)
    expected = _independent_scalar_sum(knots, density, 1., .2, .4, modes)
    assert lower[0, 0] == pytest.approx(expected, rel=1e-12, abs=1e-13)
    first = modes+.5
    coefficient = 2*.2/.4**2/math.tanh(first*math.pi*.2)*(1/math.pi)**3*(
        first**-3+1/(2*first**2))*count
    jump_squared = density[0]**2+math.fsum(float(x)**2 for x in np.diff(density))
    assert upper[0, 0]-lower[0, 0] == pytest.approx(coefficient*jump_squared, rel=1e-10, abs=1e-14)
    finer = _independent_scalar_sum(knots, density, 1., .2, .4, 4096)
    assert lower[0, 0]-1e-12 <= finer <= upper[0, 0]+1e-12
    assert info['input_cells'] == count


def test_maximum_cell_count_constant_closed_modal_coefficients():
    count, modes = 1024, 1024
    knots = np.linspace(0., 1., count+1)
    lower, upper, info = projected_modal_bracket(knots, np.ones((count, 1)), 1., .2, .4, modes)
    # For a complete constant density the integral telescopes to 2/(L*k).
    terms = []
    for n in range(modes):
        k = (n+.5)*math.pi
        alpha = math.sqrt(1+.4**2*k**2)/.4
        terms.append(.2/(2*.4**2*alpha*math.tanh(alpha*.2))*(2/k)**2)
    assert lower[0, 0] == pytest.approx(math.fsum(terms), rel=1e-12, abs=1e-13)
    assert upper[0, 0]-lower[0, 0] == pytest.approx(info['tail_coefficient'], rel=1e-9, abs=1e-14)
    assert info['limits'] == dict(cells=1024, modes=16384, columns=160, chunk_rows=256)


@pytest.mark.parametrize('projection', (np.zeros((4, 2)), np.ones((4, 2)),
                                       np.array(((1., 2.), (-1., -2.), (0., 0.), (3., 6.)))))
def test_rank_deficient_force_actions_have_valid_bracket_without_nan(projection):
    lower, upper, info = projected_modal_bracket(np.linspace(0., 1., 5), projection, 1., .2, .4, 256)
    assert np.isfinite(lower).all() and np.isfinite(upper).all()
    assert linalg.eigvalsh(upper-lower)[0] > -1e-12
    assert info['relative_loewner_tail_bound'] is None
    assert info['relative_diagnostic_status'] == 'rank_deficient_projection'
    assert np.isfinite(info['lower_min_eigenvalue'])


def test_column_limit_and_rank_deficient_wide_force_action():
    lower, upper, info = projected_modal_bracket(
        np.linspace(0., 1., 5), np.zeros((4, 160)), 1., .2, .4, 256)
    assert lower.shape == upper.shape == (160, 160)
    assert not lower.any() and not upper.any()
    assert info['projection_numerical_rank'] == 0
    assert info['relative_loewner_tail_bound'] is None
    assert info['output_gram_shape'] == [160, 160]


def test_owned_inputs_and_outputs():
    knots = np.linspace(0., 1., 5)
    projection = np.arange(8., dtype=float).reshape(4, 2)
    knots_before, projection_before = knots.copy(), projection.copy()
    knots.flags.writeable = projection.flags.writeable = False
    lower, upper, info = projected_modal_bracket(knots, projection, 1., .2, .4, 256)
    np.testing.assert_array_equal(knots, knots_before)
    np.testing.assert_array_equal(projection, projection_before)
    assert not np.shares_memory(lower, projection) and not np.shares_memory(upper, projection)
    assert not np.shares_memory(lower, upper)
    lower_before = lower.copy()
    knots.flags.writeable = projection.flags.writeable = True
    knots[:] = 7.
    projection[:] = 9.
    np.testing.assert_array_equal(lower, lower_before)
    lower[:] = -1.
    assert np.isfinite(upper).all()
    assert info['source_equation']['symbol'] == 'p0_shell_bracket'


@pytest.mark.parametrize('field,value', (
    ('knots', [0., .5, .5, 1.]), ('knots', [0., .5, .9]),
    ('knots', [0., float('nan'), 1.]), ('knots', [[0., 1.]]),
    ('knots', np.linspace(0., 1., 1026)), ('knots', [0., .5+1j, 1.]),
    ('projection', np.ones((3, 1))), ('projection', np.ones(4)),
    ('projection', np.ones((4, 0))), ('projection', np.ones((4, 161))),
    ('projection', np.full((4, 1), np.inf)), ('projection', np.ones((4, 1))*1j),
    ('length', 0.), ('width', -1.), ('ell', np.inf), ('ell', True),
    ('modes', 3), ('modes', 16385), ('modes', 256.), ('modes', True),
))
def test_invalid_inputs_are_rejected(field, value):
    args = dict(knots=np.linspace(0., 1., 5), projection=np.ones((4, 1)),
                length=1., width=.2, ell=.4, modes=256)
    args[field] = value
    with pytest.raises(ValueError):
        projected_modal_bracket(**args)
