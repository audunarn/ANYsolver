"""Canonical solve-free replay budgets for the bounded F03 screen.

The factory only freezes resource limits.  It cannot assemble, factor, solve,
recover, adjudicate, register, or authorize a scientific execution.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_recovery_composition as composition
from scripts import _b3_e4_f03_saved_work_checks as work
from scripts import _b3_e4_f03_sparse_equilibrium_checks as equilibrium
from scripts import _b3_e4_f03_sparse_integration_checks as integration
from scripts import _b3_e4_f03_sparse_positivity as positivity
from scripts import _b3_e4_f03_sparse_root_rank as rank
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_sparse_trace_binding as trace


MAX_PHYSICAL_DOFS = max(case.physical_dofs for case in cases.CASES)
MAX_INTERVALS = max(case.station_intervals for case in cases.CASES)
MAX_VIRTUAL_TESTS = max(
    3 * (case.station_intervals * (case.degree + 2) + 1)
    for case in cases.CASES
)
INTERFACE_COMPARISONS = 192
MAX_WORK_COMPARISONS = 6 * MAX_VIRTUAL_TESTS + 50
MAX_COMPOSITION_COMPARISONS = INTERFACE_COMPARISONS + MAX_WORK_COMPARISONS + 4


@dataclass(frozen=True, slots=True)
class ScientificAdjudicationBudgets:
    positivity: positivity.PositivityBudget
    binding: binding.BindingBudget
    rank: rank.RankBudget
    trace: trace.TraceBindingBudget
    equilibrium: equilibrium.EquilibriumBudget
    integration: integration.IntegrationBudget
    composition: composition.CompositionBudget

    def __post_init__(self):
        expected = (
            (self.positivity, positivity.PositivityBudget),
            (self.binding, binding.BindingBudget),
            (self.rank, rank.RankBudget),
            (self.trace, trace.TraceBindingBudget),
            (self.equilibrium, equilibrium.EquilibriumBudget),
            (self.integration, integration.IntegrationBudget),
            (self.composition, composition.CompositionBudget),
        )
        if any(type(value) is not kind for value, kind in expected):
            raise ValueError("complete typed F03 scientific adjudication budgets required")


@dataclass(frozen=True, slots=True)
class CaseBudgetPreflight:
    case_id: str
    physical_dofs: int
    station_intervals: int
    virtual_tests: int
    work_comparisons: int
    recovery_operations: int
    recovery_workspace_bytes: int
    support_operations: int
    support_symbolic_bits: int
    support_workspace_bytes: int
    trace_input_nnz_upper: int
    trace_workspace_bytes: int

    def __post_init__(self):
        values = tuple(getattr(self, item.name) for item in fields(self)[1:])
        if self.case_id not in {case.case_id for case in cases.CASES} or any(
            type(value) is not int or value <= 0 for value in values
        ):
            raise ValueError("valid positive F03 adjudication preflight required")


def make_scientific_budgets() -> ScientificAdjudicationBudgets:
    """Return the one canonical nested budget bundle for scientific replay."""
    action = enclosure.ActionBudget(
        order=64,
        max_intervals=128,
        max_fraction_bits=65_536,
        max_total_bits=200_000_000,
        max_operations=2_000_000,
        max_work_bytes=256 * 1024**2,
    )
    recovered = recovery.RecoveryBudget(
        trace_budget=cases.ASSEMBLY_BUDGET,
        max_free_dofs=MAX_PHYSICAL_DOFS,
        max_intervals=MAX_INTERVALS,
        max_integer_bits=1_000_000_000,
        max_work_bytes=256 * 1024**2,
        max_operations=2_500_000_000,
    )
    supported = support.SupportBudget(
        recovery_budget=recovered,
        max_free_dofs=MAX_PHYSICAL_DOFS,
        max_intervals=MAX_INTERVALS,
        max_operations=16_000_000,
        max_integer_bits=600_000_000,
        max_work_bytes=256 * 1024**2,
    )
    interfaced = interface.InterfaceBudget(
        recovery_budget=recovered,
        action_budget=action,
        max_intervals=MAX_INTERVALS,
        max_comparisons=INTERFACE_COMPARISONS,
        max_aggregate_operations=INTERFACE_COMPARISONS * action.max_operations,
        max_aggregate_bits=INTERFACE_COMPARISONS * action.max_total_bits,
        max_work_bytes=1024**3,
    )
    worked = work.WorkBudget(
        support_budget=supported,
        action_budget=action,
        max_virtual_tests=MAX_VIRTUAL_TESTS,
        max_comparisons=MAX_WORK_COMPARISONS,
        max_aggregate_operations=MAX_WORK_COMPARISONS * action.max_operations,
        max_aggregate_bits=MAX_WORK_COMPARISONS * action.max_total_bits,
        max_work_bytes=4 * 1024**3,
    )
    normed = norm.NormBudget(
        max_intervals=128,
        max_integer_bits=32_000_000,
        max_operations=1_000_000_000,
        max_work_bytes=128 * 1024**2,
    )
    bound = binding.BindingBudget(
        sparse_budget=cases.SYSTEM_BUDGET,
        max_combined_nnz=2 * cases.SYSTEM_BUDGET.max_nnz,
        max_fraction_bits=cases.MAX_EXACT_FRACTION_BITS,
        max_total_bits=cases.MAX_EXACT_CUMULATIVE_BITS,
        max_python_work_bytes=1024**3,
    )
    equilibrated = equilibrium.EquilibriumBudget(
        binding_budget=bound,
        max_six_block_nnz=660_000,
        max_fraction_bits=cases.MAX_EXACT_FRACTION_BITS,
        max_total_bits=cases.MAX_EXACT_CUMULATIVE_BITS,
        max_python_work_bytes=cases.MAX_EXACT_PYTHON_WORKSPACE_BYTES,
    )
    integrated = integration.IntegrationBudget(
        sparse_budget=cases.SYSTEM_BUDGET,
        max_union_nnz=2 * cases.SYSTEM_BUDGET.max_nnz,
        max_fraction_bits=cases.MAX_EXACT_FRACTION_BITS,
        max_total_bits=cases.MAX_EXACT_CUMULATIVE_BITS,
        max_python_work_bytes=2 * 1024**3,
    )
    ranked = rank.RankBudget(
        sparse_budget=cases.SYSTEM_BUDGET,
        max_fraction_bits=cases.MAX_EXACT_FRACTION_BITS,
        max_total_bits=cases.MAX_EXACT_CUMULATIVE_BITS,
        max_eigen_steps=160,
        max_work_bytes=512 * 1024**2,
    )
    traced = trace.TraceBindingBudget(
        sparse_budget=cases.SYSTEM_BUDGET,
        trace_budget=cases.ASSEMBLY_BUDGET,
        max_input_nnz=88 * MAX_PHYSICAL_DOFS,
        max_fraction_bits=cases.MAX_EXACT_FRACTION_BITS,
        max_total_bits=cases.MAX_EXACT_CUMULATIVE_BITS,
        max_work_bytes=3 * 1024**3,
    )
    composed_work = (
        equilibrated.max_python_work_bytes
        + interfaced.max_work_bytes
        + worked.max_work_bytes
        + normed.max_work_bytes
        + 256 * 1024**2
        + 65_536
    )
    composed = composition.CompositionBudget(
        equilibrium_budget=equilibrated,
        interface_budget=interfaced,
        work_budget=worked,
        norm_budget=normed,
        max_owned_bytes=256 * 1024**2,
        max_comparisons=MAX_COMPOSITION_COMPARISONS,
        max_aggregate_operations=(
            interfaced.max_aggregate_operations
            + worked.max_aggregate_operations
            + normed.max_operations
            + recovered.max_operations
            + 2 * supported.recovery_budget.max_operations
            + supported.max_operations
        ),
        max_aggregate_bits=(
            equilibrated.max_total_bits
            + interfaced.max_aggregate_bits
            + worked.max_aggregate_bits
            + normed.max_integer_bits
            + recovered.max_integer_bits
            + 2 * supported.recovery_budget.max_integer_bits
            + supported.max_integer_bits
        ),
        max_work_bytes=composed_work,
    )
    proof = positivity.PositivityBudget(
        sparse_budget=cases.FACTOR_VALIDATION_BUDGET,
        max_product_paths=cases.MAX_EXACT_PRODUCT_PATHS,
        max_residual_nnz=cases.MAX_EXACT_RESIDUAL_ENTRIES,
        max_fraction_bits=cases.MAX_EXACT_FRACTION_BITS,
        max_total_bits=cases.MAX_EXACT_CUMULATIVE_BITS,
        max_python_work_bytes=cases.MAX_EXACT_PYTHON_WORKSPACE_BYTES,
    )
    return ScientificAdjudicationBudgets(
        proof, bound, ranked, traced, equilibrated, integrated, composed,
    )


def require_scientific_budgets(value: object) -> ScientificAdjudicationBudgets:
    expected = make_scientific_budgets()
    if type(value) is not ScientificAdjudicationBudgets or value != expected:
        raise ValueError("canonical F03 scientific adjudication budgets required")
    return value


def _flatten(prefix: str, value: object) -> tuple[tuple[str, int], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        output = ()
        for item in fields(value):
            output += _flatten(f"{prefix}_{item.name}", getattr(value, item.name))
        return output
    if type(value) is not int or value <= 0:
        raise ValueError("positive integer F03 scientific budget leaf required")
    return ((prefix, value),)


def resource_contract() -> tuple[tuple[str, int], ...]:
    """Deterministic complete scalar identity for the canonical bundle."""
    values = _flatten("adjudication", make_scientific_budgets())
    names = tuple(name for name, _ in values)
    if len(names) != len(set(names)):
        raise ArithmeticError("duplicate F03 scientific adjudication budget name")
    return values


def preflight_case(
    case: cases.ScientificCase,
    budgets: ScientificAdjudicationBudgets,
) -> CaseBudgetPreflight:
    """Check topology-known replay envelopes without numerical execution."""
    budgets = require_scientific_budgets(budgets)
    if type(case) is not cases.ScientificCase or case not in cases.CASES:
        raise ValueError("registered F03 scientific case required")
    grid = cases.compile_case(case)
    n = grid.free_dofs
    intervals = len(grid.station_cuts) - 1
    rectangles = len(grid.rectangles)
    active = max((len(indices) for indices in grid.trace_incidence), default=0)
    local = 2 * (grid.p + 1) ** 2
    recovered = budgets.composition.interface_budget.recovery_budget
    supported = budgets.composition.work_budget.support_budget
    recovery_operations = (
        intervals * rectangles * 256 * (grid.p + 3) ** 4
        + rectangles * local * (local + 12)
    )
    recovery_workspace = (
        768 * (n + intervals * 180 + 128)
        + recovered.max_integer_bits // 8
        + local * local * 768
        + active * 3 * (grid.p + 3) * 768
        + recovered.trace_budget.max_trace_integer_bits // 8
    )
    support_operations = (
        rectangles * local * (local + 24) * 32
        + intervals * max(1, active) * (grid.p + 3) * 96
    )
    fraction_bits = 2 * recovery.BITS
    support_bits = (
        160 * (1 + 8 * intervals) * fraction_bits
        + (6 * intervals * 3 * 6 + intervals * 3 * 6) * fraction_bits
        + (n + 3 + len(grid.station_cuts) + 6) * fraction_bits
    )
    support_workspace = (
        768 * (12 * local * rectangles + intervals * 360 + n)
        + supported.max_integer_bits // 8
    )
    trace_nnz = 88 * n
    traced = budgets.trace
    trace_workspace = (
        1024 * (trace_nnz + 32 * n)
        + 2 * traced.max_total_bits
        + 9 * traced.trace_budget.max_work_bytes
    )
    virtual = 3 * (intervals * (grid.p + 2) + 1)
    comparisons = 6 * virtual + 50
    checks = (
        n <= recovered.max_free_dofs,
        intervals <= recovered.max_intervals,
        recovery_operations <= recovered.max_operations,
        recovery_workspace <= recovered.max_work_bytes,
        n <= supported.max_free_dofs,
        intervals <= supported.max_intervals,
        support_operations <= supported.max_operations,
        support_bits <= supported.max_integer_bits,
        support_workspace <= supported.max_work_bytes,
        virtual <= budgets.composition.work_budget.max_virtual_tests,
        comparisons <= budgets.composition.work_budget.max_comparisons,
        trace_nnz <= traced.max_input_nnz,
        trace_workspace <= traced.max_work_bytes,
    )
    if not all(checks):
        raise ValueError(f"F03 adjudication budget preflight failed: {case.case_id}")
    return CaseBudgetPreflight(
        case.case_id, n, intervals, virtual, comparisons,
        recovery_operations, recovery_workspace, support_operations,
        support_bits, support_workspace, trace_nnz, trace_workspace,
    )


def preflight_inventory(
    budgets: ScientificAdjudicationBudgets,
) -> tuple[CaseBudgetPreflight, ...]:
    budgets = require_scientific_budgets(budgets)
    return tuple(preflight_case(case, budgets) for case in cases.CASES)
