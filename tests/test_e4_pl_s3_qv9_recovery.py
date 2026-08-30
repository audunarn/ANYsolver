"""Focused authority tests for the QV8 incident and QV9 recovery harness."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
INCIDENT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_qv8_process_and_science_incident_v1.json"
CONTRACT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_qv9_recovery_contract_v1.json"
FORMAL = ROOT / "scripts" / "run_e4_pl_s3_qualification_v4.py"
SUCCESSOR = ROOT / "docs" / "reference_cases" / "e4_pl_s3_qualification_optimization_v4.py"
PRODUCER = ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_structural_producer.py"
DIAGNOSTIC = ROOT / "scripts" / "run_e4_pl_s3_qv9_diagnostic.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()
        + b"\n"
    )


def test_qv8_incident_is_canonical_hash_bound_and_never_reusable() -> None:
    raw = INCIDENT.read_bytes()
    incident = json.loads(raw)
    assert raw == _canonical(incident)
    assert incident["request"]["id"] == "d9adb98245d54d27b3a29970f8a3b0c7"
    assert incident["cycle_2_started"] is False
    assert "NEVER_REUSED" in incident["disposition"]
    assert incident["terminal"] == "BLOCKED_E4_PL_S3_DEFAULT_ACTIVATION_EVIDENCE_OR_REVIEW"
    assert len(incident["process_defects"]) == 4
    assert incident["scientific_diagnostics"]["structural_records_completed"] == 252
    contract_raw = CONTRACT.read_bytes()
    contract = json.loads(contract_raw)
    assert contract_raw == _canonical(contract)
    frozen = contract["frozen_qv8_incident"]
    assert frozen == {
        "bytes": len(raw),
        "path": "docs/reference_cases/e4_pl_s3_qv8_process_and_science_incident_v1.json",
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }
    implementation = contract["implementation"]
    assert implementation["contract_self_binding"] is False
    for row in implementation["bound_files"]:
        path = ROOT / row["path"]
        content = path.read_bytes()
        assert row["bytes"] == len(content)
        assert row["sha256"] == hashlib.sha256(content).hexdigest().upper()
    assert implementation["changed_paths"] == sorted(
        [
            "docs/reference_cases/e4_pl_s3_qualification_optimization_v4.py",
            "docs/reference_cases/e4_pl_s3_qv8_process_and_science_incident_v1.json",
            "docs/reference_cases/e4_pl_s3_qv9_recovery_contract_v1.json",
            "scripts/prepare_e4_pl_s3_qualification_v4_input.py",
            "scripts/run_e4_pl_s3_qualification_v4.py",
            "scripts/run_e4_pl_s3_qv9_diagnostic.py",
            "tests/test_e4_pl_s3_qualification_optimization_v4.py",
            "tests/test_e4_pl_s3_qv9_recovery.py",
        ]
    )


def test_structural_schedule_has_one_external_baseline_and_four_cost_ordered_groups() -> None:
    formal = _load("_qv9_formal_schedule", FORMAL)
    sequences = [
        {"diagonal": "slash", "fraction_percent": 0, "mask": "none"},
        *[
            {"diagonal": "slash", "fraction_percent": fraction, "mask": mask}
            for fraction in (1, 5, 10, 25)
            for mask in ("a", "b", "c", "d", "e")
        ],
    ]
    base = SimpleNamespace(_structural_sequences=lambda _diagonal: sequences)
    groups = formal._structural_sequence_chunks(base, "slash")
    assert len(groups) == 4
    assert [len(group) for group in groups] == [5, 5, 5, 5]
    assert all(row["fraction_percent"] != 0 for group in groups for row in group)
    identities = [
        (row["fraction_percent"], row["mask"])
        for group in groups
        for row in group
    ]
    assert sorted(identities) == sorted(
        (row["fraction_percent"], row["mask"]) for row in sequences[1:]
    )
    costs = [sum(100 + row["fraction_percent"] for row in group) for group in groups]
    assert costs == sorted(costs, reverse=True)


def test_successor_captures_and_clones_only_tracked_regular_files(tmp_path: Path) -> None:
    successor = _load("_qv9_gitless_copy", SUCCESSOR)
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    (source / "pkg").mkdir()
    (source / "pkg" / "module.py").write_text("VALUE = 7\n", encoding="utf-8")
    (source / ".gitignore").write_text("scratch/\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    (source / "scratch").mkdir()
    (source / "scratch" / "generated.bin").write_bytes(b"ignored")
    base = SimpleNamespace(QualificationError=RuntimeError)
    captured, manifest = successor.capture_tracked_execution_copy(
        base, source, tmp_path / "captured"
    )
    assert not (captured / ".git").exists()
    assert not (captured / "scratch").exists()
    clone = successor.clone_gitless_execution_copy(
        base, captured, tmp_path / "clone", manifest
    )
    assert (clone / "pkg" / "module.py").read_text(encoding="utf-8") == "VALUE = 7\n"
    (captured / "pkg" / "module.py").write_text("mutated\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="captured execution tree changed"):
        successor.clone_gitless_execution_copy(
            base, captured, tmp_path / "clone-2", manifest
        )


def test_qv9_formal_children_use_lease_and_preload_all_failed_helpers() -> None:
    formal = FORMAL.read_text(encoding="utf-8")
    successor = SUCCESSOR.read_text(encoding="utf-8")
    assert "_capture_execution_lease(" in formal
    assert "_read_execution_lease(successor_authority)" in formal
    assert "full_validation=True" in formal
    assert "captured_roots=captured_roots" in formal
    for module in (
        "scripts.run_portable_ci",
        "_e4_pl_s3_native_trial",
        "_s3_v4_nested_target",
    ):
        assert module in successor
    assert "cwd=execution_root" in successor
    assert "--rootdir" in successor and "--confcutdir" in successor


def test_shared_structural_baseline_is_reused_without_a_second_q4_solve() -> None:
    formal = _load("_qv9_shared_baseline_runner", FORMAL)
    levels = (20, 40, 80, 160)
    baseline_row = {
        "energy_defect_proxy_slope": 1.0,
        "records": [
            {"level": level, "record_id": f"N{level}:0PCT"}
            for level in levels
        ],
        "response_error_slope": 1.0,
        "sequence": {"diagonal": "slash", "fraction_percent": 0, "mask": "none"},
    }
    errors = {
        level: {(0, 0): 0.5 / level, (1, 2): 0.25 / level}
        for level in levels
    }
    shared = formal._encode_shared_baseline(baseline_row, errors)
    rows_by_level, errors_by_level = formal._decode_shared_baseline(shared)
    assert rows_by_level == {
        level: {"level": level, "record_id": f"N{level}:0PCT"}
        for level in levels
    }
    assert errors_by_level == errors
    assert shared["schema"] == formal.SHARED_BASELINE_SCHEMA
    mutated = json.loads(json.dumps(shared))
    mutated["errors"].append(mutated["errors"][0])
    with pytest.raises(formal.QualificationError, match="errors are duplicated"):
        formal._decode_shared_baseline(mutated)


def test_qv9_diagnostic_blocks_reference_defects_and_authorizes_only_v2_planning() -> None:
    diagnostic = _load("_qv9_diagnostic", DIAGNOSTIC)
    base = {
        "all_q4_control": {
            "locking_reference_valid": True,
            "q4_reference_valid": True,
        },
        "evidence_sha256": {"targeted": "A" * 64},
        "interface_audit": {"component_map_valid": True, "record_count": 12},
        "mixed_sequences": {name: True for name in diagnostic.DIAGONALS},
        "process_repairs": {name: True for name in diagnostic.PROCESS_REPAIRS},
        "schema": diagnostic.INPUT_SCHEMA,
        "v1_contradictions": [],
    }
    clean = diagnostic.adjudicate(base)
    assert clean["terminal"] == diagnostic.TERMINALS[2]
    assert clean["default_activation_authorized"] is False
    failed = json.loads(json.dumps(base))
    failed["all_q4_control"]["locking_reference_valid"] = False
    assert diagnostic.adjudicate(failed)["terminal"] == diagnostic.TERMINALS[0]
    contradiction = json.loads(json.dumps(base))
    contradiction["v1_contradictions"] = ["INTERFACE_RESULTANT:EXACT_MAP_MISMATCH"]
    result = diagnostic.adjudicate(contradiction)
    assert result["terminal"] == diagnostic.TERMINALS[1]
    assert result["v2_plan_preparation_authorized"] is True
    assert result["default_activation_authorized"] is False


def test_qv9_changes_do_not_touch_q4_mechanics_or_relax_science() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["mechanics_change"] == "NONE"
    assert contract["q4_mechanics_change"] == "NONE"
    assert contract["scientific_cases_change"] == "NONE"
    assert contract["scientific_tolerances_change"] == "NONE"
    assert contract["production_restriction"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    formal = FORMAL.read_text(encoding="utf-8")
    assert "shared structural baseline" in formal
