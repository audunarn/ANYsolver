"""Integrated controls for the exploratory guided Q4/Q4 pair slice."""

import numpy as np
import pytest

from anysolver import (
    BoundaryCondition,
    ContactDefinition,
    ContactInteraction,
    ContactSolverSettings,
    ContactSurface,
    LoadCase,
    create_shell_element,
    solve_static_nonlinear,
    validate_general_contact,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.pair import _PlanarQ4PairManager


def _guided_pair(*, split_target=False, target_shift=0.0,
                 director=None):
    model = FEModel("guided_shell_pair")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    if split_target:
        lower_positions = ((0, 0, 0), (0.5, 0, 0), (1, 0, 0),
                           (0, 1, 0), (0.5, 1, 0), (1, 1, 0))
        lower_elements = ((1, (1, 2, 5, 4)), (2, (2, 3, 6, 5)))
        upper_nodes = (7, 8, 9, 10)
        upper_element = 3
    else:
        lower_positions = ((0, 0, 0), (1, 0, 0),
                           (1, 1, 0), (0, 1, 0))
        lower_elements = ((1, (1, 2, 3, 4)),)
        upper_nodes = (5, 6, 7, 8)
        upper_element = 2
    offset = 0.05 * (np.asarray(director, dtype=float)
                     if director is not None else np.array((0.0, 0.0, 1.0)))
    upper_positions = tuple(tuple(np.asarray((x, y, 0.0)) + offset)
                            for x, y in ((0, 0), (1, 0), (1, 1), (0, 1)))
    lower_positions = tuple((x + target_shift, y, z)
                            for x, y, z in lower_positions)
    for node_id, position in enumerate((*lower_positions, *upper_positions), 1):
        model.add_node(node_id, *position)
    for element_id, nodes in lower_elements:
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            reference_normal=director,
        ))
    model.add_element(upper_element, create_shell_element(
        upper_element, upper_nodes, "elastic", thickness=0.05,
        reference_normal=director,
    ))
    lower_nodes = tuple(range(1, len(lower_positions) + 1))
    model.add_boundary_condition(BoundaryCondition(
        "lower", lower_nodes,
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "guide", upper_nodes,
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    load = LoadCase("push_upper_shell")
    for node_id in upper_nodes:
        load.add_nodal_load(node_id, forces=(0.0, 0.0, -0.1))
    definition = ContactDefinition(
        surfaces=(ContactSurface("upper", (upper_element,), side="bottom"),
                  ContactSurface("lower", tuple(item[0] for item in lower_elements),
                                 side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "upper_lower", "upper", "lower", 1.0e6, 1.0e-6,
        ),),
    )
    return model, load, definition, upper_nodes


@pytest.mark.parametrize("split_target", (False, True))
def test_guided_pair_solve_balances_both_shells_and_matches_scalar_reference(split_target):
    model, load, definition, _upper_nodes = _guided_pair(split_target=split_target)
    report = validate_general_contact(model, definition)
    assert report.valid
    assert report.profile == "PLANAR_Q4_PAIR_NORMAL_TRANSLATION_PENALTY_MORTAR_V0"
    result = solve_static_nonlinear(
        model, load, contact=definition, num_steps=1, max_iterations=12,
        kinematics="von_karman",
    )
    assert result.status == "completed", result.failure_reason
    summary = result.info["general_contact"]
    assert summary["reference_overlap_area"] == pytest.approx(1.0)
    assert summary["minimum_gap"] == pytest.approx(-0.4 / 1.0e6, abs=1e-9)
    assert summary["integration_force"] == pytest.approx((0.0, 0.0, 0.4), abs=1e-8)
    assert summary["target_force"] == pytest.approx((0.0, 0.0, -0.4), abs=1e-8)
    np.testing.assert_allclose(
        np.asarray(summary["integration_moment"])
        + np.asarray(summary["target_moment"]), 0.0, atol=1e-8
    )
    assert result.steps[-1].support_reactions["lower"][2] == pytest.approx(
        0.4, abs=1e-8
    )


def test_guided_pair_potential_tangent_and_swept_limit():
    model, _load, definition, upper_nodes = _guided_pair()
    manager = _PlanarQ4PairManager(model, definition)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    for node_id in upper_nodes:
        displacement[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -3.0e-7
    force, tangent, summary = manager.evaluate(displacement)
    assert summary.minimum_gap == pytest.approx(-3.0e-7)
    assert summary.penalty_energy == pytest.approx(0.5 * 1.0e6 * (3.0e-7) ** 2)
    direction = np.zeros_like(displacement)
    for node_id in upper_nodes:
        direction[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = 1.0
    h = 1.0e-8
    plus = manager.evaluate(displacement + h * direction, tangent=False)[0]
    minus = manager.evaluate(displacement - h * direction, tangent=False)[0]
    np.testing.assert_allclose((plus - minus) / (2 * h), tangent @ direction,
                               rtol=1e-7, atol=1e-8)
    target_direction = np.zeros_like(displacement)
    for node_id in range(1, 5):
        target_direction[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = 1.0
    plus = manager.evaluate(displacement + h * target_direction, tangent=False)[0]
    minus = manager.evaluate(displacement - h * target_direction, tangent=False)[0]
    np.testing.assert_allclose((plus - minus) / (2 * h),
                               tangent @ target_direction, rtol=1e-7, atol=1e-8)
    excessive = np.zeros_like(displacement)
    for node_id in upper_nodes:
        excessive[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -1.0e-3
    fraction = manager.admissible_step_fraction(np.zeros_like(displacement), excessive)
    assert fraction == pytest.approx(0.98e-3)
    assert manager.evaluate(fraction * excessive, tangent=False)[2].gap_tolerance_met
    assert np.linalg.norm(force) > 0.0


def test_partial_projected_overlap_transfers_equal_opposite_resultants():
    model, _load, definition, upper_nodes = _guided_pair(target_shift=0.5)
    manager = _PlanarQ4PairManager(model, definition)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    for node_id in upper_nodes:
        displacement[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -5.0e-7
    _force, _tangent, summary = manager.evaluate(displacement)
    assert summary.reference_overlap_area == pytest.approx(0.5)
    assert summary.integration_force[2] == pytest.approx(0.25)
    assert summary.target_force[2] == pytest.approx(-0.25)
    np.testing.assert_allclose(
        np.asarray(summary.integration_moment) + np.asarray(summary.target_moment),
        0.0, atol=1e-10,
    )


def test_tilted_physical_skins_transfer_offset_force_couples():
    director = np.asarray((0.1, 0.0, 1.0), dtype=float)
    director /= np.linalg.norm(director)
    model, _load, definition, upper_nodes = _guided_pair(director=director)
    manager = _PlanarQ4PairManager(model, definition)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    for node_id in upper_nodes:
        displacement[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -1.0e-4
    residual, _tangent, summary = manager.evaluate(displacement)
    upper_couple_y = -sum(
        residual[model.mesh.dof_manager.get_node_dofs(node_id)[4]]
        for node_id in upper_nodes
    )
    assert summary.minimum_gap == pytest.approx(-1.0e-4)
    assert summary.integration_force[2] == pytest.approx(100.0)
    assert upper_couple_y == pytest.approx(100.0 * 0.025 * director[0])
    np.testing.assert_allclose(
        np.asarray(summary.integration_moment) + np.asarray(summary.target_moment),
        0.0, atol=1e-10,
    )


def test_guided_pair_rejects_nonuniform_or_lateral_motion_and_restart():
    model, load, definition, upper_nodes = _guided_pair()
    manager = _PlanarQ4PairManager(model, definition)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    displacement[model.mesh.dof_manager.get_node_dofs(upper_nodes[0])[2]] = -1.0e-5
    with pytest.raises(ValueError, match="uniform normal translation"):
        manager.evaluate(displacement)
    displacement[:] = 0.0
    displacement[model.mesh.dof_manager.get_node_dofs(upper_nodes[0])[0]] = 1.0e-5
    with pytest.raises(ValueError, match="uniform normal translation"):
        manager.evaluate(displacement)
    displacement[:] = 0.0
    displacement[model.mesh.dof_manager.get_node_dofs(upper_nodes[0])[3]] = 1.0e-5
    with pytest.raises(ValueError, match="fixed shell rotations"):
        manager.evaluate(displacement)
    with pytest.raises(ValueError, match="guided shell-pair contact restart"):
        solve_static_nonlinear(model, load, contact=definition,
                               emit_restart_checkpoint=True)
    split_model, _split_load, split_definition, _split_upper = _guided_pair(
        split_target=True
    )
    with pytest.raises(MemoryError, match="candidate limit"):
        _PlanarQ4PairManager(
            split_model, split_definition,
            ContactSolverSettings(maximum_candidate_pairs=1),
        )
