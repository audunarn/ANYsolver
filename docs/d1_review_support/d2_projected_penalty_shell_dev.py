"""One bounded projected-penalty Q4/S3 press/open/recontact development slice.

The target boundary cuts both source faces. The source left edge is prescribed;
its supported pressure rows remain present. Target offset skins and all physical
and generalized reaction rows are retained. This is not method acceptance.
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
import anysolver
from anysolver import (BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathNodalForce, ContactPathProgram, ContactSolverSettings,
    ContactSurface, create_shell_element, solve_static_nonlinear, validate_general_contact)
from anysolver.fe_core import FEModel
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.nonlinear_static import _assemble_nonlinear_system, _discard_nonlinear_state_candidate
from docs.d1_review_support.d1_guided_reaction_wrench import guided_wrench_diagnostics


INPUTS = dict(stiffness_pa_per_m=[1e6, 1e7], source_z_m=.0401,
    source_thickness_m=.05, target_thickness_m=.05, target_offset_m=.01,
    young_pa=1e5, poisson=.3, peak_force_n=.5,
    source_left_prescribed_nodes=[1, 4], source_load_nodes=[3, 6],
    force_per_node_history_n=[0., -.25, 0., -.25],
    steps_per_segment=1, max_iterations=18, tolerance=1e-8,
    physical_gap_budget_m=5e-5, force_balance_relative=1e-6,
    full_virtual_work_relative=1e-10, target_static=True,
    source_rotations_prescribed_zero=True, emit_restart_checkpoint=True)


def file_identity(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def fixture(stiffness):
    model = FEModel("d2_projected_penalty_partial_overlap")
    model.add_material("elastic", 1e5, .3, density=1.)
    source = ((.1, .1), (.6, .1), (1.1, .1),
              (.1, 1.1), (.6, 1.1), (1.1, 1.1))
    target = ((0., 0.), (1., 0.), (1., 1.), (0., 1.))
    for node, (x, y) in enumerate(source, 1):
        model.add_node(node, x, y, .0401)
    for node, (x, y) in enumerate(target, 7):
        model.add_node(node, x, y, 0.)
    for eid, nodes in ((1, (1, 2, 5, 4)), (2, (2, 3, 6, 5))):
        model.add_element(eid, create_shell_element(eid, nodes, "elastic", thickness=.05,
            reference_normal=(0., 0., 1.)))
    for eid, nodes in ((3, (7, 8, 10)), (4, (8, 9, 10))):
        model.add_element(eid, create_shell_element(eid, nodes, "elastic", thickness=.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0., 0., 1.),
            reference_surface_offset=.01))
    model.add_boundary_condition(BoundaryCondition("left", (1, 4),
        {name: 0. for name in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    model.add_boundary_condition(BoundaryCondition("target", (7, 8, 9, 10),
        {name: 0. for name in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    model.add_boundary_condition(BoundaryCondition("guided", (2, 3, 5, 6),
        {name: 0. for name in ("rx", "ry", "rz")}))
    model.add_boundary_condition(BoundaryCondition("in_plane", (3, 5, 6),
        {name: 0. for name in ("ux", "uy")}))
    definition = ContactDefinition(surfaces=(
        ContactSurface("q4_source", (1, 2), "bottom"),
        ContactSurface("s3_target", (3, 4), "top")), rigid_bodies=(),
        interactions=(ContactInteraction("pair", "q4_source", "s3_target", stiffness,
            5e-5, normal_law="projected_penalty"),))
    settings = ContactSolverSettings(pair_motion="general", normal_discretization="primal_mortar",
        general_s3_difference_step=2e-5, maximum_general_s3_energy_evaluations=5000,
        q4_source_area_tolerance=1e-9, q4_source_weighted_gap_tolerance=1e-10,
        maximum_q4_source_integration_triangles=128,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1e-5, q4_source_support_hessian_tolerance=1e-5,
        q4_source_weighted_gap_gradient_tolerance=1e-5,
        q4_source_weighted_gap_hessian_tolerance=1e-5,
        q4_source_gap_certificate="overlap_local_dev", augmentation_acceleration="none",
        augmentation_support_resolution="exact", d1_interior_profile=False)
    program = ContactPathProgram(controls=(ContactPathControl.node(2, "ux"),
        ContactPathControl.node(2, "uy")), waypoints=((0., 0.),)*4, steps_per_segment=1,
        nodal_forces=tuple(ContactPathNodalForce(node, "uz", (0., -.25, 0., -.25))
                           for node in (3, 6)))
    return model, definition, settings, program


def represented_gap(model, u, *, target_shift_x_m=0.):
    """Exact bilinear skin/flat-target bound on the actual XY overlap only.

    Source in-plane motion and all rotations are fixed in this fixture; the
    optional target x shift is a separately verified prescribed translation. Source
    skins use the original vertical director, thickness/2; target top is .015 m.
    Bilinear extrema on each clipped rectangular source face occur at corners.
    This neither samples nor gates the uncovered source tips at x/y=1.1.
    """
    rows = []
    for eid in (1, 2):
        element = model.mesh.elements[eid]
        nodes = [model.mesh.nodes[n] for n in element.node_ids]
        q = np.array([u[model.mesh.dof_manager.get_node_dofs(n)[2]]
                      for n in element.node_ids])
        x0, x1, y0, y1 = nodes[0].x, nodes[1].x, nodes[0].y, nodes[3].y
        left, right, top = max(x0, target_shift_x_m), min(x1, target_shift_x_m+1.), min(y1, 1.)
        if right <= left or top <= y0:
            continue
        gaps = []
        for x, y in ((left, y0), (right, y0), (right, top), (left, top)):
            a, b = (x-x0)/(x1-x0), (y-y0)/(y1-y0)
            weights = np.array([(1-a)*(1-b), a*(1-b), a*b, (1-a)*b])
            gaps.append(float(.0401-.025-.015+weights@q))
        rows.append(dict(element_id=eid, represented_area_m2=(right-left)*(top-y0),
            physical_target_normal_corner_gap_m=gaps, minimum_gap_m=min(gaps)))
    return dict(method="independent exact bilinear physical skin over clipped XY rectangles",
        target_skin_z_m=.015, source_reference_bottom_z_m=.0151,
        source_face_bounds=rows, minimum_gap_m=min(r["minimum_gap_m"] for r in rows),
        maximum_in_plane_control_departure_m=max(abs(u[model.mesh.dof_manager.get_node_dofs(n)[axis]])
                                                  for n in model.mesh.nodes for axis in (0, 1)),
        physical_gap_roundoff_allowance_m=128*np.finfo(float).eps,
        uncovered_source_tip_excluded=True)


def pose_diagnostics(model, definition, manager, snapshot, program, history, *, rigid_target_slide=False):
    u = np.asarray(snapshot.displacements)
    shift = float(u[model.mesh.dof_manager.get_node_dofs(7)[0]]) if rigid_target_slide else 0.
    for node in model.mesh.nodes:
        dofs = np.asarray(model.mesh.dof_manager.get_node_dofs(node))
        point = model.mesh.nodes[node]
        xy = np.array([point.x, point.y])
        moving_target = rigid_target_slide and node in (7, 8, 9, 10)
        expected_translation = np.array([shift, 0.]) if moving_target else np.zeros(2)
        translation_invalid = (np.max(abs(u[dofs[:2]]-expected_translation)) > 128*np.finfo(float).eps
                               if moving_target else not np.array_equal(xy+u[dofs[:2]], xy))
        if (np.any(u[dofs[3:]] != 0.)
                or translation_invalid):
            raise ValueError("independent guided skin oracle requires zero rotations and unchanged represented XY coordinates")
    contact, _, certificate = manager.evaluate(u, tangent=False)
    source, target = manager._positions(u)
    work = manager.law.work(source, target, manager.normal_multipliers, tangent=False)
    local = -np.asarray(work.residual).reshape(-1, 3)
    origin = np.array([.6, .6, 0.])
    bodies = {}
    start = 0
    for name, ids, positions in (("source", manager.law.source_node_ids, source),
                                  ("target", manager.law.target_node_ids, target)):
        nodal = local[start:start+len(ids)]
        bodies[name] = dict(node_ids=list(ids),
            physical_contact_force=np.sum(nodal, axis=0),
            physical_contact_moment=np.sum(np.cross(positions-origin, nodal), axis=0))
        start += len(ids)
    structural, _, _ = _assemble_nonlinear_system(model, u, snapshot.element_states, 5,
        tangent=False, kinematics="von_karman", require_full_coordinates=True)
    _discard_nonlinear_state_candidate(snapshot.element_states)
    external = np.zeros(len(u))
    for load, value in zip(program.nodal_forces, program.force_values_at(snapshot.step_index), strict=True):
        external[model.mesh.dof_manager.get_node_dofs(load.node_id)[2]] += value
    free_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in (2, 3, 5, 6)]
    free = np.eye(len(u))[:, free_dofs]
    physical_force = sum((body["physical_contact_force"] for body in bodies.values()), np.zeros(3))
    physical_moment = sum((body["physical_contact_moment"] for body in bodies.values()), np.zeros(3))
    wrench = guided_wrench_diagnostics(model, u, structural, contact, external, free,
        physical_contact_force=physical_force, physical_contact_moment=physical_moment,
        origin=origin, force_scale_n=.5, moment_scale_nm=.5, bodies=bodies)
    # Independent affine skin variations include prescribed and target reaction rows.
    direction = np.linspace(-.4, .4, len(u))
    local_direction = []
    for ids, offset in ((manager.law.source_node_ids, -.025),
                         (manager.law.target_node_ids, .015)):
        for node in ids:
            dofs = model.mesh.dof_manager.get_node_dofs(node)
            local_direction.append(direction[dofs[:3]]+offset*np.cross(
                direction[dofs[3:]], np.array([0., 0., 1.])))
    physical_work = float(local.ravel() @ np.asarray(local_direction).ravel())
    mapped_work = float(-contact @ direction)
    virtual_error = abs(physical_work-mapped_work)/max(abs(physical_work), .5)
    gap = represented_gap(model, u, target_shift_x_m=shift)
    if rigid_target_slide:
        gap["target_prescribed_rigid_translation_x_m"] = shift
    pressure = np.asarray(certificate.numerical_pressure_pa)
    support = np.asarray(certificate.reference_support_m2)
    all_ids = certificate.source_pressure_node_ids
    prescribed = [dict(node_id=node, pressure_pa=float(pressure[all_ids.index(node)]),
        support_m2=float(support[all_ids.index(node)])) for node in (1, 4)]
    body_errors = [body[key] for body in wrench["bodies"].values() for key in
                   ("balance_relative_force", "balance_relative_moment",
                    "contact_conversion_max_scaled", "structural_internal_max_scaled")]
    maximum_wrench = max(body_errors+[wrench[key] for key in
        ("constraint_reconstruction_relative_force", "balance_relative_force",
         "balance_relative_moment", "contact_conversion_max_scaled", "structural_internal_max_scaled")])
    checks = dict(represented_gap=gap["minimum_gap_m"]-gap["physical_gap_roundoff_allowance_m"] >= -5e-5,
        both_body_wrench=maximum_wrench <= 1e-6, full_virtual_work=virtual_error <= 1e-10,
        pressure_nonnegative=bool(np.all(pressure >= 0.)),
        six_positive_support_rows_retained=bool(len(pressure) == 6 and np.all(support > 0.)),
        permanent_zero_algorithmic_multipliers=bool(np.all(manager.normal_multipliers == 0.)))
    return dict(step_index=snapshot.step_index, history=history,
        displacements=u.tolist(), state_count=len(snapshot.element_states),
        certificate=certificate.to_dict(), independent_gap=gap, wrench=wrench,
        prescribed_source_pressure_rows=prescribed,
        full_virtual_work=dict(physical_n_m=physical_work, mapped_n_m=mapped_work,
                               normalized_difference=virtual_error),
        maximum_wrench_relative=maximum_wrench, development_checks=checks)


def json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--saved", type=Path,
                      help="assess only the retained final checkpoint pose; no solve")
    mode.add_argument("--stiffness", type=float, nargs="+", choices=(1e6, 1e7),
                      help="explicit subset for a separately authorized continuation")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    import anysolver.general_contact.core as core
    import anysolver.general_contact.s3_patch_static as owner
    import anysolver.general_contact.static_path as path_owner
    import anysolver.general_contact.s3_patch_augmented as work_owner
    started = time.perf_counter()
    record = dict(status="development_projected_penalty_coupled_shell_slice", accepted=False,
        released=False, inputs=INPUTS, cap=dict(time_limit_seconds=180,
        memory_limit_bytes=1073741824, maximum_executions=1),
        adapter=file_identity(__file__), python_executable=sys.executable,
        actual_modules={m.__name__: file_identity(m.__file__) for m in
            (anysolver, core, owner, path_owner, work_owner)}, rows=[], failures=[])
    if args.saved is not None:
        from anysolver.nonlinear_restart import load_nonlinear_checkpoint, validate_nonlinear_checkpoint
        from anysolver.general_contact.static_path import GENERAL_Q4_S3_PATCH_REFINED_PROJECTED_PENALTY_PROFILE
        record["status"] = "development_saved_projected_penalty_final_pose_assessment_no_solve"
        record["saved_input"] = file_identity(args.saved)
        saved = json.loads(args.saved.read_text(encoding="utf-8"))
        old = saved["rows"][0]
        model, definition, settings, program = fixture(old["stiffness_pa_per_m"])
        model.apply_boundary_conditions()
        manager = GeneralS3PatchManager(model, definition, settings)
        contract = dict(schema="ANYSOLVER_STATIC_RESTART_CONTRACT_V2", control="contact_path",
            profile=GENERAL_Q4_S3_PATCH_REFINED_PROJECTED_PENALTY_PROFILE,
            general_contact=manager.restart_contract(), program=program.contract(),
            num_layers=5, max_iterations=18, tolerance=1e-8)
        row = dict(stiffness_pa_per_m=old["stiffness_pa_per_m"], saved_pose_count=1,
                   failed_original_guard=old.get("failure"), poses=[])
        record["rows"].append(row)
        try:
            root = load_nonlinear_checkpoint(old["restart_checkpoint"])
            consumed = validate_nonlinear_checkpoint(root, analysis_kind="static", model=model,
                analysis_contract=contract, num_layers=5)
            snapshot = SimpleNamespace(displacements=consumed.displacements,
                element_states=consumed.element_states, step_index=root["path_state"]["accepted_step"])
            row["poses"].append(pose_diagnostics(model, definition, manager, snapshot, program,
                                                 root["path_state"]["history"][-1]))
            row["development_checks_met"] = all(row["poses"][0]["development_checks"].values())
            if not row["development_checks_met"]:
                raise ValueError("retained final-pose mechanics check failed")
        except Exception as exc:
            row["failure"] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
            record["failures"].append(row["failure"])
        record["development_checks_met"] = not record["failures"]
        record["elapsed_seconds"] = time.perf_counter()-started
        record["limits"] = ["Only final pose retained before the original diagnostic failure; earlier snapshots unavailable.",
            "Original failed guard and raw solver history remain unchanged; no equilibrium solve performed."]
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, default=json_default, allow_nan=False)
            stream.write("\n")
        print(json.dumps(dict(development_checks_met=record["development_checks_met"],
            failures=[r["message"] for r in record["failures"]], output=str(args.output))), flush=True)
        if not record["development_checks_met"]:
            raise SystemExit(1)
        return
    selected_stiffness = args.stiffness or INPUTS["stiffness_pa_per_m"]
    record["selected_stiffness_pa_per_m"] = selected_stiffness
    for stiffness in selected_stiffness:
        row = dict(stiffness_pa_per_m=stiffness)
        record["rows"].append(row)
        try:
            print(json.dumps(dict(stage="fixture", stiffness_pa_per_m=stiffness)), flush=True)
            model, definition, settings, program = fixture(stiffness)
            validation = validate_general_contact(model, definition, settings)
            row["validation"] = dict(valid=validation.valid, profile=validation.profile,
                                      issues=list(validation.issues))
            if not validation.valid:
                raise ValueError("fixture contact admission rejected: "+"; ".join(validation.issues))
            row["program"] = program.contract()
            print(json.dumps(dict(stage="solve", stiffness_pa_per_m=stiffness)), flush=True)
            solve_started = time.perf_counter()
            result = solve_static_nonlinear(model, contact=definition, contact_settings=settings,
                contact_path_program=program, max_iterations=18, tolerance=1e-8,
                emit_restart_checkpoint=True, record_increment_snapshots=True)
            row.update(solver_status=result.status, failure_reason=result.failure_reason,
                solve_seconds=time.perf_counter()-solve_started, steps=[s.to_dict() for s in result.steps],
                solver_info=result.info, final_displacements=result.displacements.tolist(),
                restart_checkpoint=result.restart_checkpoint, poses=[])
            row["accepted_pose_displacements"] = [snapshot.displacements.tolist()
                                                   for snapshot in result.snapshots]
            if result.status != "completed" or len(result.snapshots) != 3:
                raise ValueError("press/open/recontact solver path did not complete")
            manager = GeneralS3PatchManager(model, definition, settings)
            row["manager_restart_contract"] = manager.restart_contract()
            for snapshot, history in zip(result.snapshots,
                                        result.info["force_displacement_history"], strict=True):
                print(json.dumps(dict(stage="pose_checks", stiffness_pa_per_m=stiffness,
                                      step=snapshot.step_index)), flush=True)
                pose = pose_diagnostics(model, definition, manager, snapshot, program, history)
                row["poses"].append(pose)
                if not all(pose["development_checks"].values()):
                    raise ValueError("first pose mechanics check failed: "+str(pose["development_checks"]))
            active = [pose["certificate"]["active_pressure_dofs"] for pose in row["poses"]]
            row["press_open_recontact_active_counts"] = active
            if not (active[0] > 0 and active[1] == 0 and active[2] > 0):
                raise ValueError("path does not demonstrate press/open/recontact")
            row["development_checks_met"] = True
        except Exception as exc:
            row["failure"] = dict(type=type(exc).__name__, message=str(exc),
                                   traceback=traceback.format_exc())
            record["failures"].append(dict(stiffness_pa_per_m=stiffness, **row["failure"]))
            break
    record["elapsed_seconds"] = time.perf_counter()-started
    record["development_checks_met"] = not record["failures"] and len(record["rows"]) == len(selected_stiffness)
    record["limits"] = ["Finite penalty development; no exact complementarity or accepted new method.",
        "Target static and rotations guided; no moving active rim or finite rotation admission.",
        "Prescribed source rows remain supported; active prescribed-row pressure is measured, not assumed."]
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, default=json_default, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(development_checks_met=record["development_checks_met"],
        failures=[r["message"] for r in record["failures"]], output=str(args.output))), flush=True)
    if not record["development_checks_met"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
