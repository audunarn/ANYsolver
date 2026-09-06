"""Immutable completed diagnostic inspection only; never runs beam mechanics."""

from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_centered_chord32_diagnostic as d


ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-centered-chord32-20260906-e919f22758c948f5b22dbfcbd0b1fd3a')
FILES = {
    'diagnostic.json': (4614, '3ee2e125eec84984a3823105bb997741e83d906ddbc9ea1d0d52cbd58fed0166'),
    'inputs.json': (4741, 'e66df2b6d24ad4d0bbc6cb7a138f98c6c5f21fc262564d186074f41374461a4c'),
    'centered-chord32/complete.json': (6727, '1808350fffa265535f3a40ab0115aeb3f8b1701aa8ab8d237ecd0078cb1c2e65'),
    'centered-chord32/failed_last.json': (1185851, '08329f11b7d7dd17566446f02da922fa008a9eb84ce7c709b264b4f293ab4422'),
    'centered-chord32/initial.json': (1157002, 'ae047a650282ba7f6870bf7b471372e85a6b2bbd831aec00d5eb4807c09e8cfa'),
    'centered-chord32/process-start.json': (386, '819365136fd96f83b4e4be9e0a0fe8e3673a674d2ec2cd7d19d06f3feb7d4242'),
    'centered-chord32/process.json': (99, '25ff01c0f31a6bd16b16c8c1b469678116921e94da76d9789c68ecb4835b6881'),
    'centered-chord32/progress.jsonl': (36429, 'eadc50bab49cd41027a8d89d5867ad8b8dcbc90f5c61dab422245426701f8fcc'),
    'centered-chord32/stdout.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'centered-chord32/stderr.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
}


@pytest.fixture(scope='module')
def records():
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()} == set(FILES)
    for name, (size, sha) in FILES.items():
        data = d.shared.ordinary(ROOT/name)
        assert len(data) == size and d.shared.sha(data) == sha
    assert sum(size for size, _ in FILES.values()) == 2395849
    inputs = d.shared.load(ROOT/'inputs.json')
    frozen = inputs['authority']
    assert frozen['commit'] == 'ca472021b2a4557ec12cc9b6721358482cf33db2'
    assert frozen['tree'] == '149b15d2016cb7730f61cacd7cf8f782f3da5caa'
    assert frozen['failed_inputs'] == d.failed_inputs()
    assert frozen['observation_inputs'] == d.observation_inputs()
    assert frozen['force_inputs'] == d.force_inputs()
    packet, groups = d.inspect(ROOT/'centered-chord32', frozen,
        '1b6bdcd793404eae8d19435b708701d7',
        '44848dc057f3185e93f472f483fb50b8610254e2f555cd49f3257c2eeca9ee73')
    return packet, groups, d.shared.load(ROOT/'diagnostic.json')


def test_capture_success_is_not_solver_or_qualification_success(records):
    packet, groups, diagnostic = records
    assert packet['result']['solver_outcome'] == diagnostic['solver_outcome'] == 'FAILED'
    assert diagnostic['disposition'] == 'RESEARCH_CENTERED_CHORD_COMPARISON_CAPTURED'
    assert packet['result']['production_qualified'] is diagnostic['production_qualified'] is False
    assert diagnostic['restriction'] == 'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'
    assert {k: len(v) for k, v in groups.items()} == {'INITIAL': 3, 'TARGET': 81}
    assert packet['result']['failure']['mixed_evaluations'] == 4448
    assert packet['result']['failed_trial_uncommitted'] is True
    assert not (ROOT/'aggregate.json').exists()
    assert not (ROOT/'centered-chord32/target.json').exists()


def test_frozen_process_finished_within_limits(records):
    process = d.shared.load(ROOT/'centered-chord32/process.json')
    assert process['exit_code'] == 0
    assert 0 < process['wall_seconds'] < 600
    assert 0 < process['cpu_100ns']/1e7 < 600
    assert 0 < process['peak_tree_bytes'] < 24*(1 << 30)


def test_centering_did_not_resolve_assembled_acceptance(records):
    packet, _, _ = records
    last = packet['result']['failure']['checkpoints'][-1]
    assert last['iteration'] == 16
    assert last['residual'] == 1.3856836297712436e-11 > d.CASE['residual_limit']
    prior = d.shared.load(d.FORCE_ROOT/'force-accuracy32/complete.json')
    assert prior['result']['failure']['checkpoints'][-1]['residual'] < last['residual']
    raw = d.shared.load(ROOT/'centered-chord32/failed_last.json')
    assert raw['disposition'] == 'UNCOMMITTED_DIAGNOSTIC_ONLY'
    assert raw['replay_verified'] is True
    assert raw['residual_norm'] == last['residual']
    assert sum(e['estimated_force_error'] for e in raw['response']['elements']) < 1e-13
    # A small local linearized estimate is not a bound on all arithmetic error.
    assert raw['residual_norm'] > 1e-11
