"""Whole material-panel separation, including hidden temporal contact."""
from dataclasses import replace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver.general_contact.native_surface_history import NativeSurfaceHistoryField, NativeSurfaceMotionSegment
from anysolver.general_contact.native_surface_patch import NativeS3MaterialSurfacePatch
from anysolver.general_contact.native_surface_path import material_path_pose
from anysolver.general_contact.native_surface_quadrature import NativeRoundSurfaceRule
from anysolver.general_contact.native_surface_support import (
    SupportIntervalBudget, history_endpoint_support_certified, panel_open_over_history,
)
from anysolver.general_contact.s3_friction_point import S3SkinMaterialPoint
from test_general_contact_native_surface_s3_friction import _case


def _field(*, height=.05, rotation=0., segments=(), maximum_intervals=256):
    _, point_pair, initial, _ = _case()
    angles = (1.5*np.pi-.02, 1.5*np.pi+.02)
    rule = NativeRoundSurfaceRule(7, point_pair.source.reference, .03,
        xi_range=(-.8, -.2), angle_range=angles, axial_order=1, angular_order=2)
    positions = initial.positions.copy()
    positions[:, 2] = -.04+height
    rotations = initial.cell_rotations.copy()
    rotations[0] = Rotation.from_rotvec((rotation, 0., 0.)).as_matrix()
    initial = replace(initial, positions=positions, cell_rotations=rotations)
    adapter = point_pair.target.adapter
    corners = adapter.current_positions(initial.shell_displacement)
    edges = np.column_stack((corners[1]-corners[0], corners[2]-corners[0]))
    targets = []
    for sample in rule.samples:
        point = sample.station.evaluate(initial.positions, initial.position_low, initial.cell_rotations).surface_position
        uv = np.linalg.lstsq(edges, point-corners[0], rcond=None)[0]
        targets.append(S3SkinMaterialPoint(adapter, (1-uv.sum(), *uv)))
    patch = NativeS3MaterialSurfacePatch(rule, targets, normal_stiffness_Pa_per_m=1000.,
        friction_coefficient=.3, tangential_stiffness_Pa_per_m=1000.,
        activation_policy='transverse_events', gap_check='straight_patch')
    return NativeSurfaceHistoryField(patch, initial, segments, maximum_intervals=maximum_intervals)


def _certify(field, maximum_intervals=256):
    return panel_open_over_history(field, 0, (-.8, -.2),
                                  field.patch.rule.definition['angle_range'], maximum_intervals=maximum_intervals)


def test_static_whole_panel_and_all_history_segments():
    assert _certify(_field())
    zero = NativeSurfaceMotionSegment(np.zeros((3, 3)), np.zeros((2, 3)), np.zeros(18))
    assert _certify(_field(segments=(zero, zero)), maximum_intervals=2)
    assert not _certify(_field(segments=(zero, zero)), maximum_intervals=1)


def test_hidden_contact_pulse_between_open_rotational_endpoints():
    segment = NativeSurfaceMotionSegment(np.zeros((3, 3)), np.array(((1.6, 0., 0.), (0., 0., 0.))), np.zeros(18))
    field = _field(height=.025, rotation=-.8, segments=(segment,))
    # For the centre angle, g(alpha)=.025-.03*cos(-.8+1.6*alpha).
    # The entire narrow arc is open at both endpoints and closed at midtime.
    assert .025-.03*np.cos(.8-.02) > 0.
    assert .025-.03 < 0.
    assert not _certify(field)
    # An endpoint-only rule would accept; both static endpoint fields do.
    assert _certify(_field(height=.025, rotation=-.8))
    assert _certify(_field(height=.025, rotation=.8))


def test_positive_rotating_source_with_finite_affine_target_deformation():
    shell = np.zeros(18)
    shell[8] = .01
    shell[14] = -.006
    shell[12] = .025
    segment = NativeSurfaceMotionSegment(np.tile((.015, 0., -.002), (3, 1)),
        np.array(((.2, .1, -.05), (0., 0., 0.))), shell)
    field = _field(height=.08, segments=(segment,))
    assert _certify(field)


def test_target_affine_collapse_is_not_certified_from_valid_endpoints():
    field = _field(height=.08)
    corners = field.patch.target.adapter.current_positions(field.initial.shell_displacement)
    shell = np.zeros(18)
    for i in range(3):
        shell[6*i:6*i+2] = -2*corners[i, :2]
    segment = NativeSurfaceMotionSegment(np.zeros((3, 3)), np.zeros((2, 3)), shell)
    field = _field(height=.08, segments=(segment,))
    assert not _certify(field)


def test_support_checks_domain_binding_and_captured_path_cap():
    field = _field()
    with pytest.raises(ValueError, match='half-cell'):
        panel_open_over_history(field, 0, (-.8, .1), (4.7, 4.72), maximum_intervals=2)
    with pytest.raises(ValueError, match='interval cap'):
        _certify(field, maximum_intervals=0)
    segment = NativeSurfaceMotionSegment(np.zeros((3, 3)), np.array(((1., 0., 0.), (0., 0., 0.))), np.zeros(18))
    limited = _field(height=.031, segments=(segment,), maximum_intervals=1)
    assert not _certify(limited, maximum_intervals=256)
    field.patch.pairs[0].source.radius *= 1.01
    with pytest.raises(ValueError, match='definition changed'):
        _certify(field)


def test_shared_support_budget_is_not_reset_between_panels():
    zero = NativeSurfaceMotionSegment(np.zeros((3, 3)), np.zeros((2, 3)), np.zeros(18))
    field = _field(segments=(zero,))
    budget = SupportIntervalBudget(1)
    angles = field.patch.rule.definition['angle_range']
    assert panel_open_over_history(field, 0, (-.8, -.5), angles,
                                  maximum_intervals=256, budget=budget)
    assert budget.intervals == 1
    assert not panel_open_over_history(field, 0, (-.5, -.2), angles,
                                      maximum_intervals=256, budget=budget)
    assert budget.intervals == 1


def test_near_front_affine_slide_needs_only_one_interval():
    segment = NativeSurfaceMotionSegment(np.tile((.01, 0., 0.), (3, 1)),
                                        np.zeros((2, 3)), np.zeros(18))
    field = _field(height=.0300000001, segments=(segment,))
    budget = SupportIntervalBudget(1)
    assert panel_open_over_history(field, 0, (-.8, -.2),
        field.patch.rule.definition['angle_range'], maximum_intervals=1, budget=budget)
    assert budget.intervals == 1


def test_endpoint_support_admits_affine_spatially_varying_slopes():
    translations = np.zeros((3, 3))
    translations[0, 2] = -.03
    translations[1, 2] = .03
    segment = NativeSurfaceMotionSegment(translations, np.zeros((2, 3)), np.zeros(18))
    field = _field(segments=(segment,))
    # Some material points approach the plane and others recede; each has an
    # affine gap, so uniform whole-patch derivative sign is unnecessary.
    assert history_endpoint_support_certified(field)


def test_endpoint_support_admits_uniform_monotone_finite_rotation():
    segment = NativeSurfaceMotionSegment(np.tile((0., 0., -.02), (3, 1)),
        np.array(((.2, 0., 0.), (0., 0., 0.))), np.zeros(18))
    field = _field(height=.08, segments=(segment,))
    assert history_endpoint_support_certified(field)


def test_endpoint_support_rejects_hidden_pulse_and_target_collapse():
    pulse = NativeSurfaceMotionSegment(np.zeros((3, 3)),
        np.array(((1.6, 0., 0.), (0., 0., 0.))), np.zeros(18))
    field = _field(height=.025, rotation=-.8, segments=(pulse,))
    assert not history_endpoint_support_certified(field)
    flat = _field(height=.08)
    corners = flat.patch.target.adapter.current_positions(flat.initial.shell_displacement)
    shell = np.zeros(18)
    for i in range(3):
        shell[6*i:6*i+2] = -2*corners[i, :2]
    collapse = NativeSurfaceMotionSegment(np.zeros((3, 3)), np.zeros((2, 3)), shell)
    assert not history_endpoint_support_certified(_field(height=.08, segments=(collapse,)))
