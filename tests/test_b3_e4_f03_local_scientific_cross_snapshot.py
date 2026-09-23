"""Boundary tests for the retained F03 cross-case saved-data reader."""
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_snapshot as cross
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_prolongation as transfer


DIGEST = "b" * 64
SOURCE = "a" * 40


def _passing_receipt(plan):
    settling = receipt.SettlingRecord(
        (1.0,) * 45, (1.0,) * 45, (1.0,) * 45,
        receipt.SETTLING_SCALES, (DIGEST,) * 45,
    )
    functional = receipt.FunctionalRecord(
        DIGEST, (1.0,) * 6, (1.0,) * 2, (1.0,) * 36,
        (True,) * 18, (True,) * 6, (False,) * 2, ((), ()),
    )
    return receipt.CaseReceipt(
        receipt.SCHEMA, plan.case_id, SOURCE, DIGEST,
        lifecycle.plan_sha256(plan), DIGEST, DIGEST, DIGEST, DIGEST,
        DIGEST, 123, "completed", 0, "PASSED_CASE_NUMERICAL_SCREEN",
        tuple(receipt.PredicateRecord(name, "PASSED", ())
              for name in receipt.PREDICATE_NAMES),
        receipt.WorkRecord(tuple((name, 0) for name in receipt.WORK_NAMES)),
        settling, functional, (),
    )


def _mock_snapshot(monkeypatch, tmp_path, *, stale_on_exit=False):
    records = cases.preflight_inventory()
    record = records[0]
    plan = archive.make_case_plan(record, records, SOURCE)
    value = _passing_receipt(plan)
    directory = tmp_path / "cases" / record.case.case_id
    directory.mkdir(parents=True)
    snapshot = tmp_path / "private"
    snapshot.mkdir()
    index = SimpleNamespace(total_bytes=123)
    saved = SimpleNamespace(
        operator_primary=object(), scaled=object(), port_evidence=object(),
    )
    functional = object()
    seen = []
    registered = SimpleNamespace(
        source_commit=SOURCE,
        cases=tuple(SimpleNamespace(case_id=item.case.case_id,
                                    plan_archive_sha256=DIGEST) for item in records),
    )
    monkeypatch.setattr(cross.registration, "read_registration",
                        lambda *a: (registered, DIGEST))
    monkeypatch.setattr(cross, "_owned_receipt_digest", lambda _: DIGEST)
    monkeypatch.setattr(cross.adjudicator, "_verify_registered_plan_bytes", lambda *a: seen.append("plan"))
    monkeypatch.setattr(cross.archive, "read_plan", lambda *a: plan)
    monkeypatch.setattr(
        cross.lifecycle, "read_start", lambda *a: ({"pid": 7}, DIGEST),
    )
    monkeypatch.setattr(
        cross.lifecycle, "read_terminal",
        lambda *a: ({"reason": "completed", "exit_code": 0,
                    "start_sha256": DIGEST, "root_pid": 7}, DIGEST),
    )
    calls = [0]

    def read_evidence(*_):
        calls[0] += 1
        return (SimpleNamespace(total_bytes=124) if stale_on_exit and calls[0] == 2 else index), DIGEST

    monkeypatch.setattr(cross.evidence_index, "read_index", read_evidence)

    @contextmanager
    def retained(*_):
        seen.append("enter")
        yield snapshot
        seen.append("exit")

    monkeypatch.setattr(cross.evidence_index, "materialized_snapshot", retained)
    monkeypatch.setattr(cross.numerical_index, "read_index", lambda *a: ("header", DIGEST))
    monkeypatch.setattr(cross.numerical_index, "read_saved", lambda *a: ("header", saved))
    monkeypatch.setattr(cross.inverse_storage, "read_index", lambda *a: (object(), DIGEST))
    monkeypatch.setattr(cross.saved_storage, "read_interface", lambda *a: object())
    monkeypatch.setattr(cross.interface_checks, "_saved_functional", lambda *a: functional)
    monkeypatch.setattr(cross.saved_storage, "read_norm", lambda *a: object())
    monkeypatch.setattr(cross.norm_checks, "input_identity", lambda *a: DIGEST)
    monkeypatch.setattr(cross.prolongation_storage, "read", lambda *a: None)
    return directory, record, records, value, saved, functional, seen


def test_snapshot_retains_one_read_for_comparison_and_rechecks_on_exit(monkeypatch, tmp_path):
    directory, record, records, value, saved, functional, seen = _mock_snapshot(
        monkeypatch, tmp_path,
    )
    with cross.open_case_snapshot(
        directory, record, records, SOURCE, DIGEST, value, DIGEST,
        run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
    ) as opened:
        assert opened.case_id == record.case.case_id
        assert opened.saved is saved
        assert opened.functional is functional
        assert seen == ["plan", "enter"]
    assert seen == ["plan", "enter", "plan", "exit"]


def test_snapshot_rejects_changed_index_before_returning_success(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(
        monkeypatch, tmp_path, stale_on_exit=True,
    )
    with pytest.raises(ValueError, match="evidence changed"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            pass


def test_snapshot_rejects_stale_functional_identity(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(monkeypatch, tmp_path)
    monkeypatch.setattr(cross.norm_checks, "input_identity", lambda *a: "c" * 64)
    with pytest.raises(ValueError, match="functional input identity"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            pass


def test_snapshot_rejects_receipt_change_during_comparison(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(monkeypatch, tmp_path)
    hashes = iter((DIGEST, "c" * 64))
    monkeypatch.setattr(cross, "_owned_receipt_digest", lambda _: next(hashes))
    with pytest.raises(ValueError, match="receipt changed during"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            pass


def test_snapshot_rechecks_registered_source_identity_on_exit(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(monkeypatch, tmp_path)
    original = cross.registration.read_registration
    calls = [0]

    def changed_source(*args):
        calls[0] += 1
        registered, digest = original(*args)
        if calls[0] == 2:
            return SimpleNamespace(source_commit="c" * 40, cases=registered.cases), digest
        return registered, digest

    monkeypatch.setattr(cross.registration, "read_registration", changed_source)
    with pytest.raises(ValueError, match="source or registration changed"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            pass


def test_snapshot_rechecks_mutation_on_exceptional_exit(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(
        monkeypatch, tmp_path, stale_on_exit=True,
    )
    with pytest.raises(ValueError, match="evidence changed"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            raise RuntimeError("comparison aborted")


def test_snapshot_preserves_clean_comparison_exception(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError, match="comparison aborted"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            raise RuntimeError("comparison aborted")


def test_snapshot_rejects_nonpassing_case_before_any_source_read(monkeypatch, tmp_path):
    directory, record, records, value, *_ = _mock_snapshot(monkeypatch, tmp_path)
    value = replace(value, status="FAILED_NUMERICAL_SCREEN", reasons=("failed",))
    with pytest.raises(ValueError, match="passing replayed"):
        with cross.open_case_snapshot(
            directory, record, records, SOURCE, DIGEST, value, DIGEST,
            run_root=directory.parent.parent, plan_archive_sha256=DIGEST,
        ):
            pass


def test_frozen_topology_rederivation_rejects_changed_exact_interpolation():
    case = cases.case_by_id("Q1_L1")
    source = cases.case_by_id("Q1_L0")
    expected = transfer.prolongation(
        cases.compile_case(source), cases.compile_case(case),
        max_entries=case.physical_dofs * (source.degree + 1) ** 2,
        max_integer_bits=cases.ASSEMBLY_BUDGET.max_trace_integer_bits,
        max_work_bytes=cases.ASSEMBLY_BUDGET.max_work_bytes,
    )
    saved, rebuilt = cross._verified_prolongation(case, expected)
    assert saved is expected
    assert np.array_equal(rebuilt.rows, expected.rows)
    changed = object.__new__(transfer.ExactProlongation)
    for name in expected.__dataclass_fields__:
        object.__setattr__(changed, name, getattr(expected, name))
    rows = np.array(expected.rows, copy=True)
    rows[0] += 1
    object.__setattr__(changed, "rows", rows)
    with pytest.raises(ValueError, match="disagrees with frozen topology"):
        cross._verified_prolongation(case, changed)


def test_snapshot_adapts_saved_physical_blocks_without_recovery(monkeypatch):
    records = cases.preflight_inventory()
    plan = archive.make_case_plan(records[0], records, SOURCE)
    value = _passing_receipt(plan)
    primary = SimpleNamespace(shell="shell", beam="beam", root="root", load="load")
    ports = SimpleNamespace(samples="samples", root="root port", tip="tip port",
                            free_slope="slope")
    saved = SimpleNamespace(operator_primary=primary,
                            scaled=SimpleNamespace(q="physical q"), port_evidence=ports)
    snapshot = cross.CaseSnapshot(
        records[0].case.case_id, value, DIGEST, DIGEST, DIGEST, DIGEST, DIGEST,
        saved, "owned functional", None, None,
    )
    captured = []
    monkeypatch.setattr(cross.cross_math, "CaseData", lambda *args: captured.append(args))
    snapshot.case_data()
    assert len(captured) == 1
    assert captured[0][:4] == (
        records[0].case.case_id, value.settling, value.functional, "owned functional",
    )
    assert captured[0][4:] == (
        "physical q", "shell", "beam", "root", "load", "samples",
        "root port", "tip port", "slope",
    )
