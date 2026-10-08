"""One owned development job; sampled process-tree resource supervision."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
CI = REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
sys.path.insert(0, str(CI))
import psutil

psutil.Process().cpu_affinity([0])
env = os.environ.copy()
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS',
             'NUMEXPR_NUM_THREADS', 'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
             'NUMBA_DISABLE_JIT'):
    env[name] = '1'
for name in ('OPENBLAS_CORETYPE', 'NPY_DISABLE_CPU_FEATURES'):
    env.pop(name, None)
env['PYTHONPATH'] = os.pathsep.join((str(RAW/'installed-host-v1'), str(CI)))
env['PYTHONUTF8'] = '1'
env['PYTHONDONTWRITEBYTECODE'] = '1'
command = ['C:/Python/Python314/python.exe', str(RAW/'installed-entry-v1.py')]
started = time.monotonic()
peak = 0
seen = set()
reason = None
with (RAW/'installed-stdout-v1.log').open('wb') as out, (RAW/'installed-stderr-v1.log').open('wb') as err:
    child = subprocess.Popen(command, cwd=REPO, env=env, stdout=out, stderr=err)
    (RAW/'installed-live-job-v1.json').write_text(json.dumps({'pid': child.pid, 'command': command,
        'seconds_limit': 600, 'memory_limit_bytes': 2147483648,
        'affinity_inherited_from_parent': [0], 'status': 'RUNNING'}, indent=2)+'\n')
    print(json.dumps({'pid': child.pid, 'status': 'RUNNING'}), flush=True)
    while child.poll() is None:
        elapsed = time.monotonic()-started
        processes = []
        try:
            parent = psutil.Process(child.pid)
            processes = [parent, *parent.children(recursive=True)]
        except psutil.NoSuchProcess:
            pass
        memory = 0
        for process in processes:
            try:
                memory += process.memory_info().rss
                seen.add(process.pid)
            except psutil.NoSuchProcess:
                pass
        peak = max(peak, memory)
        if elapsed > 600:
            reason = 'time_limit'
        elif memory > 2147483648:
            reason = 'memory_limit'
        elif max((RAW/'installed-stdout-v1.log').stat().st_size,
                 (RAW/'installed-stderr-v1.log').stat().st_size) > 8388608:
            reason = 'output_limit'
        if reason:
            for process in reversed(processes):
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
            break
        time.sleep(.1)
    code = child.wait(timeout=10)
receipt = dict(status=reason or ('completed' if code == 0 else 'failed'), exit_code=code,
    child_pid=child.pid, command=command, observed_pids=sorted(seen),
    elapsed_seconds=time.monotonic()-started, sampled_peak_tree_bytes=peak,
    seconds_limit=600, memory_limit_bytes=2147483648, affinity_before_child_code=[0],
    numerical_job_count=1, memory_scope='sampled RSS; not peak-memory qualification')
(RAW/'installed-resource-receipt-v1.json').write_text(json.dumps(receipt, indent=2)+'\n')
(RAW/'installed-live-job-v1.json').write_text(json.dumps({'pid': child.pid, 'status': receipt['status']})+'\n')
print(json.dumps(receipt), flush=True)
raise SystemExit(code if code else (1 if reason else 0))


