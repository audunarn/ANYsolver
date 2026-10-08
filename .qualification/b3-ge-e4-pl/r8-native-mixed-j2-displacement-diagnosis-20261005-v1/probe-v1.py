"""One decision-oriented actual-update discriminator; no state acceptance."""
from pathlib import Path
from dataclasses import asdict
import hashlib, json, os, sys
import numpy as np
from threadpoolctl import threadpool_info
import anysolver
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_displacement_corrector import DisplacementCorrectorFailure
import anysolver._stiffened_shell_displacement_corrector as corrector
from test_stiffened_shell_native_plastic_s3_displacement import definition

root=Path(__file__).resolve().parent;repo=root.parents[2]
assert Path(anysolver.__file__).resolve().is_relative_to(repo/'src')
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert all(p['num_threads']==1 for p in threadpool_info())
model=definition(True,True)
reference=ss.create_analysis(definition=model);owner=ss.create_analysis(definition=model)
options=dict(max_iterations=20,max_backtracks=12)
actions=(ss.NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),)
direction=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),)
record=dict(scope='Mixed fixed-target failure discriminator; no qualification',
            source_parent='189ebb84',pools=threadpool_info(),jit_disabled=True)
out=root/'result-v1.json'
def write():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
    linear=reference.solve_linear(actions)
    target=float(linear.beam_coordinates[6*reference._beam_index[105]+2])*1.01
    owner.solve((ss.NodalAction('beam',105,(0.,0.,0.,0.,0.,0.)),),(1.,),**options)
    saved=owner.checkpoint();(root/'accepted-zero.checkpoint').write_bytes(saved)
    driver=owner._finite_driver;predecessor=driver._state
    shell=driver._shell_origins;beam=driver._beam_origins
    pattern=driver._load(direction);norm=float(pattern@pattern)
    original_assemble=driver._assemble;original_advance=driver._advance
    original_border=corrector.bordered_correction
    trajectory=[];last={}
    def branch(evaluation):
        return tuple(tuple(np.asarray(state['alpha'])>np.asarray(parent['alpha']))
                     for state,parent in zip(evaluation[4],shell,strict=True))
    def observed(state,*args,**kwargs):
        evaluation=original_assemble(state,*args,**kwargs)
        load=kwargs['applied_load']
        trajectory.append(dict(amplitude=float(load@pattern/norm),
            control=float(state.q[ss.DisplacementControl('beam',105,2).dof(owner)]),
            equilibrium=float(evaluation[2]),gap=float(evaluation[3]),
            alpha=[float(np.max(s['alpha'])) for s in evaluation[4]]))
        return evaluation
    def advanced(state,step,amount):
        last.update(state=state,step=np.array(step,copy=True),amount=float(amount))
        return original_advance(state,step,amount)
    def bordered(*args):
        step,delta=original_border(*args)
        last['delta']=delta
        last['matrix']=args[0];last['residual']=args[1];last['load_column']=args[2]
        return step,delta
    driver._assemble=observed;driver._advance=advanced;corrector.bordered_correction=bordered
    try:
        owner.solve(direction,(target,),displacement_control=ss.DisplacementControl('beam',105,2),**options)
        raise AssertionError('Frozen failure did not reproduce; inspect changed dependencies')
    except DisplacementCorrectorFailure as failure:
        record['failure']=dict(message=str(failure),detail=asdict(failure.detail))
    finally:
        driver._assemble=original_assemble;driver._advance=original_advance
        corrector.bordered_correction=original_border
    record['trajectory']=trajectory;record['target']=target
    assert owner.checkpoint()==saved and driver._state is predecessor
    state=last['state'];step=last['step'];delta=last['delta']
    amplitude=record['failure']['detail']['amplitude']
    evaluation=original_assemble(state,0.,shell,beam,applied_load=amplitude*pattern)
    residual,tangent=evaluation[:2];count=owner._K.shape[0]
    free=np.r_[owner._free,np.arange(count,tangent.shape[0])]
    energy=float(np.max((abs(owner._K)@owner._coordinate_scale)*owner._coordinate_scale))
    weights=np.r_[owner._coordinate_scale,energy/owner._constraint_scale]/energy
    column=np.r_[pattern,np.zeros(tangent.shape[0]-count)]
    predicted=tangent@step-column*delta
    weighted=residual[free]*weights[free];old=float(np.linalg.norm(weighted))
    floor=max(float(np.linalg.norm(predicted[free]*weights[free]))*1e-10,np.finfo(float).tiny)
    record['limiting']=dict(merit=old,equilibrium=float(evaluation[2]),gap=float(evaluation[3]),
        scaled_step_norm=float(np.linalg.norm(step[:count]/owner._coordinate_scale)),
        delta=delta,solve_relative_defect=float(np.linalg.norm((predicted+residual)[free]*weights[free])/
        max(np.linalg.norm(residual[free]*weights[free]),np.finfo(float).tiny)),
        predicted_merit_slope=float(weighted@(predicted[free]*weights[free])/max(old,np.finfo(float).tiny)))
    derivatives=[]
    for magnitude in (1e-4,1e-5,1e-6):
        positive=original_assemble(original_advance(state,step,magnitude),0.,shell,beam,
            applied_load=(amplitude+magnitude*delta)*pattern)
        negative=original_assemble(original_advance(state,step,-magnitude),0.,shell,beam,
            applied_load=(amplitude-magnitude*delta)*pattern)
        observed=(positive[0]-negative[0])/(2*magnitude)
        blocks={}
        for name,start,end in (('shell',0,owner._shell_count),('native',owner._shell_count,count),
                               ('constraints',count,len(residual))):
            rows=np.arange(start,end);rows=rows[np.isin(rows,free)]
            norm_pred=float(np.linalg.norm(predicted[rows]*weights[rows]))
            blocks[name]=dict(relative_error=float(np.linalg.norm((observed-predicted)[rows]*weights[rows])/
                             max(norm_pred,floor)),predicted_norm=norm_pred)
        derivatives.append(dict(magnitude=magnitude,blocks=blocks,
            branch_same=branch(positive)==branch(negative)==branch(evaluation),
            observed_merit_slope=float(weighted@(observed[free]*weights[free])/max(old,np.finfo(float).tiny))))
    record['derivatives']=derivatives
    trials=[]
    for magnitude in (1.,.5,2.**-6,2.**-12):
        response=original_assemble(original_advance(state,step,magnitude),0.,shell,beam,
            applied_load=(amplitude+magnitude*delta)*pattern)
        trials.append(dict(amount=magnitude,merit=float(np.linalg.norm(response[0][free]*weights[free])),
            equilibrium=float(response[2]),gap=float(response[3]),branch_same=branch(response)==branch(evaluation)))
    record['limiting_trials']=trials
    np.savez_compressed(root/'limiting-state-v1.npz',q=state.q,frames=state.frames,cells=state.cells,
        resultants=state.resultants,multipliers=state.multipliers,step=step,residual=residual,
        pattern=pattern,weights=weights,free=free)
    assert owner.checkpoint()==saved and driver._state is predecessor
    record['accepted_prefix_unchanged']=True;record['exit_code']=0
    write();print(json.dumps(dict(failure=record['failure'],limiting=record['limiting'],
        derivatives=derivatives,limiting_trials=trials)),flush=True)
finally:reference.close();owner.close()
