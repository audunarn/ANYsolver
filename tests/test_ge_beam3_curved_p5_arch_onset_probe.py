"""Synthetic bounded search plus one small two-element correctness smoke."""

import ast
from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_probe as onset
from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import canonical, sha


def row(drop, value, uncertainty=1e-12):
    return {'drop': drop, 'load': .03, 'lowest': value, 'uncertainty': uncertainty,
            'negative': int(value < -uncertainty), 'unresolved': int(abs(value) <= uncertainty)}


def test_fixed_grid_and_bisection_have_bounded_accepted_origin_graph():
    seen = {}
    root = .04612345
    def evaluate(label, drop, origin):
        if label == 'grid-00':
            assert origin is None
        else:
            assert origin in seen
        if label.startswith('bisect'):
            assert seen[origin]['lowest'] > 0 and seen[origin]['drop'] < drop
        made = row(drop, root-drop);seen[label] = made
        return made
    result = onset.locate(evaluate)
    assert [r['drop'] for r in result['samples'][:13]] == list(onset.DROPS)
    assert len(seen) <= 13+onset.MAX_BISECTIONS
    assert result['disposition'] == 'SAMPLED_LATERAL_SIGN_BRACKET_LOCALIZED'
    bracket = result['bracket']
    assert seen[bracket['left_id']]['drop'] < root < seen[bracket['right_id']]['drop']
    assert 0 < bracket['width'] <= onset.WIDTH
    assert result['production_qualified'] is False
    assert result['first_critical_point_proven'] is False
    assert result['interval_is_rigorous'] is False


def test_uncertain_midpoint_keeps_original_separated_endpoints_without_retry():
    calls = []
    def evaluate(label, drop, origin):
        calls.append(label)
        return row(drop, 0. if label.startswith('bisect') else .046-drop)
    result = onset.locate(evaluate)
    assert result['disposition'] == 'MIDPOINT_LATERAL_SIGN_UNRESOLVED'
    assert result['bracket']['left_id'] == 'grid-09'
    assert result['bracket']['right_id'] == 'grid-10'
    assert len(calls) == 14


@pytest.mark.parametrize('root,disposition',[
    (-.1, 'REFERENCE_LATERAL_POSITIVITY_UNRESOLVED'),
    (.1, 'NO_LATERAL_CROSSING_OBSERVED_ON_FIXED_GRID'),
    (.045, 'GRID_LATERAL_SIGN_UNRESOLVED'),
])
def test_no_interval_extension_or_fabricated_crossing(root, disposition):
    result = onset.locate(lambda label, drop, origin: row(drop, root-drop))
    assert result['disposition'] == disposition and result['bracket'] is None
    assert len(result['samples']) == len(onset.DROPS)


def test_bisection_budget_is_a_stop_not_an_automatic_retry(monkeypatch):
    monkeypatch.setattr(onset, 'MAX_BISECTIONS', 1)
    result = onset.locate(lambda label, drop, origin: row(drop, .04612345-drop))
    assert result['disposition'] == 'BISECTION_BUDGET_EXHAUSTED'
    assert len(result['samples']) == 14


def test_first_observed_grid_crossing_is_used_without_uniqueness_claim():
    def evaluate(label, drop, origin):
        return row(drop, (.02112345-drop)*(.03312345-drop)*(.05112345-drop))
    result = onset.locate(evaluate)
    indexed = {r['id']: r for r in result['samples']}
    assert indexed[result['bracket']['right_id']]['drop'] < .025
    assert result['first_critical_point_proven'] is False


def test_failure_propagates_without_retry():
    calls = []
    def evaluate(label, drop, origin):
        calls.append(label)
        if label == 'grid-02': raise RuntimeError('failed worker')
        return row(drop, .05-drop)
    with pytest.raises(RuntimeError, match='failed worker'): onset.locate(evaluate)
    assert calls == ['grid-00', 'grid-01', 'grid-02']


@pytest.mark.parametrize('changes',[
    {'lowest': float('nan')}, {'load': float('inf')}, {'uncertainty': -1.},
    {'drop': .061}, {'drop': True}, {'negative': True}, {'negative': 1},
    {'unresolved': 1}, {'extra': 0}, {'lowest': -1., 'negative': 0},
    {'lowest': 0., 'unresolved': 0},
])
def test_malformed_or_inconsistent_inertia_rejected(changes):
    with pytest.raises(ValueError): onset.sign(dict(row(.01, 1.), **changes))


@pytest.mark.parametrize('value,expected',[(2., 1), (1., 0), (0., 0), (-1., 0), (-2., -1)])
def test_uncertainty_boundary_is_not_treated_as_a_resolved_sign(value, expected):
    assert onset.sign(row(.01, value, uncertainty=1.)) == expected


def test_target_mutation_and_missing_schema_fail_closed():
    with pytest.raises(ValueError, match='scheduled target'):
        onset.locate(lambda label, drop, origin: row(.01, 1.))
    with pytest.raises(ValueError, match='schema'):
        onset.locate(lambda *args: None)


def test_deterministic_serialization_and_bound_inputs():
    evaluate = lambda label, drop, origin: row(drop, .04612345-drop)
    assert canonical(onset.locate(evaluate)) == canonical(onset.locate(evaluate))
    assert onset.MESHES == (4, 8, 16)
    assert onset.DROPS == tuple(i/200 for i in range(13))
    assert onset.MAX_BISECTIONS == 16 and onset.WIDTH == 1e-7
    with pytest.raises(ValueError): onset.records(count=32, progress=None, publish_raw=None)


def test_module_import_does_not_start_numerics_or_processes():
    tree = ast.parse(Path(onset.__file__).read_text())
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert len(imports) == 1 and isinstance(imports[0], ast.Import)
    assert [a.name for a in imports[0].names] == ['math']
    assert not any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) for n in tree.body)


def test_small_two_element_smoke_full_tangent_and_raw_origin_bindings(monkeypatch):
    # Only three low-load states: NOT the multi-mesh campaign or root study.
    monkeypatch.setattr(onset, 'DROPS', (0., .005, .01))
    saved, progress = {}, []
    def publish(label, raw):
        assert label not in saved
        saved[label] = raw
        data = canonical(raw)
        return {'name': label+'.json', 'bytes': len(data), 'sha256': sha(data)}
    result = onset.records(count=2, progress=lambda phase, label: progress.append((phase, label)), publish_raw=publish)
    assert result['disposition'] == 'NO_LATERAL_CROSSING_OBSERVED_ON_FIXED_GRID'
    assert list(saved) == ['grid-00', 'grid-01', 'grid-02']
    for label, raw in saved.items():
        assert len(raw['trial']['assembly']['positions']) == 5
        assert raw['trial']['assembly']['response']['tangent'].shape == (30, 30)
        assert raw['spectra']['free_dimension'] == 18
        assert raw['spectra']['out_of_plane_dimension'] == 9
        assert raw['spectra']['out_of_plane']['lowest_nodal_increment'].shape == (5, 6)
        assert max(raw['state_errors'].values()) <= 1e-11
        assert result['raw_bindings'][label]['sha256'] == sha(canonical(raw))
    assert progress[0] == ('INITIALIZATION', None)
    assert progress[-1] == ('PROBE_COMPLETE', None)
    assert len(progress) == 8
