"""Independent bounded piecewise-linear pressure response diagnostic."""

import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares


def main(input_path, output_path):
    evidence = json.loads(Path(input_path).read_text(encoding="utf-8"))
    initial = np.asarray(evidence["initial_pressure_pa"], dtype=float)
    gap = np.asarray(evidence["initial_normalized_gap_m"], dtype=float)
    response = np.asarray(evidence["equilibrated_gap_response_m_per_pa"],
                          dtype=float)
    stiffness = float(evidence["normal_stiffness_pa_per_m"])
    maximum_step = float(evidence["maximum_pressure_step_pa"])
    maximum_pressure = float(evidence["maximum_pressure_pa"])
    lower = np.maximum(0.0, initial-maximum_step)
    upper = np.minimum(maximum_pressure, initial+maximum_step)

    def argument(pressure):
        return pressure-stiffness*(gap+response @ (pressure-initial))

    def projected_residual(pressure):
        return np.maximum(0.0, argument(pressure))-pressure

    def branch_jacobian(pressure):
        active = argument(pressure) > 0.0
        jacobian = -np.eye(len(pressure))
        jacobian[active] = -stiffness*response[active]
        return jacobian

    solutions = []
    for seed in (initial, lower, upper, np.clip(initial+0.01, lower, upper)):
        solution = least_squares(
            projected_residual, seed, jac=branch_jacobian,
            bounds=(lower, upper), xtol=1.0e-13, ftol=1.0e-13,
            gtol=1.0e-13, max_nfev=500,
        )
        candidate = solution.x
        solutions.append({
            "pressure_pa": candidate.tolist(),
            "residual_inf_pa": float(np.linalg.norm(
                projected_residual(candidate), ord=np.inf)),
            "residual_l2_pa": float(np.linalg.norm(
                projected_residual(candidate))),
            "active_indices": np.flatnonzero(argument(candidate) > 0.0).tolist(),
            "evaluations": int(solution.nfev),
            "success": bool(solution.success),
        })
    output = {
        "initial_residual_pa": evidence["initial_projected_residual_pa"],
        "required_residual_pa": evidence["required_residual_pa"],
        "solutions": solutions,
    }
    Path(output_path).write_text(json.dumps(output, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps({
        "best_bounded_residual_pa": min(
            solution["residual_inf_pa"] for solution in solutions),
        "best_solution": min(solutions,
                             key=lambda item: item["residual_inf_pa"]),
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
