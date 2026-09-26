"""Bounded many-mode pressure proposal through the ordinary static path."""

from dataclasses import replace

import numpy as np

from anysolver import (
    BoundaryCondition, ContactPathControl, ContactPathProgram,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from test_general_contact_q4_s3_refined_patch import _two_q4_two_s3


def _case():
    model, definition, settings = _two_q4_two_s3()
    for node in (7, 8, 9, 10):
        model.mesh.get_node(node).x -= 0.5
    definition = replace(definition, interactions=(replace(
        definition.interactions[0], gap_tolerance=0.005,
    ),))
    settings = replace(
        settings, pressure_tolerance=0.002,
        maximum_augmentations=7,
        augmentation_acceleration="supported_schur_dev",
        augmentation_schur_maximum_modes=8,
        augmentation_schur_maximum_pressure_pa=100.0,
        augmentation_schur_maximum_step_pa=50.0,
        augmentation_schur_difference_step_m=2.0e-6,
    )
    model.add_boundary_condition(BoundaryCondition(
        "target_fixed", (7, 8, 9, 10),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_guide", (1, 2, 3, 4, 5, 6),
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(1, "uz")),
        waypoints=((0.0, 0.0), (0.0, -0.01505)),
        steps_per_segment=1,
    )
    return model, definition, settings, program


def test_supported_schur_settings_are_explicit_and_profile_bounded():
    model, definition, settings, _ = _case()
    assert validate_general_contact(model, definition, settings).valid
    wrong = replace(settings, augmentation_schur_maximum_modes=2)
    assert validate_general_contact(model, definition, wrong).valid
    original = replace(settings, augmentation_acceleration="none",
                       augmentation_schur_maximum_modes=None,
                       augmentation_schur_maximum_pressure_pa=None,
                       augmentation_schur_maximum_step_pa=None,
                       augmentation_schur_difference_step_m=None)
    assert validate_general_contact(model, definition, original).valid
    contract = GeneralS3PatchManager(model, definition, settings).restart_contract()
    changed = GeneralS3PatchManager(
        model, definition,
        replace(settings, augmentation_schur_maximum_step_pa=25.0),
    ).restart_contract()
    assert contract != changed
    assert contract["settings"]["augmentation_schur_maximum_modes"] == 8


def test_projection_branch_declines_schur_and_preserves_static_failure():
    model, definition, settings, program = _case()
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=12,
        emit_restart_checkpoint=True,
    )
    assert result.status == "diverged"
    assert result.failure_reason == "maximum_augmentations_reached"
    failure = result.info["contact_failure"]
    trace = failure["augmentation_trace"]
    assert len(trace) == settings.maximum_augmentations
    assert trace[1]["schur_proposed"] is False
    assert trace[1]["schur_ineligible"] == "projection_branch_or_nonfinite_response"
    assert trace[1]["pressure_gram_scaled_rank"] == 4
    assert failure["schur_attempts"] == 1
    assert failure["schur_applied"] == failure["schur_rejected"] == 0
    assert trace[-1]["pressure_change"] > settings.pressure_tolerance
    assert result.steps == []
    assert result.restart_checkpoint is None
    np.testing.assert_array_equal(result.displacements, 0.0)
