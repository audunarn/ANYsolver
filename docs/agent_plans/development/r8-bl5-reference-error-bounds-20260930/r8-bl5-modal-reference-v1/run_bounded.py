from pathlib import Path
import json,os,subprocess,sys,time
import psutil
r=Path.cwd();env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1')
t=time.monotonic();peak=0;limit=None
with (r/'run.log').open('w') as out:
 p=subprocess.Popen([sys.executable,'-u','run_case.py','--output','result.json'],cwd=r,env=env,stdout=out,stderr=subprocess.STDOUT)
 parent=psutil.Process(p.pid)
 while p.poll() is None:
  tree=[]
  try:
   tree=[parent]+parent.children(recursive=True);peak=max(peak,sum(x.memory_info().rss for x in tree if x.is_running()))
  except (psutil.NoSuchProcess,psutil.AccessDenied):pass
  if time.monotonic()-t>600 or peak>8*1024**3:
   limit='resource limit exceeded'
   for x in reversed(tree):
    try:x.kill()
    except psutil.NoSuchProcess:pass
   break
  time.sleep(.1)
 code=p.wait()
result=dict(exit_code=code,status=limit or ('passed' if code==0 else 'failed'),elapsed_seconds=time.monotonic()-t,process_tree_peak_rss_bytes=peak,timeout_seconds=600,memory_limit_bytes=8*1024**3)
(r/'execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));print('\n'.join((r/'run.log').read_text().splitlines()[-8:]));sys.exit(code if not limit else 124)
