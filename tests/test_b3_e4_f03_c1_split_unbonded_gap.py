"""Physical same-XY face-gap witness for the saved split-law solid."""

import numpy as np

from scripts.b3_e4_f03_c1_split_unbonded_gap import _same_xy_plate_gap


PLATE = np.array(((-1., -1., 0.), (1., -1., 0.),
                  (1., 1., 0.), (-1., 1., 0.),
                  (0., -1., 0.), (1., 0., 0.),
                  (0., 1., 0.), (-1., 0., 0.)))


def test_same_xy_projection_detects_interior_penetration():
    result = _same_xy_plate_gap(PLATE, np.array((.1, .2, -.01)), 0., 0.)
    assert result is not None
    gap, parameters, xy_defect = result
    assert abs(gap+.01) < 1e-15
    np.testing.assert_allclose(parameters, (.1, .2), rtol=0, atol=1e-12)
    assert xy_defect < 1e-12


def test_same_xy_projection_rejects_nonoverlapping_face():
    assert _same_xy_plate_gap(PLATE, np.array((2., 0., -.01)), 0., 0.) is None
