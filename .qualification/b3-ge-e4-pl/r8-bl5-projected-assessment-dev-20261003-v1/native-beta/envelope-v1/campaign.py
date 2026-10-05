from pathlib import Path
import sys,os,subprocess,time,json,psutil,hashlib
repo=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
raw=repo/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1'
output=raw/'native-beta/envelope-v1';output.mkdir(exist_ok=False)
env=os.environ.copy();env.update(PYTHONPATH=str(repo),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',ANYSOLVER_TEST_THREADS='1')
site=Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2/site';wheel=site.parent/'dist/anysolver-0.4.7-py3-none-any.whl'
reused={'ns16_b1_2':raw/'ratios/whole_half/owner-v1','ns16_b2':raw/'ratios/whole_double/owner-v1','ns32_b1':raw/'joint32/installed-v2/owner'}
result=dict(status='STARTED',source_sha256=hashlib.sha256((repo/'scripts/r8_bl5_projected_native_beta_dev.py').read_bytes()).hexdigest(),cases={},formal_f03_authority_consumed=False,qualified=False)
prior=raw/'native-beta/ns16_b8-v3/native-beta.json';v=json.loads(prior.read_text());assert v['status']=='PASSED_NATIVE_AUXILIARY_BETA_DEVELOPMENT_ONLY' and all(x is True for x in v['predicates'].values())
result['cases']['ns16_b8']=dict(status=v['status'],beta=v['beta'],floor=v['safe_case_floor'],reused=True,source_sha256=v['source_sha256'],result_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),reason='Only added reference-row resource guard; prior actual subdivision1/1536rows already admitted; scientific equations and inputs unchanged.')
for nx in (16,32,64):
 for ratio in ('1_8','1_4','1_2','1','2','4','8'):
  case=f'ns{nx}_b{ratio}'
  if case in result['cases']:continue
  target=output/case;target.mkdir()
  version=2 if case in ('ns64_b4','ns64_b8') else 1
  command=[sys.executable,'-m','scripts.r8_bl5_projected_native_beta_dev','--case',case,'--root',str(reused.get(case,raw/'envelope/owners'/case/'owner-v1')),'--registration',str(raw/'envelope/registrations'/case/f'registration-v{version}.json'),'--wheel',str(wheel),'--site',str(site),'--output',str(target/'native-beta.json')]
  started=time.monotonic();peak=0;failure=None
  with (target/'execution.log').open('x') as log:
   child=subprocess.Popen(command,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT);proc=psutil.Process(child.pid)
   while child.poll() is None:
    try:peak=max(peak,sum(p.memory_info().rss for p in [proc]+proc.children(recursive=True) if p.is_running()))
    except psutil.NoSuchProcess:pass
    if peak>2*1024**3 or time.monotonic()-started>600:
     failure='memory' if peak>2*1024**3 else 'timeout';subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False);child.wait();break
    time.sleep(.1)
  execution=dict(command=command,exit_code=child.wait(),failure=failure,elapsed_seconds=time.monotonic()-started,peak_sampled_bytes=peak,limit_bytes=2*1024**3,timeout_seconds=600)
  (target/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
  record=json.loads((target/'native-beta.json').read_text()) if (target/'native-beta.json').is_file() else {}
  passed=execution['exit_code']==0 and not failure and record.get('status')=='PASSED_NATIVE_AUXILIARY_BETA_DEVELOPMENT_ONLY' and record.get('predicates') and all(x is True for x in record['predicates'].values())
  result['cases'][case]=dict(status=record.get('status','NO_RESULT'),beta=record.get('beta'),floor=record.get('safe_case_floor'),passed=bool(passed),reused=False,elapsed_seconds=execution['elapsed_seconds'],peak_sampled_bytes=peak)
  (output/'aggregate.json').write_text(json.dumps(result,indent=2)+'\n')
  print(case, result['cases'][case],flush=True)
  if not passed:
   result['status']='STOPPED_AT_FAILED_OR_UNCERTAIN_CASE';(output/'aggregate.json').write_text(json.dumps(result,indent=2)+'\n');raise SystemExit(1)
result['status']='ALL21_NATIVE_AUXILIARY_BETA_DEVELOPMENT_ONLY';(output/'aggregate.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',len(result['cases']),flush=True)
