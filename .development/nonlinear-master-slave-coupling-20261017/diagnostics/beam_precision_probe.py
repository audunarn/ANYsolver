"""Capture one real near-converged analytical increment and compare beam arithmetic.

Only run through the task numerical harness. No controls/tolerances are changed.
The first capture is written before any monkeypatched comparison. Replay uses
identical u/material inputs, T/F and source identity; originals remain unchanged.
"""
from __future__ import annotations
import argparse
import copy
import inspect
import json
from pathlib import Path
import pickle

import numpy as np

import arc_reference
from assessment_support import identical, source_identity
import anysolver.corotational as cr
import anysolver.nonlinear_static as ns
from anysolver.assembly import build_constraint_transformation
from anysolver.constraint_audit import constraint_residual_summary
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.linalg import MatrixClass, factorize
from anysolver.matrix_assembly import assemble_stiffness_matrix, assemble_load_vector


class Captured(BaseException):
    pass


def centered(values):
    if len(values) == 2:
        half = .5*(values[1]-values[0])
        return np.array([-half, half])
    offset = values-values[0]
    return offset-offset.mean(axis=0)


def stable_deformation(original, *, center_geometry):
    def evaluate(reference, element, u_element, **kwargs):
        if reference.category != "beam":
            return original(reference, element, u_element, **kwargs)
        u = np.asarray(u_element).reshape(element.num_nodes, 6)
        arm, offset = centered(reference.coordinates), centered(u[:, :3])
        if center_geometry:
            deformed = arm+offset
            R = cr._beam_rigid_rotation(reference.coordinates, deformed, u[:, 3:])
        else:
            deformed = reference.coordinates+u[:, :3]
            R = cr._beam_rigid_rotation(reference.coordinates, deformed, u[:, 3:])
        ud = np.zeros_like(u)
        difference = cr._stable_shell_rotation_difference(R)
        for i in range(element.num_nodes):
            ud[i, :3] = R.T@offset[i]+difference@arm[i]
            ud[i, 3:] = cr.rotation_vector_from_matrix(R.T@cr.rotation_matrix_from_vector(u[i, 3:]))
        return ud.reshape(-1), R, deformed
    return evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    ap.add_argument("--capture", type=Path)
    ap.add_argument("--product-only", action="store_true")
    ap.add_argument("--corrections", type=int, choices=range(4), default=3)
    args = ap.parse_args()
    args.output.mkdir(exist_ok=False)
    model, load, _probes, _nb, _root = arc_reference.build_model(16, "matching", arc_reference.oracle(.002, 30))
    original = cr._corotational_deformation_state
    if args.capture is None:
        captured = {}
        def status(_message):
            frame = inspect.currentframe().f_back
            try:
                if frame.f_code.co_name != "_newton_increment":
                    raise RuntimeError("unexpected status callback origin")
                c = frame.f_locals
                if c["iteration"] >= 5 and c["residual_norm"] < 1e-7:
                    captured.update(u=c["u"].copy(), q=c["q_trial"].copy(),
                                    states=copy.deepcopy(dict(c["committed_states"])),
                                    lam=float(c["path_factor"]), reference=float(c["reference"]),
                                    residual=c["residual"].copy(), K=c["K_T"].copy(),
                                    F_int=c["F_int"].copy(), iteration=int(c["iteration"]))
                    raise Captured()
            finally:
                del frame
        try:
            ns.solve_static_nonlinear(
                model, load, kinematics="corotational", corotational_tangent="work_conjugate",
                num_steps=12, max_iterations=40, tolerance=1e-8, status_callback=status,
                emit_restart_checkpoint=False)
        except Captured:
            pass
        if not captured:
            raise RuntimeError("no near-converged state captured")
        captured["identity"] = source_identity()
        with (args.output / "capture.pkl").open("xb") as stream:
            pickle.dump(captured, stream, protocol=5)
    else:
        with args.capture.open("rb") as stream:
            captured = pickle.load(stream)
    u = captured["u"].copy()
    states_before = copy.deepcopy(captured["states"])
    K0, _ = assemble_stiffness_matrix(model)
    F, _ = assemble_load_vector(model, load)
    _, _, T, _u0, _, _ = build_constraint_transformation(K0, F, model)
    mapping = build_nonlinear_rotating_mpc_map(model, T)
    Fext = captured["lam"]*np.asarray(F)
    modes = [("current_product", original)]
    if not args.product_only:
        modes += [("beam_displacement_form", stable_deformation(original, center_geometry=False)),
                  ("beam_centered_geometry", stable_deformation(original, center_geometry=True))]
    records = []
    try:
        for name, deformation in modes:
            cr._corotational_deformation_state = deformation
            hh = copy.deepcopy(captured["states"])
            uu = u.copy()
            fint, K, trial = ns._assemble_nonlinear_system(
                model, uu, hh, 5, tangent=True, kinematics="corotational",
                corotational_tangent="work_conjugate")
            if not np.array_equal(uu, u) or not identical(hh, states_before):
                raise AssertionError("frozen probe mutated actual evaluation inputs")
            residual = mapping.reduce_force(u, Fext-fint)
            Kred = mapping.reduce_tangent(u, K, fint-Fext, None)
            dq = np.asarray(factorize(Kred, MatrixClass.GENERAL).solve(residual)).reshape(-1)
            du = np.asarray(mapping.jacobian(u)@dq).reshape(-1)
            ratios = []
            for eid, element in model.mesh.elements.items():
                if cr._element_category(element) != "beam":
                    continue
                dofs = np.concatenate([model.mesh.dof_manager.get_node_dofs(nid) for nid in element.node_ids])
                coords = np.asarray(element.get_node_coordinates(model.mesh))+u[dofs].reshape(-1, 6)[:, :3]
                change = du[dofs].reshape(-1, 6)[:, :3]
                mask = (coords != 0) & (change != 0)
                ratios.extend((abs(change[mask])/abs(np.spacing(coords[mask]))).tolist())
            row = dict(mode=name, residual_norm=float(np.linalg.norm(residual)),
                       reference=captured["reference"], tolerance=1e-8,
                       meets_original_force_tolerance=bool(np.linalg.norm(residual) <= 1e-8*captured["reference"]),
                       captured_rhs_difference=float(np.linalg.norm(residual-captured["residual"])),
                       force_difference_from_capture=float(np.linalg.norm(fint-captured["F_int"])),
                       linear_relative_backward_error=float(np.linalg.norm(Kred@dq-residual))/max(np.linalg.norm(residual), 1e-300),
                       q_correction_norm=float(np.linalg.norm(dq)),
                       beam_coordinate_ulp_ratio_min=float(min(ratios)),
                       beam_coordinate_ulp_ratio_median=float(np.median(ratios)),
                       beam_coordinate_ulp_ratio_max=float(max(ratios)),
                       beam_coordinate_corrections_below_one_ulp=int(sum(r < 1 for r in ratios)),
                       constraint_summary=constraint_residual_summary(model, mapping.to_linear_displacement(u)),
                       actual_inputs_unchanged=True)
            correction_residuals = [row["residual_norm"]]
            q_corrected, correction = captured["q"].copy(), dq.copy()
            corrected_states = []
            for _ in range(args.corrections):
                q_corrected += correction
                u_corrected = mapping.apply_kinematics(np.asarray(T@q_corrected+_u0).reshape(-1))
                h_corrected = copy.deepcopy(captured["states"])
                u_preimage = u_corrected.copy()
                fc, kc, _sc = ns._assemble_nonlinear_system(
                    model, u_corrected, h_corrected, 5, tangent=True,
                    kinematics="corotational", corotational_tangent="work_conjugate")
                if not np.array_equal(u_corrected, u_preimage) or not identical(h_corrected, states_before):
                    raise AssertionError("frozen correction mutated actual inputs")
                rc = mapping.reduce_force(u_corrected, Fext-fc)
                krc = mapping.reduce_tangent(u_corrected, kc, fc-Fext, None)
                correction = np.asarray(factorize(krc, MatrixClass.GENERAL).solve(rc)).reshape(-1)
                correction_residuals.append(float(np.linalg.norm(rc)))
                corrected_states.append(dict(q=q_corrected.copy(), u=u_corrected, force=fc, residual=rc))
            row["fixed_history_newton_residuals"] = correction_residuals
            records.append(row)
            with (args.output / f"{name}.pkl").open("xb") as stream:
                pickle.dump(dict(u=u, states=hh, fint=fint, K=K, residual=residual, dq=dq, du=du,
                                 corrected_states=corrected_states), stream, protocol=5)
            print(json.dumps(row, allow_nan=False), flush=True)
    finally:
        cr._corotational_deformation_state = original
    with (args.output / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(dict(identity=source_identity(), captured_identity=captured["identity"],
                       captured_iteration=captured["iteration"], load_factor=captured["lam"],
                       records=records, original_input_unchanged=identical(captured["states"], states_before)), stream, indent=2)


if __name__ == "__main__":
    main()
