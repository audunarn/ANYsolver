"""Bounded plastic attribution batch (Slice 3 deliverable 2).

Question: does the coupled plastic solve reach an equilibrium at the reported
load factor, and is the reported state the committed equilibrium state?

Historical attribution BEFORE the later beam precision, elastic-limit and
return-map repairs (HANDOVER section 4.3, supervisor_findings.md):
  The three CR plastic cases are partial-load equilibria: the solver stops at
  lambda ~ 0.94 with minimum_load_increment_reached and a small independent
  reduced residual (about 3e-9 relative) at that achieved lambda. The
  near-constant tip displacement across -6k/-10k/-14k describes those partial
  equilibria; it does not establish physical collapse or a limiting load.
  VK elastic and plastic observations reproduced on clean HEAD for that
  historical candidate. Later source repairs require affected revalidation;
  this description does not assert equality for the current candidate.

Bounded experiment: for each case, solve with the original parameters
(num_steps=6, max_iterations=30, default tolerance, repository S355 curve),
then reconstruct the reduced residual independently at the achieved lambda
and at the requested lambda=1 from a deep copy of the returned state,
without re-evolving it. Deep input-state immutability is verified.

Decision rules (adopted after the seven-case batch, supervisor_findings.md):
  - lambda < 1 with a small independent residual at the achieved lambda is a
    valid partial equilibrium (stopped_at_limit with
    minimum_load_increment_reached), not a solver/reporting bug; the
    requested-lambda residual is then large by construction.
  - A large independent residual at the achieved lambda, invalid completion or
    a mixed trial/committed state would be a defect: repair and add a
    regression.
  - If the batch cannot distinguish explanations, stop with evidence.

Usage:
  python ep_attribution.py CASE [CASE ...]   # from anywhere; prints one JSON
"""
from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from ep_isolation import shell_model  # noqa: E402
from anysolver import solve_static_nonlinear  # noqa: E402
from anysolver.assembly import build_constraint_transformation  # noqa: E402
from anysolver.matrix_assembly import (  # noqa: E402
    assemble_load_vector,
    assemble_stiffness_matrix,
)
from anysolver.nonlinear_static import _assemble_nonlinear_system  # noqa: E402

try:  # absent on clean HEAD; only needed for corotational cases
    from anysolver.corotational import build_nonlinear_rotating_mpc_map  # noqa: E402
except ImportError:  # pragma: no cover - clean-HEAD attribution runs
    build_nonlinear_rotating_mpc_map = None

CASES = {
    "cr_plastic_6k": ("corotational", 1.0, -6000.0),
    "cr_plastic_10k": ("corotational", 1.0, -10000.0),
    "cr_plastic_14k": ("corotational", 1.0, -14000.0),
    "vk_elastic_6k": ("von_karman", 1.0e4, -6000.0),
    "vk_plastic_6k": ("von_karman", 1.0, -6000.0),
}


def _deep_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, np.ndarray):
        return a.shape == b.shape and np.array_equal(a, b)
    if isinstance(a, dict):
        return set(a) == set(b) and all(_deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(_deep_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return a == b or (a != a and b != b)
    return a == b


def _alpha_max(states):
    values = [
        float(np.max(np.abs(s.get("alpha", 0.0))))
        for s in states.values()
        if isinstance(s, dict)
    ]
    return max(values, default=0.0)


def run_case(name):
    kin, scale, fz = CASES[name]
    model, load_case, probe = shell_model(scale, True, fz)
    result = solve_static_nonlinear(
        model,
        load_case,
        kinematics=kin,
        num_steps=6,
        max_iterations=30,
        record_increment_snapshots=True,
    )
    info = result.info
    dofs = model.mesh.dof_manager.get_node_dofs(probe)

    u_returned = np.asarray(result.displacements, dtype=float).reshape(-1).copy()
    states_returned = copy.deepcopy(result.element_states)
    states_snapshot = copy.deepcopy(states_returned)

    # Independent reconstruction from copied state (no re-evolution).
    K0, _ = assemble_stiffness_matrix(model)
    F_prop, _ = assemble_load_vector(model, load_case)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, F_prop, model)
    mpc_map = (
        build_nonlinear_rotating_mpc_map(model, T)
        if kin == "corotational"
        else None
    )
    states_for_assembly = copy.deepcopy(states_returned)
    F_int, _, _ = _assemble_nonlinear_system(
        model,
        u_returned,
        states_for_assembly,
        5,
        tangent=False,
        kinematics=kin,
        corotational_tangent="work_conjugate" if kin == "corotational" else "auto",
    )

    def reduced(force_full):
        if mpc_map is not None:
            return np.asarray(mpc_map.reduce_force(u_returned, force_full), dtype=float).reshape(-1)
        return np.asarray(T.T @ force_full, dtype=float).reshape(-1)

    lam = float(result.load_factor)
    residual_achieved = reduced(lam * np.asarray(F_prop, dtype=float) - F_int)
    residual_requested = reduced(1.0 * np.asarray(F_prop, dtype=float) - F_int)
    reference = reduced(max(abs(lam), 1.0) * np.asarray(F_prop, dtype=float))
    ref_norm = max(float(np.linalg.norm(reference)), 1.0)

    immutability = {
        "assembly_states_unchanged": _deep_equal(states_for_assembly, states_snapshot),
        "returned_states_unchanged": _deep_equal(result.element_states, states_returned),
        "returned_displacements_unchanged": bool(
            np.array_equal(np.asarray(result.displacements, dtype=float).reshape(-1), u_returned)
        ),
    }

    adaptation = info.get("convergence_adaptation", [])
    cutbacks = [a for a in adaptation if a.get("action") == "cutback_after_nonconvergence"]

    report = {
        "case": name,
        "kinematics": kin,
        "material_scale": scale,
        "fz_per_node": fz,
        "solve_params": {"num_steps": 6, "max_iterations": 30, "tolerance_default": True},
        "status": result.status,
        "status_category": result.status_category,
        "converged": result.converged,
        "requested_load_factor": 1.0,
        "achieved_load_factor": lam,
        "peak_load_factor": result.peak_load_factor,
        "last_converged_load_factor": result.last_converged_load_factor,
        "stop_reason": result.stop_reason,
        "failure_reason": result.failure_reason,
        "steps": [
            {
                "step_index": s.step_index,
                "load_factor": s.load_factor,
                "iterations": s.iterations,
                "residual_norm": s.residual_norm,
                "max_eq_plastic_strain": s.max_equivalent_plastic_strain,
                "support_reactions": {k: list(v) for k, v in s.support_reactions.items()},
            }
            for s in result.steps
        ],
        "snapshot_count": len(result.snapshots),
        "snapshot_load_factors": [s.load_factor for s in result.snapshots],
        "total_newton_iterations": info.get("total_newton_iterations"),
        "cutback_count": len(cutbacks),
        "cutbacks": cutbacks,
        "adaptation_actions": [a.get("action") for a in adaptation],
        "alpha_max_returned": _alpha_max(result.element_states),
        "probe_uz": float(u_returned[dofs[2]]),
        "independent_residual": {
            "achieved_lambda": {
                "lambda": lam,
                "norm": float(np.linalg.norm(residual_achieved)),
                "relative": float(np.linalg.norm(residual_achieved)) / ref_norm,
            },
            "requested_lambda_1": {
                "lambda": 1.0,
                "norm": float(np.linalg.norm(residual_requested)),
                "relative": float(np.linalg.norm(residual_requested)) / ref_norm,
            },
            "reference_norm": ref_norm,
        },
        "immutability": immutability,
    }
    return report


def main():
    names = sys.argv[1:] or list(CASES)
    first = True
    for name in names:
        try:
            report = run_case(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            report = {"case": name, "error": f"{type(exc).__name__}: {exc}",
                      "traceback": traceback.format_exc()[-4000:]}
        prefix = "" if first else ",\n"
        print(prefix + json.dumps(report, indent=2), flush=True)
        first = False
    if not first:
        print("\n[all-case-reports-complete]", flush=True)


if __name__ == "__main__":
    main()
