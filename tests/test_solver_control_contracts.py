from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from anysolver import (
    CancellationToken,
    ConstraintEquation,
    ProgressEvent,
    SolveCancelled,
    audit_constraints,
    describe_result_quantities,
    solve_nonlinear_load_stepping,
)
from anysolver.assembly import (
    build_constraint_transformation,
    build_reduced_rigid_body_modes,
    reconstruct_full_solution,
)
from anysolver.boundary import BoundaryCondition, FixedSupport, LoadCase
from anysolver.elements import BeamElement
from anysolver.fe_core import FEModel
from anysolver.nonlinear_static import solve_static_nonlinear


def _elastic_cantilever() -> tuple[FEModel, LoadCase]:
    model = FEModel("solver-control-cantilever")
    model.add_material("steel", 210.0e9, 0.3)
    section = {
        "area": 0.01,
        "Iy": 1.0e-6,
        "Iz": 1.0e-6,
        "J": 1.0e-6,
        "orientation": (0.0, 0.0, 1.0),
    }
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    model.add_element(1, BeamElement(1, [1, 2], "steel", section))
    model.add_boundary_condition(FixedSupport("fixed", [1]))
    load = LoadCase("tip")
    load.add_nodal_load(2, [0.0, 0.0, 10.0, 0.0, 0.0, 0.0])
    return model, load


def test_force_control_ramps_nonzero_prescribed_displacement_by_increment() -> None:
    model, _load = _elastic_cantilever()
    target = 4.0e-3
    model.add_boundary_condition(
        BoundaryCondition("prescribed-tip-x", [2], {"ux": target})
    )
    progress = []
    result = solve_static_nonlinear(
        model,
        load_case=None,
        num_steps=4,
        record_increment_snapshots=True,
        progress_callback=progress.append,
    )

    assert result.converged
    assert len(result.snapshots) >= 2
    ux = model.mesh.nodes[2].dofs[0]
    imposed = [snapshot.displacements[ux] for snapshot in result.snapshots]
    factors = [snapshot.load_factor for snapshot in result.snapshots]
    assert imposed == pytest.approx([factor * target for factor in factors])
    assert imposed[0] < imposed[-1]
    assert result.displacements[ux] == pytest.approx(target)
    assert result.info["prescribed_displacement_path"]["mode"] == (
        "proportional_to_load_factor"
    )
    assert result.steps[-1].support_reactions["fixed"][0] == pytest.approx(
        -result.steps[-1].support_reactions["prescribed-tip-x"][0]
    )
    assert abs(result.steps[-1].support_reactions["fixed"][0]) > 0.0
    assert progress[-1]["support_reactions"]["fixed"][0] == pytest.approx(
        result.steps[-1].support_reactions["fixed"][0]
    )


def test_cancellation_token_is_one_way_and_reports_safe_point() -> None:
    token = CancellationToken()
    assert not token.is_cancelled
    assert token.cancel("operator request")
    assert not token.cancel("later reason")
    assert token.reason == "operator request"
    with pytest.raises(SolveCancelled, match="nonlinear_limit.start") as caught:
        solve_nonlinear_load_stepping(FEModel("cancelled"), cancellation_token=token)
    assert caught.value.reason == "operator request"
    assert caught.value.stage == "nonlinear_limit.start"


def test_progress_event_is_typed_and_legacy_mapping_compatible() -> None:
    event = ProgressEvent(
        "nonlinear_static_step",
        "nonlinear_static.force",
        completed=2,
        total=4,
        iteration=3,
        metadata={"load_factor": 0.5},
    )
    assert event.type == "nonlinear_static_step"
    assert event.fraction == pytest.approx(0.5)
    assert event["load_factor"] == pytest.approx(0.5)
    assert event.get("iteration") == 3
    assert dict(event)["stage"] == "nonlinear_static.force"


def test_general_constraint_equation_uses_common_affine_transformation() -> None:
    model = FEModel("general-equation")
    node = model.add_node(1, 0.0, 0.0, 0.0)
    ux, uy = node.dofs[:2]
    model.add_boundary_condition(BoundaryCondition("prescribed-y", [1], {"uy": 1.0}))
    equation = model.add_constraint_equation(
        terms=((ux, 1.0), (uy, 1.0)),
        rhs=3.0,
        source_id="local-x",
    )
    assert isinstance(equation, ConstraintEquation)

    report = audit_constraints(model)
    assert report.feasible
    assert report.origin_counts["equation"] == 1
    assert report.equations[-1].source_id == "equation:local-x"

    K = sparse.eye(6, format="csr")
    K_red, F_red, T, u0, _independent, info = build_constraint_transformation(
        K,
        np.zeros(6),
        model,
    )
    assert info["num_generalized_constraint_equations"] == 1
    q = np.zeros(K_red.shape[0], dtype=float)
    displacement = reconstruct_full_solution(T, q, u0)
    assert displacement[uy] == pytest.approx(1.0)
    assert displacement[ux] == pytest.approx(2.0)
    assert F_red.shape == (K_red.shape[0],)


def test_constraint_equation_retains_legacy_constructor_aliases() -> None:
    equation = ConstraintEquation(2, ((2, 1.0), (3, -0.5)), 4.0, "legacy", "mpc")
    assert equation.dependent_dof == 2
    assert equation.coefficients == equation.terms
    assert equation.value == equation.rhs == pytest.approx(4.0)
    assert equation.origin == equation.source_id == "legacy"


def test_independent_rotated_rows_are_sparse_row_reduced_without_cycle() -> None:
    model = FEModel("rotated-equations")
    node = model.add_node(1, 0.0, 0.0, 0.0)
    ux, uy = node.dofs[:2]
    c = float(np.sqrt(0.5))
    model.add_constraint_equation(
        terms=((ux, c), (uy, c)),
        rhs=1.0,
        source_id="local-x",
    )
    model.add_constraint_equation(
        terms=((uy, c), (ux, -c)),
        rhs=2.0,
        source_id="local-y",
    )

    report = audit_constraints(model)
    assert report.feasible
    assert report.max_dependency_depth == 2
    K_red, _F_red, T, u0, independent, _info = build_constraint_transformation(
        sparse.eye(6, format="csr"),
        np.zeros(6),
        model,
    )
    displacement = reconstruct_full_solution(T, np.zeros(K_red.shape[0]), u0)
    expected = np.linalg.solve(
        np.array([[c, c], [-c, c]], dtype=float),
        np.array([1.0, 2.0], dtype=float),
    )
    assert displacement[[ux, uy]] == pytest.approx(expected)
    rigid_modes, rigid_info = build_reduced_rigid_body_modes(
        model,
        independent,
        6,
        transformation=T,
    )
    assert rigid_modes.shape[1] == 4
    assert rigid_info["constraint_compatibility_method"] == "affine_transformation_intersection"


def test_nonlinear_increment_snapshots_are_opt_in_and_committed() -> None:
    model, load = _elastic_cantilever()

    progress = []
    status = []
    result = solve_static_nonlinear(
        model,
        load,
        num_steps=2,
        record_increment_snapshots=True,
        progress_callback=progress.append,
        status_callback=status.append,
    )

    assert result.status == "completed"
    assert len(result.snapshots) == len(result.steps) == 2
    assert np.array_equal(result.snapshots[-1].displacements, result.displacements)
    assert not result.snapshots[-1].displacements.flags.writeable
    assert result.snapshots[-1].element_states is not result.element_states
    assert all(isinstance(event, ProgressEvent) for event in progress)
    assert all(event["nominal_increment_count"] == 2 for event in progress)
    assert all(event["load_increment"] > 0.0 for event in progress)
    assert status
    assert all("/2" not in message for message in status)
    assert "Increment trial 1" in status[0]
    assert "load factor" in status[0]
    assert "Newton iteration" in status[0]
    assert "residual" in status[0]
    quantities = describe_result_quantities(result)
    assert {quantity.quantity_id for quantity in quantities} >= {"displacement", "load_factor"}


def test_progress_observer_can_request_cooperative_cancellation() -> None:
    model, load = _elastic_cantilever()
    token = CancellationToken()

    def cancel_after_first_step(event: ProgressEvent) -> None:
        assert event["step_index"] == 1
        token.cancel("stop after preview")

    with pytest.raises(SolveCancelled, match="stop after preview"):
        solve_static_nonlinear(
            model,
            load,
            num_steps=4,
            cancellation_token=token,
            progress_callback=cancel_after_first_step,
        )
