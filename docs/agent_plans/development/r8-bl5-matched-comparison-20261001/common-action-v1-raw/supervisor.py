"""One bounded, exclusive saved-operator control; no formal F03 authority."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import psutil

temp = Path(tempfile.gettempdir())
parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--cases', nargs='+', choices=('fy', 'mx', 'mz'), required=True)
parser.add_argument('--screen-only', action='store_true')
args = parser.parse_args()
assert args.name.startswith('r8-bl5-common-density-') and Path(args.name).name == args.name
assert len(set(args.cases)) == len(args.cases)
source = temp/'r8-bl5-common-density-control.py'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == '594c8b73f7ca9b8fa5ecb809c7debbc4ee0e0fc5ae0f26dc0a1934c448a18d51'
review = temp/'r8-bl5-common-density-prerun-review.md'
assert review.exists(), 'No numerical route before independent review'
root = temp/args.name
root.mkdir(exist_ok=False)
for origin, name in ((source, 'control.py'), (review, 'prerun-review.md'),
                     (temp/'r8-bl5-common-density-design.md', 'design.md'),
                     (Path(__file__), 'supervisor.py')):
    shutil.copyfile(origin, root/name)
env = os.environ.copy()
env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
           NUMBA_NUM_THREADS='1', NUMBA_DISABLE_JIT='1', PYTHONNOUSERSITE='1',
           PYTHONDONTWRITEBYTECODE='1', NUMEXPR_NUM_THREADS='1')
env.pop('PYTHONPATH', None)
command = [sys.executable, '-u', str(source), '--output-dir', str(root/'run'), '--cases', *args.cases]
if args.screen_only:
    command.append('--screen-only')
start = time.monotonic()
peak = 0
failure = None
with (root/'execution.log').open('x') as log:
    child = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    process = psutil.Process(child.pid)
    try:
        while child.poll() is None:
            try:
                tree = [process] + process.children(recursive=True)
                peak = max(peak, sum(p.memory_info().rss for p in tree if p.is_running()))
            except psutil.NoSuchProcess:
                pass
            if time.monotonic()-start > 600 or peak > 8*1024**3:
                failure = 'time or memory ceiling exceeded'
                break
            time.sleep(.02)
    except BaseException as error:
        failure = type(error).__name__ + ': ' + str(error)
    finally:
        if failure and child.poll() is None:
            for item in reversed([process]+process.children(recursive=True)):
                try:
                    item.kill()
                except psutil.NoSuchProcess:
                    pass
        code = child.wait()
record = {'status': 'completed' if code == 0 and failure is None else 'failed',
          'exit_code': code, 'resource_failure': failure, 'command': command,
          'source_sha256': digest, 'elapsed_seconds': time.monotonic()-start,
          'sampled_process_tree_peak_rss_bytes': peak,
          'limits': {'seconds': 600, 'bytes': 8*1024**3, 'numerical_threads': 8},
          'formal_F03_consumed': False, 'scope': 'saved finest-domain diagnostic, not qualification'}
(root/'execution.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record), flush=True)
if code or failure:
    print('\n'.join((root/'execution.log').read_text().splitlines()[-18:]), flush=True)
    sys.exit(1)
result = json.loads((root/'run/result.json').read_text())
assert result['source_sha256'] == digest, 'actual executed source must match launch binding'
print(json.dumps({'result_status': result['status'], 'cases': list(result['cases']),
                  'factorizations': result.get('factorizations', 0),
                  'actual_source_binding': True}), flush=True)
