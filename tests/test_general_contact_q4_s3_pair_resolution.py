"""Local gates for Q4/S3 float/Jet2 geometry comparison."""

import numpy as np
import pytest
from dataclasses import replace
import json
from pathlib import Path

from scripts.general_contact_d1_coupled_refinement import build_case
from anysolver.general_contact.core import ContactSolverSettings
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


def test_shared_edge_tie_settings_require_explicit_bounded_jet2_profile():
    with pytest.raises(ValueError, match="needs step, direction and relative tolerance"):
        ContactSolverSettings(q4_s3_shared_edge_tie_step_m=3.0e-8)
    with pytest.raises(ValueError, match="needs Jet2 Q4/S3"):
        ContactSolverSettings(
            q4_s3_shared_edge_tie_step_m=3.0e-8,
            q4_s3_shared_edge_tie_direction=(1.0, 0.0, 0.0),
            q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
        )
    with pytest.raises(ValueError, match="unit 3-vector"):
        ContactSolverSettings(
            general_s3_differentiation="jet2_q4_s3_dev",
            q4_s3_shared_edge_tie_step_m=3.0e-8,
            q4_s3_shared_edge_tie_direction=(2.0, 0.0, 0.0),
            q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
        )


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
    assert "q4_s3_shared_edge_tie_step_m" not in owner.restart_contract()["settings"]
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


def test_opt_in_exact_shared_edge_limit_preserves_exact_state_and_wrench():
    model, definition, settings, _ = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    settings = replace(
        settings, q4_s3_shared_edge_tie_step_m=3.0e-8,
        q4_s3_shared_edge_tie_direction=(1.0, 0.0, 0.0),
        q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    assert owner.restart_contract()["settings"]["q4_s3_shared_edge_tie_direction"] == [1.0, 0.0, 0.0]
    geometry = owner.law.geometry
    source = geometry.reference_source.copy()
    source[:, 0] += 0.05
    source[:, 2] -= 0.01504
    target = geometry.reference_target
    multipliers = np.zeros(len(geometry.source_node_ids))
    exact = owner.law.evaluate(source, target, multipliers)
    work = owner.law.work(source, target, multipliers, tangent=True)
    assert work.state is not exact
    np.testing.assert_array_equal(work.state.reference_support,
                                  exact.reference_support)
    np.testing.assert_array_equal(work.state.pressure, exact.pressure)
    assert work.tie_resolution_relative_error is not None
    assert work.tie_resolution_relative_error < 1.0e-6
    assert work.energy_evaluations <= settings.maximum_general_s3_energy_evaluations
    force = work.residual.reshape(-1, 3)
    points = np.vstack((source, target))
    np.testing.assert_allclose(force.sum(axis=0), 0.0, atol=1.0e-8)
    np.testing.assert_allclose(np.cross(points, force).sum(axis=0),
                               0.0, atol=1.0e-8)
    for sign in (-1, 1):
        neighbor = source.copy()
        neighbor[:, 0] += sign*1.5e-8
        smooth = owner.law.work(neighbor, target, multipliers, tangent=True)
        assert np.linalg.norm(work.residual-smooth.residual)/np.linalg.norm(work.residual) < 1.0e-6
        assert np.linalg.norm(work.tangent-smooth.tangent)/np.linalg.norm(work.tangent) < 1.0e-6
    direction = np.zeros_like(points)
    direction[:len(source), 2] = 1.0
    plus = source.copy()
    minus = source.copy()
    plus[:, 2] += 1.0e-6
    minus[:, 2] -= 1.0e-6
    finite_difference = (
        owner.law.work(plus, target, multipliers, tangent=False).residual
        - owner.law.work(minus, target, multipliers, tangent=False).residual
    )/(2.0e-6)
    tangent_action = work.tangent @ direction.ravel()
    assert np.linalg.norm(finite_difference-tangent_action)/max(
        1.0, np.linalg.norm(tangent_action)) < 1.0e-5

    normal_axes = np.arange(2, work.residual.size, 3)
    owner.law.set_tangent_active_coordinates(normal_axes)
    reduced = owner.law.work(source, target, multipliers, tangent=True)
    np.testing.assert_allclose(reduced.residual, work.residual, rtol=1.0e-10,
                               atol=1.0e-12)
    np.testing.assert_array_equal(
        reduced.tangent[:, np.setdiff1d(np.arange(work.residual.size), normal_axes)],
        0.0,
    )
    owner.law.set_tangent_active_coordinates(np.arange(work.residual.size))

    owner.law.shared_edge_tie = (3.0e-8, np.array((1.0, 0.0, 0.0)), 1.0e-12)
    with pytest.raises(UnsupportedQ4S3Branch, match="shared-edge tie"):
        owner.law.work(source, target, multipliers, tangent=True)
    owner.law.shared_edge_tie = (3.0e-8, np.array((1.0, 0.0, 0.0)), 1.0e-6)
    warped = target.copy()
    warped[2, 2] += 1.0e-4
    assert not owner.law._only_artificial_shared_edge_ties(source, warped)


@pytest.mark.parametrize("fixture_name, unresolved", [
    ("general_contact_q4_s3_recontact_shared_edge_pose.json",
     "degenerate integration triangle"),
    ("general_contact_q4_s3_augmented_shared_edge_pose.json",
     "paired overlap area agreement is unresolved"),
])
def test_recontact_tiny_shared_edge_wedge_uses_resolved_limit(
        fixture_name, unresolved):
    fixture = json.loads((Path(__file__).parent / "fixtures" /
                          fixture_name).read_text())
    model, definition, settings, _ = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    settings = replace(
        settings, q4_s3_shared_edge_tie_step_m=3.0e-8,
        q4_s3_shared_edge_tie_direction=(1.0, 0.0, 0.0),
        q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    source = np.asarray(fixture["source"])
    target = np.asarray(fixture["target"])
    multipliers = np.asarray(fixture["multipliers"])
    assert owner.law._only_artificial_shared_edge_ties(
        source, target, failed_pair=2)
    with pytest.raises(UnsupportedQ4S3Branch, match=unresolved):
        owner.law._work_unresolved(source, target, multipliers, tangent=True)
    work = owner.law.work(source, target, multipliers, tangent=True)
    assert work.tie_resolution_relative_error < 1.0e-6
    assert work.energy_evaluations <= settings.maximum_general_s3_energy_evaluations
    force = work.residual.reshape(-1, 3)
    points = np.vstack((source, target))
    np.testing.assert_allclose(force.sum(axis=0), 0.0, atol=1.0e-8)
    np.testing.assert_allclose(np.cross(points, force).sum(axis=0),
                               0.0, atol=1.0e-8)


def test_tiny_wedge_requires_verified_reduced_derivatives():
    fixture = json.loads((Path(__file__).parent / "fixtures" /
                          "general_contact_q4_s3_neighbor_value_gate_pose.json").read_text())
    model, definition, settings, _ = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    settings = replace(
        settings, q4_s3_shared_edge_tie_step_m=3.0e-8,
        q4_s3_shared_edge_tie_direction=(1.0, 0.0, 0.0),
        q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    with pytest.raises(UnsupportedQ4S3Branch,
                       match="shared-edge tie smooth neighbor unresolved"):
        owner.law.work(np.asarray(fixture["source"]),
                       np.asarray(fixture["target"]),
                       np.asarray(fixture["multipliers"]), tangent=True)
    owner.law.set_tangent_active_coordinates([
        3*node+axis for node in range(len(owner.law.source_node_ids))
        for axis in (0, 2)
    ])
    work = owner.law.work(np.asarray(fixture["source"]),
                          np.asarray(fixture["target"]),
                          np.asarray(fixture["multipliers"]), tangent=True)
    assert work.tie_resolution_relative_error < 1.0e-6
    assert work.energy_evaluations <= settings.maximum_general_s3_energy_evaluations
    force = work.residual.reshape(-1, 3)
    np.testing.assert_allclose(force.sum(axis=0), 0.0, atol=1.0e-8)


def test_exact_seam_uses_resolved_outer_directional_quotient():
    fixture = json.loads((Path(__file__).parent / "fixtures" /
                          "general_contact_q4_s3_neighbor_value_gate_pose.json").read_text())
    model, definition, settings, _ = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    settings = replace(
        settings, q4_s3_shared_edge_tie_step_m=3.0e-8,
        q4_s3_shared_edge_tie_direction=(1.0, 0.0, 0.0),
        q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    owner.law.set_tangent_active_coordinates([
        3*node+axis for node in range(len(owner.law.source_node_ids))
        for axis in (0, 2)
    ])
    # A saved rejected Schur proposal at this pose has concentrated pressure.
    multipliers = np.asarray((
        21.541356, 0.0, 0.0, 0.0, 0.0,
        13.067722, 1.0e-6, 0.0, 0.0, 0.0,
        43.148131, 0.0, 0.0, 0.0, 0.0,
    ))
    work = owner.law.work(
        np.asarray(fixture["source"]), np.asarray(fixture["target"]),
        multipliers, tangent=True,
    )
    assert work.tie_resolution_relative_error < 1.0e-6
    assert work.energy_evaluations <= settings.maximum_general_s3_energy_evaluations
