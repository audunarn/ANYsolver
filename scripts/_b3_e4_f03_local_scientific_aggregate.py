"""Read-only F03 aggregate inventory, replay and cross-case adjudication.

All five registered cases are inventoried before replay.  Failed or missing
evidence cannot be replaced by a fresh child run.  The prerequisite single-case
replay performs its separately recorded saved-evidence recovery checks; the
cross-case comparison itself does no assembly, factorization, solve or recovery.
"""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_aggregate_receipt as aggregate_receipt
from scripts import _b3_e4_f03_local_scientific_budgets as budget_contract
from scripts import _b3_e4_f03_local_scientific_case_adjudicator as adjudicator
from scripts import _b3_e4_f03_local_scientific_case_receipt as case_receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_bundle as cross_bundle
from scripts import _b3_e4_f03_local_scientific_cross_math as cross_math
from scripts import _b3_e4_f03_local_scientific_cross_snapshot as cross_snapshot
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_registration as registration


READY = "READY_FOR_REPLAY"
CASE_ORDER = tuple(case.case_id for case in cases.CASES)


@dataclass(frozen=True, slots=True)
class CaseInventory:
    case_id: str
    plan_archive_sha256: str
    receipt_sha256: str | None
    status: str
    reason: str | None
    replayed: case_receipt.CaseReceipt | None
    prolongation_sha256: str | None = None

    def __post_init__(self) -> None:
        if (
            self.case_id not in CASE_ORDER
            or not case_receipt._digest(self.plan_archive_sha256)
            or (self.receipt_sha256 is not None
                and not case_receipt._digest(self.receipt_sha256))
            or (self.prolongation_sha256 is not None
                and not case_receipt._digest(self.prolongation_sha256))
            or self.status not in (READY, *case_receipt.CASE_STATUSES)
            or (self.reason is not None and
                (type(self.reason) is not str or not self.reason or len(self.reason) > 2048))
            or (self.replayed is not None and
                (type(self.replayed) is not case_receipt.CaseReceipt
                 or self.replayed.case_id != self.case_id
                 or self.replayed.status != self.status
                 or self.receipt_sha256 is None))
        ):
            raise ValueError("invalid F03 aggregate case inventory")


@dataclass(frozen=True, slots=True)
class CrossOutcome:
    registered: registration.Registration
    registration_sha256: str
    initial_inventory: tuple[CaseInventory, ...]
    inventory: tuple[CaseInventory, ...]
    chain: cross_math.ChainResult | None
    status: str
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not case_receipt._digest(self.registration_sha256)
            or tuple(item.case_id for item in self.initial_inventory) != CASE_ORDER
            or tuple(item.case_id for item in self.inventory) != CASE_ORDER
            or self.status not in registration.TERMINAL_PRECEDENCE
            or type(self.reasons) is not tuple
            or any(type(reason) is not str or not reason or len(reason) > 2048
                   for reason in self.reasons)
            or len(self.reasons) > aggregate_receipt.MAX_REASON_COUNT
            or (self.status == "PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN")
                != (self.chain is not None and self.chain.passed)
            or (self.chain is not None and type(self.chain) is not cross_math.ChainResult)
        ):
            raise ValueError("invalid F03 aggregate decision")


def _bounded_detail(value: str) -> str:
    return "".join(char if ord(char) >= 32 else f"\\u{ord(char):04x}"
                   for char in value)[:1900]


def _reason(exc: Exception) -> str:
    return _bounded_detail(f"{type(exc).__name__}: {exc}")


def _receipt_reason(value: case_receipt.CaseReceipt) -> str:
    return _bounded_detail("; ".join(value.reasons) or value.status)


def _case_directory(run_root: Path, case_id: str) -> Path:
    if case_id not in CASE_ORDER:
        raise ValueError("frozen F03 case ID required")
    return run_root / "cases" / case_id


def _inventory_one(
    run_root: Path,
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    registered: registration.Registration,
    registration_sha256: str,
    bound: registration.CaseBinding,
) -> CaseInventory:
    directory = _case_directory(run_root, record.case.case_id)
    try:
        plan_path = directory / "plan.zip"
        adjudicator._verify_registered_plan_bytes(plan_path, bound.plan_archive_sha256)
        plan = archive.read_plan(plan_path, record, records, registered.source_commit)
        if lifecycle.plan_sha256(plan) != bound.plan_sha256:
            raise ValueError("registered F03 case plan semantic identity mismatch")
        terminal, _ = lifecycle.read_terminal(
            directory, plan, registration_sha256,
        )
        digest = cross_snapshot._owned_receipt_digest(directory)
        if terminal["reason"] == "completed" and terminal["exit_code"] == 0:
            start, start_sha256 = lifecycle.read_start(
                directory, plan, registration_sha256,
            )
            if (
                terminal["start_sha256"] != start_sha256
                or not lifecycle.terminal_owns_start(terminal, start)
            ):
                raise ValueError("F03 successful lifecycle disagrees with start marker")
            retained, retained_sha256 = case_receipt.read_receipt_inventory(
                directory, plan, registration_sha256,
            )
            if (retained_sha256 != digest
                    or retained.status not in (
                        "PASSED_CASE_NUMERICAL_SCREEN", "FAILED_NUMERICAL_SCREEN",
                        "UNRESOLVED_NUMERICAL_SCREEN",
                    )):
                raise ValueError("successful F03 execution has invalid closure receipt")
            return CaseInventory(record.case.case_id, bound.plan_archive_sha256,
                                 digest, READY, None, None)
        retained, retained_sha256 = case_receipt.read_receipt(
            directory, plan, registration_sha256,
        )
        if retained_sha256 != digest or retained.status not in (
            "FAILED_EVIDENCE", "FAILED_EXECUTION",
        ):
            raise ValueError("incomplete F03 execution has invalid closure receipt")
        return CaseInventory(record.case.case_id, bound.plan_archive_sha256,
                             digest, retained.status, _receipt_reason(retained), retained)
    except (OSError, ValueError) as exc:
        return CaseInventory(record.case.case_id, bound.plan_archive_sha256,
                             None, "FAILED_EVIDENCE", _reason(exc), None)


def _terminal_status(inventory: tuple[CaseInventory, ...]) -> str | None:
    statuses = {item.status for item in inventory}
    for status in registration.TERMINAL_PRECEDENCE[:4]:
        if status in statuses:
            return status
    return None


def _reasons(inventory: tuple[CaseInventory, ...]) -> tuple[str, ...]:
    return tuple(f"{item.case_id}: {item.status}: {item.reason or item.status}"
                 for item in inventory
                 if item.status not in (READY, "PASSED_CASE_NUMERICAL_SCREEN"))


def _verify_final_inventory(
    run_root: Path, records: tuple[cases.CasePreflight, ...],
    registered: registration.Registration, registration_sha256: str,
    original: tuple[CaseInventory, ...],
) -> None:
    """Reject any change in case evidence since the first five-case inventory."""
    observed = tuple(
        _inventory_one(run_root, record, records, registered,
                       registration_sha256, bound)
        for record, bound in zip(records, registered.cases)
    )
    if any(
        (before.case_id, before.plan_archive_sha256, before.receipt_sha256,
         before.status, before.reason)
        != (after.case_id, after.plan_archive_sha256, after.receipt_sha256,
            after.status, after.reason)
        for before, after in zip(original, observed)
    ):
        raise ValueError("F03 case evidence changed during aggregate adjudication")


def adjudicate(
    run_root: Path,
    *,
    registration_sha256: str,
    budgets: budget_contract.ScientificAdjudicationBudgets,
) -> CrossOutcome:
    """Recompute the complete registered screen from sealed saved evidence."""
    run_root = Path(run_root)
    budget_contract.require_scientific_budgets(budgets)
    registered, digest = registration.read_registration(
        run_root, registration_sha256,
    )
    if digest != registration_sha256:
        raise ValueError("F03 immutable registration identity mismatch")
    records = cases.preflight_inventory()
    if (
        tuple(item.case_id for item in registered.cases) != CASE_ORDER
        or tuple(item.case.case_id for item in records) != CASE_ORDER
    ):
        raise ValueError("exact ordered F03 registered case inventory required")
    first_inventory = tuple(
        _inventory_one(run_root, record, records, registered, digest, bound)
        for record, bound in zip(records, registered.cases)
    )
    inventory = first_inventory
    if any(item.status != READY for item in inventory):
        status = _terminal_status(inventory)
        if status is None:
            raise ValueError("invalid F03 incomplete-case precedence")
        result = CrossOutcome(registered, digest, first_inventory, inventory, None,
                              status, _reasons(inventory))
    else:
        replayed = []
        for item, record in zip(inventory, records):
            directory = _case_directory(run_root, item.case_id)
            try:
                value, case_digest = adjudicator.replay_case(
                    directory, record, records, registered.source_commit, digest,
                    budgets, plan_archive_sha256=item.plan_archive_sha256,
                )
                if case_digest != item.receipt_sha256:
                    raise ValueError("F03 case receipt changed after inventory")
                replayed.append(replace(
                    item, status=value.status,
                    reason=(None if value.status == "PASSED_CASE_NUMERICAL_SCREEN"
                            else _receipt_reason(value)),
                    replayed=value,
                ))
            except (OSError, ValueError) as exc:
                replayed.append(replace(item, status="FAILED_EVIDENCE",
                                        reason=_reason(exc), replayed=None))
        inventory = tuple(replayed)
        status = _terminal_status(inventory)
        if status is not None:
            result = CrossOutcome(registered, digest, first_inventory, inventory, None,
                                  status, _reasons(inventory))
        elif any(item.status != "PASSED_CASE_NUMERICAL_SCREEN" for item in inventory):
            raise ValueError("invalid F03 replayed case status inventory")
        else:
            try:
                with ExitStack() as stack:
                    snapshots = tuple(stack.enter_context(cross_snapshot.open_case_snapshot(
                        _case_directory(run_root, record.case.case_id), record, records,
                        registered.source_commit, digest, item.replayed,
                        item.receipt_sha256, run_root=run_root,
                        plan_archive_sha256=item.plan_archive_sha256,
                    )) for record, item in zip(records, inventory))
                    chain = cross_bundle.compare_snapshots(snapshots)
                    prolongation_sha256s = tuple(
                        snapshot.prolongation_sha256 for snapshot in snapshots
                    )
            except (OSError, ValueError) as exc:
                # A failed retained-evidence read is an identity/evidence
                # defect.  A valid numerical comparison returns ChainResult.
                result = CrossOutcome(registered, digest, first_inventory, inventory, None,
                                      "FAILED_EVIDENCE",
                                      (f"cross-case evidence: {_reason(exc)}",))
            else:
                inventory = tuple(replace(item, prolongation_sha256=sha)
                                  for item, sha in zip(inventory, prolongation_sha256s))
                status = ("PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN" if chain.passed
                          else "UNRESOLVED_LOCAL_REFERENCE")
                result = CrossOutcome(registered, digest, first_inventory, inventory, chain, status,
                                      chain.failures)
    _verify_final_inventory(run_root, records, registered, digest, first_inventory)
    final_registration, final_digest = registration.read_registration(
        run_root, registration_sha256,
    )
    if final_registration != registered or final_digest != digest:
        raise ValueError("F03 registration changed during aggregate adjudication")
    return result


def make_receipt(value: CrossOutcome) -> aggregate_receipt.AggregateReceipt:
    """Bind the complete read-only decision to registered identities."""
    if type(value) is not CrossOutcome:
        raise ValueError("validated F03 cross-case decision required")
    registered = value.registered
    source_hashes = {item.role: item.sha256 for item in registered.sources}
    case_records = tuple(aggregate_receipt.CaseRecord(
        item.case_id, item.plan_archive_sha256, item.receipt_sha256,
        item.status,
        item.replayed.evidence_index_sha256 if item.replayed is not None else None,
        item.replayed.numerical_index_sha256 if item.replayed is not None else None,
        item.replayed.inverse_index_sha256 if item.replayed is not None else None,
        item.prolongation_sha256, item.reason,
    ) for item in value.inventory)
    pair_results = (
        value.chain.pairs if value.chain is not None
        else (None,) * len(cross_math.PAIR_ORDER)
    )
    if len(pair_results) != len(cross_math.PAIR_ORDER):
        raise ValueError("complete ordered F03 cross-case result required")
    pairs = tuple(aggregate_receipt.PairRecord(pair, result)
                  for pair, result in zip(cross_math.PAIR_ORDER, pair_results))
    if value.chain is None:
        predicates = tuple(aggregate_receipt.PredicateRecord(
            name, "NOT_EVALUATED", (),
        ) for name in aggregate_receipt.PREDICATE_NAMES)
    else:
        predicates = tuple(aggregate_receipt.PredicateRecord(
            name, "PASSED" if result.passed else "FAILED", result.failures,
        ) for name, result in zip(aggregate_receipt.PREDICATE_NAMES[:-1], pair_results)) + (
            aggregate_receipt.PredicateRecord(
                "chain", "PASSED" if value.chain.passed else "FAILED",
                value.chain.failures,
            ),
        )
    return aggregate_receipt.AggregateReceipt(
        aggregate_receipt.SCHEMA, registered.source_commit,
        value.registration_sha256, source_hashes["cross_math"],
        registered.sources, registered.process_limits, registered.resource_limits,
        registered.tolerances, case_records, pairs, predicates, value.status,
        value.reasons, 0, 0, 0, 0,
    )


def adjudicate_and_write(
    run_root: Path,
    *,
    registration_sha256: str,
    budgets: budget_contract.ScientificAdjudicationBudgets,
) -> tuple[aggregate_receipt.AggregateReceipt, str]:
    """Exclusively close one registered aggregate, without launching cases."""
    run_root = Path(run_root)
    outcome = adjudicate(run_root, registration_sha256=registration_sha256,
                         budgets=budgets)
    value = make_receipt(outcome)
    before, before_sha256 = registration.read_registration(
        run_root, registration_sha256,
    )
    if before != outcome.registered or before_sha256 != outcome.registration_sha256:
        raise ValueError("F03 registration changed before aggregate receipt write")
    _verify_final_inventory(
        run_root, cases.preflight_inventory(), outcome.registered,
        registration_sha256, outcome.initial_inventory,
    )
    digest = aggregate_receipt.write_receipt(run_root, value)
    observed, observed_digest = aggregate_receipt.read_receipt(
        run_root, registration_sha256,
    )
    if observed != value or observed_digest != digest:
        raise ValueError("F03 aggregate receipt disagrees with exclusive write")
    after, after_sha256 = registration.read_registration(
        run_root, registration_sha256,
    )
    if after != outcome.registered or after_sha256 != outcome.registration_sha256:
        raise ValueError("F03 registration changed after aggregate receipt write")
    _verify_final_inventory(
        run_root, cases.preflight_inventory(), outcome.registered,
        registration_sha256, outcome.initial_inventory,
    )
    return value, digest


def replay_aggregate(
    run_root: Path,
    *,
    registration_sha256: str,
    budgets: budget_contract.ScientificAdjudicationBudgets,
) -> tuple[aggregate_receipt.AggregateReceipt, str]:
    """Independently recompute and compare the sealed aggregate without writes."""
    run_root = Path(run_root)
    outcome = adjudicate(
        run_root, registration_sha256=registration_sha256, budgets=budgets,
    )
    expected = make_receipt(outcome)
    retained, digest = aggregate_receipt.read_receipt(run_root, registration_sha256)
    if retained != expected:
        raise ValueError("F03 aggregate receipt disagrees with independent replay")
    after, after_sha256 = registration.read_registration(
        run_root, registration_sha256,
    )
    if after != outcome.registered or after_sha256 != outcome.registration_sha256:
        raise ValueError("F03 registration changed after aggregate replay")
    _verify_final_inventory(
        run_root, cases.preflight_inventory(), outcome.registered,
        registration_sha256, outcome.initial_inventory,
    )
    return retained, digest
