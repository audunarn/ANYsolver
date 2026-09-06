"""Small semidiscrete temporal comparisons, not independent mechanics proof."""

import ast
from dataclasses import replace
import json
import math
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_rk4_time_reference as separate
from docs.reference_cases.ge_beam3_curved_p5_midpoint_dynamics_probe import MidpointDynamicProbe
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from test_ge_beam3_curved_p5_algebra_probe import reference,section
from test_ge_beam3_curved_p5_mass_probe import section_mass


DURATION=.08


def setup():
    ref=reference(.4);oracle=separate.SeparateTimeReference(ref,section(),section_mass(),order=8)
    x=ref.coordinates+np.array([[.01,-.02,.015],[-.015,.01,.02],[.02,.015,-.01]])
    cells=np.array([rotation([.2,-.1,.15]),rotation([-.1,.18,.05])])
    v=np.array([[.04,-.02,.03],[-.01,.05,-.02],[.02,-.03,.01]])
    w=np.array([[.3,-.2,.4],[-.25,.35,.15]])
    return ref,oracle,oracle.observe(x,cells,v,w)


def midpoint(ref,oracle,initial,steps):
    made=MidpointDynamicProbe(ref,section(),section_mass(),order=8,fixed_nodes=())
    p=initial.point
    state=replace(made.committed,positions=p.positions,vertex_frames=p.vertex_frames,
                  cell_rotations=p.cell_rotations,nodal_velocity=p.nodal_velocity,
                  cell_angular_velocity=p.cell_angular_velocity)
    made._check_state(state)
    # Research-only initial-value fixture, not a production restart/load API.
    made._checkpoint=(state,None)
    for _ in range(steps):
        trial=made.trial(DURATION/steps,np.zeros((3,3)))
        made.commit(trial)
        assert digest(made.replay())==digest(trial.response)
        assert trial.residual_norm<=1e-11 and trial.response.trace_residual_norm<=1e-11
    end=made.committed
    observed=oracle.observe(end.positions,end.cell_rotations,end.nodal_velocity,end.cell_angular_velocity)
    assert np.linalg.norm(observed.point.vertex_frames-end.vertex_frames)<1e-11
    return observed


def drifts(initial,final):
    return {'energy':abs(final.energy-initial.energy)/initial.energy,
            'linear_momentum':float(np.linalg.norm(final.linear_momentum-initial.linear_momentum))/max(1.,np.linalg.norm(initial.linear_momentum)),
            'angular_momentum':float(np.linalg.norm(final.angular_momentum-initial.angular_momentum))/max(1.,np.linalg.norm(initial.angular_momentum))}


def test_reference_imports_no_existing_time_stepper():
    tree=ast.parse(Path(separate.__file__).read_text())
    imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any('midpoint' in name or 'implicit_dynamics' in name for name in imports)
    assert any('finite_inertia_probe' in name for name in imports)  # explicitly shared physics


def test_separate_inverse_exp_jacobian_gives_spatial_angular_velocity():
    omega=np.array([.3,-.4,.2]);epsilon=1e-6
    for beta in (np.zeros(3),np.array([1e-6,-2e-6,3e-6]),np.array([.5,-.3,.4])):
        rate=separate.inverse_left_jacobian(beta)@omega
        derivative=(rotation(beta+epsilon*rate)-rotation(beta-epsilon*rate))/(2*epsilon)
        cross=derivative@rotation(beta).T
        measured=np.array([cross[2,1]-cross[1,2],cross[0,2]-cross[2,0],cross[1,0]-cross[0,1]])/2
        assert np.linalg.norm(measured-omega)<1e-7
    with pytest.raises(ValueError): separate.inverse_left_jacobian([np.pi,0.,0.])


def test_free_reference_acceleration_preserves_instantaneous_energy_and_momentum():
    _,oracle,initial=setup();p=initial.point;a=initial.acceleration
    epsilon=1e-6;observations=[]
    for sign in (-1,1):
        dt=sign*epsilon
        x=p.positions+dt*p.nodal_velocity
        cells=np.array([rotation(dt*w)@u for w,u in zip(p.cell_angular_velocity,p.cell_rotations)])
        v=p.nodal_velocity+dt*a[:18].reshape(3,6)[:,:3]
        w=p.cell_angular_velocity+dt*a[18:].reshape(2,3)
        observations.append(oracle.observe(x,cells,v,w))
    minus,plus=observations
    assert abs((plus.energy-minus.energy)/(2*epsilon))<1e-7*max(1.,initial.energy)
    assert np.linalg.norm((plus.linear_momentum-minus.linear_momentum)/(2*epsilon))<1e-7
    assert np.linalg.norm((plus.angular_momentum-minus.angular_momentum)/(2*epsilon))<1e-7
    assert initial.trace_residual_norm<=1e-11 and initial.physical_residual_norm<=1e-11


def test_four_step_smoke_is_finite_and_keeps_real_cell_inertia():
    ref,oracle,initial=setup()
    rk,count=oracle.integrate(initial.point,DURATION,4)
    mid=midpoint(ref,oracle,initial,4)
    assert count==16 and np.isfinite(rk.energy+mid.energy)
    assert separate.state_distance(rk.point,initial.point,oracle.length,DURATION)>1e-3
    print('\nSMOKE',json.dumps({'rk4_rhs':count,'rk4_drift':drifts(initial,rk),'midpoint_drift':drifts(initial,mid)},sort_keys=True))


@pytest.fixture(scope='module')
def study():
    ref,oracle,initial=setup()
    coarse,count16=oracle.integrate(initial.point,DURATION,16)
    fine,count32=oracle.integrate(initial.point,DURATION,32)
    scale=separate.state_distance(fine.point,initial.point,oracle.length,DURATION)
    results=[midpoint(ref,oracle,initial,n) for n in (4,8,16)]
    errors=[separate.state_distance(r.point,fine.point,oracle.length,DURATION)/scale for r in results]
    uncertainty=separate.state_distance(coarse.point,fine.point,oracle.length,DURATION)/scale
    record={'schema':separate.SCHEMA,'rk4_rhs':[count16,count32],
            'midpoint_steps':[4,8,16],'state_errors':errors,'reference_refinement_difference':uncertainty,
            'observed_order':math.log2(errors[-2]/errors[-1]),
            'midpoint_drifts':[drifts(initial,r) for r in results],
            'reference_drifts':[drifts(initial,coarse),drifts(initial,fine)],'production_qualified':False}
    print('\nTIME_COMPARISON',json.dumps(record,sort_keys=True,allow_nan=False))
    return record


def test_curved_finite_motion_has_second_order_temporal_convergence(study):
    errors=study['state_errors']
    assert study['rk4_rhs']==[64,128]
    assert study['reference_refinement_difference']<errors[-1]/20
    assert all(b<a for a,b in zip(errors,errors[1:]))
    assert 1.8<=study['observed_order']<=2.2


def test_nonlinear_energy_and_momentum_drift_is_disclosed_and_refines(study):
    for key in ('energy','linear_momentum','angular_momentum'):
        values=[row[key] for row in study['midpoint_drifts']]
        assert all(b<a or max(a,b)<1e-11 for a,b in zip(values,values[1:]))
    # The method is NOT represented as exactly energy-momentum conserving.
    assert study['midpoint_drifts'][0]['energy']>1e-11
    assert study['production_qualified'] is False


def test_reference_rejects_bad_input_and_enforces_wall_bound(monkeypatch):
    _,oracle,initial=setup()
    for duration,steps in ((True,4),(0.,4),(.11,4),(.08,True),(.08,64)):
        with pytest.raises(ValueError): oracle.integrate(initial.point,duration,steps)
    bad=replace(initial.point,vertex_frames=reference(.4).nodal_triads)
    with pytest.raises(ValueError,match='inconsistent'): oracle.integrate(bad,.08,4)
    ticks=iter((0.,601.))
    monkeypatch.setattr(separate.time,'monotonic',lambda:next(ticks))
    with pytest.raises(separate.TimeReferenceError,match='wall limit'):
        oracle.integrate(initial.point,.08,4)


def test_comparison_cannot_hide_nonfinite_or_invalid_rotation_data():
    _,oracle,initial=setup();point=initial.point
    for length,duration in ((True,.08),(0.,.08),(2.,float('nan'))):
        with pytest.raises(ValueError): separate.state_distance(point,point,length,duration)
    for field in ('positions','cell_rotations','nodal_velocity','cell_angular_velocity'):
        corrupted=getattr(point,field).copy();corrupted.flat[0]=float('nan')
        with pytest.raises(ValueError):
            separate.state_distance(replace(point,**{field:corrupted}),point,oracle.length,.08)
    invalid=point.cell_rotations.copy();invalid[0]*=2
    with pytest.raises(ValueError):
        separate.state_distance(replace(point,cell_rotations=invalid),point,oracle.length,.08)


def test_reference_trace_failure_leaves_input_unchanged(monkeypatch):
    _,oracle,initial=setup();before=digest(initial)
    original=oracle.elastic._jet
    def never_converge(*args,**kwargs):
        value=original(*args,**kwargs)
        value.gradient[separate.TRACES]=1.
        return value
    monkeypatch.setattr(oracle.elastic,'_jet',never_converge)
    with pytest.raises(separate.TimeReferenceError,match='line search'):
        oracle.integrate(initial.point,.08,4)
    assert digest(initial)==before
