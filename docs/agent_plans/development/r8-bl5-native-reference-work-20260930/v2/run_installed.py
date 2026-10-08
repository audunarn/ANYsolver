from pathlib import Path
import hashlib,json,runpy,sys
import anysolver
r=Path.cwd();source=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling');site=Path(r'C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-aggregation-installed-v1/site');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((r/'source-manifest.json').read_text());assert all(sha(source/p)==h==sha(site/p.replace('src/','',1)) for p,h in s.items())
identity={'product_modules_match':len(s),'site':str(site),'source_parent':'7987074bf9cbb420926c54ecf6e618fa25e84a05','frozen_files_sha256':{str(p.relative_to(r)):sha(p) for p in sorted(r.rglob('*.py'))}}
(r/'identity.json').write_text(json.dumps(identity,indent=2))
sys.argv=['run_case.py','--output','result.json'];runpy.run_path(str(r/'run_case.py'),run_name='__main__')
imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.copy().items() if n.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(site) for p in imports.values());(r/'imports.json').write_text(json.dumps(imports,indent=2));print(json.dumps({'onsite_imports':len(imports)}))
