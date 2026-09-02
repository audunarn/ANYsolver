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
CONTRACT = REFERENCE / "e4_pl_s3_v6k_stage4a_publisher_contract.json"
PUBLISHER = REFERENCE / "e4_pl_s3_v6k_stage4a_request_publisher.py"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6k_stage4a_execution_authorization.json"
FORMAL_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6k-2d91bba2"
)
GRAPH = FORMAL_ROOT / "execution-graph.json"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_v6k_publisher_contract_is_canonical_and_nonexecuting() -> None:
    raw = CONTRACT.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    assert value["publication_policy"] == {
        "exclusive_request_creation": True,
        "ledger_mutation": False,
        "request_execution": False,
        "request_overwrite_forbidden": True,
    }
    assert value["production_boundary"]["activation_authorized"] is False


def test_v6k_publisher_is_standard_library_only() -> None:
    tree = ast.parse(PUBLISHER.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__", "argparse", "hashlib", "importlib", "pathlib", "sys",
        "types", "typing",
    }


def test_v6k_disposable_publication_is_exact_and_exclusive(tmp_path: Path) -> None:
    publisher = _module(PUBLISHER, "v6k_disposable_publisher")
    request_root = tmp_path / "requests"
    request_root.mkdir()
    made = publisher.publish_authorized(GRAPH, AUTHORIZATION, request_root)
    assert made["request_count"] == 27
    assert len(list(request_root.glob("*.json"))) == 27
    authorization = json.loads(AUTHORIZATION.read_bytes())
    for row in authorization["requests"]:
        path = request_root / f"{row['request']['request_id']}.json"
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest().upper() == row["request_sha256"]
    with pytest.raises(FileExistsError):
        publisher.publish_authorized(GRAPH, AUTHORIZATION, request_root)


def test_v6k_publisher_extent_has_no_production_paths() -> None:
    contract = json.loads(CONTRACT.read_bytes())
    assert all(
        path.startswith("docs/reference_cases/") or path.startswith("tests/")
        for path in contract["authority_commit"]["expected_paths"]
    )
