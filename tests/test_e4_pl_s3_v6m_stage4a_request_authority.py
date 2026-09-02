from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6m_stage4a_request_contract.json"
AUTHORITY = REFERENCE / "e4_pl_s3_v6m_stage4a_authority.py"
PUBLISHER = REFERENCE / "e4_pl_s3_v6m_stage4a_request_publisher.py"
EXECUTOR = REFERENCE / "e4_pl_s3_v6m_stage4a_serial_executor.py"
PREDECESSORS = (
    REFERENCE / "e4_pl_s3_v6j_stage4a_execution_authorization.json",
    REFERENCE / "e4_pl_s3_v6k_stage4a_execution_authorization.json",
    REFERENCE / "e4_pl_s3_v6l_stage4a_execution_authorization.json",
)
FORMAL_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6m-validator-safe"
)
GRAPH = FORMAL_ROOT / "execution-graph.json"
ARCHIVE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6k-2d91bba2\candidate-source.tar"
)


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_v6m_request_contract_is_canonical_and_nonactivating() -> None:
    raw = CONTRACT.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    assert value["request_authority"]["request_count"] == 27
    assert value["production_boundary"]["activation_authorized"] is False


def test_v6m_authority_is_deterministic_and_disjoint() -> None:
    authority = _module(AUTHORITY, "v6m_request_authority")
    authorization_path = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_authorization.json"
    request_root = Path(r"C:\Github\.resource-manager\requests")
    first = authority.generate(GRAPH, ARCHIVE, FORMAL_ROOT, authorization_path, request_root)
    second = authority.generate(GRAPH, ARCHIVE, FORMAL_ROOT, authorization_path, request_root)
    assert authority.canonical_bytes(first) == authority.canonical_bytes(second)
    ids = {row["request"]["request_id"] for row in first["requests"]}
    old_ids = {
        row["request"]["request_id"]
        for path in PREDECESSORS
        for row in json.loads(path.read_bytes())["requests"]
    }
    assert len(ids) == 27 and ids.isdisjoint(old_ids)
    assert all(
        "e4_pl_s3_v6m_stage4a_execution_graph.py" in row["request"]["command"]
        for row in first["requests"]
    )


def test_v6m_publication_and_executor_validate_disposably(tmp_path: Path) -> None:
    authority = _module(AUTHORITY, "v6m_publish_authority")
    publisher = _module(PUBLISHER, "v6m_disposable_publisher")
    executor = _module(EXECUTOR, "v6m_disposable_executor")
    disposable = tmp_path / "authorization.json"
    authorization = authority.generate(
        GRAPH,
        ARCHIVE,
        FORMAL_ROOT,
        disposable,
        Path(r"C:\Github\.resource-manager\requests"),
    )
    disposable.write_bytes(authority.canonical_bytes(authorization))
    value, raw, graph, graph_raw = executor.validate_authorization(
        disposable, GRAPH, ARCHIVE
    )
    assert len(value["requests"]) == 27
    assert graph["runtime_policy"]["maximum_concurrent_workers"] == 2
    assert len(raw) > 40_000 and len(graph_raw) == 155_579
    request_root = tmp_path / "requests"
    request_root.mkdir()
    receipt = publisher.publish_authorized(GRAPH, disposable, request_root)
    assert receipt["request_count"] == 27
    for row in authorization["requests"]:
        raw_request = (request_root / f"{row['request']['request_id']}.json").read_bytes()
        assert hashlib.sha256(raw_request).hexdigest().upper() == row["request_sha256"]
    with pytest.raises(FileExistsError):
        publisher.publish_authorized(GRAPH, disposable, request_root)
