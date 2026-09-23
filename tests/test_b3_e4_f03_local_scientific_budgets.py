from dataclasses import replace

import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_cases as cases


def test_canonical_budget_contract_is_complete_stable_and_archive_bound():
    value = budgets.make_scientific_budgets()
    assert budgets.require_scientific_budgets(value) is value
    contract = budgets.resource_contract()
    assert len(contract) == len({name for name, _ in contract})
    assert all(name.startswith('adjudication_') and type(number) is int and number > 0
               for name, number in contract)
    assert archive.resource_contract() == cases.resource_contract() + contract
    records = cases.preflight_inventory()
    plan = archive.make_case_plan(records[-1], records, 'a' * 40)
    assert plan.resource_limits == archive.resource_contract()


def test_budget_mutation_is_not_canonical_and_plan_rejects_it():
    value = budgets.make_scientific_budgets()
    changed_binding = replace(
        value.binding, max_combined_nnz=value.binding.max_combined_nnz + 1,
    )
    changed = replace(value, binding=changed_binding)
    with pytest.raises(ValueError, match='canonical'):
        budgets.require_scientific_budgets(changed)
    records = cases.preflight_inventory()
    plan = archive.make_case_plan(records[0], records, 'a' * 40)
    with pytest.raises(ValueError, match='invalid F03 case archive plan'):
        replace(
            plan,
            resource_limits=plan.resource_limits[:-1]
            + ((plan.resource_limits[-1][0], plan.resource_limits[-1][1] + 1),),
        )


def test_all_five_topology_known_replay_preflights_pass_exact_caps():
    value = budgets.make_scientific_budgets()
    records = budgets.preflight_inventory(value)
    assert tuple(record.case_id for record in records) == tuple(
        case.case_id for case in cases.CASES
    )
    largest = next(record for record in records if record.case_id == 'Q1_L2')
    assert largest.physical_dofs == budgets.MAX_PHYSICAL_DOFS == 1470
    assert largest.station_intervals == budgets.MAX_INTERVALS == 47
    assert largest.virtual_tests == budgets.MAX_VIRTUAL_TESTS == 426
    assert largest.work_comparisons == budgets.MAX_WORK_COMPARISONS == 2606
    assert largest.recovery_operations == 2_217_853_440
    assert largest.support_symbolic_bits == 555_163_648
    assert largest.trace_input_nnz_upper == 129_360
