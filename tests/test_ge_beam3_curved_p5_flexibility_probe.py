"""Reference-only diagnostic tests; Decimal reconstruction shares metric inputs.

The 80-digit check below reconstructs the original primal stationary system,
not the flexibility algorithm. It is an alternative arithmetic/algebra check,
NOT independently authored formulation or quadrature qualification.
"""

from decimal import Decimal, localcontext

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import (
    HALVES, T6, metrics, reference_hessians, rotation,
)
from docs.reference_cases.ge_beam3_curved_p5_factor_probe import constant_spatial_moment_mode
from docs.reference_cases.ge_beam3_curved_p5_flexibility_probe import reference_flexibility
from test_ge_beam3_curved_p5_algebra_probe import assert_scaled_close, reference, section


def decimal_matrix(value):
    return [[Decimal.from_float(float(item)) for item in row] for row in value]


def transpose(value):
    return list(map(list, zip(*value)))


def multiply(left, right):
    return [[sum((x*y for x, y in zip(row, column)), Decimal(0))
             for column in transpose(right)] for row in left]


def add(left, right):
    return [[x+y for x, y in zip(a, b)] for a, b in zip(left, right)]


def solve(matrix, rhs):
    """Decimal Gaussian elimination with deterministic partial pivoting."""
    size = len(matrix)
    rows = [list(a)+list(b) for a, b in zip(matrix, rhs)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(rows[row][column]))
        if rows[pivot][column] == 0:
            raise ValueError("singular Decimal system")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [x/divisor for x in rows[column]]
        for row in range(size):
            if row != column:
                factor = rows[row][column]
                rows[row] = [x-factor*y for x, y in zip(rows[row], rows[column])]
    return [row[size:] for row in rows]


def decimal_stationary_energy(ref, elastic, displacement):
    """Original z/ell potential and three local rotations per half, at 80 digits.

    Every supplied binary64 coordinate, frame, metric and displacement is
    converted exactly to Decimal. No rounded assembled stiffness is imported.
    The residual and local Hessian are assembled independently below.
    """
    with localcontext() as context:
        context.prec = 80
        coordinates = decimal_matrix(ref.coordinates)
        frames = [decimal_matrix(frame) for frame in ref.nodal_triads]
        nodal = decimal_matrix(np.asarray(displacement).reshape(3, 6))
        total = Decimal(0)
        for cell, (left, right) in enumerate(HALVES):
            data = metrics(ref, elastic, cell)
            f, h, j = map(decimal_matrix, (data.force, data.compliance, data.coupling))
            x, y, z = [b-a for a, b in zip(coordinates[left], coordinates[right])]
            cross = [[Decimal(0), -z, y], [z, Decimal(0), -x], [-y, x, Decimal(0)]]
            relative = [[nodal[right][i]-nodal[left][i]] for i in range(3)]
            left_rotation = [[item] for item in nodal[left][3:]]
            right_rotation = [[item] for item in nodal[right][3:]]
            lt, rt = transpose(frames[left]), transpose(frames[right])
            ell = [[-row[0]] for row in multiply(lt, left_rotation)] + multiply(rt, right_rotation)
            local_ell = lt + [[-item for item in row] for row in rt]
            e0 = add(multiply(j, relative), ell)
            derivative = add(multiply(j, cross), local_ell)
            local_hessian = add(multiply(transpose(cross), multiply(f, cross)),
                                multiply(transpose(derivative), solve(h, derivative)))
            gradient = add(multiply(transpose(cross), multiply(f, relative)),
                           multiply(transpose(derivative), solve(h, e0)))
            local = solve(local_hessian, [[-row[0]] for row in gradient])
            force_strain = add(relative, multiply(cross, local))
            moment_strain = add(e0, multiply(derivative, local))
            total += (multiply(transpose(force_strain), multiply(f, force_strain))[0][0]
                      + multiply(transpose(moment_strain), solve(h, moment_strain))[0][0])/2
        return float(total)


@pytest.mark.parametrize("geometry", [(0., 0., 0.), (.4, 0., 0.), (.6, .2, .15)])
@pytest.mark.parametrize("rho", [1., 100., 10000., 1000000.])
def test_equilibrated_energy_matches_moment_mode_and_80_digit_original_system(geometry, rho):
    ref = reference(*geometry)
    elastic = np.diag([rho*rho]*3+[1., 2., 3.])
    q, _, expected = constant_spatial_moment_mode(ref, elastic, [.3, -.4, 1.])
    actual = reference_flexibility(ref, elastic).energy(q)
    assert abs(actual-expected) <= 1e-11*abs(expected)
    checked = decimal_stationary_energy(ref, elastic, q)
    assert abs(actual-checked) <= 1e-11*abs(checked)


@pytest.mark.parametrize("rho", [1., 1000000.])
def test_coupled_section_arbitrary_and_small_response_matches_decimal(rho):
    ref = reference(.6, .2, .15)
    scaling = np.diag([rho]*3+[1.]*3)
    elastic = scaling @ section() @ scaling
    q = np.linspace(-.4, .3, 18)
    for amplitude in (1., 1e-6):
        actual = reference_flexibility(ref, elastic).energy(amplitude*q)
        expected = decimal_stationary_energy(ref, elastic, amplitude*q)
        assert abs(actual-expected) <= 1e-11*abs(expected)


def test_moderate_dense_operator_equivalence_and_rigid_energy():
    ref = reference(.6, .2, .15)
    elastic = section()
    flexibility = reference_flexibility(ref, elastic)
    expected = reference_hessians(ref, elastic)[2]
    # Construct a diagnostic Hessian via the linear work map, not differentiation.
    made = np.zeros((18, 18))
    unit = np.eye(18).reshape(18, 3, 6)
    for cell, (left, right) in zip(flexibility.cells, HALVES):
        work = np.column_stack([cell.deformation(row[left], row[right]) for row in unit])
        force = np.column_stack([cell.stresses(work[:, column]) for column in range(18)])
        made += work.T @ force
    assert_scaled_close(made, expected)
    translation = np.array([2., -1., .3])
    omega = np.array([.2, -.3, .4])
    q = np.zeros((3, 6))
    q[:, :3] = translation + np.cross(omega, ref.coordinates)
    q[:, 3:] = omega
    assert flexibility.energy(q.ravel()) < 1e-25


def test_high_contrast_moment_recovery_and_covariance_reversal():
    ref = reference(.6, .2, .15)
    elastic = np.diag([1e12]*3+[1., 2., 3.])
    moment = np.array([.3, -.4, 1.])
    q, _, expected = constant_spatial_moment_mode(ref, elastic, moment)
    nodal = q.reshape(3, 6)
    original = reference_flexibility(ref, elastic)
    # Only moment recovery is checked here. Axial force on rounded low-energy
    # nodal data is itself conditioning-sensitive and is not silently zeroed.
    for cell, (left, right) in zip(original.cells, HALVES):
        stress = cell.stresses(cell.deformation(nodal[left], nodal[right]))
        assert_scaled_close(cell.basis @ stress[3:], moment)
    transform = rotation((.6, -.8, 1.1))
    moved = ref.rigidly_transformed(transform, np.array([3., -2., 1.]))
    rotated = nodal.copy()
    rotated[:, :3] = nodal[:, :3] @ transform.T
    rotated[:, 3:] = nodal[:, 3:] @ transform.T
    assert_scaled_close(reference_flexibility(moved, elastic).energy(rotated.ravel()), expected)
    assert_scaled_close(reference_flexibility(ref.reversed(), T6 @ elastic @ T6.T).energy(
        nodal[::-1].ravel()), expected)


def test_invalid_inputs_and_repeatability():
    ref = reference()
    a, b = reference_flexibility(ref, section()), reference_flexibility(ref, section())
    for left, right in zip(a.cells, b.cells):
        for field in ("basis", "cholesky", "scale", "moment_map"):
            assert np.array_equal(getattr(left, field), getattr(right, field))
            assert not getattr(left, field).flags.writeable
    for bad in (np.zeros(17), np.full(18, np.nan), np.zeros((3, 6))):
        with pytest.raises(ValueError, match="18-component"):
            a.energy(bad)
