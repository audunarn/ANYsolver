"""Pure, bounded comparisons of already validated F03 case snapshots.

This module neither reads evidence nor reconstructs mechanical observations.
The caller must bind each input to one replayed, sealed case receipt, and must
derive the expected exact prolongation from the frozen topology independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_functional as green
from scripts import _b3_e4_f03_local_prolongation as transfer
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_sparse_trace_binding as trace
from scripts import _b3_e4_f03_spatial_contract as spatial


NESTED_PAIRS = cases.NESTED_TRANSITIONS
CROSS_PAIR = ("Q1_L2", "Q2_L1")
PAIR_ORDER = (*NESTED_PAIRS, CROSS_PAIR)
SCALAR_LIMIT = 0.01
FUNCTIONAL_LIMIT = 0.01
RESOLUTION_LIMIT = 1e-10
ENERGY_LIMIT = 1e-10
INTEGRATION_LIMIT = 1e-11
TRACE_LIMIT = 1e-11
ACTION_LIMIT = 1e-11
MAX_UNION_INTERVALS = 128
MAX_FUNCTIONAL_BITS = 32_000_000
MAX_FUNCTIONAL_OPERATIONS = 1_000_000_000
MAX_FUNCTIONAL_WORK_BYTES = 128 * 1024**2
MAX_MATRIX_NNZ = 2_162_370
MAX_CASE_NNZ = 2_500_000
MAX_PRODUCT_PATHS = 50_000_000
MAX_MATRIX_WORK_BYTES = 1024**3


def _finite_array(value: object, shape: tuple[int, ...], label: str) -> np.ndarray:
    if (type(value) is not np.ndarray or value.dtype != np.float64
            or value.shape != shape or not value.flags.c_contiguous
            or not np.isfinite(value).all()):
        raise ValueError(f"finite contiguous F03 {label} required")
    return value


def _csr(value: object, shape: tuple[int, int], label: str) -> sparse.csr_matrix:
    if (type(value) is not sparse.csr_matrix or value.shape != shape
            or value.nnz > MAX_MATRIX_NNZ or not value.has_canonical_format
            or value.dtype != np.float64 or not np.isfinite(value.data).all()):
        raise ValueError(f"bounded canonical F03 {label} CSR required")
    return value


def _owned_vector(value: np.ndarray) -> np.ndarray:
    result = np.array(value, dtype=np.float64, copy=True, order="C")
    result.setflags(write=False)
    return result


def _owned_matrix(value: sparse.csr_matrix) -> sparse.csr_matrix:
    result = value.copy()
    for part in (result.data, result.indices, result.indptr):
        part.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class CaseData:
    case_id: str
    settling: receipt.SettlingRecord
    functional_record: receipt.FunctionalRecord
    functional: green.Functional
    q: np.ndarray
    shell: sparse.csr_matrix
    beam: sparse.csr_matrix
    root: sparse.csr_matrix
    load: np.ndarray
    ports: tuple[trace.SavedPort, ...]
    root_port: sparse.csr_matrix
    tip_port: sparse.csr_matrix
    free_slope: sparse.csr_matrix

    def __post_init__(self) -> None:
        if self.case_id not in {case.case_id for case in cases.CASES}:
            raise ValueError("frozen F03 case ID required")
        if (type(self.settling) is not receipt.SettlingRecord
                or type(self.functional_record) is not receipt.FunctionalRecord
                or type(self.functional) is not green.Functional):
            raise ValueError("validated F03 receipt observations and functional required")
        n = self.q.shape[0] if type(self.q) is np.ndarray and self.q.ndim == 1 else -1
        if n <= 0 or n > 1470:
            raise ValueError("bounded F03 physical state required")
        _finite_array(self.q, (n,), "state")
        _finite_array(self.load, (n,), "load")
        for name in ("shell", "beam"):
            _csr(getattr(self, name), (n, n), name)
        _csr(self.root, (3, n), "root")
        for name, rows in (("root_port", 3), ("tip_port", 3), ("free_slope", 1)):
            _csr(getattr(self, name), (rows, n), name)
        if type(self.ports) is not tuple or len(self.ports) != len(trace.KEYS):
            raise ValueError("complete common F03 trace-port inventory required")
        for sample, key in zip(self.ports, trace.KEYS):
            if (type(sample) is not trace.SavedPort
                    or (sample.station, sample.order, sample.side) != key):
                raise ValueError("common F03 trace-port key required")
            _csr(sample.operator, (3, n), "trace port")
            _finite_array(sample.action, (3,), "trace action")
        all_matrices = (self.shell, self.beam, self.root, self.root_port,
                        self.tip_port, self.free_slope,
                        *(sample.operator for sample in self.ports))
        if sum(matrix.nnz for matrix in all_matrices) > MAX_CASE_NNZ:
            raise ValueError("F03 cross-case matrix inventory exceeds case budget")
        object.__setattr__(self, "q", _owned_vector(self.q))
        object.__setattr__(self, "load", _owned_vector(self.load))
        for name in ("shell", "beam", "root", "root_port", "tip_port", "free_slope"):
            object.__setattr__(self, name, _owned_matrix(getattr(self, name)))
        object.__setattr__(self, "ports", tuple(
            trace.SavedPort(sample.station, sample.order, sample.side,
                            _owned_matrix(sample.operator), _owned_vector(sample.action))
            for sample in self.ports
        ))


@dataclass(frozen=True, slots=True)
class PairResult:
    pair: tuple[str, str]
    nested: bool
    passed: bool
    failures: tuple[str, ...]
    scalar_relatives: tuple[float, ...]
    scalar_changes: tuple[float, ...]
    functional_first_norm: float | None
    functional_second_norm: float | None
    functional_difference_norm: float | None
    functional_relative: float | None
    functional_resolution: float | None
    energy_distance: float | None
    energy_defect_relative: float | None
    compatibility: tuple[tuple[str, float], ...]
    functional_preflight: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ChainResult:
    passed: bool
    failures: tuple[str, ...]
    pairs: tuple[PairResult, ...]


def same_prolongation(
    saved: transfer.ExactProlongation,
    rederived: transfer.ExactProlongation,
) -> bool:
    """Compare exact sparse entries, order, dimensions and Fraction weights."""
    if type(saved) is not transfer.ExactProlongation or type(rederived) is not transfer.ExactProlongation:
        raise ValueError("two exact F03 prolongations required")
    return (
        saved.source_dofs == rederived.source_dofs
        and saved.target_dofs == rederived.target_dofs
        and saved.integer_bits == rederived.integer_bits
        and np.array_equal(saved.rows, rederived.rows)
        and np.array_equal(saved.columns, rederived.columns)
        and saved.weights == rederived.weights
    )


def _maximum(matrix: sparse.csr_matrix) -> int:
    if matrix.shape[0] == 0:
        return 0
    return int(max(np.diff(matrix.indptr), default=0))


def _admit_product(left: sparse.csr_matrix, right: sparse.csr_matrix) -> None:
    if left.shape[1] != right.shape[0]:
        raise ValueError("incompatible F03 sparse product")
    paths = left.nnz * max(1, _maximum(right))
    if paths > MAX_PRODUCT_PATHS or 24 * paths > MAX_MATRIX_WORK_BYTES:
        raise ValueError("F03 cross-case sparse product exceeds work budget")


def _product(left: sparse.csr_matrix, right: sparse.csr_matrix) -> sparse.csr_matrix:
    _admit_product(left, right)
    result = (left @ right).tocsr()
    if result.nnz > MAX_MATRIX_NNZ or not np.isfinite(result.data).all():
        raise ValueError("F03 cross-case sparse product exceeds evidence envelope")
    result.sum_duplicates()
    result.sort_indices()
    return result


def _frobenius(value: sparse.csr_matrix) -> float:
    norm = float(np.linalg.norm(value.data))
    if not math.isfinite(norm):
        raise ValueError("nonfinite F03 sparse norm")
    return norm


def _matrix_ratio(first: sparse.csr_matrix, second: sparse.csr_matrix) -> float:
    if first.shape != second.shape:
        raise ValueError("incompatible F03 saved matrix shapes")
    diff = (first - second).tocsr()
    if diff.nnz > MAX_MATRIX_NNZ or not np.isfinite(diff.data).all():
        raise ValueError("F03 sparse difference exceeds evidence envelope")
    a, b, d = _frobenius(first), _frobenius(second), _frobenius(diff)
    denominator = max(a, b)
    return 0.0 if denominator == 0.0 else d / denominator


def _matrix_absolute(first: sparse.csr_matrix, second: sparse.csr_matrix) -> float:
    if first.shape != second.shape:
        raise ValueError("incompatible F03 saved matrix shapes")
    diff = (first - second).tocsr()
    if diff.nnz > MAX_MATRIX_NNZ or not np.isfinite(diff.data).all():
        raise ValueError("F03 sparse difference exceeds evidence envelope")
    return float(np.max(np.abs(diff.data))) if diff.nnz else 0.0


def _vector_ratio(first: np.ndarray, second: np.ndarray) -> float:
    if first.shape != second.shape:
        raise ValueError("incompatible F03 saved vector shapes")
    norms = tuple(float(np.linalg.norm(value)) for value in (first, second, first - second))
    if not all(math.isfinite(value) for value in norms):
        raise ValueError("nonfinite F03 vector norm")
    return 0.0 if max(norms[:2]) == 0.0 else norms[2] / max(norms[:2])


def _vector_absolute(first: np.ndarray, second: np.ndarray) -> float:
    if first.shape != second.shape:
        raise ValueError("incompatible F03 saved action shapes")
    value = float(np.max(np.abs(first - second))) if first.size else 0.0
    if not math.isfinite(value):
        raise ValueError("nonfinite F03 saved action difference")
    return value


def _functional_preflight(first: green.Functional, second: green.Functional) -> tuple[tuple[str, int], ...]:
    union = tuple(sorted(set(first.cuts + second.cuts)))
    intervals = len(union) - 1
    if intervals <= 0 or intervals > min(MAX_UNION_INTERVALS, green.UNION_INTERVALS):
        raise ValueError("F03 functional union interval cap exceeded")
    values = (*first.cuts, *second.cuts, *first.cosine, *second.cosine,
              *(v for row in first.atoms + second.atoms for v in row),
              *(v for functional in (first, second) for row in functional.coefficients
                for channel in row for v in channel))
    bits = sum(v.numerator.bit_length() + v.denominator.bit_length() for v in values)
    if bits > MAX_FUNCTIONAL_BITS:
        raise ValueError("F03 functional input integer-bit cap exceeded")
    operations = 2 * 3 * intervals * (64**2 * 96 + 64 * 96) + 16_384
    count = len(union) + 18 * intervals + 9
    workspace = (2 * count * (512 + (2 * green.DERIVED_INTEGER_BITS + 7) // 8)
                 + 64**2 * 8 * 96 + intervals * 3 * 8 * 256 + 65_536)
    if operations > MAX_FUNCTIONAL_OPERATIONS or workspace > MAX_FUNCTIONAL_WORK_BYTES:
        raise ValueError("F03 functional operation or workspace cap exceeded")
    return (("union_intervals", intervals), ("input_integer_bits", bits),
            ("operations_estimate", operations), ("workspace_estimate_bytes", workspace))


def _record_norm(record: receipt.FunctionalRecord) -> float:
    if not record.numerically_admissible:
        raise ValueError("inadmissible saved F03 functional observation")
    deltas = []
    for a, b in zip((*record.channels[:3], *record.totals[:1]),
                    (*record.channels[3:], *record.totals[1:])):
        assert a is not None and b is not None
        deltas.append(abs(a - b) / max(abs(a), abs(b), 1000.0**2))
    if max(deltas) > RESOLUTION_LIMIT:
        raise ValueError("unresolved saved F03 functional observation")
    total = record.totals[1]
    assert total is not None
    return math.sqrt(total)


def _difference_norm(value: green.Functional) -> tuple[float | None, float | None, tuple[str, ...]]:
    observations = tuple(green.norm_observation_at_order(value, order) for order in (48, 64))
    failures = []
    for item in observations:
        if (not item["admissible"] or not all(item["channel_finite"])
                or not all(item["channel_nonnegative"])
                or not all(item["channel_nonzero_valid"])
                or not item["total_finite"] or not item["total_nonnegative"]
                or item["failures"]):
            failures.append(f"difference Green observation at order {item['order']} is inadmissible")
    if failures:
        return None, None, tuple(failures)
    first, second = observations
    values = tuple(zip((*first["channels"], first["squared_norm"]),
                       (*second["channels"], second["squared_norm"])))
    resolution = max(abs(a - b) / max(abs(a), abs(b), 1000.0**2) for a, b in values)
    if not math.isfinite(resolution) or resolution > RESOLUTION_LIMIT:
        return None, resolution, ("difference Green 48/64 resolution exceeds 1e-10",)
    squared = second["squared_norm"]
    if squared is None or squared < 0 or not math.isfinite(squared):
        return None, resolution, ("difference Green norm is unavailable",)
    return math.sqrt(squared), resolution, ()


def _nested_compatibility(coarse: CaseData, fine: CaseData,
                          p: sparse.csr_matrix) -> tuple[tuple[str, float], ...]:
    pt = p.T.tocsr()
    out = []
    for name in ("shell", "beam"):
        fine_block = getattr(fine, name)
        coarse_block = getattr(coarse, name)
        transformed = _product(pt, _product(fine_block, p))
        out.append((f"{name}_stiffness", _matrix_ratio(transformed, coarse_block)))
    out.append(("load", _vector_ratio(np.asarray(pt @ fine.load).reshape(-1), coarse.load)))
    root = _product(fine.root, p)
    out.extend((("root", _matrix_ratio(root, coarse.root)),
                ("root_absolute", _matrix_absolute(root, coarse.root))))
    for index, (f, c) in enumerate(zip(fine.ports, coarse.ports)):
        projected = _product(f.operator, p)
        out.extend(((f"trace_{index:02d}", _matrix_ratio(projected, c.operator)),
                    (f"trace_{index:02d}_absolute", _matrix_absolute(projected, c.operator)),
                    (f"trace_{index:02d}_coarse_saved_action_absolute",
                     _vector_absolute(np.asarray(c.operator @ coarse.q).reshape(-1), c.action)),
                    (f"trace_{index:02d}_fine_saved_action_absolute",
                     _vector_absolute(np.asarray(f.operator @ fine.q).reshape(-1), f.action)),
                    (f"trace_{index:02d}_common_action_absolute",
                     _vector_absolute(np.asarray(projected @ coarse.q).reshape(-1), c.action))))
    for name in ("root_port", "tip_port", "free_slope"):
        projected = _product(getattr(fine, name), p)
        coarse_port = getattr(coarse, name)
        out.extend(((name, _matrix_ratio(projected, coarse_port)),
                    (f"{name}_absolute", _matrix_absolute(projected, coarse_port))))
    return tuple(out)


def compare_pair(
    coarse: CaseData, fine: CaseData, *,
    saved_prolongation: transfer.ExactProlongation | None = None,
    rederived_prolongation: transfer.ExactProlongation | None = None,
) -> PairResult:
    """Compare one frozen pair; failed predicates remain explicit in the result."""
    if type(coarse) is not CaseData or type(fine) is not CaseData:
        raise ValueError("two validated F03 saved case snapshots required")
    pair = (coarse.case_id, fine.case_id)
    if pair not in PAIR_ORDER:
        raise ValueError("only frozen F03 settling pairs are admissible")
    nested = pair in NESTED_PAIRS
    if nested != (saved_prolongation is not None and rederived_prolongation is not None):
        raise ValueError("nested pair needs saved and independently rederived exact transfer")
    failures = []
    changes = tuple(abs(f - c) for c, f in zip(coarse.settling.values, fine.settling.values))
    relatives = tuple(d / max(abs(c), abs(f), 1e-3 * scale)
                      for d, c, f, scale in zip(changes, coarse.settling.values,
                                                fine.settling.values, coarse.settling.scales))
    failures.extend(f"scalar {receipt.SETTLING_NAMES[index]} exceeds 1%"
                    for index, value in enumerate(relatives) if value > SCALAR_LIMIT)

    preflight = _functional_preflight(coarse.functional, fine.functional)
    first_norm = second_norm = diff_norm = relative = resolution = None
    try:
        first_norm = _record_norm(coarse.functional_record)
        second_norm = _record_norm(fine.functional_record)
    except ValueError as exc:
        failures.append(str(exc))
    diff = green.difference(fine.functional, coarse.functional)
    diff_norm, resolution, norm_failures = _difference_norm(diff)
    failures.extend(norm_failures)
    if None not in (first_norm, second_norm, diff_norm):
        assert first_norm is not None and second_norm is not None and diff_norm is not None
        relative = diff_norm / max(first_norm, second_norm, 1000.0)
        if relative > FUNCTIONAL_LIMIT:
            failures.append("complete signed functional difference exceeds 1%")

    compatibility = ()
    distance = defect = None
    if nested:
        assert saved_prolongation is not None and rederived_prolongation is not None
        if not same_prolongation(saved_prolongation, rederived_prolongation):
            failures.append("saved exact prolongation disagrees with frozen topology")
        else:
            if (saved_prolongation.source_dofs != coarse.q.size
                    or saved_prolongation.target_dofs != fine.q.size):
                raise ValueError("F03 exact transfer dimensions disagree with physical states")
            p = saved_prolongation.matrix()
            compatibility = _nested_compatibility(coarse, fine, p)
            for name, value in compatibility:
                limit = (ACTION_LIMIT if name.endswith("_absolute")
                         else INTEGRATION_LIMIT if name in
                         ("shell_stiffness", "beam_stiffness", "load", "root")
                         else TRACE_LIMIT)
                if value > limit:
                    failures.append(f"nested {name} saved action disagrees with coarse space")
            delta = fine.q - p @ coarse.q
            fine_k_delta = fine.shell @ delta + fine.beam @ delta
            distance = 0.5 * float(np.dot(delta, fine_k_delta))
            e_c, e_f = coarse.settling.values[14], fine.settling.values[14]
            e0 = float(spatial.E0)
            if not all(math.isfinite(value) for value in (distance, e_c, e_f)):
                raise ValueError("finite F03 nested energy required")
            if distance < 0.0:
                failures.append("nested Ritz distance is negative")
            if e_f < e_c - ENERGY_LIMIT * e0:
                failures.append("nested Ritz total energy decreased")
            defect = abs((e_f - e_c) - distance) / max(e0, abs(e_c) + abs(e_f) + abs(distance))
            if defect > ENERGY_LIMIT:
                failures.append("nested Ritz energy identity exceeds 1e-10")
    return PairResult(pair, nested, not failures, tuple(failures), relatives, changes,
                      first_norm, second_norm, diff_norm, relative, resolution,
                      distance, defect, compatibility, preflight)


def compare_chains(pairs: tuple[PairResult, ...]) -> ChainResult:
    """Check both two-transition chains and the sole gating cross-family pair."""
    if (type(pairs) is not tuple or len(pairs) != len(PAIR_ORDER)
            or tuple(item.pair for item in pairs if type(item) is PairResult) != PAIR_ORDER
            or any(type(item) is not PairResult for item in pairs)):
        raise ValueError("complete ordered F03 pair inventory required")
    failures = [f"{a}/{b}: {reason}" for item in pairs for reason in item.failures
                for a, b in (item.pair,)]
    for item in pairs:
        if item.nested != (item.pair in NESTED_PAIRS) or not item.passed and not item.failures:
            failures.append(f"{item.pair}: invalid pair disposition")
    for first_index, second_index in ((0, 1), (2, 3)):
        first, second = pairs[first_index], pairs[second_index]
        for index, (earlier, later, scale) in enumerate(zip(
            first.scalar_changes, second.scalar_changes, receipt.SETTLING_SCALES,
        )):
            if later > earlier + 1e-5 * scale:
                failures.append(f"{second.pair}: scalar {receipt.SETTLING_NAMES[index]} does not settle")
        if (first.functional_difference_norm is None or second.functional_difference_norm is None):
            failures.append(f"{second.pair}: functional chain norm unavailable")
        elif second.functional_difference_norm > first.functional_difference_norm + 10.0:
            failures.append(f"{second.pair}: functional difference does not settle")
    return ChainResult(not failures, tuple(failures), pairs)
