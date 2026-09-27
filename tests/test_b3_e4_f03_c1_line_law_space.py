"""Bounded row-span identity and distinct-law checks."""

import numpy as np

from scripts.b3_e4_f03_c1_line_law_space import row_space_comparison


def test_row_basis_change_preserves_supported_space():
    first = np.array(((1., 2., 0., 0.), (0., 1., 3., 0.)))
    second = np.array(((2., 5., 3., 0.), (1., 2., 0., 0.)))
    result = row_space_comparison(first, second)
    assert result["same_row_space_at_1e-9"]
    assert result["first_rank"] == result["second_rank"] == result["union_rank"] == 2


def test_new_physical_row_is_not_a_basis_change():
    first = np.array(((1., 0., 0.), (0., 1., 0.)))
    second = np.array(((1., 0., 0.), (0., 0., 1.)))
    result = row_space_comparison(first, second)
    assert result["union_rank"] == 3
    assert not result["same_row_space_at_1e-9"]
    assert result["first_outside_second_relative"] > .5
