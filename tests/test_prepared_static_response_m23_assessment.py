"""M23 formal assessment: A1-A4, A1-L..A3-L and the MPC holdout A5-L under C1-C8 (frozen)."""
import json
import os
from pathlib import Path

import pytest

import prepared_static_response_m16_assessment as assessment

EVIDENCE = Path(__file__).resolve().parents[1] / '.prepared-static-evidence' / 'm23-assessment-01.json'


@pytest.mark.skipif(os.environ.get('PREPARED_STATIC_WRITE_EVIDENCE') != 'm23-assessment-01',
                    reason='one-shot milestone evidence; opt in with PREPARED_STATIC_WRITE_EVIDENCE=m23-assessment-01')
def test_m23_formal_assessment():
    mode = 'certified_vectorized'
    summaries = [assessment.holdout_a1(mode, native_loads=True), assessment.holdout_a2(mode, native_loads=True),
                 assessment.holdout_a3(mode, native_loads=True), assessment.holdout_a5(mode, native_loads=True),
                 assessment.holdout_a1(mode), assessment.holdout_a2(mode), assessment.holdout_a3(mode),
                 assessment.holdout_a4(mode)]
    go = all(s['failure_count'] == 0 for s in summaries)
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open('x', encoding='utf-8') as handle:
        json.dump({'stress_execution': mode, 'holdouts': summaries, 'go': go}, handle, indent=1, default=float)
    for summary in summaries:
        print('M23 holdout', summary['label'], json.dumps({k: v for k, v in summary.items() if k != 'failures'}, default=float))
    for summary in summaries:
        assert summary['failure_count'] == 0, summary
    a5 = summaries[3]
    assert a5['master_entries_checked'] > 0 and a5['compiled_load_cases'] > 0 and a5['node_envelope_entries'] > 0
