"""Topology-only controls for the optional macro-Q1 pressure basis."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from anysolver.general_contact.pressure_basis import (
    MACRO_Q1_PAIR_VERSION,
    PressureBasis,
    build_q4_source_macro_q1_pair_basis,
)


def _strip_faces(cells):
    stride = cells+1
    return tuple((1+j, 2+j, stride+2+j, stride+1+j)
                 for j in range(cells))


@pytest.mark.parametrize("cells", (16, 24))
def test_pairwise_macro_q1_is_positive_shared_and_partition_unity(cells):
    basis = build_q4_source_macro_q1_pair_basis(_strip_faces(cells))
    B = basis.as_array()
    assert basis.version == MACRO_Q1_PAIR_VERSION
    assert B.shape == (2*(cells+1), 2*(cells//2+1))
    assert basis.fine_source_node_ids == tuple(range(1, 2*(cells+1)+1))
    assert basis.mode_ids == tuple(
        [1+j for j in range(0, cells+1, 2)]
        + [cells+2+j for j in range(0, cells+1, 2)]
    )
    assert np.all(B >= 0.0)
    np.testing.assert_array_equal(B @ np.ones(len(basis.mode_ids)), 1.0)
    assert np.linalg.matrix_rank(B) == len(basis.mode_ids)
    for lower_offset in (0, cells+1):
        for column in range(cells+1):
            row = B[lower_offset+column]
            if column % 2 == 0:
                assert np.count_nonzero(row) == 1
                assert row.max() == 1.0
            else:
                assert np.count_nonzero(row) == 2
                np.testing.assert_array_equal(row[row > 0.0], [0.5, 0.5])


def test_basis_identity_does_not_depend_on_current_coordinates():
    faces = _strip_faces(16)
    original = build_q4_source_macro_q1_pair_basis(faces)
    coordinates = {node: np.array([float(node), 0.0, 0.0])
                   for node in original.fine_source_node_ids}
    for node in coordinates:
        coordinates[node] += np.array([0.031, -0.004, 0.002])
    # The builder consumes material incidence, so motion cannot change IDs/B.
    moved = build_q4_source_macro_q1_pair_basis(faces)
    assert moved == original
    with pytest.raises(FrozenInstanceError):
        original.mode_ids = ()
    with pytest.raises(TypeError):
        original.B[0][0] = 0.0
    detached = original.as_array()
    detached[0, :] = 0.0
    assert original.B[0][0] == 1.0


@pytest.mark.parametrize("faces", (
    (),
    _strip_faces(3),
    _strip_faces(34),
    ((1, 2, 5, 4), (7, 8, 9, 10)),
    ((1, 2, 5, 4), (5, 6, 7, 2)),
    ((1, 2, 5, 4), (2, 3, 1, 5)),
    ((1, 2, 5, 4), (2, 3, 6, 5), (3, 4, 7, 6), (4, 1, 8, 7)),
    ((1, 2, 5, 4), (2, 3, 3, 5)),
    ((0, 2, 5, 4), (2, 3, 6, 5)),
))
def test_unsupported_strip_topology_is_rejected(faces):
    with pytest.raises(ValueError):
        build_q4_source_macro_q1_pair_basis(faces)


def test_pressure_basis_constructor_rejects_nonpositive_or_unanchored_rows():
    with pytest.raises(ValueError):
        PressureBasis(MACRO_Q1_PAIR_VERSION, (1, 2), (1,), ((1.0,), (-0.1,)))
    with pytest.raises(ValueError):
        PressureBasis(MACRO_Q1_PAIR_VERSION, (1, 2), (1, 2),
                      ((0.5, 0.5), (0.5, 0.5)))
    mutable = [[1.0], [1.0]]
    basis = PressureBasis(MACRO_Q1_PAIR_VERSION, [1, 2], [1], mutable)
    mutable[0][0] = 0.0
    assert basis.B == ((1.0,), (1.0,))


def test_malformed_face_values_fail_with_explicit_error():
    with pytest.raises(ValueError, match="four distinct"):
        build_q4_source_macro_q1_pair_basis(
            ((1, 2, 5, 4), (2, [3], 6, 5)),
        )


def test_saved_weak_three_node_pattern_has_small_euclidean_macro_projection():
    # A heuristic on the *scaled* saved mode, not a physical Schur or
    # response qualification. The physical metric and column scaling still
    # need to be restored before any acceptance claim.
    basis = build_q4_source_macro_q1_pair_basis(_strip_faces(24))
    B = basis.as_array()
    weak = np.zeros(len(basis.fine_source_node_ids))
    for node, value in ((42, -0.422), (43, 0.813), (44, -0.400)):
        weak[basis.fine_source_node_ids.index(node)] = value
    projection = B @ np.linalg.lstsq(B, weak, rcond=None)[0]
    assert np.linalg.norm(projection)/np.linalg.norm(weak) < 0.03
