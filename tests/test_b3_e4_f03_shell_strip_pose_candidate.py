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
    LineMultiplierSpace, assemble_channel_split_reference_kkt,
    assemble_reference_kkt, integrate_channel_split_weak_line,
    integrate_weak_line,
)
from scripts.b3_e4_f03_weak_line_resolution_screen import (
    channel_split_reference_modes, chord_reference_modes, one_case)


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


@pytest.mark.parametrize("kind", ("piecewise_constant", "continuous_linear",
                                   "dual_linear"))
def test_square_patch_retained_interface_action_is_consistent(kind):
    mode=chord_reference_modes(
        "Q4", 2, kind, n_s=2, n_y=4,
        native_half_cells=4, shell_port="physical_strip_005_005")
    assert mode["shell_port"] == "physical_strip_005_005"
    assert mode["row_rank"] == mode["row_count"]
    assert mode["shell_only_row_rank"] <= mode["row_count"]
    assert mode["beam_only_row_rank"] <= mode["row_count"]
    assert mode["decomposition_relative_error"] < 1e-9
    dual=mode["density_dual_diagnostic"]
    assert dual["space"] == kind
    assert dual["transverse_beta_lower"] <= (
        dual["transverse_beta_upper"] + 1e-10)
    assert dual["gram_relative_enclosure"] < 1e-3
    assert 0. <= dual["weakest_fz_norm_share"] <= 1.
    assert mode["scope"].endswith("not physical inf-sup acceptance")


def test_split_mx_rows_preserve_constant_torque_and_end_member_parity():
    shell=FlatE4TrialPanel(make_shell(2,"Q4",n_y=4))
    beam=build(4)
    options=dict(shell_port="physical_strip_005_005",
                 shell_support_policy="full_left_edge")
    coarse=assemble_reference_kkt(
        shell,beam,LineMultiplierSpace("piecewise_constant",(0.,.5,1.)),
        **options)
    fine=assemble_reference_kkt(
        shell,beam,LineMultiplierSpace(
            "piecewise_constant",(0.,.25,.5,.75,1.)),**options)
    split=assemble_channel_split_reference_kkt(
        shell,beam,coarse_intervals=2,fine_intervals=4,
        fine_channels=(3,),**options)
    no_refinement=assemble_channel_split_reference_kkt(
        shell,beam,coarse_intervals=2,fine_intervals=4,
        fine_channels=(),**options)
    all_refined=assemble_channel_split_reference_kkt(
        shell,beam,coarse_intervals=2,fine_intervals=4,
        fine_channels=(0,1,2,3,4,5),**options)
    np.testing.assert_array_equal(no_refinement.constraint_jacobian,
                                  coarse.constraint_jacobian)
    np.testing.assert_array_equal(all_refined.constraint_jacobian,
                                  fine.constraint_jacobian)
    assert split.constraint_jacobian.shape[0] == 14
    density=np.zeros(14)
    density[-4:]=100.
    nodal=(split.constraint_jacobian.T@density)[:6*shell.panel.node_count]
    nodal=nodal.reshape(-1,6)
    nodes=reference_nodes(shell.panel)
    torque_x=np.sum(nodal[:,3]+nodes[:,1]*nodal[:,2]-
                    nodes[:,2]*nodal[:,1])
    assert torque_x == pytest.approx(-100.,abs=2e-10)
    assert np.max(np.abs(nodal[:,5])) < 1e-13
    direction=np.arange(split.primal_tangent.shape[0],dtype=float)*1e-7
    assert density@(split.constraint_jacobian@direction) == pytest.approx(
        direction@(split.constraint_jacobian.T@density),abs=1e-12)
    with pytest.raises(ValueError,match="ordered unique"):
        assemble_channel_split_reference_kkt(
            shell,beam,coarse_intervals=2,fine_intervals=4,
            fine_channels=(3,3),**options)


def test_split_mx_dual_norm_matches_coarse_transverse_control():
    kwargs=dict(n_s=2,n_y=4,native_half_cells=4)
    split=channel_split_reference_modes(
        "Q4",coarse_intervals=2,fine_intervals=4,
        fine_channels=(3,),**kwargs)
    coarse=chord_reference_modes(
        "Q4",2,"piecewise_constant",
        shell_port="physical_strip_005_005",**kwargs)
    assert split["row_rank"] == split["row_count"] == 14
    assert split["decomposition_relative_error"] < 1e-9
    assert split["gram_relative_enclosure"] < 1e-3
    assert split["transverse_beta_lower"] == pytest.approx(
        coarse["density_dual_diagnostic"]["transverse_beta_lower"],rel=1e-10)
    assert split["weakest_channel_dual_norm_shares_fz_mx_my"][0] > .3


def test_split_mx_recovers_fine_torque_without_refining_transverse_force():
    kwargs=dict(shell_port="physical_strip_005_005",n_s=2,n_y=4,
                native_half_cells=4,shell_support_policy="full_left_edge")
    refined=dict(fine_intervals=4,fine_channels=(3,))
    torque_fine=one_case("Q4",4,"piecewise_constant",
                         load_kind="torsion",**kwargs)
    torque_split=one_case("Q4",2,"piecewise_constant",
                          load_kind="torsion",**refined,**kwargs)
    shear_coarse=one_case("Q4",2,"piecewise_constant",
                          load_kind="transverse_force_z",**kwargs)
    shear_split=one_case("Q4",2,"piecewise_constant",
                         load_kind="transverse_force_z",**refined,**kwargs)
    assert torque_split["tip_rx_rad"] == pytest.approx(
        torque_fine["tip_rx_rad"],rel=1e-9)
    assert shear_split["beam_tip_uz_m"] == pytest.approx(
        shear_coarse["beam_tip_uz_m"],rel=1e-9)
    for result in (torque_split,shear_split):
        assert result["shell_component_physical_energy_j"] > 0.
        assert abs(result["shell_numerical_energy_j"]) < 1e-12
        assert abs(result["global_work_error_j"]) < 1e-10
        assert abs(result["global_torque_x_balance_n_m"]) < 1e-8
        assert abs(result["global_force_z_balance_n"]) < 1e-8


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("shell_port", (
    "physical_strip_005_005", "physical_strip_line_origin_005_005"))
def test_split_mx_weak_work_matches_actual_chart_derivatives(
        topology, shell_port):
    shell=FlatE4TrialPanel(make_shell(1,topology,n_y=4))
    beam=build(4)
    rng=np.random.default_rng(731)
    shape=(shell.panel.node_count,6)
    reference=np.zeros(shape)
    current=rng.normal(scale=.001,size=shape)
    first=rng.normal(scale=.01,size=shape)
    second=rng.normal(scale=.01,size=shape)
    beam_base=np.zeros(beam.context.count)
    beam_base[6:12]=(.001,-.002,.0015,.01,-.007,.004)
    beam_base[beam.context.nodal_count+3:beam.context.nodal_count+6]=(
        .012,-.008,.006)
    state=beam.context.advance(beam.context.initial.mechanical,beam_base)
    beam_first=np.zeros_like(beam_base)
    beam_second=np.zeros_like(beam_base)
    beam_first[6:12]=(.02,-.01,.015,.03,-.02,.01)
    beam_first[beam.context.nodal_count+3:beam.context.nodal_count+6]=(
        .04,-.03,.02)
    beam_second[12:18]=(-.015,.02,-.01,-.02,.01,.025)
    beam_second[beam.context.nodal_count+6:beam.context.nodal_count+9]=(
        -.02,.03,-.01)
    coefficients=np.linspace(-12.,11.,14)
    def work(a,b,with_directions=False):
        moved=beam.context.advance(state,a*beam_first+b*beam_second)
        return integrate_channel_split_weak_line(
            shell,beam,2,4,(3,),coefficients,reference.ravel(),
            (current+a*first+b*second).ravel(),
            first if with_directions else np.zeros_like(first),
            second if with_directions else np.zeros_like(second),
            moved,beam_first if with_directions else np.zeros_like(beam_first),
            beam_second if with_directions else np.zeros_like(beam_second),
            shell_port=shell_port)
    result=work(0.,0.,True)
    assert result.potential == pytest.approx(
        coefficients@result.weak_constraints,abs=2e-10)
    assert result.first == pytest.approx(
        coefficients@result.weak_first,abs=2e-9)
    assert result.second == pytest.approx(
        coefficients@result.weak_second,abs=2e-9)
    h=1e-5
    assert result.first == pytest.approx(
        (work(h,0.).potential-work(-h,0.).potential)/(2*h),
        rel=2e-6,abs=2e-8)
    assert result.second == pytest.approx(
        (work(0.,h).potential-work(0.,-h).potential)/(2*h),
        rel=2e-6,abs=2e-8)
    h=2e-3
    mixed=(work(h,h).potential-work(h,-h).potential-
           work(-h,h).potential+work(-h,-h).potential)/(4*h*h)
    assert result.mixed == pytest.approx(mixed,rel=5e-5,abs=5e-7)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("shell_port", (
    "physical_strip_005_005", "physical_strip_line_origin_005_005"))
def test_split_mx_reference_rows_match_nonlinear_first_variation(
        topology, shell_port):
    shell=FlatE4TrialPanel(make_shell(1,topology,n_y=4))
    beam=build(4)
    kkt=assemble_channel_split_reference_kkt(
        shell,beam,coarse_intervals=2,fine_intervals=4,
        fine_channels=(3,),shell_port=shell_port)
    rng=np.random.default_rng(1901)
    shell_first=rng.normal(scale=.001,size=(shell.panel.node_count,6))
    beam_first=rng.normal(scale=.001,size=beam.context.count)
    beam_first[list(beam.context.fixed)]=0.
    zeros_shell=np.zeros_like(shell_first)
    zeros_beam=np.zeros_like(beam_first)
    result=integrate_channel_split_weak_line(
        shell,beam,2,4,(3,),np.zeros(14),zeros_shell.ravel(),
        zeros_shell.ravel(),shell_first,zeros_shell,
        beam.context.initial.mechanical,beam_first,zeros_beam,
        shell_port=shell_port)
    direction=np.r_[shell_first.ravel(),beam_first]
    np.testing.assert_allclose(result.weak_first,
                               kkt.constraint_jacobian@direction,
                               rtol=2e-10,atol=2e-11)


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
@pytest.mark.parametrize("width,line_origin", (
    (WIDTH, False), (SQUARE, False), (SQUARE, True)))
def test_strip_finite_objectivity_chart_derivatives_and_shear(
        topology, width, line_origin):
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
        panel, station, rigid.ravel(), line_origin=line_origin, **width)
    np.testing.assert_allclose(position,
                               rigid_frame@(station, 0., 0.)+shift, atol=2e-12)
    np.testing.assert_allclose(frame, rigid_frame, atol=2e-12)

    rng = np.random.default_rng(3401)
    first = rng.normal(size=rigid.shape)*.04
    second = rng.normal(size=rigid.shape)*.04
    analytic = directional_pose_from_e4_total_strip(
        panel, station, rigid.ravel(), first, second,
        line_origin=line_origin, **width)

    def moved(a, b):
        return pose_from_e4_total_strip(
            panel, station, (rigid+a*first+b*second).ravel(),
            line_origin=line_origin, **width)

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
        panel, station, zero.ravel(), first, zero,
        line_origin=line_origin, **width)
    derivative = at_reference.frame_first
    spin = np.array((derivative[2, 1]-derivative[1, 2],
                     derivative[0, 2]-derivative[2, 0],
                     derivative[1, 0]-derivative[0, 1]))/2
    np.testing.assert_allclose(
        np.r_[at_reference.position_first, spin],
        reference_spatial_trace_strip(
            panel, station, line_origin=line_origin, **width)@first.ravel(),
        atol=2e-13)

    shear = np.zeros_like(rigid)
    shear[:, 2] = .07*nodes[:, 0]
    _, sheared_frame = pose_from_e4_total_strip(
        panel, station, shear.ravel(), line_origin=line_origin, **width)
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
