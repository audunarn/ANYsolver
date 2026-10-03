"""One supervised numerical child at a time, shared600s/1GiB process tree."""
from pathlib import Path
import importlib.util,os,sys
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
if sys.argv[1]=='test':
 m.supervise([sys.executable,'-m','pytest','-q',str(REPO/'tests/test_r8_bl5_sparse_envelope_kernel_dev.py'),str(REPO/'tests/test_r8_bl5_sparse_kernel_saved_dev.py'),str(REPO/'tests/test_r8_bl5_sparse_kernel_interval_dev.py'),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v6')],'test-v6',1024**3)
elif sys.argv[1]=='bind':
 m.supervise([sys.executable,str(ROOT/'bind-smoke-v3.py')],'bind-smoke-v3',1024**3)
elif sys.argv[1]=='incidence':
 m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_sparse_envelope_kernel_dev.py'),'--case','ns16_b8','--owner',str(REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/envelope/owners/ns16_b8/owner-v1'),'--output',str(ROOT/'ns16_b8/incidence-v1.json'),'--stationary-bound','incidence','--precision','100'],'ns16_b8-incidence-v1',1024**3)
elif sys.argv[1]=='precision':
 m.supervise([sys.executable,str(ROOT/'probe-representative-v2.py')],'representative-precision100-v2',1024**3)
else:raise ValueError(sys.argv[1])
