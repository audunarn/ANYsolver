"""Independent finite-dimensional work and exact-integration controls; no OpenSees."""
from fractions import Fraction as F
import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import r8_bl5_external_affine_reference_dev as affine


@pytest.fixture(scope="module")
def fixture():
    refinement, p0, frozen, service, reference = affine.services()
    model = refinement.geometry(16, reference)
    pairing = affine.aggregate_rows(model, reference)
    return refinement, p0, frozen, service, reference, model, pairing


def dense(rows, nodes):
    slots = {(n, d): 6*i+d-1 for i, n in enumerate(nodes) for d in range(1, 7)}
    matrix = np.zeros((len(rows), 6*len(nodes)))
    for i, row in enumerate(rows):
        for n, d, value in zip(row[::3], row[1::3], row[2::3]):
            matrix[i, slots[n, d]] += value
    return matrix, slots


@pytest.mark.parametrize("intervals,first", ((16, 1), (32, 100001)))
def test_signed_exact_weight_identities_and_independent_quadrature(intervals, first):
    left, right = F(1, 10), F(7, 10)
    knots = sorted({F(i, 32) for i in range(33)} | {F(i, 16) for i in range(17)})
    weights, pieces = affine.integrated_affine_weights(left, right, intervals, first, knots)
    assert sum(weights[0].values()) == right-left
    assert sum(weights[1].values()) == 0
    assert min(weights[1].values()) < 0 < max(weights[1].values())
    gauss, quadrature = np.polynomial.legendre.leggauss(3)
    expected = np.zeros((2, intervals+1))
    shape_knots = np.linspace(0., 1., intervals+1)
    # Integrate independently by evaluating nodal hats at interior Gauss points.
    for piece in pieces:
        a, b = piece["interval_m"]
        for xi, wi in zip(gauss, quadrature):
            x = (a+b)/2+(b-a)*xi/2
            basis = np.array((1., 2*(x-float(left))/float(right-left)-1.))
            for node in range(intervals+1):
                nodal = np.zeros(intervals+1); nodal[node] = 1.
                expected[:, node] += (b-a)*wi/2*basis*np.interp(x, shape_knots, nodal)
    actual = np.array([[float(w.get(first+i, 0)) for i in range(intervals+1)] for w in weights])
    np.testing.assert_allclose(actual, expected, rtol=3e-14, atol=2e-16)


def test_four_interval_support_weights_and_invisible_center():
    knots = [F(i, 32) for i in range(33)]
    weights, _ = affine.integrated_affine_weights(F(0), F(1, 8), 32, 100001, knots)
    h = F(1, 8)
    assert [weights[0][100001+i] for i in range(5)] == [h*v for v in (F(1,8),F(1,4),F(1,4),F(1,4),F(1,8))]
    assert [weights[1][100001+i] for i in range(5)] == [h*v for v in (-F(5,48),-F(1,8),F(0),F(1,8),F(5,48))]
    assert weights[1][100003] == 0  # A P0 center recovery loses a nonzero slope.


def test_emission_is_verified_invertible_row_transform_and_unique_free_dependencies(fixture):
    *_, model, pairing = fixture
    nodes = sorted(model["nodes"])
    c, slots = dense(pairing["physical_rows"], nodes)
    emitted, _ = dense(pairing["emitted_rows"], nodes)
    dependencies = [tuple(key) for s in pairing["supports"] for key in s["dependent_node_dofs"]]
    assert len(set(dependencies)) == len(pairing["physical_rows"]) == 80
    assert not any(model["fixes"].get(n, (0,)*6)[d-1] for n, d in dependencies)
    np.testing.assert_array_equal(emitted[:, [slots[key] for key in dependencies]], np.eye(80))
    for support in pairing["supports"]:
        ids = support["row_indices"]
        columns = [slots[tuple(key)] for key in support["dependent_node_dofs"]]
        d = c[np.ix_(ids, columns)]
        expected = np.linalg.solve(d, c[ids])
        np.testing.assert_allclose(emitted[ids], expected, rtol=2e-14, atol=2e-16)
        e = np.array(support["emitted_from_physical_E"])
        np.testing.assert_allclose(e@d, np.eye(10), atol=2e-16, rtol=0.)
    assert not np.any(c[:, 5::6])  # Released normal spin in all five channels.


def test_density_to_emitted_dual_and_noncompatible_virtual_work(fixture):
    *_, model, pairing = fixture
    nodes = sorted(model["nodes"])
    c, slots = dense(pairing["physical_rows"], nodes)
    emitted, _ = dense(pairing["emitted_rows"], nodes)
    rng = np.random.default_rng(833)
    lam, q = rng.normal(size=80), rng.normal(size=6*len(nodes))
    mu = np.zeros(80)
    for support in pairing["supports"]:
        ids = support["row_indices"]
        columns = [slots[tuple(key)] for key in support["dependent_node_dofs"]]
        mu[ids] = c[np.ix_(ids, columns)].T@lam[ids]
    np.testing.assert_allclose(emitted.T@mu, c.T@lam, rtol=2e-14, atol=2e-16)
    np.testing.assert_allclose(mu@emitted@q, lam@c@q, rtol=3e-14, atol=2e-16)
    field = {n: q[6*i:6*i+6] for i, n in enumerate(nodes)}
    resisted = affine.transpose_action(pairing["physical_rows"], lam, nodes)
    assert abs(sum(np.dot(resisted[n], field[n]) for n in nodes)-lam@c@q) < 2e-15


def test_all_channel_continuous_virtual_work_against_independent_point_gap(fixture):
    _, _, _, _, reference, model, pairing = fixture
    nodes = sorted(model["nodes"])
    rng = np.random.default_rng(622)
    field = {n: rng.normal(size=6) for n in nodes}
    lam = rng.normal(size=80)
    bx, sx = np.linspace(0., 1., 33), np.linspace(0., 1., 17)
    bq = np.array([field[n] for n in model["beam_node_ids"]])
    sq = np.array([field[n] for n in range(1, 18)])
    rb, rs = reference.BEAM_BOTTOM_ARM_M, reference.SHELL_THICKNESS_M/2
    gauss, weights = np.polynomial.legendre.leggauss(3)
    continuous_work = 0.
    for support in pairing["supports"]:
        a, b = support["interval_m"]
        coefficients = lam[support["row_indices"]].reshape(5, 2)
        for piece in support["beam_pieces"]:
            left, right = piece["interval_m"]
            for xi, weight in zip(gauss, weights):
                x = (left+right)/2+(right-left)*xi/2
                ub = np.array([np.interp(x, bx, bq[:, d]) for d in range(6)])
                us = np.array([np.interp(x, sx, sq[:, d]) for d in range(6)])
                gap = np.array((ub[0]-us[0]+rb*ub[4]-rs*us[4],
                    ub[1]-us[1]-rb*ub[3]+rs*us[3], ub[2]-us[2], ub[3]-us[3], ub[4]-us[4]))
                density = coefficients@np.array((1., 2*(x-a)/(b-a)-1.))
                continuous_work += (right-left)*weight/2*np.dot(density, gap)
    discrete_work = np.dot(lam, affine.row_action(pairing["physical_rows"], field))
    np.testing.assert_allclose(discrete_work, continuous_work, rtol=3e-14, atol=2e-16)


def test_known_synthetic_coefficients_recover_through_independent_arm_map(fixture):
    _, _, _, _, reference, model, pairing = fixture
    rng = np.random.default_rng(280)
    known = rng.normal(size=80)*200.
    resisting = {n: [0.]*6 for n in model["beam_node_ids"]}
    rb = reference.BEAM_BOTTOM_ARM_M
    for support in pairing["supports"]:
        coefficients = known[support["row_indices"]].reshape(5, 2)
        h = support["width_m"]
        for n, sign in zip(support["recovery_beam_nodes"], (-1., 1.)):
            weighted = coefficients@np.array((h/4, sign*h/8))
            resisting[n] = [*weighted[:3], weighted[3]-rb*weighted[1],
                             weighted[4]+rb*weighted[0], 0.]
    recovered, records = affine.recover_densities(pairing, resisting, rb)
    np.testing.assert_allclose(recovered, known, atol=2e-13, rtol=2e-15)
    assert max(abs(v) for record in records for v in record["residual"]) < 8e-15
    for support, record in zip(pairing["supports"], records):
        np.testing.assert_array_equal(np.array(record["actual_D_transpose"]),
                                      np.array(support["dependent_coefficient_block_D"]).T)


def test_affine_physical_wrench_moments_and_windows_are_analytic(fixture):
    _, _, _, _, reference, _, pairing = fixture
    density = np.zeros(80)
    # lambda_y=-x produces physical beam Fy=x and Mz=x^2 about the root.
    for support in pairing["supports"]:
        a, b = support["interval_m"]
        base = 10*support["support_id"]
        density[base+2:base+4] = (-(a+b)/2, -(b-a)/2)
    measures = affine.density_measures(pairing["supports"], density.tolist(), reference)
    for k in range(4):
        np.testing.assert_allclose(measures["polynomial_x_moments"][str(k)],
            (0., 1/(k+2), 0., -reference.BEAM_BOTTOM_ARM_M/(k+2), 0., 1/(k+3)), atol=2e-16, rtol=2e-15)
    assert measures["polynomial_x_moments"]["3"][1] == pytest.approx(.2, abs=1e-16)
    # This observable would be wrong under the production two-point Gauss rule.
    x, w = np.polynomial.legendre.leggauss(2)
    wrong = np.dot(w/2, ((x+1)/2)**4)
    assert abs(wrong-.2) > .005
    windows = measures["fixed_region_025_075"]
    assert windows["open"] == windows["closed"]
    assert windows["endpoint_atoms"] == [0.]*6
    np.testing.assert_allclose(windows["open"][1], (.75**2-.25**2)/2, atol=1e-16)
    x, w = np.polynomial.legendre.leggauss(5)
    x, w = .5+.25*x, .25*w
    smooth = 256*(x-.25)**2*(.75-x)**2
    np.testing.assert_allclose(windows["smooth_unit_peak"][1], np.dot(w, x*smooth), atol=2e-16)
    np.testing.assert_allclose(windows["smooth_unit_peak"][5], np.dot(w, x*x*smooth), atol=2e-16)
    np.testing.assert_allclose(np.sum([r["wrench"] for r in measures["fixed_distance_regions"]], axis=0),
                               measures["polynomial_x_moments"]["0"], atol=2e-16)


def test_existing_derivative_objectivity_controls_with_both_modes(fixture):
    refinement, p0, frozen, service, reference, model, pairing = fixture
    controls = affine.preparation_controls(model, pairing, refinement, p0, frozen, service, reference)
    assert max(controls["six_common_rigid_field_average_gap_scaled"]) < affine.GAP_LIMIT
    assert max(controls["objective_average_gap_scaled"].values()) < affine.GAP_LIMIT
    assert max(controls["actual_left_exp_derivative_relative"]) < affine.DERIVATIVE_LIMIT
    assert controls["row_transform_max_abs"] < affine.BALANCE_LIMIT
    assert controls["normal_spin_columns_zero"]


def test_helper_identity_failure_is_retained_without_loaded_services(tmp_path, monkeypatch):
    def fail():
        raise RuntimeError("helper identity sentinel")
    monkeypatch.setattr(affine, "services", fail)
    output = tmp_path/"failed-source"
    with pytest.raises(RuntimeError, match="helper identity sentinel"):
        affine.main(tmp_path/"unused-site", output, "mz")
    summary = json.loads((output/"summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["error"]["message"] == "helper identity sentinel"
    assert not (output/"raw-inventory.json").exists()


@pytest.mark.parametrize("earlier_error", (False, True))
def test_cleanup_failure_preserves_raw_marks_failed_and_respects_original_error(tmp_path, earlier_error):
    def wipe():
        raise RuntimeError("wipe sentinel")
    def atomic(path, value):
        path.write_text(json.dumps(value))
    recorder = SimpleNamespace(raw={"poses": {1: [0.]*6}}, ops=SimpleNamespace(wipe=wipe))
    service = SimpleNamespace(_atomic=atomic)
    summary = {"status": "completed"}
    if earlier_error:
        summary["error"] = {"message": "primary sentinel"}
        affine.finalize(recorder, service, tmp_path, summary, earlier_error=True)
    else:
        with pytest.raises(RuntimeError, match="wipe sentinel"):
            affine.finalize(recorder, service, tmp_path, summary, earlier_error=False)
    saved = json.loads((tmp_path/"summary.json").read_text())
    assert saved["status"] == "failed"
    assert "wipe sentinel" in saved["cleanup_error"]
    assert (tmp_path/"raw-inventory.json").exists()
    if earlier_error:
        assert saved["error"]["message"] == "primary sentinel"


def test_failed_raw_retention_still_closes_and_reports(tmp_path):
    closed = []
    def fail(*args):
        raise OSError("retention sentinel")
    recorder = SimpleNamespace(raw={}, ops=SimpleNamespace(wipe=lambda: closed.append(True)))
    with pytest.raises(OSError, match="retention sentinel"):
        affine.finalize(recorder, SimpleNamespace(_atomic=fail), tmp_path, {"status": "completed"}, earlier_error=False)
    assert closed == [True]
    summary = json.loads((tmp_path/"summary.json").read_text())
    assert summary["status"] == "failed" and "retention sentinel" in summary["raw_retention_error"]
