from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "docs/reference_cases/e4_pl_q1s_reference_raw.json"


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in items:
        if key in out:
            raise ValueError(key)
        out[key] = value
    return out


def _payload() -> dict[str, object]:
    assert RAW.is_file(), "registered reference output is absent"
    value = json.loads(
        RAW.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )
    return value["certificate_payload"]


def test_q1s_actual_38_field_condensation_rank_and_rigid_modes() -> None:
    payload = _payload()
    local = payload["local_algebra"]
    assert set(local) == {
        "all_38_field_blocks_invertible", "all_condensed_rank_18",
        "all_mixed_condensed_equalities_exact", "all_psd",
        "all_six_rigid_actions_exact_zero", "all_symmetric", "quotient_rule",
        "unresolved_at_1024",
    }
    assert local["quotient_rule"] == "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE"
    for key in set(local) - {"quotient_rule"}:
        assert isinstance(local[key], bool)
    cases = payload["case_certificates"]
    for row in cases:
        certificate = row["local_algebra"]
        assert set(certificate) == {
            "field_count", "internal_invertible", "rank_18", "six_rigid_exact",
            "symmetric", "psd", "mixed_condensed_exact", "unresolved",
        }
        assert certificate["field_count"] == 38
        assert all(isinstance(certificate[key], bool) for key in set(certificate) - {"field_count"})
    contradiction = not all(
        local[key]
        for key in (
            "all_38_field_blocks_invertible", "all_condensed_rank_18",
            "all_mixed_condensed_equalities_exact", "all_psd",
            "all_six_rigid_actions_exact_zero", "all_symmetric",
        )
    )
    terminal = payload["classification"]["terminal"]
    if contradiction:
        assert terminal == "NO_GO_E4_PL_Q1S_LOCAL_ALGEBRA"
    elif local["unresolved_at_1024"]:
        assert terminal == "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY"
