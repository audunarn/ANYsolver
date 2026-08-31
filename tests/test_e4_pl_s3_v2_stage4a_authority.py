from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json"


def _reject_constant(value: str) -> None:
    raise ValueError(value)


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key: {key}")
        made[key] = value
    return made


def _canonical(value: object) -> bytes:
    def visit(item: object) -> None:
        if isinstance(item, float):
            assert math.isfinite(item)
        elif isinstance(item, list):
            for member in item:
                visit(member)
        elif isinstance(item, dict):
            for key, member in item.items():
                assert isinstance(key, str)
                visit(member)

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


@pytest.fixture(scope="module")
def authority() -> dict[str, object]:
    raw = AUTHORITY.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_constant,
    )
    assert raw == _canonical(value)
    return value


def test_stage4a_authority_binds_exact_parent_and_protocol(authority) -> None:
    assert authority["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v2"
    assert authority["parent"] == {
        "commit": "2d3c7511846485c649c47873a96cdbf039d7a406",
        "subject": "test: bind S3 V2A producer progress phases",
        "tree": "15927925b8dbaa7b0e860b811c97c46b14a30e0e",
    }
    assert authority["scope_base"] == {
        "commit": "d1f6d3d264882cc70a34b6a764476f5ec6baeb3b",
        "subject": "test: make S3 V2 evidence hashes checkout portable",
        "tree": "5fb2bfa183018e7365cb9fa5f864912fab003b97",
    }
    phase = authority["formal_phase"]
    assert phase["classifying_record_count"] == 81
    assert phase["v1_diagnostic_record_count"] == 72
    assert authority["formal_protocol"]["support"] == {
        "all_edge_translations": ["ux", "uy", "uz"],
        "constant_x_edge_rotation": "theta_y",
        "constant_y_edge_rotation": "theta_x",
        "identity": "HARD_NAVIER_TRANSLATIONS_PLUS_TANGENTIAL_ROTATIONS_V2",
    }


def test_stage4a_advisory_margins_cannot_become_scientific_no_go(authority) -> None:
    advisory = authority["advisory_policy"]
    assert advisory["classification"] == "NONCLASSIFYING_INDEPENDENT_REVIEW_TRIGGER"
    assert advisory["successor_expansion_authorized_on_trigger"] is False
    assert authority["terminals"]["formal_no_go"] == (
        "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE"
    )


def test_stage4a_authority_preserves_defaults_and_mechanics_boundaries(authority) -> None:
    assert authority["production_boundary"] == {
        "default_s3_formulation": "legacy-s3",
        "default_s3_unchanged": True,
        "q4_default": "e4-pl",
        "q4_mechanics_unchanged": True,
        "v1_fallback_forbidden": True,
    }
    extent = authority["allowed_extent"]
    assert extent["q4_or_v1_mechanics_change_authorized"] is False
    assert extent["v2_matrix_or_equation_change_authorized"] is False
    assert "src/anysolver/e4_pl_element.py" not in extent["implementation_paths"]
    assert "src/anysolver/e4_pl_s3_element.py" not in extent["implementation_paths"]
    assert "src/anysolver/boundary.py" not in extent["implementation_paths"]


def test_stage4a_authority_correction_preserves_original_and_closes_paths(authority) -> None:
    assert authority["correction"] == {
        "classification": "AUTHORITY_SCHEMA_CORRECTION_ONLY",
        "mechanics_or_protocol_changed": False,
        "prior_authority": {
            "bytes": 3726,
            "commit": "0f0979db7548cf0e715451d052fa837da61cbdf6",
            "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
            "sha256": "061BD82022D7FB6D6403057DA81389C8E59282FCD48E57CC3B2B824693AFE6B3",
            "subject": "docs: authorize S3 V2A flat mixed funnel",
            "tree": "873962fcfafbd71ff1be1240f47afa04e2acad41",
        },
        "reason": "INCOMPLETE_DOWNSTREAM_PATH_ENUMERATION",
    }
    extent = authority["allowed_extent"]
    assert set(extent["freeze_authorization_paths"]) == {
        "docs/reference_cases/e4_pl_s3_v2_stage4a_contract.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_execution_authorization.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_process_implementation_review.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_scientific_implementation_review.json",
    }
    assert set(extent["outcome_paths"]) == {
        "docs/reference_cases/e4_pl_s3_v2_stage4a_evidence.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_result.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_scientific_review.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_status.json",
        "tests/test_e4_pl_s3_v2_stage4a_closeout.py",
    }


def test_registered_parent_objects_exist_and_match(authority) -> None:
    for identity in (authority["parent"], authority["scope_base"]):
        commit = subprocess.run(
            ["git", "rev-parse", identity["commit"]],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", f"{identity['commit']}^{{tree}}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subject = subprocess.run(
            ["git", "show", "-s", "--format=%s", identity["commit"]],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert (commit, tree, subject) == (
            identity["commit"],
            identity["tree"],
            identity["subject"],
        )


def test_stage4a_authority_has_stable_identity() -> None:
    raw = AUTHORITY.read_bytes()
    assert len(raw) > 2_000
    assert len(hashlib.sha256(raw).hexdigest()) == 64
