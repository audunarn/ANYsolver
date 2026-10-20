"""Two actual standalone installed pre-yield CLI runs, with retained JSON."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
BUNDLE = Path('C:/ANYworkspaceWork/beam-shell-incremental-delivery-20261020/build-6fb907a1c-v2/bundle')
spec = importlib.util.spec_from_file_location('installed_guard', BUNDLE / 'tests/conftest.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
guard.inspect_runtime()
records = []
for coupling in ('direct', 'interpolated'):
    command = [sys.executable, '-I', str(BUNDLE / 'examples/beam_shell_coupling.py'), '--coupling', coupling]
    start = time.perf_counter()
    with (HERE / (coupling + '-preyield.stdout.json')).open('wb') as out, (HERE / (coupling + '-preyield.stderr.txt')).open('wb') as err:
        process = subprocess.Popen(command, cwd=BUNDLE, stdout=out, stderr=err)
        status = 'running'
        try:
            code = process.wait(timeout=45)
            status = 'exit'
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            process.wait()
            status = 'timeout'
            raise
        finally:
            records.append(dict(command=command, status=status, exit_code=process.returncode,
                process_wall_seconds=time.perf_counter() - start))
            (HERE / 'smoke-commands.json').write_text(json.dumps(records, indent=2) + '\n')
    assert code == 0
    result = json.loads((HERE / (coupling + '-preyield.stdout.json')).read_text())
    assert result['completed'] and result['status'] == 'completed'
    assert abs(result['achieved_load_factor'] - 1.) <= 1e-8
    assert result['constraint_postcheck']['status'] == 'passed'
(HERE / 'smoke-result.json').write_text(json.dumps(dict(status='PASS', cli_runs=records,
    runtime=guard.inspect_runtime()), indent=2) + '\n')
