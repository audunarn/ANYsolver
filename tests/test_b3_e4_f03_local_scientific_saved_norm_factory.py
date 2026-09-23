from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_saved_norm_factory as factory
from scripts import _b3_e4_f03_local_scientific_saved_storage as storage
from scripts import _b3_e4_f03_saved_norm_checks as norm


def _functional():
    cuts = (Fraction(0), Fraction(1, 2), Fraction(1))
    rows = (
        ((Fraction(1),) + (Fraction(0),) * 5,) * 3,
        ((Fraction(2),) + (Fraction(0),) * 5,) * 3,
    )
    return functional.Functional(
        cuts, rows,
        (Fraction(1, 4), Fraction(-1, 8), Fraction(1, 16)),
        ((Fraction(1), Fraction(2), Fraction(3)),
         (Fraction(-1), Fraction(1), Fraction(-2))),
    )


def test_factory_observes_fixed_orders_and_roundtrips(tmp_path, monkeypatch):
    value = _functional()
    budget = budgets.make_scientific_budgets().composition.norm_budget
    calls = []
    original = functional.norm_observation_at_order

    def observed(item, order):
        calls.append(order)
        return original(item, order)

    monkeypatch.setattr(factory.functional, "norm_observation_at_order", observed)
    saved = factory.produce_saved_norm(value, budget=budget)
    assert calls == [48, 64]
    path = tmp_path / "saved_norm.npz"
    storage.write_norm(path, saved)
    restored = storage.read_norm(path)
    checked = norm.verify_norm(value, restored, budget=budget)
    assert checked["status"] == "PASSED"


@pytest.mark.parametrize(
    "leaf", ("max_intervals", "max_integer_bits", "max_operations", "max_work_bytes"),
)
def test_factory_resource_failure_precedes_observation(monkeypatch, leaf):
    value = _functional()
    budget = budgets.make_scientific_budgets().composition.norm_budget
    rejected = replace(budget, **{leaf: 1})
    monkeypatch.setattr(
        factory.functional, "norm_observation_at_order",
        lambda *args: pytest.fail("observation preceded resource preflight"),
    )
    with pytest.raises(ValueError, match="norm .*budget"):
        factory.produce_saved_norm(value, budget=rejected)


def test_factory_preserves_identified_missing_observation(monkeypatch):
    value = _functional()
    budget = budgets.make_scientific_budgets().composition.norm_budget
    original = functional.norm_observation_at_order

    def observed(item, order):
        result = original(item, order)
        if order == 64:
            result = dict(result)
            result["channels"] = list(result["channels"])
            result["channels"][1] = None
            result["channel_finite"] = list(result["channel_finite"])
            result["channel_finite"][1] = False
            result["admissible"] = False
            result["failures"] = ({
                "stage": "test_observation", "channel": 1,
                "reason": "identified unavailable response",
            },)
        return result

    monkeypatch.setattr(factory.functional, "norm_observation_at_order", observed)
    saved = factory.produce_saved_norm(value, budget=budget)
    assert np.isnan(saved.channels[1, 1])
    assert saved.failures[1] == (
        ("test_observation", 1, "identified unavailable response"),
    )


def test_factory_owns_immutable_arrays():
    value = factory.produce_saved_norm(
        _functional(),
        budget=budgets.make_scientific_budgets().composition.norm_budget,
    )
    arrays = (
        value.channels, value.totals, value.components, value.channel_flags,
        value.total_flags, value.exact_zero,
    )
    assert all(not item.flags.writeable for item in arrays)
    assert not any(
        np.shares_memory(first, second)
        for index, first in enumerate(arrays)
        for second in arrays[index + 1:]
    )
