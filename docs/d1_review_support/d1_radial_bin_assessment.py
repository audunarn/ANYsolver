"""Prospective finite-fixture physical-bin gates; missing evidence never passes."""
from __future__ import annotations

import numpy as np


def assess_physical_source_bins(evidence, exact_bins_n, saved_source_force_n,
                               *, exact_bin_error_n=None, force_scale_n=.08):
    """Apply the declared 2% response and one-tenth uncertainty budgets."""
    result = dict(scope="guided whole-source-face physical vertical-force bins",
                  development_checks_met=False)
    try:
        comparison = evidence["production_comparison"]
        if comparison["status"] != "measured":
            raise ValueError("production bin comparison is not measured")
        keys = ("independent_geometry_work_bins_n", "estimated_quadrature_error_bins_n",
                "conversion_allowance_bins_n", "reference_pressure_estimated_error_bins_n")
        arrays = [np.asarray(evidence[key], dtype=float) for key in keys]
        exact = np.asarray(exact_bins_n, dtype=float)
        reference_error = np.asarray(exact_bin_error_n, dtype=float)
        physical = np.asarray(comparison["source_pair_gradient_bins_n"], dtype=float)
        total = float(comparison["validated_total_source_vertical_work_n"])
        saved = float(saved_source_force_n)
        if (not np.isfinite(force_scale_n) or force_scale_n <= 0.
                or not np.isfinite((total, saved)).all()
                or any(a.shape != (2, 2) or not np.isfinite(a).all()
                       for a in arrays+[exact, physical, reference_error])
                or np.any(exact <= 0.) or np.any(reference_error < 0.)
                or any(np.any(a < 0.) for a in arrays[1:])):
            raise ValueError("finite complete four-bin evidence and positive scales required")
        independent, quadrature, conversion, pressure_error = arrays
        # The actual work-map difference and measured integration/conversion
        # allowances all enter the finite comparison budget.
        uncertainty = (abs(physical-independent)+quadrature+conversion
                       +pressure_error+reference_error)
        budget = .002*exact
        difference = physical-exact
        l1 = float(np.sum(abs(difference))/np.sum(abs(exact)))
        l2 = float(np.linalg.norm(difference)/np.linalg.norm(exact))
        accounted_l1 = float(np.sum(abs(difference)+uncertainty)/np.sum(abs(exact)))
        accounted_l2 = float(np.linalg.norm(abs(difference)+uncertainty)/np.linalg.norm(exact))
        sum_parity = abs(float(np.sum(physical))-total)/force_scale_n
        saved_parity = abs(total-saved)/force_scale_n
        result.update(physical_bins_n=physical.tolist(), exact_bins_n=exact.tolist(),
            uncertainty_bins_n=uncertainty.tolist(), uncertainty_budget_bins_n=budget.tolist(),
            exact_reference_error_bins_n=reference_error.tolist(),
            physical_bin_force_l1_relative_error=l1, physical_bin_force_l2_relative_error=l2,
            uncertainty_accounted_l1_relative_error=accounted_l1,
            uncertainty_accounted_l2_relative_error=accounted_l2,
            bins_to_reassembled_force_relative_difference=sum_parity,
            reassembled_to_saved_force_relative_difference=saved_parity,
            uncertainty_budget_met=bool(np.all(uncertainty <= budget)),
            development_checks_met=bool(accounted_l1 <= .02 and accounted_l2 <= .02
                and np.all(uncertainty <= budget) and sum_parity <= 1e-6
                and saved_parity <= 1e-6))
    except (KeyError, TypeError, ValueError) as exc:
        result["missing_or_invalid_evidence"] = f"{type(exc).__name__}: {exc}"
    return result
