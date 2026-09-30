"""Frozen single new D6 midpoint process entry and effective identity audit."""
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path

directory = Path(__file__).resolve().parent
inputs = json.loads((directory/'d6_native_midpoint_v2_20260930.inputs.json').read_text())
for key, value in inputs['environment'].items():
    assert os.environ.get(key) == value, (key, os.environ.get(key), value)
for path, value in inputs['source_sha256'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == value, path
print(json.dumps(dict(stage='effective_environment_preimport', environment=inputs['environment'])), flush=True)
import anysolver
from anysolver._ge_beam3_native_midpoint import MidpointContext
from anysolver._ge_beam3_centered_finite_inertia import evaluate_centered_finite_inertia
root = Path(inputs['managed_worktree']).resolve()
for symbol, relative in ((MidpointContext, '_ge_beam3_native_midpoint.py'),
                         (evaluate_centered_finite_inertia, '_ge_beam3_centered_finite_inertia.py')):
    assert Path(inspect.getsourcefile(symbol)).resolve() == root/'src/anysolver'/relative
assert Path(anysolver.__file__).resolve().parent == root/'src/anysolver'
assert Path(os.environ['NUMBA_CACHE_DIR']).is_dir()
print(json.dumps(dict(stage='effective_import_verified', anysolver=anysolver.__file__,
    midpoint=str(Path(inspect.getsourcefile(MidpointContext))),
    finite_inertia=str(Path(inspect.getsourcefile(evaluate_centered_finite_inertia))),
    cache=os.environ['NUMBA_CACHE_DIR'])), flush=True)
import pytest
raise SystemExit(pytest.main(inputs['pytest_args']))
