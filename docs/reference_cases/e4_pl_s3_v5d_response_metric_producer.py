"""Produce V5D spatial-response diagnostic shards."""

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
import e4_pl_s3_v5c_stage4a_producer as v5c


CONTRACT = REFERENCE / "e4_pl_s3_v5d_response_metric_contract.json"
FORMULATION_ID = v5c.FORMULATION_ID
SCHEMA = "anysolver.e4-pl-s3-v5d-response-metric-shard-v1"
DIAGONALS = v5c.DIAGONALS
LEVELS = v5c.LEVELS
MASKS = v5c.MASKS
FRACTIONS = (10, 25)
NORMAL = v5c.NORMAL
PRESSURE = v5c.PRESSURE


class DiagnosisError(RuntimeError):
    pass


canonical_bytes = v5c.canonical_bytes
sha256_bytes = v5c.sha256_bytes
sha256_file = v5c.sha256_file
exclusive_write = v5c.exclusive_write


def _load_contract() -> Mapping[str, Any]:
    raw = CONTRACT.read_bytes()
    value = json.loads(raw)
    if raw != canonical_bytes(value) or value.get("schema") != "anysolver.e4-pl-s3-v5d-response-metric-contract-v1":
        raise DiagnosisError("invalid V5D contract")
    for binding in value["frozen_inputs"]:
        payload = (ROOT / binding["path"]).read_bytes()
        if len(payload) != binding["bytes"] or sha256_bytes(payload) != binding["sha256"]:
            raise DiagnosisError(f"frozen input mismatch: {binding['path']}")
    return value


def _state_record(level: int, fraction: int, mask: str, diagonal: str) -> dict[str, Any]:
    from scipy import sparse
    from e4_pl_s3_v2_flat_funnel_producer import mindlin_nodal_reference

    if fraction == 0:
        base: tuple[tuple[int, int], ...] = ()
        mask = "dispersed"
    elif fraction in FRACTIONS and mask in MASKS:
        base = mesh_manifest.selected_base_cells(mask, fraction * 4)
    else:
        raise DiagnosisError("unregistered diagnosis record")
    split = mesh_manifest.expanded_split_cells(base, level)
    count = (level + 1) ** 2
    coordinates = np.asarray(tuple((i / level, j / level, 0.0) for j in range(level + 1) for i in range(level + 1)))
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    load = np.zeros(6 * count)
    h = 1.0 / level
    q4_coordinates = np.asarray(((0.0, 0.0, 0.0), (h, 0.0, 0.0), (h, h, 0.0), (0.0, h, 0.0)))
    q4 = v5b.v5a.q4_source._qualified_q4_components(q4_coordinates, NORMAL)
    q4_load = np.zeros(24)
    q4_load[2::6] = PRESSURE * h * h / 4.0
    s3_cache: dict[tuple[int, ...], Mapping[str, Any]] = {}
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
                nodes = (j * (level + 1) + i, j * (level + 1) + i + 1, (j + 1) * (level + 1) + i + 1, (j + 1) * (level + 1) + i)
                entries.append((nodes, q4, q4_load))
            for nodes, made, local_load in entries:
                dofs = np.asarray([6 * node + dof for node in nodes for dof in range(6)], dtype=np.intp)
                rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
                rows.extend(rr.reshape(-1).tolist())
                columns.extend(cc.reshape(-1).tolist())
                values.extend(np.asarray(made["total"]).reshape(-1).tolist())
                np.add.at(load, dofs, local_load)
    size = 6 * count
    stiffness = sparse.coo_matrix((values, (rows, columns)), shape=(size, size)).tocsr()
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
    solution[free] = v5c._solve(stiffness[free][:, free], load[free])
    residual = float(np.linalg.norm((stiffness @ solution - load)[free], ord=np.inf) / max(np.linalg.norm(load[free], ord=np.inf), 1.0))
    reference, reference_sha, reference_center = mindlin_nodal_reference(level)
    center_node = (level // 2) * (level + 1) + level // 2
    center = float(solution[6 * center_node + 2])
    center_signed = center / reference_center - 1.0
    w, w_reference = solution[2::6], reference[2::6]
    rotations = np.column_stack((solution[3::6], solution[4::6])).reshape(-1)
    rotations_reference = np.column_stack((reference[3::6], reference[4::6])).reshape(-1)
    w_error = w - w_reference
    rotation_error = rotations - rotations_reference
    w_l2 = float(np.linalg.norm(w_error) / max(np.linalg.norm(w_reference), np.finfo(np.float64).tiny))
    w_linf = float(np.linalg.norm(w_error, ord=np.inf) / max(np.linalg.norm(w_reference, ord=np.inf), np.finfo(np.float64).tiny))
    rotation_l2 = float(np.linalg.norm(rotation_error) / max(np.linalg.norm(rotations_reference), np.finfo(np.float64).tiny))
    solution_total = float(solution @ (stiffness @ solution))
    reference_total = float(reference @ (stiffness @ reference))
    cross = float(solution @ (stiffness @ reference))
    raw_energy_error = solution_total + reference_total - 2.0 * cross
    tolerance = 256.0 * np.finfo(np.float64).eps * max(abs(solution_total), abs(reference_total), abs(cross), 1.0)
    if raw_energy_error < -tolerance:
        raise DiagnosisError("negative diagnostic energy-error form")
    energy = math.sqrt(max(raw_energy_error, 0.0) / max(reference_total, np.finfo(np.float64).tiny))
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


def _specs(diagonal: str) -> list[tuple[int, int, str, str]]:
    return [
        spec
        for level in LEVELS
        for spec in (
            (level, 0, "dispersed", diagonal),
            *((level, fraction, mask, diagonal) for mask in MASKS for fraction in FRACTIONS),
        )
    ]


def produce(diagonal: str, progress: Path | None = None) -> dict[str, Any]:
    _load_contract()
    if diagonal not in DIAGONALS:
        raise DiagnosisError("unregistered diagonal")
    if progress is not None:
        progress.parent.mkdir(parents=True, exist_ok=True)
        progress.touch(exist_ok=False)
    records = []
    for sequence, spec in enumerate(_specs(diagonal), start=1):
        row = _state_record(*spec)
        records.append(row)
        if progress is not None:
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"record_id": row["record_id"], "sequence": sequence}))
    records.sort(key=lambda row: row["record_id"])
    ids = [row["record_id"] for row in records]
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "diagonal": diagonal,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "record_count": 15,
        "record_ids_sha256": sha256_bytes(canonical_bytes(ids)),
        "records": records,
        "schema": SCHEMA,
        "v5c_reclassified": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-diagnostic-shard", action="store_true", required=True)
    parser.add_argument("--diagonal", choices=DIAGONALS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path)
    args = parser.parse_args(argv)
    exclusive_write(args.output, produce(args.diagonal, args.progress))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
