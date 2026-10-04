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
original=FinitePointDriver._assemble
records=[]; last=None
def observed(self,state,factor,shell_origins,beam_origins,**kwargs):
    global last
    value=original(self,state,factor,shell_origins,beam_origins,**kwargs)
    last=(self,state,factor,shell_origins,beam_origins,kwargs,value)
    records.append(dict(factor=factor,relative=value[2],gap=value[3],
        shell_alpha=max(float(np.max(v['alpha'])) for v in value[4])))
    return value
FinitePointDriver._assemble=observed
owner=ss.create_analysis(definition=definition())
failure=None
try:
    try: owner.solve(actions(),(.25,.5,.75,1.),max_iterations=20,max_backtracks=12)
    except ss.FiniteIncrementFailure as error: failure=error.attempt.__dict__
    FinitePointDriver._assemble=original
    driver,state,factor,shell_origins,beam_origins,kwargs,value=last
    residual,matrix=value[:2]
    free=np.r_[owner._free,np.arange(owner._K.shape[0],matrix.shape[0])]
    direction=np.zeros(len(residual)); direction[free]=splu(matrix[free][:,free].tocsc()).solve(-residual[free])
    weights=np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])]
    fd={}
    before=owner.checkpoint()
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
        trajectory=records,last_factor=factor,last_relative=value[2],fd=fd)
    (ROOT/'diagnosis-v1.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(failure=failure,last_relative=value[2],fd=fd),allow_nan=False))
finally:
    FinitePointDriver._assemble=original;owner.close()
