"""End-to-end prestressed modal and buckling parity for qualified S3."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import linalg

from anysolver import (
    AnalysisSession,
    BoundaryCondition,
    FEModel,
    FixedSupport,
    QualifiedE4PLS3ShellElement,
    QualifiedE4PLShellElement,
    solve_static_nonlinear,
    solve_eigenvalue_buckling,
    solve_free_vibration,
)
from anysolver.boundary import LoadCase
from anysolver.assembly import build_constraint_transformation
from anysolver.e4_pl_s3_element import (
    REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID,
)
from anysolver.e4_pl_s3_state import canonical_json_bytes
from anysolver.matrix_assembly import (
    assemble_geometric_stiffness_matrix,
    assemble_mass_matrix,
    assemble_stiffness_matrix,
)
from anysolver.modal import CURRENT_STATE_MODAL_POLICY_ID, PRESTRESSED_MODAL_POLICY_ID
from anysolver.nonlinear_state import (
    NonlinearStateStore,
    create_model_native_rotation_store,
    discard_active_state_candidate,
)
from anysolver.shell_sections import GeneralizedShellSection


def _model() -> FEModel:
    model = FEModel("qualified-s3-prestressed-eigen")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinates in enumerate(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)),
        start=1,
    ):
        model.add_node(node_id, *coordinates)
    model.add_element(
        1,
        QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "steel",
            thickness=0.02,
            reference_normal=np.asarray((0.0, 0.0, 1.0)),
        ),
    )
    model.add_boundary_condition(FixedSupport("fixed-edge", [1, 2]))
    model.add_boundary_condition(
        BoundaryCondition("node-3-in-plane", [3], {"ux": 0.0, "uy": 0.0})
    )
    return model


def _compression(scale: float = 1.0) -> dict[str, object]:
    pressure = 1.0e5 * float(scale)
    thickness = 0.02
    return {
        "bubble_linearization_policy": (
            REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID
        ),
        "membrane_compression": [pressure, pressure, 0.0],
        "bending_compression": [0.0, 0.0, 0.0],
        "stress_second_moment": [
            pressure * thickness**2 / 12.0,
            pressure * thickness**2 / 12.0,
            0.0,
        ],
    }


def _finite_descriptor_values(
    stiffness: np.ndarray, mass: np.ndarray
) -> np.ndarray:
    alpha_beta, _vectors = linalg.eig(
        stiffness,
        mass,
        homogeneous_eigvals=True,
        right=True,
    )
    alpha, beta = alpha_beta
    scale = max(float(np.max(np.abs(beta))), np.finfo(float).tiny)
    finite = np.abs(beta) > np.finfo(float).eps * len(beta) * scale
    values = np.real_if_close(alpha[finite] / beta[finite], tol=1000)
    values = np.asarray(np.real(values), dtype=float)
    return np.sort(values[np.isfinite(values)])


def _reduced_operators(
    model: FEModel, state: dict[str, object]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.apply_boundary_conditions()
    stiffness, _stiffness_info = assemble_stiffness_matrix(model)
    geometric, _geometric_info = assemble_geometric_stiffness_matrix(
        model, {1: state}
    )
    mass, _mass_info = assemble_mass_matrix(model)
    reduced_stiffness, _, transform, _, _, _ = build_constraint_transformation(
        stiffness,
        np.zeros(stiffness.shape[0], dtype=float),
        model,
    )
    return (
        reduced_stiffness.toarray(),
        (transform.T @ geometric @ transform).toarray(),
        (transform.T @ mass @ transform).toarray(),
    )


def _axial_nonlinear_model() -> tuple[FEModel, LoadCase]:
    model = FEModel("qualified-s3-current-state-modal")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinates in enumerate(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)),
        start=1,
    ):
        model.add_node(node_id, *coordinates)
    model.add_element(
        1,
        QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "steel",
            thickness=0.01,
            reference_normal=np.asarray((0.0, 0.0, 1.0)),
        ),
    )
    model.add_boundary_condition(FixedSupport("node-1", [1]))
    model.add_boundary_condition(
        BoundaryCondition(
            "node-2-axial-only",
            [2],
            {"uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
        )
    )
    model.add_boundary_condition(FixedSupport("node-3", [3]))
    load = LoadCase("pull")
    load.add_nodal_load(2, [1.0e3, 0.0, 0.0, 0.0, 0.0, 0.0])
    return model, load


def _committed_trial_force(
    model: FEModel,
    committed_displacements: np.ndarray,
    trial_displacements: np.ndarray,
    states: dict[int, object],
) -> np.ndarray:
    store = NonlinearStateStore.from_shell_layouts((), states)
    native = create_model_native_rotation_store(
        model, store, committed_displacements
    )
    assert native is not None
    store.attach_native_rotation_store(native)
    try:
        from anysolver.nonlinear_static import _assemble_nonlinear_system

        force, _tangent, _candidate = _assemble_nonlinear_system(
            model,
            trial_displacements,
            store,
            3,
            tangent=False,
            require_full_coordinates=True,
        )
        return np.asarray(force, dtype=float)
    finally:
        discard_active_state_candidate(store)


def test_prestressed_modal_matches_independent_descriptor_pencil() -> None:
    model = _model()
    state = _compression()
    material, geometric, mass = _reduced_operators(model, state)
    oracle = _finite_descriptor_values(material - geometric, mass)

    baseline = solve_free_vibration(model, num_modes=3)
    result = solve_free_vibration(
        model,
        num_modes=3,
        prestress_states={1: state},
    )

    assert result.solver_status == "ok"
    assert result.assembly_info["prestressed_modal_policy_id"] == (
        PRESTRESSED_MODAL_POLICY_ID
    )
    assert result.assembly_info["geometric_stiffness"]["matrix_type"] == (
        "geometric_stiffness"
    )
    np.testing.assert_allclose(
        np.asarray([mode.eigenvalue for mode in result.modes]),
        oracle[:3],
        rtol=3.0e-10,
        atol=2.0e-7,
    )
    assert result.frequencies_hz[0] < baseline.frequencies_hz[0]
    assert result.diagnostics["max_residual_norm"] < 3.0e-10


def test_prestressed_modal_session_matches_uncached_path() -> None:
    model = _model()
    states = {1: _compression(0.4)}
    expected = solve_free_vibration(
        model,
        num_modes=3,
        prestress_states=states,
    )

    with AnalysisSession(model) as session:
        first = solve_free_vibration(
            model,
            num_modes=3,
            session=session,
            prestress_states=states,
        )
        repeated = solve_free_vibration(
            model,
            num_modes=3,
            session=session,
            prestress_states=states,
        )

    np.testing.assert_allclose(
        first.frequencies_hz, expected.frequencies_hz, rtol=2.0e-12
    )
    np.testing.assert_allclose(
        repeated.frequencies_hz, first.frequencies_hz, rtol=2.0e-12
    )
    assert repeated.diagnostics["analysis_session"]["plan_reused"] is True


def test_committed_current_state_modal_matches_force_difference_tangent() -> None:
    model, load = _axial_nonlinear_model()
    static = solve_static_nonlinear(
        model,
        load,
        num_steps=2,
        num_layers=3,
    )
    assert static.status == "completed"
    frozen_state = canonical_json_bytes(static.element_states[1])

    result = solve_free_vibration(
        model,
        num_modes=1,
        current_state_displacements=static.displacements,
        current_state_element_states=static.element_states,
        current_state_num_layers=3,
    )

    model.apply_boundary_conditions()
    mass, _mass_info = assemble_mass_matrix(model)
    material, _stiffness_info = assemble_stiffness_matrix(model)
    _reduced, _, transform, _, _, _ = build_constraint_transformation(
        material,
        np.zeros(material.shape[0], dtype=float),
        model,
    )
    assert transform.shape[1] == 1
    direction = np.asarray(transform[:, 0].toarray(), dtype=float).reshape(-1)
    step = 1.0e-7
    plus = _committed_trial_force(
        model,
        np.asarray(static.displacements),
        np.asarray(static.displacements) + step * direction,
        static.element_states,
    )
    minus = _committed_trial_force(
        model,
        np.asarray(static.displacements),
        np.asarray(static.displacements) - step * direction,
        static.element_states,
    )
    tangent_action = (plus - minus) / (2.0 * step)
    stiffness_scalar = float(direction @ tangent_action)
    mass_scalar = float(direction @ (mass @ direction))
    oracle = stiffness_scalar / mass_scalar

    assert result.solver_status == "ok"
    assert canonical_json_bytes(static.element_states[1]) == frozen_state
    assert result.assembly_info["current_state_modal_policy_id"] == (
        CURRENT_STATE_MODAL_POLICY_ID
    )
    assert result.assembly_info["current_state_tangent"][
        "relative_symmetry_error"
    ] <= 512.0 * np.finfo(np.float64).eps
    np.testing.assert_allclose(
        result.modes[0].eigenvalue,
        oracle,
        rtol=2.0e-7,
        atol=0.0,
    )


def test_mixed_q4_s3_current_state_modal_matches_virgin_reference() -> None:
    model = FEModel("mixed-qualified-current-state-modal")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinates in enumerate(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (2.0, 0.5, 0.0),
        ),
        start=1,
    ):
        model.add_node(node_id, *coordinates)
    model.add_element(
        1,
        QualifiedE4PLShellElement(
            1, [1, 2, 3, 4], "steel", thickness=0.02
        ),
    )
    s3 = QualifiedE4PLS3ShellElement(
        2,
        [2, 5, 3],
        "steel",
        thickness=0.02,
        reference_normal=np.asarray((0.0, 0.0, 1.0)),
    )
    model.add_element(2, s3)
    model.add_boundary_condition(FixedSupport("left-edge", [1, 4]))
    zero = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    states = {
        2: s3.init_model_bound_nonlinear_state(
            model.mesh, model.get_material("steel"), 3
        )
    }

    reference = solve_free_vibration(model, num_modes=4)
    current = solve_free_vibration(
        model,
        num_modes=4,
        current_state_displacements=zero,
        current_state_element_states=states,
        current_state_num_layers=3,
    )

    assert reference.solver_status == current.solver_status == "ok"
    np.testing.assert_allclose(
        current.frequencies_hz,
        reference.frequencies_hz,
        rtol=8.0e-10,
        atol=1.0e-8,
    )
    assert current.diagnostics["declared_algebraic_element_ids"] == [2]


def test_generalized_section_current_state_modal_uses_native_tangent() -> None:
    model = FEModel("generalized-s3-current-state-modal")
    model.add_material("carrier", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinates in enumerate(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)),
        start=1,
    ):
        model.add_node(node_id, *coordinates)
    section = GeneralizedShellSection(
        A=np.asarray(((2.3e9, 0.7e9, 0.0), (0.7e9, 2.1e9, 0.0), (0.0, 0.0, 0.8e9))),
        B=np.asarray(((1.2e5, -0.3e5, 0.0), (-0.3e5, 0.9e5, 0.0), (0.0, 0.0, 0.2e5))),
        D=np.asarray(((1.9e5, 0.5e5, 0.0), (0.5e5, 1.7e5, 0.0), (0.0, 0.0, 0.6e5))),
        As=np.asarray(((7.0e8, 0.0), (0.0, 6.0e8))),
    )
    model.add_element(
        1,
        QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "carrier",
            thickness=0.01,
            shell_section=section,
            material_direction=np.asarray((1.0, 0.0, 0.0)),
            reference_normal=np.asarray((0.0, 0.0, 1.0)),
        ),
    )
    model.add_boundary_condition(FixedSupport("node-1", [1]))
    model.add_boundary_condition(
        BoundaryCondition(
            "node-2-axial-only",
            [2],
            {"uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
        )
    )
    model.add_boundary_condition(FixedSupport("node-3", [3]))
    load = LoadCase("pull")
    load.add_nodal_load(2, [25.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    static = solve_static_nonlinear(
        model, load, num_steps=2, num_layers=3
    )
    assert static.status == "completed"

    result = solve_free_vibration(
        model,
        num_modes=1,
        current_state_displacements=static.displacements,
        current_state_element_states=static.element_states,
        current_state_num_layers=3,
    )

    assert result.solver_status == "ok"
    assert result.modes[0].eigenvalue > 0.0
    assert result.assembly_info["current_state_tangent"]["state_digests"] == {
        "1": static.element_states[1]["state_integrity_sha256"]
    }


def test_buckling_matches_independent_pencil_and_inverse_load_scaling() -> None:
    model = _model()
    state = _compression()
    material, geometric, _mass = _reduced_operators(model, state)
    oracle = _finite_descriptor_values(material, geometric)
    oracle = oracle[oracle > 0.0]

    result = solve_eigenvalue_buckling(
        model,
        {1: state},
        num_modes=4,
        dense_size_limit=1000,
        allow_free_mechanisms=True,
        reference_elastic_only=True,
    )
    doubled = solve_eigenvalue_buckling(
        model,
        {1: _compression(2.0)},
        num_modes=4,
        dense_size_limit=1000,
        allow_free_mechanisms=True,
        reference_elastic_only=True,
    )

    factors = np.asarray([mode.load_factor for mode in result.modes])
    doubled_factors = np.asarray([mode.load_factor for mode in doubled.modes])
    assert result.solver_status == "ok"
    np.testing.assert_allclose(factors, oracle[: len(factors)], rtol=3.0e-12)
    np.testing.assert_allclose(doubled_factors, 0.5 * factors, rtol=3.0e-12)
    assert result.diagnostics["max_residual_norm"] < 1.0e-10


def test_capability_matrix_records_both_eigen_workflows_as_native() -> None:
    matrix = _model().mesh.elements[1].capability_matrix()

    assert matrix["reference_elastic_prestressed_modal"] == "PARITY_REPLACED"
    assert matrix["reference_elastic_buckling"] == "PARITY_REPLACED"
    assert matrix["current_state_modal"] == "PARITY_REPLACED"
    assert matrix["buckling"] == "PARITY_GAP"


def test_eigen_authority_profiles_reject_ambiguous_inputs_before_mechanics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model()

    def forbidden() -> None:
        raise AssertionError("eigen input validation reached model evaluation")

    monkeypatch.setattr(model, "apply_boundary_conditions", forbidden)
    with pytest.raises(ValueError, match="requires both committed"):
        solve_free_vibration(
            model,
            current_state_displacements=np.zeros(18),
        )
    with pytest.raises(ValueError, match="mutually exclusive"):
        solve_free_vibration(
            model,
            prestress_states={1: _compression()},
            current_state_displacements=np.zeros(18),
            current_state_element_states={},
        )
    malformed = _compression()
    malformed.pop("bubble_linearization_policy")
    with pytest.raises(ValueError, match="bubble_linearization_policy"):
        solve_eigenvalue_buckling(
            model,
            {1: malformed},
            reference_elastic_only=True,
        )
