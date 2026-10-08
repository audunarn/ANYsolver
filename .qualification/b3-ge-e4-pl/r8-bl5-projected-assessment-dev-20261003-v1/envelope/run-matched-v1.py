"""Changed-wheel coarse matched case, not replay of an unchanged campaign."""
from pathlib import Path
import importlib.util, os, sys
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
old=Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2';name='ns16_b1'
m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_owner_dev.py'),'--case',name,'--site',str(old/'site'),'--wheel',str(old/'dist/anysolver-0.4.7-py3-none-any.whl'),'--source',str(REPO),'--registration',str(ROOT/'registrations'/name/'registration-v1.json'),'--output',str(ROOT/'owners'/name/'owner-v1')],'owner-'+name+'-v1',1024**3)
