"""Independent current-skin overlap check at the saved 4-Q4/32-S3 pose.

Development evidence only. Reuses the existing independent clipping quadrature;
does not solve equilibrium or certify a spatial reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

import anysolver
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from examples.general_contact_free_target_cycle_dev import (
    _independent_projected_gap_bound,
)
from docs.d1_review_support.d1_two_body_current_skin_quadrature import (
    integrate_current_skin, physical_vertices,
)
from docs.d1_review_support.d1_two_body_reference_oracle import _clip
from docs.d1_review_support.d1_two_body_refined_target_route import build_refined_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-record", type=Path,
                        default=Path(__file__).with_name(
                            "d1_target_grid_4x4_20260929.json"))
    parser.add_argument("--accepted-step", type=int, default=2)
    args = parser.parse_args()
    source_path = args.saved_record
    saved_bytes = source_path.read_bytes()
    saved = json.loads(saved_bytes)
    assert saved["status"] == "completed" and saved["accepted_steps"] == 2
    assert saved["source_q4_faces"] == 4 and saved["target_s3_faces"] == 32
    model, definition, settings, _program, _x, _y = build_refined_case(4, 4, 4)
    if args.accepted_step == 2:
        pose = np.asarray(saved["final_displacements"], dtype=float)
    elif args.accepted_step == 1 and "accepted_displacements" in saved["steps"][0]:
        pose = np.asarray(saved["steps"][0]["accepted_displacements"],
                          dtype=float)
    else:
        raise ValueError("requested accepted pose is not saved")
    assert pose.shape == (model.mesh.dof_manager.total_dofs,)

    independent = integrate_current_skin(
        model, definition, pose, pressure_gram=True,
    )
    support, weighted_gap, xy_area, points, _topology, gram = independent
    manager = GeneralS3PatchManager(model, definition, settings)
    source, target = manager._positions(pose)
    production = manager.law.geometry.evaluate(source, target)
    assert tuple(manager.law.pressure_mode_ids) == tuple(sorted({
        node for eid in definition.surfaces[0].element_ids
        for node in model.mesh.elements[eid].node_ids
    }))
    assert np.all(support > 0.0)
    assert np.array_equal(production.reference_support > 0.0, support > 0.0)
    gap_budget = definition.interactions[0].gap_tolerance
    independent_gap_lower = _independent_projected_gap_bound(
        model, definition, pose, gap_budget,
    )

    face_counts = {}
    pair_areas = []
    for source_id in definition.surfaces[0].element_ids:
        source_element = model.mesh.elements[source_id]
        _reference, source_current = physical_vertices(
            model, source_element, pose, "bottom",
        )
        count = 0
        for target_id in definition.surfaces[1].element_ids:
            target_element = model.mesh.elements[target_id]
            _reference, target_current = physical_vertices(
                model, target_element, pose, "top",
            )
            polygon = _clip(source_current[:, :2], target_current[:, :2])
            if len(polygon) < 3:
                continue
            area = 0.5*abs(float(np.dot(polygon[:, 0],
                                             np.roll(polygon[:, 1], -1))
                                 - np.dot(polygon[:, 1],
                                          np.roll(polygon[:, 0], -1))))
            if area > 1e-12:
                count += 1
                pair_areas.append((int(source_id), int(target_id), area))
        face_counts[str(source_id)] = count

    scaled_support = float(np.linalg.norm(
        support-production.reference_support,
    )/np.linalg.norm(production.reference_support))
    scaled_gram = float(np.linalg.norm(
        gram-production.pressure_gram,
    )/np.linalg.norm(production.pressure_gram))
    normalized_gap_difference = float(np.max(np.abs(
        weighted_gap/support-production.normalized_gap,
    )))
    record = {
        "status": "development_saved_pose_independent_multiface_geometry",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True,
        ).strip(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "accepted_step": args.accepted_step,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_source_sha256": hashlib.sha256(Path(
            "docs/d1_review_support/d1_two_body_current_skin_quadrature.py",
        ).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "source_positive_overlap_target_counts": face_counts,
        "maximum_target_faces_per_source": max(face_counts.values()),
        "positive_overlap_pairs": len(pair_areas),
        "pair_areas_m2": pair_areas,
        "independent_quadrature_points": points,
        "independent_projected_area_m2": xy_area,
        "independent_reference_area_m2": float(np.sum(support)),
        "production_reference_area_m2": production.reference_overlap_area,
        "support_relative_l2": scaled_support,
        "pressure_gram_relative_frobenius": scaled_gram,
        "maximum_normalized_gap_difference_m": normalized_gap_difference,
        "registered_gap_budget_m": gap_budget,
        "independent_projected_gap_lower_m": independent_gap_lower,
        "production_integration_triangles": production.integration_triangles,
    }
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
