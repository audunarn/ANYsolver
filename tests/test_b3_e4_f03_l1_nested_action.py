"""Whole-space nested L1 action identity, without reference-stiffness claims."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_nested_action import (
    SPACES, grid, injection, report, samples, work_map,
)
from scripts.b3_e4_f03_l1_space_design import (
    action_matrix, build_macroelement, reference_gap_jacobian,
    sampled_dual_spaces,
)


@pytest.mark.parametrize("coarse_edges", (2, 4, 8))
@pytest.mark.parametrize("space", SPACES)
def test_entire_coarse_multiplier_space_has_exact_fine_work(
        coarse_edges, space):
    coarse, fine = grid(coarse_edges), grid(2*coarse_edges)
    j = injection(coarse, fine, space)
    fine_basis = samples(fine.cuts, fine.stations, space)
    coarse_basis = samples(coarse.cuts, fine.stations, space)
    np.testing.assert_allclose(fine_basis@j, coarse_basis,
                               rtol=0., atol=2e-15)
    left, right = work_map(coarse, fine, space)
    np.testing.assert_allclose(left, right, rtol=0., atol=2e-15)
    # One arbitrary six-channel gap and multiplier pair exercises the dual
    # relation, while the matrix identity above covers the complete spaces.
    rng = np.random.default_rng(940+coarse_edges+len(space))
    multiplier = rng.normal(size=j.shape[1])
    gap = rng.normal(size=6*len(fine.stations))
    np.testing.assert_allclose(multiplier@left@gap,
                               (j@multiplier)@(
                                   fine_basis.T@(np.repeat(fine.weights, 6)*gap)),
                               rtol=2e-14, atol=2e-14)


def test_actual_native_l1_fine_work_uses_the_same_injection():
    macro = build_macroelement(4)
    coarse, fine = grid(2), grid(4)
    np.testing.assert_array_equal(macro.cuts, fine.cuts)
    np.testing.assert_allclose(macro.stations, fine.stations, atol=2e-16)
    gap = reference_gap_jacobian(macro)
    for space in SPACES:
        fine_basis = samples(fine.cuts, fine.stations, space)
        np.testing.assert_allclose(fine_basis,
                                   sampled_dual_spaces(macro)[space],
                                   rtol=0., atol=2e-15)
        j = injection(coarse, fine, space)
        actual = action_matrix(macro, fine_basis, gap)
        coarse_on_fine = samples(coarse.cuts, fine.stations, space)
        expected = coarse_on_fine.T@(
            np.repeat(fine.weights, 6)[:, None]*gap)
        np.testing.assert_allclose(j.T@actual, expected,
                                   rtol=3e-14, atol=2e-14)


def test_non_nested_reference_is_rejected_and_report_is_bounded():
    with pytest.raises(ValueError, match="nested same-line"):
        injection(grid(2), grid(4, start=.4), SPACES[0])
    rows = report()
    assert len(rows) == 6
    assert all(row["line_interval_m"] == [.5, 1.] for row in rows)
    assert max(row["whole_basis_sample_error"] for row in rows) < 2e-15
    assert max(row["whole_space_work_map_error"] for row in rows) < 2e-15
