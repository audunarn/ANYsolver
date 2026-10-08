"""Authenticate the once-only input before importing the solver or fixture."""
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

path = Path(sys.argv[1])
raw = path.read_bytes()
assert sha256(raw).hexdigest() == sys.argv[2]
spec = json.loads(raw)
os.environ.update(spec['environment'])
sys.path[:0] = spec['pythonpath']
for source, expected in spec['source_sha256'].items():
    assert sha256(Path(source).read_bytes()).hexdigest() == expected, source
for row in spec['historical'].values():
    assert sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
for target in spec['outputs'].values():
    assert not Path(target).exists(), target
print(json.dumps(dict(stage='authenticated_before_import', input_sha256=sha256(raw).hexdigest(),
    source_bindings=len(spec['source_sha256']))), flush=True)

import anysolver
import numpy as np
import pytest
from threadpoolctl import threadpool_info

assert Path(anysolver.__file__).resolve() == Path(spec['actual_anysolver_module']).resolve()
threads = threadpool_info()
assert threads and all(row['num_threads'] == 1 for row in threads)
identity = dict(input_sha256=sha256(raw).hexdigest(), module_file=anysolver.__file__,
    effective_environment={key: os.environ.get(key) for key in spec['environment']},
    threads=threads, source_bindings=len(spec['source_sha256']))
Path(spec['outputs']['environment']).write_text(json.dumps(identity, indent=2)+'\n', encoding='utf-8', newline='\n')
code = pytest.main([spec['test_source']+'::test_public_loaded_clamped_acceleration_split_restart',
    '-q', '-s', '--import-mode=importlib', '-p', 'no:cacheprovider',
    '--basetemp='+spec['basetemp'], '--junitxml='+spec['outputs']['xml']])
mismatches = [source for source, expected in spec['source_sha256'].items()
    if sha256(Path(source).read_bytes()).hexdigest() != expected]
identity.update(pytest_exit_code=int(code), post_source_mismatches=mismatches)
Path(spec['outputs']['environment']).write_text(json.dumps(identity, indent=2)+'\n', encoding='utf-8', newline='\n')
assert not mismatches
raise SystemExit(int(code))
