from pathlib import Path
import importlib.util,os,sys,json,hashlib
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ids=[f'ns{nx}_b{ratio}' for nx in (16,32,64) for ratio in ('1_8','1_4','1_2','1','2','4','8')]
state=dict(schema='PROJECTED_BL5_ENVELOPE_DEVELOPMENT_CAMPAIGN_V1',source_parent='a7327da2',
 source_sha256={name:sha(REPO/'scripts'/name) for name in ('r8_bl5_projected_envelope_norm_dev.py','r8_bl5_projected_envelope_owner_dev.py','r8_bl5_projected_modal_envelope_dev.py')},
 decision='Independent scalar eligibility on all21 cases before new native beta; no frozen/formal F03 authority consumed',
 case_order=ids,cases={name:dict(status='NOT_STARTED') for name in ids},formal_f03_authority_consumed=False)
manifest=ROOT/'campaign-v1.json'
with manifest.open('x') as f:json.dump(state,f,indent=2)
for name in ids:
 folder=ROOT/'registrations'/name;folder.mkdir(parents=True,exist_ok=False)
 state['cases'][name]['status']='RUNNING';manifest.write_text(json.dumps(state,indent=2)+'\n')
 try:
  m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_envelope_norm_dev.py'),'--fixture-case',name,'--output',str(folder/'registration-v1.json')],'register-'+name+'-v1',1024**3)
  result=json.loads((folder/'registration-v1.json').read_text())
  state['cases'][name]=dict(status=result['status'],json_sha256=sha(folder/'registration-v1.json'),arrays_sha256=result.get('arrays_sha256'),safe_case_floor=result.get('safe_case_floor'),predicates=result.get('predicates'))
 except BaseException as error:
  state['cases'][name]=dict(status='FAILED_EXECUTION',error_type=type(error).__name__,detail=str(error))
  manifest.write_text(json.dumps(state,indent=2)+'\n');raise
 manifest.write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps(dict(cases=len(ids),eligible=sum(c['status']=='REGISTERED_ENVELOPE_DEVELOPMENT_BOUND' for c in state['cases'].values()))))
