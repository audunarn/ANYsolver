from pathlib import Path
import hashlib
import json
import runpy
import sys

root = Path.cwd()
site = Path('C:\\Users\\AUDUNA~1\\AppData\\Local\\Temp\\r8-accepted-observer-installed-v1\\site')
source = Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver')
files = sorted(source.rglob('*.py'))
assert len(files) == 387
for path in files:
    assert path.read_bytes() == (site/'anysolver'/path.relative_to(source)).read_bytes()
manifest = {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
    for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(root/'identity.json').write_text(json.dumps(dict(product_modules_match=387,
    site=str(site),frozen_sha256=manifest),indent=2))
import pytest, numba, threadpoolctl
pools=threadpoolctl.threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
(root/'effective-settings.json').write_text(json.dumps(dict(threadpools=pools,
    numba_threads=1,jit_disabled=True,python=sys.version),indent=2))
try:
    raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','test_case.py','--junitxml=checks.xml','-o','junit_family=legacy','--basetemp=snapshots']))
finally:
    modules = {name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
        if name.startswith('anysolver') and getattr(module,'__file__',None)}
    assert modules and all(Path(p).is_relative_to(site) for p in modules.values())
    (root/'imports.json').write_text(json.dumps(modules,indent=2))
