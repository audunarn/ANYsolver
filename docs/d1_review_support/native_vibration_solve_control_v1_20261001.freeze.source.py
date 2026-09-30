"""Freeze the isolated source impact and two independently selected checks."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

folder = Path('C:/ANYworkspaceWork/ANYsolver-general-contact/docs/d1_review_support')
prior = json.loads((folder/'native_vibration_small_control_v1_20261001.inputs.json').read_text())
root = Path(prior['managed_worktree'])
owner = root/'src/anysolver/_ge_beam3_native_midpoint.py'
old_hash = '5931f8d1d5c123e85acaf22bb58ec94a80f4dd86f8e2beeba76f7149a143526c'
new_hash = '36da82603885f6f110adf40404331a5d519c7dccbe284dc67bb93ec44f75d1ac'
hashes = dict(prior['source_sha256'])
assert len(hashes) == 441 and hashes[owner.as_posix()] == old_hash
for path, expected in hashes.items():
    if path == owner.as_posix():
        expected = new_hash
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
hashes[owner.as_posix()] = new_hash
test = root/'tests/test_ge_beam3_native_vibration_solve_control.py'
test_hash = sha256(test.read_bytes()).hexdigest()
assert test_hash == '8561378f9e3d7cad1296fb702571709d5cbc60d4909e519998294c9cba9ac569'
hashes[test.as_posix()] = test_hash
assert len(hashes) == 442
historical = dict(prior['historical'])
historical.update(small_control_raw_path=(folder/'native_vibration_small_control_v1_20261001.raw.json').as_posix(),
    small_control_raw_sha256='6546ec7c5d7acbf2956a4aa9756a7a04504009e6f246c4c42b2dc6457d875c5d',
    small_control_input_path=(folder/'native_vibration_small_control_v1_20261001.inputs.json').as_posix(),
    small_control_input_sha256='9bb06c066c1521004a4b7f0c70f3a72be87c5374baf04b8fd32f03e005fa68ed')
for label in ('v2', 'v3', 'initial_forcing', 'small_control'):
    for kind in ('raw', 'input'):
        assert sha256(Path(historical[label+'_'+kind+'_path']).read_bytes()).hexdigest() == historical[label+'_'+kind+'_sha256']
impact = {owner.as_posix(): dict(historical_sha256=old_hash, current_sha256=new_hash,
    scope='Explicit identity/operation-bound stage residual tolerance and read-only authenticated candidate audit; mechanics unchanged')}
contract_hash = sha256((folder/'D6_NATIVE_MIDPOINT_DEVELOPMENT_20260930.md').read_bytes()).hexdigest()
for name, selector, steps in (
    ('native_vibration_solve_identity_v1_20261001', 'test_explicit_stage_tolerance_default_identity_and_guard', 0),
    ('native_vibration_solve_control_v1_20261001', 'test_explicit_tighter_solve_with_authenticated_stage_impulse_audit', 20)):
    stem = folder/name
    environment = {key: value.replace('native_vibration_small_control_v1_20261001', name)
                   for key, value in prior['environment'].items()}
    Path(environment['NUMBA_CACHE_DIR']).mkdir(exist_ok=False)
    inputs = dict(managed_worktree=root.as_posix(), historical=historical, environment=environment,
        source_sha256=hashes, source_impact=impact, maximum_new_steps=steps,
        stage_residual_tolerance=1e-15, internal_time_limit_seconds=120,
        time_limit_seconds=180, memory_limit_bytes=1073741824,
        contract_sha256=contract_hash, criteria=prior['criteria'],
        scope='Focused default/identity check only' if steps == 0 else
            'Same smaller-amplitude mechanics/gates at explicit tighter solve; signed before-commit stage audit',
        pytest_args=[test.as_posix()+'::'+selector, '-q', '-o', 'junit_family=xunit1', '--junitxml='+str(stem)+'.xml'])
    input_path = Path(str(stem)+'.inputs.json')
    with input_path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(inputs, indent=2)+'\n')
    input_hash = sha256(input_path.read_bytes()).hexdigest()
    entry = (folder/'native_vibration_small_control_v1_20261001.entry.source.py').read_text()
    entry = entry.replace('native_vibration_small_control_v1_20261001', name)
    entry = entry.replace('9bb06c066c1521004a4b7f0c70f3a72be87c5374baf04b8fd32f03e005fa68ed', input_hash)
    entry_path = Path(str(stem)+'.entry.source.py')
    with entry_path.open('x', encoding='utf-8') as stream:
        stream.write(entry)
    for label, path in (('midpoint', owner), ('test', test),
        ('dynamic', root/'src/anysolver/_ge_beam3_dynamic_elastic_state.py'),
        ('inertia', root/'src/anysolver/_ge_beam3_centered_finite_inertia.py'),
        ('fixture', root/'tests/test_ge_beam3_native_midpoint.py')):
        target = Path(str(stem)+'.'+label+'.source.py')
        if target.exists():
            assert target.read_bytes() == path.read_bytes()
        else:
            shutil.copyfile(path, target)
    print(json.dumps(dict(stem=name, source_count=len(hashes), source_sha256=new_hash,
        test_sha256=test_hash, input_sha256=input_hash,
        entry_sha256=sha256(entry_path.read_bytes()).hexdigest(), maximum_steps=steps)))
