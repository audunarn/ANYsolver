from pathlib import Path
import hashlib, json, subprocess, sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
dist = ROOT / 'dist-v1'
dist.mkdir()
wheel = dist / 'anysolver-0.4.7-py3-none-any.whl'
commands = [
    [sys.executable, '-m', 'pip', 'wheel', '.', '--no-deps', '--no-build-isolation',
     '--no-cache-dir', '-w', str(dist)],
    [sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-cache-dir',
     '--target', str(ROOT / 'site-v1'), str(wheel)],
]
for tag, command in zip(('build-v1', 'install-v1'), commands):
    with (ROOT / (tag + '.log')).open('xb') as out:
        result = subprocess.run(command, cwd=REPO, stdout=out, stderr=subprocess.STDOUT, timeout=120)
    assert result.returncode == 0, (tag, result.returncode)
(ROOT / 'artifact-v1.json').open('x').write(json.dumps(dict(
    commands=commands, wheel=str(wheel),
    wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest()), indent=2) + '\n')
print('Built isolated development wheel; no publication.')
