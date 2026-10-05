"""Missing native physical cases only; serial, bounded, failed records retained."""
from pathlib import Path
import importlib.util, os, sys, json, hashlib
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
old=Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2'
ids=[f'ns{nx}_b{ratio}' for nx in (32,64) for ratio in ('1_8','1_4','1_2','1','2','4','8') if not (nx==32 and ratio=='1')]
state=dict(schema='MISSING_NATIVE_ENVELOPE_DEVELOPMENT_V1',case_order=ids,
 source_sha256=hashlib.sha256((REPO/'scripts/r8_bl5_projected_envelope_owner_dev.py').read_bytes()).hexdigest(),
 criteria='eligible fixed scalar bound, existing owner work1e-8/constraints1e-9/factor1/corrections6; no qualification',cases={})
manifest=ROOT/'native-campaign-v1.json'
with manifest.open('x') as f:json.dump(state,f,indent=2)
for name in ids:
 version=2 if name in ('ns64_b4','ns64_b8') else 1
 try:
  m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_owner_dev.py'),'--case',name,'--site',str(old/'site'),'--wheel',str(old/'dist/anysolver-0.4.7-py3-none-any.whl'),'--source',str(REPO),'--registration',str(ROOT/'registrations'/name/f'registration-v{version}.json'),'--output',str(ROOT/'owners'/name/'owner-v1')],'owner-'+name+'-v1',1024**3)
  report=json.loads((ROOT/'owners'/name/'owner-v1'/'summary.json').read_text())
  state['cases'][name]=dict(status=report['status'],summary_sha256=hashlib.sha256((ROOT/'owners'/name/'owner-v1'/'summary.json').read_bytes()).hexdigest())
 except BaseException as error:
  state['cases'][name]=dict(status='FAILED_EXECUTION',type=type(error).__name__,detail=str(error));raise
 finally:manifest.write_text(json.dumps(state,indent=2)+'\n')
