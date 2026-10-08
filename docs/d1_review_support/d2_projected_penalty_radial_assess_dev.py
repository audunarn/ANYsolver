"""Recover saved finite-law radial work/bins; never repeat the coupled solve."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import numpy as np

from docs.d1_review_support.d2_projected_penalty_shell_dev import fixture, file_identity
from docs.d1_review_support.d1_radial_spatial_assessment import radial_sample_reference_errors
from scripts import general_contact_d1_interior_press_dev as retained


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--stage", choices=("wrench", "bins", "summary"), required=True)
    parser.add_argument("--saved", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bins", type=Path)
    parser.add_argument("--wrench", type=Path)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    saved = json.loads(args.saved.read_text(encoding="utf-8"))
    if saved.get("normal_law") != "projected_penalty" or saved.get("status") != "completed":
        raise ValueError("completed finite-law source required")
    regularization = float(saved["normal_regularization_pa_per_m"])
    if not np.isfinite(regularization) or regularization <= 0.:
        raise ValueError("saved regularization must be finite and positive")
    for name, sha in saved["changed_kernel_sha256"].items():
        if file_identity(Path(retained.anysolver.__file__).parent/"general_contact"/name)["sha256"] != sha:
            raise ValueError(f"production contact identity changed: {name}")
    original_factory = retained.build_radial_guided_case

    def factory(**kwargs):
        model, definition, _, program, reference, inputs = original_factory(**kwargs)
        definition = replace(definition, interactions=tuple(replace(i,
            normal_law="projected_penalty", normal_stiffness=regularization) for i in definition.interactions))
        return model, definition, fixture(regularization)[2], program, reference, inputs

    retained.build_radial_guided_case = factory
    try:
        if args.stage == "wrench": retained.radial_wrench_check(args.output, args.saved)
        elif args.stage == "bins": retained.radial_source_bin_check(args.output, args.saved)
        else:
            if not args.bins or not args.wrench: parser.error("summary requires bins and wrench")
            bins = json.loads(args.bins.read_text(encoding="utf-8"))
            wrench = json.loads(args.wrench.read_text(encoding="utf-8"))
            source_sha = file_identity(args.saved)["sha256"]
            if any(r["input_sha256"] != source_sha for r in (bins, wrench)):
                raise ValueError("recovered evidence differs from source identity")
            checks = {"completed_two_steps": saved.get("accepted_steps") == 2,
                "finite_law_profile": saved["history"][-1]["contact"]["profile"] ==
                    "Q4_S3_PATCH_REFINED_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0",
                "force_response": saved["force_relative_error"] <= .02,
                "independent_physical_gap": np.isfinite(saved["independent_gap_lower_m"]) and saved["independent_gap_lower_m"] >= -5e-5,
                "physical_bins": bins.get("assessment", {}).get("development_checks_met") is True,
                "both_body_reaction_and_work": wrench.get("development_checks_met") is True}
            sample_metrics = {}
            for body in ("source", "target"):
                rows = saved[body+"_displacement_samples"]
                errors = radial_sample_reference_errors(saved, rows, body)
                accounted = []
                for row in rows:
                    error = errors[(row["x_m"], row["y_m"])]
                    if abs(row["exact_uz_m"]) <= error:
                        raise ValueError("reference uncertainty does not resolve nonzero response")
                    accounted.append(float((abs(row["actual_uz_m"]-row["exact_uz_m"])+error)
                        /(abs(row["exact_uz_m"])-error)))
                sample_metrics[body+"_accounted_relative_errors"] = accounted
                checks[body+"_displacement_response"] = len(rows) == 3 and max(accounted) <= .02
            record = {"accepted": False, "released": False, "checks": checks,
                "development_checks_met": all(checks.values()), "metrics": sample_metrics,
                "source_record": file_identity(args.saved), "bins_record": file_identity(args.bins),
                "wrench_record": file_identity(args.wrench),
                "force_relative_error": saved["force_relative_error"],
                "independent_gap_lower_m": saved["independent_gap_lower_m"],
                "limits": "hard-contact continuum reference: penalty, spatial and trace errors combined; no exact finite-law KKT or boundary acceptance"}
            args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    finally:
        retained.build_radial_guided_case = original_factory
    record = json.loads(args.output.read_text(encoding="utf-8"))
    record["adapter"] = file_identity(__file__)
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"stage": args.stage, "development_checks_met": record.get("development_checks_met", record.get("assessment", {}).get("development_checks_met"))}), flush=True)


if __name__ == "__main__":
    main()
