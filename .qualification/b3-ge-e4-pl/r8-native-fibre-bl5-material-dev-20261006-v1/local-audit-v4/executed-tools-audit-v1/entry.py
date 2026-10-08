from pathlib import Path
import json, os, sys
import numpy, scipy, numba, llvmlite, psutil, anysolver
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;EVIDENCE=ROOT.parent
phase=os.environ['LOCAL_AUDIT_PHASE'];folder=ROOT/phase
CI=EVIDENCE.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2';SITE=(EVIDENCE/'installed-wheel-v1').resolve()
dependencies={m.__name__:dict(path=str(Path(m.__file__).resolve()),version=m.__version__) for m in (numpy,scipy,numba,llvmlite)}
(folder/'dependency-preflight.json').write_text(json.dumps(dependencies,indent=2))
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve()),dependencies
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
assert len(psutil.Process().cpu_affinity())==1 and numba.config.DISABLE_JIT and numba.get_num_threads()==1
assert all(p['num_threads']==1 for p in threadpool_info())
import audit
try:
    result=audit.execute(folder,EVIDENCE)
    print(json.dumps(dict(status=result['status'],local_calls=result['local_audit_responses'],
        smooth=[dict(family=r['family'],error=r['smooth_relative_error'],pass_=r['smooth_pass']) for r in result['results']])))
    if result['status']!='completed':raise AssertionError('unchanged local smooth criterion failed')
finally:
    modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
        if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
    assert all(Path(p).is_relative_to(SITE) for p in modules.values())
    assert all(p['num_threads']==1 for p in threadpool_info())
    (folder/'runtime.json').write_text(json.dumps(dict(dependencies=dependencies,imports=modules,
        pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT)),indent=2)+'\n')
