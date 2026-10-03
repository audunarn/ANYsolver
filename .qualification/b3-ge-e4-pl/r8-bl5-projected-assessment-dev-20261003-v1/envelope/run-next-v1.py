from pathlib import Path
import importlib.util,os,sys,json,hashlib
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
if sys.argv[1]=='last':
 name='ns64_b8';folder=ROOT/'registrations'/name;folder.mkdir(exist_ok=False)
 cmd=[sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_norm_dev.py'),'--fixture-case',name,'--output',str(folder/'registration-v1.json')]
 try:m.supervise(cmd,'register-'+name+'-v1',1024**3)
 finally:
  manifest=ROOT/'campaign-v1.json';state=json.loads(manifest.read_text())
  result=json.loads((folder/'registration-v1.json').read_text())
  state['cases'][name]=dict(status=result['status'],json_sha256=hashlib.sha256((folder/'registration-v1.json').read_bytes()).hexdigest(),failure=result.get('failure'))
  manifest.write_text(json.dumps(state,indent=2)+'\n')
elif sys.argv[1]=='owner':
 name='ns16_b1_8';old=Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2'
 m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_owner_dev.py'),'--case',name,'--site',str(old/'site'),'--wheel',str(old/'dist/anysolver-0.4.7-py3-none-any.whl'),'--source',str(REPO),'--registration',str(ROOT/'registrations'/name/'registration-v1.json'),'--output',str(ROOT/'owners'/name/'owner-v1')],'owner-'+name+'-v1',1024**3)
else:raise ValueError(sys.argv[1])
