from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from anysolver.e4_pl_s3_element import (
    BUBBLE_OFFSET_D,
    FORMULATION_ID,
    MITC3_PLUS_SOURCE_BYTES,
    MITC3_PLUS_SOURCE_SHA256,
    QUADRATURE_ID,
    TRIANGLE_QUADRATURE,
    TYING_POINTS,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/reference_cases/e4_pl_s3_formulation_contract.json"


def _reject_constant(value: str):
    raise ValueError(f"non-finite JSON constant {value}")


def _contract() -> dict:
    raw = CONTRACT_PATH.read_bytes()
    assert raw.endswith(b"\n")
    return json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)


def test_contract_binds_the_exact_public_source_and_candidate() -> None:
    contract = _contract()
    primary = contract["source_authority"]["primary"]

    assert contract["schema"] == "anysolver.e4-pl-s3-formulation-contract-v1"
    assert contract["candidate_id"] == FORMULATION_ID
    assert primary["bytes"] == MITC3_PLUS_SOURCE_BYTES == 1_146_142
    assert primary["sha256"] == MITC3_PLUS_SOURCE_SHA256
    assert contract["formulation"]["bubble_offset_d"] == "1/10000"
    assert BUBBLE_OFFSET_D == pytest.approx(1.0e-4, rel=0.0, abs=0.0)


def test_tying_points_and_quadrature_are_transcribed_without_aliases() -> None:
    contract = _contract()
    assert set(TYING_POINTS) == {"A", "B", "C", "D", "E", "F"}
    assert TYING_POINTS["A"] == pytest.approx((1.0 / 6.0, 2.0 / 3.0))
    assert TYING_POINTS["F"] == pytest.approx(
        (1.0 / 3.0 + 1.0e-4, 1.0 / 3.0 + 1.0e-4)
    )
    assert contract["quadrature"]["stiffness"]["id"].startswith("DUNAVANT_DEGREE_5")
    assert QUADRATURE_ID == "dunavant_degree5_7point"
    assert len(TRIANGLE_QUADRATURE) == 7
    assert sum(weight for _r, _s, weight in TRIANGLE_QUADRATURE) == pytest.approx(0.5)


def test_pl_and_rank_contract_are_exactly_frozen() -> None:
    contract = _contract()
    pl = contract["pl_completion"]
    ranks = contract["rank_contract"]

    assert pl["one_point_centroid_integration"] == "FORBIDDEN"
    assert pl["saddle_tau_tau"] == "-M/kD"
    assert ranks["uncondensed_physical_17"] == {
        "inertia_negative": 0,
        "inertia_positive": 11,
        "inertia_zero": 6,
        "nullity": 6,
        "rank": 11,
    }
    assert ranks["condensed_external_18"] == {"nullity": 6, "rank": 12}
    assert ranks["full_saddle_23"] == {
        "inertia_negative": 3,
        "inertia_positive": 14,
        "inertia_zero": 6,
        "nullity": 6,
        "rank": 17,
    }
    assert contract["serialization_fingerprint"] == {
        "bubble_convention": "hierarchical_rotation_relative_to_corner_average",
        "dynamic_reduction_policy": "GUYAN_STATIC_BUBBLE_FULL_CONSISTENT_MASS_V1",
        "formulation_id": FORMULATION_ID,
        "formulation_schema": "anysolver.e4_pl_s3.linear.v1",
        "quadrature_id": "dunavant_degree5_7point",
        "state_layout_id": "S3_EXTERNAL18_BUBBLE2_PL3_LINEAR_V1",
    }


def test_quadrature_decimal_authority_integrates_reference_area() -> None:
    contract = _contract()
    rows = contract["quadrature"]["stiffness"]["points_r_s_weight"]
    total = sum(Decimal(row[2]) for row in rows)
    assert abs(total - Decimal("0.5")) <= Decimal("2e-15")
    for r_text, s_text, weight_text in rows:
        r = Decimal(r_text)
        s = Decimal(s_text)
        weight = Decimal(weight_text)
        assert r >= 0 and s >= 0 and r + s <= Decimal(1) + Decimal("1e-15")
        assert weight > 0
