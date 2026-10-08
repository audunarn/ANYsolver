"""Frozen environment-only D6 v2 entry; source/test mechanics unchanged."""
import hashlib
import inspect
import json
import os
from pathlib import Path

directory = Path(__file__).resolve().parent
inputs = json.loads((directory/"d6_centered_finite_inertia_v3_20260930.inputs.json").read_text())
for name, expected in inputs["environment"].items():
    assert os.environ.get(name) == expected, (name, os.environ.get(name), expected)
for path, expected in inputs["source_sha256"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
print(json.dumps(dict(stage="effective_environment_preimport", environment=inputs["environment"])), flush=True)

import anysolver
from anysolver._ge_beam3_centered_finite_inertia import evaluate_centered_finite_inertia
module = Path(inspect.getsourcefile(evaluate_centered_finite_inertia)).resolve()
expected = Path(inputs["managed_worktree"])/"src/anysolver/_ge_beam3_centered_finite_inertia.py"
assert module == expected
assert Path(anysolver.__file__).resolve().parent == expected.parent
cache = Path(os.environ["NUMBA_CACHE_DIR"]).resolve()
assert cache.is_dir(), cache
print(json.dumps(dict(stage="effective_import_verified", module=str(module),
    module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
    anysolver=anysolver.__file__, numba_cache_dir=str(cache),
    numba_cache_directory_present=cache.is_dir())), flush=True)

import pytest
raise SystemExit(pytest.main(inputs["pytest_args"]))
