"""Small compensated assembly/state tests; no 32-element execution."""

from copy import deepcopy
from dataclasses import asdict, replace
from types import SimpleNamespace

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_compensated_assembly import (
    CompensatedAssemblyHistoryProbe, CompensatedState, CompensatedTrial,
    CompensatedElementResponse, COORDINATES, SCHEMA, move_pairs,
)
from docs.reference_cases.ge_beam3_curved_p5_compensated_control import CompensatedDisplacementControlledAssemblyProbe
from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import (
    DisplacementControlledAssemblyProbe, DisplacementControlError, ControlObservationError,
)
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import AssemblyPathError, AssemblyTransactionError
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import canonical
from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
from test_ge_beam3_curved_p5_assembly_history_probe import model, forces


def compensated(old):
    return CompensatedAssemblyHistoryProbe(old._references,[tuple(int(n) for n in row) for row in old._maps],
        old._sections,fixed_nodes=tuple(int(n) for n in old._fixed),order=old._order,extent=old._extent)


def driver():
    old,_=make_beam(2)
    return CompensatedDisplacementControlledAssemblyProbe(compensated(old),node=2)


@pytest.fixture(scope='module')
def loaded():
    made=compensated(model())
    return made,made.trial(.1*forces())


def test_normalized_nodal_update_retains_sub_ulp_values():
    high=np.ones((3,3));low=np.zeros_like(high);delta=np.full_like(high,2.**-60)
    a,b=move_pairs(high,low,delta)
    np.testing.assert_array_equal(a,high)
    np.testing.assert_array_equal(b,delta)
    c,d=move_pairs(a,b,-delta)
    np.testing.assert_array_equal(c,high);np.testing.assert_array_equal(d,low)


def test_trial_contains_low_parts_in_all_bound_records(loaded):
    made,trial=loaded
    assert type(made.committed) is CompensatedState and type(trial) is CompensatedTrial
    assert trial.coordinate_schema==made.committed.coordinate_schema==COORDINATES
    assert np.any(trial.position_low) and trial.residual_norm<=1e-11
    assert not np.any(trial.position_low[made._fixed])
    for row,e in zip(made._maps,trial.response.elements):
        assert type(e) is CompensatedElementResponse and e.accuracy_schema==SCHEMA
        np.testing.assert_array_equal(e.position_low,trial.position_low[row])
    assert digest(made._reconstruct(trial))==digest(trial.response)


def test_plastic_loading_unloading_discard_and_fresh_replay(loaded):
    made=deepcopy(loaded[0]);trial=made._pending;made.commit(trial)
    assert any(s.response.plastic_active for e in trial.response.elements for s in e.stations)
    np.testing.assert_array_equal(made.committed.position_low,trial.position_low)
    assert digest(made.replay())==digest(trial.response)
    after=digest(made.committed)
    declined=made.trial(.12*forces());made.discard(declined)
    assert digest(made.committed)==after
    unloading=made.trial(.05*forces());made.commit(unloading)
    assert digest(made.replay())==digest(unloading.response)
    assert unloading.origins==tuple(tuple(s.response.history for s in e.stations) for e in trial.response.elements)
    fresh=deepcopy(made)
    assert digest(fresh.replay())==digest(unloading.response)


@pytest.mark.parametrize('mutation',['schema','low','element_low','both_low','clamp','policy','origin','missing'])
def test_rehashed_trial_mutations_fail_without_commit(loaded,mutation):
    made=deepcopy(loaded[0]);trial=made._pending;before=digest(made.committed)
    low=trial.position_low.copy();elements=list(trial.response.elements)
    if mutation=='schema': trial=replace(trial,coordinate_schema='old')
    if mutation in ('low','both_low'): low[2,0]+=2.**-60
    if mutation=='clamp': low[0,0]=2.**-60
    if mutation in ('low','both_low','clamp'): trial=replace(trial,position_low=low)
    if mutation in ('element_low','both_low'):
        row=made._maps[0];changed=elements[0].position_low.copy()
        if mutation=='both_low': changed=low[row]
        else: changed[2,0]+=2.**-60
        elements[0]=replace(elements[0],position_low=changed)
        trial=replace(trial,response=replace(trial.response,elements=tuple(elements)))
    if mutation=='policy':
        elements[0]=replace(elements[0],accuracy_schema='old')
        trial=replace(trial,response=replace(trial.response,elements=tuple(elements)))
    if mutation=='origin':
        origins=list(trial.origins);first=list(origins[0]);first[0]=replace(first[0],accumulated=.01)
        origins[0]=tuple(first);trial=replace(trial,origins=tuple(origins))
    if mutation=='missing':
        from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import AssemblyTrial
        from dataclasses import fields
        trial=AssemblyTrial(**{f.name:getattr(trial,f.name) for f in fields(AssemblyTrial)})
    made._pending,made._pending_digest=trial,digest(trial)
    with pytest.raises(AssemblyTransactionError): made.commit(trial)
    assert digest(made.committed)==before


def test_late_replay_failure_budget_and_foreign_trial_leave_state_unchanged(loaded,monkeypatch):
    made=deepcopy(loaded[0]);trial=made._pending;before=digest(made.committed)
    real=made._reconstruct_element
    def fail_last(index,trial):
        if index==1: raise ValueError('injected last element failure')
        return real(index,trial)
    monkeypatch.setattr(made,'_reconstruct_element',fail_last)
    with pytest.raises(AssemblyTransactionError): made.commit(trial)
    assert digest(made.committed)==before
    other=compensated(model())
    with pytest.raises(AssemblyTransactionError): other.commit(loaded[1])
    with pytest.raises(AssemblyPathError): other.trial(.1*forces(),max_mixed_evaluations=0)
    assert other._pending is None and digest(other.committed)==before


def test_displacement_correction_and_committed_low_parts_are_deterministic():
    one,two=driver(),driver()
    for target in (.1,.095,.097):
        a,b=one.trial(target),two.trial(target)
        assert canonical(asdict(a))==canonical(asdict(b))
        assert a.assembly.position_low[2,1]==0. and a.assembly.positions[2,1]==target
        one.commit(a);two.commit(b)
        assert digest(one.committed_model.replay())==digest(a.assembly.response)
        assert digest(one.committed_model.committed)==digest(two.committed_model.committed)


def test_failure_snapshot_preserves_and_reconstructs_coordinate_parts():
    d=driver();before=digest(d.committed_model.committed);saved=[];events=[]
    with pytest.raises(DisplacementControlError):
        d.trial(.095,max_iterations=0,observer=events.append,failure_observer=saved.append)
    assert len(saved)==1 and d._pending is None
    raw=saved[0]
    assert raw['schema']=='GE_BEAM3_P5_COMPENSATED_FAILED_LAST_EVALUATION_V1'
    assert raw['coordinate_schema']==COORDINATES and raw['disposition']=='UNCOMMITTED_DIAGNOSTIC_ONLY'
    assert np.any(raw['position_low'])
    assert digest(d.committed_model._reconstruct(SimpleNamespace(**raw)))==digest(raw['response'])
    assert digest(d.committed_model.committed)==before
    raw['position_low'].setflags(write=True);raw['position_low'][:]=99
    assert digest(d.committed_model.committed)==before


def test_failure_sink_and_no_initial_response_do_not_publish():
    d=driver();before=digest(d.committed_model.committed)
    def deny(raw): raise OSError('disk unavailable')
    with pytest.raises(ControlObservationError): d.trial(.095,max_iterations=0,failure_observer=deny)
    assert d._pending is None and digest(d.committed_model.committed)==before
    saved=[]
    with pytest.raises(DisplacementControlError): d.trial(.095,max_mixed_evaluations=0,failure_observer=saved.append)
    assert not saved


def test_old_profile_is_not_upgraded_and_checkpoint_low_mutation_is_rejected(loaded):
    old=model();new=compensated(old)
    with pytest.raises(ValueError): DisplacementControlledAssemblyProbe(new,node=2)
    with pytest.raises(ValueError): CompensatedDisplacementControlledAssemblyProbe(old,node=2)
    new._checkpoint=deepcopy(old._checkpoint)
    with pytest.raises(AssemblyTransactionError): _=new.committed
    made=deepcopy(loaded[0]);trial=made._pending;made.commit(trial)
    state,accepted=made._checkpoint;low=state.position_low.copy();low[2,0]+=2.**-60
    made._checkpoint=(replace(state,position_low=low),accepted)
    with pytest.raises(AssemblyTransactionError): made.replay()


def test_observation_and_failure_sink_do_not_change_success_bytes():
    plain,observed=driver(),driver();rows=[];failures=[]
    a=plain.trial(.095)
    b=observed.trial(.095,observer=rows.append,failure_observer=failures.append)
    assert canonical(asdict(a))==canonical(asdict(b)) and not failures
    assert rows[-1]['phase']=='CONVERGED'
    assert all('position_low_change_max' in r['metrics'] for r in rows if r['phase']=='CANDIDATE')


def test_rehashed_controller_trial_must_match_staged_assembly():
    d=driver();trial=d.trial(.095);before=digest(d.committed_model.committed)
    changed=replace(trial,control_dof=0)
    d._pending,d._pending_digest=changed,digest(changed)
    with pytest.raises(DisplacementControlError): d.commit(changed)
    assert digest(d.committed_model.committed)==before


def test_interface_force_and_moment_work_balance(loaded):
    made,trial=loaded
    first,second=[e.residual.reshape(3,6) for e in trial.response.elements]
    assert np.linalg.norm(first[2]+second[0])<=1e-11
    r=trial.response.residual.reshape(made._nodes,6)
    assert np.linalg.norm(r[:,:3].sum(axis=0))<=1e-11
    # Compute the low-part moment contribution separately, not x_hi+x_lo.
    moment=r[:,3:]+np.cross(trial.positions,r[:,:3])+np.cross(trial.position_low,r[:,:3])
    assert np.linalg.norm(moment.sum(axis=0))<=1e-11
    assert np.linalg.norm(r[made._free_nodes,:3]-trial.forces[made._free_nodes])<=1e-11


def test_assembled_spatial_tangent_with_compensated_perturbations(loaded):
    from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
    from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative
    made,trial=loaded;direction=np.sin(np.arange(6*made._nodes)+.3)/20
    direction.reshape(made._nodes,6)[made._fixed]=0.
    epsilon=1e-6;responses=[]
    for sign in (1.,-1.):
        delta=(sign*epsilon*direction).reshape(made._nodes,6)
        x,low=move_pairs(trial.positions,trial.position_low,delta[:,:3])
        u=np.array([rotation(d[3:])@old for d,old in zip(delta,trial.rotations)])
        responses.append(made.response_at(x,u,position_low=low))
    plus,minus=responses
    active=lambda r:tuple(s.response.plastic_active for e in r.elements for s in e.stations)
    assert active(plus)==active(trial.response)==active(minus)
    expected=spatial_derivative(trial.response)@direction
    assert np.linalg.norm((plus.residual-minus.residual)/(2*epsilon)-expected)/max(1.,np.linalg.norm(expected))<=1e-7
    assert abs((plus.potential-minus.potential)/(2*epsilon)-trial.response.residual@direction)<=1e-7
