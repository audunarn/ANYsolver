from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_license_compliance.py"
SPEC = importlib.util.spec_from_file_location("check_license_compliance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def test_repository_license_contract() -> None:
    CHECK.validate_repository(ROOT)


def test_dependency_inventory_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "inventory.json"
    path.write_text('{"schema":"one","schema":"two"}\n', encoding="utf-8")
    with pytest.raises(CHECK.ComplianceError, match="duplicate JSON key"):
        CHECK._load_inventory(path)


def test_dependency_inventory_is_canonical() -> None:
    path = ROOT / "dependency-licenses.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    assert path.read_text(encoding="utf-8").replace("\r\n", "\n") == expected


def test_license_hash_detects_mutation(tmp_path: Path) -> None:
    path = tmp_path / "LICENSE"
    path.write_text((ROOT / "LICENSE").read_text(encoding="utf-8") + "changed\n")
    digest = CHECK.hashlib.sha256(CHECK._normalized_license_bytes(path)).hexdigest()
    assert digest != CHECK.EXPECTED_LICENSE_SHA256
