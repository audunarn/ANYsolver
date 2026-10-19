"""One trust-region experiment on the captured failed interval, not a load sweep."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import pickle
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model, _add_tip_load
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from assessment_support import identical, source_identity


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("output")
    ap.add_argument("--exact-control", action="store_true")
    args = ap.parse_args()
    output = Path(args.output)
    if output.exists():
        ap.error("refusing to overwrite existing result")
    # Input is the task-owned binary artifact, never an external pickle.
    with Path(args.capture).open("rb") as stream:
        c = pickle.load(stream)
    model, load, probe, grid = _build_ep_model("direct")
    _add_tip_load(model, load, grid)
    mapping = build_nonlinear_rotating_mpc_map(model, c["T"])
    before = copy.deepcopy(c["states"])
    history = []
    cache = {}
    scale = np.r_[np.full(c["q"].size, c["reference"]), c["target_scale"]]
    row_red = np.asarray(c["row"] @ c["T"]).reshape(-1)
    pivot = int(np.argmax(np.abs(row_red)))
    free = np.delete(np.arange(c["q"].size), pivot)
    P = np.eye(c["q"].size)[:, free]
    P[pivot] = -row_red[free]/row_red[pivot]

    def expand(x):
        if not args.exact_control:
            return x
        q = P @ x[:-1]
        q[pivot] += (c["target"]-float(c["row"] @ c["u0"]))/row_red[pivot]
        return np.r_[q, x[-1]]

    def evaluate(x):
        if "x" in cache and np.array_equal(cache["x"], x):
            return cache["residual"], cache["jac"]
        full_x = expand(x)
        u = mapping.apply_kinematics(np.asarray(c["T"]@full_x[:-1]+c["u0"]).reshape(-1))
        if args.exact_control and abs(c["target"]-float(c["row"]@u)) > 1e-14:
            raise ValueError("control elimination is inapplicable to this nonlinear coordinate")
        states = copy.deepcopy(c["states"])
        fint, K, trial = _assemble_nonlinear_system(
            model, u, states, 5, tangent=True, kinematics="corotational",
            corotational_tangent="work_conjugate")
        if not identical(states, before):
            raise AssertionError("constitutive assembly mutated the actual reconstruction input")
        external = c["F_const"]+full_x[-1]*c["F"]
        r = mapping.reduce_force(u, external-fint)
        fred = mapping.reduce_force(u, c["F"])
        kred = mapping.reduce_tangent(u, K, fint-external, None)
        row = np.asarray(c["row"]@mapping.jacobian(u)).reshape(-1)
        residual = np.r_[r, c["target"]-float(c["row"]@u)]/scale
        jac = np.block([[-kred.toarray(), fred[:, None]], [-row[None, :], np.zeros((1, 1))]])/scale[:, None]
        if args.exact_control:
            residual = residual[:-1]
            jac = np.column_stack([jac[:-1, :-1] @ P, jac[:-1, -1]])
        cache.update(x=x.copy(), residual=residual, jac=jac, u=u, trial=trial)
        history.append(dict(evaluation=len(history)+1, residual_norm=float(np.linalg.norm(r)),
                            control_error=float(abs(c["target"]-c["row"]@u)),
                            lam=float(x[-1])))
        print(json.dumps(history[-1]), flush=True)
        return residual, jac

    x0 = np.r_[c["q"], c["lam"]]
    if args.exact_control:
        x0 = np.r_[c["q"][free], c["lam"]]
    remaining = 40-c["iteration"]
    result = least_squares(lambda x: evaluate(x)[0], x0,
                           jac=lambda x: evaluate(x)[1], method="trf",
                           tr_solver="exact", x_scale="jac", max_nfev=remaining,
                           ftol=1e-12, xtol=1e-12, gtol=1e-12)
    residual, _ = evaluate(result.x)
    actual_reference = max(np.linalg.norm(mapping.reduce_force(
        cache["u"], c["F_const"]+max(abs(result.x[-1]), 1)*c["F"])), 1)
    relative = np.linalg.norm(residual * scale[:-1] if args.exact_control else residual[:-1]*scale[:-1])/actual_reference
    control_error = abs(c["target"]-float(c["row"]@cache["u"]))
    record = dict(kind="frozen_interval_only", diagnostic_only=True,
                  identity=source_identity(), scipy_status=int(result.status),
                  message=result.message, nfev=result.nfev, njev=result.njev,
                  original_iteration=c["iteration"], allowance=remaining,
                  exact_control=args.exact_control,
                  relative_residual=float(relative), control_error=float(control_error),
                  interval_equilibrated=bool(relative <= 1e-8 and control_error <= 1e-8*c["target_scale"]),
                  target=c["target"], lam=float(result.x[-1]), history=history,
                  original_history_unchanged=identical(before, c["states"]))
    output.write_text(json.dumps(record, indent=2, allow_nan=False))
    print(json.dumps({k:v for k,v in record.items() if k not in ("identity", "history")}), flush=True)


if __name__ == "__main__":
    main()
