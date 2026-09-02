from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"


def _canonical(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    return raw, value


def test_v5m_closeout_binds_accepted_r1_without_activation() -> None:
    result_raw, result = _canonical(REFERENCE / "e4_pl_s3_v5m_parity_result.json")
    review_raw, review = _canonical(REFERENCE / "e4_pl_s3_v5m_parity_review.json")
    _status_raw, status = _canonical(REFERENCE / "e4_pl_s3_v5m_parity_status.json")
    assert result["terminal"] == "PROVISIONAL_GO_E4_PL_S3_V5M_PARITY_CLOSED_ONLY"
    assert result["activation_authorized"] is False
    assert result["production_boundary"] == {
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }
    assert all(value == "PASS_MEASURED_REGISTERED_SCOPE" for value in result["gate_status"].values())
    assert review["findings"] == {"P0": [], "P1": []}
    assert review["verdict"] == "ACCEPT_S3_V5M_PARITY_NO_P0_P1"
    assert status["result"] == {"bytes": len(result_raw), "sha256": hashlib.sha256(result_raw).hexdigest().upper()}
    assert status["review"] == {"bytes": len(review_raw), "sha256": hashlib.sha256(review_raw).hexdigest().upper()}
    assert status["next_gate"] == "V5N_FULL_ACTIVATION_QUALIFICATION_PROTOCOL"


def test_v5m_closeout_preserves_superseded_first_evidence() -> None:
    _raw, result = _canonical(REFERENCE / "e4_pl_s3_v5m_parity_result.json")
    assert result["predecessor_evidence"] == {
        "aggregate_sha256": "0EC2BAE6AB58EE964F29275C046D525C50808C44EBA10E404E50CE3A74E7DEE4",
        "disposition": "SUPERSEDED_INSUFFICIENT_INSTALLED_SOURCE_BINDING",
        "preserved": True,
    }
