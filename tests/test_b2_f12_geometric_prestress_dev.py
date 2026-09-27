"""Bounded private B2 constant-axial prestress mechanics screen."""

import math

import numpy as np
import pytest
from scipy.linalg import eig

from anysolver._b2_physical_flexibility_linear import LinearOperator, LinearSection
from anysolver._b2_physical_linear_definition import PhysicalB2Member


def _section(radius_m=.005):
    inertia = math.pi*radius_m**4/4
    return LinearSection.isotropic(
        E=210e9, nu=.3, area=math.pi*radius_m**2,
        Iy=inertia, Iz=inertia, J=2*inertia, ky=.9, kz=.9)


@pytest.mark.parametrize("generalized", (False, True))
def test_constant_axial_hessian_matches_independent_trace_slope_work(generalized):
    if generalized:
        stiffness = np.diag([10., 7., 9., 3., 2., 4.])
        stiffness[0, 4] = stiffness[4, 0] = .4
        stiffness[1, 5] = stiffness[5, 1] = .3
        section = LinearSection.generalized(stiffness)
    else:
        section = _section()
    operator = LinearOperator(1.3, section)
    axial_force = 8500.
    geometric = operator.candidate_constant_axial_geometric_stiffness(axial_force)
    assert geometric.shape == (12, 12)
    np.testing.assert_allclose(geometric, geometric.T, rtol=0., atol=0.)
    translation = np.zeros(12)
    translation[[1, 2, 7, 8]] = (.002, -.003, .002, -.003)
    np.testing.assert_allclose(geometric@translation, 0., atol=1e-12)

    displacement = np.array((.001, -.002, .003, .004, -.005, .006,
                             -.001, .007, -.008, -.003, .002, -.004))
    nodes, weights = np.polynomial.legendre.leggauss(5)
    h = 1e-5
    slope_energy = 0.
    for node, weight in zip(nodes, weights):
        station = float((node+1.)/2.)
        pose = operator.trace(displacement,
                              stations=(station-h, station+h)).pose
        slope = (pose[1, 1:3]-pose[0, 1:3])/(2*h*1.3)
        slope_energy += weight*float(slope@slope)
    slope_energy *= axial_force*1.3/4.
    quadratic_energy = .5*float(displacement@geometric@displacement)
    assert abs(quadratic_energy-slope_energy)/quadratic_energy <= 1e-8
    np.testing.assert_allclose(
        operator.candidate_constant_axial_geometric_stiffness(-axial_force),
        -geometric, rtol=0., atol=0.)
    with pytest.raises(ValueError, match="axial force"):
        operator.candidate_constant_axial_geometric_stiffness(float("nan"))


def test_slender_cantilever_first_compressive_factor_converges_to_matched_shear_limit():
    radius = .005
    inertia = math.pi*radius**4/4
    euler = math.pi**2*210e9*inertia/4.
    shear_rigidity = .9*(210e9/(2*(1+.3)))*math.pi*radius**2
    # Eliminating the Timoshenko cross-section rotation gives the
    # shear-corrected critical force for this cantilever.
    matched = euler/(1.+euler/shear_rigidity)
    errors = []
    for count in (1, 2, 4, 8):
        member = LinearOperator(1./count, _section(radius))
        stiffness = member.evaluate(np.zeros(12)).tangent
        compression = -member.candidate_constant_axial_geometric_stiffness(-1.)
        k = np.zeros((6*(count+1), 6*(count+1)))
        g = np.zeros_like(k)
        for element in range(count):
            local = slice(6*element, 6*(element+2))
            k[local, local] += stiffness
            g[local, local] += compression
        reduced_k, reduced_g = k[6:, 6:], g[6:, 6:]
        eigenvalues, vectors = eig(reduced_k, reduced_g)
        positive = [(float(value.real), vectors[:, index])
                    for index, value in enumerate(eigenvalues)
                    if np.isfinite(value) and abs(value.imag) <= 1e-7*abs(value.real)
                    and value.real > 0.]
        assert positive
        first, mode = min(positive, key=lambda pair: pair[0])
        residual = reduced_k@mode-first*reduced_g@mode
        scale = np.linalg.norm(reduced_k@mode)+first*np.linalg.norm(reduced_g@mode)
        assert np.linalg.norm(residual)/scale <= 1e-8
        errors.append(abs(first/matched-1.))
    assert errors[-1] < .01
    assert all(later < earlier for earlier, later in zip(errors, errors[1:])), errors


def test_global_constant_axial_term_preserves_work_on_member_reversal():
    point = (.8, 0., .6)
    common = dict(source_id="physical-axis", section_id="circle",
                  section=_section(), local_y_global=(0., 1., 0.))
    forward = PhysicalB2Member("forward", node_ids=(1, 2),
                               reference_points_m=((0., 0., 0.), point),
                               **common).compile_local()
    reverse = PhysicalB2Member("reverse", node_ids=(2, 1),
                               reference_points_m=(point, (0., 0., 0.)),
                               **common).compile_local()
    original = forward.global_candidate_constant_axial_geometric_stiffness(17.)
    reversed_order = reverse.global_candidate_constant_axial_geometric_stiffness(17.)
    permutation = np.block([[np.zeros((6, 6)), np.eye(6)],
                            [np.eye(6), np.zeros((6, 6))]])
    np.testing.assert_allclose(original,
                               permutation.T@reversed_order@permutation,
                               rtol=1e-13, atol=1e-11)
    original[0, 0] = 42.
    assert forward.global_candidate_constant_axial_geometric_stiffness(17.)[0, 0] != 42.
