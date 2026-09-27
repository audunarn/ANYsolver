"""Private G0 material-line position trace on actual E4 and retained B3 poses.

This derives only the three translational channels. A physical orientation
law, line multipliers, stability and production ownership remain separate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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
    port: NativeHalfCellSpatialPort
    reference_gap: np.ndarray


class MaterialLinePosition:
    """Bounded, local shell-top to beam-bottom material-line position map."""

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
                    stations.append(_Station(x, float(weight)*(b-a)/2,
                                             nodes.copy(), shape.copy(), port,
                                             reference_gap.copy()))
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
