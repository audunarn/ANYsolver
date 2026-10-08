from pathlib import Path
import importlib.util,os,sys,hashlib
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
if hashlib.sha256(p.read_bytes()).hexdigest()!='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':raise ValueError('pinned shared supervisor required')
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
mode=sys.argv[1]
if mode=='test':
 m.supervise([sys.executable,'-m','pytest','-q',str(REPO/'tests/test_r8_bl5_density_subspace_dev.py'),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')],'test-v1',1024**3)
elif mode in ('prepare','case'):
 m.supervise(([sys.executable,'-u',str(ROOT/'case-entry-v1.py')] if mode=='case' else [sys.executable,'-u',str(ROOT/'probe-v1.py'),mode]),mode+'-v1',2*1024**3)
else:raise ValueError(mode)
