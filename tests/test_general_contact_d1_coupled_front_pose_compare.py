"""Polynomial check for the saved-pose comparison integral."""

import numpy as np
import pytest

from scripts.general_contact_d1_coupled_front_pose_compare import (
    _squared_difference,
)


def test_piecewise_linear_pose_difference_integrates_exactly_on_front():
    earlier = {"columns": 2, "physical_gap": np.array([
        [0.0, 0.5, 1.0], [0.0, 0.5, 1.0],
    ])}
    later = {"columns": 3, "physical_gap": np.zeros((2, 4))}
    left, right = 0.625, 0.75
    exact = (right**3 - left**3) / 3.0
    assert _squared_difference(
        earlier, later, "physical_gap", left, right,
    ) == pytest.approx(exact, abs=1.0e-15)
