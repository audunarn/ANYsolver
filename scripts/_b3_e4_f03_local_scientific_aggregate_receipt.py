"""Exclusive, canonical, solve-free F03 aggregate decision receipt.

This codec records registered identities and already computed comparisons.  It
does not read cases, create snapshots, or perform mechanical work.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from scripts import _b3_e4_f03_local_scientific_case_receipt as case_receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_math as cross_math
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence
from scripts import _b3_e4_f03_local_scientific_registration as registration
from scripts import _b3_e4_f03_sparse_trace_binding as trace


SCHEMA = "f03_local_scientific_aggregate_receipt_v1"
FILENAME = "aggregate_receipt.json"
MAX_BYTES = 1024 * 1024
MAX_TEXT = 4096
MAX_CASE_REASON = 2048
MAX_REASON_COUNT = 4096
MAX_ABSOLUTE_FLOAT = 1e300
PREDICATE_NAMES = tuple(f"{coarse}/{fine}" for coarse, fine in cross_math.PAIR_ORDER) + ("chain",)
DISPOSITIONS = ("PASSED", "FAILED", "NOT_EVALUATED")
CASE_STATUSES = ("MISSING", "READY_FOR_REPLAY", *case_receipt.CASE_STATUSES)
WORK_NAMES = (
    "cross_factorizations", "cross_solves", "cross_element_assemblies", "cross_recoveries",
)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_PREFLIGHT_LIMITS = (
    ("union_intervals", cross_math.MAX_UNION_INTERVALS),
    ("input_integer_bits", cross_math.MAX_FUNCTIONAL_BITS),
    ("operations_estimate", cross_math.MAX_FUNCTIONAL_OPERATIONS),
    ("workspace_estimate_bytes", cross_math.MAX_FUNCTIONAL_WORK_BYTES),
)
_COMPATIBILITY_NAMES = (
    "shell_stiffness", "beam_stiffness", "load", "root", "root_absolute",
    *(name for index in range(len(trace.KEYS)) for name in (
        f"trace_{index:02d}", f"trace_{index:02d}_absolute",
        f"trace_{index:02d}_coarse_saved_action_absolute",
        f"trace_{index:02d}_fine_saved_action_absolute",
        f"trace_{index:02d}_common_action_absolute",
    )),
    "root_port", "root_port_absolute", "tip_port", "tip_port_absolute",
    "free_slope", "free_slope_absolute",
)


def _digest(value: object) -> bool:
    return type(value) is str and _DIGEST.fullmatch(value) is not None


def _optional_digest(value: object) -> bool:
    return value is None or _digest(value)


def _reasons(value: object, *, empty: bool = True) -> None:
    if (type(value) is not tuple or len(value) > MAX_REASON_COUNT or
            (not empty and not value) or any(
                type(item) is not str or not item or len(item) > MAX_TEXT
                or any(ord(char) < 32 for char in item) for item in value)):
        raise ValueError("bounded F03 aggregate reasons required")


def _number(value: object, *, nonnegative: bool = True) -> bool:
    return (type(value) is float and math.isfinite(value)
            and abs(value) <= MAX_ABSOLUTE_FLOAT
            and (not nonnegative or value >= 0.0))


@dataclass(frozen=True, slots=True)
class CaseRecord:
    case_id: str
    plan_archive_sha256: str
    case_receipt_sha256: str | None
    status: str
    evidence_index_sha256: str | None
    numerical_index_sha256: str | None
    inverse_index_sha256: str | None
    exact_prolongation_sha256: str | None
    reason: str | None = None

    def __post_init__(self) -> None:
        if (self.case_id not in {case.case_id for case in cases.CASES}
                or not _digest(self.plan_archive_sha256)
                or not all(_optional_digest(getattr(self, name)) for name in (
                    "case_receipt_sha256", "evidence_index_sha256",
                    "numerical_index_sha256", "inverse_index_sha256",
                    "exact_prolongation_sha256"))
                or self.status not in CASE_STATUSES
                or (self.status == "MISSING" and self.case_receipt_sha256 is not None)
                or (self.status not in ("MISSING", "FAILED_EVIDENCE")
                    and self.case_receipt_sha256 is None)
                or (self.status == "PASSED_CASE_NUMERICAL_SCREEN" and any(
                    getattr(self, name) is None for name in (
                        "case_receipt_sha256", "evidence_index_sha256",
                        "numerical_index_sha256", "inverse_index_sha256")))
                or (self.reason is not None and (
                    type(self.reason) is not str or not self.reason
                    or len(self.reason) > MAX_CASE_REASON
                    or any(ord(char) < 32 for char in self.reason)))
                or ((self.status in ("READY_FOR_REPLAY", "PASSED_CASE_NUMERICAL_SCREEN"))
                    != (self.reason is None))):
            raise ValueError("invalid F03 aggregate case record")


def _validate_pair_result(result: cross_math.PairResult) -> None:
    if type(result) is not cross_math.PairResult:
        raise ValueError("complete F03 pair result required")
    if (type(result.nested) is not bool or result.nested != (result.pair in cross_math.NESTED_PAIRS)
            or type(result.passed) is not bool):
        raise ValueError("invalid F03 pair disposition")
    _reasons(result.failures, empty=result.passed)
    if result.passed == bool(result.failures):
        raise ValueError("F03 pair pass/failure contradiction")
    for name in ("scalar_relatives", "scalar_changes"):
        numbers = getattr(result, name)
        if (type(numbers) is not tuple or len(numbers) != len(case_receipt.SETTLING_NAMES)
                or any(not _number(item) for item in numbers)):
            raise ValueError("complete finite F03 scalar comparison required")
    for name in (
        "functional_first_norm", "functional_second_norm", "functional_difference_norm",
        "functional_relative", "functional_resolution", "energy_defect_relative",
    ):
        value = getattr(result, name)
        if value is not None and not _number(value):
            raise ValueError("finite F03 functional or energy result required")
    if result.energy_distance is not None and not _number(result.energy_distance, nonnegative=False):
        raise ValueError("finite F03 Ritz distance required")
    if (not result.nested and (result.energy_distance is not None
                               or result.energy_defect_relative is not None
                               or result.compatibility)):
        raise ValueError("cross-family F03 result cannot claim nesting")
    if (type(result.compatibility) is not tuple
            or tuple(name for name, _ in result.compatibility) not in ((), _COMPATIBILITY_NAMES)
            or any(not _number(value) for _, value in result.compatibility)):
        raise ValueError("invalid F03 nested compatibility inventory")
    if (type(result.functional_preflight) is not tuple
            or tuple(name for name, _ in result.functional_preflight)
            != tuple(name for name, _ in _PREFLIGHT_LIMITS)
            or any(type(value) is not int or not 0 < value <= limit
                   for (_, value), (_, limit) in zip(result.functional_preflight, _PREFLIGHT_LIMITS))):
        raise ValueError("invalid F03 functional preflight budget")
    def _compatibility_exceeds() -> bool:
        for name, value in result.compatibility:
            limit = (cross_math.ACTION_LIMIT if name.endswith("_absolute")
                     else cross_math.INTEGRATION_LIMIT if name in (
                         "shell_stiffness", "beam_stiffness", "load", "root")
                     else cross_math.TRACE_LIMIT)
            if value > limit:
                return True
        return False

    if result.passed and (
        any(value > cross_math.SCALAR_LIMIT for value in result.scalar_relatives)
        or any(getattr(result, name) is None for name in (
            "functional_first_norm", "functional_second_norm",
            "functional_difference_norm", "functional_relative", "functional_resolution"))
        or result.functional_relative > cross_math.FUNCTIONAL_LIMIT
        or result.functional_resolution > cross_math.RESOLUTION_LIMIT
        or _compatibility_exceeds()
        or (result.nested and (
            result.energy_distance is None or result.energy_distance < 0
            or result.energy_defect_relative is None
            or result.energy_defect_relative > cross_math.ENERGY_LIMIT
            or tuple(name for name, _ in result.compatibility) != _COMPATIBILITY_NAMES
        ))):
        raise ValueError("passing F03 pair lacks required valid observations")


@dataclass(frozen=True, slots=True)
class PairRecord:
    pair: tuple[str, str]
    result: cross_math.PairResult | None

    def __post_init__(self) -> None:
        if (type(self.pair) is not tuple or self.pair not in cross_math.PAIR_ORDER
                or (self.result is not None and self.result.pair != self.pair)):
            raise ValueError("invalid F03 aggregate pair")
        if self.result is not None:
            _validate_pair_result(self.result)


@dataclass(frozen=True, slots=True)
class PredicateRecord:
    name: str
    disposition: str
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.name not in PREDICATE_NAMES or self.disposition not in DISPOSITIONS:
            raise ValueError("invalid F03 aggregate predicate")
        _reasons(self.reasons, empty=self.disposition != "FAILED")
        if self.disposition != "FAILED" and self.reasons:
            raise ValueError("unevaluated/passing F03 predicate has failures")


def _expected_status(value: "AggregateReceipt") -> tuple[str, tuple[str, ...]]:
    statuses = tuple(item.status for item in value.cases)
    case_reasons = tuple(
        f"{item.case_id}: {item.status}" +
        (f": {item.reason}" if item.reason is not None else "")
        for item in value.cases
        if item.status not in ("PASSED_CASE_NUMERICAL_SCREEN", "READY_FOR_REPLAY")
    )
    for terminal in registration.TERMINAL_PRECEDENCE[:4]:
        if terminal == "FAILED_EVIDENCE":
            matches = tuple(item for item in value.cases if item.status in ("MISSING", terminal))
        else:
            matches = tuple(item for item in value.cases if item.status == terminal)
        if matches:
            return terminal, case_reasons
    if "READY_FOR_REPLAY" in statuses:
        return "FAILED_EVIDENCE", case_reasons or ("aggregate case replay incomplete",)
    if all(status == "PASSED_CASE_NUMERICAL_SCREEN" for status in statuses):
        results = tuple(item.result for item in value.pairs)
        if all(result is not None for result in results):
            chain = cross_math.compare_chains(results)
            if chain.passed:
                return "PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN", ()
            return "UNRESOLVED_LOCAL_REFERENCE", chain.failures
        if (value.status == "FAILED_EVIDENCE" and value.reasons
                and all(result is None for result in results)):
            return "FAILED_EVIDENCE", value.reasons
        raise ValueError("complete F03 case replay requires a cross-case result or evidence failure")
    raise ValueError("invalid F03 case terminal inventory")


@dataclass(frozen=True, slots=True)
class AggregateReceipt:
    schema: str
    source_commit: str
    registration_sha256: str
    comparator_sha256: str
    sources: tuple[registration.SourceIdentity, ...]
    process_limits: tuple[tuple[str, str], ...]
    resource_limits: tuple[tuple[str, int], ...]
    tolerances: tuple[tuple[str, str], ...]
    cases: tuple[CaseRecord, ...]
    pairs: tuple[PairRecord, ...]
    predicates: tuple[PredicateRecord, ...]
    status: str
    reasons: tuple[str, ...]
    cross_factorizations: int
    cross_solves: int
    cross_element_assemblies: int
    cross_recoveries: int

    def __post_init__(self) -> None:
        if (
            self.schema != SCHEMA or type(self.source_commit) is not str
            or _COMMIT.fullmatch(self.source_commit) is None
            or not _digest(self.registration_sha256) or not _digest(self.comparator_sha256)
            or type(self.sources) is not tuple
            or any(type(item) is not registration.SourceIdentity for item in self.sources)
            or tuple((item.role, item.path) for item in self.sources) != registration.SOURCE_ROLES
            or self.comparator_sha256 != next(item.sha256 for item in self.sources
                                              if item.role == "cross_math")
            or self.process_limits != registration.process_contract()
            or self.resource_limits != registration.resource_contract()
            or self.tolerances != registration.tolerance_contract()
            or type(self.cases) is not tuple
            or tuple(item.case_id for item in self.cases if type(item) is CaseRecord)
               != tuple(case.case_id for case in cases.CASES)
            or len(self.cases) != len(cases.CASES)
            or type(self.pairs) is not tuple
            or tuple(item.pair for item in self.pairs if type(item) is PairRecord)
               != cross_math.PAIR_ORDER
            or len(self.pairs) != len(cross_math.PAIR_ORDER)
            or type(self.predicates) is not tuple
            or tuple(item.name for item in self.predicates if type(item) is PredicateRecord)
               != PREDICATE_NAMES
            or len(self.predicates) != len(PREDICATE_NAMES)
            or any(type(getattr(self, name)) is not int or getattr(self, name) != 0
                   for name in WORK_NAMES)
            or self.status not in registration.TERMINAL_PRECEDENCE
        ):
            raise ValueError("invalid F03 aggregate receipt inventory")
        _reasons(self.reasons, empty=self.status == "PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN")
        results = tuple(item.result for item in self.pairs)
        nested_targets = {fine for _, fine in cross_math.NESTED_PAIRS}
        if any(item.case_id not in nested_targets
               and item.exact_prolongation_sha256 is not None
               for item in self.cases):
            raise ValueError("coarsest F03 case cannot claim exact prolongation")
        all_cases_pass = all(item.status == "PASSED_CASE_NUMERICAL_SCREEN"
                             for item in self.cases)
        if (any(item is not None for item in results) and
                (not all_cases_pass or any(item is None for item in results))):
            raise ValueError("partial F03 cross-case comparison prohibited")
        if all_cases_pass and all(item is not None for item in results):
            for item in self.cases:
                if ((item.case_id in nested_targets)
                        != (item.exact_prolongation_sha256 is not None)):
                    raise ValueError("F03 exact prolongation hash disagrees with topology")
            chain = cross_math.compare_chains(results)
            expected_predicates = tuple(PredicateRecord(
                name, "PASSED" if result.passed else "FAILED", result.failures,
            ) for name, result in zip(PREDICATE_NAMES[:-1], results)) + (
                PredicateRecord("chain", "PASSED" if chain.passed else "FAILED", chain.failures),
            )
        else:
            expected_predicates = tuple(PredicateRecord(name, "NOT_EVALUATED", ())
                                        for name in PREDICATE_NAMES)
        expected_status, expected_reasons = _expected_status(self)
        if (self.predicates != expected_predicates or self.status != expected_status
                or self.reasons != expected_reasons):
            raise ValueError("F03 aggregate predicates or terminal precedence disagree")


def _plain(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_plain(item) for item in value]
    return value


def _payload(value: AggregateReceipt) -> bytes:
    if type(value) is not AggregateReceipt:
        raise ValueError("validated F03 aggregate receipt required")
    # Revalidate after construction, even though the dataclass is frozen.
    value.__post_init__()
    payload = (json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
    if len(payload) > MAX_BYTES:
        raise ValueError("F03 aggregate receipt exceeds 1 MiB")
    return payload


def _object(raw: object, cls: type) -> dict:
    if type(raw) is not dict or set(raw) != {field.name for field in fields(cls)}:
        raise ValueError(f"invalid F03 {cls.__name__} fields")
    return raw


def _pairs(raw: object, *, item_types: tuple[type, type]) -> tuple:
    if type(raw) is not list or any(type(item) is not list or len(item) != 2
                                    or any(type(part) is not expected
                                           for part, expected in zip(item, item_types))
                                    for item in raw):
        raise ValueError("invalid F03 ordered pair inventory")
    return tuple(tuple(item) for item in raw)


def _tuple(raw: object, *, count: int | None = None) -> tuple:
    if type(raw) is not list or (count is not None and len(raw) != count):
        raise ValueError("invalid F03 ordered array")
    return tuple(raw)


def _decode_pair_result(raw: object) -> cross_math.PairResult:
    record = _object(raw, cross_math.PairResult)
    return cross_math.PairResult(
        pair=_tuple(record["pair"], count=2), nested=record["nested"],
        passed=record["passed"], failures=_tuple(record["failures"]),
        scalar_relatives=_tuple(record["scalar_relatives"]),
        scalar_changes=_tuple(record["scalar_changes"]),
        functional_first_norm=record["functional_first_norm"],
        functional_second_norm=record["functional_second_norm"],
        functional_difference_norm=record["functional_difference_norm"],
        functional_relative=record["functional_relative"],
        functional_resolution=record["functional_resolution"],
        energy_distance=record["energy_distance"],
        energy_defect_relative=record["energy_defect_relative"],
        compatibility=_pairs(record["compatibility"], item_types=(str, float)),
        functional_preflight=_pairs(record["functional_preflight"], item_types=(str, int)),
    )


def _decode(payload: bytes) -> AggregateReceipt:
    if type(payload) is not bytes or len(payload) > MAX_BYTES:
        raise ValueError("invalid bounded F03 aggregate payload")
    try:
        raw = json.loads(payload.decode("ascii"), parse_constant=lambda _: (_ for _ in ()).throw(
            ValueError("nonfinite JSON number")))
        data = _object(raw, AggregateReceipt)
        sources = tuple(registration.SourceIdentity(**_object(item, registration.SourceIdentity))
                        for item in _tuple(data["sources"]))
        case_items = tuple(CaseRecord(**_object(item, CaseRecord))
                           for item in _tuple(data["cases"]))
        pair_items = tuple(PairRecord(
            pair=_tuple(item["pair"], count=2),
            result=None if item["result"] is None else _decode_pair_result(item["result"]),
        ) for entry in _tuple(data["pairs"]) for item in (_object(entry, PairRecord),))
        predicates = tuple(PredicateRecord(
            name=item["name"], disposition=item["disposition"],
            reasons=_tuple(item["reasons"]),
        ) for entry in _tuple(data["predicates"])
            for item in (_object(entry, PredicateRecord),))
        value = AggregateReceipt(
            schema=data["schema"], source_commit=data["source_commit"],
            registration_sha256=data["registration_sha256"],
            comparator_sha256=data["comparator_sha256"], sources=sources,
            process_limits=_pairs(data["process_limits"], item_types=(str, str)),
            resource_limits=_pairs(data["resource_limits"], item_types=(str, int)),
            tolerances=_pairs(data["tolerances"], item_types=(str, str)),
            cases=case_items, pairs=pair_items, predicates=predicates,
            status=data["status"], reasons=_tuple(data["reasons"]),
            **{name: data[name] for name in WORK_NAMES},
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError, AttributeError,
            OverflowError) as exc:
        raise ValueError("invalid F03 aggregate JSON") from exc
    if _payload(value) != payload:
        raise ValueError("noncanonical F03 aggregate encoding")
    return value


def write_receipt(run_root: Path, value: AggregateReceipt) -> str:
    run_root = Path(run_root)
    if not run_root.is_dir() or run_root.is_symlink():
        raise ValueError("owned F03 run directory required")
    payload = _payload(value)
    with (run_root / FILENAME).open("xb") as stream:
        stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def read_receipt(run_root: Path, expected_regsha: str) -> tuple[AggregateReceipt, str]:
    run_root = Path(run_root)
    if not _digest(expected_regsha) or not run_root.is_dir() or run_root.is_symlink():
        raise ValueError("owned F03 run directory and registration digest required")
    path = run_root / FILENAME
    path_stat = path.lstat()
    if not stat.S_ISREG(path_stat.st_mode) or path_stat.st_nlink != 1:
        raise ValueError("regular owned F03 aggregate receipt required")
    # Windows fstat can report a different ctime for the same file.  Bind
    # ctime on each API's own before/after snapshots, and match the stable
    # cross-API identity separately.
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size,
                              value.st_mtime_ns)
    with evidence._open_no_follow(path) as stream:
        opened = os.fstat(stream.fileno())
        if identity(opened) != identity(path_stat):
            raise ValueError("F03 aggregate receipt changed before read")
        payload = stream.read(MAX_BYTES + 1)
        observed = os.fstat(stream.fileno())
        if (not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1
                or observed.st_size != len(payload)
                or identity(observed) != identity(opened)
                or observed.st_ctime_ns != opened.st_ctime_ns):
            raise ValueError("stable owned F03 aggregate receipt required")
    after = path.lstat()
    if identity(after) != identity(observed) or after.st_ctime_ns != path_stat.st_ctime_ns:
        raise ValueError("F03 aggregate receipt changed after read")
    value = _decode(payload)
    if value.registration_sha256 != expected_regsha:
        raise ValueError("F03 aggregate registration digest mismatch")
    return value, hashlib.sha256(payload).hexdigest()
