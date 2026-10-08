"""Uniform-tail equations and fallback controls; no acceptance campaign."""
from fractions import Fraction

import numpy as np
import pytest
from scipy import linalg

from scripts.r8_bl5_projected_modal_envelope_dev import projected_modal_bracket
from scripts.r8_bl5_projected_uniform_modal_dev import projected_uniform_modal_bracket


@pytest.mark.parametrize('count', (1, 2, 7, 16))
@pytest.mark.parametrize('start', (0, 1, 11, 123))
def test_complete_cosine_gram_identity_at_arbitrary_block_start(count, start):
    modes = np.arange(start, start+2*count)
    vectors = np.cos((modes[:, None]+.5)*np.pi*np.arange(count)[None, :]/count)
    expected = count*np.eye(count)
    expected[0, 0] = 2*count
    np.testing.assert_allclose(vectors.T@vectors, expected, rtol=1e-12, atol=1e-10)


def _omitted_gram(knots, projection, start, stop, length=1., width=.2, ell=.4):
    out = np.zeros((projection.shape[1], projection.shape[1]))
    for first in range(start, stop, 128):
        n = np.arange(first, min(first+128, stop))
        k = (n+.5)*np.pi/length
        alpha = np.sqrt(1+ell**2*k**2)/ell
        integral = 2/(length*k[:, None])*(
            np.cos(k[:, None]*knots[:-1])-np.cos(k[:, None]*knots[1:]))
        coefficients = integral@projection
        weight = length**2*width/(2*ell**2*alpha*np.tanh(alpha*width))
        out += coefficients.T@(weight[:, None]*coefficients)
    return out


@pytest.mark.parametrize('count,modes', ((8, 31), (32, 137), (256, 4096)))
def test_finite_omitted_sums_are_bounded_with_signed_density_and_unaligned_start(count, modes):
    knots = np.linspace(0., 1., count+1)
    projection = np.column_stack((np.ones(count), np.linspace(-1., 1., count),
                                  (-1.)**np.arange(count)))
    lower, upper, info = projected_uniform_modal_bracket(knots, projection, 1., .2, .4, modes)
    old_lower, old_upper, old_info = projected_modal_bracket(knots, projection, 1., .2, .4, modes)
    np.testing.assert_array_equal(lower, old_lower)
    omitted = _omitted_gram(knots, projection, modes, modes+4096)
    assert linalg.eigvalsh(upper-lower-omitted)[0] > -1e-12
    first = modes+.5
    ratio = (4+first/count)/(2+first)
    assert linalg.eigvalsh(ratio*(old_upper-old_lower)-(upper-lower))[0] > -1e-12
    assert info['exact_uniform_stored_knots']
    assert info['cosine_period_modes'] == 2*count
    expected_relative = linalg.eigvalsh(upper-lower, lower)[-1]
    assert info['relative_loewner_tail_bound'] == pytest.approx(expected_relative, rel=1e-10, abs=1e-12)
    assert info['relative_loewner_tail_bound'] <= ratio*old_info['relative_loewner_tail_bound']+1e-12


@pytest.mark.parametrize('projection', (np.zeros((16, 3)), np.ones((16, 2)),
    np.column_stack((np.arange(16.), -2*np.arange(16.)))))
def test_zero_and_duplicate_signed_actions_need_no_full_rank(projection):
    lower, upper, info = projected_uniform_modal_bracket(np.linspace(0., 1., 17), projection, 1., .2, .4, 256)
    assert np.isfinite(lower).all() and np.isfinite(upper).all()
    assert linalg.eigvalsh(upper-lower)[0] > -1e-12
    assert info['relative_loewner_tail_bound'] is None
    assert info['relative_diagnostic_status'] == 'rank_deficient_projection'
    if not projection.any():
        assert not lower.any() and not upper.any()


def test_mixed_basis_and_reciprocal_density_units_preserve_complete_bracket():
    knots = np.linspace(0., 1., 33)
    p = np.column_stack((np.ones(32), np.linspace(-2., 3., 32), np.cos(np.arange(32))))
    lower, upper, info = projected_uniform_modal_bracket(knots, p, 1., .2, .4, 512)
    change = np.array(((2., -1., .3), (0., -.5, 2.), (.7, 0., 1.)))
    mixed_lower, mixed_upper, _ = projected_uniform_modal_bracket(knots, p@change, 1., .2, .4, 512)
    np.testing.assert_allclose(mixed_lower, change.T@lower@change, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(mixed_upper, change.T@upper@change, rtol=1e-12, atol=1e-12)
    scaled_lower, scaled_upper, scaled_info = projected_uniform_modal_bracket(
        1000*knots, p/1000, 1000., 200., 400., 512)
    np.testing.assert_allclose(scaled_lower, lower, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(scaled_upper, upper, rtol=1e-12, atol=1e-12)
    assert info['exact_uniform_stored_knots'] and scaled_info['exact_uniform_stored_knots']


@pytest.mark.parametrize('knots', (np.array((0., .07, .21, .49, .76, 1.)),
    np.array((0., .25, .5+2**-45, .75, 1.)), np.linspace(0., 1., 8)))
def test_nonuniform_or_rounded_uniform_knots_retain_exact_original_fallback(knots):
    count = len(knots)-1
    p = np.column_stack((np.ones(count), np.linspace(-1., 1., count)))
    lower, upper, info = projected_uniform_modal_bracket(knots, p, 1., .2, .4, 256)
    original_lower, original_upper, original_info = projected_modal_bracket(knots, p, 1., .2, .4, 256)
    np.testing.assert_array_equal(lower, original_lower)
    np.testing.assert_array_equal(upper, original_upper)
    assert not info['exact_uniform_stored_knots']
    assert info['tail_method'] == 'ORIGINAL_PROJECTED_CAUCHY_FALLBACK'
    assert info['relative_loewner_tail_bound'] == original_info['relative_loewner_tail_bound']
    assert any(Fraction.from_float(float(x))*count != Fraction(j) for j, x in enumerate(knots))


def test_owned_readonly_inputs_and_separate_outputs():
    knots, p = np.linspace(0., 1., 9), np.arange(16.).reshape(8, 2)
    original_knots, original_p = knots.copy(), p.copy()
    knots.flags.writeable = p.flags.writeable = False
    lower, upper, info = projected_uniform_modal_bracket(knots, p, 1., .2, .4, 256)
    np.testing.assert_array_equal(knots, original_knots)
    np.testing.assert_array_equal(p, original_p)
    assert not np.shares_memory(lower, upper)
    assert not np.shares_memory(lower, p) and not np.shares_memory(upper, knots)
    saved_upper = upper.copy()
    knots.flags.writeable = p.flags.writeable = True
    knots[:] = 42.
    p[:] = -1.
    lower[:] = 7.
    np.testing.assert_array_equal(upper, saved_upper)
    info['source_equation']['tail'] = 'caller mutation'
    _, _, fresh_info = projected_uniform_modal_bracket(original_knots, original_p, 1., .2, .4, 256)
    assert fresh_info['source_equation']['tail'] != 'caller mutation'


def test_original_caps_stay_admitted_without_widening():
    for count, columns, modes in ((1024, 1, 1024), (4, 160, 4), (1, 1, 16384)):
        lower, upper, info = projected_uniform_modal_bracket(
            np.linspace(0., 1., count+1), np.zeros((count, columns)), 1., .2, .4, modes)
        assert lower.shape == upper.shape == (columns, columns)
        assert info['limits'] == dict(cells=1024, modes=16384, columns=160, chunk_rows=256)
    # N=1 remains valid but the structured bound need not dominate the old one.
    _, _, info = projected_uniform_modal_bracket((0., 1.), ((1.,),), 1., .2, .4, 1)
    assert info['analytical_old_tail_domination_multiplier'] > 1.
    assert not info['analytical_old_tail_domination_certified']


@pytest.mark.parametrize('field,value', (
    ('knots', np.linspace(0., 1., 1026)), ('knots', (0., .5, .5, 1.)),
    ('knots', (0., .5+1j, 1.)), ('knots', (0., np.nan, 1.)),
    ('projection', np.zeros((4, 161))), ('projection', np.zeros((4, 0))),
    ('projection', np.zeros((3, 1))), ('projection', np.full((4, 1), np.inf)),
    ('modes', 16385), ('modes', 3), ('modes', True), ('modes', 256.),
    ('length', 0.), ('width', np.inf), ('ell', -.4),
))
def test_invalid_inputs_keep_original_validation(field, value):
    args = dict(knots=np.linspace(0., 1., 5), projection=np.ones((4, 1)),
                length=1., width=.2, ell=.4, modes=256)
    args[field] = value
    with pytest.raises(ValueError):
        projected_uniform_modal_bracket(**args)
