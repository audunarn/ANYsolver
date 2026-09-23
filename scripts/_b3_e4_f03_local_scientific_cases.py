"""Frozen topology and resource contract for the bounded F03 local screen.

This module performs topology-only preflight.  It does not assemble a
mechanical operator, factor a matrix, solve equilibrium, or authorize the
scientific run described by the protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_saved_recovery_composition as composition
from scripts import _b3_e4_f03_spatial_contract as contract
from scripts import _b3_e4_f03_sparse_certificate as certificate


SCHEMA = "f03_local_scientific_cases_v1"
GRAPH_PREFLIGHT_BYTES = 256 * 1024**2
ARCHIVE_BYTES = 512 * 1024**2
ARCHIVE_PLAN_BYTES = 8 * 1024**2
EVIDENCE_INDEX_BYTES = 1024**2
CASE_RECEIPT_BYTES = 1024**2
INVERSE_INDEX_BYTES = 1024**2
NUMERICAL_INDEX_BYTES = 1024**2
PROLONGATION_WEIGHT_BYTES = 4 * 1024**2
MAX_INCIDENCE_ENTRIES = 1_000_000
INVERSE_EVIDENCE_BYTES = 37_068_136
MAX_KKT_FACTOR_NNZ = 2_171_202
MAX_INVERSE_EVIDENCE_BYTES_PER_CASE = 17_357_832
MAX_COMBINED_FACTOR_NNZ = 2_162_370
MAX_CANONICAL_FACTOR_BYTES = 67_108_864
MAX_EXACT_PRODUCT_PATHS = 50_000_000
MAX_EXACT_RESIDUAL_ENTRIES = 300_000
MAX_EXACT_FRACTION_BITS = 16_384
MAX_EXACT_CUMULATIVE_BITS = 100_000_000
MAX_EXACT_PYTHON_WORKSPACE_BYTES = 4_294_967_296
MAX_SECONDS_PER_CASE = 1_800
MAX_RSS_BYTES_PER_CASE = 6 * 1024**3
LAUNCH_CUTOFF_SECONDS = 7_200

ASSEMBLY_BUDGET = assembly.AssemblyBudget(
    max_trace_dofs=280,
    max_triplets=1_045_600,
    max_trace_integer_bits=8_000_000,
    max_work_bytes=268_435_456,
)
SYSTEM_BUDGET = certificate.SparseBudget(
    max_order=1_473,
    max_nnz=234_772,
    max_block_columns=4,
    max_work_bytes=67_108_864,
)
FACTOR_VALIDATION_BUDGET = certificate.SparseBudget(
    max_order=1_470,
    max_nnz=2_162_370,
    max_block_columns=1,
    max_work_bytes=277_536_256,
)


def resource_contract() -> tuple[tuple[str, int], ...]:
    """Complete ordered resource envelope bound by plans and registration."""
    return (
        ("graph_preflight_bytes", GRAPH_PREFLIGHT_BYTES),
        ("raw_archive_bytes", ARCHIVE_BYTES),
        ("archive_plan_bytes", ARCHIVE_PLAN_BYTES),
        ("evidence_index_bytes", EVIDENCE_INDEX_BYTES),
        ("case_receipt_bytes", CASE_RECEIPT_BYTES),
        ("inverse_index_bytes", INVERSE_INDEX_BYTES),
        ("numerical_index_bytes", NUMERICAL_INDEX_BYTES),
        ("prolongation_weight_bytes", PROLONGATION_WEIGHT_BYTES),
        ("max_incidence_entries", MAX_INCIDENCE_ENTRIES),
        ("assembly_max_trace_dofs", ASSEMBLY_BUDGET.max_trace_dofs),
        ("assembly_max_triplets", ASSEMBLY_BUDGET.max_triplets),
        ("assembly_max_trace_integer_bits", ASSEMBLY_BUDGET.max_trace_integer_bits),
        ("assembly_max_work_bytes", ASSEMBLY_BUDGET.max_work_bytes),
        ("system_max_order", SYSTEM_BUDGET.max_order),
        ("system_max_nnz", SYSTEM_BUDGET.max_nnz),
        ("system_max_block_columns", SYSTEM_BUDGET.max_block_columns),
        ("system_max_work_bytes", SYSTEM_BUDGET.max_work_bytes),
        ("factor_validation_max_order", FACTOR_VALIDATION_BUDGET.max_order),
        ("factor_validation_max_nnz", FACTOR_VALIDATION_BUDGET.max_nnz),
        ("factor_validation_max_block_columns", FACTOR_VALIDATION_BUDGET.max_block_columns),
        ("factor_validation_max_work_bytes", FACTOR_VALIDATION_BUDGET.max_work_bytes),
        ("max_kkt_factor_nnz", MAX_KKT_FACTOR_NNZ),
        ("max_inverse_evidence_bytes_per_case", MAX_INVERSE_EVIDENCE_BYTES_PER_CASE),
        ("max_combined_factor_nnz", MAX_COMBINED_FACTOR_NNZ),
        ("max_canonical_factor_bytes", MAX_CANONICAL_FACTOR_BYTES),
        ("max_exact_product_paths", MAX_EXACT_PRODUCT_PATHS),
        ("max_exact_residual_entries", MAX_EXACT_RESIDUAL_ENTRIES),
        ("max_exact_fraction_bits", MAX_EXACT_FRACTION_BITS),
        ("max_exact_cumulative_bits", MAX_EXACT_CUMULATIVE_BITS),
        ("max_exact_python_workspace_bytes", MAX_EXACT_PYTHON_WORKSPACE_BYTES),
        ("max_seconds_per_case", MAX_SECONDS_PER_CASE),
        ("max_rss_bytes_per_case", MAX_RSS_BYTES_PER_CASE),
        ("launch_cutoff_seconds", LAUNCH_CUTOFF_SECONDS),
        ("thread_cap", 1),
        ("supervisor_poll_milliseconds", 100),
        ("complete_inverse_evidence_bytes", INVERSE_EVIDENCE_BYTES),
    )


@dataclass(frozen=True, slots=True)
class ScientificCase:
    case_id: str
    degree: int
    level: int
    x_cells: int
    y_cells: int
    physical_dofs: int
    kkt_order: int
    station_intervals: int
    max_active_trace_dofs: int
    kkt_nnz: int
    assembly_triplets: int

    def __post_init__(self):
        values = (
            self.degree,
            self.level,
            self.x_cells,
            self.y_cells,
            self.physical_dofs,
            self.kkt_order,
            self.station_intervals,
            self.max_active_trace_dofs,
            self.kkt_nnz,
            self.assembly_triplets,
        )
        if (
            type(self.case_id) is not str
            or self.case_id not in {"Q1_L0", "Q1_L1", "Q1_L2", "Q2_L0", "Q2_L1"}
            or any(type(value) is not int for value in values)
            or self.degree not in (1, 2)
            or self.level not in (0, 1, 2)
            or any(value <= 0 for value in values[2:])
            or self.kkt_order != self.physical_dofs + 3
        ):
            raise ValueError("invalid frozen F03 scientific case")

    @property
    def inverse_evidence_bytes(self) -> int:
        return 8 * self.kkt_order * self.kkt_order


CASES = (
    ScientificCase("Q1_L0", 1, 0, 9, 5, 96, 99, 9, 40, 3_792, 12_112),
    ScientificCase("Q1_L1", 1, 1, 18, 10, 374, 377, 23, 96, 25_268, 112_656),
    ScientificCase("Q1_L2", 1, 2, 36, 20, 1_470, 1_473, 47, 240, 201_092, 1_045_600),
    ScientificCase("Q2_L0", 2, 0, 9, 5, 374, 377, 9, 108, 29_388, 75_492),
    ScientificCase("Q2_L1", 2, 1, 18, 10, 1_470, 1_473, 23, 280, 234_772, 852_000),
)

NESTED_TRANSITIONS = (
    ("Q1_L0", "Q1_L1"),
    ("Q1_L1", "Q1_L2"),
    ("Q1_L0", "Q2_L0"),
    ("Q2_L0", "Q2_L1"),
)
CROSS_FAMILY_COMPARISONS = (
    ("Q1_L1", "Q2_L0"),
    ("Q1_L2", "Q2_L1"),
)


@dataclass(frozen=True, slots=True, init=False)
class CasePreflight:
    schema: str
    case: ScientificCase
    topology_sha256: str
    graph_storage_bound_bytes: int
    one_csc_bound_bytes: int
    dense_factor_bound_bytes: int
    assembly_workspace_bytes: int

    def __init__(self, *args, **kwargs):
        raise TypeError("CasePreflight requires topology-only preflight factory")

    def _validate(self):
        if (
            self.schema != SCHEMA
            or type(self.case) is not ScientificCase
            or type(self.topology_sha256) is not str
            or len(self.topology_sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in self.topology_sha256)
            or any(
                type(value) is not int or value <= 0
                for value in (
                    self.graph_storage_bound_bytes,
                    self.one_csc_bound_bytes,
                    self.dense_factor_bound_bytes,
                    self.assembly_workspace_bytes,
                )
            )
        ):
            raise ValueError("invalid F03 scientific case preflight")


def _case_preflight(
    case: ScientificCase,
    topology_sha256: str,
    graph_storage_bound_bytes: int,
    one_csc_bound_bytes: int,
    dense_factor_bound_bytes: int,
    assembly_workspace_bytes: int,
) -> CasePreflight:
    result = object.__new__(CasePreflight)
    for name, value in (
        ("schema", SCHEMA),
        ("case", case),
        ("topology_sha256", topology_sha256),
        ("graph_storage_bound_bytes", graph_storage_bound_bytes),
        ("one_csc_bound_bytes", one_csc_bound_bytes),
        ("dense_factor_bound_bytes", dense_factor_bound_bytes),
        ("assembly_workspace_bytes", assembly_workspace_bytes),
    ):
        object.__setattr__(result, name, value)
    result._validate()
    return result


def midpoint_refine(cuts: tuple[Fraction, ...], levels: int) -> tuple[Fraction, ...]:
    """Insert exact midpoints without converting represented coordinates."""
    if (
        type(cuts) is not tuple
        or len(cuts) < 2
        or any(type(value) is not Fraction for value in cuts)
        or any(left >= right for left, right in zip(cuts, cuts[1:]))
        or type(levels) is not int
        or not 0 <= levels <= 2
    ):
        raise ValueError("bounded exact cuts and refinement level required")
    result = cuts
    for _ in range(levels):
        result = tuple(
            value
            for left, right in zip(result, result[1:])
            for value in (left, (left + right) / 2)
        ) + (result[-1],)
    return result


def case_by_id(case_id: str) -> ScientificCase:
    matches = tuple(case for case in CASES if case.case_id == case_id)
    if len(matches) != 1:
        raise ValueError("unknown F03 scientific case identity")
    return matches[0]


def compile_case(case: ScientificCase):
    if type(case) is not ScientificCase or case not in CASES:
        raise ValueError("registered F03 scientific case required")
    return topology.compile_grid(
        midpoint_refine(tuple(contract.X_CUTS), case.level),
        midpoint_refine(tuple(contract.Y_CUTS), case.level),
        case.degree,
        max_incidence_entries=MAX_INCIDENCE_ENTRIES,
    )


def preflight_case(case: ScientificCase) -> CasePreflight:
    """Recompute every frozen topology count before any numeric assembly."""
    grid = compile_case(case)
    graph = topology.incidence_envelope(grid, max_graph_bytes=GRAPH_PREFLIGHT_BYTES)
    work = assembly.preflight(grid, ASSEMBLY_BUDGET)
    observed = (
        len(grid.x_cuts) - 1,
        len(grid.y_cuts) - 1,
        graph["physical_free_dofs"],
        graph["physical_free_dofs"] + graph["root_multipliers"],
        graph["station_intervals"],
        graph["max_active_trace_dofs"],
        graph["kkt_nnz_envelope"],
        work["triplets_envelope"],
    )
    expected = (
        case.x_cells,
        case.y_cells,
        case.physical_dofs,
        case.kkt_order,
        case.station_intervals,
        case.max_active_trace_dofs,
        case.kkt_nnz,
        case.assembly_triplets,
    )
    if observed != expected:
        raise ValueError(f"frozen F03 case topology changed: {case.case_id}")
    if (
        case.kkt_order > SYSTEM_BUDGET.max_order
        or case.kkt_nnz > SYSTEM_BUDGET.max_nnz
        or case.inverse_evidence_bytes > MAX_INVERSE_EVIDENCE_BYTES_PER_CASE
        or work["workspace_estimate_bytes"] > ASSEMBLY_BUDGET.max_work_bytes
    ):
        raise ValueError(f"frozen F03 case exceeds protocol budget: {case.case_id}")
    return _case_preflight(
        case,
        composition._hash_grid(grid),
        graph["graph_storage_bound_bytes"],
        graph["one_csc_int64_values_bound_bytes"],
        graph["dense_L_plus_U_int64_values_bound_bytes"],
        work["workspace_estimate_bytes"],
    )


def preflight_inventory() -> tuple[CasePreflight, ...]:
    """Return the exact five-case admission inventory in launch order."""
    records = tuple(preflight_case(case) for case in CASES)
    if sum(record.case.inverse_evidence_bytes for record in records) != INVERSE_EVIDENCE_BYTES:
        raise ValueError("frozen F03 inverse evidence arithmetic changed")
    ids = tuple(record.case.case_id for record in records)
    if len(ids) != len(set(ids)) or ids != tuple(case.case_id for case in CASES):
        raise ValueError("invalid F03 launch inventory")
    return records


def inventory_sha256(records: tuple[CasePreflight, ...]) -> str:
    if type(records) is not tuple or len(records) != len(CASES):
        raise ValueError("complete ordered F03 preflight inventory required")
    fresh = tuple(preflight_case(case) for case in CASES)
    if records != fresh:
        raise ValueError("stale, fabricated or reordered F03 preflight inventory")
    digest = hashlib.sha256(b"F03_LOCAL_SCIENTIFIC_CASES_V1\0")
    for expected, record in zip(CASES, records):
        for value in (
            record.case.case_id,
            str(record.case.degree),
            str(record.case.level),
            str(record.case.kkt_order),
            str(record.case.kkt_nnz),
            str(record.case.assembly_triplets),
            str(record.case.inverse_evidence_bytes),
            record.topology_sha256,
            str(record.graph_storage_bound_bytes),
            str(record.one_csc_bound_bytes),
            str(record.dense_factor_bound_bytes),
            str(record.assembly_workspace_bytes),
        ):
            encoded = value.encode("ascii")
            digest.update(len(encoded).to_bytes(4, "little") + encoded)
    for name, value in resource_contract():
        encoded = name.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "little") + encoded)
        digest.update(value.to_bytes(8, "little"))
    return digest.hexdigest()
