"""One independent fixed-geometry finite-penalty radial discriminator.

Structural K and prescribed radial traces are declared shared inputs. Contact S
and G are integrated by the retained independent Q1/P1 oracle, never by a
production contact kernel. This convex normal-coordinate problem is a comparator
for the saved moving-contact result, not nonlinear or continuum qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import anysolver
import numpy as np
import scipy
from scipy import linalg, sparse
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_interior_press_dev import build_radial_guided_case
from docs.d1_review_support.d1_two_body_reference_oracle import (
    independent_gap_work, _source_shape, _target_shape,
)

KAPPA = 1e7
FORCE_SCALE_N = .08
FORCE_GATE = 1e-6
PROJECTION_GATE = 1e-6
SOLVE_RELATIVE_FORCE = 1e-11
MAX_ITERATIONS = 40
POINTS = ((.6, .6), (.6, .85), (.6, 1.))


def identity(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def csr_record(matrix):
    matrix = sparse.csr_matrix(matrix)
    matrix.eliminate_zeros()  # Exact zeros only: no support/mode threshold.
    return dict(format="csr", shape=list(matrix.shape), data=matrix.data.tolist(),
                indices=matrix.indices.tolist(), indptr=matrix.indptr.tolist())


def samples(model, definition, q, reference):
    result = []
    for point in POINTS:
        item = dict(xy_m=list(point))
        for side_index, side in enumerate(definition.surfaces):
            matches = []
            for eid in side.element_ids:
                nodes = model.mesh.elements[eid].node_ids
                xy = np.array([(model.mesh.nodes[n].x, model.mesh.nodes[n].y) for n in nodes])
                basis = (_source_shape(np.array(point), xy) if side_index == 0 else
                         _target_shape(np.array(point), xy))
                if np.min(basis) >= -1e-12 and np.max(basis) <= 1.+1e-12:
                    local = q[[model.mesh.dof_manager.get_node_dofs(n)[2] for n in nodes]]
                    matches.append(float(basis @ local))
            if not matches or np.ptp(matches) > 1e-12:
                raise ValueError("independent sample uncovered or discontinuous")
            body = "source" if side_index == 0 else "target"
            exact = float(reference.fields_xy([point])[body+"_w"][0])
            item[body+"_uz_m"] = matches[0]
            item[body+"_continuum_uz_m"] = exact
            item[body+"_relative_continuum_error"] = abs(matches[0]-exact)/abs(exact)
        item["parallel_skin_gap_m"] = reference.gap_m+item["source_uz_m"]-item["target_uz_m"]
        result.append(item)
    return result


def finite_solve(k, force, a, support, gap0):
    """Primal semismooth Newton with Armijo energy safeguarding, max 40 steps.

    g=gap0+A*y/S, p=kappa[-g]+, r=K*y-f-A.T*p;
    J=K+kappa*A_active.T*diag(1/S_active)*A_active.
    The all-free structural prediction is the sole initial guess.
    """
    def state(y):
        g = gap0+(a @ y)/support
        p = KAPPA*np.maximum(-g, 0.)
        r = k @ y-force-a.T @ p
        e = .5*y @ k @ y-force @ y+.5*KAPPA*np.dot(support, np.minimum(g, 0.)**2)
        return g, p, r, float(e)

    y = linalg.solve(k, force, assume_a="pos")
    history = []
    for iteration in range(MAX_ITERATIONS+1):
        g, p, r, energy = state(y)
        active = g < 0.
        jacobian = k+KAPPA*(a[active].T/support[active]) @ a[active]
        relative = float(np.linalg.norm(r)/FORCE_SCALE_N)
        row = dict(iteration=iteration, energy_j=energy, relative_force_residual=relative,
                   active_modes=int(active.sum()), minimum_gap_m=float(g.min()))
        history.append(row)
        if relative <= SOLVE_RELATIVE_FORCE:
            correction = linalg.solve(jacobian, r, assume_a="pos")
            gap_correction = np.abs(a @ correction)/support
            row.update(estimated_maximum_newton_gap_correction_m=float(gap_correction.max()),
                       estimated_active_set_stable=bool(np.all(np.abs(g) > gap_correction)))
            return y, p, g, r, jacobian, history
        if iteration == MAX_ITERATIONS:
            raise RuntimeError("fixed-geometry semismooth iteration cap reached")
        delta = linalg.solve(jacobian, -r, assume_a="pos")
        slope = float(r @ delta)
        if not np.isfinite(slope) or slope >= 0:
            raise RuntimeError("Newton direction is not an energy descent")
        alpha = 1.
        for backtrack in range(41):
            candidate = y+alpha*delta
            cg, cp, cr, ce = state(candidate)
            # Roundoff bound applies to evaluated quadratic/storage operands;
            # near equal energies additionally require decreasing force residual.
            scale = abs(.5*candidate @ k @ candidate)+abs(force @ candidate)
            scale += .5*KAPPA*np.dot(support, np.minimum(cg, 0.)**2)
            allowance = 64*np.finfo(float).eps*max(scale, np.finfo(float).tiny)
            armijo = ce <= energy+1e-4*alpha*slope
            roundoff = (ce <= energy+allowance and np.linalg.norm(cr) < np.linalg.norm(r))
            if armijo or roundoff:
                row.update(step_length=alpha, energy_backtracks=backtrack,
                           armijo_satisfied=bool(armijo), energy_roundoff_allowance_j=float(allowance))
                y = candidate
                break
            alpha *= .5
        else:
            raise RuntimeError("fixed-geometry energy line search failed")
    raise AssertionError("unreachable")


def execute(args, stage, frozen):
    actual = json.loads(args.actual.read_text(encoding="utf-8"))
    hard = json.loads(args.hard.read_text(encoding="utf-8"))
    assessment = json.loads(args.hard_assessment.read_text(encoding="utf-8"))
    if assessment["input_sha256"] != identity(args.hard)["sha256"]:
        raise ValueError("hard q input does not match retained assessment")
    if not hard.get("steps") or not hard["steps"][-1].get("displacements"):
        raise ValueError("retained hard-reference q payload missing; no reconstruction authorized")
    for saved in (actual, hard):
        if saved["target_cells"] != 12 or saved["target_right_x_m"] != 1.297:
            raise ValueError("frozen 12/12 right=1.297 fixture mismatch")
        if saved.get("target_y0_m", -.113) != -.113:
            raise ValueError("frozen target y0 mismatch")
    stage("shared_structural_fixture")
    model, definition, settings, program, reference, metadata = build_radial_guided_case(
        target_cells=12, target_y0_m=-.113, target_right_x_m=1.297)
    if reference.load_pa != FORCE_SCALE_N:
        raise ValueError("frozen .08N force scale changed")
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    ndof = model.mesh.dof_manager.total_dofs
    _, _, transform, offset, _, _ = build_constraint_transformation(stiffness, np.zeros(ndof), model)
    if np.linalg.norm(offset) != 0:
        raise ValueError("homogeneous structural constraints required")
    controls = np.zeros((2, ndof))
    for row, control in enumerate(program.controls):
        for node, dof, coefficient in control.terms:
            if dof != "uz":
                raise ValueError("guided fixed-normal controls required")
            controls[row, model.mesh.dof_manager.get_node_dofs(node)[2]] = coefficient
    reduced_controls = np.asarray(controls @ transform)
    null = linalg.null_space(reduced_controls)
    free_map = np.asarray(transform @ null)
    k = free_map.T @ stiffness @ free_map
    linalg.cholesky(k)
    targets = np.asarray(program.target_at(2))
    prescribed = np.asarray(transform @ (reduced_controls.T @ linalg.solve(
        reduced_controls @ reduced_controls.T, targets, assume_a="pos")))
    external = np.zeros(ndof)
    for load, value in zip(program.nodal_forces, program.force_values_at(2), strict=True):
        if load.dof != "uz":
            raise ValueError("normal loads required")
        external[model.mesh.dof_manager.get_node_dofs(load.node_id)[2]] += value
    force = free_map.T @ (external-stiffness @ prescribed)
    stage("independent_normal_integrals")
    source_ids, support, work, area = independent_gap_work(model, definition, 0.)
    a = work @ free_map
    gap0 = reference.gap_m+(work @ prescribed)/support
    actual_q = np.asarray(actual["displacements"], dtype=float)
    hard_q = np.asarray(hard["steps"][-1]["displacements"], dtype=float)
    contact = actual["history"][-1]["contact"]
    if list(source_ids) != contact["source_pressure_node_ids"]:
        raise ValueError("saved pressure node ordering mismatch")
    actual_p = np.asarray(contact["numerical_pressure_pa"])
    actual_s = np.asarray(contact["reference_support_m2"])
    hard_z = np.asarray(hard["steps"][-1]["nodal_force_n"])
    if actual_q.shape != (ndof,) or hard_q.shape != (ndof,):
        raise ValueError("saved full-coordinate q dimension mismatch")
    if actual_p.shape != support.shape or hard_z.shape != support.shape:
        raise ValueError("saved pressure dimension mismatch")
    source_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in source_ids]
    target_ids = sorted({n for eid in definition.surfaces[1].element_ids
                         for n in model.mesh.elements[eid].node_ids})
    target_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in target_ids]
    if np.max(abs(work[:, source_dofs].sum(axis=1)-support)) > 1e-12:
        raise ValueError("source partition reproduction failed")
    if np.max(abs(work[:, target_dofs].sum(axis=1)+support)) > 1e-12:
        raise ValueError("target partition reproduction failed")
    projection_gram = free_map.T @ free_map

    def pose_record(q, pressure):
        y = linalg.solve(projection_gram, free_map.T @ (q-prescribed), assume_a="pos")
        defect = q-prescribed-free_map @ y
        gap = reference.gap_m+(work @ q)/support
        full_residual = stiffness @ q-external-work.T @ pressure
        reduced_residual = np.asarray(transform.T @ full_residual)
        reactions = linalg.solve(reduced_controls @ reduced_controls.T,
                                 reduced_controls @ reduced_residual, assume_a="pos")
        source_contact = (work.T @ pressure)[source_dofs]
        target_contact = (work.T @ pressure)[target_dofs]
        fixed_p = KAPPA*np.maximum(-gap, 0.)
        return dict(displacements_m=q.tolist(), normal_displacements_m=q[source_dofs+target_dofs].tolist(),
                    pressure_pa=pressure.tolist(), normalized_weighted_gap_m=gap.tolist(),
                    integrated_pressure_n=float(support @ pressure),
                    source_physical_contact_force_n=float(source_contact.sum()),
                    target_physical_contact_force_n=float(target_contact.sum()),
                    source_contact_nodal_normal_n=source_contact.tolist(),
                    target_contact_nodal_normal_n=target_contact.tolist(),
                    control_reaction_n=reactions.tolist(),
                    reduced_force_residual_n=(free_map.T @ full_residual).tolist(),
                    relative_free_force_residual=float(np.linalg.norm(free_map.T @ full_residual)/FORCE_SCALE_N),
                    max_pose_projection_defect_m=float(np.max(abs(defect))),
                    relative_pose_projection_defect=float(np.max(abs(defect))/reference.gap_m),
                    relative_control_error=float(np.max(abs(controls @ q-targets))/reference.gap_m),
                    fixed_finite_constitutive_pressure_pa=fixed_p.tolist(),
                    fixed_finite_constitutive_relative_force_defect=float(support @ abs(pressure-fixed_p)/FORCE_SCALE_N),
                    samples=samples(model, definition, q, reference))

    stage("finite_primal_solve")
    y, pressure, gap, residual, jacobian, history = finite_solve(k, force, a, support, gap0)
    finite_q = prescribed+free_map @ y
    stage("saved_pose_comparisons")
    predicted = pose_record(finite_q, pressure)
    observed = pose_record(actual_q, actual_p)
    hard_record = pose_record(hard_q, hard_z/support)
    # Physical minimum gap: Q1-P1 on each common polygon can have interior
    # extrema. Only the declared three point gaps and weak gaps are reported;
    # no vertex-only minimum is substituted for an independent physical bound.
    eigk, eigj = linalg.eigvalsh(k), linalg.eigvalsh(jacobian)
    summary = []
    for i, point in enumerate(POINTS):
        item = dict(xy_m=list(point))
        for body in ("source", "target"):
            values = [r["samples"][i][body+"_uz_m"] for r in (predicted, observed, hard_record)]
            item[body] = dict(finite_prediction_m=values[0], nonlinear_saved_m=values[1],
                              hard_saved_m=values[2], finite_minus_hard_m=values[0]-values[2],
                              nonlinear_minus_finite_m=values[1]-values[0],
                              continuum_m=predicted["samples"][i][body+"_continuum_uz_m"],
                              finite_relative_continuum_error=predicted["samples"][i][body+"_relative_continuum_error"],
                              nonlinear_relative_continuum_error=observed["samples"][i][body+"_relative_continuum_error"],
                              hard_relative_continuum_error=hard_record["samples"][i][body+"_relative_continuum_error"])
        summary.append(item)
    projection_checks = {label: bool(rec["relative_pose_projection_defect"] <= PROJECTION_GATE and
                                    rec["relative_control_error"] <= PROJECTION_GATE)
                         for label, rec in (("finite", predicted), ("nonlinear_saved", observed),
                                            ("hard_saved", hard_record))}
    passed = bool(predicted["relative_free_force_residual"] <= FORCE_GATE and all(projection_checks.values()))
    return dict(status="development_reference_consistent" if passed else "development_reference_inconsistency",
                accepted=False, released=False, mathematical_scope=frozen["mathematical_scope"],
                inputs=frozen, fixture_metadata=metadata, shared_structural_operator=True,
                production_contact_calls=0, independent_overlap_area_m2=area,
                source_node_ids=list(source_ids), target_node_ids=target_ids,
                joint_normal_global_dof_indices=source_dofs+target_dofs,
                nodes=[dict(id=n, xyz_m=[node.x, node.y, node.z]) for n, node in sorted(model.mesh.nodes.items())],
                elements=[dict(id=eid, node_ids=list(model.mesh.elements[eid].node_ids))
                          for side in definition.surfaces for eid in side.element_ids],
                dimensions=dict(full=ndof, structural=transform.shape[1], free_normal=k.shape[0], pressure=len(support)),
                matrix_condition=dict(reduced_structural_eigenvalue_min_n_per_m=float(eigk[0]),
                                      reduced_structural_eigenvalue_max_n_per_m=float(eigk[-1]),
                                      reduced_structural_condition_2=float(eigk[-1]/eigk[0]),
                                      final_active_tangent_eigenvalue_min_n_per_m=float(eigj[0]),
                                      final_active_tangent_eigenvalue_max_n_per_m=float(eigj[-1]),
                                      final_active_tangent_condition_2=float(eigj[-1]/eigj[0])),
                support_m2=support.tolist(), work_m2=csr_record(work), structural_k_n_per_m=csr_record(stiffness),
                structural_transform=csr_record(transform), free_map=csr_record(free_map),
                reduced_structural_k_n_per_m=k.tolist(), reduced_work_a_m2=a.tolist(),
                controls=csr_record(controls), final_control_targets_m=targets.tolist(),
                final_prescribed_q_m=prescribed.tolist(), external_load_n=external.tolist(),
                reduced_external_force_n=force.tolist(), prescribed_gap0_m=gap0.tolist(),
                newton_history=history, finite_prediction=predicted, nonlinear_saved=observed,
                hard_saved=hard_record, retained_hard_assessment=assessment,
                nonlinear_reported_control_reaction_n=actual["history"][-1]["reaction_generalized"],
                nonlinear_saved_support_m2=actual_s.tolist(),
                nonlinear_saved_weighted_gap_m=contact["normalized_weighted_gap_m"],
                force_comparison=dict(continuum_contact_n=reference.force_n,
                    finite_n=predicted["integrated_pressure_n"], nonlinear_saved_n=float(actual_s @ actual_p),
                    nonlinear_reported_n=contact["integration_force"][2], hard_saved_n=float(hard_z.sum()),
                    finite_relative_continuum_error=abs(predicted["integrated_pressure_n"]-reference.force_n)/reference.force_n),
                displacement_comparison=dict(maximum_normal_nonlinear_minus_finite_m=float(np.max(abs(actual_q[source_dofs+target_dofs]-finite_q[source_dofs+target_dofs]))),
                    maximum_normal_finite_minus_hard_m=float(np.max(abs(finite_q[source_dofs+target_dofs]-hard_q[source_dofs+target_dofs])))),
                pressure_comparison=dict(weighted_nonlinear_minus_finite_relative_force=float(support @ abs(actual_p-pressure)/FORCE_SCALE_N),
                    maximum_nonlinear_minus_finite_pa=float(np.max(abs(actual_p-pressure)))),
                sample_comparison=summary, checks=dict(force_relative_gate=FORCE_GATE,
                    pose_projection_relative_reference_gap_gate=PROJECTION_GATE,
                    finite_force_pass=bool(predicted["relative_free_force_residual"] <= FORCE_GATE),
                    pose_projection_pass=projection_checks, reference_consistent=passed),
                physical_gap_scope="independent weak gaps and three declared point gaps; no global physical minimum certificate",
                contact_signs="work.T*p is physical contact force: source positive normal, target negative; residual Kq-F-work.T*p",
                limitations=["fixed reference overlap/projection/normal, linear shared structural K and final fixed traces only",
                             "does not test exact moving-support derivative terms or nonlinear stability",
                             "hard saved pressure need not satisfy the finite constitutive law",
                             "no continuum/scientific acceptance, penalty sweep, mesh change or new coupled solve"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--hard", type=Path, required=True)
    parser.add_argument("--hard-assessment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.inputs_output.exists():
        parser.error("exclusive output already exists")
    start = time.perf_counter()

    def stage(name):
        print(json.dumps(dict(stage=name, elapsed_seconds=time.perf_counter()-start)), flush=True)

    sources = {name: identity(inspect.getsourcefile(obj)) for name, obj in
               (("runner", main), ("fixture", build_radial_guided_case),
                ("independent_integrals", independent_gap_work), ("shared_stiffness", assemble_stiffness_matrix),
                ("shared_constraints", build_constraint_transformation))}
    for relative in ("docs/d1_review_support/d1_radial_two_body_reference.py",
                     "scripts/general_contact_d1_mixed_mesh_jet2_schur_press.py",
                     "docs/d1_review_support/d1_radial_linear_saved_assessment.py"):
        sources[relative] = identity(relative)
    frozen = dict(purpose="finite-kappa bias versus spatial/operator/trace discrepancy",
                  mathematical_scope="E=.5*y.T*Kr*y-fr.T*y+.5*kappa*sum(S*[-(g0+A*y/S)]+^2); fixed-geometry both-body G",
                  kappa_pa_per_m=KAPPA, frozen_force_scale_n=FORCE_SCALE_N,
                  solve_relative_force=SOLVE_RELATIVE_FORCE, force_relative_gate=FORCE_GATE,
                  pose_projection_relative_reference_gap_gate=PROJECTION_GATE,
                  max_iterations=MAX_ITERATIONS, maximum_energy_backtracks=40,
                  resource_caps=dict(seconds=180, process_tree_bytes=1073741824),
                  fixture=dict(source_cells=[12, 12], target_cells=[12, 12], target_right_x_m=1.297,
                               target_y0_m=-.113, final_step=2, sample_points_m=POINTS),
                  input_files={name: identity(path) for name, path in
                               (("actual", args.actual), ("hard", args.hard), ("hard_assessment", args.hard_assessment))},
                  sources=sources, argv=sys.argv, environment=dict(executable=sys.executable,
                  python=sys.version, platform=platform.platform(), numpy=np.__version__, scipy=scipy.__version__,
                  anysolver_path=anysolver.__file__, anysolver_sha256=identity(anysolver.__file__)["sha256"],
                  threads={name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                  git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  production_source_hashes={str(path): identity(path)["sha256"]
                                            for path in sorted(Path("src/anysolver").rglob("*.py"))},
                  accepted=False, released=False)
    with args.inputs_output.open("x", encoding="utf-8") as stream:
        json.dump(frozen, stream, indent=2)
    stage("frozen_inputs_saved")
    try:
        result = execute(args, stage, frozen)
    except Exception as exc:
        result = dict(status="development_reference_failure", accepted=False, released=False,
                      inputs=frozen, error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
    result["elapsed_seconds"] = time.perf_counter()-start
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({key: result[key] for key in ("status", "elapsed_seconds")}), flush=True)
    if result["status"] != "development_reference_consistent":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
