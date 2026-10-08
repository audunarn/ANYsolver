from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time
import psutil
root=Path(__file__).resolve().parent; repo=root.parents[2]
source=root/'wheel-source-v1'; source.mkdir(exist_ok=False)
for name in ('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'):
    shutil.copyfile(repo/name,source/name)
shutil.copytree(repo/'src/anysolver',source/'src/anysolver',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
wheels=root/'wheel-v1';wheels.mkdir(exist_ok=False)
env=os.environ.copy()
env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',NUMEXPR_NUM_THREADS='1',PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1')
psutil.Process().cpu_affinity([0])
resources=[]
def bounded(command,log):
    start=time.monotonic(); peak=0
    proc=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        while proc.poll() is None:
            tree=[psutil.Process(proc.pid)];tree+=tree[0].children(recursive=True)
            size=0
            for p in tree:
                try:
                    assert p.cpu_affinity()==[0]
                    size+=p.memory_info().rss
                except psutil.NoSuchProcess:pass
            peak=max(peak,size)
            assert size<=2*1024**3 and time.monotonic()-start<=600
            time.sleep(.05)
        assert proc.returncode==0,proc.returncode
    except BaseException:
        for p in reversed(tree):
            try:p.kill()
            except psutil.NoSuchProcess:pass
        proc.wait();raise
    finally:
        resources.append(dict(command=command,returncode=proc.returncode,elapsed_seconds=time.monotonic()-start,sampled_peak_tree_bytes=peak,pid=proc.pid,affinity=[0],seconds_limit=600,memory_limit_bytes=2*1024**3,numerical_execution=False))
        (root/'build-resource.json').write_text(json.dumps(resources,indent=2))
command=[sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(wheels),str(source)]
with (root/'wheel-build-v1.log').open('w') as log:
    bounded(command,log)
artifact=next(wheels.glob('*.whl'))
target=root/'installed-wheel-v1'
with (root/'wheel-install-v1.log').open('w') as log:
    bounded([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(target),str(artifact)],log)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(artifact=str(artifact),sha256=sha(artifact),installed_root=str(target),
    build_command=command,source={str(p.relative_to(source)):sha(p) for p in (source/'src/anysolver').rglob('*.py')})
(root/'artifact-binding-v1.json').write_text(json.dumps(record,indent=2))
print(json.dumps(dict(artifact=str(artifact),sha256=sha(artifact),source_count=len(record['source']))))
