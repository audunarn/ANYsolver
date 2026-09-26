"""Independent cut-wrench checks for fixed-magnitude mixed B2 loading."""

from fractions import Fraction
import math

import numpy as np
import pytest

from anysolver._b2_physical_flexibility_linear import (
    ConditioningAdmissionError, LinearSection, _flexibility,
)
from anysolver._b2_physical_linear_definition import PhysicalB2Member


def _inverse(matrix):
    """Exact Gauss-Jordan inverse, independent of the operator's LDL route."""
    n = len(matrix)
    rows = [[Fraction(value) for value in row] +
            [Fraction(i == j) for j in range(n)]
            for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = rows[j][j]
        assert pivot > 0
        rows[j] = [value / pivot for value in rows[j]]
        for i in range(n):
            if i != j:
                multiplier = rows[i][j]
                rows[i] = [value - multiplier * other
                           for value, other in zip(rows[i], rows[j])]
    return [row[n:] for row in rows]


def _cut_map(remaining):
    # Tip wrench -> section wrench, in the rooted member's local frame.
    a = [[Fraction(i == j) for j in range(6)] for i in range(6)]
    a[4][2] = -remaining
    a[5][1] = remaining
    return a


def _tip_compliance_exact(length, stiffness):
    length = Fraction(float(length))
    compliance = _inverse(stiffness)
    result = [[Fraction(0) for _ in range(6)] for _ in range(6)]
    for weight, remaining in ((1, length), (4, length / 2), (1, Fraction(0))):
        a = _cut_map(remaining)
        for i in range(6):
            for j in range(6):
                result[i][j] += weight * sum(
                    a[k][i] * compliance[k][m] * a[m][j]
                    for k in range(6) for m in range(6)) * length / 6
    return result


def _tip_compliance(length, stiffness):
    return np.array([[float(value) for value in row]
                     for row in _tip_compliance_exact(length, stiffness)])


def _congruence(matrix, transform):
    n = len(matrix)
    return [[sum(transform[a][i] * matrix[a][b] * transform[b][j]
                 for a in range(n) for b in range(n))
             for j in range(n)] for i in range(n)]


def _ldl_pivot_ratios(matrix):
    """Exact normalized pivots, with no engineering admission decision."""
    n = len(matrix)
    lower = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    pivots = []
    for j in range(n):
        pivot = matrix[j][j] - sum(lower[j][k]**2 * pivots[k]
                                     for k in range(j))
        assert pivot > 0
        pivots.append(pivot)
        for i in range(j + 1, n):
            lower[i][j] = (matrix[i][j] - sum(
                lower[i][k] * pivots[k] * lower[j][k]
                for k in range(j))) / pivot
    return [pivot / matrix[i][i] for i, pivot in enumerate(pivots)]


def _member(points, local_y, section):
    return PhysicalB2Member("fixed-wrench", "fixed-wrench-source", (1, 2),
                            points, local_y, "fixed-wrench-section", section)


@pytest.mark.parametrize("points,local_y", [
    (((0., 0., 0.), (2., 0., 0.)), (0., 1., 0.)),
    (((0., 0., 0.), (0., 2., 0.)), (-1., 0., 0.)),
    (((2., 0., 0.), (0., 0., 0.)), (0., 1., 0.)),
])
@pytest.mark.parametrize("generalized,weak_exponent", [
    (False, 16), (False, 40), (True, 16),
])
def test_fixed_mixed_tip_wrench_matches_independent_cut_energy(points, local_y,
                                                                generalized,
                                                                weak_exponent):
    if generalized:
        stiffness = np.diag([12., 2.**-weak_exponent,
                             2.**(1 - weak_exponent), 4., 3., 5.])
        stiffness[0, 4] = stiffness[4, 0] = .5
        stiffness[1, 2] = stiffness[2, 1] = 2.**(-weak_exponent - 2)
        stiffness[3, 5] = stiffness[5, 3] = .25
        section = LinearSection.generalized(stiffness)
    else:
        section = LinearSection.isotropic(E=12., nu=.25, area=2.**-weak_exponent,
                                          Iy=.25, Iz=.4, J=.5, ky=.8, kz=.6)
        stiffness = np.asarray(section.stiffness)

    member = _member(points, local_y, section)
    # Forces stay order one as shear stiffness falls; moments remain present.
    local_wrench = np.array([.7, -.8, .5, .2, -.3, .4])
    expected_tip = _tip_compliance(member.length_m, stiffness) @ local_wrench
    frame = member.local_frame_rows()
    transform = member.local_dof_map()
    global_tip = np.r_[frame.T @ expected_tip[:3], frame.T @ expected_tip[3:]]
    global_u = np.r_[np.zeros(6), global_tip]
    response = member.local_operator().evaluate(transform @ global_u)
    root_reaction = np.r_[-local_wrench[:3],
                          -local_wrench[3:] - np.cross(
                              [member.length_m, 0., 0.], local_wrench[:3])]

    np.testing.assert_allclose(response.force, np.r_[root_reaction, local_wrench],
                               rtol=3e-11, atol=1e-11)
    assert response.energy == pytest.approx(.5 * local_wrench @ expected_tip,
                                            rel=3e-11)
    for station, resultant in zip(response.stations, response.resultants):
        cut = _cut_map(Fraction(float(member.length_m)) *
                       (1 - Fraction(float(station))))
        expected_cut = np.array([float(sum(row[j] * Fraction(float(local_wrench[j]))
                                           for j in range(6))) for row in cut])
        np.testing.assert_allclose(resultant, expected_cut, rtol=3e-11, atol=1e-11)


def test_generalized_very_weak_shear_has_explicit_provisional_admission_limit():
    stiffness = np.diag([12., 2.**-40, 2.**-39, 4., 3., 5.])
    stiffness[0, 4] = stiffness[4, 0] = .5
    stiffness[1, 2] = stiffness[2, 1] = 2.**-42
    stiffness[3, 5] = stiffness[5, 3] = .25
    member = _member(((0., 0., 0.), (2., 0., 0.)), (0., 1., 0.),
                     LinearSection.generalized(stiffness))
    wrench = np.array([.7, -.8, .5, .2, -.3, .4])
    tip = _tip_compliance(member.length_m, stiffness) @ wrench
    assert np.isfinite(tip).all() and np.max(np.abs(tip)) > 1e10
    assert .5 * wrench @ tip > 0
    with pytest.raises(ConditioningAdmissionError, match="ill-conditioned"):
        member.local_operator()


def test_weak_generalized_pivot_screen_depends_on_bending_wrench_basis():
    stiffness = np.diag([12., 2.**-40, 2.**-39, 4., 3., 5.])
    stiffness[0, 4] = stiffness[4, 0] = .5
    stiffness[1, 2] = stiffness[2, 1] = 2.**-42
    stiffness[3, 5] = stiffness[5, 3] = .25
    length = Fraction(2)  # m; force and moment reference scales are 1 N and 2 N m.
    tip = _tip_compliance_exact(length, stiffness)

    # Original basic q=(N,T,My_left,My_right,Mz_left,Mz_right).
    # R maps q to the physical tip wrench (N,Vy,Vz,T,My,Mz).
    r = [[Fraction(0) for _ in range(6)] for _ in range(6)]
    for row, col in ((0, 0), (3, 1), (4, 3), (5, 5)):
        r[row][col] = 1
    r[1][4] = r[1][5] = -1 / length
    r[2][2] = r[2][3] = 1 / length
    original = _congruence(tip, r)
    assert original == _flexibility(length, _inverse(stiffness))

    # p=(N,T,Vz,My_at_midspan,Vy,Mz_at_midspan) separates each
    # force-like shear mode from its moment-like bending mode.
    # Columns are scaled by 1 N for forces and 2 N m for moments.
    change = [[Fraction(0) for _ in range(6)] for _ in range(6)]
    change[0][0], change[1][1] = 1, length
    change[2][2], change[3][2] = length / 2, length / 2
    change[2][3], change[3][3] = -length, length
    change[4][4], change[5][4] = -length / 2, -length / 2
    change[4][5], change[5][5] = -length, length
    separated = _congruence(original, change)

    assert min(_ldl_pivot_ratios(original)) < Fraction(1, 10**12)
    assert min(_ldl_pivot_ratios(separated)) > Fraction(1, 100)
    wrench = [Fraction(float(value)) for value in (.7, -.8, .5, .2, -.3, .4)]
    displacement = [sum(tip[i][j] * wrench[j] for j in range(6))
                    for i in range(6)]
    assert all(math.isfinite(float(value)) and
               (value == 0 or float(value) != 0) for value in displacement)
    assert all(math.isfinite(float(value)) and
               (value == 0 or float(value) != 0)
               for row in _inverse(separated) for value in row)
