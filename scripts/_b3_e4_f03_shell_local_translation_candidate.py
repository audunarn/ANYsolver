"""Bounded local-midsurface translation with the existing rail frame.

Only the shell-side pose origin changes: it is interpolated at (x=s, y=0)
instead of averaged over the four finite-width rail samples. The director
and in-plane proper-fit frame remain the existing verified candidate. This
is an exploratory line-pose alternative, not a selected production law.
"""

from __future__ import annotations

import numpy as np

from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    DirectionalPose, directional_pose_from_e4_total,
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_spatial_linear_port import reference_spatial_trace
from scripts._b3_e4_f03_shell_trace import ShellPanel


def local_weights(panel: ShellPanel, station: float) -> np.ndarray:
    """Reference Q4/S3 shape values at the actual material line station."""
    if not isinstance(panel, ShellPanel):
        raise TypeError("bounded shell panel required")
    if not np.isfinite(station) or not 0. <= station <= 1.:
        raise ValueError("finite line station in [0, 1] required")
    indices, values = panel._shape(float(station), 0.)
    result = np.zeros(panel.node_count)
    result[indices] = values
    return result


def pose_from_e4_total_local_translation(
        panel: ShellPanel, station: float,
        total_u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Use the local material point as origin and the existing physical frame."""
    _, frame = pose_from_e4_total(panel, station, total_u)
    positions = reference_nodes(panel)+np.asarray(total_u).reshape(-1, 6)[:, :3]
    return (local_weights(panel, station)@positions).copy(), frame


def directional_pose_from_e4_total_local_translation(
        panel: ShellPanel, station: float, total_u: np.ndarray,
        first: np.ndarray, second: np.ndarray) -> DirectionalPose:
    """Exact additive-coordinate derivatives of the local origin and frame."""
    rail = directional_pose_from_e4_total(
        panel, station, total_u, first, second)
    weights = local_weights(panel, station)
    first_values = np.asarray(first).reshape(-1, 6)
    second_values = np.asarray(second).reshape(-1, 6)
    return DirectionalPose(
        (weights@first_values[:, :3]).copy(),
        (weights@second_values[:, :3]).copy(),
        np.zeros(3), rail.frame_first, rail.frame_second,
        rail.frame_mixed)


def reference_spatial_trace_local_translation(
        panel: ShellPanel, station: float) -> np.ndarray:
    """Reference tangent matching this alternate finite pose exactly."""
    result = reference_spatial_trace(panel, station).copy()
    weights = local_weights(panel, station)
    for axis in range(3):
        result[axis, axis::6] = weights
    return result


def pose_from_e4_total_local_director(
        panel: ShellPanel, station: float,
        total_u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Alternative bonded-line pose with a director at the material point.

    The in-plane orientation still uses the declared four-sample proper fit.
    This is a bounded G0 diagnostic, not a selected connection law.
    """
    weights = local_weights(panel, station)
    _, frame = pose_from_e4_total(
        panel, station, total_u, _director_weights=weights)
    positions = reference_nodes(panel)+np.asarray(total_u).reshape(-1, 6)[:, :3]
    return (weights@positions).copy(), frame


def directional_pose_from_e4_total_local_director(
        panel: ShellPanel, station: float, total_u: np.ndarray,
        first: np.ndarray, second: np.ndarray) -> DirectionalPose:
    """First and mixed second variations of the local-director alternative."""
    weights = local_weights(panel, station)
    rail = directional_pose_from_e4_total(
        panel, station, total_u, first, second,
        _director_weights=weights)
    first_values = np.asarray(first).reshape(-1, 6)
    second_values = np.asarray(second).reshape(-1, 6)
    return DirectionalPose(
        (weights@first_values[:, :3]).copy(),
        (weights@second_values[:, :3]).copy(),
        np.zeros(3), rail.frame_first, rail.frame_second,
        rail.frame_mixed)


def reference_spatial_trace_local_director(
        panel: ShellPanel, station: float) -> np.ndarray:
    """Reference trace of the local material-point pose and director."""
    result = reference_spatial_trace_local_translation(panel, station)
    weights = local_weights(panel, station)
    result[3, 3::6] = weights
    result[4, 4::6] = weights
    return result
