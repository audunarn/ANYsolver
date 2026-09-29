"""Two Q4s, two native physical B2 members, and two F10 point joints."""

import numpy as np
import pytest
from dataclasses import replace
from types import SimpleNamespace
from scipy import sparse
from scipy.linalg import null_space
from anysolver import stiffened_shell

from anysolver._b2_f10_f11_point_attachment import compile_reference_point
from anysolver._b2_physical_flexibility_linear import LinearSection
from anysolver._b2_physical_linear_definition import PhysicalB2Member
from anysolver.control import CancellationToken
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


@pytest.mark.parametrize("count", (1, 10, 100))
def test_point_panel_batch_reuses_factorization_and_selects_recovery(count):
    nodes, shells, members, points, free = _panel()
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PanelDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            nodes, shells, members, points,
            sparse.eye(54, format="csr")[:, free], np.zeros(54)))
    selected = (6*8+1, 6*5+2)
    cases = []
    for index in range(count):
        load = np.zeros(54)
        load[6*8+1] = .08*(1.+index/count)
        load[6*5+2] = -.16*(1.+index/count)
        cases.append((f"load-{index:03d}", load))
    result = analysis.solve_linear_many(
        cases, selected_dofs=selected, selected_points=("joint-right",),
        recover_members={"beam-right": (.25, .75)})
    assert result.status == "completed"
    assert len(result.cases) == count
    assert tuple(case.case_id for case in result.cases) == tuple(
        name for name, _ in cases)
    assert result.factorization_count == 1
    assert result.solve_count == count
    assert result.maximum_rhs_chunk == 1
    assert result.selected_points == ("joint-right",)
    assert all(len(case.selected_displacements) == 2 and
               len(case.selected_affine_reactions) == 2 and
               len(case.beam_resultants_local) == 1 and
               case.beam_resultants_local[0][0] == "beam-right" and
               len(case.beam_resultants_local[0][1]) == 2
               for case in result.cases)
    single = analysis.solve_linear(
        cases[-1][1], recover_members={"beam-right": (.25, .75)})
    assert single.status == "completed"
    np.testing.assert_allclose(
        result.cases[-1].selected_displacements,
        np.asarray(single.displacements)[list(selected)], rtol=0., atol=0.)
    np.testing.assert_allclose(
        result.cases[-1].selected_affine_reactions,
        np.asarray(single.affine_reactions)[list(selected)], rtol=0., atol=0.)
    assert result.cases[-1].point_multipliers == single.point_multipliers[1:]
    assert result.cases[-1].point_gaps == single.point_gaps[1:]
    assert result.cases[-1].internal_strain_energy == single.internal_strain_energy
    assert analysis._handle.factorization_count == 1
    analysis.close()


def test_point_panel_batch_cancellation_keeps_complete_prefix():
    nodes, shells, members, points, free = _panel()
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PanelDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            nodes, shells, members, points,
            sparse.eye(54, format="csr")[:, free], np.zeros(54)))
    token = CancellationToken()
    load = np.zeros(54)
    load[6*8+1] = .08
    names = []

    def after_case(case_id):
        names.append(case_id)
        if len(names) == 3:
            token.cancel("bounded panel prefix")

    result = analysis.solve_linear_many(
        tuple((f"case-{index}", load) for index in range(10)),
        selected_dofs=(6*8+1,), cancellation_token=token,
        on_case=after_case)
    assert result.status == "cancelled"
    assert names == ["case-0", "case-1", "case-2"]
    assert tuple(case.case_id for case in result.cases) == tuple(names)
    assert result.factorization_count == 1
    assert result.solve_count == 3
    assert all(case.internal_strain_energy > 0. for case in result.cases)
    assert all(not case.point_multipliers and not case.point_gaps
               for case in result.cases)
    with pytest.raises(ValueError, match="selected physical B2 member"):
        analysis.solve_linear_many(
            (("bad", load),), selected_dofs=(0,),
            recover_members={"missing": (.5,)})
    assert analysis._handle.solve_count == 3
    analysis.close()


def test_point_panel_batch_rejects_mutated_load_and_preserves_failed_prefix():
    nodes, shells, members, points, free = _panel()
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PanelDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            nodes, shells, members, points,
            sparse.eye(54, format="csr")[:, free], np.zeros(54)))
    first = np.zeros(54)
    first[6*8+1] = .08
    second = first.copy()
    cases = (("first", first), ("second", second))

    def mutate_next(_case_id):
        second[6*8+1] = .16

    with pytest.raises(ValueError, match="changed after submission"):
        analysis.solve_linear_many(
            cases, selected_dofs=(6*8+1,), on_case=mutate_next)
    assert analysis._handle.factorization_count == 1
    assert analysis._handle.solve_count == 1

    original = analysis._handle

    class FailSecond:
        @property
        def factorization_count(self):
            return original.factorization_count

        @property
        def solve_count(self):
            return original.solve_count

        def solve(self, rhs):
            if original.solve_count == 2:
                raise RuntimeError("injected backend failure")
            return original.solve(rhs)

    analysis._handle = FailSecond()
    failed = analysis.solve_linear_many(
        (("accepted", first), ("broken", first), ("later", first)),
        selected_dofs=(6*8+1,))
    assert failed.status == "failed"
    assert tuple(item.case_id for item in failed.cases) == ("accepted",)
    assert failed.failure_reason == "broken: injected backend failure"
    assert failed.factorization_count == 1
    assert failed.solve_count == 2
    analysis.close()


@pytest.mark.parametrize("tip_dof", (1, 3))
def test_small_load_requires_relative_equilibrium_not_unit_floor(tip_dof):
    nodes, shells, members, points, free = _panel()
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PanelDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            nodes, shells, members, points,
            sparse.eye(54, format="csr")[:, free], np.zeros(54)))
    load = np.zeros(54)
    load[6*8+tip_dof] = 1e-12
    reference = analysis.solve_linear(load*1e12)
    small = analysis.solve_linear(load)
    assert reference.status == small.status == "completed"
    np.testing.assert_allclose(small.displacements,
                               np.asarray(reference.displacements)*1e-12,
                               rtol=1e-8, atol=1e-24)

    # A backend returning zero for this small nonzero RHS used to pass the
    # former absolute 1 N residual floor and claim a completed solution.
    factor = analysis._handle
    analysis._handle = SimpleNamespace(
        solve=lambda rhs: np.zeros_like(rhs),
        factorization_count=factor.factorization_count,
        solve_count=factor.solve_count)
    failed = analysis.solve_linear(load)
    assert failed.status == "failed"
    assert "equilibrium" in failed.failure_reason
    analysis.close()


def test_mixed_force_scales_report_insufficient_resolution():
    nodes, shells, members, points, free = _panel()
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PanelDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            nodes, shells, members, points,
            sparse.eye(54, format="csr")[:, free], np.zeros(54)))
    load = np.zeros(54)
    load[6*2+2] = 1000.
    load[6*8+1] = 1e-12
    result = analysis.solve_linear(load)
    assert result.status == "failed"
    assert result.failure_reason == "panel mixed-load resolution insufficient"
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
