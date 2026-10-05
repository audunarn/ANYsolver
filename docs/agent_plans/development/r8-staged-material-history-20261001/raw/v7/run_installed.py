from pathlib import Path
import hashlib,json,sys,zipfile
from importlib import metadata
import anysolver,numba,pytest,threadpoolctl
r=Path.cwd(); old=r.parent/'r8-staged-load-installed-v1'; site=old/'site'
w=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((old/'source-manifest.json').read_text())
assert all(sha(w/p)==h for p,h in source.items())
wheel=next((old/'wheels').glob('*.whl'))
assert sha(wheel)=='0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c'
with zipfile.ZipFile(wheel) as z:
    files={p for p in z.namelist() if p.startswith('anysolver/') and p.endswith('.py')}
    assert files=={p.replace('src/','',1) for p in source}
    assert all(z.read(p)==(site/p).read_bytes()==(w/'src'/p).read_bytes() for p in files)
pools=threadpoolctl.threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.get_num_threads()==1
(r/'identity.json').write_text(json.dumps({'wheel_sha256':sha(wheel),'matching_modules':len(files),
    'python':sys.version,'site':str(site),'threads':pools,'numba_threads':numba.get_num_threads(),'jit_disabled':True,
    'fixtures_sha256':{p.name:sha(p) for p in (r/'fixtures').glob('*.py')},
    'dependencies':{n:metadata.version(n) for n in ('numpy','scipy','numba','pytest','threadpoolctl','ANYmaterial','ANYmesher','ANYfileio')}},indent=2))
case=sys.argv[1]
target=r/'fixtures'/'test_stiffened_shell_staged_material_history.py'
code=pytest.main(['-q','-c',str(r/'pytest.ini'),'--basetemp='+str(r/(case+'-states')),
                 '--junitxml='+str(r/(case+'-inventory.xml')),str(target) if case=='all' else str(target)+'::'+case])
imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.copy().items()
         if n.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
(r/(case+'-imports.json')).write_text(json.dumps(imports,indent=2))
assert all(Path(p).is_relative_to(site.resolve()) for p in imports.values())
assert numba.get_num_threads()==1 and all(p['num_threads']==1 for p in threadpoolctl.threadpool_info())
print(json.dumps({'pytest_exit':code,'onsite_imports':len(imports),'case':case}),flush=True)
sys.exit(code)

