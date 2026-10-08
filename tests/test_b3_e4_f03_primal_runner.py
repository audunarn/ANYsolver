"""Execution authority and adversarial evidence checks without reference solves."""
from pathlib import Path
import json
import sys

import numpy as np
import pytest

_scripts = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(_scripts))
import b3_e4_f03_primal_ritz as runner
import _b3_e4_f03_primal_archive as archive
import _b3_e4_f03_primal_checks as checks


def write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def test_registration_is_exclusive_and_case_inventory_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner.supervisor, '_clean', lambda: True)
    monkeypatch.setattr(runner, 'contract', lambda: {'cases': runner.CASES})
    root = tmp_path/'.qualification/b3-ge-e4-pl/reference-unit'
    runner.register(root)
    digest = runner.sha(root/'registration.json')
    assert [case['degree'] for case in runner.CASES.values()] == [4, 8, 12, 16, 24]
    with pytest.raises(FileExistsError):
        runner.register(root)
    assert runner.sha(root/'registration.json') == digest
    monkeypatch.setattr(runner.supervisor, '_clean', lambda: False)
    with pytest.raises(ValueError, match='commit'):
        runner.register(root.parent/'another')


def test_private_child_cannot_replay_scientific_work(tmp_path, monkeypatch):
    directory = tmp_path/'n04'; directory.mkdir()
    write(directory/'child_started.json', {'already': 'consumed'})
    monkeypatch.setattr(runner, 'registered', lambda root: {'identity': {}})
    monkeypatch.setattr(runner.supervisor, '_registration_hash', lambda root: 'registered')
    monkeypatch.setattr(checks, 'evaluate_case', lambda n: pytest.fail('consumed child must not evaluate'))
    for name in runner.supervisor.THREADS:
        monkeypatch.setenv(name, '1')
    with pytest.raises(FileExistsError):
        runner.child(tmp_path, 'n04')


def test_cancellation_preserves_receipt_and_stops_further_launches(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'register', lambda root: None)
    monkeypatch.setattr(runner.supervisor, '_registration_hash', lambda root: 'registered')
    launched = []
    def execute(root, name):
        launched.append(name)
        if len(launched) == 2:
            (root/name).mkdir()
            write(root/name/'supervision.json', {'reason': 'supervisor_failure',
                'failure': 'KeyboardInterrupt: cancelled'})
            return False
        return True
    monkeypatch.setattr(runner.supervisor, 'execute', execute)
    with pytest.raises(KeyboardInterrupt):
        runner.run_once(tmp_path)
    assert launched == ['n04', 'n08']
    assert not runner.read(tmp_path/'orchestration.json')['inventory_complete']
    assert (tmp_path/'n08/supervision.json').is_file()


@pytest.fixture
def complete_case(tmp_path, monkeypatch):
    name = 'n04'; directory = tmp_path/name; directory.mkdir()
    manifest = {'identity': {'source': 'unit-fixture'}}
    monkeypatch.setattr(runner.supervisor, '_registration_hash', lambda root: 'registered')
    monkeypatch.setattr(archive, 'unpack', lambda path, n: {'q': 'owned-unit-fixture'})
    metrics = {'checks': {'check': .25}, 'observables': {}, 'details': {}}
    monkeypatch.setattr(checks, 'LIMITS', {'check': 1.})
    monkeypatch.setattr(checks, 'verify_saved', lambda arrays, n: metrics)
    (directory/'arrays.npz').write_bytes(b'unit-artifact')
    write(directory/'child_started.json', {'case': name, 'registration_sha256': 'registered',
        'pid': 123, 'started_unix_seconds': 12345.})
    write(directory/'observables.json', {'metrics': metrics, 'equilibrium_solves': 1,
        'assembly_descriptions': 2, 'scope': runner.SCOPE})
    event = runner.observable_event(directory, name, runner.CASES[name], False)
    events = [{'phase': 'identity', 'case': name, 'identity': manifest['identity'],
        'registration_sha256': 'registered', 'threadpools': [{'num_threads': 1}]}, event]
    (directory/'stdout.jsonl').write_text('\n'.join(map(json.dumps, events)), encoding='utf-8')
    receipt = {'reason': 'completed', 'exit_code': 0, 'elapsed_seconds': 1.,
        'sampled_peak_rss_bytes': 1024, 'phases': ['identity', 'observables'],
        'registration_sha256': 'registered', 'failure': None,
        'observables_sha256': event['sha256']}
    write(directory/'supervision.json', receipt)
    return tmp_path, name, manifest, receipt


def test_complete_receipt_and_recomputed_metrics(complete_case):
    root, name, manifest, _ = complete_case
    decision, arrays = runner.verify_case(root, name, manifest)
    assert decision['status'] == 'PASSED_NUMERICAL_SCREEN'
    assert arrays['q'] == 'owned-unit-fixture'


@pytest.mark.parametrize('mutation', ['contradictory_failure', 'missing_failure', 'extra', 'wrong_exit', 'resource', 'registration'])
def test_receipt_contradictions_are_evidence_failures(complete_case, mutation):
    root, name, manifest, receipt = complete_case
    if mutation == 'contradictory_failure': receipt['failure'] = 'MemoryError: not a success'
    if mutation == 'missing_failure': del receipt['failure']
    if mutation == 'extra': receipt['unexpected'] = True
    if mutation == 'wrong_exit': receipt['exit_code'] = 1
    if mutation == 'resource': receipt['elapsed_seconds'] = runner.MAX_SECONDS+1
    if mutation == 'registration': receipt['registration_sha256'] = 'different'
    write(root/name/'supervision.json', receipt)
    with pytest.raises(ValueError):
        runner.verify_case(root, name, manifest)


def test_failed_execution_keeps_receipt_without_final_arrays(complete_case):
    root, name, manifest, receipt = complete_case
    receipt.update(reason='time_limit', exit_code=1, failure=None)
    write(root/name/'supervision.json', receipt)
    (root/name/'arrays.npz').unlink()
    decision, arrays = runner.verify_case(root, name, manifest)
    assert decision['status'] == 'FAILED_EXECUTION' and arrays is None


def test_missing_case_prevents_canonical_adjudication(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'registered', lambda root: {})
    with pytest.raises(ValueError, match='complete five-case'):
        runner.adjudicate(tmp_path)
    assert not (tmp_path/'adjudication.json').exists()


def test_bind_metrics_rejects_values_shapes_and_boolean_substitution():
    for first, second in (({'a': 1.}, {'a': 2.}), ([1.], [1., 2.]), (True, 1), (float('nan'), 0.)):
        with pytest.raises(ValueError):
            runner.bind_metrics(first, second)


def test_json_roundtrip_preserves_numpy_real_semantics_and_names_failure_path():
    metrics = {'details': {'perturbation_delta': np.float64(1.234567890123e-12)},
               'checks': {'value': .25}, 'observables': {'nullable': None}}
    runner.bind_metrics(json.loads(json.dumps(metrics)), metrics)
    changed = json.loads(json.dumps(metrics)); changed['checks']['value'] = .5
    with pytest.raises(ValueError, match='metrics/checks/value'):
        runner.bind_metrics(changed, metrics)
    for first, second in ((True, np.float64(1)), (np.float64(1), True)):
        with pytest.raises(ValueError):
            runner.bind_metrics(first, second)


def test_known_undefined_quantity_is_completed_numerical_failure(complete_case, monkeypatch):
    root, name, manifest, receipt = complete_case
    metrics = {'checks': {'functional_norm_nonfinite_violation': 1.},
        'observables': {'full_functional_norm_N': None},
        'details': {'norm_squared_48': None, 'perturbation_bound': None}}
    monkeypatch.setattr(checks, 'LIMITS', {'functional_norm_nonfinite_violation': 0.})
    monkeypatch.setattr(checks, 'verify_saved', lambda arrays, n: metrics)
    monkeypatch.setattr(checks, 'evaluate_case', lambda n: pytest.fail('audit must not retry equilibrium'))
    directory = root/name
    write(directory/'observables.json', {'metrics': metrics, 'equilibrium_solves': 1,
        'assembly_descriptions': 2, 'scope': runner.SCOPE})
    event = runner.observable_event(directory, name, runner.CASES[name], False)
    events = [json.loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines()]
    events[1] = event
    (directory/'stdout.jsonl').write_text('\n'.join(map(json.dumps, events)), encoding='utf-8')
    receipt['observables_sha256'] = event['sha256']
    write(directory/'supervision.json', receipt)
    decision, arrays = runner.verify_case(root, name, manifest)
    assert decision['status'] == 'FAILED_NUMERICAL_SCREEN'
    assert arrays is not None
    assert decision['metrics']['observables']['full_functional_norm_N'] is None


def test_numerical_failure_prevents_trend_acceptance_and_preserves_adjudication(tmp_path, monkeypatch):
    import _b3_e4_f03_primal_trends as trends
    monkeypatch.setattr(runner, 'registered', lambda root: {'identity': {'fixture': 'numerical-failure'}})
    monkeypatch.setattr(runner.supervisor, '_registration_hash', lambda root: 'registered')
    monkeypatch.setattr(trends, 'assess_sequence', lambda *a: pytest.fail('failed numerical gate cannot advance'))
    for name in runner.CASES:
        (tmp_path/name).mkdir()
        write(tmp_path/name/'supervision.json', {})
    def verify(root, name, manifest):
        status = 'FAILED_NUMERICAL_SCREEN' if name == 'n24' else 'PASSED_NUMERICAL_SCREEN'
        return {'status': status, 'metrics': {'details': {'undefined_bound': None}}}, {'q': 'available'}
    monkeypatch.setattr(runner, 'verify_case', verify)
    assert runner.adjudicate(tmp_path) is False
    decision = runner.read(tmp_path/'adjudication.json')
    assert decision['status'] == 'FAILED_NUMERICAL_SCREEN'
    assert decision['trends'] is None
    assert decision['cases']['n24']['metrics']['details']['undefined_bound'] is None
