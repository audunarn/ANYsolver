"""Bounded ordinary contact press with source bending rotations free."""

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from anysolver import BoundaryCondition, solve_static_nonlinear
from anysolver.general_contact.core import suspend_contact
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.s3_patch_static import _normal_controls
from anysolver.general_contact.q4_source_overlap import (
    q4_source_projected_swept_gap_lower,
)
from anysolver.general_contact.semismooth import linearize
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_free_target_press_probe import (
    build_free_target_case,
)
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import _json_default


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--left-ry-clamp", action="store_true")
parser.add_argument("--first-load-n", type=float)
parser.add_argument("--next-load-n", type=float)
parser.add_argument("--diagnose-admission", action="store_true")
args = parser.parse_args()
if args.output.exists():
    parser.error("output already exists")
if args.first_load_n is not None and not 0.0 < args.first_load_n <= 0.3:
    parser.error("first-load-n must be in (0, 0.3] N")
if args.next_load_n is not None and (
        args.first_load_n is None
        or not args.first_load_n < args.next_load_n <= 0.3):
    parser.error("next-load-n needs first-load-n < next-load-n <= 0.3 N")
started = time.perf_counter()
model, definition, settings, program = build_free_target_case(
    4, steps_per_segment=2, four_phase=False,
    enforcement_solver="monolithic_active_set",
)
guide = next(bc for bc in model.boundary_conditions
             if bc.name == "source_guide")
if guide.dof_constraints != {"uy": 0.0, "rx": 0.0,
                             "ry": 0.0, "rz": 0.0}:
    raise AssertionError("unexpected source guide definition")
model.boundary_conditions = [
    BoundaryCondition(guide.name, guide.node_ids,
                      {"uy": 0.0, "rx": 0.0, "rz": 0.0})
    if bc is guide else bc for bc in model.boundary_conditions
]
if args.left_ry_clamp:
    support = next(bc for bc in model.boundary_conditions
                   if bc.name == "source_left_support")
    if support.dof_constraints != {"uz": 0.0}:
        raise AssertionError("unexpected source support definition")
    model.boundary_conditions = [
        BoundaryCondition(support.name, support.node_ids,
                          {"uz": 0.0, "ry": 0.0})
        if bc is support else bc for bc in model.boundary_conditions]
if args.first_load_n is not None:
    fraction = args.first_load_n/0.3
    settings = replace(settings,
                       complementarity_force_scale_n=(
                           args.next_load_n or args.first_load_n))
    if args.next_load_n is None:
        program = replace(
            program, steps_per_segment=1,
            nodal_forces=tuple(replace(
                load, values_n=(0.0, float(load.values_n[-1])*fraction))
                for load in program.nodal_forces))
    else:
        next_fraction = args.next_load_n/0.3
        program = replace(
            program, steps_per_segment=1,
            waypoints=(program.waypoints[0], program.waypoints[0],
                       program.waypoints[0]),
            nodal_forces=tuple(replace(
                load, values_n=(0.0,
                               float(load.values_n[-1])*fraction,
                               float(load.values_n[-1])*next_fraction))
                for load in program.nodal_forces))
admission_diagnostics = []
if args.diagnose_admission:
    original_admissible_step_fraction = GeneralS3PatchManager.admissible_step_fraction

    def observed_admissible_step_fraction(self, start, end):
        fraction = original_admissible_step_fraction(self, start, end)
        if fraction == 0.0:
            first_u = np.asarray(start, dtype=float).reshape(-1)
            delta_u = np.asarray(end, dtype=float).reshape(-1)-first_u
            first = self._positions(first_u)
            checks = []
            for scale in (0.0, 2.0**-self.settings.maximum_swept_subdivisions,
                          2.0**-10, 1.0):
                last = self._positions(first_u+scale*delta_u)
                orientation_min = min(
                    float(control@reference)
                    for side, indices, reference in (
                        (0, self.law.source_face_indices, self.reference_normals[0]),
                        (1, self.law.target_face_indices, self.reference_normals[1]),
                    )
                    for face in indices
                    for triple in (((0, 1, 2),) if len(face) == 3 else
                                   ((0, 1, 2), (1, 2, 3), (2, 3, 0), (3, 0, 1)))
                    for control in _normal_controls(
                        first[side][face[list(triple)]],
                        last[side][face[list(triple)]],
                    )
                )
                swept_min = min(
                    float(q4_source_projected_swept_gap_lower(
                        first[0][si], last[0][si],
                        first[1][ti], last[1][ti], self.reference_normals[0],
                    ))
                    for si in self.law.source_face_indices
                    for ti in self.law.target_face_indices
                )
                checks.append({
                    "fraction": scale,
                    "endpoint_gap_lower_m": float(self._gap_lower(last)),
                    "orientation_control_min": orientation_min,
                    "swept_gap_lower_m": swept_min,
                    "admitted": bool(self._swept_admissible(first_u,
                                              first_u+scale*delta_u)),
                })
            admission_diagnostics.append({
                "gap_tolerance_m": self.gap_tolerance,
                "maximum_swept_subdivisions": self.settings.maximum_swept_subdivisions,
                "start_gap_lower_m": float(self._gap_lower(first)),
                "direction_norm": float(np.linalg.norm(delta_u)),
                "checks": checks,
            })
        return fraction

    GeneralS3PatchManager.admissible_step_fraction = observed_admissible_step_fraction

result = solve_static_nonlinear(
    model, contact=definition, contact_settings=settings,
    contact_path_program=program, max_iterations=18,
    record_increment_snapshots=True,
)
record = {
    "status": "development_free_source_director_press",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "solver_status": result.status,
    "failure_reason": result.failure_reason,
    "accepted_steps": len(result.steps),
    "source_rotational_constraint": (
        "left-edge ry fixed; other source ry free; uy/rx/rz retained"
        if args.left_ry_clamp else "all source ry released; uy/rx/rz retained"),
    "first_load_n": args.first_load_n,
    "next_load_n": args.next_load_n,
    "contact_failure": result.info.get("contact_failure"),
    "admission_diagnostics": admission_diagnostics,
    "maximum_ry_rad": None,
    "maximum_source_contact_ry_moment_nm": None,
    "maximum_free_ry_equilibrium_nm": None,
    "final_contact": result.info.get("general_contact"),
}
if result.status == "completed" and result.snapshots:
    manager = GeneralS3PatchManager(model, definition, settings)
    source_ry = np.asarray([
        model.mesh.dof_manager.get_node_dofs(node)[4]
        for node in manager.law.source_node_ids], dtype=int)
    free_source_ry = np.asarray([
        model.mesh.dof_manager.get_node_dofs(node)[4]
        for node in manager.law.source_node_ids
        if not args.left_ry_clamp or node not in (1, 6)], dtype=int)
    history = result.info["force_displacement_history"]
    step_records = []
    for snapshot, row in zip(result.snapshots, history, strict=True):
        certificate = row["contact"]
        pressure_force = (
            np.asarray(certificate["numerical_pressure_pa"])
            * np.asarray(certificate["reference_support_m2"]))
        contact = linearize(manager, snapshot.displacements,
                            pressure_force, tangent=False)
        with suspend_contact():
            internal, _tangent, _states = _assemble_nonlinear_system(
                model, snapshot.displacements, snapshot.element_states, 5,
                tangent=False, kinematics="von_karman",
                require_full_coordinates=True)
        source_contact_moment = np.asarray(contact.force)[source_ry]
        source_internal_moment = np.asarray(internal)[source_ry]
        unprescribed_residual = (np.asarray(internal+contact.force)
                                [free_source_ry])
        step_records.append({
            "step": int(snapshot.step_index),
            "active_pressure_modes": int(certificate["active_pressure_dofs"]),
            "maximum_ry_rad": float(np.max(np.abs(
                snapshot.displacements[source_ry]))),
            "maximum_source_contact_ry_moment_nm": float(np.max(
                np.abs(source_contact_moment))),
            "maximum_free_ry_equilibrium_nm": float(np.max(
                np.abs(unprescribed_residual))),
            "contact_ry_norm_nm": float(np.linalg.norm(source_contact_moment)),
            "internal_ry_norm_nm": float(np.linalg.norm(source_internal_moment)),
        })
    record["steps"] = step_records
    record["maximum_ry_rad"] = max(row["maximum_ry_rad"]
                                    for row in step_records)
    record["maximum_source_contact_ry_moment_nm"] = max(
        row["maximum_source_contact_ry_moment_nm"] for row in step_records)
    record["maximum_free_ry_equilibrium_nm"] = max(
        row["maximum_free_ry_equilibrium_nm"] for row in step_records)
record["elapsed_seconds"] = time.perf_counter()-started
args.output.write_text(json.dumps(record, indent=2, default=_json_default)+"\n",
                       encoding="utf-8")
print(json.dumps({key: record[key] for key in (
    "solver_status", "failure_reason", "accepted_steps", "steps",
    "elapsed_seconds") if key in record}, indent=2))
