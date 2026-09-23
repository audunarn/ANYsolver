from fractions import Fraction
from dataclasses import replace

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
    resources = dict(scientific.resource_contract())
    assert resources["raw_archive_bytes"] == 512 * 1024**2
    assert resources["evidence_index_bytes"] == 1024**2
    assert resources["case_receipt_bytes"] == 1024**2
    assert resources["inverse_index_bytes"] == 1024**2
    assert resources["numerical_index_bytes"] == 1024**2
    assert resources["factor_validation_max_work_bytes"] == (
        128 * 2_162_370 + 128 * (1_470 + 1_470 + 2) + 256 * 1_470
    ) == 277_536_256
    assert resources["max_kkt_factor_nnz"] == 1_473 * 1_474


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


def test_preflight_is_factory_owned_and_fabricated_observations_are_rederived():
    records = scientific.preflight_inventory()
    with pytest.raises(TypeError):
        scientific.CasePreflight(
            scientific.SCHEMA, records[0].case, "0" * 64, 1, 1, 1, 1,
        )
    with pytest.raises(TypeError):
        replace(records[0], topology_sha256="0" * 64)
    forged = object.__new__(scientific.CasePreflight)
    for field in records[0].__dataclass_fields__:
        object.__setattr__(forged, field, getattr(records[0], field))
    object.__setattr__(forged, "topology_sha256", "0" * 64)
    object.__setattr__(forged, "graph_storage_bound_bytes", 1)
    with pytest.raises(ValueError, match="fabricated"):
        scientific.inventory_sha256((forged, *records[1:]))


def test_resource_contract_is_bound_by_inventory_hash(monkeypatch):
    records = scientific.preflight_inventory()
    original = scientific.inventory_sha256(records)
    altered = scientific.assembly.AssemblyBudget(
        scientific.ASSEMBLY_BUDGET.max_trace_dofs,
        scientific.ASSEMBLY_BUDGET.max_triplets,
        scientific.ASSEMBLY_BUDGET.max_work_bytes + 1,
        scientific.ASSEMBLY_BUDGET.max_trace_integer_bits,
    )
    monkeypatch.setattr(scientific, "ASSEMBLY_BUDGET", altered)
    altered_hash = scientific.inventory_sha256(records)
    assert original != altered_hash
    assert altered_hash == scientific.inventory_sha256(scientific.preflight_inventory())


def test_preflight_is_topology_only(monkeypatch):
    import scripts._b3_e4_f03_local_primal_assembly as assembly

    monkeypatch.setattr(assembly, "assemble", lambda *a, **k: pytest.fail("must not assemble"))
    records = scientific.preflight_inventory()
    assert len(records) == 5
