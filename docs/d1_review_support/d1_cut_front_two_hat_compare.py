"""Check the corrected cut-front oracle against three final-source poses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).parent
OUTPUT = HERE / "d1_cut_front_two_hat_compare_20260929.json"


def read(name):
    return json.loads((HERE/name).read_text(encoding="utf-8"))


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    oracle = read("d1_cut_front_two_hat_limit_v3_20260929.json")
    c = np.asarray(oracle["unit_l2_null_coefficients"])
    x_mass = np.asarray((c[0]/12, c[0]/3+c[1]/12,
                         c[0]/12+c[1]/3, c[1]/12))
    production_sha = hashlib.sha256(
        (HERE/"d1_cut_front_shell_work.py").read_bytes()).hexdigest()
    rows = []
    for name in ("010", "005", "0025"):
        current = read(f"d1_cut_front_two_hat_touch_{name}_v7_20260929.json")
        resources = read(
            f"d1_cut_front_two_hat_touch_{name}_v7_resource_20260929.json")
        theta = current["theta"]
        exact_source = (np.linalg.norm(x_mass)
                        *current["expected_scalar_last_y_work"])
        exact_target = np.asarray(oracle[
            "finite_cut_exact_polynomial_work"][str(theta)][
                "normal_gap_gradient_work"])
        actual_target = np.asarray(current[
            "target_normal_work_by_node"])[1:3]
        source_relative = abs(current["source_free_normal_work_l2"]
                              /exact_source-1.0)
        target_relative = float(np.linalg.norm(
            actual_target-exact_target)/np.linalg.norm(exact_target))
        check = current["active_baseline_check"]
        energy = current["energy_check"]
        assert resources["exit_code"] == 0
        assert resources["elapsed_seconds"] < 180.0
        assert resources["peak_process_tree_memory_mb"] < 1000.0
        assert current["probe_sha256"] == production_sha
        assert current["touching"] and current["two_hat_mode"]
        assert source_relative <= 1.0e-12
        assert target_relative <= 1.0e-10
        assert current["virtual_work_residual_l2"] < 1.0e-15
        assert energy["stiffness_minimum_eigenvalue"] > 0.0
        assert energy["stiffness_symmetry_relative"] < 1.0e-10
        assert check["strict_positive_pressure_modes"] == 6
        assert check["selected_projected_active_modes"] == 6
        assert check["signed_half_pascal_perturbation_minimum_pressure_pa"] > 0.0
        assert check["all_supported_complementarity_l1_n"] < 1.0e-10
        rows.append({
            "theta": theta,
            "source_oracle_relative_error": source_relative,
            "target_oracle_relative_error": target_relative,
            "discrete_dual_over_theta_cubed":
                energy["discrete_energy_dual_work"]/theta**3,
            "all_supported_complementarity_l1_n":
                check["all_supported_complementarity_l1_n"],
            "process_elapsed_s": resources["elapsed_seconds"],
            "peak_process_tree_memory_mb":
                resources["peak_process_tree_memory_mb"],
        })
    zero_energy = read("d1_cut_front_zero_cut_energy_v2_20260929.json")
    assert zero_energy["model_builder_sha256"] == production_sha
    assert zero_energy["minimum_eigenvalue"] > 0.0
    assert read("d1_cut_front_zero_cut_energy_v2_resource_20260929.json")[
        "exit_code"] == 0
    result = {
        "status": "development_two_body_cut_front_corrob",
        "production_probe_sha256": production_sha,
        "oracle_null_residual_l2": oracle["null_residual_l2"],
        "oracle_limit_matrix": oracle["full_limit_matrix"],
        "oracle_coefficients": c.tolist(),
        "zero_cut_minimum_stiffness_eigenvalue":
            zero_energy["minimum_eigenvalue"],
        "maximum_source_oracle_relative_error": max(
            row["source_oracle_relative_error"] for row in rows),
        "maximum_target_oracle_relative_error": max(
            row["target_oracle_relative_error"] for row in rows),
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "maximum_source_oracle_relative_error",
        "maximum_target_oracle_relative_error",
        "zero_cut_minimum_stiffness_eigenvalue",
    )}))


if __name__ == "__main__":
    main()
