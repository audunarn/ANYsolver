"""Independent Q1 pressure-space controls on partial Q4/Q4 overlap."""

from dataclasses import replace

import numpy as np

from anysolver.general_contact.q4_source_overlap import q4_source_overlap_integrals
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from test_general_contact_q4_q4_augmented import _augmented_case


def _reference_support_gram(start):
    abscissas, weights = np.polynomial.legendre.leggauss(6)
    x = start+(1-start)*(abscissas+1)/2
    x_weights = (1-start)*weights/2
    y = (abscissas+1)/2
    y_weights = weights/2
    support = np.zeros(4)
    gram = np.zeros((4, 4))
    for first, first_weight in zip(x, x_weights):
        for second, second_weight in zip(y, y_weights):
            basis = np.array(((1-first)*(1-second),
                              first*(1-second), first*second,
                              (1-first)*second))
            weight = first_weight*second_weight
            support += weight*basis
            gram += weight*np.outer(basis, basis)
    return support, gram


def test_q4_partial_overlap_retains_q1_support_and_gram_rank():
    source = np.array(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                       (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)))
    for start in (0.5, 0.98):
        target = source.copy()
        target[:, 0] += start
        state = q4_source_overlap_integrals(
            source, source, target,
            area_tolerance=1e-11, weighted_gap_tolerance=1e-11,
            maximum_triangles=300,
        )
        expected_support, expected_gram = _reference_support_gram(start)
        np.testing.assert_allclose(state.support, expected_support,
                                   rtol=0.0, atol=1e-10)
        np.testing.assert_allclose(state.pressure_gram, expected_gram,
                                   rtol=0.0, atol=1e-10)
        np.testing.assert_allclose(state.pressure_gram.sum(axis=1),
                                   state.support, atol=1e-11)
        np.testing.assert_allclose(state.support.sum(),
                                   1-start, atol=1e-11)
        assert np.min(np.linalg.eigvalsh(state.pressure_gram)) > 0.0
        assert state.integration_triangles <= 300


def test_q4_partial_overlap_constant_augmented_pressure_balances_bodies():
    model, definition, settings = _augmented_case()
    for node in (5, 6, 7, 8):
        model.mesh.get_node(node).x += 0.5
    settings = replace(settings, q4_source_gap_certificate="projected_matching")
    manager = GeneralS3PatchManager(model, definition, settings)
    manager.set_normal_multipliers(np.full(4, 10.0))
    displacement = np.zeros(manager.n_dof)
    for node in (1, 2, 3, 4):
        displacement[model.mesh.dof_manager.get_node_dofs(node)[2]] = -0.015
    _force, _tangent, contact = manager.evaluate(displacement, tangent=False)
    assert contact.active_pressure_dofs == 4
    np.testing.assert_allclose(contact.numerical_pressure_pa, 10.0,
                               rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(contact.current_overlap_area, 0.54, atol=1e-10)
    np.testing.assert_allclose(contact.integration_force[2], 5.4,
                               atol=1e-7)
    np.testing.assert_allclose(
        np.asarray(contact.integration_force)+contact.target_force,
        0.0, atol=1e-7,
    )
