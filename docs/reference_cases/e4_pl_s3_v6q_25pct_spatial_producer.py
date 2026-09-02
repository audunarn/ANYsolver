"""Produce bounded V6Q 25% spatial-response shards from frozen V2D source."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tarfile
from types import ModuleType
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_contract.json"
MANIFEST = REFERENCE / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
ADAPTER = REFERENCE / "e4_pl_s3_v6h_stage4a_adapter.py"
SCHEMA = "anysolver.e4-pl-s3-v6q-25pct-spatial-shard-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
IMPLEMENTATION_ID = "E4_PL_S3_V2D_RECOVERY_CURRENT_EIGEN_GATE_V1"
DIAGONALS = ("slash", "backslash", "alternating")
MASKS = ("dispersed", "chain")
LEVELS = (20, 40, 80)


class V6QProducerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise V6QProducerError(f"nonfinite JSON constant: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6QProducerError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_reject_pairs)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6QProducerError(f"noncanonical JSON: {path}")
    return value, raw


def _binding(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "path": str(path), "sha256": sha256(raw)}


def validate_authority() -> tuple[dict[str, Any], bytes]:
    contract, raw = strict_json(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v6q-25pct-spatial-contract-v1":
        raise V6QProducerError("V6Q contract schema differs")
    if contract.get("activation_authorized") is not False:
        raise V6QProducerError("V6Q cannot authorize activation")
    for item in contract.get("frozen_inputs", []):
        path = Path(str(item["path"]))
        if not path.is_absolute():
            path = ROOT / path
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or sha256(payload) != item["sha256"]:
            raise V6QProducerError(f"frozen input differs: {path}")
    return contract, raw


def _safe_extract(archive: Path, destination: Path, *, support_only: bool) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    with tarfile.open(archive.resolve(), mode="r:") as bundle:
        for member in bundle.getmembers():
            name = member.name.rstrip("/")
            if not name:
                continue
            pure = Path(name.replace("/", os.sep))
            canonical = "/".join(pure.parts)
            folded = canonical.casefold()
            if (
                pure.is_absolute()
                or any(part in {"", ".", ".."} for part in pure.parts)
                or folded in seen
                or not (member.isdir() or member.isfile())
                or (support_only and not (canonical == "src" or canonical.startswith("src/anyfileio")))
            ):
                raise V6QProducerError("unsafe frozen archive member")
            seen.add(folded)
            target = destination.joinpath(*pure.parts).resolve()
            try:
                target.relative_to(destination.resolve())
            except ValueError as exc:
                raise V6QProducerError("archive extraction escapes destination") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            source = bundle.extractfile(member)
            if source is None:
                raise V6QProducerError("archive member is unreadable")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                shutil.copyfileobj(source, stream, length=1 << 20)


def _load_adapter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_s3_v6q_frozen_adapter", ADAPTER)
    if spec is None or spec.loader is None:
        raise V6QProducerError("cannot load frozen V2D adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _records(diagonal: str) -> list[tuple[int, dict[str, Any]]]:
    manifest, _ = strict_json(MANIFEST)
    wanted = {
        (level, mask, diagonal)
        for level in LEVELS
        for mask in MASKS
    }
    made = [
        (index, record)
        for index, record in enumerate(manifest["records"])
        if record["s3_area_fraction_percent"] == 25
        and (record["level"], record["mask"], record["diagonal"]) in wanted
    ]
    if len(made) != 6 or {
        (row["level"], row["mask"], row["diagonal"]) for _index, row in made
    } != wanted:
        raise V6QProducerError("V6Q manifest coverage differs")
    return sorted(made, key=lambda item: (item[1]["level"], item[1]["mask"]))


def _metric_record(base: ModuleType, index: int, record: Mapping[str, Any]) -> dict[str, Any]:
    import numpy as np

    model, kinds, _elements, _counts = base._build_model(
        record, s3_selector=base.SELECTOR
    )
    reference, reference_sha, reference_center = base.mindlin_nodal_reference(
        int(record["level"])
    )
    solver, measured, solution = base._solve_and_measure(model, kinds, reference)
    level = int(record["level"])
    center_node = model.mesh.nodes[base._node_id(level // 2, level // 2, level)]
    center = float(solution[center_node.dofs[2]])
    center_signed = center / reference_center - 1.0
    transverse = solution[2::6]
    transverse_reference = reference[2::6]
    rotations = np.column_stack((solution[3::6], solution[4::6])).reshape(-1)
    rotations_reference = np.column_stack((reference[3::6], reference[4::6])).reshape(-1)
    tiny = np.finfo(np.float64).tiny
    w_error = transverse - transverse_reference
    rotation_error = rotations - rotations_reference
    values = {
        "center_relative_error_hex": abs(center_signed).hex(),
        "center_signed_error_hex": center_signed.hex(),
        "connectivity_sha256": str(record["connectivity_sha256"]),
        "diagonal": str(record["diagonal"]),
        "energy_relative_error_hex": float(measured["energy_relative"]).hex(),
        "level": level,
        "manifest_index": index,
        "mask": str(record["mask"]),
        "record_id": f"N{level}:25PCT:{record['mask']}:{record['diagonal']}",
        "reference_sha256": reference_sha,
        "rotation_relative_l2_error_hex": float(
            np.linalg.norm(rotation_error) / max(np.linalg.norm(rotations_reference), tiny)
        ).hex(),
        "s3_area_fraction_percent": 25,
        "solve_residual_relative_inf_hex": float(solver["residual_relative"]).hex(),
        "w_relative_l2_error_hex": float(
            np.linalg.norm(w_error) / max(np.linalg.norm(transverse_reference), tiny)
        ).hex(),
        "w_relative_linf_error_hex": float(
            np.linalg.norm(w_error, ord=np.inf)
            / max(np.linalg.norm(transverse_reference, ord=np.inf), tiny)
        ).hex(),
    }
    if any(not math.isfinite(float.fromhex(values[key])) for key in values if key.endswith("_hex")):
        raise V6QProducerError("nonfinite spatial metric")
    return values


def _append_progress(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("ab") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def produce(
    diagonal: str,
    source_root: Path,
    candidate_archive: Path,
    support_archive: Path,
    progress: Path,
) -> dict[str, Any]:
    contract, contract_raw = validate_authority()
    if diagonal not in DIAGONALS:
        raise V6QProducerError("unregistered diagonal")
    if (
        candidate_archive.resolve() != Path(contract["candidate"]["archive_path"]).resolve()
        or support_archive.resolve() != Path(contract["support"]["archive_path"]).resolve()
        or sha256(candidate_archive.read_bytes()) != contract["candidate"]["archive_sha256"]
        or sha256(support_archive.read_bytes()) != contract["support"]["archive_sha256"]
    ):
        raise V6QProducerError("worker archive authority differs")
    if source_root.exists() or progress.exists():
        raise V6QProducerError("worker source and progress paths must be exclusive")
    progress.parent.mkdir(parents=True, exist_ok=True)
    progress.touch(exist_ok=False)
    _append_progress(progress, {"completed": 0, "phase": "INITIALIZATION", "total": 6})
    candidate_root = source_root / "candidate"
    support_root = source_root / "support"
    source_root.mkdir(parents=True, exist_ok=False)
    _safe_extract(candidate_archive, candidate_root, support_only=False)
    _safe_extract(support_archive, support_root, support_only=True)
    sys.path.insert(0, str((support_root / "src").resolve()))
    adapter = _load_adapter()
    base = adapter.configure()
    base.validate_extracted_candidate_source(
        candidate_root, candidate_archive, contract["candidate"]["archive_sha256"]
    )
    base.activate_frozen_candidate_source(candidate_root)
    _append_progress(progress, {"completed": 0, "phase": "AUTHORITY_COMPLETE", "total": 6})
    records: list[dict[str, Any]] = []
    for sequence, (index, record) in enumerate(_records(diagonal), start=1):
        made = _metric_record(base, index, record)
        records.append(made)
        _append_progress(
            progress,
            {"completed": sequence, "phase": "CASE_OR_REFINEMENT_OR_STATION", "record_id": made["record_id"], "total": 6},
        )
    records.sort(key=lambda item: item["record_id"])
    _append_progress(progress, {"completed": 6, "phase": "STAGING", "total": 6})
    result = {
        "activation_authorized": False,
        "candidate_commit": contract["candidate"]["commit"],
        "candidate_formulation_id": FORMULATION_ID,
        "candidate_implementation_id": IMPLEMENTATION_ID,
        "candidate_tree": contract["candidate"]["tree"],
        "center_metric_classifying": False,
        "contract_sha256": sha256(contract_raw),
        "diagonal": diagonal,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "record_count": 6,
        "record_ids_sha256": sha256(canonical_bytes([row["record_id"] for row in records])),
        "records": records,
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "schema": SCHEMA,
    }
    _append_progress(progress, {"completed": 6, "phase": "VALIDATION", "total": 6})
    _append_progress(progress, {"completed": 6, "phase": "COMPLETION", "total": 6})
    return result


def _exclusive(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-spatial-shard", action="store_true", required=True)
    parser.add_argument("--diagonal", choices=DIAGONALS, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--support-archive", type=Path, required=True)
    parser.add_argument("--progress", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    _exclusive(
        args.output,
        produce(args.diagonal, args.source_root, args.candidate_archive, args.support_archive, args.progress),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
