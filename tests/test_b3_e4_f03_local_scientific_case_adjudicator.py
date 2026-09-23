from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_balance_adjudication as balance
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_case_adjudicator as adjudicator
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_replay_binding as replay
from scripts import _b3_e4_f03_local_scientific_supervisor as supervisor


DIGEST = "ab" * 32
SOURCE = "a" * 40


def _pass_result(status):
    return {"status": status, "failures": ()}


def test_predicate_mapping_distinguishes_failure_hold_and_unresolved():
    assert adjudicator._status_record(
        "state_scaling", _pass_result("BINDING_PASSED"),
        "BINDING_PASSED", "FAILED",
    ).disposition == "PASSED"
    failed = adjudicator._status_record(
        "state_scaling", {"status": "HOLD", "failures": ("mismatch",)},
        "BINDING_PASSED", "FAILED",
    )
    held = adjudicator._status_record(
        "integration", {"status": "HOLD", "failures": ("unresolved",)},
        "NUMERICAL_PERTURBATION_PASSED", "HOLD",
    )
    assert (failed.disposition, failed.reasons) == ("FAILED", ("mismatch",))
    assert (held.disposition, held.reasons) == ("HOLD", ("unresolved",))
    for status, expected in (
        ("COMPONENT_CHECKS_PASSED", "PASSED"),
        ("COMPOSITION_FAILED", "FAILED"),
        ("HOLD_NUMERICAL", "HOLD"),
        ("HOLD_UNRESOLVED", "HOLD_UNRESOLVED"),
    ):
        reasons = () if expected == "PASSED" else ("reason",)
        assert adjudicator._composition_record(
            {"status": status, "reasons": reasons},
        ).disposition == expected


def test_positivity_hold_never_attempts_to_invent_a_proof():
    bound = replay.ReplayBinding("HOLD", "native maps differ", *([DIGEST] * 4))
    value = adjudicator._positivity_record(bound, None)
    assert value.disposition == "HOLD"
    assert value.reasons == ("native maps differ",)


def _install_complete_archive_mocks(monkeypatch, tmp_path, *, mutate_final=False):
    records = cases.preflight_inventory()
    record = records[0]
    plan = archive.make_case_plan(record, records, SOURCE)
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    snapshot_dir = tmp_path / "retained-snapshot"
    snapshot_dir.mkdir()
    grid = object()
    saved_interface = object()
    saved_work = object()
    saved_norm = object()
    composed = {
        "status": "COMPONENT_CHECKS_PASSED", "reasons": (),
    }
    bindings = SimpleNamespace(settling=object(), functional=object())
    primary = SimpleNamespace(shell=object(), beam=object(), root=object(), load=object())
    alternate = SimpleNamespace(shell=object(), beam=object())
    scaled = SimpleNamespace(
        h=object(), h_alternate=object(), b=object(), b_alternate=object(),
        z=object(), d=object(), q=object(), eta=object(), h_z=object(),
    )
    proof = SimpleNamespace(
        kbar=object(), lower=object(), diagonal=object(),
        inverse_gather=np.arange(3, dtype=np.int64),
    )
    ports = SimpleNamespace(samples=object(), root=object(), tip=object(), free_slope=object())
    saved = SimpleNamespace(
        operator_primary=primary, operator_alternate=alternate, scaled=scaled,
        positivity=proof, port_evidence=ports,
    )
    numerical = SimpleNamespace(positivity_producer=object())
    observed = SimpleNamespace(total_bytes=12345)
    final = SimpleNamespace(total_bytes=12346) if mutate_final else observed
    events = []

    monkeypatch.setattr(adjudicator.cases, "preflight_inventory", lambda: records)
    monkeypatch.setattr(adjudicator.cases, "compile_case", lambda value: grid)
    monkeypatch.setattr(adjudicator.archive, "read_plan", lambda *args: plan)
    monkeypatch.setattr(
        adjudicator.lifecycle, "read_terminal",
        lambda *args: ({"reason": "completed", "exit_code": 0,
                       "start_sha256": DIGEST, "root_pid": 7}, DIGEST),
    )
    monkeypatch.setattr(
        adjudicator.lifecycle, "read_start", lambda *args: ({"pid": 7}, DIGEST),
    )
    evidence_calls = iter(((observed, DIGEST), (final, DIGEST)))
    monkeypatch.setattr(adjudicator.evidence_index, "read_index", lambda *args: next(evidence_calls))
    @contextmanager
    def retained(*args):
        events.append("snapshot_enter")
        yield snapshot_dir
        events.append("snapshot_exit")
    monkeypatch.setattr(adjudicator.evidence_index, "materialized_snapshot", retained)
    monkeypatch.setattr(adjudicator.numerical_index, "read_index", lambda *args: (numerical, DIGEST))
    monkeypatch.setattr(adjudicator.numerical_index, "read_saved", lambda *args: (numerical, saved))
    inverse_index = SimpleNamespace(
        blocks=tuple(SimpleNamespace(start=block.start) for block in plan.inverse_blocks),
    )
    monkeypatch.setattr(
        adjudicator.inverse_storage, "read_index", lambda *args: (inverse_index, DIGEST),
    )
    monkeypatch.setattr(adjudicator.prolongation_storage, "read", lambda *args: None)
    monkeypatch.setattr(adjudicator.saved_storage, "read_interface", lambda *args: saved_interface)
    monkeypatch.setattr(adjudicator.saved_storage, "read_work", lambda *args: saved_work)
    monkeypatch.setattr(adjudicator.saved_storage, "read_norm", lambda *args: saved_norm)
    monkeypatch.setattr(adjudicator.result_storage, "read_composition", lambda *args: "summary")
    monkeypatch.setattr(adjudicator.result_storage, "read_balances", lambda *args: object())
    monkeypatch.setattr(
        adjudicator.replay_binding, "verify_numerical_binding",
        lambda *args: replay.ReplayBinding("CANDIDATE_CREATED", None, *([DIGEST] * 4)),
    )

    starts = []
    def read_block(directory, value, start):
        assert directory == snapshot_dir
        starts.append(start)
        block = next(item for item in value.inverse_blocks if item.start == start)
        return np.zeros((value.kkt_order, block.columns))
    monkeypatch.setattr(adjudicator.inverse_storage, "read_block", read_block)

    def integrate(*args, **kwargs):
        source = args[5]
        first = list(source)
        assert list(source) == []
        assert len(first) == len(plan.inverse_blocks)
        events.append("integration")
        return {
            "status": "NUMERICAL_PERTURBATION_PASSED", "failures": (),
            "primary_certificate": {"status": "CERTIFIED_WITHIN_LIMIT"},
        }
    monkeypatch.setattr(adjudicator.integration, "verify_integration", integrate)
    monkeypatch.setattr(
        adjudicator.positivity, "certify_positive",
        lambda *args, **kwargs: events.append("positivity") or
        {"status": "POSITIVE_QUADRATIC_FORM", "reason": None},
    )
    monkeypatch.setattr(
        adjudicator.state_binding, "verify_binding",
        lambda *args, **kwargs: _pass_result("BINDING_PASSED"),
    )
    monkeypatch.setattr(
        adjudicator.rank, "verify_root_rank",
        lambda *args, **kwargs: {"status": "PORT_RANK_PASSED"},
    )
    monkeypatch.setattr(
        adjudicator.trace, "verify_trace_binding",
        lambda *args, **kwargs: _pass_result("TRACE_BINDING_PASSED"),
    )
    monkeypatch.setattr(
        adjudicator.equilibrium, "verify_equilibrium",
        lambda *args, **kwargs: _pass_result("NUMERICAL_MECHANICAL_CHECKS_PASSED"),
    )
    monkeypatch.setattr(adjudicator.composition, "verify_composition", lambda *args, **kwargs: composed)
    monkeypatch.setattr(adjudicator.result_storage, "composition_summary", lambda value: "summary")
    monkeypatch.setattr(
        adjudicator.balance, "verify_balance",
        lambda *args: balance.BalanceAdjudication("PASSED", (), (DIGEST,) * 14),
    )
    monkeypatch.setattr(adjudicator.binding_records, "make_bindings", lambda *args: bindings)
    monkeypatch.setattr(
        adjudicator.receipt, "CaseReceipt",
        lambda *args: SimpleNamespace(arguments=args, predicates=args[14], work=args[15]),
    )
    written = []
    monkeypatch.setattr(
        adjudicator.receipt, "write_receipt",
        lambda *args: written.append(args) or DIGEST,
    )
    return records, record, plan, case_dir, starts, written, events


def test_complete_saved_only_route_consumes_inverse_stream_once_and_writes_exclusively(
    monkeypatch, tmp_path,
):
    records, record, plan, case_dir, starts, written, events = _install_complete_archive_mocks(
        monkeypatch, tmp_path,
    )
    value, digest = adjudicator.adjudicate_case(
        case_dir, record, records, SOURCE, DIGEST, budgets.make_scientific_budgets(),
    )
    assert digest == DIGEST
    assert starts == [block.start for block in plan.inverse_blocks]
    assert events == ["snapshot_enter", "integration", "positivity", "snapshot_exit"]
    assert len(written) == 1
    assert tuple(item.name for item in value.predicates) == receipt.PREDICATE_NAMES
    assert all(item.disposition == "PASSED" for item in value.predicates)
    assert value.work.as_dict()["replay_factorizations"] == 0
    assert value.work.as_dict()["replay_equilibrium_solves"] == 0


def test_final_evidence_snapshot_change_prevents_receipt(monkeypatch, tmp_path):
    records, record, _, case_dir, _, written, _ = _install_complete_archive_mocks(
        monkeypatch, tmp_path, mutate_final=True,
    )
    with pytest.raises(ValueError, match="changed during"):
        adjudicator.adjudicate_case(
            case_dir, record, records, SOURCE, DIGEST, budgets.make_scientific_budgets(),
        )
    assert written == []


def test_missing_plan_or_terminal_failure_cannot_write_receipt(monkeypatch, tmp_path):
    records = cases.preflight_inventory()
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    monkeypatch.setattr(adjudicator.cases, "preflight_inventory", lambda: records)
    monkeypatch.setattr(adjudicator.cases, "compile_case", lambda case: object())
    monkeypatch.setattr(
        adjudicator.archive, "read_plan",
        lambda *args: (_ for _ in ()).throw(FileNotFoundError("plan.zip")),
    )
    monkeypatch.setattr(
        adjudicator.receipt, "write_receipt",
        lambda *args: pytest.fail("receipt written after missing plan"),
    )
    with pytest.raises(FileNotFoundError):
        adjudicator.adjudicate_case(
            case_dir, records[0], records, SOURCE, DIGEST,
            budgets.make_scientific_budgets(),
        )


def _failure_case(tmp_path, *, reason="launch_failure", exit_code=None, with_start=False):
    records = cases.preflight_inventory()
    plan = archive.make_case_plan(records[0], records, SOURCE)
    directory = tmp_path / reason
    directory.mkdir()
    root_pid = 731 if with_start else None
    if with_start:
        lifecycle.write_start(directory, plan, DIGEST, root_pid)
    lifecycle.write_terminal(
        directory, plan, DIGEST,
        supervisor.SupervisionReceipt(
            reason, exit_code, root_pid, 0.25, 4096 if root_pid is not None else 0,
            (root_pid,) if root_pid is not None else (),
            (root_pid,) if root_pid is not None else (),
            f"synthetic {reason}",
        ),
    )
    return plan, directory


def _complete_evidence_mocks(monkeypatch, plan):
    kkt = SimpleNamespace(
        factorization_count=1,
        candidate_rhs_solves=1,
        certificate_solve_calls=len(plan.inverse_blocks),
        certificate_rhs_attempted=plan.kkt_order,
        certificate_rhs_completed=plan.kkt_order,
        recovery_factorizations=0,
        recovery_solves=0,
    )
    positive = SimpleNamespace(factorization_count=1)
    indexed = SimpleNamespace(kkt_producer=kkt, positivity_producer=positive)
    monkeypatch.setattr(
        adjudicator.evidence_index, "read_index",
        lambda *args: (SimpleNamespace(total_bytes=1234), DIGEST),
    )
    monkeypatch.setattr(
        adjudicator.numerical_index, "read_index",
        lambda *args: (indexed, DIGEST),
    )
    monkeypatch.setattr(
        adjudicator.inverse_storage, "read_index", lambda *args: (object(), DIGEST),
    )


def test_failure_factory_closes_launch_failure_as_failed_evidence(tmp_path):
    plan, directory = _failure_case(tmp_path)
    value, digest = adjudicator.close_failed_case(
        directory, plan, DIGEST,
        evidence_failure="registered child could not be launched",
    )
    assert len(digest) == 64
    assert value.status == "FAILED_EVIDENCE"
    assert value.predicates[0].disposition == "FAILED"
    assert all(item.disposition == "NOT_EVALUATED" for item in value.predicates[1:])
    assert all(count == 0 for _, count in value.work.values)
    restored, restored_digest = receipt.read_receipt(directory, plan, DIGEST)
    assert (restored, restored_digest) == (value, digest)
    with pytest.raises(FileExistsError):
        adjudicator.close_failed_case(
            directory, plan, DIGEST,
            evidence_failure="second closure is forbidden",
        )


def test_failure_factory_missing_archive_precedes_execution_failure(tmp_path):
    plan, directory = _failure_case(
        tmp_path, reason="time_limit", exit_code=-9, with_start=True,
    )
    value, _ = adjudicator.close_failed_case(directory, plan, DIGEST)
    assert value.status == "FAILED_EVIDENCE"
    assert value.predicates[0].disposition == "FAILED"
    assert value.predicates[1].disposition == "NOT_EVALUATED"
    assert "evidence index" in value.predicates[0].reasons[0]


def test_failure_factory_retains_complete_evidence_for_execution_failure(
    monkeypatch, tmp_path,
):
    plan, directory = _failure_case(
        tmp_path, reason="time_limit", exit_code=-9, with_start=True,
    )
    _complete_evidence_mocks(monkeypatch, plan)
    value, _ = adjudicator.close_failed_case(directory, plan, DIGEST)
    assert value.status == "FAILED_EXECUTION"
    assert value.predicates[0].disposition == "PASSED"
    assert value.predicates[1].disposition == "FAILED"
    assert all(item.disposition == "NOT_EVALUATED" for item in value.predicates[2:])
    assert value.evidence_total_bytes == 1234
    assert value.evidence_index_sha256 == DIGEST
    assert value.work.as_dict()["producer_kkt_factorizations"] == 1
    assert value.work.as_dict()["replay_recovery_recomputations"] == 0


def test_explicit_evidence_failure_has_precedence_without_reading_archive(
    monkeypatch, tmp_path,
):
    plan, directory = _failure_case(
        tmp_path, reason="time_limit", exit_code=-9, with_start=True,
    )
    monkeypatch.setattr(
        adjudicator.evidence_index, "read_index",
        lambda *args: pytest.fail("archive read after explicit evidence failure"),
    )
    value, _ = adjudicator.close_failed_case(
        directory, plan, DIGEST, evidence_failure="supervisor integrity failure",
    )
    assert value.status == "FAILED_EVIDENCE"
    assert value.evidence_index_sha256 is None


def test_failure_factory_rejects_successful_lifecycle(monkeypatch, tmp_path):
    plan, directory = _failure_case(
        tmp_path, reason="completed", exit_code=0, with_start=True,
    )
    _complete_evidence_mocks(monkeypatch, plan)
    with pytest.raises(ValueError, match="requires full adjudication"):
        adjudicator.close_failed_case(directory, plan, DIGEST)
    assert not (directory / "case_receipt.json").exists()


def test_failure_factory_does_not_classify_programming_or_memory_faults(
    monkeypatch, tmp_path,
):
    plan, directory = _failure_case(
        tmp_path, reason="time_limit", exit_code=-9, with_start=True,
    )
    monkeypatch.setattr(
        adjudicator.evidence_index, "read_index",
        lambda *args: (_ for _ in ()).throw(MemoryError("synthetic exhaustion")),
    )
    with pytest.raises(MemoryError, match="synthetic exhaustion"):
        adjudicator.close_failed_case(directory, plan, DIGEST)
    assert not (directory / "case_receipt.json").exists()
