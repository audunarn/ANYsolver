"""Produce bounded, independently observed F03 saved-interface evidence.

The analytic route evaluates the exact recovered Actions.  The two numerical
routes integrate the exact piecewise density independently at fixed 48- and
64-point Gauss orders.  This module performs no recovery, assembly, factor,
or equilibrium solve.
"""
from __future__ import annotations

from fractions import Fraction
import math

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_spatial_contract as contract


ZERO = Fraction(0)
ONE = Fraction(1)
POLYNOMIAL_COEFFICIENTS = 6


def _finite_float(value: Fraction, name: str) -> float:
    try:
        observed = float(value)
    except OverflowError as exc:
        raise ValueError(f"unrepresentable saved-interface {name}") from exc
    if not math.isfinite(observed) or (value != 0 and observed == 0.0):
        raise ValueError(f"nonfinite or underflowed saved-interface {name}")
    return observed


def _display(action: recovery.Action) -> float:
    try:
        decimal = action.decimal_value()
        value = float(decimal)
    except (ArithmeticError, OverflowError) as exc:
        raise ValueError("unrepresentable saved-interface Action") from exc
    if not math.isfinite(value) or (decimal != 0 and value == 0.0):
        raise ValueError("nonfinite or underflowed saved-interface Action")
    return value


def _admit_actions(
    actions: tuple[recovery.Action, ...], budget: interface.InterfaceBudget,
) -> None:
    nested = budget.action_budget
    for action in actions:
        fractions = (action.rational,) + tuple(
            item
            for left, right, polynomial in action.cosine_terms
            for item in (left, right, *polynomial)
        )
        if len(fractions) > nested.max_operations:
            raise ValueError("saved-interface nested Action operation budget exceeded")
        if any(
            item.numerator.bit_length() > nested.max_fraction_bits
            or item.denominator.bit_length() > nested.max_fraction_bits
            for item in fractions
        ):
            raise ValueError("saved-interface nested Action fraction budget exceeded")
        if sum(
            item.numerator.bit_length() + item.denominator.bit_length()
            for item in fractions
        ) > nested.max_total_bits:
            raise ValueError("saved-interface nested Action total-bit budget exceeded")


def _endpoint_actions(
    value: recovery.Recovery, left: Fraction, right: Fraction,
) -> tuple[recovery.Action, recovery.Action, recovery.Action]:
    result = [ZERO, ZERO, ZERO]
    for station, atom, include in (
        (ZERO, value.interface.atoms[0], left == ZERO),
        (ONE, value.interface.atoms[1], right == ONE),
    ):
        if include:
            result[0] += atom[0]
            result[1] += atom[1]
            result[2] += station * atom[1] + atom[2]
    return tuple(recovery.Action(item) for item in result)


def _quadrature_band(
    value: recovery.Recovery, left: Fraction, right: Fraction, order: int,
    rule: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    """Observe one band directly from exact local density coefficients."""
    if order not in (48, 64):
        raise ValueError("fixed saved-interface quadrature order required")
    nodes, weights = rule
    if (
        type(nodes) is not np.ndarray or type(weights) is not np.ndarray
        or nodes.dtype != np.float64 or weights.dtype != np.float64
        or nodes.shape != (order,) or weights.shape != (order,)
    ):
        raise ValueError("owned saved-interface quadrature rule required")
    total = np.zeros(3, dtype=np.float64)
    for (a, b), density in zip(
        zip(value.cuts, value.cuts[1:]), value.interface.coefficients,
    ):
        lo = max(a, left)
        hi = min(b, right)
        if lo >= hi:
            continue
        width = _finite_float(hi - lo, "quadrature width")
        interval_width = _finite_float(b - a, "recovery interval width")
        local_start = _finite_float((lo - a) / (b - a), "local start")
        local_width = _finite_float((hi - lo) / (b - a), "local width")
        station_start = _finite_float(lo, "band station")
        local = local_start + local_width * nodes
        station = station_start + width * nodes
        coefficients = np.asarray(
            [[_finite_float(item, "density coefficient") for item in row]
             for row in density],
            dtype=np.float64,
        )
        amplitudes = np.asarray(
            [_finite_float(item, "cosine amplitude")
             for item in value.interface.cosine],
            dtype=np.float64,
        )
        observed = np.stack(
            [np.polynomial.polynomial.polyval(local, row) for row in coefficients],
            axis=1,
        )
        observed += np.cos(contract.OMEGA * station)[:, None] * amplitudes
        observed[:, 2] += station * observed[:, 1]
        contribution = width * np.einsum("i,ij->j", weights, observed)
        if not np.all(np.isfinite(contribution)):
            raise ValueError("nonfinite saved-interface quadrature response")
        total += contribution
    for station, atom, include in (
        (ZERO, value.interface.atoms[0], left == ZERO),
        (ONE, value.interface.atoms[1], right == ONE),
    ):
        if include:
            atom_values = np.asarray(
                [_finite_float(item, "endpoint atom") for item in atom],
                dtype=np.float64,
            )
            total += atom_values
            total[2] += _finite_float(station * atom[1], "endpoint lever arm")
    if not np.all(np.isfinite(total)):
        raise ValueError("nonfinite saved-interface band response")
    return total


def _quadrature_rule(order: int) -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = leggauss(order)
    return (
        np.ascontiguousarray((nodes + 1.0) / 2.0, dtype=np.float64),
        np.ascontiguousarray(weights / 2.0, dtype=np.float64),
    )


def _resource_requirements(
    value: recovery.Recovery, budget: interface.InterfaceBudget,
) -> tuple[int, int, int]:
    intervals = len(value.cuts) - 1
    exact = (
        value.cuts
        + value.interface.cosine
        + tuple(item for row in value.interface.atoms for item in row)
        + tuple(
            item
            for block in value.interface.coefficients
            for row in block
            for item in row
        )
    )
    if any(type(item) is not Fraction for item in exact):
        raise ValueError("exact saved-interface Recovery inventory required")
    bit_sizes = tuple(
        item.numerator.bit_length() + item.denominator.bit_length()
        for item in exact
    )
    if any(
        item.numerator.bit_length() > budget.action_budget.max_fraction_bits
        or item.denominator.bit_length() > budget.action_budget.max_fraction_bits
        for item in exact
    ):
        raise ValueError("saved-interface producer fraction bit budget exceeded")
    # Per band: three total Actions, three endpoint Actions and three
    # line-only differences.  The bound charges each of those 72 Action
    # constructions at the declared total-bit envelope.
    action_constructions = len(interface.BANDS) * 9
    aggregate_bits = sum(bit_sizes) + (
        action_constructions * budget.action_budget.max_total_bits
    )
    quadrature_operations = (
        len(interface.BANDS) * intervals * (48 + 64) * 48
    )
    exact_action_operations = len(interface.BANDS) * intervals * 3 * 6 * 64
    decimal_operations = len(interface.BANDS) * 6 * 120 * 6 * 32
    operations = quadrature_operations + exact_action_operations + decimal_operations

    fraction_slot = 512 + (2 * budget.action_budget.max_fraction_bits + 7) // 8
    exact_storage = len(exact) * fraction_slot
    live_action_storage = 8 * (1 + 8 * intervals) * fraction_slot
    decimal_scratch = 120 * 12 * 512
    gauss_scratch = 2 * (64 * 64 * 8 * 32 + 64 * 8 * 16)
    retained_numeric = (
        intervals * 3 * POLYNOMIAL_COEFFICIENTS * 16
        + 2 * 64 * 3 * 8
        + 7 * len(interface.BANDS) * 3 * 8
    )
    workspace = (
        exact_storage + live_action_storage + decimal_scratch
        + gauss_scratch + retained_numeric
    )
    return operations, aggregate_bits, workspace


def produce_saved_interface(
    value: recovery.Recovery, *, budget: interface.InterfaceBudget,
) -> interface.SavedInterface:
    """Create one owned saved-interface record without recomputing recovery."""
    if type(value) is not recovery.Recovery or type(budget) is not interface.InterfaceBudget:
        raise ValueError("owned Recovery and explicit InterfaceBudget required")
    intervals = len(value.cuts) - 1
    if intervals <= 0 or intervals > budget.max_intervals:
        raise ValueError("saved-interface producer interval budget exceeded")
    operations, aggregate_bits, workspace = _resource_requirements(value, budget)
    if operations > budget.max_aggregate_operations:
        raise ValueError("saved-interface producer operation budget exceeded")
    if aggregate_bits > budget.max_aggregate_bits:
        raise ValueError("saved-interface producer aggregate bit budget exceeded")
    if workspace > budget.max_work_bytes:
        raise ValueError("saved-interface producer workspace budget exceeded")

    rules = {order: _quadrature_rule(order) for order in (48, 64)}

    density = np.asarray(
        [[[_finite_float(item, "density coefficient") for item in row]
          for row in block]
         for block in value.interface.coefficients],
        dtype=np.float64,
    )
    cosine = np.asarray(
        [_finite_float(item, "cosine amplitude") for item in value.interface.cosine],
        dtype=np.float64,
    )
    atoms = np.asarray(
        [[_finite_float(item, "endpoint atom") for item in row]
         for row in value.interface.atoms],
        dtype=np.float64,
    )
    analytic = []
    line = []
    observed48 = []
    observed64 = []
    for left, right in interface.BANDS:
        actions = recovery.band(value, left, right)
        endpoints = _endpoint_actions(value, left, right)
        line_actions = tuple(
            item - endpoint for item, endpoint in zip(actions, endpoints)
        )
        _admit_actions(actions + endpoints + line_actions, budget)
        analytic.append([_display(item) for item in actions])
        line.append([_display(item) for item in line_actions])
        observed48.append(_quadrature_band(value, left, right, 48, rules[48]))
        observed64.append(_quadrature_band(value, left, right, 64, rules[64]))
    return interface.SavedInterface(
        value.cuts,
        density,
        cosine,
        atoms,
        np.asarray(analytic, dtype=np.float64),
        np.asarray(observed48, dtype=np.float64),
        np.asarray(observed64, dtype=np.float64),
        np.asarray(line, dtype=np.float64),
    )
