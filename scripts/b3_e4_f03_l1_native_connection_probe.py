"""One-point L1 six-channel kinematic probe; no selected law or F03 claim.

The E4 line uses its physical top-face nodal positions and directors.  Its
frame is made from the mean director and the projected top-face material-line
tangent.  The beam side is an actual retained B3 open-half-cell port.  The
reference-offset SO(3) Log pairing reuses the existing pose-joint operator;
its derivative is pulled through both physical traces.  This is not an
integrated connection or an accepted line law.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from anysolver import _ge_beam3_mixed_ad as ad
from anysolver._ge_beam3_pose_joint import RigidPoseJoint
from anysolver.corotational import rotation_matrix_from_vector


def _unit(vector: np.ndarray, label: str) -> np.ndarray:
    size = float(np.linalg.norm(vector))
    if not np.isfinite(size) or size <= 1e-10:
        raise ValueError(f"degenerate {label}")
    return vector / size


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _vee(matrix: np.ndarray) -> np.ndarray:
    return np.array((matrix[2, 1], matrix[0, 2], matrix[1, 0]))


def _jet_unit(vector: list[ad.Jet2], label: str) -> list[ad.Jet2]:
    squared = ad.dot(vector, vector)
    if not np.isfinite(squared.value) or squared.value <= 1e-20:
        raise ValueError(f"degenerate {label}")
    length = ad.sqrt(squared)
    return [entry/length for entry in vector]


def _jet_cross(left: list[ad.Jet2], right: list[ad.Jet2]) -> list[ad.Jet2]:
    return [left[1]*right[2]-left[2]*right[1],
            left[2]*right[0]-left[0]*right[2],
            left[0]*right[1]-left[1]*right[0]]


def spatial_gap(shell: np.ndarray, shell_frame: np.ndarray,
                beam: np.ndarray, beam_frame: np.ndarray) -> np.ndarray:
    """Early local axial-skew comparator for physical poses."""
    relative = shell_frame.T@beam_frame
    # The axial-skew angular chart loses its axial derivative at 90 degrees.
    # Retained only as a bounded comparator for the Log prototype below.
    if float(np.trace(relative)) <= 1. + 1e-8:
        raise ValueError("relative rotation lies outside the local probe chart")
    return np.r_[shell_frame.T@(shell-beam),
                 .5*_vee(relative-relative.T)]


def shell_trace(reference: np.ndarray, total: np.ndarray, thickness: float,
                direction: np.ndarray | None = None
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]:
    """Physical E4 top point/frame and their total-coordinate variation."""
    reference = np.asarray(reference, dtype=float)
    total = np.asarray(total, dtype=float)
    if (reference.shape != (2, 3) or total.shape != (2, 6) or
            not np.isfinite(reference).all() or not np.isfinite(total).all() or
            not np.isfinite(thickness) or thickness <= 0):
        raise ValueError("two finite E4 line nodes and positive thickness required")
    if direction is not None:
        direction = np.asarray(direction, dtype=float)
        if direction.shape != (2, 6) or not np.isfinite(direction).all():
            raise ValueError("two finite E4 variation nodes required")
    directors, director_steps = [], []
    for node in range(2):
        theta = total[node, 3:]
        director = rotation_matrix_from_vector(theta)[:, 2]
        directors.append(director)
        if direction is not None:
            eps = ad.Jet2.variable(0., 0, 1)
            spin = [ad.Jet2.constant(theta[j], 1) +
                    eps * direction[node, 3+j] for j in range(3)]
            jet = ad.so3_exp(spin)
            director_steps.append(np.array([jet[j][2].gradient[0]
                                            for j in range(3)]))
    top = reference + total[:, :3] + .5*thickness*np.asarray(directors)
    center = .5*(top[0]+top[1])
    mean_director = .5*(directors[0]+directors[1])
    normal = _unit(mean_director, "E4 mean director")
    raw_tangent = top[1]-top[0]
    projection = raw_tangent-normal*(normal@raw_tangent)
    tangent = _unit(projection, "projected E4 material-line tangent")
    frame = np.column_stack((tangent, np.cross(normal, tangent), normal))
    if direction is None:
        return center, frame, None, None
    top_step = direction[:, :3] + .5*thickness*np.asarray(director_steps)
    center_step = .5*(top_step[0]+top_step[1])
    mean_step = .5*(director_steps[0]+director_steps[1])
    normal_step = (mean_step-normal*(normal@mean_step))/np.linalg.norm(mean_director)
    raw_step = top_step[1]-top_step[0]
    projected_step = (raw_step-normal_step*(normal@raw_tangent)-
                      normal*(normal_step@raw_tangent+normal@raw_step))
    tangent_step = (projected_step-tangent*(tangent@projected_step))/np.linalg.norm(projection)
    frame_step = np.column_stack((tangent_step,
                                  np.cross(normal_step, tangent)+np.cross(normal, tangent_step),
                                  normal_step))
    return center, frame, center_step, frame_step


def six_gap(reference: np.ndarray, total: np.ndarray, thickness: float,
            port, beam_state, *, shell_direction: np.ndarray | None = None,
            beam_direction: np.ndarray | None = None,
            beam_offset: tuple[float, float, float] = (0., 0., -.05)
            ) -> tuple[np.ndarray, np.ndarray | None]:
    """Six rows and exact first variation through the actual B3 update chart.

    Rows 0:3 are shell-top minus B3-bottom displacement in the shell line
    frame.  Rows 3:6 are the axial skew of shell-frame transpose times the B3
    frame.  The angular chart is locally full rank, but not a global SO(3) Log.
    """
    directional = shell_direction is not None or beam_direction is not None
    if directional and (shell_direction is None or beam_direction is None):
        raise ValueError("paired E4/B3 directions required")
    shell, frame, shell_step, frame_step = shell_trace(
        reference, total, thickness, shell_direction)
    high, low, beam_frame = port.pose_pair(beam_state)
    offset = np.asarray(beam_offset, dtype=float)
    if offset.shape != (3,) or not np.isfinite(offset).all():
        raise ValueError("finite B3 section offset required")
    arm = beam_frame@offset
    beam = high+low+arm
    gap = spatial_gap(shell, frame, beam, beam_frame)
    if not directional:
        return gap, None
    beam_direction = np.asarray(beam_direction, dtype=float)
    if (beam_direction.shape != (port.context.count,) or
            not np.isfinite(beam_direction).all()):
        raise ValueError("complete finite retained B3 direction required")
    spatial = port.tangent(beam_state)@beam_direction
    beam_step = spatial[:3]+np.cross(spatial[3:], arm)
    beam_frame_step = _skew(spatial[3:])@beam_frame
    relative_step = frame_step.T@beam_frame+frame.T@beam_frame_step
    derivative = np.r_[frame_step.T@(shell-beam)+frame.T@(shell_step-beam_step),
                       .5*_vee(relative_step-relative_step.T)]
    return gap, derivative


@dataclass(frozen=True)
class L1LogConnection:
    """Reference-offset Log pairing on the two physical L1 trace poses.

    The supplied pose joint defines e=Fs0.T(rb0-rs0), A=Fs0.T Fb0 and
    c=[Fs.T(rb-rs)-e, Log(A.T Fs.T Fb)]. Its existing spatial Jacobian is
    pulled through the E4 total-coordinate and B3 retained-update maps.
    ``evaluate`` composes first variation; ``work_tangent`` composes the
    local-chart Hessian through both maps. Neither is integrated line work.
    """

    reference: np.ndarray
    thickness: float
    port: object
    beam_offset: tuple[float, float, float]
    joint: RigidPoseJoint

    @classmethod
    def at_reference(cls, reference: np.ndarray, total: np.ndarray,
                     thickness: float, port, beam_state, *,
                     beam_offset: tuple[float, float, float] = (0., 0., -.05)):
        reference = np.asarray(reference, dtype=float).copy()
        shell, shell_frame, _, _ = shell_trace(reference, total, thickness)
        high, low, beam_frame = port.pose_pair(beam_state)
        offset = np.asarray(beam_offset, dtype=float)
        if offset.shape != (3,) or not np.isfinite(offset).all():
            raise ValueError("finite B3 section offset required")
        beam = high+low+beam_frame@offset
        joint = RigidPoseJoint(np.array((shell, beam), dtype=np.float64),
                               np.array((shell_frame, beam_frame), dtype=np.float64))
        owned_reference = np.frombuffer(reference.tobytes(), dtype=float).reshape(
            reference.shape)
        return cls(owned_reference, float(thickness), port, tuple(offset), joint)

    def evaluate(self, total: np.ndarray, beam_state, *,
                 shell_direction: np.ndarray | None = None,
                 beam_direction: np.ndarray | None = None
                 ) -> tuple[np.ndarray, np.ndarray | None]:
        directional = shell_direction is not None or beam_direction is not None
        if directional and (shell_direction is None or beam_direction is None):
            raise ValueError("paired E4/B3 directions required")
        shell, shell_frame, shell_step, frame_step = shell_trace(
            self.reference, total, self.thickness, shell_direction)
        high, low, beam_frame = self.port.pose_pair(beam_state)
        arm = beam_frame@np.asarray(self.beam_offset)
        beam = high+low+arm
        poses = np.array((shell, beam), dtype=np.float64)
        frames = np.array((shell_frame, beam_frame), dtype=np.float64)
        evaluation = self.joint.evaluate(poses, frames, np.zeros(6, dtype=np.float64))
        if not directional:
            return evaluation.constraints.copy(), None
        beam_direction = np.asarray(beam_direction, dtype=float)
        if (beam_direction.shape != (self.port.context.count,) or
                not np.isfinite(beam_direction).all()):
            raise ValueError("complete finite retained B3 direction required")
        spatial = self.port.tangent(beam_state)@beam_direction
        beam_step = spatial[:3]+np.cross(spatial[3:], arm)
        spin = frame_step@shell_frame.T
        shell_spin = .5*_vee(spin-spin.T)
        pose_step = np.r_[shell_step, shell_spin, beam_step, spatial[3:]]
        return (evaluation.constraints.copy(),
                evaluation.constraint_jacobian@pose_step)

    def work_tangent(self, total: np.ndarray, beam_state,
                     multipliers: np.ndarray
                     ) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
        """Local-chart value, six gaps, residual and composed Hessian.

        The chart is additive E4 total coordinates and one native
        ``Context.advance`` exponential from ``beam_state``. The 21 active
        variables are 12 E4 coordinates, two B3 endpoint translations and
        one retained half-cell rotation. Resultant and unrelated columns are
        exactly zero in the returned full coordinate arrays. This is the
        Hessian of multiplier work, not a material stiffness or assembled law.
        The current high/low position sum is verified at ordinary coordinates;
        large-origin compensated accuracy remains a separate check.
        """
        total = np.asarray(total, dtype=float)
        multiplier = np.asarray(multipliers, dtype=float)
        if total.shape != (2, 6) or not np.isfinite(total).all():
            raise ValueError("finite two-node E4 total coordinates required")
        if multiplier.shape != (6,) or not np.isfinite(multiplier).all():
            raise ValueError("finite six-channel multipliers required")
        self.joint.guard()
        owned, left, right, lift, _, rotation = self.port._parts(beam_state)
        high, low, beam_frame0 = self.port.pose_pair(owned)
        local_size = 21
        constant = lambda value: ad.Jet2.constant(float(value), local_size)
        nodal = [[ad.Jet2.variable(total[i, j], 6*i+j, local_size)
                  for j in range(6)] for i in range(2)]
        ez = [constant(0.), constant(0.), constant(1.)]
        directors = [ad.matvec(ad.so3_exp(node[3:]), ez) for node in nodal]
        top = [[constant(self.reference[i, j])+nodal[i][j]+
                .5*self.thickness*directors[i][j] for j in range(3)]
               for i in range(2)]
        shell = [(top[0][j]+top[1][j])*.5 for j in range(3)]
        mean = [(directors[0][j]+directors[1][j])*.5 for j in range(3)]
        normal = _jet_unit(mean, "E4 mean director")
        raw = [top[1][j]-top[0][j] for j in range(3)]
        component = ad.dot(normal, raw)
        tangent = _jet_unit([raw[j]-normal[j]*component for j in range(3)],
                            "projected E4 material-line tangent")
        side = _jet_cross(normal, tangent)
        shell_frame = [[tangent[j], side[j], normal[j]] for j in range(3)]

        spin = [ad.Jet2.variable(0., 18+j, local_size) for j in range(3)]
        increment = ad.so3_exp(spin)
        beam_frame = ad.matmul(increment, ad.constant_matrix(beam_frame0, local_size))
        rotated_lift = ad.matvec(increment,
                                 [constant(v) for v in rotation@lift])
        beam_origin = [constant(high[j]+low[j])+
                       (1.-self.port.weight)*ad.Jet2.variable(0., 12+j, local_size)+
                       self.port.weight*ad.Jet2.variable(0., 15+j, local_size)+
                       rotated_lift[j]-constant((rotation@lift)[j])
                       for j in range(3)]
        arm = ad.matvec(beam_frame, [constant(v) for v in self.beam_offset])
        beam = [beam_origin[j]+arm[j] for j in range(3)]

        distance = [beam[j]-shell[j] for j in range(3)]
        translation = [entry-constant(offset) for entry, offset in zip(
            ad.matvec(ad.transpose(shell_frame), distance), self.joint._offset)]
        relative = ad.matmul(
            ad.constant_matrix(self.joint._relative.T, local_size),
            ad.matmul(ad.transpose(shell_frame), beam_frame))
        gaps = translation+ad.so3_log(relative)
        work = sum((constant(multiplier[j])*gaps[j] for j in range(6)),
                   start=constant(0.))
        full_size = 12+self.port.context.count
        indices = list(range(12))
        indices.extend(12+6*left+j for j in range(3))
        indices.extend(12+6*right+j for j in range(3))
        cell_column = (self.port.context.nodal_count+
                       24*self.port.element_index+3*self.port.cell)
        indices.extend(12+cell_column+j for j in range(3))
        residual = np.zeros(full_size)
        hessian = np.zeros((full_size, full_size))
        residual[indices] = work.gradient
        hessian[np.ix_(indices, indices)] = work.hessian
        return (work.value, np.array([entry.value for entry in gaps]),
                residual, hessian)
