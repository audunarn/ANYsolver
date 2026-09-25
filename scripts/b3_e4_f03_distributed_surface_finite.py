"""Bounded finite-chart proof for the physical surface-moment bond candidate.

This is a G0B mechanics experiment, not a production attachment or a line
mortar. The six rows are the mean material-frame surface-position gap and its
reference-arm first moment over one flat terminal footprint.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_mixed_ad import rotation_exponential
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_local_footprint_work import (
    distributed_surface_patch_trace, skew, structured_q4_point_shape,
)


@dataclass(frozen=True)
class _Point:
    x: float
    y: float
    weight: float
    nodes: np.ndarray
    shape: np.ndarray
    port: NativeHalfCellSpatialPort


class FiniteSurfaceMomentPatch:
    """Actual E4 director and retained B3 half-cell chart at a bounded patch."""

    def __init__(self, xs: np.ndarray, ys: np.ndarray, beam, *, thickness: float):
        self.xs = np.asarray(xs, dtype=float)
        self.ys = np.asarray(ys, dtype=float)
        self.beam = beam
        self.top = thickness / 2
        self.shell_count = len(self.xs) * len(self.ys)
        self.shell_size = 6 * self.shell_count
        self.reference_nodes = np.array(
            [(x, y, 0.) for y in self.ys for x in self.xs], dtype=float)
        self.points = []
        roots, weights = np.polynomial.legendre.leggauss(3)
        inertia = np.zeros((3, 3))
        area = 0.
        for x0, x1 in zip(self.xs[:-1], self.xs[1:]):
            lx, hx = max(float(x0), .9), min(float(x1), 1.)
            if hx <= lx:
                continue
            for y0, y1 in zip(self.ys[:-1], self.ys[1:]):
                ly, hy = max(float(y0), -.05), min(float(y1), .05)
                if hy <= ly:
                    continue
                jac = (hx-lx)*(hy-ly)/4
                for xi, wx in zip(roots, weights):
                    x = (lx+hx)/2 + float(xi)*(hx-lx)/2
                    element, cell, fraction, _ = beam._locate(x)
                    port = NativeHalfCellSpatialPort(
                        beam.context, element, cell, fraction)
                    for eta, wy in zip(roots, weights):
                        y = (ly+hy)/2 + float(eta)*(hy-ly)/2
                        nodes, shape = structured_q4_point_shape(
                            self.xs, self.ys, x, y)
                        w = float(wx*wy*jac)/.01
                        self.points.append(_Point(x, y, w, nodes, shape, port))
                        arm = np.array((x-.95, y, 0.))
                        inertia += w*((arm@arm)*np.eye(3)-np.outer(arm, arm))
                        area += float(wx*wy*jac)
        if abs(area-.01) > 1e-12 or len(self.points) == 0:
            raise ValueError("complete bounded 0.1 by 0.1 m patch required")
        self.inertia = inertia
        if np.linalg.eigvalsh(inertia)[0] <= 1e-8:
            raise ValueError("physical footprint inertia is degenerate")
        element, cell, fraction, _ = beam._locate(.95)
        self.center = NativeHalfCellSpatialPort(
            beam.context, element, cell, fraction)

    def _shell(self, coordinates: np.ndarray, frames: np.ndarray,
               point: _Point):
        position = np.zeros(3)
        offset = np.array((0., 0., self.top))
        for node, shape in zip(point.nodes, point.shape):
            node = int(node)
            directed = frames[node] @ offset
            position += shape*(coordinates[node]+directed)
        return position

    def evaluate(self, shell_coordinates: np.ndarray, shell_frames: np.ndarray,
                 beam_state, first=None, second=None):
        """Return six gaps and, optionally, exact first and mixed variations.

        Both directions are applied with spatial Exp updates from the same
        predecessor. The result includes curvature of the moving material
        frame, E4 director, and retained B3 cell frame.
        """
        coordinates = np.asarray(shell_coordinates, dtype=float)
        frames = np.asarray(shell_frames, dtype=float)
        if coordinates.shape != (self.shell_count, 3) or frames.shape != (self.shell_count, 3, 3):
            raise ValueError("complete shell physical state required")
        directional = first is not None or second is not None
        if directional:
            if first is None or second is None:
                raise ValueError("two directions required")
            su, bu = first
            sv, bv = second
            su, sv = np.asarray(su).reshape(self.shell_count, 6), np.asarray(sv).reshape(self.shell_count, 6)
            bu, bv = np.asarray(bu), np.asarray(bv)
        _, _, center_frame = self.center.pose_pair(beam_state)
        qc = center_frame.T
        if directional:
            center_u = self.center.tangent(beam_state) @ bu
            center_v = self.center.tangent(beam_state) @ bv
            qc_u = (skew(center_u[3:]) @ center_frame).T
            qc_v = (skew(center_v[3:]) @ center_frame).T
            _, center_uv = self.center.second_variation(beam_state, bu, bv)
            qc_uv = center_uv.T
        rows = np.zeros((3, 4 if directional else 1))
        moments = np.zeros_like(rows)
        for point in self.points:
            shell = self._shell(coordinates, frames, point)
            high, low, beam_frame = point.port.pose_pair(beam_state)
            offset = np.array((0., point.y, -.05))
            beam_position = high+low+beam_frame @ offset
            gap = shell-beam_position
            values = [qc @ gap]
            if directional:
                shell_u = np.zeros(3)
                shell_v = np.zeros(3)
                shell_uv = np.zeros(3)
                directed_offset = np.array((0., 0., self.top))
                for node, shape in zip(point.nodes, point.shape):
                    node = int(node)
                    directed = frames[node] @ directed_offset
                    a, b = skew(su[node, 3:]), skew(sv[node, 3:])
                    shell_u += shape*(su[node, :3]+a @ directed)
                    shell_v += shape*(sv[node, :3]+b @ directed)
                    shell_uv += shape*(.5*(a@b+b@a) @ directed)
                port = point.port.tangent(beam_state)
                pu, pv = port@bu, port@bv
                beam_u = pu[:3]+np.cross(pu[3:], beam_frame @ offset)
                beam_v = pv[:3]+np.cross(pv[3:], beam_frame @ offset)
                position_uv, frame_uv = point.port.second_variation(beam_state, bu, bv)
                beam_uv = position_uv+frame_uv@offset
                gap_u, gap_v = shell_u-beam_u, shell_v-beam_v
                values.extend((qc_u@gap+qc@gap_u,
                               qc_v@gap+qc@gap_v,
                               qc_uv@gap+qc_u@gap_v+qc_v@gap_u+qc@(shell_uv-beam_uv)))
            arm = np.array((point.x-.95, point.y, 0.))
            for column, value in enumerate(values):
                rows[:, column] += point.weight*value
                moments[:, column] += point.weight*np.cross(arm, value)
        return np.vstack((rows, np.linalg.solve(self.inertia, moments)))

    def advance(self, coordinates, frames, beam_state, shell_step, beam_step):
        shell_step = np.asarray(shell_step).reshape(self.shell_count, 6)
        made_coordinates = np.asarray(coordinates)+shell_step[:, :3]
        made_frames = np.array([
            rotation_exponential(step[3:]) @ frame
            for step, frame in zip(shell_step, frames)])
        return (made_coordinates, made_frames,
                self.beam.context.advance(beam_state, np.asarray(beam_step)))


def finite_chart_screen() -> dict:
    """One deterministic, bounded nonzero-gap and nonzero-multiplier proof."""
    from scripts._b3_e4_f03_native_fixture import build
    from scripts.b3_e4_f03_square_section_control import square_torsion_constant

    beam = build(4, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    patch = FiniteSurfaceMomentPatch(
        np.linspace(-.5, 1.5, 5), np.linspace(-.5, .5, 3), beam,
        thickness=.035)
    count = patch.shell_count
    shell0 = patch.reference_nodes.copy()
    frame0 = np.broadcast_to(np.eye(3), (count, 3, 3)).copy()
    beam0 = beam.context.initial.mechanical
    reference = patch.evaluate(shell0, frame0, beam0)[:, 0]
    rng = np.random.default_rng(1729)
    shell_base = rng.normal(size=(count, 6)) * np.array((.001, .001, .001, .025, .025, .025))
    beam_base = np.zeros(beam.context.count)
    beam_base[6:beam.context.nodal_count] = rng.normal(
        size=beam.context.nodal_count-6) * .001
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        beam_base[begin:begin+6] = rng.normal(size=6)*.02
    coordinates, frames, state = patch.advance(
        shell0, frame0, beam0, shell_base, beam_base)
    shell_u = rng.normal(size=(count, 6))*np.array((.002, .002, .002, .04, .04, .04))
    shell_v = rng.normal(size=(count, 6))*np.array((.002, .002, .002, .04, .04, .04))
    beam_u = rng.normal(size=beam.context.count)*.001
    beam_v = rng.normal(size=beam.context.count)*.001
    beam_u[:6] = 0.
    beam_v[:6] = 0.
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        beam_u[begin:begin+6] *= 30
        beam_v[begin:begin+6] *= 30
    u, v = (shell_u, beam_u), (shell_v, beam_v)
    derivatives = patch.evaluate(coordinates, frames, state, u, v)
    multipliers = np.array((18., -23., 31., 7., -100., 13.))

    def work(a, b):
        c, f, s = patch.advance(
            coordinates, frames, state, a*shell_u+b*shell_v,
            a*beam_u+b*beam_v)
        return float(multipliers @ patch.evaluate(c, f, s)[:, 0])

    h1 = 1e-5
    h2 = 2e-3
    first_error = max(
        abs(float(multipliers@derivatives[:, 1])-(work(h1, 0)-work(-h1, 0))/(2*h1)),
        abs(float(multipliers@derivatives[:, 2])-(work(0, h1)-work(0, -h1))/(2*h1)))
    mixed = float(multipliers@derivatives[:, 3])
    mixed_fd = (work(h2, h2)-work(h2, -h2)-work(-h2, h2)+work(-h2, -h2))/(4*h2*h2)
    mixed_error = abs(mixed-mixed_fd)

    # The reference Jacobian must be the screened six-row linear operator.
    trace, _ = distributed_surface_patch_trace(
        patch.xs, patch.ys, beam, plate_thickness=.035)
    reference_direction = np.r_[shell_u.ravel(), beam_u]
    reference_first = patch.evaluate(shell0, frame0, beam0, u, v)[:, 1]
    reference_error = float(np.max(np.abs(reference_first-trace@reference_direction)))

    # Full finite common rigid motion, including retained cell frames.
    omega = np.array((.07, -.05, .04))
    translation = np.array((.003, -.002, .004))
    rigid = rotation_exponential(omega)
    rigid_shell = coordinates @ rigid.T + translation
    rigid_frames = rigid @ frames
    rigid_step = np.zeros(beam.context.count)
    for node in range(beam.context.nodal_count//6):
        start = 6*node
        position = state.positions[node]+state.position_low[node]
        rigid_step[start:start+3] = rigid@position+translation-position
        rigid_step[start+3:start+6] = omega
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        rigid_step[begin:begin+6] = np.tile(omega, 2)
    # Only terminal half-cell nodes enter this patch. Keep the fixture's
    # fixed root untouched while transforming every participating pose.
    rigid_step[:6] = 0.
    rigid_state = beam.context.advance(state, rigid_step)
    rigid_error = float(np.max(np.abs(
        patch.evaluate(rigid_shell, rigid_frames, rigid_state)[:, 0]-derivatives[:, 0])))
    rigid_shell_direction = np.zeros((count, 6))
    rigid_beam_direction = np.zeros(beam.context.count)
    for node in range(count):
        rigid_shell_direction[node, :3] = (
            translation+np.cross(omega, coordinates[node]))
        rigid_shell_direction[node, 3:] = omega
    for node in range(1, beam.context.nodal_count//6):
        start = 6*node
        position = state.positions[node]+state.position_low[node]
        rigid_beam_direction[start:start+3] = (
            translation+np.cross(omega, position))
        rigid_beam_direction[start+3:start+6] = omega
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        rigid_beam_direction[begin:begin+6] = np.tile(omega, 2)
    rigid_direction = (rigid_shell_direction, rigid_beam_direction)
    rigid_virtual_work = float(multipliers @ patch.evaluate(
        coordinates, frames, state, rigid_direction, rigid_direction)[:, 1])
    return {
        "reference_gap_max_m_rad": float(np.max(np.abs(reference))),
        "reference_jacobian_direction_error": reference_error,
        "nonzero_gap_norm_m_rad": float(np.linalg.norm(derivatives[:, 0])),
        "nonzero_multiplier_mixed_work_j": mixed,
        "first_direction_error_j": first_error,
        "mixed_direction_error_j": mixed_error,
        "finite_common_rigid_gap_error": rigid_error,
        "common_rigid_virtual_work_j": rigid_virtual_work,
        "quadrature_points": len(patch.points),
        "scope": "actual E4 director and retained B3 half-cell charts; bounded finite six-resultant surface-position law",
    }
