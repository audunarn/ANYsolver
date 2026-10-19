import importlib.util
import numpy as np

_spec = importlib.util.spec_from_file_location(
    "coupling_tests",
    "tests/test_nonlinear_beam_shell_coupling.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_interp_map_with_distinct_master_rotations = _mod._interp_map_with_distinct_master_rotations
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.corotational import (
    _so3_weighted_mean,
    rotation_matrix_from_vector,
    rotation_vector_from_matrix,
)

model, meta, T, u0, q, mpc_map, u_lin = _interp_map_with_distinct_master_rotations()
u_nl = mpc_map.apply_kinematics(u_lin)

entry = mpc_map.entries[0]
thetas = entry.master_rotations(u_nl)
weights = [w for _u, _t, w in entry.masters]
theta_m, G = _so3_weighted_mean(thetas, weights, entry.label_prefix)
print("masters:", thetas)
print("weights:", weights)
print("theta_m:", theta_m)

# equivariance of the mean itself
psi = np.array([0.23, -0.31, 0.42])
Q = rotation_matrix_from_vector(psi)
spun = [rotation_vector_from_matrix(Q @ rotation_matrix_from_vector(t)) for t in thetas]
theta_m_spun, G_spun = _so3_weighted_mean(spun, weights, "dbg")
err = np.linalg.norm(rotation_matrix_from_vector(theta_m_spun) - Q @ rotation_matrix_from_vector(theta_m))
print("mean equivariance err:", err)

# check the mean condition at the returned theta_m
R_m = rotation_matrix_from_vector(theta_m)
cond = np.zeros(3)
for t, w in zip(thetas, weights):
    cond += w * rotation_vector_from_matrix(R_m.T @ rotation_matrix_from_vector(t))
print("mean condition residual:", np.linalg.norm(cond))

# FD of apply_kinematics vs jacobian
n_red = int(T.shape[1])
J = mpc_map.jacobian(u_nl).toarray()
eps = 1e-7
maxerr = 0.0
for j in range(n_red):
    dq = np.zeros(n_red); dq[j] = eps
    up = mpc_map.apply_kinematics(np.asarray(T @ (q + dq) + u0, dtype=float).reshape(-1))
    um = mpc_map.apply_kinematics(np.asarray(T @ (q - dq) + u0, dtype=float).reshape(-1))
    fd = (up - um) / (2 * eps)
    maxerr = max(maxerr, float(np.linalg.norm(fd - J[:, j])))
print("J vs FD max col err:", maxerr)

# check slave rows explicitly: which rows mismatch
for j in (0, 1, 2, 3):
    dq = np.zeros(n_red); dq[j] = eps
    up = mpc_map.apply_kinematics(np.asarray(T @ (q + dq) + u0, dtype=float).reshape(-1))
    um = mpc_map.apply_kinematics(np.asarray(T @ (q - dq) + u0, dtype=float).reshape(-1))
    fd = (up - um) / (2 * eps)
    diff = np.abs(fd - J[:, j])
    bad = np.where(diff > 1e-6)[0]
    print("col", j, "bad rows:", bad[:10], "max diff:", diff.max() if len(diff) else 0)
