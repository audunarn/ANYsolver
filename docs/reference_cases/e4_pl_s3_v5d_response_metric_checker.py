"""Independent checker for the V5D spatial-response diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_mixed_mesh_manifest as mesh_manifest
import e4_pl_s3_v2_flat_funnel_checker as reference_checker
import e4_pl_s3_v5b_relaxed_screen_checker as v5b_check
import e4_pl_s3_v5c_stage4a_checker as v5c_check


CONTRACT = REFERENCE / "e4_pl_s3_v5d_response_metric_contract.json"
FORMULATION_ID = v5c_check.FORMULATION_ID
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5d-response-metric-shard-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5d-response-metric-check-v1"
DIAGONALS = v5c_check.DIAGONALS
LEVELS = v5c_check.LEVELS
MASKS = v5c_check.MASKS
FRACTIONS = (10, 25)
NORMAL = v5c_check.NORMAL
PRESSURE = v5c_check.PRESSURE
Z_ONE_SIDED_95 = v5c_check.Z_ONE_SIDED_95


class DiagnosisCheckerError(RuntimeError):
    pass


canonical_bytes = v5c_check.canonical_bytes
sha256_bytes = v5c_check.sha256_bytes
sha256_file = v5c_check.sha256_file
load_canonical = v5c_check.load_canonical
exclusive_write = v5c_check.exclusive_write


def _state_record(level: int, fraction: int, mask: str, diagonal: str) -> dict[str, Any]:
    from scipy import sparse

    if fraction == 0:
        selected: tuple[tuple[int, int], ...] = ()
        mask = "dispersed"
    elif fraction in FRACTIONS and mask in MASKS:
        selected = mesh_manifest.selected_base_cells(mask, fraction * 4)
    else:
        raise DiagnosisCheckerError("unregistered record")
    split = mesh_manifest.expanded_split_cells(selected, level)
    count = (level + 1) ** 2
    coordinates = np.asarray(tuple((i / level, j / level, 0.0) for j in range(level + 1) for i in range(level + 1)))
    row_indices: list[int] = []
    column_indices: list[int] = []
    entries: list[float] = []
    load = np.zeros(6 * count)
    h = 1.0 / level
    q4_coordinates = np.asarray(((0.0, 0.0, 0.0), (h, 0.0, 0.0), (h, h, 0.0), (0.0, h, 0.0)))
    q4 = v5b_check.v5a_check.independent_q4._q4(q4_coordinates, NORMAL)
    q4_load = np.zeros(24)
    q4_load[2::6] = PRESSURE * h * h / 4.0
    cache: dict[tuple[int, ...], Mapping[str, Any]] = {}
    for j in range(level):
        for i in range(level):
            local_entries: list[tuple[tuple[int, ...], Mapping[str, Any], np.ndarray]] = []
            if (i, j) in split:
                for triangle in v5c_check._cell_triangles(i, j, level, diagonal):
                    signature = tuple(node - triangle[0] for node in triangle)
                    made = cache.get(signature)
                    if made is None:
                        origin = coordinates[triangle[0]]
                        made = v5b_check.reconstruct(coordinates[np.asarray(triangle)] - origin)
                        cache[signature] = made
                    local_entries.append((triangle, made, np.asarray(made["pressure_load"])))
            else:
                nodes = (j * (level + 1) + i, j * (level + 1) + i + 1, (j + 1) * (level + 1) + i + 1, (j + 1) * (level + 1) + i)
                local_entries.append((nodes, q4, q4_load))
            for nodes, made, local_load in local_entries:
                dofs = np.asarray([6 * node + dof for node in nodes for dof in range(6)], dtype=np.intp)
                rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
                row_indices.extend(rr.reshape(-1).tolist())
                column_indices.extend(cc.reshape(-1).tolist())
                entries.extend(np.asarray(made["total"]).reshape(-1).tolist())
                np.add.at(load, dofs, local_load)
    size = 6 * count
    stiffness = sparse.coo_matrix((entries, (row_indices, column_indices)), shape=(size, size)).tocsr()
    fixed: set[int] = set()
    for j in range(level + 1):
        for i in range(level + 1):
            node = j * (level + 1) + i
            if i in (0, level) or j in (0, level):
                fixed.update((6 * node, 6 * node + 1, 6 * node + 2))
            if i in (0, level):
                fixed.add(6 * node + 3)
            if j in (0, level):
                fixed.add(6 * node + 4)
    free = np.asarray([index for index in range(size) if index not in fixed], dtype=np.intp)
    solution = np.zeros(size)
    solution[free] = v5c_check._solve(stiffness[free][:, free], load[free])
    residual = float(np.linalg.norm((stiffness @ solution - load)[free], ord=np.inf) / max(np.linalg.norm(load[free], ord=np.inf), 1.0))
    reference_document, reference_center = reference_checker.reference_vector_document(level)
    reference = np.asarray(reference_document["values"], dtype=np.float64)
    reference_sha = sha256_bytes(reference_checker.canonical_bytes(reference_document))
    center_node = (level // 2) * (level + 1) + level // 2
    center = float(solution[6 * center_node + 2])
    center_signed = center / reference_center - 1.0
    w_error = solution[2::6] - reference[2::6]
    rotation = np.column_stack((solution[3::6], solution[4::6])).reshape(-1)
    rotation_reference = np.column_stack((reference[3::6], reference[4::6])).reshape(-1)
    rotation_error = rotation - rotation_reference
    w_l2 = float(np.linalg.norm(w_error) / max(np.linalg.norm(reference[2::6]), np.finfo(np.float64).tiny))
    w_linf = float(np.linalg.norm(w_error, ord=np.inf) / max(np.linalg.norm(reference[2::6], ord=np.inf), np.finfo(np.float64).tiny))
    rotation_l2 = float(np.linalg.norm(rotation_error) / max(np.linalg.norm(rotation_reference), np.finfo(np.float64).tiny))
    solution_total = float(solution @ (stiffness @ solution))
    reference_total = float(reference @ (stiffness @ reference))
    cross = float(solution @ (stiffness @ reference))
    energy_raw = solution_total + reference_total - 2.0 * cross
    floor = 256.0 * np.finfo(np.float64).eps * max(abs(solution_total), abs(reference_total), abs(cross), 1.0)
    if energy_raw < -floor:
        raise DiagnosisCheckerError("negative independent energy-error form")
    energy = math.sqrt(max(energy_raw, 0.0) / max(reference_total, np.finfo(np.float64).tiny))
    return {
        "center_relative_error_hex": abs(center_signed).hex(),
        "center_signed_error_hex": center_signed.hex(),
        "connectivity_sha256": mesh_manifest.connectivity_sha256(level, split, diagonal),
        "diagonal": diagonal,
        "energy_relative_error_hex": energy.hex(),
        "level": level,
        "mask": mask,
        "record_id": f"N{level}:{fraction}PCT:{mask}:{diagonal}",
        "reference_sha256": reference_sha,
        "rotation_relative_l2_error_hex": rotation_l2.hex(),
        "s3_area_fraction_percent": fraction,
        "solve_residual_relative_inf_hex": residual.hex(),
        "w_relative_l2_error_hex": w_l2.hex(),
        "w_relative_linf_error_hex": w_linf.hex(),
    }


def _identity(claim: Mapping[str, Any], independent: Mapping[str, Any]) -> float:
    exact = ("connectivity_sha256", "diagonal", "level", "mask", "record_id", "reference_sha256", "s3_area_fraction_percent")
    if any(claim.get(key) != independent.get(key) for key in exact):
        raise DiagnosisCheckerError("diagnostic record identity mismatch")
    worst = 0.0
    for key in (
        "center_relative_error_hex",
        "center_signed_error_hex",
        "energy_relative_error_hex",
        "rotation_relative_l2_error_hex",
        "w_relative_l2_error_hex",
        "w_relative_linf_error_hex",
    ):
        left = float.fromhex(str(claim[key]))
        right = float.fromhex(str(independent[key]))
        worst = max(worst, abs(left - right) / max(abs(right), 1.0))
    if max(float.fromhex(str(claim["solve_residual_relative_inf_hex"])), float.fromhex(str(independent["solve_residual_relative_inf_hex"]))) > 1.0e-8:
        raise DiagnosisCheckerError("diagnostic residual exceeds bound")
    return worst


def _slope(values: Sequence[float]) -> tuple[float, float]:
    if len(values) != 3 or any(value <= 0.0 for value in values):
        raise DiagnosisCheckerError("invalid slope values")
    x = [math.log(float(level)) for level in LEVELS]
    y = [-math.log(value) for value in values]
    mean_x, mean_y = sum(x) / 3.0, sum(y) / 3.0
    sxx = sum((value - mean_x) ** 2 for value in x)
    slope = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / sxx
    intercept = mean_y - slope * mean_x
    residual = sum((b - (intercept + slope * a)) ** 2 for a, b in zip(x, y))
    return slope, slope - Z_ONE_SIDED_95 * math.sqrt(max(residual, 0.0) / sxx)


def _metric_gate(values: Sequence[float], baseline: Sequence[float], fraction: int) -> tuple[bool, float, float, float, bool]:
    slope, _lower = _slope(values)
    baseline_slope, _ = _slope(baseline)
    ratio = values[-1] / baseline[-1]
    limit = 1.50 if fraction == 25 else 1.25
    successive = all(fine <= 1.02 * coarse for coarse, fine in zip(values, values[1:]))
    passed = slope >= 1.80 and baseline_slope - slope <= 0.15 and ratio <= limit and successive
    return passed, slope, baseline_slope - slope, ratio, successive


def _sequence(rows: Sequence[Mapping[str, Any]], baseline: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: int(row["level"]))
    q4 = sorted(baseline, key=lambda row: int(row["level"]))
    center = [float.fromhex(str(row["center_relative_error_hex"])) for row in ordered]
    center_q4 = [float.fromhex(str(row["center_relative_error_hex"])) for row in q4]
    spatial = [float.fromhex(str(row["w_relative_l2_error_hex"])) for row in ordered]
    spatial_q4 = [float.fromhex(str(row["w_relative_l2_error_hex"])) for row in q4]
    energy = [float.fromhex(str(row["energy_relative_error_hex"])) for row in ordered]
    center_gate, center_slope, center_deficit, center_ratio, center_successive = _metric_gate(center, center_q4, int(ordered[0]["s3_area_fraction_percent"]))
    spatial_gate, spatial_slope, spatial_deficit, spatial_ratio, spatial_successive = _metric_gate(spatial, spatial_q4, int(ordered[0]["s3_area_fraction_percent"]))
    energy_slope, energy_lower = _slope(energy)
    return {
        "center_finest_ratio_hex": center_ratio.hex(),
        "center_gate_passed": center_gate,
        "center_slope_deficit_hex": center_deficit.hex(),
        "center_slope_hex": center_slope.hex(),
        "center_successive_passed": center_successive,
        "energy_slope_hex": energy_slope.hex(),
        "energy_slope_lower_95_hex": energy_lower.hex(),
        "energy_slope_passed": energy_lower >= 0.90,
        "fraction_percent": int(ordered[0]["s3_area_fraction_percent"]),
        "mask": str(ordered[0]["mask"]),
        "record_ids": [str(row["record_id"]) for row in ordered],
        "spatial_finest_ratio_hex": spatial_ratio.hex(),
        "spatial_gate_passed": spatial_gate,
        "spatial_slope_deficit_hex": spatial_deficit.hex(),
        "spatial_slope_hex": spatial_slope.hex(),
        "spatial_successive_passed": spatial_successive,
    }


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise DiagnosisCheckerError("diagnostic proof identity mismatch")
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise DiagnosisCheckerError("diagnostic contract mismatch")
    diagonal = str(proof.get("diagonal"))
    specs = [(level, 0, "dispersed", diagonal) for level in LEVELS]
    specs += [(level, fraction, mask, diagonal) for level in LEVELS for mask in MASKS for fraction in FRACTIONS]
    checked = [_state_record(*spec) for spec in specs]
    claims = {str(row["record_id"]): row for row in proof.get("records", [])}
    if diagonal not in DIAGONALS or len(claims) != 15 or set(claims) != {row["record_id"] for row in checked}:
        raise DiagnosisCheckerError("diagnostic coverage mismatch")
    worst = max(_identity(claims[row["record_id"]], row) for row in checked)
    baseline = [row for row in checked if row["s3_area_fraction_percent"] == 0]
    sequences = []
    for mask in MASKS:
        for fraction in FRACTIONS:
            rows = [row for row in checked if row["mask"] == mask and row["s3_area_fraction_percent"] == fraction]
            sequences.append(_sequence(rows, baseline))
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "diagonal": diagonal,
        "independent_record_count": 15,
        "record_identity_passed": worst <= 3.0e-12,
        "record_identity_worst_relative_inf_hex": worst.hex(),
        "schema": CHECK_SCHEMA,
        "sequence_count": 4,
        "sequence_results": sequences,
        "v5c_reclassified": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-diagnostic-shard", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_canonical(args.proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
