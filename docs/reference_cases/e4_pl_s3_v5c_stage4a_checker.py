"""Independently reconstruct and check one V5C Stage 4A diagonal shard."""

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


CONTRACT = REFERENCE / "e4_pl_s3_v5c_stage4a_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5c-stage4a-shard-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5c-stage4a-shard-check-v1"
DIAGONALS = ("slash", "backslash", "alternating")
LEVELS = (20, 40, 80)
MASKS = ("dispersed", "chain")
FRACTIONS = (1, 5, 10, 25)
PRESSURE = 1000.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
Z_ONE_SIDED_95 = 1.6448536269514722
THRESHOLDS = {
    "energy_slope_lower_95": 0.90,
    "ratio_25": 1.50,
    "ratio_through_10": 1.25,
    "record_identity": 3.0e-12,
    "residual": 1.0e-8,
    "response_slope": 1.80,
    "slope_deficit": 0.15,
    "successive": 1.02,
}


class CheckerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Mapping[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_reject_pairs)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise CheckerError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def _solve(matrix: Any, right: np.ndarray) -> np.ndarray:
    from scipy import sparse
    from scipy.sparse.linalg import splu

    diagonal = np.asarray(matrix.diagonal(), dtype=np.float64)
    root = np.sqrt(np.maximum(np.abs(diagonal), np.finfo(np.float64).tiny))
    inverse = 1.0 / root
    scaling = sparse.diags(inverse, format="csc")
    lu = splu((scaling @ matrix @ scaling).tocsc(), permc_spec="COLAMD")

    def solve(rhs: np.ndarray) -> np.ndarray:
        return inverse * lu.solve(inverse * np.asarray(rhs, dtype=np.float64))

    answer = solve(right)
    for _pass in range(2):
        answer = answer + solve(right - matrix @ answer)
    return answer


def _cell_triangles(i: int, j: int, level: int, diagonal: str) -> tuple[tuple[int, int, int], ...]:
    lower_left = j * (level + 1) + i
    lower_right = lower_left + 1
    upper_left = lower_left + level + 1
    upper_right = lower_left + level + 2
    chosen = diagonal
    if diagonal == "alternating":
        chosen = "backslash" if (i + j) % 2 == 0 else "slash"
    if chosen == "slash":
        return (lower_left, lower_right, upper_left), (lower_right, upper_right, upper_left)
    if chosen == "backslash":
        return (lower_left, lower_right, upper_right), (lower_left, upper_right, upper_left)
    raise CheckerError("unknown diagonal")


def _record(level: int, fraction: int, mask: str, diagonal: str) -> dict[str, Any]:
    from scipy import sparse

    if fraction == 0:
        base: tuple[tuple[int, int], ...] = ()
        mask = "dispersed"
    elif mask in MASKS and fraction in FRACTIONS:
        base = mesh_manifest.selected_base_cells(mask, fraction * 4)
    else:
        raise CheckerError("unregistered mask or fraction")
    split = mesh_manifest.expanded_split_cells(base, level)
    count = (level + 1) ** 2
    coordinates = np.asarray(tuple((i / level, j / level, 0.0) for j in range(level + 1) for i in range(level + 1)))
    matrix_rows: list[int] = []
    matrix_columns: list[int] = []
    matrix_values: list[float] = []
    pl_values: list[float] = []
    load = np.zeros(6 * count)
    h = 1.0 / level
    q4_coordinates = np.asarray(((0.0, 0.0, 0.0), (h, 0.0, 0.0), (h, h, 0.0), (0.0, h, 0.0)))
    q4 = v5b_check.v5a_check.independent_q4._q4(q4_coordinates, NORMAL)
    q4_load = np.zeros(24)
    q4_load[2::6] = PRESSURE * h * h / 4.0
    s3_cache: dict[tuple[int, ...], dict[str, Any]] = {}
    for j in range(level):
        for i in range(level):
            entries: list[tuple[tuple[int, ...], Mapping[str, Any], np.ndarray]] = []
            if (i, j) in split:
                for triangle in _cell_triangles(i, j, level, diagonal):
                    signature = tuple(node - triangle[0] for node in triangle)
                    made = s3_cache.get(signature)
                    if made is None:
                        origin = coordinates[triangle[0]]
                        made = v5b_check.reconstruct(coordinates[np.asarray(triangle)] - origin)
                        s3_cache[signature] = made
                    entries.append((triangle, made, np.asarray(made["pressure_load"])))
            else:
                nodes = (j * (level + 1) + i, j * (level + 1) + i + 1, (j + 1) * (level + 1) + i + 1, (j + 1) * (level + 1) + i)
                entries.append((nodes, q4, q4_load))
            for nodes, made, local_load in entries:
                dofs = np.asarray([6 * node + dof for node in nodes for dof in range(6)], dtype=np.intp)
                rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
                matrix_rows.extend(rr.reshape(-1).tolist())
                matrix_columns.extend(cc.reshape(-1).tolist())
                matrix_values.extend(np.asarray(made["total"]).reshape(-1).tolist())
                pl_values.extend(np.asarray(made.get("pl", np.zeros_like(made["total"]))).reshape(-1).tolist())
                np.add.at(load, dofs, local_load)
    size = 6 * count
    stiffness = sparse.coo_matrix((matrix_values, (matrix_rows, matrix_columns)), shape=(size, size)).tocsr()
    pl_matrix = sparse.coo_matrix((pl_values, (matrix_rows, matrix_columns)), shape=(size, size)).tocsr()
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
    displacement = np.zeros(size)
    displacement[free] = _solve(stiffness[free][:, free], load[free])
    residual = float(np.linalg.norm((stiffness @ displacement - load)[free], ord=np.inf) / max(np.linalg.norm(load[free], ord=np.inf), 1.0))
    reference_document, reference_center = reference_checker.reference_vector_document(level)
    reference = np.asarray(reference_document["values"], dtype=np.float64)
    reference_sha = sha256_bytes(reference_checker.canonical_bytes(reference_document))
    center_node = (level // 2) * (level + 1) + level // 2
    center = float(displacement[6 * center_node + 2])
    response_error = abs(center / reference_center - 1.0)
    solution_total = float(displacement @ (stiffness @ displacement))
    reference_total = float(reference @ (stiffness @ reference))
    cross = float(displacement @ (stiffness @ reference))
    raw_error = solution_total + reference_total - 2.0 * cross
    floor = 256.0 * np.finfo(np.float64).eps * max(abs(solution_total), abs(reference_total), abs(cross), 1.0)
    if raw_error < -floor:
        raise CheckerError("independent energy-error form is negative")
    energy_relative = math.sqrt(max(raw_error, 0.0) / max(reference_total, np.finfo(np.float64).tiny))
    pl_energy = float(displacement @ (pl_matrix @ displacement))
    return {
        "connectivity_sha256": mesh_manifest.connectivity_sha256(level, split, diagonal),
        "diagonal": diagonal,
        "energy_relative_hex": energy_relative.hex(),
        "level": level,
        "mask": mask,
        "pl_participation_hex": (abs(pl_energy) / max(abs(solution_total), 1.0)).hex(),
        "record_id": f"N{level}:{fraction}PCT:{mask}:{diagonal}",
        "reference_center_hex": float(reference_center).hex(),
        "reference_sha256": reference_sha,
        "response_center_hex": center.hex(),
        "response_relative_error_hex": response_error.hex(),
        "s3_area_fraction_percent": fraction,
        "solve_residual_relative_inf_hex": residual.hex(),
    }


def _record_identity(claim: Mapping[str, Any], checked: Mapping[str, Any]) -> float:
    exact = ("connectivity_sha256", "diagonal", "level", "mask", "record_id", "reference_sha256", "s3_area_fraction_percent")
    if any(claim.get(key) != checked.get(key) for key in exact):
        raise CheckerError("record identity mismatch")
    worst = 0.0
    for key in ("energy_relative_hex", "pl_participation_hex", "reference_center_hex", "response_center_hex", "response_relative_error_hex"):
        left, right = float.fromhex(str(claim[key])), float.fromhex(str(checked[key]))
        worst = max(worst, abs(left - right) / max(abs(right), 1.0))
    if max(float.fromhex(str(claim["solve_residual_relative_inf_hex"])), float.fromhex(str(checked["solve_residual_relative_inf_hex"]))) > THRESHOLDS["residual"]:
        raise CheckerError("solve residual exceeds frozen bound")
    return worst


def _positive_log_slope(values: Sequence[float]) -> tuple[float, float]:
    if len(values) != 3 or any(value <= 0.0 for value in values):
        raise CheckerError("slope inputs must be positive")
    x = [math.log(float(level)) for level in LEVELS]
    y = [-math.log(float(value)) for value in values]
    mx, my = sum(x) / 3.0, sum(y) / 3.0
    sxx = sum((value - mx) ** 2 for value in x)
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    intercept = my - slope * mx
    residual = sum((b - (intercept + slope * a)) ** 2 for a, b in zip(x, y))
    error = math.sqrt(max(residual, 0.0) / sxx)
    return slope, slope - Z_ONE_SIDED_95 * error


def _sequence(rows: Sequence[Mapping[str, Any]], baseline: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: int(row["level"]))
    base = sorted(baseline, key=lambda row: int(row["level"]))
    response = [float.fromhex(str(row["response_relative_error_hex"])) for row in ordered]
    energy = [float.fromhex(str(row["energy_relative_hex"])) for row in ordered]
    q4 = [float.fromhex(str(row["response_relative_error_hex"])) for row in base]
    response_slope, _ = _positive_log_slope(response)
    q4_slope, _ = _positive_log_slope(q4)
    energy_slope, energy_lower = _positive_log_slope(energy)
    ratio = response[-1] / q4[-1]
    fraction = int(ordered[0]["s3_area_fraction_percent"])
    failures: list[str] = []
    if response_slope < THRESHOLDS["response_slope"]:
        failures.append("RESPONSE_SLOPE")
    if q4_slope - response_slope > THRESHOLDS["slope_deficit"]:
        failures.append("RESPONSE_SLOPE_DEFICIT")
    if energy_lower < THRESHOLDS["energy_slope_lower_95"]:
        failures.append("ENERGY_SLOPE_LOWER_95")
    if any(fine > THRESHOLDS["successive"] * coarse for coarse, fine in zip(response, response[1:])):
        failures.append("SUCCESSIVE_RESPONSE_ERROR")
    limit = THRESHOLDS["ratio_25"] if fraction == 25 else THRESHOLDS["ratio_through_10"]
    if ratio > limit:
        failures.append("FINEST_RESPONSE_ERROR_RATIO")
    return {
        "all_q4_response_slope_hex": q4_slope.hex(),
        "energy_norm_slope_hex": energy_slope.hex(),
        "energy_norm_slope_lower_95_hex": energy_lower.hex(),
        "failed_subgates": failures,
        "finest_error_ratio_to_all_q4_hex": ratio.hex(),
        "fraction_percent": fraction,
        "mask": str(ordered[0]["mask"]),
        "record_ids": [str(row["record_id"]) for row in ordered],
        "response_error_slope_hex": response_slope.hex(),
        "slope_deficit_from_all_q4_hex": (q4_slope - response_slope).hex(),
    }


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise CheckerError("proof identity mismatch")
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise CheckerError("proof contract mismatch")
    diagonal = str(proof.get("diagonal"))
    if diagonal not in DIAGONALS or proof.get("record_count") != 27:
        raise CheckerError("proof coverage mismatch")
    claims = {str(row["record_id"]): row for row in proof.get("records", [])}
    specs = [(level, 0, "dispersed", diagonal) for level in LEVELS]
    specs += [(level, fraction, mask, diagonal) for level in LEVELS for mask in MASKS for fraction in FRACTIONS]
    checked = [_record(*spec) for spec in specs]
    if len(claims) != 27 or set(claims) != {row["record_id"] for row in checked}:
        raise CheckerError("proof record set mismatch")
    identity = max(_record_identity(claims[row["record_id"]], row) for row in checked)
    baseline = [row for row in checked if row["s3_area_fraction_percent"] == 0]
    sequences = []
    for mask in MASKS:
        for fraction in FRACTIONS:
            rows = [row for row in checked if row["mask"] == mask and row["s3_area_fraction_percent"] == fraction]
            sequences.append(_sequence(rows, baseline))
    failures = [f"{diagonal}:{row['mask']}:{row['fraction_percent']}:{failure}" for row in sequences for failure in row["failed_subgates"]]
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "diagonal": diagonal,
        "formal_failure_count": len(failures),
        "formal_failures": failures,
        "independent_record_count": 27,
        "record_identity_passed": identity <= THRESHOLDS["record_identity"],
        "record_identity_worst_relative_inf_hex": identity.hex(),
        "schema": CHECK_SCHEMA,
        "sequence_count": 8,
        "sequence_results": sequences,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-shard", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_canonical(args.proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
