"""Bounded segmented six-channel F03 weak-line work diagnostic.

This is an exploratory Lagrange-multiplier work integral, evaluated by
bounded Gauss quadrature over fixed reference correspondence. It composes
verified station ports and includes a small reference KKT oracle. It selects
neither a stable multiplier space nor a production attachment implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_pose_joint import RigidPoseJoint
from anysolver._ge_beam3_retained_generalized_state import Mechanical

from scripts._b3_e4_f03_coupled_point_work_candidate import (
    directional_point_work)
from scripts._b3_e4_f03_e4_trial_panel import (
    FlatE4TrialPanel, TrialPanelResponse)
from scripts._b3_e4_f03_native_fixture import Fixture, SECTION_DIAGONAL
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import pose_from_e4_total
from scripts._b3_e4_f03_shell_local_translation_candidate import (
    pose_from_e4_total_local_translation,
    pose_from_e4_total_local_director,
    pose_from_e4_total_local_frame,
    reference_spatial_trace_local_translation,
    reference_spatial_trace_local_director,
    reference_spatial_trace_local_frame)
from scripts._b3_e4_f03_shell_spatial_linear_port import reference_spatial_trace
from scripts._b3_e4_f03_shell_strip_pose_candidate import (
    pose_from_e4_total_strip, reference_spatial_trace_strip)
from scripts._b3_e4_f03_shell_chord_pose_candidate import (
    pose_from_e4_total_chord, reference_spatial_trace_chord)


@dataclass(frozen=True)
class LineMultiplierSpace:
    """P0, continuous P1 or local biorthogonal dual-P1 six-vectors."""

    kind: str
    knots: tuple[float, ...]

    def __post_init__(self) -> None:
        values = np.asarray(self.knots, dtype=float)
        if (self.kind not in ("piecewise_constant", "continuous_linear",
                              "dual_linear") or
                values.ndim != 1 or len(values) < 2 or
                not np.isfinite(values).all() or
                values[0] != 0. or values[-1] != 1. or
                not np.all(np.diff(values) > 0.)):
            raise ValueError("valid fixed line multiplier space required")
        object.__setattr__(self, "knots", tuple(float(value) for value in values))

    @property
    def count(self) -> int:
        return len(self.knots)-1 if self.kind == "piecewise_constant" else len(self.knots)

    def values(self, station: float) -> np.ndarray:
        if not np.isfinite(station) or not 0. <= station <= 1.:
            raise ValueError("finite line station in [0, 1] required")
        index = min(int(np.searchsorted(self.knots, station, side="right"))-1,
                    len(self.knots)-2)
        out = np.zeros(self.count)
        if self.kind == "piecewise_constant":
            out[index] = 1.
        else:
            fraction = ((station-self.knots[index]) /
                        (self.knots[index+1]-self.knots[index]))
            if self.kind == "continuous_linear":
                out[index:index+2] = (1.-fraction, fraction)
            else:
                # On one cell, psi_L=2*N_L-N_R and psi_R=2*N_R-N_L.
                # Assembly is biorthogonal to the continuous P1 nodal hats.
                out[index:index+2] = (2.-3.*fraction, 3.*fraction-1.)
        return out


@dataclass(frozen=True)
class WeakLineWork:
    potential: float
    weak_constraints: np.ndarray
    weak_first: np.ndarray
    weak_second: np.ndarray
    first: float
    second: float
    mixed: float
    segment_count: int
    quadrature_count: int
    shell_trial: TrialPanelResponse


@dataclass(frozen=True)
class ReferenceKKT:
    """Small dense oracle of the virgin constrained reference linearization."""

    primal_tangent: np.ndarray
    constraint_jacobian: np.ndarray
    free_primal: np.ndarray
    system: np.ndarray
    coordinate_scale: np.ndarray
    energy_scale: float
    scaled_system: np.ndarray
    segment_count: int
    shell_support_policy: str


def segments(shell: FlatE4TrialPanel, beam: Fixture,
             space: LineMultiplierSpace, *,
             shell_port: str = "rail") -> np.ndarray:
    """Split at shell hosts, native half-cells, and multiplier knots."""
    if not isinstance(shell, FlatE4TrialPanel) or not isinstance(beam, Fixture):
        raise TypeError("bounded E4 and native B3 fixtures required")
    shell.guard()
    beam.context.guard()
    if shell_port == "local_frame":
        shell_sites = -.5+np.arange(shell.panel.x_interval_count+1)/shell.panel.n_s
        shell_sites = shell_sites[(shell_sites >= 0.) & (shell_sites <= 1.)]
        shell_sites = np.r_[0., shell_sites, 1.]
    elif shell_port == "physical_strip_020_023":
        x_grid = -.5+np.arange(shell.panel.x_interval_count+1)/shell.panel.n_s
        sites = [0., 1.]
        for edge in x_grid:
            sites.extend((edge-.2, edge+.2))
        if shell.panel.topology == "S3-V2D":
            for y in (-.23, .23):
                eta = (y+.5)*shell.panel.n_y
                eta -= np.floor(eta)
                for edge in x_grid[:-1]:
                    diagonal = edge+eta/shell.panel.n_s
                    sites.extend((diagonal-.2, diagonal+.2))
        shell_sites = np.array([s for s in sites if 0. <= s <= 1.])
    elif shell_port == "line_chord_020":
        x_grid = -.5+np.arange(shell.panel.x_interval_count+1)/shell.panel.n_s
        hosts = list(x_grid)
        if shell.panel.topology == "S3-V2D":
            eta = .5*shell.panel.n_y
            eta -= np.floor(eta)
            hosts.extend(x_grid[:-1]+eta/shell.panel.n_s)
        shell_sites = np.array([
            x-offset for x in hosts for offset in (0., -.2, .2)
            if 0. <= x-offset <= 1.])
    elif shell_port in ("rail", "local_translation", "local_director"):
        shell_sites = shell.panel.breakpoints()
    else:
        raise ValueError("unknown bounded shell pose port")
    sites = np.r_[shell_sites,
                  np.arange(beam.n_half_cells+1)/beam.n_half_cells,
                  space.knots]
    edges = np.unique(np.round(sites, 14))
    if (edges[0] != 0. or edges[-1] != 1. or
            np.min(np.diff(edges)) <= 1e-12):
        raise ValueError("degenerate segmented line")
    return edges


def integrate_weak_line(
        shell: FlatE4TrialPanel, beam: Fixture,
        space: LineMultiplierSpace, multipliers: np.ndarray,
        shell_reference_total: np.ndarray, shell_total: np.ndarray,
        shell_first: np.ndarray, shell_second: np.ndarray,
        beam_state: Mechanical, beam_first: np.ndarray,
        beam_second: np.ndarray, *, order: int = 4,
        shell_port: str = "rail") -> WeakLineWork:
    """Integrate exact multiplier work and its physical directional Hessian.

    The reference joint is captured separately at every material station.
    The E4 material trial uses the same total coordinates as the shell pose.
    The native B3 state is a complete retained mechanical trial. No candidate
    from either domain is accepted by this diagnostic.
    """
    if not isinstance(space, LineMultiplierSpace):
        raise TypeError("line multiplier space required")
    if shell_port not in ("rail", "local_translation", "local_director",
                          "local_frame", "physical_strip_020_023",
                          "line_chord_020"):
        raise ValueError("unknown bounded shell pose port")
    pose_map = {"rail": pose_from_e4_total,
                "local_translation": pose_from_e4_total_local_translation,
                "local_director": pose_from_e4_total_local_director,
                "local_frame": pose_from_e4_total_local_frame,
                "physical_strip_020_023": lambda p, s, u: (
                    pose_from_e4_total_strip(
                        p, s, u, half_length=.2, half_width=.23)),
                "line_chord_020": pose_from_e4_total_chord}[shell_port]
    if type(order) is not int or order not in (2, 3, 4, 5):
        raise ValueError("bounded Gauss order 2 through 5 required")
    coefficients = np.asarray(multipliers, dtype=float)
    if (coefficients.shape != (space.count, 6) or
            not np.isfinite(coefficients).all()):
        raise ValueError("finite six-vector multiplier coefficients required")
    edges = segments(shell, beam, space, shell_port=shell_port)
    # Both calls validate complete vectors and predecessor/definition identity.
    shell.evaluate(shell_reference_total, .5)
    shell_trial = shell.evaluate(shell_total, .5)
    points, weights = np.polynomial.legendre.leggauss(order)
    weak = np.zeros((space.count, 6))
    weak_first = np.zeros_like(weak)
    weak_second = np.zeros_like(weak)
    potential = first = second = mixed = 0.
    for left, right in zip(edges[:-1], edges[1:]):
        half = .5*(right-left)
        center = .5*(left+right)
        for point, gauss_weight in zip(points, weights):
            station = center+half*point
            basis = space.values(station)
            element, cell, fraction, _ = beam._locate(station)
            port = NativeHalfCellSpatialPort(
                beam.context, element, cell, fraction)
            shell_ref_position, shell_ref_frame = pose_map(
                shell.panel, station, shell_reference_total)
            beam_high, beam_low, beam_frame = port.pose_pair(
                beam.context.initial.mechanical)
            joint = RigidPoseJoint(
                np.array((shell_ref_position, beam_high+beam_low)),
                np.array((shell_ref_frame, beam_frame)))
            local = directional_point_work(
                joint, shell.panel, station, shell_total,
                shell_first, shell_second, port, beam_state,
                beam_first, beam_second, basis@coefficients,
                shell_port=shell_port)
            measure = half*gauss_weight
            potential += measure*local.potential
            weak += measure*basis[:, None]*local.constraints[None, :]
            weak_first += measure*basis[:, None]*local.constraints_first[None, :]
            weak_second += measure*basis[:, None]*local.constraints_second[None, :]
            first += measure*local.first
            second += measure*local.second
            mixed += measure*local.mixed
    return WeakLineWork(float(potential), weak, weak_first, weak_second,
                        float(first), float(second), float(mixed), len(edges)-1,
                        order*(len(edges)-1), shell_trial)


def assemble_reference_kkt(shell: FlatE4TrialPanel, beam: Fixture,
                           space: LineMultiplierSpace, *,
                           order: int = 4,
                           shell_port: str = "rail",
                           shell_support_policy: str = "legacy_three_left_nodes"
                           ) -> ReferenceKKT:
    """Assemble a bounded zero-multiplier shell/B3/weak-line KKT oracle.

    The shell and beam are at their flat virgin reference. The historical
    default fixes all six coordinates at three left-edge shell nodes.
    ``full_left_edge`` fixes all six coordinates at every left-edge node.
    ``both_xy_edges`` fixes in-plane coordinates at both complete x edges,
    plus out-of-plane coordinates on the left edge to remove rigid modes.
    This is a small full-matrix derivation check, not production assembly.
    """
    if not isinstance(space, LineMultiplierSpace):
        raise TypeError("line multiplier space required")
    if shell_port not in ("rail", "local_translation", "local_director",
                          "local_frame", "physical_strip_020_023",
                          "line_chord_020"):
        raise ValueError("unknown bounded shell pose port")
    if shell_support_policy not in ("legacy_three_left_nodes",
                                    "full_left_edge", "both_xy_edges"):
        raise ValueError("unknown bounded shell support policy")
    pose_map = {"rail": pose_from_e4_total,
                "local_translation": pose_from_e4_total_local_translation,
                "local_director": pose_from_e4_total_local_director,
                "local_frame": pose_from_e4_total_local_frame,
                "physical_strip_020_023": lambda p, s, u: (
                    pose_from_e4_total_strip(
                        p, s, u, half_length=.2, half_width=.23)),
                "line_chord_020": pose_from_e4_total_chord}[shell_port]
    reference_trace = {
        "rail": reference_spatial_trace,
        "local_translation": reference_spatial_trace_local_translation,
        "local_director": reference_spatial_trace_local_director,
        "local_frame": reference_spatial_trace_local_frame,
        "physical_strip_020_023": lambda p, s: (
            reference_spatial_trace_strip(
                p, s, half_length=.2, half_width=.23)),
        "line_chord_020": reference_spatial_trace_chord}[shell_port]
    if type(order) is not int or order not in (2, 3, 4, 5):
        raise ValueError("bounded Gauss order 2 through 5 required")
    edges = segments(shell, beam, space, shell_port=shell_port)
    shell_size = 6*shell.panel.node_count
    beam_size = beam.context.count
    shell_trial = shell.evaluate(np.zeros(shell_size), .5)
    primal = np.zeros((shell_size+beam_size,)*2)
    primal[:shell_size, :shell_size] = shell_trial.tangent
    primal[shell_size:, shell_size:] = beam.tangent.toarray()
    constraint = np.zeros((6*space.count, shell_size+beam_size))
    points, weights = np.polynomial.legendre.leggauss(order)
    shell_zero = np.zeros(shell_size)
    for left, right in zip(edges[:-1], edges[1:]):
        half, center = .5*(right-left), .5*(left+right)
        for point, gauss_weight in zip(points, weights):
            station = center+half*point
            element, cell, fraction, _ = beam._locate(station)
            port = NativeHalfCellSpatialPort(
                beam.context, element, cell, fraction)
            shell_position, shell_frame = pose_map(
                shell.panel, station, shell_zero)
            beam_high, beam_low, beam_frame = port.pose_pair(
                beam.context.initial.mechanical)
            joint = RigidPoseJoint(
                np.array((shell_position, beam_high+beam_low)),
                np.array((shell_frame, beam_frame)))
            evaluation = joint.evaluate(
                np.array((shell_position, beam_high)),
                np.array((shell_frame, beam_frame)), np.zeros(6),
                position_low=np.array((np.zeros(3), beam_low)))
            if np.linalg.norm(evaluation.constraints) > 1e-11:
                raise ValueError("nonzero virgin weak-line reference gap")
            derivative = np.column_stack((
                evaluation.constraint_jacobian[:, :6]@
                reference_trace(shell.panel, station),
                evaluation.constraint_jacobian[:, 6:]@port.tangent(
                    beam.context.initial.mechanical)))
            for row, basis_value in enumerate(space.values(station)):
                constraint[6*row:6*row+6] += (
                    half*gauss_weight*basis_value*derivative)
    nx = 2*shell.panel.n_s
    if shell_support_policy == "legacy_three_left_nodes":
        clamped_shell_nodes = (0, nx+1, 2*(nx+1))
        clamped_shell = {6*node+axis for node in clamped_shell_nodes
                         for axis in range(6)}
    elif shell_support_policy == "full_left_edge":
        clamped_shell = {
            6*j*(nx+1)+axis
            for j in range(shell.panel.n_y+1)
            for axis in range(6)}
    else:
        clamped_shell = {
            6*(j*(nx+1)+i)+axis
            for j in range(shell.panel.n_y+1)
            for i in (0, nx) for axis in (0, 1)}
        clamped_shell.update({
            6*(j*(nx+1))+axis
            for j in range(shell.panel.n_y+1)
            for axis in (2, 3, 4)})
    fixed_beam = {shell_size+index for index in beam.context.fixed}
    free = np.array([index for index in range(shell_size+beam_size)
                     if index not in clamped_shell and index not in fixed_beam],
                    dtype=int)
    reduced = primal[np.ix_(free, free)]
    rows = constraint[:, free]
    system = np.block([[reduced, rows.T],
                       [rows, np.zeros((len(rows), len(rows)))]])
    force_scale = 1e6
    length_scale = 1.
    displacement_scale = force_scale/(210e9*.07)
    nodal_scale = np.tile(np.r_[np.full(3, displacement_scale),
                                np.full(3, displacement_scale/length_scale)],
                          shell.panel.node_count+beam.context.nodal_count//6)
    resultants = np.r_[np.tile(SECTION_DIAGONAL[:3]*displacement_scale, 2),
                       np.tile(SECTION_DIAGONAL[3:]*
                               (displacement_scale/length_scale), 4)]
    retained_scale = np.tile(np.r_[
        np.full(6, displacement_scale/length_scale), resultants],
        beam.n_half_cells//2)
    full_scale = np.r_[nodal_scale, retained_scale]
    if len(full_scale) != shell_size+beam_size:
        raise ValueError("native retained scaling layout changed")
    coordinate_scale = np.r_[full_scale[free],
                             np.full(len(rows), force_scale)]
    energy_scale = force_scale*displacement_scale
    scaled_system = ((coordinate_scale[:, None]*system)*
                     coordinate_scale[None, :])/energy_scale
    return ReferenceKKT(primal, constraint, free, system,
                        coordinate_scale, energy_scale,
                        scaled_system, len(edges)-1, shell_support_policy)
