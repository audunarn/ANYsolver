from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
PROGRAM = REFERENCE / "e4_pl_s3_v6p_stage4a_completion.py"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6p_stage4a_execution_authorization.json"
STATUS = REFERENCE / "e4_pl_s3_v6p_stage4a_execution_status.json"


def _module():
    spec = importlib.util.spec_from_file_location("v6p_execution_authority", PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v6p_execution_authority"] = module
    spec.loader.exec_module(module)
    return module


def _canonical(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return value, raw


def test_v6p_execution_authorization_is_canonical_valid_and_nonactivating() -> None:
    module = _module()
    authorization, raw = _canonical(AUTHORIZATION)
    status, _ = _canonical(STATUS)
    made, made_raw = module._validate_execution_authorization(module.CONTRACT.read_bytes())
    assert made == authorization and made_raw == raw
    assert authorization["activation_authorized"] is False
    assert status["execution"]["mechanics_rerun"] is False
    assert status["execution"]["record_count"] == 81


def test_v6p_authority_commit_identity_is_exact() -> None:
    lines = subprocess.run(
        [
            "git", "show", "-s", "--format=%H%n%T%n%P%n%s",
            "77fa2fd0f4e766804a6dabf1efd9b492af54e9cf",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.splitlines()
    assert lines == [
        "77fa2fd0f4e766804a6dabf1efd9b492af54e9cf",
        "d02d80e154be5c76f992a4142beb03ba4984b30c",
        "a646dff05b991f4beac05d9702823258bfe49154",
        "docs: authorize S3 V6P Stage 4A completion",
    ]
