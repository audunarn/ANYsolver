from pathlib import Path
import os,sys,json,traceback
import numpy,scipy,numba,llvmlite,anysolver,psutil,pytest
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
SITE=Path(os.environ['ANYSOLVER_PORT_INSTALLED']).resolve();CI=ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'

def runtime():
    imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
    assert all(Path(p).is_relative_to(SITE) for p in imports.values())
    for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
        assert Path(m.__file__).resolve().is_relative_to(CI.resolve()) and m.__version__==v
    assert all(p['num_threads']==1 for p in threadpool_info())
    assert psutil.Process().cpu_affinity()==[0] and numba.config.DISABLE_JIT and numba.get_num_threads()==1
    return dict(imports=imports,dependencies={m.__name__:dict(path=m.__file__,version=m.__version__) for m in (numpy,scipy,numba,llvmlite)},pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_off=bool(numba.config.DISABLE_JIT),numba_threads=numba.get_num_threads())
status='PRE_RHS';error=None
try:
    (ROOT/'runtime-preflight.json').write_text(json.dumps(runtime(),indent=2)+'\n')
    code=pytest.main(['-q','-o','pythonpath=','-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-new-v1'),'--junitxml='+str(ROOT/'junit-v1.xml'),str(REPO/'tests/test_r8_bl5_body_port_twofold_workflow.py')])
    if code:raise RuntimeError('focused consumer checks failed before any specimen RHS')
    from scripts import r8_bl5_body_port_twofold_workflow as w
    saved=w.original.load_saved(os.environ['ANYSOLVER_PORT_SAVED']);prepared=w.original.prepare(saved)
    owner,loads,rigid,preflight=prepared
    oldpath=ROOT.parent/'r8-bl5-body-port-dev-20261006-v1/results-v2/probe/preflight.json'
    prior=json.loads(oldpath.read_text())
    assert loads.tolist()==prior['full_native_physical_load_covector'], 'same failed original native RHS required'
    assert preflight==prior, 'unchanged prepared density/rigid/common-wrench prerequisites required'
    numpy.savez(ROOT/'prepared-original-operators.npz',K_data=owner._K.data,K_indices=owner._K.indices,K_indptr=owner._K.indptr,K_shape=owner._K.shape,C_data=owner._C.data,C_indices=owner._C.indices,C_indptr=owner._C.indptr,C_shape=owner._C.shape,load=loads,rigid=rigid,scale=owner._coordinate_scale,fixed=owner._fixed)
    (ROOT/'runtime-before-RHS.json').write_text(json.dumps(runtime(),indent=2)+'\n')
    status='BODY_RHS_STARTED'
    result=w.run(saved,prepared,ROOT/'results-v1');status=result['status']
except BaseException as exc:
    error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());raise
finally:
    (ROOT/'runtime-final.json').write_text(json.dumps(dict(status=status,error=error,**runtime()),indent=2)+'\n')

