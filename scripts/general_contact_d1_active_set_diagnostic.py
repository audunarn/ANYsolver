"""Capture the failed six-mode pressure response and test bounded alternatives.

Development-only readout. No candidate is applied to the mechanical solve.
"""

import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares

import anysolver.general_contact.linearized_pivot as pivot
from anysolver import solve_static_nonlinear

from general_contact_d1_coupled_refinement import build_case


def main(output):
    captured = []
    original = pivot.propose_supported_schur_step

    def capture(multipliers, normalized_gap, supported,
                equilibrated_gap_response, **kwargs):
        selected = np.flatnonzero(supported)
        captured.append({
            "multipliers": np.asarray(multipliers)[selected].copy(),
            "gap": np.asarray(normalized_gap)[selected].copy(),
            "response": np.asarray(equilibrated_gap_response).copy(),
            "stiffness": kwargs["normal_stiffness"],
            "max_step": kwargs["maximum_pressure_step"],
            "max_pressure": kwargs["maximum_pressure"],
        })
        return original(multipliers, normalized_gap, supported,
                        equilibrated_gap_response, **kwargs)

    pivot.propose_supported_schur_step = capture
    try:
        model, definition, settings, program = build_case(4)
        result = solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=12,
            emit_restart_checkpoint=True,
        )
    finally:
        pivot.propose_supported_schur_step = original
    if result.status != "diverged" or len(captured) != 2:
        raise RuntimeError("the recorded two-proposal failure was not reproduced")
    state = captured[1]
    lam = state["multipliers"]
    gap = state["gap"]
    response = state["response"]
    epsilon = state["stiffness"]
    lower = np.maximum(0.0, lam-state["max_step"])
    upper = np.minimum(state["max_pressure"], lam+state["max_step"])

    def projected_residual(candidate):
        predicted_gap = gap + response @ (candidate-lam)
        return np.maximum(0.0, candidate-epsilon*predicted_gap)-candidate

    before = float(np.linalg.norm(projected_residual(lam), ord=np.inf))
    solutions = []
    for seed in (lam, lower, upper, np.clip(lam+0.01, lower, upper)):
        optimum = least_squares(projected_residual, seed,
                                bounds=(lower, upper),
                                xtol=1.0e-13, ftol=1.0e-13,
                                gtol=1.0e-13, max_nfev=500)
        candidate = optimum.x
        solutions.append({
            "pressure": candidate.tolist(),
            "residual_inf_pa": float(np.linalg.norm(
                projected_residual(candidate), ord=np.inf)),
            "residual_l2_pa": float(np.linalg.norm(
                projected_residual(candidate))),
            "success": bool(optimum.success),
            "evaluations": int(optimum.nfev),
        })
    evidence = {
        "status": result.status,
        "failure_reason": result.failure_reason,
        "candidate_count": len(captured),
        "initial_pressure_pa": lam.tolist(),
        "initial_normalized_gap_m": gap.tolist(),
        "equilibrated_gap_response_m_per_pa": response.tolist(),
        "normal_stiffness_pa_per_m": epsilon,
        "maximum_pressure_step_pa": state["max_step"],
        "maximum_pressure_pa": state["max_pressure"],
        "initial_projected_residual_pa": before,
        "required_residual_pa": 0.75*before,
        "bounded_least_squares_solutions": solutions,
    }
    Path(output).write_text(json.dumps(evidence, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps({
        "status": result.status,
        "initial_residual_pa": before,
        "required_residual_pa": 0.75*before,
        "best_bounded_residual_pa": min(x["residual_inf_pa"]
                                        for x in solutions),
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
