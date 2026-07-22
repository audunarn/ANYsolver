"""Manifest-driven beam/shell verification report tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from anysolver import run_beam_shell_verification, verification_manifest_cases, write_beam_shell_verification_report


def test_manifest_contains_stable_case_ids_from_spec() -> None:
    cases = verification_manifest_cases()
    ids = {case.case_id for case in cases}

    assert len(cases) == 130
    assert "META-001" in ids
    assert "ALG-001" in ids
    assert "BEAM-010" in ids
    assert "BEAM-011" in ids
    assert "SHELL-008" in ids
    assert "SHELL-011" in ids
    assert "SHELL-007" in ids
    assert "COUP-005" in ids
    assert "COUP-011" in ids
    assert "COUP-014" in ids
    assert "COUP-016" in ids
    assert "MAT-007" in ids
    assert "PERF-002" in ids
    assert "EIG-005" in ids
    assert "COUP-019" in ids
    assert "MLBC-001" in ids
    assert "MLBC-009" in ids
    assert "CONTACT-001" in ids
    assert "CONTACT-006" in ids
    assert "CONTACT-012" in ids
    assert "FRACT-001" in ids
    assert "FRACT-012" in ids
    assert "CYL-003" in ids
    assert "NLG-008" in ids
    assert "DYN-001" in ids
    assert "EXT-002" in ids
    assert "VVR-001" in ids


def test_beam_shell_verification_report_separates_pass_and_xfail() -> None:
    report = run_beam_shell_verification()

    assert report["status"] == "passed"
    assert report["test_execution_status"] == "passed"
    assert report["verification_completion_status"] == "complete"
    assert report["release_gate_status"] == "passed"
    assert "verification_programme" in report
    assert "V1" in report["verification_programme"]["batches"]
    assert "fully_documented_verified_release" in report["release_gates"]
    assert report["counts"]["PASS"] >= 35
    assert report["counts"]["XFAIL"] >= 1
    assert report["required_failures"] == []
    statuses = {item["case_id"]: item["status"] for item in report["results"]}
    semantics = {item["case_id"]: item for item in report["results"]}
    assert statuses["META-001"] == "PASS"
    assert semantics["META-001"]["batch"] == "V1"
    assert semantics["META-001"]["evidence_type"] == "invariant"
    assert "solver_commit" in semantics["META-001"]
    assert statuses["ALG-001"] == "PASS"
    assert statuses["BEAM-001"] == "PASS"
    assert statuses["SHELL-005"] == "PASS"
    assert statuses["COUP-007"] == "PASS"
    assert statuses["SHELL-008"] == "PASS"
    assert statuses["BUC-005"] == "PASS"
    assert statuses["BENCH-002"] == "PASS"
    assert statuses["COUP-014"] == "PASS"
    assert statuses["COUP-015"] == "PASS"
    assert statuses["COUP-016"] == "PASS"
    assert statuses["COUP-017"] == "PASS"
    assert statuses["EIG-005"] == "PASS"
    assert statuses["PERF-001"] == "PASS"
    assert statuses["PERF-002"] == "PASS"
    assert statuses["MLBC-001"] == "PASS"
    assert statuses["MLBC-009"] == "PASS"
    assert statuses["CONTACT-001"] == "PASS"
    assert statuses["CONTACT-006"] == "PASS"
    assert statuses["CONTACT-012"] == "PASS"
    assert statuses["FRACT-001"] == "PASS"
    assert statuses["FRACT-012"] == "PASS"
    assert semantics["COUP-014"]["test_execution_status"] == "passed"
    assert semantics["COUP-014"]["verification_completion_status"] == "complete"
    assert semantics["COUP-014"]["checks"]["rows"]
    assert report["release_gates"]["thin_stiffened_shell"]["status"] == "passed"
    assert report["release_gates"]["thin_stiffened_shell"]["alias_for"] == "flat_thin_stiffened_shell"
    assert report["release_gates"]["flat_thin_stiffened_shell"]["status"] == "passed"
    assert report["release_gates"]["flat_thin_shell"]["status"] == "passed"
    assert report["release_gates"]["mesh_load_bc"]["status"] == "passed"
    assert report["release_gates"]["contact"]["status"] == "passed"
    assert report["release_gates"]["simplified_fracture"]["status"] == "passed"
    assert report["release_gates"]["thin_stiffened_shell"]["release_gate_status"] == "passed"
    assert report["release_gates"]["thin_stiffened_shell"]["verification_completion_status"] == "complete"
    blocker_ids = {item["case_id"] for item in report["release_gates"]["thin_stiffened_shell"]["blockers"]}
    assert blocker_ids == set()
    curved_blocker_ids = {item["case_id"] for item in report["release_gates"]["curved_thin_stiffened_shell"]["blockers"]}
    assert curved_blocker_ids == set()
    assert report["release_gates"]["curved_thin_stiffened_shell"]["status"] == "passed"


def test_beam_shell_verification_report_writer_and_cli() -> None:
    output_dir = Path(".pytest_tmp_beam_shell_verification")
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "beam_shell_verification.json"
    markdown = output_dir / "beam_shell_verification.md"

    report = write_beam_shell_verification_report(output, markdown=markdown, selected_ids=["ALG-001", "BENCH-001"])

    assert report["status"] == "passed"
    assert output.exists()
    assert markdown.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert [item["case_id"] for item in payload["results"]] == ["ALG-001", "BENCH-001"]

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_beam_shell_verification.py",
            "--output",
            str(output_dir / "cli.json"),
            "--markdown",
            str(output_dir / "cli.md"),
            "--case-id",
            "ALG-001",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
