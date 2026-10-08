"""Analytic positive-support pressure null at a guided shell clamp.

Derive the tensor-Q1 source-transverse null independently, construct a
continuous admissible virtual-work witness, then compare the same vectors
with the saved nonlinear shell contact work. No new equilibrium is solved.
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
from scipy import sparse

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def _q1_mass(knots, *, upper):
    """Exact polynomial Q1 mass on each full or clipped line element."""
    result = np.zeros((len(knots), len(knots)))
    for element in range(len(knots)-1):
        left = float(knots[element])
        width = float(knots[element+1]-left)
        end = min(1.0, max(0.0, (upper-left)/width))
        if end <= 0.0:
            continue
        diagonal_left = width*(end-end*end+end**3/3.0)
        offdiagonal = width*(end*end/2.0-end**3/3.0)
        diagonal_right = width*end**3/3.0
        local = np.array(((diagonal_left, offdiagonal),
                          (offdiagonal, diagonal_right)))
        ids = np.array((element, element+1))
        result[np.ix_(ids, ids)] += local
    return result


def _continuous_x_witness(x, coefficients):
    """Integrate x*r(x)^2 exactly by two-point Gauss on each element."""
    value = 0.0
    for element in range(len(x)-1):
        left, right = x[element:element+2]
        width = right-left
        for root in (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0)):
            point = (left+right+root*width)/2.0
            shape = np.array(((right-point)/width,
                              (point-left)/width))
            line = float(shape @ coefficients[element:element+2])
            value += width/2.0*point*line*line
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    started = time.perf_counter()
    saved_bytes = args.saved.read_bytes()
    saved = json.loads(saved_bytes)
    if (saved.get("status") != "completed" or saved.get("columns") != 16
            or saved.get("source_rows") != 8
            or saved.get("source_y_profile") != "near_rim8"):
        raise ValueError("saved shell pose differs from the 16×8 near-rim fixture")
    columns = saved["columns"]
    rows = saved["source_rows"]
    x = np.linspace(0.0, 1.0, columns+1)
    y = np.array((0.0, 0.2, 0.4, 0.6, 0.75, 0.825, 0.875, 0.895, 1.0))
    mx = _q1_mass(x, upper=1.0)
    my = _q1_mass(y, upper=0.9)
    gram = np.kron(my, mx)
    x_null = np.linalg.solve(mx, np.eye(len(x))[:, 0])
    null_vectors = np.kron(np.eye(len(y)), x_null[:, None])
    free_x = np.flatnonzero(np.arange(len(x)*len(y)) % len(x) != 0)
    discrete_work = gram[free_x]
    absolute_null_work = float(np.linalg.norm(discrete_work @ null_vectors))
    scaled_null_work = absolute_null_work / (
        np.linalg.norm(discrete_work)*np.linalg.norm(null_vectors))
    rank = int(np.linalg.matrix_rank(discrete_work, tol=1e-10))
    full_mass_energy = float(x_null @ mx @ x_null)
    x_witness_work = _continuous_x_witness(x, x_null)
    continuous_witnesses = (x_witness_work*np.diag(my)).tolist()
    physical_mass_norms_squared = (full_mass_energy*np.diag(my)).tolist()
    if (rank != columns*(rows+1)
            or scaled_null_work > 1e-12
            or min(continuous_witnesses) <= 0.0
            or min(physical_mass_norms_squared) <= 0.0
            or np.linalg.eigvalsh(gram)[0] <= 0.0):
        raise AssertionError("analytic Q1 null or physical work check failed")
    shell_record = json.loads(Path(
        "docs/d1_review_support/d1_shell_energy_final_20260928.json"
    ).read_text(encoding="utf-8"))
    if (shell_record["full_supported"]["modes"] != len(x)*len(y)
            or shell_record["full_supported"]["scaled_rank_1e_10"] != rank):
        raise AssertionError("saved shell pressure rank differs")

    model, definition, settings, program = build_case(
        columns, source_rows=rows,
        source_y_profile=saved["source_y_profile"],
        target_right_x_m=saved["target_right_x_m"],
        target_reference_slope=saved["target_reference_slope"],
        target_columns=saved["target_columns"],
        full_width_target=saved["full_width_target"],
        load_profile=saved["load_profile"],
        total_force_n=saved["total_downward_force_n"],
        steps_per_segment=saved["steps_per_segment"],
        four_phase=saved["four_phase"],
    )
    model.apply_boundary_conditions()
    manager = GeneralS3PatchManager(model, definition, settings)
    pose = np.asarray(saved["final_displacements"])
    pressure = np.asarray(saved["contact"]["numerical_pressure_pa"])
    support = np.asarray(saved["contact"]["reference_support_m2"])
    if list(manager.law.pressure_mode_ids) != saved["contact"][
            "source_pressure_node_ids"]:
        raise AssertionError("saved pressure-node identity differs")
    contact = linearize(manager, pose, pressure*support, tangent=False)
    if np.linalg.norm(contact.state.reference_support-support) > 1e-8*np.linalg.norm(support):
        raise AssertionError("saved contact support changed")
    full_work = contact.state.reference_support[:, None]*contact.gap_gradient
    shell_stiffness, _information = assemble_stiffness_matrix(model)
    _reduced, _rhs, transform, _offset, _fixed, _info = (
        build_constraint_transformation(
            shell_stiffness, np.zeros_like(pose), model)
    )
    controlled = tuple(int(model.mesh.dof_manager.get_node_dofs(node)[0])
                       for node in (1, columns+2))
    controlled_reduced = []
    transform = transform.tocsr()
    for dof in controlled:
        row = transform.getrow(dof)
        if row.nnz != 1 or row.data[0] != 1.0:
            raise AssertionError("source control reduction changed")
        controlled_reduced.append(int(row.indices[0]))
    free = np.setdiff1d(np.arange(transform.shape[1]), controlled_reduced)
    physical_transform = transform[:, free]
    shell_reduced_work = np.asarray(full_work @ physical_transform)
    shell_null_work = np.asarray(null_vectors.T @ shell_reduced_work)
    source_nodes = list(map(int, manager.law.source_node_ids))
    source_uz = [int(model.mesh.dof_manager.get_node_dofs(node)[2])
                 for node in source_nodes]
    source_work = np.asarray(full_work[:, source_uz])
    source_mass_relative_error = float(np.linalg.norm(source_work-gram)
                                       /np.linalg.norm(gram))
    shell_null_relative = float(np.linalg.norm(shell_null_work)
                                /(np.linalg.norm(shell_reduced_work)
                                  *np.linalg.norm(null_vectors)))
    result = {
        "status": "development_prescribed_edge_discrete_null",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "runtime_identity": {"python": platform.python_version(),
                             "numpy": np.__version__},
        "pressure_modes": len(x)*len(y),
        "free_source_transverse_coordinates": len(free_x),
        "predicted_discrete_work_rank": rank,
        "saved_full_shell_scaled_rank_1e_10": shell_record[
            "full_supported"]["scaled_rank_1e_10"],
        "exact_x_null_mass_residual": float(np.linalg.norm(
            mx @ x_null-np.eye(len(x))[:, 0])),
        "tensor_null_scaled_work": scaled_null_work,
        "tensor_pressure_gram_minimum_eigenvalue": float(
            np.linalg.eigvalsh(gram)[0]),
        "physical_pressure_mass_norms_squared": physical_mass_norms_squared,
        "continuous_admissible_virtual_work": continuous_witnesses,
        "continuous_x_witness_work": x_witness_work,
        "source_uz_work_relative_tensor_mass_error_at_saved_pose":
            source_mass_relative_error,
        "shell_full_admissible_null_scaled_work_at_saved_pose":
            shell_null_relative,
        "shell_null_residual_norm_by_y_mode": np.linalg.norm(
            shell_null_work, axis=1).tolist(),
        "elapsed_seconds": time.perf_counter()-started,
    }
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "pressure_modes", "predicted_discrete_work_rank",
        "tensor_null_scaled_work",
        "source_uz_work_relative_tensor_mass_error_at_saved_pose",
        "shell_full_admissible_null_scaled_work_at_saved_pose",
        "elapsed_seconds",
    )}, indent=2))


if __name__ == "__main__":
    main()
