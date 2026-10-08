from dataclasses import asdict
from pathlib import Path
import hashlib, json, os, sys, traceback
import numpy as np, numba
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver import _stiffened_shell_ge_finite_experimental as finite
from test_stiffened_shell_ge_footprint_gravity import _definition
root=Path(os.environ['TASK_EVIDENCE'])
def write(name,value):
    (root/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf8')
def angle(matrices):
    return float(np.max(np.arccos(np.clip((np.trace(matrices,axis1=-2,axis2=-1)-1)/2,-1,1)),initial=0.))
runtime={'python':sys.executable,'pools':threadpool_info(),'numba_threads':numba.get_num_threads(),'numba_disable_jit':numba.config.DISABLE_JIT,'pid':os.getpid()}
write('runtime.json',runtime);print(json.dumps(runtime),flush=True)
write('inputs.json',{'only':False,'targets':[.1,.2],'max_iterations':20,'max_backtracks':12,'acceleration_m_s2':[0.,0.,-9.81],'source_hashes':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['src/anysolver/_stiffened_shell_ge_body_load.py','src/anysolver/_stiffened_shell_ge_experimental.py','tests/test_stiffened_shell_ge_footprint_gravity.py']}})
owner=ss.create_analysis(definition=_definition(only=False))
load=ss.GEBodyLoad(owner.preflight()['identity'],(0.,0.,-9.81))
original=finite.FinitePointDriver._assemble
records=[];last={};driver_seen=None

def observed(self,state,factor,*args,**kwargs):
    global driver_seen,last
    driver_seen=self
    result=original(self,state,factor,*args,**kwargs)
    residual,matrix,relative,gap,*_=result
    applied=self._external_at(state,factor)[0]
    free=owner._free;rr=residual[free];ff=applied[free];scale=owner._coordinate_scale[free]
    active=ff!=0.
    ratios=np.zeros(len(free));ratios[active]=np.abs(rr[active]/ff[active])
    worst=int(np.argmax(ratios))
    wr=rr*scale;wf=ff*scale;magnitude=max(float(np.max(np.abs(wr),initial=0.)),float(np.max(np.abs(wf),initial=0.)))
    global_ratio=float(np.linalg.norm(wr/magnitude)/np.linalg.norm(wf/magnitude)) if magnitude else 0.
    record={'evaluation':len(records)+1,'factor':float(factor),'relative':float(relative),'global_work_ratio':global_ratio,'active_ratio':float(ratios[worst]),'worst_active_primal_row':int(free[worst]),'worst_active_residual':float(rr[worst]),'worst_active_applied':float(ff[worst]),'gap':float(gap),'free_residual_max':float(np.max(np.abs(rr),initial=0.)),'constraint_raw_max':float(np.max(np.abs(residual[len(state.q):]),initial=0.)),'shell_translation_max':float(np.max(np.abs(state.q[:owner._shell_count].reshape(-1,6)[:,:3]),initial=0.)),'shell_coordinate_rotation_norm_max':float(np.max(np.linalg.norm(state.q[:owner._shell_count].reshape(-1,6)[:,3:],axis=1),initial=0.)),'beam_rotation_angle_max':angle(state.frames),'cell_rotation_angle_max':angle(state.cells),'q_norm':float(np.linalg.norm(state.q))}
    records.append(record)
    with (root/'evaluations.jsonl').open('a',encoding='utf8') as stream: stream.write(json.dumps(record)+'\n')
    last={'state':state,'residual':residual.copy(),'matrix':matrix.copy(),'applied':applied.copy()}
    return result
finite.FinitePointDriver._assemble=observed
outcome={'status':'running'}
try:
    answer=owner.solve(load,(.1,.2),max_iterations=20,max_backtracks=12)
    outcome={'status':'completed','generation':answer.generation,'accepted_factors':list(answer.accepted_factors)}
except finite.FiniteIncrementFailure as error:
    outcome={'status':'failed','exception':type(error).__name__,'message':str(error),'attempt':asdict(error.attempt)}
    traceback.print_exc()
except BaseException as error:
    outcome={'status':'unexpected_failure','exception':type(error).__name__,'message':str(error)}
    traceback.print_exc()
finally:
    outcome['observed_evaluations']=len(records)
    outcome['owner_generation']=owner._generation
    outcome['owner_retains_driver']=owner._finite_driver is not None
    outcome['accepted_factors']=[] if driver_seen is None else list(driver_seen._accepted_factors)
    outcome['accepted_prefix_checkpoint']=None
    if owner._finite_driver is not None:
        raw=owner.checkpoint();(root/'accepted-prefix.checkpoint').write_bytes(raw)
        outcome['accepted_prefix_checkpoint']=hashlib.sha256(raw).hexdigest()
    if last:
        state=last['state'];matrix=last['matrix'].tocsc()
        np.savez(root/'last-trial.npz',q=state.q,frames=state.frames,cells=state.cells,resultants=state.resultants,multipliers=state.multipliers,shell_anchors=state.shell_anchors,residual=last['residual'],applied=last['applied'],free=owner._free,fixed=owner._fixed,coordinate_scale=owner._coordinate_scale,constraint_scale=owner._constraint_scale,matrix_data=matrix.data,matrix_indices=matrix.indices,matrix_indptr=matrix.indptr,matrix_shape=matrix.shape)
        outcome['last_evaluation']=records[-1]
    write('result.json',outcome)
    print(json.dumps(outcome),flush=True)
    finite.FinitePointDriver._assemble=original
    owner.close()
raise SystemExit(0 if outcome['status']=='completed' else 1)
