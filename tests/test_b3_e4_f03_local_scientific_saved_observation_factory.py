from dataclasses import replace
from fractions import Fraction

import pytest

from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_result_storage as result_storage
from scripts import _b3_e4_f03_local_scientific_saved_observation_factory as factory
from scripts import _b3_e4_f03_local_scientific_saved_storage as storage
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_work_checks as work


CASE = cases.CASES[0]


def _inputs():
    grid = cases.compile_case(CASE)
    q = tuple(Fraction(0) for _ in range(grid.free_dofs))
    eta = (Fraction(0), Fraction(0), Fraction(0))
    budget = budgets.make_scientific_budgets().composition
    return grid, q, eta, budget


def test_factory_uses_expected_bounded_work_counts(monkeypatch):
    grid, q, eta, budget = _inputs()
    recoveries = []
    supports = []
    norms = []
    original_recover = recovery.recover
    original_support = factory.work_factory.support.support_recovery
    original_norm = factory.norm_factory.functional.norm_observation_at_order

    def observed_recover(*args, **kwargs):
        recoveries.append(1)
        return original_recover(*args, **kwargs)

    def observed_support(*args, **kwargs):
        supports.append(1)
        return original_support(*args, **kwargs)

    def observed_norm(*args, **kwargs):
        norms.append(args[1])
        return original_norm(*args, **kwargs)

    monkeypatch.setattr(recovery, "recover", observed_recover)
    monkeypatch.setattr(factory.work_factory.support, "support_recovery", observed_support)
    monkeypatch.setattr(
        factory.norm_factory.functional, "norm_observation_at_order", observed_norm,
    )
    result = factory.produce_saved_observations(grid, q, eta, budget=budget)
    assert len(recoveries) == result.diagnostics["state_recoveries"] == 2
    assert len(supports) == result.diagnostics["support_recoveries"] == 1
    assert norms == [48, 64]
    assert result.diagnostics["equilibrium_solves"] == 0
    assert result.diagnostics["factorizations"] == 0


def test_factory_components_roundtrip_and_support_balance(tmp_path):
    grid, q, eta, budget = _inputs()
    result = factory.produce_saved_observations(grid, q, eta, budget=budget)
    interface_path = tmp_path / "saved_interface.npz"
    work_path = tmp_path / "saved_work.npz"
    norm_path = tmp_path / "saved_norm.npz"
    storage.write_interface(interface_path, result.interface, CASE)
    storage.write_work(work_path, result.work, CASE)
    storage.write_norm(norm_path, result.norm)
    restored_interface = storage.read_interface(interface_path, CASE)
    restored_work = storage.read_work(work_path, CASE)
    restored_norm = storage.read_norm(norm_path)
    assert interface.saved_identity(restored_interface) == interface.saved_identity(result.interface)
    assert work.input_identity(grid, result.recovery, restored_work) == work.input_identity(
        grid, result.recovery, result.work,
    )
    saved_functional = interface._saved_functional(restored_interface)
    assert norm.input_identity(saved_functional, restored_norm) == norm.input_identity(
        saved_functional, result.norm,
    )
    snapshot = result_storage.balance_snapshot(result.support, restored_interface)
    assert len(snapshot.action_sha256s) > 0


@pytest.mark.parametrize(
    "leaf", ("max_aggregate_operations", "max_aggregate_bits", "max_owned_bytes", "max_work_bytes"),
)
def test_outer_budget_failure_precedes_recovery(monkeypatch, leaf):
    grid, q, eta, budget = _inputs()
    rejected = replace(budget, **{leaf: 1})
    monkeypatch.setattr(
        recovery, "recover", lambda *args: pytest.fail("recovery preceded outer preflight"),
    )
    with pytest.raises(ValueError, match="saved-observation .*budget"):
        factory.produce_saved_observations(grid, q, eta, budget=rejected)
