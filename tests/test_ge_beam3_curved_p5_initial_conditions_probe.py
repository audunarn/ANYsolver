"""Explicit bounded initial-state checks; not initial-history qualification."""

from dataclasses import replace

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_initial_conditions_probe as initial
from docs.reference_cases import ge_beam3_curved_p5_dynamic_restart_probe as old_codec
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_rk4_time_reference import SeparateTimeReference
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import reference_kinetic_factors
from test_ge_beam3_curved_p5_dynamic_assembly_probe import model,load,close,assembly,digest


def finite_request(made):
    n,m=made._nodes,made._count
    positions=made._coordinates+.01*np.sin(np.arange(3*n).reshape(n,3)+.3)
    v=.04*np.cos(np.arange(3*n).reshape(n,3)+.2)
    u=np.array([rotation(.15*np.sin(np.arange(3)+i+.1)) for i in range(2*m)]).reshape(m,2,3,3)
    w=.3*np.cos(np.arange(6*m).reshape(m,2,3)+.4)
    return initial.request(made,positions=positions,cell_rotations=u,nodal_velocity=v,cell_angular_velocity=w)


def test_reference_rest_initialization_preserves_zero_state_physics():
    base=model();before=digest(base.committed);made=initial.initialize(base,initial.request(base))
    receipt=made.initialization
    assert digest(base.committed)==before and made.committed.epoch==0 and made.committed.time==0.
    assert made.committed.model_sha256!=base.committed.model_sha256
    close(receipt.rate,np.zeros(base._size));close(receipt.acceleration,np.zeros(base._size))
    close(receipt.elastic_energy,0.);close(receipt.kinetic_energy,0.)
    a=base.trial(.02,load(base));b=made.trial(.02,load(base))
    close(a.response.state.positions,b.response.state.positions)
    close(a.response.state.cell_rotations,b.response.state.cell_rotations)
    made.commit(b);assert digest(made.replay())==digest(b.response)


def test_free_nonzero_uniform_velocity_continues_without_artificial_rotation():
    base=model(fixed_nodes=());velocity=np.array([.04,-.02,.03]);n=base._nodes
    conditions=initial.request(base,nodal_velocity=np.tile(velocity,(n,1)))
    made=initial.initialize(base,conditions);receipt=made.initialization
    close(receipt.acceleration,np.zeros(base._size));close(receipt.rate[base._traces],np.zeros(len(base._traces)))
    for step in range(1,4):
        trial=made.trial(.02,np.zeros((n,3)));made.commit(trial)
        close(made.committed.positions,base._coordinates+step*.02*velocity)
        close(made.committed.nodal_velocity,np.tile(velocity,(n,1)))
        close(made.committed.cell_angular_velocity,np.zeros((2,2,3)))
        assert digest(made.replay())==digest(trial.response)


def test_curved_initial_constraints_rates_and_accelerations_are_consistent():
    base=model(fixed_nodes=());conditions=finite_request(base);made=initial.initialize(base,conditions)
    r=made.initialization;core=made._core
    assert r.trace_residual_norm<=1e-11 and r.rate_residual_norm<=1e-11 and r.physical_residual_norm<=1e-11
    assert r.trace_iterations<=8 and r.trace_evaluations<=64
    assert np.array_equal(r.state.positions,conditions.positions)
    assert np.array_equal(r.state.cell_rotations,conditions.cell_rotations)
    assert np.array_equal(r.state.nodal_velocity,conditions.nodal_velocity)
    assert np.array_equal(r.state.cell_angular_velocity,conditions.cell_angular_velocity)
    assert np.linalg.norm(r.rate[core._traces])>1e-3
    epsilon=1e-6;gradients=[]
    for sign in (-1,1):
        dt=sign*epsilon;nodal=r.rate[:core._nodal].reshape(core._nodes,6)
        spins=r.rate[core._nodal:].reshape(core._count,2,3)
        q=np.array([rotation(dt*v[3:])@u for v,u in zip(nodal,r.state.rotations)])
        cells=np.array([[rotation(dt*w)@u for w,u in zip(ww,uu)] for ww,uu in zip(spins,r.state.cell_rotations)])
        state=replace(r.state,positions=r.state.positions+dt*nodal[:,:3],cell_rotations=cells)
        gradients.append(core._endpoint(state,q,lambda:None)[1])
    derivative=(gradients[1]-gradients[0])/(2*epsilon)
    close(derivative[core._traces]/core._length,np.zeros(len(core._traces)),1e-7)
    balance=r.endpoint_force.copy()
    for e,(element,row,slots) in enumerate(zip(core._elements,core._maps,core._slots)):
        kinetics=element._kinetic.evaluate(r.state.positions[row],r.state.cell_rotations[e],r.rate[slots],r.acceleration[slots])
        balance[slots]+=kinetics.inertia
    balance[:core._nodal].reshape(core._nodes,6)[:,:3]-=conditions.forces
    close(balance,r.balance)
    assert core._norm(balance,conditions.forces)<=1e-11
    trial=made.trial(.01,np.zeros((core._nodes,3)));made.commit(trial)
    assert digest(made.replay())==digest(trial.response)


def test_one_macro_acceleration_matches_separate_time_reference():
    base=model(1,fixed_nodes=());conditions=finite_request(base);made=initial.initialize(base,conditions)
    r=made.initialization;element=base._elements[0]
    reference=SeparateTimeReference(element._reference,element._elastic.section,element._kinetic.section_mass,order=8)
    other=reference.observe(r.state.positions,r.state.cell_rotations[0],r.state.nodal_velocity,r.state.cell_angular_velocity[0])
    close(r.acceleration,other.acceleration)
    close(r.state.rotations@element._reference.nodal_triads,other.point.vertex_frames)
    close(r.elastic_energy+r.kinetic_energy,other.energy)
    close(r.linear_momentum,other.linear_momentum);close(r.angular_momentum,other.angular_momentum)


def test_initial_dead_force_acceleration_matches_reference_full_mass():
    base=model();made=initial.initialize(base,initial.request(base,forces=load(base)));r=made.initialization
    mass=np.zeros((base._size,base._size))
    for element,slots in zip(base._elements,base._slots):
        factors=reference_kinetic_factors(element._reference,element._elastic.section,element._kinetic.section_mass,order=8)
        mass[np.ix_(slots,slots)]+=factors.full.T@factors.full
    physical=np.array([i for i in base._free if i>=base._nodal or i%6<3])
    external=np.zeros(base._size);external[:base._nodal].reshape(base._nodes,6)[:,:3]=load(base)
    expected=np.linalg.solve(mass[np.ix_(physical,physical)],external[physical])
    close(r.acceleration[physical],expected)
    assert np.linalg.norm(r.acceleration)>1e-3 and r.physical_residual_norm<=1e-11


def test_large_common_rigid_rotation_is_not_mistaken_for_relative_chart_exhaustion():
    base=model(fixed_nodes=());g=rotation([2.6,-1.4,.8]);shift=np.array([2.,-1.,3.])
    x=base._coordinates@g.T+shift;omega=np.array([.2,-.3,.1])
    velocity=np.array([.02,-.03,.01])+np.cross(omega,x)
    conditions=initial.request(base,positions=x,trace_seed=np.tile(g,(base._nodes,1,1)),
        cell_rotations=np.tile(g,(base._count,2,1,1)),nodal_velocity=velocity,
        cell_angular_velocity=np.tile(omega,(base._count,2,1)))
    receipt=initial.initialize(base,conditions).initialization
    close(receipt.elastic_energy,0.)
    close(receipt.state.rotations,np.tile(g,(base._nodes,1,1)))
    close(receipt.rate[:base._nodal].reshape(base._nodes,6)[:,3:],np.tile(omega,(base._nodes,1)))


def test_initialization_is_observer_covariant():
    base=model(fixed_nodes=());conditions=finite_request(base);a=initial.initialize(base,conditions).initialization
    g=rotation([1.4,-1.8,.9]);shift=np.array([2.,-1.,3.])
    refs=[e._reference.rigidly_transformed(g,shift) for e in base._elements]
    other=assembly.DynamicAssemblyProbe(refs,[(0,1,2),(2,3,4)],
        [e._elastic.section for e in base._elements],[e._kinetic.section_mass for e in base._elements],fixed_nodes=(),order=8)
    changed=initial.request(other,positions=conditions.positions@g.T+shift,trace_seed=g@conditions.trace_seed@g.T,
        cell_rotations=g@conditions.cell_rotations@g.T,nodal_velocity=conditions.nodal_velocity@g.T,
        cell_angular_velocity=conditions.cell_angular_velocity@g.T,forces=conditions.forces@g.T)
    b=initial.initialize(other,changed).initialization
    close(b.state.positions,a.state.positions@g.T+shift);close(b.state.rotations,g@a.state.rotations@g.T)
    close(b.rate.reshape(-1,3),a.rate.reshape(-1,3)@g.T)
    close(b.acceleration.reshape(-1,3),a.acceleration.reshape(-1,3)@g.T)
    close(b.linear_momentum,g@a.linear_momentum)
    close(b.angular_momentum,g@a.angular_momentum+np.cross(shift,g@a.linear_momentum))


def test_deterministic_receipts_and_public_copy_ownership():
    base=model(fixed_nodes=());conditions=finite_request(base)
    first=initial.initialize(base,conditions);second=initial.initialize(base,conditions)
    assert digest(first.initialization)==digest(second.initialization)
    saved=digest(first.initialization);copy=first.initialization
    copy.state.positions[-1,0]+=1.
    object.__setattr__(conditions,'forces',conditions.forces+1.)
    assert digest(first.initialization)==saved
    trial=first.trial(.01,np.zeros((base._nodes,3)));first.discard(trial)
    again=first.trial(.01,np.zeros((base._nodes,3)));assert digest(trial)==digest(again)


@pytest.mark.parametrize('field',['schema','model_sha256','positions','trace_seed','cell_rotations','nodal_velocity'])
def test_bad_or_clamp_incompatible_requests_do_not_mutate_expected(field):
    base=model();before=digest(base.committed);conditions=initial.request(base)
    value=getattr(conditions,field)
    if field in ('schema','model_sha256'): value='invalid'
    else:
        value=value.copy()
        if field=='positions': value[0,0]+=.1
        elif field=='nodal_velocity': value[0,0]=.1
        else: value.flat[0]=float('nan')
    with pytest.raises(initial.InitializationError): initial.initialize(base,replace(conditions,**{field:value}))
    assert digest(base.committed)==before and base._pending is None


def test_existing_trajectory_is_not_silently_reset_and_old_codec_rejects_initialized_engine():
    base=model();conditions=initial.request(base);trial=base.trial(.02,load(base))
    with pytest.raises(initial.InitializationError): initial.initialize(base,conditions)
    base.commit(trial);saved=digest(base.committed)
    with pytest.raises(initial.InitializationError): initial.initialize(base,conditions)
    assert digest(base.committed)==saved
    pristine=model();made=initial.initialize(pristine,initial.request(pristine))
    with pytest.raises(old_codec.RestartError): old_codec.dumps(made)
    with pytest.raises(old_codec.RestartError): old_codec.dumps(made._core)


def test_failure_watchdog_and_altered_initialization_context_are_atomic(monkeypatch):
    base=model();conditions=initial.request(base);before=digest(base.committed)
    original=initial._InitializedCore._recover
    def fail(*args): raise assembly.DynamicStepError('injected initialization failure')
    monkeypatch.setattr(initial._InitializedCore,'_recover',fail)
    with pytest.raises(initial.InitializationError): initial.initialize(base,conditions)
    assert digest(base.committed)==before
    monkeypatch.setattr(initial._InitializedCore,'_recover',original)
    made=initial.initialize(base,conditions)
    object.__setattr__(made._receipt,'schema','invalid')
    with pytest.raises(assembly.DynamicTransactionError): made.trial(.02,load(base))
    assert made.committed.epoch==0
    ticks=iter((0.,601.));monkeypatch.setattr(assembly.time,'monotonic',lambda:next(ticks))
    with pytest.raises(initial.InitializationError): initial.initialize(base,conditions)
    assert digest(base.committed)==before
