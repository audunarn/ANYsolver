"""Small continuum-reference checks by the same author, not qualification."""

import ast
from decimal import ROUND_DOWN, localcontext
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_continuum_reference as analytical
from docs.reference_cases import ge_beam3_curved_p5_continuum_probe as discrete
from docs.reference_cases.ge_beam3_curved_p5_chain_probe import ReferenceChainProbe
from test_ge_beam3_curved_p5_algebra_probe import section


def quadrature_reference(height, elastic):
    """Direct continuum equilibrium/virtual work, no producer metrics/frames.

    This independently coded quadrature checks the analytical integral, not
    independent authorship. It is not an adaptive multiprecision oracle.
    """
    result = np.zeros((6, 6))
    points, weights = np.polynomial.legendre.leggauss(96)
    for t, weight in zip(points, weights):
        jacobian = np.sqrt(1+4*height*height*t*t)
        frame = np.array([[1/jacobian, 0., -2*height*t/jacobian],
                          [-2*height*t/jacobian, 0., -1/jacobian],
                          [0., 1., 0.]])
        lever = np.array([1-t, -height*(1-t*t), 0.])
        # Build moment columns with cross products, not the polynomial code.
        cross = np.column_stack([np.cross(lever, axis) for axis in np.eye(3)])
        loads = np.zeros((6, 6))
        loads[:3, :3] = frame.T
        loads[3:, :3] = frame.T @ cross
        loads[3:, 3:] = frame.T
        result += weight*jacobian*(loads.T @ np.linalg.solve(elastic, loads))
    return result


def sections():
    scale = np.diag([1e6]*3+[1.]*3)
    return (np.diag([1.]*3+[1., 2., 3.]),
            np.diag([1e12]*3+[1., 2., 3.]), section(), scale @ section() @ scale)


@pytest.mark.parametrize("height", [0., 1e-100, 1e-8, .25, .25000001, .4, .75])
def test_analytical_integrals_match_direct_continuum_quadrature(height):
    for elastic in sections():
        exact = np.array(analytical.parabolic_tip_compliance(height, elastic), dtype=float)
        other = quadrature_reference(height, elastic)
        assert np.linalg.norm(exact-other) <= 1e-11*np.linalg.norm(exact)
        assert np.linalg.norm(exact-exact.T) <= 1e-11*np.linalg.norm(exact)
        assert np.linalg.eigvalsh(exact).min() > 0


def test_straight_reference_matches_closed_timoshenko_tip_formula():
    a, sy, sz, torsion, by, bz = 11., 13., 17., 19., 23., 29.
    exact = np.array(analytical.parabolic_tip_compliance(
        0., np.diag([a, sy, sz, torsion, by, bz])), dtype=float)
    length = 2.
    expected = np.diag([length/a, length/sz+length**3/(3*by),
                        length/sy+length**3/(3*bz), length/torsion,
                        length/bz, length/by])
    expected[1, 5] = expected[5, 1] = length**2/(2*by)
    expected[2, 4] = expected[4, 2] = -length**2/(2*bz)
    assert np.linalg.norm(exact-expected) <= 1e-14*np.linalg.norm(expected)


@pytest.mark.parametrize("elastic", sections(), ids=["unit", "thin", "coupled", "thin-coupled"])
def test_sampled_curved_tip_compliance_converges_without_section_ablation(elastic):
    exact = np.array(analytical.parabolic_tip_compliance(.4, elastic), dtype=float)
    errors = [np.linalg.norm(discrete.discrete_tip_compliance(
        discrete.parabolic_references(.4, count), elastic)-exact)/np.linalg.norm(exact)
        for count in (1, 2, 4, 8)]
    # Engineering development observations only, not a domain/locking gate.
    assert all(b < a for a, b in zip(errors, errors[1:]))
    assert errors[-1] < .02
    assert np.log2(errors[-2]/errors[-1]) >= 1.8
    finest = discrete.discrete_tip_compliance(discrete.parabolic_references(.4, 8), elastic)
    assert np.max(np.linalg.norm(finest-exact, axis=0)/np.linalg.norm(exact, axis=0)) < .02
    # Relative complementary work for every combination of the six tip loads,
    # not just a Frobenius norm dominated by the most compliant direction.
    factor = np.linalg.cholesky(exact)
    normalized = np.linalg.solve(factor, np.linalg.solve(factor, finest-exact).T).T
    assert np.max(np.abs(np.linalg.eigvalsh(normalized))) < .02


@pytest.mark.parametrize("count", [1, 2])
def test_discrete_complementary_work_agrees_with_existing_assembled_solve(count):
    refs = discrete.parabolic_references(.4, count)
    elastic = section()
    model = ReferenceChainProbe(refs, elastic)
    load = np.zeros(model.size)
    load[-6:] = [.2, -.3, .1, .03, .02, -.04]
    response = model.solve(load)
    expected = discrete.discrete_tip_compliance(refs, elastic) @ load[-6:]
    assert np.linalg.norm(response.displacement_high[-6:]+response.displacement_low[-6:]-expected) <= 1e-11


def test_reference_context_independence_and_deterministic_outputs():
    ordinary = analytical.parabolic_tip_compliance(.4, section())
    with localcontext() as context:
        context.prec = 7
        context.rounding = ROUND_DOWN
        context.Emax = 20
        changed = analytical.parabolic_tip_compliance(.4, section())
    assert ordinary == changed
    assert tuple(tuple(str(value) for value in row) for row in ordinary) == tuple(
        tuple(str(value) for value in row) for row in changed)
    refs = discrete.parabolic_references(.4, 2)
    assert np.array_equal(discrete.discrete_tip_compliance(refs, section()),
                          discrete.discrete_tip_compliance(refs, section()))


def test_invalid_inputs_fail_closed():
    for height in (-1., .76, float('nan'), float('inf')):
        with pytest.raises(ValueError, match="height"):
            analytical.parabolic_tip_compliance(height, section())
        with pytest.raises(ValueError, match="bounded"):
            discrete.parabolic_references(height, 1)
    for count in (0, 3, 16, True, 2.):
        with pytest.raises(ValueError, match="bounded"):
            discrete.parabolic_references(.4, count)
    for bad in (np.eye(5), np.full((6, 6), np.nan), -np.eye(6),
                np.eye(6)+np.diag(np.ones(5), 1)):
        with pytest.raises(ValueError):
            analytical.parabolic_tip_compliance(.4, bad)
    refs = discrete.parabolic_references(.4, 1)
    with pytest.raises(ValueError, match="shared"):
        discrete.discrete_tip_compliance(refs*2, section())
    with pytest.raises(ValueError, match="macro"):
        discrete.discrete_tip_compliance(refs*3, section())


def test_force_moment_mapping_mutation_is_detected(monkeypatch):
    refs = discrete.parabolic_references(.4, 2)
    expected = discrete.discrete_tip_compliance(refs, section())
    original = discrete.skew
    monkeypatch.setattr(discrete, 'skew', lambda vector: -original(vector))
    changed = discrete.discrete_tip_compliance(refs, section())
    assert np.linalg.norm(changed-expected) > .1*np.linalg.norm(expected)


def test_analytical_reference_has_only_standalone_standard_library_imports():
    tree = ast.parse(Path(analytical.__file__).read_text(encoding='utf-8'))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ('__import__', 'eval', 'exec', 'compile')
    assert set(imports) == {'decimal', 'math'}
