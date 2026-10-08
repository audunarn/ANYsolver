"""Finite rigid-motion check for the alternate local shell pose origin."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_local_translation_candidate import (
    directional_pose_from_e4_total_local_director,
    directional_pose_from_e4_total_local_frame,
    pose_from_e4_total_local_translation,
    pose_from_e4_total_local_director,
    pose_from_e4_total_local_frame,
    local_material_gradient_weights,
    reference_spatial_trace_local_director,
    reference_spatial_trace_local_frame)
from scripts._b3_e4_f03_shell_spatial_linear_port import (
    physical_shell_stiffness, reference_spatial_trace)
from scripts._b3_e4_f03_shell_trace import make_shell


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("n_s", (1, 2, 4))
def test_local_shell_pose_follows_common_finite_rigid_motion(topology, n_s):
    panel = make_shell(n_s, topology)
    nodes = reference_nodes(panel)
    angle = np.array((.13, -.21, .18))
    frame = Rotation.from_rotvec(angle).as_matrix()
    shift = np.array((.31, -.27, .19))
    total = np.zeros((panel.node_count, 6))
    total[:, :3] = nodes@frame.T+shift-nodes
    total[:, 3:] = angle
    for station in (0., .125, .375, .5, .875, 1.):
        position, current_frame = pose_from_e4_total_local_translation(
            panel, station, total.ravel())
        np.testing.assert_allclose(
            position, frame@np.array((station, 0., 0.))+shift,
            rtol=0., atol=2e-12)
        np.testing.assert_allclose(current_frame, frame, rtol=0., atol=2e-12)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_origin_follows_declared_center_material_point(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    total = np.zeros((panel.node_count, 6))
    total[:, 0] = 1e-3*nodes[:, 0]**2
    station = .5  # A shell node, so the center material value is exact.
    local = pose_from_e4_total_local_translation(
        panel, station, total.ravel())[0]
    rail = pose_from_e4_total(panel, station, total.ravel())[0]
    np.testing.assert_allclose(local[0], station+1e-3*station**2,
                               atol=1e-14)
    assert rail[0]-local[0] > 3e-5


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_director_preserves_rigid_pose_and_actual_chart_derivatives(topology):
    panel = make_shell(2, topology)
    nodes = reference_nodes(panel)
    angle = np.array((.13, -.21, .18))
    frame = Rotation.from_rotvec(angle).as_matrix()
    shift = np.array((.31, -.27, .19))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = nodes@frame.T+shift-nodes
    rigid[:, 3:] = angle
    position, current_frame = pose_from_e4_total_local_director(
        panel, .37, rigid.ravel())
    np.testing.assert_allclose(position, frame@(.37, 0., 0.)+shift,
                               atol=2e-12)
    np.testing.assert_allclose(current_frame, frame, atol=2e-12)

    rng = np.random.default_rng(3914)
    first = rng.normal(size=rigid.shape)*.04
    second = rng.normal(size=rigid.shape)*.04
    analytic = directional_pose_from_e4_total_local_director(
        panel, .37, rigid.ravel(), first, second)

    def moved(a, b):
        return pose_from_e4_total_local_director(
            panel, .37, (rigid+a*first+b*second).ravel())

    h = 1e-5
    plus, minus = moved(h, 0.), moved(-h, 0.)
    np.testing.assert_allclose(analytic.position_first,
                               (plus[0]-minus[0])/(2*h),
                               rtol=2e-7, atol=2e-9)
    np.testing.assert_allclose(analytic.frame_first,
                               (plus[1]-minus[1])/(2*h),
                               rtol=2e-7, atol=2e-9)
    h = 2e-3
    pp, pm, mp, mm = (moved(h, h), moved(h, -h),
                      moved(-h, h), moved(-h, -h))
    np.testing.assert_allclose(analytic.position_mixed,
        (pp[0]-pm[0]-mp[0]+mm[0])/(4*h*h), rtol=2e-5, atol=2e-8)
    np.testing.assert_allclose(analytic.frame_mixed,
        (pp[1]-pm[1]-mp[1]+mm[1])/(4*h*h), rtol=2e-5, atol=2e-8)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_director_recovers_physical_torque_work_hidden_by_rail(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    wavenumber = 2.5*np.pi  # Rail samples at x ±.2 cancel this wave.
    amplitude = 1e-4
    direction = np.zeros(6*panel.node_count)
    direction[3::6] = amplitude*np.sin(wavenumber*nodes[:, 0])
    stations, weights = np.polynomial.legendre.leggauss(32)
    stations, weights = (stations+1)/2, weights/2
    local = amplitude*np.sin(wavenumber*stations)
    reference_work = float(np.dot(weights, local*local))
    rail = np.array([reference_spatial_trace(panel, float(s))[3]@direction
                     for s in stations])
    point = np.array([
        reference_spatial_trace_local_director(panel, float(s))[3]@direction
        for s in stations])
    assert abs(np.dot(weights, local*rail)/reference_work) < 1e-3
    assert np.dot(weights, local*point)/reference_work > .9
    assert .5*direction@(physical_shell_stiffness(panel)@direction) > 0.


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_director_reference_trace_matches_finite_pose_variation(topology):
    panel = make_shell(2, topology)
    rng = np.random.default_rng(3915)
    direction = rng.normal(size=(panel.node_count, 6))
    zero = np.zeros_like(direction)
    analytic = directional_pose_from_e4_total_local_director(
        panel, .37, zero.ravel(), direction, zero)
    derivative = analytic.frame_first
    angular = np.array((derivative[2, 1]-derivative[1, 2],
                        derivative[0, 2]-derivative[2, 0],
                        derivative[1, 0]-derivative[0, 1]))/2
    observed = np.r_[analytic.position_first, angular]
    np.testing.assert_allclose(
        observed,
        reference_spatial_trace_local_director(panel, .37)@direction.ravel(),
        rtol=0., atol=2e-13)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_director_alternative_still_has_finite_rail_yaw_blind_mode(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    wavenumber = 5*np.pi  # Finite x ±.2 yaw fit has sinc(k*.2)=0.
    amplitude = 1e-4/wavenumber
    direction = np.zeros(6*panel.node_count)
    direction[1::6] = amplitude*np.sin(wavenumber*nodes[:, 0])
    stations, weights = np.polynomial.legendre.leggauss(32)
    stations, weights = (stations+1)/2, weights/2
    local_gradient = amplitude*wavenumber*np.cos(wavenumber*stations)
    mapped = np.array([
        reference_spatial_trace_local_director(panel, float(s))[5]@direction
        for s in stations])
    reference_work = np.dot(weights, local_gradient*local_gradient)
    assert abs(np.dot(weights, local_gradient*mapped)/reference_work) < 1e-3
    assert .5*direction@(physical_shell_stiffness(panel)@direction) > 0.


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_frame_rigid_patch_and_restored_yaw_work(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    translation = np.array((.1, -.2, .3))
    omega = np.array((.02, -.03, .04))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = translation+np.cross(omega, nodes)
    rigid[:, 3:] = omega
    for station in (.113, .367, .811):
        trace = reference_spatial_trace_local_frame(panel, station)
        np.testing.assert_allclose(
            trace@rigid.ravel(),
            np.r_[translation+np.cross(omega, (station, 0., 0.)), omega],
            rtol=0., atol=1e-14)
        gradient = local_material_gradient_weights(panel, station)
        np.testing.assert_allclose(gradient@nodes,
                                   ((1., 0., 0.), (0., 1., 0.)),
                                   rtol=0., atol=1e-14)

    wavenumber = 5*np.pi
    amplitude = 1e-4/wavenumber
    direction = np.zeros(6*panel.node_count)
    direction[1::6] = amplitude*np.sin(wavenumber*nodes[:, 0])
    stations, weights = np.polynomial.legendre.leggauss(64)
    stations, weights = (stations+1)/2, weights/2
    local_polar_spin = .5*amplitude*wavenumber*np.cos(
        wavenumber*stations)
    mapped = np.array([
        reference_spatial_trace_local_frame(panel, float(s))[5]@direction
        for s in stations])
    reference_work = np.dot(weights, local_polar_spin*local_polar_spin)
    assert np.dot(weights, local_polar_spin*mapped)/reference_work > .6


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_gradient_boundary_has_explicit_one_sided_host(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    field = nodes[:, 0]**2
    station = .375  # An x-host edge; the center-line field stays C0.
    left = local_material_gradient_weights(panel, station-1e-9)[0]@field
    at_edge = local_material_gradient_weights(panel, station)[0]@field
    right = local_material_gradient_weights(panel, station+1e-9)[0]@field
    np.testing.assert_allclose(at_edge, left, atol=1e-12)
    assert abs(right-left) > .1


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_finite_local_frame_objectivity_derivatives_and_reference_trace(topology):
    panel = make_shell(2, topology)
    nodes = reference_nodes(panel)
    station = .37
    angle = np.array((.13, -.21, .18))
    frame = Rotation.from_rotvec(angle).as_matrix()
    shift = np.array((.31, -.27, .19))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = nodes@frame.T+shift-nodes
    rigid[:, 3:] = angle
    position, current_frame = pose_from_e4_total_local_frame(
        panel, station, rigid.ravel())
    np.testing.assert_allclose(position, frame@(station, 0., 0.)+shift,
                               atol=2e-12)
    np.testing.assert_allclose(current_frame, frame, atol=2e-12)

    rng = np.random.default_rng(3916)
    first = rng.normal(size=rigid.shape)*.04
    second = rng.normal(size=rigid.shape)*.04
    analytic = directional_pose_from_e4_total_local_frame(
        panel, station, rigid.ravel(), first, second)

    def moved(a, b):
        return pose_from_e4_total_local_frame(
            panel, station, (rigid+a*first+b*second).ravel())

    h = 1e-5
    plus, minus = moved(h, 0.), moved(-h, 0.)
    np.testing.assert_allclose(analytic.position_first,
                               (plus[0]-minus[0])/(2*h),
                               rtol=2e-7, atol=2e-9)
    np.testing.assert_allclose(analytic.frame_first,
                               (plus[1]-minus[1])/(2*h),
                               rtol=2e-7, atol=2e-9)
    h = 2e-3
    pp, pm, mp, mm = (moved(h, h), moved(h, -h),
                      moved(-h, h), moved(-h, -h))
    np.testing.assert_allclose(analytic.position_mixed,
        (pp[0]-pm[0]-mp[0]+mm[0])/(4*h*h), rtol=2e-5, atol=2e-8)
    np.testing.assert_allclose(analytic.frame_mixed,
        (pp[1]-pm[1]-mp[1]+mm[1])/(4*h*h), rtol=2e-5, atol=2e-8)

    zero = np.zeros_like(rigid)
    reference = directional_pose_from_e4_total_local_frame(
        panel, station, zero.ravel(), first, zero)
    derivative = reference.frame_first
    angular = np.array((derivative[2, 1]-derivative[1, 2],
                        derivative[0, 2]-derivative[2, 0],
                        derivative[1, 0]-derivative[0, 1]))/2
    np.testing.assert_allclose(
        np.r_[reference.position_first, angular],
        reference_spatial_trace_local_frame(panel, station)@first.ravel(),
        rtol=0., atol=2e-13)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_finite_local_frame_does_not_force_director_to_surface_normal(topology):
    panel = make_shell(2, topology)
    nodes = reference_nodes(panel)
    total = np.zeros((panel.node_count, 6))
    total[:, 2] = .07*nodes[:, 0]
    _, frame = pose_from_e4_total_local_frame(panel, .37, total.ravel())
    np.testing.assert_allclose(frame[:, 2], (0., 0., 1.), atol=2e-14)
    surface_normal = np.cross((1., 0., .07), (0., 1., 0.))
    surface_normal /= np.linalg.norm(surface_normal)
    assert np.linalg.norm(frame[:, 2]-surface_normal) > .05
