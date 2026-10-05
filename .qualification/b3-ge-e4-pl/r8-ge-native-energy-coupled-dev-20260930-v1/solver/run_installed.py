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
selected=[root/"tests"/name for name in ['test_stiffened_shell_ge_experimental.py', 'test_stiffened_shell_ge_finite_experimental.py', 'test_stiffened_shell_ge_physical_fibre_finite.py', 'test_stiffened_shell_ge_physical_fibre_linear.py', 'test_stiffened_shell_native_fibre_energy.py', 'test_stiffened_shell_native_coupled_material.py', 'test_ge_beam3_fibre_cell.py', 'test_ge_beam3_retained_fibre.py']]
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--junitxml',str(root/'inventory.xml'),
    '--basetemp',str(root/'pytest-tmp')]+[str(p) for p in selected])
assert code==0,code
sys.path.insert(0,str(root/'scripts'))
example=runpy.run_path(str(root/'scripts/experimental_stiffened_ge_fibre_history.py'))
reports={name:example['run'](mixed) for name,mixed in (('physical',False),('mixed',True))}
for report in reports.values():
    assert report['status']=='completed' and not report['production_qualified']
    assert report['maximum_accumulated_fibre_strain']>0.
    assert report['maximum_last_fibre_plastic_increment']>0.
    assert report['equilibrium_ratio']<=1e-8 and report['constraint_max']<=1e-9
    assert report['restart_bytes_equal']
(root/'examples.json').write_text(json.dumps(reports,indent=2))
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
    if name.split('.')[0] in ('anysolver','anyfem') and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values())
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
print(json.dumps({'loaded_modules':len(loaded),'history_examples':len(reports)}),flush=True)
