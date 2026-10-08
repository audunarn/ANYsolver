from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys
root=Path(__file__).resolve().parent; repo=root.parents[2]
source=root/'wheel-source-v1'; source.mkdir(exist_ok=False)
for name in ('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'):
    shutil.copyfile(repo/name,source/name)
shutil.copytree(repo/'src/anysolver',source/'src/anysolver',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
wheels=root/'wheel-v1';wheels.mkdir(exist_ok=False)
env=os.environ.copy()
env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1')
command=[sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(wheels),str(source)]
with (root/'wheel-build-v1.log').open('w') as log:
    subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
artifact=next(wheels.glob('*.whl'))
target=root/'installed-wheel-v1'
with (root/'wheel-install-v1.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--target',str(target),str(artifact)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(artifact=str(artifact),sha256=sha(artifact),installed_root=str(target),
    build_command=command,source={str(p.relative_to(source)):sha(p) for p in (source/'src/anysolver').rglob('*.py')})
(root/'artifact-binding-v1.json').write_text(json.dumps(record,indent=2))
print(json.dumps(dict(artifact=str(artifact),sha256=sha(artifact),source_count=len(record['source']))))
