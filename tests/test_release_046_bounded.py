"""Bounded ANYsolver 0.4.6 compatibility-release guards."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from anysolver import __version__, b3_ge
from anysolver.elements import QuadraticBeamElement, create_element
from scripts import verify_release_046 as gate


ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_and_g7_boundary_are_exact() -> None:
    assert __version__ == gate.VERSION == "0.4.6"
    records = gate._validate_g7()
    assert set(records) == {"confirmation", "contract", "review", "status"}
    assert b3_ge.SELECTOR == "b3-ge"
    assert b3_ge.NAME == "B3-GE"
    assert type(create_element("quadratic_beam", 1, [1, 2, 3])) is QuadraticBeamElement
    with pytest.raises(ValueError, match="Unknown element type"):
        create_element("b3-ge", 2, [1, 2, 3])


def test_release_archive_contains_only_current_user_documents() -> None:
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8").splitlines()
    included_docs = {
        line.removeprefix("include ")
        for line in manifest
        if line.startswith("include docs/")
    }
    assert included_docs == gate.RELEASE_DOCS
    assert {
        "prune docs",
        "prune reports",
        "prune scripts",
        "prune tests",
    } <= set(manifest)


def test_cleanup_retains_only_referenced_authority_plans() -> None:
    plans = sorted((ROOT / "docs/agent_plans").glob("*.md"))
    assert len(plans) == 121
    assert (
        ROOT
        / "docs/agent_plans/NONLINEAR_NONFOLLOWER_SHARED_HOTSPOT_GATE.md"
    ).is_file()
    assert (ROOT / "docs/agent_plans/S3_E4_PL_V6W_FINAL_QUALIFICATION_PLAN.md").is_file()
    assert (ROOT / "docs/agent_plans/S4_E4_PL_Q1V_LOCAL_COMPLETION_PLAN.md").is_file()
    assert (ROOT / "docs/agent_plans/GE_BEAM3_VARIATIONAL_SHELL_MAP.md").is_file()
    assert not (ROOT / "docs/agent_plans/GE_BEAM3_ACTIVE_PLASTIC_ARC_SMOKE.md").exists()


@pytest.mark.parametrize(
    "payload, message",
    (
        ('{"a":1,"a":2}\n', "duplicate JSON key"),
        ('{"a":NaN}\n', "nonfinite JSON value"),
        ('{"b":1,"a":2}\n', "not canonical"),
    ),
)
def test_strict_json_rejects_malformed_evidence(tmp_path: Path, payload: str, message: str) -> None:
    path = tmp_path / "record.json"
    path.write_text(payload, encoding="ascii")
    with pytest.raises(gate.GateError, match=message):
        gate._strict_json(path)


def test_publish_workflow_uses_bounded_gate_before_upload() -> None:
    workflow = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    command = "python scripts/verify_release_046.py"
    upload = "name: python-package-distributions"
    assert workflow.count(command) == 1
    assert workflow.index(command) < workflow.index(upload)
    assert "--wheel dist/anysolver-0.4.6-py3-none-any.whl" in workflow
    assert "--sdist dist/anysolver-0.4.6.tar.gz" in workflow
    assert "--expected-commit ${{ github.sha }}" in workflow


def test_installed_probe_installs_declared_runtime_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "-c" in command:
            payload = {
                "dependencies": {
                    "ANYfileio": "0.3.2",
                    "ANYgeometry": "0.4.3",
                    "ANYmaterial": "0.2.0",
                    "ANYmesher": "0.5.0",
                },
                "installed_origin": True,
                "legacy_b3_default": True,
                "name": "B3-GE",
                "selector": "b3-ge",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    assert gate._installed_probe(tmp_path / "anysolver-0.4.6-py3-none-any.whl")[
        "legacy_b3_default"
    ]
    assert calls[0][1:5] == ["-m", "pip", "install", "--disable-pip-version-check"]
    assert "--no-deps" not in calls[0]
    assert "--target" in calls[0]


def test_release_gate_result_serializes_without_nonfinite_values() -> None:
    sample = {
        "schema": "ANYSOLVER_0_4_6_BOUNDED_COMPATIBILITY_RELEASE_GATE_V1",
        "terminal": gate.TERMINAL,
    }
    assert json.dumps(sample, sort_keys=True, separators=(",", ":"), allow_nan=False)
