"""One frozen 12-step loaded finite-motion native development discriminator."""
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path

inputs = json.loads(Path(__file__).with_name('d6_native_loaded_temporal_v2_20260930.inputs.json').read_text())
for key, expected in inputs['environment'].items():
    assert os.environ.get(key) == expected, (key, os.environ.get(key), expected)
for path, expected in inputs['source_sha256'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
print(json.dumps(dict(stage='effective_environment_preimport', environment=inputs['environment'],
    source_file_count=len(inputs['source_sha256']))), flush=True)
import anysolver
from anysolver._ge_beam3_native_midpoint import MidpointContext
from anysolver._ge_beam3_dynamic_elastic_state import DynamicElasticContext
from anysolver._ge_beam3_centered_finite_inertia import evaluate_centered_finite_inertia
root = Path(inputs['managed_worktree']).resolve()
assert Path(anysolver.__file__).resolve().parent == root/'src/anysolver'
paths = {}
for symbol, relative in ((MidpointContext, '_ge_beam3_native_midpoint.py'),
                        (DynamicElasticContext, '_ge_beam3_dynamic_elastic_state.py'),
                        (evaluate_centered_finite_inertia, '_ge_beam3_centered_finite_inertia.py')):
    path = Path(inspect.getsourcefile(symbol)).resolve()
    assert path == root/'src/anysolver'/relative
    paths[relative] = str(path)
assert Path(os.environ['NUMBA_CACHE_DIR']).is_dir()
print(json.dumps(dict(stage='effective_import_verified', anysolver=anysolver.__file__,
    module_paths=paths, cache=os.environ['NUMBA_CACHE_DIR'])), flush=True)
import pytest
raise SystemExit(pytest.main(inputs['pytest_args']))
