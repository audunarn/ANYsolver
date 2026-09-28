"""Bounded ordinary displacement contact and its physical force reference."""

from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from anysolver import solve_static_nonlinear
from anysolver.boundary import BoundaryCondition
from anysolver.nonlinear_static import DisplacementControl
from anysolver.general_contact.static_path import (
    ContactPathControl, ContactPathProgram,
    _elastic_displacement_force_predictor, solve_static_contact_path,
)
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def _case():
    model, definition, settings, _program = build_case(4)
    model.add_boundary_condition(BoundaryCondition(
        "source_x_support", (1, 6), {"ux": 0.0},
    ))
    settings = replace(
        settings, enforcement_solver="monolithic_active_set",
        complementarity_force_scale_n=0.01,
        monolithic_linear_solver="block_response_dev",
        augmentation_acceleration="none",
        augmentation_schur_maximum_modes=None,
        augmentation_schur_maximum_pressure_pa=None,
        augmentation_schur_maximum_step_pa=None,
        augmentation_schur_difference_step_m=None,
        augmentation_schur_maximum_attempts=1,
        augmentation_schur_maximum_relinearizations=0,
    )
    control = DisplacementControl(
        node_id=5, dof="uz", target_displacement=-8.0e-5,
    )
    return model, definition, settings, control


def test_contact_free_elastic_force_predictor_matches_diagonal_spring():
    stiffness = sparse.diags([2.0, 3.0], format="csr")
    transform = sparse.eye(2, format="csr")
    reaction = _elastic_displacement_force_predictor(
        stiffness, transform, np.array([1.0, 0.0]), 0.5,
    )
    assert reaction == pytest.approx(1.0, rel=1e-13)


def test_ordinary_displacement_contact_and_split_restart():
    model, definition, settings, control = _case()
    full = solve_static_nonlinear(
        model, control="displacement", displacement_control=control,
        num_steps=4, contact=definition, contact_settings=settings,
        max_iterations=18, emit_restart_checkpoint=True,
    )
    assert full.status == "completed", (
        full.failure_reason, full.info.get("contact_failure"),
    )
    assert full.info["contact_free_elastic_force_predictor_n"] >= (
        settings.complementarity_force_scale_n
    )
    assert full.info["general_contact"]["active_pressure_dofs"] > 0, (
        full.info["general_contact"]["minimum_gap"],
        full.info["contact_free_elastic_force_predictor_n"],
    )
    assert full.info["general_contact"]["gap_tolerance_met"]

    scaled = solve_static_nonlinear(
        model, control="displacement", displacement_control=control,
        num_steps=4, contact=definition,
        contact_settings=replace(settings, complementarity_force_scale_n=0.02),
        max_iterations=18,
    )
    assert scaled.status == "completed", scaled.failure_reason
    np.testing.assert_allclose(scaled.displacements, full.displacements,
                               rtol=0, atol=1e-10)
    np.testing.assert_allclose(
        scaled.info["general_contact"]["integration_force"],
        full.info["general_contact"]["integration_force"],
        rtol=0, atol=1e-8,
    )

    half = solve_static_nonlinear(
        model, control="displacement", displacement_control=control,
        num_steps=4, max_load_factor=0.5,
        contact=definition, contact_settings=settings,
        max_iterations=18, emit_restart_checkpoint=True,
    )
    assert half.status == "completed" and len(half.steps) == 2
    resumed = solve_static_nonlinear(
        model, control="displacement", displacement_control=control,
        num_steps=4, contact=definition, contact_settings=settings,
        max_iterations=18, restart_checkpoint=half.to_restart_checkpoint(),
    )
    assert resumed.status == "completed"
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=0, atol=1e-10)
    with pytest.raises(ValueError, match="incompatible"):
        solve_static_nonlinear(
            model, control="displacement",
            displacement_control=replace(control, target_displacement=-7.5e-5),
            num_steps=4, contact=definition, contact_settings=settings,
            max_iterations=18,
            restart_checkpoint=half.to_restart_checkpoint(),
        )


def test_ordinary_displacement_rejects_unphysical_force_scale():
    model, definition, settings, control = _case()
    with pytest.raises(ValueError, match="exceeds the contact-free elastic"):
        solve_static_nonlinear(
            model, control="displacement", displacement_control=control,
            num_steps=2, contact=definition,
            contact_settings=replace(settings, complementarity_force_scale_n=1.0e9),
        )


@pytest.mark.parametrize("program", [
    ContactPathProgram(
        (ContactPathControl(((5, "uz", 2.0),)),),
        ((0.0,), (-8.0e-5,)),
    ),
    ContactPathProgram(
        (ContactPathControl(((5, "uz", 1.0), (4, "uz", 1.0))),),
        ((0.0,), (-8.0e-5,)),
    ),
    ContactPathProgram(
        (ContactPathControl.node(5, "uz"),),
        ((0.0,), (-4.0e-5,), (-8.0e-5,)),
    ),
])
def test_one_control_path_rejects_broader_unverified_programs(program):
    model, definition, settings, _control = _case()
    with pytest.raises(ValueError, match="one-control contact path requires"):
        solve_static_contact_path(model, definition, settings, program)
