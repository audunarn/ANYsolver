"""Admission and ownership of a retained numerical diagnostic candidate."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    'completion_diagnostic', Path(__file__).parents[1]/'scripts/b3_e4_bl5_completion_sensitivity_dev.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


def test_refined_candidate_has_owned_storage_and_exact_rhs(tmp_path):
    path = tmp_path/'candidate.npz'
    rhs, solution = np.array([1., 0.]), np.array([2., 3.])
    np.savez(path, rhs=rhs, solution=solution)
    first = diagnostic.load_refined_solve(path, rhs, solution.shape)
    first[:] = 99.
    np.testing.assert_array_equal(diagnostic.load_refined_solve(path, rhs, solution.shape), solution)
    with pytest.raises(ValueError, match='unchanged refined derivative RHS'):
        diagnostic.load_refined_solve(path, np.array([1., 1e-30]), solution.shape)


@pytest.mark.parametrize('solution', [np.array([np.nan, 0.]), np.array([np.inf, 0.]),
                                     np.array([1.]), np.array([1., 0.], dtype=np.float32)])
def test_invalid_retained_candidate_is_rejected(tmp_path, solution):
    path = tmp_path/'candidate.npz'
    rhs = np.array([1., 0.])
    np.savez(path, rhs=rhs, solution=solution)
    with pytest.raises(ValueError, match='finite binary64'):
        diagnostic.load_refined_solve(path, rhs, (2,))


def test_refined_candidate_cannot_bypass_original_binding(tmp_path):
    with pytest.raises(ValueError, match='bound retained solve'):
        diagnostic.main(tmp_path, tmp_path, tmp_path/'unused', refined=tmp_path/'candidate.npz')
    assert not (tmp_path/'unused').exists()
