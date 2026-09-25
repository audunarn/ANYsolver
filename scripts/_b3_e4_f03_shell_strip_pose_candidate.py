"""Bounded physical-area shell pose for an explicitly finite material strip.

This G0 candidate averages position, physical director and deformation
gradient over one fixed rectangle centered at a beam station. Its support
does not shrink with mesh size. It is a finite-width connection, not a
zero-width bonded-line trace or a selected production footprint.
"""

from __future__ import annotations

import numpy as np

from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    DirectionalPose, directional_pose_from_e4_total, pose_from_e4_total,
    reference_nodes,
)
from scripts._b3_e4_f03_shell_trace import ShellPanel


STRIP_PORTS = {
    "physical_strip_020_023": (.2, .23),
    "physical_strip_005_005": (.05, .05),
}


def _clip(polygon: list[np.ndarray], axis: int, bound: float,
          sign: int) -> list[np.ndarray]:
    """Clip one CCW host polygon by sign*(coordinate-bound)>=0."""
    if not polygon:
        return []
    result = []
    prior = polygon[-1]
    prior_side = sign*(prior[axis]-bound)
    for current in polygon:
        current_side = sign*(current[axis]-bound)
        if (prior_side >= 0.) != (current_side >= 0.):
            factor = prior_side/(prior_side-current_side)
            result.append(prior+factor*(current-prior))
        if current_side >= 0.:
            result.append(current)
        prior, prior_side = current, current_side
    return result


def _quadrature(polygon: list[np.ndarray]):
    """Degree-three exact integration on a clipped convex polygon."""
    for index in range(1, len(polygon)-1):
        a, b, c = polygon[0], polygon[index], polygon[index+1]
        area = .5*abs(float(np.linalg.det(np.column_stack((b-a, c-a)))))
        if area <= 0.:
            continue
        for coefficient, barycentric in (
                (-27/48, (1/3, 1/3, 1/3)),
                (25/48, (3/5, 1/5, 1/5)),
                (25/48, (1/5, 3/5, 1/5)),
                (25/48, (1/5, 1/5, 3/5))):
            yield area*coefficient, (
                barycentric[0]*a+barycentric[1]*b+barycentric[2]*c)


def _shape_gradient(panel: ShellPanel, x: float, y: float
                    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Exact Q4/S3 host shape and reference x/y derivatives."""
    dx, dy = 1./panel.n_s, 1./panel.n_y
    nx = panel.x_interval_count
    i = int(np.clip(np.ceil((x+.5)/dx)-1, 0, nx-1))
    j = int(np.clip(np.ceil((y+.5)/dy)-1, 0, panel.n_y-1))
    xi = (x-(-.5+i*dx))/dx
    eta = (y-(-.5+j*dy))/dy
    nodes, values = panel._shape(x, y)
    if panel.topology == "Q4":
        dxi = np.array((-(1-eta), 1-eta, eta, -eta))
        deta = np.array((-(1-xi), -xi, xi, 1-xi))
    elif eta <= xi:
        dxi = np.array((-1., 1., 0.))
        deta = np.array((0., -1., 1.))
    else:
        dxi = np.array((0., 1., -1.))
        deta = np.array((-1., 0., 1.))
    return nodes, values, np.stack((dxi/dx, deta/dy))


def strip_weights(panel: ShellPanel, station: float, *,
                  half_length: float, half_width: float
                  ) -> tuple[np.ndarray, np.ndarray]:
    """Area-mean shape row and two mean material-gradient rows.

    Host polygons are clipped before exact Q4/S3 integration, including S3
    diagonals. The gradient mean equals a boundary-displacement functional
    by the divergence theorem and is bounded by H1 energy at fixed area.
    """
    if (not isinstance(panel, ShellPanel) or
            panel.topology not in ("Q4", "S3-V2D") or
            not np.isfinite(station) or not 0. <= station <= 1. or
            not np.isfinite(half_length) or
            not np.isfinite(half_width) or
            not .05 <= half_length <= .25 or
            not .05 <= half_width <= .25):
        raise ValueError("bounded finite material strip required")
    x0, x1 = station-half_length, station+half_length
    y0, y1 = -half_width, half_width
    if x0 < -.5 or x1 > 1.5 or y0 < -.5 or y1 > .5:
        raise ValueError("strip leaves selected reference panel")
    nx = panel.x_interval_count
    x_grid = np.linspace(-.5, 1.5, nx+1)
    y_grid = np.linspace(-.5, .5, panel.n_y+1)
    mean = np.zeros(panel.node_count)
    gradients = np.zeros((2, panel.node_count))
    covered = 0.
    for j in range(panel.n_y):
        if y_grid[j] >= y1 or y_grid[j+1] <= y0:
            continue
        for i in range(nx):
            if x_grid[i] >= x1 or x_grid[i+1] <= x0:
                continue
            a = np.array((x_grid[i], y_grid[j]))
            b = np.array((x_grid[i+1], y_grid[j]))
            c = np.array((x_grid[i+1], y_grid[j+1]))
            d = np.array((x_grid[i], y_grid[j+1]))
            hosts = ([a, b, c, d],) if panel.topology == "Q4" else (
                [a, b, c], [a, c, d])
            for host in hosts:
                polygon = host
                for axis, bound, sign in ((0, x0, 1), (0, x1, -1),
                                          (1, y0, 1), (1, y1, -1)):
                    polygon = _clip(polygon, axis, bound, sign)
                for weight, point in _quadrature(polygon):
                    indices, values, derivatives = _shape_gradient(
                        panel, float(point[0]), float(point[1]))
                    mean[indices] += weight*values
                    gradients[:, indices] += weight*derivatives
                    covered += weight
    area = 4*half_length*half_width
    if abs(covered-area) > 2e-10*area:
        raise ArithmeticError("strip host area incomplete or overlapping")
    mean /= area
    gradients /= area
    nodes = reference_nodes(panel)
    reference_gradient = gradients@nodes[:, :2]
    if (abs(float(np.sum(mean))-1.) > 2e-11 or
            np.linalg.norm(gradients@np.ones(panel.node_count)) > 2e-11 or
            np.linalg.norm(reference_gradient-np.eye(2)) > 2e-11):
        raise ArithmeticError("strip reference partition or gradient failed")
    return mean, gradients


def reference_spatial_trace_strip(
        panel: ShellPanel, station: float, *,
        half_length: float, half_width: float) -> np.ndarray:
    """Flat-reference six-channel strip trace with physical polar yaw."""
    mean, gradients = strip_weights(
        panel, station, half_length=half_length, half_width=half_width)
    result = np.zeros((6, 6*panel.node_count))
    for axis in range(3):
        result[axis, axis::6] = mean
    result[3, 3::6] = mean
    result[4, 4::6] = mean
    result[5, 0::6] = -.5*gradients[1]
    result[5, 1::6] = .5*gradients[0]
    return result


def pose_from_e4_total_strip(
        panel: ShellPanel, station: float, total_u: np.ndarray, *,
        half_length: float, half_width: float
        ) -> tuple[np.ndarray, np.ndarray]:
    """Finite material-strip pose through the actual flat E4 chart."""
    mean, gradients = strip_weights(
        panel, station, half_length=half_length, half_width=half_width)
    return pose_from_e4_total(
        panel, station, total_u, _origin_weights=mean,
        _director_weights=mean, _planar_weights=gradients)


def directional_pose_from_e4_total_strip(
        panel: ShellPanel, station: float, total_u: np.ndarray,
        first: np.ndarray, second: np.ndarray, *,
        half_length: float, half_width: float) -> DirectionalPose:
    """Owned first/mixed-second strip derivatives in the actual E4 chart."""
    mean, gradients = strip_weights(
        panel, station, half_length=half_length, half_width=half_width)
    return directional_pose_from_e4_total(
        panel, station, total_u, first, second,
        _origin_weights=mean, _director_weights=mean,
        _planar_weights=gradients)
