"""Two Q4s, two native physical B2 members, and two F10 point joints."""

import numpy as np
import pytest
from dataclasses import replace
from scipy import sparse
from scipy.linalg import null_space
from anysolver import stiffened_shell

from anysolver._b2_f10_f11_point_attachment import compile_reference_point
from anysolver._b2_physical_flexibility_linear import LinearSection
from anysolver._b2_physical_linear_definition import PhysicalB2Member
from anysolver._stiffened_shell_b2_q4_panel_experimental import (
    Q4B2Point, Q4PanelShell, _require_independent_supported_point_rows,
)
from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.fe_core import FEModel
from anysolver.linalg import MatrixClass, factorize_cached


def _panel():
    nodes = {
        1: (0., 0., 0.), 2: (1., 0., 0.), 3: (2., 0., 0.),
        4: (0., 1., 0.), 5: (1., 1., 0.), 6: (2., 1., 0.),
    }
    shells = (
        Q4PanelShell("left", (1, 2, 5, 4), 1000., .3, .15),
        Q4PanelShell("right", (2, 3, 6, 5), 1000., .3, .15),
    )
    section = LinearSection.isotropic(
        E=2000., nu=.25, area=.04, Iy=.00015, Iz=.0003,
        J=.0004, ky=.8, kz=.7)
    members = (
        PhysicalB2Member("beam-left", "beam-source-left", (10, 11),
                         ((.2, .5, .2), (1.2, .5, .2)),
                         (0., 1., 0.), "beam-section", section),
        PhysicalB2Member("beam-right", "beam-source-right", (11, 12),
                         ((1.2, .5, .2), (2.2, .5, .2)),
                         (0., 1., 0.), "beam-section", section),
    )
    points = (
        Q4B2Point("joint-left", "left", "beam-left", .5,
                  (0., .08, -.03)),
        Q4B2Point("joint-right", "right", "beam-right", .5,
                  (0., .08, -.03)),
    )
    shell_ids = tuple(sorted(nodes))
    beam_ids = (10, 11, 12)
    shell_index = {node_id: i for i, node_id in enumerate(shell_ids)}
    beam_index = {node_id: i+len(shell_ids)
                  for i, node_id in enumerate(beam_ids)}
    fixed = set()
    for node_id in (1, 4):
        fixed.update(6*shell_index[node_id]+j for j in range(6))
    fixed.update(6*beam_index[10]+j for j in range(6))
    for node_id in (2, 3, 5, 6):
        fixed.add(6*shell_index[node_id]+5)
    free = np.array([i for i in range(54) if i not in fixed])
    return nodes, shells, members, points, free


def _independent_dense(nodes, shells, members, points):
    """Assemble from local operators without calling the panel owner."""
    model = FEModel("independent-panel")
    for node_id, position in nodes.items():
        model.add_node(node_id, *position)
    shell_index = {node_id: i for i, node_id in enumerate(sorted(nodes))}
    beam_index = {node_id: i+len(nodes)
                  for i, node_id in enumerate((10, 11, 12))}
    stiffness = np.zeros((54, 54))
    constraint = np.zeros((12, 54))
    for index, shell in enumerate(shells, 1):
        material = f"oracle-{index}"
        model.add_material(material, shell.E, shell.nu)
        element = QualifiedE4PLShellElement(
            index, shell.node_ids, material, thickness=shell.thickness_m,
            reference_normal=np.array(shell.reference_normal))
        model.add_element(index, element)
        local = element.compute_stiffness_matrix(
            model.mesh, model.get_material(material))
        slots = np.array([6*shell_index[node_id]+j
                          for node_id in shell.node_ids for j in range(6)])
        stiffness[np.ix_(slots, slots)] += local
    for member in members:
        frame = member.local_dof_map()
        local = frame.T @ member.local_operator().evaluate(
            np.zeros(12)).tangent @ frame
        slots = np.array([6*beam_index[node_id]+j
                          for node_id in member.node_ids for j in range(6)])
        stiffness[np.ix_(slots, slots)] += local
    shell_by_id = {shell.shell_id: shell for shell in shells}
    member_by_id = {member.member_id: member for member in members}
    for index, point in enumerate(points):
        shell = shell_by_id[point.shell_id]
        member = member_by_id[point.member_id]
        vertices = np.array([nodes[node_id] for node_id in shell.node_ids])
        law = compile_reference_point(
            member, vertices, station=point.station,
            offset_local_m=point.offset_local_m)
        slots = np.array(
            [6*shell_index[node_id]+j for node_id in shell.node_ids
             for j in range(6)] +
            [6*beam_index[node_id]+j for node_id in member.node_ids
             for j in range(6)])
        constraint[6*index:6*index+6, slots] += law.constraint
    return stiffness, constraint


def test_supported_point_row_audit_bounds_dense_work(monkeypatch):
    small = sparse.csr_matrix(((1., 2.), (0, 0), (0, 2)), shape=(1, 3))
    _require_independent_supported_point_rows(small)
    with pytest.raises(ValueError, match="independent supported point rows"):
        _require_independent_supported_point_rows(
            sparse.csr_matrix(((1., 2.), ([0, 1], [0, 0])), shape=(2, 2)))

    def forbid_dense(_self, *args, **kwargs):
        raise AssertionError("large supported-row audit materialized a dense matrix")

    monkeypatch.setattr(sparse.csr_matrix, "toarray", forbid_dense)
    monkeypatch.setattr(sparse.csc_matrix, "toarray", forbid_dense)
    large = sparse.eye(96, 192, format="csc")
    _require_independent_supported_point_rows(large)
    dependent = large.tolil()
    dependent[1, :] = 0.
    dependent[1, 0] = 2.
    with pytest.raises(ValueError, match="structurally independent"):
        _require_independent_supported_point_rows(dependent.tocsc())

    # Structural rank alone cannot detect proportional rows with two distinct
    # columns; the production sparse KKT factorization must reject them.
    proportional = sparse.eye(60, 61, format="lil")
    proportional[0, 1] = 1.
    proportional[1, :] = 0.
    proportional[1, 0] = 2.
    proportional[1, 1] = 2.
    proportional = proportional.tocsc()
    _require_independent_supported_point_rows(proportional)
    kkt = sparse.bmat(((sparse.eye(61, format="csc"), proportional.T),
                       (proportional, None)), format="csc")
    factor = factorize_cached(kkt, MatrixClass.SYMMETRIC_INDEFINITE)
    assert factor.status == "failed"


def test_multi_q4_multi_b2_panel_matches_bounded_dense_oracle():
    nodes, shells, members, points, free = _panel()
    T = sparse.eye(54, format="csr")[:, free]
    u0 = np.zeros(54)
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PanelDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            nodes, shells, members, points, T, u0))
    assert analysis.shell_node_ids == (1, 2, 3, 4, 5, 6)
    assert analysis.beam_node_ids == (10, 11, 12)
    assert analysis.capabilities.status == "experimental"
    T.data[:] = 0.
    u0[:] = 1.
    stiffness, constraint = _independent_dense(nodes, shells, members, points)
    c = constraint[:, free]
    z = null_space(c)
    reduced_k = stiffness[np.ix_(free, free)]
    for scale in (1., 1.7):
        load = np.zeros(54)
        load[6*2+2] = -.12*scale
        load[6*5+2] = -.16*scale
        load[6*8+1] = .08*scale
        result = analysis.solve_linear(load)
        assert result.status == "completed", result.failure_reason
        assert result.factorization_count == 1
        u = np.asarray(result.displacements)
        lam = np.concatenate([row for _, row in result.point_multipliers])
        expected = z @ np.linalg.solve(z.T @ reduced_k @ z,
                                        z.T @ load[free])
        expected_lam = np.linalg.lstsq(
            c.T, load[free]-reduced_k @ expected, rcond=None)[0]
        np.testing.assert_allclose(u[free], expected, rtol=2e-9, atol=2e-10)
        np.testing.assert_allclose(lam, expected_lam, rtol=2e-9, atol=2e-10)
        np.testing.assert_allclose(constraint @ u, 0., atol=1e-10)
        reaction = np.asarray(result.affine_reactions)
        np.testing.assert_allclose(reaction[free], 0., atol=1e-9)
        assert np.linalg.norm(reaction) > 0.
        assert abs(u @ load - 2*result.internal_strain_energy) < 1e-9
        assert len(result.beam_resultants_local) == 2
        assert len(result.point_gaps) == 2
    analysis.close()


def test_disconnected_supported_panels_fail_topology_preflight():
    nodes, shells, members, points, _ = _panel()
    separated_nodes = {node_id: nodes[node_id] for node_id in (1, 2, 4, 5)}
    separated_nodes.update({
        7: (4., 0., 0.), 8: (5., 0., 0.),
        9: (5., 1., 0.), 10: (4., 1., 0.),
    })
    separated_shells = (
        shells[0], replace(shells[1], shell_id="far", node_ids=(7, 8, 9, 10)))
    separated_members = (
        members[0], replace(members[1], node_ids=(20, 21),
                            reference_points_m=((4.2, .5, .2),
                                                (5.2, .5, .2))))
    separated_points = (
        points[0], replace(points[1], shell_id="far"))
    with pytest.raises(ValueError, match="connected shell/beam point panel"):
        stiffened_shell.create_analysis(definition=
            stiffened_shell.B2Q4PanelDefinition(
                stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
                separated_nodes, separated_shells, separated_members,
                separated_points, sparse.eye(72, format="csr"),
                np.zeros(72)))
