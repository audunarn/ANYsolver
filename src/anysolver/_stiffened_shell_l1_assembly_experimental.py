"""Sparse reference-linear assembly of two unqualified L1 weak-line spaces.

The definition explicitly pairs shell trace edges with native beam half-cells.
This is a replaceable development route, not reference search, a selected
multiplier policy, or a qualified bonded line.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

from ._ge_beam3_retained_generalized_state import Mechanical
from ._stiffened_shell_l1_local_experimental import (
    L1LocalOperator, NativeHalfCellPort,
)


SPACE_A = "P1_translation_twist_P0_pitch_normal"
SPACE_B = "P0_translation_twist_pair_P0_pitch_normal"
SPACES = (SPACE_A, SPACE_B)


@dataclass(frozen=True)
class ExperimentalL1Line:
    """One explicitly mapped material line for reference-linear experiments."""

    shell_nodes: tuple[int, ...]
    beam_halfcells: tuple[tuple[int, int], ...]
    multiplier_space: str
    beam_offset: tuple[float, float, float] = (0., 0., -.05)
    expected_shell_offset: tuple[float, float, float] = (0., 0., 0.)

    def __post_init__(self):
        n = len(self.beam_halfcells)
        if (type(self.shell_nodes) is not tuple or
                type(self.beam_halfcells) is not tuple or
                n < 2 or n % 2 or len(self.shell_nodes) != n+1 or
                len(set(self.shell_nodes)) != n+1 or
                any(type(v) is not int or v <= 0 for v in self.shell_nodes) or
                any(type(pair) is not tuple or len(pair) != 2 or
                    type(pair[0]) is not int or type(pair[1]) is not int or
                    pair[0] < 0 or pair[1] not in (0, 1)
                    for pair in self.beam_halfcells) or
                len(set(self.beam_halfcells)) != n or
                self.multiplier_space not in SPACES):
            raise ValueError("ordered even-edge experimental L1 line required")
        for values in (self.beam_offset, self.expected_shell_offset):
            if (type(values) is not tuple or len(values) != 3 or
                    not np.isfinite(values).all()):
                raise ValueError("finite declared L1 offset required")

    def descriptor(self):
        return dict(shell_nodes=self.shell_nodes,
                    beam_halfcells=self.beam_halfcells,
                    multiplier_space=self.multiplier_space,
                    beam_offset=self.beam_offset,
                    expected_shell_offset=self.expected_shell_offset)


def _sample_rows(line: ExperimentalL1Line, edge: int, alpha: float,
                 channel: int):
    n = len(line.beam_halfcells)
    if line.multiplier_space == SPACE_A:
        if channel < 4:
            base = channel*(n+1)
            return ((base+edge, 1.-alpha), (base+edge+1, alpha))
        return ((4*(n+1)+(channel-4)*n+edge, 1.),)
    if channel < 4:
        return ((channel*n+edge, 1.),)
    return ((4*n+(channel-4)*(n//2)+edge//2, 1.),)


def _row_count(line: ExperimentalL1Line):
    n = len(line.beam_halfcells)
    return 4*(n+1)+2*n if line.multiplier_space == SPACE_A else 4*n+n


def compile_lines(lines, *, shell_ids, shell_xyz, shell_cells,
                  thickness, beam_ids, beam_nodes, beam_parts,
                  shell_count, beam_count):
    """Build the fixed sparse C rows and keep local operators for later work.

    The returned rows are derivatives of integrated constraint work with
    respect to multiplier coefficients, not pointwise collocation equations.
    """
    if type(lines) is not tuple or any(type(line) is not ExperimentalL1Line
                                       for line in lines):
        raise ValueError("typed experimental L1 lines required")
    shell_index = {node: i for i, node in enumerate(shell_ids)}
    beam_index = {node: i for i, node in enumerate(beam_ids)}
    shell_edges = {frozenset((cell[j], cell[(j+1) % len(cell)]))
                   for cell in shell_cells for j in range(len(cell))}
    positions = np.array([beam_nodes[node][0] for node in beam_ids])
    frames = np.array([beam_nodes[node][1] for node in beam_ids])
    state = Mechanical(positions, np.zeros_like(positions), frames,
                       np.tile(np.eye(3), (len(beam_parts), 2, 1, 1)),
                       np.zeros((len(beam_parts), 18)))
    count = shell_count+beam_count
    row_indices, columns, values = [], [], []
    samples = []
    line_row = 0
    seen_lines = set()
    abscissae = (.5-.5/np.sqrt(3.), .5+.5/np.sqrt(3.))
    for line in lines:
        line.__post_init__()
        identity = (line.shell_nodes, line.beam_halfcells)
        if identity in seen_lines:
            raise ValueError("repeated experimental L1 material line")
        seen_lines.add(identity)
        n = len(line.beam_halfcells)
        if any(node not in shell_index for node in line.shell_nodes):
            raise ValueError("L1 line references unknown shell node")
        if any(frozenset((line.shell_nodes[i], line.shell_nodes[i+1]))
               not in shell_edges for i in range(n)):
            raise ValueError("L1 material trace must follow shell element edges")
        seen_stations = set()
        for edge, (element_index, cell) in enumerate(line.beam_halfcells):
            if element_index >= len(beam_parts):
                raise ValueError("L1 line references unknown native beam half-cell")
            element = beam_parts[element_index][0]
            reference = element.operator.reference
            node_rows = tuple(beam_index[node] for node in element.node_ids)
            shell_pair = line.shell_nodes[edge:edge+2]
            shell_rows = tuple(shell_index[node] for node in shell_pair)
            shell_reference = shell_xyz[list(shell_rows)]
            shell_slots = np.r_[np.arange(6*shell_rows[0], 6*shell_rows[0]+6),
                                np.arange(6*shell_rows[1], 6*shell_rows[1]+6)]
            length = float(np.linalg.norm(shell_reference[1]-shell_reference[0]))
            if not np.isfinite(length) or length <= 1e-10:
                raise ValueError("nondegenerate L1 reference edge required")
            for alpha in abscissae:
                station = (element_index, cell, float(alpha))
                if station in seen_stations:
                    raise ValueError("repeated native L1 station")
                seen_stations.add(station)
                port = NativeHalfCellPort.from_reference(
                    reference, node_rows, element_index, cell, float(alpha),
                    beam_count-24*len(beam_parts), beam_count)
                local_operator = L1LocalOperator.at_reference(
                    shell_reference, np.zeros((2, 6)), thickness, port, state,
                    offset=line.beam_offset, station=float(alpha))
                if not np.allclose(local_operator.reference_offset,
                                   line.expected_shell_offset,
                                   rtol=1e-10, atol=1e-10):
                    raise ValueError("L1 reference correspondence offset mismatch")
                local = local_operator.evaluate(
                    np.zeros((2, 6)), state, np.zeros(6))
                if np.max(np.abs(local.gap)) > 2e-13:
                    raise ValueError("L1 material reference gap is not zero")
                global_slots = np.r_[shell_slots,
                                     shell_count+local.beam_slots]
                weight = .5*length
                for channel in range(6):
                    for row, coefficient in _sample_rows(
                            line, edge, float(alpha), channel):
                        jacobian = weight*coefficient*local.gap_jacobian[channel]
                        row_indices.extend([line_row+row]*len(global_slots))
                        columns.extend(global_slots.tolist())
                        values.extend(jacobian.tolist())
                samples.append((local_operator, global_slots, weight,
                                edge, float(alpha)))
        line_row += _row_count(line)
    matrix = sparse.coo_matrix((values, (row_indices, columns)),
                               shape=(line_row, count)).tocsr()
    matrix.eliminate_zeros()
    return matrix, tuple(samples)
