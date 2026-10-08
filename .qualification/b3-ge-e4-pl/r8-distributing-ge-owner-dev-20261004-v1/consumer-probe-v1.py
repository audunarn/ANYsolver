"""One fail-closed consumer guard against an installed new solver."""
from pathlib import Path
import hashlib, json, os, sys
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as api
import anyfem.solve.stiffened_shell as consumer

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
test = REPO/'tests/test_stiffened_shell_ge_reference_modal_consumer.py'
paths = (ROOT/'site/anysolver/stiffened_shell.py', REPO/'src/anyfem/solve/stiffened_shell.py')
for module, path in zip((api, consumer), paths):
    if Path(module.__file__).resolve() != path.resolve():
        raise ValueError('installed solver/source consumer imports required')
if 'distributing_footprints' not in api.LinearDefinition.__dataclass_fields__:
    raise ValueError('new distributing definition field required; no skipped branch')
pools = threadpool_info()
if not pools or any(p['num_threads'] != 1 for p in pools) or sys.flags.optimize or os.environ.get('NUMBA_DISABLE_JIT') != '1':
    raise ValueError('effective pools1/unoptimized/JIT-off required')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
record = dict(scope='source ANYfem guard against installed new solver, not full consumer qualification',
    imports=[str(p) for p in paths], source_sha256={str(p):sha(p) for p in paths},
    tests_sha256=sha(test), effective_pools=pools, new_field_verified=True)
status = pytest.main(['-q', str(test)+'::test_from_definition_rejects_unverified_attachment_and_material_scope',
    '-p', 'no:cacheprovider', '--basetemp', str(ROOT/'consumer-pytest-v1')])
record['exit_code'] = int(status)
(ROOT/'consumer-runtime-v1.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
raise SystemExit(status)
