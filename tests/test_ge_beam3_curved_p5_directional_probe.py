"""Directional action development checks; Decimal oracle shares metric inputs."""

from decimal import Decimal, localcontext
from dataclasses import replace
import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES, metrics, rotation
from docs.reference_cases.ge_beam3_curved_p5_factor_probe import constant_spatial_moment_mode
from docs.reference_cases.ge_beam3_curved_p5_directional_probe import DirectionalResponseProbe, accurate_products
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import LocalStationarityError
from test_ge_beam3_curved_p5_algebra_probe import reference, section, perturbed, assert_scaled_close
from test_ge_beam3_curved_p5_flexibility_probe import decimal_matrix, transpose, multiply, add, solve


def decimal_stationary_action(ref, elastic, displacement):
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
        action = [[Decimal(0)] for _ in range(18)]
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
            moments = solve(h, moment_strain)
            force = add(multiply(f, force_strain), multiply(transpose(j), moments))
            left_moment = multiply(frames[left], moments[:3])
            right_moment = multiply(frames[right], moments[3:])
            for i in range(3):
                action[left*6+i][0] -= force[i][0]
                action[right*6+i][0] += force[i][0]
                action[left*6+3+i][0] -= left_moment[i][0]
                action[right*6+3+i][0] += right_moment[i][0]
        return float(total), np.array([float(row[0]) for row in action])


@pytest.mark.parametrize("geometry", [(0., 0., 0.), (.4, 0., 0.), (.6, .2, .15)])
@pytest.mark.parametrize("rho", [1., 100., 10000., 1000000.])
def test_small_mode_energy_and_force_action_match_80_digit_original_system(geometry, rho):
    ref = reference(*geometry)
    elastic = np.diag([rho*rho]*3+[1., 2., 3.])
    direction, _, manufactured = constant_spatial_moment_mode(ref, elastic, [.3, -.4, 1.])
    model = DirectionalResponseProbe(ref, elastic, ref.coordinates, ref.nodal_triads)
    response = model.evaluate()
    made = model.tangent_action(response, direction)
    energy, action = decimal_stationary_action(ref, elastic, direction)
    assert abs(made.directional_stiffness/2-energy) <= 1e-11*abs(energy)
    assert abs(made.directional_stiffness/2-manufactured) <= 1e-11*abs(manufactured)
    assert_scaled_close(made.action, action)
    assert_scaled_close(direction @ made.action, made.directional_stiffness)


@pytest.mark.parametrize("rho", [1., 1000000.])
def test_coupled_reference_arbitrary_action_matches_decimal(rho):
    ref = reference(.6, .2, .15)
    scaling = np.diag([rho]*3+[1.]*3)
    elastic = scaling @ section() @ scaling
    direction = np.cos(np.arange(18)+.3)/7
    model = DirectionalResponseProbe(ref, elastic, ref.coordinates, ref.nodal_triads)
    made = model.tangent_action(model.evaluate(), direction)
    energy, action = decimal_stationary_action(ref, elastic, direction)
    assert abs(made.directional_stiffness/2-energy) <= 1e-11*abs(energy)
    assert_scaled_close(made.action, action)


@pytest.mark.parametrize("nonzero_chart", [False, True])
def test_finite_action_matches_directional_residual_and_same_chart_dense_operator(nonzero_chart):
    ref = reference(.4, .1, .15)
    x, q, _ = perturbed(ref)
    model = DirectionalResponseProbe(ref, section(), x, q, line_force=[.1, -.2, .3])
    chart = .2*np.sin(np.arange(18)+.2) if nonzero_chart else np.zeros(18)
    response = model.evaluate(increment=chart)
    direction = np.cos(np.arange(18)+.7)/5
    made = model.tangent_action(response, direction)
    assert_scaled_close(made.action, response.tangent @ direction)
    assert_scaled_close(made.directional_stiffness, direction @ response.tangent @ direction)
    step = 2e-5
    plus = model.evaluate(increment=chart+step*direction)
    minus = model.evaluate(increment=chart-step*direction)
    assert_scaled_close(made.action, (plus.residual-minus.residual)/(2*step), 1e-7)


def test_finite_action_linearity_reciprocity_and_zero_direction():
    ref = reference(.6, .2, .15)
    x, q, _ = perturbed(ref)
    model = DirectionalResponseProbe(ref, section(), x, q)
    response = model.evaluate()
    a, b = np.sin(np.arange(18))/7, np.cos(np.arange(18)+.1)/9
    fa, fb = model.tangent_action(response, a), model.tangent_action(response, b)
    combined = model.tangent_action(response, 2*a-3*b)
    assert_scaled_close(combined.action, 2*fa.action-3*fb.action)
    assert_scaled_close(a @ fb.action, b @ fa.action)
    zero = model.tangent_action(response, np.zeros(18))
    assert np.array_equal(zero.action, np.zeros(18))
    assert zero.directional_stiffness == 0


def test_high_contrast_rotated_reference_and_input_direction_match_decimal():
    ref = reference(.6, .2, .15)
    g = rotation([.6, -.8, 1.1])
    elastic = np.diag([1e12]*3+[1., 2., 3.])
    direction, _, _ = constant_spatial_moment_mode(ref, elastic, [.3, -.4, 1.])
    nodal = direction.reshape(3, 6)
    rotated = nodal.copy()
    rotated[:, :3] = nodal[:, :3] @ g.T
    rotated[:, 3:] = nodal[:, 3:] @ g.T
    ref = ref.rigidly_transformed(g, np.array([3., -2., 1.]))
    model = DirectionalResponseProbe(ref, elastic, ref.coordinates, ref.nodal_triads)
    made = model.tangent_action(model.evaluate(), rotated.ravel())
    expected_energy, expected_action = decimal_stationary_action(ref, elastic, rotated.ravel())
    assert_scaled_close(made.action, expected_action)
    assert_scaled_close(made.directional_stiffness/2, expected_energy)


def test_compensated_products_preserve_roundoff_remainders_and_reject_bad_input():
    # Exact binary64 inputs; the rounded leading products cancel to zero,
    # while the real product sum is nonzero. The 80-digit result is decisive.
    coefficients = [1.+2**-27, -1.]
    values = [1.-2**-27, 1.]
    with localcontext() as context:
        context.prec = 80
        expected = float(sum(Decimal.from_float(a)*Decimal.from_float(b)
                             for a, b in zip(coefficients, values)))
    assert accurate_products(coefficients, values) == expected == -(2**-54)
    with pytest.raises(ValueError, match="lengths"):
        accurate_products([1.], [])
    with pytest.raises(ValueError, match="nonfinite"):
        accurate_products([1e308], [1e308])


def test_directional_state_binding_seed_validation_and_repeatability(monkeypatch):
    ref = reference()
    x, q, _ = perturbed(ref)
    model = DirectionalResponseProbe(ref, section(), x, q)
    response = model.evaluate()
    direction = np.linspace(-.3, .4, 18)
    first, second = model.tangent_action(response, direction), model.tangent_action(response, direction)
    assert np.array_equal(first.action, second.action)
    assert first.directional_stiffness == second.directional_stiffness
    assert not first.action.flags.writeable
    changed = response.parameters.copy()
    changed[0] += .001
    with pytest.raises(ValueError, match="fingerprint"):
        model.tangent_action(replace(response, parameters=changed), direction)
    changed_rotations = response.rotations.copy()
    changed_rotations[0, 0, 0] += .001
    with pytest.raises(ValueError, match="rotations mismatch"):
        model.tangent_action(replace(response, rotations=changed_rotations), direction)
    for bad in (np.zeros(17), np.full(18, np.nan)):
        with pytest.raises(ValueError, match="direction"):
            model.tangent_action(response, bad)
    for bad in (np.zeros((17, 2)), np.zeros((18, 0)), np.zeros((18, 20)), np.full((18, 1), np.nan)):
        with pytest.raises(ValueError, match="seed"):
            model._functional(response.parameters, external=True, directions=bad)
    original_solve = np.linalg.solve
    def broken_local_solve(matrix, rhs):
        return np.full_like(rhs, np.nan) if matrix.shape == (6, 6) else original_solve(matrix, rhs)
    monkeypatch.setattr(np.linalg, "solve", broken_local_solve)
    with pytest.raises(LocalStationarityError, match="nonfinite"):
        model.tangent_action(response, direction)
