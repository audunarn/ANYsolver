"""One independent fixed-geometry finite-penalty radial discriminator.

Structural K and prescribed radial traces are declared shared inputs. Contact S
and G are integrated by the retained independent Q1/P1 oracle, never by a
production contact kernel. This convex normal-coordinate problem is a comparator
for the saved moving-contact result, not nonlinear or continuum qualification.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
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
from types import SimpleNamespace

import anysolver
import numpy as np
import scipy
from scipy import linalg, sparse
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_interior_press_dev import build_radial_guided_case
from docs.d1_review_support.d1_two_body_reference_oracle import (
    independent_gap_work, _source_shape, _target_shape, _clip,
)
from docs.d1_review_support.d1_radial_linear_saved_assessment import (
    _audit_gap_coefficients, _checked_inverse, _gamma, _sample_uncertainties,
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


def finite_solve(k, force, a, support, gap0, kappa):
    """Primal semismooth Newton with Armijo energy safeguarding, max 40 steps.

    g=gap0+A*y/S, p=kappa[-g]+, r=K*y-f-A.T*p;
    J=K+kappa*A_active.T*diag(1/S_active)*A_active.
    The all-free structural prediction is the sole initial guess.
    """
    def state(y):
        g = gap0+(a @ y)/support
        p = kappa*np.maximum(-g, 0.)
        r = k @ y-force-a.T @ p
        e = .5*y @ k @ y-force @ y+.5*kappa*np.dot(support, np.minimum(g, 0.)**2)
        return g, p, r, float(e)

    y = linalg.solve(k, force, assume_a="pos")
    history = []
    for iteration in range(MAX_ITERATIONS+1):
        g, p, r, energy = state(y)
        active = g < 0.
        jacobian = k+kappa*(a[active].T/support[active]) @ a[active]
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
            scale += .5*kappa*np.dot(support, np.minimum(cg, 0.)**2)
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


def physical_gap_minimum(model, definition, q, clearance):
    """Exact polynomial minimization on the floating common polygons.

    Q1 minus P1 is bilinear on an axis-aligned source rectangle. Its interior
    stationary point is a saddle when the mixed coefficient is nonzero; affine
    cases attain a minimum on the boundary too. Each polygon edge is quadratic,
    so vertices and edge stationary points exhaust minimum candidates.
    Clipping is the retained independent floating oracle, not production geometry.
    """
    best = dict(minimum_gap_m=float("inf"))
    count = 0
    for sid in definition.surfaces[0].element_ids:
        sn = model.mesh.elements[sid].node_ids
        sx = np.array([(model.mesh.nodes[n].x, model.mesh.nodes[n].y) for n in sn])
        if not np.array_equal(sx, np.array(((sx[0, 0], sx[0, 1]), (sx[1, 0], sx[0, 1]),
                                          (sx[1, 0], sx[2, 1]), (sx[0, 0], sx[2, 1])))):
            raise ValueError("physical gap audit requires rectangular Q1 source cells")
        sq = q[[model.mesh.dof_manager.get_node_dofs(n)[2] for n in sn]]
        for tid in definition.surfaces[1].element_ids:
            tn = model.mesh.elements[tid].node_ids
            tx = np.array([(model.mesh.nodes[n].x, model.mesh.nodes[n].y) for n in tn])
            polygon = _clip(sx, tx)
            if len(polygon) < 3:
                continue
            count += 1
            tq = q[[model.mesh.dof_manager.get_node_dofs(n)[2] for n in tn]]
            values = np.array([clearance+sq[i]-_target_shape(point, tx) @ tq
                               for i, point in enumerate(sx)])
            aa, bb, cc = values[0], values[1]-values[0], values[3]-values[0]
            dd = values[2]-aa-bb-cc
            normalized = (polygon-sx[0])/(sx[2]-sx[0])
            for edge, (first, second) in enumerate(zip(normalized, np.roll(normalized, -1, axis=0))):
                delta = second-first
                quadratic = dd*delta[0]*delta[1]
                linear = bb*delta[0]+cc*delta[1]+dd*(first[0]*delta[1]+first[1]*delta[0])
                parameters = [0., 1.]
                if quadratic != 0.:
                    stationary = -linear/(2*quadratic)
                    if 0. < stationary < 1.:
                        parameters.append(float(stationary))
                for parameter in parameters:
                    xi, eta = first+parameter*delta
                    gap = float(aa+bb*xi+cc*eta+dd*xi*eta)
                    if gap < best["minimum_gap_m"]:
                        best = dict(minimum_gap_m=gap, xy_m=(sx[0]+np.array((xi, eta))*(sx[2]-sx[0])).tolist(),
                                    source_element_id=int(sid), target_element_id=int(tid),
                                    polygon_edge=edge, edge_parameter=parameter)
    best.update(common_polygon_count=count,
                scope="complete Q1-P1 boundary quadratic minimization on independently clipped floating polygons")
    return best


def finite_uncertainty(model, definition, reference, stiffness, free_map, k, force, external,
                       support, work, a, prescribed, q, y, pressure, residual, jacobian, kappa):
    """Checked inverse + exact rational contact-coefficient perturbation bound.

    Shared structural K, constraint/free bases, prescribed q and loads are frozen
    binary-float inputs. Exact supplied binary-XY geometry gives P=G/S and S
    coefficient envelopes. Propagate these through the finite active tangent,
    including support error, and verify all active/inactive signs under the bound.
    """
    n, m = len(q), len(support)
    absolute_free = np.abs(free_map)
    gap_map = work/support[:, None]
    prepared = SimpleNamespace(source_ids=tuple(sorted({node for eid in definition.surfaces[0].element_ids
                               for node in model.mesh.elements[eid].node_ids})), support=support, gap_map=gap_map)
    gap_error, support_error, audit = _audit_gap_coefficients(model, definition, prepared)
    _, inverse, rho, inverse_norm = _checked_inverse(jacobian)
    t = a/support[:, None]
    t_error = gap_error @ absolute_free+_gamma(4*n+4)*(np.abs(gap_map) @ absolute_free+np.abs(t))
    k_error = _gamma(4*n+4)*np.asarray(absolute_free.T @ abs(stiffness) @ absolute_free)
    active = pressure > 0.
    b, eb, s, es = np.abs(t[active]), t_error[active], support[active], support_error[active]
    j_error = k_error+kappa*(b.T @ (s[:, None]*eb)+eb.T @ (s[:, None]*b)
        +eb.T @ (s[:, None]*eb)+(b+eb).T @ (es[:, None]*(b+eb)))
    j_error += _gamma(4*m+4)*(np.abs(k)+kappa*b.T @ (s[:, None]*b))
    coefficient_norm = float(np.max(np.sum(j_error, axis=1)))*(1+_gamma(len(y)))
    eta = float(np.nextafter(inverse_norm*coefficient_norm, np.inf))
    if not np.isfinite(eta) or eta >= .1:
        raise ValueError("finite active coefficient uncertainty unresolved")
    gap_rounding = _gamma(2*n+4)*(abs(reference.gap_m)+np.abs(gap_map) @ np.abs(q))
    gap_envelope = gap_error @ np.abs(q)+gap_rounding
    p_error = kappa*gap_envelope
    contact_error = ((np.abs(gap_map)+gap_error).T @ ((support+support_error)*p_error)
                     +gap_error.T @ (support*pressure)+np.abs(gap_map).T @ (support_error*pressure))
    magnitude = (np.abs(k) @ np.abs(y)+np.abs(force)+np.abs(a).T @ pressure)
    force_operand = absolute_free.T @ (np.abs(external)+abs(stiffness) @ np.abs(prescribed))
    residual_upper = np.abs(residual)+absolute_free.T @ contact_error+_gamma(4*n+4*m+8)*(magnitude+force_operand)
    row_norm = np.sum(np.abs(inverse), axis=1)*(1+_gamma(len(y)))
    base = np.abs(inverse) @ residual_upper+row_norm*rho/(1-rho)*float(np.max(residual_upper))
    y_error = base+eta*float(np.max(base))/(1-eta)
    y_error = np.nextafter(y_error*(1+_gamma(2*len(y)+8)), np.inf)
    q_error = absolute_free @ y_error+_gamma(2*n+4)*(np.abs(prescribed)+absolute_free @ np.abs(y))
    signs = gap_envelope+(np.abs(gap_map)+gap_error) @ q_error
    gap = reference.gap_m+gap_map @ q
    if np.any(np.abs(gap) <= signs) or not np.all(np.isfinite(q_error)):
        raise ValueError("finite active/inactive gap signs unresolved under coefficient envelope")
    sample_error = _sample_uncertainties(model, definition, samples(model, definition, q, reference), q, q_error)
    force_error = float(support @ (kappa*signs)+support_error @ (pressure+kappa*signs))
    return dict(assessed=True, coefficient_audit=audit, inverse_residual_infinity_bound=rho,
                inverse_norm_infinity_bound=inverse_norm, coefficient_perturbation_bound=eta,
                active_set_signs_resolved=True, maximum_pose_uncertainty_m=float(q_error.max()),
                q_uncertainty_m=q_error.tolist(), sample_uncertainty_m=sample_error,
                integrated_force_uncertainty_n=force_error,
                physical_gap_solution_uncertainty_m=float(2*q_error.max()),
                scope="exact rational supplied binary-XY contact coefficients; shared K/bases/load/clearance frozen; no material/model uncertainty")


def continuum_sample_roundoff(reference, point):
    with localcontext() as context:
        context.prec = 70
        ds, dt, load, radius, a = map(Decimal.from_float,
                                    (reference.ds, reference.dt, reference.load_pa, reference.radius_m, reference.contact_radius_m))
        x, y = map(Decimal.from_float, point)
        center = Decimal.from_float(.6)
        r = ((x-center)**2+(y-center)**2).sqrt()
        gap = load/(4*ds)*(radius**2-a**2-2*a**2*(radius/a).ln())
        if r <= a:
            wt = load*(r*r-a*a)/(4*(ds+dt))+load*a*a*(a/radius).ln()/(2*(ds+dt))
            ws = wt-gap
        else:
            wt = load*a*a*(r/radius).ln()/(2*(ds+dt))
            ws = wt+load*(r*r-a*a-2*a*a*(r/a).ln())/(4*ds)-gap
        floats = reference.fields_xy([point])
        return {body: float(abs(value-Decimal.from_float(float(floats[body+"_w"][0])))+Decimal("1e-60"))
                for body, value in (("source", ws), ("target", wt))}


def execute(args, stage, frozen):
    kappa = args.normal_regularization
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
        fixed_p = kappa*np.maximum(-gap, 0.)
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
    y, pressure, gap, residual, jacobian, history = finite_solve(k, force, a, support, gap0, kappa)
    finite_q = prescribed+free_map @ y
    stage("saved_pose_comparisons")
    predicted = pose_record(finite_q, pressure)
    observed = pose_record(actual_q, actual_p)
    hard_record = pose_record(hard_q, hard_z/support)
    stage("candidate_reference_uncertainty")
    uncertainty = finite_uncertainty(model, definition, reference, stiffness, free_map, k, force, external,
                                     support, work, a, prescribed, finite_q, y, pressure, residual, jacobian, kappa)
    stage("candidate_physical_gap")
    physical_gap = physical_gap_minimum(model, definition, finite_q, reference.gap_m)
    physical_gap["solution_uncertainty_m"] = uncertainty["physical_gap_solution_uncertainty_m"]
    physical_gap["convex_nodal_physical_gap_lower_m"] = float(reference.gap_m+np.min(finite_q[source_dofs])
        -np.max(finite_q[target_dofs])-uncertainty["physical_gap_solution_uncertainty_m"])
    physical_gap["lower_bound_scope"] = "nonnegative Q1/P1 partition unity on full represented coverage; nodal lower bound avoids dependence on floating polygon clipping"
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
    candidate_samples = []
    for i, point in enumerate(POINTS):
        rounding = continuum_sample_roundoff(reference, point)
        item = dict(xy_m=list(point))
        for bi, body in enumerate(("source", "target")):
            raw = predicted["samples"][i]
            exact = abs(raw[body+"_continuum_uz_m"])
            total = uncertainty["sample_uncertainty_m"][bi][i]+rounding[body]
            upper = float(np.nextafter((abs(raw[body+"_uz_m"]-raw[body+"_continuum_uz_m"])+total)/(exact-rounding[body]), np.inf))
            item[body] = dict(raw_relative_error=raw[body+"_relative_continuum_error"],
                              solution_uncertainty_m=uncertainty["sample_uncertainty_m"][bi][i],
                              analytical_roundoff_envelope_m=rounding[body],
                              accounted_relative_error_upper=upper, gate=.02, preflight_pass=bool(upper <= .02))
        candidate_samples.append(item)
    force_upper = (abs(predicted["integrated_pressure_n"]-reference.force_n)+uncertainty["integrated_force_uncertainty_n"])/reference.force_n
    physical_lower = physical_gap["convex_nodal_physical_gap_lower_m"]
    candidate_pass = bool(all(item["target"]["preflight_pass"] for item in candidate_samples)
                          and force_upper <= .02 and physical_lower >= -50e-6)
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
                candidate_reference_uncertainty=uncertainty, candidate_physical_gap=physical_gap,
                candidate_accounted_samples=candidate_samples,
                candidate_preflight=dict(target_samples_with_uncertainty_pass=bool(all(item["target"]["preflight_pass"] for item in candidate_samples)),
                    force_relative_error_upper=force_upper, force_gate=.02,
                    minimum_physical_gap_lower_m=physical_lower, gap_gate_m=-50e-6,
                    candidate_eligible_for_coupled_check=bool(candidate_pass and passed), accepted=False),
                saved_nonlinear_model_comparison=dict(candidate_kappa_pa_per_m=kappa,
                    saved_kappa_pa_per_m=actual["normal_regularization_pa_per_m"],
                    same_penalty_model=bool(kappa == actual["normal_regularization_pa_per_m"]),
                    scope="different-model response sensitivity when kappa differs; no same-kappa agreement gate applied"),
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
                physical_gap_scope=physical_gap["scope"],
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
    parser.add_argument("--normal-regularization", type=float, default=KAPPA)
    args = parser.parse_args()
    if args.output.exists() or args.inputs_output.exists():
        parser.error("exclusive output already exists")
    if not np.isfinite(args.normal_regularization) or args.normal_regularization <= 0:
        parser.error("normal regularization must be finite and positive")
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
                  kappa_pa_per_m=args.normal_regularization, frozen_force_scale_n=FORCE_SCALE_N,
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
