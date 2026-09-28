"""Fixed-mesh E4-PL stiffness nesting discriminator, not qualification."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy import linalg, sparse

from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--saved", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("output already exists")
started = time.perf_counter()
saved_bytes = args.saved.read_bytes()
saved = json.loads(saved_bytes)
if saved["status"] != "completed" or saved["columns"] != 16:
    raise ValueError("expected the saved completed 16-column fixture")


def model_at(columns):
    model, _definition, _settings, _program = build_case(
        columns, source_rows=saved["source_rows"],
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
    stiffness = assemble_stiffness_matrix(model)[0]
    _k, _f, transform, offset, _fixed, _info = (
        build_constraint_transformation(
            stiffness, np.zeros(stiffness.shape[0]), model))
    if np.linalg.norm(offset) != 0.0:
        raise AssertionError("unexpected constraint offset")
    transform = transform.tocsr()
    stride = columns+1
    controlled = []
    for node in (1, stride+1):
        dof = int(model.mesh.dof_manager.get_node_dofs(node)[0])
        row = transform.getrow(dof)
        if row.nnz != 1 or row.data[0] != 1.0:
            raise AssertionError("ambiguous program control")
        controlled.append(int(row.indices[0]))
    free = np.setdiff1d(np.arange(transform.shape[1]), controlled)
    return model, stiffness, transform[:, free]


coarse, coarse_stiffness, coarse_physical = model_at(16)
fine, fine_stiffness, fine_physical = model_at(32)
coarse_dofs = coarse.mesh.dof_manager
fine_dofs = fine.mesh.dof_manager
coarse_stride, fine_stride = 17, 33
prolongation = sparse.lil_matrix(
    (fine_dofs.total_dofs, coarse_dofs.total_dofs))
for row in range(saved["source_rows"]+1):
    for column in range(fine_stride):
        left = column//2
        first = 1+row*coarse_stride+left
        fine_node = 1+row*fine_stride+column
        for local, fine_dof in enumerate(fine_dofs.get_node_dofs(fine_node)):
            first_dof = coarse_dofs.get_node_dofs(first)[local]
            if column % 2:
                second_dof = coarse_dofs.get_node_dofs(first+1)[local]
                prolongation[fine_dof, first_dof] = 0.5
                prolongation[fine_dof, second_dof] = 0.5
            else:
                prolongation[fine_dof, first_dof] = 1.0
prolongation = prolongation.tocsr()
fine_on_coarse = prolongation @ coarse_physical
fine_reduced = fine_physical.T @ fine_on_coarse
reconstructed = fine_physical @ fine_reduced
reconstruction_error = np.linalg.norm(
    (fine_on_coarse-reconstructed).toarray(), ord="fro")/np.linalg.norm(
        fine_on_coarse.toarray(), ord="fro")
if reconstruction_error > 1e-12:
    raise AssertionError("coarse admissible motions do not prolong")


def reduced_q4_components(model, physical):
    n = model.mesh.dof_manager.total_dofs
    rows = []
    columns = []
    values = {name: [] for name in ("core", "pl", "hourglass")}
    count = 0
    for element in model.mesh.elements.values():
        if len(element.node_ids) != 4:
            continue
        if getattr(element, "formulation_id", None) is None:
            raise AssertionError("source Q4 has no formulation identity")
        components = element.compute_stiffness_components(
            model.mesh, model.get_material(element.material_name))
        dofs = np.concatenate([
            model.mesh.dof_manager.get_node_dofs(node)
            for node in element.node_ids])
        rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
        rows.extend(rr.ravel().tolist())
        columns.extend(cc.ravel().tolist())
        for name in values:
            values[name].extend(np.asarray(components[name]).ravel().tolist())
        count += 1
    reduced = {}
    for name, data in values.items():
        matrix = sparse.coo_matrix((data, (rows, columns)),
                                   shape=(n, n)).tocsr()
        reduced[name] = np.asarray(
            (physical.T @ matrix @ physical).toarray())
    return reduced, count


coarse_parts, coarse_count = reduced_q4_components(coarse, coarse_physical)
fine_parts, fine_count = reduced_q4_components(fine, fine_on_coarse)
coarse_total = np.asarray((coarse_physical.T @ coarse_stiffness
                           @ coarse_physical).toarray())
fine_total = np.asarray((fine_on_coarse.T @ fine_stiffness
                         @ fine_on_coarse).toarray())
reference_norm = np.linalg.norm(coarse_total, ord="fro")
coarse_sum = sum(coarse_parts.values())
fine_sum = sum(fine_parts.values())
coarse_closure = float(np.linalg.norm(coarse_total-coarse_sum, ord="fro")
                       /reference_norm)
fine_closure = float(np.linalg.norm(fine_total-fine_sum, ord="fro")
                     /reference_norm)
if coarse_closure > 1e-10 or fine_closure > 1e-10:
    raise AssertionError("Q4 component sum differs from assembled stiffness")
delta = fine_total-coarse_total
eigenvalues = linalg.eigvalsh(fine_total, coarse_total)
result = {
    "status": "development_q4_stiffness_component_discriminator",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "saved_pose_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "coarse_q4_elements": coarse_count,
    "fine_q4_elements": fine_count,
    "reconstruction_relative": float(reconstruction_error),
    "coarse_component_closure_relative": coarse_closure,
    "fine_component_closure_relative": fine_closure,
    "total_restricted_energy_difference_relative": float(
        np.linalg.norm(delta, ord="fro")/reference_norm),
    "restricted_energy_ratio_minimum": float(eigenvalues[0]),
    "restricted_energy_ratio_maximum": float(eigenvalues[-1]),
    "components": {
        name: {
            "coarse_norm_over_total": float(
                np.linalg.norm(coarse_parts[name], ord="fro")/reference_norm),
            "difference_over_total": float(
                np.linalg.norm(fine_parts[name]-coarse_parts[name],
                               ord="fro")/reference_norm),
        } for name in coarse_parts
    },
    "elapsed_seconds": time.perf_counter()-started,
}
args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result, indent=2))
