from types import SimpleNamespace

import pytest

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_bundle as bundle
from scripts import _b3_e4_f03_local_scientific_cross_math as arithmetic
from scripts import _b3_e4_f03_local_scientific_cross_snapshot as retained


def _snapshots():
    return tuple(retained.CaseSnapshot(
        case.case_id, None, "a" * 64, "a" * 64, "a" * 64, "a" * 64,
        "a" * 64, None, None, case.case_id + " saved P",
        case.case_id + " rebuilt P",
    ) for case in cases.CASES)


def test_bundle_uses_only_four_nested_pairs_and_one_gating_cross_pair(monkeypatch):
    snapshots = _snapshots()
    monkeypatch.setattr(retained.CaseSnapshot, "case_data", lambda self: self.case_id)
    calls = []

    def compare(coarse, fine, **kwargs):
        calls.append((coarse, fine, kwargs))
        return SimpleNamespace(pair=(coarse, fine))

    monkeypatch.setattr(arithmetic, "compare_pair", compare)
    monkeypatch.setattr(arithmetic, "compare_chains", lambda pairs: pairs)
    result = bundle.compare_snapshots(snapshots)
    assert tuple(item.pair for item in result) == arithmetic.PAIR_ORDER
    assert len(calls) == 5
    for coarse, fine, kwargs in calls[:4]:
        assert kwargs == {
            "saved_prolongation": fine + " saved P",
            "rederived_prolongation": fine + " rebuilt P",
        }
    assert calls[-1] == ("Q1_L2", "Q2_L1", {})


def test_bundle_rejects_incomplete_or_reordered_inventory():
    snapshots = _snapshots()
    for invalid in (snapshots[:-1], tuple(reversed(snapshots))):
        with pytest.raises(ValueError, match="complete ordered"):
            bundle.compare_snapshots(invalid)
