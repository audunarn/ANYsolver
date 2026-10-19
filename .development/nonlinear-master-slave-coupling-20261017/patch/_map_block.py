class NonlinearRotatingMPCEntry:
    """One finite-rotation eccentric beam-shell coupling descriptor."""

    def __init__(
        self,
        *,
        element_id: int,
        slave_u_dofs: Tuple[int, int, int],
        slave_theta_dofs: Tuple[int, int, int],
        masters: Tuple[Tuple[Tuple[int, ...], Tuple[int, ...], float], ...],
        eccentricity: np.ndarray,
        theta_proj: Any,
        label_prefix: str,
        master_theta_projs: Tuple[Any, ...] = (),
    ) -> None:
        self.element_id = int(element_id)
        self.slave_u_dofs = np.asarray(slave_u_dofs, dtype=np.intp)
        self.slave_theta_dofs = np.asarray(slave_theta_dofs, dtype=np.intp)
        self.masters = tuple(
            (
                np.asarray(m_u, dtype=np.intp),
                np.asarray(m_theta, dtype=np.intp),
                float(w),
            )
            for m_u, m_theta, w in masters
        )
        self.eccentricity = np.asarray(eccentricity, dtype=float).reshape(3).copy()
        self.r_skew = _skew(self.eccentricity)
        self.theta_proj = theta_proj.tocsr()
        self.label_prefix = str(label_prefix)
        self.master_theta_projs = tuple(p.tocsr() for p in master_theta_projs)

    def master_rotation(self, u: np.ndarray) -> np.ndarray:
        """Linear average ``theta_lin = sum_i w_i theta_i`` (legacy relation)."""
        theta_bar = np.zeros(3, dtype=float)
        for _m_u, m_theta, w in self.masters:
            theta_bar += w * u[m_theta]
        return theta_bar

    def master_rotations(self, u: np.ndarray) -> list:
        """Individual master rotation vectors ``theta_i``."""
        return [
            np.asarray(u[m_theta], dtype=float).reshape(3).copy()
            for _m_u, m_theta, _w in self.masters
        ]

    def mean_state(self, u: np.ndarray) -> Tuple[np.ndarray, Tuple[np.ndarray, ...]]:
        """Intrinsic weighted SO(3) mean of the master rotations and tangents."""
        thetas = self.master_rotations(u)
        weights = [w for _m_u, _m_theta, w in self.masters]
        return _so3_weighted_mean(thetas, weights, self.label_prefix)

    def master_translation(self, u: np.ndarray) -> np.ndarray:
        u_bar = np.zeros(3, dtype=float)
        for m_u, _m_theta, w in self.masters:
            u_bar += w * u[m_u]
        return u_bar


class NonlinearRotatingMPCMap:
    """State-dependent master-slave kinematic map for rotating eccentricities.

    Given the reference linear constraint transformation ``T_linear`` (which
    encodes ``u_b,lin = sum_i w_i u_{s,i} + theta_lin x r_0`` and
    ``theta_b = theta_lin := sum_i w_i theta_{s,i}``), the nonlinear
    kinematic map replaces the linearized lever-arm offset and the
    non-objective averaged orientation with the intrinsic weighted SO(3)
    mean ``R_m = mean(R_i, w_i)`` on the active rotating-offset route:

        u_b(q)     = sum_i w_i u_{s,i}(q)
                     + (R_m(q) - I) r_0 - theta_lin(q) x r_0
        theta_b(q) = theta_m(q) = Log(R_m(q))

    Under a common superposed rigid rotation ``Q`` the weighted deformed
    attachment point and the slave orientation transform equivariantly,
    ``x_b -> Q x_b`` and ``R_b -> Q R_b`` (adopted rigid-spin contract),
    while the direct single-master route and the identical-rotation limit
    reproduce the legacy map exactly.  Zero Lagrange multipliers are used.
    """

    def __init__(
        self,
        T_linear: Any,
        entries: Tuple[NonlinearRotatingMPCEntry, ...],
    ) -> None:
        from scipy import sparse

        self.T_linear = sparse.csr_matrix(T_linear, dtype=float)
        self.entries = tuple(entries)
        self.total_dofs = int(self.T_linear.shape[0])
        self.n_red = int(self.T_linear.shape[1])

    @property
    def active(self) -> bool:
        return bool(self.entries)

    def _slave_corrections(self, u: np.ndarray) -> list:
        """Per-entry slave translation/rotation corrections ``(d_u, d_theta)``.

        Both corrections are evaluated from the supplied state only: master
        rotations are never corrected by the map, so the result is a proper
        function of the input state and forward/inverse application is
        order-independent across chained entries.
        """
        corrections = []
        for entry in self.entries:
            theta_lin = entry.master_rotation(u)
            theta_m, _G = entry.mean_state(u)
            d_theta = theta_m - theta_lin
            d_u = _nonlinear_minus_linear_rotation(theta_m) @ entry.eccentricity
            d_u = d_u + np.cross(d_theta, entry.eccentricity)
            corrections.append((entry, d_u, d_theta))
        return corrections

    def apply_kinematics(self, u_linear: np.ndarray) -> np.ndarray:
        """Map a linear MPC displacement state ``u_lin`` to the nonlinear manifold."""
        u = np.asarray(u_linear, dtype=float).reshape(-1).copy()
        if not self.entries:
            return u
        for entry, d_u, d_theta in self._slave_corrections(u):
            u[entry.slave_u_dofs] += d_u
            u[entry.slave_theta_dofs] += d_theta
        return u

    def to_linear_displacement(self, u_nonlinear: np.ndarray) -> np.ndarray:
        """Exact inverse diffeomorphism mapping ``u`` back to linear MPC coordinates."""
        u_lin = np.asarray(u_nonlinear, dtype=float).reshape(-1).copy()
        if not self.entries:
            return u_lin
        for entry, d_u, d_theta in self._slave_corrections(u_lin):
            u_lin[entry.slave_u_dofs] -= d_u
            u_lin[entry.slave_theta_dofs] -= d_theta
        return u_lin

    def jacobian(self, u_current: np.ndarray) -> Any:
        """Return the state-dependent kinematic Jacobian ``J(u) = du / dq``."""
        from scipy import sparse

        if not self.entries:
            return self.T_linear
        u = np.asarray(u_current, dtype=float).reshape(-1)
        row_blocks = []
        col_blocks = []
        data_blocks = []
        for entry in self.entries:
            if entry.theta_proj.nnz == 0 and all(
                p.nnz == 0 for p in entry.master_theta_projs
            ):
                continue
            theta_m, G_list = entry.mean_state(u)
            A = rotating_mpc_lever_arm_jacobian(theta_m, entry.eccentricity)
            # M_proj = dtheta_m/dq = sum_i G_i dtheta_i/dq
            M = None
            for G, P in zip(G_list, entry.master_theta_projs):
                if P.nnz == 0:
                    continue
                term = sparse.csr_matrix(G) @ P
                M = term if M is None else (M + term)
            if M is None:
                continue
            # slave translations: A @ M + skew(r_0) @ theta_proj
            C_u = sparse.csr_matrix(A) @ M + sparse.csr_matrix(entry.r_skew) @ entry.theta_proj
            # slave rotations: M - theta_proj
            C_theta = M - entry.theta_proj
            for rows, block in ((entry.slave_u_dofs, C_u), (entry.slave_theta_dofs, C_theta)):
                coo = block.tocoo()
                if coo.nnz and np.any(coo.data):
                    row_blocks.append(np.asarray(rows)[coo.row])
                    col_blocks.append(coo.col)
                    data_blocks.append(coo.data)
        if not data_blocks:
            return self.T_linear
        delta_T = sparse.coo_matrix(
            (
                np.concatenate(data_blocks),
                (np.concatenate(row_blocks), np.concatenate(col_blocks)),
            ),
            shape=(self.total_dofs, self.n_red),
            dtype=float,
        ).tocsr()
        return (self.T_linear + delta_T).tocsr()

    def reduce_force(self, u_current: np.ndarray, full_force: np.ndarray) -> np.ndarray:
        """Return ``J(u)^T full_force`` without materializing ``J(u)``."""
        f = np.asarray(full_force, dtype=float).reshape(-1)
        if not self.entries:
            return np.asarray(self.T_linear.T @ f, dtype=float).reshape(-1)
        u = np.asarray(u_current, dtype=float).reshape(-1)
        f_mod = f.copy()
        for entry in self.entries:
            f_b = f[entry.slave_u_dofs]
            m_b = f[entry.slave_theta_dofs]
            if float(np.linalg.norm(f_b)) <= 1.0e-30 and float(np.linalg.norm(m_b)) <= 1.0e-30:
                continue
            theta_m, G_list = entry.mean_state(u)
            A = rotating_mpc_lever_arm_jacobian(theta_m, entry.eccentricity)
            v = A.T @ f_b + m_b
            const = entry.r_skew.T @ f_b - m_b
            for (_m_u, m_theta, w), G in zip(entry.masters, G_list):
                f_mod[m_theta] += G.T @ v + w * const
        return np.asarray(self.T_linear.T @ f_mod, dtype=float).reshape(-1)

    def geometric_tangent(
        self,
        u_current: np.ndarray,
        full_imbalance: np.ndarray,
    ) -> Any:
        """Return ``K_mpc,geom(u, F_int - F_ext) = d(J^T F)/dq`` (F frozen).

        The complete second derivative of the slave correction is included:
        second derivatives of the intrinsic mean and of the slave
        orientation contracted with the full slave rotation imbalance
        ``m_b``, and offset-translation derivatives contracted with ``f_b``.
        It is evaluated by central finite differences of the exact
        per-master covector correction of :meth:`reduce_force`, so it stays
        consistent with the forward map by construction.
        """
        from scipy import sparse

        if not self.entries or self.n_red == 0:
            return sparse.csr_matrix((self.n_red, self.n_red), dtype=float)
        u = np.asarray(u_current, dtype=float).reshape(-1)
        imbalance = np.asarray(full_imbalance, dtype=float).reshape(-1)
        terms = []
        h = 1.0e-6
        for entry in self.entries:
            projs = entry.master_theta_projs
            if all(p.nnz == 0 for p in projs):
                continue
            f_b = imbalance[entry.slave_u_dofs]
            m_b = imbalance[entry.slave_theta_dofs]
            if float(np.linalg.norm(f_b)) <= 1.0e-30 and float(np.linalg.norm(m_b)) <= 1.0e-30:
                continue
            thetas = entry.master_rotations(u)
            weights = [w for _m_u, _m_theta, w in entry.masters]

            def covectors(state_thetas):
                theta_m, G_list = _so3_weighted_mean(
                    state_thetas, weights, entry.label_prefix
                )
                A = rotating_mpc_lever_arm_jacobian(theta_m, entry.eccentricity)
                vv = A.T @ f_b + m_b
                return [G.T @ vv for G in G_list]

            n_m = len(projs)
            D = [[np.zeros((3, 3), dtype=float) for _ in range(n_m)] for _ in range(n_m)]
            for j in range(n_m):
                for c in range(3):
                    plus = [t.copy() for t in thetas]
                    minus = [t.copy() for t in thetas]
                    plus[j][c] += h
                    minus[j][c] -= h
                    cp = covectors(plus)
                    cm = covectors(minus)
                    for i in range(n_m):
                        D[i][j][:, c] = (cp[i] - cm[i]) / (2.0 * h)
            for i in range(n_m):
                for j in range(n_m):
                    if not np.any(D[i][j]):
                        continue
                    term = projs[i].T @ sparse.csr_matrix(D[i][j]) @ projs[j]
                    if term.nnz:
                        terms.append(term)
        if not terms:
            return sparse.csr_matrix((self.n_red, self.n_red), dtype=float)
        total = terms[0]
        for term in terms[1:]:
            total = total + term
        total = (total + total.T).tocsr()
        return 0.5 * total

    def reduce_tangent(
        self,
        u_current: np.ndarray,
        K_T: Any,
        full_imbalance: Optional[np.ndarray] = None,
        K_ext: Optional[Any] = None,
    ) -> Any:
        """Return ``J(u)^T (K_T - K_ext) J(u) + K_mpc,geom(u, full_imbalance)``."""
        J = self.jacobian(u_current)
        K_red = (J.T @ K_T @ J).tocsr()
        if K_ext is not None and getattr(K_ext, "nnz", 0):
            K_red = (K_red - (J.T @ K_ext @ J)).tocsr()
        if full_imbalance is not None:
            K_geom = self.geometric_tangent(u_current, full_imbalance)
            if K_geom.nnz:
                K_red = (K_red + K_geom).tocsr()
        return K_red

    def transfer_slave_imbalance_to_masters(
        self,
        u_current: np.ndarray,
        full_imbalance: np.ndarray,
    ) -> np.ndarray:
        """Transfer slave forces/moments to master shell DOFs for support reactions.

        The slave force ``f_b`` is distributed with the linear weights to the
        master translations; the mean-chart slave moment covector
        ``m_b + A(theta_m)^T f_b`` is distributed through the transposed mean
        tangents ``G_i^T`` to the master rotation covectors.  This is the
        exact adjoint of the nonlinear slave orientation map, so the total
        physical spatial wrench is preserved (the old common-covector
        shortcut left a moment defect ``D^T (m_b + A^T f_b)``).
        """
        imbalance = np.asarray(full_imbalance, dtype=float).reshape(-1).copy()
        if not self.entries:
            return imbalance
        u = np.asarray(u_current, dtype=float).reshape(-1)
        for entry in self.entries:
            f_b = imbalance[entry.slave_u_dofs].copy()
            m_b = imbalance[entry.slave_theta_dofs].copy()
            if float(np.linalg.norm(f_b)) <= 1.0e-30 and float(np.linalg.norm(m_b)) <= 1.0e-30:
                imbalance[entry.slave_u_dofs] = 0.0
                imbalance[entry.slave_theta_dofs] = 0.0
                continue
            theta_m, G_list = entry.mean_state(u)
            A = rotating_mpc_lever_arm_jacobian(theta_m, entry.eccentricity)
            moment_covector = m_b + A.T @ f_b
            for (m_u, m_theta, w), G in zip(entry.masters, G_list):
                imbalance[m_u] += w * f_b
                imbalance[m_theta] += G.T @ moment_covector
            imbalance[entry.slave_u_dofs] = 0.0
            imbalance[entry.slave_theta_dofs] = 0.0
        return imbalance


def has_nonlinear_rotating_mpc(model: "FEModel") -> bool:
    """Return True if ``model`` contains active rotating-arm beam-shell MPCs."""
    mesh = getattr(model, "mesh", None)
    elements = getattr(mesh, "elements", None)
    if not elements:
        return False
    for element in elements.values():
        getter = getattr(element, "get_nonlinear_mpc_descriptor", None)
        if callable(getter) and getter(mesh) is not None:
            return True
    return False


def _reject_downstream_rotating_slave_translation_dependencies(
    model: "FEModel",
    entries: Tuple[NonlinearRotatingMPCEntry, ...],
) -> None:
    """Fail closed when an admitted affine equation consumes a rotating slave DOF.

    The rotating map corrects each descriptor's own slave translations, and
    the intrinsic SO(3) mean makes the slave rotation of every multi-master
    coupling a nonlinear function of the master rotations.  Any other
    admitted affine equation that uses one of those DOFs as a nonzero
    master would silently retain the linearized value in the returned
    physical displacement, so such compositions are refused before
    constitutive activation instead of being solved on the wrong manifold.
    The check uses the actual normalized audit equations, including their
    coefficient filtering.  Ordinary linear chains without a rotating
    descriptor and upstream shell row ties remain supported; single-master
    direct slave rotations stay linear under the map and are not
    restricted.  A currently identical multi-master state does not admit a
    dependency that becomes nonlinear later.
    """
    rotating_slave_translations: set = set()
    nonlinear_slave_rotations: set = set()
    for entry in entries:
        rotating_slave_translations.update(int(d) for d in entry.slave_u_dofs)
        if len(entry.masters) > 1:
            nonlinear_slave_rotations.update(int(d) for d in entry.slave_theta_dofs)
    blocked = rotating_slave_translations | nonlinear_slave_rotations
    if not blocked:
        return
    from .constraint_audit import require_valid_constraints

    report = require_valid_constraints(model)
    for equation in report.equations:
        if str(equation.kind) == "support":
            continue
        dependent = int(equation.dependent_dof)
        for dof, coefficient in equation.coefficients:
            master = int(dof)
            if master == dependent or float(coefficient) == 0.0:
                continue
            if master in blocked:
                raise ValueError(
                    f"Rotating-MPC route: affine equation '{equation.origin}' "
                    f"(dependent DOF {dependent}) uses rotating slave "
                    f"DOF {master} as a master. Downstream dependencies on "
                    "rotating slave translations, or on the nonlinearly "
                    "interpolated slave rotations of multi-master couplings, "
                    "are not supported; remove the downstream equation or the "
                    "rotating coupling."
                )


def build_nonlinear_rotating_mpc_map(
    model: "FEModel",
    T_linear: Any,
) -> Optional[NonlinearRotatingMPCMap]:
    """Build a :class:`NonlinearRotatingMPCMap` if rotating-arm MPCs are present."""
    from scipy import sparse

    mesh = getattr(model, "mesh", None)
    elements = getattr(mesh, "elements", None)
    if not elements:
        return None
    T_csr = sparse.csr_matrix(T_linear, dtype=float)
    entries = []
    for _elem_id, element in sorted(elements.items(), key=lambda item: int(item[0])):
        getter = getattr(element, "get_nonlinear_mpc_descriptor", None)
        if not callable(getter):
            continue
        desc = getter(mesh)
        if desc is None:
            continue
        masters = tuple(desc["masters"])
        if len(masters) > 1 and any(w < 0.0 for _m_u, _m_theta, w in masters):
            raise ValueError(
                f"{desc['label_prefix']}: the intrinsic SO(3) mean on the "
                "active rotating-offset route requires nonnegative shape "
                f"weights; got {[w for _m_u, _m_theta, w in masters]}"
            )
        slave_theta = tuple(int(d) for d in desc["slave_theta_dofs"])
        theta_proj = T_csr[list(slave_theta), :]
        master_theta_projs = tuple(
            T_csr[[int(d) for d in m_theta], :]
            for _m_u, m_theta, _w in masters
        )
        entries.append(
            NonlinearRotatingMPCEntry(
                element_id=int(desc["element_id"]),
                slave_u_dofs=tuple(int(d) for d in desc["slave_u_dofs"]),
                slave_theta_dofs=slave_theta,
                masters=masters,
                eccentricity=np.asarray(desc["eccentricity"], dtype=float),
                theta_proj=theta_proj,
                label_prefix=str(desc["label_prefix"]),
                master_theta_projs=master_theta_projs,
            )
        )
    if not entries:
        return None
    _reject_downstream_rotating_slave_translation_dependencies(model, tuple(entries))
    return NonlinearRotatingMPCMap(T_csr, tuple(entries))
