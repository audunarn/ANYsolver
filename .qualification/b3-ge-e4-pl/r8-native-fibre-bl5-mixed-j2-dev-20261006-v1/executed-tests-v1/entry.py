from pathlib import Path
import hashlib,json,sys,traceback
import numpy,scipy,numba,llvmlite,psutil,anysolver
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;EVIDENCE=ROOT;REPO=ROOT.parents[2];folder=ROOT/__import__('os').environ['BOUNDARY_PHASE']
CI=EVIDENCE.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2';SITE=(REPO/'src').resolve()
dependencies={m.__name__:dict(path=str(Path(m.__file__).resolve()),version=m.__version__) for m in (numpy,scipy,numba,llvmlite)}
(folder/'dependency-preflight.json').write_text(json.dumps(dependencies,indent=2))
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve()),dependencies
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
assert len(psutil.Process().cpu_affinity())==1 and numba.config.DISABLE_JIT and numba.get_num_threads()==1
assert all(p['num_threads']==1 for p in threadpool_info())
try:
    import pytest
    status=pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(folder/'tmp'),str(REPO/'tests/test_native_fibre_bl5_mixed_j2_displacement.py')])
    (folder/'result.json').write_text(json.dumps(dict(pytest_exit_code=int(status))))
    if status:raise SystemExit(status)
except BaseException:
    (folder/'unexpected-failure.txt').write_text(traceback.format_exc());raise
finally:
    modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
    assert all(Path(p).is_relative_to(SITE) for p in modules.values())
    assert all(p['num_threads']==1 for p in threadpool_info())
    (folder/'runtime.json').write_text(json.dumps(dict(dependencies=dependencies,imports=modules,
        source_hashes={n:hashlib.sha256(Path(p).read_bytes()).hexdigest() for n,p in modules.items()},
        pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT)),indent=2)+'\n')
