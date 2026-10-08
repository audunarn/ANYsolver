"""Connect five retained F03 snapshots to the frozen cross-case arithmetic."""
from __future__ import annotations

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_math as arithmetic
from scripts import _b3_e4_f03_local_scientific_cross_snapshot as retained


def compare_snapshots(
    snapshots: tuple[retained.CaseSnapshot, ...],
) -> arithmetic.ChainResult:
    expected = tuple(case.case_id for case in cases.CASES)
    if (
        type(snapshots) is not tuple
        or len(snapshots) != len(expected)
        or any(type(item) is not retained.CaseSnapshot for item in snapshots)
        or tuple(item.case_id for item in snapshots) != expected
    ):
        raise ValueError("complete ordered replayed F03 snapshots required")
    observations = {item.case_id: item.case_data() for item in snapshots}
    by_case = {item.case_id: item for item in snapshots}
    results = []
    for coarse_id, fine_id in arithmetic.PAIR_ORDER:
        fine = by_case[fine_id]
        if (coarse_id, fine_id) in arithmetic.NESTED_PAIRS:
            result = arithmetic.compare_pair(
                observations[coarse_id], observations[fine_id],
                saved_prolongation=fine.prolongation,
                rederived_prolongation=fine.rederived_prolongation,
            )
        else:
            result = arithmetic.compare_pair(
                observations[coarse_id], observations[fine_id],
            )
        results.append(result)
    return arithmetic.compare_chains(tuple(results))
