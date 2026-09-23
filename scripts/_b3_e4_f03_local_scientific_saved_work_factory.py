"""Produce bounded saved F03 support and virtual-work observations."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_saved_work_checks as work
from scripts import _b3_e4_f03_spatial_contract as contract


@dataclass(frozen=True, slots=True)
class ProducedWorkEvidence:
    saved: work.SavedWork
    support: support.SupportResult

    def __post_init__(self):
        if type(self.saved) is not work.SavedWork or type(self.support) is not support.SupportResult:
            raise ValueError("validated saved work and support result required")


def _finite_float(value: Fraction, name: str) -> float:
    try:
        observed = float(value)
    except OverflowError as exc:
        raise ValueError(f"unrepresentable saved-work {name}") from exc
    if not math.isfinite(observed) or (value != 0 and observed == 0.0):
        raise ValueError(f"nonfinite or underflowed saved-work {name}")
    return observed


def _display(action: recovery.Action) -> float:
    try:
        observed = float(action.decimal_value())
    except (ArithmeticError, OverflowError) as exc:
        raise ValueError("unrepresentable saved-work Action") from exc
    if not math.isfinite(observed):
        raise ValueError("nonfinite saved-work Action")
    return observed


def _admit_actions(actions: tuple[recovery.Action, ...], budget: work.WorkBudget) -> None:
    nested = budget.action_budget
    for action in actions:
        fractions = (action.rational,) + tuple(
            item
            for left, right, polynomial in action.cosine_terms
            for item in (left, right, *polynomial)
        )
        if len(fractions) > nested.max_operations:
            raise ValueError("saved-work nested Action operation budget exceeded")
        if any(
            item.numerator.bit_length() > nested.max_fraction_bits
            or item.denominator.bit_length() > nested.max_fraction_bits
            for item in fractions
        ):
            raise ValueError("saved-work nested Action fraction budget exceeded")
        if sum(
            item.numerator.bit_length() + item.denominator.bit_length()
            for item in fractions
        ) > nested.max_total_bits:
            raise ValueError("saved-work nested Action total-bit budget exceeded")


def _exact_inventory(value: recovery.Recovery) -> tuple[Fraction, ...]:
    return (
        value.q + value.eta + value.cuts
        + tuple(item for block in value.pose for row in block for item in row)
        + tuple(item for block in value.resultants for row in block for item in row)
        + tuple(
            item for block in value.interface.coefficients
            for row in block for item in row
        )
        + value.interface.cosine
        + tuple(item for row in value.interface.atoms for item in row)
    )


def _resource_requirements(
    grid: topology.CompiledGrid,
    value: recovery.Recovery,
    budget: work.WorkBudget,
) -> tuple[int, int, int, int]:
    intervals = len(value.cuts) - 1
    virtual_tests = 3 * (intervals * (grid.p + 2) + 1)
    exact = _exact_inventory(value)
    if any(type(item) is not Fraction for item in exact):
        raise ValueError("exact saved-work Recovery inventory required")
    action_budget = budget.action_budget
    if any(
        item.numerator.bit_length() > action_budget.max_fraction_bits
        or item.denominator.bit_length() > action_budget.max_fraction_bits
        for item in exact
    ):
        raise ValueError("saved-work fraction bit budget exceeded")
    input_bits = sum(
        item.numerator.bit_length() + item.denominator.bit_length()
        for item in exact
    )
    displayed_actions = 22
    aggregate_bits = input_bits + displayed_actions * action_budget.max_total_bits
    quadrature_operations = virtual_tests * intervals * 48 * 192
    decimal_operations = displayed_actions * 120 * 6 * 32
    operations = (
        budget.support_budget.max_operations
        + budget.support_budget.recovery_budget.max_operations
        + quadrature_operations + decimal_operations
    )
    fraction_slot = 512 + (2 * action_budget.max_fraction_bits + 7) // 8
    exact_storage = len(exact) * fraction_slot
    live_action_storage = 32 * (1 + 8 * intervals) * fraction_slot
    decimal_scratch = 120 * 12 * 512
    gauss_scratch = 64 * 64 * 8 * 32 + 64 * 8 * 16
    numeric_values = (
        6 * intervals * 3 * 6 + 24 + 4 + virtual_tests * 5
    )
    retained_numeric = 2 * numeric_values * 8
    workspace = (
        budget.support_budget.max_work_bytes
        + budget.support_budget.recovery_budget.max_work_bytes
        + action_budget.max_work_bytes
        + exact_storage + live_action_storage + decimal_scratch
        + gauss_scratch + retained_numeric
    )
    return virtual_tests, operations, aggregate_bits, workspace


def _quadrature_rule() -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = leggauss(48)
    return (
        np.ascontiguousarray((nodes + 1.0) / 2.0, dtype=np.float64),
        np.ascontiguousarray(weights / 2.0, dtype=np.float64),
    )


def _numerical_virtual(
    value: recovery.Recovery,
    rows: tuple,
    rule: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    nodes, weights = rule
    if (
        type(nodes) is not np.ndarray or type(weights) is not np.ndarray
        or nodes.dtype != np.float64 or weights.dtype != np.float64
        or nodes.shape != (48,) or weights.shape != (48,)
    ):
        raise ValueError("owned saved-work quadrature rule required")
    terms = np.zeros(4, dtype=np.float64)
    for a, b, test_rows, resultants, density in zip(
        value.cuts, value.cuts[1:], rows, value.resultants,
        value.interface.coefficients,
    ):
        width = _finite_float(b - a, "interval width")
        station = _finite_float(a, "station") + width * nodes
        test = np.asarray([
            np.polynomial.polynomial.polyval(
                nodes, [_finite_float(item, "test coefficient") for item in row],
            )
            for row in test_rows
        ], dtype=np.float64)
        derivative = np.asarray([
            np.polynomial.polynomial.polyval(
                nodes,
                np.arange(1, len(row), dtype=np.float64)
                * np.asarray([
                    _finite_float(item, "test derivative coefficient")
                    for item in row[1:]
                ]),
            ) / width
            for row in test_rows
        ], dtype=np.float64)
        stress = np.asarray([
            np.polynomial.polynomial.polyval(
                nodes, [_finite_float(item, "resultant coefficient") for item in row],
            )
            for row in resultants
        ], dtype=np.float64)
        density_values = np.asarray([
            np.polynomial.polynomial.polyval(
                nodes, [_finite_float(item, "density coefficient") for item in row],
            ) + _finite_float(amplitude, "cosine amplitude") * np.cos(contract.OMEGA * station)
            for row, amplitude in zip(density, value.interface.cosine)
        ], dtype=np.float64)
        terms[0] += width * np.sum(weights * np.sum(density_values * test, axis=0))
        terms[1] += width * np.sum(weights * (
            stress[0] * derivative[0]
            + stress[1] * (derivative[1] - test[2])
            + stress[2] * derivative[2]
        ))
        terms[2] += width * np.sum(
            weights * contract.F0 * (1.0 + 0.25 * np.cos(contract.OMEGA * station))
            * test[1]
        )
    endpoint0 = np.asarray([
        _finite_float(row[0], "root test value") for row in rows[0]
    ])
    endpoint1 = np.asarray([
        _finite_float(sum(row), "tip test value") for row in rows[-1]
    ])
    atoms = np.asarray([
        [_finite_float(item, "endpoint atom") for item in row]
        for row in value.interface.atoms
    ], dtype=np.float64)
    eta = np.asarray([
        _finite_float(item, "support multiplier") for item in value.eta
    ], dtype=np.float64)
    terms[0] += atoms[0] @ endpoint0
    terms[0] += atoms[1] @ endpoint1
    terms[3] = eta @ endpoint0
    if not np.all(np.isfinite(terms)):
        raise ValueError("nonfinite saved-work virtual observation")
    return terms


def produce_saved_work(
    grid: topology.CompiledGrid,
    value: recovery.Recovery,
    *,
    budget: work.WorkBudget,
) -> ProducedWorkEvidence:
    """Create saved support/work evidence while retaining its support result."""
    if (
        type(grid) is not topology.CompiledGrid
        or type(value) is not recovery.Recovery
        or type(budget) is not work.WorkBudget
    ):
        raise ValueError("compiled grid, owned Recovery and explicit WorkBudget required")
    intervals = len(grid.station_cuts) - 1
    if (
        value.cuts != grid.station_cuts or len(value.q) != grid.free_dofs
        or len(value.eta) != 3 or intervals <= 0
    ):
        raise ValueError("saved-work state and grid inventory mismatch")
    virtual_tests, operations, aggregate_bits, workspace = _resource_requirements(
        grid, value, budget,
    )
    if virtual_tests > budget.max_virtual_tests:
        raise ValueError("saved-work virtual-test budget exceeded")
    if operations > budget.max_aggregate_operations:
        raise ValueError("saved-work producer operation budget exceeded")
    if aggregate_bits > budget.max_aggregate_bits:
        raise ValueError("saved-work producer aggregate bit budget exceeded")
    if workspace > budget.max_work_bytes:
        raise ValueError("saved-work producer workspace budget exceeded")

    supported = support.support_recovery(grid, value, budget.support_budget)
    rule = _quadrature_rule()
    observations = np.asarray([
        _numerical_virtual(value, rows, rule)
        for _, rows in work.virtual_inventory(value.cuts, grid.p)
    ], dtype=np.float64)
    if observations.shape != (virtual_tests, 4):
        raise ArithmeticError("incomplete saved-work virtual inventory")
    terms = observations.reshape(3, virtual_tests // 3, 4)
    defects = terms[:, :, 0] + terms[:, :, 1] - terms[:, :, 2] + terms[:, :, 3]
    def action_values(actions):
        actions = tuple(actions)
        _admit_actions(actions, budget)
        return np.asarray([_display(item) for item in actions], dtype=np.float64)
    saved = work.SavedWork(
        grid.p,
        value.cuts,
        supported.lift_family,
        np.asarray([
            support.lift_pose(value.cuts, side, channel, grid.p)
            for side in ("left", "right") for channel in range(3)
        ], dtype=np.float64),
        np.asarray([
            _finite_float(item, "shell work") for item in supported.shell_work
        ], dtype=np.float64),
        action_values(supported.interface_work),
        action_values(supported.route1),
        action_values(supported.route2),
        action_values((
            supported.first_free_route1_residual,
            supported.first_free_route2_residual,
        )),
        action_values((supported.shift_route1_delta, supported.shift_route2_delta)),
        terms,
        defects,
    )
    return ProducedWorkEvidence(saved, supported)
