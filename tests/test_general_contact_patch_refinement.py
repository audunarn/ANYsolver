"""Coupled nonmatching Q4/S3 partial-contact resolution control."""

import pytest

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, LoadCase, create_shell_element,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.fe_core import FEModel


def test_refined_q4_patch_on_s3_meets_declared_pointwise_gap_budget():
    divisions = 4
    model = FEModel("partial_q4_s3_patch_refinement")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node, (x, y) in enumerate(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)), 1):
        model.add_node(node, x, y, 0.0)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3), "elastic", thickness=0.05,
        formulation="e4-pl-s3-v2d", reference_normal=(0, 0, 1),
        reference_surface_offset=0.01,
    ))

    def upper_node(i, j):
        return 4 + j * (divisions + 1) + i

    upper_nodes = []
    for j in range(divisions + 1):
        for i in range(divisions + 1):
            node = upper_node(i, j)
            model.add_node(node, 0.15 + i / divisions, 0.1 + j / divisions, 0.04)
            upper_nodes.append(node)
    source_elements = []
    load_weights = {node: 0.0 for node in upper_nodes}
    for j in range(divisions):
        for i in range(divisions):
            element = 2 + j * divisions + i
            nodes = (
                upper_node(i, j), upper_node(i + 1, j),
                upper_node(i + 1, j + 1), upper_node(i, j + 1),
            )
            model.add_element(element, create_shell_element(
                element, nodes, "elastic", thickness=0.05,
            ))
            source_elements.append(element)
            for node in nodes:
                load_weights[node] += 0.25 / divisions**2
    assert sum(load_weights.values()) == pytest.approx(1.0)
    model.add_boundary_condition(BoundaryCondition(
        "target_fixed", (1, 2, 3),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_normal_guide", tuple(upper_nodes),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    load = LoadCase("uniform_pressure_on_upper_square")
    for node, weight in load_weights.items():
        load.add_nodal_load(node, forces=(0.0, 0.0, -0.4 * weight))
    definition = ContactDefinition(
        surfaces=(ContactSurface("source", tuple(source_elements), side="bottom"),
                  ContactSurface("target", (1,), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "source", "target", 4.0e6, 1.0e-5,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="restricted_sliding", sliding_difference_step=1.0e-8,
    )
    report = validate_general_contact(model, definition, settings)
    assert report.valid, report.issues
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        kinematics="von_karman", num_steps=1, max_iterations=12,
        min_step_fraction=0.1,
    )
    assert result.status == "completed", (
        result.failure_reason, result.load_factor, result.info.get("general_contact"),
    )
    contact = result.info["general_contact"]
    assert contact["profile"] == "PLANAR_Q4_S3_PATCH_RESTRICTED_SLIDING_MORTAR_DEV_V0"
    assert contact["pressure_rank"] == 13
    assert contact["current_overlap_area"] == pytest.approx(0.28125)
    assert contact["gap_tolerance_met"]
    assert contact["conservative_lower_gap"] >= -1.0e-5
    assert contact["integration_force"][2] == pytest.approx(0.4, rel=1e-6)
    assert contact["target_force"][2] == pytest.approx(-0.4, rel=1e-6)
    assert result.steps[-1].support_reactions["target_fixed"][2] == pytest.approx(
        0.4, rel=1e-6,
    )
