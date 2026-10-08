from pathlib import Path
import importlib.util,os,sys,hashlib
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
if hashlib.sha256(p.read_bytes()).hexdigest()!='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':raise ValueError('pinned shared supervisor source required')
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
if sys.argv[1]=='test':
 m.supervise([sys.executable,'-m','pytest','-q',str(REPO/'tests/test_r8_bl5_sparse_gram_margin_dev.py'),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')],'test-v1',1024**3)
elif sys.argv[1]=='case':
 if hashlib.sha256((ROOT/'probe-v1.py').read_bytes()).hexdigest()!='4b92d6399e3b0ab5140ee4214bd86fbbbb6ce1a6674840a26483b143532eb051':raise ValueError('reviewed driver source differs')
 m.supervise([sys.executable,'-u',str(ROOT/'probe-v1.py')],'ns16_b8-v1',2*1024**3)
else:raise ValueError(sys.argv[1])
