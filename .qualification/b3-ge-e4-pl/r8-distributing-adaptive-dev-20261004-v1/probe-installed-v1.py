from pathlib import Path
import hashlib, importlib.metadata, json, os, sys, time
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SITE = ROOT / 'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(SITE)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT'] == '1'
# Import numerical runtime before observing its effective pools.
import numpy, scipy.linalg
pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
sources = {}
for path in (SITE / 'anysolver').rglob('*.py'):
    relative = path.relative_to(SITE)
    assert path.read_bytes() == (REPO / 'src' / relative).read_bytes(), relative
    sources[str(relative).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
names = (
    'test_stiffened_shell_distributing_adaptive.py',
    'test_stiffened_shell_increment_control.py',
    'test_stiffened_shell_accepted_observer_experimental.py',
    'test_stiffened_shell_ge_distributing_finite_public.py',
    'test_stiffened_shell_ge_distributing_material.py',
    'test_stiffened_shell_material_rotation_numerics.py',
)
tests = [str(REPO / 'tests' / name) for name in names]
record = dict(scope='installed development slice, not mechanics qualification',
    sources=sources, pools=pools, tests={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in tests},
    wheel_sha256=hashlib.sha256((ROOT / 'dist-v1/anysolver-0.4.7-py3-none-any.whl').read_bytes()).hexdigest(),
    dependencies={name:importlib.metadata.version(name) for name in ('ANYsolver','ANYmaterial','numpy','scipy','pytest')})
out = ROOT / 'installed-runtime-v1.json'
out.open('x', encoding='utf-8').write(json.dumps(record, indent=2) + '\n')
started = time.monotonic()
status = pytest.main(['-q', *tests, '-p', 'no:cacheprovider', '--basetemp', str(ROOT / 'pytest-v1')])
record.update(exit_code=int(status), checks_seconds=time.monotonic()-started)
record['imported_paths'] = {name:module.__file__ for name,module in sys.modules.items()
    if (name == 'anysolver' or name.startswith('anysolver.')) and getattr(module,'__file__',None)}
assert all(Path(path).resolve().is_relative_to(SITE) for path in record['imported_paths'].values())
out.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
raise SystemExit(status)
