"""Evidence-only V6P completion of the 81-record Stage 4A campaign."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
from types import ModuleType
from typing import Any, Mapping, Sequence


REFERENCE = Path(__file__).resolve().parent
ROOT = REFERENCE.parents[1]
CONTRACT = REFERENCE / "e4_pl_s3_v6p_stage4a_completion_contract.json"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6p_stage4a_execution_authorization.json"
COORDINATOR = REFERENCE / "e4_pl_s3_v2_stage4a_coordinator.py"
CHECKER = REFERENCE / "e4_pl_s3_v2_flat_funnel_checker.py"
V6N_RESULT = REFERENCE / "e4_pl_s3_v6n_lease_optimization_result.json"
V6M_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6m-validator-safe"
)
V6O_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6o-missing-leaves-fb7d1fe"
)
V6M_GRAPH = V6M_ROOT / "execution-graph.json"
V6M_AUTHORIZATION = V6M_ROOT / "authorization-replica.json"
V6M_LEDGER = V6M_ROOT / "ledger-terminal.md"
V6M_ARCHIVE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6k-2d91bba2\candidate-source.tar"
)
V6O_GRAPH = V6O_ROOT / "execution-graph.json"
V6O_AUTHORIZATION = REFERENCE / "e4_pl_s3_v6o_stage4a_execution_authorization.json"
V6O_LEDGER = V6O_ROOT / "ledger-terminal.md"
V6O_ARCHIVE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6n-lease-optimization-c1e2ad9\candidate-source.tar"
)
PLAN_SHA256 = "03095DB243064F7D70F9EA0BF4CCCCEF36DF983D441B5A3B09E8D6568412C9E0"
UNION_SCHEMA = "anysolver.e4-pl-s3-v6p-stage4a-completion-union-v1"
RESULT_SCHEMA = "anysolver.e4-pl-s3-v6p-stage4a-completion-result-v1"
BLOCKED = "BLOCKED_E4_PL_S3_V6P_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V2D_STAGE4A_MIXED_FLEXURAL_CONVERGENCE"
PASS = "PROVISIONAL_GO_E4_PL_S3_V2D_STAGE4B_EXTENSION"


class V6PError(RuntimeError):
    """Raised when the evidence-only completion graph differs."""


def _reject_constant(value: str) -> None:
    raise V6PError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6PError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise V6PError("nonfinite JSON number is forbidden")
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise V6PError("JSON keys must be strings")
                visit(child)
            return
        raise V6PError(f"unsupported JSON type: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.resolve().read_bytes()
    value = json.loads(
        raw.decode(), object_pairs_hook=_reject_pairs, parse_constant=_reject_constant
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6PError(f"noncanonical JSON: {path}")
    return value, raw


def _binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise V6PError(f"required regular file is absent: {resolved}")
    raw = resolved.read_bytes()
    return {"byte_count": len(raw), "path": str(resolved), "sha256": sha256(raw)}


def _require_binding(path: Path, byte_count: int, digest: str) -> bytes:
    binding = _binding(path)
    if binding["byte_count"] != byte_count or binding["sha256"] != digest:
        raise V6PError(f"frozen input differs: {path}")
    return path.resolve().read_bytes()


def _load_module(path: Path, name: str, digest: str) -> ModuleType:
    raw = path.read_bytes()
    if sha256(raw) != digest:
        raise V6PError(f"frozen program differs: {path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6PError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _ledger_has_pass(ledger_raw: bytes, request_id: str) -> bool:
    lines = ledger_raw.decode("utf-8").splitlines()
    matches = [
        line
        for line in lines
        if f"| {request_id} | COMPLETED_PASS |" in line
    ]
    return len(matches) == 1


def _plan_members(coordinator: ModuleType, plan: Mapping[str, Any], plan_raw: bytes):
    return {
        str(member["record_id"]): member
        for shard in coordinator._stage4a_plan_shards(plan, plan_raw)
        for member in shard["records"]
    }


def _validate_source(
    *,
    label: str,
    root: Path,
    graph_path: Path,
    graph_bytes: int,
    graph_sha256: str,
    authorization_path: Path,
    authorization_bytes: int,
    authorization_sha256: str,
    ledger_path: Path,
    ledger_bytes: int,
    ledger_sha256: str,
    wave_count: int,
    coordinator: ModuleType,
    plan: Mapping[str, Any],
    plan_raw: bytes,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    graph_raw = _require_binding(graph_path, graph_bytes, graph_sha256)
    graph = json.loads(graph_raw)
    auth_raw = _require_binding(
        authorization_path, authorization_bytes, authorization_sha256
    )
    authorization = json.loads(auth_raw)
    ledger_raw = _require_binding(ledger_path, ledger_bytes, ledger_sha256)
    waves = graph.get("waves")
    requests = authorization.get("requests")
    catalog = graph.get("leaf_catalog")
    if (
        not isinstance(waves, list)
        or len(waves) < wave_count
        or not isinstance(requests, list)
        or len(requests) < wave_count
        or not isinstance(catalog, list)
    ):
        raise V6PError(f"{label} source authority coverage differs")
    entries = {
        str(entry["assignment"]["record_id"]): entry for entry in catalog
    }
    members = _plan_members(coordinator, plan, plan_raw)
    made: dict[str, dict[str, Any]] = {}
    wave_bindings: list[dict[str, Any]] = []
    for wave_index in range(wave_count):
        wave = waves[wave_index]
        request = requests[wave_index]["request"]
        request_id = str(request["request_id"])
        if not _ledger_has_pass(ledger_raw, request_id):
            raise V6PError(f"{label} wave {wave_index + 1} lacks one PASS ledger row")
        wave_root = root / f"wave-{wave_index + 1:02d}"
        plan_path = wave_root / "stage4a-plan.json"
        bounded_path = wave_root / "bounded-result.json"
        wrapper_path = wave_root / "wave-wrapper-result.json"
        if sha256(plan_path.read_bytes()) != PLAN_SHA256:
            raise V6PError(f"{label} wave plan differs")
        bounded, bounded_raw = strict_json(bounded_path)
        wrapper, wrapper_raw = strict_json(wrapper_path)
        workers = bounded.get("workers")
        expected_workers = wave.get("workers")
        if (
            bounded.get("terminal") != "COMPLETED"
            or wrapper.get("terminal") != "COMPLETED"
            or wrapper.get("wave_index") != wave_index
            or wrapper.get("graph_sha256") != graph_sha256
            or wrapper.get("bounded_result_sha256") != sha256(bounded_raw)
            or not isinstance(workers, list)
            or len(workers) != 3
            or not isinstance(expected_workers, list)
            or len(expected_workers) != 3
        ):
            raise V6PError(f"{label} wave {wave_index + 1} terminal differs")
        for worker_index, (worker, expected) in enumerate(
            zip(workers, expected_workers), start=1
        ):
            proof_path = wave_root / f"worker-{worker_index}" / "scientific.json"
            proof, proof_raw = strict_json(proof_path)
            record_ids = proof.get("record_ids")
            if not isinstance(record_ids, list) or len(record_ids) != 1:
                raise V6PError(f"{label} leaf record count differs")
            record_id = str(record_ids[0])
            entry = entries.get(record_id)
            member = members.get(record_id)
            if (
                record_id != expected.get("record_id")
                or entry is None
                or member is None
                or worker.get("assignment_sha256")
                != expected.get("leaf_assignment_sha256")
                or proof.get("assignment_sha256")
                != expected.get("leaf_assignment_sha256")
                or worker.get("scientific_sha256") != sha256(proof_raw)
                or worker.get("scientific_payload_sha256")
                != proof.get("scientific_payload_sha256")
                or worker.get("status") != "COMPLETED"
                or worker.get("termination_proven") is not True
            ):
                raise V6PError(f"{label} leaf binding differs: {record_id}")
            validated = coordinator.validate_stage4a_leaf_proof(
                proof, proof_raw, entry=entry, member=member
            )
            if record_id in made:
                raise V6PError(f"duplicate scientific record: {record_id}")
            made[record_id] = {
                "document": validated,
                "path": proof_path.resolve(),
                "raw": proof_raw,
                "source": label,
            }
        wave_bindings.append(
            {
                "bounded_result": _binding(bounded_path),
                "request_id": request_id,
                "wave_index": wave_index,
                "wrapper": _binding(wrapper_path),
            }
        )
    return made, {
        "authorization": _binding(authorization_path),
        "execution_graph": _binding(graph_path),
        "ledger_terminal": _binding(ledger_path),
        "record_count": len(made),
        "wave_bindings": wave_bindings,
    }


def build_union_document() -> tuple[dict[str, Any], Mapping[str, Any], bytes, ModuleType]:
    contract, contract_raw = strict_json(CONTRACT)
    coordinator = _load_module(
        COORDINATOR,
        "_s3_v6p_stage4a_coordinator",
        str(contract["coordinator"]["sha256"]),
    )
    _require_binding(
        CHECKER,
        int(contract["checker"]["byte_count"]),
        str(contract["checker"]["sha256"]),
    )
    _require_binding(
        V6M_ARCHIVE,
        int(contract["predecessor_source"]["candidate_archive"]["bytes"]),
        str(contract["predecessor_source"]["candidate_archive"]["sha256"]),
    )
    _require_binding(
        V6O_ARCHIVE,
        int(contract["optimized_source"]["candidate_archive"]["bytes"]),
        str(contract["optimized_source"]["candidate_archive"]["sha256"]),
    )
    v6n, _v6n_raw = strict_json(V6N_RESULT)
    if (
        v6n.get("terminal")
        != "PROVISIONAL_GO_E4_PL_S3_V6N_MISSING_LEAF_COMPLETION"
        or v6n.get("optimization", {}).get("mechanics_changed") is not False
        or v6n.get("predecessor", {}).get("completed_scientific_record_count") != 69
        or v6n.get("predecessor", {}).get("missing_scientific_record_count") != 12
    ):
        raise V6PError("V6N equivalence authority differs")
    plan_path = V6M_ROOT / "wave-01" / "stage4a-plan.json"
    plan_raw = plan_path.read_bytes()
    if sha256(plan_raw) != PLAN_SHA256:
        raise V6PError("Stage 4A plan differs")
    plan, _ = coordinator._validate_stage4a_plan_raw(plan_raw, label=str(plan_path))
    old, old_source = _validate_source(
        label="V6M_PREDECESSOR",
        root=V6M_ROOT,
        graph_path=V6M_GRAPH,
        graph_bytes=155579,
        graph_sha256="604CDECA29FF0387B1BB9D18D8539C79277B8FB3CE593F870C8C5EFB19D8219E",
        authorization_path=V6M_AUTHORIZATION,
        authorization_bytes=45761,
        authorization_sha256="3A0488921ADA4C088E55E66FAD42E941AE68714EAC631961D58713D9BF8C1E9C",
        ledger_path=V6M_LEDGER,
        ledger_bytes=346340,
        ledger_sha256="108565B10E533BF6C5C0ABDBE896E9609763D3A8DB9E43B99829C654DE35B925",
        wave_count=23,
        coordinator=coordinator,
        plan=plan,
        plan_raw=plan_raw,
    )
    new, new_source = _validate_source(
        label="V6O_OPTIMIZED",
        root=V6O_ROOT,
        graph_path=V6O_GRAPH,
        graph_bytes=59361,
        graph_sha256="F9925409ED0115DFF5D1C69F8B4D225E1097AD92E44285966102084AC488E929",
        authorization_path=V6O_AUTHORIZATION,
        authorization_bytes=7155,
        authorization_sha256="DED781EFD7DBB190D1D6A0154F45A581E020957C575A84D60A90821F803440D2",
        ledger_path=V6O_LEDGER,
        ledger_bytes=353076,
        ledger_sha256="1D711CC8EA29066EDCDE7183F69076F35846B9340C39647A67E7284885187A87",
        wave_count=4,
        coordinator=coordinator,
        plan=plan,
        plan_raw=plan_raw,
    )
    overlap = set(old) & set(new)
    made = old | new
    expected = [
        str(member["record_id"])
        for shard in coordinator._stage4a_plan_shards(plan, plan_raw)
        for member in shard["records"]
    ]
    if overlap or len(old) != 69 or len(new) != 12 or set(made) != set(expected):
        raise V6PError("joined scientific coverage is not exactly 69 + 12 = 81")
    records = [
        {
            "byte_count": len(made[record_id]["raw"]),
            "record_id": record_id,
            "scientific_payload_sha256": made[record_id]["document"][
                "scientific_payload_sha256"
            ],
            "sha256": sha256(made[record_id]["raw"]),
            "source": made[record_id]["source"],
        }
        for record_id in expected
    ]
    union = {
        "activation_authorized": False,
        "plan_sha256": PLAN_SHA256,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "record_count": 81,
        "records": records,
        "schema": UNION_SCHEMA,
        "source_groups": [old_source, new_source],
        "v6n_equivalence": _binding(V6N_RESULT),
    }
    return union, plan, plan_raw, coordinator


def _diagonal_documents(
    records: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
    plan_raw: bytes,
    coordinator: ModuleType,
) -> dict[str, dict[str, Any]]:
    protocol: Mapping[str, Any] | None = None
    made: dict[str, dict[str, Any]] = {}
    for shard in coordinator._stage4a_plan_shards(plan, plan_raw):
        assignment_id = str(shard["assignment_id"])
        classifying = []
        ids = []
        for member in shard["records"]:
            record_id = str(member["record_id"])
            document = records[record_id]["document"]
            payload = document["scientific_payload"]
            if protocol is None:
                protocol = payload["protocol"]
            elif payload["protocol"] != protocol:
                raise V6PError("scientific protocols disagree across source groups")
            classifying.append(payload["record"])
            ids.append(record_id)
        payload = {
            "assignment_id": assignment_id,
            "classifying_records": classifying,
            "diagonal": shard["diagonal"],
            "phase": "4A",
            "protocol": protocol,
            "schema": coordinator.DIAGONAL_PAYLOAD_SCHEMA,
            "scope": "full",
            "v1_comparator_diagnostics": [],
            "v1_comparator_disposition": coordinator.LEAF_V1_DISPOSITION,
        }
        made[assignment_id] = {
            "assignment_sha256": shard["assignment_sha256"],
            "plan_sha256": sha256(plan_raw),
            "record_count": 27,
            "record_ids": ids,
            "record_ids_sha256": sha256(canonical_bytes(ids)),
            "schema": coordinator.DIAGONAL_SCIENTIFIC_SCHEMA,
            "scientific_payload": payload,
            "scientific_payload_sha256": sha256(canonical_bytes(payload)),
            "selector": coordinator.LEAF_SELECTOR,
            "terminal": coordinator.LEAF_PROOF_TERMINAL,
        }
    return made


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _validate_execution_authorization(contract_raw: bytes) -> tuple[dict[str, Any], bytes]:
    authorization, raw = strict_json(AUTHORIZATION)
    expected = {
        "activation_authorized",
        "authority_commit",
        "contract_sha256",
        "execution_authorized",
        "program_sha256",
        "review_sha256",
        "schema",
        "user_approval",
    }
    if set(authorization) != expected:
        raise V6PError("V6P execution authorization keys differ")
    if (
        authorization["schema"]
        != "anysolver.e4-pl-s3-v6p-stage4a-execution-authorization-v1"
        or authorization["activation_authorized"] is not False
        or authorization["execution_authorized"] is not True
        or authorization["contract_sha256"] != sha256(contract_raw)
        or authorization["program_sha256"] != sha256(Path(__file__).read_bytes())
        or authorization["review_sha256"]
        != sha256((REFERENCE / "e4_pl_s3_v6p_stage4a_completion_review.json").read_bytes())
        or authorization["user_approval"] != "STANDING_S3_QUALIFICATION_APPROVAL"
    ):
        raise V6PError("V6P execution authorization differs")
    return authorization, raw


def run_completion(output_root: Path) -> dict[str, Any]:
    started = time.monotonic()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=False)
    union, plan, plan_raw, coordinator = build_union_document()
    contract, contract_raw = strict_json(CONTRACT)
    _authorization, authorization_raw = _validate_execution_authorization(contract_raw)
    union_raw = canonical_bytes(union)
    union_path = output_root / "completion-union.json"
    plan_path = output_root / "stage4a-plan.json"
    _write_exclusive(union_path, union_raw)
    _write_exclusive(plan_path, plan_raw)
    union_records = {str(row["record_id"]): row for row in union["records"]}
    records: dict[str, dict[str, Any]] = {}
    for source, root, count in (
        ("V6M_PREDECESSOR", V6M_ROOT, 23),
        ("V6O_OPTIMIZED", V6O_ROOT, 4),
    ):
        for wave_index in range(count):
            for worker_index in range(1, 4):
                path = root / f"wave-{wave_index + 1:02d}" / f"worker-{worker_index}" / "scientific.json"
                value, raw = strict_json(path)
                record_id = str(value["record_ids"][0])
                binding = union_records.get(record_id)
                if (
                    binding is None
                    or binding["source"] != source
                    or binding["byte_count"] != len(raw)
                    or binding["sha256"] != sha256(raw)
                    or binding["scientific_payload_sha256"]
                    != value["scientific_payload_sha256"]
                    or record_id in records
                ):
                    raise V6PError(f"scientific record changed after union validation: {record_id}")
                records[record_id] = {
                    "document": value,
                    "path": path,
                    "raw": raw,
                    "source": source,
                }
    documents = _diagonal_documents(records, plan, plan_raw, coordinator)
    proofs = coordinator.publish_stage4a_diagonal_documents(documents, output_root)
    deadline = started + int(contract["execution"]["complete_wall_seconds"])
    replicas: list[list[dict[str, Any]]] = [[], []]
    for assignment_id in coordinator.EXPECTED_SHARDS:
        proof = Path(proofs[assignment_id]["proof_path"])
        def launch(replica: int) -> dict[str, Any]:
            root = output_root / f"checker-replica-{replica + 1}" / assignment_id
            return coordinator._run_checker_process(
                assignment_id=assignment_id,
                proof=proof,
                plan=plan_path,
                output=root / "result.json",
                stdout_path=root / "stdout.bin",
                stderr_path=root / "stderr.bin",
                deadline=deadline,
            )
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(launch, replica) for replica in range(2)]
            pair = [future.result() for future in futures]
        for replica, wrapper in enumerate(pair):
            replicas[replica].append(wrapper)
    checker_aggregate = coordinator.aggregate_checker_results(
        replicas,
        producer_proofs=proofs,
        producer_result_sha256=sha256(union_raw),
        contract_sha256=sha256(contract_raw),
        authorization_sha256=sha256(authorization_raw),
    )
    final_union, _final_plan, final_plan_raw, _final_coordinator = build_union_document()
    _final_authorization, final_authorization_raw = _validate_execution_authorization(
        CONTRACT.read_bytes()
    )
    if (
        canonical_bytes(final_union) != union_raw
        or final_plan_raw != plan_raw
        or final_authorization_raw != authorization_raw
        or union_path.read_bytes() != union_raw
        or plan_path.read_bytes() != plan_raw
    ):
        raise V6PError("completion authority or scientific union changed before publication")
    if checker_aggregate["terminal"] == coordinator.NO_GO:
        terminal = NO_GO
    elif checker_aggregate["terminal"] == coordinator.PASS:
        terminal = PASS
    else:
        raise V6PError("checker aggregate terminal is unregistered")
    result = {
        "activation_authorized": False,
        "checker_aggregate": checker_aggregate,
        "completion_union": {
            "bytes": len(union_raw),
            "record_count": 81,
            "sha256": sha256(union_raw),
        },
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": RESULT_SCHEMA,
        "stage4b_extension_authorized": terminal == PASS,
        "terminal": terminal,
    }
    _write_exclusive(output_root / "completion-result.json", canonical_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-union", action="store_true")
    parser.add_argument("--run-completion", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    if args.validate_union == args.run_completion:
        raise V6PError("select exactly one completion mode")
    if args.validate_union:
        union, _plan, _plan_raw, _coordinator = build_union_document()
        print(sha256(canonical_bytes(union)))
        return 0
    if args.output_root is None:
        raise V6PError("--output-root is required")
    result = run_completion(args.output_root)
    return 0 if result["terminal"] in {PASS, NO_GO} else 2


if __name__ == "__main__":
    raise SystemExit(main())
