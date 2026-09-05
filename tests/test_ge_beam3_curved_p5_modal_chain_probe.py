"""Continuum comparison of bounded full-inertia chains; author research only."""

import ast
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_modal_reference as continuum
from docs.reference_cases.ge_beam3_curved_p5_modal_chain_probe import clamped_full_inertia_chain
from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_continuum_reference import parabolic_tip_compliance
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import symmetric_modes, reference_chain_pencil, reference_kinetic_factors, full_inertia_pencil
from test_ge_beam3_curved_p5_mass_probe import section, section_mass


@pytest.fixture(scope='module', params=[0., .4, .7])
def sample(request):
    height = request.param
    target = continuum.parabolic_modal_reference(height, section(), section_mass(), terms=16)
    return height, target


def test_reference_polynomial_and_quadrature_convergence(sample):
    height, target = sample
    lower = continuum.parabolic_modal_reference(height, section(), section_mass(), terms=12)
    other = continuum.parabolic_modal_reference(height, section(), section_mass(), terms=16, order=96)
    # This 1e-7 p-refinement check is a declared research reference-accuracy
    # check, not a certified continuum bound or a changed mechanics tolerance.
    assert np.max(np.abs(np.sqrt(lower.squared_frequencies[:6]/target.squared_frequencies[:6])-1)) < 1e-7
    assert np.max(np.abs(np.sqrt(other.squared_frequencies[:6]/target.squared_frequencies[:6])-1)) < 1e-11
    modes = target.coefficients[:, :6]
    residual = target.stiffness @ modes-(target.mass @ modes)*target.squared_frequencies[:6]
    assert np.linalg.norm(residual) <= 1e-11*max(1., np.linalg.norm(target.stiffness @ modes))
    assert np.linalg.norm(modes.T @ target.mass @ modes-np.eye(6)) <= 1e-11


def test_continuum_zero_frequency_limit_matches_analytic_tip_compliance(sample):
    height, target = sample
    tip = np.tile(2*np.eye(6), (1, 16))
    made = tip @ np.linalg.solve(target.stiffness, tip.T)
    exact = np.array(parabolic_tip_compliance(height, section()), dtype=float)
    # Approximation of a nonpolynomial continuum solution, not an exact identity.
    assert np.linalg.norm(made-exact) <= 1e-9*np.linalg.norm(exact)


def mode_overlap(refs, expanded, coefficients, inertia):
    """Compare actual spatial kinetic fields, not nodal eigenvector ordering."""
    count = len(refs)
    nodal_size = 6*(2*count+1)
    modes = expanded.shape[1]
    terms = coefficients.shape[0]//6
    overlap = np.zeros((modes, modes))
    norm_beam, norm_reference = np.zeros(modes), np.zeros(modes)
    points, weights = np.polynomial.legendre.leggauss(16)
    for element, ref in enumerate(refs):
        for cell in (0, 1):
            spin = expanded[nodal_size+6*element+3*cell:nodal_size+6*element+3*cell+3]
            left, right = 2*element+cell, 2*element+cell+1
            for point, weight in zip(points, weights):
                t = (point+1)/2
                xi = cell-1+t
                global_t = -1+(2*element+cell+t)/count
                offset = ref.position(xi)-((1-t)*ref.coordinates[cell]+t*ref.coordinates[cell+1])
                translation = (1-t)*expanded[6*left:6*left+3]+t*expanded[6*right:6*right+3]
                translation += np.cross(spin.T, offset).T
                shape = (global_t+1)*np.polynomial.legendre.legvander(global_t, terms-1).ravel()
                reference_field = np.einsum('j,jik->ik', shape, coefficients.reshape(terms, 6, modes))
                frame = ref.frame(xi)
                transform = np.kron(np.eye(2), frame.T)
                beam_field = transform @ np.vstack((translation, spin))
                reference_field = transform @ reference_field
                measure = weight*ref.jacobian(xi)/2
                overlap += measure*(beam_field.T @ inertia @ reference_field)
                norm_beam += measure*np.sum(beam_field*(inertia @ beam_field), axis=0)
                norm_reference += measure*np.sum(reference_field*(inertia @ reference_field), axis=0)
    return overlap**2/(norm_beam[:, None]*norm_reference[None, :])


def test_first_six_frequencies_and_physical_modes_approach_continuum(sample):
    height, target = sample
    errors = []
    for count in (1, 2, 4, 8):
        refs = parabolic_references(height, count)
        pencil = clamped_full_inertia_chain(refs, section(), section_mass())
        eig, vectors = symmetric_modes(pencil.stiffness, pencil.mass)
        assert eig.min() > 0 and len(eig) == 12*count
        errors.append(np.sqrt(eig[:6]/target.squared_frequencies[:6])-1)
    assert np.max(np.abs(errors[-1])) < .02
    assert np.all(np.abs(errors[-1]) < np.abs(errors[-2]))
    expanded = pencil.map @ vectors[:, :6]
    residual = (pencil.full_stiffness @ expanded-(pencil.full_mass @ expanded)*eig[:6])[6:]
    assert np.linalg.norm(residual) <= 1e-11*max(1., np.linalg.norm((pencil.full_stiffness @ expanded)[6:]))
    mac = mode_overlap(refs, expanded, target.coefficients[:, :6], section_mass())
    assert np.all(np.diag(mac) >= .95)
    assert np.array_equal(np.argmax(mac, axis=1), np.arange(6))
    if height == .7:
        # Preserve the observed coarse first-mode nonmonotonicity; this is
        # not a claim that every mode improves on every refinement.
        assert abs(errors[1][0]) > abs(errors[0][0])


def test_single_macro_assembly_matches_prior_full_inertia_pencil():
    refs = parabolic_references(.4, 1)
    factors = reference_kinetic_factors(refs[0], section(), section_mass())
    mapping, stiffness, mass = full_inertia_pencil(factors, clamped=True)
    assembled = clamped_full_inertia_chain(refs, section(), section_mass())
    assert np.linalg.norm(assembled.map-mapping) <= 1e-11
    assert np.linalg.norm(assembled.stiffness-stiffness) <= 1e-11
    assert np.linalg.norm(assembled.mass-mass) <= 1e-11


def test_independent_straight_bending_limit_includes_both_planes():
    elastic = np.diag([1e4]*3+[10., 1., 2.])
    inertia = np.diag([1.]*3+[1e-4]*3)
    target = continuum.parabolic_modal_reference(0., elastic, inertia, terms=16)
    # Euler-Bernoulli asymptotic engineering reference, not an exact equality
    # for a shear-flexible/rotary-inertia continuum. Both bending planes enter.
    expected = 1.875104068711961**2/4*np.sqrt([1., 2.])
    assert np.max(np.abs(np.sqrt(target.squared_frequencies[:2])/expected-1)) < .02
    made = clamped_full_inertia_chain(parabolic_references(0., 8), elastic, inertia)
    eig, _ = symmetric_modes(made.stiffness, made.mass)
    assert np.max(np.abs(np.sqrt(eig[:2])/expected-1)) < .02


def test_static_reduction_converges_but_does_not_replace_full_inertia():
    target = continuum.parabolic_modal_reference(.4, section(), section_mass(), terms=16)
    refs = parabolic_references(.4, 8)
    stiffness, mass = reference_chain_pencil(refs, section(), section_mass())
    eig, _ = symmetric_modes(stiffness[6:, 6:], mass[6:, 6:])
    assert np.max(np.abs(np.sqrt(eig[:6]/target.squared_frequencies[:6])-1)) < .02
    full = clamped_full_inertia_chain(refs, section(), section_mass())
    full_eig, _ = symmetric_modes(full.stiffness, full.mass)
    assert np.max(np.abs(np.sqrt(eig[:6]/full_eig[:6])-1)) > 1e-4


def test_reference_has_no_producer_or_frame_imports():
    tree = ast.parse(Path(continuum.__file__).read_text(encoding='utf-8'))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ('__import__', 'eval', 'exec', 'compile')
    assert set(imports) == {'dataclasses', 'numpy'}


def test_invalid_bounds_inputs_and_nonconforming_chain_are_rejected():
    for kwargs in ({'terms': 17}, {'terms': True}, {'order': 128}):
        with pytest.raises(ValueError):
            continuum.parabolic_modal_reference(.4, section(), section_mass(), **kwargs)
    for height in (-1., .76, np.nan):
        with pytest.raises(ValueError):
            continuum.parabolic_modal_reference(height, section(), section_mass())
    for matrix in (-np.eye(6), np.full((6, 6), np.nan), np.eye(5)):
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            continuum.parabolic_modal_reference(.4, matrix, section_mass())
    ref = parabolic_references(.4, 1)[0]
    with pytest.raises(ValueError, match='macros'):
        clamped_full_inertia_chain([ref]*3, section(), section_mass())
    with pytest.raises(ValueError, match='shared'):
        clamped_full_inertia_chain([ref]*2, section(), section_mass())
