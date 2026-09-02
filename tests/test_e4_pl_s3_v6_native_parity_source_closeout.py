from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"


def _canonical(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    value = json.loads(raw)
    expected = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    assert raw == expected
    return raw, value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def test_v6_closeout_binds_byte_identical_evidence_and_review() -> None:
    result_raw, result = _canonical(REFERENCE / "e4_pl_s3_v6_native_parity_source_result.json")
    review_raw, review = _canonical(REFERENCE / "e4_pl_s3_v6_native_parity_source_review.json")
    _status_raw, status = _canonical(REFERENCE / "e4_pl_s3_v6_native_parity_source_status.json")
    assert status["result"] == {"bytes": len(result_raw), "sha256": _sha(result_raw)}
    assert status["review"] == {"bytes": len(review_raw), "sha256": _sha(review_raw)}
    assert result["cycles"] == {
        "byte_identical": True,
        "count": 2,
        "evidence_bytes": 1402,
        "evidence_sha256": "29E331FCA91D790EDBC912900EA111720C8503FF3CF999F9B248253CC7F5D264",
    }
    assert review["findings"] == {"P0": [], "P1": []}


def test_v6_closeout_authorizes_only_native_parity_implementation() -> None:
    _raw, result = _canonical(REFERENCE / "e4_pl_s3_v6_native_parity_source_result.json")
    assert result["terminal"] == "PROVISIONAL_GO_E4_PL_S3_V6_V2D_NATIVE_PARITY_IMPLEMENTATION"
    assert result["v2d_native_parity_implementation_authorized"] is True
    assert result["v2c_small_strain_operator_change_authorized"] is False
    assert result["activation_authorized"] is False
    assert result["complete_activation_execution_authorized"] is False
    assert result["next_gate"] == "V6A_V2D_NATIVE_PARITY_IMPLEMENTATION"
    assert result["production_boundary"]["default_q4_formulation"] == "e4-pl"
    assert result["production_boundary"]["default_s3_formulation"] == "legacy-s3"
    assert result["production_boundary"]["q4_mechanics_unchanged"] is True


def test_v6_authority_commit_has_exact_five_path_extent() -> None:
    import subprocess

    _raw, result = _canonical(REFERENCE / "e4_pl_s3_v6_native_parity_source_result.json")
    commit = result["authority"]["commit"]
    paths = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.splitlines()
    assert sorted(paths) == sorted(
        [
            "docs/reference_cases/e4_pl_s3_v6_native_parity_source_authority.py",
            "docs/reference_cases/e4_pl_s3_v6_native_parity_source_contract.json",
            "docs/reference_cases/e4_pl_s3_v6_native_parity_source_plan.json",
            "docs/reference_cases/e4_pl_s3_v6_native_parity_source_selection.json",
            "tests/test_e4_pl_s3_v6_native_parity_source_authority.py",
        ]
    )
