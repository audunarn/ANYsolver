"""Preparatory physical B2 graph covariance checks, not F09 acceptance."""

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu

from anysolver._b2_physical_flexibility_linear import LinearSection
from anysolver._b2_physical_linear_definition import PhysicalB2Member


def _members(rotation=np.eye(3), origin=np.zeros(3)):
    section = np.diag([22., 13., 17., 9., 7., 11.])
    section[0, 4] = section[4, 0] = 1.5
    section[1, 5] = section[5, 1] = -.7
    law = LinearSection.generalized(section)
    points = np.array([[0., 0., 0.], [2., 0., 0.], [2., 1.5, 0.]])
    points = points @ rotation.T + origin
    axes = np.array([[0., 1., 0.], [-1., 0., 0.]]) @ rotation.T
    return tuple(PhysicalB2Member(
        f"member-{i}", f"source-{i}", (i, i + 1),
        (points[i], points[i + 1]), axes[i], "generalized-A", law,
    ) for i in range(2)), points


def _solve(members, load):
    rows, cols, values = [], [], []
    for beam in members:
        transform = beam.local_dof_map()
        stiffness = transform.T @ beam.local_operator().evaluate(np.zeros(12)).tangent @ transform
        dofs = np.r_[np.arange(6 * beam.node_ids[0], 6 * beam.node_ids[0] + 6),
                     np.arange(6 * beam.node_ids[1], 6 * beam.node_ids[1] + 6)]
        for i, row in enumerate(dofs):
            for j, col in enumerate(dofs):
                rows.append(int(row))
                cols.append(int(col))
                values.append(stiffness[i, j])
    assembled = sparse.coo_matrix((values, (rows, cols)), shape=(18, 18)).tocsc()
    free = np.arange(6, 18)
    displacement = np.zeros(18)
    displacement[free] = splu(assembled[free, :][:, free]).solve(load[free])
    reaction = assembled @ displacement - load
    return displacement, reaction, assembled


def test_oriented_two_member_graph_covariance_work_and_balance():
    members, points = _members()
    load = np.zeros(18)
    load[12:18] = [0.4, -0.9, 0.7, -0.2, 0.3, 0.1]
    displacement, reaction, stiffness = _solve(members, load)
    assert np.linalg.norm(reaction[6:]) < 1e-13
    np.testing.assert_allclose(reaction[:3], -load[12:15], rtol=0, atol=1e-13)
    np.testing.assert_allclose(
        reaction[3:6] + load[15:18] + np.cross(points[2] - points[0], load[12:15]),
        0, rtol=0, atol=1e-13,
    )
    energy = .5 * displacement @ (stiffness @ displacement)
    assert energy == pytest.approx(.5 * displacement @ load, rel=2e-14)
    assert energy > 0

    # Rigid rotation and translation of the reference graph must transform
    # both forces and moments without changing the elastic work.
    exact_axes = np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]])
    axis = np.array([1., 2., 3.]) / np.sqrt(14.)
    cross = np.array([[0., -axis[2], axis[1]],
                      [axis[2], 0., -axis[0]],
                      [-axis[1], axis[0], 0.]])
    oblique = np.eye(3) + np.sin(.37) * cross + (1. - np.cos(.37)) * cross @ cross
    for rotation in (exact_axes, oblique):
        moved, _ = _members(rotation, np.array([4., -2., 3.]))
        block = np.kron(np.eye(6), rotation)
        moved_displacement, moved_reaction, moved_stiffness = _solve(moved, block @ load)
        np.testing.assert_allclose(moved_displacement, block @ displacement,
                                   rtol=2e-13, atol=2e-13)
        np.testing.assert_allclose(moved_reaction, block @ reaction,
                                   rtol=2e-13, atol=2e-13)
        np.testing.assert_allclose(moved_stiffness.toarray(),
                                   block @ stiffness.toarray() @ block.T,
                                   rtol=2e-13, atol=2e-13)
        assert .5 * moved_displacement @ (moved_stiffness @ moved_displacement) == pytest.approx(
            energy, rel=2e-13)
