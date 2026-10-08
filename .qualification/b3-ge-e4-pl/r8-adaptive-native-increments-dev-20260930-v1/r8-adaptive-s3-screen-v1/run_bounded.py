from pathlib import Path
import json, os, subprocess, sys, time
import psutil
root=Path.cwd()
env=os.environ.copy();env.update(PYTHONPATH='C:\\Github\\ANYsolver\\.perf2-worktrees\\b3-ge-e4-pl-coupling\\src;C:\\Github\\ANYsolver\\.perf2-worktrees\\b3-ge-e4-pl-coupling\\tests'+os.pathsep+str(root),NUMBA_DISABLE_JIT='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')
start=time.monotonic();peak=0;status=None
with (root/'screen.log').open('w') as out:
    process=subprocess.Popen([sys.executable,'-u','screen.py','s3'],cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
    parent=psutil.Process(process.pid)
    while process.poll() is None:
        try:
            tree=[parent]+parent.children(recursive=True)
            peak=max(peak,sum(p.memory_info().rss for p in tree if p.is_running()))
        except (psutil.NoSuchProcess,psutil.AccessDenied): pass
        if time.monotonic()-start>600 or peak>8*1024**3:
            status='resource limit exceeded'
            for p in reversed(tree):
                try:p.kill()
                except psutil.NoSuchProcess:pass
            break
        time.sleep(.5)
    code=process.wait()
result={'exit_code':code,'status':status or ('passed' if code==0 else 'failed'),'process_tree_peak_rss_bytes':peak,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':600,'memory_limit_bytes':8*1024**3}
(root/'execution.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result));print('\n'.join((root/'screen.log').read_text().splitlines()[-4:]))
sys.exit(code if status is None else 124)

