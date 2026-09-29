"""Bounded independent dense scatter oracle for the sparse GE point owner."""

from dataclasses import replace

import numpy as np
import pytest

from anysolver._ge_beam3_generalized_static_boundary import spatial_jacobian
from anysolver._ge_beam3_pose_joint import RigidPoseJoint
from anysolver._stiffened_shell_ge_experimental import (
    ExperimentalGEAnalysis, NodalAction,
)
from anysolver.corotational import corotational_element_response

from test_stiffened_shell_ge_experimental import _panel


def _dense_reference(owner, definition):
    """Assemble local operators by a separate dense gather/scatter path."""
    count = owner._K.shape[0]
    shell_count = owner._shell_count
    residual = np.zeros(count)
    stiffness = np.zeros((count, count))

    for eid, element, _compiled_slots, origin in owner._shell_parts:
        slots = np.array([6*owner._shell_index[node]+axis
                          for node in element.node_ids for axis in range(6)])
        if len(element.node_ids) == 3:
            force, tangent, _ = element.compute_nonlinear_response(
                owner._shell_model.mesh,
                owner._shell_model.get_material("shell"),
                np.zeros(18), origin, 3, True)
        else:
            force, tangent, _ = corotational_element_response(
                owner._shell_model, eid, element, np.zeros(24), True,
                committed_state=origin, num_layers=3,
                tangent_mode="consistent")
        np.add.at(residual, slots, force)
        stiffness[np.ix_(slots, slots)] += tangent

    beam_nodal = 6*len(owner._beam_ids)
    for member, (element, _compiled_slots, origin) in enumerate(
            owner._beam_parts):
        slots = np.array(
            [shell_count+6*owner._beam_index[node]+axis
             for node in element.node_ids for axis in range(6)] +
            list(range(shell_count+beam_nodal+24*member,
                       shell_count+beam_nodal+24*(member+1))))
        positions = np.array([owner._beam_nodes[node][0]
                              for node in element.node_ids])
        frames = np.array([owner._beam_nodes[node][1]
                           for node in element.node_ids])
        response = element.operator.evaluate(
            positions, np.zeros((3, 3)), frames,
            np.tile(np.eye(3), (2, 1, 1)), np.zeros(18),
            origin=origin, check=element.operator.guard)
        tangent = spatial_jacobian(
            response.residual, response.hessian+response.hessian_low)
        np.add.at(residual, slots, response.residual)
        stiffness[np.ix_(slots, slots)] += tangent

    constraints = np.zeros((6*len(definition.points), count))
    for joint_index, tie in enumerate(definition.points):
        shell_node = owner._shell_index[tie.shell_node]
        beam_node = owner._beam_index[tie.beam_node]
        positions = np.array((owner._shell_xyz[shell_node],
                              owner._beam_nodes[tie.beam_node][0]))
        frames = np.array((np.eye(3),
                           owner._beam_nodes[tie.beam_node][1]))
        joint = RigidPoseJoint(positions, frames)
        evaluated = joint.evaluate(positions, frames, np.zeros(6))
        assert np.max(np.abs(evaluated.constraints)) <= 1e-10
        slots = np.r_[np.arange(6*shell_node, 6*shell_node+6),
                      np.arange(shell_count+6*beam_node,
                                shell_count+6*beam_node+6)]
        constraints[6*joint_index:6*joint_index+6, slots] = (
            evaluated.constraint_jacobian)
    return residual, stiffness, constraints


@pytest.mark.parametrize("q4,s3", [
    (((1, 2, 5, 4), (2, 3, 6, 5)), ()),
    (((1, 2, 5, 4),), ((2, 3, 6), (2, 6, 5))),
])
def test_dense_local_assembly_matches_sparse_owner(q4, s3):
    base = _panel()
    definition = replace(base, shell=replace(
        base.shell, q4_elements=q4, s3_elements=s3))
    owner = ExperimentalGEAnalysis(definition)
    residual, stiffness, constraints = _dense_reference(owner, definition)
    assert np.max(np.abs(residual)) < 1e-10
    sparse_stiffness = owner._K.toarray()
    # One mixed Q4/S3 entry nearly cancels under a different accumulation
    # order. Judge assembly against the registered relative matrix criterion,
    # while retaining the raw difference for failure diagnostics.
    stiffness_error = np.linalg.norm(stiffness-sparse_stiffness) / np.linalg.norm(
        sparse_stiffness)
    assert stiffness_error <= 1e-10, stiffness_error
    np.testing.assert_allclose(constraints, owner._C.toarray(),
                               rtol=1e-10, atol=1e-12)

    action = (NodalAction("beam", 105, (0., 0., 100., 0., 0., 0.)),)
    sparse_result = owner.solve_linear(action)
    load = owner._accepted[1]
    free = owner._free
    dense_system = np.block([
        [stiffness[np.ix_(free, free)], constraints[:, free].T],
        [constraints[:, free], np.zeros((len(constraints), len(constraints)))],
    ])
    dense_solution = np.linalg.solve(
        dense_system, np.r_[load[free], np.zeros(len(constraints))])
    sparse_coordinates = np.r_[sparse_result.shell_displacement,
                               sparse_result.beam_coordinates]
    coordinate_error = np.linalg.norm(
        sparse_coordinates[free]-dense_solution[:len(free)]) / np.linalg.norm(
            dense_solution[:len(free)])
    multiplier_error = np.linalg.norm(
        sparse_result.multipliers-dense_solution[len(free):]) / np.linalg.norm(
            dense_solution[len(free):])
    assert coordinate_error <= 1e-10, coordinate_error
    assert multiplier_error <= 1e-10, multiplier_error
    q = np.zeros(len(load))
    q[free] = dense_solution[:len(free)]
    reactions = stiffness@q+constraints.T@dense_solution[len(free):]-load
    reaction_error = (np.linalg.norm(
        sparse_result.reactions[owner._fixed]-reactions[owner._fixed]) /
        np.linalg.norm(reactions[owner._fixed]))
    assert reaction_error <= 1e-10, reaction_error
