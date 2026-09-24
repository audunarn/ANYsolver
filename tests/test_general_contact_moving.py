"""Independent scalar controls for translating planar mortar patches."""

import numpy as np
import pytest

from anysolver.general_contact.moving import (
    TranslatedPairMortar,
    moving_mortar_state,
)
from anysolver.general_contact.overlap import PlanarFace


def _square(feature, x0, y0, z=0.0):
    return PlanarFace(feature, np.asarray((
        (x0, y0, z), (x0 + 1.0, y0, z),
        (x0 + 1.0, y0 + 1.0, z), (x0, y0 + 1.0, z),
    )))


def test_translating_pair_potential_force_tangent_and_common_motion():
    law = TranslatedPairMortar(
        (_square((1, 1), 0.0, 0.0),),
        (_square((2, 1), 0.5, 0.25),),
        np.array((0.0, 0.0, 1.0)), 1.0e6,
    )
    source = np.array((0.0, 0.0, -1.0e-4))
    target = np.zeros(3)
    result = law.evaluate(source, target)
    assert result.overlap_area == pytest.approx(0.375)
    assert result.gap == pytest.approx(-1.0e-4)
    assert result.energy == pytest.approx(0.001875)
    np.testing.assert_allclose(result.source_residual,
                               (0.00375, 0.0025, -37.5), atol=1e-10)
    np.testing.assert_allclose(result.source_residual + result.target_residual,
                               0.0, atol=1e-12)
    np.testing.assert_allclose(result.relative_tangent,
                               result.relative_tangent.T, atol=1e-10)
    perturbation = np.array((0.3, -0.2, 0.4))
    h = 1.0e-6
    plus = law.evaluate(source + h * perturbation, target)
    minus = law.evaluate(source - h * perturbation, target)
    assert ((plus.energy - minus.energy) / (2.0 * h)
            == pytest.approx(float(result.source_residual @ perturbation), rel=1e-8))
    np.testing.assert_allclose(
        (plus.source_residual - minus.source_residual) / (2.0 * h),
        result.relative_tangent @ perturbation,
        rtol=1e-7, atol=1e-7,
    )
    common = np.array((0.2, -0.1, 0.3))
    translated = law.evaluate(source + common, target + common)
    assert translated.energy == pytest.approx(result.energy)
    np.testing.assert_allclose(translated.source_residual,
                               result.source_residual, atol=1e-9)
    np.testing.assert_allclose(result.tangent @ np.r_[common, common],
                               0.0, atol=1e-9)


def test_translating_pair_opens_loses_overlap_and_recontacts():
    law = TranslatedPairMortar(
        (_square((1, 1), 0.0, 0.0),),
        (_square((2, 1), 0.5, 0.25),),
        np.array((0.0, 0.0, 1.0)), 1.0e6,
    )
    reference = law.evaluate(np.array((0.0, 0.0, -1.0e-4)), np.zeros(3))
    open_pose = law.evaluate(np.array((0.0, 0.0, 1.0e-4)), np.zeros(3))
    assert open_pose.overlap_area == pytest.approx(reference.overlap_area)
    assert open_pose.energy == 0.0
    np.testing.assert_array_equal(open_pose.source_residual, np.zeros(3))
    distant = law.evaluate(np.array((-1.1, 0.0, -1.0e-4)), np.zeros(3))
    assert distant.overlap_area == 0.0
    assert distant.energy == 0.0
    recontact = law.evaluate(np.array((0.2, 0.0, -1.0e-4)), np.zeros(3))
    assert recontact.overlap_area > 0.0
    assert recontact.energy > 0.0


def test_translated_nonmatching_patch_and_candidate_budget():
    source = (_square((1, 1), 0.0, 0.0),)
    targets = (_square((2, 1), 0.0, 0.0),
               _square((2, 2), 1.0, 0.0))
    law = TranslatedPairMortar(source, targets,
                               np.array((0.0, 0.0, 1.0)), 1.0e6)
    result = law.evaluate(np.array((0.5, 0.0, -1.0e-6)), np.zeros(3))
    assert result.overlap_area == pytest.approx(1.0)
    assert result.energy == pytest.approx(0.5e-6)
    with pytest.raises(MemoryError, match="candidate limit"):
        TranslatedPairMortar(source, targets,
                             np.array((0.0, 0.0, 1.0)), 1.0e6,
                             maximum_candidate_pairs=1)


def test_moving_q1_pressure_reproduces_constant_gap_and_both_body_work():
    source = _square((1, 1), 0.0, 0.0)
    target = _square((2, 1), 0.5, 0.25)
    zero = np.zeros(3)
    source_height = np.full(4, -1.0e-4)
    target_height = np.zeros(4)
    state = moving_mortar_state(
        source, target, np.array((0.0, 0.0, 1.0)), 1.0e6,
        zero, zero, source_height, target_height,
    )
    assert state.overlap_area == pytest.approx(0.375)
    assert np.sum(state.support) == pytest.approx(state.overlap_area)
    np.testing.assert_allclose(state.normalized_gap, -1.0e-4, atol=1e-12)
    assert state.energy == pytest.approx(0.001875)
    assert np.sum(state.normal_residual[:4]) == pytest.approx(-37.5)
    assert np.sum(state.normal_residual[4:]) == pytest.approx(37.5)
    assert state.minimum_vertex_gap == pytest.approx(-1.0e-4)
    direction = np.array((0.1, -0.2, 0.3, 0.05,
                          -0.1, 0.2, -0.05, 0.15))
    h = 1.0e-6
    def trial(fraction):
        return moving_mortar_state(
            source, target, np.array((0.0, 0.0, 1.0)), 1.0e6,
            zero, zero,
            source_height + fraction * direction[:4],
            target_height + fraction * direction[4:],
        )
    plus, minus = trial(h), trial(-h)
    assert ((plus.energy - minus.energy) / (2.0 * h)
            == pytest.approx(float(state.normal_residual @ direction), rel=1e-8))
    np.testing.assert_allclose(
        (plus.normal_residual - minus.normal_residual) / (2.0 * h),
        state.normal_tangent @ direction,
        rtol=1e-7, atol=1e-7,
    )


def test_moving_p1_q1_partial_gap_uses_independent_physical_vertex_check():
    source = PlanarFace((1, 1), np.asarray(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    ))
    target = _square((2, 1), 0.0, 0.0)
    zero = np.zeros(3)
    state = moving_mortar_state(
        source, target, np.array((0.0, 0.0, 1.0)), 1.0e6,
        np.array((0.2, 0.0, 0.0)), zero,
        np.array((-1.0e-4, 0.0, 0.0)), np.zeros(4),
    )
    assert state.overlap_area > 0.0
    assert state.minimum_vertex_gap < 0.0
    assert state.energy > 0.0
    assert np.all(state.support > 0.0)
    assert np.sum(state.normal_residual[:3]) == pytest.approx(
        -np.sum(state.normal_residual[3:])
    )


def test_moving_pressure_energy_matches_translation_boundary_control():
    source = _square((1, 1), 0.0, 0.0)
    target = _square((2, 1), 0.5, 0.25)
    control = TranslatedPairMortar((source,), (target,),
                                   np.array((0.0, 0.0, 1.0)), 1.0e6)
    direction = np.array((0.3, -0.2, 0.0))
    def energy(shift):
        return moving_mortar_state(
            source, target, np.array((0.0, 0.0, 1.0)), 1.0e6,
            shift * direction, np.zeros(3),
            np.full(4, -1.0e-4), np.zeros(4),
        ).energy
    h = 1.0e-6
    reference = control.evaluate(np.array((0.0, 0.0, -1.0e-4)), np.zeros(3))
    assert energy(0.0) == pytest.approx(reference.energy)
    assert ((energy(h) - energy(-h)) / (2.0 * h)
            == pytest.approx(float(reference.source_residual @ direction), rel=1e-8))
