"""Topology-only candidate basis for a refined Q4 source pressure strip.

This builds pressure interpolation data. It does not change the contact law,
integration side, virtual work, tangent, or solver admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

import numpy as np


MACRO_Q1_PAIR_VERSION = "q4_source_macro_q1_pair_v1"
MAX_STRIP_CELLS = 32


@dataclass(frozen=True)
class PressureBasis:
    """Immutable fine-node to macro-pressure interpolation on one Q4 strip.

    ``B[i][a]`` is the value of macro basis function ``a`` at fine source
    node ``i``. The node and mode orders are explicit and both use stable
    material IDs, never current coordinates.
    """

    version: str
    fine_source_node_ids: tuple[int, ...]
    mode_ids: tuple[int, ...]
    B: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        try:
            fine = tuple(self.fine_source_node_ids)
            modes = tuple(self.mode_ids)
            matrix = tuple(tuple(float(value) for value in row)
                           for row in self.B)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("pressure-basis IDs and rows must be finite sequences") from exc
        object.__setattr__(self, "fine_source_node_ids", fine)
        object.__setattr__(self, "mode_ids", modes)
        object.__setattr__(self, "B", matrix)
        if self.version != MACRO_Q1_PAIR_VERSION:
            raise ValueError("unsupported Q4 source pressure-basis version")
        if (not fine or not modes
                or any(type(node) is not int or node <= 0 for node in (*fine, *modes))
                or len(set(fine)) != len(fine)
                or len(set(modes)) != len(modes)
                or not set(modes).issubset(fine)
                or len(matrix) != len(fine)):
            raise ValueError("pressure-basis IDs or matrix dimensions are invalid")
        for row in matrix:
            if (len(row) != len(modes)
                    or any(not isfinite(value) or value < 0.0 for value in row)
                    or abs(sum(row)-1.0) > 1.0e-14):
                raise ValueError("pressure basis must be finite, positive and partition unity")
        fine_index = {node: index for index, node in enumerate(fine)}
        for column, node in enumerate(modes):
            anchor = matrix[fine_index[node]]
            if any(value != (1.0 if index == column else 0.0)
                   for index, value in enumerate(anchor)):
                raise ValueError("each pressure mode must have its own nodal anchor")

    def as_array(self) -> np.ndarray:
        """Return a detached numeric copy of the immutable interpolation."""
        return np.asarray(self.B, dtype=float).copy()


def build_q4_source_macro_q1_pair_basis(
    ordered_faces: Iterable[tuple[int, int, int, int]],
) -> PressureBasis:
    """Build one macro Q1 pressure cell per adjacent pair of Q4 faces.

    Faces must be declared in strip order as (lower-left, lower-right,
    upper-right, upper-left), all with the same combinatorial orientation.
    Incidence alone cannot certify physical Jacobian sign or element shape;
    the geometry owner retains those checks.
    """
    try:
        faces = tuple(tuple(face) for face in ordered_faces)
    except TypeError as exc:
        raise ValueError("Q4 strip must declare ordered four-node faces") from exc
    cells = len(faces)
    if cells < 2 or cells % 2 or cells > MAX_STRIP_CELLS:
        raise ValueError("macro Q1 pressure basis needs 2–32 even ordered Q4 cells")
    for face in faces:
        if (len(face) != 4
                or any(type(node) is not int or node <= 0 for node in face)
                or len(set(face)) != 4):
            raise ValueError("each Q4 face needs four distinct positive material node IDs")

    lower = [faces[0][0]]
    upper = [faces[0][3]]
    for face in faces:
        if face[0] != lower[-1] or face[3] != upper[-1]:
            raise ValueError("Q4 faces must share one oriented cross-strip edge")
        lower.append(face[1])
        upper.append(face[2])
    rows = (tuple(lower), tuple(upper))
    if len(set(lower + upper)) != 2*(cells+1):
        raise ValueError("Q4 strip reuses a node outside its shared edges")

    fine = tuple(sorted(lower + upper))
    anchors = tuple(row[column] for row in rows
                    for column in range(0, cells+1, 2))
    modes = tuple(sorted(anchors))
    mode_index = {node: index for index, node in enumerate(modes)}
    weights: dict[int, tuple[float, ...]] = {}
    for row in rows:
        for column, node in enumerate(row):
            values = [0.0]*len(modes)
            if column % 2 == 0:
                values[mode_index[node]] = 1.0
            else:
                values[mode_index[row[column-1]]] = 0.5
                values[mode_index[row[column+1]]] = 0.5
            weights[node] = tuple(values)
    return PressureBasis(
        MACRO_Q1_PAIR_VERSION, fine, modes,
        tuple(weights[node] for node in fine),
    )
