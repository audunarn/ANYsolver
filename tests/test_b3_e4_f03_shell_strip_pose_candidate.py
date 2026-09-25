"""Bounded physical checks for a distinct finite material-strip pose."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_strip_pose_candidate import (
    directional_pose_from_e4_total_strip, pose_from_e4_total_strip,
    reference_spatial_trace_strip, strip_weights,
)
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt, integrate_weak_line,
)
from scripts.b3_e4_f03_weak_line_resolution_screen import (
    chord_reference_modes, one_case)


WIDTH = dict(half_length=.2, half_width=.23)
SQUARE = dict(half_length=.05, half_width=.05)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_square_patch_has_physical_yaw_and_no_drilling_work(topology):
    panel = make_shell(2, topology, n_y=4)
    nodes = reference_nodes(panel)
    trace = reference_spatial_trace_strip(panel, .5, **SQUARE)
    assert np.count_nonzero(trace[5, 5::6]) == 0
    gamma = 1e-4
    displacement = np.zeros((panel.node_count, 6))
    displacement[:, 1] = gamma * nodes[:, 0]
    assert (trace @ displacement.ravel())[5] == pytest.approx(gamma/2, abs=1e-16)
    displacement.fill(0.)
    displacement[:, 0] = gamma * nodes[:, 1]
    assert (trace @ displacement.ravel())[5] == pytest.approx(-gamma/2, abs=1e-16)
    # A unit yaw couple pulls back to a physical force couple of 1 Nm.
    nodal = trace[5].reshape(-1, 6)
    moment = np.sum(nodes[:, 0]*nodal[:, 1]-nodes[:, 1]*nodal[:, 0])
    assert moment == pytest.approx(1., abs=2e-13)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("load", ("torsion", "transverse_force_z"))
def test_square_patch_native_load_work_is_physical(topology, load):
    loaded = one_case(
        topology, 2, "piecewise_constant",
        shell_port="physical_strip_005_005", load_kind=load,
        n_s=2, n_y=4, native_half_cells=4,
        shell_support_policy="full_left_edge")
    assert loaded["shell_component_physical_energy_j"] > 0.
    assert abs(loaded["shell_numerical_energy_j"]) < 1e-12
    assert abs(loaded["global_work_error_j"]) < 1e-10
    assert abs(loaded["global_torque_x_balance_n_m"]) < 1e-8
    assert abs(loaded["global_force_z_balance_n"]) < 1e-8
    assert abs(loaded["global_moment_y_balance_n_m"]) < 1e-8
    if load == "torsion":
        assert loaded["tip_rx_rad"] > 0.
    else:
        assert loaded["beam_tip_uz_m"] > 0.


def test_square_patch_retained_interface_action_is_consistent():
    mode=chord_reference_modes(
        "Q4", 2, "piecewise_constant", n_s=2, n_y=4,
        native_half_cells=4, shell_port="physical_strip_005_005")
    assert mode["shell_port"] == "physical_strip_005_005"
    assert mode["row_rank"] == mode["row_count"]
    assert mode["shell_only_row_rank"] <= mode["row_count"]
    assert mode["beam_only_row_rank"] <= mode["row_count"]
    assert mode["decomposition_relative_error"] < 1e-9
    dual=mode["p0_dual_diagnostic"]
    assert dual["transverse_beta_lower"] <= dual["transverse_beta_upper"]
    assert dual["gram_relative_enclosure"] < 1e-3
    assert 0. <= dual["weakest_fz_norm_share"] <= 1.
    assert mode["scope"].endswith("not physical inf-sup acceptance")


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_strip_reference_area_and_rigid_work(topology):
    panel = make_shell(2, topology, n_y=4)
    nodes = reference_nodes(panel)
    translation = np.array((.1, -.2, .3))
    omega = np.array((.02, -.03, .04))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = translation+np.cross(omega, nodes)
    rigid[:, 3:] = omega
    for station in (0., .37, 1.):
        mean, gradients = strip_weights(panel, station, **WIDTH)
        np.testing.assert_allclose(mean@nodes, (station, 0., 0.), atol=2e-14)
        np.testing.assert_allclose(gradients@nodes,
                                   ((1., 0., 0.), (0., 1., 0.)), atol=2e-14)
        trace = reference_spatial_trace_strip(panel, station, **WIDTH)
        np.testing.assert_allclose(
            trace@rigid.ravel(),
            np.r_[translation+np.cross(omega, (station, 0., 0.)), omega],
            atol=2e-14)
        assert np.array_equal(trace[5, 5::6], np.zeros(panel.node_count))


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("width", (WIDTH, SQUARE))
def test_strip_finite_objectivity_chart_derivatives_and_shear(topology, width):
    panel = make_shell(2, topology, n_y=4)
    nodes = reference_nodes(panel)
    station = .37
    angle = np.array((.13, -.21, .18))
    rigid_frame = Rotation.from_rotvec(angle).as_matrix()
    shift = np.array((.31, -.27, .19))
    rigid = np.zeros((panel.node_count, 6))
    rigid[:, :3] = nodes@rigid_frame.T+shift-nodes
    rigid[:, 3:] = angle
    position, frame = pose_from_e4_total_strip(
        panel, station, rigid.ravel(), **width)
    np.testing.assert_allclose(position,
                               rigid_frame@(station, 0., 0.)+shift, atol=2e-12)
    np.testing.assert_allclose(frame, rigid_frame, atol=2e-12)

    rng = np.random.default_rng(3401)
    first = rng.normal(size=rigid.shape)*.04
    second = rng.normal(size=rigid.shape)*.04
    analytic = directional_pose_from_e4_total_strip(
        panel, station, rigid.ravel(), first, second, **width)

    def moved(a, b):
        return pose_from_e4_total_strip(
            panel, station, (rigid+a*first+b*second).ravel(), **width)

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
    at_reference = directional_pose_from_e4_total_strip(
        panel, station, zero.ravel(), first, zero, **width)
    derivative = at_reference.frame_first
    spin = np.array((derivative[2, 1]-derivative[1, 2],
                     derivative[0, 2]-derivative[2, 0],
                     derivative[1, 0]-derivative[0, 1]))/2
    np.testing.assert_allclose(
        np.r_[at_reference.position_first, spin],
        reference_spatial_trace_strip(panel, station, **width)@first.ravel(),
        atol=2e-13)

    shear = np.zeros_like(rigid)
    shear[:, 2] = .07*nodes[:, 0]
    _, sheared_frame = pose_from_e4_total_strip(
        panel, station, shear.ravel(), **width)
    np.testing.assert_allclose(sheared_frame[:, 2], (0., 0., 1.), atol=2e-14)
    surface_normal = np.cross((1., 0., .07), (0., 1., 0.))
    surface_normal /= np.linalg.norm(surface_normal)
    assert np.linalg.norm(sheared_frame[:, 2]-surface_normal) > .05


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_strip_has_intentional_finite_longitudinal_filter(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    k = 5*np.pi  # Wavelength .4 m equals the declared strip length.
    direction = np.zeros(6*panel.node_count)
    direction[1::6] = 1e-4/k*np.sin(k*nodes[:, 0])
    stations = (.1, .25, .4, .6, .8)
    for station in stations:
        observed = reference_spatial_trace_strip(
            panel, station, **WIDTH)[5]@direction
        assert abs(observed) < 1.5e-6


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_strip_weak_work_and_loaded_global_moment_balance(topology):
    shell = FlatE4TrialPanel(make_shell(1, topology, n_y=4))
    beam = build(4)
    space = LineMultiplierSpace("piecewise_constant", (0., .5, 1.))
    zero = np.zeros((shell.panel.node_count, 6))
    direction = np.zeros_like(zero)
    direction[:, 0] = .001
    beam_zero = np.zeros(beam.context.count)
    coefficients = np.arange(1., 13.).reshape(2, 6)
    result = integrate_weak_line(
        shell, beam, space, coefficients, zero.ravel(),
        direction.ravel(), direction, zero,
        beam.context.initial.mechanical, beam_zero, beam_zero,
        shell_port="physical_strip_020_023")
    np.testing.assert_allclose(
        result.potential, np.sum(coefficients*result.weak_constraints),
        atol=1e-11)
    np.testing.assert_allclose(
        result.first, np.sum(coefficients*result.weak_first),
        atol=1e-11)
    assert result.segment_count >= beam.n_half_cells
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port="physical_strip_020_023",
        shell_support_policy="full_left_edge")
    assert kkt.constraint_jacobian.shape[0] == 12
    loaded = one_case(
        topology, 2, "piecewise_constant",
        shell_port="physical_strip_020_023", load_kind="yaw_torque_z",
        n_s=2, n_y=4, native_half_cells=4,
        shell_support_policy="full_left_edge")
    assert loaded["tip_rz_rad"] > 0.
    assert loaded["shell_physical_inplane_energy_j"] > 0.
    assert abs(loaded["global_moment_z_balance_n_m"]) < 1e-8
    assert abs(loaded["global_work_error_j"]) < 1e-10
