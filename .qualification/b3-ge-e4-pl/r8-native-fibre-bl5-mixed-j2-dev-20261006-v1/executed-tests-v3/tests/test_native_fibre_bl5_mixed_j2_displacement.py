"""Public yielded all-S3/mixed native BL5 histories and exact predecessor checks."""
from dataclasses import replace
import json
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken,SolveCancelled
from anysolver._stiffened_shell_displacement_checkpoint import identities,decode_snapshot
from examples.stiffened_shell_native_fibre_bl5_mixed_j2_displacement import definition
from examples.stiffened_shell_native_fibre_bl5_displacement import ACTIONS,CONTROL,OPTIONS,TARGETS

@pytest.fixture(scope='module',params=(('s3','biaxial','mixed','p0'),('mixed','biaxial','mixed','continuous_p1_coarse'),('s3','axial','fibre','p0')))
def loaded(request):
    model=definition(*request.param);owner=ss.create_analysis(definition=model)
    try:
        seed=owner.solve(ACTIONS,(.001,),**OPTIONS);assert seed.status=='completed'
        raw=owner.checkpoint();fresh=ss.create_analysis(definition=model)
        try:fresh.restore(raw);assert fresh.checkpoint()==raw
        finally:fresh.close()
        observed=[]
        result=owner.solve(ACTIONS,TARGETS[:2],displacement_control=CONTROL,on_accepted=observed.append,**OPTIONS)
        assert result.status=='completed'
        assert max(map(max,result.beam_station_accumulated))>0
        if request.param[1]=='biaxial':assert max(map(max,result.shell_layer_alpha))>0
        assert result.shell_s3_material and result.beam_fibre_material
        assert bool(result.shell_q4_material)==bool(model.shell.q4_elements)
        if request.param[2]=='mixed':assert result.beam_generalized_material
        yield model,owner.checkpoint()
    finally:owner.close()


def test_public_restart_continue_and_atomic_refusals(loaded,tmp_path,monkeypatch):
    model,saved=loaded;owner=ss.create_analysis(definition=model);owner.restore(saved)
    fresh=ss.create_analysis(definition=owner._definition)
    try:
        restored=fresh.restore(saved);assert fresh.checkpoint()==saved
        assert restored.shell_layer_alpha==owner.recover().shell_layer_alpha
        assert owner.capabilities()['displacement_control']=='experimental_native_fibre_bl5_mixed_shell_j2_fixed_translation_v1'
        assert 'Q4/S3 J2' in owner.capabilities()['native_bl5_material_domain']
        assert identities(owner)[1]=='B3_GE_NATIVE_FIBRE_BL5_MIXED_SHELL_J2_DISPLACEMENT_V1_DEV'
        metadata,arrays=decode_snapshot(owner,saved)
        assert len(arrays['s3_states'])==2*len(owner._definition.shell.s3_elements)
        for opts in (dict(increment_control=ss.AdaptiveIncrementControl()),dict(displacement_control=replace(CONTROL,trial_policy=ss.GENERALIZED_BRANCH_EVENT_TRIAL))):
            options=dict(displacement_control=CONTROL,**OPTIONS);options.update(opts)
            with pytest.raises(ValueError):owner.solve(ACTIONS,TARGETS[2:],**options)
            assert owner.checkpoint()==saved
        corrupt=ss.create_analysis(definition=model)
        try:
            with pytest.raises(ValueError):corrupt.restore(saved[:-1]+bytes((saved[-1]^1,)))
            assert corrupt._finite_driver is None
        finally:corrupt.close()
        assert owner.checkpoint()==saved
        token=CancellationToken();driver=owner._finite_driver;original=driver._advance
        def cancel_candidate(*args,**kwargs):
            candidate=original(*args,**kwargs);token.cancel('owned candidate before material/publication');return candidate
        with monkeypatch.context() as patch:
            patch.setattr(driver,'_advance',cancel_candidate)
            with pytest.raises(SolveCancelled):owner.solve(ACTIONS,TARGETS[2:],displacement_control=CONTROL,cancellation_token=token,**OPTIONS)
        assert owner.checkpoint()==saved
        final=owner.solve(ACTIONS,TARGETS[2:],displacement_control=CONTROL,**OPTIONS)
        resumed=fresh.solve(ACTIONS,TARGETS[2:],displacement_control=CONTROL,**OPTIONS)
        assert final.status==resumed.status=='completed' and owner.checkpoint()==fresh.checkpoint()
        assert final.free_equilibrium_ratio<=1e-8 and final.constraint_max<=1e-9
        (tmp_path/'result.json').write_text(json.dumps(dict(shell=owner._definition.shell.s3_elements,generation=final.generation,shell_alpha=final.shell_layer_alpha,fibre_alpha=final.beam_station_accumulated,relative=final.free_equilibrium_ratio,gap=final.constraint_max)))
    finally:fresh.close();owner.close()


def test_yielded_assembled_tangent_and_material_capture(loaded,tmp_path):
    model,saved=loaded;owner=ss.create_analysis(definition=model);owner.restore(saved);driver=owner._finite_driver
    state=driver._state;shell=driver._shell_predecessors;beam=driver._beam_predecessors
    applied=owner.recover().applied_dead_load
    base=driver._assemble(state,0.,shell,beam,applied_load=applied)
    direction=np.zeros(base[1].shape[0]);direction[owner._free]=np.linspace(-1.,1.,len(owner._free))*1e-6
    direction[len(state.q):]=np.linspace(-1.,1.,len(state.multipliers))
    for j in range(len(owner._beam_parts)):
        offset=owner._shell_count+6*len(owner._beam_ids)+24*j
        direction[offset+6:offset+24]=np.linspace(-1.,1.,18)
    captured=driver._q4_boundary_trial[3]
    assert len(captured)==len(shell)
    exact=base[1]@direction;errors=[];strain_errors=[]
    for h in (1e-5,1e-6):
        plus=driver._advance(state,direction,h);minus=driver._advance(state,direction,-h)
        ep=driver._assemble(plus,0.,shell,beam,applied_load=applied)
        em=driver._assemble(minus,0.,shell,beam,applied_load=applied)
        errors.append(float(np.linalg.norm((ep[0]-em[0])/(2*h)-exact)/max(np.linalg.norm(exact),1.)))
        for i,(slots,trial) in enumerate(captured):
            deriv=(ep[4][i]['layer_strain']-em[4][i]['layer_strain'])/(2*h)
            expected=np.asarray(trial.strain_differential)@direction[list(slots)]
            strain_errors.append(float(np.linalg.norm(deriv-expected)/max(np.linalg.norm(expected),1e-12)))
    assert max(errors)<=1e-5,errors
    assert max(strain_errors)<=1e-5,strain_errors
    from anysolver._stiffened_shell_s3_material_event import boundary_amount
    from anysolver._stiffened_shell_q4_material_event import boundary_amount as q4_boundary
    for slots,trial in captured:
        function=boundary_amount if len(slots)==18 else q4_boundary
        assert function(trial,np.zeros(len(slots)),origin=trial.origin) is None
        with pytest.raises(ValueError):function(trial,np.zeros(17),origin=trial.origin)
        with pytest.raises(ValueError):function(trial,np.zeros(len(slots)),origin=dict(trial.origin))
        if len(slots)==18:
            changed=dict(trial.origin);changed['initial_generalized_prestrain']=np.asarray(changed['initial_generalized_prestrain']).copy();changed['initial_generalized_prestrain'][0,0]+=1e-6
            from anysolver._stiffened_shell_q4_material_event import _origin_values
            assert _origin_values(changed)!=trial.origin_values
    assert owner.checkpoint()==saved
    owner.close()
    (tmp_path/'tangent.json').write_text(json.dumps(dict(errors=errors,strain_errors=strain_errors,criterion=1e-5)))

@pytest.mark.parametrize('shell',('s3','mixed'))
def test_distinct_policy_preserves_legacy_guards(shell):
    model=definition(shell)
    for policy in (ss.BL5_NATIVE_FIBRE_MATERIAL_V1,ss.BL5_ELASTIC_NATIVE_FIBRE_MIXED_SHELL_V1):
        with pytest.raises(ValueError):ss.create_analysis(definition=replace(model,bl5_material_policy=policy))
    with pytest.raises(ValueError):ss.create_analysis(definition=replace(model,shell=replace(model.shell,j2_curve=None)))
