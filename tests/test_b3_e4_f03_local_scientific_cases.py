from fractions import Fraction

import pytest

from scripts import _b3_e4_f03_local_scientific_cases as scientific
from scripts import _b3_e4_f03_spatial_contract as contract


def test_exact_five_case_inventory_and_resource_arithmetic():
    records = scientific.preflight_inventory()
    assert tuple(record.case.case_id for record in records) == (
        "Q1_L0", "Q1_L1", "Q1_L2", "Q2_L0", "Q2_L1",
    )
    assert tuple(record.case.assembly_triplets for record in records) == (
        12_112, 112_656, 1_045_600, 75_492, 852_000,
    )
    assert sum(record.case.inverse_evidence_bytes for record in records) == 37_068_136
    assert max(record.case.inverse_evidence_bytes for record in records) == 17_357_832
    assert all(record.case.kkt_order <= scientific.SYSTEM_BUDGET.max_order for record in records)
    assert all(record.case.kkt_nnz <= scientific.SYSTEM_BUDGET.max_nnz for record in records)
    assert len(scientific.inventory_sha256(records)) == 64


def test_exact_midpoint_refinement_is_nested_and_does_not_alias_input():
    source = tuple(contract.X_CUTS)
    first = scientific.midpoint_refine(source, 1)
    second = scientific.midpoint_refine(source, 2)
    assert source is not first and first is not second
    assert len(first) == 2 * len(source) - 1
    assert len(second) == 2 * len(first) - 1
    assert all(value in first for value in source)
    assert all(value in second for value in first)
    assert all(type(value) is Fraction for value in second)


@pytest.mark.parametrize("cuts,level", [
    ([Fraction(0), Fraction(1)], 0),
    ((Fraction(0), Fraction(0)), 0),
    ((Fraction(0), Fraction(1)), True),
    ((Fraction(0), Fraction(1)), 3),
])
def test_invalid_refinement_rejected(cuts, level):
    with pytest.raises(ValueError):
        scientific.midpoint_refine(cuts, level)


def test_stale_reordered_or_partial_inventory_cannot_be_hashed():
    records = scientific.preflight_inventory()
    for invalid in (records[:-1], tuple(reversed(records))):
        with pytest.raises(ValueError):
            scientific.inventory_sha256(invalid)
    with pytest.raises(ValueError):
        scientific.case_by_id("Q2_L2")


def test_preflight_is_topology_only(monkeypatch):
    import scripts._b3_e4_f03_local_primal_assembly as assembly

    monkeypatch.setattr(assembly, "assemble", lambda *a, **k: pytest.fail("must not assemble"))
    records = scientific.preflight_inventory()
    assert len(records) == 5
