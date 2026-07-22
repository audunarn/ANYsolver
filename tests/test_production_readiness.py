"""Production-readiness artifact tests."""

from __future__ import annotations

import json
from pathlib import Path

from anysolver.production_readiness import (
    build_capability_matrix,
    build_verification_scope_statement,
    scope_statement_markdown,
    write_production_readiness_artifacts,
)


def _fake_report() -> dict:
    return {
        "release_gates": {
            "flat_thin_shell": {
                "status": "blocked",
                "blockers": [{"case_id": "SHELL-009"}],
            },
            "flat_thin_stiffened_shell": {
                "status": "blocked",
                "blockers": [{"case_id": "COUP-012"}, {"case_id": "BUC-005"}],
            },
            "curved_thin_stiffened_shell": {
                "status": "not_evaluated",
                "blockers": [],
            },
            "nonlinear_capacity": {
                "status": "blocked",
                "blockers": [{"case_id": "NLG-007"}],
            },
            "fully_documented_verified_release": {
                "status": "blocked",
                "blockers": [{"case_id": "EXT-001"}],
            },
        }
    }


def test_capability_matrix_reflects_blocked_gates() -> None:
    matrix = build_capability_matrix(_fake_report())
    by_feature = {entry.feature: entry for entry in matrix}

    assert by_feature["flat_thin_shell_linear_static_modal_buckling"].status == "not_qualified"
    assert by_feature["flat_thin_shell_linear_static_modal_buckling"].gate_blockers == ["SHELL-009"]
    assert by_feature["curved_thin_stiffened_shell"].status == "not_evaluated"
    assert by_feature["unsupported_general_purpose_fe"].status == "unsupported"


def test_scope_statement_and_artifact_writer() -> None:
    report = _fake_report()
    scope = build_verification_scope_statement(report)
    markdown = scope_statement_markdown(scope)
    output_dir = Path(".pytest_tmp_production_readiness")

    assert scope["production_release_status"] == "not_qualified"
    assert "unsupported_general_purpose_fe" in scope["unsupported"]
    assert "Follower pressure unless implemented and verified." in scope["explicit_limitations"]
    assert "Production release status: not_qualified" in markdown

    result = write_production_readiness_artifacts(output_dir, report=report)
    assert result["production_release_status"] == "not_qualified"
    matrix = json.loads((output_dir / "capability_matrix.json").read_text(encoding="utf-8"))
    scope_payload = json.loads((output_dir / "verification_scope.json").read_text(encoding="utf-8"))
    assert len(matrix) >= 5
    assert scope_payload["production_release_status"] == "not_qualified"
    assert (output_dir / "verification_scope.md").exists()
