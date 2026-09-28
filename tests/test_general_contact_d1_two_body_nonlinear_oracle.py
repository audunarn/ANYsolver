"""Bounded nonlinear Q4/S3 two-body response with independent contact work."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_saved_slide_matches_independent_current_contact_kkt():
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((
        str(root / "src"), str(root), str(root / "docs" / "d1_review_support"),
    ))
    completed = subprocess.run(
        [sys.executable, str(root / "docs" / "d1_review_support"
                                   / "d1_two_body_nonlinear_kkt_compare.py")],
        cwd=root, env=environment, capture_output=True, text=True,
        check=True, timeout=120,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "development_independent_contact_nonlinear_kkt"
    assert result["active_pressure_modes"] == [3, 8]
    assert result["final_scaled_merit"] <= 1e-9
    assert result["minimum_inactive_gap_m"] >= -1e-9
    assert min(row["minimum_active_force_n"] for row in result["trace"]) > 0
    assert result["maximum_displacement_difference_m_or_rad"] <= 1e-9
    derivative = result["gradient_step_sensitivity"]
    assert derivative["directions"] == 30
    assert derivative["resolved_columns_at_norm_1e_minus_4"] >= 10
    assert derivative["maximum_half_vs_nominal_resolved_relative_difference"] <= 1e-5
    assert derivative["maximum_double_vs_nominal_resolved_relative_difference"] <= 1e-5
    assert derivative["maximum_half_vs_nominal_absolute_difference"] <= 1e-8
    assert derivative["maximum_double_vs_nominal_absolute_difference"] <= 1e-8
    for name in (
        "relative_pressure_l2_difference",
        "relative_nodal_force_l2_difference",
        "relative_integrated_force_difference",
        "control_reaction_relative_l2_difference",
    ):
        assert result[name] <= 1e-6, (name, result[name])
