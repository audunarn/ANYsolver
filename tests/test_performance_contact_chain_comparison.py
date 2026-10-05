"""Explicit development timing comparison; not scientific qualification.

Set ANYSOLVER_RUN_CONTACT_CHAIN_BENCHMARK=1 to run the preserved balanced
protocol. CONTACT_APP_RESULT_RECORD optionally selects its JSON output path.
"""
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

import numpy as np
import pytest

from test_general_contact_beam_chain_consistent import (
    _assert_displacement_route_mechanics, _solve_displacement_route_comparison,
)


@pytest.mark.skipif(
    os.environ.get('ANYSOLVER_RUN_CONTACT_CHAIN_BENCHMARK') != '1',
    reason='explicit contact-chain development benchmark opt-in required',
)
def test_balanced_displacement_route_timing_comparison():
    rows=[]; solutions=[]
    # One import/cache warm-up per selection precedes three balanced pairs.
    for tag in ('finite_difference','consistent_dev'):
        warm=_solve_displacement_route_comparison(tag)
        assert warm.status=='completed',warm.failure_reason
    for pair,order in enumerate((('consistent_dev','finite_difference'),
                                 ('finite_difference','consistent_dev'),
                                 ('consistent_dev','finite_difference'))):
        values={}
        for tag in order:
            started=time.perf_counter()
            result=_solve_displacement_route_comparison(tag)
            elapsed=time.perf_counter()-started
            assert result.status=='completed',result.failure_reason
            values[tag]=result
            rows.append({'pair':pair,'selection':tag,'elapsed_s':elapsed,
                'contact':result.info['general_contact'],'solver_info':result.info})
        old,new=(values[tag] for tag in ('finite_difference','consistent_dev'))
        _assert_displacement_route_mechanics(old,new)
        solutions.append(float(np.linalg.norm(new.displacements-old.displacements)))
    times={tag:[r['elapsed_s'] for r in rows if r['selection']==tag]
           for tag in ('finite_difference','consistent_dev')}
    median={tag:float(np.median(values)) for tag,values in times.items()}
    evidence={'scope':'guided four-step displacement-controlled B2 two-chain development comparison; not universal speed qualification',
        'times_s':times,'median_s':median,'speed_ratio':median['finite_difference']/median['consistent_dev'],
        'displacement_difference_norm_m':solutions,'rows':rows}
    record=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if record:
        Path(record).write_text(json.dumps(evidence,indent=2,default=lambda x:np.asarray(x).tolist()),encoding='utf8')


def test_balanced_timing_protocol_without_numerical_solves(monkeypatch,tmp_path):
    calls=[]; results=[]

    def solve(tag):
        calls.append(tag)
        result=SimpleNamespace(status='completed',failure_reason=None,
            displacements=np.array([.008]),
            info={'general_contact':{'beam_a_force':np.array([1.])}})
        results.append(result)
        return result

    monkeypatch.setitem(test_balanced_displacement_route_timing_comparison.__globals__,
        '_solve_displacement_route_comparison',solve)
    ticks=iter(range(12))
    monkeypatch.setitem(test_balanced_displacement_route_timing_comparison.__globals__,
        'time',SimpleNamespace(perf_counter=lambda:next(ticks)))
    record=tmp_path/'comparison.json'
    monkeypatch.setenv('CONTACT_APP_RESULT_RECORD',str(record))
    test_balanced_displacement_route_timing_comparison()
    assert calls==['finite_difference','consistent_dev',
        'consistent_dev','finite_difference','finite_difference','consistent_dev',
        'consistent_dev','finite_difference']
    assert len({id(result) for result in results})==8
    evidence=json.loads(record.read_text())
    assert [row['pair'] for row in evidence['rows']]==[0,0,1,1,2,2]
    assert [row['selection'] for row in evidence['rows']]==calls[2:]
    assert evidence['times_s']=={'finite_difference':[1.,1.,1.],'consistent_dev':[1.,1.,1.]}
    assert evidence['median_s']=={'finite_difference':1.,'consistent_dev':1.}
    assert evidence['speed_ratio']==1.
    assert evidence['displacement_difference_norm_m']==[0.,0.,0.]
