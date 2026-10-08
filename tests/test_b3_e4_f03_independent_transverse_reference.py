"""Analytical and assembled checks for the independent F03 transverse model."""

import numpy as np
import pytest

from scripts.b3_e4_f03_independent_transverse_reference import (
    BENDING_D, BEAM_I, BEAM_J, BEAM_SHEAR_AREA, E, G,
    assemble, beam_basis, beam_strain_rows, plate_basis,
    plate_strain_rows, shell_trace, solve)


def test_supported_plate_twist_patch_has_analytical_energy_and_zero_shear():
    kappa = .001
    ks, _, _, _, _, _ = assemble(2, 2, 2, 2)
    q = np.zeros(12)
    # w=kappa*(x+.5)^2*y, rx=kappa*(x+.5)^2,
    # ry=-2*kappa*(x+.5)*y; all vanish on the fixed x=-.5 edge.
    q[1] = q[3] = kappa
    q[4] = q[6] = 2*kappa
    q[8+1] = -2*kappa
    expected = BENDING_D*kappa**2*(1+32*(1-.3))/3
    np.testing.assert_allclose(.5*q@ks@q, expected, rtol=1e-12)
    for x, y in ((-.3, -.21), (.27, .11), (1.21, .35)):
        value, _, _ = plate_basis(2, 2, x, y)
        np.testing.assert_allclose(value@q[:4],
                                   kappa*(x+.5)**2*y, atol=1e-16)
        bending, shear = plate_strain_rows(2, 2, x, y)
        np.testing.assert_allclose(shear@q, 0., atol=1e-15)
        np.testing.assert_allclose(bending@q,
                                   (2*kappa*y, 0., 2*kappa*(x+.5)),
                                   atol=1e-15)


def test_rooted_beam_torsion_bending_and_shear_patches():
    _, kb, _, _, _, _ = assemble(2, 2, 2, 2)
    kappa = .001
    torsion = np.zeros(6)
    torsion[2] = kappa  # rx=kappa*s
    np.testing.assert_allclose(.5*torsion@kb@torsion,
                               .5*G*BEAM_J*kappa**2, rtol=1e-12)
    bending = np.zeros(6)
    bending[:2] = kappa/4  # w=kappa*s^2/2
    bending[4] = -kappa  # ry=-kappa*s
    np.testing.assert_allclose(.5*bending@kb@bending,
                               .5*E*BEAM_I*kappa**2, rtol=1e-12)
    shear = np.zeros(6)
    shear[0] = kappa  # w=kappa*s, ry=0
    np.testing.assert_allclose(.5*shear@kb@shear,
                               .5*G*BEAM_SHEAR_AREA*kappa**2, rtol=1e-12)
    for s in (.13, .57, .91):
        np.testing.assert_allclose(beam_strain_rows(2, s)@bending,
                                   (0., -kappa, 0.), atol=1e-15)
        value, _ = beam_basis(2, s)
        np.testing.assert_allclose(value@torsion[2:4],
                                   kappa*s, atol=1e-16)


def test_rail_and_local_traces_share_rigid_pose_but_are_distinct_fields():
    for origin in ("rail", "local"):
        trace = shell_trace(4, 4, .37, origin)
        assert trace.shape == (3, 48)
        # The rooted shell basis has no rigid coordinates, but each trace
        # must apply the same mean director variations to rx and ry.
        np.testing.assert_allclose(trace[1:],
                                   shell_trace(4, 4, .37, "rail")[1:])
    assert not np.allclose(shell_trace(4, 4, .37, "rail")[0],
                           shell_trace(4, 4, .37, "local")[0])


def test_square_strip_trace_is_distinct_and_default_geometry_is_preserved():
    old = shell_trace(4, 4, .37, "strip", director="strip")
    explicit = shell_trace(4, 4, .37, "strip", director="strip",
                           strip_half_length=.2, strip_half_width=.23)
    square = shell_trace(4, 4, .37, "strip", director="strip",
                         strip_half_length=.05, strip_half_width=.05)
    np.testing.assert_allclose(old, explicit, rtol=0., atol=1e-14)
    assert np.linalg.norm(square-old) > 1e-4
    with pytest.raises(ValueError, match="strip half dimensions"):
        shell_trace(4, 4, .37, "strip", strip_half_length=0.)


@pytest.mark.parametrize("load", ("force_z", "torque_x"))
def test_square_strip_independent_torque_shear_work_and_balance(load):
    result = solve(
        4, 4, 4, 2, basis="spline", multiplier="p0",
        origin="strip", director="strip", strip_half_length=.05,
        strip_half_width=.05,
        tip_force_z=1000. if load == "force_z" else 0.,
        tip_torque_x=100. if load == "torque_x" else 0.)
    assert result["shell_energy_j"] > 0.
    assert result["beam_energy_j"] > 0.
    assert abs(result["work_error_j"]) < 1e-10
    assert abs(result["balance_fz_n"]) < 1e-9
    assert abs(result["balance_mx_n_m"]) < 1e-9
    assert abs(result["balance_my_n_m"]) < 1e-9


@pytest.mark.parametrize("origin", ("rail", "local"))
@pytest.mark.parametrize("load", ("force_z", "torque_x"))
def test_loaded_reference_equilibrium_work_and_wrench_balance(origin, load):
    result = solve(4, 4, 4, 4, origin=origin,
                   tip_force_z=1000. if load == "force_z" else 0.,
                   tip_torque_x=100. if load == "torque_x" else 0.)
    assert result["matrix_size"] == 75
    assert result["matrix_condition"] < 1e9
    assert result["scaled_equation_residual"] < 1e-9
    assert result["weak_gap_l2"] < 1e-10
    assert abs(result["work_error_j"]) < 1e-10
    assert abs(result["balance_fz_n"]) < 1e-9
    assert abs(result["balance_mx_n_m"]) < 1e-9
    assert abs(result["balance_my_n_m"]) < 1e-9
    assert result["shell_energy_j"] > 0.
    assert result["beam_energy_j"] > 0.
    if load == "force_z":
        assert result["tip_z_m"] > 0.
    else:
        assert result["tip_rx_rad"] > 0.


def test_independent_weak_rows_full_rank_on_small_case():
    for origin in ("rail", "local"):
        for multiplier in ("p0", "p1"):
            ks, kb, c, moments, first, _ = assemble(
                4, 4, 4, 4, origin=origin, multiplier=multiplier)
            assert ks.shape == (48, 48)
            assert kb.shape == (12, 12)
            assert np.linalg.matrix_rank(c) == len(c)
            assert np.linalg.norm(ks-ks.T)/np.linalg.norm(ks) < 1e-12
            assert np.linalg.norm(kb-kb.T)/np.linalg.norm(kb) < 1e-12
            np.testing.assert_allclose(np.sum(moments), 1., atol=1e-14)
            np.testing.assert_allclose(np.sum(first), .5, atol=1e-14)


def test_line_resolution_rejects_dependent_rows_and_exposes_weak_null_mode():
    with pytest.raises(ValueError, match="exceed the polynomial trace image"):
        assemble(6, 6, 6, 8, multiplier="p1")

    ks, _, c, _, _, _ = assemble(6, 6, 8, 6, multiplier="p1")
    beam_rows = c[:, len(ks):]
    _, _, vectors = np.linalg.svd(beam_rows, full_matrices=True)
    weak_null = vectors[-1]
    assert np.linalg.norm(beam_rows@weak_null) < 1e-12
    n = 8
    stations = np.linspace(0., 1., 129)
    physical_gap = np.array([
        [beam_basis(n, float(s))[0]@weak_null[i*n:(i+1)*n]
         for i in range(3)] for s in stations])
    assert np.sqrt(np.trapezoid(np.sum(physical_gap**2, axis=1),
                                stations)) > 1e-6


def test_local_spline_support_and_analytical_plate_beam_patches():
    nx = ny = nb = 2
    kappa = .001
    xs = np.linspace(-.3, 1.4, nx+2)
    ys = np.linspace(-.5, .5, ny+3)
    points = [(x, y) for x in xs for y in ys]
    collocation = np.array([plate_basis(nx, ny, x, y, basis="spline")[0]
                            for x, y in points])
    q = np.zeros(3*len(collocation))
    xlocal = lambda x: x+.5
    target = (lambda x, y: kappa*xlocal(x)**2*y,
              lambda x, y: kappa*xlocal(x)**2,
              lambda x, y: -2*kappa*xlocal(x)*y)
    for channel, field in enumerate(target):
        q[channel*len(points):(channel+1)*len(points)] = np.linalg.solve(
            collocation, [field(x, y) for x, y in points])
    np.testing.assert_allclose(plate_basis(nx, ny, -.5, .13,
                                           basis="spline")[0], 0.)
    for x, y in ((-.3, -.21), (.27, .11), (1.21, .35)):
        bending, shear = plate_strain_rows(nx, ny, x, y, basis="spline")
        np.testing.assert_allclose(shear@q, 0., atol=1e-14)
        np.testing.assert_allclose(bending@q,
                                   (2*kappa*y, 0., 2*kappa*xlocal(x)),
                                   atol=1e-14)
    ks, kb, _, _, _, _ = assemble(nx, ny, nb, 4, basis="spline")
    expected = BENDING_D*kappa**2*(1+32*(1-.3))/3
    np.testing.assert_allclose(.5*q@ks@q, expected, rtol=1e-12)

    stations = np.linspace(.1, 1., nb+2)
    bm = np.array([beam_basis(nb, s, basis="spline")[0] for s in stations])
    bq = np.zeros(3*len(stations))
    bq[len(stations):2*len(stations)] = np.linalg.solve(
        bm, kappa*stations)
    np.testing.assert_allclose(beam_basis(nb, 0., basis="spline")[0], 0.)
    for s in (.13, .57, .91):
        np.testing.assert_allclose(beam_strain_rows(nb, s, basis="spline")@bq,
                                   (kappa, 0., 0.), atol=1e-14)
    np.testing.assert_allclose(.5*bq@kb@bq, .5*G*BEAM_J*kappa**2,
                               rtol=1e-12)


def test_local_spline_line_rank_limits_are_explicit():
    for origin in ("rail", "local"):
        for n, intervals in ((2, 4), (4, 6), (8, 10)):
            _, _, c, moments, first, _ = assemble(
                n, n, n, intervals, basis="spline", origin=origin)
            assert np.linalg.matrix_rank(c) == len(c)
            np.testing.assert_allclose(sum(moments), 1., atol=1e-14)
            np.testing.assert_allclose(sum(first), .5, atol=1e-14)
    for origin, intervals in (("rail", 16), ("local", 12)):
        with pytest.raises(ValueError, match="exceed the spline trace image"):
            assemble(8, 8, 8, intervals, basis="spline", origin=origin)


def test_independent_local_director_has_center_work_and_same_position():
    nx, ny, station = 3, 2, .37
    count = len(plate_basis(nx, ny, station, 0.)[0])
    q = np.zeros(3*count)
    # In the rooted global basis, 2*X*(1+P1)=4*X²=(x+.5)².
    q[count+0] = q[count+ny] = 2.
    rail = shell_trace(nx, ny, station, "local", director="rail")
    local = shell_trace(nx, ny, station, "local", director="local")
    np.testing.assert_array_equal(rail[0], local[0])
    np.testing.assert_allclose(local[1]@q, (station+.5)**2, atol=1e-14)
    np.testing.assert_allclose(rail[1]@q, (station+.5)**2+.2**2,
                               atol=1e-14)


def test_independent_finite_strip_means_quadratic_field_and_balances_loads():
    nx = ny = nb = 2
    xs = np.linspace(-.3, 1.4, nx+2)
    ys = np.linspace(-.5, .5, ny+3)
    points = [(x, y) for x in xs for y in ys]
    collocation = np.array([
        plate_basis(nx, ny, x, y, basis="spline")[0]
        for x, y in points])
    polynomial = np.array([(x+.5)**2 for x, _ in points])
    coefficients = np.linalg.solve(collocation, polynomial)
    q = np.r_[coefficients, coefficients, np.zeros_like(coefficients)]
    station = .37
    trace = shell_trace(nx, ny, station, "strip", basis="spline",
                        director="strip")
    expected = (station+.5)**2+.2**2/3
    np.testing.assert_allclose(trace@q, (expected, expected, 0.),
                               atol=2e-14)

    for force, torque in ((1000., 0.), (0., 100.)):
        result = solve(4, 4, 4, 2, origin="strip", director="strip",
                       multiplier="p0", basis="spline",
                       tip_force_z=force, tip_torque_x=torque)
        assert result["scaled_equation_residual"] < 1e-9
        assert result["weak_gap_l2"] < 1e-10
        assert abs(result["work_error_j"]) < 1e-10
        assert abs(result["balance_fz_n"]) < 1e-9
        assert abs(result["balance_mx_n_m"]) < 1e-9
        assert result["shell_energy_j"] > 0.
