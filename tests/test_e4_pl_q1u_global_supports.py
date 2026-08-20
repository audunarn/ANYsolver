from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q1u_global_transform_load_support_solution_and_reactions() -> None:
    path = ROOT / "docs/reference_cases/e4_pl_q1u_oracle_raw.json"
    assert path.is_file(), "registered oracle output is absent"
    payload = json.loads(path.read_text(encoding="utf-8"))["certificate_payload"]
    aggregate = payload["global_supports"]
    assert set(aggregate) == {"all_global_field_recovery_exact", "all_global_loads_exact", "all_global_projectors_exact", "all_global_reactions_exact", "all_global_support_solutions_exact", "all_global_supports_exact", "all_numerical_reactions_separate", "all_translation_invariant", "direct_drill_excluded", "physical_supports_only"}
    assert all(isinstance(value, bool) for value in aggregate.values())
    assert aggregate["physical_supports_only"] is True
    assert aggregate["direct_drill_excluded"] is True
    for row in payload["case_certificates"]:
        item = row["global_support"]
        assert set(item) == {"projectors_exact", "load_exact", "support_exact", "solution_exact", "reaction_exact", "recovery_exact", "numerical_separate"}
        assert all(isinstance(value, bool) for value in item.values())
