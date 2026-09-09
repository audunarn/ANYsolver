"""Bounded continuum identities; no production qualification claim."""

import ast
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_straight_prestress_reference as ref


def reference(tension=0.):
    return ref.StraightPrestress(2., 3000., 1000., 1., 1., .001, tension)


@pytest.mark.parametrize('n', [F(-3, 5), F(0), F(2, 3)])
def test_rational_second_variation_from_unexpanded_strains(n):
    ea, s, b, v, theta, curvature = map(F, (3000, 1000, 1, 2, 3, 5))
    stretch = 1+n/ea
    # epsilon^2 coefficient of gamma1; gamma2 and curvature start at epsilon.
    g10, g12 = stretch-1, v*theta-stretch*theta*theta/2
    g21 = v-stretch*theta
    second = 2*ea*g10*g12+s*g21*g21+b*curvature*curvature
    c, d = n-s*stretch, s*stretch*stretch-n*stretch
    assert second == s*v*v+2*c*v*theta+d*theta*theta+b*curvature*curvature
    assert d-c*c/s == n*(stretch-n/s)


def test_static_critical_shape_and_propagator_agree():
    base = reference(); pressure = base.critical_compression()
    loaded = replace(base, tension=-pressure)
    k = np.pi/(2*base.length)
    assert abs(pressure*(1+pressure*(1/base.shear-1/base.axial))-base.bending*k*k) < 1e-14
    # Start with T=0, M=B*k, theta=v=0; exact critical sine rotation.
    from scipy.linalg import expm
    end = expm(base.length*loaded.system(0.))@np.array([0., 0., 0., base.bending*k])
    expected = [(loaded.stretch+pressure/base.shear)/k, 1., 0., 0.]
    np.testing.assert_allclose(end, expected, rtol=1e-11, atol=1e-11)
    assert abs(loaded.bracketed_squared_frequency((-2., 4.))) < 1e-11


@pytest.mark.parametrize('ratio', [0., .5, .98, 1.02, -.5])
def test_signed_shooting_root_matches_conforming_refinement(ratio):
    base = reference(); loaded = replace(base, tension=-ratio*base.critical_compression())
    root = loaded.bracketed_squared_frequency((-2., 4.))
    lower = ref.ritz_squared_frequencies(loaded, terms=8)[0]
    upper = ref.ritz_squared_frequencies(loaded, terms=12)[0]
    # Numerical reference convergence, not interval certification.
    assert abs(lower-root) < 1e-7*max(1., abs(root))
    assert abs(upper-root) < 1e-7*max(1., abs(root))
    assert (root < 0.) == (ratio > 1.)


def test_unloaded_limit_matches_existing_separate_spatial_continuum():
    from docs.reference_cases.ge_beam3_curved_p5_modal_reference import parabolic_modal_reference
    base = reference(); root = base.bracketed_squared_frequency((-2., 4.))
    full = parabolic_modal_reference(0., np.diag([3000., 1000., 1000., 2., 1., 1.]),
        np.diag([1., 1., 1., .002, .001, .001]), terms=16)
    np.testing.assert_allclose(full.squared_frequencies[:2], root, rtol=1e-8, atol=1e-10)


def test_static_tip_compliance_and_equal_modulus_onset_limit():
    from scipy.linalg import expm
    base = reference()
    transfer = expm(base.length*base.system(0.))
    reactions = np.linalg.solve(transfer[2:, 2:], [1., 0.])
    tip = transfer@np.r_[0., 0., reactions]
    np.testing.assert_allclose(tip[:2], [base.length**3/(3*base.bending)+base.length/base.shear,
        base.length**2/(2*base.bending)], rtol=1e-11, atol=1e-11)
    same = replace(base, shear=base.axial)
    assert same.critical_compression() == same.bending*(np.pi/(2*same.length))**2


def test_shooting_operator_mutation_is_detected_by_weak_form(monkeypatch):
    base = reference(); loaded = replace(base, tension=-.5*base.critical_compression())
    expected = ref.ritz_squared_frequencies(loaded)[0]
    original = ref.StraightPrestress.system
    def missing_geometric_term(self, squared_frequency):
        matrix = original(self, squared_frequency)
        matrix[3, 1] = -squared_frequency*self.rotary_mass
        return matrix
    monkeypatch.setattr(ref.StraightPrestress, 'system', missing_geometric_term)
    wrong = loaded.bracketed_squared_frequency((-2., 4.))
    assert abs(wrong-expected) > .1


@pytest.mark.parametrize('changes', [{'length': 0.}, {'shear': 4000.}, {'tension': -3000.},
    {'line_mass': float('nan')}, {'rotary_mass': -1.}, {'bending': True}])
def test_invalid_continuum_inputs_rejected(changes):
    with pytest.raises(ValueError): replace(reference(), **changes)


def test_bad_brackets_fail_without_automatic_search():
    for bracket in ((1., 0.), (-2, 4), (float('nan'), 4.), (-2., -1.)):
        with pytest.raises(ValueError): reference().bracketed_squared_frequency(bracket)


def test_reference_import_boundary():
    tree = ast.parse(Path(ref.__file__).read_text(encoding='utf-8'))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): imports.update(a.name for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.add(node.module)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ('eval', 'exec', '__import__', 'compile')
    assert imports == {'dataclasses', 'math', 'numpy', 'scipy.linalg', 'scipy.optimize'}
