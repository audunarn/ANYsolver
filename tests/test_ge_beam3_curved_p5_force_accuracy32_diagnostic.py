"""Small observed solver paths and synthetic integrity checks; no 32 solve."""

import copy
from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_force_accuracy32_diagnostic as diagnostic
from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import DisplacementControlledAssemblyProbe


@pytest.fixture(scope='module')
def captures():
    result = {}
    original = DisplacementControlledAssemblyProbe.trial
    for fail in (False, True):
        rows, raws = [], {}
        def publish(name, raw):
            data = diagnostic.shared.canonical(raw);raws[name] = data
            return {'name': name+'.json', 'bytes': len(data), 'sha256': diagnostic.shared.sha(data)}
        def bounded(self, target, **kwargs):
            if target == .095: kwargs['max_iterations'] = 0
            return original(self, target, **kwargs)
        try:
            if fail: DisplacementControlledAssemblyProbe.trial = bounded
            made = diagnostic.capture(count=2, observe=rows.append, publish_raw=publish)
        finally:
            DisplacementControlledAssemblyProbe.trial = original
        result[fail] = (made, rows, raws)
    return result


def packet(tmp_path, captures, fail):
    result, rows, raws = copy.deepcopy(captures[fail])
    folder = tmp_path/'observed';folder.mkdir()
    for name, data in raws.items(): (folder/(name+'.json')).write_bytes(data)
    (folder/'progress.jsonl').write_bytes(b''.join(diagnostic.shared.canonical(r) for r in rows))
    made = {'schema': diagnostic.SCHEMA, 'authority': {}, 'request_id': 'a'*32, 'request_sha256': 'b'*64, 'result': result}
    diagnostic.shared.publish(folder/'complete.json', made)
    return folder, made, rows


@pytest.mark.parametrize('fail', [False, True])
def test_success_and_captured_failure_are_distinct_valid_diagnostics(tmp_path, captures, fail):
    folder, made, _ = packet(tmp_path, captures, fail)
    one, groups = diagnostic.inspect(folder, {}, 'a'*32, 'b'*64, count=2)
    assert one == made
    assert made['result']['solver_outcome'] == ('FAILED' if fail else 'TARGET_CONVERGED')
    assert made['result']['production_qualified'] is False
    assert (folder/'target.json').exists() is not fail
    assert groups['TARGET'][-1]['phase'] == ('FAILURE' if fail else 'CONVERGED')
    assert diagnostic.shared.canonical(one) == diagnostic.shared.canonical(diagnostic.inspect(folder, {}, 'a'*32, 'b'*64, count=2)[0])


@pytest.mark.parametrize('mutation', ['sequence', 'mixed_count', 'target', 'residual_components', 'acceptance',
    'nonfinite', 'key', 'interleave', 'terminal', 'checkpoint', 'digest', 'outcome', 'raw_hash', 'fake_target'])
def test_rehashed_observation_and_outcome_mutations_rejected(tmp_path, captures, mutation):
    fail = mutation in ('checkpoint', 'digest', 'outcome', 'fake_target')
    folder, made, rows = packet(tmp_path, captures, fail)
    event = next(r['event'] for r in rows if r['state'] == 'TARGET' and r['event']['phase'] == 'ITERATION')
    if mutation == 'sequence': event['sequence'] = 99
    if mutation == 'mixed_count': event['mixed_evaluations'] = 8193
    if mutation == 'target': next(r['event'] for r in rows if r['state'] == 'TARGET')['metrics']['target'] = .09
    if mutation == 'residual_components': event['metrics']['translation_residual'] = 1.
    if mutation == 'acceptance':
        candidate = next(r['event'] for r in rows if r['event']['phase'] == 'CANDIDATE')
        candidate['metrics']['accepted'] = not candidate['metrics']['accepted']
    if mutation == 'nonfinite': event['metrics']['residual'] = 'NaN'
    if mutation == 'key': event['metrics']['extra'] = 1.
    if mutation == 'interleave': rows.append(rows[0])
    if mutation == 'terminal': rows[-1]['event']['phase'] = 'INITIALIZATION'
    if mutation == 'checkpoint': made['result']['failure']['checkpoints'][0]['residual'] = 0.
    if mutation == 'digest': made['result']['initial_checkpoint_sha256'] = '0'*64
    if mutation == 'outcome': made['result']['solver_outcome'] = 'TARGET_CONVERGED'
    if mutation == 'raw_hash': made['result']['bindings']['initial']['sha256'] = '0'*64
    if mutation == 'fake_target': (folder/'target.json').write_text('{}\n')
    (folder/'progress.jsonl').write_bytes(b''.join(diagnostic.shared.canonical(r) for r in rows))
    (folder/'complete.json').write_bytes(diagnostic.shared.canonical(made))
    with pytest.raises(ValueError): diagnostic.inspect(folder, {}, 'a'*32, 'b'*64, count=2)


def test_duplicate_and_noncanonical_observation_json_rejected(tmp_path):
    path = tmp_path/'progress.jsonl'
    for data in (b'{"state":"INITIAL","state":"TARGET","event":{}}\n', b' { }\n', b'{"x":NaN}\n'):
        path.write_bytes(data*2)
        with pytest.raises(ValueError): diagnostic.parse_observations(path, count=2)


@pytest.mark.parametrize('guard', ['authority', 'lease'])
def test_guards_before_numerical_capture(monkeypatch, tmp_path, guard):
    def deny(*args): raise ValueError('denied')
    monkeypatch.setattr(diagnostic, 'authority', deny if guard == 'authority' else lambda *a: {})
    monkeypatch.setattr(diagnostic, 'lease', deny)
    monkeypatch.setattr(diagnostic, 'capture', lambda **kw: pytest.fail('numerics before guards'))
    with pytest.raises(ValueError, match='denied'): diagnostic.worker(tmp_path, 'a'*40, tmp_path)


@pytest.mark.parametrize('mutation', ['head', 'dirty', 'extent', 'parent', 'sibling', 'environment', 'failure_input'])
def test_frozen_identity_mutations(monkeypatch, tmp_path, mutation):
    shared = diagnostic.shared;commit = 'a'*40
    def git(repo, *args):
        if args[0] == 'status': return 'dirty' if mutation == 'dirty' else ''
        if args == ('rev-parse', 'HEAD'):
            if repo == shared.SIBLING: return 'b'*40 if mutation == 'sibling' else shared.SIBLING_COMMIT
            return 'b'*40 if mutation == 'head' else commit
        if args == ('rev-parse', 'HEAD^'): return 'b'*40 if mutation == 'parent' else diagnostic.BASE
        if args[0] == 'diff': return '\n'.join(diagnostic.ALLOWED | ({'src/changed.py'} if mutation == 'extent' else set()))
        if args == ('rev-parse', 'HEAD^{tree}'): return shared.SIBLING_TREE
        raise AssertionError(args)
    monkeypatch.setattr(shared, 'git', git);monkeypatch.setattr(shared, 'environment', lambda: {})
    monkeypatch.setattr(shared, 'ENVIRONMENT_SHA', 'bad' if mutation == 'environment' else shared.sha(shared.canonical({})))
    def failure():
        if mutation == 'failure_input': raise ValueError('changed failure')
        return {}
    monkeypatch.setattr(diagnostic, 'failed_inputs', failure)
    monkeypatch.setattr(diagnostic, 'observation_inputs', lambda: {})
    with pytest.raises(ValueError): diagnostic.authority(tmp_path, commit)


def test_consumed_lease_and_wrong_command_rejected(tmp_path):
    manager = tmp_path/'manager';(manager/'requests').mkdir(parents=True);(manager/'active-lock').mkdir()
    repo = tmp_path/'repo';repo.mkdir();output = tmp_path/'output';commit = 'a'*40;request_id = 'b'*32
    record = {'request_id': request_id, 'repository': str(repo), 'command': diagnostic.command(repo, commit, output)}
    diagnostic.shared.publish(manager/'requests'/(request_id+'.json'), record)
    diagnostic.shared.publish(manager/'active-lock/owner.json', record)
    ledger = manager/'ledger.md';ledger.write_text(f'| now | {request_id} | APPROVED | test |\n')
    assert diagnostic.lease(repo, commit, output, manager=manager)[0] == request_id
    with pytest.raises(ValueError): diagnostic.lease(repo, commit, tmp_path/'other', manager=manager)
    ledger.write_text(ledger.read_text()+f'| now | {request_id} | COMPLETED_FAIL | test |\n')
    with pytest.raises(ValueError): diagnostic.lease(repo, commit, output, manager=manager)


@pytest.mark.parametrize('failure', ['exit', 'timeout', 'memory'])
def test_worker_failure_preserves_logs_without_diagnostic_publication(tmp_path, monkeypatch, failure):
    manager = tmp_path/'manager';(manager/'claims').mkdir(parents=True)
    repo = tmp_path/'repo';repo.mkdir();output = tmp_path/'external';calls = []
    monkeypatch.setattr(diagnostic, 'MANAGER', manager)
    monkeypatch.setattr(diagnostic, 'authority', lambda *a: {})
    monkeypatch.setattr(diagnostic, 'lease', lambda *a: ('b'*32, 'd'*64))
    def fail(line, folder, *args, **kwargs):
        calls.append(line)
        assert kwargs == {'timeout': 600., 'inactivity': 300., 'memory': 24*(1 << 30)}
        (folder/'partial.log').write_text('preserved')
        if failure == 'exit': return {'exit_code': 1}
        raise ValueError(failure)
    monkeypatch.setattr(diagnostic.shared, 'run_child', fail)
    with pytest.raises(ValueError): diagnostic.coordinate(repo, 'a'*40, output)
    assert len(calls) == 1 and not (output/'diagnostic.json').exists()
    assert (output/'blocked-diagnostic.json').exists() and (output/'force-accuracy32/partial.log').read_text() == 'preserved'
    with pytest.raises(FileExistsError): diagnostic.coordinate(repo, 'a'*40, tmp_path/'retry')


def test_preserved_historical_bindings_are_correct_read_only():
    assert len(diagnostic.failed_inputs()) == 8
    assert len(diagnostic.observation_inputs()) == 9


@pytest.mark.parametrize('mutation', ['schema', 'policy', 'estimate', 'station', 'origin',
    'disposition', 'replay', 'residual', 'clamp', 'reaction', 'omit'])
def test_failed_snapshot_rehashed_mutations_rejected(tmp_path, captures, mutation):
    folder, packet_data, _ = packet(tmp_path, captures, True)
    assert packet_data['result']['failure_snapshot'] is True
    path = folder/'failed_last.json';raw = diagnostic.shared.load(path)
    e = raw['response']['elements'][0]
    if mutation == 'schema': e['accuracy_schema'] = 'old'
    if mutation == 'policy': e['force_accuracy']['limit'] = 1e-11
    if mutation == 'estimate': e['estimated_force_error'] = 1e-10
    if mutation == 'station': e['stations'][0]['index'] = 1
    if mutation == 'origin': raw['origins'][0][0]['accumulated'] += 1.
    if mutation == 'disposition': raw['disposition'] = 'ACCEPTED'
    if mutation == 'replay': raw['replay_verified'] = False
    if mutation == 'residual': raw['residual_norm'] = 0.
    if mutation == 'clamp': raw['positions'][0][0] += 1.
    if mutation == 'reaction': raw['forces'][2][1] += 1.
    if mutation == 'omit':
        path.unlink();packet_data['result']['failure_snapshot'] = False
        del packet_data['result']['bindings']['failed_last']
    else:
        data = diagnostic.shared.canonical(raw);path.write_bytes(data)
        packet_data['result']['bindings']['failed_last'] = {'name': path.name, 'bytes': len(data), 'sha256': diagnostic.shared.sha(data)}
    (folder/'complete.json').write_bytes(diagnostic.shared.canonical(packet_data))
    with pytest.raises(ValueError): diagnostic.inspect(folder, {}, 'a'*32, 'b'*64, count=2)
