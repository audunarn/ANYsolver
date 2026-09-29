"""Screen the full interior Q1 pressure work at an accepted D1 press pose.

This is a finite-mesh development diagnostic, not an inf-sup certificate.
The production gap gradient is compared with a separately clipped,
frozen-footprint vertical-work oracle from the retained reference programme.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import linalg

from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from docs.d1_review_support.d1_two_body_reference_oracle import independent_gap_work
from scripts.general_contact_d1_interior_press_dev import build_interior_press


_Q1_MASS = np.array(((4, 2, 1, 2), (2, 4, 2, 1),
                     (1, 2, 4, 2), (2, 1, 2, 4)), dtype=float)/36.0
_DOF = {"ux": 0, "uy": 1, "uz": 2}


def _reference_mass(manager):
    """Exact Q1 pressure mass on the planar reference Q4 faces."""
    count = len(manager.law.source_node_ids)
    mass = np.zeros((count, count))
    for local_ids in manager.law.source_face_indices:
        points = manager.reference[0][local_ids]
        v1 = points[1]-points[0]
        v2 = points[3]-points[0]
        area = float(np.linalg.norm(np.cross(v1, v2)))
        plane_error = abs(float(np.dot(points[2]-points[0],
                                        np.cross(v1, v2))))/area
        if area <= 0.0 or plane_error > 1.0e-10:
            raise ValueError("pressure mass requires positive planar Q4 faces")
        mass[np.ix_(local_ids, local_ids)] += area*_Q1_MASS
    return mass


def evaluate(path: Path):
    saved = json.loads(path.read_text(encoding="utf-8"))
    expected = {"status": "completed", "accepted_steps": 2,
                "source_support": "perimeter", "source_rows": 4,
                "load_shape": "interior_distributed", "four_phase": False,
                "slide_body": "target", "force_n": 0.04,
                "reference_slope": 1.0e-4}
    if any(saved.get(key) != value for key, value in expected.items()):
        raise ValueError(f"incompatible accepted press pose: {path}")
    model, definition, settings, program = build_interior_press(
        source_support="perimeter", source_rows=4,
        source_columns=saved["source_columns"],
        target_columns=saved["target_s3_faces"]//2,
        load_shape="interior_distributed", force_n=0.04,
        reference_slope=1.0e-4, slide_body="target",
    )
    displacement = np.asarray(saved["displacements"], dtype=float)
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    zeros = np.zeros(model.mesh.dof_manager.total_dofs)
    _, _, transform, offset, _, _ = build_constraint_transformation(
        stiffness, zeros, model)
    if displacement.shape != zeros.shape or np.linalg.norm(offset) > 1.0e-12:
        raise ValueError("saved press pose or structural constraints changed")
    manager = GeneralS3PatchManager(model, definition, settings)
    manager.restrict_tangent_to_reduced_variations(transform)
    state = linearize(manager, displacement,
                      np.zeros(len(manager.law.source_node_ids)), tangent=False)
    controls = np.zeros((len(program.controls), len(zeros)))
    for index, control in enumerate(program.controls):
        for node, name, weight in control.terms:
            controls[index, model.mesh.dof_manager.get_node_dofs(node)[
                _DOF[name]]] += weight
    reduced_controls = np.asarray(controls @ transform)
    null = linalg.null_space(reduced_controls)
    variations = np.asarray(transform @ null)
    reduced_stiffness = np.asarray(variations.T @ stiffness @ variations)
    symmetry_error = float(np.linalg.norm(
        reduced_stiffness-reduced_stiffness.T)
        / max(np.linalg.norm(reduced_stiffness), 1.0))
    if symmetry_error > 1.0e-9:
        raise ValueError("reference structural stiffness is nonsymmetric")
    reduced_stiffness = 0.5*(reduced_stiffness+reduced_stiffness.T)
    stiffness_min = float(linalg.eigvalsh(reduced_stiffness,
                                         subset_by_index=(0, 0))[0])
    if stiffness_min <= 0.0:
        raise ValueError("constrained structural reference has a mechanism")

    source_ids = manager.law.source_node_ids
    selected = np.array([source_ids.index(node)
                         for node in saved["interior_pressure_node_ids"]],
                        dtype=int)
    supports = state.state.reference_support[selected]
    if np.any(supports <= 0.0):
        raise ValueError("interior pressure mode lacks support")
    mass = _reference_mass(manager)[np.ix_(selected, selected)]
    work = (supports[:, None]
            * np.asarray(state.gap_gradient @ variations)[selected])
    response = linalg.solve(reduced_stiffness, work.T, assume_a="pos")
    dual = 0.5*(work @ response + response.T @ work.T)
    values, vectors = linalg.eigh(dual, mass)

    # This oracle is intentionally frozen to reference XY. Physical skin
    # directors shift current Q4 rows, outside its admitted horizontal-row
    # construction. Compare operator trends, never call this moving-work parity.
    oracle_ids, oracle_support, oracle_work, oracle_area = independent_gap_work(
        model, definition, 0.0)
    if tuple(source_ids) != oracle_ids:
        raise ValueError("independent pressure node order changed")
    independent_work = np.asarray(oracle_work @ variations)[selected]
    independent_response = linalg.solve(reduced_stiffness,
                                        independent_work.T, assume_a="pos")
    independent_dual = 0.5*(
        independent_work @ independent_response
        + independent_response.T @ independent_work.T)
    independent_values = linalg.eigh(independent_dual, mass,
                                     eigvals_only=True)
    active_ids = [node for node, pressure in zip(
        saved["history"][-1]["contact"]["source_pressure_node_ids"],
        saved["history"][-1]["contact"]["numerical_pressure_pa"])
        if pressure > 0.0]
    return {
        "input": str(path),
        "source_q4_faces": saved["source_q4_faces"],
        "target_s3_faces": saved["target_s3_faces"],
        "active_pressure_node_ids": active_ids,
        "signed_interior_mode_ids": list(saved["interior_pressure_node_ids"]),
        "constrained_structural_coordinates": len(null.T),
        "structural_stiffness_minimum": stiffness_min,
        "structural_symmetry_error": symmetry_error,
        "reference_mass_minimum": float(np.min(linalg.eigvalsh(mass))),
        "production_reference_support_m2": supports.tolist(),
        "independent_frozen_support_m2": oracle_support[selected].tolist(),
        "independent_frozen_overlap_area_m2": oracle_area,
        "production_work_singular_values_squared": values.tolist(),
        "independent_vertical_work_singular_values_squared": (
            independent_values.tolist()),
        "smallest_signed_mode_mass_normalized": vectors[:, 0].tolist(),
    }


def main(inputs: list[Path], output: Path):
    if output.exists():
        raise FileExistsError(output)
    cases = [evaluate(path) for path in inputs]
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({"cases": [{
        "source_q4_faces": case["source_q4_faces"],
        "interior_modes": len(case["signed_interior_mode_ids"]),
        "minimum_work": case["production_work_singular_values_squared"][0],
        "oracle_minimum_work": (
            case["independent_vertical_work_singular_values_squared"][0]),
    } for case in cases]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    main(args.inputs, args.output)
