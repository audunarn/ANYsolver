"""Private G0 material-line pose feasibility on E4 and retained B3 states.

The position and orientation gaps have bounded Jacobian checks. The
orientation gap has a private mixed second variation; complete six-channel
work, multiplier space, stability and production ownership remain separate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_local_footprint_work import (
    bond_x_segments, structured_c1_mixed_point_shape,
    structured_q4_point_shape,
)


def _skew(vector):
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


@dataclass(frozen=True)
class _Station:
    x: float
    weight: float
    nodes: np.ndarray
    shape: np.ndarray
    dshape_dx: np.ndarray
    port: NativeHalfCellSpatialPort
    reference_gap: np.ndarray
    reference_orientation: np.ndarray


def _shape_derivative_x(reference_nodes, nodes, shape, x, y):
    """Physical longitudinal derivative of the selected Q4 or S3 host."""
    xy = reference_nodes[nodes, :2]
    if len(nodes) == 3:
        matrix = np.vstack((np.ones(3), xy.T))
        if abs(np.linalg.det(matrix)) <= 1e-14:
            raise ValueError("degenerate material-line triangle")
        return np.linalg.solve(matrix, (0., 1., 0.))
    if len(nodes) != 4:
        raise ValueError("Q4 or S3 material-line host required")
    dx = xy[1, 0]-xy[0, 0]
    dy = xy[3, 1]-xy[0, 1]
    if dx <= 0 or dy <= 0:
        raise ValueError("oriented material-line Q4 host required")
    eta = (y-xy[0, 1])/dy
    if not -1e-12 <= eta <= 1.+1e-12 or abs(sum(shape)-1.) > 1e-12:
        raise ValueError("material-line interpolation left host")
    return np.array((-(1.-eta), 1.-eta, eta, -eta))/dx


def _shell_frame_terms(coordinates, frames, station, top):
    nodes, shape = station.nodes, station.shape
    director = sum((weight*frames[int(node), :, 2]
                    for node, weight in zip(nodes, shape)), np.zeros(3))
    length = np.linalg.norm(director)
    if not np.isfinite(length) or length <= .5:
        raise ValueError("material-line director is degenerate")
    director /= length
    top_points = np.array([coordinates[int(node)]+frames[int(node)]@top
                           for node in nodes])
    tangent = station.dshape_dx@top_points
    projected = tangent-director*np.dot(director, tangent)
    projected_length = np.linalg.norm(projected)
    if (not np.isfinite(projected_length) or
            projected_length <= .2*np.linalg.norm(tangent)):
        raise ValueError("material-line projected tangent is degenerate")
    x_axis = projected/projected_length
    y_axis = np.cross(director, x_axis)
    return (np.column_stack((x_axis, y_axis, director)), director,
            tangent, projected_length)


def _shell_frame(coordinates, frames, station, top):
    return _shell_frame_terms(coordinates, frames, station, top)[0]


def _shell_angular_variation(frame, director, tangent, projected_length,
                             delta_director_raw, delta_tangent, raw_length):
    """Spatial angular variation of the projected-tangent shell frame."""
    delta_director = (delta_director_raw-director*np.dot(
        director, delta_director_raw))/raw_length
    delta_projected = (delta_tangent
                       -delta_director*np.dot(director, tangent)
                       -director*(np.dot(delta_director, tangent)
                                  +np.dot(director, delta_tangent)))
    x_axis = frame[:, 0]
    delta_x = (delta_projected-x_axis*np.dot(
        x_axis, delta_projected))/projected_length
    delta_y = (np.cross(delta_director, x_axis)
               +np.cross(director, delta_x))
    return .5*(np.cross(x_axis, delta_x)
               +np.cross(frame[:, 1], delta_y)
               +np.cross(director, delta_director))


def _log_left_inverse(vector):
    """SO(3) left-Jacobian inverse inside the admitted relative chart."""
    angle = np.linalg.norm(vector)
    cross = _skew(vector)
    if angle < 1e-4:
        coefficient = 1./12.+angle**2/720.+angle**4/30240.
    else:
        coefficient = (1.-.5*angle/np.tan(.5*angle))/angle**2
    return np.eye(3)-.5*cross+coefficient*cross@cross


def _normalized_variations(value, first, second, mixed):
    """Value, two first variations and symmetric mixed variation of v/|v|."""
    length = np.linalg.norm(value)
    if not np.isfinite(length) or length <= 0.:
        raise ValueError("degenerate material-line normalization")
    unit = value/length
    projection = np.eye(3)-np.outer(unit, unit)
    du = projection@first/length
    dv = projection@second/length
    duv = ((projection@mixed
            -np.dot(unit, first)*dv-np.dot(unit, second)*du)/length
           -unit*np.dot(du, dv))
    return unit, du, dv, duv


def _log_left_inverse_variation(vector, variation):
    """Directional derivative of the SO(3) left-Log Jacobian inverse."""
    angle = np.linalg.norm(vector)
    cross, delta_cross = _skew(vector), _skew(variation)
    if angle < 1e-4:
        coefficient = 1./12.+angle**2/720.+angle**4/30240.
        coefficient_direction = (1./360.+angle**2/7560.)*np.dot(
            vector, variation)
    else:
        half = .5*angle
        cotangent = 1./np.tan(half)
        f = 1.-half*cotangent
        df = -.5*cotangent+.25*angle/(np.sin(half)**2)
        coefficient = f/angle**2
        coefficient_direction = (df/angle**3-2.*f/angle**4)*np.dot(
            vector, variation)
    return (-.5*delta_cross+coefficient_direction*cross@cross
            +coefficient*(delta_cross@cross+cross@delta_cross))


def _vee_skew(matrix):
    skew = .5*(matrix-matrix.T)
    return np.array((skew[2, 1], skew[0, 2], skew[1, 0]))


def _shell_frame_second_variation(coordinates, frames, station, top,
                                  first_shell, second_shell):
    """Material-line shell frame and mixed variation in one exponential chart."""
    director_raw = np.zeros(3)
    director_u = np.zeros(3)
    director_v = np.zeros(3)
    director_uv = np.zeros(3)
    tangent = np.zeros(3)
    tangent_u = np.zeros(3)
    tangent_v = np.zeros(3)
    tangent_uv = np.zeros(3)
    normal = np.array((0., 0., 1.))
    for node, weight, derivative in zip(
            station.nodes, station.shape, station.dshape_dx):
        node = int(node)
        frame = frames[node]
        u, v = first_shell[node], second_shell[node]
        rotation_u, rotation_v = _skew(u[3:]), _skew(v[3:])
        rotation_uv = .5*(rotation_u@rotation_v+rotation_v@rotation_u)
        current_normal, current_top = frame@normal, frame@top
        director_raw += weight*current_normal
        director_u += weight*rotation_u@current_normal
        director_v += weight*rotation_v@current_normal
        director_uv += weight*rotation_uv@current_normal
        tangent += derivative*(coordinates[node]+current_top)
        tangent_u += derivative*(u[:3]+rotation_u@current_top)
        tangent_v += derivative*(v[:3]+rotation_v@current_top)
        tangent_uv += derivative*rotation_uv@current_top
    if np.linalg.norm(director_raw) <= .5:
        raise ValueError("material-line director is degenerate")
    d, du, dv, duv = _normalized_variations(
        director_raw, director_u, director_v, director_uv)
    c = np.dot(d, tangent)
    cu = np.dot(du, tangent)+np.dot(d, tangent_u)
    cv = np.dot(dv, tangent)+np.dot(d, tangent_v)
    cuv = (np.dot(duv, tangent)+np.dot(du, tangent_v)
           +np.dot(dv, tangent_u)+np.dot(d, tangent_uv))
    projected = tangent-d*c
    projected_u = tangent_u-du*c-d*cu
    projected_v = tangent_v-dv*c-d*cv
    projected_uv = tangent_uv-duv*c-du*cv-dv*cu-d*cuv
    if np.linalg.norm(projected) <= .2*np.linalg.norm(tangent):
        raise ValueError("material-line projected tangent is degenerate")
    e, eu, ev, euv = _normalized_variations(
        projected, projected_u, projected_v, projected_uv)
    b = np.cross(d, e)
    bu = np.cross(du, e)+np.cross(d, eu)
    bv = np.cross(dv, e)+np.cross(d, ev)
    buv = (np.cross(duv, e)+np.cross(du, ev)
           +np.cross(dv, eu)+np.cross(d, euv))
    return (np.column_stack((e, b, d)),
            np.column_stack((eu, bu, du)),
            np.column_stack((ev, bv, dv)),
            np.column_stack((euv, buv, duv)))


class MaterialLinePosition:
    """Bounded position map and private material-line orientation probe."""

    def __init__(self, xs, ys, beam, *, thickness=.035, beam_depth=.1,
                 quadrature_order=3, mixed_s3=False, diagonal="bl_tr"):
        self.xs = np.asarray(xs, dtype=float)
        self.ys = np.asarray(ys, dtype=float)
        self.beam = beam
        if (self.xs.ndim != 1 or self.ys.ndim != 1 or
                not np.isfinite(self.xs).all() or not np.isfinite(self.ys).all() or
                np.any(np.diff(self.xs) <= 0) or np.any(np.diff(self.ys) <= 0) or
                quadrature_order not in (3, 5) or not np.isfinite((thickness, beam_depth)).all() or
                thickness <= 0 or beam_depth <= 0):
            raise ValueError("bounded finite material-line geometry required")
        self.top = np.array((0., 0., thickness/2))
        self.bottom = np.array((0., 0., -beam_depth/2))
        self.reference_nodes = np.array([(x, y, 0.) for y in self.ys for x in self.xs])
        self.shell_count = len(self.reference_nodes)
        if mixed_s3:
            from scripts.b3_e4_f03_plate_patch_work import c1_mixed_s3_cells
            cells = c1_mixed_s3_cells(self.xs, self.ys)
            point_shape = lambda x: structured_c1_mixed_point_shape(
                self.xs, self.ys, x, 0., cells, diagonal=diagonal)
        else:
            if diagonal != "bl_tr":
                raise ValueError("Q4 material line has no triangle diagonal")
            point_shape = lambda x: structured_q4_point_shape(self.xs, self.ys, x, 0.)
        roots, weights = np.polynomial.legendre.leggauss(quadrature_order)
        state = beam.context.initial.mechanical
        stations = []
        for x0, x1 in zip(self.xs[:-1], self.xs[1:]):
            low, high = max(float(x0), .9), min(float(x1), 1.)
            if high <= low:
                continue
            for a, b in bond_x_segments(low, high, beam.abscissae):
                for root, weight in zip(roots, weights):
                    x = (a+b)/2 + float(root)*(b-a)/2
                    nodes, shape = point_shape(x)
                    element, cell, fraction, _ = beam._locate(x)
                    port = NativeHalfCellSpatialPort(beam.context, element, cell, fraction)
                    high_position, low_position, frame = port.pose_pair(state)
                    shell_top = shape@(self.reference_nodes[nodes]+self.top)
                    beam_bottom = high_position+low_position+frame@self.bottom
                    reference_gap = frame.T@(shell_top-beam_bottom)
                    if np.max(np.abs(reference_gap)) > 1e-10:
                        raise ValueError("material-line reference geometry is not coincident")
                    derivative = _shape_derivative_x(
                        self.reference_nodes, nodes, shape, x, 0.)
                    provisional = _Station(x, float(weight)*(b-a)/2,
                                           nodes.copy(), shape.copy(),
                                           derivative.copy(), port,
                                           reference_gap.copy(), np.eye(3))
                    shell_frame = _shell_frame(
                        self.reference_nodes,
                        np.broadcast_to(np.eye(3), (self.shell_count, 3, 3)),
                        provisional, self.top)
                    stations.append(_Station(x, provisional.weight,
                                             nodes.copy(), shape.copy(),
                                             derivative.copy(), port,
                                             reference_gap.copy(),
                                             (shell_frame.T@frame).copy()))
        if not stations or abs(sum(s.weight for s in stations)-.1) > 1e-12:
            raise ValueError("complete 0.1 m material line required")
        self.stations = tuple(stations)

    def evaluate(self, shell_coordinates, shell_frames, beam_state):
        coordinates = np.asarray(shell_coordinates, dtype=float)
        frames = np.asarray(shell_frames, dtype=float)
        if (coordinates.shape != (self.shell_count, 3) or
                frames.shape != (self.shell_count, 3, 3) or
                not np.isfinite(coordinates).all() or not np.isfinite(frames).all()):
            raise ValueError("complete finite shell state required")
        gaps = []
        for station in self.stations:
            high, low, frame = station.port.pose_pair(beam_state)
            shell_top = sum((weight*(coordinates[int(node)]+frames[int(node)]@self.top)
                             for node, weight in zip(station.nodes, station.shape)),
                            np.zeros(3))
            beam_bottom = high+low+frame@self.bottom
            gaps.append(frame.T@(shell_top-beam_bottom)-station.reference_gap)
        return np.asarray(gaps)

    def reference_jacobian(self):
        """Exact first variation in the native accepted reference chart."""
        state = self.beam.context.initial.mechanical
        result = np.zeros((3*len(self.stations), 6*self.shell_count+self.beam.context.count))
        for k, station in enumerate(self.stations):
            high, low, frame = station.port.pose_pair(state)
            shell_top = station.shape@(self.reference_nodes[station.nodes]+self.top)
            center = high+low
            tangent = station.port.tangent(state)
            block = result[3*k:3*k+3]
            for node, weight in zip(station.nodes, station.shape):
                node = int(node)
                block[:, 6*node:6*node+3] += weight*frame.T
                block[:, 6*node+3:6*node+6] -= weight*frame.T@_skew(self.top)
            block[:, 6*self.shell_count:] = frame.T@(
                -tangent[:3]+_skew(shell_top-center)@tangent[3:])
        return result

    def orientation_gap(self, shell_coordinates, shell_frames, beam_state):
        """Objective beam-relative Log on the admitted finite rotation chart."""
        coordinates = np.asarray(shell_coordinates, dtype=float)
        frames = np.asarray(shell_frames, dtype=float)
        if (coordinates.shape != (self.shell_count, 3) or
                frames.shape != (self.shell_count, 3, 3) or
                not np.isfinite(coordinates).all() or not np.isfinite(frames).all()):
            raise ValueError("complete finite shell state required")
        gaps = []
        for station in self.stations:
            shell_frame = _shell_frame(coordinates, frames, station, self.top)
            _, _, beam_frame = station.port.pose_pair(beam_state)
            relative = station.reference_orientation.T@(
                shell_frame.T@beam_frame)
            gap = Rotation.from_matrix(relative).as_rotvec()
            if not np.isfinite(gap).all() or np.linalg.norm(gap) >= np.pi-.1:
                raise ValueError("material-line relative rotation left chart")
            gaps.append(gap)
        return np.asarray(gaps)

    def orientation_jacobian(self, shell_coordinates, shell_frames, beam_state):
        """First Log variation through current left-multiplicative updates."""
        coordinates = np.asarray(shell_coordinates, dtype=float)
        frames = np.asarray(shell_frames, dtype=float)
        if (coordinates.shape != (self.shell_count, 3) or
                frames.shape != (self.shell_count, 3, 3) or
                not np.isfinite(coordinates).all() or not np.isfinite(frames).all()):
            raise ValueError("complete finite shell state required")
        result = np.zeros((3*len(self.stations),
                           6*self.shell_count+self.beam.context.count))
        basis = np.eye(3)
        for k, station in enumerate(self.stations):
            shell_frame, director, tangent, projected_length = (
                _shell_frame_terms(coordinates, frames, station, self.top))
            raw_director = sum((weight*frames[int(node), :, 2]
                                for node, weight in zip(station.nodes,
                                                        station.shape)),
                               np.zeros(3))
            raw_length = np.linalg.norm(raw_director)
            _, _, beam_frame = station.port.pose_pair(beam_state)
            relative = station.reference_orientation.T@(
                shell_frame.T@beam_frame)
            gap = Rotation.from_matrix(relative).as_rotvec()
            if not np.isfinite(gap).all() or np.linalg.norm(gap) >= np.pi-.1:
                raise ValueError("material-line relative rotation left chart")
            pullback = (_log_left_inverse(gap)@
                        station.reference_orientation.T@shell_frame.T)
            block = result[3*k:3*k+3]
            for node, weight, derivative in zip(
                    station.nodes, station.shape, station.dshape_dx):
                node = int(node)
                for axis, vector in enumerate(basis):
                    column = 6*node+axis
                    omega = _shell_angular_variation(
                        shell_frame, director, tangent, projected_length,
                        np.zeros(3), derivative*vector, raw_length)
                    block[:, column] = -pullback@omega
                    column += 3
                    omega = _shell_angular_variation(
                        shell_frame, director, tangent, projected_length,
                        weight*np.cross(vector, frames[node, :, 2]),
                        derivative*np.cross(vector, frames[node]@self.top),
                        raw_length)
                    block[:, column] = -pullback@omega
            block[:, 6*self.shell_count:] = (
                pullback@station.port.tangent(beam_state)[3:])
        return result

    def reference_orientation_jacobian(self):
        """Specialize the orientation Jacobian to the accepted reference."""
        return self.orientation_jacobian(
            self.reference_nodes,
            np.broadcast_to(np.eye(3), (self.shell_count, 3, 3)),
            self.beam.context.initial.mechanical)

    def orientation_second_variation(self, shell_coordinates, shell_frames,
                                     beam_state, first, second):
        """Mixed Log variation in one chart for the private G0 proof."""
        coordinates = np.asarray(shell_coordinates, dtype=float)
        frames = np.asarray(shell_frames, dtype=float)
        first = np.asarray(first, dtype=float)
        second = np.asarray(second, dtype=float)
        total = 6*self.shell_count+self.beam.context.count
        if (coordinates.shape != (self.shell_count, 3) or
                frames.shape != (self.shell_count, 3, 3) or
                first.shape != (total,) or second.shape != (total,) or
                not all(np.isfinite(item).all() for item in
                        (coordinates, frames, first, second))):
            raise ValueError("complete finite material-line state and directions required")
        split = 6*self.shell_count
        shell_u = first[:split].reshape(-1, 6)
        shell_v = second[:split].reshape(-1, 6)
        beam_u, beam_v = first[split:], second[split:]
        result = []
        for station in self.stations:
            shell, shell_first, shell_second, shell_mixed = (
                _shell_frame_second_variation(
                    coordinates, frames, station, self.top, shell_u, shell_v))
            _, _, beam = station.port.pose_pair(beam_state)
            port_tangent = station.port.tangent(beam_state)[3:]
            beam_first = _skew(port_tangent@beam_u)@beam
            beam_second = _skew(port_tangent@beam_v)@beam
            _, beam_mixed = station.port.second_variation(
                beam_state, beam_u, beam_v)
            reference = station.reference_orientation.T
            relative = reference@shell.T@beam
            relative_first = reference@(
                shell_first.T@beam+shell.T@beam_first)
            relative_second = reference@(
                shell_second.T@beam+shell.T@beam_second)
            relative_mixed = reference@(
                shell_mixed.T@beam+shell_first.T@beam_second
                +shell_second.T@beam_first+shell.T@beam_mixed)
            gap = Rotation.from_matrix(relative).as_rotvec()
            if not np.isfinite(gap).all() or np.linalg.norm(gap) >= np.pi-.1:
                raise ValueError("material-line relative rotation left chart")
            inverse = _log_left_inverse(gap)
            eta_first = _vee_skew(relative_first@relative.T)
            eta_second = _vee_skew(relative_second@relative.T)
            eta_mixed = _vee_skew(
                relative_mixed@relative.T
                +relative_first@relative_second.T)
            gap_second = inverse@eta_second
            result.append(_log_left_inverse_variation(
                gap, gap_second)@eta_first+inverse@eta_mixed)
        return np.asarray(result)
