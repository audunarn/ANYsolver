from pathlib import Path
import sys,os,json,hashlib,time,threading,shutil,subprocess
RAW=Path(__file__).resolve().parent; REPO=RAW.parents[2]
CI=RAW.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
sys.path.insert(0,str(CI))
import psutil
mode,attempt=sys.argv[1:3]; folder=RAW/attempt
process=psutil.Process(); process.cpu_affinity([0]); assert process.cpu_affinity()==[0]
samples=[]; affinity_events=[]; ready=threading.Event(); stop=threading.Event(); started=time.perf_counter()
def monitor():
    while not stop.is_set():
        try:
            tree=[process]+process.children(recursive=True)
            rss=sum(p.memory_info().rss for p in tree if p.is_running())
            samples.append(dict(seconds=time.perf_counter()-started,rss=rss))
            if len(samples)%50==0:
                (folder/'rss-partial.json').write_text(json.dumps(samples))
            for p in tree:
                if p.is_running() and p.cpu_affinity()!=[0]:
                    affinity_events.append(dict(pid=p.pid,name=p.name(),before=p.cpu_affinity(),seconds=time.perf_counter()-started,numerical_ready=ready.is_set()))
                    if ready.is_set() and p.name().lower()!='conhost.exe':
                        (folder/'affinity-failure.json').write_text(json.dumps(affinity_events[-1]))
                        for target in reversed(tree):target.kill()
                    p.cpu_affinity([0])
            if rss>2147483648:
                (folder/'resource-failure.json').write_text(json.dumps(samples[-1]))
                for p in reversed(tree):p.kill()
        except psutil.NoSuchProcess:pass
        stop.wait(.02)
thread=threading.Thread(target=monitor,daemon=True);thread.start()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,value):(folder/name).write_text(json.dumps(value,indent=2)+'\n')
try:
    solver=RAW/'site-v1' if mode=='installed' else REPO/'src'
    inputs_root=RAW/'installed-input-snapshot-v1' if mode=='installed' else REPO
    sys.path[:0]=[str(solver),str(inputs_root)]
    if mode in ('build','install'):
        if mode=='build':command=[sys.executable,'-m','pip','wheel',str(REPO),'--no-deps','--no-build-isolation','--no-cache-dir','--no-index','-w',str(RAW/'wheel-v1')]
        else:command=[sys.executable,'-m','pip','install','--no-deps','--no-cache-dir','--no-index','--target',str(RAW/'site-v1'),str(next((RAW/'wheel-v1').glob('*.whl')))]
        write('inner-command.json',command)
        code=subprocess.call(command,env=os.environ.copy(),cwd=RAW)
        raise SystemExit(code)
    import anysolver,anymaterial,numpy,scipy.linalg,numba,llvmlite
    from threadpoolctl import threadpool_info
    def runtime():return dict(affinity=process.cpu_affinity(),pools=threadpool_info(),numba_threads=numba.get_num_threads(),jit_off=bool(numba.config.DISABLE_JIT),versions={m.__name__:getattr(m,'__version__',None) for m in (anysolver,numpy,scipy,numba,llvmlite)},imports={m.__name__:m.__file__ for m in (anysolver,anymaterial,numpy,scipy,numba,llvmlite)})
    effective=runtime();write('runtime-before.json',effective)
    assert Path(anysolver.__file__).resolve().is_relative_to(solver.resolve())
    assert Path(anymaterial.__file__).resolve()==Path('C:/Github/ANYmaterial/src/anymaterial/__init__.py').resolve()
    assert sha(anymaterial.__file__)=='46d9c80639435e40c8533d78d89364c51f1cef65969b1c418eab4f36a7512900'
    for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
        assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve())
    assert effective['affinity']==[0] and effective['numba_threads']==1 and effective['jit_off']
    assert all(p['num_threads']==1 for p in effective['pools']) and os.environ.get('OPENBLAS_CORETYPE') is None
    source={str(p.relative_to(REPO/'src')).replace('\\','/'):sha(p) for p in (REPO/'src/anysolver').rglob('*.py')}
    write('source-binding.json',source)
    if mode=='installed':
        import zipfile
        wheel=next((RAW/'wheel-v1').glob('*.whl'))
        with zipfile.ZipFile(wheel) as archive:
            payload={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('anysolver/') and name.endswith('.py')}
        installed={str(p.relative_to(solver)).replace('\\','/'):sha(p) for p in (solver/'anysolver').rglob('*.py')}
        assert source==payload==installed
        write('artifact-binding.json',dict(wheel=str(wheel),wheel_sha256=sha(wheel),payload=payload,site=str(solver)))
    selectors=json.loads((RAW/(attempt+'-selectors.json')).read_text())
    write('selectors.json',selectors)
    inputs={}
    for s in selectors:
        p=Path(s.split('::')[0]);inputs[str(p)]=sha(p)
        shutil.copy2(p,folder/p.name)
    for p in (inputs_root/'examples').glob('stiffened_shell_native*fibre*bl5*.py'):
        inputs[str(p)]=sha(p);shutil.copy2(p,folder/p.name)
    p=inputs_root/'examples/stiffened_shell_native_material_bl5_arc.py';inputs[str(p)]=sha(p);shutil.copy2(p,folder/p.name)
    write('inputs.json',inputs)
    import pytest
    class Reports:
        def pytest_runtest_logreport(self,report):
            with (folder/'case-reports.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,duration=report.duration,detail=str(report.longrepr) if report.failed else None))+'\n')
    ready.set()
    code=pytest.main(['-q','-c',str(REPO/'pyproject.toml'),'-o','pythonpath=','--basetemp',str(folder/'temp'),'--junitxml='+str(folder/'junit.xml'),*selectors],plugins=[Reports()])
    loaded={name:dict(path=m.__file__,sha256=sha(m.__file__)) for name,m in sys.modules.items() if getattr(m,'__file__',None) and Path(m.__file__).is_file() and (name.startswith(('anysolver','anymaterial','anymesh','anygeometry','anyfile','numpy','scipy','numba','llvmlite','examples')))}
    write('loaded-modules.json',loaded)
    assert all(Path(row['path']).resolve().is_relative_to(solver.resolve()) for name,row in loaded.items() if name.startswith('anysolver'))
    for name,row in loaded.items():
        if name.startswith('anysolver'):
            key=str(Path(row['path']).relative_to(solver)).replace('\\','/')
            assert row['sha256']==source[key]
    if mode=='installed':
        assert all(Path(row['path']).resolve().is_relative_to(inputs_root.resolve()) for name,row in loaded.items() if name.startswith('examples') and Path(row['path']).suffix=='.py')
    after=runtime();write('runtime-after.json',after)
    assert after['affinity']==[0] and after['numba_threads']==1 and after['jit_off'] and all(p['num_threads']==1 for p in after['pools'])
    assert all(sha(p)==digest for p,digest in inputs.items())
    raise SystemExit(code)
finally:
    stop.set();thread.join(timeout=1);write('rss-samples.json',samples)
    write('resource-summary.json',dict(peak_tree_rss=max((s['rss'] for s in samples),default=0),samples=len(samples),affinity_setup_events=affinity_events))




