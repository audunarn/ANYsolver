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


def local_material_gradient_weights(
        panel: ShellPanel, station: float) -> np.ndarray:
    """One-sided physical x/y derivatives in the deterministic line host.

    Q4 and S3 fields are C0, so their derivatives need not agree across an
    element edge. This returns the host selected by ``ShellPanel._shape``;
    weak-line integration must split at every center-line host boundary.
    """
    local_weights(panel, station)  # Validate panel, station, and center host.
    dx, dy = 1./panel.n_s, 1./panel.n_y
    i = int(np.clip(np.ceil((station+.5)/dx)-1, 0,
                    panel.x_interval_count-1))
    j = int(np.clip(np.ceil(.5/dy)-1, 0, panel.n_y-1))
    xi = (station-(-.5+i*dx))/dx
    eta = (.5-j*dy)/dy
    indices, _ = panel._shape(float(station), 0.)
    if panel.topology == "Q4":
        dxi = np.array((-(1-eta), 1-eta, eta, -eta))
        deta = np.array((-(1-xi), -xi, xi, 1-xi))
    elif eta <= xi:
        dxi = np.array((-1., 1., 0.))
        deta = np.array((0., -1., 1.))
    else:
        dxi = np.array((0., 1., -1.))
        deta = np.array((-1., 0., 1.))
    result = np.zeros((2, panel.node_count))
    result[0, indices] = dxi/dx
    result[1, indices] = deta/dy
    return result


def reference_spatial_trace_local_frame(
        panel: ShellPanel, station: float) -> np.ndarray:
    """Flat-reference local director plus local polar material yaw candidate.

    The yaw is half the in-plane displacement curl. It has no drilling
    column. This bounded operator is not yet a qualified finite pose.
    """
    result = reference_spatial_trace_local_director(panel, station)
    gradient = local_material_gradient_weights(panel, station)
    result[5, 0::6] = -.5*gradient[1]
    result[5, 1::6] = .5*gradient[0]
    return result


def pose_from_e4_total_local_frame(
        panel: ShellPanel, station: float,
        total_u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Finite local material point, physical director and polar tangent frame.

    The tangents are piecewise element gradients. A line integral using this
    candidate must split at their reference host boundaries. This is a G0
    diagnostic, not a selected production shell/beam connection.
    """
    weights = local_weights(panel, station)
    gradients = local_material_gradient_weights(panel, station)
    return pose_from_e4_total(
        panel, station, total_u,
        _origin_weights=weights,
        _director_weights=weights,
        _planar_weights=gradients)


def directional_pose_from_e4_total_local_frame(
        panel: ShellPanel, station: float, total_u: np.ndarray,
        first: np.ndarray, second: np.ndarray) -> DirectionalPose:
    """Owned first and mixed second derivatives of the local finite frame."""
    weights = local_weights(panel, station)
    gradients = local_material_gradient_weights(panel, station)
    return directional_pose_from_e4_total(
        panel, station, total_u, first, second,
        _origin_weights=weights,
        _director_weights=weights,
        _planar_weights=gradients)
