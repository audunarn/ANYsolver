"""Produce one bounded diagonal shard for the V5C Stage 4A reauthorization."""

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
import e4_pl_s3_v5b_relaxed_screen_producer as v5b


CONTRACT = REFERENCE / "e4_pl_s3_v5c_stage4a_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1"
SCHEMA = "anysolver.e4-pl-s3-v5c-stage4a-shard-proof-v1"
DIAGONALS = ("slash", "backslash", "alternating")
LEVELS = (20, 40, 80)
MASKS = ("dispersed", "chain")
FRACTIONS = (1, 5, 10, 25)
THICKNESS = 0.01
PRESSURE = 1000.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)


class Stage4AError(RuntimeError):
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
        raise Stage4AError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def validate_authority() -> Mapping[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5c-stage4a-contract-v1":
        raise Stage4AError("unexpected V5C contract schema")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / str(binding["path"])
        raw = path.read_bytes()
        if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
            raise Stage4AError(f"frozen input mismatch: {path}")
    if contract.get("production_boundary") != {
        "activation_authorized": False,
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise Stage4AError("production boundary mismatch")
    return contract


def _solve(matrix: Any, right: np.ndarray) -> np.ndarray:
    from scipy import sparse
    from scipy.sparse.linalg import splu

    diagonal = np.asarray(matrix.diagonal(), dtype=np.float64)
    scale = np.sqrt(np.maximum(np.abs(diagonal), np.finfo(np.float64).tiny))
    inverse = 1.0 / scale
    d = sparse.diags(inverse, format="csc")
    factor = splu((d @ matrix @ d).tocsc(), permc_spec="COLAMD")

    def solve(rhs: np.ndarray) -> np.ndarray:
        return inverse * factor.solve(inverse * np.asarray(rhs, dtype=np.float64))

    solution = solve(right)
    for _pass in range(2):
        solution = solution + solve(right - matrix @ solution)
    return solution


def _record(level: int, fraction: int, mask: str, diagonal: str) -> dict[str, Any]:
    from scipy import sparse
    from e4_pl_s3_v2_flat_funnel_producer import mindlin_nodal_reference

    if diagonal not in DIAGONALS or level not in LEVELS:
        raise Stage4AError("unregistered diagonal or level")
    if fraction == 0:
        base: tuple[tuple[int, int], ...] = ()
        mask = "dispersed"
    elif mask in MASKS and fraction in FRACTIONS:
        base = mesh_manifest.selected_base_cells(mask, fraction * 4)
    else:
        raise Stage4AError("unregistered mask or fraction")
    split = mesh_manifest.expanded_split_cells(base, level)
    count = (level + 1) ** 2
    coordinates = np.asarray(
        tuple((i / level, j / level, 0.0) for j in range(level + 1) for i in range(level + 1)),
        dtype=np.float64,
    )
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    pl_values: list[float] = []
    load = np.zeros(6 * count, dtype=np.float64)
    h = 1.0 / level
    q4_coordinates = np.asarray(((0.0, 0.0, 0.0), (h, 0.0, 0.0), (h, h, 0.0), (0.0, h, 0.0)))
    q4 = v5b.v5a.q4_source._qualified_q4_components(q4_coordinates, NORMAL)
    q4_load = np.zeros(24)
    q4_load[2::6] = PRESSURE * h * h / 4.0
    s3_cache: dict[tuple[int, ...], dict[str, Any]] = {}
    for j in range(level):
        for i in range(level):
            entries: list[tuple[tuple[int, ...], Mapping[str, Any], np.ndarray]] = []
            if (i, j) in split:
                for triangle in v5b._cell_triangles(i, j, level, diagonal):
                    signature = tuple(node - triangle[0] for node in triangle)
                    made = s3_cache.get(signature)
                    if made is None:
                        origin = coordinates[triangle[0]]
                        made = v5b.min3_components(coordinates[np.asarray(triangle)] - origin)
                        s3_cache[signature] = made
                    entries.append((triangle, made, np.asarray(made["pressure_load"])))
            else:
                nodes = (
                    j * (level + 1) + i,
                    j * (level + 1) + i + 1,
                    (j + 1) * (level + 1) + i + 1,
                    (j + 1) * (level + 1) + i,
                )
                entries.append((nodes, q4, q4_load))
            for nodes, made, local_load in entries:
                dofs = np.asarray([6 * node + dof for node in nodes for dof in range(6)], dtype=np.intp)
                rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
                rows.extend(rr.reshape(-1).tolist())
                columns.extend(cc.reshape(-1).tolist())
                values.extend(np.asarray(made["total"]).reshape(-1).tolist())
                pl = np.asarray(made.get("pl", np.zeros_like(made["total"])))
                pl_values.extend(pl.reshape(-1).tolist())
                np.add.at(load, dofs, local_load)
    shape = (6 * count, 6 * count)
    stiffness = sparse.coo_matrix((values, (rows, columns)), shape=shape).tocsr()
    pl_matrix = sparse.coo_matrix((pl_values, (rows, columns)), shape=shape).tocsr()
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
    free = np.asarray([index for index in range(shape[0]) if index not in fixed], dtype=np.intp)
    displacement = np.zeros(shape[0], dtype=np.float64)
    free_matrix = stiffness[free][:, free]
    displacement[free] = _solve(free_matrix, load[free])
    residual = float(
        np.linalg.norm((stiffness @ displacement - load)[free], ord=np.inf)
        / max(np.linalg.norm(load[free], ord=np.inf), 1.0)
    )
    reference, reference_sha, reference_center = mindlin_nodal_reference(level)
    center_node = (level // 2) * (level + 1) + level // 2
    center = float(displacement[6 * center_node + 2])
    response_error = abs(center / reference_center - 1.0)
    solution_total = float(displacement @ (stiffness @ displacement))
    reference_total = float(reference @ (stiffness @ reference))
    cross = float(displacement @ (stiffness @ reference))
    raw_error = solution_total + reference_total - 2.0 * cross
    roundoff = 256.0 * np.finfo(np.float64).eps * max(abs(solution_total), abs(reference_total), abs(cross), 1.0)
    if raw_error < -roundoff:
        raise Stage4AError("assembled energy-error form is negative")
    energy_relative = math.sqrt(max(raw_error, 0.0) / max(reference_total, np.finfo(np.float64).tiny))
    pl_energy = float(displacement @ (pl_matrix @ displacement))
    record_id = f"N{level}:{fraction}PCT:{mask}:{diagonal}"
    return {
        "connectivity_sha256": mesh_manifest.connectivity_sha256(level, split, diagonal),
        "diagonal": diagonal,
        "energy_relative_hex": energy_relative.hex(),
        "level": level,
        "mask": mask,
        "pl_participation_hex": (abs(pl_energy) / max(abs(solution_total), 1.0)).hex(),
        "record_id": record_id,
        "reference_center_hex": float(reference_center).hex(),
        "reference_sha256": reference_sha,
        "response_center_hex": center.hex(),
        "response_relative_error_hex": response_error.hex(),
        "s3_area_fraction_percent": fraction,
        "solve_residual_relative_inf_hex": residual.hex(),
    }


def _specs(diagonal: str) -> list[tuple[int, int, str, str]]:
    if diagonal not in DIAGONALS:
        raise Stage4AError("unregistered diagonal")
    made: list[tuple[int, int, str, str]] = []
    for level in LEVELS:
        made.append((level, 0, "dispersed", diagonal))
        made.extend((level, fraction, mask, diagonal) for mask in MASKS for fraction in FRACTIONS)
    return made


def produce_shard(diagonal: str, progress: Path | None = None) -> dict[str, Any]:
    validate_authority()
    if progress is not None:
        progress.parent.mkdir(parents=True, exist_ok=True)
        progress.touch(exist_ok=False)
    records: list[dict[str, Any]] = []
    for sequence, spec in enumerate(_specs(diagonal), start=1):
        record = _record(*spec)
        records.append(record)
        if progress is not None:
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"record_id": record["record_id"], "sequence": sequence}))
                stream.flush()
                os.fsync(stream.fileno())
    records.sort(key=lambda row: row["record_id"])
    record_ids = [str(row["record_id"]) for row in records]
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "diagonal": diagonal,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "record_count": 27,
        "record_ids_sha256": sha256_bytes(canonical_bytes(record_ids)),
        "records": records,
        "schema": SCHEMA,
        "stage4b_preparation_authorized": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-shard", action="store_true", required=True)
    parser.add_argument("--diagonal", choices=DIAGONALS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path)
    args = parser.parse_args(argv)
    exclusive_write(args.output, produce_shard(args.diagonal, args.progress))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
