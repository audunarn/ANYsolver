"""M17 formal holdout assessment (A1-A4) of the vectorized route under the frozen M16 criteria."""
import json
from pathlib import Path

import prepared_static_response_m16_assessment as assessment

EVIDENCE = Path(__file__).resolve().parents[1] / '.prepared-static-evidence' / 'm17-assessment-01.json'


def test_m17_formal_holdout_assessment():
    mode = 'certified_vectorized'
    summaries = [assessment.holdout_a1(mode), assessment.holdout_a2(mode), assessment.holdout_a3(mode), assessment.holdout_a4(mode)]
    with EVIDENCE.open('x', encoding='utf-8') as handle:
        json.dump({'stress_execution': mode, 'holdouts': summaries,
                   'go': all(s['failure_count'] == 0 for s in summaries)}, handle, indent=1, default=float)
    for summary in summaries:
        print('M17 holdout', summary['label'], json.dumps({k: v for k, v in summary.items() if k != 'failures'}, default=float))
    for summary in summaries:
        assert summary['failure_count'] == 0, summary
