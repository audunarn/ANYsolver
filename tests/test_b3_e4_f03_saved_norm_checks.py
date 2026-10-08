"""Saved signed Green observation binding, without a scientific equilibrium."""
from dataclasses import replace
from fractions import Fraction as F
import copy
import math
import numpy as np
import pytest
from scripts import _b3_e4_f03_saved_norm_checks as check
from scripts import _b3_e4_f03_local_functional as green

Z=F(0);O=F(1)
B=check.NormBudget(128,32_000_000,1_000_000_000,128*1024**2)


def _functional(zero=False):
    rows=(((Z if zero else O,Z,Z,Z,Z,Z),(Z,)*6,(Z,)*6),)
    return green.Functional((Z,O),rows,(Z,Z,Z),((Z,Z,Z),(Z,Z,Z)))


def _functional_all_channels():
    rows=(((O,Z,Z,Z,Z,Z),(O,Z,Z,Z,Z,Z),(O,Z,Z,Z,Z,Z)),)
    return green.Functional((Z,O),rows,(Z,Z,Z),((Z,Z,Z),(Z,Z,Z)))


def _raw(order,*,channels=(1.,0.,0.),total=1.,zero=False):
    zeros=[0.,0.,0.]
    return dict(order=order,squared_norm=total,channels=list(channels),
        diagonal=list(channels),offdiagonal=zeros.copy(),atom_cross=zeros.copy(),
        atom_gram=zeros.copy(),sum_abs_terms=list(channels),
        cancellation_ratio=zeros.copy(),exact_zero=zero,intervals=1,
        channel_finite=[True]*3,channel_nonnegative=[True]*3,channel_nonzero_valid=[True]*3,
        total_finite=True,total_nonnegative=True,admissible=True,failures=())


def _observations(monkeypatch,first,second):
    monkeypatch.setattr(green,'norm_observation_at_order',
                        lambda value,order:copy.deepcopy(first if order==48 else second),
                        raising=False)
    return check._pack((first,second))


def test_bind_all_actual_raw_fields_and_exact_zero():
    for value in (_functional(),_functional(True)):
        raw=tuple(green.norm_observation_at_order(value,order) for order in (48,64))
        saved=check._pack(raw)
        result=check.verify_norm(value,saved,budget=B)
        assert result['status']=='PASSED'
        assert result['saved_bit_parity']
        assert result['diagnostics']['norm_evaluations']==2
        assert result['resolution']<=F.from_float(1e-10)


@pytest.mark.parametrize('field',('channels','totals','components','channel_flags',
                                 'total_flags','exact_zero','failures'))
def test_every_saved_field_is_bound(monkeypatch,field):
    first,second=_raw(48),_raw(64)
    saved=_observations(monkeypatch,first,second)
    if field=='failures':
        bad=replace(saved,failures=((('fake',None,'changed'),),()))
    else:
        changed=getattr(saved,field).copy()
        changed.flat[0]=(not changed.flat[0]) if changed.dtype==np.bool_ else changed.flat[0]+.01
        bad=replace(saved,**{field:changed})
    result=check.verify_norm(_functional(),bad,budget=B)
    assert result['status']=='FAILED' and not result['saved_bit_parity']


def test_negative_channel_with_positive_total_is_retained_and_fails(monkeypatch):
    first,second=_raw(48,channels=(-1.,2.,0.)),_raw(64,channels=(-1.,2.,0.))
    for item in (first,second):
        item['channel_nonnegative'][0]=False;item['admissible']=False
        item['failures']=({'stage':'channel_sum','channel':0,'reason':'negative'},)
    saved=_observations(monkeypatch,first,second)
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['saved_bit_parity'] and result['status']=='FAILED'
    assert result['raw48']['channels'][0]==-1 and result['raw48']['squared_norm']==1
    assert result['resolution']==0


def test_missing_channel_keeps_finite_peers_and_rejects(monkeypatch):
    first,second=_raw(48,channels=(1.,None,0.),total=None),_raw(64,channels=(1.,None,0.),total=None)
    for item in (first,second):
        item['channel_finite'][1]=False;item['total_finite']=False;item['admissible']=False
        item['failures']=({'stage':'density','channel':1,'reason':'overflow'},)
    saved=_observations(monkeypatch,first,second)
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['saved_bit_parity'] and result['status']=='FAILED'
    assert result['raw48']['channels']==(1.,None,0.)
    assert result['resolution'] is None


def test_finite_channels_survive_total_overflow(monkeypatch):
    first,second=_raw(48,channels=(1e308,1e308,0.),total=None),_raw(64,channels=(1e308,1e308,0.),total=None)
    for item in (first,second):
        item['total_finite']=False;item['admissible']=False
        item['failures']=({'stage':'total_sum','channel':None,'reason':'overflow'},)
    saved=_observations(monkeypatch,first,second)
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['status']=='FAILED' and result['saved_bit_parity']
    assert result['raw64']['channels'][:2]==(1e308,1e308)


def test_nonzero_exact_channel_cannot_pass_with_zero_even_if_flags_lie(monkeypatch):
    saved=_observations(monkeypatch,_raw(48,channels=(0.,0.,0.),total=0.),
                        _raw(64,channels=(0.,0.,0.),total=0.))
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['status']=='FAILED' and result['saved_bit_parity']


def test_exact_zero_channel_cannot_pass_with_positive_observation(monkeypatch):
    saved=_observations(monkeypatch,_raw(48,channels=(1.,1.,0.),total=2.),
                        _raw(64,channels=(1.,1.,0.),total=2.))
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['status']=='FAILED' and result['saved_bit_parity']


def test_total_requires_legacy_fsum_of_finite_channels(monkeypatch):
    channels=(1.977708810389016e-156,7.8502843677752e130,1.2194270879481232e131)
    expected=math.fsum(channels)
    assert expected!=sum(channels)
    good=_observations(monkeypatch,_raw(48,channels=channels,total=expected),
                       _raw(64,channels=channels,total=expected))
    result=check.verify_norm(_functional_all_channels(),good,budget=B)
    assert result['status']=='PASSED' and result['saved_bit_parity']
    bad=_observations(monkeypatch,_raw(48,channels=channels,total=sum(channels)),
                      _raw(64,channels=channels,total=sum(channels)))
    result=check.verify_norm(_functional_all_channels(),bad,budget=B)
    assert result['status']=='FAILED' and result['saved_bit_parity']


def test_total_consistency_does_not_hide_programming_errors(monkeypatch):
    saved=_observations(monkeypatch,_raw(48),_raw(64))
    def failure(values):raise RuntimeError('programming failure')
    monkeypatch.setattr(check.math,'fsum',failure)
    with pytest.raises(RuntimeError,match='programming'):
        check.verify_norm(_functional(),saved,budget=B)


def test_resolution_uses_signed_channels_and_floor(monkeypatch):
    saved=_observations(monkeypatch,_raw(48),_raw(64,channels=(1.001,0.,0.),total=1.001))
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['status']=='HOLD_UNRESOLVED'
    assert result['resolution']==abs(F.from_float(1.001)-1)/1_000_000


def test_owned_saved_arrays_and_explicit_nan_storage(monkeypatch):
    saved=_observations(monkeypatch,_raw(48),_raw(64))
    source=saved.channels.copy();owned=replace(saved,channels=source)
    source[:]=22
    assert np.array_equal(owned.channels,[[1.,0.,0.],[1.,0.,0.]])
    with pytest.raises(ValueError):owned.channels.setflags(write=True)
    with pytest.raises(ValueError,match='infinity'):
        replace(saved,totals=np.array([np.inf,1.]))
    with pytest.raises(ValueError,match='array'):
        replace(saved,total_flags=np.ones((2,3),dtype=np.int64))


def test_preflight_and_programming_failure_propagate(monkeypatch):
    saved=_observations(monkeypatch,_raw(48),_raw(64))
    def failure(*args):raise RuntimeError('programming failure')
    monkeypatch.setattr(green,'norm_observation_at_order',failure)
    for name in ('max_integer_bits','max_operations','max_work_bytes'):
        with pytest.raises(ValueError,match='budget'):
            check.verify_norm(_functional(),saved,budget=replace(B,**{name:1}))
    with pytest.raises(RuntimeError,match='programming'):
        check.verify_norm(_functional(),saved,budget=B)


def test_unavailable_contribution_cannot_pass_with_admissible_flags(monkeypatch):
    first,second=_raw(48),_raw(64)
    for item in (first,second):item['atom_cross'][0]=None
    saved=_observations(monkeypatch,first,second)
    result=check.verify_norm(_functional(),saved,budget=B)
    assert result['saved_bit_parity'] and result['status']=='FAILED'


def test_raw_flags_and_interval_metadata_must_be_typed(monkeypatch):
    first,second=_raw(48),_raw(64)
    first['admissible']='true'
    with pytest.raises(ValueError,match='booleans'):check._pack((first,second))
    first=_raw(48);saved=_observations(monkeypatch,first,second)
    first['intervals']=2
    with pytest.raises(ValueError,match='interval identity'):
        check.verify_norm(_functional(),saved,budget=B)


@pytest.mark.parametrize('channels,total',(((1.,0.,0.),1.),((0.,0.,0.),1.)))
def test_exact_zero_requires_zero_channels_and_total(monkeypatch,channels,total):
    saved=_observations(monkeypatch,_raw(48,channels=channels,total=total,zero=True),
                        _raw(64,channels=channels,total=total,zero=True))
    result=check.verify_norm(_functional(True),saved,budget=B)
    assert result['saved_bit_parity'] and result['status']=='FAILED'
