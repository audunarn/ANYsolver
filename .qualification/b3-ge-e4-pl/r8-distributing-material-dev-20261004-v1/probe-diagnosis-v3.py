"""Discriminate fixed-predecessor derivative defect from force-route failure."""
from pathlib import Path
import hashlib, json, os, sys
import numpy as np
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info
from test_stiffened_shell_ge_distributing_material import definition, actions
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info(); assert pools and all(p['num_threads']==1 for p in pools)
original=FinitePointDriver._assemble; original_advance=FinitePointDriver._advance
records=[]; last=None; base_capture=None
def observed(self,state,factor,shell_origins,beam_origins,**kwargs):
    global last
    value=original(self,state,factor,shell_origins,beam_origins,**kwargs)
    last=(self,state,factor,shell_origins,beam_origins,kwargs,value)
    records.append(dict(factor=factor,relative=value[2],gap=value[3],
        shell_alpha=max(float(np.max(v['alpha'])) for v in value[4])))
    return value
FinitePointDriver._assemble=observed
def observed_advance(self,state,direction,alpha):
    global base_capture
    if alpha==1.:
        assert last is not None and last[0] is self and last[1] is state
        base_capture=(last,direction.copy())
    return original_advance(self,state,direction,alpha)
FinitePointDriver._advance=observed_advance
owner=ss.create_analysis(definition=definition())
failure=None
try:
    try: owner.solve(actions(),(.25,.5,.75,1.),max_iterations=20,max_backtracks=12)
    except ss.FiniteIncrementFailure as error: failure=error.attempt.__dict__
    FinitePointDriver._assemble=original; FinitePointDriver._advance=original_advance
    driver,state,factor,shell_origins,beam_origins,kwargs,value=base_capture[0]
    residual,matrix=value[:2]
    free=np.r_[owner._free,np.arange(owner._K.shape[0],matrix.shape[0])]
    direction=base_capture[1]
    weights=np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])]
    linear_error=(matrix@direction+residual)[free]*weights[free]
    linear_relative=float(np.linalg.norm(linear_error)/np.linalg.norm(residual[free]*weights[free]))
    candidates=[]
    for alpha in (1.,2.**-8,2.**-12,2.**-13,2.**-14,2.**-15,2.**-16):
        changed=original(driver,driver._advance(state,direction,alpha),factor,shell_origins,beam_origins,**kwargs)
        candidates.append(dict(alpha=alpha,relative=changed[2],gap=changed[3],
            weighted_norm=float(np.linalg.norm(changed[0][free]*weights[free])),
            predicted_norm=float(np.linalg.norm((residual+alpha*(matrix@direction))[free]*weights[free]))))
    fd={}
    before=owner.checkpoint()
    (ROOT/'failed-prefix-v3.bin').open('xb').write(before)
    with (ROOT/'failed-base-v3.npz').open('xb') as handle:
        np.savez(handle,q=state.q,frames=state.frames,cells=state.cells,
            resultants=state.resultants,multipliers=state.multipliers,
            direction=direction,residual=residual,pattern=kwargs['pattern'],
            matrix_data=matrix.data,matrix_indices=matrix.indices,matrix_indptr=matrix.indptr,
            matrix_shape=np.array(matrix.shape))
    for label in ('newton','shell','beam'):
        vector=direction.copy()
        if label=='shell': vector[owner._shell_count:]=0.
        elif label=='beam': vector[:owner._shell_count]=0.;vector[owner._K.shape[0]:]=0.
        predicted=(matrix@vector)*weights; norm=float(np.linalg.norm(predicted)); measures=[]
        for h in (1e-4,1e-5,1e-6):
            plus=original(driver,driver._advance(state,vector,h),factor,shell_origins,beam_origins,**kwargs)
            minus=original(driver,driver._advance(state,vector,-h),factor,shell_origins,beam_origins,**kwargs)
            observed_derivative=(plus[0]-minus[0])/(2*h)*weights
            measures.append(dict(h=h,relative=float(np.linalg.norm(observed_derivative-predicted)/max(norm,np.finfo(float).tiny)),
                predicted_norm=norm,observed_norm=float(np.linalg.norm(observed_derivative)),
                plus_alpha=max(float(np.max(v['alpha'])) for v in plus[4]),
                minus_alpha=max(float(np.max(v['alpha'])) for v in minus[4])))
        fd[label]=measures
    assert owner.checkpoint()==before
    sources={str(p.relative_to(REPO)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (REPO/'tests/test_stiffened_shell_ge_distributing_material.py',
                  REPO/'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
                  REPO/'src/anysolver/_stiffened_shell_q4_algorithmic_pullback.py')}
    result=dict(scope='development derivative diagnosis; failed prefix preserved, no qualification',
        sources=sources,pools=pools,failure=failure,generation=owner._generation,
        trajectory=records,last_factor=factor,last_relative=value[2],fd=fd,
        linear_relative=linear_relative,candidates=candidates)
    result['anchor']='Actual failing base and original driver spsolve correction'
    result['snapshots']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('failed-prefix-v3.bin','failed-base-v3.npz')}
    (ROOT/'diagnosis-v3.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(linear_relative=linear_relative,candidates=candidates),allow_nan=False))
finally:
    FinitePointDriver._assemble=original;FinitePointDriver._advance=original_advance;owner.close()
