"""Independent checker for the source-authorized relaxed MIN3 repair funnel."""

from __future__ import annotations

import argparse
import importlib
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
import e4_pl_s3_v5a_screen_checker as v5a_check


CONTRACT = REFERENCE / "e4_pl_s3_v5b_relaxed_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5b-relaxed-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5b-relaxed-screen-check-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
PRESSURE = 1000.0
CBMIN3 = 2.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
ROTATIONAL_INDICES = (3, 4, 9, 10, 15, 16)
DIAGONALS = ("slash", "backslash", "alternating")
FRACTIONS = (1, 5, 10, 25)
LEVELS = (20, 40, 80)
DEVELOPMENT = (
    (20, 5, "dispersed", "slash"),
    (40, 5, "dispersed", "slash"),
    (20, 10, "dispersed", "slash"),
    (40, 10, "dispersed", "slash"),
)
DISPERSED_CAMPAIGN = tuple(
    (level, fraction, "dispersed", diagonal)
    for diagonal in DIAGONALS
    for fraction in FRACTIONS
    for level in LEVELS
)
CHAIN_HOLDOUT = tuple((level, 10, "chain", "slash") for level in LEVELS)
ALL_S3_CONTROL = tuple((level, 100, "all_cells", "alternating") for level in LEVELS)
THIN_THICKNESSES = ("1e-1", "1e-2", "1e-3", "1e-4", "1e-5", "1e-6")


canonical_bytes = v5a_check.canonical_bytes
sha256_file = v5a_check.sha256_file
load_document = v5a_check.load_document
decode_array = v5a_check.decode_array
relative_inf = v5a_check.relative_inf
rank = v5a_check.rank


def _constitutive(thickness: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = float(thickness)
    if not np.isfinite(t) or t <= 0.0:
        raise ValueError("positive finite V5B thickness required")
    plane = np.asarray(
        ((1.0, POISSON, 0.0), (POISSON, 1.0, 0.0), (0.0, 0.0, (1.0 - POISSON) / 2.0)),
        dtype=np.float64,
    )
    membrane = YOUNG * t / (1.0 - POISSON**2) * plane
    bending = YOUNG * t**3 / (12.0 * (1.0 - POISSON**2)) * plane
    shear = (5.0 / 6.0) * YOUNG * t / (2.0 * (1.0 + POISSON)) * np.eye(2)
    return membrane, bending, shear


def _source_phi(bending: np.ndarray, unrelaxed_shear: np.ndarray) -> tuple[float, float, float]:
    bend = float(sum(bending[index, index] for index in ROTATIONAL_INDICES))
    shear = float(sum(unrelaxed_shear[index, index] for index in ROTATIONAL_INDICES))
    if bend <= 0.0 or shear <= 0.0 or not np.isfinite((bend, shear)).all():
        raise ValueError("independent relaxation sums are invalid")
    psi = bend / shear
    return CBMIN3 * psi / (1.0 + CBMIN3 * psi), bend, shear


def reconstruct(vertices: np.ndarray, *, thickness: float = THICKNESS) -> dict[str, Any]:
    points = np.asarray(vertices, dtype=np.float64)
    area, _nx, _ny = v5a_check._metric(points)
    membrane_section, bending_section, shear_section = _constitutive(thickness)
    membrane_b, bending_b, _shear_b = v5a_check._strain_maps(points, (1.0 / 3.0,) * 3)
    membrane = area * membrane_b.T @ membrane_section @ membrane_b
    bending = area * bending_b.T @ bending_section @ bending_b
    unrelaxed_shear = np.zeros((18, 18), dtype=np.float64)
    pressure = np.zeros(18, dtype=np.float64)
    stations = (
        (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
        (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    )
    for coordinate in stations:
        _bm, _bk, shear_b = v5a_check._strain_maps(points, coordinate)
        unrelaxed_shear += area / 3.0 * shear_b.T @ shear_section @ shear_b
        n, l, m, _lg, _mg = v5a_check._interpolation(points, coordinate)
        for node in range(3):
            pressure[6 * node + 2] += PRESSURE * area * n[node] / 3.0
            pressure[6 * node + 3] -= PRESSURE * area * l[node] / 3.0
            pressure[6 * node + 4] += PRESSURE * area * m[node] / 3.0
    phi_squared, bending_sum, shear_sum = _source_phi(bending, unrelaxed_shear)
    shear = phi_squared * unrelaxed_shear
    _local, inverse, determinant = v5a_check.independent_pl._geometry(points[:, :2])
    drill_scale = float(thickness) * YOUNG / (2.0 * (1.0 + POISSON))
    constraint, gram, pl = v5a_check.independent_pl._pl_blocks(inverse, determinant, drill_scale)
    physical = membrane + bending + shear
    total = physical + pl
    return {
        "bending": 0.5 * (bending + bending.T),
        "bending_rotational_diagonal_sum": bending_sum,
        "drill_scale": drill_scale,
        "membrane": 0.5 * (membrane + membrane.T),
        "phi_squared": phi_squared,
        "physical": 0.5 * (physical + physical.T),
        "pl": 0.5 * (pl + pl.T),
        "pl_constraint": constraint,
        "pl_gram": gram,
        "pressure_load": pressure,
        "shear": 0.5 * (shear + shear.T),
        "total": 0.5 * (total + total.T),
        "unrelaxed_shear": 0.5 * (unrelaxed_shear + unrelaxed_shear.T),
        "unrelaxed_shear_rotational_diagonal_sum": shear_sum,
    }


def _local_checks(expected: Mapping[str, Any], vertices: np.ndarray) -> dict[str, Any]:
    sections = dict(zip(("membrane", "bending", "shear"), _constitutive(THICKNESS)))
    area, _nx, _ny = v5a_check._metric(vertices)
    patch_worst = 0.0
    for name in (
        "membrane_x", "membrane_y", "membrane_xy", "shear_x", "shear_y",
        "curvature_xx", "curvature_yy", "curvature_xy",
    ):
        vector, component, target = v5a_check._patch(vertices, name)
        actual = float(vector @ expected[component] @ vector)
        scale = float(expected["phi_squared"]) if component == "shear" else 1.0
        reference = float(scale * area * target @ sections[component] @ target)
        patch_worst = max(patch_worst, abs(actual - reference) / max(abs(reference), 1.0))
        operator_index = {"membrane": 0, "bending": 1, "shear": 2}[component]
        for coordinate in (
            (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
            (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
            (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
        ):
            patch_worst = max(patch_worst, relative_inf(v5a_check._strain_maps(vertices, coordinate)[operator_index] @ vector, target))
    edge_worst = 0.0
    for left, right, opposite in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        tangent = vertices[right, :2] - vertices[left, :2]
        tangent /= np.linalg.norm(tangent)
        rows = []
        for fraction in (0.0, 0.5, 1.0):
            coordinate = np.zeros(3)
            coordinate[left], coordinate[right], coordinate[opposite] = 1.0 - fraction, fraction, 0.0
            rows.append(tangent @ v5a_check._strain_maps(vertices, coordinate)[2])
        edge_worst = max(edge_worst, relative_inf(rows[1], rows[0]), relative_inf(rows[2], rows[0]))
    rigid = float(np.linalg.norm(expected["total"] @ v5a_check._rigid(vertices), ord=np.inf) / max(np.linalg.norm(expected["total"], ord=np.inf), 1.0))
    ranks = {name: rank(expected[name], 1.0e-10) for name in ("physical", "pl", "total")}
    alpha = float(expected["unrelaxed_shear_rotational_diagonal_sum"]) / float(expected["bending_rotational_diagonal_sum"])
    formula_error = abs(float(expected["phi_squared"]) - 1.0 / (1.0 + 0.5 * alpha))
    passed = bool(
        ranks == {"physical": 9, "pl": 3, "total": 12}
        and 0.0 < float(expected["phi_squared"]) <= 1.0
        and max(edge_worst, patch_worst, rigid, formula_error) <= 3.0e-12
    )
    return {
        "edge_worst": edge_worst,
        "formula_error": formula_error,
        "passed": passed,
        "patch_worst": patch_worst,
        "ranks": ranks,
        "rigid": rigid,
    }


def _cell_triangles(i: int, j: int, level: int, diagonal: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    ll = j * (level + 1) + i
    lr, ul, ur = ll + 1, ll + level + 1, ll + level + 2
    selected = diagonal
    if diagonal == "alternating":
        selected = "backslash" if (i + j) % 2 == 0 else "slash"
    if selected == "slash":
        return (ll, lr, ul), (lr, ur, ul)
    if selected == "backslash":
        return (ll, lr, ur), (ll, ur, ul)
    raise ValueError(f"unknown diagonal {diagonal!r}")


def _grid(size: int, diagonal: str, variant: str) -> dict[str, Any]:
    old_reconstruct = v5a_check.reconstruct
    old_triangles = v5a_check._triangles
    try:
        v5a_check.reconstruct = lambda vertices: reconstruct(vertices)
        v5a_check._triangles = _cell_triangles
        return v5a_check._grid(size, diagonal, variant)
    finally:
        v5a_check.reconstruct = old_reconstruct
        v5a_check._triangles = old_triangles


def _macro_expected_energy(made: Mapping[str, Any], component: str, target: np.ndarray) -> float:
    sections = dict(zip(("membrane", "bending", "shear"), _constitutive(THICKNESS)))
    weighted_area = 0.0
    for element in made["elements"]:
        vertices = made["coordinates"][np.asarray(element)]
        if len(element) == 3:
            area, _nx, _ny = v5a_check._metric(vertices)
            scale = float(reconstruct(vertices)["phi_squared"]) if component == "shear" else 1.0
        else:
            x, y = vertices[:, 0], vertices[:, 1]
            area = 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
            scale = 1.0
        weighted_area += scale * area
    return float(weighted_area * target @ sections[component] @ target)


def _record(
    level: int,
    fraction: int,
    mask: str,
    diagonal: str,
    *,
    thickness: float = THICKNESS,
) -> dict[str, Any]:
    reference = importlib.import_module("e4_pl_s3_v2_flat_funnel_checker")
    sparse_linalg = importlib.import_module("scipy.sparse.linalg")
    original_reconstruct = v5a_check.reconstruct
    original_triangles = v5a_check._triangles
    original_selected = mesh_manifest.selected_base_cells
    original_connectivity = mesh_manifest.connectivity_sha256
    original_thickness = reference.REFERENCE["thickness"]
    original_spsolve = sparse_linalg.spsolve
    all_s3 = mask == "all_cells"

    def refined_spsolve(matrix: Any, right: Any) -> Any:
        sparse = importlib.import_module("scipy.sparse")
        diagonal = np.asarray(matrix.diagonal(), dtype=np.float64)
        scale = np.sqrt(np.maximum(np.abs(diagonal), np.finfo(np.float64).tiny))
        inverse_scale = 1.0 / scale
        diagonal_scale = sparse.diags(inverse_scale, format="csc")
        equilibrated = (diagonal_scale @ matrix @ diagonal_scale).tocsc()
        factor = sparse_linalg.splu(equilibrated, permc_spec="COLAMD")

        def solve(rhs: Any) -> Any:
            values = np.asarray(rhs, dtype=np.float64)
            scaled = inverse_scale * values if values.ndim == 1 else inverse_scale[:, None] * values
            answer = factor.solve(scaled)
            return inverse_scale * answer if answer.ndim == 1 else inverse_scale[:, None] * answer

        solution = solve(right)
        for _pass in range(2):
            solution = solution + solve(right - matrix @ solution)
        return solution

    try:
        v5a_check.reconstruct = lambda vertices: reconstruct(vertices, thickness=thickness)
        v5a_check._triangles = _cell_triangles
        mesh_manifest.selected_base_cells = (
            (lambda _mask, _count: tuple((i, j) for j in range(20) for i in range(20)))
            if all_s3
            else (lambda _mask, count: original_selected(mask, count))
        )
        mesh_manifest.connectivity_sha256 = lambda made_level, split, _diagonal: original_connectivity(
            made_level, split, diagonal
        )
        reference.REFERENCE["thickness"] = float(thickness)
        reference._REFERENCE_DOCUMENT_CACHE.clear()
        sparse_linalg.spsolve = refined_spsolve
        row = v5a_check._development(level, 25 if all_s3 else fraction)
    finally:
        v5a_check.reconstruct = original_reconstruct
        v5a_check._triangles = original_triangles
        mesh_manifest.selected_base_cells = original_selected
        mesh_manifest.connectivity_sha256 = original_connectivity
        reference.REFERENCE["thickness"] = original_thickness
        reference._REFERENCE_DOCUMENT_CACHE.clear()
        sparse_linalg.spsolve = original_spsolve
    row["diagonal"] = diagonal
    row["mask"] = mask
    row["record_id"] = f"N{level}:{fraction}PCT:{mask}:{diagonal}:t={float(thickness).hex()}"
    row["thickness_hex"] = float(thickness).hex()
    return row


def _record_identity(produced: Mapping[str, Any], checked: Mapping[str, Any]) -> float:
    for key in ("connectivity_sha256", "diagonal", "level", "mask", "record_id", "reference_sha256", "thickness_hex"):
        if produced.get(key) != checked.get(key):
            raise ValueError(f"repair-funnel record identity mismatch: {key}")
    worst = 0.0
    for key in (
        "pl_participation_hex", "reference_center_hex", "response_center_hex",
        "response_relative_error_hex",
    ):
        left = float.fromhex(str(produced[key]))
        right = float.fromhex(str(checked[key]))
        worst = max(worst, abs(left - right) / max(abs(right), 1.0))
    # Sparse assembly/solve order can change the reported backward residual by
    # a few ulps without changing the scientific response.  Require both
    # independently computed residuals to satisfy the preregistered hard bound
    # instead of misclassifying their diagnostic difference as construction
    # drift.
    if max(
        float.fromhex(str(produced["solve_residual_relative_inf_hex"])),
        float.fromhex(str(checked["solve_residual_relative_inf_hex"])),
    ) > 1.0e-8:
        raise ValueError("repair-funnel solve residual exceeds its hard bound")
    return worst


def _development_gate(rows: Sequence[Mapping[str, Any]]) -> bool:
    by_pair = {(int(row["level"]), int(str(row["record_id"]).split(":")[1][:-3])): row for row in rows}
    if len(rows) != 4:
        return False
    passed = True
    for fraction in (5, 10):
        coarse = float.fromhex(by_pair[(20, fraction)]["response_relative_error_hex"])
        fine = float.fromhex(by_pair[(40, fraction)]["response_relative_error_hex"])
        passed = passed and fine <= 1.02 * coarse and fine <= 0.02
    return bool(passed and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in rows))


def _campaign_gate(rows: Sequence[Mapping[str, Any]], q4_rows: Sequence[Mapping[str, Any]]) -> bool:
    q4 = {int(row["level"]): float.fromhex(row["response_relative_error_hex"]) for row in q4_rows}
    groups: dict[tuple[str, int, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        fraction = int(str(row["record_id"]).split(":")[1][:-3])
        groups.setdefault((str(row["mask"]), fraction, str(row["diagonal"])), []).append(row)
    if len(rows) != 42 or len(groups) != 14:
        return False
    passed = True
    for (mask, fraction, _diagonal), sequence in groups.items():
        ordered = sorted(sequence, key=lambda item: int(item["level"]))
        errors = [float.fromhex(item["response_relative_error_hex"]) for item in ordered]
        passed = passed and all(fine <= 1.02 * coarse for coarse, fine in zip(errors, errors[1:])) and errors[-1] <= 0.02
        if mask != "all_cells":
            limit = 1.5 if fraction == 25 else 1.25
            passed = passed and errors[-1] <= limit * q4[80]
    return bool(passed and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in rows))


def _thin_gate(rows: Sequence[Mapping[str, Any]]) -> bool:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["thickness_token"]), []).append(row)
    if len(rows) != 12 or tuple(groups) != THIN_THICKNESSES:
        return False
    passed = True
    ratios: list[float] = []
    phi: dict[int, list[float]] = {20: [], 40: []}
    for token in THIN_THICKNESSES:
        sequence = sorted(groups[token], key=lambda item: int(item["level"]))
        errors = [float.fromhex(item["response_relative_error_hex"]) for item in sequence]
        passed = passed and errors[1] <= 1.02 * errors[0] and errors[1] <= 0.02
        ratios.append(float.fromhex(sequence[1]["response_center_hex"]) / float.fromhex(sequence[1]["reference_center_hex"]))
        for item in sequence:
            value = float.fromhex(item["phi_squared_hex"])
            phi[int(item["level"])].append(value)
            passed = passed and 0.0 < value <= 1.0
    passed = passed and all(all(right < left for left, right in zip(values, values[1:])) for values in phi.values())
    thin = ratios[2:]
    spread = (max(thin) - min(thin)) / max(abs(sum(thin) / len(thin)), np.finfo(float).tiny)
    return bool(passed and spread <= 0.005 and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in rows))


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise ValueError("unexpected V5B proof identity")
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise ValueError("V5B proof contract hash mismatch")
    if proof.get("production_boundary") != {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise ValueError("V5B production boundary mismatch")
    if proof.get("stage4a_rerun_authorized") is not False or proof.get("activation_authorized") is not False:
        raise ValueError("V5B screen improperly authorizes a later stage")
    contract = load_document(CONTRACT)
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    expected = reconstruct(vertices)
    payloads = proof["local"]["payloads"]
    local_identity = max(
        relative_inf(decode_array(payloads[name]), value)
        for name, value in expected.items()
        if isinstance(value, np.ndarray)
    )
    local = _local_checks(expected, vertices)
    construction_identity = local_identity

    macro_identity = 0.0
    macro_hard = 0.0
    macro_count = 0
    macro = proof.get("macrocell", {})
    if local["passed"] and macro:
        stored_rows = {
            (row["size"], row["diagonal"], row["variant"]): row
            for row in macro.get("records", [])
        }
        for size in (1, 2, 4):
            variants = ("all_s3",) if size == 1 else ("all_s3", "isolated", "strip")
            for diagonal in DIAGONALS:
                for variant in variants:
                    made = _grid(size, diagonal, variant)
                    key = f"{size}x{size}:{diagonal}:{variant}"
                    stored_matrix = macro["matrices"][key]
                    macro_identity = max(
                        macro_identity,
                        relative_inf(decode_array(stored_matrix["condensed"]), made["condensed"]),
                        relative_inf(decode_array(stored_matrix["q4_condensed"]), made["q4_condensed"]),
                    )
                    stored = stored_rows[(size, diagonal, variant)]
                    interface = v5a_check._interface_normal_worst(made["coordinates"], made["elements"])
                    macro_hard = max(macro_hard, interface, abs(float.fromhex(stored["interface_action_reaction_relative_inf_hex"]) - interface))
                    for name in (
                        "membrane_x", "membrane_y", "membrane_xy", "shear_x", "shear_y",
                        "curvature_xx", "curvature_yy", "curvature_xy",
                    ):
                        vector, component, target = v5a_check._patch(made["coordinates"], name)
                        energy = float(vector @ made["total"] @ vector)
                        source_expected = _macro_expected_energy(made, component, target)
                        error = abs(energy - source_expected) / max(abs(source_expected), 1.0)
                        claim = stored["patch_modes"][name]
                        macro_hard = max(
                            macro_hard,
                            error,
                            abs(float.fromhex(claim["energy_relative_error_hex"]) - error),
                            abs(float.fromhex(claim["source_expected_energy_hex"]) - source_expected) / max(abs(source_expected), 1.0),
                        )
                    rigid = v5a_check._rigid(made["coordinates"])
                    load_error = max(
                        abs(float(rigid[:, 2] @ made["load"]) - PRESSURE),
                        abs(float(rigid[:, 3] @ made["load"]) - PRESSURE / 2.0),
                        abs(float(rigid[:, 4] @ made["load"]) + PRESSURE / 2.0),
                    ) / PRESSURE
                    macro_hard = max(macro_hard, load_error, abs(float.fromhex(stored["load_work_relative_error_hex"]) - load_error))
                    macro_count += 1
    mixed = bool(local["passed"] and macro_count == 21 and macro_identity <= 3.0e-13 and macro_hard <= 1.0e-10)
    construction_identity = max(construction_identity, macro_identity)

    funnel = proof.get("repair_funnel", {})
    development_claims = funnel.get("development", {}).get("records", [])
    development_rows = [_record(*spec) for spec in DEVELOPMENT] if mixed else []
    record_identity = 0.0
    if len(development_claims) == len(development_rows):
        claims = {row["record_id"]: row for row in development_claims}
        for row in development_rows:
            record_identity = max(record_identity, _record_identity(claims[row["record_id"]], row))
    else:
        record_identity = float("inf")
    development_passed = bool(mixed and record_identity <= 3.0e-12 and _development_gate(development_rows))

    campaign_passed = False
    thin_passed = False
    campaign_count = 0
    thin_count = 0
    if development_passed:
        specs = sorted(set(DISPERSED_CAMPAIGN + CHAIN_HOLDOUT + ALL_S3_CONTROL))
        campaign_rows = [_record(*spec) for spec in specs]
        campaign_rows.sort(key=lambda row: row["record_id"])
        q4_rows = [_record(level, 0, "dispersed", "slash") for level in LEVELS]
        campaign_claims = {row["record_id"]: row for row in funnel.get("campaign", {}).get("records", [])}
        q4_claims = {row["record_id"]: row for row in funnel.get("campaign", {}).get("q4_baseline_records", [])}
        if len(campaign_claims) == len(campaign_rows) and len(q4_claims) == len(q4_rows):
            for row in campaign_rows:
                record_identity = max(record_identity, _record_identity(campaign_claims[row["record_id"]], row))
            for row in q4_rows:
                record_identity = max(record_identity, _record_identity(q4_claims[row["record_id"]], row))
            campaign_passed = bool(record_identity <= 3.0e-12 and _campaign_gate(campaign_rows, q4_rows))
        campaign_count = len(campaign_rows)
    if campaign_passed:
        thin_rows: list[dict[str, Any]] = []
        for token in THIN_THICKNESSES:
            thickness = float(token)
            for level in (20, 40):
                row = _record(level, 100, "all_cells", "slash", thickness=thickness)
                triangle = np.asarray(((0.0, 0.0, 0.0), (1.0 / level, 0.0, 0.0), (0.0, 1.0 / level, 0.0)))
                row["phi_squared_hex"] = float(reconstruct(triangle, thickness=thickness)["phi_squared"]).hex()
                row["thickness_token"] = token
                thin_rows.append(row)
        thin_claims = {row["record_id"]: row for row in funnel.get("thin_regime", {}).get("records", [])}
        if len(thin_claims) == len(thin_rows):
            for row in thin_rows:
                claim = thin_claims[row["record_id"]]
                record_identity = max(record_identity, _record_identity(claim, row))
                record_identity = max(record_identity, abs(float.fromhex(claim["phi_squared_hex"]) - float.fromhex(row["phi_squared_hex"])))
                if claim.get("thickness_token") != row["thickness_token"]:
                    raise ValueError("thin-regime thickness token mismatch")
            thin_passed = bool(record_identity <= 3.0e-12 and _thin_gate(thin_rows))
        thin_count = len(thin_rows)
    construction = bool(construction_identity <= 3.0e-13 and record_identity <= 3.0e-12)
    return {
        "authority_complete": contract.get("schema") == "anysolver.e4-pl-s3-v5b-relaxed-screen-contract-v1",
        "campaign_passed": campaign_passed,
        "candidate_formulation_id": FORMULATION_ID,
        "construction_identity_passed": construction,
        "development_passed": development_passed,
        "independent_campaign_record_count": campaign_count,
        "independent_local_identity_worst_relative_inf_hex": local_identity.hex(),
        "independent_macrocell_hard_worst_relative_inf_hex": macro_hard.hex(),
        "independent_macrocell_identity_worst_relative_inf_hex": macro_identity.hex(),
        "independent_macrocell_record_count": macro_count,
        "independent_record_identity_worst_relative_inf_hex": record_identity.hex(),
        "independent_thin_record_count": thin_count,
        "local_operator_passed": bool(local["passed"]),
        "mixed_interface_passed": mixed,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
        "thin_regime_passed": thin_passed,
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_document(args.verify_proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
