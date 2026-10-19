"""Bounded paired-history derivative / forward-arc event discriminator.

UNEXECUTED until root grants one <=120s task-harness window. Preserve the original
arc probe and its evidence. At its saved endpoint11, compare R(x;H10) and R(x;H11)
along its actual saved arriving tangent. Central differences alone are inadequate
at a constitutive active-set boundary: report both one-sided derivatives and
material activity without changing yield criteria. Then independently correct two
nested positive arc spans from the SAME immutable H11, not a load sweep or a
production path. Same 40-Newton / four-span-halving bounds and physical oracles.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import pickle
import time

import numpy as np
from scipy import sparse

import continuation_owner_arc_probe as arc

PROBE_SHA256 = "cf7dd7572330d2815d7049f7ad6b1b2e26e35443ec3db667c566093c36a77e97"


def material_delta(base, candidate):
    """Exact activity counts plus magnitudes; no invented activity tolerance."""
    result = {}
    for eid, old in base.items():
        if not isinstance(old, dict) or "alpha" not in old:
            continue
        new = candidate[eid]
        aa, bb = np.asarray(old["alpha"]), np.asarray(new["alpha"])
        pp, qq = np.asarray(old["plastic_strain"]), np.asarray(new["plastic_strain"])
        if aa.shape != bb.shape or pp.shape != qq.shape:
            raise arc.DiagnosticBoundary("material-state layout changed")
        result[str(eid)] = dict(
            positive_alpha_indices=np.flatnonzero((bb-aa).reshape(-1) > 0),
            negative_alpha_indices=np.flatnonzero((bb-aa).reshape(-1) < 0),
            max_alpha_increment=float(np.max(bb-aa, initial=0)),
            min_alpha_increment=float(np.min(bb-aa, initial=0)),
            plastic_strain_change_norm=float(np.linalg.norm(qq-pp)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float, default=100.0)
    args = parser.parse_args()
    if not 0 < args.seconds <= 100:
        parser.error("internal deadline must be in(0,100]seconds")
    args.output.mkdir(exist_ok=False)
    start = time.perf_counter()
    originals, original_copies, input_hashes = [], [], {}
    live, derivatives, correctors = {}, [], []
    summary = dict(diagnostic_only=True, scientific_completion_claim=False,
                   production_adoption=False, outcome="initializing")

    def deadline():
        if time.perf_counter()-start >= args.seconds:
            raise arc.DiagnosticDeadline("internal wall deadline")

    def emit(row, *, console=False):
        row = dict(elapsed=time.perf_counter()-start, **row)
        with (args.output / "trace.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, default=arc.json_default, allow_nan=False)+"\n")
            stream.flush()
        if console:
            print(json.dumps(row, default=arc.json_default, allow_nan=False), flush=True)

    def save(name, payload):
        with (args.output / name).open("xb") as stream:
            pickle.dump(payload, stream, protocol=5)

    try:
        if arc.digest(Path(arc.__file__)) != PROBE_SHA256:
            raise arc.DiagnosticBoundary("original diagnostic changed")
        identity = arc.source_identity()
        if identity["sha256"]["src/anysolver/nonlinear_static.py"] != arc.EXPECTED_STATIC:
            raise arc.DiagnosticBoundary("frozen production source changed")
        paths = [args.event_directory / f"accepted-{index:02d}.pkl" for index in (10, 11)]
        for path in paths:
            input_hashes[str(path.resolve())] = arc.digest(path)
            with path.open("rb") as stream:
                originals.append(pickle.load(stream))
        original_copies = copy.deepcopy(originals)
        if [s["arc_index"] for s in originals] != [10, 11]:
            raise arc.DiagnosticBoundary("not the specified event endpoints10/11")
        with (args.output / "identity.json").open("x", encoding="utf-8") as stream:
            json.dump(dict(identity=identity, input_sha256=input_hashes,
                           original_probe_sha256=PROBE_SHA256), stream, indent=2)
        model, load, probe, grid = arc._build_ep_model("direct")
        arc._add_tip_load(model, load, grid)
        if any(bool(getattr(e, "formulation_native_total_lagrangian", False))
               for e in model.mesh.elements.values()):
            raise arc.DiagnosticBoundary("offline legacy diagnostic cannot own native TL state")
        K0, _ = arc.assemble_stiffness_matrix(model)
        F, _ = arc.assemble_load_vector(model, load)
        F = np.asarray(F, dtype=float)
        _, _, T, u0, _, _ = arc.build_constraint_transformation(K0, F, model)
        u0 = np.asarray(u0).reshape(-1)
        mapping = arc.build_nonlinear_rotating_mpc_map(model, T)
        if mapping is None or not mapping.active:
            raise arc.DiagnosticBoundary("missing direct rotating map")
        x0 = np.array(originals[1]["x"], dtype=float, copy=True)
        tangent = np.array(originals[1]["direction"], dtype=float, copy=True)
        lambda_scale = float(originals[1]["lambda_scale"])
        span = float(originals[1]["target_arc_span"])
        if (not np.all(np.isfinite(x0)) or not np.all(np.isfinite(tangent))
                or not np.isfinite(lambda_scale) or lambda_scale <= 0
                or not np.isfinite(span) or span <= 0
                or float(np.linalg.norm(tangent)) <= 0):
            raise arc.DiagnosticBoundary("saved scaled endpoint/direction is not finite and nondegenerate")
        histories = [copy.deepcopy(s["element_states"]) for s in originals]
        base_history = histories[1]
        base_history_before = copy.deepcopy(base_history)
        probe_dof = model.mesh.dof_manager.get_node_dofs(probe)[2]
        row = np.zeros_like(F)
        row[probe_dof] = 1
        schema = dict(model=model, coupling="direct")

        def expand(x):
            return (mapping.apply_kinematics(np.asarray(T@x[:-1]+u0).reshape(-1)),
                    float(lambda_scale*x[-1]))

        def evaluate(x, history, *, tangent_matrix=False):
            deadline()
            u, lam = expand(x)
            u_before = u.copy()
            hh = copy.deepcopy(history)
            before = copy.deepcopy(hh)
            fint, K, candidate = arc.ns._assemble_nonlinear_system(
                model, u, hh, 5, tangent=tangent_matrix, kinematics="corotational",
                corotational_tangent="work_conjugate")
            if (not np.array_equal(u, u_before) or not arc.identical(hh, before)
                    or not arc.identical(base_history, base_history_before)):
                raise arc.DiagnosticBoundary("residual evaluation mutated its actual inputs/base")
            residual = mapping.reduce_force(u, fint-lam*F)
            if not np.all(np.isfinite(residual)):
                raise arc.DiagnosticBoundary("nonfinite residual")
            D = None
            if tangent_matrix:
                Kred = mapping.reduce_tangent(u, K, fint-lam*F, None)
                fred = mapping.reduce_force(u, F)
                D = sparse.hstack((Kred, sparse.csr_matrix((-lambda_scale*fred)[:, None])), format="csr")
            return residual, D, copy.deepcopy(dict(candidate)), u, lam

        def independent(u, lam, history):
            deadline()
            uu, hh = np.array(u, copy=True), copy.deepcopy(history)
            ub, hb = uu.copy(), copy.deepcopy(hh)
            arc._assert_material_schema(schema, hh)
            fint, _, _ = arc.ns._assemble_nonlinear_system(
                model, uu, hh, 5, tangent=False, kinematics="corotational",
                corotational_tangent="work_conjugate")
            immutable = np.array_equal(uu, ub) and arc.identical(hh, hb)
            if not immutable:
                raise arc.DiagnosticBoundary("independent oracle mutated actual reconstruction inputs")
            relative = float(np.linalg.norm(mapping.reduce_force(uu, fint-lam*F)))/max(
                float(np.linalg.norm(mapping.reduce_force(uu, lam*F))), 1.0)
            constraints = arc.constraint_residual_summary(model, mapping.to_linear_displacement(uu))
            imbalance = mapping.transfer_slave_imbalance_to_masters(uu, fint-lam*F)
            support, applied = np.zeros(6), np.zeros(6)
            for iy in range(arc.NY+1):
                for ix, accum, is_root in ((0, support, True), (arc.NX, applied, False)):
                    nid = grid[(ix, iy)]
                    dofs = model.mesh.dof_manager.get_node_dofs(nid)
                    node = model.mesh.nodes[nid]
                    pos = np.array([node.x, node.y, node.z])+uu[dofs[:3]]
                    if is_root and np.linalg.norm(uu[dofs[3:]]) > 1e-12:
                        raise arc.DiagnosticBoundary("root wrench requires zero root rotations")
                    ff = imbalance if is_root else lam*F
                    accum[:3] += ff[dofs[:3]]
                    accum[3:] += np.cross(pos, ff[dofs[:3]])+ff[dofs[3:]]
            balance = support+applied
            wrench = float(np.linalg.norm(balance))/max(float(np.linalg.norm(applied)), 1e-30)
            return dict(passed=bool(relative <= 1e-7 and constraints["status"] == "passed"
                                    and wrench <= 1e-6 and immutable),
                        relative_residual=relative, constraint_summary=constraints,
                        wrench_relative=wrench, support_wrench=support, applied_wrench=applied,
                        balance=balance, actual_reconstruction_inputs_unchanged=immutable)

        for index, payload in enumerate(originals):
            checks = independent(payload["displacements"], float(payload["lam"]), payload["element_states"])
            emit(dict(kind="input_checks", index=index+10, checks=checks), console=True)
            if not checks["passed"]:
                raise arc.DiagnosticBoundary("saved endpoint fails independent admission")
        u0physical, lam0 = expand(x0)
        if (np.max(abs(u0physical-originals[1]["displacements"])) > 1e-9
                or abs(lam0-float(originals[1]["lam"])) > 1e-12):
            raise arc.DiagnosticBoundary("saved scaled coordinates do not reconstruct physical endpoint")
        force_scale = max(float(np.linalg.norm(mapping.reduce_force(u0physical, lam0*F))), 1.0)
        control0 = float(u0physical[probe_dof])
        control_row = np.asarray(row@mapping.jacobian(u0physical)).reshape(-1)
        predicted_control_tangent = float(control_row@tangent[:-1])
        baseline = []
        for label, history in zip(("arriving_H10", "committed_H11"), histories):
            residual0, D, candidate0, _, _ = evaluate(x0, history, tangent_matrix=True)
            expected = np.asarray(D@tangent).reshape(-1)
            mechanical = np.asarray(D[:, :-1]@tangent[:-1]).reshape(-1)
            proportional = np.asarray(D[:, -1].toarray()).reshape(-1)*tangent[-1]
            normalizer = float(np.linalg.norm(mechanical)+np.linalg.norm(proportional))
            if not np.isfinite(normalizer) or normalizer <= 0:
                raise arc.DiagnosticBoundary("directional force scale is degenerate")
            bordered = sparse.vstack((D/force_scale, sparse.csr_matrix(tangent[None, :])), format="csr")
            handle = arc.factorize(bordered, arc.MatrixClass.GENERAL, signature=f"event_null:{label}")
            own_tangent = np.asarray(handle.solve(np.r_[np.zeros(D.shape[0]), 1.0])).reshape(-1)
            own_norm = float(np.linalg.norm(own_tangent))
            if not np.isfinite(own_norm) or own_norm <= 0:
                raise arc.DiagnosticBoundary("same-history null tangent is nonfinite or degenerate")
            own_tangent /= own_norm
            if float(own_tangent@tangent) < 0:
                own_tangent *= -1
            baseline.append(dict(label=label, residual_norm=float(np.linalg.norm(residual0)),
                                 expected_derivative_norm=float(np.linalg.norm(expected)),
                                 derivative_normalizer=normalizer,
                                 own_control_tangent=float(control_row@own_tangent[:-1]),
                                 stored_control_tangent=predicted_control_tangent,
                                 state_delta_from_base=material_delta(history, candidate0)))
            save(f"baseline-{label}.pkl", dict(x=x0, residual=residual0, D=D, tangent=tangent,
                                             own_tangent=own_tangent, candidate_states=candidate0))
            for divisor in (16, 64, 256):
                h = span/divisor
                plus, _, plus_states, _, _ = evaluate(x0+h*tangent, history)
                minus, _, minus_states, _, _ = evaluate(x0-h*tangent, history)
                forward, backward = (plus-residual0)/h, (residual0-minus)/h
                central = (plus-minus)/(2*h)
                entry = dict(label=label, h=h,
                             relative_forward_error=float(np.linalg.norm(forward-expected))/normalizer,
                             relative_backward_error=float(np.linalg.norm(backward-expected))/normalizer,
                             relative_central_error=float(np.linalg.norm(central-expected))/normalizer,
                             relative_one_sided_spread=float(np.linalg.norm(forward-backward))/normalizer,
                             forward_activity=material_delta(history, plus_states),
                             backward_activity=material_delta(history, minus_states))
                derivatives.append(entry)
                save(f"stencil-{label}-{divisor}.pkl", dict(x0=x0, h=h, direction=tangent,
                      residual0=residual0, plus_residual=plus, minus_residual=minus,
                      plus_states=plus_states, minus_states=minus_states, expected_derivative=expected))
                emit(dict(kind="paired_history_derivative", **entry))
        summary["baseline"] = baseline
        summary["zero_order_force_difference"] = float(np.linalg.norm(
            evaluate(x0, histories[0])[0]-evaluate(x0, histories[1])[0]))
        emit(dict(kind="paired_baselines", baseline=baseline,
                  zero_order_force_difference=summary["zero_order_force_difference"]), console=True)

        # Two nested local correctors independently restart from identical H11.
        # This is local step refinement, not two sequential history advances.
        for refinement in (0, 1):
            nominal_span = span/(4*(2**refinement))
            solved = False
            for halving in range(5):
                ds = nominal_span*(.5**halving)
                y = x0+ds*tangent
                failure = "maximum_iterations_reached"
                for iteration in range(1, 41):
                    deadline()
                    live.update(refinement=refinement, halving=halving, iteration=iteration,
                                x=y.copy(), base_x=x0.copy(), base_history=copy.deepcopy(base_history),
                                direction=tangent.copy(), target_arc_span=ds)
                    try:
                        residual, D, candidate, u, lam = evaluate(y, base_history, tangent_matrix=True)
                    except arc.SO3MeanDomainError as error:
                        failure = "trial_domain_refused: "+str(error)
                        break
                    plane = float(tangent@(y-x0)-ds)
                    norm = float(np.linalg.norm(residual))
                    reference = max(float(np.linalg.norm(mapping.reduce_force(u, max(abs(lam), 1.0)*F))), 1.0)
                    if not np.all(np.isfinite([norm, reference, plane, lam])):
                        failure = "nonfinite_corrector_residual"
                        break
                    emit(dict(kind="forward_newton", refinement=refinement, halving=halving,
                              iteration=iteration, target_arc_span=ds, control=float(u[probe_dof]),
                              lam=lam, residual_norm=norm, reference=reference, arc_residual=plane))
                    if norm <= 1e-8*reference and abs(plane) <= 1e-8*span:
                        checks = independent(u, lam, candidate)
                        if not checks["passed"]:
                            save(f"failed-admission-{refinement}-{halving}.pkl", dict(live, candidate=candidate, checks=checks))
                            raise arc.DiagnosticBoundary("forward-corrected candidate failed independent admission")
                        private_committed = arc.ns._commit_nonlinear_state_candidate(
                            copy.deepcopy(base_history), candidate, model=model,
                            accepted_displacements=u)
                        private_committed = copy.deepcopy(dict(private_committed))
                        if (not arc.identical(private_committed, candidate)
                                or not arc.identical(base_history, base_history_before)):
                            raise arc.DiagnosticBoundary("private legacy commit altered candidate/base unexpectedly")
                        result = dict(refinement=refinement, halving=halving, iterations=iteration,
                                      target_arc_span=ds, control=float(u[probe_dof]), lam=lam,
                                      actual_arc_chord=float(np.linalg.norm(y-x0)),
                                      correction_from_predictor_norm=float(np.linalg.norm(y-x0-ds*tangent)),
                                      chord_dot_stored_tangent=float(tangent@(y-x0)),
                                      actual_control_increment=float(u[probe_dof]-control0),
                                      predicted_control_increment=ds*predicted_control_tangent,
                                      activity=material_delta(base_history, candidate), checks=checks)
                        save(f"forward-accepted-{refinement}.pkl", dict(
                            x=y.copy(), displacements=u.copy(), element_states=private_committed,
                            base_history=copy.deepcopy(base_history), **result))
                        correctors.append(result)
                        emit(dict(kind="forward_corrected", **result), console=True)
                        solved = True
                        break
                    bordered = sparse.vstack((D/force_scale, sparse.csr_matrix(tangent[None, :])), format="csr")
                    try:
                        handle = arc.factorize(bordered, arc.MatrixClass.GENERAL,
                                               signature=f"event_corrector:{refinement}:{halving}:{iteration}")
                        delta = np.asarray(handle.solve(-np.r_[residual/force_scale, plane])).reshape(-1)
                    except (RuntimeError, np.linalg.LinAlgError) as error:
                        failure = "bordered_solve_failed: "+str(error)
                        break
                    if not np.all(np.isfinite(delta)):
                        failure = "nonfinite_bordered_solution"
                        break
                    y += delta
                if solved:
                    break
                save(f"forward-failed-{refinement}-{halving}.pkl", dict(live, failure=failure))
                emit(dict(kind="forward_failed", refinement=refinement, halving=halving,
                          target_arc_span=ds, failure=failure), console=True)
            if not solved:
                summary["outcome"] = "bounded_forward_corrector_failure"
                break
        else:
            summary["outcome"] = "paired_derivatives_and_nested_correctors_complete"
    except arc.DiagnosticDeadline as error:
        summary.update(outcome="diagnostic_deadline", reason=str(error))
    except Exception as error:
        summary.update(outcome="boundary_or_oracle_failure", error_type=type(error).__name__, reason=str(error))
    finally:
        if live:
            save("last-forward-attempt.pkl", live)
        increments = [r["actual_control_increment"] for r in correctors]
        summary.update(derivatives=derivatives, corrected_states=correctors,
                       independently_admitted_control_increments=increments,
                       both_positive_above_existing_resolution=bool(len(increments) == 2 and all(v > 1e-8 for v in increments)),
                       both_negative_above_existing_resolution=bool(len(increments) == 2 and all(v < -1e-8 for v in increments)),
                       original_input_objects_unchanged=bool(len(originals) == len(original_copies) == 2
                                                             and arc.identical(originals, original_copies)),
                       original_input_files_unchanged=bool(input_hashes and all(arc.digest(Path(p)) == h for p, h in input_hashes.items())),
                       elapsed=time.perf_counter()-start,
                       interpretation_rules=[
                           "Both admitted positive corrected increments corroborate a local reversed control segment; they do not establish global fold topology or collapse.",
                           "Negative corrected increments reject a fold inference from the stored arriving tangent alone.",
                           "Refining one-sided derivative spread with changed material activity indicates constitutive branch selection; a smooth two-sided residual derivative persistently disagreeing with its same-history matrix indicates a tangent consistency question.",
                           "H10 and H11 force agreement is zeroth-order consistency, not equality of their forward tangents.",
                           "Failed or timed-out correctors prove neither root nonexistence nor collapse."])
        with (args.output / "summary.json").open("x", encoding="utf-8") as stream:
            json.dump(summary, stream, default=arc.json_default, indent=2, allow_nan=False)
        emit(dict(kind="terminal", outcome=summary["outcome"], independently_admitted_control_increments=increments), console=True)


if __name__ == "__main__":
    main()
