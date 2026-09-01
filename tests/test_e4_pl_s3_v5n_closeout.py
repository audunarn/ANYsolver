from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"


def _load(name: str) -> tuple[bytes, dict]:
    raw = (REFERENCE / name).read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    return raw, value


def test_v5n_closeout_routes_to_source_selection_without_activation() -> None:
    result_raw, result = _load("e4_pl_s3_v5n_activation_audit_result.json")
    review_raw, review = _load("e4_pl_s3_v5n_activation_audit_review.json")
    _status_raw, status = _load("e4_pl_s3_v5n_activation_audit_status.json")
    assert result["terminal"] == "UNCLASSIFIED_E4_PL_S3_V5N_NATIVE_PARITY_SOURCE_REQUIRED"
    assert result["activation_authorized"] is False
    assert result["qualified_gate_count"] == 8
    assert result["required_gate_count"] == 20
    assert len(result["missing_gate_ids"]) == 12
    assert review["findings"] == {"P0": [], "P1": []}
    assert review["conclusions"]["v6_source_selection_authorized"] is True
    assert status["result"] == {"bytes": len(result_raw), "sha256": hashlib.sha256(result_raw).hexdigest().upper()}
    assert status["review"] == {"bytes": len(review_raw), "sha256": hashlib.sha256(review_raw).hexdigest().upper()}
    assert status["next_gate"] == "V6_NATIVE_PARITY_SOURCE_SELECTION"
