"""Produce bounded saved 48/64 F03 Green-norm observations."""
from __future__ import annotations

from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_saved_norm_checks as norm


def produce_saved_norm(
    value: functional.Functional, *, budget: norm.NormBudget,
) -> norm.SavedNorm:
    """Observe both fixed orders after the complete resource preflight."""
    owned = norm.preflight_observation(value, budget=budget)
    observations = tuple(
        functional.norm_observation_at_order(owned, order)
        for order in norm.ORDERS
    )
    intervals = len(owned.cuts) - 1
    if any(
        type(item.get("intervals")) is not int or item["intervals"] != intervals
        for item in observations
    ):
        raise ValueError("raw norm interval identity mismatch")
    return norm.pack_observations(observations)
