"""One new Fy load case on the already executed native80 geometry/operator."""
from pathlib import Path
import hashlib, importlib.metadata, json, os, sys, time, zipfile
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from scripts.r8_e02_distributing_feasibility import _native_load_cases
from scripts.r8_e02_distributing_native_adequacy import geometry

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = ROOT.parent / 'r8-distributing-multihost-dev-20261004-v1'
SITE = BASE / 'site'
WHEEL = BASE / 'dist/anysolver-0.4.7-py3-none-any.whl'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(WHEEL) == 'b7ae7ca03b92e98463a148c1ba30810a263d20bc68a81c32665d5f17c0526d9a'
assert Path(ss.__file__).resolve().is_relative_to(SITE)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools = threadpool_info()
assert pools and all(pool['num_threads']==1 for pool in pools)
prior = json.loads((ROOT.parent / 'r8-distributing-native-adequacy-dev-20261004-v1/binding.json').read_text())
for name, digest in prior['sources'].items():
    assert sha(REPO / name) == digest, name
installed = {}
with zipfile.ZipFile(WHEEL) as archive:
    for name in archive.namelist():
        if name.startswith('anysolver/') and name.endswith('.py'):
            raw = (SITE / name).read_bytes()
            assert raw == archive.read(name), name
            installed[name] = hashlib.sha256(raw).hexdigest()
bindings = dict(scope='new Fy RHS development only; prior Mx/My authority remains consumed',
    source_parent='bf3243dd', fixtures=prior['sources'], installed_files=installed,
    wheel=str(WHEEL), wheel_sha256=sha(WHEEL), pools=pools,
    dependencies={name:importlib.metadata.version(name) for name in ('ANYsolver','ANYmaterial','numpy','scipy')},
    reference='.qualification/b3-ge-e4-pl/r8-e02-double-output-dev-20261004-v1/fine-comparison-v1.json',
    excluded='no new mesh/external solve/criterion change/asymptotic pass/formalF03')
(ROOT / 'binding-v1.json').open('x').write(json.dumps(bindings,indent=2)+'\n')
started = time.monotonic()
record = dict(status='RUNNING', scope=bindings['scope'])
terminal = ROOT / 'terminal-v1.json'
terminal.open('x').write(json.dumps(record,indent=2)+'\n')
try:
    native = _native_load_cases(80,32,{'Fy':(0.,10.,0.,0.,0.,0.)},geometry_builder=geometry)
    assert set(native['results']) == {'Fy'}
    assert native['factors'] == 1
    result = native['results']['Fy']
    assert result['status'] == 'completed'
    record = dict(status='COMPLETED_DEVELOPMENT_ONLY', native=native, seconds=time.monotonic()-started)
    (ROOT / 'native-v1.json').open('x').write(json.dumps(record,indent=2,allow_nan=False)+'\n')
except BaseException as error:
    record = dict(status='FAILED', type=type(error).__name__, message=str(error), seconds=time.monotonic()-started)
    raise
finally:
    record['imported_paths'] = {name:mod.__file__ for name,mod in sys.modules.items()
        if (name=='anysolver' or name.startswith('anysolver.')) and getattr(mod,'__file__',None)}
    assert all(Path(path).resolve().is_relative_to(SITE) for path in record['imported_paths'].values())
    terminal.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
print('One native80 Fy RHS completed; no qualification claim.')
