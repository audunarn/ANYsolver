"""Bounded same-XY sampling semantics for saved-reference screening."""

import numpy as np

from scripts.b3_e4_f03_reverse_fz_same_xy_gap import sample_matching_faces


def test_same_xy_face_order_distinguishes_overlap_and_opening():
    xy = ((-1., -1.), (1., -1.), (1., 1.), (-1., 1.),
          (0., -1.), (1., 0.), (0., 1.), (-1., 0.))
    coordinates = {i + 1: np.array((x, y, 0.)) for i, (x, y) in enumerate(xy)}
    coordinates.update({i + 9: np.array((x, y, 0.)) for i, (x, y) in enumerate(xy)})
    pairs = [[(i + 1, i + 9) for i in range(8)]]
    displacement = {node: np.zeros(3) for node in coordinates}
    for i in range(9, 17):
        displacement[i] = np.array((0., 0., 1e-4))
    opened = sample_matching_faces(pairs, coordinates, displacement, roots=[0.])
    assert opened["sample_count"] == opened["same_face_projected_count"] == 1
    assert opened["negative_same_xy_count"] == 0
    assert abs(opened["minimum_same_xy_gap_m"] - 1e-4) < 1e-15
    for i in range(9, 17):
        displacement[i] = np.array((0., 0., -1e-4))
    overlap = sample_matching_faces(pairs, coordinates, displacement, roots=[0.])
    assert overlap["negative_same_xy_count"] == 1
    assert abs(overlap["minimum_same_xy_gap_m"] + 1e-4) < 1e-15


def test_positive_paired_gap_can_hide_same_xy_overlap():
    xy = ((-1., -1.), (1., -1.), (1., 1.), (-1., 1.),
          (0., -1.), (1., 0.), (0., 1.), (-1., 0.))
    coordinates = {i + 1: np.array((x, y, x)) for i, (x, y) in enumerate(xy)}
    coordinates.update({i + 9: np.array((x, y, x)) for i, (x, y) in enumerate(xy)})
    displacement = {node: np.zeros(3) for node in coordinates}
    for i in range(9, 17):
        displacement[i] = np.array((.1, 0., .05))
    result = sample_matching_faces([[(i + 1, i + 9) for i in range(8)]],
                                   coordinates, displacement, roots=[0.],
                                   face_indices=[17])
    assert result["negative_same_xy_count"] == 1
    assert abs(result["minimum_same_xy_gap_m"] + .05) < 1e-12
    assert result["minimum_sample"]["face_index"] == 17
