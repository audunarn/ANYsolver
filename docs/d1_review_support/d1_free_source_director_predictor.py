"""Contact-free constrained predictor for the free-source-ry press failure."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from anysolver import BoundaryCondition
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_free_target_press_probe import (
    build_free_target_case,
)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("output already exists")
started = time.perf_counter()


def predict(free_ry, left_ry_clamp=False):
    model, definition, settings, program = build_free_target_case(
        4, steps_per_segment=2, four_phase=False,
        enforcement_solver="monolithic_active_set")
    if free_ry:
        guide = next(bc for bc in model.boundary_conditions
                     if bc.name == "source_guide")
        model.boundary_conditions = [
            BoundaryCondition(guide.name, guide.node_ids,
                              {"uy": 0.0, "rx": 0.0, "rz": 0.0})
            if bc is guide else bc for bc in model.boundary_conditions]
    if left_ry_clamp:
        if not free_ry:
            raise AssertionError("left-edge ry correction requires free interior ry")
        support = next(bc for bc in model.boundary_conditions
                       if bc.name == "source_left_support")
        if support.dof_constraints != {"uz": 0.0}:
            raise AssertionError("unexpected source support definition")
        model.boundary_conditions = [
            BoundaryCondition(support.name, support.node_ids,
                              {"uz": 0.0, "ry": 0.0})
            if bc is support else bc for bc in model.boundary_conditions]
    model.apply_boundary_conditions()
    stiffness = assemble_stiffness_matrix(model)[0]
    rhs = np.zeros(stiffness.shape[0])
    for load in program.nodal_forces:
        if load.dof != "uz" or len(load.values_n) != 2:
            raise AssertionError("unexpected nodal load profile")
        rhs[model.mesh.dof_manager.get_node_dofs(load.node_id)[2]] += (
            0.5*load.values_n[-1])
    _k, _f, transform, offset, _fixed, _info = (
        build_constraint_transformation(stiffness, rhs, model))
    if np.linalg.norm(offset) != 0.0:
        raise AssertionError("unexpected boundary offset")
    transform = transform.tocsr()
    control_indices = []
    for control in program.controls:
        if len(control.terms) != 1:
            raise AssertionError("unexpected control profile")
        node, dof_name, weight = control.terms[0]
        if dof_name != "ux" or weight != 1.0:
            raise AssertionError("unexpected controlled coordinate")
        full_dof = model.mesh.dof_manager.get_node_dofs(node)[0]
        row = transform.getrow(full_dof)
        if row.nnz != 1 or row.data[0] != 1.0:
            raise AssertionError("ambiguous controlled coordinate")
        control_indices.append(int(row.indices[0]))
    free = np.setdiff1d(np.arange(transform.shape[1]), control_indices)
    physical = transform[:, free]
    reduced = (physical.T @ stiffness @ physical).tocsc()
    diagonal = reduced.diagonal()
    scaled = (sparse.diags(1.0/np.sqrt(diagonal)) @ reduced
              @ sparse.diags(1.0/np.sqrt(diagonal))).toarray()
    minimum = float(np.linalg.eigvalsh(0.5*(scaled+scaled.T))[0])
    if minimum <= 1e-10:
        ideal = np.zeros(stiffness.shape[0])
        for node in range(1, 11):
            dofs = model.mesh.dof_manager.get_node_dofs(node)
            ideal[dofs[2]] = -(model.mesh.nodes[node].x-0.1)
            ideal[dofs[4]] = 1.0
        projection = np.asarray(physical @ (physical.T @ ideal)).reshape(-1)
        reduced_force = np.asarray(physical.T @ (stiffness @ ideal)).reshape(-1)
        reference_force = np.asarray(physical.T @ (
            stiffness.diagonal()*ideal)).reshape(-1)
        return {"free_ry": free_ry,
                "left_ry_clamp": left_ry_clamp,
                "scaled_stiffness_minimum": minimum,
                "status": "structural_metric_nonpositive",
                "ideal_rigid_y_constraint_error": float(np.linalg.norm(
                    ideal-projection)/np.linalg.norm(ideal)),
                "ideal_rigid_y_scaled_energy": float(
                    ideal @ stiffness @ ideal
                    /max(ideal @ (stiffness.diagonal()*ideal), 1e-30)),
                "ideal_rigid_y_reduced_force_ratio": float(
                    np.linalg.norm(reduced_force)
                    /max(np.linalg.norm(reference_force), 1e-30))}
    reduced_rhs = np.asarray(physical.T @ rhs).reshape(-1)
    solution = spsolve(reduced, reduced_rhs)
    displacement = np.asarray(physical @ solution).reshape(-1)
    manager = GeneralS3PatchManager(model, definition, settings)
    source, target = manager._positions(displacement)
    state = manager.law.evaluate(
        source, target, np.zeros(len(manager.law.pressure_mode_ids)))
    ry = [model.mesh.dof_manager.get_node_dofs(node)[4]
          for node in manager.law.source_node_ids]
    return {
        "free_ry": free_ry,
        "left_ry_clamp": left_ry_clamp,
        "status": "linear_predictor_complete",
        "scaled_stiffness_minimum": minimum,
        "free_coordinates": int(reduced.shape[0]),
        "linear_solve_relative_residual": float(np.linalg.norm(
            reduced @ solution-reduced_rhs)
            /max(np.linalg.norm(reduced_rhs), 1e-30)),
        "maximum_source_ry_rad": float(np.max(np.abs(displacement[ry]))),
        "minimum_sampled_physical_gap_m": float(state.minimum_physical_gap),
        "minimum_normalized_gap_m": float(np.min(state.normalized_gap)),
        "maximum_normalized_gap_m": float(np.max(state.normalized_gap)),
        "source_uz_range_m": [float(np.min(displacement[[
            model.mesh.dof_manager.get_node_dofs(node)[2]
            for node in manager.law.source_node_ids]])),
            float(np.max(displacement[[
                model.mesh.dof_manager.get_node_dofs(node)[2]
                for node in manager.law.source_node_ids]]))],
    }


record = {
    "status": "development_free_ry_linear_predictor",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "load_fraction": 0.5,
    "guided": predict(False),
    "free_ry": predict(True),
    "free_interior_ry": predict(True, left_ry_clamp=True),
    "elapsed_seconds": time.perf_counter()-started,
}
args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
print(json.dumps(record, indent=2))
