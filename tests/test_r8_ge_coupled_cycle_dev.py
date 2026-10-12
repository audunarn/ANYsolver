"""Eight explicit pure source controls and one supervised connected public cycle."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts import r8_ge_coupled_cycle_dev as cycle

def good():
    return dict(equilibrium=1e-10,gap=1e-12,target=0.,amplitude=-.4,
        point_work_max=1e-19,point_count=4,constitutive_valid=True,monotonic=True)

def test_source_exact_path_and_limits():
    assert cycle.PLAN['targets']==[cycle.TARGET/2.,0.,cycle.TARGET/2.,cycle.TARGET]
    assert cycle.PLAN['control']==['shell',2,0] and cycle.PLAN['control_dof']==6
    assert cycle.PLAN['adaptive'] is False and cycle.PLAN['trial_policy'] is None
    assert cycle.PLAN['rejected_probe_from']=='completed-cycle-final' and cycle.PLAN['rejected_probe_target']==cycle.TARGET/2.
    assert cycle.PLAN['primary_accepts']==4 and cycle.PLAN['cold_continuation_accepts']==cycle.PLAN['rebased_continuation_accepts']==2

def test_source_changed_adoption_refused():
    value=dict(status='CYCLE_ADOPTED',plan=copy.deepcopy(cycle.PLAN));cycle.require_adoption(value)
    for key,new in (('targets',[0.,cycle.TARGET]),('max_iterations',21),('chart_invariant_limit',1e-8)):
        bad=copy.deepcopy(value);bad['plan'][key]=new
        with pytest.raises(ValueError):cycle.require_adoption(bad)
    with pytest.raises(ValueError):cycle.require_adoption(dict(status='PROPOSED',plan=cycle.PLAN))

def test_source_binding_drift_refused():
    expected={'a.py':'1','b.py':'2'};cycle.verify_bindings(expected,expected)
    with pytest.raises(ValueError):cycle.verify_bindings(expected,{'a.py':'1','b.py':'3'})
    with pytest.raises(ValueError):cycle.verify_bindings({'a/x.py':'1','b/x.py':'2'},{'a/x.py':'1','b/x.py':'2'})

def test_source_exact_junit_counts(tmp_path):
    path=tmp_path/'junit.xml'
    path.write_text('<testsuites><testsuite tests="8" errors="0" failures="0" skipped="0"/></testsuites>')
    cycle.counts(path,8)
    for total,skipped in ((7,0),(8,1),(0,0)):
        path.write_text(f'<testsuites><testsuite tests="{total}" errors="0" failures="0" skipped="{skipped}"/></testsuites>')
        with pytest.raises(ValueError):cycle.counts(path,8)
    assert len(cycle.SOURCE_NAMES)==8 and len(set(cycle.SOURCE_NAMES))==8
    assert 'test_installed_connected_cycle' not in cycle.SOURCE_NAMES

def test_source_finite_acceptance_and_work_refusal():
    cycle.validate_metrics(good())
    for key,new in (('equilibrium',1e-7),('gap',1e-8),('point_work_max',1e-11),('point_count',3),('amplitude',float('nan')),('constitutive_valid',False)):
        row=good();row[key]=new
        with pytest.raises(ValueError):cycle.validate_metrics(row)
    flags={k:True for k in cycle.ATOMIC_KEYS};cycle.check_atomic(flags)
    refused=[]
    for key in flags:
        changed=dict(flags);changed[key]=False
        with pytest.raises(AssertionError):cycle.check_atomic(changed)
        refused.append(key)
    import os
    if 'GE_CYCLE_OUTPUT' in os.environ:
        cycle.write(Path(os.environ['GE_CYCLE_OUTPUT'])/'atomic-negative-calibration.json',dict(all_flags_checked=True,individually_refused_false_keys=refused))
    physical=dict(shell_translations=[[.1,.2,.3]],support_reactions=[10.,0.,2.],
        **{'point/0/shell_action':[1.,2.,3.,4.,5.,6.],'point/0/beam_action':[-1.,-2.,-3.,-4.,-5.,-6.]})
    cycle.compare_physical_values(physical,copy.deepcopy(physical))
    for key in physical:
        changed=copy.deepcopy(physical)
        if key=='shell_translations':changed[key][0][0]+=1e-5
        else:changed[key][0]+=1e-5
        with pytest.raises(ValueError):cycle.compare_physical_values(physical,changed)
    for key in physical:
        missing=copy.deepcopy(physical);missing.pop(key)
        with pytest.raises(ValueError):cycle.compare_physical_values(physical,missing)
    truncated=copy.deepcopy(physical);truncated['point/0/shell_action'].pop()
    with pytest.raises(ValueError):cycle.compare_physical_values(physical,truncated)
    # Exercise the real parity caller, not only its norm helper.
    point=dict(shell_node_id=2,beam_node_id=103,configuration='current',
        shell_position_m=[0.,0.,0.],beam_position_m=[0.,0.,0.],
        shell_position_low_m=[0.,0.,0.],beam_position_low_m=[0.,0.,0.],
        shell_action=[0.]*6,beam_action=[0.]*6,gap=[0.]*6)
    snapshot=SimpleNamespace(shell_frames=[[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]],
        beam_positions=[[0.,0.,0.]],beam_frames=[],cell_frames=[],cell_resultants=[],
        multipliers=[0.]*24,applied_dead_load=[0.]*6,support_reactions=[0.]*6,
        shell_displacement=[.1,.2,.3,0.,0.,0.],
        point_wrenches=[dict(point,point_index=i) for i in range(4)])
    equivalent=copy.deepcopy(snapshot);equivalent.shell_displacement[3:]=[.4,.5,.6]
    cycle.parity(snapshot,equivalent)  # raw chart rotations are intentionally absent
    for role in ('shell_translation','support','shell_point_action','beam_point_action'):
        changed=copy.deepcopy(snapshot)
        if role=='shell_translation':changed.shell_displacement[0]+=1e-5
        elif role=='support':changed.support_reactions[3]+=1e-5
        else:changed.point_wrenches[0]['shell_action' if role=='shell_point_action' else 'beam_action'][3]+=1e-5
        with pytest.raises(ValueError):cycle.parity(snapshot,changed)
    missing=copy.deepcopy(snapshot);missing.point_wrenches.pop()
    with pytest.raises(ValueError):cycle.parity(snapshot,missing)

def test_source_pair_monotonicity():
    a={'fibre':cycle.pair([1.,-1e-18]),'shell':cycle.pair([0.,0.])}
    b={'fibre':cycle.pair([1.,0.]),'shell':cycle.pair([1e-12,0.])}
    cycle.monotone(a,b)
    with pytest.raises(ValueError):cycle.monotone(b,a)
    with pytest.raises(ValueError):cycle.monotone(a,{'fibre':b['fibre']})
    for bad in ([1.],[1.,0.,0.],[float('nan'),0.]):
        with pytest.raises(ValueError):cycle.pair(bad)

def test_source_physical_reversal_reporting():
    assert cycle.reversal([{'fibre0':1,'fibre1':0},{'fibre0':-1,'fibre1':-1}])==['fibre0']
    assert cycle.reversal([{'fibre0':0},{'fibre0':-1}])==[]

def test_source_production_public_sequence(tmp_path):
    class FakeOwner:
        def __init__(self,fail_at=None):self.calls=[];self.fail_at=fail_at;self.history=[]
        def solve(self,loads,targets,**kwargs):
            assert loads=='actual-loads' and kwargs['displacement_control']=='actual-control'
            assert kwargs['max_iterations']==20 and kwargs['max_backtracks']==8
            self.calls.append(targets)
            if len(self.calls)==self.fail_at:raise RuntimeError('actual caller failure')
            self.history.append(targets[0]);result=SimpleNamespace(target=targets[0],generation=len(self.history))
            kwargs['on_accepted'](copy.deepcopy(result));return result
    saved=[]
    def writer(owner,index,result):
        saved.append((index,result.target));(tmp_path/(str(index)+'.json')).write_text(json.dumps(owner.history))
    owner=FakeOwner();returned=cycle.execute_targets(owner,'actual-loads','actual-control',cycle.PLAN['targets'],writer)
    assert returned is owner and owner.history==cycle.PLAN['targets'] and len(saved)==4
    resumed=FakeOwner();resumed.history=owner.history[:2]
    cycle.execute_targets(resumed,'actual-loads','actual-control',cycle.PLAN['targets'][2:],writer,offset=2)
    assert resumed.history==owner.history
    failed=FakeOwner(fail_at=2)
    with pytest.raises(RuntimeError):cycle.execute_targets(failed,'actual-loads','actual-control',cycle.PLAN['targets'],writer)
    assert failed.history==cycle.PLAN['targets'][:1] and len(failed.calls)==2

def test_installed_connected_cycle():
    import os
    if 'GE_CYCLE_OUTPUT' not in os.environ:pytest.skip('GE_CYCLE_OUTPUT supervised installed-cycle binding absent')
    cycle.connected(Path(os.environ['GE_CYCLE_OUTPUT']))
