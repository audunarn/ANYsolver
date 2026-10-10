"""M25 (after the review fixes): one-shot formal lean holdout assessment, opt-in.

Writes milestone evidence once and refuses to overwrite existing evidence
(m25-assessment-01 to -05.json are earlier M25 runs and are preserved). It
is skipped in ordinary test runs; set PREPARED_STATIC_WRITE_EVIDENCE=m25-assessment-06
to run it (M25f, opt-in trusted capture enabled). The same holdouts run repeatably, without writing, in
test_prepared_static_response_m25.py.
"""
import json
import os
from pathlib import Path

import pytest

import prepared_static_response_m16_assessment as assessment

NAME = 'm25-assessment-06'
EVIDENCE = Path(__file__).resolve().parents[1] / '.prepared-static-evidence' / (NAME + '.json')


@pytest.mark.skipif(os.environ.get('PREPARED_STATIC_WRITE_EVIDENCE') != NAME,
                    reason='one-shot milestone evidence; opt in with PREPARED_STATIC_WRITE_EVIDENCE=' + NAME)
def test_m25_review_fix_lean_holdouts_formal_assessment():
    lean = {'selected_reaction_diagnostics': 'lean', 'trusted_capture': True}
    mode = 'certified_vectorized'
    summaries = [assessment.holdout_a1(mode, native_loads=True, route_options=lean),
                 assessment.holdout_a3(mode, native_loads=True, route_options=lean),
                 assessment.holdout_a5(mode, native_loads=True, route_options=lean),
                 assessment.holdout_a4(mode, route_options=lean)]
    go = all(s['failure_count'] == 0 for s in summaries)
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open('x', encoding='utf-8') as handle:
        json.dump({'milestone': 'M25f opt-in trusted capture', 'selected_reaction_diagnostics': 'lean',
                   'holdouts': summaries, 'go': go}, handle, indent=1, default=float)
    for summary in summaries:
        assert summary['failure_count'] == 0, summary
    assert summaries[2]['master_entries_checked'] > 0
