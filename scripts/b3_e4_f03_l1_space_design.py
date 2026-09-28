"""Bounded six-channel L1 macroelement space comparison, not formal F03.

All three multiplier spaces act on the same shell-frame Log gap and native
retained half-cell trace. This is a local work-map diagnostic, not a coupled
stability, transfer, convergence, or production-law result. Gauss work is the
exactly differentiated *discrete* action; finite-rotation continuum work is
not asserted to be a cubic polynomial.

At a straight reference, the shell-normal rotation gap Jacobian is constant
inside each segment: projected E4 tangent yaw depends on the edgewise
transverse displacement slope, while native half-cell spin is constant there.
Thus the full-P1 normal dual with alternating nodal values has zero mean and
exactly zero work on every segment. P0 normal rows remove this particular
checkerboard; they do not prove inf-sup stability or absence of locking.
"""

from __future__ import annotations

from dataclasses import dataclass
import json

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_l1_native_connection_probe import SegmentedL1WeakWork


@dataclass(frozen=True)
class Macroelement:
    """Even number of E4 edges coincident with actual native half-cell cuts."""

    fixture: object
    blocks: tuple[SegmentedL1WeakWork, ...]
    cuts: np.ndarray
    stations: np.ndarray
    weights: np.ndarray

    @property
    def connections(self):
        return tuple(c for block in self.blocks for c in block.connections)

    @property
    def segments(self):
        return len(self.cuts)-1

    @property
    def coordinate_count(self):
        return 6*(self.segments+1)+self.fixture.context.count


def build_macroelement(segments: int) -> Macroelement:
    """Use only the fixture's 4/8-half-cell straight cases (2/4 edges)."""
    if type(segments) is not int or segments not in (2, 4):
        raise ValueError("bounded even 2- or 4-segment design fixture required")
    fixture = build(2*segments, z_offset=.0675, assemble=False)
    cuts = fixture.abscissae[segments:].copy()
    reference = np.column_stack((cuts, np.zeros(segments+1),
                                 np.zeros(segments+1)))
    total = np.zeros((segments+1, 6))
    state = fixture.context.initial.mechanical

    def port_at(station):
        element, cell, weight, _ = fixture._locate(station)
        return NativeHalfCellSpatialPort(fixture.context, element, cell, weight)

    blocks = tuple(SegmentedL1WeakWork.at_reference(
        reference[i:i+3], total[i:i+3], .035, cuts[i:i+3], port_at, state)
        for i in range(0, segments, 2))
    stations = np.array([s for block in blocks for s in block.stations])
    weights = np.array([w for block in blocks for w in block.weights])
    return Macroelement(fixture, blocks, cuts, stations, weights)


def sampled_dual_spaces(macro: Macroelement) -> dict[str, np.ndarray]:
    """Return complete six-channel dual sampling matrices at Gauss stations.

    A: P1 continuous channels 0:4, P0 per edge channels 4:6.
    B: P0 per edge channels 0:4, P0 per *two-edge* patch channels 4:6.
    C: discrete L2-biorthogonal dual to continuous P1 on all six channels.
    C is a basis transformation of full P1, not a new stabilization.
    """
    n = macro.segments
    q = len(macro.stations)
    hat = np.zeros((q, n+1))
    cell = np.zeros((q, n))
    patch = np.zeros((q, n//2))
    for sample, station in enumerate(macro.stations):
        edge = sample//2
        alpha = (station-macro.cuts[edge])/(macro.cuts[edge+1]-macro.cuts[edge])
        hat[sample, edge:edge+2] = (1.-alpha, alpha)
        cell[sample, edge] = 1.
        patch[sample, edge//2] = 1.
    mass = hat.T@(macro.weights[:, None]*hat)
    biorthogonal = hat@np.linalg.inv(mass)

    def stack(channel_bases):
        count = sum(base.shape[1] for base in channel_bases)
        sampled = np.zeros((6*q, count))
        offset = 0
        for channel, base in enumerate(channel_bases):
            width = base.shape[1]
            sampled[channel::6, offset:offset+width] = base
            offset += width
        return sampled

    return {
        "P1_translation_twist_P0_pitch_normal": stack([hat]*4+[cell]*2),
        "P0_translation_twist_pair_P0_pitch_normal": stack([cell]*4+[patch]*2),
        "P1_consistent_biorthogonal_dual": stack([biorthogonal]*6),
    }


def reference_gap_jacobian(macro: Macroelement) -> np.ndarray:
    """Differentiate actual E4 totals and Context.advance at each L1 station."""
    n = macro.segments
    state = macro.fixture.context.initial.mechanical
    beam_size = macro.fixture.context.count
    jacobian = np.zeros((6*len(macro.stations), macro.coordinate_count))
    beam_zero = np.zeros(beam_size)
    shell_zero = np.zeros((2, 6))
    for sample, connection in enumerate(macro.connections):
        edge = sample//2
        shell_total = shell_zero.copy()
        gap, _ = connection.evaluate(shell_total, state)
        if not np.allclose(gap, 0., atol=2e-14, rtol=0.):
            raise ValueError("macroelement reference gap is not zero")
        rows = slice(6*sample, 6*sample+6)
        for local in range(12):
            direction = shell_zero.copy()
            direction.flat[local] = 1.
            jacobian[rows, 6*edge+local] = connection.evaluate(
                shell_total, state, shell_direction=direction,
                beam_direction=beam_zero)[1]
        active = np.flatnonzero(np.any(connection.port.tangent(state) != 0., axis=0))
        for column in active:
            direction = np.zeros(beam_size)
            direction[column] = 1.
            jacobian[rows, 6*(n+1)+column] = connection.evaluate(
                shell_total, state, shell_direction=shell_zero,
                beam_direction=direction)[1]
    return jacobian


def action_matrix(macro: Macroelement, dual_samples: np.ndarray,
                  gap_jacobian: np.ndarray) -> np.ndarray:
    """Multiplier coefficients to exact discrete virtual-work action."""
    if (dual_samples.shape[0] != gap_jacobian.shape[0] or
            gap_jacobian.shape[1] != macro.coordinate_count):
        raise ValueError("compatible six-channel sample and native action required")
    weight = np.repeat(macro.weights, 6)
    return dual_samples.T@(weight[:, None]*gap_jacobian)


def _weighted_projection_error(macro, samples, channel, pattern):
    row = np.arange(channel, 6*len(macro.stations), 6)
    basis = samples[row]
    weighted = np.sqrt(macro.weights)
    target = np.array([pattern(i//2) for i in range(len(macro.stations))])
    coefficient = np.linalg.lstsq(weighted[:, None]*basis,
                                   weighted*target, rcond=None)[0]
    error = weighted*(basis@coefficient-target)
    return float(np.linalg.norm(error)/np.linalg.norm(weighted*target))


def design_report(macro: Macroelement) -> dict:
    """Small deterministic diagnostics; rank alone does not select a space."""
    gap = reference_gap_jacobian(macro)
    spaces = sampled_dual_spaces(macro)
    n = macro.segments
    shell_count = 6*(n+1)
    shear = np.zeros(macro.coordinate_count)
    shear[1:shell_count:6] = 1.
    drill = np.zeros(macro.coordinate_count)
    drill[5:shell_count:6] = 1.
    twist = np.zeros(macro.coordinate_count)
    for connection in macro.connections:
        port = connection.port
        cell = (port.context.nodal_count+24*port.element_index+3*port.cell)
        twist[shell_count+cell] = 1.
    response = {
        "shear_gap_y": (gap@shear)[1::6].tolist(),
        "shell_drill_gap_norm": float(np.linalg.norm(gap@drill)),
        "native_twist_gap_x": (gap@twist)[3::6].tolist(),
        "normal_row_pair_difference": [float(np.linalg.norm(
            gap[6*(2*edge)+5]-gap[6*(2*edge+1)+5]))
            for edge in range(n)],
    }
    output = {"segments": n, "cuts": macro.cuts.tolist(),
              "stations": macro.stations.tolist(),
              "weights": macro.weights.tolist(),
              "reference_gap_checked": True, "physical_response": response,
              "candidates": {}}
    weighted = np.repeat(macro.weights, 6)
    native = gap[:, shell_count:]
    active_native = np.flatnonzero(np.any(native != 0., axis=0))
    fixed = np.asarray(macro.fixture.context.fixed, dtype=int)
    supported_native = np.setdiff1d(active_native, fixed)
    supported_columns = np.r_[np.arange(shell_count),
                              shell_count+supported_native]
    output["trace_ownership"] = {
        "supported_native_active": int(len(supported_native)),
        "fixed_native_action_norm": float(np.linalg.norm(native[:, fixed])),
        "retained_resultant_action_norm": float(np.linalg.norm(native[:, [
            macro.fixture.context.nodal_count+24*element+6+component
            for element in range(len(macro.fixture.context.elements))
            for component in range(18)]])),
    }
    for name, samples in spaces.items():
        action = action_matrix(macro, samples, gap)
        physical_action = action[:, supported_columns]
        left_vectors, singular, _ = np.linalg.svd(
            physical_action, full_matrices=False)
        tolerance = max(physical_action.shape)*np.finfo(float).eps*singular[0]
        # The alternating cell field exposes omitted modes as well as exact
        # action nulls; the two phenomena must not be conflated.
        projection = {
            "translation_alternation": _weighted_projection_error(
                macro, samples, 1, lambda edge: (-1.)**edge),
            "pitch_alternation": _weighted_projection_error(
                macro, samples, 4, lambda edge: (-1.)**edge),
            "normal_alternation": _weighted_projection_error(
                macro, samples, 5, lambda edge: (-1.)**edge),
        }
        # An independent coefficient/coordinate pair checks the assembled
        # weak-work map against the quadrature sum, including all six rows.
        rng = np.random.default_rng(761+n+samples.shape[1])
        multiplier = rng.normal(size=samples.shape[1])
        direction = rng.normal(size=macro.coordinate_count)
        left = float(multiplier@action@direction)
        right = float((samples@multiplier)@(weighted*(gap@direction)))
        physical_work = {}
        for label, channel, motion in (("shear", 1, shear),
                                       ("twist_torque", 3, twist),
                                       ("shell_drill", 5, drill)):
            target = np.zeros(6*len(macro.stations))
            target[channel::6] = 1.
            fitted = np.linalg.lstsq(
                np.sqrt(weighted)[:, None]*samples,
                np.sqrt(weighted)*target, rcond=None)[0]
            physical_work[label] = float(fitted@action@motion)
        null = None
        if singular[-1] <= tolerance:
            coefficient = left_vectors[:, -1]
            field = (samples@coefficient).reshape(-1, 6)
            energy = np.sum(macro.weights[:, None]*field**2, axis=0)
            alternating_hat = np.zeros(len(macro.stations))
            nodal_alternation = (-1.)**np.arange(n+1)
            for sample, station in enumerate(macro.stations):
                edge = sample//2
                alpha = (station-macro.cuts[edge])/(macro.cuts[edge+1]-macro.cuts[edge])
                alternating_hat[sample] = ((1.-alpha)*nodal_alternation[edge]+
                                           alpha*nodal_alternation[edge+1])
            normal = field[:, 5]
            correlation = abs(np.dot(macro.weights*normal, alternating_hat))/(
                np.sqrt(np.dot(macro.weights*normal, normal))*
                np.sqrt(np.dot(macro.weights*alternating_hat, alternating_hat)))
            null = {
                "channel_energy_fraction": (energy/np.sum(energy)).tolist(),
                "normal_nodal_alternation_correlation": float(correlation),
                "action_norm": float(np.linalg.norm(physical_action.T@coefficient)),
            }
        output["candidates"][name] = {
            "dual_dimension": int(samples.shape[1]),
            "action_rank": int(np.count_nonzero(singular > tolerance)),
            "least_singular_action": float(singular[-1]),
            "work_map_error": abs(left-right),
            "physical_work": physical_work,
            "alternating_cell_projection_error": projection,
            "zero_action_mode": null,
        }
    return output


if __name__ == "__main__":
    print(json.dumps([design_report(build_macroelement(n)) for n in (2, 4)],
                     indent=2))
