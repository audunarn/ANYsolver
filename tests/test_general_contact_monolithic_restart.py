"""State continuity and identity for the opt-in monolithic contact route."""

from dataclasses import replace
import copy

import numpy as np
import pytest

from anysolver import solve_static_nonlinear
from anysolver.nonlinear_restart import _checkpoint_without_hash, _sha256
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def _case():
    model, definition, settings, program = build_case(
        4, load_profile="distributed", total_force_n=0.3,
        target_right_x_m=1.3,
    )
    settings = replace(
        settings, enforcement_solver="monolithic_active_set",
        complementarity_force_scale_n=0.3,
        augmentation_acceleration="none",
        augmentation_schur_maximum_modes=None,
        augmentation_schur_maximum_pressure_pa=None,
        augmentation_schur_maximum_step_pa=None,
        augmentation_schur_difference_step_m=None,
        augmentation_schur_maximum_attempts=1,
        augmentation_schur_maximum_relinearizations=0,
    )
    return model, definition, settings, program


def test_monolithic_rejects_unimplemented_ordinary_dispatch():
    model, definition, settings, program = _case()
    with pytest.raises(ValueError, match="requires contact_path_program"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
        )
    with pytest.raises(ValueError, match="force scale must be bounded"):
        solve_static_nonlinear(
            model, contact=definition,
            contact_settings=replace(settings, complementarity_force_scale_n=1e9),
            contact_path_program=program,
        )


def test_monolithic_active_contact_split_restart_and_mode_identity():
    model, definition, settings, program = _case()
    full = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    assert full.status == "completed"
    assert len(full.steps) == 2

    model, definition, settings, program = _case()
    half = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        max_load_factor=0.5, emit_restart_checkpoint=True,
    )
    assert half.status == "completed"
    assert len(half.steps) == 1
    assert half.restart_checkpoint is not None
    assert "normal_forces" in half.restart_checkpoint["path_state"]
    pressure = np.asarray(
        half.info["force_displacement_history"][-1]["contact"]["numerical_pressure_pa"]
    )
    support = np.asarray(
        half.info["force_displacement_history"][-1]["contact"]["reference_support_m2"]
    )
    np.testing.assert_allclose(
        pressure*support,
        half.restart_checkpoint["path_state"]["normal_forces"],
        rtol=0.0, atol=1e-12,
    )

    damaged = copy.deepcopy(half.to_restart_checkpoint())
    damaged["path_state"]["normal_multipliers"][0] += 0.01
    damaged["checkpoint_sha256"] = _sha256(_checkpoint_without_hash(damaged))
    model, definition, settings, program = _case()
    with pytest.raises(ValueError, match="pressure and nodal forces are incompatible"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18,
            restart_checkpoint=damaged,
        )

    model, definition, settings, program = _case()
    resumed = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        restart_checkpoint=half.to_restart_checkpoint(),
        emit_restart_checkpoint=True,
    )
    assert resumed.status == "completed"
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=0.0, atol=1e-10)
    np.testing.assert_allclose(
        resumed.info["force_displacement_history"][-1]["contact"]["integration_force"],
        full.info["force_displacement_history"][-1]["contact"]["integration_force"],
        rtol=0.0, atol=1e-10,
    )

    changed = replace(settings, complementarity_force_scale_n=0.2)
    with pytest.raises(ValueError, match="incompatible"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=changed,
            contact_path_program=program, max_iterations=18,
            restart_checkpoint=half.to_restart_checkpoint(),
        )
    changed_pivots = replace(settings, monolithic_maximum_pivots=32)
    with pytest.raises(ValueError, match="incompatible"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=changed_pivots,
            contact_path_program=program, max_iterations=18,
            restart_checkpoint=half.to_restart_checkpoint(),
        )
    changed_linear_solver = replace(settings,
                                    monolithic_linear_solver="block_response_dev")
    with pytest.raises(ValueError, match="incompatible"):
        solve_static_nonlinear(
            model, contact=definition, contact_settings=changed_linear_solver,
            contact_path_program=program, max_iterations=18,
            restart_checkpoint=half.to_restart_checkpoint(),
        )
