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
from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSurface, create_shell_element,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from examples.general_contact_free_target_cycle_dev import build_case


def build_patch(theta: float):
    model = FEModel("d1_cut_front_two_body_work")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    x = np.linspace(0.0, 2.0, 5)
    y = (0.0, 1.0, 2.0)
    for row, ordinate in enumerate(y):
        for column, abscissa in enumerate(x):
            model.add_node(1+5*row+column, float(abscissa), ordinate,
                           0.04004)
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
    args = parser.parse_args()
    if not 0.0 < args.theta <= 1.0:
        parser.error("theta must lie in (0,1]")
    if args.output.exists():
        parser.error("output already exists")
    start = time.perf_counter()
    model, definition, settings = build_patch(args.theta)
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
        "pressure_modes": count,
        "pressure_node_ids": [3, 8, 13],
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
