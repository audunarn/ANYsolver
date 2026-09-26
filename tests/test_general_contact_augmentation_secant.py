"""Safeguards for the optional projected augmented-contact predictor."""

from dataclasses import replace

import numpy as np
import pytest

from anysolver import (
    ContactSolverSettings, solve_static_nonlinear, validate_general_contact,
)
from anysolver.general_contact.augmentation import ProjectedAugmentationSecant
from examples.general_contact_refined_q4_s3_mixed_path import make_case


def test_active_secant_predicts_independent_affine_two_pressure_root():
    root = np.array((0.12, 0.15))
    compliance = np.array(((0.217469849, 0.154498127),
                           (0.188831044, 0.172447028)))
    predictor = ProjectedAugmentationSecant()
    current = np.zeros(2)
    proposals = []
    for _ in range(7):
        projected = np.maximum(0.0, current - compliance @ (current - root))
        proposals.append(predictor.propose(current, projected))
        current = projected
    assert all(value is None for value in proposals[:3])
    np.testing.assert_allclose(proposals[3], root, atol=1.0e-8, rtol=0.0)
    assert predictor.applied >= 1


def test_active_secant_resets_at_active_set_change_and_rejects_invalid_samples():
    predictor = ProjectedAugmentationSecant()
    assert predictor.propose(np.zeros(2), np.array((0.1, 0.0))) is None
    assert predictor.propose(np.array((0.1, 0.0)), np.array((0.2, 0.0))) is None
    assert predictor.propose(np.array((0.2, 0.0)), np.array((0.3, 0.1))) is None
    assert predictor.applied == 0
    assert predictor.propose(np.array((0.3, 0.1)), np.zeros(2)) is None
    assert predictor.applied == 0
    try:
        predictor.propose(np.zeros(2), np.array((float("nan"), 0.0)))
    except ValueError:
        pass
    else:
        raise AssertionError("nonfinite multiplier projection was accepted")


def test_active_secant_falls_back_for_unidentifiable_multiplier_map():
    predictor = ProjectedAugmentationSecant()
    for _ in range(4):
        assert predictor.propose(np.array((0.1, 0.1)),
                                 np.array((0.2, 0.2))) is None
    assert predictor.attempts == 1
    assert predictor.applied == 0


def test_active_secant_setting_is_explicit_and_validated():
    assert ContactSolverSettings().augmentation_acceleration == "none"
    assert ContactSolverSettings(
        augmentation_acceleration="active_secant"
    ).augmentation_acceleration == "active_secant"
    with pytest.raises(ValueError, match="augmentation_acceleration"):
        ContactSolverSettings(augmentation_acceleration="automatic")
    model, definition, settings, _program = make_case()
    penalty = replace(definition, interactions=(replace(
        definition.interactions[0], normal_law="penalty",
    ),))
    report = validate_general_contact(
        model, penalty, replace(settings, augmentation_acceleration="active_secant"),
    )
    assert not report.valid
    assert "requires one augmented" in report.issues[0]
    with pytest.raises(ValueError, match="requires the contact path analysis owner"):
        solve_static_nonlinear(
            model, contact=definition,
            contact_settings=replace(
                settings, augmentation_acceleration="active_secant",
            ),
        )
