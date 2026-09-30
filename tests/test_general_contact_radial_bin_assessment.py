from copy import deepcopy

import numpy as np

from docs.d1_review_support.d1_radial_bin_assessment import assess_physical_source_bins


def evidence():
    return dict(independent_geometry_work_bins_n=[[.005]*2]*2,
        estimated_quadrature_error_bins_n=[[1e-9]*2]*2,
        conversion_allowance_bins_n=[[1e-9]*2]*2,
        reference_pressure_estimated_error_bins_n=[[1e-12]*2]*2,
        production_comparison=dict(status="measured",
            source_pair_gradient_bins_n=[[.005]*2]*2,
            validated_total_source_vertical_work_n=.02))


def assess(record):
    return assess_physical_source_bins(record, [[.005]*2]*2, .02,
                                      exact_bin_error_n=[[0.]*2]*2)


def test_missing_nonfinite_or_unmeasured_physical_bins_cannot_pass():
    good = evidence()
    assert assess(good)["development_checks_met"]
    records = [dict(), deepcopy(good), deepcopy(good), deepcopy(good)]
    records[1]["production_comparison"]["status"] = "not_checked"
    records[2]["estimated_quadrature_error_bins_n"][0][0] = np.nan
    records[3]["conversion_allowance_bins_n"][0][0] = -1e-10
    assert all(not assess(record)["development_checks_met"] for record in records)


def test_equal_opposite_bin_errors_cannot_hide_behind_total_force():
    record = evidence()
    record["production_comparison"]["source_pair_gradient_bins_n"] = [
        [.0052, .0048], [.005, .005]]
    assert not assess(record)["development_checks_met"]
    record = evidence()
    record["production_comparison"]["validated_total_source_vertical_work_n"] += 1e-6
    assert not assess(record)["development_checks_met"]


def test_uncertainty_can_fail_an_observed_response_below_two_percent():
    record = evidence()
    actual = .005*1.019
    record["production_comparison"]["source_pair_gradient_bins_n"] = [[actual]*2]*2
    record["independent_geometry_work_bins_n"] = [[actual]*2]*2
    record["conversion_allowance_bins_n"] = [[.005*.0015]*2]*2
    record["production_comparison"]["validated_total_source_vertical_work_n"] = actual*4
    result = assess_physical_source_bins(record, [[.005]*2]*2, actual*4,
                                        exact_bin_error_n=[[0.]*2]*2)
    assert result["physical_bin_force_l1_relative_error"] < .02
    assert result["uncertainty_budget_met"]
    assert not result["development_checks_met"]


def test_missing_exact_reference_uncertainty_cannot_pass():
    assert not assess_physical_source_bins(evidence(), [[.005]*2]*2, .02)[
        "development_checks_met"]
    result = assess_physical_source_bins(evidence(), [[.005]*2]*2, .02,
                                        exact_bin_error_n=[[1e-3]*2]*2)
    assert not result["uncertainty_budget_met"]
