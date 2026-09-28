"""One-point L1 six-channel kinematic probe; no selected law or F03 claim.

The E4 line uses its physical top-face nodal positions and directors.  Its
frame is made from the mean director and the projected top-face material-line
tangent.  The beam side is an actual retained B3 open-half-cell port.  This
local residual is a candidate for subsequent work and multiplier studies, not
an integrated connection or a finite-rotation Log law.
"""

from __future__ import annotations

import numpy as np

from anysolver import _ge_beam3_mixed_ad as ad
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


def spatial_gap(shell: np.ndarray, shell_frame: np.ndarray,
                beam: np.ndarray, beam_frame: np.ndarray) -> np.ndarray:
    """Objective six-row point pairing for independently supplied physical poses."""
    relative = shell_frame.T@beam_frame
    # The axial-skew angular chart loses its axial derivative at 90 degrees.
    # This probe is local; a production line law needs a separately derived Log.
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
