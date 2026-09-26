"""Coupled regression for the opt-in refined projected gap certificate."""

from scripts.general_contact_d1_coupled_refinement import build_case

from anysolver import solve_static_nonlinear, validate_general_contact


def test_refined_projected_patch_press_slide_open_recontact_with_tight_gap():
    model, definition, settings, program = build_case(
        2, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
        four_phase=True,
    )
    capability = validate_general_contact(model, definition, settings)
    assert capability.valid, capability.issues
    assert "REFINED_PROJECTED" in capability.profile
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=12,
        emit_restart_checkpoint=True,
    )
    assert result.status == "completed", result.info.get("contact_failure")
    assert len(result.steps) == 4
    assert result.restart_checkpoint is not None
    history = result.info["force_displacement_history"]
    assert [item["contact"]["active_pressure_dofs"] > 0
            for item in history] == [True, True, False, True]
    assert history[1]["target"][0] == 0.05
    for item in history:
        assert item["normal_multiplier_change"] <= settings.pressure_tolerance
        assert item["contact"]["minimum_gap"] >= -definition.interactions[0].gap_tolerance
        assert item["contact"]["pressure_gram_scaled_rank"] == 6
        assert abs(item["reaction_generalized"][1]
                   + item["contact"]["integration_force"][2]) <= 1e-6
