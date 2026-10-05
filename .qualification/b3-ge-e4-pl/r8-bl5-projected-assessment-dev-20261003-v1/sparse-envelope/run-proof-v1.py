from pathlib import Path
import importlib.util,os,sys
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
case=sys.argv[1]
if case not in ('whole_half','whole_double'):raise ValueError('exact saved reciprocal only')
saved=Path(os.environ['TEMP'])/'r8-bl5-projected-offratio-dev-v1'/case
out=ROOT/(case+'-saved-proof-v1');out.mkdir(exist_ok=False)
m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_sparse_kernel_saved_dev.py'),'--owner',str(saved/'owner-v1'),'--kernel',str(saved/'kernel-v1.json'),'--output',str(out/'assessment.json')],case+'-proof-job-v1',1024**3)
