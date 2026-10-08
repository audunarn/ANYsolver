"""Verify effective imports/settings before focused consequence checks."""
from pathlib import Path
import hashlib, importlib, importlib.metadata, json, os, runpy, sys, time
import numpy as np
import pytest
from threadpoolctl import threadpool_info

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
kind = os.environ['R8_DISTRIBUTING_OWNER_KIND']
base = REPO/'src' if kind == 'source' else ROOT/'site'
names = ('stiffened_shell', '_stiffened_shell_ge_experimental',
    '_stiffened_shell_ge_distributing_reference', '_stiffened_shell_distributing_footprint',
    '_stiffened_shell_ge_body_load', '_stiffened_shell_ge_distributed_load',
    '_stiffened_shell_ge_pressure_load', '_stiffened_shell_ge_reference_modal')
modules = [importlib.import_module('anysolver.'+name) for name in names]
paths = [base/'anysolver'/(name+'.py') for name in names]
for module, path in zip(modules, paths):
    if Path(module.__file__).resolve() != path.resolve():
        raise ValueError('actual import differs from declared '+kind+' identity')
    source = REPO/'src/anysolver'/path.name
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
        raise ValueError('artifact/source file differs: '+path.name)
if sys.flags.optimize or os.environ.get('NUMBA_DISABLE_JIT') != '1':
    raise ValueError('unoptimized JIT-off checks required')
pools = threadpool_info()
if not pools or any(pool['num_threads'] != 1 for pool in pools):
    raise ValueError('effective numerical pools1 required')
tests = [REPO/'tests'/name for name in ('test_stiffened_shell_ge_distributing_owner.py',
    'test_stiffened_shell_ge_distributing_reference.py', 'test_stiffened_shell_ge_experimental.py')]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
record = dict(scope='experimental reference-linear owner; no scientific/release qualification',
    kind=kind, imports=[str(p) for p in paths], source_sha256={p.name:sha(p) for p in paths},
    test_sha256={p.name:sha(p) for p in tests}, effective_pools=pools, jit_disabled=True,
    versions={name:importlib.metadata.version(name) for name in
        ('numpy', 'scipy', 'pytest', 'ANYmaterial', 'ANYmesher', 'ANYfileio')})
if kind != 'source':
    wheel, = (ROOT/'dist').glob('*.whl')
    record['wheel'] = dict(path=str(wheel), sha256=sha(wheel), bytes=wheel.stat().st_size)
path = ROOT/(kind+'-runtime-v1.json')
path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
started = time.monotonic()
if kind == 'example':
    example = REPO/'examples/stiffened_shell_ge_distributing_reference.py'
    record['example_sha256'] = sha(example)
    runpy.run_path(str(example), run_name='__main__')
    status = 0
else:
    status = pytest.main(['-q', *map(str, tests), '-p', 'no:cacheprovider',
        '--basetemp', str(ROOT/(kind+'-pytest-v1'))])
record.update(exit_code=int(status), checks_seconds=time.monotonic()-started)
path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
raise SystemExit(status)
