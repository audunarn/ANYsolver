"""Prepared independent axial-deformation/support reference; UNEXECUTED."""
from hashlib import sha256
import json
import os
from pathlib import Path
import numpy as np
import pytest
from examples import native_connected_deformation_reference as ref
from examples.native_connected_deformation_dev import run


def _save_result(tag,result):
    """Optional fixed-name raw evidence; ordinary pytest needs no environment."""
    allowed={'response2','response4','work2','split2_full','split2_prefix','split2_resumed',
             'split4_full','split4_prefix','split4_resumed'}
    assert tag in allowed
    destination=os.environ.get('NATIVE_TRANSIENT_RESULT_RECORD')
    if not destination:return
    base=Path(destination);base.parent.mkdir(parents=True,exist_ok=True)
    capsule=base.with_name(base.stem+'_'+tag+'.checkpoint')
    capsule.write_bytes(result.checkpoint)
    report=base.with_name(base.stem+'_'+tag+'.json')
    report.write_text(json.dumps(dict(result=result.to_dict(),
        checkpoint_sha256=sha256(result.checkpoint).hexdigest(),checkpoint_path=str(capsule)),
        sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def _axial(record):
    state=record['state']
    positions=np.asarray(state['positions'])+np.asarray(state['position_low'])
    baseline=ref.ORIGIN+np.arange(5)[:,None]*ref.ELL*ref.DIRECTION
    q=(positions-baseline)@ref.DIRECTION
    v=np.asarray(state['velocity'])[:30].reshape(5,6)[:,:3]@ref.DIRECTION
    a=np.asarray(state['acceleration'])[:30].reshape(5,6)[:,:3]@ref.DIRECTION
    return q,v,a


def _account_error(actual,expected):
    errors={}
    for name in ('elastic_energy','kinetic_energy','total_energy'):
        errors[name]=abs(actual[name]-expected[name])/ref.ENERGY_SCALE
    for name,scale in (('linear_momentum',ref.FORCE_SCALE*ref.DT),('angular_momentum',ref.MOMENT_SCALE*ref.DT)):
        value=np.asarray(actual[name])+np.asarray(actual[name+'_low'])
        errors[name]=float(np.max(np.abs(value-expected[name])))/scale
    return errors


@pytest.mark.parametrize('steps',[2,4])
def test_public_axial_deformation_endpoint_stage_support_and_analytic_reference(steps):
    owner,result=run(steps);_save_result('response'+str(steps),result)
    data=result.to_dict();q,v=ref.initial()
    initial=ref.account(q,v)
    assert result.success and data['accepted_steps']==steps
    assert ref.ENERGY_SCALE==pytest.approx(initial['elastic_energy'],rel=1.e-14)
    assert np.max(np.abs(np.diff(q)))>0.  # Genuine physical strain, not rigid motion.
    iq,iv,ia=_axial(data['initial']);initial_a=ref.endpoint_acceleration(q)
    assert np.max(np.abs(iq-q))/ref.AMPLITUDE<=1.e-6
    assert np.max(np.abs(iv-v))/ref.VELOCITY_SCALE<=1.e-6
    assert np.max(np.abs(ia-initial_a))/ref.ACCELERATION_SCALE<=1.e-6
    initial_acceleration=np.asarray(data['initial']['state']['acceleration'])
    assert np.max(np.abs(initial_acceleration[:30].reshape(5,6)[:,:3]-initial_a[:,None]*ref.DIRECTION))/ref.ACCELERATION_SCALE<=1.e-6
    initial_rotation=[6*i+3+a for i in range(5) for a in range(3)]+list(range(30,42))
    assert np.max(np.abs(initial_acceleration[initial_rotation]))/(ref.ACCELERATION_SCALE/ref.ELL)<=1.e-6
    assert max(_account_error(data['initial']['accounting'],initial).values())<=1.e-6
    observed_force=[];observed_moment=[];worst_energy=0.
    for row in data['steps']:
        expected=ref.step(q,v,row['dt']);actualq,actualv,actuala=_axial(row['endpoint'])
        assert np.max(np.abs(actualq-expected['q']))/ref.AMPLITUDE<=1.e-6
        assert np.max(np.abs(actualv-expected['v']))/ref.VELOCITY_SCALE<=1.e-6
        assert np.max(np.abs(actuala-expected['a']))/ref.ACCELERATION_SCALE<=1.e-6
        mass,stiffness=ref.operators()
        endpoint_root=(mass@expected['a']+stiffness@expected['q'])[0]*ref.DIRECTION
        endpoint_reaction=np.asarray(row['endpoint_reaction_global'])
        assert np.max(np.abs(endpoint_reaction[:3]-endpoint_root))/ref.FORCE_SCALE<=1.e-6
        assert np.max(np.abs(endpoint_reaction[3:6]))/ref.MOMENT_SCALE<=1.e-6
        stageq,stagev,stagea=_axial(row['stage'])
        assert np.max(np.abs(stageq-expected['stage_q']))/ref.AMPLITUDE<=1.e-6
        assert np.max(np.abs(stagev-expected['stage_v']))/ref.VELOCITY_SCALE<=1.e-6
        assert np.max(np.abs(stagea-expected['stage_a']))/ref.ACCELERATION_SCALE<=1.e-6
        for record,eq,ev,ea in ((row['endpoint'],expected['q'],expected['v'],expected['a']),(row['stage'],expected['stage_q'],expected['stage_v'],expected['stage_a'])):
            assert max(_account_error(record['accounting'],ref.account(eq,ev)).values())<=1.e-6
            assert np.max(np.abs(np.asarray(record['state']['nodal_frames'])-ref.FRAME))<=1.e-6
            assert np.max(np.abs(np.asarray(record['state']['cell_rotations'])-np.eye(3)))<=1.e-6
            saved=record['state'];baseline=ref.ORIGIN+np.arange(5)[:,None]*ref.ELL*ref.DIRECTION
            positions=np.asarray(saved['positions'])+np.asarray(saved['position_low'])
            assert np.max(np.abs(positions-baseline-eq[:,None]*ref.DIRECTION))/ref.AMPLITUDE<=1.e-6
            speed=np.asarray(saved['velocity']);accel=np.asarray(saved['acceleration'])
            assert np.max(np.abs(speed[:30].reshape(5,6)[:,:3]-ev[:,None]*ref.DIRECTION))/ref.VELOCITY_SCALE<=1.e-6
            assert np.max(np.abs(accel[:30].reshape(5,6)[:,:3]-ea[:,None]*ref.DIRECTION))/ref.ACCELERATION_SCALE<=1.e-6
            rotational=[6*i+3+a for i in range(5) for a in range(3)]+list(range(30,42))
            assert np.max(np.abs(speed[rotational]))/(ref.VELOCITY_SCALE/ref.ELL)<=1.e-6
            assert np.max(np.abs(accel[rotational]))/(ref.ACCELERATION_SCALE/ref.ELL)<=1.e-6
            assert np.max(np.abs(np.asarray(saved['resultants'])[:,6:]))/ref.MOMENT_SCALE<=1.e-6
            retained=np.asarray(record['state']['resultants'])[:,:6].reshape(4,3)
            force=ref.EA/ref.ELL*np.diff(eq)[:,None]*ref.DIRECTION
            assert np.max(np.abs(retained-force))/ref.FORCE_SCALE<=1.e-6
        support=row['midpoint_support'];h=row['dt']
        impulse=np.asarray(support['force_impulse_ns']);moment=np.asarray(support['moment_impulse_nms'])
        assert np.max(np.abs(impulse-expected['force_impulse']))/(ref.FORCE_SCALE*h)<=1.e-6
        assert np.max(np.abs(moment-expected['moment_impulse']))/(ref.MOMENT_SCALE*h)<=1.e-6
        assert abs(support['work_j']-expected['support_work'])/ref.ENERGY_SCALE<=1.e-6
        # Independent complete momentum balance, not a residual minus its stored reaction.
        previous=ref.account(q,v);current=row['endpoint']['accounting']
        p=np.asarray(current['linear_momentum'])+np.asarray(current['linear_momentum_low'])
        angular=np.asarray(current['angular_momentum'])+np.asarray(current['angular_momentum_low'])
        assert np.max(np.abs(p-previous['linear_momentum']-impulse))/(ref.FORCE_SCALE*h)<=1.e-6
        assert np.max(np.abs(angular-previous['angular_momentum']-moment))/(ref.MOMENT_SCALE*h)<=1.e-6
        worst_energy=max(worst_energy,abs(current['total_energy']-initial['total_energy'])/ref.ENERGY_SCALE)
        analytic_reference=ref.semidiscrete_exact(row['end_time'])
        for actual,analytic,scale in zip((actualq,actualv,actuala),analytic_reference,(ref.AMPLITUDE,ref.VELOCITY_SCALE,ref.ACCELERATION_SCALE)):
            assert np.max(np.abs(actual-analytic))/scale<=1.e-3
        observed_force.append(np.linalg.norm(impulse)/h);observed_moment.append(np.linalg.norm(moment)/h)
        q,v=expected['q'],expected['v']
    assert max(observed_force)>0. and max(observed_moment)>0.
    assert worst_energy<=.02  # Integrated gate; midpoint linear invariant is stronger analytically.


def test_independent_axial_mass_virtual_work_and_condensed_tangent():
    owner,result=run(2);_save_result('work2',result)
    state=owner.current;q,v,_=_axial(result.to_dict()['final'])
    mass,stiffness=ref.operators();axial=[6*i+1 for i in range(5)]
    # Production recovery is the quantity tested; the reference helper has no solver imports.
    with owner._operation():
        force,jacobian,_,actual_mass,*_=owner._evaluate(state)
        z=list(owner.z)
        condensed=jacobian-jacobian[:,z]@np.linalg.solve(jacobian[np.ix_(z,z)],jacobian[z,:])
    assert np.linalg.norm(actual_mass[np.ix_(axial,axial)]-mass)/np.linalg.norm(mass)<=1.e-6
    assert not np.any(actual_mass[list(owner.algebraic),:])
    assert not np.any(actual_mass[:,list(owner.algebraic)])
    assert np.max(np.abs(force[axial]-stiffness@q))/ref.FORCE_SCALE<=1.e-5
    physical_direction=np.zeros(owner.size)
    physical_direction[axial]=ref.AMPLITUDE*np.array((0.,.3,-.1,.2,.4))
    work=float(force@physical_direction);expected_work=float((stiffness@q)@physical_direction[axial])
    assert abs(work-expected_work)/ref.ENERGY_SCALE<=1.e-5
    response=condensed@physical_direction
    assert np.max(np.abs(response[axial]-stiffness@physical_direction[axial]))/ref.FORCE_SCALE<=1.e-5
    translations=[6*i+a for i in range(5) for a in range(3)]
    expected=np.zeros(owner.size);expected[axial]=stiffness@physical_direction[axial]
    moments=[6*i+3+a for i in range(5) for a in range(3)]+list(range(30,42))
    assert np.max(np.abs(response[translations]-expected[translations]))/ref.FORCE_SCALE<=1.e-5
    assert np.max(np.abs(response[moments]))/ref.MOMENT_SCALE<=1.e-5
    assert np.max(np.abs(force[moments]))/ref.MOMENT_SCALE<=1.e-5


@pytest.mark.parametrize('steps',[2,4])
def test_deforming_fresh_split_restart_preserves_full_journal(steps):
    _,full=run(steps);_save_result('split'+str(steps)+'_full',full)
    _,prefix=run(steps//2);_save_result('split'+str(steps)+'_prefix',prefix)
    _,resumed=run(steps,checkpoint=prefix.checkpoint,expected_sha256=sha256(prefix.checkpoint).hexdigest())
    _save_result('split'+str(steps)+'_resumed',resumed)
    assert resumed.checkpoint==full.checkpoint and resumed.to_dict()==full.to_dict()
