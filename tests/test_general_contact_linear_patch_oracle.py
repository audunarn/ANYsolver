"""Independent Q1 mortar calculation for a bounded Q4/S3 patch.

The contact oracle integrates the Q1 pressure basis analytically. The
production kernel is queried only after its expected active set and resultant
have been calculated independently.
"""

import numpy as np

from anysolver import (
    BoundaryCondition,
    ContactDefinition,
    ContactInteraction,
    ContactSolverSettings,
    ContactSurface,
    create_shell_element,
    validate_general_contact,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.core import contact_scope


def test_q4_against_nonmatching_s3_partial_pressure_oracle():
    gap = 50.0e-6
    selected_displacement = 90.0e-6
    epsilon = 100_000.0
    model = FEModel("q4_s3_linear_full_overlap_oracle")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node, x, y, z in (
        (1, 0.0, 0.0, 0.04005),
        (2, 0.5, 0.0, 0.04005),
        (3, 1.0, 0.0, 0.04005),
        (4, 0.0, 1.0, 0.04005),
        (5, 0.5, 1.0, 0.04005),
        (6, 1.0, 1.0, 0.04005),
        (7, -0.2, -0.1, 0.0),
        (8, 1.2, -0.1, 0.0),
        (9, 1.2, 1.1, 0.0),
        (10, -0.2, 1.1, 0.0),
    ):
        model.add_node(node, x, y, z)
    for element_id, nodes in ((1, (1, 2, 5, 4)),
                              (2, (2, 3, 6, 5))):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            reference_normal=(0.0, 0.0, 1.0),
        ))
    for element_id, nodes in ((3, (7, 8, 10)), (4, (8, 9, 10))):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d",
            reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "fixed_target", (7, 8, 9, 10),
        {axis: 0.0 for axis in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "guided_source", (1, 2, 3, 4, 5, 6),
        {axis: 0.0 for axis in ("ux", "uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "supported_left_edge", (1, 4), {"uz": 0.0},
    ))

    # Each Q4 is a half-width rectangle. Independently assemble the exact
    # Q1 mass matrix and positive support over the two source faces.
    one_dimensional_mass = np.array([[1.0 / 3.0, 1.0 / 6.0],
                                      [1.0 / 6.0, 1.0 / 3.0]])
    q1_corners = ((0, 0), (1, 0), (1, 1), (0, 1))
    local_mass = np.array([
        [one_dimensional_mass[ix, jx] * one_dimensional_mass[iy, jy]
         for jx, jy in q1_corners]
        for ix, iy in q1_corners
    ])
    mortar_mass = np.zeros((6, 6))
    for nodes in ((0, 1, 4, 3), (1, 2, 5, 4)):
        mortar_mass[np.ix_(nodes, nodes)] += 0.5 * local_mass
    support = np.sum(mortar_mass, axis=1)
    prescribed_shape = np.array((0.0, -0.5, -1.0, 0.0, -0.5, -1.0))
    weighted_gap = gap + mortar_mass @ (
        prescribed_shape * selected_displacement
    ) / support
    pressure = np.maximum(0.0, -epsilon * weighted_gap)
    np.testing.assert_array_equal(
        pressure > 0.0, (False, False, True, False, False, True)
    )
    expected_contact_force = float(np.dot(support, pressure))
    expected_right_contact_force = float(np.sum(
        (mortar_mass @ pressure)[[2, 5]]
    ))

    definition = ContactDefinition(
        surfaces=(
            ContactSurface("q4_source", (1, 2), "bottom"),
            ContactSurface("s3_target", (3, 4), "top"),
        ),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", epsilon, 50.0e-6,
            normal_law="augmented",
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", normal_discretization="primal_mortar",
        q4_source_gap_certificate="projected_matching",
        general_s3_difference_step=2.0e-5,
        maximum_general_s3_energy_evaluations=5000,
        q4_source_area_tolerance=1.0e-9,
        q4_source_weighted_gap_tolerance=1.0e-10,
        maximum_q4_source_integration_triangles=128,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1.0e-5,
        q4_source_support_hessian_tolerance=1.0e-5,
        q4_source_weighted_gap_gradient_tolerance=1.0e-5,
        q4_source_weighted_gap_hessian_tolerance=1.0e-5,
        pressure_tolerance=1.0e-5,
        maximum_augmentations=7,
    )
    capability = validate_general_contact(model, definition, settings)
    assert capability.valid, capability.issues
    with contact_scope(model, definition, settings,
                       allow_augmented=True) as manager:
        displacement = np.zeros(manager.n_dof)
        for node, shape in enumerate(prescribed_shape, start=1):
            displacement[model.mesh.get_node(node).dofs[2]] = (
                shape * selected_displacement
            )
        contact_force, contact_tangent, contact = manager.evaluate(
            displacement, tangent=True,
        )
    np.testing.assert_array_equal(contact.source_pressure_node_ids,
                                  (1, 2, 3, 4, 5, 6))
    np.testing.assert_allclose(contact.reference_support_m2, support,
                               rtol=1.0e-8, atol=1.0e-10)
    np.testing.assert_allclose(contact.normalized_weighted_gap_m,
                               weighted_gap, rtol=1.0e-3, atol=1.0e-8)
    np.testing.assert_allclose(contact.numerical_pressure_pa,
                               pressure, rtol=1.0e-3, atol=1.0e-6)
    np.testing.assert_allclose(
        contact.integration_force[2], expected_contact_force,
        rtol=1.0e-3, atol=1.0e-6,
    )
    np.testing.assert_allclose(
        np.asarray(contact.integration_force)
        + np.asarray(contact.target_force),
        0.0, atol=1.0e-8,
    )
    np.testing.assert_allclose(
        -sum(contact_force[model.mesh.get_node(node).dofs[2]]
             for node in (3, 6)),
        expected_right_contact_force,
        rtol=1.0e-3, atol=1.0e-6,
    )
    active = (pressure > 0.0).astype(float)
    expected_contact_tangent = (
        epsilon * mortar_mass @ np.diag(active / support) @ mortar_mass
    )
    right_dofs = [model.mesh.get_node(node).dofs[2] for node in (3, 6)]
    np.testing.assert_allclose(
        np.sum(contact_tangent[np.ix_(right_dofs, right_dofs)]),
        np.sum(expected_contact_tangent[np.ix_([2, 5], [2, 5])]),
        rtol=1.0e-3, atol=1.0e-3,
    )
    assert contact.gap_tolerance_met
    assert contact.active_pressure_dofs == 2
