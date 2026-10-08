"""One authorised independent analytical development discriminator.

Question: does the V4 full-reference-mass-normalised constructive source
pairing detect the retained positive-cut loss? Inputs are the corrected
touching two-hat v7 records at theta=.1/.05/.025 and their documented exact
four-by-two source / two-S3 target geometry. No mechanics kernel, coupled
solver, historical execution authority or structural-energy optimisation is
used. Cap: one process, 180 s / 1 GB. Decision: record same-measure loss,
with all 15 historical pressure hats retained and the actual source clamp
explicit; do not infer full-system instability from this source subspace.
"""

from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy import linalg
import psutil


HERE = Path(__file__).resolve().parent
STEM = "d1_cut_eta_discriminator_20260929"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mass_1d(knots):
    result = [[Q(0) for _ in knots] for _ in knots]
    for i, (a, b) in enumerate(zip(knots, knots[1:])):
        for j, k, factor in ((i, i, 2), (i, i+1, 1),
                             (i+1, i, 1), (i+1, i+1, 2)):
            result[j][k] += (b-a)*factor/6
    return result


def array(values):
    return np.asarray(values, dtype=float)


def cut_y(theta):
    b = theta**2/2-theta**3/3
    return [[Q(1, 3), Q(1, 6), Q(0)],
            [Q(1, 6), Q(1, 3)+theta-theta**2+theta**3/3, b],
            [Q(0), b, theta**3/3]]


def main():
    started = time.perf_counter()
    paths = {suffix: HERE/f"{STEM}.{suffix}"
             for suffix in ("json", "log", "resources.json")}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError("Retain the existing discriminator evidence")
    x = [Q(0), Q(1, 2), Q(1), Q(3, 2), Q(2)]
    y = [Q(0), Q(1), Q(2)]
    mx, my = mass_1d(x), mass_1d(y)
    mass = np.kron(array(my), array(mx))
    free = np.asarray([i for i in range(15) if i % 5 != 0])
    clamped = np.asarray([0, 5, 10])
    free_mass = mass[np.ix_(free, free)]
    input_paths = [HERE/f"d1_cut_front_two_hat_touch_{name}_v7_20260929.json"
                   for name in ("010", "005", "0025")]
    rows = []
    for path in input_paths:
        saved = json.loads(path.read_text())
        assert (saved["status"] == "development_fixed_pose_work_map"
                and saved["pressure_modes"] == 15
                and saved["source_faces"] == 8 and saved["target_faces"] == 2
                and saved["two_hat_mode"] and saved["touching"]
                and set(saved["pressure_node_ids"]) == {3, 4, 8, 9, 13, 14})
        declared_theta = Q(saved["theta"])
        # Enclose the actual declared builder's binary64 upper edge identity:
        # target y_max is the stored float 1.0+theta, not an ideal decimal.
        theta = Q(float(1.0+saved["theta"]))-1
        b = theta**2/2-theta**3/3
        d = Q(1, 4)+theta-theta**2+theta**3/3
        beta = -b/d
        py = [-beta/2, beta, Q(1)]
        c = [Q(value) for value in saved["x_hat_coefficients"]]
        px = [Q(0), Q(0), c[0], c[1], Q(0)]
        coefficients_exact = [ay*ax for ay in py for ax in px]
        coefficients = array(coefficients_exact)
        overlap_y = cut_y(theta)
        overlap = np.kron(array(overlap_y), array(mx))
        weighted_work = overlap @ coefficients
        # Exact arithmetic independently confirms zero work on all clamp
        # nodes; this is not a tolerance-based deletion of pressure modes.
        exact_work = [sum(overlap_y[i//5][j//5]*mx[i % 5][j % 5]
                          *coefficients_exact[j] for j in range(15))
                      for i in range(15)]
        assert all(exact_work[i] == 0 for i in clamped)
        pressure_mass_squared = sum(
            coefficients_exact[i]*my[i//5][j//5]*mx[i % 5][j % 5]
            *coefficients_exact[j] for i in range(15) for j in range(15))
        x_mass_squared = sum(px[i]*mx[i][j]*px[j]
                             for i in range(5) for j in range(5))
        y_mass_squared = sum(py[i]*my[i][j]*py[j]
                             for i in range(3) for j in range(3))
        assert pressure_mass_squared == x_mass_squared*y_mass_squared
        actual_source_work = array([exact_work[i] for i in free])
        actual_dual_squared = float(actual_source_work @ linalg.solve(
            free_mass, actual_source_work, assume_a="pos"))
        witness_ratio = np.sqrt(actual_dual_squared/float(pressure_mass_squared))
        full_values = linalg.eigvalsh(overlap, mass)
        free_values = linalg.eigvalsh(overlap[np.ix_(free, free)], free_mass)
        r2 = theta**3/3-b*b/d
        rayleigh = r2/y_mass_squared
        assert full_values[0] > 0.0
        assert full_values[0] <= float(rayleigh)*(1+1e-9)
        assert np.isclose(full_values[0], free_values[0], rtol=1e-8, atol=1e-14)
        # All supported pressure hats remain in the historical law. The
        # compatible principal-space spectrum below is a diagnostic, not a
        # modified contact problem or a full two-body inf-sup result.
        full_cover_work = (mass @ coefficients)[free]
        full_cover_ratio = np.sqrt(float(full_cover_work @ linalg.solve(
            free_mass, full_cover_work, assume_a="pos"))/float(pressure_mass_squared))
        assert abs(full_cover_ratio-1) < 1e-12
        rows.append({
            "input": path.name, "input_sha256": sha(path),
            "theta_declared": float(declared_theta),
            "theta_binary64_target_edge": float(theta),
            "target_y_upper_m": float(1+theta),
            "all_supported_historical_pressure_modes": 15,
            "witness_nonzero_nodes_row_major": [i+1 for i, p in
                                                enumerate(coefficients_exact) if p],
            "witness_coefficients_all_15_row_major": coefficients.tolist(),
            "actual_source_free_normal_nodes": (free+1).tolist(),
            "source_clamped_normal_nodes": (clamped+1).tolist(),
            "exact_clamped_work_is_zero": True,
            "exact_matching_witness_motion_satisfies_source_clamp": True,
            "all_overlap_supports_positive": bool(np.all(overlap @ np.ones(15) > 0)),
            "reference_x_mass_norm_squared": float(x_mass_squared),
            "reference_y_mass_norm_squared": float(y_mass_squared),
            "full_reference_pressure_mass_norm_squared": float(pressure_mass_squared),
            "exact_residual_y_work_r2": float(r2),
            "geometric_all_15_eta": float(full_values[0]),
            "compatible_principal_12_eta": float(free_values[0]),
            "analytic_eta_rayleigh_upper_bound": float(rayleigh),
            "actual_constrained_source_mass_dual_witness_ratio": float(witness_ratio),
            "full_cover_same_witness_ratio": float(full_cover_ratio),
            "criterion_eta_0_9_rejected": bool(full_values[0] < .9),
        })
    assert all(rows[i+1]["geometric_all_15_eta"] < rows[i]["geometric_all_15_eta"]
               for i in range(2))
    elapsed = time.perf_counter()-started
    info = psutil.Process().memory_info()
    peak = getattr(info, "peak_wset", info.rss)/(1024**2)
    assert elapsed <= 180 and peak <= 1000
    result = {
        "status": "development_independent_same_measure_cut_discriminator",
        "script_sha256": sha(Path(__file__)),
        "source_x_knots_m": list(map(float, x)), "source_y_knots_m": list(map(float, y)),
        "target_x_extent_m": [-.113, 2.127], "target_y_lower_m": -.087,
        "source_and_target_left_edges_fully_clamped": True,
        "source_reference_normal": [0, 0, 1], "pose": "flat_physical_skins_touching",
        "mass_convention": "whole source reference patch Q1 mass; no clipped-mass normalization",
        "pairing_identity": "At exact touching S D(gbar) Q is the tensor overlap mass for source normal hats.",
        "spectral_scope": "All15 geometric normal hats and compatible12 principal map are separately labelled. The actual source constraint has12 normal motions; all15 pressure modes remain in the historical law, so the rectangular full-pressure/source-only map also has a structural nullspace at full cover. Its minimal singular value is not used as the cut discriminator.",
        "asymptotic_proof": "For py=(-beta/2,beta,1), Cy py=(0,0,r2), r2=theta^3/3-b^2/d. Full-reference norm remains positive; Rayleigh eta upper bound and constrained source mass-dual witness ratio tend to zero as O(theta^3). The x mass factor is included and cancels in the normalized ratio.",
        "scope_limit": "Constructive source pairing detects retained cut loss. A smaller eta alone does not prove full-system instability; corrected two-body cancellation and its retained failure disposition remain separate. Different constraints, physical rims, target modulus, hmin and pressure spaces prevent regrading or comparing scaled gamma directly.",
        "production_kernel_or_coupled_execution": False,
        "rows": rows,
    }
    paths["json"].write_text(json.dumps(result, indent=2)+"\n")
    resources = {"elapsed_seconds": elapsed, "peak_process_tree_memory_mb": peak,
                 "children_spawned": 0, "time_cap_seconds": 180,
                 "memory_cap_mb": 1000, "exit_code": 0,
                 "command": "C:/Python/Python314/python.exe docs/d1_review_support/d1_cut_eta_discriminator_20260929.py"}
    paths["resources.json"].write_text(json.dumps(resources, indent=2)+"\n")
    paths["log"].write_text("Independent exact tensor overlap-mass calculation completed.\n"
                            +json.dumps(resources, indent=2)+"\n")
    print(json.dumps({"status": result["status"],
                      "eta": [r["geometric_all_15_eta"] for r in rows],
                      "constrained_witness_ratio": [r["actual_constrained_source_mass_dual_witness_ratio"] for r in rows],
                      "elapsed_seconds": elapsed, "peak_mb": peak}))


if __name__ == "__main__":
    main()
