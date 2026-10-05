from pathlib import Path
import json, os, subprocess, sys, time
import psutil
root=Path(__file__).resolve().parent
env=os.environ.copy()
env.update(PYTHONPATH=str(root/'site'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTEST_ADDOPTS='')
started=time.monotonic();peak=0;failure=None
command=[sys.executable,str(root/'check-installed.py')]
with (root/'installed.log').open('x') as out:
    child=subprocess.Popen(command,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak=max(peak,sum(p.memory_info().rss for p in [proc]+proc.children(recursive=True) if p.is_running()))
        except psutil.NoSuchProcess: pass
        if peak>2*1024**3 or time.monotonic()-started>180:
            failure='memory' if peak>2*1024**3 else 'timeout'
            subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
            child.wait();break
        time.sleep(.1)
record=dict(command=command,status='failed_limit' if failure else 'terminal',failure=failure,exit_code=child.wait(),peak_sampled_bytes=peak,elapsed_seconds=time.monotonic()-started,limit_bytes=2*1024**3,timeout_seconds=180)
(root/'resource.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));print((root/'installed.log').read_text()[-6000:])
raise SystemExit(record['exit_code'] or bool(failure))
