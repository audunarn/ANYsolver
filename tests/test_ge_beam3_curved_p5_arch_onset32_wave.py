"""Bounded successor integrity tests; no 32-element nonlinear computation."""

import ast
import copy
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_onset32_wave as wave
from docs.reference_cases.ge_beam3_curved_p5_arch_stability_inspection import classify_matrix


def test_exact_registered_scope_and_no_default_profile_expansion():
    assert wave.CASE['meshes'] == [32] and wave.CASE['extent'] == 'ARCH_ONSET32'
    assert wave.CASE['nodes'] == 65 and wave.CASE['free_dimension'] == 378
    assert wave.CASE['stations_per_state'] == 512 and wave.CASE['maximum_states'] == 29
    assert wave.CASE['child_seconds'] == 600 and wave.CASE['wave_seconds'] == 900
    assert wave.probe.MESHES == (4, 8, 16)
    assert wave.CASE['drops'] == wave.prior.CASE['drops']
    assert wave.CASE['section_diagonal'] == wave.prior.CASE['section_diagonal']
    assert wave.CASE['physical_limit'] == wave.prior.CASE['physical_limit'] == 1e-11


def synthetic_raw():
    """Fabricated diagonal algebra/state fixture, never mechanics evidence."""
    nodes = 65;t = np.linspace(-1., 1., nodes)
    x = np.column_stack((t, .1*(1-t*t), np.zeros(nodes)))
    tangent = np.diag(np.arange(1., 391.))
    spectra = classify_matrix(tangent, nodes=nodes, extent=wave.PROFILE)
    odd = spectra['out_of_plane']
    sample = {'id': 'grid-00', 'origin_id': None, 'sign': 1, 'drop': 0., 'load': 0.,
              'lowest': float(odd['values'][0]), 'uncertainty': odd['uncertainty_band'],
              'negative': 0, 'unresolved': 0}
    state_errors = dict.fromkeys(('equilibrium', 'position_planarity', 'rotation_planarity',
        'rotation_orthogonality', 'rotation_determinant', 'fixed_positions', 'fixed_rotations', 'load_pattern'), 0.)
    history = {'plastic_coordinate': 0., 'accumulated': 0.}
    assembly = {'positions': x, 'rotations': np.tile(np.eye(3), (nodes, 1, 1)),
        'forces': np.zeros((nodes, 3)), 'residual_norm': 0., 'iterations': 0, 'mixed_evaluations': 32,
        'origins': [[copy.deepcopy(history) for _ in range(16)] for _ in range(32)],
        'response': {'residual': np.zeros(390), 'tangent': tangent,
            'elements': [{'stations': [{'response': {'plastic_active': False, 'history': copy.deepcopy(history)}}
                                      for _ in range(16)]} for _ in range(32)]}}
    raw = {'id': 'grid-00', 'origin_id': None, 'elements': 32, 'production_qualified': False,
        'sample': {k: v for k, v in sample.items() if k not in ('id', 'origin_id', 'sign')},
        'state_errors': state_errors, 'spectra': spectra,
        'trial': {'control_dof': 193, 'target': .1, 'reaction_derivative': 1., 'assembly': assembly}}
    return raw, sample


def test_synthetic_32_raw_requires_explicit_profile():
    raw, sample = synthetic_raw()
    wave.prior.check_raw(raw, sample, 32, extent=wave.PROFILE)
    with pytest.raises(ValueError): wave.prior.check_raw(raw, sample, 32)


@pytest.mark.parametrize('mutation', ['nodes', 'budget', 'stations', 'history', 'tangent', 'spectrum'])
def test_large_shape_and_bound_mutations_rejected(mutation):
    raw, sample = synthetic_raw();assembly = raw['trial']['assembly']
    if mutation == 'nodes': assembly['positions'] = assembly['positions'][:-1]
    if mutation == 'budget': assembly['mixed_evaluations'] = 8193
    if mutation == 'stations': assembly['response']['elements'][0]['stations'].pop()
    if mutation == 'history': assembly['origins'][0][0]['accumulated'] = .01
    if mutation == 'tangent': assembly['response']['tangent'][8, 8] = -1.
    if mutation == 'spectrum': raw['spectra']['out_of_plane']['values'][0] += 1.
    with pytest.raises(ValueError): wave.prior.check_raw(raw, sample, 32, extent=wave.PROFILE)


def test_preserved_background_hash_is_not_replaceable(monkeypatch, tmp_path):
    path = tmp_path/'aggregate.json';wave.prior.publish(path, {'replacement': True})
    monkeypatch.setattr(wave, 'PREVIOUS', path)
    with pytest.raises(ValueError, match='hash'): wave.previous()


@pytest.mark.parametrize('guard', ['authority', 'lease'])
def test_numerical_computation_follows_both_guards(monkeypatch, tmp_path, guard):
    def denied(*args): raise wave.prior.RefinementError('denied')
    monkeypatch.setattr(wave, 'authority', denied if guard == 'authority' else lambda *a: {})
    monkeypatch.setattr(wave, 'lease', denied)
    monkeypatch.setattr(wave.probe, 'records', lambda **kw: pytest.fail('numerics before guards'))
    with pytest.raises(ValueError, match='denied'): wave.worker(tmp_path, 'a'*40, tmp_path)


@pytest.mark.parametrize('mutation', ['dirty', 'head', 'parent', 'extent', 'sibling', 'environment', 'previous'])
def test_exact_freeze_and_environment_guards(monkeypatch, tmp_path, mutation):
    commit = 'a'*40
    def git(repo, *args):
        if args[0] == 'status': return 'dirty' if mutation == 'dirty' else ''
        if args == ('rev-parse', 'HEAD'):
            if repo == wave.prior.SIBLING:
                return 'b'*40 if mutation == 'sibling' else wave.prior.SIBLING_COMMIT
            return 'b'*40 if mutation == 'head' else commit
        if args == ('rev-parse', 'HEAD^'): return 'b'*40 if mutation == 'parent' else wave.BASE
        if args[0] == 'diff': return '\n'.join(wave.ALLOWED | ({'src/unsafe.py'} if mutation == 'extent' else set()))
        if args == ('rev-parse', 'HEAD^{tree}'): return wave.prior.SIBLING_TREE
        raise AssertionError(args)
    monkeypatch.setattr(wave.prior, 'git', git)
    monkeypatch.setattr(wave.prior, 'environment', lambda: {})
    monkeypatch.setattr(wave.prior, 'ENVIRONMENT_SHA', 'wrong' if mutation == 'environment' else wave.prior.sha(wave.prior.canonical({})))
    monkeypatch.setattr(wave.prior, 'references', lambda: {})
    def previous():
        if mutation == 'previous': raise ValueError('mutated previous')
        return {}
    monkeypatch.setattr(wave, 'previous', previous)
    with pytest.raises(ValueError): wave.authority(tmp_path, commit)


def test_new_request_command_is_distinct_and_consumption_rejected(tmp_path):
    manager = tmp_path/'manager';(manager/'requests').mkdir(parents=True);(manager/'active-lock').mkdir()
    repo = tmp_path/'repo';repo.mkdir();output = tmp_path/'output';commit = 'a'*40;request_id = 'b'*32
    data = {'request_id': request_id, 'repository': str(repo), 'command': wave.command(repo, commit, output)}
    assert data['command'] != wave.prior.command(repo, commit, output)
    wave.prior.publish(manager/'requests'/(request_id+'.json'), data)
    wave.prior.publish(manager/'active-lock/owner.json', data)
    ledger = manager/'ledger.md';ledger.write_text(f'| now | {request_id} | APPROVED | test |\n')
    assert wave.lease(repo, commit, output, manager=manager)[0] == request_id
    with pytest.raises(ValueError): wave.lease(repo, commit, tmp_path/'other', manager=manager)
    ledger.write_text(ledger.read_text()+f'| now | {request_id} | COMPLETED_FAIL | test |\n')
    with pytest.raises(ValueError): wave.lease(repo, commit, output, manager=manager)


@pytest.mark.parametrize('failure', ['exit', 'timeout', 'memory'])
def test_one_child_failure_is_preserved_without_retry_or_aggregate(tmp_path, monkeypatch, failure):
    manager = tmp_path/'manager';(manager/'claims').mkdir(parents=True)
    repo = tmp_path/'repo';repo.mkdir();output = tmp_path/'external';calls = []
    monkeypatch.setattr(wave, 'MANAGER', manager)
    monkeypatch.setattr(wave, 'authority', lambda *a: {'commit': 'a'*40})
    monkeypatch.setattr(wave, 'lease', lambda *a: ('b'*32, 'd'*64))
    def fail(line, folder, *args, **kwargs):
        calls.append(line)
        assert '--worker' in line and line[line.index('-m')+1] == wave.MODULE
        assert kwargs == {'timeout': 600., 'inactivity': 300., 'memory': 24*(1 << 30)}
        (folder/'partial.log').write_text('preserved')
        if failure == 'exit': return {'exit_code': 1}
        raise ValueError(failure)
    monkeypatch.setattr(wave.prior, 'run_child', fail)
    with pytest.raises(ValueError): wave.coordinate(repo, 'a'*40, output)
    assert len(calls) == 1 and not (output/'aggregate.json').exists()
    assert (output/'blocked-diagnostic.json').exists()
    assert (output/'elements-32/partial.log').read_text() == 'preserved'
    assert (manager/'claims'/('ge-beam3-onset32-'+'b'*32)).exists()
    with pytest.raises(FileExistsError): wave.coordinate(repo, 'a'*40, tmp_path/'second')


def test_comparison_preserves_history_and_uncertainty_without_a_gate():
    def row(label, drop, origin):
        v = .04612345-drop
        return {'drop': drop, 'load': .03, 'lowest': v, 'uncertainty': 1e-12,
                'negative': int(v < -1e-12), 'unresolved': int(abs(v) <= 1e-12)}
    result = wave.probe.locate(row);result['elements'] = 32
    roots = {'1': {'result': {'left': {'displacement': .046, 'load': .029},
                             'right': {'displacement': .04600001, 'load': .02899999}}}}
    historical = {'comparisons': [{'elements': 16, 'disposition': 'MIDPOINT_LATERAL_SIGN_UNRESOLVED'}]}
    original = wave.prior.canonical(historical)
    compared = wave.compare({'result': result}, roots, historical)
    assert wave.prior.canonical(historical) == original
    assert compared['historical_comparisons'] == historical['comparisons']
    assert compared['historical_recomputed'] is False and compared['production_qualified'] is False
    assert compared['accuracy_qualified'] is False and compared['first_critical_point_proven'] is False
    assert compared['current']['comparison']['continuum']['1']['left']['discrete_endpoint_relative_load_errors'] == [.03/.029-1]*2
    assert wave.prior.canonical(compared) == wave.prior.canonical(wave.compare({'result': result}, roots, historical))


def test_no_top_level_numerics_or_old_worker_invocation():
    tree = ast.parse(Path(wave.__file__).read_text())
    top = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert not any('numpy' in n or 'scipy' in n or 'arch_refinement_case' in n for n in top)
    text = ast.unparse(tree)
    assert 'prior.worker(' not in text and 'prior.coordinate(' not in text
