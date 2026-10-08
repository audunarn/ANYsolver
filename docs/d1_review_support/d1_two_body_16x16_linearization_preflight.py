"""Bounded active-pose local-cost preflight before a 16x16 target solve.

Uses the accepted 8x8 pose and pressure, interpolates only target structural
coordinates to a nested 16x16 mesh, and times one complete monolithic contact
linearization at each size. No equilibrium solve or reference claim is made.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

import anysolver
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from docs.d1_review_support.d1_two_body_refined_target_route import build_refined_case


def interpolate_target(old_model, old_pose, old_x, old_y,
                       fine_model, fine_x, fine_y):
    np.testing.assert_allclose(fine_x[::2], old_x, rtol=0, atol=1e-14)
    np.testing.assert_allclose(fine_y[::2], old_y, rtol=0, atol=1e-14)
    result = np.zeros(fine_model.mesh.dof_manager.total_dofs)
    for node in range(1, 11):
        result[fine_model.mesh.dof_manager.get_node_dofs(node)] = (
            old_pose[old_model.mesh.dof_manager.get_node_dofs(node)]
        )
    old_stride = len(old_x)
    fine_stride = len(fine_x)
    for row, y in enumerate(fine_y):
        for column, x in enumerate(fine_x):
            i = min(len(old_x)-2, max(0, int(np.searchsorted(old_x, x,
                                                          side="right")-1)))
            j = min(len(old_y)-2, max(0, int(np.searchsorted(old_y, y,
                                                          side="right")-1)))
            xi = float((x-old_x[i])/(old_x[i+1]-old_x[i]))
            eta = float((y-old_y[j])/(old_y[j+1]-old_y[j]))
            bl = 11+j*old_stride+i
            br = bl+1
            tl = bl+old_stride
            tr = tl+1
            if xi+eta <= 1.0:
                nodes = (bl, br, tl)
                weights = (1.0-xi-eta, xi, eta)
            else:
                nodes = (br, tr, tl)
                weights = (1.0-eta, xi+eta-1.0, 1.0-xi)
            fine_node = 11+row*fine_stride+column
            fine_dofs = fine_model.mesh.dof_manager.get_node_dofs(fine_node)
            result[fine_dofs] = sum(
                weight*old_pose[old_model.mesh.dof_manager.get_node_dofs(node)]
                for node, weight in zip(nodes, weights, strict=True)
            )
    return result


def one_case(model, definition, settings, pose, nodal_forces):
    started = time.perf_counter()
    model.apply_boundary_conditions()
    structural, _info = assemble_stiffness_matrix(model)
    structural_seconds = time.perf_counter()-started
    manager = GeneralS3PatchManager(model, definition, settings)
    preparation_seconds = time.perf_counter()-started-structural_seconds
    linearized = linearize(manager, pose, nodal_forces, tangent=True)
    linearization_seconds = (time.perf_counter()-started
                             -structural_seconds-preparation_seconds)
    return {
        "target_s3_faces": len(definition.surfaces[1].element_ids),
        "structural_dofs": model.mesh.dof_manager.total_dofs,
        "structural_nnz": structural.nnz,
        "structural_assembly_seconds": structural_seconds,
        "contact_preparation_seconds": preparation_seconds,
        "active_contact_linearization_seconds": linearization_seconds,
        "contact_tangent_nnz": linearized.tangent.nnz,
        "contact_evaluations": linearized.evaluations,
        "supported_pressure_modes": int(np.count_nonzero(
            linearized.state.reference_support > 0.0,
        )),
        "reference_overlap_area_m2":
            linearized.state.reference_overlap_area,
        "normalized_gap_m": linearized.state.normalized_gap.tolist(),
        "reference_support_m2": linearized.state.reference_support.tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    saved_bytes = args.saved_record.read_bytes()
    saved = json.loads(saved_bytes)
    assert saved["status"] == "completed" and saved["accepted_steps"] == 2
    assert saved["source_q4_faces"] == 4 and saved["target_s3_faces"] == 128
    old_model, old_definition, old_settings, _path, old_x, old_y = (
        build_refined_case(4, 8, 8)
    )
    np.testing.assert_array_equal(old_x, saved["target_x_knots_m"])
    np.testing.assert_array_equal(old_y, saved["target_y_knots_m"])
    fine_model, fine_definition, fine_settings, _path, fine_x, fine_y = (
        build_refined_case(4, 16, 16)
    )
    old_pose = np.asarray(saved["final_displacements"], dtype=float)
    fine_pose = interpolate_target(old_model, old_pose, old_x, old_y,
                                   fine_model, fine_x, fine_y)
    saved_step = saved["steps"][-1]
    assert saved_step["source_pressure_node_ids"] == list(range(1, 11))
    nodal_forces = (np.asarray(saved_step["numerical_pressure_pa"])
                    *np.asarray(saved_step["reference_support_m2"]))
    old_case = one_case(old_model, old_definition, old_settings,
                        old_pose, nodal_forces)
    np.testing.assert_allclose(old_case["reference_support_m2"],
                               saved_step["reference_support_m2"],
                               rtol=1e-10, atol=1e-12)
    fine_case = one_case(fine_model, fine_definition, fine_settings,
                         fine_pose, nodal_forces)
    record = {
        "status": "development_16x16_active_local_cost_preflight",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True,
        ).strip(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "old_case": old_case,
        "fine_case": fine_case,
        "fine_pose_maximum_translation_m": float(np.max(np.abs(
            fine_pose.reshape(-1, 6)[:, :3],
        ))),
    }
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "status": record["status"],
        "old_linearization_seconds": old_case["active_contact_linearization_seconds"],
        "fine_linearization_seconds": fine_case["active_contact_linearization_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
