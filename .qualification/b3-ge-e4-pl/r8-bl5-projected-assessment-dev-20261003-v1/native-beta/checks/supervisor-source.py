from pathlib import Path
import os,subprocess,sys,time,json,psutil
root=Path(__file__).resolve().parent
repo=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
mode=sys.argv[1]
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTEST_ADDOPTS='',ANYSOLVER_TEST_THREADS='1')
if mode.startswith('tests'):
 env['PYTHONPATH']=str(repo)+';'+str(repo/'src')
 command=[sys.executable,'-m','pytest','tests/test_r8_bl5_projected_native_beta_dev.py','-q','--basetemp',str(root/(mode+'-pytest'))]
else:
 env['PYTHONPATH']=str(repo)
 command=[sys.executable,'-m','scripts.r8_bl5_projected_native_beta_dev','--case','ns16_b8','--root',str(repo/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/envelope/owners/ns16_b8/owner-v1'),'--registration',str(Path(os.environ['TEMP'])/'r8-bl5-envelope-campaign-v1/registrations/ns16_b8/registration-v1.json'),'--wheel',str(Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2/dist/anysolver-0.4.7-py3-none-any.whl'),'--site',str(Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2/site'),'--output',str(repo/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/native-beta/ns16_b8-v3/native-beta.json')]
started=time.monotonic();peak=0;failure=None
with (root/(mode+'.log')).open('x') as out:
 child=subprocess.Popen(command,cwd=repo,env=env,stdout=out,stderr=subprocess.STDOUT);proc=psutil.Process(child.pid)
 while child.poll() is None:
  try:peak=max(peak,sum(p.memory_info().rss for p in [proc]+proc.children(recursive=True) if p.is_running()))
  except psutil.NoSuchProcess:pass
  if peak>2*1024**3 or time.monotonic()-started>600:
   failure='memory' if peak>2*1024**3 else 'timeout';subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False);child.wait();break
  time.sleep(.1)
record=dict(command=command,status='failed_limit' if failure else 'terminal',failure=failure,exit_code=child.wait(),peak_sampled_bytes=peak,elapsed_seconds=time.monotonic()-started,limit_bytes=2*1024**3,timeout_seconds=600)
(root/(mode+'-resource.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));print((root/(mode+'.log')).read_text()[-2000:]);raise SystemExit(record['exit_code'] or bool(failure))
