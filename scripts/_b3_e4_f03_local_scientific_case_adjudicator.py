"""Solve-free adjudication of one completed F03 scientific case archive.

This reader replays bounded checks against immutable saved evidence.  It does
not assemble, factor, solve, retry, register, supervise, or authorize a run.
Missing or incomplete lifecycle evidence raises before a receipt is written.
"""
from __future__ import annotations

from pathlib import Path

from scripts import _b3_e4_f03_local_scientific_adjudication_bindings as binding_records
from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_balance_adjudication as balance
from scripts import _b3_e4_f03_local_scientific_budgets as budget_contract
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence_index
from scripts import _b3_e4_f03_local_scientific_inverse_storage as inverse_storage
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_numerical_index as numerical_index
from scripts import _b3_e4_f03_local_scientific_prolongation_storage as prolongation_storage
from scripts import _b3_e4_f03_local_scientific_replay_binding as replay_binding
from scripts import _b3_e4_f03_local_scientific_result_storage as result_storage
from scripts import _b3_e4_f03_local_scientific_saved_storage as saved_storage
from scripts import _b3_e4_f03_saved_recovery_composition as composition
from scripts import _b3_e4_f03_sparse_equilibrium_checks as equilibrium
from scripts import _b3_e4_f03_sparse_integration_checks as integration
from scripts import _b3_e4_f03_sparse_positivity as positivity
from scripts import _b3_e4_f03_sparse_root_rank as rank
from scripts import _b3_e4_f03_sparse_state_binding as state_binding
from scripts import _b3_e4_f03_sparse_trace_binding as trace


def _record(name: str, disposition: str, reasons=()) -> receipt.PredicateRecord:
    values = tuple(str(value) for value in reasons if str(value))
    if disposition == "PASSED":
        values = ()
    elif not values:
        values = (f"{name} did not pass",)
    return receipt.PredicateRecord(name, disposition, values)


def _reason(value: object, fallback: str) -> tuple[str, ...]:
    return (value,) if type(value) is str and value else (fallback,)


def _condition_record(value: dict) -> receipt.PredicateRecord:
    status = value.get("status")
    return _record(
        "condition_backward",
        "PASSED" if status == "CERTIFIED_WITHIN_LIMIT" else "HOLD",
        () if status == "CERTIFIED_WITHIN_LIMIT" else
        (f"primary condition/backward certificate status: {status}",),
    )


def _positivity_record(
    bound: replay_binding.ReplayBinding, proof: dict | None,
) -> receipt.PredicateRecord:
    if bound.positivity_candidate_status == "HOLD":
        return _record("positivity", "HOLD", _reason(
            bound.positivity_candidate_reason,
            "saved positivity candidate is on hold",
        ))
    if type(proof) is not dict:
        raise ValueError("complete F03 positivity proof required for admitted candidate")
    passed = proof.get("status") == "POSITIVE_QUADRATIC_FORM"
    return _record(
        "positivity", "PASSED" if passed else "HOLD",
        () if passed else _reason(proof.get("reason"), "positivity proof did not pass"),
    )


def _status_record(
    name: str, value: dict, passed_status: str, failure_disposition: str,
) -> receipt.PredicateRecord:
    passed = value.get("status") == passed_status
    reasons = value.get("failures", ())
    if type(reasons) is not tuple:
        raise ValueError(f"canonical F03 {name} failure inventory required")
    return _record(
        name, "PASSED" if passed else failure_disposition,
        () if passed else (reasons or (f"{name} status: {value.get('status')}",)),
    )


def _rank_record(value: dict) -> receipt.PredicateRecord:
    if value.get("status") == "PORT_RANK_PASSED":
        return _record("rank", "PASSED")
    reasons = []
    for key in ("root", "root_and_free_slope"):
        item = value.get(key)
        if isinstance(item, dict) and type(item.get("reason")) is str and item["reason"]:
            reasons.append(f"{key}: {item['reason']}")
    return _record("rank", "HOLD", tuple(reasons) or ("scaled port rank proof did not pass",))


def _composition_record(value: composition.CompositionResult) -> receipt.PredicateRecord:
    status = value["status"]
    mapping = {
        "COMPONENT_CHECKS_PASSED": "PASSED",
        "COMPOSITION_FAILED": "FAILED",
        "HOLD_NUMERICAL": "HOLD",
        "HOLD_UNRESOLVED": "HOLD_UNRESOLVED",
    }
    if status not in mapping or type(value["reasons"]) is not tuple:
        raise ValueError("canonical F03 composition disposition required")
    return _record("composition", mapping[status], value["reasons"])


def _balance_record(value: balance.BalanceAdjudication) -> receipt.PredicateRecord:
    if type(value) is not balance.BalanceAdjudication:
        raise ValueError("canonical F03 balance adjudication required")
    return _record("balance", value.status, value.reasons)


def _work(plan: archive.CaseArchivePlan) -> receipt.WorkRecord:
    values = {
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
    }
    return receipt.WorkRecord(tuple((name, values[name]) for name in receipt.WORK_NAMES))


def _zero_work() -> receipt.WorkRecord:
    return receipt.WorkRecord(tuple((name, 0) for name in receipt.WORK_NAMES))


def _saved_producer_work(index, plan: archive.CaseArchivePlan) -> receipt.WorkRecord:
    kkt = index.kkt_producer
    positive = index.positivity_producer
    values = {
        "producer_kkt_factorizations": kkt.factorization_count,
        "producer_positivity_factorizations": positive.factorization_count,
        "producer_candidate_rhs_solves": kkt.candidate_rhs_solves,
        "producer_certificate_solve_calls": kkt.certificate_solve_calls,
        "producer_certificate_rhs_attempted": kkt.certificate_rhs_attempted,
        "producer_certificate_rhs_completed": kkt.certificate_rhs_completed,
        "producer_recovery_factorizations": kkt.recovery_factorizations,
        "producer_recovery_solves": kkt.recovery_solves,
        "replay_factorizations": 0,
        "replay_equilibrium_solves": 0,
        "replay_recovery_recomputations": 0,
        "replay_norm_evaluations": 0,
    }
    value = receipt.WorkRecord(
        tuple((name, values[name]) for name in receipt.WORK_NAMES),
    )
    if (
        kkt.certificate_solve_calls != len(plan.inverse_blocks)
        or kkt.certificate_rhs_attempted != plan.kkt_order
        or kkt.certificate_rhs_completed != plan.kkt_order
    ):
        raise ValueError("saved F03 producer work disagrees with plan")
    return value


def _bounded_failure_reason(value: object, fallback: str) -> str:
    reason = value if type(value) is str and value else fallback
    if len(reason) > 2048:
        reason = reason[:2048]
    return reason


def _failed_predicates(
    *, evidence_reason: str | None, execution_reason: str | None,
) -> tuple[receipt.PredicateRecord, ...]:
    if evidence_reason is not None:
        return tuple(
            _record(
                name,
                "FAILED" if name == "evidence" else "NOT_EVALUATED",
                (evidence_reason,) if name == "evidence" else
                ("not evaluated after evidence failure",),
            )
            for name in receipt.PREDICATE_NAMES
        )
    if execution_reason is None:
        raise ValueError("explicit F03 execution failure reason required")
    return tuple(
        _record(
            name,
            "PASSED" if name == "evidence" else
            "FAILED" if name == "execution" else "NOT_EVALUATED",
            (execution_reason,) if name == "execution" else
            ("not evaluated after execution failure",)
            if name not in ("evidence", "execution") else (),
        )
        for name in receipt.PREDICATE_NAMES
    )


def close_failed_case(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    *,
    evidence_failure: str | None = None,
) -> tuple[receipt.CaseReceipt, str]:
    """Write one canonical failure receipt without replaying mechanics.

    A supplied ``evidence_failure`` has precedence over otherwise readable
    evidence. Without it, complete indexed evidence is retained and an
    unsuccessful terminal lifecycle is classified as execution failure.
    """
    directory = Path(directory)
    if not directory.is_dir() or type(plan) is not archive.CaseArchivePlan:
        raise ValueError("validated F03 failure-closure inputs required")
    terminal, terminal_sha256 = lifecycle.read_terminal(
        directory, plan, registration_sha256,
    )
    start_sha256 = None
    if (directory / "start.json").exists():
        _, start_sha256 = lifecycle.read_start(
            directory, plan, registration_sha256,
        )

    evidence_sha256 = None
    numerical_sha256 = None
    inverse_sha256 = None
    evidence_total_bytes = None
    indexed = None
    observed_failure = evidence_failure
    if observed_failure is None:
        if start_sha256 is None:
            observed_failure = "registered child did not create a start marker"
        else:
            try:
                evidence, evidence_sha256 = evidence_index.read_index(
                    directory, plan, registration_sha256, start_sha256,
                )
                indexed, numerical_sha256 = numerical_index.read_index(
                    directory / "numerical_index.json", plan,
                )
                _, inverse_sha256 = inverse_storage.read_index(directory, plan)
                evidence_total_bytes = evidence.total_bytes
            except (OSError, ValueError) as exc:
                observed_failure = _bounded_failure_reason(
                    f"{type(exc).__name__}: {exc}",
                    "incomplete or invalid F03 evidence",
                )
                evidence_sha256 = numerical_sha256 = inverse_sha256 = None
                evidence_total_bytes = None
                indexed = None

    if observed_failure is not None:
        observed_failure = _bounded_failure_reason(
            observed_failure, "F03 evidence did not pass",
        )
        predicates = _failed_predicates(
            evidence_reason=observed_failure, execution_reason=None,
        )
        work = _zero_work()
        evidence_sha256 = numerical_sha256 = inverse_sha256 = None
        evidence_total_bytes = None
    else:
        if terminal["reason"] == "completed" and terminal["exit_code"] == 0:
            raise ValueError("successful F03 lifecycle requires full adjudication")
        execution_reason = _bounded_failure_reason(
            terminal.get("failure"),
            f"terminal reason={terminal['reason']}; exit_code={terminal['exit_code']}",
        )
        predicates = _failed_predicates(
            evidence_reason=None, execution_reason=execution_reason,
        )
        work = _saved_producer_work(indexed, plan)

    status = receipt._expected_status(
        predicates, terminal["reason"], terminal["exit_code"],
    )
    reasons = tuple(
        f"{item.name}: {reason}"
        for item in predicates
        if item.disposition != "PASSED"
        for reason in item.reasons
        if item.disposition != "NOT_EVALUATED"
    )
    value = receipt.CaseReceipt(
        receipt.SCHEMA,
        plan.case_id,
        plan.source_commit,
        registration_sha256,
        lifecycle.plan_sha256(plan),
        start_sha256,
        terminal_sha256,
        evidence_sha256,
        numerical_sha256,
        inverse_sha256,
        evidence_total_bytes,
        terminal["reason"],
        terminal["exit_code"],
        status,
        predicates,
        work,
        None,
        None,
        reasons,
    )
    digest = receipt.write_receipt(
        directory, value, plan, registration_sha256,
    )
    return value, digest


def _case_status(predicates: tuple[receipt.PredicateRecord, ...]) -> str:
    return receipt._expected_status(predicates, "completed", 0)


def _case_reasons(predicates: tuple[receipt.PredicateRecord, ...]) -> tuple[str, ...]:
    if all(value.disposition == "PASSED" for value in predicates):
        return ()
    values = tuple(
        f"{predicate.name}: {reason}"
        for predicate in predicates
        if predicate.disposition != "PASSED"
        for reason in predicate.reasons
    )
    if not values or len(values) > 128:
        raise ValueError("bounded F03 case reason inventory required")
    return values


def adjudicate_case(
    directory: Path,
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    source_commit: str,
    registration_sha256: str,
    budgets: budget_contract.ScientificAdjudicationBudgets,
) -> tuple[receipt.CaseReceipt, str]:
    """Replay one complete case and exclusively write its closure receipt."""
    directory = Path(directory)
    fresh = cases.preflight_inventory()
    budget_contract.require_scientific_budgets(budgets)
    if (
        not directory.is_dir()
        or type(record) is not cases.CasePreflight
        or type(records) is not tuple
        or records != fresh
        or record not in records
    ):
        raise ValueError("exact preflighted F03 case directory and inventory required")
    case = record.case
    grid = cases.compile_case(case)
    plan = archive.read_plan(directory / "plan.zip", record, records, source_commit)
    terminal, terminal_sha256 = lifecycle.read_terminal(
        directory, plan, registration_sha256,
    )
    start, start_sha256 = lifecycle.read_start(directory, plan, registration_sha256)
    if (
        terminal["reason"] != "completed"
        or terminal["exit_code"] != 0
        or terminal["start_sha256"] != start_sha256
        or terminal["root_pid"] != start["pid"]
    ):
        raise ValueError("complete successful F03 lifecycle required for numerical adjudication")

    evidence, evidence_sha256 = evidence_index.read_index(
        directory, plan, registration_sha256, start_sha256,
    )
    with evidence_index.materialized_snapshot(
        directory, plan, evidence,
        (("start.json", start_sha256), ("terminal.json", terminal_sha256)),
    ) as snapshot:
        retained_terminal, retained_terminal_sha256 = lifecycle.read_terminal(
            snapshot, plan, registration_sha256,
        )
        retained_start, retained_start_sha256 = lifecycle.read_start(
            snapshot, plan, registration_sha256,
        )
        if (
            retained_terminal != terminal
            or retained_terminal_sha256 != terminal_sha256
            or retained_start != start
            or retained_start_sha256 != start_sha256
        ):
            raise ValueError("F03 retained lifecycle evidence disagrees with source read")
        terminal = retained_terminal
        terminal_sha256 = retained_terminal_sha256
        start_sha256 = retained_start_sha256
        indexed, numerical_sha256 = numerical_index.read_index(
            snapshot / "numerical_index.json", plan,
        )
        saved_index, saved = numerical_index.read_saved(snapshot, plan)
        if saved_index != indexed:
            raise ValueError("F03 saved numerical evidence changed after index verification")
        inverse_index, inverse_sha256 = inverse_storage.read_index(snapshot, plan)
        # The nested/cross-family transfer evidence is part of every case archive;
        # it is structurally validated here and consumed by later inventory gates.
        prolongation_storage.read(snapshot, case)
        saved_interface = saved_storage.read_interface(
            snapshot / "saved_interface.npz", case,
        )
        saved_work = saved_storage.read_work(snapshot / "saved_work.npz", case)
        saved_norm = saved_storage.read_norm(snapshot / "saved_norm.npz")
        saved_summary = result_storage.read_composition(
            snapshot / "saved_composition.npz",
        )
        saved_balances = result_storage.read_balances(snapshot / "balances.npz")

        bound = replay_binding.verify_numerical_binding(
            indexed.positivity_producer, saved,
        )
        primary, alternate, scaled, proof, ports = (
            saved.operator_primary, saved.operator_alternate, saved.scaled,
            saved.positivity, saved.port_evidence,
        )

        def inverse_blocks():
            for block, indexed_block in zip(plan.inverse_blocks, inverse_index.blocks):
                if block.start != indexed_block.start:
                    raise ValueError("F03 inverse index order disagrees with plan")
                yield inverse_storage.read_block(snapshot, plan, block.start)

        integrated = integration.verify_integration(
            scaled.h, scaled.h_alternate, scaled.b, scaled.b_alternate, scaled.z,
            inverse_blocks(), case.physical_dofs, budget=budgets.integration,
        )
        positive = None
        if bound.positivity_candidate_status == "CANDIDATE_CREATED":
            positive = positivity.certify_positive(
                proof.kbar, proof.lower, proof.diagonal,
                tuple(int(value) for value in proof.inverse_gather),
                budget=budgets.positivity,
            )
        state = state_binding.verify_binding(
            primary.shell, primary.beam, primary.root, primary.load,
            scaled.d, scaled.h, scaled.b, scaled.q, scaled.eta, scaled.z,
            h_z=scaled.h_z, budget=budgets.binding,
        )
        ranked = rank.verify_root_rank(
            primary.root, ports.free_slope, scaled.d, budget=budgets.rank,
        )
        traced = trace.verify_trace_binding(
            grid, scaled.q, scaled.d, ports.samples, ports.root, ports.tip,
            ports.free_slope, budget=budgets.trace,
        )
        equilibrated = equilibrium.verify_equilibrium(
            primary.shell, primary.beam, alternate.shell, alternate.beam,
            primary.root, primary.load, scaled.d, scaled.h, scaled.b,
            scaled.q, scaled.eta, scaled.z, scaled.h_z,
            budget=budgets.equilibrium,
        )
        composed = composition.verify_composition(
            grid, primary.shell, primary.beam, alternate.shell, alternate.beam,
            primary.root, primary.load, scaled.d, scaled.h, scaled.b,
            scaled.q, scaled.eta, scaled.z, scaled.h_z,
            saved_interface, saved_work, saved_norm, budget=budgets.composition,
        )
        if result_storage.composition_summary(composed) != saved_summary:
            raise ValueError("F03 saved composition summary disagrees with replay")
        balanced = balance.verify_balance(composed, saved_interface, saved_balances)
        bindings = binding_records.make_bindings(
            composed, grid, saved_interface, saved_work, saved_norm,
        )

        # Re-open the complete source evidence while the retained handles are
        # still live and require the same canonical identity before receipt.
        final_evidence, final_evidence_sha256 = evidence_index.read_index(
            directory, plan, registration_sha256, start_sha256,
        )
        if final_evidence != evidence or final_evidence_sha256 != evidence_sha256:
            raise ValueError("F03 evidence changed during solve-free adjudication")

        predicates = (
            _record("evidence", "PASSED"),
            _record("execution", "PASSED"),
            _condition_record(integrated["primary_certificate"]),
            _positivity_record(bound, positive),
            _status_record("state_scaling", state, "BINDING_PASSED", "FAILED"),
            _rank_record(ranked),
            _status_record("trace", traced, "TRACE_BINDING_PASSED", "FAILED"),
            _status_record(
                "equilibrium_energy", equilibrated,
                "NUMERICAL_MECHANICAL_CHECKS_PASSED", "HOLD",
            ),
            _status_record(
                "integration", integrated,
                "NUMERICAL_PERTURBATION_PASSED", "HOLD",
            ),
            _composition_record(composed),
            _balance_record(balanced),
        )
        value = receipt.CaseReceipt(
            receipt.SCHEMA, plan.case_id, plan.source_commit, registration_sha256,
            lifecycle.plan_sha256(plan), start_sha256, terminal_sha256,
            evidence_sha256, numerical_sha256, inverse_sha256,
            evidence.total_bytes, terminal["reason"], terminal["exit_code"],
            _case_status(predicates), predicates, _work(plan),
            bindings.settling, bindings.functional, _case_reasons(predicates),
        )
    digest = receipt.write_receipt(
        directory, value, plan, registration_sha256, bindings,
    )
    return value, digest
