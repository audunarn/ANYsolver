from pathlib import Path
import sys, os, json, hashlib, threading, time, importlib.util, shutil
RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
CI = RAW.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
METRIC = RAW.parent/'r8-native-director-arc-metric-dev-20261006-v1'
sys.path.insert(0, str(CI))
import psutil
mode, attempt = sys.argv[1:3]
assert mode == 'saved-data', 'Existing capture diagnostic only; no physical execution'
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
    manifest = json.loads((RAW/'inputs-manifest-sampling-v1.json').read_text())
    inputs_root = RAW/'inputs-snapshot-sampling-v1'
    solver = REPO/'src'
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
        from examples import stiffened_shell_native_fold_local_diagnostic as local
        import numpy as np
        from scipy.sparse import csc_matrix
        saved_manifest = json.loads((RAW/'saved-sampling-inputs-v1.json').read_text())
        saved_bindings = saved_manifest['references']
        assert all(sha(RAW/name)==digest for name,digest in saved_bindings.items())
        write('saved-input-bindings.json',saved_bindings)
        saved = json.loads((RAW/'installed-remaining-endpoints-v1/g14/local-result.json').read_text())
        matrix = saved['actual_mixed_tangent']
        assert matrix['format']=='csc' and matrix['shape']==[local.MIXED_ROWS,local.MIXED_ROWS]
        J = csc_matrix((matrix['data'],matrix['indices'],matrix['indptr']),shape=matrix['shape'])
        assert saved['generation']==14 and saved['difference_pair']==local.INTERMEDIATE_PAIR
        assert saved['numerical_candidate']==local.LOG_ONLY_CANDIDATE
        source_check = json.loads((RAW/'root-sampling-source-pass-v1.json').read_text())
        assert source_check['tests']==dict(passed=61,failed=0,errors=0,skipped=0)
        checks=[]
        for index, original in enumerate(saved['checks']):
            h=original['step']
            minus_name=f'installed-remaining-endpoints-v1/g14/evaluation-{2*index+1:02d}.json'
            plus_name=f'installed-remaining-endpoints-v1/g14/evaluation-{2*index+2:02d}.json'
            minus=json.loads((RAW/minus_name).read_text())
            plus=json.loads((RAW/plus_name).read_text())
            assert minus['label']==f'h={h:.0e},sign=-1' and plus['label']==f'h={h:.0e},sign=+1'
            witness=local.shell_translation_sampling_witness(
                np.asarray(minus['actual_mixed_state']['q'][:local.SHELL_ROWS]),
                np.asarray(plus['actual_mixed_state']['q'][:local.SHELL_ROWS]),
                saved['actual_mixed_direction'],h,J,saved['row_scales'],
                np.asarray(saved['free_rows'],dtype=int),saved['constraint_start'],
                saved['full_unit_factor_load'],original['assembled_original_difference'],
                difference_pair=local.INTERMEDIATE_PAIR)
            assert witness['original_witness']==original['assembled_witness']
            assert witness['diagnostic_only'] and not witness['changes_registered_acceptance']
            checks.append(dict(step=h,shell_translation_sampling=local.case._plain(witness)))
            del minus,plus
        result=dict(status='COMPLETED_SAVED_INPUT_DIAGNOSTIC',generation=14,
                    checks=checks,original_raw_status=saved['status'],
                    original_plateau=saved['plateau']['witness'],original_g14_criterion='FAILED',
                    g15='NOT_RUN',solver_evaluations=0,owner_constructions=0,
                    scientific_acceptance=False,operator_defect_excluded=False,
                    primary_authority='CONSUMED',changes_registered_acceptance=False)
        write('saved-sampling-result.json',result)
        assert all(sha(RAW/name)==digest for name,digest in saved_bindings.items())
        code=0
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
