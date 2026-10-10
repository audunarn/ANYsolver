"""Eight supervised stdlib controls and one held installed saved-state discriminator."""
import ast,copy,json,os
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from scripts import r8_ge_paired_trial_derivative_dev as d
SOURCE=pytest.mark.skipif(os.environ.get('GE_TRIAL_DERIVATIVE_STAGE')!='source-controls',reason='fresh supervised source stage required')
INSTALLED=pytest.mark.skipif(os.environ.get('GE_TRIAL_DERIVATIVE_STAGE')!='installed-derivative',reason='sole fresh installed stage required')
@SOURCE
def test_source_input_identity():
    value=d.input_data()
    assert value['evaluation']['evaluation']==14 and value['solve']['solve']==5
    assert d.sha(d.INPUT)==json.loads((d.DOC/'DERIVATIVE_INPUT_IDENTITY.json').read_text())['sha256']
    assert value['evaluation']['value']==-0.4221978243592915
    inner,_,fixed=d.saved.select_inner(d.saved.OUTER.read_bytes())
    assert inner==d.saved.INNER.read_bytes() and fixed['generation']==11
@SOURCE
def test_source_complete_direction():
    value=d.input_data();step=value['solve']['full_correction']
    assert len(step)==132 and any(step[:24]) and any(step[24:60]) and any(step[60:108]) and any(step[108:])
    assert value['solve']['amplitude_delta']==5.834498331439366
    assert d.PLAN['direction_scale']==1.
@SOURCE
def test_source_work_weight_formula():
    assert d.work_weights([2.,4.],[5.,10.],2.)==[1.,2.,.2,.1]
    with pytest.raises(ValueError):d.work_weights([2.],[0.],1.)
    with pytest.raises(ValueError):d.work_weights([2.],[1.],0.)
    assert d.cancellation_ratio(10.,2.)==5.
    assert d.cancellation_ratio(10.,0.) is None
    assert d.cancellation_ratio(10.,1e-30)>1e30
@SOURCE
def test_source_centered_step_pair():
    calls=[]
    driver=NS(_advance=lambda state,direction,amount:calls.append((state,direction,amount)) or amount)
    state=object();direction=object()
    assert d.step_pair(driver,state,direction,1e-5)==(1e-5,-1e-5)
    assert calls==[(state,direction,1e-5),(state,direction,-1e-5)]
    with pytest.raises(ValueError):d.step_pair(driver,state,direction,1e-7)
@SOURCE
def test_source_override_failure_restore(tmp_path):
    observer=NS(applied='accepted');calls=[]
    def evaluate(label,state):
        calls.append((label,state,observer.applied))
        if label=='cancel':raise RuntimeError('cancelled')
        return 17
    observer.evaluate=evaluate
    assert d.evaluate_at(observer,'base','scratch',3.,10.,2.)==17
    assert observer.applied=='accepted' and calls[0]==('base','scratch',16.)
    with pytest.raises(RuntimeError,match='cancelled'):d.evaluate_at(observer,'cancel','scratch',4.,10.,2.)
    assert observer.applied=='accepted' and calls[-1][2]==18.
    flags={str(i):True for i in range(21)};owner=object()
    atomic=NS(capture=lambda x:owner,atomic_flags=lambda x,before:flags,
              checked=lambda values:d.require_replay(values))
    assert d.evaluate_atomic(observer,owner,atomic,'caller','scratch',3.,10.,2.,tmp_path)==17
    assert json.loads((tmp_path/'caller-atomic.json').read_text())==flags
    with pytest.raises(RuntimeError,match='cancelled'):
        d.evaluate_atomic(observer,owner,atomic,'cancel','scratch',4.,10.,2.,tmp_path)
    assert json.loads((tmp_path/'cancel-atomic.json').read_text())==flags
    flags['0']=False
    with pytest.raises(ValueError,match='replay mismatch'):
        d.evaluate_atomic(observer,owner,atomic,'mutation','scratch',3.,10.,2.,tmp_path)
    assert json.loads((tmp_path/'mutation-atomic.json').read_text())['0'] is False
@SOURCE
def test_source_actual_branch_refusal():
    from scripts import r8_f06_paired_active_tangent_dev as old
    marker=dict(active=[True],hardening_segment=[2],hardening_knot=[False],flow_sign=[[1,0,-1]])
    base=[marker];cross=copy.deepcopy(base);cross[0]['flow_sign']=[[0,1,-1]]
    assert d.require_branches(old,base,cross,base)
    for key,value in (('active',[False]),('hardening_segment',[1]),('hardening_knot',[True])):
        changed=copy.deepcopy(base);changed[0][key]=value
        assert not d.require_branches(old,base,changed,base)
    fibre=[[dict(station=0,fibre='0',branch='PLASTIC_POSITIVE',active=True,hardening_segment=1,flow_sign=1,hardening_knot=False)]]
    changed=copy.deepcopy(fibre);changed[0][0].update(branch='PLASTIC_NEGATIVE',flow_sign=-1)
    assert not d.require_branches(old,fibre,changed,fibre)
@SOURCE
def test_source_inventory_and_no_new_solver():
    tree=ast.parse(Path(d.__file__).read_text());names={node.name for node in ast.parse(Path(__file__).read_text()).body if isinstance(node,ast.FunctionDef)}
    assert len(d.SOURCE_NAMES)==8 and set(d.SOURCE_NAMES)<=names
    assert 'test_installed_actual_update_direction' not in d.SOURCE_NAMES
    connected=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='connected')
    assert not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in ('solve','spsolve') for node in ast.walk(connected))
    body=ast.get_source_segment(Path(d.__file__).read_text(),connected)
    assert 'observer.shell=driver._shell_origins;observer.beam=driver._beam_origins' in body
    assert 'base[0][1]@direction-external*delta' in body and 'work_relative' in body
    assert 'abs(base[0][1])@abs(direction)+abs(external*delta)' in body
    assert 'scattered-external_error' in body and 'error-local_predicted_assembled_error' in body
    assert 'UNRESOLVED_DIRECTIONAL_CRITERION' in body
@SOURCE
def test_source_replay_refusal():
    d.require_replay(dict(residual=True,tangent=True,native_origins=True))
    for flags in ({},dict(residual=False,tangent=True),dict(residual=1,tangent=True)):
        with pytest.raises(ValueError,match='replay mismatch'):d.require_replay(flags)
@INSTALLED
def test_installed_actual_update_direction():
    d.connected(Path(os.environ['GE_TRIAL_DERIVATIVE_OUTPUT']))
