"""S3/S3 force-control code verification against fixed-geometry P1 integrals.

Structural K is an explicitly shared input; rectangle clipping, support, mass
and all active-set solves here are independent of production contact kernels.
The 10 nm starting clearance is a new small-motion fixture, not a regrade of
the recorded 100 micrometre Q4 cut-front cases.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import time
import traceback
import numpy as np
from anysolver import (BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSurface, ContactSolverSettings, ContactPathControl, ContactPathNodalForce,
    ContactPathProgram, create_shell_element, solve_static_nonlinear)
from anysolver.boundary import LoadCase
from anysolver.fe_core import FEModel
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.nonlinear_static import _assemble_nonlinear_system, _discard_nonlinear_state_candidate
from docs.d1_review_support.d1_guided_reaction_wrench import guided_wrench_diagnostics
from docs.d1_review_support.d2_projected_penalty_shell_dev import file_identity, json_default

XY = np.array(((.1, .1), (.6, .1), (1.1, .1), (.1, 1.1), (.6, 1.1), (1.1, 1.1)))
CELLS = ((1, 2, 4), (2, 5, 4), (2, 3, 5), (3, 6, 5))


def build(target_extent=1., deformable_target=False):
    m = FEModel("d2_s3_projected_small_motion")
    m.add_material("elastic", 1e5, .3, density=1.)
    for n, (x, y) in enumerate(XY, 1): m.add_node(n, float(x), float(y), .04+1e-8)
    for n, (x, y) in enumerate(((0., 0.), (target_extent, 0.),
            (target_extent, target_extent), (0., target_extent)), 7): m.add_node(n, x, y, 0.)
    for eid, ids in enumerate(CELLS+((7, 8, 10), (8, 9, 10)), 1):
        m.add_element(eid, create_shell_element(eid, ids, "elastic", thickness=.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0., 0., 1.),
            reference_surface_offset=.01 if eid > 4 else 0.))
    for name, ids in (("left", (1, 4)), ("target", (7, 8, 9, 10))):
        m.add_boundary_condition(BoundaryCondition(name, ids,
            {d: 0. for d in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    if deformable_target:
        m.boundary_conditions = [replace(bc, node_ids=(7, 10))
            if bc.name == "target" else bc for bc in m.boundary_conditions]
        m.add_boundary_condition(BoundaryCondition("target_guided", (8, 9),
            {d: 0. for d in ("ux", "uy", "rx", "ry", "rz")}))
    m.add_boundary_condition(BoundaryCondition("guided", (2, 3, 5, 6),
        {d: 0. for d in ("ux", "uy", "rx", "ry", "rz")}))
    d = ContactDefinition(surfaces=(ContactSurface("source", (1, 2, 3, 4), "bottom"),
        ContactSurface("target", (5, 6), "top")), rigid_bodies=(), interactions=(
        ContactInteraction("pair", "source", "target", 1e7, 5e-5, normal_law="projected_penalty"),))
    s = ContactSolverSettings(pair_motion="general", normal_discretization="primal_mortar",
        general_s3_difference_step=2e-5, maximum_general_s3_energy_evaluations=5000,
        general_s3_differentiation="jet2_s3_dev", augmentation_support_resolution="exact")
    load = LoadCase("half_newton_press")
    for node in (3, 6): load.add_nodal_load(node, forces=np.array([0., 0., -.25]))
    return m, d, s, load


def clip_rectangle(vertices, upper=1.):
    poly = [np.array(v, dtype=float) for v in vertices]
    for axis, bound, lower in ((0, 0., True), (0, upper, False), (1, 0., True), (1, upper, False)):
        result = []
        if not poly: break
        previous = poly[-1]
        inside_prev = previous[axis] >= bound if lower else previous[axis] <= bound
        for current in poly:
            inside = current[axis] >= bound if lower else current[axis] <= bound
            if inside != inside_prev:
                fraction = (bound-previous[axis])/(current[axis]-previous[axis])
                result.append(previous+fraction*(current-previous))
            if inside: result.append(current)
            previous, inside_prev = current, inside
        poly = result
    return np.asarray(poly)


def integrals(upper=1.):
    support, mass, cells = np.zeros(6), np.zeros((6, 6)), []
    for ids in CELLS:
        ix = np.array(ids)-1
        vertices = XY[ix]
        poly = clip_rectangle(vertices, upper)
        basis = np.linalg.inv(np.c_[vertices, np.ones(3)])
        local_s, local_m = np.zeros(3), np.zeros((3, 3))
        for j in range(1, len(poly)-1):
            tri = np.array([poly[0], poly[j], poly[j+1]])
            area = abs(float(np.linalg.det(np.stack((tri[1]-tri[0], tri[2]-tri[0])))))/2
            values = np.c_[tri, np.ones(3)]@basis
            sums = values.sum(axis=0)
            local_s += area*sums/3
            local_m += area*(np.outer(sums, sums)+values.T@values)/12
        support[ix] += local_s
        mass[np.ix_(ix, ix)] += local_m
        cells.append({"ids": ids, "clipped_vertices_xy_m": poly.tolist(), "basis_coefficients": basis.tolist()})
    area = (min(upper, 1.1)-.1)**2
    if not np.all(support > 0) or abs(support.sum()-area) > 1e-13 or np.linalg.norm(mass@np.ones(6)-support) > 1e-13:
        raise ValueError("independent P1 integrals inconsistent")
    return support, mass, cells


def reference(model, support, mass, prescribed_force=None):
    k, _ = assemble_stiffness_matrix(model)
    free = np.array([model.mesh.dof_manager.get_node_dofs(n)[2] for n in (2, 3, 5, 6)])
    kff = k.toarray()[np.ix_(free, free)]
    columns = [1, 2, 4, 5]
    g = mass[:, columns]
    force = np.array([0., -.25, 0., -.25]) if prescribed_force is None else np.asarray(prescribed_force)
    answers = []
    for mask in range(64):
        active = np.array([bool(mask & (1 << i)) for i in range(6)])
        a = kff+1e7*(g[active].T/support[active])@g[active]
        rhs = force-1e7*1e-8*g[active].T@np.ones(active.sum())
        q = np.linalg.solve(a, rhs)
        gap = 1e-8+g@q/support
        p = 1e7*np.maximum(-gap, 0.)
        residual = kff@q-g.T@p-force
        if np.any(gap[active] > 1e-14) or np.any(gap[~active] < -1e-14) or np.linalg.norm(residual) > 1e-10: continue
        all_q = np.zeros(6)
        all_q[columns] = q
        answers.append({"source_normal_displacements_m": all_q.tolist(), "pressure_pa": p.tolist(),
            "active_nodes": (np.flatnonzero(active)+1).tolist(), "free_residual_n": residual.tolist(),
            "contact_force_n": float(support@p), "kff": kff.tolist(), "condition_number": float(np.linalg.cond(a))})
    if len(answers) != 1: raise ValueError(f"independent active-set reference has {len(answers)} solutions")
    return answers[0]


def assess(model, definition, settings, result, support, oracle, cells, force, force_scale,
           deformable_target=False):
    u = result.displacements
    manager = GeneralS3PatchManager(model, definition, settings)
    contact, _, cert = manager.evaluate(u, tangent=False)
    source, target = manager._positions(u)
    work = manager.law.work(source, target, manager.normal_multipliers, tangent=False)
    physical = -np.asarray(work.residual).reshape(-1, 3)
    bodies, start = {}, 0
    origin = np.array([.6, .6, 0.])
    for name, ids, positions in (("source", manager.law.source_node_ids, source), ("target", manager.law.target_node_ids, target)):
        local = physical[start:start+len(ids)]
        bodies[name] = {"node_ids": list(ids), "physical_contact_force": local.sum(axis=0),
            "physical_contact_moment": np.cross(positions-origin, local).sum(axis=0)}
        start += len(ids)
    internal, _, trials = _assemble_nonlinear_system(model, u, result.element_states, 5,
        tangent=False, kinematics="von_karman", require_full_coordinates=True)
    _discard_nonlinear_state_candidate(trials)
    _discard_nonlinear_state_candidate(result.element_states)
    external = np.zeros(len(u))
    force_nodes = tuple(range(1, 11)) if deformable_target else (2, 3, 5, 6)
    for n, value in zip(force_nodes, force, strict=True):
        external[model.mesh.dof_manager.get_node_dofs(n)[2]] = value
    free_nodes = (2, 3, 5, 6, 8, 9) if deformable_target else (2, 3, 5, 6)
    free = np.eye(len(u))[:, [model.mesh.dof_manager.get_node_dofs(n)[2] for n in free_nodes]]
    wrench = guided_wrench_diagnostics(model, u, internal, contact, external, free,
        physical_contact_force=sum((b["physical_contact_force"] for b in bodies.values()), np.zeros(3)),
        physical_contact_moment=sum((b["physical_contact_moment"] for b in bodies.values()), np.zeros(3)),
        origin=origin, force_scale_n=force_scale, moment_scale_nm=force_scale, bodies=bodies)
    q = np.array([u[model.mesh.dof_manager.get_node_dofs(n)[2]] for n in range(1, 7)])
    gaps = []
    target_q = np.array([u[model.mesh.dof_manager.get_node_dofs(n)[2]] for n in range(7, 11)])
    for cell in cells:
        if deformable_target:
            values = np.asarray(cell["source_values"])
            target_values = np.asarray(cell["target_values"])
            gaps.extend((1e-8+values@q[cell["source_indices"]]
                -target_values@target_q[cell["target_indices"]]).tolist())
        else:
            ix = np.array(cell["ids"])-1
            values = np.c_[np.asarray(cell["clipped_vertices_xy_m"]), np.ones(len(cell["clipped_vertices_xy_m"]))]@np.asarray(cell["basis_coefficients"])
            gaps.extend((1e-8+values@q[ix]).tolist())
    pressure_by_id = dict(zip(cert.source_pressure_node_ids, cert.numerical_pressure_pa, strict=True))
    pressure = np.array([pressure_by_id[n] for n in range(1, 7)])
    qref = np.asarray(oracle["normal_displacements_m"][:6] if deformable_target
        else oracle["source_normal_displacements_m"])
    pref = np.asarray(oracle["pressure_pa"])
    compared = {"normal_displacement_relative": float(np.linalg.norm(q-qref)/np.linalg.norm(qref)),
        "normal_pressure_relative": float(np.linalg.norm(pressure-pref)/np.linalg.norm(pref)),
        "contact_force_relative": abs(float(bodies["source"]["physical_contact_force"][2])-oracle["contact_force_n"])/force_scale}
    normal_work = None
    if deformable_target:
        compared["target_normal_displacement_relative"] = float(
            np.linalg.norm(target_q-np.asarray(oracle["normal_displacements_m"])[6:])
            /np.linalg.norm(np.asarray(oracle["normal_displacements_m"])[6:]))
        normal_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in range(1, 11)]
        full_normal_contact = contact[normal_dofs]
        independent_normal_contact = -np.asarray(oracle["G"]).T@pressure
        compared["full_normal_contact_residual_relative"] = float(
            np.linalg.norm(full_normal_contact-independent_normal_contact)/force_scale)
        directions = np.array([[1., -.2, .3, -.4, .5, -.6, 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., .7, -.8, .9, -1.],
            [.2, 0., 0., -.4, 0., 0., -.1, 0., 0., .3]])
        normal_work = {"virtual_displacements_m": directions.tolist(),
            "production_virtual_work_j": (directions@full_normal_contact).tolist(),
            "independent_virtual_work_j": (directions@independent_normal_contact).tolist(),
            "work_scale_j": force_scale,
            "relative_error": float(np.max(abs(directions@(full_normal_contact-independent_normal_contact)))/force_scale)}
        compared["both_body_prescribed_row_normal_work_relative"] = normal_work["relative_error"]
    keys = ("balance_relative_force", "balance_relative_moment", "contact_conversion_max_scaled", "structural_internal_max_scaled")
    max_wrench = max([wrench[k] for k in keys]+[wrench["constraint_reconstruction_relative_force"]]+
        [b[k] for b in wrench["bodies"].values() for k in keys])
    checks = {"fixed_geometry_normal_reference": max(compared.values()) <= 1e-6,
        "both_body_wrench": max_wrench <= 1e-6, "physical_gap": min(gaps)-128*np.finfo(float).eps >= -5e-5,
        "production_gap": bool(cert.gap_tolerance_met), "all_six_supports_retained": len(pressure) == 6 and bool(np.all(np.asarray(cert.reference_support_m2) > 0)),
        "nonnegative_pressure": bool(np.all(pressure >= 0)), "zero_multipliers": bool(np.all(manager.normal_multipliers == 0))}
    return {"certificate": cert.to_dict(), "wrench": wrench, "comparison": compared,
        "both_body_normal_virtual_work": normal_work,
        "independent_target_normal_gap_m": min(gaps), "checks": checks,
        "limits": "fixed-XY/vertical-normal oracle; tangential geometry and general continuum accuracy outside this comparison"}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force-path", action="store_true",
        help="route the same load through two zero in-plane path controls")
    parser.add_argument("--target-extent", type=float, default=1.,
        help="upper x/y of target square; 1.4 covers the source faces")
    parser.add_argument("--manufactured", action="store_true",
        help="independent manufactured normal field on covered source, not point-load accuracy")
    parser.add_argument("--deformable-target", action="store_true",
        help="manufactured two-body code fixture with target8/9 normal motion")
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    if args.target_extent not in (1., 1.4):
        parser.error("registered development fixtures use target extent1.0 or1.4")
    if args.manufactured and args.target_extent != 1.4:
        parser.error("manufactured code check uses the covered-source fixture")
    if args.deformable_target and not args.manufactured:
        parser.error("deformable target requires the independent manufactured code fixture")
    runner_snapshot = args.output.with_suffix(".runner.source.py")
    if runner_snapshot.exists(): raise FileExistsError(runner_snapshot)
    runner_snapshot.write_bytes(Path(__file__).read_bytes())
    started = time.perf_counter()
    record = {"accepted": False, "released": False, "kind": "s3_s3_projected_penalty_force_code_verification_development",
        "adapter": file_identity(__file__), "production": {name: file_identity(Path("src/anysolver")/name) for name in (
            "nonlinear_static.py", "general_contact/core.py", "general_contact/s3_patch_static.py",
            "general_contact/s3_patch_augmented.py", "general_contact/s3_overlap_derivatives.py",
            "general_contact/triangle_mortar_energy.py", "general_contact/static_path.py")},
        "inputs": {"initial_clearance_m": 1e-8, "normal_regularization_pa_per_m": 1e7, "force_n": .5,
            "gap_budget_m": 5e-5, "code_comparison_relative": 1e-6, "force_and_moment_scales": [.5, .5],
            "time_cap_s": 180, "memory_cap_bytes": 1000000000}}
    try:
        model, definition, settings, load = build(args.target_extent, args.deformable_target)
        record["inputs"]["target_extent_m"] = args.target_extent
        record["inputs"]["deformable_target"] = args.deformable_target
        program = None
        if args.force_path:
            model.boundary_conditions = [replace(bc, node_ids=(3, 5, 6))
                if bc.name == "guided" else bc for bc in model.boundary_conditions]
            model.add_boundary_condition(BoundaryCondition("controlled_node_rotations", (2,),
                {d: 0. for d in ("rx", "ry", "rz")}))
        model.apply_boundary_conditions()
        oracle = None
        force = np.array([0., -.25, 0., -.25])
        if args.deformable_target:
            from docs.d1_review_support import d2_s3_deformable_mms_reference_dev as two_body_reference
            target_xy = np.array(((0., 0.), (1.4, 0.), (1.4, 1.4), (0., 1.4)))
            support, mass, cross_mass, cells = two_body_reference.independent_p1_integrals(
                XY, CELLS, target_xy, ((7, 8, 10), (8, 9, 10)))
            k, _ = assemble_stiffness_matrix(model)
            joint_normal_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in range(1, 11)]
            free_indices = np.array((1, 2, 4, 5, 7, 8))
            free_dofs = np.asarray(joint_normal_dofs)[free_indices]
            known_q = np.array((0., -1e-6, -1e-6, 0., -1e-6, -1e-6, 0., .3e-6, .3e-6, 0.))
            oracle = two_body_reference.normal_reference(
                k.toarray()[np.ix_(free_dofs, free_dofs)], free_indices,
                support, mass, cross_mass, known_q, gap0=1e-8, kappa=1e7)
            force = np.zeros(10)
            force[free_indices] = oracle["free_normal_forces_n"]
            load = LoadCase("independent_two_body_manufactured_normal_field")
            for n, value in enumerate(force, 1):
                if value != 0.: load.add_nodal_load(n, forces=np.array((0., 0., value)))
            record["reference_source"] = file_identity(two_body_reference.__file__)
            record["manufactured"] = {"known_normal_displacements_m": known_q.tolist(),
                "scope": "two-body code verification; no point-load or continuum accuracy claim"}
        else:
            support, mass, cells = integrals(args.target_extent)
        if args.manufactured and not args.deformable_target:
            k, _ = assemble_stiffness_matrix(model)
            free_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in (2, 3, 5, 6)]
            known_q = np.array([0., -1e-6, -1e-6, 0., -1e-6, -1e-6])
            known_pressure = 1e7*np.maximum(-(1e-8+mass@known_q/support), 0.)
            force = k.toarray()[np.ix_(free_dofs, free_dofs)]@known_q[[1, 2, 4, 5]]-mass[:, [1, 2, 4, 5]].T@known_pressure
            load = LoadCase("independent_manufactured_normal_field")
            for n, value in zip((2, 3, 5, 6), force, strict=True):
                load.add_nodal_load(n, forces=np.array([0., 0., value]))
            record["manufactured"] = {"known_normal_displacements_m": known_q.tolist(),
                "independently_computed_pressure_pa": known_pressure.tolist(),
                "scope": "code verification; no point-load or continuum accuracy claim"}
        force_scale = float(np.sum(np.abs(force)))
        record["inputs"].update(force_n=force_scale, free_normal_nodal_forces_n=force.tolist(),
            force_and_moment_scales=[force_scale, force_scale])
        if args.force_path:
            program = ContactPathProgram(
                controls=(ContactPathControl.node(2, "ux"), ContactPathControl.node(2, "uy")),
                waypoints=((0., 0.), (0., 0.)), steps_per_segment=2,
                nodal_forces=tuple(ContactPathNodalForce(n, "uz", (0., value))
                    for n, value in zip(tuple(range(1, 11)) if args.deformable_target
                        else (2, 3, 5, 6), force, strict=True) if value != 0.))
            record["program"] = program.contract()
        if oracle is None: oracle = reference(model, support, mass, force)
        record["oracle"] = oracle
        record["independent_integrals"] = {"support_m2": support.tolist(), "mass_m2": mass.tolist(), "cells": cells}
        if args.deformable_target:
            record["independent_integrals"]["cross_mass_m2"] = cross_mass.tolist()
        reference_gaps = []
        for cell in cells:
            if args.deformable_target:
                source_q = np.asarray(oracle["normal_displacements_m"])[:6]
                target_q = np.asarray(oracle["normal_displacements_m"])[6:]
                reference_gaps.extend((1e-8+np.asarray(cell["source_values"])@source_q[cell["source_indices"]]
                    -np.asarray(cell["target_values"])@target_q[cell["target_indices"]]).tolist())
            else:
                ix = np.array(cell["ids"])-1
                values = np.c_[np.asarray(cell["clipped_vertices_xy_m"]),
                    np.ones(len(cell["clipped_vertices_xy_m"]))]@np.asarray(cell["basis_coefficients"])
                reference_gaps.extend((1e-8+values@np.asarray(oracle["source_normal_displacements_m"])[ix]).tolist())
        record["independent_reference_gap_preflight_m"] = min(reference_gaps)
        if min(reference_gaps) < -5e-5:
            raise RuntimeError("independent reference predicts physical gap outside declared budget; coupled solve withheld")
        print("ordinary S3/S3 finite-penalty force solve", flush=True)
        result = solve_static_nonlinear(model, load_case=None if program else load,
            contact_path_program=program, contact=definition, contact_settings=settings,
            **({} if program else {"num_steps": 2}), max_iterations=18, tolerance=1e-8,
            emit_restart_checkpoint=True, record_increment_snapshots=True)
        record.update(status=result.status, failure=result.failure_reason, info=result.info,
            displacements=result.displacements.tolist(), steps=[s.to_dict() for s in result.steps], checkpoint=result.restart_checkpoint)
        if result.status != "completed": raise RuntimeError("S3/S3 ordinary force solve did not complete")
        record["assessment"] = assess(model, definition, settings, result, support, oracle, cells,
            force, force_scale, args.deformable_target)
        record["development_checks_met"] = all(record["assessment"]["checks"].values())
        if not record["development_checks_met"]: raise RuntimeError("S3/S3 code-verification predicate failed")
    except Exception as exc:
        record["development_checks_met"] = False
        record["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        record["elapsed_seconds"] = time.perf_counter()-started
        args.output.write_text(json.dumps(record, indent=2, default=json_default)+"\n", encoding="utf-8")
        print(json.dumps({"development_checks_met": record["development_checks_met"], "elapsed_seconds": record["elapsed_seconds"],
            "error": record.get("error", {}).get("message")}), flush=True)
    raise SystemExit(0 if record["development_checks_met"] else 1)


if __name__ == "__main__": main()
