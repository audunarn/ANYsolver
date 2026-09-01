"""Bounded producer for the source-authorized relaxed MIN3 repair funnel.

The V5A interpolation and unrelaxed operators remain frozen.  V5B applies
only the official MYSTRAN/UHM relaxation identity, with CBMIN3=2 and hence
C_s=1/2.  This research producer does not import or modify an S3 production
implementation and cannot authorize Stage 4A or activation.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib
import itertools
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_mixed_mesh_manifest as mesh_manifest
import e4_pl_s3_v5a_screen_producer as v5a


CONTRACT = REFERENCE / "e4_pl_s3_v5b_relaxed_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5b-relaxed-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5b-relaxed-screen-check-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v5b-relaxed-screen-aggregate-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
PRESSURE = 1000.0
SHEAR_CORRECTION = 5.0 / 6.0
CBMIN3 = 2.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
ROTATIONAL_INDICES = np.asarray((3, 4, 9, 10, 15, 16), dtype=np.intp)
PERMUTATIONS = tuple(itertools.permutations(range(3)))
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
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


class ScreenError(RuntimeError):
    pass


canonical_bytes = v5a.canonical_bytes
sha256_file = v5a.sha256_file
load_canonical = v5a.load_canonical
exclusive_write = v5a.exclusive_write
array_payload = v5a.array_payload
relative_inf = v5a.relative_inf


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5b-relaxed-screen-contract-v1":
        raise ScreenError("unexpected V5B relaxed-screen contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != item["bytes"]
            or sha256_file(path) != item["sha256"]
        ):
            raise ScreenError(f"frozen input mismatch: {path}")
    status = load_canonical(REFERENCE / "e4_pl_s3_v5b_relaxation_authority_status.json")
    if (
        status.get("terminal") != "PROVISIONAL_GO_E4_PL_S3_V5B_RELAXED_REPAIR_FUNNEL"
        or status.get("next_gate") != "BOUNDED_V5B_RELAXED_LOCAL_INTERFACE_THIN_SCREEN"
        or status.get("stage4a_rerun_authorized") is not False
    ):
        raise ScreenError("V5B relaxation authority does not authorize this screen")
    relaxation = contract.get("relaxation", {})
    if relaxation != {
        "cbmin3": "2",
        "coefficient_fitting_forbidden": True,
        "formula": "PHI_SQUARED=CBMIN3*BENSUM/SHRSUM/(1+CBMIN3*BENSUM/SHRSUM)",
        "uhm_c_s": "1/2",
    }:
        raise ScreenError("V5B relaxation identity mismatch")
    return contract


def _section(thickness: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = float(thickness)
    if not np.isfinite(t) or t <= 0.0:
        raise ScreenError("V5B thickness must be finite and positive")
    normalized = np.asarray(
        ((1.0, POISSON, 0.0), (POISSON, 1.0, 0.0), (0.0, 0.0, (1.0 - POISSON) / 2.0)),
        dtype=np.float64,
    )
    membrane = YOUNG * t / (1.0 - POISSON**2) * normalized
    bending = YOUNG * t**3 / (12.0 * (1.0 - POISSON**2)) * normalized
    shear = SHEAR_CORRECTION * YOUNG * t / (2.0 * (1.0 + POISSON)) * np.eye(2)
    return membrane, bending, shear


def _phi_squared(bending: np.ndarray, unrelaxed_shear: np.ndarray) -> tuple[float, float, float]:
    bending_sum = float(sum(bending[index, index] for index in ROTATIONAL_INDICES))
    shear_sum = float(sum(unrelaxed_shear[index, index] for index in ROTATIONAL_INDICES))
    if not np.isfinite(bending_sum) or not np.isfinite(shear_sum) or bending_sum <= 0.0 or shear_sum <= 0.0:
        raise ScreenError("MIN3 relaxation diagonal sums must be finite and positive")
    psi_hat = bending_sum / shear_sum
    phi_squared = CBMIN3 * psi_hat / (1.0 + CBMIN3 * psi_hat)
    if not 0.0 < phi_squared <= 1.0:
        raise ScreenError("MIN3 relaxation factor is outside (0,1]")
    return phi_squared, bending_sum, shear_sum


def min3_components(
    coordinates: Sequence[Sequence[float]],
    *,
    thickness: float = THICKNESS,
    normal: Sequence[float] = NORMAL,
) -> dict[str, Any]:
    vertices = np.asarray(coordinates, dtype=np.float64)
    if vertices.shape == (3, 2):
        vertices = np.column_stack((vertices, np.zeros(3)))
    if vertices.shape != (3, 3) or not np.all(np.isfinite(vertices)):
        raise ScreenError("V5B vertices must be finite 3x2 or 3x3 coordinates")
    normal_array = np.asarray(normal, dtype=np.float64)
    if normal_array.shape != (3,) or not np.isfinite(normal_array).all() or np.linalg.norm(normal_array) == 0.0:
        raise ScreenError("V5B normal must be a finite nonzero vector")
    _xy, area, _dx, _dy = v5a._geometry(vertices)
    membrane_section, bending_section, shear_section = _section(thickness)
    membrane_b, bending_b, _ = v5a._operators(vertices, (1.0 / 3.0,) * 3)
    membrane = area * membrane_b.T @ membrane_section @ membrane_b
    bending = area * bending_b.T @ bending_section @ bending_b
    unrelaxed_shear = np.zeros((18, 18), dtype=np.float64)
    for station in (
        (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
        (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    ):
        _bm, _bb, shear_b = v5a._operators(vertices, station)
        unrelaxed_shear += area / 3.0 * shear_b.T @ shear_section @ shear_b
    phi_squared, bending_sum, shear_sum = _phi_squared(bending, unrelaxed_shear)
    shear = phi_squared * unrelaxed_shear
    constraint, gram, _old_pl, _old_scale = v5a.common._native_pl(vertices)
    drill_scale = float(thickness) * YOUNG / (2.0 * (1.0 + POISSON))
    pl = drill_scale * constraint.T @ gram @ constraint
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
        "pressure_load": v5a._pressure_load(vertices),
        "shear": 0.5 * (shear + shear.T),
        "total": 0.5 * (total + total.T),
        "unrelaxed_shear": 0.5 * (unrelaxed_shear + unrelaxed_shear.T),
        "unrelaxed_shear_rotational_diagonal_sum": shear_sum,
    }


def _source_expected_energy(
    made: Mapping[str, Any], area: float, component: str, target: np.ndarray, sections: Mapping[str, np.ndarray]
) -> float:
    scale = float(made["phi_squared"]) if component == "shear" else 1.0
    return float(scale * area * target @ sections[component] @ target)


def local_proof() -> dict[str, Any]:
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    made = min3_components(vertices)
    sections = dict(zip(("membrane", "bending", "shear"), _section(THICKNESS)))
    _xy, area, _dx, _dy = v5a._geometry(vertices)
    patch_worst = 0.0
    patch_rows: dict[str, Any] = {}
    for name, (vector, component, target) in v5a._patch_modes(vertices).items():
        energy = float(vector @ made[component] @ vector)
        expected = _source_expected_energy(made, area, component, target, sections)
        energy_error = abs(energy - expected) / max(abs(expected), 1.0)
        operator_index = {"membrane": 0, "bending": 1, "shear": 2}[component]
        field_error = 0.0
        for station in (
            (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
            (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
            (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
        ):
            field_error = max(field_error, relative_inf(v5a._operators(vertices, station)[operator_index] @ vector, target))
        patch_worst = max(patch_worst, energy_error, field_error)
        patch_rows[name] = {
            "energy_hex": energy.hex(),
            "field_relative_inf_hex": field_error.hex(),
            "source_expected_energy_hex": expected.hex(),
            "source_relative_error_hex": energy_error.hex(),
        }
    d3_worst = 0.0
    reversal_worst = 0.0
    for order in PERMUTATIONS:
        permutation = v5a.q4_source._block_permutation(order)
        permuted = min3_components(vertices[np.asarray(order)])
        reversed_made = min3_components(vertices[np.asarray(order)], normal=-NORMAL)
        d3_worst = max(d3_worst, relative_inf(permutation.T @ permuted["total"] @ permutation, made["total"]))
        reversal_worst = max(reversal_worst, relative_inf(permutation.T @ reversed_made["total"] @ permutation, made["total"]))
    rigid = float(np.linalg.norm(made["total"] @ v5a._rigid_modes(vertices), ord=np.inf) / max(np.linalg.norm(made["total"], ord=np.inf), 1.0))
    ranks = {name: v5a.common._rank(made[name], 1.0e-10) for name in ("physical", "pl", "total")}
    first, second = np.arange(1.0, 19.0), np.arange(18.0, 0.0, -1.0)
    work = abs(float(first @ made["total"] @ second) - float(second @ made["total"] @ first)) / max(abs(float(first @ made["total"] @ second)), 1.0)
    rigid_modes = v5a._rigid_modes(vertices)
    load = made["pressure_load"]
    centroid = np.mean(vertices[:, :2], axis=0)
    load_worst = max(
        abs(float(rigid_modes[:, 2] @ load) - PRESSURE * area),
        abs(float(rigid_modes[:, 3] @ load) - PRESSURE * area * centroid[1]),
        abs(float(rigid_modes[:, 4] @ load) + PRESSURE * area * centroid[0]),
    ) / max(PRESSURE * area, 1.0)
    alpha = float(made["unrelaxed_shear_rotational_diagonal_sum"]) / float(made["bending_rotational_diagonal_sum"])
    uhm_phi = 1.0 / (1.0 + 0.5 * alpha)
    relaxation_error = abs(float(made["phi_squared"]) - uhm_phi) / max(abs(uhm_phi), 1.0)
    diagnostics = {
        "d3_worst_relative_inf_hex": d3_worst.hex(),
        "director_reversal_worst_relative_inf_hex": reversal_worst.hex(),
        "edge_tangential_shear_worst_relative_inf_hex": v5a._edge_shear_worst(vertices).hex(),
        "load_work_worst_relative_inf_hex": load_worst.hex(),
        "patch_worst_relative_error_hex": patch_worst.hex(),
        "phi_squared_hex": float(made["phi_squared"]).hex(),
        "physical_rank": ranks["physical"],
        "pl_rank": ranks["pl"],
        "relaxation_formula_relative_error_hex": relaxation_error.hex(),
        "rigid_residual_relative_inf_hex": rigid.hex(),
        "symmetry_relative_inf_hex": relative_inf(made["total"], made["total"].T).hex(),
        "total_rank": ranks["total"],
        "work_conjugacy_relative_hex": work.hex(),
    }
    diagnostics["gate_passed"] = bool(
        ranks == {"physical": 9, "pl": 3, "total": 12}
        and 0.0 < float(made["phi_squared"]) <= 1.0
        and max(patch_worst, rigid, load_worst, work, relaxation_error, d3_worst, reversal_worst) <= 3.0e-12
        and float.fromhex(diagnostics["edge_tangential_shear_worst_relative_inf_hex"]) <= 3.0e-12
        and float.fromhex(diagnostics["symmetry_relative_inf_hex"]) <= 3.0e-13
    )
    payloads = {name: array_payload(np.asarray(value)) for name, value in made.items() if isinstance(value, np.ndarray)}
    return {"diagnostics": diagnostics, "patch_modes": patch_rows, "payloads": payloads}


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
    raise ScreenError(f"unknown diagonal {diagonal!r}")


def _with_v5b_grid(size: int, diagonal: str, variant: str) -> dict[str, Any]:
    old_component = v5a.min3_components
    old_triangles = v5a.common._cell_triangles
    try:
        v5a.min3_components = lambda coordinates, normal=NORMAL: min3_components(coordinates, normal=normal)
        v5a.common._cell_triangles = _cell_triangles
        return v5a._grid(size, diagonal, variant)
    finally:
        v5a.min3_components = old_component
        v5a.common._cell_triangles = old_triangles


def _macro_expected_energy(made: Mapping[str, Any], component: str, target: np.ndarray) -> float:
    sections = dict(zip(("membrane", "bending", "shear"), _section(THICKNESS)))
    weighted_area = 0.0
    for element in made["elements"]:
        vertices = made["coordinates"][np.asarray(element)]
        if len(element) == 3:
            _xy, area, _dx, _dy = v5a._geometry(vertices)
            scale = float(min3_components(vertices)["phi_squared"]) if component == "shear" else 1.0
        else:
            x, y = vertices[:, 0], vertices[:, 1]
            area = 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
            scale = 1.0
        weighted_area += scale * area
    return float(weighted_area * target @ sections[component] @ target)


def macrocell_proof() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    matrices: dict[str, Any] = {}
    hard_worst = 0.0
    dtn_worst = 0.0
    for size in (1, 2, 4):
        variants = ("all_s3",) if size == 1 else ("all_s3", "isolated", "strip")
        for diagonal in DIAGONALS:
            for variant in variants:
                made = _with_v5b_grid(size, diagonal, variant)
                key = f"{size}x{size}:{diagonal}:{variant}"
                matrices[key] = {
                    "condensed": array_payload(made["condensed"]),
                    "q4_condensed": array_payload(made["q4_condensed"]),
                }
                patch_rows: dict[str, Any] = {}
                interface_error = v5a._interface_normal_worst(made["coordinates"], made["elements"])
                hard_worst = max(hard_worst, interface_error)
                for name, (vector, component, target) in v5a._patch_modes(made["coordinates"]).items():
                    energy = float(vector @ made["total"] @ vector)
                    expected = _macro_expected_energy(made, component, target)
                    error = abs(energy - expected) / max(abs(expected), 1.0)
                    action = made["total"] @ vector
                    interior_error = 0.0
                    if made["interior"].size:
                        interior_error = float(np.linalg.norm(action[made["interior"]], ord=np.inf) / max(np.linalg.norm(action[made["boundary"]], ord=np.inf), 1.0))
                    patch_rows[name] = {
                        "energy_relative_error_hex": error.hex(),
                        "interior_action_classifying": False,
                        "interior_action_relative_inf_hex": interior_error.hex(),
                        "source_expected_energy_hex": expected.hex(),
                    }
                    hard_worst = max(hard_worst, error)
                rigid = v5a._rigid_modes(made["coordinates"])
                load_error = max(
                    abs(float(rigid[:, 2] @ made["load"]) - PRESSURE),
                    abs(float(rigid[:, 3] @ made["load"]) - PRESSURE / 2.0),
                    abs(float(rigid[:, 4] @ made["load"]) + PRESSURE / 2.0),
                ) / PRESSURE
                hard_worst = max(hard_worst, load_error)
                dtn = relative_inf(made["condensed"], made["q4_condensed"])
                dtn_worst = max(dtn_worst, dtn)
                records.append({
                    "diagonal": diagonal,
                    "dtn_q4_relative_inf_hex": dtn.hex(),
                    "interface_action_reaction_relative_inf_hex": interface_error.hex(),
                    "load_work_relative_error_hex": load_error.hex(),
                    "patch_modes": patch_rows,
                    "size": size,
                    "variant": variant,
                })
    return {
        "diagnostics": {
            "dtn_q4_diagnostic_worst_relative_inf_hex": dtn_worst.hex(),
            "gate_passed": hard_worst <= 1.0e-10,
            "hard_source_patch_interface_worst_relative_inf_hex": hard_worst.hex(),
            "record_count": len(records),
        },
        "matrices": matrices,
        "records": records,
    }


def _record(
    level: int,
    fraction: int,
    mask: str,
    diagonal: str,
    *,
    thickness: float = THICKNESS,
) -> dict[str, Any]:
    reference = importlib.import_module("e4_pl_s3_v2_flat_funnel_producer")
    sparse_linalg = importlib.import_module("scipy.sparse.linalg")
    original_component = v5a.min3_components
    original_triangles = v5a.common._cell_triangles
    original_selected = mesh_manifest.selected_base_cells
    original_connectivity = mesh_manifest.connectivity_sha256
    original_thickness = reference.THICKNESS
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
        # Reuse one deterministic, diagonally equilibrated factorization for
        # residual correction.  The assembled system itself is unchanged.
        for _pass in range(2):
            solution = solution + solve(right - matrix @ solution)
        return solution

    try:
        v5a.min3_components = lambda coordinates, normal=NORMAL: min3_components(
            coordinates, thickness=thickness, normal=normal
        )
        v5a.common._cell_triangles = _cell_triangles
        mesh_manifest.selected_base_cells = (
            (lambda _mask, _count: tuple((i, j) for j in range(20) for i in range(20)))
            if all_s3
            else (lambda _mask, count: original_selected(mask, count))
        )
        mesh_manifest.connectivity_sha256 = lambda made_level, split, _diagonal: original_connectivity(
            made_level, split, diagonal
        )
        reference.THICKNESS = float(thickness)
        reference._REFERENCE_CACHE.clear()
        sparse_linalg.spsolve = refined_spsolve
        row = v5a._development_record(level, 25 if all_s3 else fraction)
    finally:
        v5a.min3_components = original_component
        v5a.common._cell_triangles = original_triangles
        mesh_manifest.selected_base_cells = original_selected
        mesh_manifest.connectivity_sha256 = original_connectivity
        reference.THICKNESS = original_thickness
        reference._REFERENCE_CACHE.clear()
        sparse_linalg.spsolve = original_spsolve
    row["diagonal"] = diagonal
    row["mask"] = mask
    row["record_id"] = f"N{level}:{fraction}PCT:{mask}:{diagonal}:t={float(thickness).hex()}"
    row["thickness_hex"] = float(thickness).hex()
    return row


def _development_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_id = {(int(row["level"]), int(row["record_id"].split(":")[1][:-3])): row for row in rows}
    worst_factor = 0.0
    passed = len(rows) == 4
    for fraction in (5, 10):
        coarse = float.fromhex(by_id[(20, fraction)]["response_relative_error_hex"])
        fine = float.fromhex(by_id[(40, fraction)]["response_relative_error_hex"])
        factor = fine / max(coarse, np.finfo(float).tiny)
        worst_factor = max(worst_factor, factor)
        passed = passed and fine <= 1.02 * coarse and fine <= 0.02
    passed = passed and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in rows)
    return {"gate_passed": bool(passed), "record_count": len(rows), "successive_error_factor_worst_hex": worst_factor.hex()}


def _campaign_gate(rows: Sequence[Mapping[str, Any]], q4_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    q4 = {int(row["level"]): float.fromhex(row["response_relative_error_hex"]) for row in q4_rows}
    groups: dict[tuple[str, int, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        parts = str(row["record_id"]).split(":")
        fraction = int(parts[1][:-3])
        groups.setdefault((str(row["mask"]), fraction, str(row["diagonal"])), []).append(row)
    worst_factor = 0.0
    worst_ratio = 0.0
    passed = len(rows) == 42 and len(groups) == 14
    for (mask, fraction, _diagonal), sequence in groups.items():
        ordered = sorted(sequence, key=lambda item: int(item["level"]))
        errors = [float.fromhex(item["response_relative_error_hex"]) for item in ordered]
        for coarse, fine in zip(errors, errors[1:]):
            factor = fine / max(coarse, np.finfo(float).tiny)
            worst_factor = max(worst_factor, factor)
            passed = passed and fine <= 1.02 * coarse
        passed = passed and errors[-1] <= 0.02
        if mask != "all_cells":
            limit = 1.5 if fraction == 25 else 1.25
            ratio = errors[-1] / max(q4[80], np.finfo(float).tiny)
            worst_ratio = max(worst_ratio, ratio / limit)
            passed = passed and ratio <= limit
    passed = passed and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in rows)
    return {
        "gate_passed": bool(passed),
        "record_count": len(rows),
        "sequence_count": len(groups),
        "successive_error_factor_worst_hex": worst_factor.hex(),
        "threshold_normalized_finest_error_ratio_worst_hex": worst_ratio.hex(),
    }


def _thin_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["thickness_token"]), []).append(row)
    passed = len(rows) == 12 and tuple(groups) == THIN_THICKNESSES
    fine_ratios: list[float] = []
    phi_by_level: dict[int, list[float]] = {20: [], 40: []}
    worst_factor = 0.0
    for token in THIN_THICKNESSES:
        sequence = sorted(groups[token], key=lambda item: int(item["level"]))
        errors = [float.fromhex(item["response_relative_error_hex"]) for item in sequence]
        factor = errors[1] / max(errors[0], np.finfo(float).tiny)
        worst_factor = max(worst_factor, factor)
        passed = passed and factor <= 1.02 and errors[1] <= 0.02
        fine_ratios.append(float.fromhex(sequence[1]["response_center_hex"]) / float.fromhex(sequence[1]["reference_center_hex"]))
        for item in sequence:
            phi = float.fromhex(item["phi_squared_hex"])
            phi_by_level[int(item["level"])].append(phi)
            passed = passed and 0.0 < phi <= 1.0
    for values in phi_by_level.values():
        passed = passed and all(right < left for left, right in zip(values, values[1:]))
    thin = fine_ratios[2:]
    spread = (max(thin) - min(thin)) / max(abs(sum(thin) / len(thin)), np.finfo(float).tiny)
    passed = passed and spread <= 0.005
    passed = passed and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in rows)
    return {
        "gate_passed": bool(passed),
        "record_count": len(rows),
        "successive_error_factor_worst_hex": worst_factor.hex(),
        "thin_range_response_ratio_spread_hex": spread.hex(),
    }


def repair_funnel_proof() -> dict[str, Any]:
    development_rows = [_record(*spec) for spec in DEVELOPMENT]
    development = _development_gate(development_rows)
    result: dict[str, Any] = {"development": {"diagnostics": development, "records": development_rows}}
    if not development["gate_passed"]:
        return result | {"campaign": {}, "thin_regime": {}}
    development_ids = {row["record_id"] for row in development_rows}
    campaign_rows = list(development_rows)
    campaign_rows.extend(_record(*spec) for spec in DISPERSED_CAMPAIGN if f"N{spec[0]}:{spec[1]}PCT:{spec[2]}:{spec[3]}:t={THICKNESS.hex()}" not in development_ids)
    campaign_rows.extend(_record(*spec) for spec in CHAIN_HOLDOUT)
    campaign_rows.extend(_record(*spec) for spec in ALL_S3_CONTROL)
    campaign_rows.sort(key=lambda row: row["record_id"])
    q4_rows = [_record(level, 0, "dispersed", "slash") for level in LEVELS]
    campaign = _campaign_gate(campaign_rows, q4_rows)
    result["campaign"] = {"diagnostics": campaign, "q4_baseline_records": q4_rows, "records": campaign_rows}
    if not campaign["gate_passed"]:
        return result | {"thin_regime": {}}
    thin_rows: list[dict[str, Any]] = []
    for token in THIN_THICKNESSES:
        thickness = float(token)
        for level in (20, 40):
            row = _record(level, 100, "all_cells", "slash", thickness=thickness)
            triangle = np.asarray(((0.0, 0.0, 0.0), (1.0 / level, 0.0, 0.0), (0.0, 1.0 / level, 0.0)))
            row["phi_squared_hex"] = float(min3_components(triangle, thickness=thickness)["phi_squared"]).hex()
            row["thickness_token"] = token
            thin_rows.append(row)
    thin = _thin_gate(thin_rows)
    result["thin_regime"] = {"diagnostics": thin, "records": thin_rows}
    return result


def produce_proof() -> dict[str, Any]:
    validate_authority()
    local = local_proof()
    base = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "local": local,
        "production_boundary": {
            "anymesh_untouched": True,
            "default_q4_formulation": "e4-pl",
            "default_s3_formulation": "legacy-s3",
            "q4_mechanics_unchanged": True,
        },
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "relaxation_policy": "CBMIN3_EXACTLY_2_UHM_C_S_EXACTLY_ONE_HALF",
        "schema": PROOF_SCHEMA,
        "stage4a_rerun_authorized": False,
    }
    if not local["diagnostics"]["gate_passed"]:
        return base | {"later_stages": "NOT_EXECUTED_LOCAL_GATE_FAILED", "macrocell": {}, "repair_funnel": {}}
    macrocell = macrocell_proof()
    if not macrocell["diagnostics"]["gate_passed"]:
        return base | {"later_stages": "NOT_EXECUTED_MACROCELL_GATE_FAILED", "macrocell": macrocell, "repair_funnel": {}}
    funnel = repair_funnel_proof()
    gates = [
        funnel.get("development", {}).get("diagnostics", {}).get("gate_passed", False),
        funnel.get("campaign", {}).get("diagnostics", {}).get("gate_passed", False),
        funnel.get("thin_regime", {}).get("diagnostics", {}).get("gate_passed", False),
    ]
    return base | {
        "later_stages": "STAGE4A_REAUTHORIZATION_REQUIRED" if all(gates) else "REPAIR_FUNNEL_GATE_FAILED",
        "macrocell": macrocell,
        "repair_funnel": funnel,
    }


def adjudicate(*, identical: bool, report: Mapping[str, Any]) -> str:
    if not identical or not report.get("authority_complete") or not report.get("construction_identity_passed"):
        return "BLOCKED_E4_PL_S3_V5B_PROCESS_OR_EVIDENCE"
    if not report.get("local_operator_passed"):
        return "NO_GO_E4_PL_S3_V5B_RELAXATION_SOURCE_OR_LOCAL_OPERATOR"
    if not report.get("mixed_interface_passed") or not report.get("campaign_passed"):
        return "NO_GO_E4_PL_S3_V5B_MIXED_INTERFACE"
    if not report.get("thin_regime_passed"):
        return "NO_GO_E4_PL_S3_V5B_THIN_REGIME"
    return "PROVISIONAL_GO_E4_PL_S3_V5B_STAGE4A_RERUN"


def _run_child(command: list[str], timeout_seconds: int) -> None:
    v5a.common._run_child(command, timeout_seconds)


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise ScreenError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    checker = REFERENCE / "e4_pl_s3_v5b_relaxed_screen_checker.py"
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V5B_PROCESS_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checks = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION", "sequence": 0}))
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            _run_child([sys.executable, str(Path(__file__).resolve()), "--emit-proof", "--output", str(proof)], remaining)
            commands = [
                [sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)]
                for path in checks
            ]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(_run_child, command, int(max(1, min(timeout_seconds, deadline - time.monotonic()))))
                    for command in commands
                ]
                for future in futures:
                    future.result()
            identical = checks[0].read_bytes() == checks[1].read_bytes()
            report = load_canonical(checks[0])
            terminal = adjudicate(identical=identical, report=report)
            cycles.append({
                "checker_replicas_byte_identical": identical,
                "checker_sha256": sha256_file(checks[0]),
                "cycle": cycle,
                "proof_bytes": proof.stat().st_size,
                "proof_sha256": sha256_file(proof),
                "terminal": terminal,
            })
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE", "sequence": 1}))
        if cycles[0]["proof_sha256"] != cycles[1]["proof_sha256"] or cycles[0]["checker_sha256"] != cycles[1]["checker_sha256"]:
            terminal = "BLOCKED_E4_PL_S3_V5B_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V5B_PROCESS_OR_EVIDENCE"
    aggregate = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "cycles": cycles,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": AGGREGATE_SCHEMA,
        "stage4a_reauthorization_preparation_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V5B_STAGE4A_RERUN",
        "stage4a_rerun_authorized": False,
        "terminal": terminal,
    }
    exclusive_write(root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-proof", action="store_true")
    mode.add_argument("--run-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--wave-timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    if args.emit_proof:
        if args.output is None:
            raise ScreenError("--output is required")
        exclusive_write(args.output, produce_proof())
    else:
        if args.output_root is None:
            raise ScreenError("--output-root is required")
        run_bounded(args.output_root, timeout_seconds=args.timeout_seconds, wave_timeout_seconds=args.wave_timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
