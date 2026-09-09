"""Small signed linear-algebra checks; no mechanics qualification claim."""

import numpy as np
import pytest
from docs.reference_cases.ge_beam3_signed_spectrum_probe import (
    reduce_signed_split, shifted_inertia, bracket_lowest,
)


def test_small_signed_roots_survive_large_material_diagonal():
    d = np.array([1., 2., 1e24])
    g = np.array([[-3., .25, 1.], [.25, 0., 2.], [1., 2., 0.]])
    intervals = bracket_lowest(d, g, (-4., 4.), 2)
    expected = np.array([-1., 1.])*np.sqrt(4.+.25**2)
    # High-block correction is O(1e-24), far below the frozen root width.
    assert np.all(intervals[:, 0] <= expected) and np.all(expected <= intervals[:, 1])
    assert intervals[0, 1] < 0. < intervals[1, 0]


def test_exact_zero_cluster_is_bracketed_not_clipped_or_lost():
    intervals = bracket_lowest(np.array([1., 1., 1e24]), np.diag([-1., -1., 0.]), (-1., 1.), 2)
    assert np.all(intervals[:, 0] < 0.) and np.all(intervals[:, 1] > 0.)
    with pytest.raises(ValueError, match='unresolved shifted sign'):
        shifted_inertia(np.ones(2), -np.eye(2), 0.)


def test_large_off_diagonal_stress_coupling_is_not_discarded():
    d = np.array([1., 1e24]); g = np.array([[-3., 1e12], [1e12, 0.]])
    intervals = bracket_lowest(d, g, (-5., 0.), 1)
    # Exact low root approaches -3, not the diagonal-only answer -2.
    assert intervals[0, 0] < -3. < intervals[0, 1]


def test_signed_algebraic_elimination_includes_geometric_trace_and_coupling():
    rng = np.random.default_rng(54)
    f = rng.normal(size=(12, 6)); g = rng.normal(size=(6, 6)); g = .05*(g+g.T)
    mass = np.diag([1., 2., 3., 4., 0., 0.]); free = tuple(range(6)); algebraic = (4, 5)
    d, signed, vectors = reduce_signed_split(f, g, mass, free, algebraic)
    k = f.T@f+g
    np.testing.assert_allclose(vectors.T@k@vectors, np.diag(d)+signed, atol=1e-11, rtol=1e-11)
    np.testing.assert_allclose(vectors.T@mass@vectors, np.eye(4), atol=1e-11, rtol=1e-11)
    np.testing.assert_allclose((k@vectors)[[4, 5]], 0., atol=1e-11)
    assert np.linalg.norm(signed) > .01


@pytest.mark.parametrize('mutation', ['inertia', 'trace', 'nan', 'asymmetric', 'dofs'])
def test_signed_reduction_fails_closed(mutation):
    f = np.eye(4); g = np.zeros((4, 4)); m = np.diag([1., 1., 1., 0.]); dofs = (0, 1, 2, 3)
    if mutation == 'inertia': m[3, 3] = 1e-100
    if mutation == 'trace': g[3, 3] = -2.
    if mutation == 'nan': g[0, 0] = np.nan
    if mutation == 'asymmetric': g[0, 1] = 1.
    if mutation == 'dofs': dofs = (0, 1, 2, 2)
    with pytest.raises((ValueError, np.linalg.LinAlgError)):
        reduce_signed_split(f, g, m, dofs, (3,))


def test_search_does_not_skip_unstable_roots_outside_user_bounds():
    with pytest.raises(ValueError, match='lowest requested'):
        bracket_lowest(np.array([1., 2.]), np.diag([-3., 0.]), (0., 3.), 1)


def test_exact_discrete_characteristic_reference_and_import_boundary():
    import ast
    from fractions import Fraction as F
    from pathlib import Path
    from docs.reference_cases import ge_beam3_straight_discrete_signed_reference as reference
    coefficients = reference.characteristic(100, 0.)
    assert len(coefficients) == 5 and all(type(c) is F for c in coefficients)
    assert coefficients[-1] > 0. and coefficients[0] > 0.
    roots = reference.bending_roots(100, 0.)
    assert 0. < roots[0] < roots[1]
    tree = ast.parse(Path(reference.__file__).read_text())
    assert {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} == {
        'decimal', 'fractions', 'itertools'}
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
