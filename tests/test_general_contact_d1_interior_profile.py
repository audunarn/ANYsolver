"""Admission checks for the opt-in planar Q4/S3 interior slice."""

from dataclasses import replace

import numpy as np
import pytest

from anysolver import BoundaryCondition, solve_static_nonlinear
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_interior_press_dev import build_interior_press
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
