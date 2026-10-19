"""Probe: current-source direct full-target DC stop diagnosis (final repair).

One discriminating instrumented run, no sweeps. Runs the EP edge coupling to
uz=-0.20 (12 steps, 40 iterations, 1e-8) on the CURRENT source and records,
per augmented solve (one per Newton iteration):

  - reduced residual norm ||rhs[:-1]|| and control constraint rhs[-1]
  - step sizes ||delta[:-1]|| and load-factor increment delta[-1]
  - residual line-search trial assemblies since the previous solve
    (tangent=False assemblies are line-search trials; the main loop uses
    tangent=True)

plus the per-accepted step records and final status/stop info. This is the
current per-accepted progress/iteration evidence required by
SLICE3_FINAL_REPAIR.md; the earlier probes predate the residual line search.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tests"
    ),
)

import numpy as np

import anysolver.nonlinear_static as nonlinear_static
from test_nonlinear_beam_shell_slice3_continuation import (  # noqa: E402
    _add_tip_load,
    _build_ep_model,
)
from anysolver import DisplacementControl, solve_static_nonlinear  # noqa: E402


def main() -> None:
    coupling = sys.argv[1] if len(sys.argv) > 1 else "direct"
    real_factorize = nonlinear_static.factorize
    real_assemble = nonlinear_static._assemble_nonlinear_system
    trials = {"n": 0}
    iter_count = {"n": 0}

    def counting_assemble(*args, **kwargs):
        if not bool(kwargs.get("tangent", True)):
            trials["n"] += 1
        return real_assemble(*args, **kwargs)

    class _ProbingHandle:
        def __init__(self, handle):
            self._handle = handle

        def solve(self, rhs):
            rhs = np.asarray(rhs, dtype=float).reshape(-1)
            delta = np.asarray(self._handle.solve(rhs), dtype=float).reshape(-1)
            iter_count["n"] += 1
            print(
                json.dumps(
                    {
                        "stage": "solve",
                        "n": iter_count["n"],
                        "residual_rhs": float(np.linalg.norm(rhs[:-1])),
                        "constraint_rhs": float(rhs[-1]),
                        "dq_norm": float(np.linalg.norm(delta[:-1])),
                        "dlam": float(delta[-1]),
                        "line_search_trials_prev": trials["n"],
                    }
                ),
                flush=True,
            )
            trials["n"] = 0
            return delta

    def probing_factorize(matrix, matrix_class, signature=None, **kwargs):
        handle = real_factorize(matrix, matrix_class, signature=signature, **kwargs)
        return _ProbingHandle(handle)

    nonlinear_static.factorize = probing_factorize
    nonlinear_static._assemble_nonlinear_system = counting_assemble
    try:
        model, load, probe, grid = _build_ep_model(coupling)
        _add_tip_load(model, load, grid)
        result = solve_static_nonlinear(
            model,
            load,
            control="displacement",
            displacement_control=DisplacementControl(
                node_id=probe, dof="uz", target_displacement=-0.20
            ),
            kinematics="corotational",
            num_steps=12,
            max_iterations=40,
            tolerance=1.0e-8,
        )
        dofs = model.mesh.dof_manager.get_node_dofs(probe)
        uz = float(np.asarray(result.displacements)[dofs[2]])
        summary = {
            "stage": "terminal",
            "coupling": coupling,
            "status": result.status,
            "stop_reason": result.info.get("stop_reason"),
            "failure_reason": result.info.get("failure_reason"),
            "converged": result.converged,
            "load_factor": result.load_factor,
            "uz_probe": uz,
            "total_newton_iterations": result.info.get("total_newton_iterations"),
            "control_attempts": result.info.get("control_attempts"),
            "control_cutbacks": result.info.get("control_cutbacks"),
            "control_line_search_reductions": result.info.get(
                "control_line_search_reductions"
            ),
            "steps": [
                {
                    "step": s.step_index,
                    "lam": s.load_factor,
                    "iters": s.iterations,
                    "res": s.residual_norm,
                    "ctrl": s.control_value,
                    "eps_p": s.max_equivalent_plastic_strain,
                }
                for s in result.steps
            ],
        }
        print(json.dumps(summary), flush=True)
    finally:
        nonlinear_static.factorize = real_factorize
        nonlinear_static._assemble_nonlinear_system = real_assemble


if __name__ == "__main__":
    main()
