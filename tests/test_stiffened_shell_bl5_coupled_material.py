"""Simultaneous shell J2/generalized beam history on experimental Q4 BL5."""
from dataclasses import replace
import numpy as np
import pytest
from anymaterial import DNVC208MaterialCurve
from anysolver import stiffened_shell as ss
from test_stiffened_shell_bl5_material import model, make
from test_stiffened_shell_bl5_finite import _action


def coupled(basis="p0"):
    base=model(basis,hardening=1e8)
    p=1e6
    curve=DNVC208MaterialCurve(p,1.05*p,1.1*p,.005,.01,4*p,.2)
    return replace(base,shell=replace(base.shell,j2_curve=curve),
                   bl5_material_policy=ss.BL5_COUPLED_J2_MATERIAL_V1)


def _coupled_history_roundtrip(request,monkeypatch,tmp_path,basis,*,reversal):
    from anysolver.control import CancellationToken,SolveCancelled
    from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
    definition=coupled(basis);a=make(request,definition)
    assert "shell J2 plastic" not in a.capabilities["excluded"]
    programme=ss.StagedDeadLoadProgramme(a.preflight()["identity"],
                                       (_action(500.),_action(-500. if reversal else 550.)))
    targets=(.5,1.,1.25,1.75,2.) if reversal else (.5,1.,2.);control=ss.AdaptiveIncrementControl(4,64)
    kwargs=dict(max_iterations=20,max_backtracks=12,increment_control=control)
    token=CancellationToken()
    def observe(result):
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        if result.load_position==1.:token.cancel("coupled accepted prefix")
    with pytest.raises(SolveCancelled):
        a.solve(programme,targets,on_accepted=observe,cancellation_token=token,**kwargs)
    result=a.recover();assert result.load_position==1.
    assert np.max(result.beam_station_accumulated)>0
    assert np.max(result.shell_layer_alpha)>0
    saved=a.checkpoint();b=make(request,definition);b.restore(saved)
    assert b.checkpoint()==saved
    for left,right in zip(result.shell_q4_material,b.recover().shell_q4_material):
        np.testing.assert_array_equal(left.alpha,right.alpha)
        np.testing.assert_array_equal(left.layer_stress,right.layer_stress)
    driver=a._finite_driver;state=driver._state
    def evaluate(trial):
        return driver._assemble(trial,1.,driver._shell_predecessors,
            driver._beam_predecessors,applied_load=result.applied_dead_load)
    residual,tangent,*_=evaluate(state);direction=np.zeros(len(residual))
    direction[:a._shell_count:6]=np.linspace(0.,1e-4,len(a._shell_ids))
    for i in range(len(a._beam_ids)):direction[a._shell_count+6*i+2]=.001*(i+1)
    direction[a._fixed]=0.;predicted=tangent@direction
    weights=np.r_[a._coordinate_scale,np.ones(a._C.shape[0])];errors=[]
    for h in (1e-4,1e-5,1e-6):
        plus=evaluate(driver._advance(state,direction,h))[0]
        minus=evaluate(driver._advance(state,direction,-h))[0]
        errors.append(np.linalg.norm(((plus-minus)/(2*h)-predicted)*weights)/
                      max(np.linalg.norm(predicted*weights),1.))
    assert min(errors)<=1e-5,errors
    original=FinitePointDriver._assemble
    def broken(self,*args,**kw):
        original(self,*args,**kw);raise RuntimeError("injected coupled trial")
    with monkeypatch.context() as patch:
        patch.setattr(FinitePointDriver,"_assemble",broken)
        with pytest.raises(RuntimeError,match="injected coupled"):
            a.solve(programme,targets,**kwargs)
    assert a.checkpoint()==saved
    a.rebase_rotations(result.generation)
    repeated=driver._assemble(driver._state,1.,driver._shell_origins,
        driver._beam_origins,applied_load=result.applied_dead_load)[4]
    for before,after in zip(result.shell_q4_material,repeated):
        np.testing.assert_allclose(before.layer_stress,after["layer_stress"],rtol=1e-10,atol=1e-7)
        np.testing.assert_allclose(before.layer_strain,after["layer_strain"],rtol=1e-10,atol=1e-12)
    b=make(request,definition);b.restore(a.checkpoint())
    from pathlib import Path
    from dataclasses import asdict
    import json
    evidence=tmp_path/"coupled-history"
    evidence.mkdir()
    (evidence/(basis+"-prefix.bin")).write_bytes(a.checkpoint())
    try:
        final=a.solve(programme,targets,**kwargs)
    except ss.AdaptiveIncrementExhausted as error:
        accepted=a.recover()
        (evidence/(basis+"-failure.json")).write_text(json.dumps(dict(
            attempts=[asdict(item) for item in error.attempts],
            accepted_factors=error.accepted_factors,
            load_position=accepted.load_position,
            applied_load_norm=float(np.linalg.norm(accepted.applied_dead_load)),
            tangent_errors=errors),indent=2))
        (evidence/(basis+"-failure-prefix.bin")).write_bytes(a.checkpoint())
        raise
    resumed=b.solve(programme,targets,**kwargs)
    assert final.load_programme_complete
    assert np.max(final.shell_layer_alpha)>np.max(result.shell_layer_alpha)
    assert np.max(final.beam_station_accumulated)>np.max(result.beam_station_accumulated)
    np.testing.assert_array_equal(final.shell_displacement,resumed.shell_displacement)
    assert a.checkpoint()==b.checkpoint()



@pytest.mark.parametrize("basis",("p0","continuous_p1_coarse"))
def test_coupled_bl5_history_roundtrip(request,monkeypatch,tmp_path,basis):
    # Full signed-history requirement remains separate and currently unresolved.
    _coupled_history_roundtrip(request,monkeypatch,tmp_path,basis,reversal=True)


def test_coupled_bl5_monotonic_lifecycle(request,monkeypatch,tmp_path):
    # A bounded lifecycle check, not a substitute for signed-history acceptance.
    _coupled_history_roundtrip(request,monkeypatch,tmp_path,"p0",reversal=False)


def test_coupled_native_retained_force_moment_scales_and_legacy_isolation(request):
    selected=make(request,coupled());legacy=make(request,model(hardening=1e8))
    assert selected.preflight()["identity"]!=legacy.preflight()["identity"]
    start=selected._shell_count+6*len(selected._beam_ids)
    length=selected._reference_length
    for i,definition in enumerate(selected._definition.beams):
        element,_=definition.instantiate()
        force=np.abs(element.section.elastic)[:3]@np.r_[np.ones(3),np.ones(3)/length]
        moment=np.abs(element.section.elastic)[3:]@np.r_[np.ones(3),np.ones(3)/length]
        actual=selected._coordinate_scale[start+24*i+6:start+24*i+24].reshape(6,3)
        np.testing.assert_array_equal(actual[:2],np.tile(force,(2,1)))
        np.testing.assert_array_equal(actual[2:],np.tile(moment,(4,1)))
        old=legacy._coordinate_scale[start+24*i+6:start+24*i+24]
        np.testing.assert_array_equal(old,np.tile(np.r_[force,moment],3))
    for bad in (replace(coupled(),bl5_material_policy=ss.BL5_GENERALIZED_MATERIAL_V1),
                replace(model(),bl5_material_policy=ss.BL5_COUPLED_J2_MATERIAL_V1)):
        with pytest.raises(ValueError):ss.create_analysis(definition=bad)
