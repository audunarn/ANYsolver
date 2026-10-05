from pathlib import Path
import json,os,subprocess,sys,time
import psutil
r=Path.cwd();case=sys.argv[1];old=r.parent/'r8-staged-load-installed-v1'
env=os.environ.copy();env.update(PYTHONPATH=os.pathsep.join(map(str,[old/'site',r/'fixtures',r])),PYTHONNOUSERSITE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',NUMBA_DISABLE_JIT='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')
start=time.monotonic();peak=0;status=None;tree=[]
with (r/(case+'-installed.log')).open('w') as out:
    process=subprocess.Popen([sys.executable,'-u',str(r/'run_installed.py'),case],cwd=r,env=env,stdout=out,stderr=subprocess.STDOUT)
    parent=psutil.Process(process.pid)
    while process.poll() is None:
        try:
            tree=[parent]+parent.children(recursive=True)
            peak=max(peak,sum(p.memory_info().rss for p in tree if p.is_running()))
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        if time.monotonic()-start>600 or peak>8*1024**3:
            status='resource limit exceeded'
            for p in reversed(tree):
                try:p.kill()
                except psutil.NoSuchProcess:pass
            break
        time.sleep(.5)
    code=process.wait()
result={'exit_code':code,'status':status or ('passed' if code==0 else 'failed'),'process_tree_peak_rss_bytes':peak,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':600,'memory_limit_bytes':8*1024**3,'case':case}
(r/(case+'-execution.json')).write_text(json.dumps(result,indent=2))
print(json.dumps(result));print('\n'.join((r/(case+'-installed.log')).read_text().splitlines()[-12:]))
sys.exit(code if status is None else 124)
