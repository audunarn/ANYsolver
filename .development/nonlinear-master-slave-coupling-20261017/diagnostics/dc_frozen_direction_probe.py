"""Capture one exhausted current-source DC search; differentiate frozen history.

Run ONLY through the task harness. No production patch or load sweep. The capture
is written before derivative evaluations, so a process timeout preserves its
discriminating input. Frame locals bind the actual production Newton direction;
this private diagnostic intentionally fails if that production layout changes.
"""
from __future__ import annotations

import argparse
import copy
import inspect
import json
import pickle
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_nonlinear_beam_shell_slice3_continuation import _add_tip_load, _build_ep_model
from anysolver import DisplacementControl, solve_static_nonlinear
import anysolver.nonlinear_static as ns
from assessment_support import identical, source_identity


class Captured(BaseException):
    """Intentional diagnostic interruption, never a solver completion result."""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("coupling", choices=("direct", "interp"))
    parser.add_argument("output")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("refusing to overwrite an existing diagnostic capture")
    output.mkdir(parents=True)
    real_assemble, real_factorize = ns._assemble_nonlinear_system, ns.factorize
    real_snapshot = ns._increment_snapshot
    accepted = []
    current = {}
    captured = {}
    model, load, probe, grid = _build_ep_model(args.coupling)
    _add_tip_load(model, load, grid)

    def snapshot(*a, **kw):
        value = real_snapshot(*a, **kw)
        accepted.append(copy.deepcopy(value))
        return value

    class Handle:
        def __init__(self, handle, matrix):
            self.handle, self.matrix = handle, matrix

        def solve(self, rhs):
            delta = np.asarray(self.handle.solve(rhs)).reshape(-1)
            current.update(matrix=self.matrix.copy(), rhs=np.asarray(rhs).copy(),
                           delta=delta.copy(), trials=[])
            return delta

    def factorize(matrix, *a, **kw):
        return Handle(real_factorize(matrix, *a, **kw), matrix)

    def assemble(*a, **kw):
        value = real_assemble(*a, **kw)
        if kw.get("tangent", True) or not current:
            return value
        frame = inspect.currentframe().f_back
        try:
            # The development-performance adapter forwards assembly through
            # another frame while retaining the production solver itself.
            for _ in range(6):
                if frame is None or frame.f_code.co_name == "_solve_static_displacement_control":
                    break
                frame = frame.f_back
            if frame is None or frame.f_code.co_name != "_solve_static_displacement_control":
                return value
            c = frame.f_locals
            if "line_reduction" not in c:
                return value
            mapping = c["rotating_mpc_map"]
            u_trial = np.asarray(a[1])
            residual = mapping.reduce_force(
                u_trial, c["lam_trial"] * c["F_prop_static"]
                + c["F_const_static"] - value[0])
            constraint = c["target"] - float(c["row_full"] @ u_trial)
            merit = (np.linalg.norm(residual) / (c["tolerance"] * c["reference"])
                     + abs(constraint) / (c["tolerance"] * c["target_scale"]))
            alpha = 0.5 ** c["line_reduction"]
            improves = merit <= (1 - 1e-4 * alpha) * c["merit_current"]
            current["trials"].append(dict(alpha=alpha, merit=float(merit),
                                          improves=bool(improves)))
            dominated = (c["residual_norm"] * c["target_scale"]
                         >= c["constraint_error"] * c["reference"])
            if c["line_reduction"] != 7 or improves or not dominated:
                return value
            if any(t["improves"] for t in current["trials"]):
                raise RuntimeError("instrumentation mixed distinct Newton searches")
            captured.update(
                u=np.asarray(c["u"]).copy(), q=c["q"].copy(), lam=float(c["lam"]),
                target=float(c["target"]), target_scale=float(c["target_scale"]),
                reference=float(c["reference"]), merit=float(c["merit_current"]),
                tolerance=float(c["tolerance"]), T=c["T"].copy(),
                u0=c["u0"].copy(), row=c["row_full"].copy(),
                F=c["F_prop_static"].copy(), F_const=c["F_const_static"].copy(),
                states=copy.deepcopy(dict(c["committed_states"])),
                K_full=c["K_T"].copy(), f_int=c["F_int"].copy(),
                matrix=current["matrix"], rhs=current["rhs"],
                delta=current["delta"], trials=current["trials"],
                accepted_snapshots=accepted, step=int(c["step_index"]),
                iteration=int(c["iteration"]), mapping=mapping,
            )
            # The production map/model are recreated from the deterministic
            # fixture for replay. Store numerical arrays/history, not callables.
            payload = {k: v for k, v in captured.items() if k != "mapping"}
            with (output / "capture.pkl").open("xb") as stream:
                pickle.dump(payload, stream, protocol=5)
            (output / "identity.json").write_text(json.dumps(source_identity(), indent=2))
            print(json.dumps(dict(stage="captured", step=captured["step"],
                                  iteration=captured["iteration"],
                                  target=captured["target"], lam=captured["lam"],
                                  accepted=len(accepted))), flush=True)
            raise Captured()
        finally:
            del frame
        return value

    ns.factorize, ns._assemble_nonlinear_system = factorize, assemble
    ns._increment_snapshot = snapshot
    try:
        try:
            result = solve_static_nonlinear(
                model, load, control="displacement",
                displacement_control=DisplacementControl(
                    node_id=probe, dof="uz", target_displacement=-0.20),
                kinematics="corotational", num_steps=12, max_iterations=40,
                tolerance=1e-8, record_increment_snapshots=True,
                emit_restart_checkpoint=False,
            )
        except Captured:
            pass
        else:
            raise RuntimeError(f"no exhausted admitted search captured; status={result.status}")
    finally:
        ns.factorize, ns._assemble_nonlinear_system = real_factorize, real_assemble
        ns._increment_snapshot = real_snapshot

    c = captured
    mapping, T, u0 = c["mapping"], c["T"], c["u0"]
    q, lam, delta = c["q"], c["lam"], c["delta"]
    history_before = copy.deepcopy(c["states"])
    u_before = c["u"].copy()

    def residual_at(alpha):
        linear_u = np.asarray(T @ (q + alpha * delta[:-1]) + u0).reshape(-1)
        u = mapping.apply_kinematics(linear_u)
        states = copy.deepcopy(c["states"])
        before = copy.deepcopy(states)
        fint, _, _ = real_assemble(
            model, u, states, 5, tangent=False, kinematics="corotational",
            corotational_tangent="work_conjugate")
        if not identical(states, before):
            raise AssertionError("derivative reconstruction mutated its actual input history")
        r = mapping.reduce_force(u, c["F_const"] + (lam + alpha * delta[-1]) * c["F"] - fint)
        return np.r_[r, c["target"] - float(c["row"] @ u)]

    base = residual_at(0.0)
    expected = -np.asarray(c["matrix"] @ delta).reshape(-1)
    checks = []
    for h in (1e-3, 1e-4, 1e-5, 1e-6):
        plus, minus = residual_at(h), residual_at(-h)
        scale = max(np.linalg.norm(expected[:-1]), 1e-30)
        checks.append(dict(
            h=h,
            relative_central_error=float(np.linalg.norm((plus-minus)[:-1]/(2*h)-expected[:-1])/scale),
            relative_forward_error=float(np.linalg.norm((plus-base)[:-1]/h-expected[:-1])/scale),
            relative_backward_error=float(np.linalg.norm((base-minus)[:-1]/h-expected[:-1])/scale),
            forward_residual_norm=float(np.linalg.norm(plus[:-1])),
            control_derivative=float((plus[-1]-minus[-1])/(2*h)),
            expected_control_derivative=float(expected[-1]),
        ))
    report = dict(
        diagnostic_only=True, solver_completion_claim=False, coupling=args.coupling,
        step=c["step"], iteration=c["iteration"], target=c["target"], lam=lam,
        captured_control=float(c["row"] @ c["u"]),
        residual_norm=float(np.linalg.norm(base[:-1])),
        assembly_rhs_reconstruction_error=float(np.linalg.norm(base-c["rhs"])),
        augmented_linear_solve_relative_error=float(np.linalg.norm(c["matrix"] @ delta-c["rhs"])/max(np.linalg.norm(c["rhs"]), 1)),
        displacement_map_roundtrip_max_error=float(np.max(np.abs(mapping.apply_kinematics(np.asarray(T@q+u0).reshape(-1))-c["u"]))),
        input_history_unchanged=identical(history_before, c["states"]),
        input_displacement_unchanged=np.array_equal(u_before, c["u"]),
        trials=c["trials"], direction_checks=checks,
    )
    (output / "result.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
