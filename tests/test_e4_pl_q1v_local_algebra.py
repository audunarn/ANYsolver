from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, object]:
    path = ROOT / "docs/reference_cases/e4_pl_q1v_reference_raw.json"
    assert path.is_file(), "registered reference output is absent"
    return json.loads(path.read_text(encoding="utf-8"))["certificate_payload"]


def test_q1v_actual_38_field_condensation_rank_and_rigid_modes() -> None:
    payload = _payload()
    local = payload["local_algebra"]
    assert local["quotient_rule"] == "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE"
    assert set(local) == {"all_38_field_blocks_invertible", "all_condensed_rank_18", "all_mixed_condensed_equalities_exact", "all_psd", "all_six_rigid_actions_exact_zero", "all_symmetric", "quotient_rule", "unresolved_at_1024"}
    for row in payload["case_certificates"]:
        item = row["local_algebra"]
        assert set(item) == {"field_count", "internal_invertible", "rank_18", "six_rigid_exact", "symmetric", "psd", "mixed_condensed_exact", "unresolved"}
        assert item["field_count"] == 38
        assert all(isinstance(value, bool) for key, value in item.items() if key != "field_count")
    failed = not all(local[key] for key in ("all_38_field_blocks_invertible", "all_condensed_rank_18", "all_mixed_condensed_equalities_exact", "all_psd", "all_six_rigid_actions_exact_zero", "all_symmetric"))
    terminal = payload["classification"]["terminal"]
    if failed:
        assert terminal == "NO_GO_E4_PL_Q1V_LOCAL_ALGEBRA"
    elif local["unresolved_at_1024"]:
        assert terminal == "UNCLASSIFIED_E4_PL_Q1V_LOCAL_PLANAR_IDENTITY"
