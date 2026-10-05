from pathlib import Path
import hashlib,json,sys,zipfile,xml.etree.ElementTree as ET
import numpy as np,numba,pytest,threadpoolctl
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
manifest=json.loads((root/'input-manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source={'anysolver':Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver'),'anyfem':Path(r'C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src/anyfem')}
for name,files in manifest['modules'].items():
    wheel=next((root/'wheels').glob(name+'-*.whl'));assert sha(wheel)==manifest['wheels'][wheel.name]
    with zipfile.ZipFile(wheel) as z:
        assert {p for p in z.namelist() if p.startswith(name+'/') and p.endswith('.py')}==set(files)
        for key,h in files.items():
            src=source[name]/key.split('/',1)[1]
            assert src.read_bytes()==z.read(key)==(site/key).read_bytes() and sha(src)==h
for name,h in manifest['fixtures'].items():assert sha(root/'fixtures'/name)==h
pools=threadpoolctl.threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
(root/'identity.json').write_text(json.dumps({'modules':{k:len(v) for k,v in manifest['modules'].items()},'wheels':manifest['wheels'],'python':sys.version,'threads':pools,'jit_disabled':True,'numba_threads':1},indent=2))
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp='+str(root/'pytest-tmp'),'--junitxml='+str(root/'inventory.xml'),str(root/'fixtures/test_stiffened_shell_staged_load_consumer.py'),str(root/'fixtures/test_stiffened_shell_project.py'),str(root/'fixtures/test_installed_staged_project_route.py')])
imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.copy().items() if n.split('.')[0] in ('anysolver','anyfem') and getattr(m,'__file__',None)}
(root/'imports.json').write_text(json.dumps(imports,indent=2))
assert all(Path(p).is_relative_to(site) for p in imports.values())
cases=ET.parse(root/'inventory.xml').findall('.//testcase');counts={k:sum(c.find(k) is not None for c in cases) for k in ('failure','error','skipped')}
(root/'verification.json').write_text(json.dumps({'cases':len(cases),'counts':counts,'exit_code':code,'onsite_imports':len(imports)},indent=2))
print(json.dumps({'cases':len(cases),'counts':counts,'onsite_imports':len(imports)}),flush=True)
assert code==0 and not any(counts.values())
