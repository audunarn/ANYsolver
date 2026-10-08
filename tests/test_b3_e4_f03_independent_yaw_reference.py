"""Physical checks for the bounded independent in-plane yaw comparator."""

import numpy as np

from scripts.b3_e4_f03_independent_transverse_reference import (
    beam_basis, plate_basis,
)
from scripts.b3_e4_f03_independent_yaw_reference import (
    E, I, assemble, interface_stability, local_yaw_trace_boundary_layer,
    shell_chord_trace, shell_local_trace, shell_strip_trace, solve,
)
from scripts.b3_e4_f03_local_frame_joint_screen import physical_only_yaw


def test_local_yaw_matches_independent_displacement_difference():
    nx, ny, station = 5, 4, .31
    size = len(plate_basis(nx, ny, station, 0., basis="spline")[0])
    rng = np.random.default_rng(428)
    q = rng.standard_normal(2*size)*1e-4
    h = 1e-5

    def displacement(x, y):
        values = plate_basis(nx, ny, x, y, basis="spline")[0]
        return np.array((values@q[:size], values@q[size:]))

    uy_x = (displacement(station+h, 0.)[1]
            -displacement(station-h, 0.)[1])/(2*h)
    ux_y = (displacement(station, h)[0]
            -displacement(station, -h)[0])/(2*h)
    assert np.isclose(shell_local_trace(nx, ny, station)[2]@q,
                      .5*(uy_x-ux_y), rtol=2e-8, atol=1e-12)


def test_independent_beam_only_tip_moment_matches_cantilever():
    _, beam, _, _ = assemble(4, 2, 8, 2)
    n = len(beam)//3
    tip, _ = beam_basis(8, 1., basis="spline")
    force = np.zeros(len(beam))
    force[2*n:] = 100*tip
    q = np.linalg.solve(beam, force)
    assert np.isclose(tip@q[2*n:], 100/(E*I), rtol=1e-9)


def test_matched_yaw_work_balance_and_physical_stability():
    coarse = solve(8, 4, 8, 2)
    fine = solve(8, 4, 8, 4)
    for result in (coarse, fine):
        assert result["tip_rz_rad"] > 0.
        assert result["shell_energy_j"] > 0.
        assert abs(result["work_error_j"]) < 1e-12
        assert abs(result["global_moment_balance_n_m"]) < 1e-9
    assert fine["tip_rz_rad"] < coarse["tip_rz_rad"]
    for intervals in (2, 4):
        for kind in ("p0", "p1", "dual"):
            spectrum = interface_stability(8, 4, 8, intervals, kind=kind)
            assert spectrum["rank"] == spectrum["rows"]
            assert spectrum["normalized_beta_min"] > 0.
            lower, upper = spectrum["h_minus_half_eigen_min_bracket"]
            assert 0. < lower <= upper
            assert spectrum["h_minus_half_tail_relative"] < 1e-6
    assert not np.isclose(solve(8, 4, 8, 4, kind="p1")["tip_rz_rad"],
                          solve(8, 4, 8, 4, kind="dual")["tip_rz_rad"],
                          rtol=1e-2, atol=0.)


def test_native_physical_only_yaw_attribution_has_consistent_work():
    result = physical_only_yaw("Q4", "piecewise_constant")
    assert result["tip_rz_rad"] > 0.
    assert result["shell_physical_energy_j"] > 0.
    assert abs(result["work_error_j"]) < 1e-12
    assert result["scaled_residual"] < 1e-10


def test_zero_width_local_normal_gradient_is_not_energy_bounded():
    witnesses = [local_yaw_trace_boundary_layer(width)
                 for width in (.2, .1, .05, .025)]
    assert all(result["centerline_yaw_rad"] == -5e-5
               for result in witnesses)
    assert all(right["physical_membrane_energy_j"]
               < .51*left["physical_membrane_energy_j"]
               for left, right in zip(witnesses[:-1], witnesses[1:]))


def test_finite_strip_yaw_is_area_average_and_stability_is_channel_aware():
    nx = ny = 2
    station = .37
    points = [(x, y) for x in np.linspace(-.3, 1.4, nx+2)
              for y in np.linspace(-.5, .5, ny+3)]
    collocation = np.array([
        plate_basis(nx, ny, x, y, basis="spline")[0]
        for x, y in points])
    uy = np.linalg.solve(collocation,
                         [(x+.5)**3 for x, _ in points])
    q = np.r_[np.zeros_like(uy), uy]
    expected = 1.5*((station+.5)**2+.2**2/3)
    np.testing.assert_allclose(
        shell_strip_trace(nx, ny, station)[2]@q, expected,
        atol=2e-14)
    assert abs(shell_local_trace(nx, ny, station)[2]@q-expected) > .01

    result = solve(8, 4, 8, 4, trace_kind="strip_020_023")
    assert result["tip_rz_rad"] > 0.
    assert abs(result["work_error_j"]) < 1e-12
    assert abs(result["global_moment_balance_n_m"]) < 1e-9
    spectrum = interface_stability(8, 4, 8, 4,
                                   trace_kind="strip_020_023")
    assert spectrum["rank"] == spectrum["rows"]
    assert spectrum["lowest_mode_channel_l2"][0] > .99
    assert spectrum["single_channel_beta_min_ux_uy_yaw"][2] > 0.


def test_independent_line_chord_uses_only_displacement_trace():
    nx = ny = 2
    station = .37
    points = [(x, y) for x in np.linspace(-.3, 1.4, nx+2)
              for y in np.linspace(-.5, .5, ny+3)]
    collocation = np.array([
        plate_basis(nx, ny, x, y, basis="spline")[0]
        for x, y in points])
    ux = np.linalg.solve(collocation, [(x+.5)*y for x, y in points])
    uy = np.linalg.solve(collocation, [(x+.5)**3 for x, _ in points])
    trace = shell_chord_trace(nx, ny, station)
    expected = 3*(station+.5)**2+.2**2
    np.testing.assert_allclose(trace[2]@np.r_[ux, uy], expected,
                               atol=2e-14)
    confined = shell_chord_trace(nx, ny, station, confined=True)
    confined_midpoint = .6*station+.2
    np.testing.assert_allclose(
        confined[2]@np.r_[ux, uy],
        3*(confined_midpoint+.5)**2+.2**2, atol=2e-14)
    assert trace[2]@np.r_[ux, np.zeros_like(uy)] == 0.
    assert abs(shell_local_trace(nx, ny, station)[2]@
               np.r_[ux, np.zeros_like(uy)]) > .4

    result = solve(8, 4, 8, 4, trace_kind="chord_020")
    assert result["tip_rz_rad"] > 0.
    assert abs(result["work_error_j"]) < 1e-12
    assert abs(result["global_moment_balance_n_m"]) < 1e-9
    spectrum = interface_stability(8, 4, 8, 4,
                                   trace_kind="chord_020")
    assert spectrum["rank"] == spectrum["rows"]
    assert spectrum["lowest_mode_channel_l2"][0] > .99
    confined_result = solve(8, 4, 8, 4,
                            trace_kind="confined_chord_020")
    assert confined_result["tip_rz_rad"] > 0.
    assert abs(confined_result["work_error_j"]) < 1e-12
