"""Development cross-check of production float and Jet2 paths at a saved wedge."""

import argparse
import json
from pathlib import Path

import numpy as np

from anysolver.general_contact.q4_s3_overlap_derivatives import q4_s3_overlap_derivatives
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from scripts.general_contact_d1_coupled_refinement import build_case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pose", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--slide-offset", type=float, default=-3.0e-8)
    parser.add_argument("--difference-step", type=float, default=3.0e-9)
    args = parser.parse_args()
    saved = json.loads(args.pose.read_text(encoding="utf-8"))
    model, definition, settings, _ = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    geometry = owner.law.geometry
    source = np.asarray(saved["source"], dtype=float)
    source[:, 0] += args.slide_offset
    target = np.asarray(saved["target"], dtype=float)
    total = geometry.evaluate(source, target)
    support_error = np.zeros_like(total.reference_support)
    gap_error = np.zeros_like(total.reference_weighted_gap)
    pair_rows = []
    for pair_index, law in enumerate(geometry.pair_laws):
        source_face = pair_index // len(geometry.target_faces)
        target_face = pair_index % len(geometry.target_faces)
        source_ids = geometry.source_face_indices[source_face]
        target_ids = geometry.target_face_indices[target_face]
        local_source = source[source_ids]
        local_target = target[target_ids]
        value = law.evaluate(local_source, local_target)
        if value.reference_overlap_area <= 0.0:
            continue
        derivative = q4_s3_overlap_derivatives(
            geometry.source_faces[source_face].reference_positions,
            local_source, local_target,
            area_tolerance=geometry.q4_source_area_tolerance,
            weighted_gap_tolerance=geometry.q4_source_weighted_gap_tolerance,
            maximum_triangles=geometry.maximum_q4_source_integration_triangles,
            allow_warped_source=True,
            **dict(zip(("support_gradient_tolerance",
                        "support_hessian_tolerance",
                        "weighted_gap_gradient_tolerance",
                        "weighted_gap_hessian_tolerance"),
                       geometry.q4_source_derivative_tolerances or (None,)*4)),
        )
        ds = np.abs(value.reference_support-derivative.reference_support)
        dw = np.abs(value.reference_weighted_gap-derivative.reference_weighted_gap)
        support_error[source_ids] += ds
        gap_error[source_ids] += dw
        if pair_index != 2:
            continue
        local_coordinate_count = 3*(len(source_ids)+len(target_ids))
        directions = {}
        for name, axes in (("source_slide", (0,)), ("source_normal", (2,))):
            direction = np.zeros(local_coordinate_count)
            for index in range(len(source_ids)):
                for axis in axes:
                    direction[3*index+axis] = 1.0
            step = args.difference_step

            def float_values(scale):
                trial = np.concatenate((local_source, local_target)).reshape(-1)
                trial += scale*direction
                current = law.evaluate(
                    trial[:3*len(source_ids)].reshape(-1, 3),
                    trial[3*len(source_ids):].reshape(-1, 3),
                )
                return current.reference_support, current.reference_weighted_gap

            plus = float_values(step)
            minus = float_values(-step)
            row = {}
            for label, reference, gradient, hessian, positive, negative in (
                ("support", value.reference_support,
                 derivative.support_gradient, derivative.support_hessian,
                 plus[0], minus[0]),
                ("weighted_gap", value.reference_weighted_gap,
                 derivative.weighted_gap_gradient,
                 derivative.weighted_gap_hessian,
                 plus[1], minus[1]),
            ):
                first_float = (positive-negative)/(2*step)
                first_jet2 = gradient @ direction
                second_float = (positive-2*reference+negative)/(step*step)
                second_jet2 = np.einsum("i,kij,j->k", direction,
                                        hessian, direction)
                row[label] = {
                    "float_first": first_float.tolist(),
                    "jet2_first": first_jet2.tolist(),
                    "float_second": second_float.tolist(),
                    "jet2_second": second_jet2.tolist(),
                    "first_absolute_error": float(np.max(np.abs(first_float-first_jet2))),
                    "second_absolute_error": float(np.max(np.abs(second_float-second_jet2))),
                }
            directions[name] = row
        pair_rows.append({
            "pair": pair_index,
            "overlap_area_m2": value.overlap_area,
            "absolute_support_error_m2": ds.tolist(),
            "absolute_weighted_gap_error_m3": dw.tolist(),
            "directions": directions,
        })
    record = {
        "pose": str(args.pose), "slide_offset_m": args.slide_offset,
        "difference_step_m": args.difference_step,
        "total_support_m2": total.reference_support.tolist(),
        "total_weighted_gap_m3": total.reference_weighted_gap.tolist(),
        "sum_absolute_pair_support_error_m2": support_error.tolist(),
        "sum_absolute_pair_weighted_gap_error_m3": gap_error.tolist(),
        "pair_rows": pair_rows,
    }
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("max_relative_node_support_error", float(np.max(
        support_error/np.maximum(total.reference_support, 1.0e-20))))
    print("max_relative_node_weighted_gap_error", float(np.max(
        gap_error/np.maximum(np.abs(total.reference_weighted_gap), 1.0e-20))))
    print("pair2", pair_rows)


if __name__ == "__main__":
    main()
