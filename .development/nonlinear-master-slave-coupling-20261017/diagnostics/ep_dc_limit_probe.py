"""Probe: why do the EP DC runs to -0.20 stop at limit?

Prints, per coupling, the stop reason, achieved control value, and per-step
history (control, iterations, residual, load factor) for the 12-step run to
-0.20 and the 6-step run to -0.10, plus the resumed 6-step run.
"""
from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tests"))

import numpy as np

from test_nonlinear_beam_shell_slice3_continuation import (  # noqa: E402
    _add_tip_load,
    _build_ep_model,
)
from anysolver import DisplacementControl, solve_static_nonlinear  # noqa: E402


def run_case(coupling, target, num_steps, initial=None):
    model, load, probe, grid = _build_ep_model(coupling)
    _add_tip_load(model, load, grid)
    kwargs = {}
    if initial is not None:
        kwargs = {
            "initial_displacements": np.array(initial[0], dtype=float, copy=True),
            "initial_element_states": copy.deepcopy(initial[1]),
            "equilibrate_initial_state": False,
        }
    result = solve_static_nonlinear(
        model, load, control="displacement",
        displacement_control=DisplacementControl(
            node_id=probe, dof="uz", target_displacement=target
        ),
        kinematics="corotational", num_steps=num_steps,
        max_iterations=40, tolerance=1.0e-8, **kwargs,
    )
    dofs = model.mesh.dof_manager.get_node_dofs(probe)
    uz = float(np.asarray(result.displacements)[dofs[2]])
    return {
        "coupling": coupling, "target": target, "num_steps": num_steps,
        "restarted": initial is not None,
        "status": result.status,
        "stop_reason": result.info.get("stop_reason"),
        "failure_reason": result.info.get("failure_reason"),
        "status_category": result.info.get("status_category"),
        "converged": result.converged,
        "load_factor": result.load_factor,
        "uz_probe": uz,
        "control_error": abs(uz - target),
        "total_newton_iterations": result.info.get("total_newton_iterations"),
        "corotational_tangent": result.info.get("corotational_tangent"),
        "steps": [
            {
                "step": s.step_index, "lam": s.load_factor,
                "iters": s.iterations, "res": s.residual_norm,
                "ctrl": s.control_value,
                "eps_p": s.max_equivalent_plastic_strain,
            }
            for s in result.steps
        ],
    }


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "full"
    out = []
    if which in ("full", "all"):
        for coupling in ("direct", "interp"):
            row = run_case(coupling, -0.20, 12)
            print(json.dumps(row), flush=True)
            out.append(row)
    if which in ("half", "all"):
        for coupling in ("direct", "interp"):
            row = run_case(coupling, -0.10, 6)
            print(json.dumps(row), flush=True)
            out.append(row)
    if which in ("resume", "all"):
        half = run_case("direct", -0.10, 6)
        # rerun to obtain states for restart
        model, load, probe, grid = _build_ep_model("direct")
        _add_tip_load(model, load, grid)
        res = solve_static_nonlinear(
            model, load, control="displacement",
            displacement_control=DisplacementControl(
                node_id=probe, dof="uz", target_displacement=-0.10
            ),
            kinematics="corotational", num_steps=6,
            max_iterations=40, tolerance=1.0e-8,
        )
        row = run_case(
            "direct", -0.20, 6,
            initial=(res.displacements, dict(res.element_states)),
        )
        print(json.dumps(row), flush=True)
        out.append(row)


if __name__ == "__main__":
    main()
