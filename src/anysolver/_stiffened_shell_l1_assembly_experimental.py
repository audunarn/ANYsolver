"""Sparse reference-linear assembly of unqualified L1 and BL5 weak lines.

The definition explicitly pairs shell trace edges with native beam half-cells.
This matching-edge/half-cell development route is not reference search,
nonmatching mapping, a selected multiplier policy, or a qualified bonded line.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

from ._ge_beam3_retained_generalized_state import Mechanical
from ._stiffened_shell_l1_local_experimental import (
    L1LocalOperator, NativeHalfCellPort,
)
from ._stiffened_shell_bl5_local_experimental import BL5LocalOperator, LAW_ID


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


@dataclass(frozen=True)
class ExperimentalBL5Line:
    """Separate five-row director bond for bounded reference-linear studies."""

    shell_nodes: tuple[int, ...]
    beam_halfcells: tuple[tuple[int, int], ...]
    multiplier_span: int = 1
    expected_beam_arm: tuple[float, float, float] = (0., 0., -.05)

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
                type(self.multiplier_span) is not int or
                self.multiplier_span not in (1, 2) or
                n % self.multiplier_span or
                type(self.expected_beam_arm) is not tuple or
                len(self.expected_beam_arm) != 3 or
                not np.isfinite(self.expected_beam_arm).all()):
            raise ValueError("ordered even-edge experimental BL5 line required")

    @property
    def multiplier_space(self):
        return f"BL5_P0_span_{self.multiplier_span}"

    def descriptor(self):
        return dict(law=LAW_ID, shell_nodes=self.shell_nodes,
                    beam_halfcells=self.beam_halfcells,
                    multiplier_span=self.multiplier_span,
                    expected_beam_arm=self.expected_beam_arm)


def _sample_rows(line: ExperimentalL1Line | ExperimentalBL5Line,
                 edge: int, alpha: float,
                 channel: int):
    if type(line) is ExperimentalBL5Line:
        return ((channel*(len(line.beam_halfcells)//line.multiplier_span)+
                 edge//line.multiplier_span, 1.),)
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
    if type(line) is ExperimentalBL5Line:
        return 5*n//line.multiplier_span
    return 4*(n+1)+2*n if line.multiplier_space == SPACE_A else 4*n+n


def compile_lines(lines, *, shell_ids, shell_xyz, shell_cells,
                  thickness, beam_ids, beam_nodes, beam_parts,
                  shell_count, beam_count):
    """Build the fixed sparse C rows and keep local operators for later work.

    The returned rows are derivatives of integrated constraint work with
    respect to multiplier coefficients, not pointwise collocation equations.
    """
    if type(lines) is not tuple or any(type(line) not in
                                       (ExperimentalL1Line, ExperimentalBL5Line)
                                       for line in lines):
        raise ValueError("typed experimental weak lines required")
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
        label = "L1" if type(line) is ExperimentalL1Line else "BL5"
        identity = (line.shell_nodes, line.beam_halfcells)
        if identity in seen_lines:
            raise ValueError(f"repeated experimental {label} material line")
        seen_lines.add(identity)
        n = len(line.beam_halfcells)
        if any(node not in shell_index for node in line.shell_nodes):
            raise ValueError(f"{label} line references unknown shell node")
        if any(frozenset((line.shell_nodes[i], line.shell_nodes[i+1]))
               not in shell_edges for i in range(n)):
            raise ValueError(f"{label} material trace must follow shell element edges")
        seen_stations = set()
        for edge, (element_index, cell) in enumerate(line.beam_halfcells):
            if element_index >= len(beam_parts):
                raise ValueError(f"{label} line references unknown native beam half-cell")
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
                raise ValueError(f"nondegenerate {label} reference edge required")
            for alpha in abscissae:
                station = (element_index, cell, float(alpha))
                if station in seen_stations:
                    raise ValueError(f"repeated native {label} station")
                seen_stations.add(station)
                port = NativeHalfCellPort.from_reference(
                    reference, node_rows, element_index, cell, float(alpha),
                    beam_count-24*len(beam_parts), beam_count)
                if type(line) is ExperimentalL1Line:
                    local_operator = L1LocalOperator.at_reference(
                        shell_reference, np.zeros((2, 6)), thickness,
                        port, state, offset=line.beam_offset,
                        station=float(alpha))
                    observed_offset = local_operator.reference_offset
                    expected_offset = line.expected_shell_offset
                else:
                    local_operator = BL5LocalOperator.at_reference(
                        shell_reference, np.zeros((2, 6)), thickness,
                        port, state, station=float(alpha))
                    observed_offset = local_operator.reference_arm
                    expected_offset = line.expected_beam_arm
                if not np.allclose(observed_offset, expected_offset,
                                   rtol=1e-10, atol=1e-10):
                    raise ValueError(f"{label} reference correspondence offset mismatch")
                local = local_operator.evaluate(
                    np.zeros((2, 6)), state,
                    np.zeros(6 if type(line) is ExperimentalL1Line else 5))
                if np.max(np.abs(local.gap)) > 2e-13:
                    raise ValueError(f"{label} material reference gap is not zero")
                global_slots = np.r_[shell_slots,
                                     shell_count+local.beam_slots]
                weight = .5*length
                for channel in range(len(local.gap)):
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
