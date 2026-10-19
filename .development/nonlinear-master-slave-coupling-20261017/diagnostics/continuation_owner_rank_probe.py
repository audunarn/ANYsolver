"""Replay one original DC path and inspect dimensionless constrained rank.

Diagnostic only; no altered solver, control path or material histories. Numerical
execution is exclusively through the task harness. Scalar records stream before
the next stage so timeout evidence remains useful.
"""
from __future__ import annotations
import copy
import inspect
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_nonlinear_beam_shell_slice3_continuation import _dc_case, _equilibrium_oracle
from assessment_support import identical
import anysolver.nonlinear_static as ns


def report_rank(label, matrix, rhs, load_factor, reference):
    """Scale mechanics by L=1m, rotations=1rad, load by current load scale.

    Equilibrating the dimensionless matrix subsequently avoids reporting a raw
    mixed-unit condition number. Row factors are also applied to the residual,
    so its projection uses the actual correspondingly scaled left vector.
    """
    A = matrix.toarray() if hasattr(matrix, "toarray") else matrix.copy()
    dr = np.r_[np.full(A.shape[0]-1, 1/max(reference, 1)), 1.0]
    dc = np.r_[np.ones(A.shape[1]-1), max(abs(load_factor), 1)]
    B = dr[:, None] * A * dc[None, :]
    for _ in range(12):
        rs = 1 / np.sqrt(np.maximum(np.max(abs(B), axis=1), 1e-300))
        cs = 1 / np.sqrt(np.maximum(np.max(abs(B), axis=0), 1e-300))
        B = rs[:, None] * B * cs[None, :]
        dr *= rs
        dc *= cs
    U, s, Vt = np.linalg.svd(B)
    b = dr * rhs
    tangent = np.linalg.solve(A, np.r_[np.zeros(A.shape[0]-1), 1.0])
    record = dict(label=label, size=A.shape[0], smallest_singular=float(s[-1]),
                  largest_singular=float(s[0]), singular_ratio=float(s[-1]/s[0]),
                  scaled_residual_norm=float(np.linalg.norm(b)),
                  left_smallest_residual_projection=float(U[:, -1] @ b),
                  relative_left_projection=float(abs(U[:, -1] @ b)/max(np.linalg.norm(b), 1e-300)),
                  tangent_q_norm_per_control_m=float(np.linalg.norm(tangent[:-1])),
                  tangent_lam_per_control_m=float(tangent[-1]),
                  backward_linear_tangent_error=float(np.linalg.norm(A @ tangent - np.r_[np.zeros(A.shape[0]-1), 1.0])))
    print(json.dumps(record), flush=True)


def main():
    last = {}
    real_factorize = ns.factorize

    class Handle:
        def __init__(self, handle, matrix):
            self.handle, self.matrix = handle, matrix

        def solve(self, rhs):
            delta = self.handle.solve(rhs)
            frame = inspect.currentframe().f_back
            try:
                for _ in range(6):
                    if frame is None or frame.f_code.co_name == "_solve_static_displacement_control":
                        break
                    frame = frame.f_back
                if frame is not None and frame.f_code.co_name == "_solve_static_displacement_control":
                    c = frame.f_locals
                    last.update(matrix=self.matrix.copy(), rhs=np.asarray(rhs).copy(),
                                q=c["q"].copy(), lam=float(c["lam"]),
                                target=float(c["target"]), reference=float(c["reference"]),
                                iteration=int(c["iteration"]), step=int(c["step_index"]))
            finally:
                del frame
            return delta

    def factorize(matrix, *a, **kw):
        return Handle(real_factorize(matrix, *a, **kw), matrix)

    ns.factorize = factorize
    try:
        case = _dc_case("direct", -.20, 12, emit_restart_checkpoint=False)
    finally:
        ns.factorize = real_factorize
    result = case["result"]
    print(json.dumps(dict(kind="unaltered_original_path", status=result.status,
                          reason=result.stop_reason, achieved=result.steps[-1].control_value,
                          load_factor=result.load_factor,
                          accepted=[dict(control=s.control_value, lam=s.load_factor,
                                         alpha=s.max_equivalent_plastic_strain)
                                    for s in result.steps])), flush=True)
    report_rank(dict(kind="last_failed_corrector", target=last["target"],
                     iteration=last["iteration"], step=last["step"]),
                last["matrix"], last["rhs"], last["lam"], last["reference"])
    oracle = _equilibrium_oracle(case)
    mapping, F = oracle["mpc_map"], oracle["F_prop"]
    row = np.zeros_like(F)
    row[case["model"].mesh.dof_manager.get_node_dofs(case["probe"])[2]] = 1
    for index in (8, 9, len(result.snapshots)-2, len(result.snapshots)-1):
        s = result.snapshots[index]
        # At an accepted state, zero constitutive increment may choose an
        # unloading generalized derivative. Compare it to the actual arriving
        # increment using the preceding accepted history as its immutable base.
        for mode in ("committed_zero_increment", "arriving_increment"):
            states = copy.deepcopy(dict((s if mode == "committed_zero_increment"
                                         else result.snapshots[index-1]).element_states))
            before = copy.deepcopy(states)
            u = np.asarray(s.displacements).copy()
            fint, K, trial = ns._assemble_nonlinear_system(
                case["model"], u, states, 5, tangent=True,
                kinematics="corotational", corotational_tangent="work_conjugate")
            assert identical(states, before), "rank replay mutated its input history"
            residual = mapping.reduce_force(u, s.load_factor*F - fint)
            Kred = mapping.reduce_tangent(u, K, fint-s.load_factor*F, None).toarray()
            fred = mapping.reduce_force(u, F)
            rowred = np.asarray(row @ mapping.jacobian(u)).reshape(-1)
            A = np.block([[Kred, -fred[:, None]], [rowred[None, :], np.zeros((1, 1))]])
            reference = max(np.linalg.norm(mapping.reduce_force(u, max(abs(s.load_factor), 1)*F)), 1)
            report_rank(dict(kind=mode, index=index, control=s.control_value,
                             residual_norm=float(np.linalg.norm(residual))),
                        A, np.r_[residual, 0.0], s.load_factor, reference)


if __name__ == "__main__":
    main()
