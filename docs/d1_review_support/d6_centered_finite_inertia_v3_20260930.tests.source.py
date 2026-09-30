"""New focused centered finite-inertia checks; no solver/contact qualification."""
from fractions import Fraction as F
import hashlib
import inspect
from pathlib import Path
import anysolver
import json
import numpy as np
import pytest

from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
from anysolver._ge_beam3_centered_finite_inertia import (
    evaluate_centered_finite_inertia as evaluate, PHYSICAL_DOFS, ALGEBRAIC_DOFS,
)
from anysolver._ge_beam3_p5_centered.mass import _CenteredRestInertia, current_rest_mass
from anysolver._ge_beam3_p5_coordinates.positions import _rounded_pair
from anysolver._native_rotation_state import rotation_exponential as exp


def fixture():
    parameters = np.array((-1., 0., 1.))
    nodes = np.array([[x, .3*(1-x*x), .15*(1-x*x)] for x in parameters])
    frames = []
    for x in parameters:
        first = np.array((1., -.6*x, -.3*x))
        first /= np.linalg.norm(first)
        second = np.array((0., 0., 1.))
        second -= first*(first @ second)
        second /= np.linalg.norm(second)
        frames.append(np.column_stack((first, second, np.cross(first, second))))
    ref = Reference(nodes, np.array(frames))
    # Physical spatial inertia: mass and shifted center-of-mass cross blocks.
    mass, center = 2.7, np.array((.035, -.025, .012))
    x, y, z = center
    skew = np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))
    offset_inertia = -mass*(skew @ skew)
    offset_inertia = np.triu(offset_inertia)+np.triu(offset_inertia, 1).T
    section = np.block([[mass*np.eye(3), -mass*skew],
                        [mass*skew, np.diag((.12, .17, .19))+offset_inertia]])
    cells = np.array((exp((.19, -.11, .08)), exp((-.13, .16, .07))))
    velocity = np.array((.31, -.12, .08, .02, -.03, .01,
                         -.17, .09, .13, -.01, .05, -.04,
                         .12, .21, -.07, .03, .02, -.02,
                         .43, -.31, .19, -.24, .38, .29))
    acceleration = np.linspace(-.16, .23, 24)
    return ref, section, ref.coordinates.copy(), np.zeros((3, 3)), cells, velocity, acceleration


def run(data=None, **changes):
    ref, section, high, low, cells, velocity, acceleration = fixture() if data is None else data
    values = dict(reference=ref, section_inertia=section, positions_high=high, positions_low=low,
                  cell_rotations=cells, velocity=velocity, acceleration=acceleration, order=8)
    values.update(changes)
    return evaluate(**values)


def relative(actual, expected):
    return float(np.linalg.norm(actual-expected)/max(1e-30, np.linalg.norm(expected)))


def record(record_property, name, value):
    record_property(name, json.dumps(value))


def test_zero_velocity_exact_parity_and_rest_guard(record_property):
    expected = Path(__file__).resolve().parents[1]/"src/anysolver/_ge_beam3_centered_finite_inertia.py"
    imported = Path(inspect.getsourcefile(evaluate)).resolve()
    assert imported == expected
    record(record_property, "effective_import_identity", dict(module=str(imported),
           sha256=hashlib.sha256(imported.read_bytes()).hexdigest(), anysolver=anysolver.__file__))
    data = fixture()
    ref, section, high, low, cells, _, _ = data
    response = run(data, velocity=np.zeros(24), acceleration=np.zeros(24))
    old = current_rest_mass(ref, section, 8, high, low, cells)
    assert np.array_equal(response.mass, old)
    assert response.kinetic_energy == 0.
    for value in (response.generalized_momentum, response.inertia, response.linear_momentum,
                  response.angular_momentum, response.linear_momentum_low, response.angular_momentum_low):
        assert np.count_nonzero(value) == 0
    with pytest.raises(ValueError, match="rest linearization only"):
        _CenteredRestInertia(ref, section, order=8).evaluate(high, cells, data[5], np.zeros(24))


def test_nonzero_finite_work_cross_inertia_and_acceleration(record_property):
    data = fixture()
    response = run(data)
    rest_speed = run(data, velocity=np.zeros(24))
    gyro = run(data, acceleration=np.zeros(24))
    diagonal = data[1].copy()
    diagonal[:3, 3:] = 0.
    diagonal[3:, :3] = 0.
    no_cross = run(data, section_inertia=diagonal)
    assert response.kinetic_energy > 0.
    assert np.linalg.norm(gyro.inertia) > 1e-4
    assert np.linalg.norm(response.inertia-rest_speed.inertia) > 1e-4
    assert np.linalg.norm(response.inertia-no_cross.inertia) > 1e-4
    assert relative(response.inertia-gyro.inertia, response.mass @ data[6]) < 2e-14
    assert relative(response.generalized_momentum, response.mass @ data[5]) < 2e-14
    assert np.min(np.linalg.eigvalsh(response.mass[np.ix_(PHYSICAL_DOFS, PHYSICAL_DOFS)])) > 0.
    record(record_property, "finite_work", dict(energy=response.kinetic_energy,
           gyro_norm=float(np.linalg.norm(gyro.inertia)),
           cross_inertia_force_difference=float(np.linalg.norm(response.inertia-no_cross.inertia)),
           velocity_derivative_nonsymmetry=float(np.linalg.norm(response.velocity_derivative-response.velocity_derivative.T))))


@pytest.mark.parametrize("step", (1e-5, 2e-6))
def test_velocity_directional_derivative(step, record_property):
    data = fixture()
    direction = np.sin(np.arange(24)+.4)
    direction /= np.linalg.norm(direction)
    response = run(data)
    plus = run(data, velocity=data[5]+step*direction)
    minus = run(data, velocity=data[5]-step*direction)
    fd = (plus.inertia-minus.inertia)/(2*step)
    error = relative(fd, response.velocity_derivative @ direction)
    record(record_property, "velocity_directional", dict(step=step, relative_error=error))
    assert error < 1e-5, (step, error)


@pytest.mark.parametrize("step", (1e-5, 2e-6))
def test_left_configuration_directional_derivative(step, record_property):
    data = fixture()
    direction = np.zeros(24)
    direction[18:] = np.array((.31, -.27, .16, -.22, .13, .29))
    response = run(data)
    plus = np.array([exp(step*d) @ u for d, u in zip(direction[18:].reshape(2, 3), data[4])])
    minus = np.array([exp(-step*d) @ u for d, u in zip(direction[18:].reshape(2, 3), data[4])])
    fd = (run(data, cell_rotations=plus).inertia-run(data, cell_rotations=minus).inertia)/(2*step)
    error = relative(fd, response.configuration_derivative @ direction)
    record(record_property, "configuration_directional", dict(step=step, relative_error=error))
    assert error < 1e-5, (step, error)


def test_acceleration_directional_mass(record_property):
    data = fixture()
    direction = np.cos(np.arange(24)*.7)
    direction /= np.linalg.norm(direction)
    h = 3e-6
    response = run(data)
    fd = (run(data, acceleration=data[6]+h*direction).inertia
          -run(data, acceleration=data[6]-h*direction).inertia)/(2*h)
    error = relative(fd, response.mass @ direction)
    record(record_property, "acceleration_directional", dict(step=h, relative_error=error))
    assert error < 1e-7


def shift_pairs(high, low, translation):
    out_high, out_low = np.empty_like(high), np.empty_like(low)
    for index in np.ndindex(high.shape):
        axis = index[-1]
        out_high[index], out_low[index] = _rounded_pair(
            F(float(high[index]))+F(float(low[index]))+F(float(translation[axis])))
    return out_high, out_low


def moment_fraction(high, low):
    return [F(float(h))+F(float(l)) for h, l in zip(high, low)]


def cross_fraction(first, second):
    return (first[1]*second[2]-first[2]*second[1],
            first[2]*second[0]-first[0]*second[2],
            first[0]*second[1]-first[1]*second[0])


def test_compensated_momentum_large_translation_and_origin(record_property):
    data = fixture()
    small = np.array(((1e-9, -2e-9, 3e-9), (-4e-9, 2e-9, 1e-9), (2e-9, 5e-9, -3e-9)))
    high, low = np.empty((3, 3)), np.empty((3, 3))
    for index in np.ndindex(high.shape):
        high[index], low[index] = _rounded_pair(F(float(data[2][index]))+F(float(small[index])))
    translation = np.array((2.**40, -2.**40, 2.**41))
    shifted_high, shifted_low = shift_pairs(high, low, translation)
    origin = np.array((.07, -.12, .03))
    shifted_origin, shifted_origin_low = shift_pairs(origin, np.zeros(3), translation)
    base = run(data, positions_high=high, positions_low=low, momentum_origin_high=origin)
    shifted = run(data, positions_high=shifted_high, positions_low=shifted_low,
                  momentum_origin_high=shifted_origin, momentum_origin_low=shifted_origin_low)
    assert np.array_equal(base.mass, shifted.mass)
    assert np.array_equal(base.inertia, shifted.inertia)
    assert np.array_equal(base.linear_momentum, shifted.linear_momentum)
    assert np.linalg.norm(base.angular_momentum-shifted.angular_momentum) < 1e-13
    # Negative control: discarding valid lows materially damages origin-relative H.
    dropped = run(data, positions_high=shifted_high, positions_low=np.zeros((3, 3)),
                  momentum_origin_high=shifted_origin, momentum_origin_low=np.zeros(3))
    dropped_error = float(np.linalg.norm(dropped.angular_momentum-shifted.angular_momentum))
    assert dropped_error > 1e-7
    base_zero = run(data, positions_high=high, positions_low=low)
    shifted_zero = run(data, positions_high=shifted_high, positions_low=shifted_low)
    old = moment_fraction(base_zero.angular_momentum, base_zero.angular_momentum_low)
    new = moment_fraction(shifted_zero.angular_momentum, shifted_zero.angular_momentum_low)
    p = moment_fraction(base_zero.linear_momentum, base_zero.linear_momentum_low)
    expected_shift = cross_fraction([F(float(x)) for x in translation], p)
    error = max(abs(float(n-o-d)) for n, o, d in zip(new, old, expected_shift))
    record(record_property, "momentum_translation", dict(common_translation=translation.tolist(),
           moving_origin_error=float(np.linalg.norm(base.angular_momentum-shifted.angular_momentum)),
           fixed_origin_pair_covariance_error=error, discarded_low_error=dropped_error,
           maximum_position_low=float(np.max(np.abs(shifted_low)))))
    assert error < 1e-12


def test_rigid_rotation_momentum_and_inertia_covariance(record_property):
    data = fixture()
    rotation = exp((.41, -.23, .17))
    base = run(data)
    transformed = run(data, positions_high=data[2] @ rotation.T,
                      cell_rotations=rotation @ data[4],
                      velocity=(data[5].reshape(8, 3) @ rotation.T).ravel(),
                      acceleration=(data[6].reshape(8, 3) @ rotation.T).ravel())
    block = np.kron(np.eye(8), rotation)
    errors = dict(inertia=relative(transformed.inertia, block @ base.inertia),
                  mass=relative(transformed.mass, block @ base.mass @ block.T),
                  linear_momentum=relative(transformed.linear_momentum, rotation @ base.linear_momentum),
                  angular_momentum=relative(transformed.angular_momentum, rotation @ base.angular_momentum))
    record(record_property, "rigid_rotation_covariance", errors)
    assert max(errors.values()) < 2e-13


def test_exact_algebraic_zero_extension_and_immutable_arrays():
    response = run()
    assert response.mixed_mass.shape == (42, 42)
    for matrix in (response.mixed_mass, response.mixed_velocity_derivative, response.mixed_configuration_derivative):
        assert np.count_nonzero(matrix[list(ALGEBRAIC_DOFS), :]) == 0
        assert np.count_nonzero(matrix[:, list(ALGEBRAIC_DOFS)]) == 0
    for value in (response.mixed_generalized_momentum, response.mixed_inertia):
        assert np.count_nonzero(value[list(ALGEBRAIC_DOFS)]) == 0
    # Large nodal trace velocities/accelerations remain purely algebraic.
    data = fixture()
    speed, accel = data[5].copy(), data[6].copy()
    speed[list(ALGEBRAIC_DOFS[:9])] = 1e4
    accel[list(ALGEBRAIC_DOFS[:9])] = -2e4
    altered = run(data, velocity=speed, acceleration=accel)
    assert np.array_equal(altered.inertia, response.inertia)
    for owner in (response, response.physical):
        for value in vars(owner).values():
            if isinstance(value, np.ndarray):
                assert not value.flags.writeable
                with pytest.raises(ValueError):
                    value.flat[0] = 0.


@pytest.mark.parametrize("order", (True, 5, 8.))
def test_typed_order_rejection(order):
    with pytest.raises(ValueError, match="quadrature"):
        run(order=order)


def test_invalid_compensated_position_and_origin_rejection():
    data = fixture()
    low = data[3].copy()
    low[0, 0] = .1
    with pytest.raises(ValueError, match="normalized"):
        run(data, positions_low=low)
    with pytest.raises(ValueError, match="normalized"):
        run(data, momentum_origin_high=(1., 0., 0.), momentum_origin_low=(1e-10, 0., 0.))
