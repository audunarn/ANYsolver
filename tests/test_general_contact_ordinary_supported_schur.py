"""Bounded supported-pressure proposals in ordinary force control."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from anysolver import solve_static_nonlinear
from anysolver.general_contact import linearized_pivot
from anysolver.general_contact.supported_schur import SupportedSchurProposal
from scripts.general_contact_d1_finite_area_load import build_case


def test_ordinary_force_control_verifies_schur_before_committing():
    model, load, definition, settings = build_case(2, supported_schur=True)
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        control="force", kinematics="von_karman", num_steps=1,
        max_load_factor=0.5, max_iterations=12,
        min_step_fraction=0.5, emit_restart_checkpoint=True,
    )
    assert result.status == "completed", result.failure_reason
    assert len(result.steps) == 1
    attempts = result.info["contact_augmentation_attempts"]
    assert len(attempts) == 1
    assert attempts[0]["equilibrium_converged"]
    trace = attempts[0]["trace"]
    assert any(row.get("schur_proposed") for row in trace)
    assert any(row.get("schur_verified") for row in trace)
    assert trace[-1]["normal_multiplier_change_pa"] <= settings.pressure_tolerance
    contact = result.info["general_contact"]
    assert contact["gap_tolerance_met"]
    assert contact["active_pressure_dofs"] > 0
    np.testing.assert_allclose(
        np.asarray(contact["integration_force"])
        + np.asarray(contact["target_force"]),
        0.0, atol=1.0e-8,
    )
    assert result.restart_checkpoint is not None


def test_ordinary_schur_rejects_follower_load_before_solving():
    model, load, definition, settings = build_case(2, supported_schur=True)
    load.follower_pressure = True
    with pytest.raises(ValueError, match="one dead nodal load case"):
        solve_static_nonlinear(
            model, load, contact=definition, contact_settings=settings,
            control="force", kinematics="von_karman", num_steps=1,
        )


def test_ordinary_schur_rejects_penalty_only_before_solving():
    model, load, definition, settings = build_case(2, supported_schur=True)
    definition = replace(definition, interactions=(
        replace(definition.interactions[0], normal_law="penalty"),
    ))
    with pytest.raises(ValueError, match="one augmented contact interaction"):
        solve_static_nonlinear(
            model, load, contact=definition, contact_settings=settings,
            control="force", kinematics="von_karman", num_steps=1,
        )


def test_ordinary_schur_factorization_failure_falls_back(monkeypatch):
    model, load, definition, settings = build_case(2, supported_schur=True)
    monkeypatch.setattr(
        linearized_pivot, "factorize",
        lambda *_args, **_kwargs: SimpleNamespace(
            status="ok",
            solve=lambda _rhs: (_ for _ in ()).throw(
                RuntimeError("injected singular response")
            ),
        ),
    )
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        control="force", kinematics="von_karman", num_steps=1,
        max_load_factor=0.5, max_iterations=12, min_step_fraction=0.5,
    )
    assert any(
        row.get("schur_response_failure") == "injected singular response"
        for attempt in result.info["contact_augmentation_attempts"]
        for row in attempt["trace"]
    )
    assert any(
        row.get("schur_proposed") is False
        for attempt in result.info["contact_augmentation_attempts"]
        for row in attempt["trace"]
    )


def test_ordinary_schur_rejects_bad_candidate_and_restores_state(monkeypatch):
    model, load, definition, settings = build_case(2, supported_schur=True)

    def bad_proposal(manager, *_args, **_kwargs):
        # Deliberately claim the wrong active branch. The analysis owner must
        # verify it after equilibrium rather than trusting this local claim.
        trial = manager.normal_multipliers.copy()
        source, target = manager._positions(_args[0])
        state = manager.law.evaluate(source, target, trial)
        trial[state.reference_support > 0.0] += 0.5
        return SupportedSchurProposal(
            trial, (0,), None, 1.0, 1.0, 0.1,
        )

    monkeypatch.setattr(linearized_pivot,
                        "refined_patch_supported_schur", bad_proposal)
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        control="force", kinematics="von_karman", num_steps=1,
        max_load_factor=0.5, max_iterations=12,
        min_step_fraction=0.5,
    )
    assert result.status != "completed"
    # The quarter-load cutback can accept as an open state. The failed
    # half-load contact trial must leave that last accepted state intact.
    assert len(result.steps) == 1
    assert result.load_factor == 0.25
    assert any(row.get("schur_rejected") for attempt in
               result.info["contact_augmentation_attempts"]
               for row in attempt["trace"])
    assert np.linalg.norm(result.displacements) > 0.0
    np.testing.assert_array_equal(
        result.info["general_contact"]["normal_multiplier_estimate_pa"],
        0.0,
    )
