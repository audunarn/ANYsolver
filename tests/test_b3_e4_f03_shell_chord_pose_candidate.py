"""Bounded physical checks for a longitudinal shell-line chord pose."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_shell_chord_pose_candidate import (
    directional_pose_from_e4_total_chord, pose_from_e4_total_chord,
    reference_spatial_trace_chord,
)
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_strip_pose_candidate import (
    reference_spatial_trace_strip,
)
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt, integrate_weak_line,
)
from scripts.b3_e4_f03_weak_line_resolution_screen import (
    chord_reference_modes, one_case,
)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_chord_reference_work_rigid_motion_and_no_drilling(topology):
    panel = make_shell(2, topology, n_y=4)
    nodes = reference_nodes(panel)
    translation = np.array((.1, -.2, .3))
    omega = np.array((.02, -.03, .04))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = translation+np.cross(omega, nodes)
    rigid[:, 3:] = omega
    for station in (0., .37, 1.):
        trace = reference_spatial_trace_chord(panel, station)
        np.testing.assert_allclose(
            trace@rigid.ravel(),
            np.r_[translation+np.cross(omega, (station, 0., 0.)), omega],
            atol=2e-14)
        assert np.array_equal(trace[5, 5::6], np.zeros(panel.node_count))
        assert np.array_equal(trace[5, 0::6], np.zeros(panel.node_count))

    # The earlier normal-gradient boundary layer uses only ux. Its fixed
    # local polar yaw does not enter this line-trace functional.
    localized = np.zeros_like(rigid)
    localized[:, 0] = 1e-4*nodes[:, 0]*nodes[:, 1]
    assert reference_spatial_trace_chord(panel, .37)[5]@localized.ravel() == 0.


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_chord_objectivity_actual_chart_derivatives_and_shear(topology):
    panel = make_shell(2, topology, n_y=4)
    nodes = reference_nodes(panel)
    station = .37
    angle = np.array((.13, -.21, .18))
    rotation = Rotation.from_rotvec(angle).as_matrix()
    shift = np.array((.31, -.27, .19))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = nodes@rotation.T+shift-nodes
    rigid[:, 3:] = angle
    position, frame = pose_from_e4_total_chord(
        panel, station, rigid.ravel())
    np.testing.assert_allclose(position,
                               rotation@(station, 0., 0.)+shift, atol=2e-12)
    np.testing.assert_allclose(frame, rotation, atol=2e-12)

    rng = np.random.default_rng(3519)
    first = rng.normal(size=rigid.shape)*.04
    second = rng.normal(size=rigid.shape)*.04
    analytic = directional_pose_from_e4_total_chord(
        panel, station, rigid.ravel(), first, second)

    def moved(a, b):
        return pose_from_e4_total_chord(
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
    np.testing.assert_allclose(analytic.frame_mixed,
        (pp[1]-pm[1]-mp[1]+mm[1])/(4*h*h), rtol=2e-5, atol=2e-8)

    zero = np.zeros_like(rigid)
    reference = directional_pose_from_e4_total_chord(
        panel, station, zero.ravel(), first, zero)
    derivative = reference.frame_first
    spin = np.array((derivative[2, 1]-derivative[1, 2],
                     derivative[0, 2]-derivative[2, 0],
                     derivative[1, 0]-derivative[0, 1]))/2
    np.testing.assert_allclose(
        np.r_[reference.position_first, spin],
        reference_spatial_trace_chord(panel, station)@first.ravel(),
        atol=2e-13)

    shear = np.zeros_like(rigid)
    shear[:, 2] = .07*nodes[:, 0]
    _, sheared_frame = pose_from_e4_total_chord(
        panel, station, shear.ravel())
    np.testing.assert_allclose(sheared_frame, np.eye(3), atol=2e-14)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_chord_weak_work_derivative_and_loaded_balance(topology):
    shell = FlatE4TrialPanel(make_shell(1, topology, n_y=4))
    beam = build(4)
    space = LineMultiplierSpace("piecewise_constant", (0., .5, 1.))
    zero = np.zeros((shell.panel.node_count, 6))
    rng = np.random.default_rng(3520)
    base = rng.normal(size=zero.shape)*1e-5
    direction = rng.normal(size=zero.shape)*1e-3
    beam_zero = np.zeros(beam.context.count)
    coefficients = np.arange(1., 13.).reshape(2, 6)

    def evaluate(a):
        return integrate_weak_line(
            shell, beam, space, coefficients, zero.ravel(),
            (base+a*direction).ravel(), direction, np.zeros_like(direction),
            beam.context.initial.mechanical, beam_zero, beam_zero,
            shell_port="line_chord_020")

    central = evaluate(0.)
    h = 1e-5
    observed = (evaluate(h).potential-evaluate(-h).potential)/(2*h)
    np.testing.assert_allclose(central.first, observed,
                               rtol=2e-6, atol=2e-8)
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port="line_chord_020",
        shell_support_policy="full_left_edge")
    assert np.linalg.matrix_rank(
        kkt.constraint_jacobian[:, kkt.free_primal]) == 12
    loaded = one_case(
        topology, 2, "piecewise_constant",
        shell_port="line_chord_020", load_kind="yaw_torque_z",
        n_s=2, n_y=4, native_half_cells=4,
        shell_support_policy="full_left_edge")
    assert loaded["tip_rz_rad"] > 0.
    assert loaded["shell_physical_inplane_energy_j"] > 0.
    assert abs(loaded["global_moment_z_balance_n_m"]) < 1e-8
    assert abs(loaded["global_work_error_j"]) < 1e-10


def test_chord_native_six_channel_mode_is_not_an_axial_proxy_for_transverse():
    result = chord_reference_modes(
        "Q4", 2, "piecewise_constant", n_s=2, n_y=4,
        native_half_cells=4)
    assert result["row_rank"] == result["row_count"] == 12
    assert result["physical_stiffness_min_eigen"] > 0.
    assert result["retained_negative_modes"] > 0
    assert result["decomposition_relative_error"] < 1e-9
    np.testing.assert_allclose(sum(result["weakest_mode_channel_l2_shares"]),
                               1., atol=1e-12)
    assert result["weakest_mode_channel_l2_shares"][0] > .99
    assert result["transverse_fz_mx_my_beta"] > 0.
    assert result["transverse_mode_fz_mx_my_l2_shares"][0] > .5


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_chord_and_finite_footprint_make_distinct_inplane_shear_choices(topology):
    panel = make_shell(2, topology, n_y=4)
    nodes = reference_nodes(panel)
    chord = reference_spatial_trace_chord(panel, .37)
    strip = reference_spatial_trace_strip(
        panel, .37, half_length=.2, half_width=.23)
    gamma = .01
    along = np.zeros((panel.node_count, 6))
    along[:, 1] = gamma*nodes[:, 0]
    np.testing.assert_allclose(chord[5]@along.ravel(), gamma,
                               atol=2e-15)
    np.testing.assert_allclose(strip[5]@along.ravel(), gamma/2,
                               atol=2e-15)
    across = np.zeros_like(along)
    across[:, 0] = gamma*nodes[:, 1]
    np.testing.assert_allclose(chord[5]@across.ravel(), 0., atol=2e-15)
    np.testing.assert_allclose(strip[5]@across.ravel(), -gamma/2,
                               atol=2e-15)
