from pathlib import Path
import hashlib, json, subprocess, sys

ROOT = Path(__file__).resolve().parent
SOLVER = ROOT.parents[2]
FEM = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
commands, artifacts = [], {}
for name, repo in (('solver', SOLVER), ('fem', FEM)):
    dist = ROOT / (name + '-dist-v1')
    dist.mkdir()
    command = [sys.executable, '-m', 'pip', 'wheel', '.', '--no-deps', '--no-build-isolation',
               '--no-cache-dir', '-w', str(dist)]
    commands.append(command)
    with (ROOT / (name + '-build-v1.log')).open('xb') as out:
        result = subprocess.run(command, cwd=repo, stdout=out, stderr=subprocess.STDOUT, timeout=120)
    assert result.returncode == 0, (name, result.returncode)
    wheel, = dist.glob('*.whl')
    artifacts[name] = dict(wheel=str(wheel), sha256=hashlib.sha256(wheel.read_bytes()).hexdigest())
command = [sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-cache-dir',
           '--target', str(ROOT / 'site-v1'), *(artifacts[name]['wheel'] for name in ('solver', 'fem'))]
commands.append(command)
with (ROOT / 'install-v1.log').open('xb') as out:
    result = subprocess.run(command, cwd=SOLVER, stdout=out, stderr=subprocess.STDOUT, timeout=120)
assert result.returncode == 0, result.returncode
(ROOT / 'artifact-v1.json').open('x').write(json.dumps(dict(commands=commands, artifacts=artifacts), indent=2) + '\n')
print('Built and installed two isolated development wheels; no publication.')
