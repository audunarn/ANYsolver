from pathlib import Path
import hashlib,json,sys,zipfile
from importlib import metadata
import anysolver,numba,pytest,threadpoolctl
r=Path.cwd();w=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((r/'source-manifest.json').read_text())
assert all(sha(w/p)==h for p,h in source.items())
wheel=next((r/'wheels').glob('*.whl'))
with zipfile.ZipFile(wheel) as z:
    files={p for p in z.namelist() if p.startswith('anysolver/') and p.endswith('.py')}
    assert files=={p.replace('src/','',1) for p in source}
    assert all(z.read(p)==(r/'site'/p).read_bytes()==(w/'src'/p).read_bytes() for p in files)
pools=threadpoolctl.threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
(r/'identity.json').write_text(json.dumps({'wheel_sha256':sha(wheel),'matching_modules':len(files),
    'python':sys.version,'threads':pools,'numba_threads':1,'jit_disabled':True,
    'fixtures_sha256':{p.name:sha(p) for p in (r/'fixtures').glob('*.py')},
    'dependencies':{n:metadata.version(n) for n in ('numpy','scipy','numba','pytest','threadpoolctl','ANYmaterial','ANYmesher','ANYfileio')}},indent=2))
targets=['test_stiffened_shell_bl5_aggregation.py','test_stiffened_shell_bl5_finite.py',
         'test_stiffened_shell_bl5_local_experimental.py','test_stiffened_shell_l1_assembly_experimental.py']
code=pytest.main(['-q','-c',str(r/'pytest.ini'),'--junitxml='+str(r/'inventory.xml'),
                 *[str(r/'fixtures'/p) for p in targets]])
imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.copy().items()
         if n.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
(r/'imports.json').write_text(json.dumps(imports,indent=2))
assert all(Path(p).is_relative_to(r/'site') for p in imports.values())
print(json.dumps({'pytest_exit':code,'onsite_imports':len(imports)}),flush=True)
sys.exit(code)
