import json
from dataclasses import replace
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.sparse.linalg import spsolve
from anysolver._stiffened_shell_ge_experimental import ExperimentalGEAnalysis
from test_stiffened_shell_ge_finite_experimental import _q4_shell_j2_panel, _actions
base = _q4_shell_j2_panel()
d = replace(base, shell=replace(base.shell,q4_elements=(),s3_elements=((1,2,5),(1,5,4),(2,3,6),(2,6,5))))
first=ExperimentalGEAnalysis(d); accepted=first.solve(_actions(),(.5,),max_iterations=20,max_backtracks=12)
raw=first.checkpoint()
for mode in ('baseline','rebase'):
    o=ExperimentalGEAnalysis(d); o.restore(raw)
    if mode=='rebase': o.rebase_rotations(o.recover().generation)
    driver=o._finite_driver; state=driver._state; args=(.55,driver._shell_origins,driver._beam_origins)
    r,k,*_=driver._assemble(state,*args)
    n=o._K.shape[0]; free=np.r_[o._free,np.arange(n,k.shape[0])]
    delta=np.zeros(k.shape[0]); delta[free]=spsolve(k[free,:][:,free],-r[free])
    for position in (0., .37):
        trial=driver._advance(state,delta,position); rr,kk,*_=driver._assemble(trial,*args)
        for h in (1e-5,1e-6):
            rp=driver._assemble(driver._advance(trial,delta,h),*args)[0]
            rm=driver._assemble(driver._advance(trial,delta,-h),*args)[0]
            error=(rp-rm)/(2*h)-kk@delta
            print(json.dumps({'mode':mode,'at':position,'h':h,'tangent_error':float(np.linalg.norm(error[free])/np.linalg.norm((kk@delta)[free]))}))
    original=driver._assemble; records=[]
    def tracked(*a,**kw):
        out=original(*a,**kw);records.append([out[2],out[3]]);return out
    driver._assemble=tracked
    try:
        result=o.solve(_actions(),(.55,),max_iterations=20,max_backtracks=12)
        status='completed'
    except RuntimeError as e: status=str(e)
    print(json.dumps({'mode':mode,'status':status,'checks':len(records),'last':records[-14:], 'shell_alpha':max(max(v) for v in accepted.shell_layer_alpha),'beam_alpha':max(max(v) for v in accepted.beam_station_accumulated)}))
