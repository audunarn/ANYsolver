"""Analytical control for development Q1 field comparison."""

import numpy as np
import pytest

from scripts.general_contact_d1_compare_coupled_fields import (
    _pressure_l2_y_bands,
    _relative_q1_l2,
)
from scripts.general_contact_d1_fixed_structure_pressure_probe import (
    relative_q1_pressure_l2,
)


def test_common_refinement_integrates_two_linear_pressure_fields_exactly():
    y = np.array((0.0, 0.2, 1.0))
    coarse_x = np.linspace(0.0, 1.0, 3)
    fine_x = np.linspace(0.0, 1.0, 5)
    first = y[:, None]+coarse_x[None, :]
    second = y[:, None]+2.0*fine_x[None, :]
    # Difference is x; squared norms over the unit square are 1/3 and 8/3.
    assert _relative_q1_l2(first, second, y, support_y_max=1.0) == pytest.approx(
        np.sqrt(1.0/8.0), abs=1.0e-14,
    )
    # Clipping through an interior y cell gives squared norms 1/6 and 23/24.
    assert _relative_q1_l2(first, second, y, support_y_max=0.5) == pytest.approx(
        np.sqrt(4.0/23.0), abs=1.0e-14,
    )


def test_distinct_y_pressure_knots_and_clipped_physical_support():
    x = np.array((0.0, 1.0))
    first_y = np.array((0.0, 1.0))
    second_y = np.array((0.0, 0.5, 1.0))
    first = {"xn": x, "yn": first_y,
             "p": np.array(((0.0, 0.0), (1.0, 1.0)))}
    second = {"xn": x, "yn": second_y,
              "p": np.array(((0.0, 0.0), (0.5, 0.5), (0.0, 0.0)))}
    # Over y in [0, .75], squared difference is 1/48; q squared is 5/64.
    assert relative_q1_pressure_l2(
        first, second, support_y_max=0.75,
    ) == pytest.approx(np.sqrt(4.0/15.0), abs=1.0e-14)


def test_pressure_band_partition_recovers_exact_global_norm():
    y = np.array((0.0, 0.2, 1.0))
    x = np.array((0.0, 0.5, 1.0))
    first = np.broadcast_to(y[:, None], (len(y), len(x)))
    second = 2.0*first
    bands = _pressure_l2_y_bands(first, second, y, [0.0, 0.5, 1.0])
    assert bands["difference_energy_fraction"] == pytest.approx(
        [1.0/8.0, 7.0/8.0], abs=1.0e-14,
    )
    assert bands["band_relative_pressure_l2"] == pytest.approx(
        [0.5, 0.5], abs=1.0e-14,
    )
    assert bands["global_relative_pressure_l2"] == pytest.approx(
        _relative_q1_l2(first, second, y, support_y_max=1.0), abs=1.0e-14,
    )
