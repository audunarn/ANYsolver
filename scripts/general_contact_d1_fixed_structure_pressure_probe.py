"""One independent fixed-structure pressure-space D1 discriminator.

The structural grid is 32x8. Compare its matching Q1 pressure with a 16x8
pressure grid on the same support. This does not change the production solver.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import psutil
from scipy.optimize import minimize
import scipy.sparse as sparse
import scipy.sparse.linalg as sparse_linalg

from docs.d1_review_support import d1_rim_oracle as oracle
from scripts.general_contact_d1_near_rim_axis_refinement import _physical_gap


def cross_mass(pressure_nodes, structure_nodes, clip):
    """Exact hat-function cross mass using two-point Gaussian subintervals."""
    pressure_nodes = np.asarray(pressure_nodes)
    structure_nodes = np.asarray(structure_nodes)
    boundaries = np.unique(np.r_[pressure_nodes, structure_nodes, clip])
    boundaries = boundaries[(boundaries >= 0.0) & (boundaries <= clip)]
    result = np.zeros((len(pressure_nodes), len(structure_nodes)))
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        if right <= left:
            continue
        midpoint = 0.5*(left+right)
        half = 0.5*(right-left)
        for root in (-1/np.sqrt(3), 1/np.sqrt(3)):
            point = midpoint+half*root
            p = min(np.searchsorted(pressure_nodes, point, side="right")-1,
                    len(pressure_nodes)-2)
            s = min(np.searchsorted(structure_nodes, point, side="right")-1,
                    len(structure_nodes)-2)
            pt = (point-pressure_nodes[p])/(pressure_nodes[p+1]-pressure_nodes[p])
            st = (point-structure_nodes[s])/(structure_nodes[s+1]-structure_nodes[s])
            result[p:p+2, s:s+2] += half*np.outer((1-pt, pt), (1-st, st))
    return result


def scaled_qp_approximation(compliance, rhs):
    """Return the bounded dual QP iterate before active-set certification."""
    diagonal = np.sqrt(np.diag(compliance))
    if np.any(diagonal <= 0):
        raise RuntimeError("dual QP has nonpositive diagonal")
    hessian = compliance/np.outer(diagonal, diagonal)
    linear = rhs/diagonal
    scale = max(float(np.max(-linear)), 1.0e-12)

    def objective_and_gradient(scaled_pressure):
        response = hessian @ scaled_pressure
        return (float(0.5*scaled_pressure @ response
                      + (linear/scale) @ scaled_pressure),
                response+linear/scale)

    result = minimize(
        objective_and_gradient, np.zeros(len(rhs)), jac=True,
        method="L-BFGS-B", bounds=[(0.0, None)]*len(rhs),
        options={"maxiter": 20000, "gtol": 1.0e-11,
                 "ftol": 1.0e-15, "maxls": 50},
    )
    return result.x*scale/diagonal, result


def scaled_qp_lcp(compliance, rhs, support):
    """Independent bound-constrained dual QP, certified in original units."""
    pressure, result = scaled_qp_approximation(compliance, rhs)
    active = result.x > 1.0e-10
    switching_scale = 1.0/np.max(np.diag(compliance))
    for _ in range(100):
        pressure = np.zeros(len(rhs))
        if np.any(active):
            try:
                pressure[active] = np.linalg.solve(
                    compliance[np.ix_(active, active)], -rhs[active])
            except np.linalg.LinAlgError as exc:
                raise RuntimeError("scaled dual QP active block is singular") from exc
        gap = compliance @ pressure+rhs
        next_active = (pressure-switching_scale*gap) > 0
        if np.array_equal(next_active, active):
            break
        active = next_active
    else:
        raise RuntimeError("scaled dual QP active-set polish did not settle")
    gap = compliance @ pressure+rhs
    normalized_gap = gap/support
    certificate = max(
        float(max(0.0, -np.min(normalized_gap))),
        float(np.max(np.abs(pressure*normalized_gap))),
    )
    if (not result.success or np.min(pressure) < -1.0e-10
            or certificate > 1.0e-12):
        raise RuntimeError(
            f"scaled dual QP unresolved: success={result.success}, "
            f"iterations={result.nit}, certificate={certificate:.6g}"
        )
    return pressure


def active_work_rank_record(pressure_x, pressure_y, structure_x, structure_y,
                            saved_bins, saved_active_modes):
    """Algebraic rank of the replayed QP active cross-mass work map."""
    nx, ny = len(structure_x)-1, len(structure_y)-1
    stiffness = oracle.D*(
        sparse.kron(sparse.csr_matrix(oracle.mass1d(ny, nodes=structure_y)),
                    sparse.csr_matrix(oracle.stiff1d(nx, structure_x)))
        +sparse.kron(sparse.csr_matrix(oracle.stiff1d(ny, structure_y)),
                     sparse.csr_matrix(oracle.mass1d(nx, nodes=structure_x))))
    force = -oracle.Q*np.kron(
        oracle.mass1d(ny, nodes=structure_y).sum(axis=1),
        oracle.mass1d(nx, nodes=structure_x).sum(axis=1))
    work_all = sparse.kron(
        sparse.csr_matrix(cross_mass(pressure_y, structure_y, oracle.YR)),
        sparse.csr_matrix(cross_mass(pressure_x, structure_x, 1.0)),
    ).tocsr()
    all_support = np.asarray(work_all.sum(axis=1)).ravel()
    supported = all_support > 0
    work = work_all[supported]
    support = all_support[supported]
    free = np.ones(len(force), dtype=bool)
    free[::nx+1] = False
    factor = sparse_linalg.splu(stiffness.tocsr()[free][:, free].tocsc())
    work_free = work[:, free]
    compliance = np.asarray(work_free @ factor.solve(work_free.T.toarray()))
    compliance = 0.5*(compliance+compliance.T)
    rhs = work_free @ factor.solve(force[free])+oracle.G0*support
    pressure, result = scaled_qp_approximation(compliance, rhs)
    active = pressure > 1.0e-9
    full_pressure = np.zeros(len(all_support))
    full_pressure[supported] = pressure
    solution = {"nx": len(pressure_x)-1, "ny": len(pressure_y)-1,
                "xn": pressure_x, "yn": pressure_y,
                "p": full_pressure.reshape(len(pressure_y), len(pressure_x))}
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, oracle.YR, 10), 1.0]
    bins = oracle.q1_bins(solution, edges_x, edges_y)
    replay_bin_relative = float(
        np.linalg.norm(bins-np.asarray(saved_bins))
        /np.linalg.norm(saved_bins))
    if (int(active.sum()) != saved_active_modes
            or replay_bin_relative > 1.0e-10):
        raise AssertionError("QP active-set replay differs from saved field")
    active_work = work_free[active].T.toarray()
    column_scale = np.linalg.norm(active_work, axis=0)
    if np.any(column_scale <= 0):
        raise AssertionError("active work has a zero column")
    unit_work = active_work/column_scale
    _, singular, right = np.linalg.svd(unit_work, full_matrices=False)
    ratios = singular/singular[0]
    result_record = {
        "qp_optimizer_success": bool(result.success),
        "qp_optimizer_iterations": int(result.nit),
        "replay_bin_l2_relative": replay_bin_relative,
        "supported_modes": int(supported.sum()),
        "active_modes": int(active.sum()),
        "free_structural_coordinates": int(free.sum()),
        "active_supported_indices": np.flatnonzero(active).tolist(),
        "active_unit_column_singular_min_relative": float(ratios[-1]),
        "active_rank_relative_1e_10": int(np.count_nonzero(ratios > 1.0e-10)),
        "active_rank_relative_1e_12": int(np.count_nonzero(ratios > 1.0e-12)),
    }
    if ratios[-1] <= 1.0e-10:
        delta = right[-1]/column_scale
        full_delta = np.zeros(len(all_support))
        full_delta[np.flatnonzero(supported)[active]] = delta
        solution["p"] = full_delta.reshape(len(pressure_y), len(pressure_x))
        null_bins = oracle.q1_bins(solution, edges_x, edges_y)
        feasible_plus = min(
            (pressure[active][delta < 0]/-delta[delta < 0]).tolist()
            or [float("inf")])
        feasible_minus = min(
            (pressure[active][delta > 0]/delta[delta > 0]).tolist()
            or [float("inf")])
        feasible_step = 0.5*min(feasible_plus, feasible_minus)
        result_record.update({
            "null_work_relative": float(
                np.linalg.norm(active_work @ delta)
                /max(np.linalg.norm(active_work, 2)*np.linalg.norm(delta),
                     1.0e-30)),
            "null_bin_l2_per_pressure_l2_relative": float(
                np.linalg.norm(null_bins[:9])/np.linalg.norm(bins[:9])
                *np.linalg.norm(pressure[active])/np.linalg.norm(delta)),
            "half_feasible_null_bin_l2_relative": float(
                feasible_step*np.linalg.norm(null_bins[:9])
                /np.linalg.norm(bins[:9])),
        })
    return result_record


def solved_active_work_rank(solution, structure_x, structure_y):
    """Check the active work columns of the already certified PDAS solution."""
    pressure_x, pressure_y = solution["xn"], solution["yn"]
    work_all = sparse.kron(
        sparse.csr_matrix(cross_mass(pressure_y, structure_y, oracle.YR)),
        sparse.csr_matrix(cross_mass(pressure_x, structure_x, 1.0)),
    ).tocsr()
    support = np.asarray(work_all.sum(axis=1)).ravel()
    if np.any(support < 0):
        raise AssertionError("negative pressure support")
    active = np.flatnonzero(solution["p"].ravel() > 1.0e-9)
    if not len(active) or np.any(support[active] <= 0):
        raise AssertionError("active pressure has no physical support")
    free = np.ones((len(structure_x)*len(structure_y)), dtype=bool)
    free[::len(structure_x)] = False
    active_work = work_all[active][:, free].T.toarray()
    column_scale = np.linalg.norm(active_work, axis=0)
    if np.any(column_scale <= 0):
        raise AssertionError("active work has a zero column")
    singular = np.linalg.svd(active_work/column_scale,
                             compute_uv=False)
    ratios = singular/singular[0]
    return {
        "active_modes": int(len(active)),
        "supported_modes": int(np.count_nonzero(support > 0)),
        "active_unit_column_singular_min_relative": float(ratios[-1]),
        "active_rank_relative_1e_10": int(np.count_nonzero(ratios > 1e-10)),
        "active_rank_relative_1e_12": int(np.count_nonzero(ratios > 1e-12)),
    }


def solve_fixed_structure(pressure_x, structure_x, y, pressure_y=None,
                          lcp_method="pdas"):
    if pressure_y is None:
        pressure_y = y
    nx, ny = len(structure_x)-1, len(y)-1
    kx = oracle.stiff1d(nx, structure_x)
    mx = oracle.mass1d(nx, nodes=structure_x)
    ky = oracle.stiff1d(ny, y)
    my = oracle.mass1d(ny, nodes=y)
    stiffness = oracle.D*(
        sparse.kron(sparse.csr_matrix(my), sparse.csr_matrix(kx))
        +sparse.kron(sparse.csr_matrix(ky), sparse.csr_matrix(mx)))
    force = -oracle.Q*np.kron(my.sum(axis=1), mx.sum(axis=1))
    bx = cross_mass(pressure_x, structure_x, 1.0)
    by = cross_mass(pressure_y, y, oracle.YR)
    work_all = sparse.kron(sparse.csr_matrix(by), sparse.csr_matrix(bx)).tocsr()
    all_support = np.asarray(work_all.sum(axis=1)).ravel()
    if np.any(all_support < 0):
        raise AssertionError("negative pressure support")
    supported = all_support > 0
    work = work_all[supported]
    support = all_support[supported]
    free = np.ones(len(force), dtype=bool)
    free[np.arange(0, len(force), nx+1)] = False
    reduced = stiffness.tocsr()[free][:, free].tocsc()
    factor = sparse_linalg.splu(reduced)
    work_free = work[:, free]
    open_displacement = factor.solve(force[free])
    response = factor.solve(work_free.T.toarray())
    compliance = np.asarray(work_free @ response)
    compliance = 0.5*(compliance+compliance.T)
    rhs = work_free @ open_displacement+oracle.G0*support
    if lcp_method == "pdas":
        pressure = oracle.pdas_lcp(compliance, rhs, support)
    elif lcp_method == "scaled_qp":
        pressure = scaled_qp_lcp(compliance, rhs, support)
    else:
        raise ValueError("unsupported scalar pressure solver")
    displacement = np.zeros(len(force))
    displacement[free] = open_displacement+response @ pressure
    weighted_gap = work @ displacement+oracle.G0*support
    residual = reduced @ displacement[free]-force[free]-work_free.T @ pressure
    active = np.flatnonzero(pressure > 1e-9)
    if len(active) == 0:
        raise AssertionError("fixed-structure case has no active pressure")
    active_response = compliance[np.ix_(active, active)]
    diagonal = np.diag(active_response)
    scaled = active_response/np.sqrt(np.outer(diagonal, diagonal))
    eigenvalues = np.linalg.eigvalsh(scaled)
    full_pressure = np.zeros(len(all_support))
    full_pressure[supported] = pressure
    solution = {
        "nx": len(pressure_x)-1,
        "ny": len(pressure_y)-1,
        "xn": pressure_x,
        "yn": pressure_y,
        "p": full_pressure.reshape(len(pressure_y), len(pressure_x)),
        "w": displacement.reshape(ny+1, nx+1),
    }
    if (np.min(pressure) < -1e-10
            or np.min(weighted_gap/support) < -1e-9
            or np.linalg.norm(residual) > 1e-7):
        raise AssertionError("fixed-structure Q1 KKT check failed")
    return solution, {
        "reaction_n": float(support @ pressure),
        "equilibrium_n": float(np.linalg.norm(residual)),
        "complementarity_pa_m": float(np.max(abs(pressure*weighted_gap/support))),
        "minimum_weighted_gap_m": float(np.min(weighted_gap/support)),
        "minimum_physical_q1_gap_m": _physical_gap({
            "yn": y, "w": solution["w"]}),
        "active_pressure_modes": len(active),
        "supported_pressure_modes": int(supported.sum()),
        "exactly_unsupported_pressure_modes": int((~supported).sum()),
        "minimum_active_support_m2": float(np.min(support[active])),
        "maximum_active_support_m2": float(np.max(support[active])),
        "active_unit_diagonal_eigenvalue_ratio": float(
            eigenvalues[0]/eigenvalues[-1]),
        "active_unit_diagonal_minimum_eigenvalue": float(eigenvalues[0]),
    }


def enrichment_y_grid(y):
    """Double y pressure resolution, placing one knot at the real support rim."""
    midpoints = 0.5*(y[:-1]+y[1:])
    midpoints[-1] = oracle.YR
    result = np.sort(np.r_[y, midpoints])
    if len(result) != 2*len(y)-1 or np.any(np.diff(result) <= 0):
        raise AssertionError("invalid pressure y enrichment")
    return result


def relative_q1_pressure_l2(first, second, *, support_y_max,
                            support_y_min=0.0):
    """Exact squared Q1 comparison on a physical-support y band."""
    x_knots = np.unique(np.r_[first["xn"], second["xn"]])
    y_knots = np.unique(np.r_[first["yn"], second["yn"],
                               support_y_min, support_y_max])
    y_knots = y_knots[(y_knots >= support_y_min)
                      & (y_knots <= support_y_max)]
    roots = (-1/np.sqrt(3.0), 1/np.sqrt(3.0))

    def value(solution, x, y):
        xs, ys, p = solution["xn"], solution["yn"], solution["p"]
        i = min(int(np.searchsorted(xs, x, side="right")-1), len(xs)-2)
        j = min(int(np.searchsorted(ys, y, side="right")-1), len(ys)-2)
        a = (x-xs[i])/(xs[i+1]-xs[i])
        b = (y-ys[j])/(ys[j+1]-ys[j])
        return ((1-a)*(1-b)*p[j, i] + a*(1-b)*p[j, i+1]
                + a*b*p[j+1, i+1] + (1-a)*b*p[j+1, i])

    error = reference = 0.0
    for x0, x1 in zip(x_knots[:-1], x_knots[1:]):
        for y0, y1 in zip(y_knots[:-1], y_knots[1:]):
            weight = (x1-x0)*(y1-y0)/4.0
            for gx in roots:
                x = (x0+x1)/2.0 + (x1-x0)*gx/2.0
                for gy in roots:
                    y = (y0+y1)/2.0 + (y1-y0)*gy/2.0
                    p = value(first, x, y)
                    q = value(second, x, y)
                    error += weight*(p-q)**2
                    reference += weight*q**2
    if reference <= 0:
        raise AssertionError("zero reference pressure norm")
    return float(np.sqrt(error/reference))


def run_coarse_y(output):
    """Bounded y-pressure discriminator on the unchanged 32x8 structure."""
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    saved_path = Path("reports/general_contact_d1_16x8_near_rim_"
                      "guarded_no_checkpoint_comparison_identity_dev_20260928.json")
    saved_bytes = saved_path.read_bytes()
    saved = json.loads(saved_bytes)
    oracle_sha = hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()
    if (saved["status"] != "development_comparison_only"
            or saved["mesh"] != [16, 8]
            or saved["oracle_sha256"] != oracle_sha):
        raise ValueError("near-rim reference identity differs")
    x = np.linspace(0.0, 1.0, 33)
    y = np.asarray(saved["source_y_knots_m"])
    coarse_y = y[[0, 2, 4, 6, 8]]
    if not np.all(np.diff(coarse_y) > 0):
        raise AssertionError("invalid nested coarse y pressure knots")
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, oracle.YR, 10), 1.0]
    solutions = {}
    cases = {}
    for name, pressure_y in (("matching_32x8", y),
                             ("coarse_y_32x4", coarse_y)):
        solution, diagnostics = solve_fixed_structure(x, x, y, pressure_y)
        bins = oracle.q1_bins(solution, edges_x, edges_y)
        if abs(bins.sum()-diagnostics["reaction_n"]) > 1.0e-10:
            raise AssertionError("physical bins lose reaction")
        if name == "matching_32x8":
            independent = oracle.solve_q1(32, 8, ynodes=y)
            np.testing.assert_allclose(solution["p"], independent["p"],
                                       rtol=1.0e-9, atol=1.0e-10)
            np.testing.assert_allclose(bins, oracle.q1_bins(
                independent, edges_x, edges_y), rtol=1.0e-9, atol=1.0e-12)
        solutions[name] = solution
        cases[name] = {**diagnostics, "pressure_y_knots_m": pressure_y.tolist(),
                       "pressure_pa": solution["p"].tolist(),
                       "bins_n": bins.tolist()}
    coarse = cases["coarse_y_32x4"]
    matching = cases["matching_32x8"]
    coarse_bins = np.asarray(coarse["bins_n"])[:9]
    matching_bins = np.asarray(matching["bins_n"])[:9]
    record = {
        "status": "development_fixed_structure_coarse_y_pressure",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_sha256": oracle_sha,
        "saved_comparison_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "structural_mesh": [32, 8],
        "structural_y_knots_m": y.tolist(),
        "physical_support_y_max_m": oracle.YR,
        "common_bins": [8, 9],
        "cases": cases,
        "coarse_vs_matching_bin_l2_relative": float(
            np.linalg.norm(coarse_bins-matching_bins)
            /np.linalg.norm(matching_bins)),
        "coarse_vs_matching_rim_force_relative": float(
            abs(coarse_bins[8].sum()-matching_bins[8].sum())
            /abs(matching_bins[8].sum())),
        "coarse_vs_matching_reaction_relative": float(
            abs(coarse["reaction_n"]-matching["reaction_n"])
            /abs(matching["reaction_n"])),
        "coarse_vs_matching_physical_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["coarse_y_32x4"], solutions["matching_32x8"],
                support_y_max=oracle.YR)),
        "elapsed_seconds": time.perf_counter()-started,
        "peak_process_working_set_mb": (
            psutil.Process().memory_info().peak_wset / 1.0e6),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in record
                      if key.startswith("coarse_vs_matching_")}, indent=2))


def run_rim_knot(output):
    """Move only the near-rim Q1 pressure knot to the physical support edge."""
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    saved_path = Path("reports/general_contact_d1_16x8_near_rim_"
                      "guarded_no_checkpoint_comparison_identity_dev_20260928.json")
    saved_bytes = saved_path.read_bytes()
    saved = json.loads(saved_bytes)
    oracle_sha = hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()
    if (saved["status"] != "development_comparison_only"
            or saved["mesh"] != [16, 8]
            or saved["oracle_sha256"] != oracle_sha):
        raise ValueError("near-rim reference identity differs")
    x = np.linspace(0.0, 1.0, 33)
    y = np.asarray(saved["source_y_knots_m"])
    rim_y = y.copy()
    if not np.isclose(rim_y[-2], 0.895, rtol=0, atol=1e-12):
        raise AssertionError("unexpected near-rim knot")
    rim_y[-2] = oracle.YR
    if not np.all(np.diff(rim_y) > 0):
        raise AssertionError("rim-aligned knots are invalid")
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, oracle.YR, 10), 1.0]
    solutions = {}
    cases = {}
    for name, pressure_y in (("matching_32x8", y),
                             ("rim_aligned_32x8", rim_y)):
        solution, diagnostics = solve_fixed_structure(x, x, y, pressure_y)
        bins = oracle.q1_bins(solution, edges_x, edges_y)
        if abs(bins.sum()-diagnostics["reaction_n"]) > 1.0e-10:
            raise AssertionError("physical bins lose reaction")
        solutions[name] = solution
        cases[name] = {**diagnostics,
                       "pressure_y_knots_m": pressure_y.tolist(),
                       "pressure_pa": solution["p"].tolist(),
                       "bins_n": bins.tolist(),
                       "active_work_rank": solved_active_work_rank(
                           solution, x, y)}
    baseline = cases["matching_32x8"]
    moved = cases["rim_aligned_32x8"]
    base_bins = np.asarray(baseline["bins_n"])[:9]
    moved_bins = np.asarray(moved["bins_n"])[:9]
    record = {
        "status": "development_fixed_structure_rim_knot_discriminator",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_sha256": oracle_sha,
        "saved_comparison_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "structural_mesh": [32, 8],
        "structural_y_knots_m": y.tolist(),
        "physical_support_y_max_m": oracle.YR,
        "common_bins": [8, 9],
        "cases": cases,
        "moved_vs_matching_bin_l1_relative": float(
            np.abs(moved_bins-base_bins).sum()/np.abs(base_bins).sum()),
        "moved_vs_matching_bin_l2_relative": float(
            np.linalg.norm(moved_bins-base_bins)/np.linalg.norm(base_bins)),
        "moved_vs_matching_rim_force_relative": float(
            abs(moved_bins[8].sum()-base_bins[8].sum())
            /abs(base_bins[8].sum())),
        "moved_vs_matching_reaction_relative": float(
            abs(moved["reaction_n"]-baseline["reaction_n"])
            /abs(baseline["reaction_n"])),
        "moved_vs_matching_physical_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["rim_aligned_32x8"], solutions["matching_32x8"],
                support_y_max=oracle.YR)),
        "moved_vs_matching_regular_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["rim_aligned_32x8"], solutions["matching_32x8"],
                support_y_min=0.0, support_y_max=0.8)),
        "moved_vs_matching_rim_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["rim_aligned_32x8"], solutions["matching_32x8"],
                support_y_min=0.8, support_y_max=oracle.YR)),
        "elapsed_seconds": time.perf_counter()-started,
        "peak_process_working_set_mb": (
            psutil.Process().memory_info().peak_wset / 1.0e6),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key.startswith("moved_vs_matching_")}, indent=2))


def run_aligned_rim_x(output):
    """Preflight whether physical rim alignment changes scalar x convergence."""
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    saved_path = Path("reports/general_contact_d1_16x8_near_rim_"
                      "guarded_no_checkpoint_comparison_identity_dev_20260928.json")
    saved_bytes = saved_path.read_bytes()
    saved = json.loads(saved_bytes)
    oracle_sha = hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()
    if (saved["status"] != "development_comparison_only"
            or saved["mesh"] != [16, 8]
            or saved["oracle_sha256"] != oracle_sha):
        raise ValueError("near-rim reference identity differs")
    original_y = np.asarray(saved["source_y_knots_m"])
    aligned_y = original_y.copy()
    if not np.isclose(aligned_y[-2], 0.895, rtol=0, atol=1e-12):
        raise AssertionError("unexpected near-rim knot")
    aligned_y[-2] = oracle.YR
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, oracle.YR, 10), 1.0]
    reference_bins = np.asarray(saved["fv_bins_n"])[:9]
    solutions = {}
    cases = {}
    for profile, y in (("original", original_y),
                       ("aligned", aligned_y)):
        for nx in (16, 32):
            name = f"{profile}_{nx}x8"
            x = np.linspace(0.0, 1.0, nx+1)
            solution, diagnostics = solve_fixed_structure(x, x, y)
            independent = oracle.solve_q1(nx, 8, ynodes=y)
            np.testing.assert_allclose(solution["p"], independent["p"],
                                       rtol=1e-9, atol=1e-10)
            bins = oracle.q1_bins(solution, edges_x, edges_y)
            np.testing.assert_allclose(
                bins, oracle.q1_bins(independent, edges_x, edges_y),
                rtol=1e-9, atol=1e-12)
            if abs(bins.sum()-diagnostics["reaction_n"]) > 1e-10:
                raise AssertionError("physical bins lose reaction")
            solutions[name] = solution
            cases[name] = {**diagnostics,
                           "structural_y_knots_m": y.tolist(),
                           "pressure_pa": solution["p"].tolist(),
                           "bins_n": bins.tolist(),
                           "fv_bin_l2_relative": float(
                               np.linalg.norm(bins[:9]-reference_bins)
                               /np.linalg.norm(reference_bins)),
                           "active_work_rank": solved_active_work_rank(
                               solution, x, y)}
    comparisons = {}
    for profile in ("original", "aligned"):
        low = f"{profile}_16x8"
        high = f"{profile}_32x8"
        low_bins = np.asarray(cases[low]["bins_n"])[:9]
        high_bins = np.asarray(cases[high]["bins_n"])[:9]
        comparisons[profile] = {
            "x_refinement_bin_l2_relative": float(
                np.linalg.norm(high_bins-low_bins)/np.linalg.norm(low_bins)),
            "x_refinement_rim_force_relative": float(
                abs(high_bins[8].sum()-low_bins[8].sum())
                /abs(low_bins[8].sum())),
            "x_refinement_physical_pressure_l2_relative": (
                relative_q1_pressure_l2(
                    solutions[high], solutions[low],
                    support_y_max=oracle.YR)),
            "x_refinement_regular_pressure_l2_relative": (
                relative_q1_pressure_l2(
                    solutions[high], solutions[low],
                    support_y_min=0.0, support_y_max=0.8)),
            "x_refinement_rim_pressure_l2_relative": (
                relative_q1_pressure_l2(
                    solutions[high], solutions[low],
                    support_y_min=0.8, support_y_max=oracle.YR)),
        }
    record = {
        "status": "development_aligned_rim_x_preflight",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_sha256": oracle_sha,
        "saved_comparison_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "physical_support_y_max_m": oracle.YR,
        "common_bins": [8, 9],
        "cases": cases,
        "x_refinement_comparisons": comparisons,
        "elapsed_seconds": time.perf_counter()-started,
        "peak_process_working_set_mb": (
            psutil.Process().memory_info().peak_wset / 1.0e6),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(comparisons, indent=2))


def run_enrichment(output, *, lcp_method="pdas"):
    """One fixed-structure, pressure-only refinement discriminator."""
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    saved_path = Path("reports/general_contact_d1_16x8_near_rim_"
                      "guarded_no_checkpoint_comparison_identity_dev_20260928.json")
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    oracle_sha = hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()
    if (saved["status"] != "development_comparison_only"
            or saved["mesh"] != [16, 8]
            or saved["oracle_sha256"] != oracle_sha):
        raise ValueError("near-rim reference identity differs")
    structure_x = np.linspace(0.0, 1.0, 33)
    structure_y = np.asarray(saved["source_y_knots_m"])
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, oracle.YR, 10), 1.0]
    reference = np.asarray(saved["fv_bins_n"])
    cases = {}
    fields = {}
    grids = (
        ("matching_32x8", structure_x, structure_y),
        ("enriched_y_32x16", structure_x, enrichment_y_grid(structure_y)),
        ("enriched_x_64x8", np.linspace(0.0, 1.0, 65), structure_y),
    )
    for name, pressure_x, pressure_y in grids:
        print(f"pressure case: {name}", flush=True)
        try:
            solution, diagnostics = solve_fixed_structure(
                pressure_x, structure_x, structure_y, pressure_y,
                lcp_method="pdas" if name == "matching_32x8" else lcp_method)
        except RuntimeError as exc:
            if name == "matching_32x8":
                raise
            cases[name] = {"status": "pressure_lcp_unresolved",
                           "pressure_mesh": [len(pressure_x)-1, len(pressure_y)-1],
                           "reason": str(exc)}
            continue
        field = oracle.q1_bins(solution, edges_x, edges_y)
        if abs(field.sum()-diagnostics["reaction_n"]) > 1e-10:
            raise AssertionError("physical bins lose reaction")
        if name == "matching_32x8":
            matching = oracle.solve_q1(32, 8, ynodes=structure_y)
            np.testing.assert_allclose(solution["p"], matching["p"],
                                       rtol=1e-9, atol=1e-10)
        fields[name] = field
        diagnostics["pressure_mesh"] = [len(pressure_x)-1, len(pressure_y)-1]
        diagnostics["pressure_y_knots_m"] = pressure_y.tolist()
        diagnostics["fv_bin_l1_relative"] = float(
            np.abs(field[:9]-reference[:9]).sum()/np.abs(reference[:9]).sum())
        diagnostics["fv_bin_l2_relative"] = float(
            np.linalg.norm(field[:9]-reference[:9])/
            np.linalg.norm(reference[:9]))
        diagnostics["fv_rim_force_relative"] = float(
            abs(field[8].sum()-reference[8].sum())/abs(reference[8].sum()))
        diagnostics["bins_n"] = field.tolist()
        cases[name] = diagnostics
    base = fields["matching_32x8"][:9]
    sensitivity = {}
    for name in ("enriched_x_64x8", "enriched_y_32x16"):
        if name not in fields:
            continue
        delta = fields[name][:9]-base
        sensitivity[name] = {
            "bin_l1_relative": float(np.abs(delta).sum()/np.abs(base).sum()),
            "bin_l2_relative": float(np.linalg.norm(delta)/np.linalg.norm(base)),
            "reaction_relative": float(abs(fields[name].sum()-base.sum())/
                                       abs(base.sum())),
            "rim_force_relative": float(abs(delta[8].sum())/abs(base[8].sum())),
            "x_marginal_delta_n": delta.sum(axis=0).tolist(),
            "y_marginal_delta_n": delta.sum(axis=1).tolist(),
        }
    record = {
        "status": "development_pressure_only_enrichment_discriminator",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_sha256": oracle_sha,
        "saved_comparison_sha256": hashlib.sha256(saved_path.read_bytes()).hexdigest(),
        "structural_mesh": [32, 8],
        "structural_y_knots_m": structure_y.tolist(),
        "common_bins": [8, 9],
        "development_sensitivity_target_relative": 0.002,
        "independent_lcp_method": lcp_method,
        "retained_spatial_response_target_relative": 0.02,
        "cases": cases,
        "pressure_only_sensitivity": sensitivity,
        "all_enrichments_solved": len(sensitivity) == 2,
        "elapsed_seconds": time.perf_counter()-started,
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "pressure_only_sensitivity": sensitivity,
        "fv_bin_l2": {key: value["fv_bin_l2_relative"]
                      for key, value in cases.items()
                      if "fv_bin_l2_relative" in value},
        "elapsed_seconds": record["elapsed_seconds"],
    }, indent=2))


def run_active_rank(output):
    """Certify active work rank for the saved nonqualified QP field only."""
    if output.exists():
        raise FileExistsError(output)
    saved_path = Path(
        "docs/d1_review_support/d1_pressure_enrichment_qp_b_6c4d1887_20260928.json"
    )
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    if (saved["independent_lcp_method"] != "scaled_qp"
            or not saved["all_enrichments_solved"]):
        raise ValueError("saved approximate QP field identity differs")
    structure_x = np.linspace(0.0, 1.0, 33)
    structure_y = np.asarray(saved["structural_y_knots_m"])
    grids = {
        "enriched_x_64x8": (np.linspace(0.0, 1.0, 65), structure_y),
        "enriched_y_32x16": (structure_x, enrichment_y_grid(structure_y)),
    }
    cases = {}
    for name, (pressure_x, pressure_y) in grids.items():
        print(f"active rank case: {name}", flush=True)
        prior = saved["cases"][name]
        cases[name] = active_work_rank_record(
            pressure_x, pressure_y, structure_x, structure_y,
            prior["bins_n"], prior["active_pressure_modes"])
    record = {
        "status": "development_active_work_rank_discriminator",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_qp_field_sha256": hashlib.sha256(saved_path.read_bytes()).hexdigest(),
        "cases": cases,
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: {
        "active": value["active_modes"],
        "rank_1e_10": value["active_rank_relative_1e_10"],
        "smallest_relative_singular": value["active_unit_column_singular_min_relative"],
        "null_bin_response": value.get("half_feasible_null_bin_l2_relative"),
    } for key, value in cases.items()}, indent=2))


def main(output):
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    saved_path = Path("reports/general_contact_d1_16x8_near_rim_"
                      "guarded_no_checkpoint_comparison_identity_dev_20260928.json")
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    oracle_sha = hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()
    if (saved["status"] != "development_comparison_only"
            or saved["mesh"] != [16, 8]
            or saved["oracle_sha256"] != oracle_sha):
        raise ValueError("near-rim reference identity differs")
    structure_x = np.linspace(0.0, 1.0, 33)
    y = np.asarray(saved["source_y_knots_m"])
    pressure_grids = (("matching_32x8", structure_x),
                      ("coarse_x_16x8", np.linspace(0.0, 1.0, 17)))
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, 0.9, 10), 1.0]
    reference = np.asarray(saved["fv_bins_n"])
    matching_reference = oracle.solve_q1(32, 8, ynodes=y)
    cases = {}
    bins = {}
    solutions = {}
    for name, pressure_x in pressure_grids:
        solution, diagnostics = solve_fixed_structure(pressure_x, structure_x, y)
        field = oracle.q1_bins(solution, edges_x, edges_y)
        if abs(field.sum()-diagnostics["reaction_n"]) > 1e-10:
            raise AssertionError("fixed-structure physical bins lose reaction")
        if name == "matching_32x8":
            np.testing.assert_allclose(solution["p"], matching_reference["p"],
                                       rtol=1e-9, atol=1e-10)
            np.testing.assert_allclose(field, oracle.q1_bins(
                matching_reference, edges_x, edges_y), rtol=1e-9, atol=1e-12)
        bins[name] = field
        solutions[name] = solution
        difference = field[:9]-reference[:9]
        diagnostics["fv_bin_l2_relative"] = float(
            np.linalg.norm(difference)/np.linalg.norm(reference[:9]))
        diagnostics["fv_rim_force_relative"] = float(
            abs(field[8].sum()-reference[8].sum())/abs(reference[8].sum()))
        diagnostics["bins_n"] = field.tolist()
        diagnostics["active_work_rank"] = solved_active_work_rank(
            solution, structure_x, y)
        cases[name] = diagnostics
    record = {
        "status": "development_fixed_structure_pressure_space_probe",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_sha256": oracle_sha,
        "saved_comparison_sha256": hashlib.sha256(saved_path.read_bytes()).hexdigest(),
        "structural_mesh": [32, 8],
        "same_y_knots_m": y.tolist(),
        "common_bins": [8, 9],
        "cases": cases,
        "coarse_vs_matching_bin_l2_relative": float(np.linalg.norm(
            (bins["coarse_x_16x8"]-bins["matching_32x8"])[:9])
            /np.linalg.norm(bins["matching_32x8"][:9])),
        "coarse_vs_matching_reaction_relative": float(abs(
            cases["coarse_x_16x8"]["reaction_n"]
            -cases["matching_32x8"]["reaction_n"])
            /abs(cases["matching_32x8"]["reaction_n"])),
        "coarse_vs_matching_physical_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["coarse_x_16x8"], solutions["matching_32x8"],
                support_y_max=oracle.YR)),
        "coarse_vs_matching_regular_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["coarse_x_16x8"], solutions["matching_32x8"],
                support_y_min=0.0, support_y_max=0.8)),
        "coarse_vs_matching_rim_pressure_l2_relative": (
            relative_q1_pressure_l2(
                solutions["coarse_x_16x8"], solutions["matching_32x8"],
                support_y_min=0.8, support_y_max=oracle.YR)),
        "elapsed_seconds": time.perf_counter()-started,
        "peak_process_working_set_mb": (
            psutil.Process().memory_info().peak_wset / 1.0e6),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "bin_l2_difference": record["coarse_vs_matching_bin_l2_relative"],
        "reaction_difference": record["coarse_vs_matching_reaction_relative"],
        "case_errors": {key: value["fv_bin_l2_relative"]
                        for key, value in cases.items()},
        "elapsed_seconds": record["elapsed_seconds"],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(Path(sys.argv[1]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--enrichment":
        run_enrichment(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--enrichment-qp":
        run_enrichment(Path(sys.argv[2]), lcp_method="scaled_qp")
    elif len(sys.argv) == 3 and sys.argv[1] == "--active-rank":
        run_active_rank(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--coarse-y":
        run_coarse_y(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--rim-knot":
        run_rim_knot(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "--aligned-rim-x":
        run_aligned_rim_x(Path(sys.argv[2]))
    else:
        raise SystemExit("usage: python general_contact_d1_fixed_structure_pressure_probe.py [--enrichment|--coarse-y|--rim-knot|--aligned-rim-x] OUTPUT")
