from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_authorization.json"
AUTHORITY = REFERENCE / "e4_pl_s3_v6m_stage4a_authority.py"
EXECUTOR = REFERENCE / "e4_pl_s3_v6m_stage4a_serial_executor.py"
REVIEW = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_review.json"
STATUS = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_status.json"
FORMAL_ROOT = Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6m-validator-safe")
GRAPH = FORMAL_ROOT / "execution-graph.json"
ARCHIVE = Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6k-2d91bba2\candidate-source.tar")


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return value


def test_v6m_closeout_is_canonical_reproducible_and_nonactivating() -> None:
    authorization = _canonical(AUTHORIZATION)
    review = _canonical(REVIEW)
    status = _canonical(STATUS)
    raw = AUTHORIZATION.read_bytes()
    assert len(raw) == status["authorization"]["bytes"] == 45_761
    assert hashlib.sha256(raw).hexdigest().upper() == status["authorization"]["sha256"]
    assert review["findings"] == []
    assert status["activation_authorized"] is False
    authority = _module(AUTHORITY, "v6m_closeout_authority")
    made = authority.generate(
        GRAPH, ARCHIVE, FORMAL_ROOT, AUTHORIZATION,
        Path(r"C:\Github\.resource-manager\requests"),
    )
    assert authority.canonical_bytes(made) == raw


def test_v6m_executor_validates_and_implementation_commit_is_exact() -> None:
    executor = _module(EXECUTOR, "v6m_closeout_executor")
    authorization, raw, graph, graph_raw = executor.validate_authorization(
        AUTHORIZATION, GRAPH, ARCHIVE
    )
    assert authorization["stage4a_execution_authorized"] is True
    assert graph["runtime_policy"]["maximum_concurrent_workers"] == 2
    assert len(raw) == 45_761 and len(graph_raw) == 155_579
    lines = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%T%n%P%n%s", "5e50cfa9e809c64da94c044f68e0e5fb4677e7ab"],
        cwd=ROOT, check=True, capture_output=True, text=True, timeout=30,
    ).stdout.splitlines()
    assert lines == [
        "5e50cfa9e809c64da94c044f68e0e5fb4677e7ab",
        "400781b1af738eeffaa7f50c426dc27e95eaa80b",
        "a32497e8758f73708125196674363b83708cd71b",
        "docs: authorize S3 V2D preparation-safe requests",
    ]
