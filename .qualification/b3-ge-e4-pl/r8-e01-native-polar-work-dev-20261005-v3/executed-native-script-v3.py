"""Unadopted projected-polar work composed with actual NativeHalfCellPort.

33 local coordinates: shell24 + two native endpoint translations6 + ONE
retained half-cell spatial rotation3. All other native variables stay explicit
and untouched; this trace is not full native element work or product dispatch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

from anysolver import _ge_beam3_mixed_ad as ad
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._stiffened_shell_l1_local_experimental import NativeHalfCellPort
from anysolver._ge_beam3_p5.algebra import rotation as retained_rotation
from scripts import r8_e01_objective_polar_trace as polar


IDENTITY = "R8_E01_NATIVE_HALF_CELL_PROJECTED_POLAR_WORK_V1_PROPOSAL"
SIZE = 33


def _rotated_lift_increment(spin, lift):
    """(Exp(spin)-I) lift without adding/subtracting the identity.

    Rodrigues coefficients are the existing AD primitive's coefficients. This
    also retains the small second-order diagonal terms, rather than rounding
    Exp's diagonal to one before subtracting one.
    """
    a, b = ad._exp_coefficients(ad.dot(spin, spin))
    skew = ad.skew(spin); square = ad.matmul(skew, skew)
    difference = [[a*skew[i][j]+b*square[i][j] for j in range(3)] for i in range(3)]
    return ad.matvec(difference, lift)


@dataclass(frozen=True)
class ShellState:
    positions: np.ndarray
    directors: np.ndarray

    def __post_init__(self):
        checked = polar.PhysicalState(self.positions, self.directors, np.zeros(3), np.eye(3))
        object.__setattr__(self, "positions", checked.positions)
        object.__setattr__(self, "directors", checked.directors)


@dataclass(frozen=True)
class NativeEvaluation:
    local: polar.TraceEvaluation
    beam_slots: np.ndarray
    global_slots: np.ndarray
    beam_position_high: np.ndarray
    beam_position_low: np.ndarray
    beam_rotation: np.ndarray
    inactive_native_coordinates: int


@dataclass(frozen=True)
class NativePolarWork:
    trace: polar.PolarTrace
    port: NativeHalfCellPort
    reference_arm: np.ndarray
    shell_slots: np.ndarray
    native_base: int
    _global_slots: np.ndarray = field(init=False, repr=False, compare=False)

    @classmethod
    def at_reference(cls, xy, station, port, mechanical, shell_slots, *,
                     native_base=0, shell_offset=(0., 0., 0.)):
        if type(port) is not NativeHalfCellPort:
            raise polar.TraceDomainError("actual NativeHalfCellPort required")
        high, low, frame = port.pose_pair(mechanical)
        beam = np.array([math.fsum((float(h), float(l))) for h, l in zip(high, low, strict=True)])
        trace = polar.PolarTrace(xy, station, beam, frame, shell_offset)
        center = np.r_[trace.station, 0.]
        arm = np.array([math.fsum((float(high[j]), float(low[j]), -float(center[j]))) for j in range(3)])
        return cls(trace, port, arm, shell_slots, native_base)

    def __post_init__(self):
        if type(self.trace) is not polar.PolarTrace or type(self.port) is not NativeHalfCellPort:
            raise polar.TraceDomainError("owned trace and actual native port required")
        maximum = int(np.iinfo(np.intp).max)
        if type(self.native_base) is not int or not 0 <= self.native_base <= maximum:
            raise polar.TraceDomainError("explicit nonnegative native global base required")
        slots = np.asarray(self.shell_slots)
        if slots.shape != (24,) or slots.dtype.kind not in 'iu':
            raise polar.TraceDomainError("24 explicit integer shell gather slots required")
        # Python integers preserve unsigned input and addition before any intp
        # conversion or NumPy promotion/wraparound can change their identity.
        shell_values = [int(value) for value in slots]
        active = self.port.active_beam_slots()
        if active.shape != (9,) or active.dtype.kind not in 'iu':
            raise polar.TraceDomainError("native gather slots must fit intp")
        native_values = [self.native_base+int(value) for value in active]
        values = shell_values+native_values
        if any(value < 0 or value > maximum for value in values):
            raise polar.TraceDomainError("global gather slots must fit nonnegative intp")
        all_slots = np.array(values, dtype=np.intp)
        if len(np.unique(all_slots)) != SIZE:
            raise polar.TraceDomainError("shell/native global gather slots overlap")
        object.__setattr__(self, "shell_slots", np.frombuffer(all_slots[:24].tobytes(), dtype=np.intp))
        object.__setattr__(self, "_global_slots", np.frombuffer(all_slots.tobytes(), dtype=np.intp))
        object.__setattr__(self, "reference_arm", polar._owned(self.reference_arm, (3,), "compensated reference arm"))

    def evaluate(self, shell, mechanical, multipliers, *, increments=None):
        if type(shell) is not ShellState:
            raise polar.TraceDomainError("owned physical shell state required")
        delta = np.zeros(SIZE) if increments is None else polar._owned(increments, (SIZE,), "local native increments")
        lam = polar._owned(multipliers, (6,), "constraint multipliers")
        parts = self.port.parts(mechanical)
        high, low, frame = self.port._pose_from_parts(parts)
        rotation = parts[-1]
        constant = lambda v: ad.Jet2.constant(float(v), SIZE)
        variables = [ad.Jet2.variable(v, i, SIZE) for i, v in enumerate(delta)]
        x = [[constant(shell.positions[i, j])+variables[6*i+j] for j in range(3)] for i in range(4)]
        directors = [ad.matvec(ad.so3_exp(variables[6*i+3:6*i+6]),
                              [constant(v) for v in shell.directors[i]]) for i in range(4)]
        increment = ad.so3_exp(variables[30:33])
        beam_frame = ad.matmul(increment, ad.constant_matrix(frame, SIZE))
        lift0 = rotation@self.port.lift
        lift_increment = _rotated_lift_increment(variables[30:33], [constant(v) for v in lift0])
        # NativeHalfCellPort owns the compensated pose boundary. Subtract the
        # shell origin with fsum BEFORE collapsing the high/low beam position.
        relative = [constant(math.fsum((float(high[j]), float(low[j]), -float(shell.positions[0, j]))))+
                    (1.-self.port.weight)*variables[24+j]+self.port.weight*variables[27+j]+
                    lift_increment[j]-variables[j] for j in range(3)]
        try:
            trace_parts = polar._trace_from_jets(self.trace, x, directors, None, beam_frame,
                beam_origin_relative=relative, reference_arm=self.reference_arm)
            local = polar._evaluation_from_jets(trace_parts, lam, delta)
        except (FloatingPointError, OverflowError, ZeroDivisionError) as error:
            raise polar.TraceDomainError("finite native local derivative domain required") from error
        beam_slots = np.frombuffer(self.port.active_beam_slots().astype(np.intp).tobytes(), dtype=np.intp)
        slots = self._global_slots
        return NativeEvaluation(local, beam_slots, slots,
            polar._owned(high, (3,), "native pose high"), polar._owned(low, (3,), "native pose low"),
            polar._owned(frame, (3, 3), "native physical pose frame"), self.port.retained_count-9)


def updated_shell(shell, increments):
    delta = polar._owned(increments, (24,), "shell increments")
    dummy = polar.PhysicalState(shell.positions, shell.directors, np.zeros(3), np.eye(3))
    moved = polar.updated(dummy, np.r_[delta, np.zeros(6)])
    return ShellState(moved.positions, moved.directors)


def updated_native(mechanical, port, increments):
    """Exact selected-coordinate update pattern of native Context.advance.

    This returns a new Mechanical; it does not issue/commit an owner state.
    Nodal frames, the other cell rotation and all resultants are unchanged.
    """
    port.parts(mechanical)
    delta = polar._owned(increments, (9,), "native active increments")
    if np.linalg.norm(delta[6:]) >= .9*np.pi:
        raise polar.TraceDomainError("native retained rotation increment requires cutback")
    copied = {key: np.array(value, copy=True) for key, value in mechanical.descriptor().items()}
    for i, node in enumerate(port.nodes):
        for j in range(3):
            copied['positions'][node, j], copied['position_low'][node, j] = split_sum((
                float(mechanical.positions[node, j]), float(mechanical.position_low[node, j]), float(delta[3*i+j])))
    copied['cell_rotations'][port.element_index, port.cell] = (
        retained_rotation(delta[6:]) @ mechanical.cell_rotations[port.element_index, port.cell])
    return Mechanical(**copied)


def wrench_balance(shell, mechanical, operator, evaluation, origin=(0., 0., 0.)):
    if evaluation.local.coordinate_kind != 'spatial_left_physical':
        raise polar.TraceDomainError("recenter before interpreting native physical wrenches")
    origin = polar._owned(origin, (3,), "moment origin")
    shell_g = evaluation.local.covector[:24].reshape(4, 6)
    beam = evaluation.local.covector[24:]
    parts = operator.port.parts(mechanical)
    # Moments act at the actual endpoint positions, not the interpolated port.
    endpoint = np.array([[math.fsum((float(h[j]), float(l[j]), -float(origin[j]))) for j in range(3)]
                         for h, l in ((parts[0], parts[1]), (parts[2], parts[3]))])
    force = shell_g[:, :3].sum(axis=0)+beam[:3]+beam[3:6]
    moment = (np.cross(shell.positions-origin, shell_g[:, :3]).sum(axis=0)+shell_g[:, 3:].sum(axis=0)+
              np.cross(endpoint[0], beam[:3])+np.cross(endpoint[1], beam[3:6])+beam[6:])
    return force, moment
