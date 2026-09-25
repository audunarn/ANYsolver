"""Physical wrench and objective-work checks for the bounded traction screen."""

import numpy as np
import pytest

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_continuous_surface_traction import (
    _common_rigid_direction, continuous_traction_rows,
)
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def test_continuous_traction_spans_six_wrenches_without_drilling():
    xs = np.linspace(-.5, 1.5, 9)
    ys = np.linspace(-.5, .5, 9)
    beam = build(8, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    rows, wrench, meta = continuous_traction_rows(xs, ys, beam, intervals=2)
    shell_size = 6 * len(xs) * len(ys)
    assert meta["bond_area_m2"] == pytest.approx(.1, abs=1e-12)
    assert meta["reference_gap_m"] < 1e-11
    assert rows.shape == (12, shell_size + beam.context.count)
    assert np.max(np.abs(rows[:, 5:shell_size:6])) == 0.
    assert np.linalg.matrix_rank(wrench) == 6
    for station in range(3):
        assert wrench[:, 4 * station + 3] == pytest.approx(
            [0., 0., 0., 1., 0., 0.], abs=1e-12)
    direction = _common_rigid_direction(
        xs, ys, beam, np.array((.02, -.03, .04)),
        np.array((.003, -.005, .007)))
    assert np.max(np.abs(rows @ direction)) < 1e-11
