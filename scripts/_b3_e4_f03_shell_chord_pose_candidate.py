"""Bounded zero-transverse-width shell-line pose with a fixed axial chord.

The origin and physical director are evaluated on the shell material line.
The in-plane heading comes from two positions on that same line, separated
by a declared physical gauge length. This is an exploratory nonlocal line
law, not the local polar-frame law or a selected production connection.
"""

from __future__ import annotations

import numpy as np

from anysolver import _ge_beam3_mixed_ad as ad
from anysolver.corotational import rotation_matrix_from_vector

from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    DirectionalPose, reference_nodes,
)
from scripts._b3_e4_f03_shell_trace import ShellPanel


HALF_CHORD = .2


def _weights(panel: ShellPanel, station: float, half_chord: float
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if (not isinstance(panel, ShellPanel) or
            panel.topology not in ("Q4", "S3-V2D") or
            not np.isfinite(station) or not 0. <= station <= 1. or
            not np.isfinite(half_chord) or
            not .05 <= half_chord <= .25):
        raise ValueError("bounded fixed shell-line chord required")
    reference_nodes(panel)
    rows = []
    for x in (station, station-half_chord, station+half_chord):
        indices, values = panel._shape(x, 0.)
        row = np.zeros(panel.node_count)
        row[indices] = values
        if abs(float(np.sum(row))-1.) > 2e-12:
            raise ArithmeticError("incomplete line-trace interpolation")
        rows.append(row)
    return tuple(rows)


def reference_spatial_trace_chord(
        panel: ShellPanel, station: float, *,
        half_chord: float = HALF_CHORD) -> np.ndarray:
    """Six physical pose variations at a flat reference configuration."""
    center, minus, plus = _weights(panel, station, half_chord)
    result = np.zeros((6, 6*panel.node_count))
    for axis in range(3):
        result[axis, axis::6] = center
    result[3, 3::6] = center
    result[4, 4::6] = center
    result[5, 1::6] = (plus-minus)/(2*half_chord)
    return result


def _numeric_pose(panel: ShellPanel, station: float, total_u: np.ndarray,
                  half_chord: float) -> tuple[np.ndarray, np.ndarray]:
    center, minus, plus = _weights(panel, station, half_chord)
    reference = reference_nodes(panel)
    values = np.asarray(total_u, dtype=float)
    if values.shape != (6*panel.node_count,) or not np.isfinite(values).all():
        raise ValueError("finite complete flat E4 total coordinates required")
    nodal = values.reshape(-1, 6)
    positions = reference+nodal[:, :3]
    directors = np.array([rotation_matrix_from_vector(theta)[:, 2]
                          for theta in nodal[:, 3:]])
    director = center@directors
    dn = float(np.linalg.norm(director))
    if not np.isfinite(dn) or dn <= 1e-8:
        raise ValueError("cancelled shell-line director")
    director /= dn
    tangent = (plus-minus)@positions
    x = tangent-director*float(director@tangent)
    xn = float(np.linalg.norm(x))
    if not np.isfinite(xn) or xn <= 1e-8*half_chord:
        raise ValueError("degenerate projected shell-line chord")
    x /= xn
    y = np.cross(director, x)
    frame = np.column_stack((x, y, director))
    if (not np.isfinite(frame).all() or
            np.linalg.norm(frame.T@frame-np.eye(3)) > 2e-12 or
            np.linalg.det(frame) <= 0.):
        raise ValueError("invalid shell-line spatial frame")
    return (center@positions).copy(), frame.copy()


def pose_from_e4_total_chord(
        panel: ShellPanel, station: float, total_u: np.ndarray, *,
        half_chord: float = HALF_CHORD) -> tuple[np.ndarray, np.ndarray]:
    """Finite material-line pose through the actual flat E4 chart."""
    return _numeric_pose(panel, station, total_u, half_chord)


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0]]


def directional_pose_from_e4_total_chord(
        panel: ShellPanel, station: float, total_u: np.ndarray,
        first: np.ndarray, second: np.ndarray, *,
        half_chord: float = HALF_CHORD) -> DirectionalPose:
    """Owned first/mixed-second variations through additive E4 rotations."""
    center, minus, plus = _weights(panel, station, half_chord)
    base = np.asarray(total_u, dtype=float)
    u = np.asarray(first, dtype=float)
    v = np.asarray(second, dtype=float)
    shape = (panel.node_count, 6)
    if (base.shape != (6*panel.node_count,) or
            u.shape != shape or v.shape != shape or
            not all(np.isfinite(a).all() for a in (base, u, v))):
        raise ValueError("finite complete E4 state and two directions required")
    reference = reference_nodes(panel)
    numeric_position, numeric_frame = _numeric_pose(
        panel, station, base, half_chord)
    base = base.reshape(shape)
    epsilon = ad.Jet2.variable(0., 0, 2)
    eta = ad.Jet2.variable(0., 1, 2)
    zero = ad.Jet2.constant(0., 2)
    nodes, directors = [], []
    for index in range(panel.node_count):
        nodes.append([
            ad.Jet2.constant(reference[index, axis]+base[index, axis], 2)+
            epsilon*u[index, axis]+eta*v[index, axis]
            for axis in range(3)])
        spin = [ad.Jet2.constant(base[index, axis+3], 2)+
                epsilon*u[index, axis+3]+eta*v[index, axis+3]
                for axis in range(3)]
        directors.append(ad.matvec(ad.so3_exp(spin), [zero, zero, 1.+zero]))

    def weighted(weights, vectors):
        return [sum((weights[i]*vectors[i][axis]
                     for i in range(panel.node_count)), zero)
                for axis in range(3)]

    position = weighted(center, nodes)
    director_sum = weighted(center, directors)
    director = [entry/ad.sqrt(ad.dot(director_sum, director_sum))
                for entry in director_sum]
    chord_weights = plus-minus
    chord = weighted(chord_weights, nodes)
    projection = ad.dot(director, chord)
    x0 = [chord[i]-projection*director[i] for i in range(3)]
    norm = ad.sqrt(ad.dot(x0, x0))
    x = [entry/norm for entry in x0]
    y = _cross(director, x)
    frame = [[x[i], y[i], director[i]] for i in range(3)]
    if (np.max(np.abs(np.array([entry.value for entry in position])-
                      numeric_position)) > 1e-11 or
            np.max(np.abs(np.array([[entry.value for entry in row]
                                    for row in frame])-numeric_frame)) > 1e-11):
        raise AssertionError("shell-line pose and derivative charts disagree")

    def vector_gradient(axis):
        return np.array([entry.gradient[axis] for entry in position])

    def matrix_gradient(axis):
        return np.array([[entry.gradient[axis] for entry in row]
                         for row in frame])

    return DirectionalPose(
        vector_gradient(0), vector_gradient(1),
        np.array([entry.hessian[0, 1] for entry in position]),
        matrix_gradient(0), matrix_gradient(1),
        np.array([[entry.hessian[0, 1] for entry in row]
                  for row in frame]))
