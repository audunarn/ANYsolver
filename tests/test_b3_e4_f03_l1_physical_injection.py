"""Bounded development checks for supported native L1 work preservation."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_physical_injection import (
    _kinematic_problem, _virgin_gap_jacobian, report,
)
from scripts.b3_e4_f03_l1_space_design import reference_gap_jacobian


@pytest.mark.parametrize("coarse_edges", (2, 4))
def test_complete_six_channel_action_preserved(coarse_edges):
    result = report(coarse_edges)
    assert result["supported_to_fixed_or_resultant_leak"] == 0.
    assert result["resultant_column_action"] == 0.
    for candidate in result["spaces"].values():
        assert candidate["multiplier_rows"][1] > candidate["multiplier_rows"][0]
        assert candidate["max_abs_work_map_difference"] < 1e-12


@pytest.mark.parametrize("edges", (2, 8))
def test_derived_virgin_jacobian_matches_actual_connection_updates(edges):
    macro, _ = _kinematic_problem(edges)
    derived = _virgin_gap_jacobian(macro)
    actual = reference_gap_jacobian(macro)
    np.testing.assert_allclose(derived, actual, rtol=0., atol=2e-12)
