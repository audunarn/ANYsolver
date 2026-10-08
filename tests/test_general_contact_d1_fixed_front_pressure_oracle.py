"""Hand-computed one-cell check for the independent affine-front oracle."""

import json

import pytest

from scripts.general_contact_d1_fixed_front_pressure_oracle import analyze


def test_fixed_front_one_cell_has_known_nodal_pressure_and_field_error(tmp_path):
    # On [0,1], the left Q1 hat has mean x=1/3 and the right hat 2/3.
    # With gap=x-1/2 and unit penalty, the nodal pressures are 1/6 and 0.
    report = {
        "profile": "fixed_affine_partial_pressure_central_q4_s3_dev",
        "target_x_range_m": [0.0, 1.0],
        "target_y_range_m": [0.0, 1.0],
        "normal_stiffness_pa_per_m": 1.0,
        "gap_slope": 1.0,
        "rows": [{
            "divisions": 1,
            "rows": 1,
            "source_pressure_node_ids": [1, 2, 3, 4],
            "numerical_pressure_pa": [1/6, 0.0, 1/6, 0.0],
            "reference_support_m2": [0.25]*4,
            "supported_pressure_modes": 4,
            "reaction_z_n": 1/12,
        }],
    }
    path = tmp_path / "fixed_pose.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    row = analyze(path)["rows"][0]
    assert row["exact_supported_modes"] == 4
    assert row["max_absolute_support_error_m2"] == pytest.approx(0, abs=1e-15)
    assert row["max_absolute_nodal_pressure_error_pa"] == pytest.approx(
        0, abs=1e-15,
    )
    # Squared field error=7/432, squared continuum norm=1/24.
    assert row["relative_continuous_pressure_l2_error"] == pytest.approx(
        (7/18)**0.5, abs=1e-14,
    )
    assert row["analytic_integrated_force_n"] == pytest.approx(1/8)
