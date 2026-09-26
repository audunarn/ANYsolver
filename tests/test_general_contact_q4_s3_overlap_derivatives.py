"""Smooth affine Q4/S3 value and derivative checks."""

import numpy as np
import pytest

import anysolver.general_contact.q4_s3_overlap_derivatives as derivative_module
from anysolver.general_contact.q4_s3_overlap_derivatives import (
    UnsupportedQ4S3Branch,
    _evaluate,
    q4_s3_overlap_derivatives,
)
from anysolver.general_contact.q4_source_overlap import q4_source_overlap_integrals


REFERENCE = np.array([[0., 0., 0.], [2., 0., 0.],
                      [2., 2., 0.], [0., 2., 0.]])
SOURCE = np.array([[0., 0., 0.], [2., 0., 0.1],
                   [2., 2., 0.], [0., 2., -0.1]])
TARGET = np.array([[0.31, 0.19, -0.11], [2.21, 0.37, -0.03],
                   [0.63, 1.77, -0.15]])
OPTIONS = dict(area_tolerance=1e-9, weighted_gap_tolerance=1e-9,
               maximum_triangles=32, relative_branch_tolerance=1e-10)


def _from_flat(flat, *, unrestricted=False):
    source = flat[:12].reshape(4, 3)
    target = flat[12:].reshape(3, 3)
    if unrestricted:
        return _evaluate(REFERENCE, source, target, **OPTIONS,
                         enforce_affine=False)
    return q4_s3_overlap_derivatives(REFERENCE, source, target, **OPTIONS)


def test_values_match_q4_source_kernel_on_partial_overlap():
    ours = q4_s3_overlap_derivatives(REFERENCE, SOURCE, TARGET, **OPTIONS)
    existing = q4_source_overlap_integrals(
        REFERENCE, SOURCE, TARGET,
        area_tolerance=OPTIONS['area_tolerance'],
        weighted_gap_tolerance=OPTIONS['weighted_gap_tolerance'],
        maximum_triangles=OPTIONS['maximum_triangles'],
    )
    assert ours.overlap_area < 4.0
    assert ours.integration_triangles == existing.integration_triangles
    assert ours.overlap_area == pytest.approx(existing.overlap_area, rel=1e-12)
    assert ours.reference_overlap_area == pytest.approx(
        existing.reference_overlap_area, rel=1e-12,
    )
    np.testing.assert_allclose(ours.reference_support, existing.support,
                               rtol=1e-11, atol=1e-12)
    np.testing.assert_allclose(ours.reference_weighted_gap,
                               existing.weighted_gap, rtol=1e-11, atol=1e-12)
    assert np.all(ours.reference_support > 0)


def test_all_coordinate_derivatives_match_q1_continuation_differences():
    x = np.concatenate((SOURCE, TARGET)).reshape(-1)
    base = _from_flat(x)
    rng = np.random.default_rng(250926)
    for _ in range(2):
        direction = rng.normal(size=21)
        direction /= np.linalg.norm(direction)
        step = 1e-5
        plus = _from_flat(x+step*direction, unrestricted=True)
        minus = _from_flat(x-step*direction, unrestricted=True)
        assert plus.branch_signature == minus.branch_signature == base.branch_signature
        for value, gradient, hessian, plus_value, minus_value, plus_gradient, minus_gradient in (
            (base.reference_support, base.support_gradient, base.support_hessian,
             plus.reference_support, minus.reference_support,
             plus.support_gradient, minus.support_gradient),
            (base.reference_weighted_gap, base.weighted_gap_gradient,
             base.weighted_gap_hessian, plus.reference_weighted_gap,
             minus.reference_weighted_gap, plus.weighted_gap_gradient,
             minus.weighted_gap_gradient),
        ):
            np.testing.assert_allclose((plus_value-minus_value)/(2*step),
                                       gradient@direction, rtol=2e-5, atol=1e-8)
            np.testing.assert_allclose((plus_gradient-minus_gradient)/(2*step),
                                       np.einsum('ijk,k->ij', hessian, direction),
                                       rtol=5e-5, atol=2e-7)
            np.testing.assert_allclose(hessian, np.swapaxes(hessian, 1, 2),
                                       atol=2e-11)


def test_affine_direction_matches_existing_kernel_difference():
    x = np.concatenate((SOURCE, TARGET)).reshape(-1)
    base = _from_flat(x)
    rng = np.random.default_rng(926)
    direction = rng.normal(size=(7, 3))
    direction[2] = direction[1]+direction[3]-direction[0]
    direction = (direction/np.linalg.norm(direction)).reshape(-1)
    step = 2e-5

    def existing(at):
        values = at.reshape(7, 3)
        return q4_source_overlap_integrals(
            REFERENCE, values[:4], values[4:],
            area_tolerance=OPTIONS['area_tolerance'],
            weighted_gap_tolerance=OPTIONS['weighted_gap_tolerance'],
            maximum_triangles=OPTIONS['maximum_triangles'],
        )

    plus, minus = existing(x+step*direction), existing(x-step*direction)
    np.testing.assert_allclose((plus.support-minus.support)/(2*step),
                               base.support_gradient@direction,
                               rtol=3e-6, atol=2e-8)
    np.testing.assert_allclose((plus.weighted_gap-minus.weighted_gap)/(2*step),
                               base.weighted_gap_gradient@direction,
                               rtol=3e-6, atol=2e-8)


def test_ambient_direction_matches_existing_kernel_warped_continuation():
    x = np.concatenate((SOURCE, TARGET)).reshape(-1)
    base = _from_flat(x)
    rng = np.random.default_rng(260926)
    direction = rng.normal(size=21)
    direction /= np.linalg.norm(direction)
    deformed = direction[:12].reshape(4, 3)
    assert np.linalg.norm(deformed[0]-deformed[1]+deformed[2]-deformed[3]) > 0.1
    normal = np.cross(SOURCE[1]-SOURCE[0], SOURCE[3]-SOURCE[0])
    normal /= np.linalg.norm(normal)
    assert abs(np.dot(deformed[0]-deformed[1]+deformed[2]-deformed[3],
                      normal)) > 0.1

    def existing(at):
        positions = at.reshape(7, 3)
        return q4_source_overlap_integrals(
            REFERENCE, positions[:4], positions[4:],
            area_tolerance=OPTIONS['area_tolerance'],
            weighted_gap_tolerance=OPTIONS['weighted_gap_tolerance'],
            maximum_triangles=OPTIONS['maximum_triangles'],
        )

    first_step = 1e-5
    plus = existing(x+first_step*direction)
    minus = existing(x-first_step*direction)
    assert plus.integration_triangles == minus.integration_triangles == base.integration_triangles
    np.testing.assert_allclose(
        (plus.support-minus.support)/(2*first_step),
        base.support_gradient@direction, rtol=3e-5, atol=2e-8,
    )
    np.testing.assert_allclose(
        (plus.weighted_gap-minus.weighted_gap)/(2*first_step),
        base.weighted_gap_gradient@direction, rtol=3e-5, atol=2e-8,
    )
    second_step = 2e-4
    plus = existing(x+second_step*direction)
    minus = existing(x-second_step*direction)
    at_base = existing(x)
    assert plus.integration_triangles == minus.integration_triangles == base.integration_triangles
    np.testing.assert_allclose(
        (plus.support-2*at_base.support+minus.support)/second_step**2,
        np.einsum('i,aij,j->a', direction, base.support_hessian, direction),
        rtol=2e-4, atol=2e-6,
    )
    np.testing.assert_allclose(
        (plus.weighted_gap-2*at_base.weighted_gap+minus.weighted_gap)
        /second_step**2,
        np.einsum('i,aij,j->a', direction, base.weighted_gap_hessian, direction),
        rtol=2e-4, atol=2e-6,
    )


def test_rigid_invariance_and_force_wrench_balance():
    x = np.concatenate((SOURCE, TARGET)).reshape(-1)
    base = _from_flat(x)
    angle = 0.27
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                         [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    moved = x.reshape(7, 3)@rotation.T+np.array([0.8, -0.3, 0.6])
    other = _from_flat(moved.reshape(-1))
    np.testing.assert_allclose(other.reference_support, base.reference_support,
                               rtol=1e-11, atol=1e-11)
    np.testing.assert_allclose(other.reference_weighted_gap,
                               base.reference_weighted_gap, rtol=1e-11, atol=1e-11)
    assert other.branch_signature == base.branch_signature
    for gradient in (base.support_gradient, base.weighted_gap_gradient):
        for row in gradient:
            forces = row.reshape(7, 3)
            np.testing.assert_allclose(forces.sum(axis=0), 0, atol=1e-9)
            np.testing.assert_allclose(np.cross(x.reshape(7, 3), forces).sum(axis=0),
                                       0, atol=1e-9)


def test_non_affine_and_boundary_branches_reject():
    warped = SOURCE.copy()
    warped[2, 2] += 0.02
    with pytest.raises(UnsupportedQ4S3Branch, match="warped or non-affine"):
        q4_s3_overlap_derivatives(REFERENCE, warped, TARGET, **OPTIONS)
    with pytest.raises(UnsupportedQ4S3Branch, match="clipping boundary"):
        q4_s3_overlap_derivatives(REFERENCE, SOURCE, SOURCE[[0, 1, 3]], **OPTIONS)


def test_adaptive_required_branch_rejects(monkeypatch):
    # A centroid-only rule cannot integrate the Q1 support/Gram on this cut.
    monkeypatch.setattr(derivative_module, "_TRIANGLE_RULE",
                        (((1/3, 1/3, 1/3), 1.0),))
    with pytest.raises(UnsupportedQ4S3Branch, match="adaptive integration"):
        q4_s3_overlap_derivatives(REFERENCE, SOURCE, TARGET, **OPTIONS)
