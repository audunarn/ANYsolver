"""One spatial discriminator at fixed mechanics; development, not acceptance.

The independent fixed-geometry reference shares structural K as declared input,
but never calls the production contact law. This runner checks the actual moving
shell work, reactions and represented physical skin gap on the same neutral mesh.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
from types import SimpleNamespace
import numpy as np
import anysolver.nonlinear_static as driver
from anysolver import (BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSurface, create_shell_element, solve_static_nonlinear)
from anysolver.boundary import LoadCase
from anysolver.fe_core import FEModel
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from docs.d1_review_support.d2_projected_penalty_shell_dev import fixture
from docs.d1_review_support.d1_guided_reaction_wrench import guided_wrench_diagnostics


def identity(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build(nx=4, ny=2):
    model = FEModel("d2_projected_penalty_spatial_discriminator")
    model.add_material("elastic", 1e5, .3, density=1.)
    if (nx, ny) != (4, 2): raise ValueError("only the selected single 4x2 discriminator is authorized")
    xs, ys = (.1, .35, .6, .85, 1.1), (.1, .6, 1.1)
    source = tuple(range(1, (nx+1)*(ny+1)+1))
    nid = lambda ix, iy: 1+iy*(nx+1)+ix
    for iy, y in enumerate(ys):
        for ix, x in enumerate(xs): model.add_node(nid(ix, iy), float(x), float(y), .0401)
    targets = tuple(range(len(source)+1, len(source)+5))
    for node, (x, y) in zip(targets, ((0., 0.), (1., 0.), (1., 1.), (0., 1.)), strict=True):
        model.add_node(node, x, y, 0.)
    source_eids = []
    for iy in range(ny):
        for ix in range(nx):
            eid = 1+iy*nx+ix
            nodes = (nid(ix, iy), nid(ix+1, iy), nid(ix+1, iy+1), nid(ix, iy+1))
            model.add_element(eid, create_shell_element(eid, nodes, "elastic", thickness=.05,
                reference_normal=(0., 0., 1.)))
            source_eids.append(eid)
    target_eids = (nx*ny+1, nx*ny+2)
    for eid, nodes in zip(target_eids, ((targets[0], targets[1], targets[3]),
                                       (targets[1], targets[2], targets[3])), strict=True):
        model.add_element(eid, create_shell_element(eid, nodes, "elastic", thickness=.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0., 0., 1.), reference_surface_offset=.01))
    left = tuple(nid(0, iy) for iy in range(ny+1))
    free_nodes = tuple(node for node in source if node not in left)
    components = ("ux", "uy", "uz", "rx", "ry", "rz")
    for name, nodes in (("left", left), ("target", targets)):
        model.add_boundary_condition(BoundaryCondition(name, nodes, {d: 0. for d in components}))
    model.add_boundary_condition(BoundaryCondition("guided", free_nodes,
        {d: 0. for d in ("ux", "uy", "rx", "ry", "rz")}))
    definition = ContactDefinition(surfaces=(ContactSurface("q4_source", tuple(source_eids), "bottom"),
        ContactSurface("s3_target", target_eids, "top")), rigid_bodies=(), interactions=(
        ContactInteraction("pair", "q4_source", "s3_target", 1e7, 5e-5, normal_law="projected_penalty"),))
    settings = fixture(1e7)[2]  # Explicit unchanged, already tested derivative/gap settings.
    load = LoadCase("same_half_newton_endpoint_press")
    load_nodes = (nid(nx, 0), nid(nx, ny))
    for node in load_nodes: load.add_nodal_load(node, forces=np.array([0., 0., -.25]))
    return model, definition, settings, load, source, targets, source_eids, free_nodes, load_nodes


def physical_gap(model, u, eids):
    rows = []
    for node_id, node in model.mesh.nodes.items():
        dofs = model.mesh.dof_manager.get_node_dofs(node_id)
        if np.any(u[dofs[3:]] != 0.) or np.any(u[dofs[:2]] != 0.):
            raise ValueError("exact fixed-XY skin gap requires prescribed in-plane/rotational coordinates")
    for eid in eids:
        ids = model.mesh.elements[eid].node_ids
        nodes = [model.mesh.nodes[n] for n in ids]
        x0, x1, y0, y1 = nodes[0].x, nodes[1].x, nodes[0].y, nodes[3].y
        right, top = min(x1, 1.), min(y1, 1.)
        if right <= x0 or top <= y0: continue
        q = np.array([u[model.mesh.dof_manager.get_node_dofs(n)[2]] for n in ids])
        gaps = []
        for x, y in ((x0, y0), (right, y0), (right, top), (x0, top)):
            a, b = (x-x0)/(x1-x0), (y-y0)/(y1-y0)
            gaps.append(float(1e-4+np.array([(1-a)*(1-b), a*(1-b), a*b, (1-a)*b])@q))
        rows.append({"element_id": eid, "corners_gap_m": gaps, "minimum_gap_m": min(gaps)})
    return {"method": "independent exact bilinear skin extrema on clipped XY rectangles",
        "rows": rows, "minimum_gap_m": min(row["minimum_gap_m"] for row in rows),
        "roundoff_allowance_m": 128*np.finfo(float).eps, "uncovered_tips_excluded": True}


def diagnostics(model, definition, settings, result, source_ids, target_ids, eids, free_nodes, load_nodes):
    u = result.displacements
    manager = GeneralS3PatchManager(model, definition, settings)
    contact, _, certificate = manager.evaluate(u, tangent=False)
    source, target = manager._positions(u)
    work = manager.law.work(source, target, manager.normal_multipliers, tangent=False)
    forces = -np.asarray(work.residual).reshape(-1, 3)
    bodies, offset = {}, 0
    origin = np.array([.6, .6, 0.])
    for name, ids, positions in (("source", manager.law.source_node_ids, source),
                                  ("target", manager.law.target_node_ids, target)):
        local = forces[offset:offset+len(ids)]
        bodies[name] = {"node_ids": list(ids), "physical_contact_force": local.sum(axis=0),
            "physical_contact_moment": np.cross(positions-origin, local).sum(axis=0)}
        offset += len(ids)
    structural, _, trial_states = driver._assemble_nonlinear_system(model, u, result.element_states, 5,
        tangent=False, kinematics="von_karman", require_full_coordinates=True)
    driver._discard_nonlinear_state_candidate(trial_states)
    driver._discard_nonlinear_state_candidate(result.element_states)
    external = np.zeros(len(u))
    for node in load_nodes: external[model.mesh.dof_manager.get_node_dofs(node)[2]] = -.25
    free = np.eye(len(u))[:, [model.mesh.dof_manager.get_node_dofs(n)[2] for n in free_nodes]]
    total_force = sum((b["physical_contact_force"] for b in bodies.values()), np.zeros(3))
    total_moment = sum((b["physical_contact_moment"] for b in bodies.values()), np.zeros(3))
    wrench = guided_wrench_diagnostics(model, u, structural, contact, external, free,
        physical_contact_force=total_force, physical_contact_moment=total_moment,
        origin=origin, force_scale_n=.5, moment_scale_nm=.5, bodies=bodies)
    direction = np.linspace(-.4, .4, len(u))
    local_direction = []
    for ids, skin_offset in ((manager.law.source_node_ids, -.025), (manager.law.target_node_ids, .015)):
        for node in ids:
            dofs = model.mesh.dof_manager.get_node_dofs(node)
            local_direction.append(direction[dofs[:3]]+skin_offset*np.cross(direction[dofs[3:]], [0., 0., 1.]))
    virtual_error = abs(float(forces.ravel()@np.asarray(local_direction).ravel()+contact@direction))/.5
    q = [float(u[model.mesh.dof_manager.get_node_dofs(n)[2]]) for n in source_ids]
    return {"certificate": certificate.to_dict(), "source_normal_displacements_m": q,
        "source_node_ids": list(source_ids), "physical_gap": physical_gap(model, u, eids),
        "wrench": wrench, "bodies": bodies, "virtual_work_relative": virtual_error,
        "zero_multipliers": bool(np.all(manager.normal_multipliers == 0))}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-only", action="store_true",
        help="evaluate the reference pose without any coupled solve or physical commit")
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    record = {"accepted": False, "released": False, "kind": "fixed_stiffness_spatial_coupled_development",
        "adapter": identity(__file__), "reference": identity(args.reference), "matrix_classes": [],
        "scope": "guided elastic small motion; fixed-target discrete normal comparison; not continuum qualification",
        "inputs": {"normal_regularization_pa_per_m": 1e7, "physical_gap_budget_m": 5e-5,
            "load_n": .5, "normal_relative_comparison_target": 1e-6,
            "force_balance_target": 1e-6, "virtual_work_target": 1e-10,
            "normal_force_scale_n": .5, "moment_scale_nm": .5, "max_iterations": 18,
            "time_cap_s": 180, "process_memory_cap_bytes": 1000000000},
        "source": {name: identity(Path("src/anysolver")/name) for name in (
            "nonlinear_static.py", "general_contact/core.py", "general_contact/s3_patch_static.py")}}
    started, original = time.perf_counter(), driver.factorize
    def traced(matrix, matrix_class, *pos, **kw):
        record["matrix_classes"].append(str(matrix_class))
        return original(matrix, matrix_class, *pos, **kw)
    try:
        model, definition, settings, load, source, target, eids, free_nodes, load_nodes = build()
        record["world_node_map"] = {str(n): [model.mesh.nodes[n].x, model.mesh.nodes[n].y] for n in source}
        driver.factorize = traced
        if args.candidate_only:
            model.apply_boundary_conditions()
            q = np.asarray(reference["reference"]["source_normal_displacements_m"])
            u = np.zeros(model.mesh.dof_manager.total_dofs)
            for node, value in zip(source, q, strict=True):
                u[model.mesh.dof_manager.get_node_dofs(node)[2]] = value
            result = SimpleNamespace(displacements=u, element_states={})
            record.update(status="reference_candidate_evaluation_no_solve_no_commit",
                kind="production_operator_at_independent_spatial_reference", displacements=u.tolist(),
                prescribed_reference_normal_displacements=True, new_coupled_solves=0)
            print("candidate-only production evaluation; no physical commit", flush=True)
        else:
            if reference["reference"]["physical_gap_and_slopes"]["minimum_represented_gap_m"] < -5e-5:
                raise ValueError("reference predicts gap rejection; coupled run withheld")
            print("coupled 4x2 fixed-stiffness press", flush=True)
            result = solve_static_nonlinear(model, load_case=load, contact=definition, contact_settings=settings,
                num_steps=2, max_iterations=18, tolerance=1e-8, emit_restart_checkpoint=True,
                record_increment_snapshots=True)
            record.update(status=result.status, failure=result.failure_reason, info=result.info,
                steps=[s.to_dict() for s in result.steps], displacements=result.displacements.tolist(),
                checkpoint=result.restart_checkpoint, snapshots=[s.to_dict(include_displacements=True) for s in result.snapshots])
            if result.status != "completed": raise RuntimeError("coupled spatial press did not complete")
        record["diagnostics"] = diagnostics(model, definition, settings, result, source, target, eids, free_nodes, load_nodes)
        d, ref = record["diagnostics"], reference["reference"]
        q, qref = np.asarray(d["source_normal_displacements_m"]), np.asarray(ref["source_normal_displacements_m"])
        cert = d["certificate"]
        p = dict(zip(cert["source_pressure_node_ids"], cert["numerical_pressure_pa"], strict=True))
        pressure = np.array([p[n] for n in source])
        pref = np.asarray(ref["pressure_all_fifteen_pa"])
        target_force = -float(d["bodies"]["target"]["physical_contact_force"][2])
        target_ref = float(ref["target_normal_support_reaction_n"])
        compare = {"normal_displacement_relative": float(np.linalg.norm(q-qref)/np.linalg.norm(qref)),
            "normal_pressure_relative": float(np.linalg.norm(pressure-pref)/np.linalg.norm(pref)),
            "target_normal_force_relative": abs(target_force-target_ref)/abs(target_ref),
            "physical_gap_absolute_difference_m": abs(d["physical_gap"]["minimum_gap_m"]-
                float(ref["physical_gap_and_slopes"]["minimum_represented_gap_m"]))}
        wrench = d["wrench"]
        keys = ("balance_relative_force", "balance_relative_moment", "contact_conversion_max_scaled", "structural_internal_max_scaled")
        max_wrench = max([wrench[k] for k in keys]+[wrench["constraint_reconstruction_relative_force"]]+
            [b[k] for b in wrench["bodies"].values() for k in keys])
        record["comparison"] = compare
        compared = ("normal_pressure_relative", "target_normal_force_relative") if args.candidate_only else (
            "normal_displacement_relative", "normal_pressure_relative", "target_normal_force_relative")
        record["checks"] = {"discrete_normal_reference": max(compare[k] for k in compared) <= 1e-6,
            "independent_gap_budget": d["physical_gap"]["minimum_gap_m"]-d["physical_gap"]["roundoff_allowance_m"] >= -5e-5,
            "wrench_balance": max_wrench <= 1e-6, "full_virtual_work": d["virtual_work_relative"] <= 1e-10,
            "all_positive_supports_retained": len(cert["reference_support_m2"]) == 15 and
                bool(np.all(np.asarray(cert["reference_support_m2"]) > 0)),
            "nonnegative_pressure": bool(np.all(pressure >= 0)), "zero_multipliers": d["zero_multipliers"],
            "general_matrix": bool(record["matrix_classes"]) and all("GENERAL" in x for x in record["matrix_classes"])}
        if args.candidate_only:
            del record["checks"]["general_matrix"]
            record["gap_admission"] = {"independent_gap_budget_met": record["checks"].pop("independent_gap_budget"),
                "production_gap_budget_met": bool(cert["gap_tolerance_met"]),
                "production_lower_gap_m": cert["minimum_gap"]}
            record["checks"]["expected_gap_rejection"] = (not record["gap_admission"]["independent_gap_budget_met"]
                and not record["gap_admission"]["production_gap_budget_met"])
            record["scope_limit"] = "reference q imposed; displacement agreement is identity, not solution verification"
        record["development_checks_met"] = all(record["checks"].values())
        if not record["development_checks_met"]: raise RuntimeError("coupled spatial discriminator check failed")
    except Exception as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        driver.factorize = original
        record["elapsed_seconds"] = time.perf_counter()-started
        def scalar(value):
            if isinstance(value, np.ndarray): return value.tolist()
            if isinstance(value, np.generic): return value.item()
            raise TypeError(type(value).__name__)
        args.output.write_text(json.dumps(record, indent=2, default=scalar)+"\n", encoding="utf-8")
        print(json.dumps({"status": record.get("status"), "error": record.get("error", {}).get("message"),
            "elapsed_seconds": record["elapsed_seconds"]}), flush=True)
    raise SystemExit(1 if "error" in record else 0)


if __name__ == "__main__": main()
