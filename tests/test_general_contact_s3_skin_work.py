"""Formulation-owned S3 physical-skin contact work mapping."""

import numpy as np
import pytest
from scipy import sparse

from anysolver import create_shell_element
from anysolver.fe_core import FEModel
from anysolver.general_contact.overlap import current_planar_shell_face
from anysolver.general_contact.s3_skin_work import S3SkinWorkAdapter
from anysolver.general_contact.triangle_pair_energy import MovingS3PairPenalty


def _model():
    model = FEModel("s3_moving_skin_work")
    model.add_material("elastic", 1e5, 0.3, density=1.0)
    source = ((0.4, 0.2, 0.065), (0.9, 0.2, 0.065),
              (0.4, 0.7, 0.065))
    target = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
              (0.0, 1.0, 0.0))
    for node, position in enumerate((*source, *target), 1):
        model.add_node(node, *position)
    for element_id, nodes in ((1, (1, 2, 3)), (2, (4, 5, 6))):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0, 0, 1),
            reference_surface_offset=0.01,
        ))
    return model


def test_s3_skin_uses_formulation_offset_and_director_without_drill_work():
    model = _model()
    adapters = {
        side: S3SkinWorkAdapter.from_model(model, 1, 1, side)
        for side in ("bottom", "midsurface", "top")
    }
    for side, offset in (("bottom", -0.035),
                         ("midsurface", -0.01), ("top", 0.015)):
        adapter = adapters[side]
        assert adapter.physical_offset == pytest.approx(offset)
        np.testing.assert_allclose(adapter.reference_positions[:, 2],
                                   0.065 + offset, atol=1e-15)
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    dofs = model.mesh.dof_manager.get_node_dofs(1)
    u[dofs[:3]] = (0.01, -0.02, -0.005)
    u[dofs[3:6]] = (0.002, -0.003, 0.004)
    bottom = adapters["bottom"]
    mapped = bottom.current_positions(u)
    separate = current_planar_shell_face(model, 1, 1, "bottom", u)
    np.testing.assert_allclose(mapped, separate.corners, atol=1e-15)
    drill = np.zeros_like(u)
    drill[dofs[5]] = 1.0
    np.testing.assert_allclose(bottom.work_map @ drill, 0.0, atol=0.0)
    np.testing.assert_allclose(bottom.current_positions(u + 0.1*drill),
                               mapped, atol=0.0)
    with pytest.raises(ValueError, match="not the admitted S3"):
        S3SkinWorkAdapter.from_model(model, 3, 99, "top")


def test_s3_pair_physical_work_pullback_and_tangent_use_authoritative_dofs():
    model = _model()
    source = S3SkinWorkAdapter.from_model(model, 1, 1, "bottom")
    target = S3SkinWorkAdapter.from_model(model, 2, 2, "top")
    law = MovingS3PairPenalty(
        source.reference_positions, target.reference_positions,
        1000.0, difference_step=2e-5,
    )
    mapping = sparse.vstack((source.work_map, target.work_map)).tocsr()
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    for node in (1, 2, 3):
        u[model.mesh.dof_manager.get_node_dofs(node)[2]] = -0.025
    u[model.mesh.dof_manager.get_node_dofs(2)[0]] = 0.01
    u[model.mesh.dof_manager.get_node_dofs(3)[1]] = -0.015

    def state_at(displacement, *, tangent):
        first = source.current_positions(displacement)
        second = target.current_positions(displacement)
        return law.work(first, second, tangent=tangent)

    physical = state_at(u, tangent=True)
    residual = np.asarray(mapping.T @ physical.residual).reshape(-1)
    stiffness = (mapping.T @ sparse.csr_matrix(physical.tangent)
                 @ mapping).tocsr()
    source_part, _ = source.pullback(physical.residual[:9])
    target_part, _ = target.pullback(physical.residual[9:])
    np.testing.assert_allclose(source_part + target_part, residual, atol=1e-14)
    assert abs(residual[model.mesh.dof_manager.get_node_dofs(2)[3]]) > 1e-5
    direction = np.zeros_like(u)
    direction[model.mesh.dof_manager.get_node_dofs(1)[1]] = 0.13
    direction[model.mesh.dof_manager.get_node_dofs(2)[0]] = -0.21
    direction[model.mesh.dof_manager.get_node_dofs(2)[3]] = 0.08
    direction[model.mesh.dof_manager.get_node_dofs(5)[2]] = -0.17
    step = 3e-5
    plus, minus = u + step*direction, u - step*direction
    plus_state = state_at(plus, tangent=False)
    minus_state = state_at(minus, tangent=False)
    measured_work = ((plus_state.energy.energy - minus_state.energy.energy)
                     / (2*step))
    assert measured_work == pytest.approx(float(residual @ direction),
                                          rel=1e-5, abs=1e-7)
    measured_tangent = np.asarray(mapping.T @ (
        (plus_state.residual - minus_state.residual) / (2*step)
    )).reshape(-1)
    relative_error = float(np.linalg.norm(
        measured_tangent - stiffness @ direction
    ) / np.linalg.norm(measured_tangent))
    assert relative_error <= 1e-5
    drill = np.zeros_like(u)
    drill[model.mesh.dof_manager.get_node_dofs(1)[5]] = 1.0
    np.testing.assert_allclose(mapping @ drill, 0.0, atol=0.0)
    assert float(residual @ drill) == 0.0
