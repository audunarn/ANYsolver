"""Exact density and independent finite-pose controls; no product imports."""
from fractions import Fraction as Q
import math

import numpy as np
import pytest

from scripts import r8_bl5_density_subspace_dev as control


def basis(span, supports):
    rows = [[Q(0) for _ in range(5*2*supports)] for _ in range(5*16)]
    for channel in range(5):
        for cell in range(16):
            support = cell//span
            mean = Q(2*(cell % span)+1-span, span)
            rows[16*channel+cell][2*(channel*supports+support)] = Q(1)
            rows[16*channel+cell][2*(channel*supports+support)+1] = mean
    return rows


def test_exact_fraction_halfcell_basis_and_all_channel_dual_work():
    e = control.density_subspace_embedding().toarray()
    # Frozen actual trace row inventory, independently listed for first support.
    for coarse_row, left, right in ((0, 0, 2), (4, 8, 10), (8, 16, 18),
                                   (12, 24, 26), (16, 32, 34)):
        np.testing.assert_array_equal(np.flatnonzero(e[coarse_row]), (left, right))
        np.testing.assert_array_equal(e[coarse_row+1, [left, left+1, right, right+1]],
                                      (-.5, .5, .5, .5))
    ef = [[Q(float(x)) for x in row] for row in e]
    fine, coarse = basis(4, 4), basis(8, 2)
    for row in range(80):
        for column in range(20):
            assert sum(fine[row][k]*ef[column][k] for k in range(40)) == coarse[row][column]
    # Arbitrary signed rational coefficients and gaps, with every channel active.
    lam = [Q((-1)**j*(j+1), 7) for j in range(20)]
    gap = [Q((-1)**(j//3)*(j+2), 11) for j in range(40)]
    coarse_gap = [sum(ef[i][j]*gap[j] for j in range(40)) for i in range(20)]
    fine_dual = [sum(ef[i][j]*lam[i] for i in range(20)) for j in range(40)]
    assert sum(lam[i]*coarse_gap[i] for i in range(20)) == sum(fine_dual[j]*gap[j] for j in range(40))
    assert np.linalg.matrix_rank(e) == 20


@pytest.mark.parametrize('fine,coarse', ((True, 2), (4, False), (4., 2),
    (np.int64(4), 2), (4, 2.), (2, 1), (8, 4), (4, 4)))
def test_embedding_admission_is_exact_plain_fixed_transition(fine, coarse):
    with pytest.raises(ValueError, match='fixed support'):
        control.density_subspace_embedding(fine, coarse)


def test_embedding_owns_each_output():
    first = control.density_subspace_embedding()
    second = control.density_subspace_embedding()
    assert first.shape == (20, 40) and first.nnz == 60
    assert first.has_canonical_format
    first.data[:] = 0.
    first.indices[:] = 0
    assert np.count_nonzero(second.data) == 60 and second.has_canonical_format


def rotate(vector, rotation):
    # Independent Rodrigues vector formula, rather than the helper's skew map.
    theta = math.sqrt(float(np.dot(rotation, rotation)))
    if theta == 0.:
        return vector.copy()
    axis = rotation/theta
    return (vector*math.cos(theta)+np.cross(axis, vector)*math.sin(theta)+
            axis*np.dot(axis, vector)*(1.-math.cos(theta)))


def actual_gap(q, alpha, thickness, director, basis_rows, arm, lift, weight):
    shell = q[:12].reshape(2, 6)
    directors = [rotate(director, row[3:]) for row in shell]
    mean = (1.-alpha)*directors[0]+alpha*directors[1]
    shell_director = mean/np.linalg.norm(mean)
    top = sum(n*(row[:3]+.5*thickness*(di-director))
              for n, row, di in zip((1.-alpha, alpha), shell, directors))
    beam_origin_delta = ((1.-weight)*q[12:15]+weight*q[15:18]+
                         rotate(lift, q[18:])-lift)
    relative = arm+top-beam_origin_delta
    translation = rotate(relative, -q[18:])-arm
    director_change = rotate(shell_director, -q[18:])-director
    return np.r_[translation, basis_rows@director_change]


def args(alpha=.3, weight=.6, arm=None, lift=None):
    return dict(shell_alpha=alpha, t=.035, reference_director=np.array((0., 0., 1.)),
        director_basis=np.array(((1., 0., 0.), (0., 1., 0.))),
        reference_arm=np.array((0., 0., -.05)) if arm is None else arm,
        port_lift=np.zeros(3) if lift is None else lift, w=weight)


@pytest.mark.parametrize('alpha,weight', ((0., 0.), (.2113248654, .0528312163), (.3, .6), (1., 1.)))
def test_actual_rodrigues_reference_derivative(alpha, weight):
    parameters = args(alpha, weight, np.array((.02, -.03, -.05)), np.array((.01, .02, 0.)))
    j = control.flat_reference_jacobian(**parameters)
    h = 2e-6
    independent = np.column_stack([(actual_gap(h*e, alpha, parameters['t'],
        parameters['reference_director'], parameters['director_basis'],
        parameters['reference_arm'], parameters['port_lift'], weight)-
        actual_gap(-h*e, alpha, parameters['t'], parameters['reference_director'],
        parameters['director_basis'], parameters['reference_arm'],
        parameters['port_lift'], weight))/(2*h) for e in np.eye(21)])
    np.testing.assert_allclose(j, independent, rtol=0., atol=3e-11)


def test_common_rigid_motion_and_arm_work_sign():
    p = args(alpha=.4, weight=.25)
    j = control.flat_reference_jacobian(**p)
    shell_nodes = np.array(((0., 0., 0.), (1., 0., 0.)))
    shell_top = np.array((.4, 0., .5*p['t']))
    port_origin = shell_top-p['reference_arm']
    beam_nodes = np.array((port_origin-np.array((.25, 0., 0.)),
                           port_origin+np.array((.75, 0., 0.))))
    omega, translation = np.array((.1, -.2, .3)), np.array((.2, .1, -.05))
    q = np.r_[*[np.r_[translation+np.cross(omega, x), omega] for x in shell_nodes],
               *[translation+np.cross(omega, x) for x in beam_nodes], omega]
    np.testing.assert_allclose(j@q, 0., rtol=0., atol=2e-16)
    force = np.array((2., -3., 4.))
    torque = j[:3, 18:].T@force
    np.testing.assert_allclose(torque, np.cross(force, p['reference_arm']), atol=0., rtol=0.)
    direction = np.arange(21, dtype=float)/19.-.5
    multiplier = np.array((2., -3., 4., -5., 6.))
    h = 2e-6
    plus = actual_gap(h*direction, p['shell_alpha'], p['t'], p['reference_director'],
        p['director_basis'], p['reference_arm'], p['port_lift'], p['w'])
    minus = actual_gap(-h*direction, p['shell_alpha'], p['t'], p['reference_director'],
        p['director_basis'], p['reference_arm'], p['port_lift'], p['w'])
    assert abs(multiplier@(plus-minus)/(2*h)-(j.T@multiplier)@direction) < 2e-10


@pytest.mark.parametrize('key,value', (
    ('shell_alpha', -.1), ('shell_alpha', 1.1), ('shell_alpha', True), ('w', np.nan),
    ('w', 2.), ('t', 0.), ('t', -1.), ('t', np.inf),
    ('reference_director', (0., 1., 0.)), ('reference_director', (0., 0., 2.)),
    ('director_basis', ((0., 1., 0.), (1., 0., 0.))),
    ('director_basis', np.ones((3, 2))), ('reference_arm', (0., np.inf, 0.)),
    ('port_lift', (1., 2.)), ('port_lift', (0., 0., 1j)),
))
def test_local_malformed_or_nonfrozen_input_is_rejected(key, value):
    p = args()
    p[key] = value
    with pytest.raises(ValueError):
        control.flat_reference_jacobian(**p)


def test_local_input_and_result_ownership():
    p = args()
    originals = {key: value.copy() for key, value in p.items() if isinstance(value, np.ndarray)}
    for value in originals:
        p[value].flags.writeable = False
    j = control.flat_reference_jacobian(**p)
    before = j.copy()
    for key, value in originals.items():
        np.testing.assert_array_equal(p[key], value)
        p[key].flags.writeable = True
        p[key][:] = 13.
    np.testing.assert_array_equal(j, before)
    j[:] = 99.
    np.testing.assert_array_equal(control.flat_reference_jacobian(**args()), before)
