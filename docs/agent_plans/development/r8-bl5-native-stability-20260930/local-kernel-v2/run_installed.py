from pathlib import Path
import hashlib
import json
import runpy
import sys

root = Path.cwd()
site = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-accepted-observer-installed-v1\\site')
source = Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver')
files = sorted(source.rglob('*.py'))
assert len(files) == 387
for path in files:
    assert path.read_bytes() == (site/'anysolver'/path.relative_to(source)).read_bytes()
manifest = {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
    for p in root.rglob('*') if p.is_file() and p.suffix == '.py' and '__pycache__' not in p.parts}
(root/'identity.json').write_text(json.dumps(dict(product_modules_match=387,
    site=str(site),frozen_sha256=manifest),indent=2))
sys.argv = ['run_case.py','--output','result.json']
try:
    runpy.run_path(str(root/'run_case.py'), run_name='__main__')
finally:
    modules = {name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
        if name.startswith('anysolver') and getattr(module,'__file__',None)}
    (root/'imports.json').write_text(json.dumps(modules,indent=2))
    assert modules and all(Path(p).is_relative_to(site) for p in modules.values())
