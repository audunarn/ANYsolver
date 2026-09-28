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


def solve_fixed_structure(pressure_x, structure_x, y, pressure_y=None):
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
    pressure = oracle.pdas_lcp(compliance, rhs, support)
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


def run_enrichment(output):
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
                pressure_x, structure_x, structure_y, pressure_y)
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
        difference = field[:9]-reference[:9]
        diagnostics["fv_bin_l2_relative"] = float(
            np.linalg.norm(difference)/np.linalg.norm(reference[:9]))
        diagnostics["fv_rim_force_relative"] = float(
            abs(field[8].sum()-reference[8].sum())/abs(reference[8].sum()))
        diagnostics["bins_n"] = field.tolist()
        cases[name] = diagnostics
    record = {
        "status": "development_fixed_structure_pressure_space_probe",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
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
        "elapsed_seconds": time.perf_counter()-started,
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
    else:
        raise SystemExit("usage: python general_contact_d1_fixed_structure_pressure_probe.py [--enrichment] OUTPUT")
