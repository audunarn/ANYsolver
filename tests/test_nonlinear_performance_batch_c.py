from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from anysolver.boundary import BoundaryCondition, LoadCase
from anysolver.elements import Element
from anysolver.fe_core import FEModel
from anysolver.jit_compiler import JIT_DISABLED_REASON, JIT_ENABLED
from anysolver.mesh_gen import generate_simple_panel_mesh
from anysolver.nonlinear_performance_batch_c import (
    assemble_reduced_system,
    batch_c_status,
    build_reduced_assembly_plan,
    reset_batch_c_counters,
)
from anysolver.nonlinear_performance_bootstrap import get_nonlinear_assembly_plan
from anysolver.nonlinear_static import solve_static_nonlinear


def _weighted_transformation(total_dofs: int) -> sparse.csr_matrix:
    reduced_dofs = total_dofs - 2
    rows = list(range(reduced_dofs))
    columns = list(range(reduced_dofs))
    values = [1.0] * reduced_dofs
    rows.extend((reduced_dofs, reduced_dofs))
    columns.extend((0, 1))
    values.extend((0.75, 0.25))
    return sparse.csr_matrix(
        (values, (rows, columns)),
        shape=(total_dofs, reduced_dofs),
    )


def _selector_transformation(total_dofs: int) -> sparse.csr_matrix:
    reduced_dofs = total_dofs - 2
    active = np.arange(reduced_dofs, dtype=np.intp)
    return sparse.csr_matrix(
        (np.ones(reduced_dofs), (active, active)),
        shape=(total_dofs, reduced_dofs),
    )


def test_direct_reduced_scatter_matches_full_projection_with_mpc_coefficients() -> None:
    model = generate_simple_panel_mesh(
        1.2,
        0.8,
        0.01,
        num_divisions_x=2,
        num_divisions_y=2,
    )
    nonlinear_plan = get_nonlinear_assembly_plan(model, 5)
    transformation = _weighted_transformation(nonlinear_plan.total_dofs)
    reduced_plan = build_reduced_assembly_plan(nonlinear_plan, transformation)
    assert reduced_plan.mapping_kind == "weighted_mpc"
    assert reduced_plan.force_weighted_sources.size > 0
    assert reduced_plan.tangent_weighted_sources.size > 0

    rng = np.random.default_rng(20260618)
    q = rng.normal(scale=1.0e-5, size=transformation.shape[1])
    displacement = np.asarray(transformation @ q, dtype=float).reshape(-1)

    force_full, tangent_full, states_full = nonlinear_plan.assemble(
        displacement,
        {},
        tangent=True,
    )
    force_reduced, tangent_reduced, states_reduced = assemble_reduced_system(
        nonlinear_plan,
        reduced_plan,
        displacement,
        {},
        tangent=True,
    )

    np.testing.assert_allclose(
        force_reduced,
        np.asarray(transformation.T @ force_full, dtype=float).reshape(-1),
        rtol=2.0e-11,
        atol=1.0e-8,
    )
    np.testing.assert_allclose(
        tangent_reduced.toarray(),
        (transformation.T @ tangent_full @ transformation).toarray(),
        rtol=2.0e-11,
        atol=1.0e-5,
    )
    assert set(states_reduced) == set(states_full)


def test_selector_reduced_plan_reuses_csr_and_work_buffers() -> None:
    model = generate_simple_panel_mesh(
        1.0,
        0.6,
        0.01,
        num_divisions_x=2,
        num_divisions_y=1,
    )
    nonlinear_plan = get_nonlinear_assembly_plan(model, 5)
    transformation = _selector_transformation(nonlinear_plan.total_dofs)
    reduced_plan = build_reduced_assembly_plan(nonlinear_plan, transformation)
    assert reduced_plan.mapping_kind == "selector"
    assert reduced_plan.force_weighted_sources.size == 0
    assert reduced_plan.tangent_weighted_sources.size == 0

    identities = (
        id(reduced_plan.force_buffer),
        id(reduced_plan.tangent_buffer),
        id(reduced_plan.tangent_matrix),
        id(reduced_plan.tangent_matrix.data),
    )
    displacement = np.zeros(nonlinear_plan.total_dofs, dtype=float)
    first_force, first_tangent, _ = assemble_reduced_system(
        nonlinear_plan,
        reduced_plan,
        displacement,
        {},
        tangent=True,
    )
    first_force_copy = first_force.copy()
    first_tangent_copy = first_tangent.copy()
    second_force, second_tangent, _ = assemble_reduced_system(
        nonlinear_plan,
        reduced_plan,
        displacement,
        {},
        tangent=True,
    )

    assert identities == (
        id(reduced_plan.force_buffer),
        id(reduced_plan.tangent_buffer),
        id(reduced_plan.tangent_matrix),
        id(reduced_plan.tangent_matrix.data),
    )
    assert second_force is reduced_plan.force_buffer
    assert second_tangent is reduced_plan.tangent_matrix
    np.testing.assert_allclose(second_force, first_force_copy)
    np.testing.assert_allclose(
        second_tangent.toarray(),
        first_tangent_copy.toarray(),
    )
    for row in range(reduced_plan.reduced_dofs):
        start = int(reduced_plan.csr_indptr[row])
        stop = int(reduced_plan.csr_indptr[row + 1])
        row_indices = reduced_plan.csr_indices[start:stop]
        assert np.all(row_indices[:-1] < row_indices[1:])


@pytest.mark.skipif(
    not JIT_ENABLED,
    reason=f"Batch C requires Batch B's Numba kernel ({JIT_DISABLED_REASON})",
)
def test_direct_reduced_assembly_retains_batch_b_elastic_kernel(monkeypatch) -> None:
    model = generate_simple_panel_mesh(
        1.0,
        0.6,
        0.01,
        num_divisions_x=2,
        num_divisions_y=1,
    )
    nonlinear_plan = get_nonlinear_assembly_plan(model, 5)
    assert nonlinear_plan.shell_batches
    assert all(
        getattr(batch, "_batch_b_elastic", False)
        for batch in nonlinear_plan.shell_batches
    )
    transformation = _selector_transformation(nonlinear_plan.total_dofs)
    reduced_plan = build_reduced_assembly_plan(nonlinear_plan, transformation)

    def fail_allocating_batch_path(*_args, **_kwargs):
        raise AssertionError("Batch C bypassed the Batch B in-place shell kernel")

    for batch in nonlinear_plan.shell_batches:
        monkeypatch.setattr(batch, "evaluate", fail_allocating_batch_path)

    force, tangent, states = assemble_reduced_system(
        nonlinear_plan,
        reduced_plan,
        np.zeros(nonlinear_plan.total_dofs, dtype=float),
        {},
        tangent=True,
    )
    assert force.shape == (reduced_plan.reduced_dofs,)
    assert tangent.shape == (
        reduced_plan.reduced_dofs,
        reduced_plan.reduced_dofs,
    )
    assert len(states) == model.mesh.num_elements
    assert batch_c_status()["batch_b_local_kernel_retained"] is True


class _LinearSpringElement(Element):
    def __init__(self, element_id: int, node_id: int, stiffness: float = 2.0):
        super().__init__(element_id, [node_id], "default")
        self.stiffness = float(stiffness)

    @property
    def num_nodes(self) -> int:
        return 1

    @property
    def dofs_per_node(self) -> int:
        return 6

    def get_node_coordinates(self, mesh):
        return np.asarray([mesh.get_node(self.node_ids[0]).coords()], dtype=float)

    def compute_stiffness_matrix(self, mesh, material):
        matrix = np.eye(6, dtype=float)
        matrix[0, 0] = self.stiffness
        return matrix

    def compute_nonlinear_response(
        self,
        mesh,
        material,
        u_elem,
        state=None,
        num_layers: int = 5,
        tangent: bool = True,
    ):
        displacement = np.asarray(u_elem, dtype=float)
        force = displacement.copy()
        force[0] = self.stiffness * displacement[0]
        stiffness = None
        if tangent:
            stiffness = np.eye(6, dtype=float)
            stiffness[0, 0] = self.stiffness
        return force, stiffness, {
            "spring_displacement": float(displacement[0]),
        }


def _spring_model():
    model = FEModel("batch_c_linear_spring")
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_element(1, _LinearSpringElement(1, 1))
    model.add_boundary_condition(
        BoundaryCondition(
            "one_dof",
            [1],
            {
                "uy": 0.0,
                "uz": 0.0,
                "rx": 0.0,
                "ry": 0.0,
                "rz": 0.0,
            },
        )
    )
    load = LoadCase("reference")
    load.add_nodal_load(
        1,
        load_vector=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )
    return model, load


@pytest.mark.skipif(
    not JIT_ENABLED,
    reason=f"Batch C installation requires Numba ({JIT_DISABLED_REASON})",
)
def test_nonlinear_solver_uses_direct_reduced_assembly() -> None:
    reset_batch_c_counters()
    model, load = _spring_model()
    result = solve_static_nonlinear(
        model,
        load_case=load,
        max_load_factor=0.25,
        num_steps=2,
        max_iterations=8,
        tolerance=1.0e-10,
    )
    status = batch_c_status()
    assert result.status == "completed"
    assert status["installed"] is True
    assert status["contexts_entered"] >= 1
    assert status["reduced_plan_builds"] == 1
    assert status["reduced_assemblies"] > 0
    assert status["full_coordinate_fallbacks"] == 0
    assert status["last_plan"]["mapping_kind"] == "selector"
