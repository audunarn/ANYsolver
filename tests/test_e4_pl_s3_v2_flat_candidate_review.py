from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs" / "reference_cases" / "e4_pl_s3_v2_flat_candidate_review.json"


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _reject_nonfinite(value: str) -> object:
    raise ValueError(f"nonfinite JSON value: {value}")


def _decode(raw: bytes) -> dict[str, object]:
    made = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_nonfinite,
    )
    assert isinstance(made, dict)
    assert raw == (
        json.dumps(made, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return made


def test_review_is_canonical_independent_empty_and_hash_bound() -> None:
    review = _decode(REVIEW.read_bytes())
    assert set(review) == {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert review["findings"] == {"P0": [], "P1": []}
    assert review["schema"] == (
        "anysolver.e4-pl-s3-v2-flat-candidate-independent-review-v1"
    )
    assert review["verdict"] == (
        "ACCEPTED_STRICT_FLAT_OPT_IN_CANDIDATE_NO_P0_P1_STAGE4_UNAUTHORIZED"
    )
    independence = review["reviewer_independence"]
    assert independence["authored_reviewed_mechanics"] is False
    assert independence["production_candidate_authored"] is False

    paths = [record["path"] for record in review["reviewed_inputs"]]
    assert len(paths) == len(set(paths))
    assert "docs/reference_cases/e4_pl_s3_v2_candidate_binding.json" in paths
    for record in review["reviewed_inputs"]:
        path = ROOT / record["path"]
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == record["sha256"]


def test_review_parser_rejects_duplicate_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        _decode(b'{"a":1,"a":2}\n')
    with pytest.raises(ValueError, match="nonfinite JSON value"):
        _decode(b'{"a":NaN}\n')
