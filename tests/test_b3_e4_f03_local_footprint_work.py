"""Bounded actual E4/B3 footprint mechanics checks, not G0 acceptance."""

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from scripts._b3_e4_f03_shell_strip_pose_candidate import reference_spatial_trace_strip
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_local_footprint_work import (
    case, distributed_surface_patch_trace, distributed_surface_patch_trace_panel,
    graded_terminal_coupling, loaded_surface_patch_panel,
    structured_q4_patch_trace,
    structured_q4_point_shape,
)
from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def test_native_c1_terminal_reference_and_opening_shear_kkt():
    with threadpool_limits(limits=1):
        beam = build(12, z_offset=.0675,
                     torsion_constant=square_torsion_constant(),
                     reference_profile="c1_tangent_2um")
        positions = (beam.context.initial.mechanical.positions+
                     beam.context.initial.mechanical.position_low)
        for station, expected_z in ((0., .067502), (.75, .067502),
                                    (.825, .067501), (.9, .0675),
                                    (1., .0675)):
            index = int(np.argmin(abs(beam.abscissae-station)))
            assert beam.abscissae[index] == pytest.approx(station, abs=1e-14)
            assert positions[index, 2] == pytest.approx(expected_z, abs=1e-13)
        assert beam.dense_oracle_max_error < 1e-9
        assert np.max(np.abs(beam.residual)) < 1e-9
        tangent = beam.pose(.825)[1][:, 0]
        assert tangent[2]/tangent[0] == pytest.approx(
            -4*2e-6*.5/.15, abs=1e-11)
        result = graded_terminal_coupling(
            2, beam, plate_thickness=.035,
            include_surface_moments=True, include_line_hybrid=True,
            include_line_hybrid_segmented=True,
            include_line_hybrid_ablation=True,
            force_sign=-1.)
    for family in ("distributing", "rigid"):
        case = result["results"][family]["cases"]["tip_fz"]
        assert case["tip_uz_m"] < 0.
        assert case["total_external_work_j"] == pytest.approx(
            -1000.*case["tip_uz_m"], rel=1e-10)
        assert (case["shell_support_wrench_N_Nm"][2]+
                case["beam_root_wrench_N_Nm"][2]) == pytest.approx(
            1000., abs=1e-7)
        assert case["mechanics_error"] < 1e-7
    physical = result["results"]["surface_moments"]["cases"]["tip_mx"]
    assert physical["total_external_work_j"] == pytest.approx(
        100.*physical["tip_rx_rad"], rel=1e-10)
    assert physical["physical_shell_work_j"] > 0.
    assert abs(physical["numerical_shell_work_j"]) < (
        1e-3*physical["physical_shell_work_j"])
    assert (physical["shell_support_wrench_N_Nm"][3]+
            physical["beam_root_wrench_N_Nm"][3]) == pytest.approx(
        -100., abs=1e-7)
    assert physical["mechanics_error"] < 1e-7
    for load in ("tip_mx", "tip_fz"):
        gap = result["results"]["surface_moments"]["cases"][load][
            "surface_point_gap"]
        assert max(abs(value) for value in gap["weak_six_gap_m_rad"]) < 1e-9
        assert gap["quadrature_rms_position_gap_m"] > 0.
    hybrid = result["results"]["line_hybrid_single_interval"]
    assert hybrid["constraint_rank"] == 6
    for load, magnitude in (("tip_mx", 100.), ("tip_fz", -1000.)):
        case = hybrid["cases"][load]
        displacement = (case["tip_rx_rad"] if load == "tip_mx"
                        else case["tip_uz_m"])
        assert case["total_external_work_j"] == pytest.approx(
            magnitude*displacement, rel=1e-10)
        assert case["physical_shell_work_j"] > 0.
        assert case["mechanics_error"] < 1e-7
    for name, rows in (("line_hybrid_common_alt_fz", 7),
                       ("line_hybrid_common_alt_fx", 7),
                       ("line_hybrid_common_alt_my", 7),
                       ("line_hybrid_common_alt_fx_my", 8),
                       ("line_hybrid_common_alt_except_fz", 11),
                       ("line_hybrid_common_alt_fy_mx_mz", 9)):
        family = result["results"][name]
        assert family["constraint_rank"] == rows
        for load, magnitude in (("tip_mx", 100.), ("tip_fz", -1000.)):
            case = family["cases"][load]
            displacement = (case["tip_rx_rad"] if load == "tip_mx"
                            else case["tip_uz_m"])
            assert case["total_external_work_j"] == pytest.approx(
                magnitude*displacement, rel=1e-10)
            assert case["mechanics_error"] < 1e-7
    segmented = result["results"]["line_hybrid_two_intervals"]
    assert segmented["constraint_rank"] == 12
    for load, magnitude in (("tip_mx", 100.), ("tip_fz", -1000.)):
        case = segmented["cases"][load]
        displacement = (case["tip_rx_rad"] if load == "tip_mx"
                        else case["tip_uz_m"])
        assert case["total_external_work_j"] == pytest.approx(
            magnitude*displacement, rel=1e-10)
        assert len(case["constraint_multiplier_material_N_Nm"]) == 12
        assert np.isfinite(case["constraint_multiplier_material_N_Nm"]).all()
        stations = case["terminal_station_kinematics"]
        assert set(stations) == {"900", "950", "1000"}
        assert stations["1000"]["beam_section_rx_rad"] == pytest.approx(
            case["beam_section_rx_at_stations_rad"]["1000"], abs=1e-12)
        assert all(np.isfinite(list(values.values())).all()
                   for values in stations.values())
        assert case["physical_shell_work_j"] > 0.
        assert case["mechanics_error"] < 1e-7


def test_structured_patch_trace_matches_existing_uniform_native_rows():
    panel=make_shell(8,"Q4",n_y=8)
    xs=np.linspace(-.5,1.5,17)
    ys=np.linspace(-.5,.5,9)
    trace=structured_q4_patch_trace(xs,ys)
    native=reference_spatial_trace_strip(
        panel,.95,half_length=.05,half_width=.05)
    assert np.max(np.abs(trace-native))<1e-12
    for x in (.9,1.):
        for y in (-.05,.05):
            nodes,values=structured_q4_point_shape(xs,ys,x,y)
            expected_nodes,expected_values=panel._shape(x,y)
            observed=np.bincount(nodes,weights=values,
                                 minlength=panel.node_count)
            expected=np.bincount(expected_nodes,weights=expected_values,
                                 minlength=panel.node_count)
            assert np.max(np.abs(observed-expected))<1e-12


def test_distributed_surface_moments_preserve_physical_work_and_shear():
    beam=build(8,z_offset=.0675,
               torsion_constant=square_torsion_constant())
    xs,ys=local_grid(4)
    trace,reference=distributed_surface_patch_trace(
        xs,ys,beam,plate_thickness=.035)
    shell_size=6*len(xs)*len(ys)
    assert trace.shape==(6,shell_size+beam.context.count)
    assert np.linalg.matrix_rank(trace)==6
    assert reference["reference_gap_m"]<1e-12
    assert reference["area_m2"]==pytest.approx(.01,abs=1e-12)
    assert np.max(np.abs(trace[:,:shell_size][:,5::6]))==0.

    common=np.zeros(trace.shape[1])
    translation=np.array((.001,-.002,.003))
    rotation=np.array((.004,-.005,.006))
    for j,y in enumerate(ys):
        for i,x in enumerate(xs):
            k=6*(j*len(xs)+i)
            common[k:k+3]=translation+np.cross(rotation,(x,y,0.))
            common[k+3:k+6]=rotation
    for i in range(beam.n_half_cells+1):
        k=shell_size+6*i
        common[k:k+3]=translation+np.cross(
            rotation,(i/beam.n_half_cells,0.,.0675))
        common[k+3:k+6]=rotation
    for element in range(beam.n_half_cells//2):
        for cell in (0,1):
            k=shell_size+beam.context.nodal_count+24*element+3*cell
            common[k:k+3]=rotation
    assert np.max(np.abs(trace@common))<1e-12

    transverse=np.zeros_like(common)
    for j,y in enumerate(ys):
        for i in range(len(xs)):
            transverse[6*(j*len(xs)+i)+2]=1e-5*y
    assert (trace@transverse)[3]==pytest.approx(1e-5,abs=1e-14)
    director=np.zeros_like(common)
    director[3:shell_size:6]=1e-5
    gap=trace@director
    assert gap[1]==pytest.approx(-.0175e-5,abs=1e-14)
    assert np.max(np.abs(gap[3:]))<1e-14


@pytest.mark.parametrize("topology", ["Q4", "S3-V2D"])
def test_host_clipped_surface_moments_reproduce_six_physical_actions(topology):
    beam = build(8, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    panel = FlatE4TrialPanel(make_shell(4, topology, n_y=4,
                                       thickness=.035))
    rows, reference = distributed_surface_patch_trace_panel(panel, beam)
    xs = np.linspace(-.5, 1.5, 9)
    ys = np.linspace(-.5, .5, 5)
    shell_size = 6*panel.panel.node_count
    assert rows.shape == (6, shell_size+beam.context.count)
    assert np.linalg.matrix_rank(rows) == 6
    assert reference["reference_gap_m"] < 1e-12
    assert reference["area_m2"] == pytest.approx(.01, abs=1e-12)
    assert reference["shell_drilling_column_max"] == 0.

    if topology == "Q4":
        old, _ = distributed_surface_patch_trace(
            xs, ys, beam, plate_thickness=.035)
        assert np.max(np.abs(rows-old)) < 1e-12

    # An affine top-surface displacement t + omega x arm must reproduce
    # six independent force/moment work coordinates on either host family.
    displacement = np.zeros(rows.shape[1])
    translation = np.array((.001, -.002, .003))
    rotation = np.array((.004, -.005, .006))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            k = 6*(j*len(xs)+i)
            displacement[k:k+3] = translation + np.cross(
                rotation, (x-.95, y, 0.))
    np.testing.assert_allclose(rows@displacement,
                               np.r_[translation, rotation], atol=1e-12)

    # Rigidly moving both domains causes no work. Leaving the shell director
    # fixed while varying transverse displacement remains an admissible shear.
    common = np.zeros_like(displacement)
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            k = 6*(j*len(xs)+i)
            common[k:k+3] = translation + np.cross(rotation, (x, y, 0.))
            common[k+3:k+6] = rotation
    for i in range(beam.n_half_cells+1):
        k = shell_size+6*i
        common[k:k+3] = translation + np.cross(
            rotation, (i/beam.n_half_cells, 0., .0675))
        common[k+3:k+6] = rotation
    for element in range(beam.n_half_cells//2):
        for cell in (0, 1):
            k = shell_size+beam.context.nodal_count+24*element+3*cell
            common[k:k+3] = rotation
    assert np.max(np.abs(rows@common)) < 1e-12

    shear = np.zeros_like(displacement)
    for j, y in enumerate(ys):
        for i in range(len(xs)):
            shear[6*(j*len(xs)+i)+2] = 1e-5*y
    assert (rows@shear)[3] == pytest.approx(1e-5, abs=1e-14)


@pytest.mark.parametrize("topology", ["Q4", "S3-V2D"])
def test_loaded_surface_patch_panel_keeps_work_gap_and_support_balance(topology):
    result = loaded_surface_patch_panel(topology, 4)
    assert result["kkt_rows"] < 1000
    for response in result["loads"].values():
        assert response["scaled_equilibrium_residual"] < 1e-9
        assert response["weak_gap_norm"] < 1e-12
        assert response["work_error_j"] < 1e-9
        assert response["load_work_j"] > 0.
        assert response["physical_shell_work_j"] > 0.
        assert response["global_force_balance_n"] < 1e-7
        assert response["global_moment_balance_nm"] < 1e-7
    torque = result["loads"]["tip_mx_100nm"]
    assert (torque["plate_support_moment_nm"][0]+
            torque["beam_root_support_moment_nm"][0]) == pytest.approx(
                -100., abs=1e-7)
    shear = result["loads"]["tip_fz_1000n"]
    assert (shear["plate_support_moment_nm"][1]+
            shear["beam_root_support_moment_nm"][1]) == pytest.approx(
                1000., abs=1e-7)


@pytest.mark.parametrize("topology", ["Q4", "S3-V2D"])
def test_distinct_footprint_work_and_finite_rigid_pullback(topology):
    result = case(topology)
    mode = result["supported_shell_transverse_shear_mode"]
    chart = result["finite_rigid_chart"]
    distributing = result["finite_distributing_chart"]
    termination = result["tip_termination_local"]
    assert mode["distributing_gap_max_m_rad"] < 2e-12
    assert mode["rigid_gap_l2_m"] > 1e-5
    assert abs(result["paired_shell_my_nm"]["rigid"] - 100.) < 1e-8
    assert abs(chart["mixed_hessian_j"]) > 1e-3
    assert chart["mixed_error_j"] < 1e-5
    assert chart["objective_gap_work_error"] < 1e-10
    assert chart["force_balance_n"] < 1e-9
    assert chart["moment_balance_nm"] < 1e-9
    assert chart["physical_work_error_j"] < 1e-9
    assert abs(distributing["mixed_hessian_j"]) > 1e-3
    assert distributing["first_error_j"] < 1e-6
    assert distributing["mixed_error_j"] < 1e-5
    assert distributing["force_balance_n"] < 1e-9
    assert distributing["moment_balance_nm"] < 1e-9
    assert distributing["physical_work_error_j"] < 1e-9
    assert termination["rows_and_supported_ranks"] == {
        "distributing": [6, 6], "rigid": [12, 12]}
    assert termination["reference_gap_max"] < 1e-12
    assert abs(termination["shell_my_nm"]["distributing"]-100.) < 1e-8
    assert abs(termination["shell_my_nm"]["rigid"]-100.) < 1e-8
    loaded = termination["loaded_linear_reference"]
    for family in ("distributing", "rigid"):
        for action in ("torque_mx_100nm", "shear_fz_1000n"):
            response = loaded[family][action]
            assert response["scaled_equilibrium_residual"] < 1e-9
            assert response["weak_gap_norm"] < 1e-9
            assert response["work_error_j"] < 1e-9
            assert response["global_force_balance_n"] < 1e-7
            assert response["global_moment_balance_nm"] < 1e-7
    assert abs(loaded["distributing"]["torque_mx_100nm"]["tip_rx_rad"] -
               loaded["rigid"]["torque_mx_100nm"]["tip_rx_rad"]) > 1e-7
    assert abs(loaded["distributing"]["shear_fz_1000n"]["tip_uz_m"] -
               loaded["rigid"]["shear_fz_1000n"]["tip_uz_m"]) > 1e-7
