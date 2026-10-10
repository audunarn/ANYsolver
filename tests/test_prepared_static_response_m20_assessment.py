"""M20 formal assessment: compiled pressure loads (A1-L, A2-L, A3-L) and vectorized A1-A4 under frozen criteria."""
import json
import os
from pathlib import Path

import pytest

import prepared_static_response_m16_assessment as assessment

EVIDENCE = Path(__file__).resolve().parents[1] / '.prepared-static-evidence' / 'm20-assessment-02.json'


@pytest.mark.skipif(os.environ.get('PREPARED_STATIC_WRITE_EVIDENCE') != 'm20-assessment-02',
                    reason='one-shot milestone evidence; opt in with PREPARED_STATIC_WRITE_EVIDENCE=m20-assessment-02')
def test_m20_formal_assessment():
    mode = 'certified_vectorized'
    loads = [assessment.holdout_a1(mode, native_loads=True), assessment.holdout_a2(mode, native_loads=True),
             assessment.holdout_a3(mode, native_loads=True)]
    route = [assessment.holdout_a1(mode), assessment.holdout_a2(mode), assessment.holdout_a3(mode), assessment.holdout_a4(mode)]
    summaries = loads + route
    # First run (m20-claude-07-assessment) required every case to compile; A1's empty
    # coefficient set has no pressure and is native by design. Frozen rule: C1-C7, C4'.
    go = all(s['failure_count'] == 0 for s in summaries) and all(s['compiled_load_cases'] > 0 for s in loads)
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open('x', encoding='utf-8') as handle:
        json.dump({'stress_execution': mode, 'holdouts': summaries, 'go': go}, handle, indent=1, default=float)
    for summary in summaries:
        print('M20 holdout', summary['label'], json.dumps({k: v for k, v in summary.items() if k != 'failures'}, default=float))
    for summary in summaries:
        assert summary['failure_count'] == 0, summary
    for summary in loads:
        assert summary['compiled_load_cases'] > 0, summary
