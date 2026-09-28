"""Resolved source director moment work for admitted Q4/S3 Jet2 mortar."""

from scripts.general_contact_d1_eccentric_source_director import run


def test_eccentric_source_director_moment_has_consistent_both_body_tangent():
    result = run()
    assert result["initial_active_pressure_modes"] == 0
    assert result["initial_minimum_gap_m"] > 0.0
    assert result["active_pressure_modes"] == 6
    assert result["pair_force_balance_n"] < 1.0e-6
    assert result["pair_moment_balance_nm"] < 1.0e-6
    for trial in result["trials"]:
        assert trial["smooth"], trial["branch_checks"]
        assert trial["groups"]["source_moment"]["action_scale"] > 1.0e-4
        assert trial["groups"]["target_moment"]["action_scale"] > 1.0e-4
        assert all(group["relative_error"] <= 1.0e-5
                   for group in trial["groups"].values())
