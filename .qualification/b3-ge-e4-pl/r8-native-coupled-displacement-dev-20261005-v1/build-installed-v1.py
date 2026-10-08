from pathlib import Path
import hashlib,json,subprocess,sys
root = Path(__file__).resolve().parent
repo = root.parents[2]
previous = root.parent/'r8-distributing-native-material-dev-20261004-v1'
consumer = json.loads((previous/'artifact-v1.json').read_text(encoding='utf-8'))['artifacts']['fem']
assert hashlib.sha256(Path(consumer['wheel']).read_bytes()).hexdigest() == consumer['sha256']
dist = root/'solver-dist-v1'; dist.mkdir()
command = [sys.executable,'-m','pip','wheel','.','--no-index','--no-deps',
    '--no-build-isolation','--no-cache-dir','-w',str(dist)]
with (root/'solver-build-v1.log').open('xb') as log:
    subprocess.run(command,cwd=repo,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
wheel, = dist.glob('*.whl')
artifacts = dict(solver=dict(wheel=str(wheel),sha256=hashlib.sha256(wheel.read_bytes()).hexdigest()),fem=consumer)
install = [sys.executable,'-m','pip','install','--no-index','--no-deps','--no-cache-dir',
    '--target',str(root/'site-v1'),str(wheel),consumer['wheel']]
with (root/'install-v1.log').open('xb') as log:
    subprocess.run(install,cwd=repo,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
(root/'artifact-v1.json').open('x',encoding='utf-8').write(json.dumps(dict(
    commands=[command,install],artifacts=artifacts,source_parent='9a306013',
    scope='isolated native coupled Q4 J2 displacement development candidate; unchanged consumer reused, no release'),indent=2)+'\n')
print('Built isolated solver wheel and installed unchanged verified consumer.',flush=True)
