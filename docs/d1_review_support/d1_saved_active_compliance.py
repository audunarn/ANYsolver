"""Offline active pressure-to-gap response at a saved near-rim pose.

Development discriminator only: a local active Jacobian is not a spatial or
nonlinear pressure-space qualification.
"""

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil
from scipy import linalg, sparse
from scipy.sparse.linalg import splu

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.linearized_pivot import _jet2_integral_gradients
from anysolver.general_contact.pressure_basis import (
    PressureBasis, SELECTED_Q1_KNOTS_VERSION,
)
from anysolver.general_contact.q4_s3_overlap_derivatives import (
    q4_s3_overlap_derivatives,
)
from anysolver.general_contact.s3_patch_augmented import (
    _q4_s3_pair_value_rtol, _q4_s3_pair_values_agree,
)
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--saved", type=Path,
    default=Path(__file__).with_name("d1_saved_16x8_near_rim_field_20260928.json"),
)
parser.add_argument("--structural-energy", action="store_true")
parser.add_argument("--enriched-source-x2", action="store_true")
parser.add_argument("--enriched-source-x4", action="store_true")
parser.add_argument("--output", type=Path)
args = parser.parse_args()
enriched_source = args.enriched_source_x2 or args.enriched_source_x4
if sum((args.structural_energy, args.enriched_source_x2,
        args.enriched_source_x4)) > 1:
    parser.error("select one pressure diagnostic")
if ((args.structural_energy or enriched_source)
        and (args.output is None or args.output.exists())):
    parser.error("selected diagnostic requires a new --output path")
started = time.perf_counter()
path = args.saved.resolve()
saved_bytes = path.read_bytes()
saved = json.loads(saved_bytes)
assert saved["status"] == "completed" and saved["accepted_steps"] == 2
model, definition, settings, program = build_case(
    saved["columns"], source_rows=saved["source_rows"],
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
assert len(program.controls) == 2 and program.waypoints[-1] == (0.0, 0.0)
model.apply_boundary_conditions()
pose = np.asarray(saved["final_displacements"], dtype=float)
certificate = saved["contact"]
pressure = np.asarray(certificate["numerical_pressure_pa"], dtype=float)
support = np.asarray(certificate["reference_support_m2"], dtype=float)
assert np.all(support > 0.0) and np.all(pressure >= 0.0)
manager = GeneralS3PatchManager(model, definition, settings)
assert list(manager.law.pressure_mode_ids) == certificate["source_pressure_node_ids"]
base = linearize(manager, pose, pressure*support, tangent=True)
np.testing.assert_allclose(base.state.reference_support, support,
                           rtol=1e-8, atol=1e-13)
np.testing.assert_allclose(base.state.normalized_gap,
                           certificate["normalized_weighted_gap_m"],
                           rtol=0.0, atol=1e-9)
geometry_seconds = time.perf_counter()-started

if not (args.structural_energy or enriched_source):
    structural_tangent = _assemble_nonlinear_system(
        model, pose, {}, 5, tangent=True, kinematics="von_karman",
        require_full_coordinates=True,
    )[1]
linear_stiffness = assemble_stiffness_matrix(model)[0]
_reduced, _rhs, transform, offset, _fixed, _info = (
    build_constraint_transformation(linear_stiffness, np.zeros_like(pose), model)
)
assert np.linalg.norm(offset) == 0.0
transform = transform.tocsr()
controlled_dofs = tuple(int(model.mesh.dof_manager.get_node_dofs(node)[0])
                        for node in (1, saved["columns"]+2))
controlled_coordinates = []
for dof in controlled_dofs:
    row = transform.getrow(dof)
    assert row.nnz == 1 and row.data[0] == 1.0
    controlled_coordinates.append(int(row.indices[0]))
free_coordinates = np.setdiff1d(np.arange(transform.shape[1]),
                                controlled_coordinates)
physical_transform = transform[:, free_coordinates]
active = np.flatnonzero(pressure > 0.0)
assert len(active) == certificate["active_pressure_dofs"]
if enriched_source:
    # Keep the physical pressure field fixed while enriching only source
    # structural virtual displacements. No coupled fine-mesh solve occurs.
    refinement = 4 if args.enriched_source_x4 else 2
    fine_columns = refinement*saved["columns"]
    fine_model, fine_definition, fine_settings, _program = build_case(
        fine_columns, source_rows=saved["source_rows"],
        source_y_profile=saved["source_y_profile"],
        target_right_x_m=saved["target_right_x_m"],
        target_reference_slope=saved["target_reference_slope"],
        target_columns=saved["target_columns"],
        full_width_target=saved["full_width_target"],
        load_profile=saved["load_profile"],
        total_force_n=saved["total_downward_force_n"],
        steps_per_segment=saved["steps_per_segment"],
        four_phase=saved["four_phase"],
        offline_structural_reference_64=args.enriched_source_x4,
    )
    fine_model.apply_boundary_conditions()
    fine_manager = GeneralS3PatchManager(
        fine_model, fine_definition, fine_settings)
    coarse_stride = saved["columns"]+1
    fine_stride = fine_columns+1
    coarse_source_count = coarse_stride*(saved["source_rows"]+1)
    fine_source_count = fine_stride*(saved["source_rows"]+1)
    if (len(support) != coarse_source_count
            or fine_manager.law.source_node_ids !=
            tuple(range(1, fine_source_count+1))):
        raise AssertionError("source pressure order does not match refined grid")
    fine_pose = np.zeros(fine_model.mesh.dof_manager.total_dofs)
    coarse_dofs = model.mesh.dof_manager
    fine_dofs = fine_model.mesh.dof_manager
    pose_prolongation = sparse.lil_matrix((fine_pose.size, pose.size))
    for row in range(saved["source_rows"]+1):
        for column in range(fine_stride):
            left = column//refinement
            fraction = (column % refinement)/refinement
            first = 1+row*coarse_stride+left
            coarse_indices = coarse_dofs.get_node_dofs(first)
            value = np.asarray(pose[coarse_indices])
            if fraction:
                second = first+1
                second_indices = coarse_dofs.get_node_dofs(second)
                value = (1.0-fraction)*value+fraction*pose[second_indices]
            node = 1+row*fine_stride+column
            fine_indices = fine_dofs.get_node_dofs(node)
            fine_pose[fine_indices] = value
            for component, fine_dof in enumerate(fine_indices):
                pose_prolongation[fine_dof, coarse_indices[component]] = (
                    1.0-fraction)
                if fraction:
                    pose_prolongation[fine_dof, second_indices[component]] = (
                        fraction)
    pose_prolongation = pose_prolongation.tocsr()
    coarse_source, _coarse_target = manager._positions(pose)
    fine_source, fine_target = fine_manager._positions(fine_pose)
    expected_source = []
    for row in range(saved["source_rows"]+1):
        for column in range(fine_stride):
            left = row*coarse_stride+column//refinement
            fraction = (column % refinement)/refinement
            value = (1.0-fraction)*coarse_source[left]
            if fraction:
                value = value+fraction*coarse_source[left+1]
            expected_source.append(value)
    expected_source = np.asarray(expected_source)
    geometry_error = float(np.max(np.linalg.norm(
        fine_source-expected_source, axis=1)))
    matrix = np.zeros((fine_source_count, coarse_source_count))
    for row in range(saved["source_rows"]+1):
        for column in range(fine_stride):
            index = row*fine_stride+column
            coarse_index = row*coarse_stride+column//refinement
            fraction = (column % refinement)/refinement
            if fraction:
                matrix[index, coarse_index:coarse_index+2] = (
                    1.0-fraction, fraction)
            else:
                matrix[index, coarse_index] = 1.0
    anchors = tuple(1+row*fine_stride+refinement*column
                    for row in range(saved["source_rows"]+1)
                    for column in range(coarse_stride))
    basis = PressureBasis(
        SELECTED_Q1_KNOTS_VERSION,
        fine_manager.law.source_node_ids, anchors,
        tuple(tuple(value for value in row) for row in matrix),
    )
    geometry = fine_manager.law.geometry
    fine_state = geometry.evaluate(fine_source, fine_target)
    fine_support, fine_weighted, _fine_gram = basis.transform_integrals(
        fine_state.reference_support, fine_state.reference_weighted_gap,
        fine_state.pressure_gram,
    )
    fine_gap = fine_weighted/fine_support
    support_error = float(np.linalg.norm(fine_support-support)
                          /np.linalg.norm(support))
    gap_error = float(np.max(abs(fine_gap-base.state.normalized_gap)))
    area_error = float(abs(fine_state.reference_overlap_area
                           -base.state.reference_overlap_area)
                       /base.state.reference_overlap_area)
    record = {
        "status": "development_enriched_shell_source_x2",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "saved_runtime_identity": saved["runtime_identity"],
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "coarse_source_cells": [saved["columns"], saved["source_rows"]],
        "fine_source_cells": [fine_columns, saved["source_rows"]],
        "pressure_modes": int(len(support)),
        "settled_active_modes": int(len(active)),
        "source_skin_interpolation_error_m": geometry_error,
        "pressure_support_l2_relative": support_error,
        "normalized_gap_maximum_error_m": gap_error,
        "reference_overlap_area_relative_error": area_error,
    }
    if (geometry_error > 1e-10 or support_error > 1e-8
            or gap_error > 1e-8 or area_error > 1e-8
            or np.any(fine_support <= 0.0)):
        record["status"] = "development_enriched_shell_geometry_mismatch"
    else:
        try:
            weighted_gradient, support_gradient = _jet2_integral_gradients(
                geometry, fine_source, fine_target,
                np.arange(fine_source_count),
                3*(len(fine_source)+len(fine_target)),
                fine_settings.maximum_general_s3_energy_evaluations,
                manager=fine_manager, base=fine_state,
            )
        except ValueError as exc:
            match = re.search(r"\bpair=(\d+)\b", str(exc))
            if match is None:
                raise
            pair_index = int(match.group(1))
            source_face, target_face = divmod(
                pair_index, len(geometry.target_faces))
            source_nodes = geometry.source_face_indices[source_face]
            target_nodes = geometry.target_face_indices[target_face]
            local_source = fine_source[source_nodes]
            local_target = fine_target[target_nodes]
            local = geometry.pair_laws[pair_index].evaluate(
                local_source, local_target)
            tolerances = geometry.q4_source_derivative_tolerances
            derivative = q4_s3_overlap_derivatives(
                geometry.source_faces[source_face].reference_positions,
                local_source, local_target,
                area_tolerance=geometry.q4_source_area_tolerance,
                weighted_gap_tolerance=geometry.q4_source_weighted_gap_tolerance,
                maximum_triangles=geometry.maximum_q4_source_integration_triangles,
                allow_warped_source=True,
                support_gradient_tolerance=tolerances[0],
                support_hessian_tolerance=tolerances[1],
                weighted_gap_gradient_tolerance=tolerances[2],
                weighted_gap_hessian_tolerance=tolerances[3],
            )
            value_rtol = _q4_s3_pair_value_rtol(
                local.overlap_area, derivative.overlap_area,
                derivative.overlap_area_resolution)
            factor = 512.0*np.finfo(float).eps*max(
                1, local.integration_triangles)

            def comparison(name, old, new, normwise):
                scale = max(float(np.max(abs(old))), float(np.max(abs(new))))
                atol = factor*scale
                return {
                    "local": old.tolist(), "derivative": new.tolist(),
                    "maximum_absolute_difference": float(np.max(abs(old-new))),
                    "value_scale": scale, "roundoff_atol": atol,
                    "agrees": _q4_s3_pair_values_agree(
                        old, new, value_rtol=value_rtol,
                        roundoff_atol=atol,
                        local_area=local.overlap_area,
                        derivative_area=derivative.overlap_area,
                        area_resolution=derivative.overlap_area_resolution,
                        normwise=normwise),
                }

            record["status"] = "development_enriched_shell_pair_value_non_success"
            record["pair_guard"] = {
                "error": str(exc), "pair": pair_index,
                "source_face": source_face, "target_face": target_face,
                "local_overlap_area_m2": local.overlap_area,
                "derivative_overlap_area_m2": derivative.overlap_area,
                "area_resolution_m2": derivative.overlap_area_resolution,
                "integration_triangles": local.integration_triangles,
                "value_rtol": value_rtol,
                "support": comparison(
                    "support", local.reference_support,
                    derivative.reference_support, False),
                "weighted_gap": comparison(
                    "weighted_gap", local.reference_weighted_gap,
                    derivative.reference_weighted_gap, True),
            }
            record["elapsed_seconds"] = time.perf_counter()-started
            record["peak_process_working_set_mb"] = (
                psutil.Process().memory_info().peak_wset/1e6)
            args.output.write_text(json.dumps(record, indent=2)+"\n",
                                   encoding="utf-8")
            print(json.dumps({"status": record["status"],
                              "pair_guard": record["pair_guard"]}, indent=2))
            raise SystemExit(2)
        support_gradient, weighted_gradient = basis.transform_derivatives(
            support_gradient, weighted_gradient,
        )
        fine_work = (weighted_gradient
                     -fine_gap[:, None]*support_gradient)
        fine_stiffness = assemble_stiffness_matrix(fine_model)[0]
        _r, _f, fine_transform, fine_offset, _fixed, _info = (
            build_constraint_transformation(
                fine_stiffness, np.zeros(fine_pose.size), fine_model,
            ))
        if np.linalg.norm(fine_offset) != 0.0:
            raise AssertionError("enriched source has unexpected constraint offset")
        fine_transform = fine_transform.tocsr()
        control_nodes = (1, fine_stride+1)
        controlled = []
        for node in control_nodes:
            dof = int(fine_dofs.get_node_dofs(node)[0])
            row = fine_transform.getrow(dof)
            if row.nnz != 1 or row.data[0] != 1.0:
                raise AssertionError("enriched control coordinate is ambiguous")
            controlled.append(int(row.indices[0]))
        free = np.setdiff1d(np.arange(fine_transform.shape[1]), controlled)
        physical_fine = fine_transform[:, free]
        fine_work = np.asarray(fine_work @ fine_manager.map @ physical_fine)
        coarse_work = support[:, None]*np.asarray(
            base.gap_gradient @ physical_transform)
        coarse_energy = np.asarray(
            (physical_transform.T @ linear_stiffness @ physical_transform)
            .toarray())
        fine_energy = np.asarray(
            (physical_fine.T @ fine_stiffness @ physical_fine).toarray())
        # The pressure basis is shared, but a finite-reference ratio is a
        # nested shell test only if coarse admissible motions have the same
        # physical work and comparable energy after prolongation.
        restricted_prolongation = pose_prolongation @ physical_transform
        fine_gram = (physical_fine.T @ physical_fine).toarray()
        gram_error = float(np.linalg.norm(
            fine_gram-np.eye(fine_gram.shape[0]), ord="fro")
                            /max(np.sqrt(fine_gram.shape[0]), 1.0))
        if gram_error > 1e-10:
            raise AssertionError("fine constraint transform is not orthonormal")
        prolongation = (physical_fine.T @ restricted_prolongation).toarray()
        reconstructed = physical_fine @ prolongation
        reconstruction_error = float(np.linalg.norm(
            reconstructed-restricted_prolongation.toarray(), ord="fro")
            /max(np.linalg.norm(restricted_prolongation.toarray(),
                                ord="fro"), 1e-30))
        work_error = float(np.linalg.norm(
            fine_work @ prolongation-coarse_work, ord="fro")
            /max(np.linalg.norm(coarse_work, ord="fro"), 1e-30))
        restricted_energy = prolongation.T @ fine_energy @ prolongation
        energy_error = float(np.linalg.norm(
            restricted_energy-coarse_energy, ord="fro")
            /max(np.linalg.norm(coarse_energy, ord="fro"), 1e-30))
        record.update({
            "constraint_orthonormality_relative": gram_error,
            "structural_prolongation_reconstruction_relative":
                reconstruction_error,
            "prolongated_pressure_work_relative": work_error,
            "prolongated_structural_energy_relative": energy_error,
        })
        if reconstruction_error > 1e-12 or work_error > 1e-8:
            record["status"] = "development_enriched_shell_work_non_nested"
        elif energy_error > 1e-3:
            record["status"] = "development_enriched_shell_energy_non_nested"

        def compliance(work, energy):
            diagonal = np.diag(energy)
            if np.any(diagonal <= 0):
                raise AssertionError("nonpositive structural energy diagonal")
            scaled = energy/np.sqrt(np.outer(diagonal, diagonal))
            minimum = float(np.linalg.eigvalsh((scaled+scaled.T)/2)[0])
            if minimum <= 1e-10:
                raise AssertionError("structural energy metric is not positive")
            factor = splu(sparse.csc_matrix(energy))
            response = factor.solve(work.T)
            result = work @ response
            return 0.5*(result+result.T), minimum, float(
                np.linalg.norm(energy @ response-work.T)
                /max(np.linalg.norm(work.T), 1e-30))

        coarse_c, coarse_min, coarse_residual = compliance(
            coarse_work, coarse_energy)
        fine_c, fine_min, fine_residual = compliance(
            fine_work, fine_energy)
        singular_values = linalg.svdvals(prolongation)
        if singular_values[-1] <= 1e-10*singular_values[0]:
            raise AssertionError("admissible prolongation is rank deficient")
        exact_restricted_work = fine_work @ prolongation
        restricted_c, restricted_min, restricted_residual = compliance(
            exact_restricted_work, restricted_energy)
        metric_bridge_c, _bridge_min, _bridge_residual = compliance(
            coarse_work, restricted_energy)
        bridge_error = float(np.linalg.norm(
            restricted_c-metric_bridge_c, ord="fro")
            /max(np.linalg.norm(restricted_c, ord="fro"), 1e-30))
        fine_diagonal = np.sqrt(np.diag(fine_c))
        enrichment_defect = ((fine_c-restricted_c)
                             /np.outer(fine_diagonal, fine_diagonal))
        enrichment_psd_minimum = float(np.linalg.eigvalsh(
            0.5*(enrichment_defect+enrichment_defect.T))[0])
        if enrichment_psd_minimum < -1e-8:
            record["status"] = "development_enriched_shell_projector_non_success"

        def generalized_range(numerator, denominator):
            diagonal = np.sqrt(np.diag(denominator))
            scale = np.outer(diagonal, diagonal)
            normalized_denominator = denominator/scale
            minimum = float(np.linalg.eigvalsh(
                0.5*(normalized_denominator
                     +normalized_denominator.T))[0])
            if minimum <= 1e-11:
                raise AssertionError("active reference compliance is singular")
            values = linalg.eigvalsh(numerator/scale,
                                     normalized_denominator)
            return [float(values[0]), float(values[-1])]

        record.update({
            "coarse_free_coordinates": int(coarse_energy.shape[0]),
            "fine_free_coordinates": int(fine_energy.shape[0]),
            "coarse_metric_scaled_minimum_eigenvalue": coarse_min,
            "fine_metric_scaled_minimum_eigenvalue": fine_min,
            "coarse_response_relative_residual": coarse_residual,
            "fine_response_relative_residual": fine_residual,
            "common_metric": {
                "prolongation_minimum_singular_ratio": float(
                    singular_values[-1]/singular_values[0]),
                "restricted_energy_scaled_minimum_eigenvalue":
                    restricted_min,
                "restricted_response_relative_residual":
                    restricted_residual,
                "pressure_work_bridge_compliance_relative": bridge_error,
                "fine_minus_restricted_scaled_minimum_eigenvalue":
                    enrichment_psd_minimum,
                "settled_active_enrichment_ratio_range": generalized_range(
                    restricted_c[np.ix_(active, active)],
                    fine_c[np.ix_(active, active)]),
                "settled_active_metric_ratio_range": generalized_range(
                    coarse_c[np.ix_(active, active)],
                    metric_bridge_c[np.ix_(active, active)]),
            },
        })
        for name, rows in (("full_supported", np.arange(len(support))),
                           ("settled_active", active)):
            a = coarse_c[np.ix_(rows, rows)]
            b = fine_c[np.ix_(rows, rows)]
            diagonal = np.sqrt(np.diag(b))
            reference = b/np.outer(diagonal, diagonal)
            minimum = float(np.linalg.eigvalsh(reference)[0])
            if minimum <= 1e-11:
                record["status"] = "development_enriched_shell_reference_singular"
                record[name] = {"reference_scaled_minimum_eigenvalue": minimum}
                break
            eigenvalues, vectors = linalg.eigh(
                a/np.outer(diagonal, diagonal), reference,
                subset_by_index=(0, 0),
            )
            coefficients = vectors[:, 0]/diagonal
            dominant = np.argsort(abs(coefficients))[-5:][::-1]
            record[name] = {
                "modes": int(len(rows)),
                "beta_reference_squared": float(eigenvalues[0]),
                "reference_scaled_minimum_eigenvalue": minimum,
                "weakest_pressure_mode_ij": [
                    [int(rows[k] % coarse_stride),
                     int(rows[k] // coarse_stride)] for k in dominant],
            }
    record["elapsed_seconds"] = time.perf_counter()-started
    record["peak_process_working_set_mb"] = (
        psutil.Process().memory_info().peak_wset/1e6)
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key in ("status", "full_supported", "settled_active",
                                 "pressure_support_l2_relative",
                                 "normalized_gap_maximum_error_m",
                                 "elapsed_seconds")}, indent=2))
    raise SystemExit(0 if record["status"] ==
                     "development_enriched_shell_source_x2" else 2)

if args.structural_energy:
    # The physical pressure coefficient acts through S_i * D(gbar_i),
    # whereas the old active-response probe used D(gbar_i) with K_contact.
    energy = (physical_transform.T @ linear_stiffness
              @ physical_transform).toarray()
    symmetry = float(np.linalg.norm(energy-energy.T)
                     /max(np.linalg.norm(energy), 1e-30))
    diagonal = np.diag(energy)
    metric = None
    if np.all(diagonal > 0):
        scale = np.sqrt(diagonal)
        metric = np.linalg.eigvalsh(
            (energy+energy.T)/2/np.outer(scale, scale))
    record = {
        "status": "development_shell_structural_energy_detection",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "saved_runtime_identity": saved["runtime_identity"],
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "structural_metric_symmetry_relative": symmetry,
        "structural_metric_scaled_minimum_eigenvalue": (
            None if metric is None else float(metric[0])),
        "free_structural_coordinates": int(physical_transform.shape[1]),
        "supported_pressure_modes": int(len(support)),
        "settled_active_pressure_modes": int(len(active)),
        "geometry_seconds": geometry_seconds,
    }
    if (symmetry > 1e-10 or metric is None or metric[0] <= 1e-10):
        record["status"] = "development_shell_energy_metric_unavailable"
    else:
        force_work = support[:, None]*np.asarray(
            base.gap_gradient @ physical_transform)
        factor = splu(sparse.csc_matrix(energy))
        source_stride = saved["columns"]+1
        if len(support) != source_stride*(saved["source_rows"]+1):
            raise AssertionError("saved source grid no longer matches pressure modes")
        boundary_excluded = np.flatnonzero(
            np.arange(len(support)) % source_stride != 0)
        for name, rows in (("full_supported", np.arange(len(support))),
                           ("source_clamp_column_excluded", boundary_excluded),
                           ("settled_active", active)):
            work = force_work[rows]
            response = factor.solve(work.T)
            compliance = work @ response
            compliance = (compliance+compliance.T)/2
            row_scale = np.sqrt(np.diag(compliance))
            if np.any(row_scale <= 0):
                raise AssertionError("shell pressure work has a zero row")
            normalized = compliance/np.outer(row_scale, row_scale)
            spectrum, vectors = np.linalg.eigh(normalized)
            smallest = vectors[:, 0]/row_scale
            dominant = np.argsort(abs(smallest))[-5:][::-1]
            record[name] = {
                "scaled_smallest_eigenvalue": float(spectrum[0]),
                "scaled_largest_eigenvalue": float(spectrum[-1]),
                "scaled_rank_1e_10": int(np.count_nonzero(
                    spectrum > 1e-10*spectrum[-1])),
                "modes": int(len(rows)),
                "weakest_pressure_node_ids": [
                    int(manager.law.pressure_mode_ids[rows[k]])
                    for k in dominant],
                "weakest_pressure_mode_ij": [
                    [int(rows[k] % source_stride),
                     int(rows[k] // source_stride)] for k in dominant],
                "relative_linear_solve_residual": float(
                    np.linalg.norm(energy @ response-work.T)
                    /max(np.linalg.norm(work.T), 1e-30)),
            }
    record["elapsed_seconds"] = time.perf_counter()-started
    record["peak_process_working_set_mb"] = (
        psutil.Process().memory_info().peak_wset/1e6)
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key in ("status", "full_supported",
                                 "source_clamp_column_excluded", "settled_active",
                                 "structural_metric_scaled_minimum_eigenvalue",
                                 "elapsed_seconds")}, indent=2))
    raise SystemExit(0 if record["status"] ==
                     "development_shell_structural_energy_detection" else 2)

full_tangent = sparse.csr_matrix(structural_tangent)+base.tangent
reduced_tangent = (physical_transform.T @ full_tangent
                   @ physical_transform).tocsc()
gradient = np.asarray(base.gap_gradient[active] @ physical_transform)
factor = splu(reduced_tangent)
response = factor.solve(gradient.T)
solve_residual = reduced_tangent @ response-gradient.T
relative_solve_residual = float(np.linalg.norm(solve_residual)
                                /max(np.linalg.norm(gradient.T), 1e-30))
compliance = gradient @ response
symmetry_defect = float(np.linalg.norm(compliance-compliance.T)
                        /max(np.linalg.norm(compliance), 1e-30))
singular = np.linalg.svd(compliance, compute_uv=False)
symmetric_eigen = np.linalg.eigvalsh((compliance+compliance.T)/2)
scaled = np.sqrt(support[active])[:, None]*compliance*np.sqrt(support[active])[None, :]
scaled_singular = np.linalg.svd(scaled, compute_uv=False)
diagonal = np.diag(compliance)
assert np.all(diagonal > 0.0)
unit_diagonal = (compliance/np.sqrt(diagonal)[:, None]
                 /np.sqrt(diagonal)[None, :])
unit_diagonal_eigen = np.linalg.eigvalsh(
    (unit_diagonal+unit_diagonal.T)/2)
record = {
    "status": "development_saved_active_pressure_compliance",
    "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                              text=True).strip(),
    "saved_source_file": str(path),
    "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "saved_runtime_identity": saved["runtime_identity"],
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "anysolver_module": str(Path(anysolver.__file__).resolve()),
    "active_modes": len(active),
    "supported_modes": len(support),
    "controlled_dofs": controlled_dofs,
    "physical_free_coordinates": int(physical_transform.shape[1]),
    "reduced_tangent_nnz": int(reduced_tangent.nnz),
    "relative_linear_solve_residual": relative_solve_residual,
    "compliance_symmetry_defect": symmetry_defect,
    "minimum_symmetric_eigenvalue_m_per_n": float(symmetric_eigen[0]),
    "maximum_symmetric_eigenvalue_m_per_n": float(symmetric_eigen[-1]),
    "minimum_singular_value_m_per_n": float(singular[-1]),
    "maximum_singular_value_m_per_n": float(singular[0]),
    "unscaled_singular_ratio": float(singular[-1]/singular[0]),
    "support_scaled_singular_ratio": float(scaled_singular[-1]/scaled_singular[0]),
    "minimum_active_support_m2": float(np.min(support[active])),
    "maximum_active_support_m2": float(np.max(support[active])),
    "active_support_ratio": float(np.min(support[active])
                                  /np.max(support[active])),
    "unit_diagonal_minimum_eigenvalue": float(unit_diagonal_eigen[0]),
    "unit_diagonal_maximum_eigenvalue": float(unit_diagonal_eigen[-1]),
    "unit_diagonal_eigen_ratio": float(unit_diagonal_eigen[0]
                                       /unit_diagonal_eigen[-1]),
    "geometry_seconds": geometry_seconds,
    "elapsed_seconds": time.perf_counter()-started,
    "peak_process_working_set_mb": (
        psutil.Process().memory_info().peak_wset / 1.0e6
    ),
}
print(json.dumps(record, indent=2))
