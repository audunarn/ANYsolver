"""Bounded serial continuation; never overwrites original evidence."""
from pathlib import Path
import importlib.util, os, sys, json, hashlib
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
if sys.argv[1]=='register':
 for name in ('ns64_b4','ns64_b8'):
  folder=ROOT/'registrations'/name
  m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_norm_dev.py'),'--fixture-case',name,'--reference','exact_uniform','--output',str(folder/'registration-v2.json')],'register-'+name+'-v2',1024**3)
elif sys.argv[1]=='owners':
 old=Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2'
 # These three missing coarse cases complete the seven-ratio physical screen
 # together with four existing coarse records; no unchanged case is rerun.
 for name in ('ns16_b1_4','ns16_b4','ns16_b8'):
  m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_owner_dev.py'),'--case',name,'--site',str(old/'site'),'--wheel',str(old/'dist/anysolver-0.4.7-py3-none-any.whl'),'--source',str(REPO),'--registration',str(ROOT/'registrations'/name/'registration-v1.json'),'--output',str(ROOT/'owners'/name/'owner-v1')],'owner-'+name+'-v1',1024**3)
else:raise ValueError(sys.argv[1])
