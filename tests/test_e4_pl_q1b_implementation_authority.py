from __future__ import annotations

import ast
import os
import json
from pathlib import Path
import subprocess
import sys

import e4_pl_q1b_common as common


ROOT = Path(__file__).resolve().parents[1]


def test_q1b_implementation_hashes_and_independence(tmp_path: Path) -> None:
    registered = os.environ.get("Q1B_REGISTERED_EVIDENCE_ROOT")
    if registered:
        evidence_root = Path(registered)
        ref = evidence_root / "docs/reference_cases"
        contract_sha = common.sha256((evidence_root / common.CONTRACT_PATH).read_bytes())
        cycle1_raw, cycle1, payload1 = common.read_registered_cycle(ref / "e4_pl_q1b_cycle1.json", expected_cycle=1, expected_contract_sha256=contract_sha)
        cycle2_raw, cycle2, payload2 = common.read_registered_cycle(ref / "e4_pl_q1b_cycle2.json", expected_cycle=2, expected_contract_sha256=contract_sha)
        agreement_raw, agreement = common.read_json(ref / "e4_pl_q1b_agreement.json")
        _, output = common.read_json(ref / "e4_pl_q1b_output.json")
        assert set(agreement) == {"candidate_id", "common_payload_byte_identical", "common_payload_sha256", "cycle1_sha256", "cycle2_sha256", "production", "schema", "study_id"}
        assert agreement["schema"] == "anysolver.s4.e4-pl-q1b-agreement-v1"
        assert agreement["candidate_id"] == common.CANDIDATE_ID and agreement["study_id"] == common.STUDY_ID and agreement["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
        assert agreement["cycle1_sha256"] == common.sha256(cycle1_raw) and agreement["cycle2_sha256"] == common.sha256(cycle2_raw)
        assert agreement["common_payload_byte_identical"] is True and payload1 == payload2
        assert agreement["common_payload_sha256"] == cycle1["common_payload_sha256"] == cycle2["common_payload_sha256"] == common.sha256(payload1)
        assert set(output) == {"agreement_sha256", "candidate_id", "common_payload_sha256", "production", "schema", "study_id", "terminal"}
        assert output["schema"] == "anysolver.s4.e4-pl-q1b-output-v1" and output["agreement_sha256"] == common.sha256(agreement_raw)
        assert output["candidate_id"] == common.CANDIDATE_ID and output["study_id"] == common.STUDY_ID and output["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
        assert output["common_payload_sha256"] == agreement["common_payload_sha256"]
        assert output["terminal"] == cycle1["common_payload"]["terminal"] == "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT"
        return
    plan = json.loads((ROOT / "docs/reference_cases/e4_pl_q1b_plan_contract.json").read_text(encoding="utf-8"))
    assert len(plan["stage_paths"]["IMPLEMENTATION11"]) == 11
    assert plan["future_campaign"]["runtime"] == {
        "automatic_retry": False,
        "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1,
        "timeout_seconds_per_process": 600,
        "worker_count": 3,
    }
    checker_path = ROOT / "docs/reference_cases/e4_pl_q1b_assembled_checker.py"
    tree = ast.parse(checker_path.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imports |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert "e4_pl_q1b_assembled_producer" not in imports
    runner_source = (ROOT / "docs/reference_cases/e4_pl_q1b_bounded_runner.py").read_text(encoding="utf-8")
    authority_offset = runner_source.index("validate_authority(repository_root")
    commissioning_offset = runner_source.index('"--commission"', authority_offset)
    shard_offset = runner_source.index('"--run-shard"', commissioning_offset)
    assert authority_offset < commissioning_offset < shard_offset
    assert "q1y3_evidence_root is None" in runner_source
    for name in ("e4_pl_q1b_assembled_producer.py", "e4_pl_q1b_assembled_checker.py"):
        source = (ROOT / "docs/reference_cases" / name).read_text(encoding="utf-8")
        assert "--authority-check-only" in source
        assert "validate_execution_authority" in source
    missing_contract = tmp_path / "missing-contract.json"
    missing_authority = tmp_path / "missing-authority.json"
    base = ["--authority-check-only", "--repository-root", str(ROOT), "--contract", str(missing_contract), "--contract-sha256", "0" * 64, "--authority", str(missing_authority), "--authority-sha256", "0" * 64]
    programs = (
        ROOT / "docs/reference_cases/e4_pl_q1b_assembled_producer.py",
        ROOT / "docs/reference_cases/e4_pl_q1b_assembled_checker.py",
        ROOT / "docs/reference_cases/e4_pl_q1b_bounded_runner.py",
    )
    for program in programs:
        result = subprocess.run([sys.executable, str(program), *base], cwd=ROOT, capture_output=True, text=True, check=False, timeout=20)
        assert result.returncode == 2
        assert "PASS" not in result.stdout
    assert list(tmp_path.iterdir()) == []
    common.require_no_production_delta(ROOT, plan["base_commit"] if "base_commit" in plan else "be64f1d7f284bfa044e8dd4b40bece29e7311f44")
