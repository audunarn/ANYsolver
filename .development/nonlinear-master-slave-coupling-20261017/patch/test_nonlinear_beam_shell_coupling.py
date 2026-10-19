"""Verification of Slice 2: Direct nonlinear master-slave beam-shell kinematic coupling.

Tests the exact finite-rotation master-slave kinematic elimination:
    u_b = sum_i w_i u_{s,i} + (R(theta_bar_s) - I) r_0
    theta_b = theta_bar_s = sum_i w_i theta_{s,i}
with state-dependent Jacobian J(q) = du/dq, reduced residual
r_red(q) = J(q)^T (F_ext - F_int(u(q))), and symmetric geometric MPC tangent
K_mpc,geom(q, F_int - F_ext), using zero Lagrange multipliers.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from anysolver import (
    BoundaryCondition,
    DisplacementControl,
    FEModel,
    LoadCase,
    create_shell_element,
    solve_static_nonlinear,
)
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import (
    assemble_load_vector,
    assemble_stiffness_matrix,
)
from anysolver.corotational import (
    build_nonlinear_rotating_mpc_map,
    has_nonlinear_rotating_mpc,
    rotating_mpc_geometric_hessian,
    rotating_mpc_lever_arm_jacobian,
    rotation_matrix_from_vector,
    spatial_moment_from_rotation_covector,
)
from anysolver.constraint_audit import constraint_residual_summary
from anysolver.elements import BeamElement, CoupledBeamShellElement
from anysolver.mesh_gen import InterpolatedBeamShellMPCElement
from anysolver.nonlinear_restart import model_configuration_fingerprint
from anysolver.nonlinear_static import _assemble_nonlinear_system


def _build_coupled_cantilever(
    route: str,
    *,
    nx: int = 2,
    ny: int = 1,
    length: float = 1.0,
    width: float = 0.2,
    thickness: float = 0.02,
    eccentricity: tuple[float, float, float] = (0.0, 0.0, 0.05),
) -> tuple[FEModel, dict]:
    """Build a cantilever Q4 shell strip with a coupled eccentric beam stiffener."""
    model = FEModel(f"nonlinear_coupled_{route}")
    model.add_material("steel", 2.1e11, 0.3, density=7850.0)
    r_vec = np.asarray(eccentricity, dtype=float)

    # Create shell grid nodes: x in [0, length], y in [-width/2, width/2]
    shell_node_grid: dict[tuple[int, int], int] = {}
    node_id = 1
    xs = np.linspace(0.0, length, nx + 1)
    ys = np.linspace(-0.5 * width, 0.5 * width, ny + 1)
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            model.add_node(node_id, float(x), float(y), 0.0)
            shell_node_grid[(ix, iy)] = node_id
            node_id += 1

    elem_id = 1
    for ix in range(nx):
        for iy in range(ny):
            n1 = shell_node_grid[(ix, iy)]
            n2 = shell_node_grid[(ix + 1, iy)]
            n3 = shell_node_grid[(ix + 1, iy + 1)]
            n4 = shell_node_grid[(ix, iy + 1)]
            model.add_element(
                elem_id,
                create_shell_element(elem_id, [n1, n2, n3, n4], "steel", thickness=thickness),
            )
            elem_id += 1

    beam_nodes: list[int] = []
    couplings: list[dict] = []
    beam_base_id = 100
    mpc_base_id = 200

    if route == "eccentric":
        # Attach beam along y = -width/2 (iy = 0) one-to-one with shell nodes
        for ix, x in enumerate(xs):
            master_id = shell_node_grid[(ix, 0)]
            master_node = model.mesh.get_node(master_id)
            b_id = beam_base_id + ix
            b_xyz = np.array([master_node.x, master_node.y, master_node.z], dtype=float) + r_vec
            model.add_node(b_id, float(b_xyz[0]), float(b_xyz[1]), float(b_xyz[2]))
            beam_nodes.append(b_id)
            mpc_id = mpc_base_id + ix
            model.add_element(
                mpc_id,
                CoupledBeamShellElement(
                    mpc_id,
                    beam_node_id=b_id,
                    shell_node_id=master_id,
                    material_name="steel",
                    eccentricity=r_vec,
                ),
            )
            couplings.append(
                {
                    "slave": b_id,
                    "masters": [master_id],
                    "weights": np.array([1.0], dtype=float),
                    "r": r_vec.copy(),
                }
            )
    elif route == "interpolated":
        # Attach beam along the centerline y = 0 interpolated between iy=0 and iy=ny
        weights = np.array([0.6, 0.4], dtype=float)
        for ix, x in enumerate(xs):
            m1 = shell_node_grid[(ix, 0)]
            m2 = shell_node_grid[(ix, ny)]
            n1_obj = model.mesh.get_node(m1)
            n2_obj = model.mesh.get_node(m2)
            attach_xyz = weights[0] * np.array([n1_obj.x, n1_obj.y, n1_obj.z]) + weights[1] * np.array(
                [n2_obj.x, n2_obj.y, n2_obj.z]
            )
            b_id = beam_base_id + ix
            b_xyz = attach_xyz + r_vec
            model.add_node(b_id, float(b_xyz[0]), float(b_xyz[1]), float(b_xyz[2]))
            beam_nodes.append(b_id)
            mpc_id = mpc_base_id + ix
            model.add_element(
                mpc_id,
                InterpolatedBeamShellMPCElement(
                    mpc_id,
                    b_id,
                    [m1, m2],
                    weights,
                    eccentricity=r_vec,
                ),
            )
            couplings.append(
                {
                    "slave": b_id,
                    "masters": [m1, m2],
                    "weights": weights.copy(),
                    "r": r_vec.copy(),
                }
            )
    else:
        raise ValueError(f"Unknown route {route!r}")

    cross_section = {
        "area": 0.01 * 0.04,
        "Iy": 0.01 * (0.04**3) / 12.0,
        "Iz": 0.04 * (0.01**3) / 12.0,
        "J": 1.0e-8,
    }
    for ix in range(nx):
        b_elem_id = 300 + ix
        model.add_element(
            b_elem_id,
            BeamElement(
                b_elem_id,
                [beam_nodes[ix], beam_nodes[ix + 1]],
                material_name="steel",
                cross_section=cross_section,
            ),
        )

    root_shell_nodes = [shell_node_grid[(0, iy)] for iy in range(ny + 1)]
    tip_shell_nodes = [shell_node_grid[(nx, iy)] for iy in range(ny + 1)]
    model.add_boundary_condition(
        BoundaryCondition(
            "root",
            root_shell_nodes,
            {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
        )
    )
    model.apply_boundary_conditions()
    meta = {
        "route": route,
        "beam_nodes": beam_nodes,
        "root_shell_nodes": root_shell_nodes,
        "tip_shell_nodes": tip_shell_nodes,
        "couplings": couplings,
        "eccentricity": r_vec,
    }
    return model, meta


@pytest.mark.parametrize("route", ("eccentric", "interpolated"))
def test_mpc_descriptor_preserves_model_fingerprint(route: str) -> None:
    """Calling get_nonlinear_mpc_descriptor must never mutate element.__dict__ or model fingerprint."""
    model, _meta = _build_coupled_cantilever(route)
    K0, _ = assemble_stiffness_matrix(model)
    zero = np.zeros(K0.shape[0], dtype=float)
    _, _, T, _, _, _ = build_constraint_transformation(K0, zero, model)

    fp_before = model_configuration_fingerprint(model)
    dicts_before = {
        eid: dict(elem.__dict__) for eid, elem in model.mesh.elements.items()
    }

    assert has_nonlinear_rotating_mpc(model) is True
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    assert mpc_map is not None
    assert len(mpc_map.entries) == 3

    fp_after = model_configuration_fingerprint(model)
    assert fp_after == fp_before
    for eid, elem in model.mesh.elements.items():
        assert set(elem.__dict__.keys()) == set(dicts_before[eid].keys())


@pytest.mark.parametrize("route", ("eccentric", "interpolated"))
def test_rigid_body_motion_zero_strain_up_to_45_degrees(route: str) -> None:
    """Coupled beam-shell assembly has zero strain and zero residual under 45-deg 3D rigid motion."""
    model, meta = _build_coupled_cantilever(
        route,
        eccentricity=(0.03, -0.02, 0.08),
    )
    # Remove root clamp so all shell nodes can undergo a global rigid-body motion
    model.boundary_conditions.clear()
    model.apply_boundary_conditions()

    K0, _ = assemble_stiffness_matrix(model)
    zero = np.zeros(K0.shape[0], dtype=float)
    _, _, T, u0, independent_dofs, constraint_info = build_constraint_transformation(
        K0, zero, model
    )
    assert constraint_info["method"] == "transformation"
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    assert mpc_map is not None

    # 45-degree rotation about an oblique 3D axis + finite translation
    axis = np.array([1.0, -2.0, 1.5], dtype=float)
    axis /= np.linalg.norm(axis)
    omega = np.deg2rad(45.0) * axis
    R0 = rotation_matrix_from_vector(omega)
    c0 = np.array([0.4, -0.25, 0.7], dtype=float)
    pivot = np.array([0.2, 0.05, -0.1], dtype=float)

    # Prescribe rigid-body motion on all shell nodes
    u_shell_prescribed = np.zeros(K0.shape[0], dtype=float)
    slave_nodes = {c["slave"] for c in meta["couplings"]}
    for nid, node in model.mesh.nodes.items():
        if nid in slave_nodes:
            continue
        X = np.array([node.x, node.y, node.z], dtype=float)
        dofs = model.mesh.dof_manager.get_node_dofs(nid)
        u_shell_prescribed[dofs[:3]] = c0 + (R0 - np.eye(3)) @ (X - pivot)
        u_shell_prescribed[dofs[3:6]] = omega

    q = u_shell_prescribed[independent_dofs]
    u_lin = np.asarray(T @ q + u0, dtype=float).reshape(-1)
    u_nl = mpc_map.apply_kinematics(u_lin)

    # Verify exact rigid-body position of every coupled beam node
    for coupling in meta["couplings"]:
        slave_id = coupling["slave"]
        slave_node = model.mesh.get_node(slave_id)
        X_b = np.array([slave_node.x, slave_node.y, slave_node.z], dtype=float)
        expected_u_b = c0 + (R0 - np.eye(3)) @ (X_b - pivot)
        slave_dofs = model.mesh.dof_manager.get_node_dofs(slave_id)
        np.testing.assert_allclose(u_nl[slave_dofs[:3]], expected_u_b, atol=1.0e-14)
        np.testing.assert_allclose(u_nl[slave_dofs[3:6]], omega, atol=1.0e-14)

    # Evaluate corotational internal force at u_nl
    F_int_nl, _K_nl, _states = _assemble_nonlinear_system(
        model,
        u_nl,
        {},
        5,
        tangent=True,
        kinematics="corotational",
        corotational_tangent="work_conjugate",
    )
    r_red_nl = mpc_map.reduce_force(u_nl, F_int_nl)
    k_scale = float(np.max(np.abs(K0.diagonal())))
    assert float(np.max(np.abs(F_int_nl))) < 1.0e-15 * k_scale
    assert float(np.max(np.abs(r_red_nl))) < 1.0e-15 * k_scale

    # Contrast: the linear MPC displacement u_lin misses the true rigid-body beam position
    # by ||(skew(omega) - (R0 - I)) r_0|| > 15 mm at 45 deg, causing > 1e5 N of spurious
    # beam force when the tip beam node is at its exact rigid-body position.
    tip_slave_dofs = model.mesh.dof_manager.get_node_dofs(meta["couplings"][-1]["slave"])
    tip_slave_node = model.mesh.get_node(meta["couplings"][-1]["slave"])
    tip_X_b = np.array([tip_slave_node.x, tip_slave_node.y, tip_slave_node.z], dtype=float)
    tip_expected_u_b = c0 + (R0 - np.eye(3)) @ (tip_X_b - pivot)
    assert float(np.linalg.norm(u_lin[tip_slave_dofs[:3]] - tip_expected_u_b)) > 0.015

    u_lin_pinned_tip = u_lin.copy()
    u_lin_pinned_tip[tip_slave_dofs[:3]] = tip_expected_u_b
    F_int_lin, _, _ = _assemble_nonlinear_system(
        model,
        u_lin_pinned_tip,
        {},
        5,
        tangent=False,
        kinematics="corotational",
        corotational_tangent="work_conjugate",
    )
    assert float(np.max(np.abs(F_int_lin))) > 1.0e5


@pytest.mark.parametrize("route", ("eccentric", "interpolated"))
def test_diffeomorphism_and_constraint_residual_postcheck(route: str) -> None:
    """to_linear_displacement is the exact inverse of apply_kinematics and preserves MPC residual checks."""
    model, meta = _build_coupled_cantilever(
        route,
        eccentricity=(0.02, 0.03, -0.06),
    )
    K0, _ = assemble_stiffness_matrix(model)
    zero = np.zeros(K0.shape[0], dtype=float)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, zero, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    assert mpc_map is not None

    rng = np.random.default_rng(20261017)
    q = rng.uniform(-0.35, 0.35, int(T.shape[1]))
    u_lin = np.asarray(T @ q + u0, dtype=float).reshape(-1)
    u_nl = mpc_map.apply_kinematics(u_lin)
    u_lin_recovered = mpc_map.to_linear_displacement(u_nl)
    np.testing.assert_allclose(u_lin_recovered, u_lin, rtol=1.0e-14, atol=1.0e-15)
    np.testing.assert_allclose(
        mpc_map.apply_kinematics(u_lin_recovered), u_nl, rtol=1.0e-14, atol=1.0e-15
    )

    # Compatible nonlinear state has zero MPC residual when mapped via to_linear_displacement
    summary_ok = constraint_residual_summary(model, u_lin_recovered)
    assert summary_ok["status"] == "passed"
    assert summary_ok["max_absolute_residual"] < 1.0e-14
    assert summary_ok["max_relative_residual"] < 1.0e-14

    # Incompatible slave perturbation is detected with its exact magnitude
    u_bad = u_nl.copy()
    slave_dofs = model.mesh.dof_manager.get_node_dofs(meta["beam_nodes"][-1])
    u_bad[slave_dofs[0]] += 1.25e-3
    summary_bad = constraint_residual_summary(
        model, mpc_map.to_linear_displacement(u_bad)
    )
    assert summary_bad["status"] == "failed"
    assert summary_bad["max_absolute_residual"] == pytest.approx(1.25e-3, rel=1.0e-12)


def test_lever_arm_jacobian_and_geometric_hessian_match_finite_differences() -> None:
    """Verify A(theta_bar, r_0) and H_b(theta_bar, r_0, f_b) against central finite differences."""
    rng = np.random.default_rng(90210)
    for theta_scale in (0.0, 1.0e-7, 1.0e-4, 0.25, 0.85):
        theta_bar = theta_scale * rng.standard_normal(3)
        r0 = np.array([0.04, -0.025, 0.09], dtype=float)
        f_b = np.array([120.0, -350.0, 480.0], dtype=float)

        A = rotating_mpc_lever_arm_jacobian(theta_bar, r0)
        H = rotating_mpc_geometric_hessian(theta_bar, r0, f_b)
        np.testing.assert_allclose(H, H.T, atol=1.0e-14)

        eps = 1.0e-7
        A_fd = np.zeros((3, 3), dtype=float)
        H_fd = np.zeros((3, 3), dtype=float)
        for j in range(3):
            e_j = np.zeros(3, dtype=float)
            e_j[j] = eps
            tp = theta_bar + e_j
            tm = theta_bar - e_j
            up = (rotation_matrix_from_vector(tp) - np.eye(3)) @ r0
            um = (rotation_matrix_from_vector(tm) - np.eye(3)) @ r0
            A_fd[:, j] = (up - um) / (2.0 * eps)

            gp = rotating_mpc_lever_arm_jacobian(tp, r0).T @ f_b
            gm = rotating_mpc_lever_arm_jacobian(tm, r0).T @ f_b
            H_fd[:, j] = (gp - gm) / (2.0 * eps)

        np.testing.assert_allclose(A, A_fd, rtol=1.0e-8, atol=1.0e-10)
        np.testing.assert_allclose(H, H_fd, rtol=1.0e-7, atol=1.0e-8)


@pytest.mark.parametrize("route", ("eccentric", "interpolated"))
def test_reduced_coupled_tangent_matches_central_finite_differences(route: str) -> None:
    """Reduced coupled tangent J^T K_T J + K_mpc,geom is symmetric and matches FD to < 1e-6."""
    model, meta = _build_coupled_cantilever(
        route,
        nx=2,
        ny=1,
        eccentricity=(0.03, -0.015, 0.06),
    )
    # Apply nonzero external forces and moments directly to the eccentric beam nodes
    load = LoadCase("eccentric_beam_load")
    for idx, b_id in enumerate(meta["beam_nodes"][1:], start=1):
        load.add_nodal_load(
            b_id,
            forces=(150.0 * idx, -220.0 * idx, 400.0 * idx),
            moments=(12.0 * idx, -18.0 * idx, 9.0 * idx),
        )
    F_ext, _ = assemble_load_vector(model, load)

    K0, _ = assemble_stiffness_matrix(model)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, F_ext, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    assert mpc_map is not None

    rng = np.random.default_rng(1337 if route == "eccentric" else 7331)
    n_red = int(T.shape[1])
    # Finite deformation state with ~25-35 deg rotations and finite translations
    q = np.zeros(n_red, dtype=float)
    for col in range(n_red):
        dof = int(T.indices[T.indptr[col]])
        if dof % 6 < 3:
            q[col] = rng.uniform(-0.04, 0.04)
        else:
            q[col] = rng.uniform(-0.45, 0.45)

    def full_u(q_vec: np.ndarray) -> np.ndarray:
        return mpc_map.apply_kinematics(np.asarray(T @ q_vec + u0, dtype=float).reshape(-1))

    u = full_u(q)
    J = mpc_map.jacobian(u).toarray()

    # Check J(q) = du/dq against central finite differences
    eps_j = 1.0e-7
    J_fd = np.zeros_like(J)
    for j in range(n_red):
        dq = np.zeros(n_red, dtype=float)
        dq[j] = eps_j
        J_fd[:, j] = (full_u(q + dq) - full_u(q - dq)) / (2.0 * eps_j)
    np.testing.assert_allclose(J, J_fd, rtol=1.0e-8, atol=1.0e-10)

    # Evaluate internal force and consistent work-conjugate tangent
    F_int, K_T, _ = _assemble_nonlinear_system(
        model,
        u,
        {},
        5,
        tangent=True,
        kinematics="corotational",
        corotational_tangent="work_conjugate",
    )
    K_red = mpc_map.reduce_tangent(u, K_T, F_int - F_ext).toarray()

    # Symmetry check
    sym_err = np.linalg.norm(K_red - K_red.T, ord="fro") / max(
        np.linalg.norm(K_red, ord="fro"), 1.0
    )
    assert sym_err < 1.0e-12

    # Central finite difference of net reduced residual r_net(q) = J(q)^T (F_int(u(q)) - F_ext)
    def net_reduced_force(q_vec: np.ndarray) -> np.ndarray:
        u_q = full_u(q_vec)
        f_q, _, _ = _assemble_nonlinear_system(
            model,
            u_q,
            {},
            5,
            tangent=False,
            kinematics="corotational",
            corotational_tangent="work_conjugate",
        )
        return mpc_map.reduce_force(u_q, f_q - F_ext)

    eps = 1.0e-6
    K_fd = np.zeros_like(K_red)
    for j in range(n_red):
        dq = np.zeros(n_red, dtype=float)
        dq[j] = eps
        K_fd[:, j] = (net_reduced_force(q + dq) - net_reduced_force(q - dq)) / (2.0 * eps)

    rel_err = np.linalg.norm(K_red - K_fd, ord="fro") / np.linalg.norm(K_fd, ord="fro")
    assert rel_err < 1.0e-6

    # Confirm K_mpc,geom is non-vacuous: omitting it leaves a large O(||f_b|| ||r_0||) error
    K_without_geom = (J.T @ K_T.toarray() @ J)
    err_without_geom = np.linalg.norm(K_without_geom - K_fd, ord="fro")
    assert err_without_geom > 5.0e2 * np.linalg.norm(K_red - K_fd, ord="fro")


@pytest.mark.parametrize("route", ("eccentric", "interpolated"))
@pytest.mark.parametrize("control_mode", ("force", "displacement"))
def test_cantilever_stiffened_shell_finite_rotation_solve_and_wrench_balance(
    route: str,
    control_mode: str,
) -> None:
    """Solve coupled stiffened shell past 30 deg rotation and verify wrench & reaction balance."""
    model, meta = _build_coupled_cantilever(
        route,
        nx=4,
        ny=1,
        length=1.0,
        width=0.2,
        thickness=0.02,
        eccentricity=(0.0, 0.0, 0.05),
    )
    tip_beam_node = meta["beam_nodes"][-1]
    load = LoadCase("tip_bending_and_axial")
    # Apply transverse + axial force on the eccentric tip beam node so lever-arm
    # moment (R(theta_s) r_0) x f_b is strongly active at finite rotation (> 30 deg).
    load.add_nodal_load(
        tip_beam_node,
        forces=(-4.0e4, 1.5e4, -3.2e5),
        moments=(0.0, 2.0e4, 0.0),
    )

    if control_mode == "force":
        result = solve_static_nonlinear(
            model,
            load,
            num_steps=8,
            max_iterations=25,
            tolerance=1.0e-9,
            kinematics="corotational",
            corotational_tangent="auto",
        )
    else:
        ctrl = DisplacementControl(
            node_id=meta["tip_shell_nodes"][0],
            dof="uz",
            target_displacement=-0.45,
        )
        result = solve_static_nonlinear(
            model,
            load,
            control="displacement",
            displacement_control=ctrl,
            num_steps=8,
            max_iterations=25,
            tolerance=1.0e-9,
            kinematics="corotational",
            corotational_tangent="auto",
        )

    assert result.converged
    assert result.status == "completed"
    assert result.info["corotational_tangent"] == "work_conjugate"
    assert result.info["constraint_info"]["method"] == "transformation"
    assert result.info["constraint_postcheck"]["status"] == "passed"
    assert result.info["constraint_postcheck"]["max_absolute_residual"] <= 1.0e-12
    assert result.info["constraint_postcheck"]["max_relative_residual"] <= 1.0e-12

    u = np.asarray(result.displacements, dtype=float)
    tip_beam_dofs = model.mesh.dof_manager.get_node_dofs(tip_beam_node)
    tip_rot_norm = float(np.linalg.norm(u[tip_beam_dofs[3:6]]))
    # Verify finite rotation exceeds 30 degrees (0.5236 rad)
    assert tip_rot_norm > np.deg2rad(30.0)

    # Verify exact nonlinear rotating-arm kinematic relation at all coupled nodes
    for coupling in meta["couplings"]:
        slave_dofs = model.mesh.dof_manager.get_node_dofs(coupling["slave"])
        u_s_bar = np.zeros(3, dtype=float)
        theta_s_bar = np.zeros(3, dtype=float)
        for m_id, w in zip(coupling["masters"], coupling["weights"]):
            m_dofs = model.mesh.dof_manager.get_node_dofs(m_id)
            u_s_bar += float(w) * u[m_dofs[:3]]
            theta_s_bar += float(w) * u[m_dofs[3:6]]
        expected_u_b = u_s_bar + (rotation_matrix_from_vector(theta_s_bar) - np.eye(3)) @ coupling["r"]
        np.testing.assert_allclose(u[slave_dofs[:3]], expected_u_b, rtol=1.0e-12, atol=1.0e-14)
        np.testing.assert_allclose(u[slave_dofs[3:6]], theta_s_bar, rtol=1.0e-12, atol=1.0e-14)

    # Verify spatial wrench transfer identity and global support reaction balance
    K0, _ = assemble_stiffness_matrix(model)
    F_prop, _ = assemble_load_vector(model, load)
    F_ext = float(result.load_factor) * F_prop
    _, _, T, _, _, _ = build_constraint_transformation(K0, F_prop, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    assert mpc_map is not None

    F_int, _, _ = _assemble_nonlinear_system(
        model,
        u,
        result.element_states,
        5,
        tangent=False,
        kinematics="corotational",
        corotational_tangent="work_conjugate",
    )
    out_of_balance = F_int - F_ext
    reduced_residual = mpc_map.reduce_force(u, out_of_balance)
    ref_norm = max(float(np.linalg.norm(mpc_map.reduce_force(u, F_ext))), 1.0)
    assert float(np.linalg.norm(reduced_residual)) <= 1.0e-8 * ref_norm

    # Verify per-slave spatial wrench equivalence:
    # Since t_i = J_l(theta_i)^{-T} m_i and J_r(theta) J_l(theta)^T = R(theta),
    # J_l(theta_bar)^{-T} (m_b + A(theta_bar, r_0)^T f_b)
    #   = t_b - J_l(theta_bar)^{-T} J_r(theta_bar)^T (-hat(r_0)) R(theta_bar)^T f_b
    #   = t_b + R(theta_bar) hat(r_0) R(theta_bar)^T f_b
    #   = t_b + (R(theta_bar) r_0) x f_b !
    for entry in mpc_map.entries:
        f_b = out_of_balance[list(entry.slave_u_dofs)]
        m_b = out_of_balance[list(entry.slave_theta_dofs)]
        theta_bar = entry.master_rotation(u)
        A = rotating_mpc_lever_arm_jacobian(theta_bar, entry.eccentricity)
        spatial_torque_from_pullback = spatial_moment_from_rotation_covector(
            theta_bar, m_b + A.T @ f_b
        )
        t_b = spatial_moment_from_rotation_covector(theta_bar, m_b)
        r_spatial = rotation_matrix_from_vector(theta_bar) @ entry.eccentricity
        spatial_torque_expected = t_b + np.cross(r_spatial, f_b)
        np.testing.assert_allclose(
            spatial_torque_from_pullback,
            spatial_torque_expected,
            rtol=1.0e-11,
            atol=1.0e-11,
        )

    # Verify global support reaction force equilibrium (including root slave beam transfer)
    root_reaction = np.asarray(result.steps[-1].support_reactions["root"][:3], dtype=float)
    applied_total_force = np.array([-4.0e4, 1.5e4, -3.2e5], dtype=float) * float(
        result.load_factor
    )
    np.testing.assert_allclose(
        root_reaction + applied_total_force,
        np.zeros(3, dtype=float),
        atol=1.0e-7 * np.linalg.norm(applied_total_force),
    )


@pytest.mark.parametrize("route", ("eccentric", "interpolated"))
def test_coupled_corotational_split_restart_matches_uninterrupted(route: str) -> None:
    """Split restart at finite rotation reproduces the uninterrupted solve."""
    model, meta = _build_coupled_cantilever(
        route,
        nx=2,
        ny=1,
        eccentricity=(0.0, 0.0, 0.05),
    )
    half_load = LoadCase("half_tip_load")
    half_load.add_nodal_load(
        meta["beam_nodes"][-1],
        forces=(-1.0e4, 0.5e4, -1.25e5),
    )
    common = dict(
        num_steps=2,
        max_iterations=25,
        tolerance=1.0e-10,
        kinematics="corotational",
        corotational_tangent="auto",
    )

    half = solve_static_nonlinear(
        model,
        half_load,
        max_load_factor=1.0,
        **common,
    )
    assert half.converged
    resumed = solve_static_nonlinear(
        model,
        half_load,
        constant_load_case=half_load,
        max_load_factor=1.0,
        initial_displacements=half.displacements,
        initial_element_states=half.element_states,
        equilibrate_initial_state=False,
        **common,
    )
    assert resumed.converged

    fresh_model, fresh_meta = _build_coupled_cantilever(
        route,
        nx=2,
        ny=1,
        eccentricity=(0.0, 0.0, 0.05),
    )
    fresh_load = LoadCase("full_tip_load")
    fresh_load.add_nodal_load(
        fresh_meta["beam_nodes"][-1],
        forces=(-2.0e4, 1.0e4, -2.5e5),
    )
    uninterrupted = solve_static_nonlinear(
        fresh_model,
        fresh_load,
        max_load_factor=1.0,
        num_steps=4,
        max_iterations=25,
        tolerance=1.0e-10,
        kinematics="corotational",
        corotational_tangent="auto",
    )
    assert uninterrupted.converged
    np.testing.assert_allclose(
        resumed.displacements,
        uninterrupted.displacements,
        rtol=1.0e-8,
        atol=1.0e-10,
    )

