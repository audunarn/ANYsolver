"""Small midpoint correctness checks, not transient qualification evidence."""

from copy import deepcopy
from dataclasses import asdict, replace
import json

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_midpoint_dynamics_probe import MidpointDynamicProbe, SCHEMA
from docs.reference_cases.ge_beam3_curved_p5_implicit_dynamics_probe import (
    ImplicitDynamicProbe, DynamicStepError, DynamicTransactionError, DYNAMIC,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import reference_kinetic_factors
from docs.reference_cases import ge_beam3_curved_p5_axial_time_reference as exact
from test_ge_beam3_curved_p5_algebra_probe import reference, section
from test_ge_beam3_curved_p5_mass_probe import section_mass


def close(a,b,tolerance=1e-11):
    assert np.linalg.norm(np.asarray(a)-np.asarray(b)) <= tolerance*max(1.,np.linalg.norm(b))


def model(height=.4): return MidpointDynamicProbe(reference(height),section(),section_mass(),order=8)


def forces():
    result=np.zeros((3,3));result[-1]=[.01,-.02,.015]
    return result


@pytest.mark.parametrize('height',[0.,.4])
def test_reference_stage_matrix_has_half_configuration_and_full_trace_columns(height):
    made=model(height);h=.02
    result=made._evaluate(made.committed,np.zeros(24),h,np.zeros((3,3)))
    factors=reference_kinetic_factors(reference(height),section(),section_mass(),order=8)
    k=factors.uncondensed_stiffness_factor.T@factors.uncondensed_stiffness_factor
    m=factors.full.T@factors.full;chart=np.eye(24);chart[:,DYNAMIC]*=.5
    close(result.tangent,k@chart+2*m/h**2)
    close(result.residual,np.zeros(24))
    assert result.trace_iterations==0 and result.trace_evaluations==1


def test_nonzero_spins_and_prior_velocity_have_the_complete_analytic_stage_jacobian():
    made=model();origin=made.committed
    v=.02*np.sin(np.arange(9).reshape(3,3));v[0]=0.
    w=.03*np.cos(np.arange(6).reshape(2,3))
    origin=replace(origin,nodal_velocity=v,cell_angular_velocity=w)
    z=.003*np.sin(np.arange(24)+.2);z[:6]=0.
    direction=np.cos(np.arange(24)+.3);direction[:6]=0.;epsilon=1e-7
    response=made._stage(origin,z,.04,forces())
    plus=made._stage(origin,z+epsilon*direction,.04,forces())
    minus=made._stage(origin,z-epsilon*direction,.04,forces())
    close((plus.residual-minus.residual)/(2*epsilon),response.tangent@direction,1e-7)


@pytest.mark.parametrize('steps',[4,8,16])
def test_actual_axial_midpoint_matches_separate_recurrence_energy_and_temporal_error(steps):
    ref=reference(0.)
    elastic=np.diag([exact.EA,60.,70.,10.,12.,14.]);inertia=np.diag([exact.RHO]*3+[.2,.1,.15])
    made=MidpointDynamicProbe(ref,elastic,inertia,order=8)
    expected=exact.integrate(steps,method='MIDPOINT');h=exact.DURATION/steps;old_energy=0.
    for row in expected['records']:
        load=np.zeros((3,3));load[-1,0]=row['force'][1];old=made.committed
        trial=made.trial(h,load);made.commit(trial);state=made.committed
        close(state.positions[1:,0]-ref.coordinates[1:,0],row['positions'])
        close(state.nodal_velocity[1:,0],row['velocities'])
        energy=trial.response.elastic_energy+trial.response.kinetic_energy
        scale=max(energy,row['energy'],old_energy,1e-30)
        work=float(np.sum(load*(state.positions-old.positions)))
        assert abs(energy-row['energy'])<1e-11*scale
        assert abs(energy-old_energy-work)<1e-11*scale
        assert digest(made.replay())==digest(trial.response)
        old_energy=energy
    error=exact.temporal_error(tuple(state.positions[1:,0]-ref.coordinates[1:,0]),tuple(state.nodal_velocity[1:,0]))
    assert abs(error-expected['temporal_error'])<1e-11


@pytest.mark.parametrize('height',[0.,.4])
def test_dynamic_cell_torque_is_retained_and_endpoint_traces_are_recovered(height):
    made=model(height);before=digest(made.committed);trial=made.trial(.02,forces());r=trial.response
    assert digest(made.committed)==before and r.state.schema==SCHEMA
    assert trial.residual_norm<=1e-11 and r.trace_residual_norm<=1e-11
    assert r.trace_iterations<=8 and r.trace_evaluations<=64
    assert np.linalg.norm(r.elastic_force[18:])>1e-6
    close(r.elastic_force[18:]+r.inertia[18:],np.zeros(6))
    assert np.array_equal(r.inertia[made._traces],np.zeros(len(made._traces)))
    # Reconstruct endpoint directly, not by trusting the receipt's booleans.
    endpoint=made._elastic._jet(r.state.positions,r.state.vertex_frames,r.state.cell_rotations,external=True)
    close(endpoint.gradient,r.endpoint_elastic_force)
    close(endpoint.gradient[made._traces],np.zeros(len(made._traces)))
    assert np.linalg.norm(r.state.vertex_frames-r.stage_vertex_frames)>1e-7
    made.commit(trial);assert digest(made.replay())==digest(r)


def test_two_fresh_curved_loading_reversal_cycles_are_byte_deterministic():
    packets=[]
    for _ in range(2):
        made=model();rows=[]
        for scale in (1.,-.5,0.,.2):
            trial=made.trial(.02,scale*forces());made.commit(trial)
            assert digest(made.replay())==digest(trial.response)
            rows.append(json.dumps(asdict(trial),sort_keys=True,separators=(',',':'),
                                   allow_nan=False,default=lambda a:a.tolist()).encode('ascii'))
        assert made.committed.epoch==4
        assert np.linalg.norm(made.committed.cell_angular_velocity)>1e-6
        packets.append(rows)
    assert packets[0]==packets[1]


def test_free_translation_uses_midpoint_acceleration_not_backward_euler():
    ref=reference(0.);inertia=np.diag([2.,2.,2.,.2,.1,.15]);h=.02
    made=MidpointDynamicProbe(ref,section(),inertia,order=8,fixed_nodes=())
    acceleration=np.array([.02,-.03,.01]);load=np.array([1.,2.,1.])[:,None]*acceleration
    trial=made.trial(h,load);made.commit(trial)
    close(made.committed.positions-ref.coordinates,np.tile(.5*h*h*acceleration,(3,1)))
    close(made.committed.nodal_velocity,np.tile(h*acceleration,(3,1)))
    close(made.committed.cell_rotations,np.tile(np.eye(3),(2,1,1)))
    close(trial.response.elastic_force,np.zeros(24))


def test_observer_covariance_includes_stage_and_endpoint_traces():
    ref=reference(.4);g=rotation([1.4,-1.8,.9]);shift=np.array([2.,-1.,3.])
    first=model();second=MidpointDynamicProbe(ref.rigidly_transformed(g,shift),section(),section_mass(),order=8)
    a=first.trial(.02,forces()).response;b=second.trial(.02,forces()@g.T).response
    close(b.state.positions,a.state.positions@g.T+shift)
    close(b.state.vertex_frames,g@a.state.vertex_frames)
    close(b.stage_vertex_frames,g@a.stage_vertex_frames)
    close(b.state.cell_rotations,g@a.state.cell_rotations@g.T)
    close(b.state.nodal_velocity,a.state.nodal_velocity@g.T)
    close(b.state.cell_angular_velocity,a.state.cell_angular_velocity@g.T)


def test_small_curved_step_is_reversible_with_velocity_reversal():
    forward=model();initial=forward.trial(.02,forces());forward.commit(initial);origin=forward.committed
    trial=forward.trial(.02,forces());forward.commit(trial);end=forward.committed
    reverse=model()
    reverse._checkpoint=(replace(end,nodal_velocity=-end.nodal_velocity,
                                 cell_angular_velocity=-end.cell_angular_velocity),None)
    back=reverse.trial(.02,forces()).response.state
    close(back.positions,origin.positions);close(back.vertex_frames,origin.vertex_frames)
    close(back.cell_rotations,origin.cell_rotations)
    close(back.nodal_velocity,-origin.nodal_velocity)
    close(back.cell_angular_velocity,-origin.cell_angular_velocity)


def test_schema_and_model_identity_prevent_backward_euler_restart():
    made=model();old=ImplicitDynamicProbe(reference(.4),section(),section_mass(),order=8).committed
    assert old.schema!=made.committed.schema and old.model_sha256!=made.committed.model_sha256
    with pytest.raises(DynamicTransactionError): made._evaluate(old,np.zeros(24),.02,forces())
    with pytest.raises(DynamicTransactionError): made._evaluate(replace(old,schema=SCHEMA),np.zeros(24),.02,forces())


def test_failed_step_and_discard_do_not_change_checkpoint():
    made=model();before=digest(made.committed)
    for kwargs in ({'max_iterations':0},{'max_evaluations':1}):
        with pytest.raises(DynamicStepError): made.trial(.02,forces(),**kwargs)
        assert digest(made.committed)==before and made._pending is None
    trial=made.trial(.02,forces());made.discard(trial)
    again=made.trial(.02,forces());assert digest(again)==digest(trial)
    assert digest(made.committed)==before


@pytest.mark.parametrize('field',['endpoint_elastic_force','stage_vertex_frames','trace_residual_norm','trace_evaluations'])
def test_rehashed_endpoint_receipt_mutations_fail_fresh_replay(field):
    made=model();trial=made.trial(.02,forces());before=digest(made.committed)
    value=getattr(trial.response,field)
    object.__setattr__(trial.response,field,value+1)
    made._pending_digest=digest(trial)
    with pytest.raises(DynamicTransactionError): made.commit(trial)
    assert digest(made.committed)==before


def test_late_endpoint_recovery_failure_is_atomic(monkeypatch):
    made=model();trial=made.trial(.02,forces());before=digest(made.committed)
    def fail(*args): raise DynamicStepError('injected endpoint failure')
    monkeypatch.setattr(made,'_recover_traces',fail)
    with pytest.raises(DynamicStepError,match='injected'): made.commit(trial)
    assert digest(made.committed)==before


@pytest.mark.parametrize('factor,reason',[(2.,'update bound'),(-1.,'line search')])
def test_endpoint_root_iterations_are_bounded_under_injected_bad_newton_matrices(monkeypatch,factor,reason):
    made=model();before=digest(made.committed);state=made.committed
    positions=state.positions.copy();positions[-1]+=[.001,-.002,.0015]
    original=made._spatial_stiffness
    monkeypatch.setattr(made,'_spatial_stiffness',lambda e:factor*original(e))
    with pytest.raises(DynamicStepError,match=reason):
        made._recover_traces(replace(state,positions=positions))
    assert digest(made.committed)==before and made._pending is None


def test_foreign_trial_and_invalid_steps_are_rejected():
    made=model();before=digest(made.committed)
    for h in (True,0.,-.1,.11,float('nan')):
        with pytest.raises(DynamicStepError): made.trial(h,forces())
    assert digest(made.committed)==before
    trial=made.trial(.02,forces())
    with pytest.raises(DynamicTransactionError): made.commit(deepcopy(trial))
    assert digest(made.committed)==before
