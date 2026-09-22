import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

_scripts = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(_scripts))
import _b3_e4_f03_primal_trends as trends


def test_embedding_preserves_component_and_polynomial_indices():
    coarse = np.arange(2*(4**2-1), dtype=float)
    fine = trends.embed(coarse, 4, 8).reshape(2, 7, 9)
    np.testing.assert_array_equal(fine[:, :3, :5], coarse.reshape(2, 3, 5))
    assert np.count_nonzero(fine[:, 3:]) == 0
    assert np.count_nonzero(fine[:, :, 5:]) == 0


def test_scalar_requires_both_final_pairs_and_retains_signs():
    result = trends.scalar_trend([1., 1., 1., 1.05, 1.051], 1.)
    assert not result['passed']
    assert result['signed_changes'][-1] > 0
    assert result['relative_changes'][-1] < .01
    assert trends.scalar_trend([1., 1., 1., 1.001, 1.0011], 1.)['passed']
    assert not trends.scalar_trend([1., 1., 1., 1.0001, 1.001], 1.)['passed']


@pytest.fixture
def sequence():
    saved, metrics = {}, {}
    for n in trends.LEVELS:
        d = 2*(n*n-1)
        q = np.zeros(d); q[0] = 1
        saved[n] = {'K_shell': np.eye(d), 'K_beam': np.zeros((d, d)), 'q': q,
            'density_coefficients': np.array([[1000., 0, 0]]), 'cosine': np.zeros(3),
            'atoms': np.zeros((2, 3))}
        observables = {name: 1. for name in trends.SCALAR_SCALES}
        observables.update(total_energy_j=.5, full_functional_norm_N=1000.)
        metrics[n] = {'observables': observables}
    return saved, metrics


def test_stationary_exact_nested_sequence_and_physical_hold(sequence):
    saved, metrics = sequence
    assert trends.assess_sequence(saved, metrics)['status'] == 'PASSED_BOUNDED_PRIMAL_REFERENCE'
    metrics[24]['observables']['root_reaction'] = 100000.
    result = trends.assess_sequence(saved, metrics)
    assert result['status'] == 'UNRESOLVED_RITZ_REFERENCE'
    assert not result['scalars']['root_reaction']['passed']


def test_nested_energy_failure_has_precedence_and_inventory_required(sequence):
    saved, metrics = sequence
    metrics[24]['observables']['total_energy_j'] = .4
    result = trends.assess_sequence(saved, metrics)
    assert result['status'] == 'FAILED_NUMERICAL_SCREEN'
    assert not result['transitions'][-1]['energy_nondecreasing']
    del saved[24]
    with pytest.raises(ValueError, match='complete'):
        trends.assess_sequence(saved, metrics)


def test_nonpositive_norm_is_not_relabelled_convergence(sequence, monkeypatch):
    def negative(*args, **kwargs):
        raise trends.NegativeGreenResponse('negative quadratic form')
    monkeypatch.setattr(trends, 'norm_squared', negative)
    result = trends.assess_sequence(*sequence)
    assert result['status'] == 'FAILED_NUMERICAL_SCREEN'
    assert 'negative' in result['transitions'][0]['functional']['failure']


def test_unexpected_norm_error_is_not_disguised_as_numerical_failure(sequence, monkeypatch):
    def programming_error(*args, **kwargs):
        raise ValueError('unexpected implementation problem')
    monkeypatch.setattr(trends, 'norm_squared', programming_error)
    with pytest.raises(ValueError, match='implementation'):
        trends.assess_sequence(*sequence)
