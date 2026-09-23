"""Synthetic, no-launch tests of F03 aggregate inventory and precedence."""
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest

from scripts import _b3_e4_f03_local_scientific_aggregate as aggregate
from scripts import _b3_e4_f03_local_scientific_aggregate_receipt as aggregate_receipt
from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_math as arithmetic
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_registration as registration


DIGEST = "b" * 64
SOURCE = "a" * 40


def _pair_result(pair):
    nested = pair in arithmetic.NESTED_PAIRS
    return arithmetic.PairResult(
        pair, nested, True, (), (0.0,) * 45, (0.0,) * 45,
        1.0, 1.0, 0.0, 0.0, 0.0,
        0.0 if nested else None, 0.0 if nested else None,
        (tuple((name, 0.0) for name in aggregate_receipt._COMPATIBILITY_NAMES)
         if nested else ()),
        (("union_intervals", 1), ("input_integer_bits", 1),
         ("operations_estimate", 1), ("workspace_estimate_bytes", 1)),
    )


def _receipt(plan, status="PASSED_CASE_NUMERICAL_SCREEN"):
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
        DIGEST, 123, "completed", 0, status,
        tuple(receipt.PredicateRecord(name, "PASSED", ())
              for name in receipt.PREDICATE_NAMES),
        receipt.WorkRecord(tuple((name, 0) for name in receipt.WORK_NAMES)),
        settling, functional,
        () if status == "PASSED_CASE_NUMERICAL_SCREEN" else ("numerical failure",),
    )


def _fixture(monkeypatch, *, missing=None, incomplete=None,
             numerical=None, replay_error=None, chain_pass=True):
    records = cases.preflight_inventory()
    plans = {record.case.case_id: archive.make_case_plan(record, records, SOURCE)
             for record in records}
    bound = tuple(SimpleNamespace(
        case_id=record.case.case_id, plan_archive_sha256=DIGEST,
        plan_sha256=lifecycle.plan_sha256(plans[record.case.case_id]),
    ) for record in records)
    registered = SimpleNamespace(
        source_commit=SOURCE, cases=bound,
        sources=tuple(registration.SourceIdentity(role, path, 1, DIGEST)
                      for role, path in registration.SOURCE_ROLES),
        process_limits=registration.process_contract(),
        resource_limits=registration.resource_contract(),
        tolerances=registration.tolerance_contract(),
    )
    monkeypatch.setattr(aggregate.registration, "read_registration",
                        lambda *a: (registered, DIGEST))
    monkeypatch.setattr(aggregate.cases, "preflight_inventory", lambda: records)
    monkeypatch.setattr(aggregate.adjudicator, "_verify_registered_plan_bytes",
                        lambda *a: None)
    monkeypatch.setattr(aggregate.archive, "read_plan",
                        lambda path, *_: plans[path.parent.name])
    monkeypatch.setattr(aggregate.lifecycle, "read_terminal", lambda path, *_: (
        {"reason": "timeout" if path.name == incomplete else "completed",
         "exit_code": -1 if path.name == incomplete else 0,
         "start_sha256": DIGEST, "root_pid": 7}, DIGEST,
    ))
    monkeypatch.setattr(aggregate.lifecycle, "read_start",
                        lambda *a: ({"pid": 7}, DIGEST))

    def read_digest(path):
        if path.name == missing:
            raise FileNotFoundError("missing sealed receipt")
        return DIGEST

    monkeypatch.setattr(aggregate.cross_snapshot, "_owned_receipt_digest", read_digest)
    monkeypatch.setattr(aggregate.case_receipt, "read_receipt",
                        lambda path, *_: (
                            replace(_receipt(plans[path.name]),
                                    status="FAILED_EXECUTION", reasons=("timeout",),
                                    terminal_reason="timeout", terminal_exit_code=-1), DIGEST,
                        ))
    monkeypatch.setattr(aggregate.case_receipt, "read_receipt_inventory",
                        lambda path, *_: (_receipt(plans[path.name]), DIGEST))
    calls = {"replay": [], "snapshot": [], "compare": 0}

    def replay(path, *_args, **_kwargs):
        calls["replay"].append(path.name)
        if path.name == replay_error:
            raise ValueError("corrupt replayed observation")
        return _receipt(plans[path.name],
                        "FAILED_NUMERICAL_SCREEN" if path.name == numerical
                        else "PASSED_CASE_NUMERICAL_SCREEN"), DIGEST

    monkeypatch.setattr(aggregate.adjudicator, "replay_case", replay)

    @contextmanager
    def snapshot(path, *_args, **_kwargs):
        calls["snapshot"].append(path.name)
        yield SimpleNamespace(
            case_id=path.name,
            prolongation_sha256=(DIGEST if path.name in {
                fine for _, fine in arithmetic.NESTED_PAIRS} else None),
        )

    monkeypatch.setattr(aggregate.cross_snapshot, "open_case_snapshot", snapshot)

    def compare(values):
        calls["compare"] += 1
        assert tuple(value.case_id for value in values) == aggregate.CASE_ORDER
        pairs = tuple(_pair_result(pair) for pair in arithmetic.PAIR_ORDER)
        if not chain_pass:
            pairs = (replace(pairs[0], passed=False,
                             failures=("scalar root_reaction_x exceeds 1%",),
                             scalar_relatives=(0.02, *pairs[0].scalar_relatives[1:])),
                     *pairs[1:])
        return arithmetic.compare_chains(pairs)

    monkeypatch.setattr(aggregate.cross_bundle, "compare_snapshots", compare)
    return calls


def _adjudicate(tmp_path):
    return aggregate.adjudicate(
        tmp_path, registration_sha256=DIGEST,
        budgets=budgets.make_scientific_budgets(),
    )


def test_all_five_cases_are_replayed_before_cross_comparison(monkeypatch, tmp_path):
    calls = _fixture(monkeypatch)
    result = _adjudicate(tmp_path)
    assert result.status == "PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN"
    assert result.chain is not None and result.chain.passed
    assert tuple(item.prolongation_sha256 for item in result.inventory) == (
        None, DIGEST, DIGEST, DIGEST, DIGEST,
    )
    assert calls == {"replay": list(aggregate.CASE_ORDER),
                     "snapshot": list(aggregate.CASE_ORDER), "compare": 1}


def test_malformed_success_receipt_blocks_all_replay(monkeypatch, tmp_path):
    calls = _fixture(monkeypatch)
    original = aggregate.case_receipt.read_receipt_inventory

    def malformed(path, *args):
        if path.name == "Q1_L2":
            raise ValueError("noncanonical saved receipt")
        return original(path, *args)

    monkeypatch.setattr(aggregate.case_receipt, "read_receipt_inventory", malformed)
    result = _adjudicate(tmp_path)
    assert result.status == "FAILED_EVIDENCE"
    assert calls == {"replay": [], "snapshot": [], "compare": 0}


@pytest.mark.parametrize("incomplete,numerical", [
    ("Q2_L0", None), (None, "Q2_L0"),
])
def test_changed_case_evidence_after_inventory_is_rejected(
    monkeypatch, tmp_path, incomplete, numerical,
):
    _fixture(monkeypatch, incomplete=incomplete, numerical=numerical)
    original = aggregate.cross_snapshot._owned_receipt_digest
    reads = [0]

    def changed(path):
        reads[0] += 1
        if reads[0] > len(aggregate.CASE_ORDER) and path.name == "Q2_L0":
            return "c" * 64
        return original(path)

    monkeypatch.setattr(aggregate.cross_snapshot, "_owned_receipt_digest", changed)
    with pytest.raises(ValueError, match="case evidence changed"):
        _adjudicate(tmp_path)


@pytest.mark.parametrize("missing,incomplete,expected", [
    ("Q1_L2", None, "FAILED_EVIDENCE"),
    (None, "Q2_L0", "FAILED_EXECUTION"),
])
def test_incomplete_inventory_blocks_all_replay_and_cross_work(
    monkeypatch, tmp_path, missing, incomplete, expected,
):
    calls = _fixture(monkeypatch, missing=missing, incomplete=incomplete)
    result = _adjudicate(tmp_path)
    assert result.status == expected
    assert result.chain is None
    assert calls == {"replay": [], "snapshot": [], "compare": 0}
    assert tuple(item.case_id for item in result.inventory) == aggregate.CASE_ORDER


@pytest.mark.parametrize("numerical,replay_error,expected", [
    ("Q1_L2", None, "FAILED_NUMERICAL_SCREEN"),
    (None, "Q2_L1", "FAILED_EVIDENCE"),
])
def test_nonpassing_replay_prevents_cross_screen(
    monkeypatch, tmp_path, numerical, replay_error, expected,
):
    calls = _fixture(monkeypatch, numerical=numerical, replay_error=replay_error)
    result = _adjudicate(tmp_path)
    assert result.status == expected
    assert result.chain is None
    assert calls["replay"] == list(aggregate.CASE_ORDER)
    assert calls["snapshot"] == [] and calls["compare"] == 0


def test_valid_cross_comparison_can_remain_unresolved(monkeypatch, tmp_path):
    calls = _fixture(monkeypatch, chain_pass=False)
    result = _adjudicate(tmp_path)
    assert result.status == "UNRESOLVED_LOCAL_REFERENCE"
    assert result.reasons == ("Q1_L0/Q1_L1: scalar root_reaction_x exceeds 1%",)
    assert calls["compare"] == 1


def test_exclusive_aggregate_receipt_binds_complete_pass(monkeypatch, tmp_path):
    calls = _fixture(monkeypatch)
    value, digest = aggregate.adjudicate_and_write(
        tmp_path, registration_sha256=DIGEST,
        budgets=budgets.make_scientific_budgets(),
    )
    assert value.status == "PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN"
    assert value.cross_factorizations == value.cross_solves == 0
    assert value.cross_element_assemblies == value.cross_recoveries == 0
    assert value.comparator_sha256 == DIGEST
    assert aggregate_receipt.read_receipt(tmp_path, DIGEST) == (value, digest)
    assert calls["replay"] == list(aggregate.CASE_ORDER)
    assert aggregate.replay_aggregate(
        tmp_path, registration_sha256=DIGEST,
        budgets=budgets.make_scientific_budgets(),
    ) == (value, digest)
    with pytest.raises(FileExistsError):
        aggregate.adjudicate_and_write(
            tmp_path, registration_sha256=DIGEST,
            budgets=budgets.make_scientific_budgets(),
        )


def test_exclusive_receipt_preserves_missing_case_without_cross_claim(monkeypatch, tmp_path):
    _fixture(monkeypatch, missing="Q1_L2")
    value, digest = aggregate.adjudicate_and_write(
        tmp_path, registration_sha256=DIGEST,
        budgets=budgets.make_scientific_budgets(),
    )
    assert value.status == "FAILED_EVIDENCE"
    assert value.cases[2].status == "FAILED_EVIDENCE"
    assert all(pair.result is None for pair in value.pairs)
    assert all(item.disposition == "NOT_EVALUATED" for item in value.predicates)
    assert aggregate_receipt.read_receipt(tmp_path, DIGEST) == (value, digest)


def test_read_only_aggregate_replay_rejects_changed_cross_result(monkeypatch, tmp_path):
    _fixture(monkeypatch)
    aggregate.adjudicate_and_write(
        tmp_path, registration_sha256=DIGEST,
        budgets=budgets.make_scientific_budgets(),
    )
    pairs = tuple(_pair_result(pair) for pair in arithmetic.PAIR_ORDER)
    pairs = (replace(pairs[0], passed=False,
                     failures=("scalar root_reaction_x exceeds 1%",),
                     scalar_relatives=(0.02, *pairs[0].scalar_relatives[1:])),
             *pairs[1:])
    monkeypatch.setattr(aggregate.cross_bundle, "compare_snapshots",
                        lambda _: arithmetic.compare_chains(pairs))
    with pytest.raises(ValueError, match="disagrees with independent replay"):
        aggregate.replay_aggregate(
            tmp_path, registration_sha256=DIGEST,
            budgets=budgets.make_scientific_budgets(),
        )


def test_source_change_before_exclusive_write_leaves_no_aggregate(monkeypatch, tmp_path):
    _fixture(monkeypatch)
    original = aggregate.registration.read_registration
    calls = [0]

    def source_swap(*args):
        calls[0] += 1
        registered, digest = original(*args)
        if calls[0] == 3:
            return replace_namespace(registered, source_commit="c" * 40), digest
        return registered, digest

    def replace_namespace(value, **changes):
        return SimpleNamespace(**{**vars(value), **changes})

    monkeypatch.setattr(aggregate.registration, "read_registration", source_swap)
    with pytest.raises(ValueError, match="before aggregate receipt write"):
        aggregate.adjudicate_and_write(
            tmp_path, registration_sha256=DIGEST,
            budgets=budgets.make_scientific_budgets(),
        )
    assert not (tmp_path / aggregate_receipt.FILENAME).exists()


def test_case_change_after_adjudication_prevents_exclusive_write(monkeypatch, tmp_path):
    _fixture(monkeypatch, numerical="Q2_L0")
    original = aggregate.cross_snapshot._owned_receipt_digest
    reads = [0]

    def changed(path):
        reads[0] += 1
        if reads[0] > 2 * len(aggregate.CASE_ORDER) and path.name == "Q2_L0":
            return "c" * 64
        return original(path)

    monkeypatch.setattr(aggregate.cross_snapshot, "_owned_receipt_digest", changed)
    with pytest.raises(ValueError, match="case evidence changed"):
        aggregate.adjudicate_and_write(
            tmp_path, registration_sha256=DIGEST,
            budgets=budgets.make_scientific_budgets(),
        )
    assert not (tmp_path / aggregate_receipt.FILENAME).exists()


def test_registration_change_after_sealed_replay_is_rejected(monkeypatch, tmp_path):
    _fixture(monkeypatch)
    aggregate.adjudicate_and_write(
        tmp_path, registration_sha256=DIGEST,
        budgets=budgets.make_scientific_budgets(),
    )
    original = aggregate.registration.read_registration
    calls = [0]

    def source_swap(*args):
        calls[0] += 1
        registered, digest = original(*args)
        if calls[0] == 3:
            return SimpleNamespace(**{**vars(registered),
                                       "source_commit": "c" * 40}), digest
        return registered, digest

    monkeypatch.setattr(aggregate.registration, "read_registration", source_swap)
    with pytest.raises(ValueError, match="after aggregate replay"):
        aggregate.replay_aggregate(
            tmp_path, registration_sha256=DIGEST,
            budgets=budgets.make_scientific_budgets(),
        )
