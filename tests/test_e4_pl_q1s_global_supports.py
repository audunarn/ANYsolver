from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "docs/reference_cases/e4_pl_q1s_oracle_raw.json"


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError(key)
        result[key] = value
    return result


def test_q1s_global_transform_load_support_solution_and_reactions() -> None:
    assert RAW.is_file(), "registered oracle output is absent"
    wrapper = json.loads(
        RAW.read_text(encoding="utf-8"),
        object_pairs_hook=_unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )
    payload = wrapper["certificate_payload"]
    global_supports = payload["global_supports"]
    assert set(global_supports) == {
        "all_global_field_recovery_exact", "all_global_loads_exact",
        "all_global_projectors_exact", "all_global_reactions_exact",
        "all_global_support_solutions_exact", "all_global_supports_exact",
        "all_numerical_reactions_separate", "all_translation_invariant",
        "direct_drill_excluded", "physical_supports_only",
    }
    assert all(isinstance(value, bool) for value in global_supports.values())
    for row in payload["case_certificates"]:
        certificate = row["global_support"]
        assert set(certificate) == {
            "projectors_exact", "load_exact", "support_exact", "solution_exact",
            "reaction_exact", "recovery_exact", "numerical_separate",
        }
        assert all(isinstance(value, bool) for value in certificate.values())
    passed = all(global_supports.values())
    if not passed:
        assert payload["classification"]["terminal"] in {
            "NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE",
            "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY",
        }
    assert global_supports["physical_supports_only"] is True
    assert global_supports["direct_drill_excluded"] is True
