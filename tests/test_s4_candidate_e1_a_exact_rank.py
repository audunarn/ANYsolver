from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "docs/reference_cases/s4_candidate_e1_a_oracle.py"
CASES = ROOT / "docs/reference_cases/s4_candidate_e1_a_cases.json"
OUTPUT = ROOT / "docs/reference_cases/s4_candidate_e1_a_output.json"


def _namespace() -> dict[str, object]:
    return runpy.run_path(str(ORACLE))


def test_e1_a_serendipity_edge_trace_is_unique_and_q2_is_not() -> None:
    ns = _namespace()
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    certificate = ns["_certificate"](cases)
    assert len(certificate["s2_edges"]) == 4
    assert all(record["rank"] == 8 and record["equations"] == 12 for record in certificate["s2_edges"])
    assert certificate["q2_extension"] == {
        "nullity": 1,
        "rank": 8,
        "status": "EXCLUDED_BY_MINIMAL_S2_REGISTRATION",
    }
    assert certificate["edge_coefficient_solution"] == ["-1/8", "1/8"]


def test_e1_a_cyclic_incidence_has_exact_common_drill_kernel() -> None:
    ns = _namespace()
    rank = ns["_rank"]
    incidence = [
        [Fraction(-1), Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(-1), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(-1), Fraction(1)],
        [Fraction(1), Fraction(0), Fraction(0), Fraction(-1)],
    ]
    common = [Fraction(1)] * 4
    assert rank(incidence) == 3
    assert [sum(row[col] * common[col] for col in range(4)) for row in incidence] == [Fraction(0)] * 4
    assert ns["_rigid_and_g_rank"]([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]) == 7


def test_e1_a_rank_bound_is_material_and_quadrature_independent() -> None:
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    theorem = output["certificate"]["rank_theorem"]
    assert theorem == {
        "augmented_rigid_common_drill_rank": 7,
        "core_rank_upper_bound": 14,
        "full_rank_upper_bound": 17,
        "required_rank": 18,
    }
    assert len(output["certificate"]["d4_numbering_covariance"]) == 8
    assert all(record["shared_rowspace_rank"] == 3 for record in output["certificate"]["d4_numbering_covariance"])
    assert output["certificate"]["null_inheritance"] == {
        "condensed_common_column": ["0", "0", "0"],
        "mass_gram_common_column": ["0", "0", "0", "0"],
        "premise_B_common": ["0"],
        "premise_H_common": ["0", "0"],
        "status": "EXACT_ZERO_FACTOR_INFERENCE",
    }
    assert output["candidate_terminal"] == "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY"
    assert output["reason"] == "COMMON_DRILL_NULL_RANK_AT_MOST_17"
    assert output["e1_r_combined_or_used"] is False
