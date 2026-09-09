"""Small implicit dynamic/state checks, not full transient qualification."""

from copy import deepcopy
from dataclasses import replace

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_implicit_dynamics_probe import (
    ImplicitDynamicProbe,DynamicStepError,DynamicTransactionError,left_jacobian,ROTATIONS,DYNAMIC,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import reference_kinetic_factors
from test_ge_beam3_curved_p5_algebra_probe import reference,section
from test_ge_beam3_curved_p5_mass_probe import section_mass


def close(a,b,tolerance=1e-11):
    assert np.linalg.norm(np.asarray(a)-np.asarray(b))<=tolerance*max(1.,np.linalg.norm(b))


def model(height=.4): return ImplicitDynamicProbe(reference(height),section(),section_mass(),order=8)


def forces():
    result=np.zeros((3,3));result[-1]=[.01,-.02,.015]
    return result


def test_left_exp_jacobian_uses_spatial_not_material_increment():
    for value in ([0.,0.,0.],[1e-7,-2e-7,3e-7],[.6,-.4,.2]):
        value=np.array(value);direction=np.array([.2,.3,-.4]);epsilon=1e-6
        frame=rotation(value)
        derivative=(rotation(value+epsilon*direction)-rotation(value-epsilon*direction))/(2*epsilon)
        angular=derivative@frame.T
        vector=np.array([angular[2,1]-angular[1,2],angular[0,2]-angular[2,0],angular[1,0]-angular[0,1]])/2
        close(left_jacobian(value)@direction,vector,1e-7)
    with pytest.raises(ValueError): left_jacobian([np.pi,0.,0.])


@pytest.mark.parametrize('height',[0.,.4])
def test_zero_state_effective_matrix_matches_uncondensed_linear_pencil(height):
    ref=reference(height);made=model(height);h=.02
    result=made._evaluate(made.committed,np.zeros(24),h,np.zeros((3,3)))
    factors=reference_kinetic_factors(ref,section(),section_mass(),order=8)
    k=factors.uncondensed_stiffness_factor.T@factors.uncondensed_stiffness_factor
    m=factors.full.T@factors.full
    close(result.tangent,k+m/h**2)
    close(result.residual,np.zeros(24))


def test_complete_analytic_newton_matrix_at_nonzero_increment():
    made=model();origin=made.committed
    z=.001*np.sin(np.arange(24)+.2);z[:6]=0.
    direction=np.cos(np.arange(24)+.3);direction[:6]=0.;epsilon=1e-7
    response=made._evaluate(origin,z,.04,forces())
    plus=made._evaluate(origin,z+epsilon*direction,.04,forces())
    minus=made._evaluate(origin,z-epsilon*direction,.04,forces())
    close((plus.residual-minus.residual)/(2*epsilon),response.tangent@direction,1e-7)


@pytest.mark.parametrize('height',[0.,.4])
def test_dynamic_cell_balance_commit_and_fresh_replay(height):
    made=model(height);before=digest(made.committed)
    trial=made.trial(.02,forces())
    assert digest(made.committed)==before
    assert trial.residual_norm<=1e-11 and trial.iterations<=16 and trial.evaluations<=128
    # A dynamic spin is not statically equilibrated: elastic torque is
    # balanced by inertia, not forced to zero by a hidden local solve.
    assert np.linalg.norm(trial.response.elastic_force[18:])>1e-6
    close(trial.response.elastic_force[18:]+trial.response.inertia[18:],np.zeros(6))
    traces=np.r_[np.arange(9,12),np.arange(15,18)]
    close(trial.response.elastic_force[traces],np.zeros(6))
    assert np.array_equal(trial.response.inertia[traces],np.zeros(6))
    made.commit(trial)
    assert made.committed.epoch==1 and made.committed.time==.02
    assert digest(made.replay())==digest(trial.response)
    with pytest.raises(DynamicTransactionError): made.commit(trial)


def test_pure_axial_steps_match_linear_backward_euler_algebra():
    ref=reference(0.);elastic=np.diag([100.,60.,70.,10.,12.,14.]);inertia=np.diag([2.,2.,2.,.2,.1,.15])
    made=ImplicitDynamicProbe(ref,elastic,inertia,order=8)
    factors=reference_kinetic_factors(ref,elastic,inertia,order=8)
    k=factors.uncondensed_stiffness_factor.T@factors.uncondensed_stiffness_factor
    m=factors.full.T@factors.full;active=np.array([6,12]);ka=k[np.ix_(active,active)];ma=m[np.ix_(active,active)]
    displacement=np.zeros(2);speed=np.zeros(2);h=.02
    for force in (.1,.1,0.,0.):
        load=np.zeros((3,3));load[-1,0]=force
        speed=np.linalg.solve(ma+h*h*ka,ma@speed-h*(ka@displacement)+h*np.array([0.,force]))
        displacement+=h*speed
        trial=made.trial(h,load);made.commit(trial)
        close(made.committed.positions[1:,0]-ref.coordinates[1:,0],displacement)
        close(made.committed.nodal_velocity[1:,0],speed)


def test_free_body_uniform_translation_needs_no_artificial_constraint():
    ref=reference(0.);inertia=np.diag([2.,2.,2.,.2,.1,.15])
    made=ImplicitDynamicProbe(ref,section(),inertia,order=8,fixed_nodes=())
    acceleration=np.array([.02,-.03,.01]);h=.02
    # Integral of the piecewise linear nodal shapes times rho=2, L=2.
    loads=np.array([1.,2.,1.])[:,None]*acceleration
    trial=made.trial(h,loads);made.commit(trial)
    close(made.committed.positions-ref.coordinates,np.tile(h*h*acceleration,(3,1)))
    close(made.committed.nodal_velocity,np.tile(h*acceleration,(3,1)))
    close(made.committed.cell_rotations,np.tile(np.eye(3),(2,1,1)))
    close(made.committed.vertex_frames,ref.nodal_triads)
    close(trial.response.elastic_force,np.zeros(24))
    assert trial.residual_norm<=1e-11


def test_constant_observer_transform_preserves_one_step():
    ref=reference(.4);g=rotation([1.4,-1.8,.9]);shift=np.array([2.,-1.,3.])
    first=ImplicitDynamicProbe(ref,section(),section_mass(),order=8)
    second=ImplicitDynamicProbe(ref.rigidly_transformed(g,shift),section(),section_mass(),order=8)
    a=first.trial(.02,forces());b=second.trial(.02,forces()@g.T)
    close(b.response.state.positions,a.response.state.positions@g.T+shift)
    close(b.response.state.vertex_frames,g@a.response.state.vertex_frames)
    close(b.response.state.cell_rotations,g@a.response.state.cell_rotations@g.T)
    close(b.response.state.nodal_velocity,a.response.state.nodal_velocity@g.T)
    close(b.response.state.cell_angular_velocity,a.response.state.cell_angular_velocity@g.T)


def test_curved_coupled_loading_reversal_and_unloading_use_prior_velocity():
    made=model(.4);initial=digest(made.committed)
    for epoch,scale in enumerate((1.,-.5,0.,.2),1):
        old=made.committed;trial=made.trial(.02,scale*forces())
        assert digest(trial.origin)==digest(old)
        assert trial.residual_norm<=1e-11
        made.commit(trial)
        assert made.committed.epoch==epoch
        close(made.committed.time,epoch*.02)
        assert digest(made.replay())==digest(trial.response)
    assert digest(made.committed)!=initial and np.linalg.norm(made.committed.cell_angular_velocity)>1e-6
    preserved=digest(made.committed)
    # Public trial/committed copies cannot mutate the internal accepted receipt.
    object.__setattr__(trial.response.state,'time',4.)
    copy=made.committed;copy.positions[-1,0]+=1.
    assert digest(made.committed)==preserved
    assert digest(made.replay().state)==preserved


def test_step_failure_and_discard_leave_checkpoint_unchanged():
    made=model();initial=digest(made.committed)
    with pytest.raises(DynamicStepError): made.trial(.02,forces(),max_iterations=0)
    assert digest(made.committed)==initial and made._pending is None
    with pytest.raises(DynamicStepError): made.trial(.02,forces(),max_evaluations=1)
    assert digest(made.committed)==initial and made._pending is None
    pending=made.trial(.02,forces())
    with pytest.raises(DynamicTransactionError): made.trial(.02,forces())
    made.discard(pending)
    assert digest(made.committed)==initial
    again=made.trial(.02,forces());assert digest(again)==digest(pending)
    made.commit(again)


@pytest.mark.parametrize('mutation',['foreign','force','increment','state','origin','rehashed','metadata'])
def test_foreign_changed_and_rehashed_trial_rejected(mutation):
    made=model();trial=made.trial(.02,forces());before=digest(made.committed)
    if mutation=='foreign':
        with pytest.raises(DynamicTransactionError): made.commit(deepcopy(trial))
        assert digest(made.committed)==before;return
    if mutation=='force': object.__setattr__(trial,'forces',forces()*2)
    if mutation in ('increment','rehashed'): object.__setattr__(trial,'increment',trial.increment+np.r_[np.zeros(6),np.ones(18)*1e-3])
    if mutation=='state': object.__setattr__(trial.response,'state',replace(trial.response.state,time=.5))
    if mutation=='origin': object.__setattr__(trial,'origin',replace(trial.origin,epoch=2))
    if mutation=='metadata': object.__setattr__(trial,'evaluations',129)
    if mutation in ('rehashed','metadata'): made._pending_digest=digest(trial)
    with pytest.raises(DynamicTransactionError): made.commit(trial)
    assert digest(made.committed)==before


def test_late_reconstruction_failure_is_atomic(monkeypatch):
    made=model();trial=made.trial(.02,forces());before=digest(made.committed)
    def fail(*args): raise ValueError('injected replay failure')
    monkeypatch.setattr(made._kinetic,'evaluate',fail)
    with pytest.raises(ValueError,match='injected'): made.commit(trial)
    assert digest(made.committed)==before


def test_invalid_step_model_and_constraint_inputs_fail_closed():
    made=model();before=digest(made.committed)
    for h in (True,0.,-.1,.11,float('nan')):
        with pytest.raises(DynamicStepError): made.trial(h,forces())
    for kwargs in ({'max_iterations':True},{'max_iterations':17},{'max_evaluations':0},{'max_evaluations':129}):
        with pytest.raises(ValueError): made.trial(.01,forces(),**kwargs)
    with pytest.raises(ValueError): ImplicitDynamicProbe(reference(),section(),section_mass(),fixed_nodes=(0,0))
    with pytest.raises(ValueError): ImplicitDynamicProbe(reference(),section(),section_mass(),fixed_nodes=(True,))
    assert digest(made.committed)==before
    changed=replace(made.committed,model_sha256='a'*64)
    with pytest.raises(DynamicTransactionError): made._evaluate(changed,np.zeros(24),.02,forces())
    bad=np.zeros(24);bad[0]=.1
    with pytest.raises(ValueError): made._evaluate(made.committed,bad,.02,forces())
