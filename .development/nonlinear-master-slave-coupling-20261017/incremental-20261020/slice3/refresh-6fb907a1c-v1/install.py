"""Fresh isolated Windows Python 3.12 install of explicit candidate wheels."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
BUILD = Path('C:/ANYworkspaceWork/beam-shell-incremental-delivery-20261020/build-6fb907a1c-v2')
BUNDLE = BUILD / 'bundle'
ENV = BUILD.parent / 'venv-6fb907a1c-v3'
inputs = json.loads((HERE.parent / 'PACKAGING_INPUTS.json').read_text())
manifest = json.loads((BUNDLE / 'MANIFEST.json').read_text())
for item in inputs['private_dependency_wheels']:
    copied = BUNDLE / 'wheelhouse' / Path(item['path']).name
    assert hashlib.sha256(copied.read_bytes()).hexdigest() == item['sha256']
assert not ENV.exists(), 'preserve every prior environment'
commands = [[inputs['python312'], '-I', '-m', 'venv', str(ENV)]]
python = ENV / 'Scripts/python.exe'
wheels = [BUNDLE / 'wheelhouse' / manifest['solver_wheel']]
wheels += sorted(p for p in (BUNDLE / 'wheelhouse').glob('*.whl') if p not in wheels)
commands.append([str(python), '-I', '-m', 'pip', 'install', '-r',
    str(BUNDLE / 'requirements-tested.txt'), *map(str, wheels)])
records = []
for command in commands:
    start = time.perf_counter()
    process = subprocess.Popen(command)
    status = 'running'
    try:
        code = process.wait(timeout=100)
        status = 'exit'
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
        process.wait()
        status = 'timeout'
        raise
    finally:
        records.append(dict(command=command, status=status, exit_code=process.returncode,
            process_wall_seconds=time.perf_counter() - start))
        (HERE / 'install-commands.json').write_text(json.dumps(records, indent=2) + '\n')
    if code:
        raise SystemExit(code)
print(json.dumps(dict(python=str(python), bundle=str(BUNDLE))))
