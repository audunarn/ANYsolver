# ---------------------------------------------------------------------------
# Rigid-spin objectivity of the intrinsic SO(3) mean (adopted contract)
# ---------------------------------------------------------------------------


def test_so3_mean_counterexample_is_rigid_spin_equivariant() -> None:
    """The review's exact counterexample: the mean is equivariant where the linear average is not."""
    a = 0.5 * np.pi
    thetas = [np.array([a, 0.0, 0.0]), np.array([-a, 0.0, 0.0])]
    weights = [0.5, 0.5]
    theta_m, G = _so3_weighted_mean(thetas, weights, "test")
    # Commuting rotations: the mean is the exact weighted average.
    np.testing.assert_allclose(theta_m, np.zeros(3), atol=1.0e-14)

    # Differential rigid-spin identity: sum_i G_i J_l(theta_i)^-1 = J_l(theta_m)^-1.
    lhs = np.zeros((3, 3))
    for G_i, t_i in zip(G, thetas):
        lhs += G_i @ _rotation_left_jacobian_inverse(t_i)
    np.testing.assert_allclose(lhs, _rotation_left_jacobian_inverse(theta_m), atol=1.0e-12)

    # Superpose Q = Ry(pi/2) on both physical masters.
    Q = rotation_matrix_from_vector(np.array([0.0, a, 0.0]))
    spun = [rotation_vector_from_matrix(Q @ rotation_matrix_from_vector(t)) for t in thetas]
    theta_m_spun, G_spun = _so3_weighted_mean(spun, weights, "test")
    np.testing.assert_allclose(
        rotation_matrix_from_vector(theta_m_spun), Q, rtol=0.0, atol=1.0e-12
    )
    lhs_spun = np.zeros((3, 3))
    for G_i, t_i in zip(G_spun, spun):
        lhs_spun += G_i @ _rotation_left_jacobian_inverse(t_i)
    np.testing.assert_allclose(
        lhs_spun, _rotation_left_jacobian_inverse(theta_m_spun), atol=1.0e-12
    )

    # Discriminator: the arithmetic average of the spun principal rotation
    # vectors is NOT equivariant (it is (0, 2pi/(3sqrt3), 0), not (0, pi/2, 0)).
    lin_spun = weights[0] * spun[0] + weights[1] * spun[1]
    assert np.linalg.norm(lin_spun - np.array([0.0, a, 0.0])) > 1.0e-2


def test_so3_mean_direct_identical_limits_and_refusals() -> None:
    """Direct, identical-rotation and first-order limits are exact; unsupported cases refuse."""
    t = np.array([0.3, -0.2, 0.15])
    theta_m, G = _so3_weighted_mean([t], [1.0], "test")
    np.testing.assert_array_equal(theta_m, t)
    np.testing.assert_allclose(G[0], np.eye(3), atol=0.0)

    theta_m2, G2 = _so3_weighted_mean([t, t, t], [0.2, 0.5, 0.3], "test")
    np.testing.assert_array_equal(theta_m2, t)
    for G_i, w in zip(G2, (0.2, 0.5, 0.3)):
        np.testing.assert_allclose(G_i, w * np.eye(3), atol=1.0e-15)

    # First-order weighted linear relation for small rotations.
    small = [np.array([1.0e-3, -2.0e-3, 5.0e-4]), np.array([-1.5e-3, 1.0e-3, -3.0e-4])]
    theta_small, _G_small = _so3_weighted_mean(small, [0.6, 0.4], "test")
    lin_small = 0.6 * small[0] + 0.4 * small[1]
    assert np.linalg.norm(theta_small - lin_small) <= 1.0e-7

    with pytest.raises(ValueError, match="nonnegative"):
        _so3_weighted_mean([t, -0.5 * t], [1.5, -0.5], "test")
    with pytest.raises(ValueError, match="partition of unity"):
        _so3_weighted_mean([t, t], [0.5, 0.4], "test")


def _interp_map_with_distinct_master_rotations(eccentricity=(0.02, 0.03, -0.06)):
    """Interpolated fixture map plus a linear state with distinct finite master rotations."""
    model, meta = _build_coupled_cantilever("interpolated", eccentricity=eccentricity)
    K0, _ = assemble_stiffness_matrix(model)
    zero = np.zeros(K0.shape[0], dtype=float)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, zero, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    assert mpc_map is not None
    rng = np.random.default_rng(20261018)
    q = rng.uniform(-0.05, 0.05, int(T.shape[1]))
    u_lin = np.asarray(T @ q + u0, dtype=float).reshape(-1)
    for entry in mpc_map.entries:
        for k, (_m_u, m_theta, _w) in enumerate(entry.masters):
            u_lin[m_theta] = np.roll(np.array([0.35, -0.27, 0.19]), k) * (1.0 + 0.13 * k)
    return model, meta, T, u0, q, mpc_map, u_lin


def _node_positions_by_translation_dof(model, dof_manager):
    positions = {}
    for coupling_node_ids in ([c["slave"]] + list(c["masters"]) for c in []):
        pass
    return positions


def test_interp_map_finite_rigid_spin_covariance() -> None:
    """Weighted attachment point and slave orientation transform under a common rigid rotation."""
    model, meta, T, u0, q, mpc_map, u_lin = _interp_map_with_distinct_master_rotations()
    u_nl = mpc_map.apply_kinematics(u_lin)

    psi = np.array([0.23, -0.31, 0.42])
    Q = rotation_matrix_from_vector(psi)
    u_lin_spun = u_lin.copy()
    dof_manager = model.mesh.dof_manager
    for coupling in meta["couplings"]:
        master_states = []
        for m_id, w in zip(coupling["masters"], coupling["weights"]):
            m_dofs = dof_manager.get_node_dofs(m_id)
            m_node = model.mesh.get_node(m_id)
            X = np.array([m_node.x, m_node.y, m_node.z], dtype=float)
            u_lin_spun[m_dofs[:3]] = (Q - np.eye(3)) @ X + Q @ u_lin[m_dofs[:3]]
            u_lin_spun[m_dofs[3:6]] = rotation_vector_from_matrix(
                Q @ rotation_matrix_from_vector(u_lin[m_dofs[3:6]])
            )
            master_states.append(
                (np.array(u_lin_spun[m_dofs[:3]]), np.array(u_lin_spun[m_dofs[3:6]]), float(w))
            )
        s_dofs = dof_manager.get_node_dofs(coupling["slave"])
        u_bar = sum(w * mu for mu, _mt, w in master_states)
        theta_lin = sum(w * mt for _mu, mt, w in master_states)
        u_lin_spun[s_dofs[:3]] = u_bar + np.cross(theta_lin, coupling["r"])
        u_lin_spun[s_dofs[3:6]] = theta_lin

    u_nl_spun = mpc_map.apply_kinematics(u_lin_spun)
    for coupling in meta["couplings"]:
        s_dofs = dof_manager.get_node_dofs(coupling["slave"])
        s_node = model.mesh.get_node(coupling["slave"])
        X_b = np.array([s_node.x, s_node.y, s_node.z], dtype=float)
        x_b = X_b + u_nl[s_dofs[:3]]
        x_b_spun = X_b + u_nl_spun[s_dofs[:3]]
        np.testing.assert_allclose(x_b_spun, Q @ x_b, rtol=0.0, atol=1.0e-12)
        R_b = rotation_matrix_from_vector(u_nl[s_dofs[3:6]])
        R_b_spun = rotation_matrix_from_vector(u_nl_spun[s_dofs[3:6]])
        np.testing.assert_allclose(R_b_spun, Q @ R_b, rtol=0.0, atol=1.0e-12)


def test_interp_transfer_preserves_physical_spatial_wrench() -> None:
    """The exact moment-defect discriminator: the new transfer preserves the spatial wrench.

    The old common-covector transfer changed the total physical spatial moment
    by Delta_M = D^T (m_b + A^T f_b) with D = sum_i w_i J_l(theta_i)^-1 -
    J_l(theta_bar)^-1; the mean-tangent transfer G_i^T (m_b + A^T f_b) removes
    that defect exactly.
    """
    model, meta, T, u0, q, mpc_map, u_lin = _interp_map_with_distinct_master_rotations()
    u_nl = mpc_map.apply_kinematics(u_lin)
    dof_manager = model.mesh.dof_manager

    # dof -> node id lookup for translation dofs.
    node_of_dof = {}
    for coupling in meta["couplings"]:
        for nid in [coupling["slave"]] + list(coupling["masters"]):
            for d in dof_manager.get_node_dofs(nid):
                node_of_dof[int(d)] = int(nid)

    def node_position(nid):
        node = model.mesh.get_node(nid)
        return np.array([node.x, node.y, node.z], dtype=float)

    rng = np.random.default_rng(20261019)
    imbalance = np.zeros_like(u_nl)
    for entry in mpc_map.entries:
        imbalance[entry.slave_u_dofs] = rng.uniform(-2.0e3, 2.0e3, 3)
        imbalance[entry.slave_theta_dofs] = rng.uniform(-5.0e2, 5.0e2, 3)
    transferred = mpc_map.transfer_slave_imbalance_to_masters(u_nl, imbalance)

    for entry in mpc_map.entries:
        f_b = imbalance[entry.slave_u_dofs]
        m_b = imbalance[entry.slave_theta_dofs]
        theta_m, G_list = entry.mean_state(u_nl)
        A = rotating_mpc_lever_arm_jacobian(theta_m, entry.eccentricity)
        v = m_b + A.T @ f_b
        slave_id = node_of_dof[int(entry.slave_u_dofs[0])]
        x_b = node_position(slave_id) + u_nl[entry.slave_u_dofs]
        F_before = f_b
        M_before = spatial_moment_from_rotation_covector(
            u_nl[entry.slave_theta_dofs], m_b
        ) + np.cross(x_b, f_b)
        F_after = np.zeros(3)
        M_after = np.zeros(3)
        for (m_u, m_theta, _w), _G in zip(entry.masters, G_list):
            f_i = transferred[m_u]
            m_i = transferred[m_theta]
            x_i = node_position(node_of_dof[int(m_u[0])]) + u_nl[m_u]
            F_after += f_i
            M_after += spatial_moment_from_rotation_covector(
                u_nl[m_theta], m_i
            ) + np.cross(x_i, f_i)
        scale = max(np.linalg.norm(M_before), np.linalg.norm(F_before), 1.0)
        np.testing.assert_allclose(F_after, F_before, rtol=0.0, atol=1.0e-9 * scale)
        np.testing.assert_allclose(M_after, M_before, rtol=0.0, atol=1.0e-9 * scale)
        # The old averaged-map defect D is nonzero on this state: the removed
        # mechanism is real, not vacuous.
        D = np.zeros((3, 3))
        theta_lin = entry.master_rotation(u_nl)
        for (_m_u, m_theta, w) in entry.masters:
            D += w * _rotation_left_jacobian_inverse(u_nl[m_theta])
        D -= _rotation_left_jacobian_inverse(theta_lin)
        delta_M = D.T @ v
        assert np.linalg.norm(delta_M) > 1.0e-6 * scale


def test_interp_map_jacobian_reduced_force_and_geometric_tangent_match_fd() -> None:
    """FD of the whole forward map, reduced force and mean derivative (nonzero m_b)."""
    model, meta, T, u0, q, mpc_map, u_lin = _interp_map_with_distinct_master_rotations()
    u_nl = mpc_map.apply_kinematics(u_lin)
    n_red = int(T.shape[1])

    def full_u(q_vec):
        return mpc_map.apply_kinematics(np.asarray(T @ q_vec + u0, dtype=float).reshape(-1))

    J = mpc_map.jacobian(u_nl).toarray()
    eps = 1.0e-7
    J_fd = np.zeros_like(J)
    for j in range(n_red):
        dq = np.zeros(n_red, dtype=float)
        dq[j] = eps
        J_fd[:, j] = (full_u(q + dq) - full_u(q - dq)) / (2.0 * eps)
    np.testing.assert_allclose(J, J_fd, rtol=1.0e-7, atol=1.0e-8)

    # reduce_force is exactly J^T f, including the slave moment covector.
    rng = np.random.default_rng(20261020)
    f = rng.uniform(-1.0, 1.0, u_nl.shape[0])
    for entry in mpc_map.entries:
        f[entry.slave_u_dofs] = rng.uniform(-2.0e3, 2.0e3, 3)
        f[entry.slave_theta_dofs] = rng.uniform(-5.0e2, 5.0e2, 3)
    g = mpc_map.reduce_force(u_nl, f)
    np.testing.assert_allclose(g, J.T @ f, rtol=0.0, atol=1.0e-9)

    # Geometric tangent: complete FD of the slave-correction covector g(q),
    # including mean second derivatives and the m_b-weighted orientation
    # Hessian (the old force-only lever Hessian omits them).
    K_geom = mpc_map.geometric_tangent(u_nl, f).toarray()
    T_dense = T.toarray()
    base = g - T_dense.T @ f
    assert np.linalg.norm(base) > 0.0

    def corr(q_vec):
        u_q = full_u(q_vec)
        return mpc_map.reduce_force(u_q, f) - T_dense.T @ f

    eps_k = 1.0e-6
    K_fd = np.zeros_like(K_geom)
    for j in range(n_red):
        dq = np.zeros(n_red, dtype=float)
        dq[j] = eps_k
        K_fd[:, j] = (corr(q + dq) - corr(q - dq)) / (2.0 * eps_k)
    np.testing.assert_allclose(K_geom, K_fd, rtol=1.0e-6, atol=1.0e-6)
    # The m_b orientation Hessian is non-vacuous: a force-only geometric
    # tangent would leave a large residual on this state.
    f_force_only = f.copy()
    for entry in mpc_map.entries:
        f_force_only[entry.slave_theta_dofs] = 0.0
    K_force_only = mpc_map.geometric_tangent(u_nl, f_force_only).toarray()
    assert np.linalg.norm(K_geom - K_force_only) > 1.0e-6


def test_interp_downstream_rotation_dependency_refused_and_direct_retained() -> None:
    """Multi-master slave rotations are nonlinear and refuse downstream consumption;
    single-master direct slave rotations stay linear and admissible."""
    model, meta = _build_coupled_cantilever("interpolated")
    dof_manager = model.mesh.dof_manager
    slave_beam = meta["beam_nodes"][1]
    extra = 500
    model.add_node(extra, 0.5, 0.05, 0.0)
    ry_slave = int(dof_manager.get_node_dofs(slave_beam)[4])
    ry_extra = int(dof_manager.get_node_dofs(extra)[4])
    model.add_constraint_equation(
        terms=((ry_extra, 1.0), (ry_slave, -1.0)),
        rhs=0.0,
        source_id="downstream_interp_ry_eq",
        dependent_dof=ry_extra,
    )
    K0, _ = assemble_stiffness_matrix(model)
    zero = np.zeros(K0.shape[0], dtype=float)
    _, _, T, _, _, _ = build_constraint_transformation(K0, zero, model)
    with pytest.raises(ValueError, match="rotating slave"):
        build_nonlinear_rotating_mpc_map(model, T)

    # Direct single-master route: slave rotation stays linear, dependency remains supported.
    model_d, meta_d = _build_coupled_cantilever("eccentric")
    slave_beam_d = meta_d["beam_nodes"][1]
    model_d.add_node(extra, 0.5, 0.05, 0.0)
    ry_slave_d = int(dof_manager.get_node_dofs(slave_beam_d)[4])
    ry_extra_d = int(dof_manager.get_node_dofs(extra)[4])
    model_d.add_constraint_equation(
        terms=((ry_extra_d, 1.0), (ry_slave_d, -1.0)),
        rhs=0.0,
        source_id="downstream_direct_ry_eq",
        dependent_dof=ry_extra_d,
    )
    K0d, _ = assemble_stiffness_matrix(model_d)
    _, _, Td, _, _, _ = build_constraint_transformation(K0d, zero, model_d)
    mpc_map = build_nonlinear_rotating_mpc_map(model_d, Td)
    assert mpc_map is not None and mpc_map.active


def test_interp_negative_shape_weights_refused_at_map_build() -> None:
    """Mixed-sign weights admitted by the partition validator are refused on the mean route."""
    model, meta = _build_coupled_cantilever("interpolated")
    elem_id = 200
    old_elem = model.mesh.elements[elem_id]
    model.mesh.elements[elem_id] = InterpolatedBeamShellMPCElement(
        elem_id,
        old_elem.beam_node_id,
        old_elem.shell_node_ids,
        np.array([1.5, -0.5], dtype=float),
        eccentricity=old_elem.eccentricity,
    )
    K0, _ = assemble_stiffness_matrix(model)
    zero = np.zeros(K0.shape[0], dtype=float)
    _, _, T, _, _, _ = build_constraint_transformation(K0, zero, model)
    with pytest.raises(ValueError, match="nonnegative"):
        build_nonlinear_rotating_mpc_map(model, T)
