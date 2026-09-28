"""Bounded positive-width E4 shell pose for an F03 law decision.

This is a flat, two-column Q4 *development* trace. It averages interpolated
top-surface positions and directors over a fixed material strip before making
the projected material-line frame. It does not select a multiplier space,
verify equivalence with the E4-PL element's finite-update field, or qualify
a bonded-line connection. A bounded point composition uses the native B3 port.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from anysolver import _ge_beam3_mixed_ad as ad
from anysolver._ge_beam3_pose_joint import RigidPoseJoint
from anysolver.corotational import rotation_matrix_from_vector
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_l1_native_connection_probe import _jet_cross, _jet_unit


def _owned(value: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    result = np.array(value, dtype=float, copy=True)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError("finite rail data with declared shape required")
    return np.frombuffer(result.tobytes(), dtype=float).reshape(shape)


def _unit(value: np.ndarray, label: str) -> np.ndarray:
    size = float(np.linalg.norm(value))
    if not np.isfinite(size) or size <= 1e-10:
        raise ValueError(f"degenerate {label}")
    return value/size


def transverse_shape_integrals(cuts: np.ndarray, bounds: tuple[float, float]
                               ) -> np.ndarray:
    """Integrate piecewise-linear Q4 transverse shape over physical width."""
    y = np.asarray(cuts, dtype=float)
    lo, hi = bounds
    if (y.ndim != 1 or len(y) < 2 or not np.isfinite(y).all() or
            not np.all(np.diff(y) > 0.) or not np.isfinite((lo, hi)).all() or
            not y[0] <= lo < hi <= y[-1]):
        raise ValueError("positive supported material strip required")
    width = hi-lo
    weights = np.zeros(len(y))
    for cell, (a, b) in enumerate(zip(y[:-1], y[1:])):
        left, right = max(a, lo), min(b, hi)
        if right <= left:
            continue
        integrated_left = (b*(right-left)-(right**2-left**2)/2.)/(b-a)
        weights[cell] += integrated_left/width
        weights[cell+1] += ((right-left)-integrated_left)/width
    if not np.isclose(np.sum(weights), 1., rtol=0., atol=2e-14):
        raise ArithmeticError("material strip weights do not conserve translation")
    return np.frombuffer(weights.tobytes(), dtype=float)


@dataclass(frozen=True)
class FlatQ4PhysicalRail:
    reference: np.ndarray
    y_cuts: np.ndarray
    bounds: tuple[float, float]
    thickness: float
    weights: np.ndarray

    @classmethod
    def from_reference(cls, reference: np.ndarray, y_cuts: np.ndarray,
                       bounds: tuple[float, float], thickness: float):
        y = np.asarray(y_cuts, dtype=float)
        if y.ndim != 1 or len(y) < 2:
            raise ValueError("at least one transverse Q4 cell required")
        ref = _owned(reference, (2, len(y), 3))
        if (not np.isfinite(thickness) or thickness <= 0. or
                not np.allclose(ref[:, :, 1], y[None, :], rtol=0., atol=1e-14) or
                not np.allclose(ref[:, :, 2], 0., rtol=0., atol=1e-14) or
                not np.allclose(ref[:, :, 0], ref[:, :1, 0], rtol=0., atol=1e-14) or
                ref[1, 0, 0] <= ref[0, 0, 0]):
            raise ValueError("ordered flat Cartesian Q4 rail reference required")
        weights = transverse_shape_integrals(y, bounds)
        return cls(ref, _owned(y, (len(y),)), tuple(float(v) for v in bounds),
                   float(thickness), weights)

    def pose(self, total: np.ndarray, *, station: float = .5,
             direction: np.ndarray | None = None
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]:
        """Return shell top position/frame and actual additive-chart derivative."""
        shape = (2, len(self.y_cuts), 6)
        q = _owned(total, shape)
        if not np.isfinite(station) or not 0. <= station <= 1.:
            raise ValueError("material station inside rail edge required")
        dq = None if direction is None else _owned(direction, shape)
        directors = np.array([[rotation_matrix_from_vector(q[i, j, 3:])[:, 2]
                               for j in range(shape[1])] for i in range(2)])
        top = self.reference+q[:, :, :3]+.5*self.thickness*directors
        averaged_top = np.einsum("j,ijk->ik", self.weights, top)
        averaged_director = np.einsum("j,ijk->ik", self.weights, directors)
        center = (1.-station)*averaged_top[0]+station*averaged_top[1]
        raw_director = ((1.-station)*averaged_director[0]+
                        station*averaged_director[1])
        normal = _unit(raw_director, "averaged E4 director")
        raw_tangent = averaged_top[1]-averaged_top[0]
        projected = raw_tangent-normal*(normal@raw_tangent)
        tangent = _unit(projected, "projected averaged material tangent")
        frame = np.column_stack((tangent, np.cross(normal, tangent), normal))
        if dq is None:
            return center, frame, None, None

        director_step = np.empty_like(directors)
        for i in range(2):
            for j in range(shape[1]):
                epsilon = ad.Jet2.variable(0., 0, 1)
                theta = [ad.Jet2.constant(q[i, j, 3+k], 1) +
                         epsilon*dq[i, j, 3+k] for k in range(3)]
                rotated = ad.so3_exp(theta)
                director_step[i, j] = [rotated[k][2].gradient[0]
                                       for k in range(3)]
        top_step = dq[:, :, :3]+.5*self.thickness*director_step
        averaged_top_step = np.einsum("j,ijk->ik", self.weights, top_step)
        averaged_director_step = np.einsum(
            "j,ijk->ik", self.weights, director_step)
        center_step = ((1.-station)*averaged_top_step[0]+
                       station*averaged_top_step[1])
        raw_director_step = ((1.-station)*averaged_director_step[0]+
                             station*averaged_director_step[1])
        normal_step = ((raw_director_step-
                        normal*(normal@raw_director_step)) /
                       np.linalg.norm(raw_director))
        raw_tangent_step = averaged_top_step[1]-averaged_top_step[0]
        projected_step = (raw_tangent_step-
                          normal_step*(normal@raw_tangent)-
                          normal*(normal_step@raw_tangent+
                                  normal@raw_tangent_step))
        tangent_step = ((projected_step-
                         tangent*(tangent@projected_step)) /
                        np.linalg.norm(projected))
        frame_step = np.column_stack((
            tangent_step,
            np.cross(normal_step, tangent)+np.cross(normal, tangent_step),
            normal_step))
        if np.linalg.norm(frame_step@frame.T+frame@frame_step.T) > 1e-8:
            raise AssertionError("rail frame derivative lost orthogonality")
        return center, frame, center_step, frame_step

    def spin(self, total: np.ndarray, direction: np.ndarray, *, station: float = .5
             ) -> np.ndarray:
        """Physical frame spin from the actual shell chart derivative."""
        _, frame, _, step = self.pose(total, station=station, direction=direction)
        skew = step@frame.T
        return np.array((skew[2, 1], skew[0, 2], skew[1, 0]))


@dataclass(frozen=True)
class RailL1LogConnection:
    """Six-row objective point work at one positive-width rail station.

    The native B3 port and pose-joint laws are unchanged from the zero-width
    L1 probe. Only the shell-side pose is replaced. This is not a line mortar.
    """

    rail: FlatQ4PhysicalRail
    port: object
    beam_offset: np.ndarray
    reference_offset: np.ndarray
    station: float
    joint: RigidPoseJoint

    @classmethod
    def at_reference(cls, rail: FlatQ4PhysicalRail, total: np.ndarray,
                     port: NativeHalfCellSpatialPort, beam_state, *,
                     station: float = .5, beam_offset=(0., 0., -.05),
                     expected_reference_offset_shell=(0., 0., 0.)):
        if not isinstance(rail, FlatQ4PhysicalRail):
            raise TypeError("physical-width E4 rail required")
        if not isinstance(port, NativeHalfCellSpatialPort):
            raise TypeError("one-sided native half-cell port required")
        reference_total = np.zeros((2, len(rail.y_cuts), 6))
        if (not np.array_equal(np.asarray(total), reference_total) or
                beam_state is not port.context.initial.mechanical):
            raise ValueError("bounded rail reference requires virgin shell/native state")
        offset = _owned(beam_offset, (3,))
        expected = _owned(expected_reference_offset_shell, (3,))
        reference_shell, reference_frame, _, _ = rail.pose(
            reference_total, station=station)
        reference_high, reference_low, reference_beam_frame = port.pose_pair(
            port.context.initial.mechanical)
        reference_beam = (reference_high+reference_low+
                          reference_beam_frame@offset)
        actual_offset = reference_frame.T@(reference_beam-reference_shell)
        length_scale = max(
            np.linalg.norm(rail.reference[1, 0]-rail.reference[0, 0]),
            rail.bounds[1]-rail.bounds[0], rail.thickness,
            np.linalg.norm(offset), np.linalg.norm(expected), 1e-3)
        tolerance = 1e-10*length_scale
        origin_roundoff = (32*np.finfo(float).eps *
                           max(np.max(np.abs(reference_shell)),
                               np.max(np.abs(reference_beam))))
        if origin_roundoff > tolerance/10.:
            raise ValueError("uncompensated large-origin rail preflight is unsupported")
        if np.linalg.norm(actual_offset-expected) > tolerance:
            raise ValueError("native port and shell rail reference station/offset differ")
        shell, shell_frame, _, _ = rail.pose(total, station=station)
        high, low, beam_frame = port.pose_pair(beam_state)
        beam = high+low+beam_frame@offset
        joint = RigidPoseJoint(np.array((shell, beam), dtype=np.float64),
                               np.array((shell_frame, beam_frame),
                                        dtype=np.float64))
        return cls(rail, port, offset, expected, float(station), joint)

    def evaluate(self, total: np.ndarray, beam_state, *,
                 shell_direction: np.ndarray | None = None,
                 beam_direction: np.ndarray | None = None
                 ) -> tuple[np.ndarray, np.ndarray | None]:
        directional = shell_direction is not None or beam_direction is not None
        if directional and (shell_direction is None or beam_direction is None):
            raise ValueError("paired shell/native directions required")
        shell, shell_frame, shell_step, frame_step = self.rail.pose(
            total, station=self.station, direction=shell_direction)
        high, low, beam_frame = self.port.pose_pair(beam_state)
        arm = beam_frame@self.beam_offset
        beam = high+low+arm
        result = self.joint.evaluate(
            np.array((shell, beam), dtype=np.float64),
            np.array((shell_frame, beam_frame), dtype=np.float64),
            np.zeros(6, dtype=np.float64))
        if not directional:
            return result.constraints.copy(), None
        native_direction = _owned(beam_direction, (self.port.context.count,))
        spatial = self.port.tangent(beam_state)@native_direction
        beam_step = spatial[:3]+np.cross(spatial[3:], arm)
        shell_spin_matrix = frame_step@shell_frame.T
        shell_spin = np.array((shell_spin_matrix[2, 1],
                               shell_spin_matrix[0, 2],
                               shell_spin_matrix[1, 0]))
        pose_step = np.r_[shell_step, shell_spin, beam_step, spatial[3:]]
        return (result.constraints.copy(),
                result.constraint_jacobian@pose_step)

    def work_tangent(self, total: np.ndarray, beam_state,
                     multiplier: np.ndarray
                     ) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
        """Exact local-chart Hessian of six-channel multiplier work.

        Shell total coordinates and native increments share one predecessor.
        The generalized-resultant coordinates are absent from connection work.
        This is a bounded point operator, not segmented line assembly.
        """
        shell_shape = (2, len(self.rail.y_cuts), 6)
        q = _owned(total, shell_shape)
        lam = _owned(multiplier, (6,))
        self.joint.guard()
        owned, left, right, lift, _, rotation = self.port._parts(beam_state)
        high, low, beam_frame0 = self.port.pose_pair(owned)
        shell_size = q.size
        local_size = shell_size+9
        constant = lambda value: ad.Jet2.constant(float(value), local_size)
        variable = lambda value, index: ad.Jet2.variable(
            float(value), index, local_size)
        nodal = [[[variable(q[i, k, j], 6*(i*len(self.rail.y_cuts)+k)+j)
                   for j in range(6)] for k in range(len(self.rail.y_cuts))]
                 for i in range(2)]
        ez = [constant(0.), constant(0.), constant(1.)]
        directors = [[ad.matvec(ad.so3_exp(node[3:]), ez) for node in edge]
                     for edge in nodal]
        averaged_top, averaged_director = [], []
        for i in range(2):
            averaged_top.append([
                sum((float(self.rail.weights[k])*(
                    constant(self.rail.reference[i, k, j])+nodal[i][k][j]+
                    .5*self.rail.thickness*directors[i][k][j])
                     for k in range(len(self.rail.y_cuts))), start=constant(0.))
                for j in range(3)])
            averaged_director.append([
                sum((float(self.rail.weights[k])*directors[i][k][j]
                     for k in range(len(self.rail.y_cuts))), start=constant(0.))
                for j in range(3)])
        shell = [(1.-self.station)*averaged_top[0][j]+
                 self.station*averaged_top[1][j] for j in range(3)]
        mean = [(1.-self.station)*averaged_director[0][j]+
                self.station*averaged_director[1][j] for j in range(3)]
        normal = _jet_unit(mean, "averaged E4 director")
        raw = [averaged_top[1][j]-averaged_top[0][j] for j in range(3)]
        component = ad.dot(normal, raw)
        tangent = _jet_unit([raw[j]-normal[j]*component for j in range(3)],
                            "projected averaged material tangent")
        side = _jet_cross(normal, tangent)
        shell_frame = [[tangent[j], side[j], normal[j]] for j in range(3)]

        spin = [variable(0., shell_size+6+j) for j in range(3)]
        increment = ad.so3_exp(spin)
        beam_frame = ad.matmul(
            increment, ad.constant_matrix(beam_frame0, local_size))
        rotated_lift = ad.matvec(
            increment, [constant(value) for value in rotation@lift])
        beam_origin = [
            constant(high[j]+low[j])+
            (1.-self.port.weight)*variable(0., shell_size+j)+
            self.port.weight*variable(0., shell_size+3+j)+
            rotated_lift[j]-constant((rotation@lift)[j])
            for j in range(3)]
        arm = ad.matvec(beam_frame,
                        [constant(value) for value in self.beam_offset])
        beam = [beam_origin[j]+arm[j] for j in range(3)]

        distance = [beam[j]-shell[j] for j in range(3)]
        translation = [entry-constant(offset) for entry, offset in zip(
            ad.matvec(ad.transpose(shell_frame), distance),
            self.joint._offset)]
        relative = ad.matmul(
            ad.constant_matrix(self.joint._relative.T, local_size),
            ad.matmul(ad.transpose(shell_frame), beam_frame))
        gaps = translation+ad.so3_log(relative)
        work = sum((constant(lam[j])*gaps[j] for j in range(6)),
                   start=constant(0.))

        full_size = shell_size+self.port.context.count
        indices = list(range(shell_size))
        indices.extend(shell_size+6*left+j for j in range(3))
        indices.extend(shell_size+6*right+j for j in range(3))
        cell_column = (self.port.context.nodal_count+
                       24*self.port.element_index+3*self.port.cell)
        indices.extend(shell_size+cell_column+j for j in range(3))
        residual = np.zeros(full_size)
        hessian = np.zeros((full_size, full_size))
        residual[indices] = work.gradient
        hessian[np.ix_(indices, indices)] = work.hessian
        return (work.value, np.array([gap.value for gap in gaps]),
                residual, hessian)


@dataclass(frozen=True)
class SegmentedRailWeakWork:
    """Two material segments with exact shared-node station-work assembly.

    Two Gauss stations per segment define this bounded discrete weak action.
    The line measure is fixed reference arclength and the four six-component
    values are finite-dimensional density samples. They do not define point
    values of an arbitrary L2 equivalence class. No production multiplier
    basis, norm, or quadrature-error contract is selected.
    """

    connections: tuple[RailL1LogConnection, ...]
    weights: np.ndarray
    stations: np.ndarray
    transverse_nodes: int

    @classmethod
    def at_reference(cls, reference: np.ndarray, y_cuts: np.ndarray,
                     bounds: tuple[float, float], thickness: float,
                     port_at, beam_state, *,
                     beam_offset=(0., 0., -.05),
                     expected_reference_offset_shell=(0., 0., 0.)):
        y = np.asarray(y_cuts, dtype=float)
        if y.ndim != 1 or len(y) < 2:
            raise ValueError("transverse material cuts required")
        ref = _owned(reference, (3, len(y), 3))
        cuts = ref[:, 0, 0]
        if not np.all(np.diff(cuts) > 0.):
            raise ValueError("two ordered rail material segments required")
        abscissae = (.5-.5/np.sqrt(3.), .5+.5/np.sqrt(3.))
        connections, weights, stations = [], [], []
        for segment in range(2):
            rail = FlatQ4PhysicalRail.from_reference(
                ref[segment:segment+2], y, bounds, thickness)
            length = cuts[segment+1]-cuts[segment]
            for station in abscissae:
                physical_station = cuts[segment]+length*station
                connections.append(RailL1LogConnection.at_reference(
                    rail, np.zeros((2, len(y), 6)),
                    port_at(float(physical_station)), beam_state,
                    station=float(station), beam_offset=beam_offset,
                    expected_reference_offset_shell=
                    expected_reference_offset_shell))
                weights.append(.5*length)
                stations.append(physical_station)
        context = connections[0].port.context
        if any(c.port.context is not context for c in connections):
            raise ValueError("one native retained context required")
        return cls(tuple(connections),
                   _owned(weights, (4,)), _owned(stations, (4,)), len(y))

    def work_tangent(self, shell_total: np.ndarray, beam_state,
                     multiplier_samples: np.ndarray
                     ) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
        shell = _owned(shell_total, (3, self.transverse_nodes, 6))
        density = _owned(multiplier_samples, (4, 6))
        context = self.connections[0].port.context
        shell_size = shell.size
        size = shell_size+context.count
        gradient = np.zeros(size)
        hessian = np.zeros((size, size))
        gaps = np.empty((4, 6))
        work = 0.
        local_shell_size = 2*self.transverse_nodes*6
        beam_indices = np.arange(shell_size, size)
        for sample, connection in enumerate(self.connections):
            segment = sample//2
            local_work, gap, local_gradient, local_hessian = (
                connection.work_tangent(
                    shell[segment:segment+2], beam_state,
                    self.weights[sample]*density[sample]))
            shell_indices = np.arange(
                segment*self.transverse_nodes*6,
                (segment+2)*self.transverse_nodes*6)
            indices = np.r_[shell_indices, beam_indices]
            if len(indices) != len(local_gradient) or (
                    local_hessian.shape != (len(indices), len(indices))):
                raise AssertionError("shared rail/native scatter layout changed")
            work += local_work
            gaps[sample] = gap
            gradient[indices] += local_gradient
            hessian[np.ix_(indices, indices)] += local_hessian
        return work, gaps, gradient, hessian
