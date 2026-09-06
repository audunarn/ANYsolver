"""Coarse arch path correctness, explicitly not a coarse accuracy pass."""

from dataclasses import asdict
import json
from types import SimpleNamespace

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_path_probe as arch
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


@pytest.fixture(scope='module')
def coarse():
    checkpoints = []
    result = arch.run(2,steps=8,progress=checkpoints.append)
    assert tuple(checkpoints)==result.records
    return result


def test_coarse_spatial_arch_traverses_a_load_maximum_but_is_not_accurate(coarse):
    records = coarse.records
    assert len(records)==8 and [r.step for r in records]==list(range(1,9))
    assert all(b.crown_drop>a.crown_drop for a,b in zip(records,records[1:]))
    assert records[0].current_load_slope>0>records[-1].current_load_slope
    assert records[-1].load<max(r.load for r in records)
    assert records[0].minimum_free_eigenvalue>0>records[-1].minimum_free_eigenvalue
    assert max(r.relative_load_error for r in records)>.02
    assert coarse.production_qualified is False


def test_current_slope_is_not_mislabeled_predictor_direction(coarse):
    # A step crosses the turning point. Its old-state predictor may still have
    # positive parameter direction while the accepted-state tangent is negative.
    assert any(r.predictor_parameter_direction>0>r.current_parameter_direction for r in coarse.records)
    for r in coarse.records:
        assert (r.current_parameter_direction>0)==(r.current_load_slope>0)


def test_all_coarse_states_satisfy_physical_and_arc_equilibrium(coarse):
    for r in coarse.records:
        assert r.equilibrium_error<=1e-11 and r.arc_error<=1e-11
        assert r.symmetry_error<=1e-11
        assert r.iterations<=16 and r.mixed_evaluations<=512
    assert coarse.model.committed.epoch==8
    assert digest(coarse.model.replay())==digest(coarse.model._checkpoint[1].response)
    assert all(h.accumulated==0 for hs in coarse.model.committed.histories for h in hs)
    encoded = json.dumps([asdict(r) for r in coarse.records],sort_keys=True,allow_nan=False)
    assert len(json.loads(encoded))==8


def test_zero_deadline_never_evaluates_mechanics(monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError('must not evaluate')
    monkeypatch.setattr(arch.BeamContinuationProbe,'trial',forbidden)
    with pytest.raises(arch.ArchPathError,match='deadline') as caught:
        arch.run(2,max_seconds=0)
    assert caught.value.records==()


@pytest.mark.parametrize('count,options',[(1,{}),(True,{}),(16,{}),(2,{'steps':13}),
                                       (2,{'steps':True}),(2,{'max_seconds':61})])
def test_invalid_extent_rejected(count,options):
    with pytest.raises(ValueError):
        arch.run(count,**options)


def test_injected_failure_preserves_diagnostic_checkpoints_without_partial_result(monkeypatch):
    original = arch.BeamContinuationProbe.trial
    calls = []
    def fail_second(self,*args,**kwargs):
        calls.append(1)
        if len(calls)==2:
            raise RuntimeError('injected second increment failure')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(arch.BeamContinuationProbe,'trial',fail_second)
    with pytest.raises(arch.ArchPathError,match='second increment failure') as caught:
        arch.run(2,steps=2)
    assert len(calls)==2 and len(caught.value.records)==1
    assert caught.value.records[0].step==1
    assert not hasattr(caught.value,'model')


def test_invalid_reference_cannot_produce_a_comparison_record(monkeypatch):
    monkeypatch.setattr(arch,'continuum',lambda *args,**kwargs:SimpleNamespace(load=0.))
    with pytest.raises(arch.ArchPathError,match='reference load') as caught:
        arch.run(2,steps=1)
    assert caught.value.records==() and not hasattr(caught.value,'model')
