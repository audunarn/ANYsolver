from pathlib import Path
import hashlib
import importlib.util
import os
import sys

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
if hashlib.sha256(p.read_bytes()).hexdigest()!='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':raise ValueError('pinned supervisor required')
spec=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
if sys.argv[1]=='test':
    m.supervise([sys.executable,'-m','pytest','-q',str(REPO/'tests/test_r8_bl5_envelope_gram_dev.py'),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')],'test-v1',1024**3)
elif sys.argv[1]=='case':
    import json
    b=json.loads((ROOT/'bindings-v1.json').read_text())
    if hashlib.sha256((ROOT/'probe-v1.py').read_bytes()).hexdigest()!=b['driver_sha256']:raise ValueError('reviewed driver differs')
    m.supervise([sys.executable,'-u',str(ROOT/'probe-v1.py')],'ns32_b2-v1',2*1024**3)
else:raise ValueError(sys.argv[1])
