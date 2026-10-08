"""Produce the complete bounded F03 saved-observation bundle."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_local_scientific_saved_interface_factory as interface_factory
from scripts import _b3_e4_f03_local_scientific_saved_norm_factory as norm_factory
from scripts import _b3_e4_f03_local_scientific_saved_work_factory as work_factory
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_recovery_composition as composition
from scripts import _b3_e4_f03_saved_work_checks as work


@dataclass(frozen=True, slots=True, init=False)
class ProducedSavedObservations:
    recovery: recovery.Recovery
    interface: interface.SavedInterface
    work: work.SavedWork
    norm: norm.SavedNorm
    support: support.SupportResult
    diagnostics: object

    def __init__(self, *args, **kwargs):
        raise TypeError("ProducedSavedObservations requires validated factory")


def _result(
    recovered: recovery.Recovery,
    saved_interface: interface.SavedInterface,
    saved_work: work.SavedWork,
    saved_norm: norm.SavedNorm,
    supported: support.SupportResult,
    diagnostics: MappingProxyType,
) -> ProducedSavedObservations:
    expected = (
        (recovered, recovery.Recovery),
        (saved_interface, interface.SavedInterface),
        (saved_work, work.SavedWork),
        (saved_norm, norm.SavedNorm),
        (supported, support.SupportResult),
    )
    if any(type(value) is not kind for value, kind in expected):
        raise ValueError("complete validated F03 saved-observation bundle required")
    if (
        type(diagnostics) is not MappingProxyType
        or recovered.q != supported.q or recovered.eta != supported.eta
        or recovered.cuts != supported.cuts
        or saved_interface.cuts != recovered.cuts
        or saved_work.cuts != recovered.cuts
        or saved_work.lift_family != supported.lift_family
    ):
        raise ValueError("inconsistent common-state F03 saved-observation bundle")
    result = object.__new__(ProducedSavedObservations)
    for name, value in (
        ("recovery", recovered), ("interface", saved_interface),
        ("work", saved_work), ("norm", saved_norm),
        ("support", supported), ("diagnostics", diagnostics),
    ):
        object.__setattr__(result, name, value)
    return result


def _owned_bytes(
    grid: topology.CompiledGrid, budget: composition.CompositionBudget,
) -> int:
    intervals = len(grid.station_cuts) - 1
    virtual_tests = 3 * (intervals * (grid.p + 2) + 1)
    interface_values = intervals * 18 + 3 + 6 + 4 * 8 * 3
    work_values = 6 * intervals * 3 * 6 + 24 + 4 + 5 * virtual_tests
    norm_values = 2 * 3 + 2 + 2 * 3 * 6 + 2 * 3 * 3 + 2 * 3 + 2
    grid_values = sum(
        item.size for item in (
            grid.free_to_full, grid.full_to_free, grid.full_gathers,
            grid.free_gathers, grid.root_incidence, *grid.trace_incidence,
        )
    )
    exact_bytes = (
        budget.interface_budget.recovery_budget.max_integer_bits // 8
        + budget.work_budget.support_budget.max_integer_bits // 8
    )
    fraction_objects = (
        grid.free_dofs + 3 + 2 * len(grid.station_cuts)
        + intervals * (3 * 6 * 3 + 64 * 8)
    )
    return (
        2 * 8 * (interface_values + work_values + norm_values + grid_values)
        + exact_bytes + 256 * fraction_objects + 65536
    )


def _preflight(
    grid: topology.CompiledGrid,
    q: object,
    eta: object,
    budget: composition.CompositionBudget,
):
    if type(grid) is not topology.CompiledGrid or type(budget) is not composition.CompositionBudget:
        raise ValueError("compiled grid and explicit CompositionBudget required")
    ib = budget.interface_budget
    wb = budget.work_budget
    nb = budget.norm_budget
    q0 = recovery._vector(q, grid.free_dofs, ib.recovery_budget.max_integer_bits)
    q_bits = sum(recovery._bits(item) for item in q0)
    eta0 = recovery._vector(eta, 3, ib.recovery_budget.max_integer_bits - q_bits)
    state_bits = q_bits + sum(recovery._bits(item) for item in eta0)
    intervals = len(grid.station_cuts) - 1
    virtual_tests = 3 * (intervals * (grid.p + 2) + 1)
    if (
        intervals > ib.max_intervals or intervals > nb.max_intervals
        or grid.free_dofs > ib.recovery_budget.max_free_dofs
        or intervals > ib.recovery_budget.max_intervals
        or grid.free_dofs > wb.support_budget.max_free_dofs
        or intervals > wb.support_budget.max_intervals
        or grid.free_dofs > wb.support_budget.recovery_budget.max_free_dofs
        or intervals > wb.support_budget.recovery_budget.max_intervals
        or state_bits > wb.support_budget.recovery_budget.max_integer_bits
        or virtual_tests > wb.max_virtual_tests
    ):
        raise ValueError("saved-observation nested inventory exceeds budget")
    operations = (
        ib.recovery_budget.max_operations
        + ib.max_aggregate_operations
        + wb.support_budget.recovery_budget.max_operations
        + wb.support_budget.max_operations
        + wb.max_aggregate_operations
        + nb.max_operations
    )
    bits = (
        ib.recovery_budget.max_integer_bits
        + ib.max_aggregate_bits
        + wb.support_budget.recovery_budget.max_integer_bits
        + wb.support_budget.max_integer_bits
        + wb.max_aggregate_bits
        + nb.max_integer_bits
    )
    owned = _owned_bytes(grid, budget)
    workspace = (
        ib.recovery_budget.max_work_bytes + ib.max_work_bytes
        + wb.max_work_bytes + nb.max_work_bytes + owned
    )
    if operations > budget.max_aggregate_operations:
        raise ValueError("saved-observation aggregate operation budget exceeded")
    if bits > budget.max_aggregate_bits:
        raise ValueError("saved-observation aggregate bit budget exceeded")
    if owned > budget.max_owned_bytes:
        raise ValueError("saved-observation owned-byte budget exceeded")
    if workspace > budget.max_work_bytes:
        raise ValueError("saved-observation workspace budget exceeded")
    return q0, eta0, virtual_tests, operations, bits, owned, workspace


def produce_saved_observations(
    grid: topology.CompiledGrid,
    q: object,
    eta: object,
    *,
    budget: composition.CompositionBudget,
) -> ProducedSavedObservations:
    """Produce interface, work and norm evidence from one common state."""
    q0, eta0, virtual_tests, operations, bits, owned, workspace = _preflight(
        grid, q, eta, budget,
    )
    recovered = recovery.recover(grid, q0, eta0, budget.interface_budget.recovery_budget)
    saved_interface = interface_factory.produce_saved_interface(
        recovered, budget=budget.interface_budget,
    )
    produced_work = work_factory.produce_saved_work(
        grid, recovered, budget=budget.work_budget,
    )
    saved_functional = interface._saved_functional(saved_interface)
    if type(saved_functional) is not functional.Functional:
        raise ArithmeticError("invalid saved-interface Functional conversion")
    saved_norm = norm_factory.produce_saved_norm(
        saved_functional, budget=budget.norm_budget,
    )
    diagnostics = MappingProxyType({
        "state_recoveries": 2,
        "support_recoveries": 1,
        "interface_quadrature_observations": 16,
        "norm_observations": 2,
        "virtual_work_observations": virtual_tests,
        "equilibrium_solves": 0,
        "factorizations": 0,
        "operation_envelope": operations,
        "integer_bit_envelope": bits,
        "owned_byte_envelope": owned,
        "workspace_envelope_bytes": workspace,
    })
    return _result(
        recovered, saved_interface, produced_work.saved, saved_norm,
        produced_work.support, diagnostics,
    )
