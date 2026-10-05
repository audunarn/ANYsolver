"""Fixed-pose two-body pressure-work detection under target refinement.

Development discriminator only. The accepted 4-Q4/8x8-S3 press pose and its
ten physical source Q1 pressure functions are held fixed. Target structural
coordinates are enriched to 16x16 without solving another contact path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
from scipy import linalg, sparse

import anysolver
import scipy
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from docs.d1_review_support.d1_two_body_16x16_linearization_preflight import (
    interpolate_target,
)
from docs.d1_review_support.d1_two_body_refined_target_route import (
    build_refined_case,
)


def _target_weights(old_x, old_y, x, y, old_stride):
    i = min(len(old_x)-2, max(0, int(np.searchsorted(old_x, x,
                                                  side="right")-1)))
    j = min(len(old_y)-2, max(0, int(np.searchsorted(old_y, y,
                                                  side="right")-1)))
    xi = float((x-old_x[i])/(old_x[i+1]-old_x[i]))
    eta = float((y-old_y[j])/(old_y[j+1]-old_y[j]))
    bl = 11+j*old_stride+i
    br, tl = bl+1, bl+old_stride
    tr = tl+1
    if xi+eta <= 1.0:
        return ((bl, 1.0-xi-eta), (br, xi), (tl, eta))
    return ((br, 1.0-eta), (tr, xi+eta-1.0), (tl, 1.0-xi))


def _prolongation(coarse_model, fine_model, old_x, old_y, fine_x, fine_y):
    coarse_dofs = coarse_model.mesh.dof_manager
    fine_dofs = fine_model.mesh.dof_manager
    result = sparse.lil_matrix((fine_dofs.total_dofs, coarse_dofs.total_dofs))
    for node in range(1, 11):
        old = coarse_dofs.get_node_dofs(node)
        new = fine_dofs.get_node_dofs(node)
        for component in range(6):
            result[new[component], old[component]] = 1.0
    for row, y in enumerate(fine_y):
        for column, x in enumerate(fine_x):
            new_node = 11+row*len(fine_x)+column
            new = fine_dofs.get_node_dofs(new_node)
            for old_node, weight in _target_weights(
                    old_x, old_y, x, y, len(old_x)):
                old = coarse_dofs.get_node_dofs(old_node)
                for component in range(6):
                    result[new[component], old[component]] = weight
    return result.tocsr()


def _free_transform(model, stiffness, controlled_nodes):
    total = model.mesh.dof_manager.total_dofs
    _r, _f, transform, offset, _fixed, _info = (
        build_constraint_transformation(stiffness, np.zeros(total), model)
    )
    if float(np.linalg.norm(offset)) != 0.0:
        raise AssertionError("two-body reference has unexpected constraint offset")
    transform = transform.tocsr()
    controlled = []
    for node in controlled_nodes:
        dof = int(model.mesh.dof_manager.get_node_dofs(node)[0])
        row = transform.getrow(dof)
        if row.nnz != 1 or row.data[0] != 1.0:
            raise AssertionError("two-body control coordinate is ambiguous")
        controlled.append(int(row.indices[0]))
    free = np.setdiff1d(np.arange(transform.shape[1]), controlled)
    return transform[:, free].tocsr()


def _compliance(work, energy):
    matrix = energy.toarray() if sparse.issparse(energy) else np.asarray(energy)
    matrix = 0.5*(matrix+matrix.T)
    diagonal = np.diag(matrix)
    if np.any(diagonal <= 0.0):
        raise AssertionError("two-body structural energy has nonpositive diagonal")
    cholesky = linalg.cho_factor(matrix, lower=True, check_finite=True)
    response = linalg.cho_solve(cholesky, work.T, check_finite=True)
    result = work @ response
    residual = float(np.linalg.norm(matrix@response-work.T)
                     /max(np.linalg.norm(work.T), 1.0e-30))
    return 0.5*(result+result.T), residual


def _active_ratio(restricted, reference, active):
    a = restricted[np.ix_(active, active)]
    b = reference[np.ix_(active, active)]
    diagonal = np.sqrt(np.diag(b))
    scaled_b = b/np.outer(diagonal, diagonal)
    minimum = float(np.linalg.eigvalsh(scaled_b)[0])
    if minimum <= 1.0e-11:
        raise AssertionError("two-body active reference compliance is singular")
    values = linalg.eigvalsh(a/np.outer(diagonal, diagonal), scaled_b)
    return [float(values[0]), float(values[-1])], minimum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--nested-target", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    started = time.perf_counter()
    saved_bytes = args.saved_record.read_bytes()
    saved = json.loads(saved_bytes)
    assert saved["status"] == "completed" and saved["accepted_steps"] == 2
    assert saved["source_q4_faces"] == 4 and saved["target_s3_faces"] == 128
    coarse, coarse_definition, coarse_settings, _program, old_x, old_y = (
        build_refined_case(4, 8, 8)
    )
    def insert_midpoints(knots):
        result = np.empty(2*len(knots)-1)
        result[::2] = knots
        result[1::2] = 0.5*(knots[:-1]+knots[1:])
        return result

    explicit_knots = ((insert_midpoints(old_x), insert_midpoints(old_y))
                      if args.nested_target else None)
    fine, fine_definition, fine_settings, _program, fine_x, fine_y = (
        build_refined_case(4, 16, 16, target_knots=explicit_knots)
    )
    np.testing.assert_allclose(fine_x[::2], old_x, rtol=0, atol=1.0e-14)
    np.testing.assert_allclose(fine_y[::2], old_y, rtol=0, atol=1.0e-14)
    coarse.apply_boundary_conditions()
    fine.apply_boundary_conditions()
    old_pose = np.asarray(saved["final_displacements"], dtype=float)
    fine_pose = interpolate_target(coarse, old_pose, old_x, old_y,
                                   fine, fine_x, fine_y)
    prolongation = _prolongation(coarse, fine, old_x, old_y, fine_x, fine_y)
    pose_error = float(np.max(np.abs(fine_pose-prolongation@old_pose)))
    coarse_manager = GeneralS3PatchManager(coarse, coarse_definition,
                                           coarse_settings)
    fine_manager = GeneralS3PatchManager(fine, fine_definition, fine_settings)
    old_source, old_target = coarse_manager._positions(old_pose)
    fine_source, fine_target = fine_manager._positions(fine_pose)
    source_skin_error = float(np.max(np.linalg.norm(
        fine_source-old_source, axis=1)))
    target_skin_error = 0.0
    for row, y in enumerate(fine_y):
        for column, x in enumerate(fine_x):
            expected = sum((weight*old_target[old_node-11]
                            for old_node, weight in _target_weights(
                                old_x, old_y, x, y, len(old_x))),
                           np.zeros(3))
            index = row*len(fine_x)+column
            target_skin_error = max(target_skin_error, float(np.linalg.norm(
                fine_target[index]-expected)))
    saved_step = saved["steps"][-1]
    pressure = np.asarray(saved_step["numerical_pressure_pa"], dtype=float)
    support_saved = np.asarray(saved_step["reference_support_m2"], dtype=float)
    active = np.flatnonzero(pressure > 0.0)
    if len(active) != 2:
        raise AssertionError("saved two-body front changed")
    nodal_forces = pressure*support_saved
    old = linearize(coarse_manager, old_pose, nodal_forces, tangent=False)
    new = linearize(fine_manager, fine_pose, nodal_forces, tangent=False)
    old_support = old.state.reference_support
    new_support = new.state.reference_support
    support_error = float(np.linalg.norm(new_support-old_support)
                          /np.linalg.norm(old_support))
    saved_support_error = float(np.linalg.norm(old_support-support_saved)
                                /np.linalg.norm(support_saved))
    gap_error = float(np.max(np.abs(new.state.normalized_gap
                                    -old.state.normalized_gap)))
    coarse_k = assemble_stiffness_matrix(coarse)[0]
    fine_k = assemble_stiffness_matrix(fine)[0]
    old_free = _free_transform(coarse, coarse_k, (1, 6))
    fine_free = _free_transform(fine, fine_k, (1, 6))
    restricted_prolongation = prolongation @ old_free
    reduced_prolongation = (fine_free.T @ restricted_prolongation).tocsr()
    reconstruction_error = float(np.linalg.norm(
        (fine_free @ reduced_prolongation-restricted_prolongation).toarray())
        /max(np.linalg.norm(restricted_prolongation.toarray()), 1.0e-30))
    old_work = old_support[:, None]*np.asarray(old.gap_gradient @ old_free)
    fine_work = new_support[:, None]*np.asarray(new.gap_gradient @ fine_free)
    work_error = float(np.linalg.norm(fine_work@reduced_prolongation-old_work)
                       /max(np.linalg.norm(old_work), 1.0e-30))
    full_old_work = old_support[:, None]*old.gap_gradient
    full_fine_work = new_support[:, None]*(new.gap_gradient @ prolongation)
    full_work_delta = full_fine_work-full_old_work
    work_scale = max(np.linalg.norm(old_work), 1.0e-30)
    source_columns = np.concatenate([
        coarse.mesh.dof_manager.get_node_dofs(node)
        for node in range(1, 11)
    ])
    target_columns = np.setdiff1d(
        np.arange(coarse.mesh.dof_manager.total_dofs), source_columns)
    source_free_delta = (full_work_delta[:, source_columns]
                         @ old_free[source_columns, :])
    target_free_delta = (full_work_delta[:, target_columns]
                         @ old_free[target_columns, :])
    transferred_work_delta = full_work_delta @ old_free
    record = {
        "status": "development_two_body_work_transfer",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "runtime_identity": {
            "python": platform.python_version(),
            "numpy": np.__version__, "scipy": scipy.__version__,
            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
            "omp_threads": os.environ.get("OMP_NUM_THREADS"),
        },
        "source_q4_faces": 4, "coarse_target_s3_faces": 128,
        "fine_target_s3_faces": 512,
        "target_reference_grid": ("true_midpoint_nested"
                                  if args.nested_target else "independently_shifted"),
        "pressure_modes": len(pressure), "active_pressure_modes": active.tolist(),
        "pose_prolongation_maximum_error": pose_error,
        "source_skin_maximum_error_m": source_skin_error,
        "target_skin_maximum_error_m": target_skin_error,
        "coarse_saved_support_relative_error": saved_support_error,
        "support_l2_relative_error": support_error,
        "normalized_gap_maximum_error_m": gap_error,
        "structural_prolongation_reconstruction_relative":
            reconstruction_error,
        "pressure_work_prolongation_relative_error": work_error,
        "diagnostic_work_delta": {
            "source_free_relative": float(np.linalg.norm(source_free_delta)
                                          / work_scale),
            "target_free_relative": float(np.linalg.norm(target_free_delta)
                                          / work_scale),
            "active_free_relative": float(np.linalg.norm(
                transferred_work_delta[active]) / work_scale),
            "inactive_free_relative": float(np.linalg.norm(
                transferred_work_delta[np.setdiff1d(
                    np.arange(len(pressure)), active)]) / work_scale),
            "per_mode_free_relative": (
                np.linalg.norm(transferred_work_delta, axis=1)
                / work_scale).tolist(),
            "coarse_integration_triangles": old.state.integration_triangles,
            "fine_integration_triangles": new.state.integration_triangles,
        },
    }
    guards = (pose_error <= 1.0e-12 and source_skin_error <= 1.0e-8
              and target_skin_error <= 1.0e-8
              and support_error <= 1.0e-8 and saved_support_error <= 1.0e-8
              and gap_error <= 1.0e-8 and reconstruction_error <= 1.0e-10
              and work_error <= 1.0e-7)
    if not guards:
        record["status"] = "development_two_body_work_transfer_non_success"
    else:
        coarse_energy = (old_free.T @ coarse_k @ old_free).tocsr()
        fine_energy = (fine_free.T @ fine_k @ fine_free).tocsr()
        restricted_energy = (
            reduced_prolongation.T @ fine_energy @ reduced_prolongation
        ).tocsr()
        coarse_c, coarse_residual = _compliance(old_work, coarse_energy)
        fine_c, fine_residual = _compliance(fine_work, fine_energy)
        restricted_work = np.asarray(fine_work @ reduced_prolongation)
        restricted_c, restricted_residual = _compliance(
            restricted_work, restricted_energy)
        bridge_c, _bridge_residual = _compliance(old_work, restricted_energy)
        ratio, active_reference_minimum = _active_ratio(
            restricted_c, fine_c, active)
        active_rows = np.ix_(active, active)
        reference_scale = np.sqrt(np.diag(fine_c)[active])
        scaled_defect = ((fine_c[active_rows]-restricted_c[active_rows])
                         /np.outer(reference_scale, reference_scale))
        projector_psd_minimum = float(np.linalg.eigvalsh(
            0.5*(scaled_defect+scaled_defect.T))[0])
        bridge_error = float(np.linalg.norm(restricted_c-bridge_c)
                             /max(np.linalg.norm(restricted_c), 1.0e-30))
        record.update({
            "coarse_free_coordinates": coarse_energy.shape[0],
            "fine_free_coordinates": fine_energy.shape[0],
            "coarse_response_relative_residual": coarse_residual,
            "fine_response_relative_residual": fine_residual,
            "restricted_response_relative_residual": restricted_residual,
            "pressure_work_bridge_compliance_relative": bridge_error,
            "active_fine_minus_restricted_scaled_minimum_eigenvalue":
                projector_psd_minimum,
            "active_reference_scaled_minimum_eigenvalue":
                active_reference_minimum,
            "active_same_energy_squared_ratio_range": ratio,
        })
        if (projector_psd_minimum < -1.0e-8 or fine_residual > 1.0e-8
                or restricted_residual > 1.0e-8 or bridge_error > 1.0e-6):
            record["status"] = "development_two_body_energy_non_success"
    record["elapsed_seconds"] = time.perf_counter()-started
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key in ("status", "active_same_energy_squared_ratio_range",
                                 "pressure_work_prolongation_relative_error",
                                 "target_skin_maximum_error_m",
                                 "elapsed_seconds")}, indent=2))
    raise SystemExit(0 if record["status"] ==
                     "development_two_body_work_transfer" else 2)


if __name__ == "__main__":
    main()
