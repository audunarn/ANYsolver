"""Reference kinetic/modal development checks, not dynamic qualification."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, rigid_matrix, T6
from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import (
    reference_kinetic_factors, eliminate_trace_mass_kernel, symmetric_modes, reference_chain_pencil,
    full_inertia_pencil,
)
from test_ge_beam3_curved_p5_algebra_probe import reference, section


def section_mass():
    inertia = np.diag([2.]*3+[.2, .1, .15])
    coupling = np.array([[0., -.02, .01], [.02, 0., -.03], [-.01, .03, 0.]])
    inertia[:3, 3:] = coupling
    inertia[3:, :3] = coupling.T
    inertia[3, 4] = inertia[4, 3] = .005
    return inertia


def direct_kinetic_energy(ref, local_map, inertia, velocity):
    """Separate velocity-field evaluation; no assembled mass/factor is used."""
    nodal = velocity.reshape(3, 6)
    spin = (local_map @ velocity).reshape(2, 3)
    result = 0.
    points, weights = np.polynomial.legendre.leggauss(48)
    for cell in (0, 1):
        for point, weight in zip(points, weights):
            t = (point+1)/2
            xi = cell-1+t
            offset = ref.position(xi)-((1-t)*ref.coordinates[cell]+t*ref.coordinates[cell+1])
            translation = (1-t)*nodal[cell, :3]+t*nodal[cell+1, :3]+np.cross(spin[cell], offset)
            frame = ref.frame(xi)
            material = np.r_[frame.T @ translation, frame.T @ spin[cell]]
            result += weight*ref.jacobian(xi)*(material @ inertia @ material)/4
    return result


@pytest.mark.parametrize('height', [0., .4, .7])
def test_kinetic_energy_matches_direct_lifted_velocity_integration(height):
    ref = reference(height)
    made = reference_kinetic_factors(ref, section(), section_mass())
    velocity = np.cos(np.arange(18)+.4)/3
    expected = direct_kinetic_energy(ref, made.static_map[18:], section_mass(), velocity)
    assert abs(made.kinetic_energy(velocity)-expected) <= 1e-11*max(1., abs(expected))
    assert np.linalg.norm(made.mass-made.mass.T) <= 1e-11
    assert np.linalg.matrix_rank(made.full) == 15
    assert np.linalg.matrix_rank(made.reduced) == 15
    rotations = [6*i+j for i in range(3) for j in (3, 4, 5)]
    assert np.array_equal(made.full[:, rotations], np.zeros((made.full.shape[0], 9)))


def test_rigid_velocity_uses_the_complete_curved_centreline():
    ref = reference(.6, .2, .15)
    inertia = section_mass()
    factors = reference_kinetic_factors(ref, section(), inertia)
    shift, spin = np.array([.2, -.3, .4]), np.array([.1, .2, -.3])
    nodal = np.column_stack((shift+np.cross(spin, ref.coordinates), np.tile(spin, (3, 1))))
    assert np.linalg.norm(factors.static_map[18:] @ nodal.ravel()-np.tile(spin, 2)) <= 1e-11
    expected = 0.
    points, weights = np.polynomial.legendre.leggauss(48)
    for cell in (0, 1):
        for point, weight in zip(points, weights):
            xi = cell-1+(point+1)/2
            frame = ref.frame(xi)
            physical = np.r_[frame.T @ (shift+np.cross(spin, ref.position(xi))), frame.T @ spin]
            expected += weight*ref.jacobian(xi)*(physical @ inertia @ physical)/4
    assert abs(factors.kinetic_energy(nodal.ravel())-expected) <= 1e-11


def test_straight_rigid_kinetic_energy_matches_closed_integral():
    ref = reference(0.)
    inertia = np.diag([2.]*3+[.2, .1, .15])
    factors = reference_kinetic_factors(ref, section(), inertia)
    v, omega = np.array([.2, -.3, .4]), np.array([.1, .2, -.3])
    nodal = np.column_stack((v+np.cross(omega, ref.coordinates), np.tile(omega, (3, 1))))
    frame = ref.nodal_triads[0]
    expected = .5*(4*(v @ v)+(4/3)*(omega[1]**2+omega[2]**2)
                   +2*(omega @ frame @ inertia[3:, 3:] @ frame.T @ omega))
    assert abs(factors.kinetic_energy(nodal.ravel())-expected) <= 1e-11


@pytest.mark.parametrize('height', [0., .4])
def test_three_trace_modes_are_eliminated_without_artificial_mass(height):
    ref = reference(height)
    factors = reference_kinetic_factors(ref, section(), section_mass())
    null, mapping, stiffness, mass = eliminate_trace_mass_kernel(factors)
    assert null.shape == (18, 3) and mapping.shape == (18, 15)
    assert np.linalg.norm(factors.reduced @ null) <= 1e-11
    assert np.linalg.eigvalsh(null.T @ factors.stiffness @ null).min() > 0
    assert np.linalg.norm(null.T @ factors.stiffness @ mapping) <= 1e-11
    eig, vectors = symmetric_modes(stiffness, mass)
    assert np.max(np.abs(eig[:6])) <= 1e-11*np.max(np.abs(eig))
    assert eig[6] > 1e-3
    expanded = mapping @ vectors
    residual = factors.stiffness @ expanded-(factors.mass @ expanded)*eig
    assert np.linalg.norm(residual) <= 1e-11*max(1., np.linalg.norm(factors.stiffness @ expanded))
    assert np.linalg.norm(expanded.T @ factors.mass @ expanded-np.eye(15)) <= 1e-11
    rigid = rigid_matrix(ref.coordinates)
    assert np.linalg.norm(factors.stiffness_factor @ rigid) <= 1e-11


def test_mass_covariance_and_connectivity_reversal():
    ref = reference(.6, .2, .15)
    original = reference_kinetic_factors(ref, section(), section_mass())
    g = rotation([1.8, -1.7, 2.1])
    moved = reference_kinetic_factors(ref.rigidly_transformed(g, [2., -3., 4.]), section(), section_mass())
    transform = np.kron(np.eye(6), g)
    assert np.linalg.norm(moved.mass-transform @ original.mass @ transform.T) <= 1e-11
    rev = reference_kinetic_factors(ref.reversed(), T6 @ section() @ T6.T, T6 @ section_mass() @ T6.T)
    permutation = np.r_[np.arange(12, 18), np.arange(6, 12), np.arange(6)]
    assert np.linalg.norm(rev.mass-original.mass[np.ix_(permutation, permutation)]) <= 1e-11


def test_static_kinetic_reduction_does_not_silently_equal_p3_nodal_mass():
    ref = reference(0.)
    inertia = np.diag([2.]*3+[.2, .1, .15])
    factors = reference_kinetic_factors(ref, section(), inertia)
    transform = np.kron(np.eye(2), ref.nodal_triads[0])
    spatial = transform @ inertia @ transform.T
    p3 = np.zeros((18, 18))
    for cell in (0, 1):
        for i in (0, 1):
            for j in (0, 1):
                p3[6*(cell+i):6*(cell+i+1), 6*(cell+j):6*(cell+j+1)] += spatial*(2 if i == j else 1)/6
    assert np.linalg.matrix_rank(p3) == 18
    assert np.linalg.norm(factors.mass-p3) > .01


@pytest.mark.parametrize('family,offset', [('axial', 0), ('torsion', 3)])
def test_straight_clamped_frequency_refines_toward_rod_reference(family, offset):
    # For a fixed-free rod, omega1=pi/(2L)*sqrt(stiffness/inertia).
    # Restrict to an uncoupled exact mode family; this is not bending or
    # whole-spectrum qualification and does not conceal other eigenvalues.
    elastic = np.diag([100., 60., 70., 10., 12., 14.])
    inertia = np.diag([2.]*3+[.2, .1, .15])
    expected = np.pi/4*np.sqrt(elastic[offset, offset]/inertia[offset, offset])
    errors = []
    for count in (1, 2, 4, 8):
        stiffness, mass = reference_chain_pencil(parabolic_references(0., count), elastic, inertia)
        active = np.arange(6+offset, len(stiffness), 6)
        eigenvalues, _ = symmetric_modes(stiffness[np.ix_(active, active)], mass[np.ix_(active, active)])
        assert eigenvalues.min() > 0
        errors.append(abs(np.sqrt(eigenvalues[0])/expected-1))
    assert all(b < a for a, b in zip(errors, errors[1:]))
    assert errors[-1] < .02


def test_clamped_curved_mass_and_all_eigenvalues_are_positive():
    factors = reference_kinetic_factors(reference(.4), section(), section_mass())
    eigenvalues, modes = symmetric_modes(factors.stiffness[6:, 6:], factors.mass[6:, 6:])
    assert len(eigenvalues) == 12 and eigenvalues.min() > 0
    assert np.linalg.norm(modes.T @ factors.mass[6:, 6:] @ modes-np.eye(12)) <= 1e-11


@pytest.mark.parametrize('clamped', [False, True])
def test_full_cell_inertia_modes_satisfy_original_uncondensed_equations(clamped):
    factors = reference_kinetic_factors(reference(.4), section(), section_mass())
    mapping, stiffness, mass = full_inertia_pencil(factors, clamped=clamped)
    eig, vectors = symmetric_modes(stiffness, mass)
    expanded = mapping @ vectors
    original_k = factors.uncondensed_stiffness_factor.T @ factors.uncondensed_stiffness_factor
    original_m = factors.full.T @ factors.full
    active = slice(6, 24) if clamped else slice(None)
    residual = (original_k @ expanded-(original_m @ expanded)*eig)[active]
    assert np.linalg.norm(residual) <= 1e-11*max(1., np.linalg.norm((original_k @ expanded)[active]))
    assert np.linalg.norm(expanded.T @ original_m @ expanded-np.eye(len(eig))) <= 1e-11
    if clamped:
        assert len(eig) == 12 and eig.min() > 0
        assert np.array_equal(expanded[:6], np.zeros((6, 12)))
    else:
        assert len(eig) == 15
        assert np.max(np.abs(eig[:6])) <= 1e-11*np.max(np.abs(eig))
        assert eig[6] > 1e-3


def test_static_mass_approximation_error_is_preserved_not_called_qualification():
    factors = reference_kinetic_factors(reference(.4), section(), section_mass())
    _, k, m = full_inertia_pencil(factors, clamped=True)
    full, _ = symmetric_modes(k, m)
    approximate, _ = symmetric_modes(factors.stiffness[6:, 6:], factors.mass[6:, 6:])
    assert np.all(approximate >= full-1e-11*np.max(np.abs(full)))
    error = np.sqrt(approximate/full)-1
    # Preserve the actual coarse-macro discrepancy. Passing this test records
    # a limitation, NOT a passing 2% engineering/qualification gate.
    assert error[3] > .02 and error[5] > .04


def test_trace_inertia_mutation_is_rejected_before_algebraic_elimination():
    from dataclasses import replace
    factors = reference_kinetic_factors(reference(.4), section(), section_mass())
    changed = factors.full.copy()
    changed[0, 3] = .01
    with pytest.raises(ValueError, match='exactly absent'):
        full_inertia_pencil(replace(factors, full=changed))


def test_invalid_inputs_and_negative_eigenvalues_are_not_hidden():
    ref = reference(.4)
    for order in (1, 65, True):
        with pytest.raises(ValueError, match='order'):
            reference_kinetic_factors(ref, section(), section_mass(), order=order)
    for inertia in (-np.eye(6), np.full((6, 6), np.nan)):
        with pytest.raises(ValueError):
            reference_kinetic_factors(ref, section(), inertia)
    for refs in ([], [ref]*3, [ref]*16):
        with pytest.raises(ValueError, match='macros'):
            reference_chain_pencil(refs, section(), section_mass())
    with pytest.raises(ValueError, match='shared'):
        reference_chain_pencil([ref, ref], section(), section_mass())
    with pytest.raises(ValueError, match='symmetric'):
        symmetric_modes(np.array([[1., 1.], [0., 1.]]), np.eye(2))
    with pytest.raises(np.linalg.LinAlgError):
        symmetric_modes(np.eye(2), np.diag([1., 0.]))
    values, _ = symmetric_modes(np.diag([-2., 0., 3.]), np.eye(3))
    assert np.array_equal(values, [-2., 0., 3.])
