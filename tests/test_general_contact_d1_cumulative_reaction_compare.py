"""Hand-integrated checks for the cumulative reaction diagnostic."""

import numpy as np
import pytest

from scripts.general_contact_d1_cumulative_reaction_compare import (
    _cumulative, _maximum_cumulative_difference,
)


def test_piecewise_linear_reaction_integral_and_interior_extremum():
    increasing = np.array([0.0, 1.0])
    decreasing = np.array([1.0, 0.0])
    assert _cumulative(increasing, 0.5) == pytest.approx(0.125)
    assert _cumulative(decreasing, 0.5) == pytest.approx(0.375)
    maximum, x = _maximum_cumulative_difference(decreasing, increasing)
    # Integral of (1-2x) is x-x² and is largest at x=1/2.
    assert maximum == pytest.approx(0.25)
    assert x == pytest.approx(0.5)


def test_common_refinement_finds_interior_extremum_across_unequal_grids():
    coarse = np.array([1.0, 0.0])
    fine = np.array([0.0, 1/3, 2/3, 1.0])
    maximum, x = _maximum_cumulative_difference(coarse, fine)
    assert maximum == pytest.approx(0.25)
    assert x == pytest.approx(0.5)
