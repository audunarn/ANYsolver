from pathlib import Path
import hashlib,importlib.metadata as metadata,json,os,runpy,sys,zipfile
import anysolver,anyfem,numba,pytest,threadpoolctl
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert all(sha(root/path)==digest for path,digest in manifest['inputs'].items())

artifacts={}
for name,source in (
    ('anysolver',Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver')),
    ('anyfem',Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src/anyfem'))):
    wheel=next((root/'wheels').glob(name+'-*.whl'))
    assert sha(wheel)==manifest['wheels'][wheel.name]
    sources={name+'/'+p.relative_to(source).as_posix():p for p in source.rglob('*.py')}
    with zipfile.ZipFile(wheel) as archive:
        paths={p for p in archive.namelist() if p.startswith(name+'/') and p.endswith('.py')}
        assert paths==set(sources)
        assert all(archive.read(p)==f.read_bytes()==(site/p).read_bytes() for p,f in sources.items())
    artifacts[name]={'wheel_sha256':sha(wheel),'matching_modules':len(sources),
        'source_module_sha256':{p:sha(f) for p,f in sources.items()}}
pools=threadpoolctl.threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
environment={'python':sys.version,'threads':pools,'numba_jit_disabled':bool(numba.config.DISABLE_JIT),
    'numba_threads':numba.config.NUMBA_NUM_THREADS,'dependencies':{name:metadata.version(name)
    for name in ('numpy','scipy','numba','pytest','ANYmaterial','ANYmesher','ANYfileio')}}
(root/'identity.json').write_text(json.dumps({'artifacts':artifacts,'environment':environment},indent=2))
print(json.dumps(environment),flush=True)
selected=[root/"tests"/name for name in ['test_stiffened_shell_bl5_finite.py','test_stiffened_shell_bl5_local_experimental.py','test_stiffened_shell_l1_assembly_experimental.py','test_stiffened_shell_increment_control.py','test_stiffened_shell_s3_stable_elastic.py', 'test_stiffened_shell_ge_experimental.py', 'test_stiffened_shell_ge_finite_experimental.py', 'test_stiffened_shell_ge_physical_fibre_finite.py', 'test_stiffened_shell_ge_physical_fibre_linear.py', 'test_stiffened_shell_native_coupled_material.py', 'test_stiffened_shell_native_fibre_energy.py']]
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--junitxml',str(root/'inventory.xml'),
    '--basetemp',str(root/'pytest-tmp')]+[str(p) for p in selected])
assert code==0,code
# Cross-version restoration must retain both bytes and original policy.
sys.path.insert(0,str(root/'tests'))
from test_stiffened_shell_ge_physical_fibre_linear import _definition
from anysolver._stiffened_shell_ge_experimental import NodalAction
legacy=(root/'legacy.checkpoint').read_bytes()
owner=anysolver.stiffened_shell.create_analysis(definition=_definition(False,True))
try:
    restored=owner.restore(legacy)
    assert owner.checkpoint()==legacy and not owner._finite_driver._stable_s3
    try:owner.solve((NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),),targets=(.5,))
    except RuntimeError as error:assert str(error)=='finite mixed backtrack budget exhausted'
    else:raise AssertionError('legacy continuation status changed')
    assert owner.checkpoint()==legacy and owner.recover() is restored
    (root/'compatibility.json').write_text(json.dumps({'schema':'legacy V7','byte_equal':True,'policy':'legacy translation','accepted_prefix':restored.accepted_factors,'failure':'same baseline backtrack exhaustion'},indent=2))
finally:owner.close()
reports={}
from scripts.experimental_stiffened_ge_bl5_history import run as line_example
for basis in ('p0','continuous_p1_coarse'):
    report=line_example(basis)
    assert report['status']=='completed' and report['restart_bytes_equal']
    assert Path(report['source']).resolve().is_relative_to(site)
    reports[basis]=report
(root/'examples.json').write_text(json.dumps(reports,indent=2))

loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
    if name.split('.')[0] in ('anysolver','anyfem') and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values())
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
print(json.dumps({'loaded_modules':len(loaded),'history_examples':len(reports)}),flush=True)
