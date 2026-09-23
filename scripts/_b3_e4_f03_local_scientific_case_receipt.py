"""Canonical adjudicator-owned closure receipt for one F03 scientific case.

The receipt records validated identities and solve-free adjudication results.
It cannot assemble, factor, solve, retry, or infer missing evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_inverse_storage as inverse_storage
from scripts import _b3_e4_f03_local_scientific_numerical_index as numerical_index
from scripts import _b3_e4_f03_spatial_contract as spatial


SCHEMA = "f03_local_scientific_case_receipt_v1"
MAX_BYTES = cases.CASE_RECEIPT_BYTES
DIGEST = frozenset("0123456789abcdef")

PREDICATE_NAMES = (
    "evidence", "execution", "condition_backward", "positivity", "state_scaling",
    "rank", "trace", "equilibrium_energy", "integration", "composition", "balance",
)
DISPOSITIONS = ("PASSED", "FAILED", "HOLD", "HOLD_UNRESOLVED", "NOT_EVALUATED")
CASE_STATUSES = (
    "FAILED_EVIDENCE", "FAILED_EXECUTION", "FAILED_NUMERICAL_SCREEN",
    "UNRESOLVED_NUMERICAL_SCREEN", "PASSED_CASE_NUMERICAL_SCREEN",
)
WORK_NAMES = (
    "producer_kkt_factorizations", "producer_positivity_factorizations",
    "producer_candidate_rhs_solves", "producer_certificate_solve_calls",
    "producer_certificate_rhs_attempted", "producer_certificate_rhs_completed",
    "producer_recovery_factorizations", "producer_recovery_solves",
    "replay_factorizations", "replay_equilibrium_solves",
    "replay_recovery_recomputations", "replay_norm_evaluations",
)
SETTLING_NAMES = (
    "root_reaction_x", "root_reaction_y", "root_reaction_moment",
    "left_edge_force_x", "left_edge_force_y", "left_edge_moment",
    "right_edge_force_x", "right_edge_force_y", "right_edge_moment",
    "tip_pose_x", "tip_pose_y", "tip_pose_scaled_rotation",
    "shell_energy", "beam_energy", "total_energy",
    "root_atom_force_x", "root_atom_force_y", "root_atom_moment",
    "tip_atom_force_x", "tip_atom_force_y", "tip_atom_moment",
    *(f"band_{band}_{component}" for band in range(8)
      for component in ("force_x", "force_y", "moment")),
)
_WRENCH_SCALES = (float(spatial.F0), float(spatial.F0),
                   float(spatial.F0 * spatial.L0))
_POSE_SCALES = (float(spatial.U0),) * 3
_ENERGY_SCALES = (float(spatial.E0),) * 3
SETTLING_SCALES = (
    *_WRENCH_SCALES, *_WRENCH_SCALES, *_WRENCH_SCALES,
    *_POSE_SCALES, *_ENERGY_SCALES,
    *_WRENCH_SCALES, *_WRENCH_SCALES,
    *(_WRENCH_SCALES * 8),
)
if len(SETTLING_SCALES) != len(SETTLING_NAMES):
    raise AssertionError("F03 settling scale inventory is incomplete")


def _digest(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= DIGEST


def _optional_digest(value: object) -> bool:
    return value is None or _digest(value)


def _float_identity(first: float | None, second: float | None) -> bool:
    if first is None or second is None:
        return first is second
    return struct.pack(">d", first) == struct.pack(">d", second)


def _float_tuple_identity(first: tuple, second: tuple) -> bool:
    return len(first) == len(second) and all(
        _float_identity(left, right) for left, right in zip(first, second)
    )


def _reasons(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or not item or len(item) > 2048 for item in value
    ) or len(value) > 128 or (not allow_empty and not value):
        raise ValueError("bounded ordered F03 reason inventory required")
    return value


@dataclass(frozen=True, slots=True)
class PredicateRecord:
    name: str
    disposition: str
    reasons: tuple[str, ...]

    def __post_init__(self):
        if self.name not in PREDICATE_NAMES or self.disposition not in DISPOSITIONS:
            raise ValueError("invalid F03 predicate disposition")
        _reasons(self.reasons, allow_empty=self.disposition == "PASSED")
        if self.disposition == "PASSED" and self.reasons:
            raise ValueError("passed F03 predicate cannot retain failure reasons")


@dataclass(frozen=True, slots=True)
class WorkRecord:
    values: tuple[tuple[str, int], ...]

    def __post_init__(self):
        if (
            type(self.values) is not tuple
            or tuple(name for name, _ in self.values) != WORK_NAMES
            or any(type(value) is not int or value < 0 for _, value in self.values)
        ):
            raise ValueError("exact ordered F03 case-work inventory required")

    def as_dict(self) -> dict[str, int]:
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class SettlingRecord:
    values: tuple[float, ...]
    lower: tuple[float, ...]
    upper: tuple[float, ...]
    scales: tuple[float, ...]
    source_sha256s: tuple[str, ...]

    def __post_init__(self):
        if any(type(row) is not tuple or len(row) != len(SETTLING_NAMES)
               for row in (self.values, self.lower, self.upper, self.scales,
                           self.source_sha256s)):
            raise ValueError("complete 45-channel F03 settling inventory required")
        if any(type(value) is not float or not math.isfinite(value)
               for row in (self.values, self.lower, self.upper, self.scales) for value in row):
            raise ValueError("finite binary64 F03 settling observations required")
        if self.scales != SETTLING_SCALES or any(
            low > value or value > high
            for value, low, high in zip(self.values, self.lower, self.upper)
        ):
            raise ValueError("invalid F03 settling enclosure or frozen scale")
        if any(not _digest(value) for value in self.source_sha256s):
            raise ValueError("canonical F03 settling source identities required")


def _optional_floats(value: object, count: int, label: str) -> tuple[float | None, ...]:
    if type(value) is not tuple or len(value) != count or any(
        item is not None and (type(item) is not float or not math.isfinite(item))
        for item in value
    ):
        raise ValueError(f"bounded F03 {label} inventory required")
    return value


@dataclass(frozen=True, slots=True)
class FunctionalRecord:
    functional_sha256: str
    channels: tuple[float | None, ...]
    totals: tuple[float | None, ...]
    components: tuple[float | None, ...]
    channel_flags: tuple[bool, ...]
    total_flags: tuple[bool, ...]
    exact_zero: tuple[bool, ...]
    failures: tuple[tuple[tuple[str, int | None, str], ...], ...]

    def __post_init__(self):
        if not _digest(self.functional_sha256):
            raise ValueError("canonical F03 functional digest required")
        _optional_floats(self.channels, 6, "functional channel")
        _optional_floats(self.totals, 2, "functional total")
        _optional_floats(self.components, 36, "functional component")
        for value, count, label in (
            (self.channel_flags, 18, "channel flag"),
            (self.total_flags, 6, "total flag"),
            (self.exact_zero, 2, "zero flag"),
        ):
            if type(value) is not tuple or len(value) != count or any(type(item) is not bool for item in value):
                raise ValueError(f"complete F03 functional {label} inventory required")
        if type(self.failures) is not tuple or len(self.failures) != 2:
            raise ValueError("both F03 functional failure inventories required")
        for failures in self.failures:
            if type(failures) is not tuple or len(failures) > 32:
                raise ValueError("bounded F03 functional failure inventory required")
            for record in failures:
                if (
                    type(record) is not tuple or len(record) != 3
                    or type(record[0]) is not str or not record[0]
                    or (record[1] is not None and
                        (type(record[1]) is not int or record[1] not in (0, 1, 2)))
                    or type(record[2]) is not str or not record[2]
                ):
                    raise ValueError("invalid F03 functional failure record")

    @property
    def numerically_admissible(self) -> bool:
        numbers = (*self.channels, *self.totals, *self.components)
        if (
            any(value is None for value in numbers)
            or not all(self.channel_flags)
            or not all(self.total_flags)
            or any(self.failures)
        ):
            return False
        channels = self.channels
        totals = self.totals
        if any(value < 0.0 for value in (*channels, *totals)):
            return False
        for order, exact_zero in enumerate(self.exact_zero):
            total = totals[order]
            if (exact_zero and total != 0.0) or (not exact_zero and total == 0.0):
                return False
        return True


@dataclass(frozen=True, slots=True)
class AdjudicationBindings:
    """Observations reconstructed by the solve-free adjudicator.

    This object is deliberately external to ``CaseReceipt``.  The receipt may
    report observations, but it cannot nominate the observations against which
    it is checked.
    """

    settling: SettlingRecord
    functional: FunctionalRecord

    def __post_init__(self):
        if type(self.settling) is not SettlingRecord or type(self.functional) is not FunctionalRecord:
            raise ValueError("complete solve-free F03 adjudication bindings required")


def _settling_identity(first: SettlingRecord, second: SettlingRecord) -> bool:
    return (
        _float_tuple_identity(first.values, second.values)
        and _float_tuple_identity(first.lower, second.lower)
        and _float_tuple_identity(first.upper, second.upper)
        and _float_tuple_identity(first.scales, second.scales)
        and first.source_sha256s == second.source_sha256s
    )


def _functional_identity(first: FunctionalRecord, second: FunctionalRecord) -> bool:
    return (
        first.functional_sha256 == second.functional_sha256
        and _float_tuple_identity(first.channels, second.channels)
        and _float_tuple_identity(first.totals, second.totals)
        and _float_tuple_identity(first.components, second.components)
        and first.channel_flags == second.channel_flags
        and first.total_flags == second.total_flags
        and first.exact_zero == second.exact_zero
        and first.failures == second.failures
    )


@dataclass(frozen=True, slots=True)
class CaseReceipt:
    schema: str
    case_id: str
    source_commit: str
    registration_sha256: str
    plan_sha256: str
    start_sha256: str | None
    terminal_sha256: str
    evidence_index_sha256: str | None
    numerical_index_sha256: str | None
    inverse_index_sha256: str | None
    evidence_total_bytes: int | None
    terminal_reason: str
    terminal_exit_code: int | None
    status: str
    predicates: tuple[PredicateRecord, ...]
    work: WorkRecord
    settling: SettlingRecord | None
    functional: FunctionalRecord | None
    reasons: tuple[str, ...]

    def __post_init__(self):
        if (
            self.schema != SCHEMA
            or type(self.case_id) is not str
            or type(self.source_commit) is not str or len(self.source_commit) != 40
            or set(self.source_commit) - DIGEST
            or not _digest(self.registration_sha256) or not _digest(self.plan_sha256)
            or not _optional_digest(self.start_sha256) or not _digest(self.terminal_sha256)
            or not _optional_digest(self.evidence_index_sha256)
            or not _optional_digest(self.numerical_index_sha256)
            or not _optional_digest(self.inverse_index_sha256)
            or (self.evidence_total_bytes is not None and
                (type(self.evidence_total_bytes) is not int or self.evidence_total_bytes <= 0))
            or type(self.terminal_reason) is not str or not self.terminal_reason
            or (self.terminal_exit_code is not None and type(self.terminal_exit_code) is not int)
            or self.status not in CASE_STATUSES
            or type(self.predicates) is not tuple
            or tuple(item.name for item in self.predicates) != PREDICATE_NAMES
            or any(type(item) is not PredicateRecord for item in self.predicates)
            or type(self.work) is not WorkRecord
            or (self.settling is not None and type(self.settling) is not SettlingRecord)
            or (self.functional is not None and type(self.functional) is not FunctionalRecord)
        ):
            raise ValueError("invalid complete F03 case receipt")
        _reasons(self.reasons, allow_empty=self.status == "PASSED_CASE_NUMERICAL_SCREEN")
        if self.status == "PASSED_CASE_NUMERICAL_SCREEN" and self.reasons:
            raise ValueError("passed F03 case receipt cannot retain failure reasons")


def _expected_status(predicates: tuple[PredicateRecord, ...], terminal_reason: str,
                     terminal_exit_code: int | None) -> str:
    values = {item.name: item.disposition for item in predicates}
    if values["evidence"] != "PASSED":
        return "FAILED_EVIDENCE"
    if (values["execution"] != "PASSED" or terminal_reason != "completed"
            or terminal_exit_code != 0):
        return "FAILED_EXECUTION"
    numerical = tuple(values[name] for name in PREDICATE_NAMES[2:])
    if "NOT_EVALUATED" in numerical:
        raise ValueError("complete evidence/execution requires every F03 predicate")
    if "FAILED" in numerical:
        return "FAILED_NUMERICAL_SCREEN"
    if any(value in ("HOLD", "HOLD_UNRESOLVED") for value in numerical):
        return "UNRESOLVED_NUMERICAL_SCREEN"
    if all(value == "PASSED" for value in numerical):
        return "PASSED_CASE_NUMERICAL_SCREEN"
    raise ValueError("invalid F03 predicate precedence")


def validate_receipt(
    value: CaseReceipt, plan: archive.CaseArchivePlan, registration_sha256: str,
    bindings: AdjudicationBindings | None = None,
) -> CaseReceipt:
    if (
        type(value) is not CaseReceipt or type(plan) is not archive.CaseArchivePlan
        or not _digest(registration_sha256)
    ):
        raise ValueError("validated F03 receipt and archive plan required")
    expected = _expected_status(value.predicates, value.terminal_reason, value.terminal_exit_code)
    dispositions = {item.name: item.disposition for item in value.predicates}
    evidence_complete = dispositions["evidence"] == "PASSED"
    execution_complete = dispositions["execution"] == "PASSED"
    complete = evidence_complete and execution_complete
    identities = (
        value.start_sha256, value.evidence_index_sha256,
        value.numerical_index_sha256, value.inverse_index_sha256,
    )
    work = value.work.as_dict()
    if (
        value.case_id != plan.case_id
        or value.source_commit != plan.source_commit
        or value.registration_sha256 != registration_sha256
        or value.plan_sha256 != lifecycle.plan_sha256(plan)
        or value.status != expected
        or dispositions["evidence"] not in ("PASSED", "FAILED")
        or (evidence_complete and dispositions["execution"] not in ("PASSED", "FAILED"))
        or (not evidence_complete and any(
            dispositions[name] != "NOT_EVALUATED" for name in PREDICATE_NAMES[1:]
        ))
        or (value.status == "PASSED_CASE_NUMERICAL_SCREEN") != (not value.reasons)
        or (evidence_complete and (any(item is None for item in identities)
                                   or value.evidence_total_bytes is None))
        or (complete and (
            type(bindings) is not AdjudicationBindings
            or type(value.settling) is not SettlingRecord
            or type(value.functional) is not FunctionalRecord
            or not _settling_identity(value.settling, bindings.settling)
            or not _functional_identity(value.functional, bindings.functional)
        ))
        or (not complete and bindings is not None)
        or (not complete and (value.settling is not None or value.functional is not None))
        or (complete and not value.functional.numerically_admissible
            and dispositions["composition"] != "FAILED")
        or (complete and not value.functional.numerically_admissible
            and not any(value.functional.failures))
        or (value.status == "PASSED_CASE_NUMERICAL_SCREEN"
            and not value.functional.numerically_admissible)
        or (value.evidence_total_bytes is not None
            and value.evidence_total_bytes > plan.raw_archive_bytes)
        or (complete and work != {
            "producer_kkt_factorizations": 1,
            "producer_positivity_factorizations": 1,
            "producer_candidate_rhs_solves": 1,
            "producer_certificate_solve_calls": len(plan.inverse_blocks),
            "producer_certificate_rhs_attempted": plan.kkt_order,
            "producer_certificate_rhs_completed": plan.kkt_order,
            "producer_recovery_factorizations": 0,
            "producer_recovery_solves": 0,
            "replay_factorizations": 0,
            "replay_equilibrium_solves": 0,
            "replay_recovery_recomputations": 3,
            "replay_norm_evaluations": 2,
        })
    ):
        raise ValueError("F03 case receipt disagrees with plan, precedence, or work")
    return value


def _payload(
    value: CaseReceipt, plan: archive.CaseArchivePlan, registration_sha256: str,
    bindings: AdjudicationBindings | None = None,
) -> bytes:
    validate_receipt(value, plan, registration_sha256, bindings)
    document = {
        "schema": value.schema, "case_id": value.case_id,
        "source_commit": value.source_commit,
        "registration_sha256": value.registration_sha256,
        "plan_sha256": value.plan_sha256, "start_sha256": value.start_sha256,
        "terminal_sha256": value.terminal_sha256,
        "evidence_index_sha256": value.evidence_index_sha256,
        "numerical_index_sha256": value.numerical_index_sha256,
        "inverse_index_sha256": value.inverse_index_sha256,
        "evidence_total_bytes": value.evidence_total_bytes,
        "terminal_reason": value.terminal_reason,
        "terminal_exit_code": value.terminal_exit_code, "status": value.status,
        "predicates": [
            {"name": item.name, "disposition": item.disposition, "reasons": list(item.reasons)}
            for item in value.predicates
        ],
        "work": {name: count for name, count in value.work.values},
        "settling": None if value.settling is None else {
            "names": list(SETTLING_NAMES), "values": list(value.settling.values),
            "lower": list(value.settling.lower), "upper": list(value.settling.upper),
            "scales": list(value.settling.scales),
            "source_sha256s": list(value.settling.source_sha256s),
        },
        "functional": None if value.functional is None else {
            "functional_sha256": value.functional.functional_sha256,
            "channels": list(value.functional.channels), "totals": list(value.functional.totals),
            "components": list(value.functional.components),
            "channel_flags": list(value.functional.channel_flags),
            "total_flags": list(value.functional.total_flags),
            "exact_zero": list(value.functional.exact_zero),
            "failures": [[list(record) for record in items]
                         for items in value.functional.failures],
        },
        "reasons": list(value.reasons),
    }
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("ascii")
    if len(payload) > MAX_BYTES:
        raise ValueError("F03 case receipt exceeds declared bound")
    return payload


def write_receipt(
    directory: Path, value: CaseReceipt, plan: archive.CaseArchivePlan,
    registration_sha256: str, bindings: AdjudicationBindings | None = None,
) -> str:
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError("existing F03 case directory required")
    payload = _payload(value, plan, registration_sha256, bindings)
    path = directory / "case_receipt.json"
    with path.open("xb") as stream:
        stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def _tuple_floats(value, count, *, optional=False):
    if type(value) is not list or len(value) != count:
        raise ValueError("invalid F03 receipt numerical inventory")
    return tuple(None if item is None and optional else float(item) for item in value)


def _decode(
    payload: bytes, plan: archive.CaseArchivePlan, registration_sha256: str,
    bindings: AdjudicationBindings | None = None,
) -> CaseReceipt:
    if type(payload) is not bytes or len(payload) > MAX_BYTES:
        raise ValueError("invalid bounded F03 case receipt payload")
    try:
        raw = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 case receipt JSON") from exc
    keys = (
        "case_id", "evidence_index_sha256", "evidence_total_bytes", "functional",
        "inverse_index_sha256", "numerical_index_sha256", "plan_sha256", "predicates",
        "reasons", "registration_sha256", "schema", "settling", "source_commit",
        "start_sha256", "status", "terminal_exit_code", "terminal_reason",
        "terminal_sha256", "work",
    )
    if type(raw) is not dict or set(raw) != set(keys):
        raise ValueError("invalid F03 case receipt inventory")
    predicates = tuple(PredicateRecord(
        item["name"], item["disposition"], tuple(item["reasons"]),
    ) for item in raw["predicates"] if type(item) is dict and set(item) == {
        "name", "disposition", "reasons"
    }) if type(raw["predicates"]) is list else ()
    if type(raw["work"]) is not dict or set(raw["work"]) != set(WORK_NAMES):
        raise ValueError("invalid F03 receipt work inventory")
    work = WorkRecord(tuple((name, raw["work"][name]) for name in WORK_NAMES))
    settling = None
    if raw["settling"] is not None:
        item = raw["settling"]
        if type(item) is not dict or set(item) != {
                "names", "values", "lower", "upper", "scales", "source_sha256s"} \
                or tuple(item["names"]) != SETTLING_NAMES:
            raise ValueError("invalid F03 receipt settling inventory")
        settling = SettlingRecord(
            *(_tuple_floats(item[name], len(SETTLING_NAMES))
              for name in ("values", "lower", "upper", "scales")),
            tuple(item["source_sha256s"]),
        )
    functional = None
    if raw["functional"] is not None:
        item = raw["functional"]
        expected = {"functional_sha256", "channels", "totals", "components",
                    "channel_flags", "total_flags", "exact_zero", "failures"}
        if type(item) is not dict or set(item) != expected:
            raise ValueError("invalid F03 receipt functional inventory")
        functional = FunctionalRecord(
            item["functional_sha256"], _tuple_floats(item["channels"], 6, optional=True),
            _tuple_floats(item["totals"], 2, optional=True),
            _tuple_floats(item["components"], 36, optional=True),
            tuple(item["channel_flags"]), tuple(item["total_flags"]),
            tuple(item["exact_zero"]),
            tuple(tuple(tuple(record) for record in row) for row in item["failures"]),
        )
    receipt = CaseReceipt(
        raw["schema"], raw["case_id"], raw["source_commit"], raw["registration_sha256"],
        raw["plan_sha256"], raw["start_sha256"], raw["terminal_sha256"],
        raw["evidence_index_sha256"], raw["numerical_index_sha256"],
        raw["inverse_index_sha256"], raw["evidence_total_bytes"], raw["terminal_reason"],
        raw["terminal_exit_code"], raw["status"], predicates, work, settling, functional,
        tuple(raw["reasons"]),
    )
    if _payload(receipt, plan, registration_sha256, bindings) != payload:
        raise ValueError("noncanonical F03 case receipt encoding")
    return receipt


def read_receipt(
    directory: Path, plan: archive.CaseArchivePlan, registration_sha256: str,
    bindings: AdjudicationBindings | None = None,
) -> tuple[CaseReceipt, str]:
    directory = Path(directory)
    path = directory / "case_receipt.json"
    with evidence._open_no_follow(path) as stream:
        payload = stream.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("F03 case receipt exceeds declared bound")
    value = _decode(payload, plan, registration_sha256, bindings)
    terminal, terminal_digest = lifecycle.read_terminal(directory, plan, registration_sha256)
    start_path = directory / "start.json"
    start_digest = (
        lifecycle.read_start(directory, plan, registration_sha256)[1]
        if start_path.exists() else None
    )
    if (
        value.start_sha256 != start_digest
        or value.terminal_sha256 != terminal_digest
        or value.terminal_reason != terminal["reason"]
        or value.terminal_exit_code != terminal["exit_code"]
    ):
        raise ValueError("F03 case receipt disagrees with lifecycle evidence")
    observed_evidence = None
    if value.evidence_index_sha256 is not None:
        if start_digest is None:
            raise ValueError("F03 evidence index requires a consumed start marker")
        index, observed_evidence = evidence.read_index(
            directory, plan, registration_sha256, start_digest,
        )
        if value.evidence_total_bytes != index.total_bytes:
            raise ValueError("F03 case receipt disagrees with evidence byte inventory")
    observed_numerical = None
    if value.numerical_index_sha256 is not None:
        _, observed_numerical = numerical_index.read_index(
            directory / "numerical_index.json", plan,
        )
    observed_inverse = None
    if value.inverse_index_sha256 is not None:
        _, observed_inverse = inverse_storage.read_index(directory, plan)
    if (
        value.evidence_index_sha256 != observed_evidence
        or value.numerical_index_sha256 != observed_numerical
        or value.inverse_index_sha256 != observed_inverse
    ):
        raise ValueError("F03 case receipt disagrees with saved evidence identities")
    return value, hashlib.sha256(payload).hexdigest()
