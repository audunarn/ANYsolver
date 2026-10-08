"""Signed six-channel work decomposition for a complete P0 action."""

import numpy as np

from scripts.b3_e4_f03_c1_component_compliance import component_work


def test_coupled_channel_contributions_keep_cancellation():
    matrix = np.eye(24)
    matrix[0, 4] = matrix[4, 0] = -.25
    coefficient = np.zeros(24)
    coefficient[0], coefficient[4] = 2., 1.
    result = component_work(matrix, coefficient)
    assert result["work_J"] == 4.
    assert result["signed_work_by_channel_J"]["Fx"] == 3.5
    assert result["signed_work_by_channel_J"]["My"] == .5
    assert sum(result["signed_work_by_channel_J"].values()) == result["work_J"]
