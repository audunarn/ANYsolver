from pathlib import Path
import hashlib,json,subprocess,sys
raw=Path(__file__).resolve().parent;repo=raw.parents[2]
previous=raw.parent/'r8-native-displacement-chart-dev-20261005-v1'
consumer=json.loads((previous/'artifact-v1.json').read_bytes())['artifacts']['fem']
assert hashlib.sha256(Path(consumer['wheel']).read_bytes()).hexdigest()==consumer['sha256']
dist=raw/'solver-dist-v1';dist.mkdir(exist_ok=False)
command=[sys.executable,'-m','pip','wheel','.','--no-index','--no-deps',
    '--no-build-isolation','--no-cache-dir','-w',str(dist)]
with (raw/'solver-build-v1.log').open('xb') as log:
    subprocess.run(command,cwd=repo,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
wheel,=dist.glob('*.whl')
artifacts=dict(solver=dict(wheel=str(wheel),sha256=hashlib.sha256(wheel.read_bytes()).hexdigest()),fem=consumer)
install=[sys.executable,'-m','pip','install','--no-index','--no-deps','--no-cache-dir',
    '--target',str(raw/'site-v1'),str(wheel),consumer['wheel']]
with (raw/'install-v1.log').open('xb') as log:
    subprocess.run(install,cwd=repo,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
(raw/'artifact-v1.json').write_bytes((json.dumps(dict(commands=[command,install],
    artifacts=artifacts,source_parent='99f479cb',scope='native point arc development; no release'),indent=2)+'\n').encode('ascii'))
print('Built and installed isolated native arc wheel; unchanged consumer reused.')
