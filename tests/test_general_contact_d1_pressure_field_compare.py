"""Independent polynomial check of the development pressure-field comparison."""

import numpy as np
import pytest

from scripts.general_contact_d1_pressure_field_compare import _squared_norm


def _linear_field(columns, function):
    nodal = np.array([
        [function(i / columns, y) for i in range(columns + 1)]
        for y in (0.0, 1.0)
    ])
    return columns, nodal, {}


def test_cropped_common_refinement_integrates_squared_difference_exactly():
    first = _linear_field(3, lambda x, y: x + 2.0 * y)
    second = _linear_field(4, lambda x, y: 1.0 - x + y)
    low, high = 0.17, 0.83

    # Difference = 2x+y-1. Integrate its square first over y in [0, 1],
    # giving 4x²-2x+1/3, then over the cropped x interval.
    exact_difference = (
        4.0 / 3.0 * (high**3 - low**3)
        - (high**2 - low**2)
        + (high - low) / 3.0
    )
    # First field squared integrates over y to x²+2x+4/3.
    exact_first = (
        (high**3 - low**3) / 3.0
        + (high**2 - low**2)
        + 4.0 / 3.0 * (high - low)
    )
    assert _squared_norm(first, second, low, high) == pytest.approx(
        exact_difference, abs=1.0e-14,
    )
    assert _squared_norm(first, x_min=low, x_max=high) == pytest.approx(
        exact_first, abs=1.0e-14,
    )
