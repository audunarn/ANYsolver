from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_supervisor as supervisor


DIGEST = "ab" * 32
SOURCE = "a" * 40


@pytest.fixture(scope="module")
def plan():
    records = cases.preflight_inventory()
    return archive.make_case_plan(records[0], records, SOURCE)


def _work(plan):
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


def _predicates(**changed):
    records = []
    for name in receipt.PREDICATE_NAMES:
        disposition = changed.get(name, "PASSED")
        reasons = () if disposition == "PASSED" else (f"{name} {disposition.lower()}",)
        records.append(receipt.PredicateRecord(name, disposition, reasons))
    return tuple(records)


def _failed_evidence_predicates():
    return _predicates(**{
        name: "FAILED" if name == "evidence" else "NOT_EVALUATED"
        for name in receipt.PREDICATE_NAMES
    })


def _settling():
    count = len(receipt.SETTLING_NAMES)
    return receipt.SettlingRecord(
        tuple(float(index) for index in range(count)),
        tuple(float(index) - 0.25 for index in range(count)),
        tuple(float(index) + 0.25 for index in range(count)),
        receipt.SETTLING_SCALES,
        (DIGEST,) * count,
    )


def _functional():
    return receipt.FunctionalRecord(
        DIGEST, (1.0,) * 6, (1.0,) * 2, (1.0,) * 36,
        (True,) * 18, (True,) * 6, (False,) * 2, ((), ()),
    )


def _bindings(value):
    return receipt.AdjudicationBindings(value.settling, value.functional)


def _receipt(plan, *, predicates=None, status="PASSED_CASE_NUMERICAL_SCREEN",
             terminal_reason="completed", terminal_exit_code=0, complete=True):
    return receipt.CaseReceipt(
        receipt.SCHEMA, plan.case_id, plan.source_commit, DIGEST,
        lifecycle.plan_sha256(plan), DIGEST if complete else None, DIGEST,
        DIGEST if complete else None, DIGEST if complete else None,
        DIGEST if complete else None, 12345 if complete else None,
        terminal_reason, terminal_exit_code, status,
        _predicates() if predicates is None else predicates, _work(plan),
        _settling() if complete else None, _functional() if complete else None,
        () if status == "PASSED_CASE_NUMERICAL_SCREEN" else ("case did not pass",),
    )


def test_complete_receipt_roundtrip_is_exclusive_canonical_and_self_describing(plan, tmp_path):
    directory = tmp_path / "case"; directory.mkdir()
    value = _receipt(plan)
    bindings = _bindings(value)
    digest = receipt.write_receipt(directory, value, plan, DIGEST, bindings)
    restored = receipt._decode(
        (directory / "case_receipt.json").read_bytes(), plan, DIGEST, bindings,
    )
    observed = digest
    assert restored == value
    assert observed == digest
    assert tuple(item.name for item in restored.predicates) == receipt.PREDICATE_NAMES
    assert len(restored.settling.values) == 45
    with pytest.raises(FileExistsError):
        receipt.write_receipt(directory, value, plan, DIGEST, bindings)


@pytest.mark.parametrize("predicate,status", (
    ("condition_backward", "FAILED_NUMERICAL_SCREEN"),
    ("integration", "FAILED_NUMERICAL_SCREEN"),
    ("positivity", "UNRESOLVED_NUMERICAL_SCREEN"),
    ("composition", "UNRESOLVED_NUMERICAL_SCREEN"),
))
def test_numerical_failure_and_hold_precedence(plan, predicate, status):
    disposition = "FAILED" if status == "FAILED_NUMERICAL_SCREEN" else "HOLD_UNRESOLVED"
    value = _receipt(plan, predicates=_predicates(**{predicate: disposition}), status=status)
    bindings = _bindings(value)
    assert receipt.validate_receipt(value, plan, DIGEST, bindings) is value
    with pytest.raises(ValueError, match="precedence"):
        receipt.validate_receipt(
            replace(value, status="PASSED_CASE_NUMERICAL_SCREEN", reasons=()),
            plan, DIGEST, bindings,
        )


def test_evidence_and_execution_failure_precedence_allow_explicit_missing_artifacts(plan):
    evidence_failed = _receipt(
        plan, predicates=_failed_evidence_predicates(),
        status="FAILED_EVIDENCE", terminal_reason="completed", terminal_exit_code=1,
        complete=False,
    )
    assert receipt.validate_receipt(evidence_failed, plan, DIGEST) is evidence_failed
    execution_failed = replace(
        _receipt(
            plan, predicates=_predicates(execution="FAILED"), status="FAILED_EXECUTION",
            terminal_reason="time_limit", terminal_exit_code=-9, complete=True,
        ),
        settling=None, functional=None,
    )
    assert receipt.validate_receipt(execution_failed, plan, DIGEST) is execution_failed


def test_complete_receipt_rejects_hidden_work_missing_artifacts_and_bad_observations(plan):
    value = _receipt(plan)
    bindings = _bindings(value)
    counts = dict(value.work.values); counts["replay_factorizations"] = 1
    with pytest.raises(ValueError, match="work"):
        receipt.validate_receipt(
            replace(value, work=receipt.WorkRecord(tuple(
                (name, counts[name]) for name in receipt.WORK_NAMES
            ))), plan, DIGEST, bindings,
        )
    with pytest.raises(ValueError, match="work"):
        receipt.validate_receipt(
            replace(value, evidence_index_sha256=None), plan, DIGEST, bindings,
        )
    with pytest.raises(ValueError, match="enclosure"):
        replace(value.settling, lower=(1.0,) + value.settling.lower[1:])


def test_read_rejects_noncanonical_or_extra_json(plan, tmp_path):
    directory = tmp_path / "case"; directory.mkdir()
    value = _receipt(plan); bindings = _bindings(value)
    receipt.write_receipt(directory, value, plan, DIGEST, bindings)
    path = directory / "case_receipt.json"
    raw = json.loads(path.read_text("ascii")); raw["extra"] = True
    path.write_bytes((json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
    with pytest.raises(ValueError, match="inventory"):
        receipt.read_receipt(directory, plan, DIGEST, bindings)


def test_read_receipt_closes_actual_launch_failure_lifecycle(plan, tmp_path):
    directory = tmp_path / "failed"; directory.mkdir()
    terminal_digest = lifecycle.write_terminal(
        directory, plan, DIGEST,
        supervisor.SupervisionReceipt(
            "launch_failure", None, None, 0.5, 0, (), (), "synthetic launch failure",
        ),
    )
    value = replace(
        _receipt(
            plan, predicates=_failed_evidence_predicates(),
            status="FAILED_EVIDENCE", terminal_reason="launch_failure",
            terminal_exit_code=None, complete=False,
        ),
        terminal_sha256=terminal_digest,
    )
    receipt.write_receipt(directory, value, plan, DIGEST)
    restored, _ = receipt.read_receipt(directory, plan, DIGEST)
    assert restored == value
    with pytest.raises(ValueError):
        receipt.read_receipt(directory, plan, "cd" * 32)


def test_complete_read_closes_all_saved_identity_readers(plan, tmp_path, monkeypatch):
    directory = tmp_path / "complete-read"; directory.mkdir()
    (directory / "start.json").write_text("marker", encoding="ascii")
    value = _receipt(plan)
    bindings = _bindings(value)
    receipt.write_receipt(directory, value, plan, DIGEST, bindings)
    monkeypatch.setattr(
        receipt.lifecycle, "read_terminal",
        lambda *args: ({"reason": "completed", "exit_code": 0}, DIGEST),
    )
    monkeypatch.setattr(receipt.lifecycle, "read_start", lambda *args: ({}, DIGEST))
    monkeypatch.setattr(
        receipt.evidence, "read_index",
        lambda *args: (SimpleNamespace(total_bytes=12345), DIGEST),
    )
    monkeypatch.setattr(receipt.numerical_index, "read_index", lambda *args: (None, DIGEST))
    monkeypatch.setattr(receipt.inverse_storage, "read_index", lambda *args: (None, DIGEST))
    restored, _ = receipt.read_receipt(directory, plan, DIGEST, bindings)
    assert restored == value
    monkeypatch.setattr(
        receipt.numerical_index, "read_index", lambda *args: (None, "cd" * 32),
    )
    with pytest.raises(ValueError, match="identities"):
        receipt.read_receipt(directory, plan, DIGEST, bindings)


def test_functional_optional_values_are_explicit_and_boolean_types_are_strict():
    value = receipt.FunctionalRecord(
        DIGEST, (None,) * 6, (None,) * 2, (None,) * 36,
        (False,) * 18, (False,) * 6, (False,) * 2,
        ((("stage", 0, "unavailable 48"),),
         (("stage", 1, "unavailable 64"),)),
    )
    assert value.channels == (None,) * 6
    with pytest.raises(ValueError, match="flag"):
        replace(value, exact_zero=(0, False))


def test_complete_receipt_requires_exact_external_observation_bindings(plan):
    value = _receipt(plan)
    bindings = _bindings(value)
    assert receipt.validate_receipt(value, plan, DIGEST, bindings) is value
    with pytest.raises(ValueError, match="plan, precedence, or work"):
        receipt.validate_receipt(value, plan, DIGEST)
    changed_scales = tuple(
        scale * 2.0 if index == 0 else scale
        for index, scale in enumerate(receipt.SETTLING_SCALES)
    )
    with pytest.raises(ValueError, match="frozen scale"):
        replace(value.settling, scales=changed_scales)
    changed_sources = replace(
        value.settling,
        source_sha256s=(("cd" * 32),) + value.settling.source_sha256s[1:],
    )
    with pytest.raises(ValueError, match="plan, precedence, or work"):
        receipt.validate_receipt(
            replace(value, settling=changed_sources), plan, DIGEST, bindings,
        )
    changed_functional = replace(
        value.functional, functional_sha256="cd" * 32,
    )
    with pytest.raises(ValueError, match="plan, precedence, or work"):
        receipt.validate_receipt(
            replace(value, functional=changed_functional), plan, DIGEST, bindings,
        )
    signed_zero = replace(
        value.settling, values=(-0.0,) + value.settling.values[1:],
    )
    with pytest.raises(ValueError, match="plan, precedence, or work"):
        receipt.validate_receipt(
            replace(value, settling=signed_zero), plan, DIGEST, bindings,
        )


def test_passing_receipt_requires_complete_admissible_functional_evidence(plan):
    value = _receipt(plan)
    empty = receipt.FunctionalRecord(
        DIGEST, (None,) * 6, (None,) * 2, (None,) * 36,
        (False,) * 18, (False,) * 6, (False,) * 2, ((), ()),
    )
    invalid = replace(value, functional=empty)
    with pytest.raises(ValueError, match="plan, precedence, or work"):
        receipt.validate_receipt(
            invalid, plan, DIGEST,
            receipt.AdjudicationBindings(value.settling, empty),
        )


def test_failed_functional_layout_requires_failed_composition_predicate(plan):
    failed = receipt.FunctionalRecord(
        DIGEST, (None,) * 6, (None,) * 2, (None,) * 36,
        (False,) * 18, (False,) * 6, (False,) * 2,
        ((("quadrature", 0, "unavailable"),), ()),
    )
    predicates = _predicates(composition="FAILED")
    value = replace(
        _receipt(plan, predicates=predicates, status="FAILED_NUMERICAL_SCREEN"),
        functional=failed,
    )
    bindings = receipt.AdjudicationBindings(value.settling, failed)
    assert receipt.validate_receipt(value, plan, DIGEST, bindings) is value
    with pytest.raises(ValueError, match="plan, precedence, or work"):
        receipt.validate_receipt(
            replace(value, predicates=_predicates(integration="FAILED")),
            plan, DIGEST, bindings,
        )
