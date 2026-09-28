"""Analytical control for development Q1 field comparison."""

import numpy as np
import pytest

from scripts.general_contact_d1_compare_coupled_fields import _relative_q1_l2


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
