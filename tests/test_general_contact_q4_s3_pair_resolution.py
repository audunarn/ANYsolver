"""Local gates for Q4/S3 float/Jet2 geometry comparison."""

import numpy as np
import pytest

from scripts.general_contact_d1_coupled_refinement import build_case
from anysolver.general_contact.overlap import PlanarFace
from anysolver.general_contact.q4_s3_overlap_derivatives import UnsupportedQ4S3Branch
from anysolver.general_contact.s3_patch_augmented import (
    _q4_s3_pair_value_rtol, _touching_shared_target_edge,
)
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager


def test_tiny_wedge_area_disagreement_has_small_bounded_value_allowance():
    local = 4.45786736357e-16
    derivative = 4.45786737393e-16
    tolerance = _q4_s3_pair_value_rtol(local, derivative, 6.35274248175e-20)
    assert 1.0e-9 < tolerance < 1.0e-8


def test_near_resolution_area_cannot_open_unbounded_value_tolerance():
    with pytest.raises(UnsupportedQ4S3Branch, match="area agreement is unresolved"):
        _q4_s3_pair_value_rtol(1.0e-16, 1.1e-16, 2.0e-17)
    with pytest.raises(UnsupportedQ4S3Branch, match="area agreement is unresolved"):
        _q4_s3_pair_value_rtol(1.0e-4, 1.00000001e-4, 1.0e-14)


def test_inactive_zero_area_branch_requires_touch_on_shared_material_edge():
    source = PlanarFace((1, 1), np.array((
        (0.0, 0.25, 0.0), (1.0, 0.25, 0.0),
        (1.0, 0.75, 0.0), (0.0, 0.75, 0.0),
    )))
    ids = np.array((5, 6, 7))
    shared = {5, 6}
    shared_edge_touch = np.array(((1.0, 0.0, 0.0), (1.0, 1.0, 0.0),
                                  (1.5, 0.5, 0.0)))
    exterior_vertex_touch = np.array(((1.5, 0.0, 0.0), (1.5, 1.0, 0.0),
                                      (1.0, 0.5, 0.0)))
    shared_endpoint_touch = np.array(((1.0, 0.5, 0.0), (1.5, 1.0, 0.0),
                                      (1.5, 0.0, 0.0)))
    assert _touching_shared_target_edge(source, shared_edge_touch, ids, shared)
    assert not _touching_shared_target_edge(source, exterior_vertex_touch,
                                            ids, shared)
    assert not _touching_shared_target_edge(source, shared_endpoint_touch,
                                            ids, shared)


def test_patch_owner_fails_at_exact_positive_tie_and_balances_both_smooth_sides():
    model, definition, settings, _ = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    geometry = owner.law.geometry
    source = geometry.reference_source.copy()
    target = geometry.reference_target
    source[:, 0] += 0.05
    source[:, 2] -= 0.01504
    multipliers = np.zeros(len(geometry.source_node_ids))
    with pytest.raises(UnsupportedQ4S3Branch, match="clipping boundary"):
        owner.law.work(source, target, multipliers, tangent=True)

    for slide_offset in (-3.0e-8, 3.0e-8):
        smooth = source.copy()
        smooth[:, 0] += slide_offset
        work = owner.law.work(smooth, target, multipliers, tangent=True)
        assert work.state.active_pressure_dofs > 0
        force = work.residual.reshape(-1, 3)
        points = np.vstack((smooth, target))
        np.testing.assert_allclose(force.sum(axis=0), 0.0, atol=1.0e-8)
        np.testing.assert_allclose(np.cross(points, force).sum(axis=0),
                                   0.0, atol=1.0e-8)
        direction = np.zeros_like(points)
        direction[:len(smooth), 2] = 1.0
        direction = direction.ravel()
        step = 1.0e-6
        plus = smooth.copy()
        minus = smooth.copy()
        plus[:, 2] += step
        minus[:, 2] -= step
        finite_difference = (
            owner.law.work(plus, target, multipliers, tangent=False).residual
            - owner.law.work(minus, target, multipliers, tangent=False).residual
        )/(2.0*step)
        tangent_action = work.tangent @ direction
        error = np.linalg.norm(finite_difference-tangent_action)
        assert error/max(1.0, np.linalg.norm(tangent_action)) < 1.0e-5
