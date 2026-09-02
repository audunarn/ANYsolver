from __future__ import annotations

import json
from pathlib import Path


REFERENCE = Path(__file__).resolve().parents[1] / "docs" / "reference_cases"


def test_canonical_result_requires_v3_without_activation() -> None:
    result_path = REFERENCE / "e4_pl_s3_v2b_interface_result.json"
    review_path = REFERENCE / "e4_pl_s3_v2b_interface_review.json"
    result = json.loads(result_path.read_text())
    review = json.loads(review_path.read_text())
    assert result_path.read_bytes() == (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert review_path.read_bytes() == (json.dumps(review, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert result["terminal"] == "UNCLASSIFIED_E4_PL_S3_V2B_FORMULATION_REPLACEMENT_REQUIRED"
    assert result["v3_preregistration_authorized"] is True
    assert result["activation_authorized"] is False
    assert result["full_stage4a_rerun_authorized"] is False
    assert result["holdouts"]["executed"] is False
    assert len({cycle["aggregate"]["sha256"] for cycle in result["cycles"]}) == 1
    assert review["findings"] == {"P0": [], "P1": []}
