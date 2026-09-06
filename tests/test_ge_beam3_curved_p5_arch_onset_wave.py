"""Disposable integrity/containment tests, not the multi-mesh onset study."""

import ast
import builtins
import copy
import json
from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_wave as wave


SMALL_DROPS = (0., .005, .01)


@pytest.fixture(scope='module')
def small_result():
    saved = {}
    def publish(label, raw):
        data = wave.canonical(raw)
        saved[label] = data
        return {'name': label+'.json', 'bytes': len(data), 'sha256': wave.sha(data)}
    original = wave.probe.DROPS
    try:
        wave.probe.DROPS = SMALL_DROPS
        result = wave.probe.records(count=2, progress=lambda *a: None, publish_raw=publish)
    finally:
        wave.probe.DROPS = original
    return json.loads(wave.canonical(result)), saved


def packet(tmp_path, monkeypatch, small_result):
    monkeypatch.setattr(wave.probe, 'DROPS', SMALL_DROPS)
    folder = tmp_path/'small';folder.mkdir()
    result, saved = copy.deepcopy(small_result)
    for label, data in saved.items(): (folder/(label+'.json')).write_bytes(data)
    made = {'schema': wave.SCHEMA, 'authority': {'commit': 'c'}, 'request_id': 'b'*32,
            'request_sha256': 'd'*64, 'result': result}
    wave.publish(folder/'complete.json', made)
    return folder, made


def test_small_raw_reconstruction_and_deterministic_inspection(tmp_path, monkeypatch, small_result):
    folder, made = packet(tmp_path, monkeypatch, small_result)
    one = wave.inspect_worker(folder, 2, {'commit': 'c'}, 'b'*32, 'd'*64)
    two = wave.inspect_worker(folder, 2, {'commit': 'c'}, 'b'*32, 'd'*64)
    assert one == made and wave.canonical(one) == wave.canonical(two)


@pytest.mark.parametrize('mutation', ['hash', 'origin', 'epoch', 'target', 'force', 'residual', 'tangent',
    'spectrum', 'budget', 'history', 'station', 'state_check', 'summary', 'disposition', 'coverage', 'extra_file'])
def test_mutated_rehashed_raw_or_summary_rejected(tmp_path, monkeypatch, small_result, mutation):
    folder, made = packet(tmp_path, monkeypatch, small_result)
    result = made['result'];binding = result['raw_bindings']['grid-01']
    path = folder/'grid-01.json';raw = wave.load(path)
    if mutation == 'hash': binding['sha256'] = '0'*64
    elif mutation == 'origin': result['samples'][1]['origin_id'] = 'grid-02'
    elif mutation == 'epoch': raw['trial']['origin_epoch'] = 0
    elif mutation == 'target': raw['trial']['target'] += .001
    elif mutation == 'force': raw['trial']['assembly']['forces'][2][1] += 1.
    elif mutation == 'residual': raw['trial']['assembly']['response']['residual'][7] += 1.
    elif mutation == 'tangent': raw['trial']['assembly']['response']['tangent'][8][8] += 1.
    elif mutation == 'spectrum': raw['spectra']['out_of_plane']['values'][0] += 1.
    elif mutation == 'budget': raw['trial']['assembly']['mixed_evaluations'] = True
    elif mutation == 'history': raw['trial']['assembly']['origins'][0][0]['plastic_coordinate'] = .001
    elif mutation == 'station': raw['trial']['assembly']['response']['elements'][0]['stations'].pop()
    elif mutation == 'state_check': raw['state_errors']['equilibrium'] = .01
    elif mutation == 'summary': result['samples'][1]['lowest'] = -1.
    elif mutation == 'disposition': result['disposition'] = 'QUALIFIED'
    elif mutation == 'coverage': result['samples'].pop()
    elif mutation == 'extra_file': (folder/'surprise.txt').write_text('unexpected')
    if mutation not in ('hash', 'origin', 'summary', 'disposition', 'coverage', 'extra_file'):
        data = wave.canonical(raw);path.write_bytes(data)
        binding.update(bytes=len(data), sha256=wave.sha(data))
    (folder/'complete.json').write_bytes(wave.canonical(made))
    with pytest.raises((ValueError, StopIteration)):
        wave.inspect_worker(folder, 2, {'commit': 'c'}, 'b'*32, 'd'*64)


def make_lease(tmp_path):
    manager = tmp_path/'manager';(manager/'requests').mkdir(parents=True);(manager/'active-lock').mkdir()
    repo = tmp_path/'repo';repo.mkdir();output = tmp_path/'output';commit = 'a'*40;request_id = 'b'*32
    data = {'request_id': request_id, 'command': wave.command(repo, commit, output), 'repository': str(repo)}
    wave.publish(manager/'active-lock/owner.json', data);wave.publish(manager/'requests'/(request_id+'.json'), data)
    (manager/'ledger.md').write_text(f'| now | {request_id} | APPROVED | test |\n')
    return manager, repo, output, commit, request_id


@pytest.mark.parametrize('mutation', ['missing', 'consumed', 'duplicate', 'command', 'output'])
def test_lease_is_exact_and_single_use(tmp_path, mutation):
    manager, repo, output, commit, request_id = make_lease(tmp_path)
    assert wave.lease(repo, commit, output, manager=manager)[0] == request_id
    path = manager/'ledger.md'
    if mutation == 'missing': path.write_text('')
    if mutation == 'consumed': path.write_text(path.read_text()+f'| now | {request_id} | COMPLETED_FAIL | test |\n')
    if mutation == 'duplicate': path.write_text(path.read_text()*2)
    if mutation == 'command':
        path = manager/'active-lock/owner.json';owner = wave.load(path);owner['command'] += ' changed'
        path.write_bytes(wave.canonical(owner))
    if mutation == 'output': output = tmp_path/'other'
    with pytest.raises(wave.RefinementError): wave.lease(repo, commit, output, manager=manager)


@pytest.mark.parametrize('mutation', ['head', 'dirty', 'parent', 'extent', 'sibling', 'environment', 'reference'])
def test_authority_rejects_mutations_before_mechanics(monkeypatch, tmp_path, mutation):
    commit = 'a'*40
    def git(repo, *args):
        sibling = repo == wave.SIBLING
        if args[0] == 'status': return 'dirty' if mutation == 'dirty' else ''
        if args == ('rev-parse', 'HEAD'):
            return ('b'*40 if mutation == 'sibling' else wave.SIBLING_COMMIT) if sibling else ('b'*40 if mutation == 'head' else commit)
        if args == ('rev-parse', 'HEAD^'): return 'b'*40 if mutation == 'parent' else wave.BASE
        if args[0] == 'diff': return '\n'.join(wave.ALLOWED | ({'src/changed.py'} if mutation == 'extent' else set()))
        if args == ('rev-parse', 'HEAD^{tree}'): return wave.SIBLING_TREE if sibling else 't'
        raise AssertionError(args)
    monkeypatch.setattr(wave, 'git', git)
    monkeypatch.setattr(wave, 'environment', lambda: {})
    monkeypatch.setattr(wave, 'ENVIRONMENT_SHA', 'wrong' if mutation == 'environment' else wave.sha(wave.canonical({})))
    def refs():
        if mutation == 'reference': raise wave.RefinementError('reference mismatch')
        return {}
    monkeypatch.setattr(wave, 'references', refs)
    with pytest.raises(wave.RefinementError): wave.authority(tmp_path, commit)


@pytest.mark.parametrize('denied', ['authority', 'lease'])
def test_guards_precede_numerical_records(monkeypatch, tmp_path, denied):
    def reject(*args): raise wave.RefinementError('denied')
    def forbidden(*args, **kwargs): raise AssertionError('numerics before authority')
    monkeypatch.setattr(wave.probe, 'records', forbidden)
    monkeypatch.setattr(wave, 'authority', reject if denied == 'authority' else lambda *a: {})
    monkeypatch.setattr(wave, 'lease', reject)
    with pytest.raises(wave.RefinementError, match='denied'): wave.worker(tmp_path, 'a'*40, tmp_path, 4)


def test_top_level_has_no_numerical_import():
    tree = ast.parse(Path(wave.__file__).read_text())
    imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert not any('numpy' in n or 'scipy' in n or 'arch_refinement_case' in n for n in imports)


def test_strict_canonical_json_and_exclusive_publication(tmp_path):
    path = tmp_path/'bad.json'
    for data in (b'{"a":0,"a":1}\n', b'{"x":NaN}\n', b'{"x":1e400}\n', b' {}\n'):
        path.write_bytes(data)
        with pytest.raises(ValueError): wave.load(path)
    final = tmp_path/'once.json';wave.publish(final, {'x': 1})
    with pytest.raises(FileExistsError): wave.publish(final, {'x': 2})
    assert wave.load(final) == {'x': 1}


def test_reference_binding_rejects_even_canonical_replacement(tmp_path):
    for stride in (1, 2): wave.publish(tmp_path/f'root-stride-{stride}.json', {'schema': 'replacement'})
    with pytest.raises(wave.RefinementError, match='hash'): wave.references(tmp_path)


@pytest.mark.parametrize('failure', ['exit', 'timeout', 'memory'])
def test_failed_wave_preserves_claim_and_never_publishes_aggregate(tmp_path, monkeypatch, failure):
    manager = tmp_path/'manager';(manager/'claims').mkdir(parents=True)
    repo = tmp_path/'repo';repo.mkdir();output = tmp_path/'external'
    monkeypatch.setattr(wave, 'MANAGER', manager)
    monkeypatch.setattr(wave, 'authority', lambda *a: {'commit': 'a'*40})
    monkeypatch.setattr(wave, 'lease', lambda *a: ('b'*32, 'd'*64))
    calls = []
    def fail(line, folder, *args, **kwargs):
        calls.append(line)
        assert 0 < kwargs['timeout'] <= 600 and kwargs['inactivity'] == 300
        assert kwargs['memory'] == 24*(1 << 30)
        (folder/'partial.log').write_text('preserved')
        if failure == 'exit': return {'exit_code': 1}
        raise wave.RefinementError(failure)
    monkeypatch.setattr(wave, 'run_child', fail)
    with pytest.raises(wave.RefinementError): wave.coordinate(repo, 'a'*40, output)
    assert len(calls) == 1
    assert not (output/'aggregate.json').exists()
    assert (output/'blocked-diagnostic.json').exists()
    assert (output/'elements-04/partial.log').read_text() == 'preserved'
    assert (manager/'claims'/('ge-beam3-onset-'+'b'*32)).is_dir()
    with pytest.raises(FileExistsError): wave.coordinate(repo, 'a'*40, tmp_path/'different')


def test_ordered_adjudication_retains_uncertainty_not_qualification():
    packets = []
    for n in wave.probe.MESHES:
        result = wave.probe.locate(lambda label, drop, origin: {
            'drop': drop, 'load': .03, 'lowest': .1, 'uncertainty': 1e-12, 'negative': 0, 'unresolved': 0})
        result['elements'] = n;packets.append({'result': result})
    result = wave.adjudicate(packets, {})
    assert result['production_qualified'] is False and result['accuracy_qualified'] is False
    assert [r['elements'] for r in result['comparisons']] == [4, 8, 16]
    assert all(r['comparison'] is None for r in result['comparisons'])
    with pytest.raises(wave.RefinementError): wave.adjudicate(list(reversed(packets)), {})
