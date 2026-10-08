"""Bounded same-pose parity and timing for the value-only overlap path.

The legacy path is exactly shape_values_and_gradient(...)[0]. This probe
changes only that dispatch during the timed call and restores it afterward.
It is a development comparison, not contact qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

import anysolver
from anysolver.general_contact.overlap import ProjectedOverlap
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from docs.d1_review_support.d1_two_body_16x16_linearization_preflight import (
    interpolate_target,
)
from docs.d1_review_support.d1_two_body_refined_target_route import (
    build_refined_case,
)


def _legacy_shape_values(self, face, point):
    return self.shape_values_and_gradient(face, point)[0]


def _legacy_prepared_shape_values(self, face):
    return lambda point: _legacy_shape_values(self, face, point)


def _relative_error(first, second):
    a = np.asarray(first, dtype=float)
    b = np.asarray(second, dtype=float)
    return float(np.max(np.abs(a-b), initial=0.0) /
                 max(float(np.max(np.abs(a), initial=0.0)),
                     float(np.max(np.abs(b), initial=0.0)), 1.0e-30))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    saved_bytes = args.saved_record.read_bytes()
    saved = json.loads(saved_bytes)
    assert saved["status"] == "completed" and saved["accepted_steps"] == 2
    assert saved["source_q4_faces"] == 4 and saved["target_s3_faces"] == 128
    coarse, _definition, _settings, _path, coarse_x, coarse_y = (
        build_refined_case(4, 8, 8)
    )
    model, definition, settings, _path, fine_x, fine_y = (
        build_refined_case(4, 16, 16)
    )
    model.apply_boundary_conditions()
    pose = interpolate_target(
        coarse, np.asarray(saved["final_displacements"]),
        coarse_x, coarse_y, model, fine_x, fine_y,
    )
    saved_step = saved["steps"][-1]
    nodal_forces = (np.asarray(saved_step["numerical_pressure_pa"])
                    * np.asarray(saved_step["reference_support_m2"]))
    manager = GeneralS3PatchManager(model, definition, settings)
    optimized = ProjectedOverlap.shape_values
    optimized_prepared = ProjectedOverlap.prepared_shape_values
    observations = []
    results = {}
    try:
        for profile in ("legacy", "value_only", "value_only", "legacy"):
            ProjectedOverlap.shape_values = (
                _legacy_shape_values if profile == "legacy" else optimized
            )
            ProjectedOverlap.prepared_shape_values = (
                _legacy_prepared_shape_values if profile == "legacy"
                else optimized_prepared
            )
            started = time.perf_counter()
            result = linearize(manager, pose, nodal_forces, tangent=True)
            observations.append({"profile": profile,
                                 "seconds": time.perf_counter()-started,
                                 "evaluations": result.evaluations,
                                 "integration_triangles":
                                     result.state.integration_triangles,
                                 "overlapping_pairs":
                                     result.state.overlapping_pairs})
            results[profile] = result
    finally:
        ProjectedOverlap.shape_values = optimized
        ProjectedOverlap.prepared_shape_values = optimized_prepared
    old = results["legacy"]
    new = results["value_only"]
    comparisons = {
        name: _relative_error(getattr(old.state, name),
                              getattr(new.state, name))
        for name in ("reference_support", "reference_weighted_gap",
                     "normalized_gap", "pressure_gram")
    }
    comparisons.update({
        "force": _relative_error(old.force, new.force),
        "gap_gradient": _relative_error(old.gap_gradient, new.gap_gradient),
        "tangent": _relative_error(old.tangent.toarray(),
                                   new.tangent.toarray()),
    })
    if (old.state.overlap_signature != new.state.overlap_signature
            or old.state.integration_triangles != new.state.integration_triangles
            or old.state.overlapping_pairs != new.state.overlapping_pairs
            or old.evaluations != new.evaluations
            or max(comparisons.values()) > 1.0e-13):
        raise AssertionError(f"value-only overlap parity failed: {comparisons}")
    legacy_times = [row["seconds"] for row in observations
                    if row["profile"] == "legacy"]
    new_times = [row["seconds"] for row in observations
                 if row["profile"] == "value_only"]
    record = {
        "status": "development_value_only_shape_parity",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "observations": observations,
        "relative_errors": comparisons,
        "legacy_median_seconds": float(np.median(legacy_times)),
        "value_only_median_seconds": float(np.median(new_times)),
        "local_time_ratio": float(np.median(legacy_times)/np.median(new_times)),
    }
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "status", "relative_errors", "legacy_median_seconds",
        "value_only_median_seconds", "local_time_ratio",
    )}, indent=2))


if __name__ == "__main__":
    main()
