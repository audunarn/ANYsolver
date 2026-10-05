"""Bounded flat Q4/S3 two-body work-map cut-front discriminator.

This is an exploratory fixed-pose work check, not an equilibrium or
pressure-space qualification. It changes only the target's upper y rim.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import scipy

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSurface, create_shell_element,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import (
    complementarity, linearize, reference_nodal_support,
)
from anysolver.matrix_assembly import assemble_stiffness_matrix
from examples.general_contact_free_target_cycle_dev import build_case


def build_patch(theta: float, *, touching: bool = False):
    model = FEModel("d1_cut_front_two_body_work")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    x = np.linspace(0.0, 2.0, 5)
    y = (0.0, 1.0, 2.0)
    for row, ordinate in enumerate(y):
        for column, abscissa in enumerate(x):
            model.add_node(1+5*row+column, float(abscissa), ordinate,
                           0.04 if touching else 0.04004)
    source_elements = []
    for row in range(2):
        for column in range(4):
            bl = 1+5*row+column
            eid = 1+len(source_elements)
            model.add_element(eid, create_shell_element(
                eid, (bl, bl+1, bl+6, bl+5), "elastic", thickness=0.05,
                reference_normal=(0.0, 0.0, 1.0),
            ))
            source_elements.append(eid)
    for node, (abscissa, ordinate) in enumerate(
        ((-0.113, -0.087), (2.127, -0.087),
         (2.127, 1.0+theta), (-0.113, 1.0+theta)), start=16,
    ):
        model.add_node(node, abscissa, ordinate, 0.0)
    for eid, nodes in ((9, (16, 17, 19)), (10, (17, 18, 19))):
        model.add_element(eid, create_shell_element(
            eid, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d",
            reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "source_edge", (1, 6, 11),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "target_edge", (16, 19),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    definition = ContactDefinition(
        surfaces=(
            ContactSurface("q4_source", tuple(source_elements), "bottom"),
            ContactSurface("s3_target", (9, 10), "top"),
        ), rigid_bodies=(), interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", 10000.0, 5.0e-5,
            normal_law="augmented",
        ),),
    )
    _model, _definition, settings, _program = build_case()
    settings = replace(
        settings, maximum_candidate_pairs=32,
        maximum_q4_source_integration_triangles=1000,
    )
    model.apply_boundary_conditions()
    return model, definition, settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theta", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--two-hat-mode", action="store_true")
    parser.add_argument("--touching", action="store_true")
    args = parser.parse_args()
    if not 0.0 < args.theta <= 1.0:
        parser.error("theta must lie in (0,1]")
    if args.output.exists():
        parser.error("output already exists")
    start = time.perf_counter()
    model, definition, settings = build_patch(args.theta,
                                             touching=args.touching)
    manager = GeneralS3PatchManager(model, definition, settings)
    zero_pose = np.zeros(model.mesh.dof_manager.total_dofs)
    count = len(manager.law.pressure_mode_ids)
    state = linearize(manager, zero_pose, np.zeros(count), tangent=False)
    support = np.asarray(state.state.reference_support)
    node_index = {node: index for index, node in
                  enumerate(manager.law.pressure_mode_ids)}
    theta = args.theta
    b = theta**2/2-theta**3/3
    d = 0.25+theta-theta**2+theta**3/3
    beta = -b/d
    pressure = np.zeros(count)
    if args.two_hat_mode:
        from docs.d1_review_support.d1_cut_front_two_hat_limit import (
            limit_matrix, null_coefficients,
        )
        x_coefficients = null_coefficients(sum(limit_matrix()))
        authored_nodes = []
        for column, x_coefficient in ((2, x_coefficients[0]),
                                      (3, x_coefficients[1])):
            for row, y_coefficient in enumerate((-beta/2, beta, 1.0)):
                node = 1+5*row+column
                pressure[node_index[node]] = x_coefficient*y_coefficient
                authored_nodes.append(node)
    else:
        x_coefficients = np.asarray((1.0,))
        authored_nodes = [3, 8, 13]
        for node, coefficient in ((3, -beta/2), (8, beta), (13, 1.0)):
            pressure[node_index[node]] = coefficient
    positive = np.flatnonzero(np.abs(pressure) > 0.0)
    if np.any(support[positive] <= 0.0):
        raise AssertionError("constructed cut-front pressure has no support")
    force = support*pressure
    full_work = force @ state.gap_gradient
    source_dofs = np.concatenate([
        model.mesh.dof_manager.get_node_dofs(node)
        for node in range(1, 16)
    ])
    target_dofs = np.concatenate([
        model.mesh.dof_manager.get_node_dofs(node)
        for node in range(16, 20)
    ])
    checked = linearize(manager, zero_pose, force, tangent=False)
    work_balance = float(np.linalg.norm(checked.force+full_work))
    source_normal_by_node = full_work[source_dofs].reshape(-1, 6)[:, 2]
    target_normal_by_node = full_work[target_dofs].reshape(-1, 6)[:, 2]
    energy_check = None
    active_baseline_check = None
    if args.touching and args.two_hat_mode:
        baseline_pressure = np.zeros(count)
        baseline_pressure[positive] = 1.0
        baseline_force = support*baseline_pressure
        baseline = linearize(manager, zero_pose, baseline_force,
                             tangent=False)
        full_reference = reference_nodal_support(manager.law)
        complement, active, _, _ = complementarity(
            baseline.state, baseline_force,
            10000.0*full_reference, baseline.gap_gradient,
            tangent=False,
        )
        active_baseline_check = {
            "strict_positive_pressure_modes": int(len(positive)),
            "selected_support_minimum_m2": float(np.min(support[positive])),
            "selected_gap_maximum_abs_m": float(np.max(np.abs(
                baseline.state.normalized_gap[positive]))),
            "selected_complementarity_l1_n": float(np.sum(np.abs(
                complement[positive]))),
            "all_supported_gap_maximum_abs_m": float(np.max(np.abs(
                baseline.state.normalized_gap[support > 0.0]))),
            "all_supported_complementarity_l1_n": float(np.sum(np.abs(
                complement[support > 0.0]))),
            "other_zero_pressure_supported_modes": int(np.count_nonzero(
                (support > 0.0) & (baseline_pressure == 0.0))),
            "selected_projected_active_modes":
                int(np.count_nonzero(active[positive])),
            "signed_half_pascal_perturbation_minimum_pressure_pa":
                float(np.min(np.r_[1.0+0.5*pressure[positive],
                                   1.0-0.5*pressure[positive]])),
            "free_contact_force_l2": None,
        }
    if args.two_hat_mode:
        stiffness = assemble_stiffness_matrix(model)[0]
        _r, _f, transform, offset, _fixed, _info = (
            build_constraint_transformation(
                stiffness, np.zeros(len(zero_pose)), model,
            )
        )
        if np.linalg.norm(offset) != 0.0:
            raise AssertionError("unexpected constrained-coordinate offset")
        reduced = np.asarray((transform.T @ stiffness @ transform).toarray())
        skew = float(np.linalg.norm(reduced-reduced.T)/
                     max(np.linalg.norm(reduced), 1.0e-30))
        symmetric = 0.5*(reduced+reduced.T)
        eigenvalues = np.linalg.eigvalsh(symmetric)
        if eigenvalues[0] <= 0.0 or skew > 1.0e-10:
            raise AssertionError("contact-free reduced shell energy is not SPD")
        reduced_work = np.asarray(full_work @ transform).reshape(-1)
        if active_baseline_check is not None:
            active_baseline_check["free_contact_force_l2"] = float(
                np.linalg.norm(np.asarray(transform.T @ baseline.force)))
            manufactured = np.zeros(len(zero_pose))
            loads = []
            other_maximum = 0.0
            for node in range(1, 20):
                if node in (1, 6, 11, 16, 19):
                    continue
                dofs = np.asarray(model.mesh.dof_manager.get_node_dofs(node),
                                  dtype=int)
                value = float(baseline.force[dofs[2]])
                manufactured[dofs[2]] = value
                loads.append({"node_id": node, "uz_n": value})
                other_maximum = max(other_maximum, float(np.max(np.abs(
                    baseline.force[dofs[[0, 1, 3, 4, 5]]]))))
            active_baseline_check["manufactured_nodal_loads"] = loads
            active_baseline_check["other_free_component_maximum"] = (
                other_maximum)
            active_baseline_check["manufactured_reduced_residual_l2"] = (
                float(np.linalg.norm(np.asarray(
                    transform.T @ (baseline.force-manufactured)))))
        response = np.linalg.solve(symmetric, reduced_work)
        dual_squared = float(reduced_work @ response)
        relative_residual = float(np.linalg.norm(
            symmetric@response-reduced_work)
            /max(np.linalg.norm(reduced_work), 1.0e-30))
        energy_check = {
            "free_coordinates": int(transform.shape[1]),
            "stiffness_symmetry_relative": skew,
            "stiffness_minimum_eigenvalue": float(eigenvalues[0]),
            "stiffness_maximum_eigenvalue": float(eigenvalues[-1]),
            "reduced_work_l2": float(np.linalg.norm(reduced_work)),
            "discrete_energy_dual_work": float(np.sqrt(max(0.0,
                                                           dual_squared))),
            "energy_response_relative_residual": relative_residual,
        }
    result = {
        "status": "development_fixed_pose_work_map",
        "theta": theta,
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__, "scipy": scipy.__version__,
            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
            "omp_threads": os.environ.get("OMP_NUM_THREADS"),
        },
        "source_faces": 8, "target_faces": 2,
        "two_hat_mode": args.two_hat_mode,
        "touching": args.touching,
        "x_hat_coefficients": x_coefficients.tolist(),
        "pressure_modes": count,
        "pressure_node_ids": authored_nodes,
        "pressure_coefficients": pressure[positive].tolist(),
        "pressure_support_m2": support[positive].tolist(),
        "minimum_gap_m": float(np.min(state.state.normalized_gap[positive])),
        "expected_scalar_last_y_work": theta**3/3-b*b/d,
        "expected_scalar_continuous_witness_work": beta/120,
        "source_full_work_l2": float(np.linalg.norm(full_work[source_dofs])),
        "target_full_work_l2": float(np.linalg.norm(full_work[target_dofs])),
        "all_full_work_l2": float(np.linalg.norm(full_work)),
        "source_normal_work_l2": float(np.linalg.norm(
            full_work[source_dofs].reshape(-1, 6)[:, 2])),
        "source_rotation_work_l2": float(np.linalg.norm(
            full_work[source_dofs].reshape(-1, 6)[:, 3:])),
        "target_normal_work_l2": float(np.linalg.norm(
            full_work[target_dofs].reshape(-1, 6)[:, 2])),
        "source_normal_work_by_node": source_normal_by_node.tolist(),
        "target_normal_work_by_node": target_normal_by_node.tolist(),
        "source_free_normal_work_l2": float(np.linalg.norm(
            source_normal_by_node[[i for i in range(15)
                                   if i not in (0, 5, 10)]])),
        "target_free_normal_work_l2": float(np.linalg.norm(
            target_normal_by_node[[1, 2]])),
        "target_rotation_work_l2": float(np.linalg.norm(
            full_work[target_dofs].reshape(-1, 6)[:, 3:])),
        "energy_check": energy_check,
        "active_baseline_check": active_baseline_check,
        "virtual_work_residual_l2": work_balance,
        "elapsed_s": time.perf_counter()-start,
    }
    args.output.write_text(json.dumps(result, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        key: result[key] for key in (
            "theta", "source_full_work_l2", "target_full_work_l2",
            "all_full_work_l2", "virtual_work_residual_l2", "elapsed_s",
        )
    }))


if __name__ == "__main__":
    main()
