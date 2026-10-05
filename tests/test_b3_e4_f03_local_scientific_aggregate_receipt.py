"""Synthetic, solve-free tests for the exclusive F03 aggregate receipt."""
from __future__ import annotations

from dataclasses import replace
import json
import os

import pytest

from scripts import _b3_e4_f03_local_scientific_aggregate_receipt as aggregate
from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_case_receipt as case_receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_math as cross_math
from scripts import _b3_e4_f03_local_scientific_registration as registration


def _digest(char: str) -> str:
    return char * 64


def _sources() -> tuple[registration.SourceIdentity, ...]:
    return tuple(registration.SourceIdentity(role, path, 1, _digest("a"))
                 for role, path in registration.SOURCE_ROLES)


def _case_records() -> tuple[aggregate.CaseRecord, ...]:
    nested_targets = {fine for _, fine in cross_math.NESTED_PAIRS}
    return tuple(aggregate.CaseRecord(
        case.case_id, _digest("b"), _digest("c"),
        "PASSED_CASE_NUMERICAL_SCREEN", _digest("d"), _digest("e"), _digest("f"),
        _digest("1") if case.case_id in nested_targets else None,
    ) for case in cases.CASES)


def _pair_result(pair: tuple[str, str]) -> cross_math.PairResult:
    nested = pair in cross_math.NESTED_PAIRS
    return cross_math.PairResult(
        pair, nested, True, (),
        (0.0,) * len(case_receipt.SETTLING_NAMES),
        (0.0,) * len(case_receipt.SETTLING_NAMES),
        1.0, 1.0, 0.0, 0.0, 0.0,
        0.0 if nested else None, 0.0 if nested else None,
        tuple((name, 0.0) for name in aggregate._COMPATIBILITY_NAMES) if nested else (),
        (("union_intervals", 1), ("input_integer_bits", 1),
         ("operations_estimate", 1), ("workspace_estimate_bytes", 1)),
    )


def _receipt(*, case_items=None, pair_results=None) -> aggregate.AggregateReceipt:
    if case_items is None:
        case_items = _case_records()
    if pair_results is None:
        pair_results = tuple(_pair_result(pair) for pair in cross_math.PAIR_ORDER)
    pairs = tuple(aggregate.PairRecord(pair, result)
                  for pair, result in zip(cross_math.PAIR_ORDER, pair_results))
    if any(item.status != "PASSED_CASE_NUMERICAL_SCREEN" for item in case_items):
        status = "FAILED_EVIDENCE" if any(item.status in ("MISSING", "FAILED_EVIDENCE")
                                       for item in case_items) else "FAILED_NUMERICAL_SCREEN"
        reasons = tuple(f"{item.case_id}: {item.status}" +
                        (f": {item.reason}" if item.reason is not None else "")
                        for item in case_items
                        if item.status not in ("PASSED_CASE_NUMERICAL_SCREEN",
                                               "READY_FOR_REPLAY"))
    elif all(result is None for result in pair_results):
        status, reasons = "FAILED_EVIDENCE", ("aggregate snapshot identity mismatch",)
    else:
        chain = cross_math.compare_chains(pair_results)
        status = ("PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN" if chain.passed
                  else "UNRESOLVED_LOCAL_REFERENCE")
        reasons = chain.failures
    if all(result is not None for result in pair_results):
        chain = cross_math.compare_chains(pair_results)
        predicates = tuple(aggregate.PredicateRecord(
            name, "PASSED" if result.passed else "FAILED", result.failures,
        ) for name, result in zip(aggregate.PREDICATE_NAMES[:-1], pair_results)) + (
            aggregate.PredicateRecord("chain", "PASSED" if chain.passed else "FAILED",
                                      chain.failures),
        )
    else:
        predicates = tuple(aggregate.PredicateRecord(name, "NOT_EVALUATED", ())
                           for name in aggregate.PREDICATE_NAMES)
    return aggregate.AggregateReceipt(
        aggregate.SCHEMA, "1" * 40, _digest("2"), _digest("a"), _sources(),
        registration.process_contract(), registration.resource_contract(),
        registration.tolerance_contract(), case_items, pairs, predicates,
        status, reasons, 0, 0, 0, 0,
    )


def test_exclusive_canonical_round_trip(tmp_path):
    value = _receipt()
    digest = aggregate.write_receipt(tmp_path, value)
    observed, observed_digest = aggregate.read_receipt(tmp_path, _digest("2"))
    assert observed == value
    assert observed_digest == digest
    assert (tmp_path / aggregate.FILENAME).stat().st_size < aggregate.MAX_BYTES
    with pytest.raises(FileExistsError):
        aggregate.write_receipt(tmp_path, value)
    with pytest.raises(ValueError, match="registration"):
        aggregate.read_receipt(tmp_path, _digest("3"))


def test_large_legitimate_failed_compatibility_inventory_round_trips(tmp_path):
    pairs = list(_pair_result(pair) for pair in cross_math.PAIR_ORDER)
    pairs[0] = replace(pairs[0], passed=False,
                       failures=tuple(f"compatibility channel {index} failed"
                                      for index in range(150)))
    value = _receipt(pair_results=tuple(pairs))
    assert value.status == "UNRESOLVED_LOCAL_REFERENCE"
    assert len(value.reasons) > 128
    digest = aggregate.write_receipt(tmp_path, value)
    assert aggregate.read_receipt(tmp_path, _digest("2")) == (value, digest)


def test_reader_rejects_replacement_between_stat_and_open(monkeypatch, tmp_path):
    value = _receipt()
    aggregate.write_receipt(tmp_path, value)
    path = tmp_path / aggregate.FILENAME
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(path.read_bytes())
    original = aggregate.evidence._open_no_follow

    def replaced(target):
        os.replace(replacement, target)
        return original(target)

    monkeypatch.setattr(aggregate.evidence, "_open_no_follow", replaced)
    with pytest.raises(ValueError, match="changed before read"):
        aggregate.read_receipt(tmp_path, _digest("2"))


def test_coarsest_case_cannot_claim_exact_prolongation():
    value = _receipt()
    changed = (replace(value.cases[0], exact_prolongation_sha256=_digest("3")),
               *value.cases[1:])
    with pytest.raises(ValueError, match="coarsest"):
        replace(value, cases=changed)


def test_missing_or_failed_case_prevents_cross_comparison():
    cases_with_missing = (replace(_case_records()[0], case_receipt_sha256=None,
                                  status="MISSING", reason="sealed receipt absent"),
                          *(replace(item, status="READY_FOR_REPLAY")
                            for item in _case_records()[1:]))
    value = _receipt(case_items=cases_with_missing, pair_results=(None,) * 5)
    assert value.status == "FAILED_EVIDENCE"
    assert "sealed receipt absent" in value.reasons[0]
    assert len(value.reasons) == 1
    assert all(item.disposition == "NOT_EVALUATED" for item in value.predicates)
    with pytest.raises(ValueError, match="partial F03 cross-case"):
        _receipt(case_items=cases_with_missing)


def test_completed_replays_with_aggregate_evidence_failure(tmp_path):
    value = _receipt(pair_results=(None,) * 5)
    assert value.status == "FAILED_EVIDENCE"
    assert all(item.disposition == "NOT_EVALUATED" for item in value.predicates)
    aggregate.write_receipt(tmp_path, value)
    assert aggregate.read_receipt(tmp_path, _digest("2"))[0] == value
    with pytest.raises(ValueError, match="cross-case result or evidence failure"):
        replace(value, status="UNRESOLVED_LOCAL_REFERENCE")


def test_failed_cross_case_is_unresolved_and_preserves_failure(tmp_path):
    results = list(_pair_result(pair) for pair in cross_math.PAIR_ORDER)
    failed = results[0]
    results[0] = replace(failed, passed=False, failures=("scalar root_reaction_x exceeds 1%",),
                         scalar_relatives=(0.02, *failed.scalar_relatives[1:]))
    value = _receipt(pair_results=tuple(results))
    assert value.status == "UNRESOLVED_LOCAL_REFERENCE"
    assert value.predicates[0].disposition == "FAILED"
    aggregate.write_receipt(tmp_path, value)
    assert aggregate.read_receipt(tmp_path, _digest("2"))[0] == value


def test_reject_incomplete_pass_and_nonzero_cross_work():
    value = _receipt()
    with pytest.raises(ValueError, match="partial F03 cross-case"):
        replace(value, pairs=tuple(aggregate.PairRecord(pair, None)
                                   if index == 0 else record
                                   for index, (pair, record) in enumerate(
                                       zip(cross_math.PAIR_ORDER, value.pairs))))
    with pytest.raises(ValueError, match="inventory"):
        replace(value, cross_solves=1)
    with pytest.raises(ValueError, match="observations"):
        aggregate.PairRecord(cross_math.PAIR_ORDER[0],
                             replace(value.pairs[0].result, functional_difference_norm=None))
    with pytest.raises(ValueError, match="prolongation hash"):
        replace(value, cases=tuple(replace(item, exact_prolongation_sha256=None)
                                   if item.case_id == "Q1_L1" else item
                                   for item in value.cases))
    with pytest.raises(ValueError, match="case record"):
        replace(value.cases[0], evidence_index_sha256=None)
    with pytest.raises(ValueError, match="inventory"):
        replace(value, comparator_sha256=_digest("b"))


def test_passing_pair_cannot_hide_failed_ritz_or_signed_functional():
    pair = _pair_result(cross_math.PAIR_ORDER[0])
    with pytest.raises(ValueError, match="observations"):
        aggregate.PairRecord(pair.pair,
                             replace(pair, energy_defect_relative=2 * cross_math.ENERGY_LIMIT))
    with pytest.raises(ValueError, match="observations"):
        aggregate.PairRecord(pair.pair,
                             replace(pair, functional_relative=2 * cross_math.FUNCTIONAL_LIMIT))
    bad_compatibility = list(pair.compatibility)
    bad_compatibility[0] = (bad_compatibility[0][0], 2 * cross_math.INTEGRATION_LIMIT)
    with pytest.raises(ValueError, match="observations"):
        aggregate.PairRecord(pair.pair, replace(pair, compatibility=tuple(bad_compatibility)))


def test_reader_rejects_noncanonical_and_oversize(tmp_path):
    value = _receipt()
    aggregate.write_receipt(tmp_path, value)
    path = tmp_path / aggregate.FILENAME
    raw = json.loads(path.read_text("ascii"))
    raw["cross_factorizations"] = 1
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", "ascii")
    with pytest.raises(ValueError):
        aggregate.read_receipt(tmp_path, _digest("2"))
    path.write_bytes(b" " * (aggregate.MAX_BYTES + 1))
    with pytest.raises(ValueError, match="bounded"):
        aggregate.read_receipt(tmp_path, _digest("2"))


def test_reader_rejects_hard_link(tmp_path):
    aggregate.write_receipt(tmp_path, _receipt())
    path = tmp_path / aggregate.FILENAME
    link = tmp_path / "other.json"
    try:
        os.link(path, link)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")
    with pytest.raises(ValueError, match="owned"):
        aggregate.read_receipt(tmp_path, _digest("2"))


def test_reader_rejects_symlink(tmp_path):
    path = tmp_path / aggregate.FILENAME
    link = tmp_path / "other.json"
    link.write_bytes(aggregate._payload(_receipt()))
    try:
        os.symlink(link, path)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(ValueError, match="owned"):
        aggregate.read_receipt(tmp_path, _digest("2"))
