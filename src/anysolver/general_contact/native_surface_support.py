"""Conservative separation test for an entire straight material panel.

Spatial minima are analytic, not sampled. A uniform temporal Lipschitz bound
encloses every material point between inspected poses. False means contact or
unresolved separation; it does not prove that contact occurred. This is not a
replacement for source-orientation, target-ownership or history admission.
"""
from dataclasses import dataclass
from fractions import Fraction
from math import atan2, cos, fsum, pi, sin

import numpy as np

from anysolver._ge_beam3_p5_seeded.core import sha
from .native_surface_history import NativeSurfaceHistoryField
from .native_surface_path import material_path_pose


@dataclass
class SupportIntervalBudget:
    """Shared temporal-interval cap across an integration's support queries."""
    maximum_intervals: int
    intervals: int = 0

    def __post_init__(self):
        if type(self.maximum_intervals) is not int or self.maximum_intervals < 1:
            raise ValueError('positive shared support interval cap required')
        if type(self.intervals) is not int or self.intervals != 0:
            raise ValueError('new shared support budget must start at zero')

    def consume(self):
        if self.intervals >= self.maximum_intervals:
            return False
        self.intervals += 1
        return True


def _base(pose, cell, xi, origin):
    t = xi+1. if cell == 0 else xi
    return np.array([fsum(((1-t)*float(pose.positions[cell, i]),
                           (1-t)*float(pose.position_low[cell, i]),
                           t*float(pose.positions[cell+1, i]),
                           t*float(pose.position_low[cell+1, i]),
                           -float(origin[i]))) for i in range(3)])


def _minimum(pose, target, reference_frame, radius, cell, xis, angles):
    corners = target.adapter.current_positions(pose.shell_displacement)
    normal = np.asarray(target.physical_pose(pose.shell_displacement).material_frame)[:, 2]
    frame = pose.cell_rotations[cell] @ reference_frame
    a = radius*float(normal @ frame[:, 1])
    b = radius*float(normal @ frame[:, 2])
    phase = atan2(b, a)
    candidates = [*angles, *(phase+k*pi for k in range(-2, 5)
                              if angles[0] <= phase+k*pi <= angles[1])]
    values = [fsum((float(normal @ _base(pose, cell, xi, corners[0])),
                    a*cos(angle), b*sin(angle)))
              for xi in xis for angle in candidates]
    scale = max(1., radius, float(np.max(np.abs(pose.positions))),
                float(np.max(np.abs(pose.position_low))), float(np.max(np.abs(corners))))
    return min(values), 512*np.finfo(float).eps*scale


def panel_open_over_history(field, cell, xi_bounds, angle_bounds, *, maximum_intervals,
                            budget=None):
    """True only for whole-panel positive gap over the initial pose and history.

    The interval cap is shared by all segments. Each segment also retains the
    history field's captured per-path cap. An optional budget additionally shares
    that work limit across multiple calls. Target cross-product Bernstein bounds
    retain its orientation/area guard. Unresolved area or temporal bounds return
    False; malformed inputs and encountered invalid target geometry raise.
    """
    if type(field) is not NativeSurfaceHistoryField:
        raise TypeError('exact native surface history field required')
    if type(cell) is not int or cell not in (0, 1):
        raise ValueError('one native half-cell required')
    if type(maximum_intervals) is not int or maximum_intervals < 1:
        raise ValueError('positive aggregate support interval cap required')
    if budget is not None and type(budget) is not SupportIntervalBudget:
        raise TypeError('exact shared support interval budget required')
    if sha(field._definition()) != field.identity:
        raise ValueError('native material history field definition changed')
    xis = np.asarray(xi_bounds, dtype=float)
    angles = np.asarray(angle_bounds, dtype=float)
    rule = field.patch.rule
    for values, patch_bounds, domain in ((xis, rule.definition['xi_range'], (-1.+cell, float(cell))),
                                         (angles, rule.definition['angle_range'], (0., 2*pi))):
        if (values.shape != (2,) or not np.all(np.isfinite(values))
                or not max(domain[0], patch_bounds[0]) <= values[0] < values[1] <= min(domain[1], patch_bounds[1])):
            raise ValueError('support rectangle must lie in one declared material half-cell')
    reference = field.patch.source.reference
    coordinates, frames = reference.coordinates, reference.nodal_triads
    if (any(Fraction(float(coordinates[0, i]))+Fraction(float(coordinates[2, i]))
            != 2*Fraction(float(coordinates[1, i])) for i in range(3))
            or not np.array_equal(frames, np.tile(frames[0], (3, 1, 1)))):
        raise ValueError('material support requires exact straight untwisted reference')
    target = field.patch.target
    radius = float(rule.definition['radius'])
    pose = field.initial
    minimum, padding = _minimum(pose, target, frames[0], radius, cell, xis, angles)
    if minimum <= padding:
        return False
    reference_corners = target.adapter.reference_positions
    reference_cross = np.cross(reference_corners[1]-reference_corners[0],
                               reference_corners[2]-reference_corners[0])
    reference_area = float(np.linalg.norm(reference_cross))
    reference_normal = reference_cross/reference_area
    visited = 0
    for segment in field.segments:
        end = material_path_pose(pose, segment.translations, segment.angular, segment.shell_increment, 1.)
        first = target.adapter.current_positions(pose.shell_displacement)
        last = target.adapter.current_positions(end.shell_displacement)
        # Also validates endpoint target degeneracy and the existing polarity.
        endpoint_minimum, endpoint_padding = _minimum(end, target, frames[0], radius, cell, xis, angles)
        if endpoint_minimum <= endpoint_padding:
            return False
        a0, b0 = first[1]-first[0], first[2]-first[0]
        a1, b1 = last[1]-last[0], last[2]-last[0]
        cross_controls = (np.cross(a0, b0),
                          .5*(np.cross(a0, b1)+np.cross(a1, b0)), np.cross(a1, b1))
        area_lower = min(float(reference_normal @ c) for c in cross_controls)
        area_scale = max(reference_area, max(np.linalg.norm(a0), np.linalg.norm(a1))
                         *max(np.linalg.norm(b0), np.linalg.norm(b1)))
        if area_lower <= 1e-12*area_scale:
            return False
        target_increments = np.asarray(target.adapter.work_map @ segment.shell_increment).reshape(3, 3)
        if (not np.any(segment.angular[cell])
                and np.array_equal(target_increments, np.tile(target_increments[0], (3, 1)))):
            # Every fixed material point has an affine gap. Positive exact
            # whole-panel endpoint minima cover the entire segment, regardless
            # of tangential travel. Charge one interval to both work budgets.
            if visited >= maximum_intervals:
                return False
            if budget is not None and not budget.consume():
                return False
            visited += 1
            pose = end
            padding = endpoint_padding
            continue
        normal_speed = (np.linalg.norm(a1-a0)*max(np.linalg.norm(b0), np.linalg.norm(b1))
                        +np.linalg.norm(b1-b0)*max(np.linalg.norm(a0), np.linalg.norm(a1)))/area_lower
        # Relative affine base is bilinear in (xi,time), hence lies in the
        # convex hull of these four corners. Adding the section radius bounds
        # all material surface points, including angular extrema not sampled.
        relative_radius = max(np.linalg.norm(_base(p, cell, xi, corner))
                              for p, corner in ((pose, first[0]), (end, last[0]))
                              for xi in xis)+radius
        target_motion = target_increments[0]
        velocities = []
        for xi in xis:
            t = xi+1. if cell == 0 else xi
            velocities.append((1-t)*segment.translations[cell]+t*segment.translations[cell+1]-target_motion)
        speed = max(np.linalg.norm(v) for v in velocities)+np.linalg.norm(segment.angular[cell])*radius
        rate = float(speed+normal_speed*relative_radius)
        if not np.isfinite(rate):
            raise ValueError('nonfinite whole-panel support rate')
        pending = [(0., 1.)]
        segment_visits = 0
        while pending:
            if visited >= maximum_intervals or segment_visits >= field.maximum_intervals:
                return False
            left, right = pending.pop()
            midpoint = left+(right-left)/2.
            if midpoint == left or midpoint == right:
                return False
            if budget is not None and not budget.consume():
                return False
            current = material_path_pose(pose, segment.translations, segment.angular,
                                         segment.shell_increment, midpoint)
            value, roundoff = _minimum(current, target, frames[0], radius, cell, xis, angles)
            visited += 1
            segment_visits += 1
            if value <= roundoff:
                return False
            if value-rate*(right-left)/2. > max(roundoff, padding, endpoint_padding):
                continue
            pending.extend(((left, midpoint), (midpoint, right)))
        pose = end
        padding = endpoint_padding
    return True


def _sinusoidal_extrema(offsets, a, b, angles):
    """Exact extrema of affine-xi + a*cos(angle)+b*sin(angle)."""
    phase = atan2(b, a)
    candidates = [*angles, *(phase+k*pi for k in range(-2, 5)
                              if angles[0] <= phase+k*pi <= angles[1])]
    values = [fsum((offset, a*cos(angle), b*sin(angle)))
              for offset in offsets for angle in candidates]
    return min(values), max(values)


def history_endpoint_support_certified(field):
    """Sufficient whole-patch proof that contact cannot hide between poses.

    Every point's gap must be affine in time, or have a derivative of one
    rigorously bounded sign on each segment. Different segments may have
    different signs. This does not certify spatial quadrature accuracy or
    resolve stick/slip fronts inside the endpoint-supported contact region.
    """
    if type(field) is not NativeSurfaceHistoryField:
        raise TypeError('exact native surface history field required')
    if sha(field._definition()) != field.identity:
        raise ValueError('native material history field definition changed')
    rule = field.patch.rule
    reference = field.patch.source.reference
    coordinates, frames = reference.coordinates, reference.nodal_triads
    if (any(Fraction(float(coordinates[0, i]))+Fraction(float(coordinates[2, i]))
            != 2*Fraction(float(coordinates[1, i])) for i in range(3))
            or not np.array_equal(frames, np.tile(frames[0], (3, 1, 1)))):
        raise ValueError('material support requires exact straight untwisted reference')
    target = field.patch.target
    radius = float(rule.definition['radius'])
    lo, hi = rule.definition['xi_range']
    angles = rule.definition['angle_range']
    cells = [(c, (l, r)) for c, l, r in
             ((0, max(lo, -1.), min(hi, 0.)), (1, max(lo, 0.), min(hi, 1.))) if r > l]
    reference_corners = target.adapter.reference_positions
    reference_cross = np.cross(reference_corners[1]-reference_corners[0],
                               reference_corners[2]-reference_corners[0])
    reference_area = float(np.linalg.norm(reference_cross))
    reference_normal = reference_cross/reference_area
    pose = field.initial
    target.physical_pose(pose.shell_displacement)
    for segment in field.segments:
        end = material_path_pose(pose, segment.translations, segment.angular, segment.shell_increment, 1.)
        target.physical_pose(end.shell_displacement)
        first = target.adapter.current_positions(pose.shell_displacement)
        last = target.adapter.current_positions(end.shell_displacement)
        a0, b0 = first[1]-first[0], first[2]-first[0]
        a1, b1 = last[1]-last[0], last[2]-last[0]
        c0, c2 = np.cross(a0, b0), np.cross(a1, b1)
        c1 = .5*(np.cross(a0, b1)+np.cross(a1, b0))
        area_lower = min(float(reference_normal @ c) for c in (c0, c1, c2))
        area_scale = max(reference_area, max(np.linalg.norm(a0), np.linalg.norm(a1))
                         *max(np.linalg.norm(b0), np.linalg.norm(b1)))
        if area_lower <= 1e-12*area_scale:
            return False
        target_motion = np.asarray(target.adapter.work_map @ segment.shell_increment).reshape(3, 3)
        if (not np.any(segment.angular)
                and np.array_equal(target_motion, np.tile(target_motion[0], (3, 1)))):
            # For each fixed material coordinate the gap is affine. Its slope
            # may change sign across the patch, which is harmless to this proof.
            pose = end
            continue
        da, db = a1-a0, b1-b0
        cp0 = np.cross(da, b0)+np.cross(a0, db)
        cp1 = np.cross(da, b1)+np.cross(a1, db)
        cross_speed = max(np.linalg.norm(cp0), np.linalg.norm(cp1))
        normal_speed = cross_speed/area_lower
        normal_acceleration = (2*np.linalg.norm(np.cross(da, db))/area_lower
                               +3*(cross_speed/area_lower)**2)
        normal0 = c0/np.linalg.norm(c0)
        normal_derivative = (cp0-normal0*float(normal0 @ cp0))/np.linalg.norm(c0)
        for cell, xis in cells:
            omega = segment.angular[cell]
            frame = pose.cell_rotations[cell] @ frames[0]
            velocities = []
            offsets = []
            for xi in xis:
                t = xi+1. if cell == 0 else xi
                velocity = ((1-t)*segment.translations[cell]+t*segment.translations[cell+1]
                            -target_motion[0])
                velocities.append(velocity)
                offsets.append(float(normal_derivative @ _base(pose, cell, xi, first[0])
                                     +normal0 @ velocity))
            a = radius*float(normal_derivative @ frame[:, 1]
                             +normal0 @ np.cross(omega, frame[:, 1]))
            b = radius*float(normal_derivative @ frame[:, 2]
                             +normal0 @ np.cross(omega, frame[:, 2]))
            derivative_min, derivative_max = _sinusoidal_extrema(offsets, a, b, angles)
            relative_radius = max(np.linalg.norm(_base(p, cell, xi, corner))
                                  for p, corner in ((pose, first[0]), (end, last[0]))
                                  for xi in xis)+radius
            speed = max(np.linalg.norm(v) for v in velocities)+np.linalg.norm(omega)*radius
            curvature = (normal_acceleration*relative_radius+2*normal_speed*speed
                         +np.linalg.norm(omega)**2*radius)
            padding = 512*np.finfo(float).eps*max(1., relative_radius, speed, curvature,
                                                  abs(derivative_min), abs(derivative_max))
            if not np.all(np.isfinite((derivative_min, derivative_max, curvature, padding))):
                raise ValueError('nonfinite endpoint support derivative bound')
            if not (derivative_min-curvature > padding or derivative_max+curvature < -padding):
                return False
        pose = end
    return True


def history_target_ownership_certified(field, *, budget):
    """Prove the whole straight patch stays inside its S3 target over history.

    Three inward edge-plane minima are exact in both material coordinates.
    Temporal interval bounds cover every point, not only integration nodes.
    Source orientation remains a separate required admission check.
    """
    if type(field) is not NativeSurfaceHistoryField:
        raise TypeError('exact native surface history field required')
    if type(budget) is not SupportIntervalBudget:
        raise TypeError('exact shared support interval budget required')
    if sha(field._definition()) != field.identity:
        raise ValueError('native material history field definition changed')
    rule = field.patch.rule
    reference = field.patch.source.reference
    coordinates, frames = reference.coordinates, reference.nodal_triads
    if (any(Fraction(float(coordinates[0, i]))+Fraction(float(coordinates[2, i]))
            != 2*Fraction(float(coordinates[1, i])) for i in range(3))
            or not np.array_equal(frames, np.tile(frames[0], (3, 1, 1)))):
        raise ValueError('material support requires exact straight untwisted reference')
    target = field.patch.target
    radius = float(rule.definition['radius'])
    lo, hi = rule.definition['xi_range']
    angles = rule.definition['angle_range']
    cells = [(c, (l, r)) for c, l, r in
             ((0, max(lo, -1.), min(hi, 0.)), (1, max(lo, 0.), min(hi, 1.))) if r > l]
    reference_corners = target.adapter.reference_positions
    reference_cross = np.cross(reference_corners[1]-reference_corners[0],
                               reference_corners[2]-reference_corners[0])
    reference_area = float(np.linalg.norm(reference_cross))
    reference_normal = reference_cross/reference_area

    def margins(pose, clearance):
        corners = target.adapter.current_positions(pose.shell_displacement)
        normal = np.asarray(target.physical_pose(pose.shell_displacement).material_frame)[:, 2]
        values = []
        for cell, xis in cells:
            frame = pose.cell_rotations[cell] @ frames[0]
            for i in range(3):
                edge = corners[(i+1)%3]-corners[i]
                inward = np.cross(normal, edge/np.linalg.norm(edge))
                offsets = [float(inward @ _base(pose, cell, xi, corners[i])) for xi in xis]
                a, b = radius*float(inward @ frame[:, 1]), radius*float(inward @ frame[:, 2])
                minimum, _ = _sinusoidal_extrema(offsets, a, b, angles)
                values.append(minimum-clearance)
        scale = max(1., radius, float(np.max(np.abs(pose.positions))),
                    float(np.max(np.abs(pose.position_low))), float(np.max(np.abs(corners))))
        return np.asarray(values), 512*np.finfo(float).eps*scale

    pose = field.initial
    first = target.adapter.current_positions(pose.shell_displacement)
    initial_clearance = 1e-12*max(np.linalg.norm(first[(i+1)%3]-first[i]) for i in range(3))
    initial_values, initial_padding = margins(pose, initial_clearance)
    if np.min(initial_values) <= initial_padding:
        return False
    for segment in field.segments:
        end = material_path_pose(pose, segment.translations, segment.angular, segment.shell_increment, 1.)
        last = target.adapter.current_positions(end.shell_displacement)
        clearance = 1e-12*max(np.linalg.norm(corners[(i+1)%3]-corners[i])
                              for corners in (first, last) for i in range(3))
        first_values, first_padding = margins(pose, clearance)
        last_values, last_padding = margins(end, clearance)
        if min(np.min(first_values)-first_padding, np.min(last_values)-last_padding) <= 0.:
            return False
        a0, b0 = first[1]-first[0], first[2]-first[0]
        a1, b1 = last[1]-last[0], last[2]-last[0]
        controls = (np.cross(a0, b0), .5*(np.cross(a0, b1)+np.cross(a1, b0)), np.cross(a1, b1))
        area_lower = min(float(reference_normal @ c) for c in controls)
        area_scale = max(reference_area, max(np.linalg.norm(a0), np.linalg.norm(a1))
                         *max(np.linalg.norm(b0), np.linalg.norm(b1)))
        if area_lower <= 1e-12*area_scale:
            return False
        target_motion = np.asarray(target.adapter.work_map @ segment.shell_increment).reshape(3, 3)
        if (not np.any(segment.angular)
                and np.array_equal(target_motion, np.tile(target_motion[0], (3, 1)))):
            # All inward planes translate without changing direction; every
            # material point's edge distance is affine along the segment.
            if not budget.consume():
                return False
            pose, first = end, last
            continue
        normal_speed = (np.linalg.norm(a1-a0)*max(np.linalg.norm(b0), np.linalg.norm(b1))
                        +np.linalg.norm(b1-b0)*max(np.linalg.norm(a0), np.linalg.norm(a1)))/area_lower
        inward_rates = []
        for i in range(3):
            edge = first[(i+1)%3]-first[i]
            change = (last[(i+1)%3]-last[i])-edge
            denominator = float(change @ change)
            alpha = 0. if denominator == 0. else float(np.clip(-float(edge @ change)/denominator, 0., 1.))
            edge_lower = float(np.linalg.norm(edge+alpha*change))
            if edge_lower <= 0.:
                return False
            inward_rates.append(normal_speed+np.linalg.norm(change)/edge_lower)
        rates = []
        for cell, xis in cells:
            for i in range(3):
                relative_radius = max(np.linalg.norm(_base(p, cell, xi, corner))
                                      for p, corner in ((pose, first[i]), (end, last[i]))
                                      for xi in xis)+radius
                speeds = []
                for xi in xis:
                    t = xi+1. if cell == 0 else xi
                    speeds.append(np.linalg.norm((1-t)*segment.translations[cell]
                                  +t*segment.translations[cell+1]-target_motion[i]))
                relative_speed = max(speeds)+np.linalg.norm(segment.angular[cell])*radius
                rates.append(relative_speed+inward_rates[i]*relative_radius)
        rates = np.asarray(rates)
        if not np.all(np.isfinite(rates)):
            raise ValueError('nonfinite swept target ownership rate')
        pending = [(0., 1.)]
        segment_visits = 0
        while pending:
            if segment_visits >= field.maximum_intervals:
                return False
            left, right = pending.pop()
            midpoint = left+(right-left)/2.
            if midpoint == left or midpoint == right or not budget.consume():
                return False
            current = material_path_pose(pose, segment.translations, segment.angular,
                                         segment.shell_increment, midpoint)
            values, padding = margins(current, clearance)
            segment_visits += 1
            if np.min(values) <= padding:
                return False
            if np.all(values-rates*(right-left)/2. > max(padding, first_padding, last_padding)):
                continue
            pending.extend(((left, midpoint), (midpoint, right)))
        pose, first = end, last
    return True
