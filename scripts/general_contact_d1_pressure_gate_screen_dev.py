"""Screen the proposed interior pressure-work bound at a saved D1 pose.

This development runner evaluates the full signed interior Q1 space. It does
not freeze an acceptance candidate or establish nonlinear inf-sup stability.
"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np
from scipy import linalg

from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_interior_press_dev import build_interior_press
from scripts.general_contact_d1_interior_work_spectrum_dev import _reference_mass


def screen(saved_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    expected = {
        "status": "completed", "accepted_steps": 2,
        "source_support": "perimeter", "load_shape": "physical_bump",
        "four_phase": False, "slide_body": "target",
        "force_n": 0.04, "reference_slope": 1.0e-4,
        "target_young_multiplier": 5.0,
        "target_reference_full_left_clamp": True,
        "q4_gap_certificate": "overlap_local_dev",
    }
    if any(saved.get(key) != value for key, value in expected.items()):
        raise ValueError("saved pose is outside the deformable contrast profile")
    columns, rows = saved["source_columns"], saved["source_rows"]
    target_columns, target_rows = saved["target_columns"], saved["target_rows"]
    if (columns != rows or columns not in (4, 8, 12)
            or target_columns != target_rows or target_columns != 4
            or saved.get("source_y_profile") is not None):
        raise ValueError("saved pose is outside the pressure family")
    model, definition, settings, program = build_interior_press(
        force_n=0.04, reference_slope=1.0e-4,
        source_support="perimeter", source_columns=columns, source_rows=rows,
        target_columns=target_columns, target_rows=target_rows,
        target_young_multiplier=5.0,
        target_y0_m=saved.get("target_y0_m", -0.1),
        target_reference_full_left_clamp=True,
        load_shape="physical_bump", slide_body="target",
    )
    settings = replace(settings, q4_source_gap_certificate="overlap_local_dev")
    displacement = np.asarray(saved["displacements"], dtype=float)
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    zeros = np.zeros(model.mesh.dof_manager.total_dofs)
    _, _, transformation, offset, _, _ = build_constraint_transformation(
        stiffness, zeros, model,
    )
    if displacement.shape != zeros.shape or np.linalg.norm(offset) > 1e-12:
        raise ValueError("saved pose or structural constraints changed")
    manager = GeneralS3PatchManager(model, definition, settings)
    manager.restrict_tangent_to_reduced_variations(transformation)
    source_ids = manager.law.source_node_ids
    interior_ids = tuple(1+row*(columns+1)+column
                         for row in range(1, rows)
                         for column in range(1, columns))
    if tuple(saved["interior_pressure_node_ids"]) != interior_ids:
        raise ValueError("saved interior pressure identity changed")
    selected = np.array([source_ids.index(node) for node in interior_ids])
    contact = saved["history"][-1]["contact"]
    if tuple(contact["source_pressure_node_ids"]) != tuple(source_ids):
        raise ValueError("saved pressure order differs from the contact model")
    nodal_forces = (np.asarray(contact["numerical_pressure_pa"], dtype=float)
                    * np.asarray(contact["reference_support_m2"], dtype=float))
    state = linearize(manager, displacement, nodal_forces, tangent=False)
    if state.state.active_pressure_dofs != contact["active_pressure_dofs"]:
        raise ValueError("saved and rebuilt active pressure counts differ")
    np.testing.assert_allclose(
        state.state.reference_support,
        np.asarray(contact["reference_support_m2"], dtype=float),
        rtol=1e-9, atol=1e-12,
    )
    support = np.asarray(state.state.reference_support)[selected]
    if np.any(support <= 0.0):
        raise ValueError("interior pressure support is nonpositive")
    mass = _reference_mass(manager)[np.ix_(selected, selected)]
    mass_values, mass_vectors = linalg.eigh(mass)
    if mass_values[0] <= 0.0:
        raise ValueError("interior Q1 mass is singular")
    inverse_mass_root = ((mass_vectors / np.sqrt(mass_values))
                         @ mass_vectors.T)

    face = model.mesh.elements[definition.surfaces[0].element_ids[0]]
    points = np.asarray([(model.mesh.nodes[node].x,
                          model.mesh.nodes[node].y,
                          model.mesh.nodes[node].z)
                         for node in face.node_ids])
    normal = np.cross(points[1]-points[0], points[3]-points[0])
    normal /= np.linalg.norm(normal)
    if abs(normal[1]) > 1e-12 or abs(normal[0]+1e-4*normal[2]) > 1e-12:
        raise ValueError("source physical reference normal changed")
    constrained = transformation.tocsr()
    motions = []
    for node in interior_ids:
        columns_for_node = []
        for component in (0, 2):
            row = constrained[model.mesh.dof_manager.get_node_dofs(node)[component]]
            if row.nnz != 1 or abs(row.data[0]-1.0) > 1e-12:
                raise ValueError("source normal motion is constrained")
            columns_for_node.append(int(row.indices[0]))
        if columns_for_node[0] == columns_for_node[1]:
            raise ValueError("source normal coordinates are linked")
        motions.append(normal[0]*constrained[:, columns_for_node[0]].toarray().ravel()
                       + normal[2]*constrained[:, columns_for_node[1]].toarray().ravel())
    q = np.column_stack(motions)
    controls = np.zeros((len(program.controls), len(zeros)))
    for row, control in enumerate(program.controls):
        for node, component, weight in control.terms:
            controls[row, model.mesh.dof_manager.get_node_dofs(node)[
                {"ux": 0, "uy": 1, "uz": 2}[component]]] += weight
    control_error = float(np.max(np.abs(controls @ q), initial=0.0))
    if control_error > 1e-12:
        raise ValueError("source normal motion violates a path control")

    b = support[:, None]*np.asarray(state.gap_gradient @ q)[selected]
    k = np.asarray(q.T @ stiffness @ q)
    k = 0.5*(k+k.T)
    linalg.cholesky(k, lower=True)
    a = inverse_mass_root @ b @ inverse_mass_root
    singular_values = linalg.svdvals(a)
    energy = inverse_mass_root @ k @ inverse_mass_root
    maximum_energy = float(linalg.eigvalsh(
        energy, subset_by_index=(len(selected)-1, len(selected)-1))[0])
    if face.thickness != 0.05 or face.material_name != "elastic":
        raise ValueError("source section differs from registered fixture")
    rigidity = 1.0e5*face.thickness**3/(12*(1-0.3**2))
    hmin = min(1.0/columns, 1.0/rows)
    eta = float(singular_values[-1])
    kappa = maximum_energy*hmin**4/rigidity
    record = {
        "status": "exploratory_saved_pose_pressure_screen",
        "saved_pose": str(saved_path),
        "source_cells": [columns, rows],
        "target_cells": [target_columns, target_rows],
        "target_y0_m": saved.get("target_y0_m", -0.1),
        "source_reference_normal": normal.tolist(),
        "signed_interior_modes": len(selected),
        "active_modes": state.state.active_pressure_dofs,
        "reference_support_min_m2": float(np.min(support)),
        "reference_support_max_m2": float(np.max(support)),
        "mass_minimum_eigenvalue_m2": float(mass_values[0]),
        "path_control_error": control_error,
        "eta": eta,
        "kappa": float(kappa),
        "gamma_constructive": float(eta**2/kappa),
        "provisional_eta_level": 0.9,
        "provisional_kappa_level": 2110.0,
        "provisional_levels_met": eta >= 0.9 and kappa <= 2110.0,
        "scope_note": "Reference-energy saved-pose screen only; no nonlinear norm equivalence or acceptance claim.",
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: pressure_gate_screen SAVED_POSE OUTPUT")
    screen(Path(sys.argv[1]), Path(sys.argv[2]))
