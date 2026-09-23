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
        value = float(action.decimal_value())
    except (ArithmeticError, OverflowError) as exc:
        raise ValueError("unrepresentable saved-interface Action") from exc
    if not math.isfinite(value):
        raise ValueError("nonfinite saved-interface Action")
    return value


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
) -> np.ndarray:
    """Observe one band directly from exact local density coefficients."""
    if order not in (48, 64):
        raise ValueError("fixed saved-interface quadrature order required")
    nodes, weights = leggauss(order)
    nodes = (nodes + 1.0) / 2.0
    weights = weights / 2.0
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


def produce_saved_interface(
    value: recovery.Recovery, *, budget: interface.InterfaceBudget,
) -> interface.SavedInterface:
    """Create one owned saved-interface record without recomputing recovery."""
    if type(value) is not recovery.Recovery or type(budget) is not interface.InterfaceBudget:
        raise ValueError("owned Recovery and explicit InterfaceBudget required")
    intervals = len(value.cuts) - 1
    if intervals <= 0 or intervals > budget.max_intervals:
        raise ValueError("saved-interface producer interval budget exceeded")
    operations = len(interface.BANDS) * intervals * (48 + 64) * 48
    workspace = (
        intervals * 3 * POLYNOMIAL_COEFFICIENTS * 16
        + 2 * 64 * 3 * 8
        + 7 * len(interface.BANDS) * 3 * 8
    )
    if operations > budget.max_aggregate_operations:
        raise ValueError("saved-interface producer operation budget exceeded")
    if workspace > budget.max_work_bytes:
        raise ValueError("saved-interface producer workspace budget exceeded")

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
        analytic.append([_display(item) for item in actions])
        line.append([_display(item - endpoint) for item, endpoint in zip(actions, endpoints)])
        observed48.append(_quadrature_band(value, left, right, 48))
        observed64.append(_quadrature_band(value, left, right, 64))
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
