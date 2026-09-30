"""Frozen one-test native vibration entry; no previous temporal replay."""
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import sys
import time

STEM = Path('C:/ANYworkspaceWork/ANYsolver-general-contact/docs/d1_review_support/native_dynamic_interface_v3_20261001')
input_path = Path(str(STEM)+'.inputs.json')
assert sha256(input_path.read_bytes()).hexdigest() == 'a350502f87a436b2daa6d82b12127fc4f29a86cf5ba125413df7cafc75f5611b'
inputs = json.loads(input_path.read_text(encoding='utf-8-sig'))
for key, value in inputs['environment'].items():
    assert os.environ.get(key) == value, (key, os.environ.get(key), value)
for path, expected in inputs['source_sha256'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
root = Path(inputs['managed_worktree']).resolve()
assert Path.cwd().resolve() == root
cache = Path(os.environ['NUMBA_CACHE_DIR'])
assert cache.is_dir()
probe = cache/'effective_writability.probe'
with probe.open('x', encoding='utf-8') as stream:
    stream.write('writable')
probe.unlink()
print(json.dumps(dict(stage='effective_environment_preimport', environment=inputs['environment'],
                     source_file_count=len(inputs['source_sha256']))), flush=True)
import anysolver
from anysolver.ge_beam3_native_dynamics import create_analysis
from anysolver._ge_beam3_native_midpoint import MidpointContext
from anysolver._ge_beam3_dynamic_elastic_state import DynamicElasticContext
from anysolver._ge_beam3_centered_finite_inertia import evaluate_centered_finite_inertia
assert Path(anysolver.__file__).resolve().parent == root/'src/anysolver'
paths = {}
for symbol, relative in ((create_analysis, 'ge_beam3_native_dynamics.py'),
                        (MidpointContext, '_ge_beam3_native_midpoint.py'),
                        (DynamicElasticContext, '_ge_beam3_dynamic_elastic_state.py'),
                        (evaluate_centered_finite_inertia, '_ge_beam3_centered_finite_inertia.py')):
    actual = Path(inspect.getsourcefile(symbol)).resolve()
    assert actual == root/'src/anysolver'/relative
    paths[relative] = str(actual)
import numpy
import pytest
identity = dict(anysolver=anysolver.__file__, module_paths=paths, python=sys.executable,
                numpy_version=numpy.__version__, pytest_version=pytest.__version__,
                environment=inputs['environment'], source_count=len(inputs['source_sha256']),
                input_sha256=sha256(input_path.read_bytes()).hexdigest(),
                entry_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
print(json.dumps(dict(stage='effective_import_verified', identity=identity)), flush=True)
reports = []
class Reports:
    def pytest_runtest_logreport(self, report):
        reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                            duration_seconds=report.duration, properties=dict(report.user_properties),
                            failure=str(report.longrepr) if report.failed else None))
started = time.perf_counter()
result = pytest.main(inputs['pytest_args'], plugins=[Reports()])
with Path(str(STEM)+'.execution.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(status='PASS' if result == 0 else 'NONPASS', exit_code=int(result),
                   elapsed_seconds=time.perf_counter()-started, identity=identity,
                   reports=reports), stream, indent=2)
    stream.write('\n')
raise SystemExit(result)


