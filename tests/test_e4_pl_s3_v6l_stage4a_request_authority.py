from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6l_stage4a_request_contract.json"
AUTHORITY = REFERENCE / "e4_pl_s3_v6l_stage4a_authority.py"
PUBLISHER = REFERENCE / "e4_pl_s3_v6l_stage4a_request_publisher.py"
EXECUTOR = REFERENCE / "e4_pl_s3_v6l_stage4a_serial_executor.py"
V6J_AUTHORIZATION = REFERENCE / "e4_pl_s3_v6j_stage4a_execution_authorization.json"
V6K_AUTHORIZATION = REFERENCE / "e4_pl_s3_v6k_stage4a_execution_authorization.json"
FORMAL_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6l-dependency-closure"
)
GRAPH = FORMAL_ROOT / "execution-graph.json"
CANDIDATE_ARCHIVE = Path(
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


def test_v6l_request_contract_is_canonical_and_nonactivating() -> None:
    raw = CONTRACT.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    assert value["request_authority"]["request_count"] == 27
    assert value["request_authority"]["predecessor_ids_reused"] is False
    assert value["production_boundary"]["activation_authorized"] is False
    assert value["runtime_policy"]["maximum_concurrent_workers"] == 2


def test_v6l_authority_is_fresh_deterministic_and_exact(tmp_path: Path) -> None:
    authority = _module(AUTHORITY, "v6l_request_authority")
    request_root = Path(r"C:\Github\.resource-manager\requests")
    authorization_path = tmp_path / "authorization.json"
    qualification_root = tmp_path / "qualification"
    first = authority.generate(
        GRAPH, CANDIDATE_ARCHIVE, qualification_root, authorization_path, request_root
    )
    second = authority.generate(
        GRAPH, CANDIDATE_ARCHIVE, qualification_root, authorization_path, request_root
    )
    assert authority.canonical_bytes(first) == authority.canonical_bytes(second)
    assert first["schema"] == "anysolver.e4-pl-s3-v6l-stage4a-execution-authorization-v1"
    assert first["activation_authorized"] is False
    assert len(first["requests"]) == 27
    ids = [row["request"]["request_id"] for row in first["requests"]]
    assert len(ids) == len(set(ids)) == 27
    old_ids = {
        row["request"]["request_id"]
        for path in (V6J_AUTHORIZATION, V6K_AUTHORIZATION)
        for row in json.loads(path.read_bytes())["requests"]
    }
    assert old_ids.isdisjoint(ids)
    assert all(
        "e4_pl_s3_v6l_stage4a_execution_graph.py" in row["request"]["command"]
        for row in first["requests"]
    )


def test_v6l_disposable_publication_is_exact_and_exclusive(tmp_path: Path) -> None:
    authority = _module(AUTHORITY, "v6l_publish_authority")
    publisher = _module(PUBLISHER, "v6l_disposable_publisher")
    registered_request_root = Path(r"C:\Github\.resource-manager\requests")
    request_root = tmp_path / "requests"
    request_root.mkdir()
    authorization_path = tmp_path / "authorization.json"
    authorization = authority.generate(
        GRAPH,
        CANDIDATE_ARCHIVE,
        tmp_path / "qualification",
        authorization_path,
        registered_request_root,
    )
    authorization_path.write_bytes(authority.canonical_bytes(authorization))
    receipt = publisher.publish_authorized(GRAPH, authorization_path, request_root)
    assert receipt["request_count"] == 27
    assert len(list(request_root.glob("*.json"))) == 27
    for row in authorization["requests"]:
        path = request_root / f"{row['request']['request_id']}.json"
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest().upper() == row["request_sha256"]
    with pytest.raises(FileExistsError):
        publisher.publish_authorized(GRAPH, authorization_path, request_root)


def test_v6l_executor_accepts_disposable_successor_authority(tmp_path: Path) -> None:
    authority = _module(AUTHORITY, "v6l_executor_authority")
    executor = _module(EXECUTOR, "v6l_executor_validation")
    tracked_authorization = REFERENCE / "e4_pl_s3_v6l_stage4a_execution_authorization.json"
    made = authority.generate(
        GRAPH,
        CANDIDATE_ARCHIVE,
        FORMAL_ROOT,
        tracked_authorization,
        Path(r"C:\Github\.resource-manager\requests"),
    )
    disposable = tmp_path / "authorization.json"
    disposable.write_bytes(authority.canonical_bytes(made))
    value, raw, graph, graph_raw = executor.validate_authorization(
        disposable, GRAPH, CANDIDATE_ARCHIVE
    )
    assert len(value["requests"]) == 27
    assert value["activation_authorized"] is False
    assert graph["runtime_policy"]["maximum_concurrent_workers"] == 2
    assert len(raw) > 40_000 and len(graph_raw) == 155_579


def test_v6l_tools_are_standard_library_only_and_research_only() -> None:
    allowed = {
        "__future__", "argparse", "hashlib", "importlib", "os", "pathlib",
        "sys", "types", "typing",
    }
    for path in (AUTHORITY, PUBLISHER, EXECUTOR):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert imports <= allowed
    contract = json.loads(CONTRACT.read_bytes())
    assert all(
        path.startswith("docs/reference_cases/") or path.startswith("tests/")
        for path in contract["authority_commit"]["expected_paths"]
    )
