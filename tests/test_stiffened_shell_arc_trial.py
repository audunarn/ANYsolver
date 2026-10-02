"""Local continuation mechanics; no public or mesh-uniform qualification."""
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._stiffened_shell_arc_metric import PhysicalChordMetric
from anysolver._stiffened_shell_displacement_corrector import bordered_path_correction


def test_physical_chord_gradient_units_frame_and_ownership():
    weights=np.array([.2,.8]);metric=PhysicalChordMetric(weights,2.)
    weights[:]=9.
    with pytest.raises(ValueError):metric.weights.setflags(write=True)
    reference=np.array([rotation([.2,.1,-.3]),rotation([-.3,.2,.1])])
    frames=np.array([rotation([.1,-.2,.15])@r for r in reference])
    u=np.array([[.04,-.01,.02],[-.02,.03,.05]])
    du=np.array([[.2,.1,-.1],[-.1,.3,.2]])
    spin=np.array([[.3,-.2,.4],[.2,.1,-.3]])
    value,gt,gr=metric.evaluate(u,frames,reference)
    predicted=np.sum(gt*du)+np.sum(gr*spin)
    h=1e-5
    def changed(amount):
        return metric.evaluate(u+amount*du,
            np.array([rotation(amount*v)@r for v,r in zip(spin,frames)]),reference)[0]
    assert (changed(h)-changed(-h))/(2*h)==pytest.approx(predicted,rel=1e-8)
    basis=rotation([.5,-.1,.2])
    assert metric.evaluate(u@basis.T,basis@frames,basis@reference)[0]==pytest.approx(value,rel=1e-13)
    assert PhysicalChordMetric([.2,.8],2000.).evaluate(u*1000.,frames,reference)[0]==pytest.approx(value)
    with pytest.raises(ValueError,match='pi/2'):
        metric.evaluate(u,np.array([rotation([2.,0,0])@r for r in reference]),reference)


def test_general_border_at_fold_keeps_algebraic_equilibrium():
    # Singular physical stiffness plus an independent indefinite algebraic block.
    matrix=sparse.csc_matrix([[0.,0.,0.],[0.,0.,1.],[0.,1.,0.]])
    residual=np.array([-.4,2.,-3.]);pattern=np.array([1.,0.,0.])
    row=np.array([.6,0.,0.])
    step,load=bordered_path_correction(matrix,residual,pattern,row,-.12,np.arange(3))
    np.testing.assert_allclose(matrix@step-load*pattern,-residual,atol=1e-15)
    assert row@step==pytest.approx(.12)


def test_native_arc_trial_preserves_accepted_owner(request,tmp_path):
    from test_stiffened_shell_bl5_coupled_material import coupled
    from test_stiffened_shell_bl5_material import make
    from test_stiffened_shell_bl5_finite import _action
    from anysolver._stiffened_shell_arc_trial import correct,select_trial
    from anysolver.control import CancellationToken,SolveCancelled
    owner=make(request,coupled())
    seed=(Path(__file__).parent/'data/stiffened_shell_event_excursion/force-seed.bin').read_bytes()
    owner.restore(seed);driver=owner._finite_driver
    count=len(owner._shell_ids)+len(owner._beam_ids)
    metric=PhysicalChordMetric(np.full(count,1/count),owner._reference_length)
    args=dict(load_direction=driver._load(_action(-15.625)).copy(),metric=metric,
        radius=1e-5,predictor_dof=owner._shell_count+6*owner._beam_index[105]+2,orientation=-1)
    import json
    records=[];attempts=[]
    try:
        selected=select_trial(driver,**args,iteration_records=records,attempt_records=attempts)
        result=selected.trial
    finally:
        from dataclasses import asdict
        (tmp_path/'iterations.json').write_text(json.dumps(records,indent=2))
        (tmp_path/'attempts.json').write_text(json.dumps([asdict(row) for row in attempts],indent=2))
    assert selected.requested_radius==1e-5
    assert attempts[0].radius==1e-5 and not attempts[0].accepted
    assert result.radius<selected.requested_radius
    assert attempts[-1].accepted and attempts[-1].radius==result.radius
    assert result.evaluation[2]<=1e-8 and result.evaluation[3]<=1e-9
    assert abs(result.path_error)<=1e-9
    assert result.predecessor_state is driver._state
    assert result.shell_predecessor is driver._shell_origins
    assert result.beam_predecessor is driver._beam_origins
    np.testing.assert_array_equal(result.load_direction,args['load_direction'])
    args['load_direction'][:]=0.
    assert np.any(result.load_direction)
    for array in (result.base_load,result.load_direction,result.normal_translations,result.normal_spins):
        with pytest.raises(ValueError):array.setflags(write=True)
    assert owner.checkpoint()==seed
    token=CancellationToken();token.cancel('before trial')
    args['load_direction']=driver._load(_action(-15.625))
    with pytest.raises(SolveCancelled):correct(driver,**args,cancellation_token=token)
    assert owner.checkpoint()==seed
