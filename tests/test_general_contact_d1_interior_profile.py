"""Admission checks for the opt-in planar Q4/S3 interior slice."""

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from anysolver import BoundaryCondition, solve_static_nonlinear
from anysolver.assembly import build_constraint_transformation
from anysolver.control import SolveCancelled
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact import semismooth_path
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_interior_press_dev import build_interior_press
from scripts.general_contact_d1_target_displacement_dev import (
    build_case as build_target_displacement_case,
)
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def _free_map(model):
    model.apply_boundary_conditions()
    stiffness, _info = assemble_stiffness_matrix(model)
    zeros = np.zeros(model.mesh.dof_manager.total_dofs)
    return build_constraint_transformation(
        stiffness, zeros, model,
    )[2]


def test_target_internal_s3_seam_is_covered_and_physical_rim_is_topological():
    model, definition, settings, _program = build_interior_press(
        source_support="perimeter", source_rows=4,
        load_shape="interior_distributed", target_columns=2,
    )
    manager = GeneralS3PatchManager(model, definition, settings)
    assert manager.d1_physical_rim_node_ids == frozenset(
        (*range(1, 6), 6, 10, 11, 15, 16, 20, *range(21, 26))
    )
    assert manager.require_d1_coverage(*manager._positions(
        np.zeros(model.mesh.dof_manager.total_dofs),
    )) is None


def test_partial_target_boundary_cut_fails_before_solve():
    model, definition, settings, _program = build_case(
        4, source_rows=2, target_right_x_m=1.3,
        full_width_target=False,
    )
    settings = replace(
        settings, augmentation_acceleration="none",
        augmentation_schur_maximum_modes=None,
        augmentation_schur_maximum_pressure_pa=None,
        augmentation_schur_maximum_step_pa=None,
        augmentation_schur_difference_step_m=None,
        augmentation_schur_maximum_attempts=1,
        d1_interior_profile=True,
        d1_interior_coverage_tolerance_m2=1.0e-10,
        d1_interior_boundary_force_tolerance_n=1.0e-10,
    )
    with pytest.raises(ValueError, match="partial target coverage"):
        GeneralS3PatchManager(model, definition, settings)


def test_active_rim_pressure_rejects_but_interior_pressure_can_pass():
    model, definition, settings, _program = build_interior_press(
        source_support="perimeter", source_rows=4,
        load_shape="interior_distributed",
    )
    manager = GeneralS3PatchManager(model, definition, settings)
    transform = _free_map(model)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    _force, _tangent, certificate = manager.evaluate(displacement,
                                                       tangent=False)
    ids = certificate.source_pressure_node_ids
    support = np.asarray(certificate.reference_support_m2)

    def with_force(node):
        pressure = np.zeros(len(ids))
        index = ids.index(node)
        pressure[index] = 0.01 / support[index]
        return replace(certificate, numerical_pressure_pa=tuple(pressure))

    assert "physical source rim node 1" in manager.d1_interior_admission_issue(
        with_force(1), displacement, transform,
    )
    assert manager.d1_interior_admission_issue(
        with_force(13), displacement, transform,
    ) is None


def test_prescribed_normal_is_checked_through_physical_work_map():
    model, definition, settings, _program = build_interior_press(
        source_support="perimeter", source_rows=4,
        load_shape="interior_distributed", reference_slope=0.0,
    )
    model.add_boundary_condition(BoundaryCondition(
        "center_normal_fixed", (13,), {"uz": 0.0},
    ))
    manager = GeneralS3PatchManager(model, definition, settings)
    transform = _free_map(model)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    _force, _tangent, certificate = manager.evaluate(displacement,
                                                       tangent=False)
    pressure = np.zeros(len(certificate.source_pressure_node_ids))
    index = certificate.source_pressure_node_ids.index(13)
    pressure[index] = 0.01 / certificate.reference_support_m2[index]
    with_center_pressure = replace(
        certificate, numerical_pressure_pa=tuple(pressure),
    )
    assert "prescribed-normal source node 13" in (
        manager.d1_interior_admission_issue(
            with_center_pressure, displacement, transform,
        )
    )


def test_guarded_active_press_restarts_and_binds_profile_settings():
    def case():
        return build_interior_press(
            source_support="perimeter", source_rows=4,
            load_shape="interior_distributed", force_n=0.04,
        )

    model, definition, settings, program = case()
    full = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    assert full.status == "completed"
    assert len(full.steps) == 2

    model, definition, settings, program = case()
    half = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        max_load_factor=0.5, emit_restart_checkpoint=True,
    )
    assert half.status == "completed"
    assert len(half.steps) == 1
    assert half.restart_checkpoint is not None

    with pytest.raises(ValueError, match="incompatible"):
        model, definition, settings, program = case()
        solve_static_nonlinear(
            model, contact=definition, contact_settings=replace(
                settings, d1_interior_boundary_force_tolerance_n=2.0e-10,
            ), contact_path_program=program, max_iterations=18,
            restart_checkpoint=half.to_restart_checkpoint(),
        )

    model, definition, settings, program = case()
    resumed = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        restart_checkpoint=half.to_restart_checkpoint(),
    )
    assert resumed.status == "completed"
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=0.0, atol=1.0e-10)
    np.testing.assert_allclose(
        resumed.info["general_contact"]["integration_force"],
        full.info["general_contact"]["integration_force"],
        rtol=0.0, atol=1.0e-10,
    )


def _guarded_left_edge_press_case():
    return build_interior_press(
        source_support="perimeter", source_rows=4,
        load_shape="interior_distributed", force_n=0.04,
        reference_slope=1.0e-4, slide_body="target",
    )


def test_guarded_left_edge_press_cancel_after_step_keeps_model_reusable():

    class CancelBeforeSecondStep:
        def raise_if_cancelled(self, stage=""):
            if stage == "contact_path.step:2":
                raise SolveCancelled("left-edge development interruption",
                                     stage=stage)

    model, definition, settings, program = _guarded_left_edge_press_case()
    with pytest.raises(SolveCancelled,
                       match="left-edge development interruption"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18,
            cancellation_token=CancelBeforeSecondStep(),
        )
    rerun = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    fresh_model, fresh_definition, fresh_settings, fresh_program = (
        _guarded_left_edge_press_case())
    fresh = solve_static_nonlinear(
        fresh_model, contact=fresh_definition, contact_settings=fresh_settings,
        contact_path_program=fresh_program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    assert rerun.status == fresh.status == "completed"
    np.testing.assert_allclose(rerun.displacements, fresh.displacements,
                               rtol=0.0, atol=1.0e-10)
    np.testing.assert_allclose(
        rerun.info["general_contact"]["integration_force"],
        fresh.info["general_contact"]["integration_force"],
        rtol=0.0, atol=1.0e-10,
    )
    assert rerun.to_restart_checkpoint() == fresh.to_restart_checkpoint()


def test_guarded_left_edge_contact_exception_restores_model(monkeypatch):
    entered_second_step = [False]
    raised = [False]

    class MarkSecondStep:
        def raise_if_cancelled(self, stage=""):
            if stage == "contact_path.step:2":
                entered_second_step[0] = True

    original = semismooth_path.linearize

    def raise_after_contact(*args, **kwargs):
        work = original(*args, **kwargs)
        if entered_second_step[0] and not raised[0]:
            raised[0] = True
            raise RuntimeError("injected left-edge candidate failure")
        return work

    monkeypatch.setattr(semismooth_path, "linearize", raise_after_contact)
    model, definition, settings, program = _guarded_left_edge_press_case()
    with pytest.raises(RuntimeError,
                       match="injected left-edge candidate failure"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18,
            cancellation_token=MarkSecondStep(),
        )
    assert raised[0]
    monkeypatch.setattr(semismooth_path, "linearize", original)

    rerun = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    fresh_model, fresh_definition, fresh_settings, fresh_program = (
        _guarded_left_edge_press_case())
    fresh = solve_static_nonlinear(
        fresh_model, contact=fresh_definition, contact_settings=fresh_settings,
        contact_path_program=fresh_program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    assert rerun.status == fresh.status == "completed"
    np.testing.assert_allclose(rerun.displacements, fresh.displacements,
                               rtol=0.0, atol=1.0e-10)
    np.testing.assert_allclose(
        rerun.info["general_contact"]["integration_force"],
        fresh.info["general_contact"]["integration_force"],
        rtol=0.0, atol=1.0e-10,
    )
    assert rerun.to_restart_checkpoint() == fresh.to_restart_checkpoint()


def test_two_target_displacement_controls_bound_force_reference():
    model, definition, settings, program = build_target_displacement_case(
        normal_motion_m=-1.0e-5, force_reference_n=0.04,
    )
    with pytest.raises(ValueError,
                       match="force scale exceeds the contact-free elastic"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18,
        )


@pytest.mark.parametrize("slide_body", ["target_diagonal_dev", "target"])
def test_guarded_target_motion_open_recontact_split_restart(slide_body):
    def case():
        return build_interior_press(
            source_support="perimeter", source_rows=4,
            load_shape="interior_distributed", force_n=0.04,
            reference_slope=1.0e-4, four_phase=True,
            slide_body=slide_body,
        )

    model, definition, settings, program = case()
    full = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    assert full.status == "completed", full.failure_reason
    assert len(full.steps) == 8
    full_history = full.info["force_displacement_history"]
    assert full_history[3]["contact"]["active_pressure_dofs"] > 0
    assert full_history[5]["contact"]["active_pressure_dofs"] == 0
    assert full_history[7]["contact"]["active_pressure_dofs"] > 0

    model, definition, settings, program = case()
    opened = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        max_load_factor=0.75, emit_restart_checkpoint=True,
    )
    assert opened.status == "completed", opened.failure_reason
    assert len(opened.steps) == 6
    assert opened.restart_checkpoint is not None

    model, definition, settings, program = case()
    resumed = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        restart_checkpoint=opened.to_restart_checkpoint(),
    )
    assert resumed.status == "completed", resumed.failure_reason
    assert len(resumed.steps) == 8
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=0.0, atol=1.0e-10)
    for resumed_row, full_row in zip(
            resumed.info["force_displacement_history"], full_history):
        np.testing.assert_allclose(
            resumed_row["contact"]["integration_force"],
            full_row["contact"]["integration_force"],
            rtol=0.0, atol=1.0e-10,
        )


def test_corrected_left_edge_slide_contact_directional_tangent():
    fixture = json.loads((Path(__file__).parent / "fixtures" /
                          "general_contact_d1_left_edge_slide_pose.json").read_text())
    model, definition, settings, program = build_interior_press(
        source_support="perimeter", source_rows=4,
        load_shape="interior_distributed", force_n=0.04,
        reference_slope=1.0e-4, four_phase=True,
        slide_body="target",
    )
    assert program.total_steps == 8
    nodal_force = np.asarray(fixture["nodal_force_n"])
    assert np.count_nonzero(nodal_force > 0.0) == 1
    manager = GeneralS3PatchManager(model, definition, settings)
    transform = _free_map(model)
    manager.restrict_tangent_to_reduced_variations(transform)
    displacement = np.asarray(fixture["displacements"])
    base = linearize(manager, displacement, nodal_force, tangent=True)

    desired = np.zeros_like(displacement)
    source_dofs = model.mesh.dof_manager.get_node_dofs(13)
    target_lower = model.mesh.dof_manager.get_node_dofs(27)
    target_upper = model.mesh.dof_manager.get_node_dofs(28)
    desired[source_dofs[0]] = 0.25
    desired[source_dofs[2]] = 1.0
    desired[source_dofs[4]] = 0.2
    desired[target_lower[2]] = -0.7
    desired[target_lower[4]] = 0.15
    desired[target_upper[2]] = 0.3
    direction = np.asarray(transform @ (transform.T @ desired)).reshape(-1)
    predicted_force = np.asarray(base.tangent @ direction).reshape(-1)
    predicted_gap = base.gap_gradient @ direction
    assert np.linalg.norm(predicted_force) > 1.0e-8
    assert np.linalg.norm(predicted_gap) > 1.0e-8

    errors = []
    for step_m in (1.0e-6, 5.0e-7, 2.5e-7):
        plus = linearize(manager, displacement+step_m*direction,
                         nodal_force, tangent=False)
        minus = linearize(manager, displacement-step_m*direction,
                          nodal_force, tangent=False)
        observed_force = (plus.force-minus.force)/(2.0*step_m)
        observed_gap = ((plus.state.normalized_gap
                         - minus.state.normalized_gap)/(2.0*step_m))
        force_error = np.linalg.norm(observed_force-predicted_force)/max(
            np.linalg.norm(observed_force), np.linalg.norm(predicted_force),
            1.0e-12,
        )
        gap_error = np.linalg.norm(observed_gap-predicted_gap)/max(
            np.linalg.norm(observed_gap), np.linalg.norm(predicted_gap),
            1.0e-12,
        )
        force_from_gap_gradient = -nodal_force @ (
            (plus.gap_gradient-minus.gap_gradient)/(2.0*step_m))
        gradient_force_error = np.linalg.norm(
            observed_force-force_from_gap_gradient,
        )/max(np.linalg.norm(observed_force), 1.0e-12)
        errors.append((step_m, force_error, gap_error,
                       gradient_force_error,
                       np.linalg.norm(transform.T @ (
                           observed_force-predicted_force))
                       / max(np.linalg.norm(transform.T @ observed_force),
                             1.0e-12)))
    assert all(force_error <= 1.0e-5 and gap_error <= 1.0e-5
               and gradient_force_error <= 1.0e-5
               and reduced_force_error <= 1.0e-5
               for _, force_error, gap_error, gradient_force_error,
               reduced_force_error in errors), {
                   "errors": errors,
                   "largest_force_rows": np.argsort(np.abs(
                       predicted_force-observed_force))[-8:].tolist(),
               }
