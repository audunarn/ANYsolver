"""Fixed-pose pressure-space controls against an independent overlap integral.

The triangular overlap is (0.15, 0.10), (0.90, 0.10), (0.15, 0.85) m.
For the affine opening case, clipping that triangle by g=0 and integrating
max(-4 MPa/m * g, 0) gives the frozen force and first moments below. This
oracle does not invoke the production overlap or mortar integration kernel.
"""

import numpy as np
import pytest

from anysolver.general_contact.overlap import PlanarFace
from anysolver.general_contact.patch_mortar import MovingPatchMortar, PatchFace


_STIFFNESS = 4.0e6  # Pa/m
_POINTWISE_FORCE = 2.6041666666666674  # N
_POINTWISE_MX = 0.6673177083333336  # N m about global origin
_POINTWISE_MY = -0.797526041666667  # N m about global origin


def _square_patch(divisions: int):
    coordinates = {}
    for j in range(divisions + 1):
        for i in range(divisions + 1):
            node = 1 + j * (divisions + 1) + i
            coordinates[node] = (0.15 + i / divisions,
                                 0.10 + j / divisions)

    def node_at(i, j):
        return 1 + j * (divisions + 1) + i

    source = []
    for j in range(divisions):
        for i in range(divisions):
            ids = (node_at(i, j), node_at(i + 1, j),
                   node_at(i + 1, j + 1), node_at(i, j + 1))
            corners = np.array([(*coordinates[node], 0.0) for node in ids])
            source.append(PatchFace(PlanarFace((1, 1 + len(source)), corners), ids))
    target = PatchFace(
        PlanarFace((2, 1), np.array(((0.0, 0.0, 0.0),
                                    (1.0, 0.0, 0.0),
                                    (0.0, 1.0, 0.0)))),
        (10_001, 10_002, 10_003),
    )
    kernel = MovingPatchMortar(
        tuple(source), (target,), np.array((0.0, 0.0, 1.0)), _STIFFNESS,
    )
    return kernel, coordinates


def _wrench(kernel, coordinates, height):
    source_height = np.array([
        height(*coordinates[node]) for node in kernel.source_node_ids
    ])
    state = kernel.evaluate(
        np.zeros(3), np.zeros(3), source_height,
        np.zeros(len(kernel.target_node_ids)),
    )
    source_reaction = -state.normal_residual[:len(kernel.source_node_ids)]
    force = float(np.sum(source_reaction))
    moment_x = sum(coordinates[node][1] * local for node, local in
                   zip(kernel.source_node_ids, source_reaction))
    moment_y = -sum(coordinates[node][0] * local for node, local in
                    zip(kernel.source_node_ids, source_reaction))
    return state, force, moment_x, moment_y


def test_constant_pressure_and_refined_partial_opening_response():
    coarse, coarse_xy = _square_patch(4)
    uniform, force, mx, my = _wrench(coarse, coarse_xy,
                                    lambda _x, _y: -5.0e-6)
    assert uniform.pressure_rank == 13
    assert force == pytest.approx(5.625, rel=1.0e-12)
    assert mx == pytest.approx(1.96875, rel=1.0e-12)
    assert my == pytest.approx(-2.25, rel=1.0e-12)

    opening = lambda x, y: (2.0e-6 + 16.0e-6 * (x - 0.5)
                            + 16.0e-6 * (y - 0.5))
    _, coarse_force, _, _ = _wrench(coarse, coarse_xy, opening)
    refined, refined_xy = _square_patch(12)
    state, force, mx, my = _wrench(refined, refined_xy, opening)
    assert state.pressure_rank == 64
    assert abs(force - _POINTWISE_FORCE) < abs(coarse_force - _POINTWISE_FORCE)
    assert abs(force - _POINTWISE_FORCE) / _POINTWISE_FORCE <= 0.02
    assert abs(mx - _POINTWISE_MX) / abs(_POINTWISE_MX) <= 0.02
    assert abs(my - _POINTWISE_MY) / abs(_POINTWISE_MY) <= 0.02
