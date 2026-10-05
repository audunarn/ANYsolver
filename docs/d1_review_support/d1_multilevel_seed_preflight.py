"""Bounded preflight for coarse-pose initial iterates of the fine two-body path.

No fine equilibrium is solved, and no coarse state or checkpoint is committed.
The second sweep starts at the interpolated coarse step-one pose as a proxy;
an actual fine solve must certify its own previous-fine-to-seed sweep.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import scipy

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.core import suspend_contact
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import (
    _assemble_nonlinear_system, _discard_nonlinear_state_candidate,
)
from docs.d1_review_support.d1_two_body_16x16_linearization_preflight import (
    interpolate_target,
)
from docs.d1_review_support.d1_two_body_refined_target_route import (
    build_refined_case,
)
from docs.d1_review_support.d1_two_body_work_reference import _prolongation
from examples.general_contact_free_target_cycle_dev import (
    _independent_projected_gap_bound,
)


def _structural_residual(model, displacement):
    committed = {}
    try:
        with suspend_contact():
            internal, _tangent, _trial = _assemble_nonlinear_system(
                model, displacement, committed, 5, tangent=False,
                kinematics="von_karman", require_full_coordinates=True,
            )
        return np.asarray(internal, dtype=float)
    finally:
        _discard_nonlinear_state_candidate(committed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    started = time.perf_counter()
    saved_bytes = args.saved_record.read_bytes()
    saved = json.loads(saved_bytes)
    if (saved.get("status") != "completed" or saved.get("accepted_steps") != 2
            or saved.get("source_q4_faces") != 4
            or saved.get("target_s3_faces") != 128):
        raise ValueError("saved coarse path identity differs")
    old_model, old_definition, old_settings, old_program, old_x, old_y = (
        build_refined_case(4, 8, 8)
    )
    fine_model, fine_definition, fine_settings, fine_program, fine_x, fine_y = (
        build_refined_case(4, 16, 16)
    )
    if old_program.contract() != fine_program.contract():
        raise ValueError("coarse/fine loading programme differs")
    old_model.apply_boundary_conditions()
    fine_model.apply_boundary_conditions()
    old_manager = GeneralS3PatchManager(old_model, old_definition, old_settings)
    fine_manager = GeneralS3PatchManager(fine_model, fine_definition, fine_settings)
    full_count = fine_model.mesh.dof_manager.total_dofs
    stiffness, _info = assemble_stiffness_matrix(fine_model)
    _r, _f, transform, offset, _fixed, _constraint_info = (
        build_constraint_transformation(
            stiffness, np.zeros(full_count), fine_model)
    )
    transform = transform.tocsr()
    prolongation = _prolongation(
        old_model, fine_model, old_x, old_y, fine_x, fine_y)
    control_indices = []
    for node in (1, 6):
        dof = int(fine_model.mesh.dof_manager.get_node_dofs(node)[0])
        row = transform.getrow(dof)
        if row.nnz != 1 or row.data[0] != 1.0:
            raise ValueError("fine path control has ambiguous reduced coordinate")
        control_indices.append(int(row.indices[0]))
    free_indices = np.setdiff1d(
        np.arange(transform.shape[1]), control_indices)
    zero = np.zeros(full_count)
    zero_force = np.zeros(len(old_manager.law.pressure_mode_ids))
    initial_structural = _structural_residual(fine_model, zero)
    initial_contact = linearize(fine_manager, zero, zero_force, tangent=False)
    prior_proxy = zero
    rows = []
    for index, step in enumerate(saved["steps"], start=1):
        if step["index"] != index or step["source_pressure_node_ids"] != list(
                old_manager.law.pressure_mode_ids):
            raise ValueError("saved coarse pressure identity differs")
        old_pose = np.asarray(step["accepted_displacements"], dtype=float)
        fine_pose = interpolate_target(
            old_model, old_pose, old_x, old_y,
            fine_model, fine_x, fine_y,
        )
        if old_pose.shape != (old_model.mesh.dof_manager.total_dofs,):
            raise ValueError("saved coarse pose size differs")
        q = np.asarray(transform.T @ (fine_pose-offset)).reshape(-1)
        reconstruction = float(np.max(np.abs(
            transform @ q + offset-fine_pose)))
        target_values = fine_program.target_at(index)
        control_values = np.asarray([
            fine_pose[fine_model.mesh.dof_manager.get_node_dofs(node)[0]]
            for node in (1, 6)
        ])
        control_error = float(np.max(np.abs(control_values-target_values)))
        z = (np.asarray(step["numerical_pressure_pa"], dtype=float)
             * np.asarray(step["reference_support_m2"], dtype=float))
        old_contact = linearize(old_manager, old_pose, z, tangent=False)
        fine_contact = linearize(fine_manager, fine_pose, z, tangent=False)
        support = fine_contact.state.reference_support
        supported = bool(np.all(support[z > 0.0] > 0.0))
        nonnegative = bool(np.all(np.isfinite(z)) and np.all(z >= 0.0))
        old_work = old_contact.state.reference_support[:, None] * (
            old_contact.gap_gradient)
        fine_work = fine_contact.state.reference_support[:, None] * (
            fine_contact.gap_gradient @ prolongation)
        work_transfer = float(np.linalg.norm(fine_work-old_work)
                              / max(np.linalg.norm(old_work), 1.0e-30))
        independent_gap = float(_independent_projected_gap_bound(
            fine_model, fine_definition, fine_pose,
            fine_definition.interactions[0].gap_tolerance,
        ))
        swept = bool(fine_manager._swept_admissible(prior_proxy, fine_pose))
        internal = _structural_residual(fine_model, fine_pose)
        external = np.zeros(full_count)
        for item, value in zip(fine_program.nodal_forces,
                               fine_program.force_values_at(index), strict=True):
            if item.dof != "uz":
                raise ValueError("the saved pressure fixture requires uz forces")
            external[fine_model.mesh.dof_manager.get_node_dofs(
                item.node_id)[2]] = value
        baseline_residual = np.asarray(transform.T @ (
            initial_structural + initial_contact.force-external)).reshape(-1)
        seed_residual = np.asarray(transform.T @ (
            internal + fine_contact.force-external)).reshape(-1)
        row = {
            "step": index,
            "fine_reconstruction_maximum_error": reconstruction,
            "control_maximum_error": control_error,
            "nodal_forces_nonnegative": nonnegative,
            "forced_modes_supported": supported,
            "source_pressure_mode_ids": list(old_manager.law.pressure_mode_ids),
            "coarse_to_fine_work_relative_difference": work_transfer,
            "independent_gap_lower_m": independent_gap,
            "gap_tolerance_m": fine_definition.interactions[0].gap_tolerance,
            "proxy_previous_to_seed_swept_admissible": swept,
            "baseline_free_residual_norm_n": float(np.linalg.norm(
                baseline_residual[free_indices])),
            "seed_free_residual_norm_n": float(np.linalg.norm(
                seed_residual[free_indices])),
            "contact_integration_triangles":
                fine_contact.state.integration_triangles,
        }
        rows.append(row)
        prior_proxy = fine_pose
    status = "seed_preflight_pass" if all(
        row["fine_reconstruction_maximum_error"] <= 1.0e-10
        and row["control_maximum_error"] <= 1.0e-10
        and row["nodal_forces_nonnegative"]
        and row["forced_modes_supported"]
        and row["independent_gap_lower_m"] >= -row["gap_tolerance_m"]
        and row["proxy_previous_to_seed_swept_admissible"]
        for row in rows
    ) else "seed_preflight_non_success"
    result = {
        "status": status,
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "runtime_identity": {"python": platform.python_version(),
                             "numpy": np.__version__,
                             "scipy": scipy.__version__},
        "fine_target_s3_faces": 512,
        "fine_coordinate_count": full_count,
        "fine_reduced_coordinate_count": transform.shape[1],
        "steps": rows,
        "elapsed_seconds": time.perf_counter()-started,
    }
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": status, "steps": rows,
                      "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
    raise SystemExit(0 if status == "seed_preflight_pass" else 2)


if __name__ == "__main__":
    main()
