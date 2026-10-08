from pathlib import Path
import sys, os, json, hashlib, threading, time, importlib.util, shutil
RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
CI = RAW.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
METRIC = RAW.parent/'r8-native-director-arc-metric-dev-20261006-v1'
sys.path.insert(0, str(CI))
import psutil
mode, attempt = sys.argv[1:3]
assert mode in ('source','candidate'), 'Only separately approved local-diagnostic scope modes permitted'
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
    manifest = json.loads((RAW/'inputs-manifest-v3.json').read_text())
    inputs_root = RAW/'inputs-snapshot-v3'
    solver = REPO/'src' if mode == 'source' else METRIC/'site-v1'
    sys.path[:0] = [str(solver),str(inputs_root)]
    assert sys.pycache_prefix == str(folder/'pycache') and sys.dont_write_bytecode
    assert all(sha(inputs_root/name)==digest for name,digest in manifest['inputs'].items())
    source = {p.relative_to(REPO/'src').as_posix():sha(p) for p in (REPO/'src/anysolver').rglob('*.py')}
    assert source == manifest['source_modules']
    for name in manifest['inputs']:
        target = folder/'input-copies'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(inputs_root/name,target)
    import anysolver, anymaterial, numpy, scipy.linalg, numba, llvmlite
    from threadpoolctl import threadpool_info
    def runtime():
        return dict(executable=sys.executable,affinity=process.cpu_affinity(),pools=threadpool_info(),numba_threads=numba.get_num_threads(),jit_off=bool(numba.config.DISABLE_JIT),versions={m.__name__:getattr(m,'__version__',None) for m in (anysolver,numpy,scipy,numba,llvmlite)},imports={m.__name__:m.__file__ for m in (anysolver,anymaterial,numpy,scipy,numba,llvmlite)})
    def validate_runtime(value):
        assert value['affinity']==[0] and value['numba_threads']==1 and value['jit_off']
        assert all(p['num_threads']==1 for p in value['pools'])
        assert os.environ.get('OPENBLAS_CORETYPE') is None
    before = runtime(); write('runtime-before.json',before); validate_runtime(before)
    assert Path(anysolver.__file__).resolve().is_relative_to(solver.resolve())
    assert Path(anymaterial.__file__).resolve()==Path('C:/Github/ANYmaterial/src/anymaterial/__init__.py').resolve()
    assert sha(anymaterial.__file__)=='46d9c80639435e40c8533d78d89364c51f1cef65969b1c418eab4f36a7512900'
    for module,version in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
        assert module.__version__==version and Path(module.__file__).resolve().is_relative_to(CI.resolve())
    write('source-binding.json',source)
    if mode!='source':
        import zipfile
        wheel = METRIC/'wheel-v1/anysolver-0.4.7-py3-none-any.whl'
        assert sha(wheel)==manifest['wheel_sha256']
        with zipfile.ZipFile(wheel) as archive:
            payload={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('anysolver/') and name.endswith('.py')}
        installed={p.relative_to(solver).as_posix():sha(p) for p in (solver/'anysolver').rglob('*.py')}
        assert source==payload==installed
        write('artifact-binding.json',dict(wheel=str(wheel),wheel_sha256=sha(wheel),payload=payload,site=str(solver)))
    assert all(sha(RAW/name)==digest for name,digest in manifest['references'].items())
    ready.set()
    try:
        if mode=='source':
            import pytest
            class Reports:
                def pytest_runtest_logreport(self,report):
                    with (folder/'case-reports.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,duration=report.duration,detail=str(report.longrepr) if report.failed else None))+'\n')
            args=['-q','-c',str(inputs_root/'pyproject.toml'),'-o','pythonpath=','--basetemp',str(folder/'temp'),'--junitxml='+str(folder/'junit.xml'),str(inputs_root/'tests/test_stiffened_shell_native_fold_local_diagnostic.py')]
            write('pytest-command.json',args)
            code=pytest.main(args,plugins=[Reports()])
        else:
            from examples import stiffened_shell_native_fold_local_diagnostic as local
            write('candidate-started.json',dict(status='CONSUMED',generation=13,
                scope='ONE Log-only candidate baseline plus four signed actual assemblies, one sparse border'))
            retained=[]
            def save_evaluation(payload):
                index=len(retained)
                target=folder/f'evaluation-{index:02d}.json'
                write(target.name,payload,compact=True)

                retained.append(dict(index=index,path=target.name,label=payload['label'],
                    status=payload['status'],diagnostic_completion=payload['diagnostic_completion'],
                    sha256=sha(target)))
                write('evaluation-inventory.json',dict(status='PARTIAL',evaluations=retained))
            result=local.diagnose_saved_g13(
                RAW.parent/'r8-native-proportional-capacity-dev-20261006-v1/installed-v1',
                on_evaluation=save_evaluation,numerical_candidate=local.LOG_ONLY_CANDIDATE)
            target=folder/'local-result.json'
            write(target.name,result,compact=True)

            write('evaluation-inventory.json',dict(status=result['diagnostic_completion'],
                evaluations=retained,result_sha256=sha(target)))
            code=0 if result['diagnostic_completion']=='COMPLETED_BOUNDED_DIAGNOSTIC' else 2
    finally:
        loaded={name:dict(path=m.__file__,sha256=sha(m.__file__)) for name,m in sys.modules.items() if getattr(m,'__file__',None) and Path(m.__file__).is_file() and name.startswith(('anysolver','anymaterial','numpy','scipy','numba','llvmlite','examples'))}
        write('loaded-modules.json',loaded)
        for name,row in loaded.items():
            if name.startswith('anysolver'):
                assert Path(row['path']).resolve().is_relative_to(solver.resolve())
                assert row['sha256']==source[Path(row['path']).relative_to(solver).as_posix()]
            if name.startswith('examples') and Path(row['path']).suffix=='.py':
                assert Path(row['path']).resolve().is_relative_to(inputs_root.resolve())
        after=runtime(); write('runtime-after.json',after); validate_runtime(after)
        assert all(sha(inputs_root/name)==digest for name,digest in manifest['inputs'].items())
        assert all(sha(RAW/name)==digest for name,digest in manifest['references'].items())
    raise SystemExit(code)
finally:
    stop.set(); thread.join(timeout=1)
    write('rss-samples.json',samples)
    write('resource-summary.json',dict(peak_tree_rss=max((row['rss'] for row in samples),default=0),samples=len(samples),affinity_setup_events=affinity_events))
