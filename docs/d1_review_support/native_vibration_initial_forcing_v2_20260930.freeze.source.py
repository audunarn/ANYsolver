"""Metadata-only freeze of the authorized zero-step initial-state check."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

directory = Path('C:/ANYworkspaceWork/ANYsolver-general-contact/docs/d1_review_support')
stem = directory/'native_vibration_initial_forcing_v2_20260930'
previous = json.loads((directory/'native_vibration_v3_20260930.inputs.json').read_text(encoding='utf-8-sig'))
root = Path(previous['managed_worktree'])
hashes = dict(previous['source_sha256'])
for path, expected in hashes.items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
test = root/'tests/test_ge_beam3_native_vibration_initial_forcing.py'
test_hash = sha256(test.read_bytes()).hexdigest()
assert test_hash == '279696cad1faad048bb590af0c2dff876a2cd5d78e7bbf5fb4afc39bd4dcde41'
assert test.read_bytes() == Path(str(stem)+'.test.source.py').read_bytes()
hashes[test.as_posix()] = test_hash
assert len(hashes) == 440
historical = {}
expected_history = {
    'v2_raw': '705b627848aef2df9ce17cdce2dda937ea1ae29d1031a855f48ff567181248f7',
    'v2_input': '07b3f12777cd21ed5932fe14f51ec3254ba1796f6627d3ce8373be4c2996926d',
    'v3_raw': 'a6e22cc0d4c8ff41cb700b2bdaf5163e67feae601534c5265c6a1aa0390baa43',
    'v3_input': '95b7e2d6aa22c7cabc1c8ee0ceb17e76e659152ad6b4673d9542c7f62e550589',
}
for label, expected in expected_history.items():
    version, kind = label.split('_')
    path = directory/('native_vibration_'+version+'_20260930.'+('raw.json' if kind == 'raw' else 'inputs.json'))
    assert sha256(path.read_bytes()).hexdigest() == expected
    historical[label+'_path'] = path.as_posix()
    historical[label+'_sha256'] = expected
historical['historical_bindings_verified'] = 439
historical['old_temporal_disposition'] = 'NONPASS; no timestep replay or regrade'
environment = {key: value.replace('native_vibration_v3_20260930', stem.name)
               for key, value in previous['environment'].items()}
Path(environment['NUMBA_CACHE_DIR']).mkdir(exist_ok=False)
inputs = dict(managed_worktree=root.as_posix(), historical=historical, environment=environment,
    source_sha256=hashes, maximum_new_steps=0, internal_time_limit_seconds=120,
    time_limit_seconds=180, memory_limit_bytes=1073741824,
    contract_sha256=sha256((directory/'D6_NATIVE_MIDPOINT_DEVELOPMENT_20260930.md').read_bytes()).hexdigest(),
    criteria=dict(quadratic_relative_limit=0.01, resolution_multiplier=20,
                  initial_scaled_residual_limit=1e-11, gamma_operations=256,
                  full_amplitude=1e-4, half_amplitude=5e-5),
    scope='Consistent initial states only; all15 modal acceleration remainders; no new eigen or timestep evaluation',
    pytest_args=[test.as_posix(), '-q', '-o', 'junit_family=xunit1', '--junitxml='+str(stem)+'.xml'])
input_path = Path(str(stem)+'.inputs.json')
with input_path.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(inputs, indent=2)+'\n')
input_hash = sha256(input_path.read_bytes()).hexdigest()
entry = (directory/'native_vibration_v3_20260930.entry.source.py').read_text()
entry = entry.replace('native_vibration_v3_20260930', stem.name)
entry = entry.replace('95b7e2d6aa22c7cabc1c8ee0ceb17e76e659152ad6b4673d9542c7f62e550589', input_hash)
entry_path = Path(str(stem)+'.entry.source.py')
with entry_path.open('x', encoding='utf-8') as stream:
    stream.write(entry)
for label, relative in (('midpoint', 'src/anysolver/_ge_beam3_native_midpoint.py'),
                        ('dynamic', 'src/anysolver/_ge_beam3_dynamic_elastic_state.py'),
                        ('inertia', 'src/anysolver/_ge_beam3_centered_finite_inertia.py'),
                        ('fixture', 'tests/test_ge_beam3_native_midpoint.py')):
    target = Path(str(stem)+'.'+label+'.source.py')
    assert not target.exists()
    shutil.copyfile(root/relative, target)
print(json.dumps(dict(test_sha256=test_hash, input_sha256=input_hash,
                      entry_sha256=sha256(entry_path.read_bytes()).hexdigest(),
                      contract_sha256=inputs['contract_sha256'], source_count=len(hashes), steps=0)))
