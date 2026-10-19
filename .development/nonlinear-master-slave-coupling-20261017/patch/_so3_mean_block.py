def _so3_weighted_mean(
    master_thetas,
    weights,
    label,
):
    # -*- coding: utf-8 -*-
    """Intrinsic weighted SO(3) mean with exact tangent derivatives.

    Returns ``(theta_m, (G_i, ...))`` where ``R(theta_m)`` solves the
    Karcher-type condition ``sum_i w_i Log(R_m^T R_i) = 0`` and
    ``G_i = dtheta_m/dtheta_i`` is its exact differential in additive
    rotation-vector coordinates:

        Ghat_i = R_m B^{-1} w_i J_l(psi_i)^{-1} R_m^T      (spatial),
        G_i    = J_l(theta_m)^{-1} Ghat_i J_l(theta_i),
        B      = sum_i w_i J_l(psi_i)^{-1},  psi_i = Log(R_m^T R_i).

    The spatial blocks satisfy ``sum_i Ghat_i = I``, which makes the mean
    left-equivariant: for a common superposed rotation ``Q``,
    ``mean(Q R_i, w) = Q mean(R_i, w)``, and the parameter tangents satisfy
    the differential rigid-spin identity
    ``sum_i G_i J_l(theta_i)^{-1} = J_l(theta_m)^{-1}``, the covector
    counterpart of physical wrench preservation.

    Refusal boundary (adopted contract): weights must be nonnegative and
    form a partition of unity; the fixed-point iteration must converge from
    the linear average with every master inside the principal chart of the
    mean (``|psi_i| < pi``), and ``B`` must remain nonsingular.  Ambiguous,
    chart-crossing and singular cases are refused explicitly instead of
    silently selecting a branch.  A single master and exactly identical
    master rotations are exact short-circuits, so the direct route and the
    identical-rotation limit reproduce the legacy map bit-for-bit.
    """
    thetas = [np.asarray(t, dtype=float).reshape(3).copy() for t in master_thetas]
    ws = [float(w) for w in weights]
    if not thetas:
        raise ValueError(f"{label}: SO(3) mean requires at least one master")
    if any(w < 0.0 for w in ws):
        raise ValueError(
            f"{label}: the intrinsic SO(3) mean on the active rotating-offset "
            f"route requires nonnegative weights; got {ws}"
        )
    weight_sum = float(sum(ws))
    if abs(weight_sum - 1.0) > 1.0e-8:
        raise ValueError(
            f"{label}: the intrinsic SO(3) mean requires weights forming a "
            f"partition of unity; got sum {weight_sum!r}"
        )
    if len(thetas) == 1:
        return thetas[0], (np.eye(3),)
    first = thetas[0]
    if all(np.array_equal(t, first) for t in thetas[1:]):
        return first.copy(), tuple(w * np.eye(3) for w in ws)

    theta_m = np.zeros(3, dtype=float)
    for t, w in zip(thetas, ws):
        theta_m += w * t
    R_m = rotation_matrix_from_vector(theta_m)
    psis = []
    converged = False
    for _ in range(100):
        psis = [
            rotation_vector_from_matrix(R_m.T @ rotation_matrix_from_vector(t))
            for t in thetas
        ]
        f = np.zeros(3, dtype=float)
        for psi, w in zip(psis, ws):
            f += w * psi
        if float(np.linalg.norm(f)) <= 1.0e-14:
            converged = True
            break
        if float(np.linalg.norm(f)) >= np.pi:
            break
        R_m = R_m @ rotation_matrix_from_vector(f)
    if not converged:
        raise ValueError(
            f"{label}: intrinsic SO(3) mean did not converge in the local "
            "convex neighborhood; the master rotations are ambiguous or "
            "outside the supported chart"
        )
    for psi in psis:
        if float(np.linalg.norm(psi)) >= float(np.pi) * (1.0 - 1.0e-6):
            raise ValueError(
                f"{label}: intrinsic SO(3) mean lies on the chart boundary "
                f"to a master (|psi|={float(np.linalg.norm(psi))}); "
                "ambiguous mean refused"
            )
    theta_m = rotation_vector_from_matrix(R_m)
    A = [_rotation_left_jacobian_inverse(psi) for psi in psis]
    B = np.zeros((3, 3), dtype=float)
    for a, w in zip(A, ws):
        B += w * a
    if abs(float(np.linalg.det(B))) <= 1.0e-10:
        raise ValueError(
            f"{label}: intrinsic SO(3) mean tangent operator is singular; "
            "ambiguous mean refused"
        )
    B_inv = np.linalg.inv(B)
    Jl_m_inv = _rotation_left_jacobian_inverse(theta_m)
    G = []
    for t, a, w in zip(thetas, A, ws):
        Ghat = R_m @ (B_inv @ (w * a)) @ R_m.T
        Jl_i = _rotation_right_jacobian(t).T
        G.append(Jl_m_inv @ Ghat @ Jl_i)
    return theta_m, tuple(G)
