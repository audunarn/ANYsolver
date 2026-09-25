"""One bounded finite-chart gate for the six-resultant surface candidate."""

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_distributed_surface_finite import (
    FiniteSurfaceMomentPatch, finite_chart_screen,
)
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
