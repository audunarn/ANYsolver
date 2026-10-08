from pathlib import Path
import sys, os, json, hashlib, threading, time, importlib.util, shutil
RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
CI = RAW.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
METRIC = RAW.parent/'r8-native-director-arc-metric-dev-20261006-v1'
sys.path.insert(0, str(CI))
import psutil
mode, attempt = sys.argv[1:3]
assert mode in ('source','build','installed'), 'Consumer verification modes only'
authority=json.loads((RAW/'authority-v1.json').read_text())
assert authority['status']=='APPROVED' and authority.get('approval_evidence'), 'PENDING_USER_APPROVAL'
assert authority['total_seconds']==180 and authority['reserve_seconds']>=60
folder = RAW/attempt
process = psutil.Process()
process.cpu_affinity([0])
assert process.cpu_affinity() == [0]
samples, affinity_events = [], []
ready, stop = threading.Event(), threading.Event()
started = time.perf_counter()
def write(name, value, *, compact=False):
    target=folder/name
    temporary=target.with_suffix(target.suffix+'.part')
    with temporary.open('w',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,separators=(',',':') if compact else None,
                  indent=None if compact else 2,allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary,target)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def monitor():
    while not stop.is_set():
        try:
            tree = [process]+process.children(recursive=True)
            rss = sum(p.memory_info().rss for p in tree if p.is_running())
            samples.append(dict(seconds=time.perf_counter()-started,rss=rss))
            if len(samples)%50 == 0:
                write('rss-partial.json',samples)
            for p in tree:
                if p.is_running() and p.cpu_affinity() != [0]:
                    affinity_events.append(dict(pid=p.pid,name=p.name(),before=p.cpu_affinity(),numerical_ready=ready.is_set()))
                    if ready.is_set() and p.name().lower() != 'conhost.exe':
                        write('affinity-failure.json',affinity_events[-1])
                        for target in reversed(tree): target.kill()
                    p.cpu_affinity([0])
            if rss > 2147483648:
                write('resource-failure.json',samples[-1])
                for target in reversed(tree): target.kill()
        except psutil.NoSuchProcess:
            pass
        stop.wait(.02)
thread = threading.Thread(target=monitor,daemon=True)
thread.start()
try:
    manifest=json.loads((RAW/'inputs-manifest-v2.json').read_text())
    inputs_root=RAW/'inputs-snapshot-v2'
    assert sys.pycache_prefix==str(folder/'pycache') and sys.dont_write_bytecode
    assert all(sha(inputs_root/name)==digest for name,digest in manifest['inputs'].items())
    source={p.relative_to(REPO/'src').as_posix():sha(p) for p in (REPO/'src/anysolver').rglob('*.py')}
    assert source==manifest['source_modules']
    write('source-binding.json',source)
    for name in manifest['inputs']:
        target=folder/'input-copies'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(inputs_root/name,target)
    solver=RAW/'site-v1' if mode=='installed' else REPO/'src'
    if mode=='installed':
        import zipfile
        artifact=json.loads((RAW/'artifact-v1.json').read_text())
        wheel=Path(artifact['wheel'])
        assert sha(wheel)==artifact['wheel_sha256']
        with zipfile.ZipFile(wheel) as archive:
            payload={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                     if name.startswith('anysolver/') and name.endswith('.py')}
        installed={p.relative_to(solver).as_posix():sha(p) for p in (solver/'anysolver').rglob('*.py')}
        assert payload==installed==source
        write('artifact-binding.json',artifact)
    sys.path[:0]=[str(solver),str(inputs_root),str(inputs_root/'tests')]
    import numpy,scipy.linalg,numba,llvmlite,anymaterial
    from threadpoolctl import threadpool_info
    def runtime():
        return dict(executable=sys.executable,affinity=process.cpu_affinity(),pools=threadpool_info(),
            numba_threads=numba.get_num_threads(),jit_off=bool(numba.config.DISABLE_JIT),
            versions={m.__name__:getattr(m,'__version__',None) for m in (numpy,scipy,numba,llvmlite)},
            imports={m.__name__:m.__file__ for m in (numpy,scipy,numba,llvmlite,anymaterial)})
    def validate(value):
        assert value['affinity']==[0] and value['numba_threads']==1 and value['jit_off']
        assert all(p['num_threads']==1 for p in value['pools'])
        assert os.environ.get('OPENBLAS_CORETYPE') is None
    before=runtime();write('runtime-before.json',before);validate(before)
    assert Path(anymaterial.__file__).resolve()==Path(manifest['anymaterial_source']).resolve()
    assert sha(anymaterial.__file__)==manifest['anymaterial_sha256']
    for module,version in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
        assert module.__version__==version and Path(module.__file__).resolve().is_relative_to(CI.resolve())
    ready.set()
    code=0
    try:
        if mode=='build':
            import subprocess,zipfile
            import importlib.metadata as metadata
            write('packaging-versions.json',{name:metadata.version(name) for name in ('pip','setuptools','wheel')})
            wheels=RAW/'wheel-v1';site=RAW/'site-v1'
            assert not wheels.exists() and not site.exists(), 'Fresh artifact directories required'
            wheels.mkdir()
            commands=[[sys.executable,'-I','-m','pip','wheel','--no-deps','--no-build-isolation',
                       '--no-cache-dir','--wheel-dir',str(wheels),str(REPO)]]
            write('build-commands.json',commands)
            for index,command in enumerate(commands):
                with (folder/f'build-{index}.stdout.log').open('w') as out,(folder/f'build-{index}.stderr.log').open('w') as err:
                    subprocess.run(command,stdout=out,stderr=err,check=True)
            candidates=list(wheels.glob('anysolver-*.whl'))
            assert len(candidates)==1
            wheel=candidates[0]
            with zipfile.ZipFile(wheel) as archive:
                payload={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                         if name.startswith('anysolver/') and name.endswith('.py')}
            assert payload==source, 'Wheel package differs from frozen candidate source'
            command=[sys.executable,'-I','-m','pip','install','--no-deps','--no-compile',
                     '--no-cache-dir','--target',str(site),str(wheel)]
            commands.append(command);write('build-commands.json',commands)
            with (folder/'install.stdout.log').open('w') as out,(folder/'install.stderr.log').open('w') as err:
                subprocess.run(command,stdout=out,stderr=err,check=True)
            installed={p.relative_to(site).as_posix():sha(p) for p in (site/'anysolver').rglob('*.py')}
            assert installed==source
            artifact=dict(candidate=manifest['candidate'],wheel=str(wheel),wheel_sha256=sha(wheel),
                          site=str(site),source_manifest_sha256=sha(RAW/'inputs-manifest-v2.json'),
                          package_modules=len(source),state='BUILT_INSTALLED_NOT_VERIFIED')
            write('artifact-result.json',artifact)
            target=RAW/'artifact-v1.json'
            assert not target.exists()
            target.write_text(json.dumps(artifact,indent=2)+'\n')
        else:
            import anysolver,pytest
            assert Path(anysolver.__file__).resolve().is_relative_to(solver.resolve())
            class Reports:
                def pytest_runtest_logreport(self,report):
                    with (folder/'case-reports.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(nodeid=report.nodeid,when=report.when,
                            outcome=report.outcome,duration=report.duration,
                            detail=str(report.longrepr) if report.failed else None))+'\n')
            args=['-q','-c',str(inputs_root/'pyproject.toml'),'-o','pythonpath=',
                  '--basetemp',str(folder/'temp'),'--junitxml='+str(folder/'junit.xml'),
                  str(inputs_root/'tests/test_stiffened_shell_consumer_capabilities.py')]
            write('pytest-command.json',args)
            code=pytest.main(args,plugins=[Reports()])
    finally:
        loaded={name:dict(path=m.__file__,sha256=sha(m.__file__)) for name,m in sys.modules.items()
                if getattr(m,'__file__',None) and Path(m.__file__).is_file()
                and name.startswith(('anysolver','anymaterial','numpy','scipy','numba','llvmlite',
                                     'test_stiffened_shell'))}
        write('loaded-modules.json',loaded)
        for name,row in loaded.items():
            if name.startswith('anysolver'):
                assert Path(row['path']).resolve().is_relative_to(solver.resolve())
                assert row['sha256']==source[Path(row['path']).relative_to(solver).as_posix()]
            if name.startswith('test_stiffened_shell'):
                assert Path(row['path']).resolve().is_relative_to((inputs_root/'tests').resolve())
                relative=Path(row['path']).relative_to(inputs_root).as_posix()
                assert row['sha256']==manifest['inputs'][relative]
        after=runtime();write('runtime-after.json',after);validate(after)
        assert all(sha(inputs_root/name)==digest for name,digest in manifest['inputs'].items())
        assert source=={p.relative_to(REPO/'src').as_posix():sha(p) for p in (REPO/'src/anysolver').rglob('*.py')}
    raise SystemExit(code)
finally:
    stop.set();thread.join(timeout=1)
    write('rss-samples.json',samples)
    write('resource-summary.json',dict(peak_tree_rss=max((row['rss'] for row in samples),default=0),
                                     samples=len(samples),affinity_setup_events=affinity_events))