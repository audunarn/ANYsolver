"""Data-only assessment of the declared saved radial development fixture."""
from __future__ import annotations

import numpy as np

from docs.d1_review_support.d1_radial_bin_assessment import assess_physical_source_bins


def assess_saved_radial_spatial(saved, bins, wrench, linear, *, input_sha256):
    """Keep measured predicates separate from independent acceptance."""
    result = dict(status="development_saved_radial_spatial_assessment",
                  development_checks_met=False,
                  gates={"evidence_completeness": False}, metrics={})
    gates, metrics = result["gates"], result["metrics"]

    def below(name, value, limit):
        values = np.asarray(value, dtype=float)
        gates[name] = bool(values.size and np.isfinite(values).all()
                           and np.all(values >= 0.) and np.all(values <= limit))
        metrics[name] = dict(value=values.tolist(), limit=limit)

    def samples(rows):
        actual = {(float(r["x_m"]), float(r["y_m"])): float(r["actual_uz_m"])
                  for r in rows}
        exact = {(float(r["x_m"]), float(r["y_m"])): float(r["exact_uz_m"])
                 for r in rows}
        if set(actual) != {(.6, .6), (.6, .85), (.6, 1.)} or len(rows) != 3:
            raise ValueError("complete registered displacement samples required")
        if not np.isfinite(list(actual.values())+list(exact.values())).all():
            raise ValueError("displacement samples must be finite")
        return actual, exact

    def penetration(value):
        raw = float(value)
        if not np.isfinite(raw):
            raise ValueError("finite physical gap evidence required")
        return max(0., -raw)

    try:
        if (not isinstance(input_sha256, str) or len(input_sha256) != 64
                or any(r["input_sha256"] != input_sha256 for r in (bins, wrench))):
            raise ValueError("bin/wrench evidence must bind the same saved pose record")
        for key in ("target_cells", "target_y0_m", "target_right_x_m",
                    "source_guided_shear_n_m", "target_guided_shear_n_m",
                    "gap_m", "exact_force_n"):
            baseline = np.asarray(saved[key], dtype=float)
            if not np.isfinite(baseline).all():
                raise ValueError("finite matching fixture identities required")
            for record in (bins, wrench, linear):
                if not np.allclose(np.asarray(record[key], dtype=float), baseline,
                                   rtol=1e-12, atol=0.):
                    raise ValueError(f"fixture identity differs: {key}")
        if (saved["status"] != "completed" or saved["accepted_steps"] != 2
                or [r["step_index"] for r in saved["history"]] != [1, 2]
                or [r["step"] for r in wrench["rows"]] != [1, 2]):
            raise ValueError("completed matching two-step evidence required")
        gates["fixture_and_completion"] = True
        force_ref, moment_ref, exact_force = .08, .08, float(saved["exact_force_n"])
        if exact_force <= 0.:
            raise ValueError("positive exact final contact force required")
        contact = saved["history"][-1]["contact"]
        force = np.asarray(contact["integration_force"], dtype=float)
        moment = (np.asarray(contact["integration_moment"], dtype=float)
                  - np.cross((.6, .6, 0.), force))
        if force.shape != (3,) or moment.shape != (3,) or not np.isfinite(np.r_[force, moment]).all():
            raise ValueError("finite complete physical wrench required")
        below("physical_force_relative_error", abs(force[2]-exact_force)/exact_force, .02)
        below("physical_moment_relative_error", np.linalg.norm(moment)/exact_force, .02)
        position = None
        if abs(force[2]) > 8e-8:
            # Equivalent wrench point at z=0, not a pressure centroid.
            position = np.array((.6-moment[1]/force[2], .6+moment[0]/force[2]))
            below("moment_equivalent_position_error_over_radius",
                  np.linalg.norm(position-(.6, .6))/.35, .02)
            metrics["moment_equivalent_resultant"] = dict(xy_m=position.tolist(),
                plane_z_m=0., residual_vertical_couple_nm=float(moment[2]
                    +(moment[0]*force[0]+moment[1]*force[1])/force[2]))
        else:
            gates["moment_equivalent_position_error_over_radius"] = False
            metrics["moment_equivalent_resultant"] = None
        source, source_exact = samples(saved["source_displacement_samples"])
        target, target_exact = samples(saved["target_displacement_samples"])
        below("source_displacement_relative_errors", [abs(source[p]-source_exact[p])
              /abs(source_exact[p]) for p in source], .02)
        metrics["target_displacement_relative_errors_reported"] = [
            abs(target[p]-target_exact[p])/abs(target_exact[p]) for p in target]
        below("independent_gap_penetration_m", penetration(saved["independent_gap_lower_m"]), 50e-6)
        for row, wr in zip(saved["history"], wrench["rows"], strict=True):
            label = f"step{row['step_index']}"
            origin = np.asarray(wr["origin_m"], dtype=float)
            if (origin.shape != (3,) or not np.array_equal(origin, (.6, .6, 0.))
                    or wr["force_scale_n"] != force_ref
                    or wr["moment_scale_nm"] != moment_ref):
                raise ValueError("registered wrench origin and force/moment scales required")
            below(label+"_equilibrium_relative_force", row["residual_norm"]/force_ref, 1e-6)
            below(label+"_complementarity_relative_force", row["complementarity_relative_force"], 1e-8)
            below(label+"_physical_gap_penetration_m", penetration(row["contact"]["minimum_gap"]), 50e-6)
            net = np.asarray(wr["physical_contact_wrench"], dtype=float)
            if net.shape != (6,):
                raise ValueError("complete net contact wrench required")
            below(label+"_action_reaction_force", np.linalg.norm(net[:3])/force_ref, 1e-6)
            below(label+"_action_reaction_moment", np.linalg.norm(net[3:])/moment_ref, 1e-6)
            if set(wr["bodies"]) != {"source", "target"}:
                raise ValueError("both body reaction records required")
            below(label+"_reaction_and_work", [wr[k] for k in (
                "constraint_reconstruction_relative_force", "balance_relative_force",
                "balance_relative_moment", "contact_conversion_max_scaled",
                "structural_internal_max_scaled")]+[body[k] for body in wr["bodies"].values()
                for k in ("balance_relative_force", "balance_relative_moment",
                          "contact_conversion_max_scaled", "structural_internal_max_scaled")], 1e-6)
            ids = row["contact"]["source_pressure_node_ids"]
            z = (np.asarray(row["contact"]["numerical_pressure_pa"])
                 *np.asarray(row["contact"]["reference_support_m2"]))
            if ids != list(range(1, 170)) or z.shape != (169,) or not np.isfinite(z).all() or np.any(z < 0.):
                raise ValueError("complete nonnegative radial pressure modes required")
            grid = z.reshape(13, 13)
            below(label+"_source_rim_force_n", np.max(abs(np.r_[grid[0], grid[-1], grid[:, 0], grid[:, -1]])), 1e-10)
            below(label+"_reference_coverage_area_error_m2", abs(row["contact"]["reference_overlap_area"]-1.), 1e-10)
        exact_bins = bins["exact_disk_observables"]["bins"]
        bin_gate = assess_physical_source_bins(bins["evidence"],
            [[r["force_n"] for r in row] for row in exact_bins], force[2],
            exact_bin_error_n=[[r["estimated_absolute_error"][0] for r in row] for row in exact_bins])
        result["physical_bin_assessment"] = bin_gate
        gates["physical_bins"] = bool(bin_gate["development_checks_met"])
        q1 = saved["numerical_reference_pressure_observables"]["total"]
        q1_moment = np.asarray(q1["moment_nm"], dtype=float)
        if q1_moment.shape != (3,):
            raise ValueError("complete three-component reference-pressure moment required")
        below("reference_pressure_force_conversion_over_force_ref", abs(q1["force_n"]-force[2])/force_ref, .002)
        below("reference_pressure_moment_conversion_over_moment_ref",
              np.linalg.norm(q1_moment-moment)/moment_ref, .002)
        gates["independent_linear_kkt"] = linear["development_checks_met"] is True
        oracle = linear["final_observables"]
        solution_accounted = linear.get("solution_uncertainty_assessed") is True
        # Missing reference accuracy remains an explicit failed prerequisite;
        # provisional observed differences can still guide the next decision.
        force_uncertainty = oracle["force_solution_uncertainty_n"] if solution_accounted else 0.
        below("observed_final_force_model_discrepancy",
              (abs(force[2]-oracle["force_n"])+force_uncertainty)/exact_force, .002)
        oracle_bins = np.asarray(oracle["bins_n"], dtype=float)
        oracle_error = np.asarray(oracle["bin_estimated_error_n"], dtype=float)
        physical_bins = np.asarray(bin_gate["physical_bins_n"])
        bin_uncertainty = np.asarray(bin_gate["uncertainty_bins_n"])
        solution_bin_error = np.asarray(oracle["bin_solution_uncertainty_n"]) if solution_accounted else np.zeros((2, 2))
        exact_values = np.asarray(bin_gate["exact_bins_n"])
        if (oracle_bins.shape != (2, 2) or oracle_error.shape != (2, 2)
                or solution_bin_error.shape != (2, 2) or np.any(oracle_error < 0.)
                or np.any(solution_bin_error < 0.) or not np.isfinite(solution_bin_error).all()
                or not np.isfinite(force_uncertainty) or force_uncertainty < 0.):
            raise ValueError("complete oracle bin uncertainty required")
        below("observed_final_bin_model_discrepancy", (abs(physical_bins-oracle_bins)
              +bin_uncertainty+oracle_error+solution_bin_error)/exact_values, .002)
        for body, values, exact in (("source", source, source_exact), ("target", target, target_exact)):
            points = {(r["x_m"], r["y_m"]): r["uz_m"] for r in oracle[body+"_samples"]}
            if set(points) != set(values):
                raise ValueError("matching oracle displacement samples required")
            point_errors = {(r["x_m"], r["y_m"]): r["solution_uncertainty_m"]
                            for r in oracle[body+"_samples"]} if solution_accounted else dict.fromkeys(points, 0.)
            if not np.isfinite(list(point_errors.values())).all() or min(point_errors.values()) < 0.:
                raise ValueError("nonnegative finite oracle displacement uncertainty required")
            below("observed_final_"+body+"_model_discrepancy", [
                (abs(values[p]-points[p])+point_errors[p])/abs(exact[p]) for p in values], .002)
        oracle_moment = np.asarray(oracle["moment_about_origin_nm"])
        moment_error = np.asarray(oracle["moment_estimated_error_nm"])
        moment_solution_error = np.asarray(oracle["moment_solution_uncertainty_nm"]) if solution_accounted else np.zeros(3)
        if (oracle_moment.shape != (3,) or moment_error.shape != (3,)
                or moment_solution_error.shape != (3,) or np.any(moment_error < 0.)
                or np.any(moment_solution_error < 0.) or not np.isfinite(moment_solution_error).all()):
            raise ValueError("complete oracle moment uncertainty required")
        below("observed_final_moment_model_discrepancy",
              (np.linalg.norm(moment-oracle_moment)+np.linalg.norm(moment_error+moment_solution_error))/exact_force, .002)
        oracle_position = np.asarray(oracle["moment_equivalent_resultant_xy_m"])
        position_error = float(oracle["resultant_solution_uncertainty_m"]) if solution_accounted else 0.
        if oracle_position.shape != (2,) or not np.isfinite(position_error) or position_error < 0.:
            raise ValueError("complete finite oracle resultant uncertainty required")
        if position is None:
            gates["observed_final_resultant_model_discrepancy"] = False
        else:
            below("observed_final_resultant_model_discrepancy",
                  (np.linalg.norm(position-oracle_position)+position_error)/.35, .002)
        # A KKT residual is not, by itself, an error bound on these observables.
        # Keep this explicit prerequisite until the reference uncertainty is assessed.
        gates["oracle_solution_uncertainty_assessed"] = solution_accounted
        gates["evidence_completeness"] = True
        result["development_checks_met"] = bool(gates and all(gates.values()))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        result["missing_or_invalid_evidence"] = f"{type(exc).__name__}: {exc}"
    result["remaining_gates"] = [name for name, passed in gates.items() if not passed]
    return result
