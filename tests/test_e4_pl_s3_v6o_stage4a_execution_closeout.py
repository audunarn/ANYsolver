from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6o_stage4a_execution_authorization.json"
AUTHORITY = REFERENCE / "e4_pl_s3_v6o_stage4a_authority.py"
EXECUTOR = REFERENCE / "e4_pl_s3_v6o_stage4a_serial_executor.py"
REVIEW = REFERENCE / "e4_pl_s3_v6o_stage4a_execution_review.json"
STATUS = REFERENCE / "e4_pl_s3_v6o_stage4a_execution_status.json"
FORMAL_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6o-missing-leaves-fb7d1fe"
)
GRAPH = FORMAL_ROOT / "execution-graph.json"
ARCHIVE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6n-lease-optimization-c1e2ad9\candidate-source.tar"
)


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
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return value


def test_v6o_closeout_is_canonical_reproducible_and_nonactivating() -> None:
    authorization = _canonical(AUTHORIZATION)
    review = _canonical(REVIEW)
    status = _canonical(STATUS)
    raw = AUTHORIZATION.read_bytes()
    assert len(raw) == status["authorization"]["bytes"] == 7_155
    assert hashlib.sha256(raw).hexdigest().upper() == status["authorization"]["sha256"]
    assert len(authorization["requests"]) == 4
    assert review["findings"] == []
    assert status["activation_authorized"] is False
    authority = _module(AUTHORITY, "v6o_closeout_authority")
    made = authority.generate(
        GRAPH,
        ARCHIVE,
        FORMAL_ROOT,
        AUTHORIZATION,
        Path(r"C:\Github\.resource-manager\requests"),
    )
    assert authority.canonical_bytes(made) == raw


def test_v6o_executor_validates_and_implementation_commit_is_exact() -> None:
    executor = _module(EXECUTOR, "v6o_closeout_executor")
    authorization, raw, graph, graph_raw = executor.validate_authorization(
        AUTHORIZATION, GRAPH, ARCHIVE
    )
    assert authorization["stage4a_execution_authorized"] is True
    assert graph["runtime_policy"]["maximum_concurrent_workers"] == 2
    assert len(raw) == 7_155 and len(graph_raw) == 59_361
    lines = subprocess.run(
        [
            "git", "show", "-s", "--format=%H%n%T%n%P%n%s",
            "9c84bb95ff4055f560bdb279c6aa8308fff317c6",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.splitlines()
    assert lines == [
        "9c84bb95ff4055f560bdb279c6aa8308fff317c6",
        "a0c294b58f7836c148bd7cfbf78314379f616c2f",
        "fb7d1feef7900309fe26ed8a62027a334e98a804",
        "docs: authorize S3 V6O missing-leaf requests",
    ]
