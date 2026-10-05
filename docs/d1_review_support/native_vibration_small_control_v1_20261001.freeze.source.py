"""Metadata-only freeze for the separately authorized small-amplitude control."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

directory = Path('C:/ANYworkspaceWork/ANYsolver-general-contact/docs/d1_review_support')
stem = directory/'native_vibration_small_control_v1_20261001'
previous = json.loads((directory/'native_vibration_initial_forcing_v2_20260930.inputs.json').read_text())
original = json.loads((directory/'native_vibration_v2_20260930.inputs.json').read_text(encoding='utf-8-sig'))
root = Path(previous['managed_worktree'])
hashes = dict(previous['source_sha256'])
assert len(hashes) == 440
for path, expected in hashes.items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
test = root/'tests/test_ge_beam3_native_vibration_small_control.py'
test_hash = sha256(test.read_bytes()).hexdigest()
assert test_hash == '07a7688302a3481729d7842ba943d4062c4db9d31898e55501b52c64d7b0c1e5'
assert test.read_bytes() == Path(str(stem)+'.test.source.py').read_bytes()
hashes[test.as_posix()] = test_hash
assert len(hashes) == 441
historical = dict(previous['historical'])
for kind, expected in (
    ('raw', '76b8f5e58b2b0a5af49cd901bd971ea0a3e35ce202e4fe0a899652f79bacefa7'),
    ('input', '92b60e2d12ccdc6344fc4772639da851197eb488bf32250aea0adbe6bee6209d')):
    path = directory/('native_vibration_initial_forcing_v2_20260930.'+('raw.json' if kind == 'raw' else 'inputs.json'))
    assert sha256(path.read_bytes()).hexdigest() == expected
    historical['initial_forcing_'+kind+'_path'] = path.as_posix()
    historical['initial_forcing_'+kind+'_sha256'] = expected
for label in ('v2', 'v3'):
    for kind in ('raw', 'input'):
        assert sha256(Path(historical[label+'_'+kind+'_path']).read_bytes()).hexdigest() == historical[label+'_'+kind+'_sha256']
historical['historical_bindings_verified'] = 440
environment = {key: value.replace('native_vibration_initial_forcing_v2_20260930', stem.name)
               for key, value in previous['environment'].items()}
Path(environment['NUMBA_CACHE_DIR']).mkdir(exist_ok=False)
inputs = dict(managed_worktree=root.as_posix(), historical=historical, environment=environment,
    source_sha256=hashes, maximum_new_steps=20, internal_time_limit_seconds=120,
    time_limit_seconds=180, memory_limit_bytes=1073741824,
    contract_sha256=sha256((directory/'D6_NATIVE_MIDPOINT_DEVELOPMENT_20260930.md').read_bytes()).hexdigest(),
    criteria=dict(original['criteria'], amplitude=2.5e-5),
    prospective_screen=dict(constant_remainder_all15_velocity_envelope=0.0012121975392984285,
                            constant_remainder_mode9_velocity_envelope=0.0011740276904275695,
                            model='Quadratic initial remainder scaling; constant forcing only, not a varying-forcing proof'),
    scope='New quarter-amplitude fixture; saved M/Ke/mode/virgin history only; no eigensolve or old endpoint replay',
    pytest_args=[test.as_posix(), '-q', '-o', 'junit_family=xunit1', '--junitxml='+str(stem)+'.xml'])
input_path = Path(str(stem)+'.inputs.json')
with input_path.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(inputs, indent=2)+'\n')
input_hash = sha256(input_path.read_bytes()).hexdigest()
entry = (directory/'native_vibration_initial_forcing_v2_20260930.entry.source.py').read_text()
entry = entry.replace('native_vibration_initial_forcing_v2_20260930', stem.name)
entry = entry.replace('92b60e2d12ccdc6344fc4772639da851197eb488bf32250aea0adbe6bee6209d', input_hash)
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
                      contract_sha256=inputs['contract_sha256'], source_count=len(hashes), maximum_steps=20)))
