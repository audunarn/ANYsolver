"""Prepared source controls; execution requires a separately assigned scope.

The local-native oracle cases are distinct from the independent algebra controls.
No physical solve, CCX run, public curved owner or reference scoring occurs here.
"""
from dataclasses import FrozenInstanceError, fields, replace

import numpy as np
import pytest

from scripts.r8_e03_ge_distributing_work_bridge import (
    BridgeDomainError, ReferenceBridge, native_local_evaluation,
    native_sample_derivative, rectangular_bridge,
)


def _rotation(vector):
    vector = np.asarray(vector, dtype=float)
    angle = np.linalg.norm(vector)
    if angle == 0:
        return np.eye(3)
    x, y, z = vector/angle
    cross = np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))
    return np.eye(3)+np.sin(angle)*cross+(1-np.cos(angle))*(cross@cross)


FRAMES = (np.eye(3), _rotation((.31, -.22, .17)), _rotation((-.2, .6, -.4)))


def _bridge(frame=FRAMES[1], **kwargs):
    return rectangular_bridge(.4, .2, .008, frame=frame,
                              origin=kwargs.pop("origin", (.02, -.03, .04)), **kwargs)


@pytest.mark.parametrize("frame", FRAMES)
def test_all_six_rigid_pose_modes_and_spatial_wrench(frame):
    bridge = _bridge(frame)
    for component in range(6):
        increment = np.eye(6)[component]
        u = increment[:3]+np.cross(increment[3:], bridge.face_samples-bridge.origin)
        np.testing.assert_allclose(bridge.pose(u), increment, rtol=0, atol=2e-13)
    assert np.linalg.matrix_rank(bridge.pose_map) == 6
    wrench = np.array((.3, -.8, .4, .07, -.02, .06))
    force = bridge.forces(wrench)
    np.testing.assert_allclose(bridge.resultant(force, about=bridge.origin), wrench,
                               rtol=0, atol=2e-13)
    expected = np.r_[wrench[:3], wrench[3:]+np.cross(bridge.origin, wrench[:3])]
    np.testing.assert_allclose(bridge.resultant(force, about=np.zeros(3)), expected,
                               rtol=0, atol=2e-13)


def test_midplane_normal_slope_does_not_replace_independent_director():
    bridge = _bridge()
    n = len(bridge.world_nodes)
    normal = bridge.frame[:, 2]
    slope = .23*bridge.local_nodes[:, 0]-.17*bridge.local_nodes[:, 1]
    geometric = slope[:, None]*normal
    pose = bridge.pose(np.vstack((geometric, geometric)))
    np.testing.assert_allclose(pose, np.zeros(6), rtol=0, atol=2e-14)
    delta_director = .12*bridge.frame[:, 0]-.09*bridge.frame[:, 1]
    faces = np.vstack((np.tile(-bridge.thickness_m/2*delta_director, (n, 1)),
                       np.tile(bridge.thickness_m/2*delta_director, (n, 1))))
    expected = np.r_[np.zeros(3), np.cross(normal, delta_director)]
    np.testing.assert_allclose(bridge.pose(faces), expected, rtol=0, atol=2e-14)
    np.testing.assert_allclose(bridge.nodal_increments(faces)[:, :3], 0., atol=0.)


def test_normal_spin_comes_from_planar_polar_yaw_and_not_nodal_drill():
    bridge = _bridge()
    normal = bridge.frame[:, 2]
    nodal = np.zeros((len(bridge.world_nodes), 6))
    nodal[:, 3:] = .2*normal
    np.testing.assert_allclose(bridge.nodal_pose_map @ nodal.ravel(), 0., atol=2e-14)
    yaw = .2*np.cross(normal, bridge.face_samples-bridge.origin)
    np.testing.assert_allclose(bridge.pose(yaw), np.r_[np.zeros(3), .2*normal], atol=2e-14)
    # Normal through-thickness extension is not an aggregate pose channel.
    n = len(bridge.world_nodes)
    stretch = np.vstack((np.tile(-.03*normal, (n, 1)), np.tile(.03*normal, (n, 1))))
    np.testing.assert_allclose(bridge.pose(stretch), 0., atol=2e-14)


@pytest.mark.parametrize("frame", FRAMES[:2])
@pytest.mark.parametrize("offset_sign", (-1., 1.))
def test_eccentric_connection_exact_transpose_work_and_action_reaction(frame, offset_sign):
    bridge = _bridge(frame)
    offset = frame @ np.array((.013, -.007, offset_sign*.019))
    multiplier = np.array((.4, -.2, .7, .06, -.04, .03))
    faces, beam = bridge.connection_actions(multiplier, offset_world=offset)
    wrench = bridge.resultant(faces, about=bridge.origin)
    beam_about_origin = np.r_[beam[:3], beam[3:]+np.cross(offset, beam[:3])]
    np.testing.assert_allclose(wrench+beam_about_origin, 0., atol=2e-13)
    direction = np.linspace(-.09, .11, bridge.pose_map.shape[1]+6)
    lhs = faces.ravel() @ direction[:-6]+beam @ direction[-6:]
    rhs = multiplier @ (bridge.constraint(offset) @ direction)
    assert abs(lhs-rhs) < 2e-14


def test_local_deformation_kernel_remains_admissible_without_rigid_patch():
    bridge = _bridge()
    p = bridge.pose_map
    trial = np.linspace(-.03, .07, p.shape[1])**2
    local = trial-p.T @ np.linalg.solve(p@p.T, p@trial)
    assert np.linalg.norm(local) > 1e-4
    np.testing.assert_allclose(p@local, 0., atol=2e-14)
    assert p.shape[1]-np.linalg.matrix_rank(p) > 6


@pytest.mark.parametrize("frame", FRAMES[:2])
@pytest.mark.parametrize("offset_sign", (-1., 1.))
def test_actual_native_reference_tangent_row_frame_and_dual(frame, offset_sign):
    bridge = _bridge(frame)
    offset = frame @ np.array((.013, -.007, offset_sign*.019))
    actual = native_sample_derivative(bridge, offset)
    transform = actual["world_to_native_rows"]
    np.testing.assert_allclose(actual["evaluated_shell_frame"], frame, atol=2e-13)
    np.testing.assert_allclose(actual["constraints"], 0., atol=2e-13)
    np.testing.assert_allclose(actual["native_rows"], transform@bridge.constraint(offset),
                               rtol=0, atol=2e-12)
    native_multiplier = np.arange(1., 7.)/9
    world_multiplier = transform.T @ native_multiplier
    direction = np.linspace(-.02, .03, actual["native_rows"].shape[1])
    assert abs(native_multiplier@(actual["native_rows"]@direction)
               -world_multiplier@(bridge.constraint(offset)@direction)) < 2e-13
    assert actual["production_qualified"] is False
    assert actual["public_curved_admission"] is False
    if not np.array_equal(frame, np.eye(3)):
        assert np.linalg.norm(actual["native_rows"]-bridge.constraint(offset)) > .1


@pytest.mark.parametrize("frame", FRAMES[:2])
def test_actual_native_common_rigid_configuration_directional_derivative(frame):
    bridge = _bridge(frame)
    offset = frame @ np.array((.01, -.004, .018))
    rows = native_sample_derivative(bridge, offset)["native_rows"]
    direction = np.sin(np.arange(rows.shape[1])+1)*.02
    step = 1e-6
    def evaluate(sign):
        return native_local_evaluation(bridge, offset,
            face_delta=(sign*step*direction[:-6]).reshape(bridge.face_samples.shape),
            beam_delta=sign*step*direction[-6:]).constraints
    central = (evaluate(1)-evaluate(-1))/(2*step)
    np.testing.assert_allclose(central, rows@direction, rtol=0, atol=2e-8)


@pytest.mark.parametrize("lengths", ((0., .2, .008), (.4, -1., .008), (.4, .2, 0.),
                                    (float("nan"), .2, .008), (.4, .2, float("inf"))))
def test_invalid_declared_lengths_refuse(lengths):
    with pytest.raises(BridgeDomainError):
        rectangular_bridge(*lengths, frame=np.eye(3), origin=np.zeros(3))


@pytest.mark.parametrize("options", ({"nx": 0}, {"ny": 9}, {"nx": True},
                                     {"origin": (0., float("nan"), 0.)}))
def test_invalid_local_geometry_refuses(options):
    with pytest.raises(BridgeDomainError):
        _bridge(**options)


@pytest.mark.parametrize("frame", (np.diag((1., 1., -1.)), np.ones((3, 3)), np.eye(2)))
def test_nonproper_or_incomplete_frame_refuses(frame):
    with pytest.raises(BridgeDomainError):
        _bridge(frame)


def test_near_proper_distorted_frame_exceeding_representation_bound_refuses():
    distorted = np.diag((1., 1., 1.+4e-13))
    with pytest.raises(BridgeDomainError, match="proper orthonormal"):
        rectangular_bridge(.4, .2, .008, frame=distorted, origin=np.zeros(3))


def test_large_origin_thin_separation_is_a_representation_refusal():
    with pytest.raises(BridgeDomainError, match="ill-resolved|distinct representable"):
        rectangular_bridge(.4, .2, .001, frame=np.eye(3), origin=(0., 0., 1e10))


@pytest.mark.parametrize("width,height,origin", ((1e-12, 1., (1., 0., 0.)),
                                                (1., 1e-12, (0., 1., 0.))))
def test_off_origin_narrow_material_direction_is_a_representation_refusal(width, height, origin):
    with pytest.raises(BridgeDomainError, match="ill-resolved|distinct representable"):
        rectangular_bridge(width, height, .008, frame=np.eye(3), origin=origin)


def test_extreme_aspect_ratio_alone_does_not_reject_resolved_local_geometry():
    bridge = rectangular_bridge(1e-12, 1., .008, frame=np.eye(3), origin=np.zeros(3))
    normal_spin = np.cross(np.array((0., 0., 1.)), bridge.face_samples)
    np.testing.assert_allclose(bridge.pose(normal_spin), (0., 0., 0., 0., 0., 1.),
                               rtol=0, atol=2e-13)


def test_inputs_maps_and_results_are_owned_and_direct_construction_refuses():
    frame, origin = FRAMES[1].copy(), np.array((.02, -.03, .04))
    bridge = _bridge(frame, origin=origin)
    original_frame, original_origin = bridge.frame.copy(), bridge.origin.copy()
    frame[:] = 0.
    origin[:] = 9.
    np.testing.assert_array_equal(bridge.frame, original_frame)
    np.testing.assert_array_equal(bridge.origin, original_origin)
    arrays = [getattr(bridge, field.name) for field in fields(bridge)
              if isinstance(getattr(bridge, field.name), np.ndarray)]
    arrays.extend((bridge.pose(np.zeros_like(bridge.face_samples)), bridge.constraint(np.zeros(3))))
    for array in arrays:
        assert not array.flags.writeable
        with pytest.raises(ValueError):
            array.setflags(write=True)
    with pytest.raises(FrozenInstanceError):
        bridge.width_m = 99.
    kwargs = {field.name: getattr(bridge, field.name) for field in fields(bridge) if field.init}
    with pytest.raises(BridgeDomainError, match="direct bridge construction"):
        ReferenceBridge(**kwargs)
    with pytest.raises(BridgeDomainError, match="direct bridge construction"):
        replace(bridge, width_m=99.)


@pytest.mark.parametrize("value", (float("nan"), float("inf")))
def test_nonfinite_displacement_and_wrench_refuse(value):
    bridge = _bridge()
    face = np.zeros_like(bridge.face_samples)
    face[0, 0] = value
    with pytest.raises(BridgeDomainError):
        bridge.pose(face)
    with pytest.raises(BridgeDomainError):
        bridge.forces((value, 0., 0., 0., 0., 0.))


def test_overflow_result_refuses_instead_of_returning_nonfinite_values():
    bridge = _bridge()
    with np.errstate(over="ignore", invalid="ignore"):
        with pytest.raises(BridgeDomainError):
            bridge.forces(np.full(6, np.finfo(float).max))


def test_native_oracle_refuses_single_host_outside_existing_prototype_domain():
    bridge = _bridge(nx=1, ny=1)
    with pytest.raises(BridgeDomainError, match="two hosts"):
        native_sample_derivative(bridge, np.zeros(3))
