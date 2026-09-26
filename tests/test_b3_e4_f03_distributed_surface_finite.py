"""One bounded finite-chart gate for the six-resultant surface candidate."""

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_distributed_surface_finite import (
    FiniteSurfaceLineHybrid, FiniteSurfaceMomentPatch, finite_chart_screen,
)
from anysolver.corotational import rotation_matrix_from_vector
from scripts.b3_e4_f03_local_footprint_work import (
    bond_x_segments, distributed_surface_patch_trace,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def test_actual_e4_b3_surface_work_has_consistent_finite_derivatives():
    result = finite_chart_screen()
    assert result["reference_gap_max_m_rad"] < 1e-12
    assert result["reference_jacobian_direction_error"] < 1e-12
    assert result["nonzero_gap_norm_m_rad"] > 1e-4
    assert abs(result["nonzero_multiplier_mixed_work_j"]) > 1e-3
    assert result["first_direction_error_j"] < 1e-7
    assert result["mixed_direction_error_j"] < 1e-6
    assert result["finite_common_rigid_gap_error"] < 1e-12
    assert abs(result["common_rigid_virtual_work_j"]) < 1e-9
    assert result["quadrature_points"] == 18


def test_reference_integration_splits_native_half_cell_inside_shell_host():
    assert bond_x_segments(.925, .95, 16) == (
        (.925, .9375), (.9375, .95))
    c1_stations = np.array((0., .75, .7875, .825, .8625, .9, 1.))
    assert bond_x_segments(.78, .85, c1_stations) == (
        (.78, .7875), (.7875, .825), (.825, .85))
    xs, ys = local_grid(4)
    beam = build(16, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    patch = FiniteSurfaceMomentPatch(xs, ys, beam, thickness=.035)
    assert len(patch.points) == 180
    trace, reference = distributed_surface_patch_trace(
        xs, ys, beam, plate_thickness=.035)
    assert abs(reference["area_m2"]-.01) < 1e-12
    first = np.zeros((patch.shell_count, 6))
    first[:, 2] = 1e-5*patch.reference_nodes[:, 1]
    beam_first = np.zeros(beam.context.count)
    direction = (first, beam_first)
    frames = np.broadcast_to(np.eye(3), (patch.shell_count, 3, 3)).copy()
    derivative = patch.evaluate(
        patch.reference_nodes, frames, beam.context.initial.mechanical,
        direction, direction)[:, 1]
    assert np.max(np.abs(derivative-trace@np.r_[first.ravel(), beam_first])) < 1e-12


def test_interval_surface_means_partition_without_reprojecting_reference():
    xs, ys = local_grid(2)
    beam = build(8, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    whole, full = distributed_surface_patch_trace(
        xs, ys, beam, plate_thickness=.035, x_interval=(0., 1.))
    left, first = distributed_surface_patch_trace(
        xs, ys, beam, plate_thickness=.035, x_interval=(0., .5))
    right, second = distributed_surface_patch_trace(
        xs, ys, beam, plate_thickness=.035, x_interval=(.5, 1.))
    assert max(full["reference_gap_m"], first["reference_gap_m"],
               second["reference_gap_m"]) < 1e-12
    assert abs(full["area_m2"]-.1) < 1e-12
    assert np.max(np.abs(whole[:3]-.5*(left[:3]+right[:3]))) < 1e-12


def test_c1_surface_moment_chart_matches_linearized_native_trace():
    xs, ys = local_grid(2)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    patch = FiniteSurfaceMomentPatch(xs, ys, beam, thickness=.035)
    trace, reference = distributed_surface_patch_trace(
        xs, ys, beam, plate_thickness=.035)
    assert reference["reference_gap_m"] < 1e-12
    frames = np.broadcast_to(np.eye(3), (patch.shell_count, 3, 3)).copy()
    shell_direction = np.zeros((patch.shell_count, 6))
    shell_direction[:, 2] = 1e-5*patch.reference_nodes[:, 1]
    beam_direction = np.zeros(beam.context.count)
    beam_direction[6*beam.n_half_cells+2] = 2e-5
    direction = (shell_direction, beam_direction)
    actual = patch.evaluate(
        patch.reference_nodes, frames, beam.context.initial.mechanical,
        direction, direction)
    assert np.max(np.abs(actual[:, 0])) < 1e-12
    expected = trace@np.r_[shell_direction.ravel(), beam_direction]
    assert np.max(np.abs(actual[:, 1]-expected)) < 1e-12


def test_c1_surface_moment_finite_chart_preserves_work_and_objectivity():
    result = finite_chart_screen("c1_tangent_2um")
    assert result["reference_profile"] == "c1_tangent_2um"
    assert result["reference_gap_max_m_rad"] < 1e-12
    assert result["reference_jacobian_direction_error"] < 1e-12
    assert abs(result["nonzero_multiplier_mixed_work_j"]) > 1e-3
    assert result["first_direction_error_j"] < 1e-7
    assert result["mixed_direction_error_j"] < 1e-6
    assert result["finite_common_rigid_gap_error"] < 1e-12
    assert abs(result["common_rigid_virtual_work_j"]) < 1e-9
    assert result["quadrature_points"] == 36


def test_six_surface_moments_leave_a_real_local_slip_mode():
    xs, ys = local_grid(2)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    patch = FiniteSurfaceMomentPatch(xs, ys, beam, thickness=.035)
    shell_step = np.zeros((patch.shell_count, 6))
    slope = 1e-5
    shell_step[:, 0] = slope*(patch.reference_nodes[:, 0]-.95)
    stats = patch.linearized_gap_statistics(
        shell_step, np.zeros(beam.context.count))
    assert np.max(np.abs(stats["weak_six_gap_m_rad"])) < 1e-12
    assert abs(stats["quadrature_rms_position_gap_m"]-
               slope*.1/np.sqrt(12)) < 1e-12
    assert stats["quadrature_max_position_gap_m"] > 0.


def test_c1_hybrid_six_channel_reference_is_distinct_and_non_drilling():
    xs, ys = local_grid(2)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    hybrid = FiniteSurfaceLineHybrid(xs, ys, beam, thickness=.035)
    old, _ = distributed_surface_patch_trace(
        xs, ys, beam, plate_thickness=.035)
    trace = hybrid.reference_trace()
    frames = np.broadcast_to(np.eye(3),
                             (hybrid.shell_count, 3, 3)).copy()
    state = beam.context.initial.mechanical
    assert len(hybrid.points) == 36
    assert np.max(np.abs(hybrid.evaluate(
        hybrid.reference_nodes, frames, state)[:, 0])) < 1e-12
    assert np.linalg.matrix_rank(trace) == 6
    assert np.max(np.abs(trace[:, 5:hybrid.shell_size:6])) < 1e-12

    # Terminal shell top positions stay fixed under this pitch field.
    # The old six position moments cannot see it; the new physical
    # director-pitch channel does.
    shell_step = np.zeros((hybrid.shell_count, 6))
    terminal = hybrid.reference_nodes[:, 0] >= .9-1e-12
    angle = 1e-5
    shell_step[terminal, 0] = -.0175*angle
    shell_step[terminal, 4] = angle
    direction = np.r_[shell_step.ravel(), np.zeros(beam.context.count)]
    assert np.max(np.abs(old@direction)) < 1e-12
    response = trace@direction
    assert abs(response[4]-angle) < 1e-12
    assert np.max(np.abs(np.delete(response, 4))) < 1e-12

    # A common transverse displacement slope with unchanged directors
    # leaves the connection closed while allowing shell shear.
    shell_step[:] = 0.
    shell_step[:, 2] = angle*hybrid.reference_nodes[:, 0]
    beam_step = np.zeros(beam.context.count)
    for i in range(beam.context.nodal_count//6):
        beam_step[6*i+2] = angle*beam.abscissae[i]
    shear = trace@np.r_[shell_step.ravel(), beam_step]
    assert np.max(np.abs(shear)) < 1e-12


def test_c1_hybrid_actual_chart_has_objective_first_and_mixed_work():
    result = finite_chart_screen("c1_tangent_2um", hybrid=True)
    assert result["hybrid"] is True
    assert result["quadrature_points"] == 36
    assert result["reference_gap_max_m_rad"] < 1e-12
    assert result["reference_jacobian_direction_error"] < 1e-12
    assert result["nonzero_gap_norm_m_rad"] > 1e-4
    assert abs(result["nonzero_multiplier_mixed_work_j"]) > 1e-3
    assert result["first_direction_error_j"] < 1e-7
    assert result["mixed_direction_error_j"] < 1e-6
    assert result["finite_common_rigid_gap_error"] < 1e-12
    assert abs(result["common_rigid_virtual_work_j"]) < 1e-9


def test_c1_hybrid_two_host_intervals_preserve_chart_work_and_rank():
    xs, ys = local_grid(2)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    intervals = ((.9, .95), (.95, 1.))
    pieces = [FiniteSurfaceLineHybrid(
        xs, ys, beam, thickness=.035, x_interval=interval)
        for interval in intervals]
    trace = np.vstack([piece.reference_trace() for piece in pieces])
    fixed_shell = {6*j*len(xs)+axis for j in range(len(ys))
                   for axis in range(6)}
    fixed_beam = {pieces[0].shell_size+index
                  for index in beam.context.fixed}
    free = [i for i in range(trace.shape[1])
            if i not in fixed_shell and i not in fixed_beam]
    assert [len(piece.points) for piece in pieces] == [18, 18]
    assert np.linalg.matrix_rank(trace[:, free]) == 12
    assert np.max(np.abs(trace[:, 5:pieces[0].shell_size:6])) < 1e-12
    for interval in intervals:
        result = finite_chart_screen(
            "c1_tangent_2um", hybrid=True, x_interval=interval)
        assert result["reference_gap_max_m_rad"] < 1e-12
        assert result["reference_jacobian_direction_error"] < 1e-12
        assert result["first_direction_error_j"] < 1e-7
        assert result["mixed_direction_error_j"] < 1e-6
        assert result["finite_common_rigid_gap_error"] < 1e-12
        assert abs(result["common_rigid_virtual_work_j"]) < 1e-9


def test_c1_hybrid_uses_actual_additive_e4_total_rotation_chart():
    xs, ys = local_grid(2)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    patch = FiniteSurfaceLineHybrid(
        xs, ys, beam, thickness=.035, x_interval=(.9, .95))
    rng = np.random.default_rng(2047)
    count = patch.shell_count
    total = rng.normal(size=(count, 6))*np.array(
        (.001, .001, .001, .08, .08, .08))
    first_shell = rng.normal(size=(count, 6))*np.array(
        (.002, .002, .002, .04, .04, .04))
    second_shell = rng.normal(size=(count, 6))*np.array(
        (.002, .002, .002, .04, .04, .04))
    beam_base = np.zeros(beam.context.count)
    beam_base[6:beam.context.nodal_count] = rng.normal(
        size=beam.context.nodal_count-6)*.001
    first_beam = rng.normal(size=beam.context.count)*.001
    second_beam = rng.normal(size=beam.context.count)*.001
    first_beam[:6] = 0.
    second_beam[:6] = 0.
    state = beam.context.advance(beam.context.initial.mechanical, beam_base)
    first = (first_shell, first_beam)
    second = (second_shell, second_beam)
    actual = patch.evaluate_e4_total(total.ravel(), state, first, second)
    multipliers = np.array((18., -23., 31., 7., -100., 13.))

    def work(a, b):
        candidate = beam.context.advance(
            state, a*first_beam+b*second_beam)
        shell = total+a*first_shell+b*second_shell
        return float(multipliers@patch.evaluate_e4_total(
            shell.ravel(), candidate)[:, 0])

    h1, h2 = 1e-5, 2e-3
    first_fd = (work(h1, 0.)-work(-h1, 0.))/(2*h1)
    second_fd = (work(0., h1)-work(0., -h1))/(2*h1)
    mixed_fd = (work(h2, h2)-work(h2, -h2)-
                work(-h2, h2)+work(-h2, -h2))/(4*h2*h2)
    assert abs(float(multipliers@actual[:, 1])-first_fd) < 1e-7
    assert abs(float(multipliers@actual[:, 2])-second_fd) < 1e-7
    assert abs(float(multipliers@actual[:, 3])-mixed_fd) < 1e-6
    assert np.linalg.norm(total[:, 3:]) > .1


def test_c1_hybrid_physical_director_spin_is_null_at_finite_tilt():
    xs, ys = local_grid(2)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    patch = FiniteSurfaceLineHybrid(xs, ys, beam, thickness=.035)
    rng = np.random.default_rng(710)
    theta = rng.normal(size=(patch.shell_count, 3))*.12
    frames = np.array([rotation_matrix_from_vector(value)
                       for value in theta])
    coordinates = patch.reference_nodes.copy()
    shell_spin = np.zeros((patch.shell_count, 6))
    shell_spin[:, 3:] = frames[:, :, 2]
    direction = (shell_spin, np.zeros(beam.context.count))
    response = patch.evaluate(
        coordinates, frames, beam.context.initial.mechanical,
        direction, direction)
    assert np.max(np.abs(response[:, 1:])) < 1e-12
