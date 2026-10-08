from pathlib import Path
import hashlib, importlib.metadata, importlib.util, json, os, sys, time
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer

ROOT = Path(__file__).resolve().parent
SOLVER = ROOT.parents[2]
FEM = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
SITE = ROOT / 'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(SITE)
assert Path(consumer.__file__).resolve().is_relative_to(SITE)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT'] == '1'
import numpy, scipy.linalg
pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
sources = {}
for name, repo in (('anysolver', SOLVER), ('anyfem', FEM)):
    for path in (SITE / name).rglob('*.py'):
        relative = path.relative_to(SITE)
        assert path.read_bytes() == (repo / 'src' / relative).read_bytes(), relative
        sources[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
solver_names = (
    'test_stiffened_shell_distributing_cyclic.py',
    'test_stiffened_shell_distributing_adaptive.py',
    'test_stiffened_shell_increment_control.py',
    'test_stiffened_shell_accepted_observer_experimental.py',
    'test_stiffened_shell_ge_distributing_finite_public.py',
    'test_stiffened_shell_ge_distributing_material.py')
fem_names = (
    'test_stiffened_shell_ge_distributing_cyclic_consumer.py',
    'test_stiffened_shell_ge_distributing_material_consumer.py',
    'test_stiffened_shell_ge_finite_distributing_consumer.py',
    'test_stiffened_shell_ge_distributing_consumer.py',
    'test_stiffened_shell_ge_reference_modal_consumer.py')
tests = [str(SOLVER / 'tests' / n) for n in solver_names] + [str(FEM / 'tests' / n) for n in fem_names]
record = dict(scope='installed cyclic development slice, not aggregate mechanics qualification',
    sources=sources, pools=pools, tests={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in tests},
    artifacts=json.loads((ROOT / 'artifact-v1.json').read_text())['artifacts'],
    dependencies={n:importlib.metadata.version(n) for n in ('ANYsolver','ANYfem','ANYmaterial','numpy','scipy','pytest')})
out = ROOT / 'installed-runtime-v1.json'
out.open('x', encoding='utf-8').write(json.dumps(record, indent=2) + '\n')
started = time.monotonic()
status = pytest.main(['-q', *tests, '-p', 'no:cacheprovider', '--basetemp', str(ROOT / 'pytest-v1')])
record.update(exit_code=int(status), checks_seconds=time.monotonic()-started)
record['imported_paths'] = {n:mod.__file__ for n,mod in sys.modules.items()
    if (n == 'anysolver' or n.startswith('anysolver.') or n == 'anyfem' or n.startswith('anyfem.'))
    and getattr(mod,'__file__',None)}
assert all(Path(p).resolve().is_relative_to(SITE) for p in record['imported_paths'].values())
out.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
if status:
    raise SystemExit(status)
sys.path.insert(0, str(FEM / 'examples'))
example = FEM / 'examples/stiffened_shell_ge_distributing_cyclic_consumer.py'
s = importlib.util.spec_from_file_location('cyclic_example', example)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
started = time.monotonic()
result = m.workflow(ROOT / 'example-v1')
record.update(example_seconds=time.monotonic()-started,
    example_sha256=hashlib.sha256(example.read_bytes()).hexdigest(), example=result)
out.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print('Installed cyclic consumer example completed with exact zero-load restart.')
