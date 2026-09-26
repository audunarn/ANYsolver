"""Bounded finite-chart proofs for physical terminal-strip candidates.

This is a G0B mechanics experiment, not a production attachment or a line
mortar. The six rows are the mean material-frame surface-position gap and its
reference-arm first moment over one flat terminal footprint.
The optional hybrid replaces one position-moment row with a shell-director
pitch row. Both remain exploratory single-interval operators.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_mixed_ad import rotation_exponential
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_local_footprint_work import (
    bond_x_segments, distributed_surface_patch_trace, skew,
    structured_q4_point_shape,
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
            for sx0, sx1 in bond_x_segments(lx, hx, beam.abscissae):
                for y0, y1 in zip(self.ys[:-1], self.ys[1:]):
                    ly, hy = max(float(y0), -.05), min(float(y1), .05)
                    if hy <= ly:
                        continue
                    jac = (sx1-sx0)*(hy-ly)/4
                    for xi, wx in zip(roots, weights):
                        x = (sx0+sx1)/2 + float(xi)*(sx1-sx0)/2
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

    def linearized_gap_statistics(self, shell_step, beam_step) -> dict:
        """Recover sampled local slip separately from the six weak moments."""
        shell = np.asarray(shell_step, dtype=float).reshape(self.shell_count, 6)
        beam = np.asarray(beam_step, dtype=float)
        if beam.shape != (self.beam.context.count,) or not (
                np.isfinite(shell).all() and np.isfinite(beam).all()):
            raise ValueError("finite complete linearized surface state required")
        base = self.beam.context.initial.mechanical
        _, _, center_frame = self.center.pose_pair(base)
        material = center_frame.T
        mean = np.zeros(3)
        moment = np.zeros(3)
        square = 0.
        maximum = 0.
        for point in self.points:
            shell_displacement = np.zeros(3)
            for node, shape in zip(point.nodes, point.shape):
                step = shell[int(node)]
                shell_displacement += shape*(
                    step[:3]+np.cross(step[3:], (0., 0., self.top)))
            pose = point.port.tangent(base) @ beam
            beam_displacement = pose[:3]+np.cross(
                pose[3:], (0., point.y, -.05))
            gap = material @ (shell_displacement-beam_displacement)
            arm = np.array((point.x-.95, point.y, 0.))
            mean += point.weight*gap
            moment += point.weight*np.cross(arm, gap)
            square += point.weight*float(gap @ gap)
            maximum = max(maximum, float(np.linalg.norm(gap)))
        weak = np.r_[mean, np.linalg.solve(self.inertia, moment)]
        return {
            "quadrature_rms_position_gap_m": float(np.sqrt(square)),
            "quadrature_max_position_gap_m": maximum,
            "weak_six_gap_m_rad": weak.tolist(),
            "quadrature_points": len(self.points),
            "meaning": "sampled linearized shell-top minus native beam-bottom position; six weak moments may vanish while local slip remains",
        }

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


class FiniteSurfaceLineHybrid(FiniteSurfaceMomentPatch):
    """Bounded six-channel transverse-strip line weld, not a 3D bond.

    Mean shell-top/beam-bottom position supplies three force channels.
    Transverse position moments supply Mx/Mz; an explicit E4 director-pitch
    tie supplies My. The latter is a declared reduced-section assumption.
    Material-frame duals and actual-chart variations remain separate from
    display-ready spatial wrenches.
    """

    def __init__(self, xs: np.ndarray, ys: np.ndarray, beam, *, thickness: float):
        super().__init__(xs, ys, beam, thickness=thickness)
        self.transverse_inertia = float(sum(
            point.weight*point.y**2 for point in self.points))
        if self.transverse_inertia <= 1e-8:
            raise ValueError("C1 line has degenerate transverse arm")

    def _director(self, frames: np.ndarray, x: float):
        nodes, shape = structured_q4_point_shape(self.xs, self.ys, x, 0.)
        return nodes, shape, sum((weight*frames[int(node), :, 2]
                                  for node, weight in zip(nodes, shape)),
                                 np.zeros(3))

    @staticmethod
    def _pitch(frame: np.ndarray, director: np.ndarray,
               frame_u=None, frame_v=None, frame_uv=None,
               director_u=None, director_v=None, director_uv=None):
        x_axis, z_axis = frame[:, 0], frame[:, 2]
        a, c = float(x_axis@director), float(z_axis@director)
        if (not np.isfinite((a, c)).all() or c <= .2 or
                np.linalg.norm(director) <= .5):
            raise ValueError("C1 line director pitch left its guarded chart")
        angle = float(np.arctan2(a, c))
        if frame_u is None:
            return (angle,)
        a_u = float(frame_u[:, 0]@director+x_axis@director_u)
        c_u = float(frame_u[:, 2]@director+z_axis@director_u)
        a_v = float(frame_v[:, 0]@director+x_axis@director_v)
        c_v = float(frame_v[:, 2]@director+z_axis@director_v)
        a_uv = float(frame_uv[:, 0]@director+
                     frame_u[:, 0]@director_v+
                     frame_v[:, 0]@director_u+x_axis@director_uv)
        c_uv = float(frame_uv[:, 2]@director+
                     frame_u[:, 2]@director_v+
                     frame_v[:, 2]@director_u+z_axis@director_uv)
        denom = a*a+c*c
        n_u, n_v = c*a_u-a*c_u, c*a_v-a*c_v
        mixed = ((c_v*a_u+c*a_uv-a_v*c_u-a*c_uv)/denom-
                 n_u*(2*a*a_v+2*c*c_v)/denom**2)
        return angle, n_u/denom, n_v/denom, mixed

    def evaluate(self, shell_coordinates: np.ndarray, shell_frames: np.ndarray,
                 beam_state, first=None, second=None) -> np.ndarray:
        """Six gaps and optional exact first/mixed chart variations."""
        coordinates = np.asarray(shell_coordinates, dtype=float)
        frames = np.asarray(shell_frames, dtype=float)
        if (coordinates.shape != (self.shell_count, 3) or
                frames.shape != (self.shell_count, 3, 3) or
                not (np.isfinite(coordinates).all() and np.isfinite(frames).all())):
            raise ValueError("complete finite shell physical state required")
        directional = first is not None or second is not None
        if directional:
            if first is None or second is None:
                raise ValueError("two complete chart directions required")
            su, bu = first
            sv, bv = second
            su = np.asarray(su, dtype=float).reshape(self.shell_count, 6)
            sv = np.asarray(sv, dtype=float).reshape(self.shell_count, 6)
            bu, bv = np.asarray(bu, dtype=float), np.asarray(bv, dtype=float)
            if (bu.shape != (self.beam.context.count,) or
                    bv.shape != bu.shape or
                    not all(np.isfinite(a).all() for a in (su, sv, bu, bv))):
                raise ValueError("complete finite C1 line directions required")
        rows = np.zeros((6, 4 if directional else 1))
        offset_shell = np.array((0., 0., self.top))
        for point in self.points:
            high, low, beam_frame = point.port.pose_pair(beam_state)
            offset_beam = np.array((0., point.y, -.05))
            beam_position = high+low+beam_frame@offset_beam
            shell_position = self._shell(coordinates, frames, point)
            gap = shell_position-beam_position
            qc = beam_frame.T
            values = [qc@gap]
            center_nodes, center_shape, director = self._director(frames, point.x)
            if directional:
                port = point.port.tangent(beam_state)
                pu, pv = port@bu, port@bv
                position_uv, frame_uv = point.port.second_variation(
                    beam_state, bu, bv)
                frame_u = skew(pu[3:])@beam_frame
                frame_v = skew(pv[3:])@beam_frame
                qc_u, qc_v, qc_uv = frame_u.T, frame_v.T, frame_uv.T
                shell_u = np.zeros(3)
                shell_v = np.zeros(3)
                shell_uv = np.zeros(3)
                for node, shape in zip(point.nodes, point.shape):
                    node = int(node)
                    directed = frames[node]@offset_shell
                    a, b = skew(su[node, 3:]), skew(sv[node, 3:])
                    shell_u += shape*(su[node, :3]+a@directed)
                    shell_v += shape*(sv[node, :3]+b@directed)
                    shell_uv += shape*(.5*(a@b+b@a)@directed)
                beam_u = pu[:3]+frame_u@offset_beam
                beam_v = pv[:3]+frame_v@offset_beam
                beam_uv = position_uv+frame_uv@offset_beam
                gap_u, gap_v = shell_u-beam_u, shell_v-beam_v
                values.extend((qc_u@gap+qc@gap_u,
                               qc_v@gap+qc@gap_v,
                               qc_uv@gap+qc_u@gap_v+qc_v@gap_u+
                               qc@(shell_uv-beam_uv)))
                director_u = np.zeros(3)
                director_v = np.zeros(3)
                director_uv = np.zeros(3)
                for node, shape in zip(center_nodes, center_shape):
                    node = int(node)
                    directed = frames[node, :, 2]
                    a, b = skew(su[node, 3:]), skew(sv[node, 3:])
                    director_u += shape*(a@directed)
                    director_v += shape*(b@directed)
                    director_uv += shape*(.5*(a@b+b@a)@directed)
                pitch = self._pitch(
                    beam_frame, director, frame_u, frame_v, frame_uv,
                    director_u, director_v, director_uv)
            else:
                pitch = self._pitch(beam_frame, director)
            for column, value in enumerate(values):
                rows[:3, column] += point.weight*value
                rows[3, column] += (
                    point.weight*point.y*value[2]/self.transverse_inertia)
                rows[4, column] += point.weight*pitch[column]
                rows[5, column] -= (
                    point.weight*point.y*value[0]/self.transverse_inertia)
        return rows

    def reference_trace(self) -> np.ndarray:
        """Analytic six-row Jacobian at the physical C1 reference state."""
        shell_size = self.shell_size
        total = shell_size+self.beam.context.count
        trace = np.zeros((6, total))
        frames = np.broadcast_to(np.eye(3),
                                 (self.shell_count, 3, 3))
        state = self.beam.context.initial.mechanical
        for point in self.points:
            _, _, frame = point.port.pose_pair(state)
            port = point.port.tangent(state)
            qc = frame.T
            shell_map = np.zeros((3, total))
            for node, shape in zip(point.nodes, point.shape):
                start = 6*int(node)
                shell_map[:, start:start+3] += shape*np.eye(3)
                shell_map[:, start+3:start+6] -= shape*skew(
                    np.array((0., 0., self.top)))
            beam_map = np.column_stack((
                np.eye(3), -skew(frame@np.array((0., point.y, -.05)))))@port
            shell_map[:, shell_size:] -= beam_map
            gap_map = qc@shell_map
            trace[:3] += point.weight*gap_map
            trace[3] += point.weight*point.y*gap_map[2]/self.transverse_inertia
            trace[5] -= point.weight*point.y*gap_map[0]/self.transverse_inertia

            nodes, shape, director = self._director(frames, point.x)
            a, c = float(frame[:, 0]@director), float(frame[:, 2]@director)
            denom = a*a+c*c
            if c <= .2:
                raise ValueError("C1 reference director pitch left its chart")
            for node, weight in zip(nodes, shape):
                start = 6*int(node)+3
                dd = -skew(frames[int(node), :, 2])
                da = frame[:, 0]@dd
                dc = frame[:, 2]@dd
                trace[4, start:start+3] += (
                    point.weight*weight*(c*da-a*dc)/denom)
            beam_pitch = (c*np.cross(frame[:, 0], director)-
                          a*np.cross(frame[:, 2], director))/denom
            trace[4, shell_size:] += point.weight*beam_pitch@port[3:]
        return trace


def finite_chart_screen(reference_profile: str = "straight", *,
                        hybrid: bool = False) -> dict:
    """One deterministic, bounded nonzero-gap and nonzero-multiplier proof."""
    from scripts._b3_e4_f03_native_fixture import build
    from scripts.b3_e4_f03_square_section_control import square_torsion_constant

    if reference_profile not in ("straight", "c1_tangent_2um"):
        raise ValueError("bounded straight or C1 chart reference required")
    beam = build(4 if reference_profile == "straight" else 12,
                 z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile=reference_profile)
    patch_class = FiniteSurfaceLineHybrid if hybrid else FiniteSurfaceMomentPatch
    patch = patch_class(
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
    if hybrid:
        trace = patch.reference_trace()
    else:
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
        "reference_profile": reference_profile,
        "hybrid": hybrid,
        "reference_gap_max_m_rad": float(np.max(np.abs(reference))),
        "reference_jacobian_direction_error": reference_error,
        "nonzero_gap_norm_m_rad": float(np.linalg.norm(derivatives[:, 0])),
        "nonzero_multiplier_mixed_work_j": mixed,
        "first_direction_error_j": first_error,
        "mixed_direction_error_j": mixed_error,
        "finite_common_rigid_gap_error": rigid_error,
        "common_rigid_virtual_work_j": rigid_virtual_work,
        "quadrature_points": len(patch.points),
        "scope": ("actual E4 director and retained B3 half-cell charts; "
                  "bounded single-interval six-channel hybrid" if hybrid else
                  "actual E4 director and retained B3 half-cell charts; "
                  "bounded finite six-resultant surface-position law"),
    }


def bounded_physical_compliance_screen(*, hybrid: bool = False) -> list[dict]:
    """Compare six physical interface actions on several bounded local grids.

    This is a finite-dimensional, support-conditioned compliance diagnostic,
    not an inf-sup constant or a choice of a true-line multiplier space.
    The positive-energy Gram is formed from actual retained B3 and E4
    operators without symmetrizing either operator to repair its tangent.
    """
    from scipy import linalg

    from scripts._b3_e4_f03_native_fixture import build
    from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
    from scripts.b3_e4_f03_square_section_control import square_torsion_constant

    results = []
    actions = np.diag((1000., 1000., 1000., 100., 100., 100.))
    shell_operators = {}
    cases = ((2, 12), (4, 12)) if hybrid else (
        (2, 4), (2, 8), (4, 4), (4, 8), (4, 16))
    for patch_cells, half_cells in cases:
        xs, ys = local_grid(patch_cells)
        beam = build(half_cells, z_offset=.0675,
                     torsion_constant=square_torsion_constant(),
                     reference_profile=("c1_tangent_2um" if hybrid
                                        else "straight"))
        if patch_cells not in shell_operators:
            shell_operators[patch_cells] = raw_e4_tangent(
                xs, ys, thickness=.035)
        shell_k, shell_physical = shell_operators[patch_cells]
        if hybrid:
            patch = FiniteSurfaceLineHybrid(
                xs, ys, beam, thickness=.035)
            rows = patch.reference_trace()
            frames = np.broadcast_to(np.eye(3),
                                     (patch.shell_count, 3, 3))
            reference_gap = float(np.max(np.abs(patch.evaluate(
                patch.reference_nodes, frames,
                beam.context.initial.mechanical)[:, 0])))
        else:
            rows, reference = distributed_surface_patch_trace(
                xs, ys, beam, plate_thickness=.035)
            reference_gap = reference["reference_gap_m"]
        shell_size = shell_k.shape[0]
        total = shell_size+beam.context.count
        if total > 1900:
            raise ValueError("bounded local compliance matrix cap exceeded")
        fixed_shell = {6*j*len(xs)+axis for j in range(len(ys))
                       for axis in range(6)}
        fixed_beam = {shell_size+i for i in beam.context.fixed}
        free = np.array([i for i in range(total)
                         if i not in fixed_shell and i not in fixed_beam])
        shell_free = free[free < shell_size]
        beam_free = free[free >= shell_size]-shell_size
        shell_rows = rows[:, shell_free]
        beam_rows = rows[:, shell_size+beam_free]
        shell_block = shell_k[np.ix_(shell_free, shell_free)]
        beam_block = beam.tangent[np.ix_(beam_free, beam_free)].toarray()
        shell_response = linalg.solve(
            shell_block, shell_rows.T, assume_a="gen", check_finite=True)
        beam_response = linalg.solve(
            beam_block, beam_rows.T, assume_a="gen", check_finite=True)
        gram_shell = shell_rows@ shell_response
        gram_beam = beam_rows@ beam_response
        gram = actions@(gram_shell+gram_beam)@actions
        skew_relative = float(np.linalg.norm(gram-gram.T)/max(
            np.linalg.norm(gram), 1e-30))
        if skew_relative > 1e-8:
            raise ArithmeticError("reference physical compliance is nonsymmetric")
        diagonal = np.diag(gram)
        if np.min(diagonal) <= 0.:
            raise ArithmeticError("nonpositive physical interface action")
        energy_scale = np.sqrt(diagonal)
        normalized = gram/np.outer(energy_scale, energy_scale)
        eigenvalues, eigenvectors = np.linalg.eigh(normalized)
        mode = eigenvectors[:, 0]
        shell_action = float(mode@(
            actions@gram_shell@actions/np.outer(energy_scale, energy_scale))@mode)
        beam_action = float(mode@(
            actions@gram_beam@actions/np.outer(energy_scale, energy_scale))@mode)
        action_dual = actions@(mode/energy_scale)
        shell_mode = shell_response@action_dual
        physical_shell_block = shell_physical[np.ix_(shell_free, shell_free)]
        physical_shell_action = float(shell_mode@physical_shell_block@shell_mode)
        numerical_shell_action = shell_action-physical_shell_action
        if (eigenvalues[0] <= 0. or shell_action <= 0. or
                beam_action <= 0. or physical_shell_action <= 0. or
                abs(shell_action+beam_action-eigenvalues[0]) > 1e-8):
            raise ArithmeticError("physical interface mode action failed")
        results.append({
            "patch_cells_per_side": patch_cells,
            "beam_half_cells": half_cells,
            "shell_nodes": len(xs)*len(ys),
            "total_primal_rows": total,
            "constraint_rank_on_free": int(np.linalg.matrix_rank(rows[:, free])),
            "applied_action_scales_N_Nm": np.diag(actions).tolist(),
            "unit_action_twice_compliances_j": diagonal.tolist(),
            "normalized_mode_minimum": float(eigenvalues[0]),
            "normalized_mode_maximum": float(eigenvalues[-1]),
            "weakest_mode_components": mode.tolist(),
            "weakest_mode_shell_action": shell_action,
            "weakest_mode_physical_shell_action": physical_shell_action,
            "weakest_mode_numerical_shell_action": numerical_shell_action,
            "weakest_mode_beam_action": beam_action,
            "compliance_relative_skew": skew_relative,
            "reference_gap_m": reference_gap,
            "operator": ("C1 single-interval line hybrid" if hybrid else
                         "finite surface-moment footprint"),
            "interpretation": "support-conditioned finite-grid physical action; not continuum inf-sup or line-space qualification",
        })
    return results
