"""Deformable-target contact cycle with a checkpoint at the open state."""

import numpy as np

from anysolver import solve_static_nonlinear
from scripts.general_contact_d1_free_target_press_probe import (
    build_free_target_case,
)


def _case():
    return build_free_target_case(
        4, steps_per_segment=2, four_phase=True,
        enforcement_solver="monolithic_active_set",
    )


def _solve(*, stop=None, checkpoint=None):
    model, definition, settings, program = _case()
    kwargs = {"max_load_factor": stop} if stop is not None else {}
    return solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True, restart_checkpoint=checkpoint,
        **kwargs,
    )


def test_free_target_press_slide_open_recontact_split_restart():
    full = _solve()
    assert full.status == "completed"
    assert len(full.steps) == 8
    history = full.info["force_displacement_history"]
    assert history[1]["contact"]["integration_force"][2] > 0.0
    assert history[5]["contact"]["active_pressure_dofs"] == 0
    assert history[5]["contact"]["minimum_gap"] > 0.0
    assert history[6]["contact"]["integration_force"][2] > 0.0
    for row in history:
        source = np.asarray(row["contact"]["integration_force"])
        target = np.asarray(row["contact"]["target_force"])
        np.testing.assert_allclose(source+target, 0.0, atol=1e-9)
        assert row["contact"]["gap_tolerance_met"]
        assert row["complementarity_relative_force"] <= 1e-8

    opened = _solve(stop=0.75)
    assert opened.status == "completed"
    assert len(opened.steps) == 6
    assert opened.info["force_displacement_history"][-1]["contact"][
        "active_pressure_dofs"] == 0
    resumed = _solve(checkpoint=opened.to_restart_checkpoint())
    assert resumed.status == "completed"
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=0.0, atol=1e-10)
    np.testing.assert_allclose(
        resumed.info["general_contact"]["integration_force"],
        full.info["general_contact"]["integration_force"],
        rtol=0.0, atol=1e-10,
    )
