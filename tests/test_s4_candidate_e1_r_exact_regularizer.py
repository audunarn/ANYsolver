from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/reference_cases/s4_candidate_e1_r_output.json"


def _rank(matrix: list[list[Fraction]]) -> int:
    a = [row[:] for row in matrix]
    rank = 0
    for column in range(len(a[0]) if a else 0):
        pivot = next((row for row in range(rank, len(a)) if a[row][column]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scale = a[rank][column]
        a[rank] = [value / scale for value in a[rank]]
        for row in range(len(a)):
            if row != rank and a[row][column]:
                factor = a[row][column]
                a[row] = [left - factor * right for left, right in zip(a[row], a[rank])]
        rank += 1
    return rank


def _r4(c: Fraction) -> list[list[Fraction]]:
    return [[c if row == column else -c / 3 for column in range(4)] for row in range(4)]


def test_e1_r_q4_block_is_exact_psd_rank_three_without_ground_coupling() -> None:
    dmean = Fraction(sum([6, 6, 0] * 4), 12)
    c = Fraction(1, 100_000_000) * dmean
    matrix = _r4(c)
    assert dmean == 4 and c == Fraction(1, 25_000_000)
    assert _rank(matrix) == 3
    assert [sum(row) for row in matrix] == [Fraction(0)] * 4
    assert matrix[0][0] == c and matrix[0][1] == -c / 3
    for vector in ([1, -1, 0, 0], [1, 1, -1, -1], [1, -1, 1, -1]):
        image = [sum(row[i] * vector[i] for i in range(4)) for row in matrix]
        assert image == [Fraction(4, 3) * c * value for value in vector]


def test_e1_r_patch_and_constraint_gauges_are_exact() -> None:
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    gauge = output["certificate"]["gauge"]
    assert gauge["patch"] == {
        "area_weight_sum": "4",
        "area_weights": ["1/4", "1/2", "1/4", "1/2", "1", "1/2", "1/4", "1/2", "1/4"],
        "component_count": 1,
        "gauge_augmented_rank": 9,
        "rank": 8,
    }
    assert {name: record["added_gauge_rows"] for name, record in gauge["constraint_cases"].items()} == {
        "cross_component_equality": 1,
        "full_support": 0,
        "none": 2,
        "one_component_support": 1,
    }
    assert gauge["activity"]["positive_rank"] == 7
    assert gauge["activity"]["zero_rank"] == 6
    assert gauge["activity"]["scale_combined_once"] is True


def test_e1_r_static_and_buckling_physics_are_exactly_nonintrusive() -> None:
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    static = output["certificate"]["static"]
    assert static["physical_displacement"] == ["2", "3"]
    assert static["physical_recovery"] == "8"
    assert all(record["drill_solution"] == ["0", "0", "0"] for record in static["sensitivity_records"])
    assert static["host_null_tests"] == {
        "K0_Q_zero": True,
        "KG_Q_zero": True,
        "QT_f_zero": True,
        "recovery_Q_zero": True,
    }
    buckling = output["certificate"]["buckling"]
    assert buckling["finite_eigenvalues"] == ["2", "3"]
    assert buckling["e1_r_geometric_stiffness"] == "EXACTLY_ZERO"
    assert buckling["physical_residuals"] == [["0", "0"], ["0", "0"]]


def test_e1_r_mass_is_conditional_and_current_legacy_host_is_ineligible() -> None:
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    mass = output["certificate"]["mass"]
    assert mass["massless_host"]["status"] == "CONDITIONAL_MASS_PATTERN_CERTIFIED"
    assert mass["massless_host"]["rank"] == 3
    assert mass["legacy_host"]["status"] == "INELIGIBLE_EXISTING_DRILL_MASS"
    assert mass["physical_mass_properties_include_regularizer"] is False
    assert output["certificate"]["eligibility"]["current_legacy_host"]["status"] == "INELIGIBLE"
    assert output["certificate"]["separation"] == {
        "e1_a_combined_or_used": False,
        "legacy_host_modified_or_used": False,
        "rank_18_claimed": False,
        "sestra_binary_reproduction_claimed": False,
    }
