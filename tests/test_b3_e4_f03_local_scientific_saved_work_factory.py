from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_saved_storage as storage
from scripts import _b3_e4_f03_local_scientific_saved_work_factory as factory
from scripts import _b3_e4_f03_saved_work_checks as work


CASE = cases.CASES[0]


def _case():
    grid = cases.compile_case(CASE)
    q = tuple(Fraction(0) for _ in range(grid.free_dofs))
    eta = (Fraction(0), Fraction(0), Fraction(0))
    budget = budgets.make_scientific_budgets().composition.work_budget
    recovered = recovery.recover(grid, q, eta, budget.support_budget.recovery_budget)
    return grid, q, eta, recovered, budget


def test_factory_uses_one_support_and_one_quadrature_rule(monkeypatch):
    grid, _, _, recovered, budget = _case()
    support_calls = []
    rule_calls = []
    original_support = factory.support.support_recovery
    original_rule = factory._quadrature_rule

    def observed_support(*args, **kwargs):
        support_calls.append(1)
        return original_support(*args, **kwargs)

    def observed_rule():
        rule_calls.append(1)
        return original_rule()

    monkeypatch.setattr(factory.support, "support_recovery", observed_support)
    monkeypatch.setattr(factory, "_quadrature_rule", observed_rule)
    result = factory.produce_saved_work(grid, recovered, budget=budget)
    assert type(result.support) is factory.support.SupportResult
    assert support_calls == [1]
    assert rule_calls == [1]


def test_factory_storage_and_verifier_roundtrip(tmp_path):
    grid, q, eta, recovered, budget = _case()
    result = factory.produce_saved_work(grid, recovered, budget=budget)
    path = tmp_path / "saved_work.npz"
    storage.write_work(path, result.saved, CASE)
    restored = storage.read_work(path, CASE)
    assert work.input_identity(grid, recovered, restored) == work.input_identity(
        grid, recovered, result.saved,
    )
    checked = work.verify_work(grid, q, eta, restored, budget=budget)
    assert all(
        item["status"] == "PASSED"
        for name, item in checked["comparisons"].items()
        if "/saved" in name or name.startswith(("shell_work/", "interface_work/", "edge_route"))
    )


@pytest.mark.parametrize(
    "leaf", ("max_virtual_tests", "max_aggregate_operations", "max_aggregate_bits"),
)
def test_factory_resource_failure_precedes_support_and_quadrature(monkeypatch, leaf):
    grid, _, _, recovered, budget = _case()
    rejected = replace(budget, **{leaf: 1})
    monkeypatch.setattr(
        factory.support, "support_recovery",
        lambda *args: pytest.fail("support work preceded preflight"),
    )
    monkeypatch.setattr(
        factory, "_quadrature_rule",
        lambda: pytest.fail("quadrature work preceded preflight"),
    )
    with pytest.raises(ValueError, match="saved-work .*budget"):
        factory.produce_saved_work(grid, recovered, budget=rejected)


def test_factory_workspace_boundary_precedes_support(monkeypatch):
    grid, _, _, recovered, budget = _case()
    _, _, _, required = factory._resource_requirements(grid, recovered, budget)
    rejected = replace(budget, max_work_bytes=required - 1)
    monkeypatch.setattr(
        factory.support, "support_recovery",
        lambda *args: pytest.fail("support work preceded workspace preflight"),
    )
    with pytest.raises(ValueError, match="workspace budget"):
        factory.produce_saved_work(grid, recovered, budget=rejected)


def test_factory_enforces_nested_action_bits_before_display(monkeypatch):
    grid, _, _, recovered, budget = _case()
    action = replace(budget.action_budget, max_total_bits=1)
    rejected = replace(budget, action_budget=action)
    monkeypatch.setattr(
        factory, "_display",
        lambda *args: pytest.fail("display preceded nested Action admission"),
    )
    with pytest.raises(ValueError, match="nested Action total-bit budget"):
        factory.produce_saved_work(grid, recovered, budget=rejected)


@pytest.mark.parametrize(
    "leaf,match", (
        ("max_intervals", "interval"),
        ("max_operations", "operation"),
        ("max_work_bytes", "workspace"),
    ),
)
def test_factory_enforces_nested_action_work_before_display(monkeypatch, leaf, match):
    grid, _, _, recovered, budget = _case()
    action = replace(budget.action_budget, **{leaf: 1})
    rejected = replace(budget, action_budget=action)
    monkeypatch.setattr(
        factory, "_display",
        lambda *args: pytest.fail("display preceded nested Action work admission"),
    )
    with pytest.raises(ValueError, match=f"nested Action {match} budget"):
        factory.produce_saved_work(grid, recovered, budget=rejected)


def test_factory_rejects_underflowed_lift_coefficient(monkeypatch):
    grid, _, _, recovered, budget = _case()
    original_support = factory.support.support_recovery
    original_lift = factory.support.lift_pose

    def tiny_lift(*args, **kwargs):
        rows = [[list(polynomial) for polynomial in row]
                for row in original_lift(*args, **kwargs)]
        rows[0][0][0] = Fraction(1, 10**400)
        return tuple(tuple(tuple(polynomial) for polynomial in row) for row in rows)

    def supported(*args, **kwargs):
        result = original_support(*args, **kwargs)
        monkeypatch.setattr(factory.support, "lift_pose", tiny_lift)
        return result

    monkeypatch.setattr(factory.support, "support_recovery", supported)
    with pytest.raises(ValueError, match="underflowed saved-work lift coefficient"):
        factory.produce_saved_work(grid, recovered, budget=budget)


def test_factory_returns_owned_immutable_saved_arrays():
    grid, _, _, recovered, budget = _case()
    value = factory.produce_saved_work(grid, recovered, budget=budget).saved
    arrays = tuple(getattr(value, name) for name in (
        "lift_coefficients", "shell_work", "interface_work", "edge_route1",
        "edge_route2", "first_free", "shift_delta", "virtual_terms",
        "virtual_defects",
    ))
    assert all(not item.flags.writeable for item in arrays)
    assert not any(
        np.shares_memory(first, second)
        for index, first in enumerate(arrays)
        for second in arrays[index + 1:]
    )
