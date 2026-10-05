from pathlib import Path
import json,hashlib,sys
import anysolver,numba,pytest,threadpoolctl
r=Path.cwd();m=json.loads((r/'manifest.json').read_text())
for p,h in m['inputs_sha256'].items():
 if '/site/' in p.replace(chr(92),'/'): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
assert all(p['num_threads']==1 for p in threadpoolctl.threadpool_info())
assert numba.config.DISABLE_JIT
code=pytest.main(['-q','-c',str(r/'pytest.ini'),'--junitxml='+str(r/'inventory.xml'),str(r/'fixtures/test_stiffened_shell_bl5_finite.py')])
imports={n:str(Path(v.__file__).resolve()) for n,v in sys.modules.copy().items() if n.split('.')[0]=='anysolver' and getattr(v,'__file__',None)}
assert all('r8-ge-point-native-project-installed-v1' in p for p in imports.values())
(r/'imports.json').write_text(json.dumps(imports,indent=2))
print(json.dumps({'status':'passed' if code==0 else 'failed','import_count':len(imports)}),flush=True)
sys.exit(code)
