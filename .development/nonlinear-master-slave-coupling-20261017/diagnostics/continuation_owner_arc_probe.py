"""Prospective LOCAL pseudo-arclength diagnostic; no production capability.

Run only in a separately granted <=120s task-harness window. Starting from two
archived actual accepted states, x=(q/Q,lambda/lambda_scale), with translations
Q=1m and rotations Q=1rad (all numerical scales therefore one). For immutable
base material history H0, solve R=J(u)^T(f_int(u,H0)-lambda*F)=0 and
t.dot(x-x0)-ds=0. The GENERAL bordered Jacobian is [D/force_scale;t], where
D=[K_red*Q,-lambda_scale*F_red]. Only the force equations are row scaled.

Initial t is the forward archived secant; initial ds is one quarter its length.
Following accepted increments use the arriving-corrector local null tangent,
oriented by its dot product with the newly accepted forward secant. Span never increases: a
successful halved span is retained. Undamped Newton has at most40 iterations;
failed arc intervals may halve at most4 times. At most12 private increments.

Each evaluation deep-copies the fixed base history. Only independently admitted
equilibrated candidates advance private LEGACY material history, through the
existing candidate commit helper. Native TL elements are refused. This does not
create a public result, restart checkpoint, acceptance or collapse claim.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import pickle
import sys
import time

import numpy as np
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_nonlinear_beam_shell_slice3_continuation import (
    NX, NY, _add_tip_load, _assert_material_schema, _build_ep_model,
)
from assessment_support import identical, source_identity
from anysolver.assembly import build_constraint_transformation
from anysolver.constraint_audit import constraint_residual_summary
from anysolver.corotational import SO3MeanDomainError, build_nonlinear_rotating_mpc_map
from anysolver.linalg import MatrixClass, factorize
from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix
import anysolver.nonlinear_static as ns


EXPECTED_STATIC = "6b04a7b892f8293042ba92f1fbd4206626dfc8edff498496da161ec028a981da"


class DiagnosticDeadline(Exception):
    pass


class DiagnosticBoundary(Exception):
    pass


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float, default=100.0)
    args = parser.parse_args()
    if not 0 < args.seconds <= 100:
        parser.error("internal diagnostic deadline must be in(0,100]seconds")
    args.output.mkdir(parents=False, exist_ok=False)
    start = time.perf_counter()
    originals, original_copies, input_hashes = [], [], {}
    accepted, attempts = [], []
    live = {}
    summary = dict(diagnostic_only=True, production_adoption=False,
                   scientific_completion_claim=False, outcome="initializing")

    def emit(row, *, console=False):
        record = dict(elapsed=time.perf_counter()-start, **row)
        with (args.output / "trace.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, default=json_default, allow_nan=False)+"\n")
            stream.flush()
        if console:
            print(json.dumps(record, default=json_default, allow_nan=False), flush=True)

    def save(name, payload):
        with (args.output / name).open("xb") as stream:
            pickle.dump(payload, stream, protocol=5)

    def deadline():
        if time.perf_counter()-start >= args.seconds:
            raise DiagnosticDeadline("internal wall deadline; no completion claim")

    try:
        identity = source_identity()
        if identity["sha256"]["src/anysolver/nonlinear_static.py"].lower() != EXPECTED_STATIC:
            raise DiagnosticBoundary("frozen production source identity changed")
        repo = Path(__file__).resolve().parents[3]
        if Path(ns.__file__).resolve() != (repo / "src/anysolver/nonlinear_static.py").resolve():
            raise DiagnosticBoundary("unexpected nonlinear_static import origin")
        for path in (args.previous, args.current):
            input_hashes[str(path.resolve())] = digest(path)
            # These are explicitly authorized task-owned local binary artifacts.
            with path.open("rb") as stream:
                originals.append(pickle.load(stream))
        original_copies = copy.deepcopy(originals)
        if (abs(float(originals[0]["control"])+.18333333333333335) > 1e-12
                or abs(float(originals[1]["control"])+.18359375000000003) > 1e-12):
            raise DiagnosticBoundary("inputs are not the specified last two accepted states")
        with (args.output / "identity.json").open("x", encoding="utf-8") as stream:
            json.dump(dict(identity=identity, input_sha256=input_hashes,
                           imported_source=str(Path(ns.__file__).resolve())), stream, indent=2)
        model, load, probe, grid = _build_ep_model("direct")
        _add_tip_load(model, load, grid)
        if any(bool(getattr(e, "formulation_native_total_lagrangian", False))
               for e in model.mesh.elements.values()):
            raise DiagnosticBoundary("offline legacy history cannot own native TL transactions")
        K0, _ = assemble_stiffness_matrix(model)
        F, _ = assemble_load_vector(model, load)
        F = np.asarray(F, dtype=float)
        _, _, T, u0, _, _ = build_constraint_transformation(K0, F, model)
        u0 = np.asarray(u0, dtype=float).reshape(-1)
        mapping = build_nonlinear_rotating_mpc_map(model, T)
        if mapping is None or not mapping.active:
            raise DiagnosticBoundary("expected active direct rotating map")
        Tdense = T.toarray()
        lambda_scale = max(abs(float(s["lam"])) for s in originals)
        lambda_scale = max(lambda_scale, 1.0)
        qscale = np.ones(T.shape[1])
        probe_dof = model.mesh.dof_manager.get_node_dofs(probe)[2]
        row = np.zeros_like(F)
        row[probe_dof] = 1.0
        schema_case = dict(model=model, coupling="direct")

        def expand(x):
            q = x[:-1]*qscale
            u = mapping.apply_kinematics(np.asarray(T@q+u0).reshape(-1))
            return u, float(x[-1]*lambda_scale)

        def coordinates(payload):
            u = np.array(payload["displacements"], dtype=float, copy=True)
            linear = mapping.to_linear_displacement(u)
            q, _, rank, _ = np.linalg.lstsq(Tdense, linear-u0, rcond=None)
            if rank != T.shape[1]:
                raise DiagnosticBoundary("constraint transformation lost column rank")
            reconstructed = mapping.apply_kinematics(np.asarray(T@q+u0).reshape(-1))
            if np.max(abs(reconstructed-u)) > 1e-9:
                raise DiagnosticBoundary("archived physical displacement fails map roundtrip")
            return np.r_[q/qscale, float(payload["lam"])/lambda_scale]

        def independent(u, lam, states):
            deadline()
            uu = np.array(u, copy=True)
            hh = copy.deepcopy(dict(states))
            before_u, before_h = uu.copy(), copy.deepcopy(hh)
            _assert_material_schema(schema_case, hh)
            fint, _, _ = ns._assemble_nonlinear_system(
                model, uu, hh, 5, tangent=False, kinematics="corotational",
                corotational_tangent="work_conjugate")
            immutable = np.array_equal(uu, before_u) and identical(hh, before_h)
            if not immutable:
                raise DiagnosticBoundary("independent reconstruction mutated its actual inputs")
            residual = mapping.reduce_force(uu, fint-lam*F)
            reference = max(float(np.linalg.norm(mapping.reduce_force(uu, lam*F))), 1.0)
            relative = float(np.linalg.norm(residual))/reference
            constraints = constraint_residual_summary(model, mapping.to_linear_displacement(uu))
            imbalance = mapping.transfer_slave_imbalance_to_masters(uu, fint-lam*F)
            support, applied = np.zeros(6), np.zeros(6)
            for iy in range(NY+1):
                for ix, accumulator, is_root in ((0, support, True), (NX, applied, False)):
                    node_id = grid[(ix, iy)]
                    dofs = model.mesh.dof_manager.get_node_dofs(node_id)
                    node = model.mesh.nodes[node_id]
                    pos = np.array([node.x, node.y, node.z])+uu[dofs[:3]]
                    if is_root and np.linalg.norm(uu[dofs[3:]]) > 1e-12:
                        raise DiagnosticBoundary("root wrench convention requires zero root rotation")
                    value = imbalance if is_root else lam*F
                    accumulator[:3] += value[dofs[:3]]
                    accumulator[3:] += np.cross(pos, value[dofs[:3]])+value[dofs[3:]]
            balance = support+applied
            wrench_relative = float(np.linalg.norm(balance))/max(float(np.linalg.norm(applied)), 1e-30)
            passed = (relative <= 1e-7 and constraints.get("status") == "passed"
                      and wrench_relative <= 1e-6 and immutable)
            return dict(passed=bool(passed), relative_residual=relative,
                        constraint_summary=constraints, wrench_relative=wrench_relative,
                        support_wrench=support, applied_wrench=applied, balance=balance,
                        actual_reconstruction_inputs_unchanged=immutable)

        xx = [coordinates(s) for s in originals]
        for index, s in enumerate(originals):
            checks = independent(np.asarray(s["displacements"]), float(s["lam"]), s["element_states"])
            emit(dict(kind="archived_input_checks", index=index, checks=checks), console=True)
            if not checks["passed"]:
                raise DiagnosticBoundary("archived input fails independent admission")
        x = xx[-1].copy()
        secant = xx[-1]-xx[-2]
        length = float(np.linalg.norm(secant))
        if not np.isfinite(length) or length <= 0:
            raise DiagnosticBoundary("archived secant is not a finite nonzero direction")
        direction = secant/length
        span = initial_span = length/4.0
        states = copy.deepcopy(dict(originals[-1]["element_states"]))
        control = float(originals[-1]["control"])
        previous_control_increment = float(originals[-1]["control"]-originals[-2]["control"])
        initial_u, _ = expand(x)
        previous_control_tangent = float(np.asarray(row@mapping.jacobian(initial_u)).reshape(-1)
                                         @ (qscale*direction[:-1]))
        emit(dict(kind="scales", lambda_scale=lambda_scale, translation_scale_m=1.0,
                  rotation_scale_rad=1.0, initial_secant_length=length, initial_arc_span=span,
                  initial_control_tangent=previous_control_tangent, maximum_increments=12,
                  maximum_newton_iterations=40, maximum_span_halvings=4,
                  original_force_tolerance=1e-8, independent_achieved_tolerance=1e-7,
                  arc_constraint_tolerance=1e-8*max(initial_span, 1e-9)), console=True)

        for arc_index in range(1, 13):
            deadline()
            x0 = x.copy()
            base_states = copy.deepcopy(states)
            base_before = copy.deepcopy(base_states)
            base_u, base_lam = expand(x0)
            force_scale = max(float(np.linalg.norm(mapping.reduce_force(base_u, base_lam*F))), 1.0)
            solved = False
            for halving in range(5):
                trial_span = span*(.5**halving)
                y = x0+trial_span*direction
                attempt = dict(arc_index=arc_index, halving=halving, target_arc_span=trial_span,
                               base_control=control, base_lam=base_lam, outcome="running")
                attempts.append(attempt)
                live.update(x=y.copy(), base_x=x0.copy(), base_history=copy.deepcopy(base_states),
                            direction=direction.copy(), attempt=attempt)
                emit(dict(kind="attempt_start", **attempt))
                failure = "maximum_iterations_reached"
                for iteration in range(1, 41):
                    deadline()
                    try:
                        u, lam = expand(y)
                        eval_u_before = u.copy()
                        eval_states = copy.deepcopy(base_states)
                        eval_before = copy.deepcopy(eval_states)
                        fint, K, candidate = ns._assemble_nonlinear_system(
                            model, u, eval_states, 5, tangent=True, kinematics="corotational",
                            corotational_tangent="work_conjugate")
                        if (not np.array_equal(u, eval_u_before)
                                or not identical(eval_states, eval_before)
                                or not identical(base_states, base_before)):
                            raise DiagnosticBoundary("corrector mutated its fixed material-history input")
                        residual = mapping.reduce_force(u, fint-lam*F)
                        norm = float(np.linalg.norm(residual))
                        reference = max(float(np.linalg.norm(mapping.reduce_force(u, max(abs(lam), 1.0)*F))), 1.0)
                        plane = float(direction@(y-x0)-trial_span)
                        if not np.all(np.isfinite([norm, reference, plane, lam])):
                            failure = "nonfinite_corrector_residual"
                            break
                        Kred = mapping.reduce_tangent(u, K, fint-lam*F, None)
                        fred = mapping.reduce_force(u, F)
                        D = sparse.hstack((Kred@sparse.diags(qscale),
                                           sparse.csr_matrix((-lambda_scale*fred)[:, None])), format="csr")
                        bordered = sparse.vstack((D/force_scale, sparse.csr_matrix(direction[None, :])), format="csr")
                        live.update(x=y.copy(), force_residual=norm, arc_residual=plane,
                                    iteration=iteration, control=float(u[probe_dof]), lam=lam)
                        emit(dict(kind="newton", arc_index=arc_index, halving=halving,
                                  iteration=iteration, target_arc_span=trial_span,
                                  residual_norm=norm, force_reference=reference,
                                  relative_force=norm/reference, arc_residual=plane,
                                  control=float(u[probe_dof]), lam=lam))
                        if norm <= 1e-8*reference and abs(plane) <= 1e-8*max(initial_span, 1e-9):
                            candidate_owned = copy.deepcopy(dict(candidate))
                            checks = independent(u, lam, candidate_owned)
                            if not checks["passed"]:
                                save(f"rejected-admission-{arc_index:02d}-{halving}.pkl",
                                     dict(u=u, x=y, element_states=candidate_owned, checks=checks))
                                raise DiagnosticBoundary("equilibrated candidate failed independent admission")
                            # Use the arriving-corrector D, not a zero-increment
                            # unloading derivative after material history advances.
                            tangent_handle = factorize(bordered, MatrixClass.GENERAL,
                                                       signature=f"private_arc_tangent:{arc_index}:{halving}")
                            new_direction = np.asarray(tangent_handle.solve(np.r_[np.zeros(D.shape[0]), 1.0])).reshape(-1)
                            tangent_norm = float(np.linalg.norm(new_direction))
                            if not np.isfinite(tangent_norm) or tangent_norm <= 0:
                                raise DiagnosticBoundary("arriving tangent has no finite normalization")
                            new_direction /= tangent_norm
                            arriving_secant = y-x0
                            orientation = float(new_direction@arriving_secant)
                            if orientation == 0.0:
                                raise DiagnosticBoundary("local tangent has ambiguous forward secant orientation")
                            if orientation < 0:
                                new_direction *= -1
                            tangent_error = float(np.linalg.norm(D@new_direction))/max(float(np.linalg.norm(D.data)), 1.0)
                            next_states = ns._commit_nonlinear_state_candidate(
                                eval_states, candidate, model=model, accepted_displacements=u)
                            next_states = copy.deepcopy(dict(next_states))
                            if not identical(next_states, candidate_owned) or not identical(base_states, base_before):
                                raise DiagnosticBoundary("private legacy commit altered candidate/base unexpectedly")
                            new_control = float(u[probe_dof])
                            delta_control = new_control-control
                            control_tangent = float(np.asarray(row@mapping.jacobian(u)).reshape(-1)
                                                    @ (qscale*new_direction[:-1]))
                            increment_turn = (delta_control*previous_control_increment < 0
                                              and abs(delta_control) > 1e-8)
                            tangent_turn = (control_tangent*previous_control_tangent < 0
                                            and abs(control_tangent) > 1e-8)
                            target_crossing = control > -.20 and new_control <= -.20
                            accepted_row = dict(arc_index=arc_index, halving=halving,
                                                iterations=iteration, target_arc_span=trial_span,
                                                actual_arc_chord=float(np.linalg.norm(y-x0)),
                                                control=new_control, lam=lam, control_increment=delta_control,
                                                control_tangent_per_arc=control_tangent,
                                                lam_tangent_per_arc=float(lambda_scale*new_direction[-1]),
                                                tangent_dot_previous=float(new_direction@direction),
                                                tangent_dot_forward_secant=float(new_direction@arriving_secant)
                                                / float(np.linalg.norm(arriving_secant)),
                                                tangent_relative_residual=tangent_error,
                                                control_increment_reversal=bool(increment_turn),
                                                control_tangent_sign_change=bool(tangent_turn),
                                                target_crossing=bool(target_crossing), checks=checks)
                            save(f"accepted-{arc_index:02d}.pkl", dict(
                                displacements=np.array(u, copy=True), element_states=next_states,
                                x=y.copy(), q=y[:-1]*qscale, direction=new_direction.copy(),
                                lambda_scale=lambda_scale, **accepted_row))
                            accepted.append(accepted_row)
                            attempt.update(outcome="accepted", iterations=iteration)
                            emit(dict(kind="private_accepted", **accepted_row), console=True)
                            x, states, direction = y.copy(), next_states, new_direction
                            span, control = trial_span, new_control
                            previous_control_increment, previous_control_tangent = delta_control, control_tangent
                            solved = True
                            break
                        rhs = -np.r_[residual/force_scale, plane]
                        try:
                            handle = factorize(bordered, MatrixClass.GENERAL,
                                               signature=f"private_arc_corrector:{arc_index}:{halving}:{iteration}")
                            delta = np.asarray(handle.solve(rhs)).reshape(-1)
                        except (RuntimeError, np.linalg.LinAlgError) as error:
                            failure = "bordered_linear_solve_failed: "+str(error)
                            break
                        if not np.all(np.isfinite(delta)):
                            failure = "nonfinite_bordered_solution"
                            break
                        emit(dict(kind="linear_solve", arc_index=arc_index, halving=halving,
                                  iteration=iteration,
                                  relative_backward_error=float(np.linalg.norm(bordered@delta-rhs))
                                  / max(float(np.linalg.norm(rhs)), 1e-300)))
                        y += delta
                        live["x"] = y.copy()
                    except SO3MeanDomainError as error:
                        failure = "trial_domain_refused: "+str(error)
                        break
                if solved:
                    if increment_turn or tangent_turn or target_crossing:
                        summary.update(outcome="discriminating_path_event",
                                       control_increment_reversal=bool(increment_turn),
                                       control_tangent_sign_change=bool(tangent_turn),
                                       target_crossing=bool(target_crossing))
                    break
                attempt.update(outcome=failure)
                save(f"failed-{arc_index:02d}-{halving}.pkl", copy.deepcopy(live))
                emit(dict(kind="attempt_failed", **attempt), console=True)
            if not solved:
                summary.update(outcome="bounded_corrector_failure")
                break
            if summary["outcome"] == "discriminating_path_event":
                break
        else:
            summary.update(outcome="maximum_private_increments")
    except DiagnosticDeadline as error:
        summary.update(outcome="diagnostic_deadline", reason=str(error))
    except Exception as error:
        # Preserve concrete metadata/oracle/factorization boundaries; never
        # bypass them or relabel the failure as a missing physical root.
        summary.update(outcome="boundary_or_oracle_failure", error_type=type(error).__name__, reason=str(error))
    finally:
        if live:
            save("last-attempt.pkl", live)
        inputs_unchanged = (len(originals) == len(original_copies) == 2
                            and identical(originals, original_copies))
        files_unchanged = bool(input_hashes) and all(digest(Path(p)) == h for p, h in input_hashes.items())
        summary.update(accepted_private_increments=len(accepted), attempts=attempts,
                       accepted=accepted, original_input_objects_unchanged=bool(inputs_unchanged),
                       original_input_files_unchanged=bool(files_unchanged),
                       elapsed=time.perf_counter()-start,
                       interpretation="Local diagnostic evidence only; no public capability, root nonexistence or collapse claim.")
        with (args.output / "summary.json").open("x", encoding="utf-8") as stream:
            json.dump(summary, stream, default=json_default, indent=2, allow_nan=False)
        emit(dict(kind="terminal", outcome=summary["outcome"],
                  accepted_private_increments=len(accepted),
                  original_input_objects_unchanged=bool(inputs_unchanged),
                  original_input_files_unchanged=bool(files_unchanged)), console=True)


if __name__ == "__main__":
    main()
