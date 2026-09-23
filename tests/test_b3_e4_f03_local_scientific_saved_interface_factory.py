from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_saved_interface_factory as factory
from scripts import _b3_e4_f03_local_scientific_saved_storage as storage
from scripts import _b3_e4_f03_saved_interface_checks as interface


CASE = cases.CASES[0]


def _recovered():
    grid = cases.compile_case(CASE)
    q = tuple(Fraction(0) for _ in range(grid.free_dofs))
    eta = (Fraction(0), Fraction(0), Fraction(0))
    bundle = budgets.make_scientific_budgets()
    return grid, q, eta, recovery.recover(
        grid, q, eta, bundle.composition.interface_budget.recovery_budget,
    ), bundle.composition.interface_budget


def test_factory_produces_three_real_routes_and_verifier_roundtrip(monkeypatch):
    grid, q, eta, recovered, budget = _recovered()
    calls = []
    original = factory._quadrature_band

    def observed(value, left, right, order, rule):
        calls.append((left, right, order))
        return original(value, left, right, order, rule)

    monkeypatch.setattr(factory, "_quadrature_band", observed)
    saved = factory.produce_saved_interface(recovered, budget=budget)
    assert [order for _, _, order in calls] == [item for _ in interface.BANDS for item in (48, 64)]
    assert not np.shares_memory(saved.band_analytic, saved.band48)
    assert not np.shares_memory(saved.band48, saved.band64)
    checked = interface.verify_interface(grid, q, eta, saved, budget=budget)
    assert checked.status == "PASSED"
    assert checked.diagnostics["recovery_recomputations"] == 1


def test_factory_does_not_recover_assemble_factor_or_solve(monkeypatch):
    _, _, _, recovered, budget = _recovered()
    monkeypatch.setattr(
        factory.recovery, "recover", lambda *args, **kwargs: pytest.fail("recovery repeated"),
    )
    value = factory.produce_saved_interface(recovered, budget=budget)
    assert value.band48.shape == (8, 3)


def test_factory_storage_roundtrip_preserves_identity(tmp_path):
    _, _, _, recovered, budget = _recovered()
    value = factory.produce_saved_interface(recovered, budget=budget)
    path = tmp_path / "saved_interface.npz"
    storage.write_interface(path, value, CASE)
    restored = storage.read_interface(path, CASE)
    assert interface.saved_identity(restored) == interface.saved_identity(value)


def test_factory_owns_all_arrays():
    _, _, _, recovered, budget = _recovered()
    value = factory.produce_saved_interface(recovered, budget=budget)
    arrays = [
        value.density, value.cosine, value.atoms, value.band_analytic,
        value.band48, value.band64, value.line_band_analytic,
    ]
    assert not any(
        np.shares_memory(first, second)
        for index, first in enumerate(arrays)
        for second in arrays[index + 1:]
    )
    assert all(not item.flags.writeable for item in arrays)


@pytest.mark.parametrize(
    "leaf", ("max_intervals", "max_aggregate_operations", "max_aggregate_bits"),
)
def test_factory_resource_failure_precedes_numerical_observation(monkeypatch, leaf):
    _, _, _, recovered, budget = _recovered()
    rejected = replace(budget, **{leaf: 1})
    monkeypatch.setattr(
        factory, "_quadrature_band", lambda *args: pytest.fail("observation preceded preflight"),
    )
    with pytest.raises(ValueError, match="producer .* budget"):
        factory.produce_saved_interface(recovered, budget=rejected)


def test_factory_workspace_boundary_precedes_actions_and_quadrature(monkeypatch):
    _, _, _, recovered, budget = _recovered()
    _, _, required = factory._resource_requirements(recovered, budget)
    rejected = replace(budget, max_work_bytes=required - 1)
    monkeypatch.setattr(
        factory.recovery, "band", lambda *args: pytest.fail("Action work preceded preflight"),
    )
    monkeypatch.setattr(
        factory, "_quadrature_rule", lambda *args: pytest.fail("Gauss work preceded preflight"),
    )
    with pytest.raises(ValueError, match="workspace budget"):
        factory.produce_saved_interface(recovered, budget=rejected)


def test_factory_builds_each_quadrature_rule_once(monkeypatch):
    _, _, _, recovered, budget = _recovered()
    calls = []
    original = factory._quadrature_rule

    def observed(order):
        calls.append(order)
        return original(order)

    monkeypatch.setattr(factory, "_quadrature_rule", observed)
    factory.produce_saved_interface(recovered, budget=budget)
    assert calls == [48, 64]


def test_factory_enforces_nested_action_total_bits_before_decimal_display(monkeypatch):
    _, _, _, recovered, budget = _recovered()
    action = replace(budget.action_budget, max_total_bits=1)
    rejected = replace(budget, action_budget=action)
    monkeypatch.setattr(
        factory, "_display",
        lambda *args: pytest.fail("decimal display preceded nested Action admission"),
    )
    with pytest.raises(ValueError, match="nested Action total-bit budget"):
        factory.produce_saved_interface(recovered, budget=rejected)


def test_factory_rejects_wrong_input_before_observation(monkeypatch):
    _, _, _, _, budget = _recovered()
    monkeypatch.setattr(
        factory, "_quadrature_band", lambda *args: pytest.fail("invalid input reached observation"),
    )
    with pytest.raises(ValueError, match="owned Recovery"):
        factory.produce_saved_interface(object(), budget=budget)
