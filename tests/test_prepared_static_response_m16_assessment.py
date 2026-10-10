"""M16 formal holdout assessment (A1-A4) under the frozen criteria; writes evidence JSON."""
import json
import os
from pathlib import Path

import pytest

import prepared_static_response_m16_assessment as assessment

EVIDENCE = Path(__file__).resolve().parents[1] / '.prepared-static-evidence' / 'm16-assessment-01.json'


@pytest.mark.skipif(os.environ.get('PREPARED_STATIC_WRITE_EVIDENCE') != 'm16-assessment-01',
                    reason='one-shot milestone evidence; opt in with PREPARED_STATIC_WRITE_EVIDENCE=m16-assessment-01')
def test_m16_formal_holdout_assessment():
    summaries = [assessment.holdout_a1(), assessment.holdout_a2(), assessment.holdout_a3(), assessment.holdout_a4()]
    criteria = dict(unit_roundoff=assessment.UNIT_ROUNDOFF, tau_linear=assessment.TAU_LINEAR,
                    tau_derived=assessment.TAU_DERIVED, relative=assessment.RELATIVE,
                    displacement_tolerances={'supported': [1e-12, 1e-14], 'free_free': [1e-11, 1e-13]})
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open('x', encoding='utf-8') as handle:
        json.dump({'criteria': criteria, 'holdouts': summaries,
                   'go': all(s['failure_count'] == 0 for s in summaries)}, handle, indent=1, default=float)
    for summary in summaries:
        print('M16 holdout', summary['label'], json.dumps({k: v for k, v in summary.items() if k != 'failures'}, default=float))
    for summary in summaries:
        assert summary['failure_count'] == 0, summary
