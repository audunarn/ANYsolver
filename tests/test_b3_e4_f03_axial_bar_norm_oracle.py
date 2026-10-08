"""Independent numerical integration of the alternating axial-bar work."""

import numpy as np
import pytest

from scripts.b3_e4_f03_axial_bar_norm_oracle import (
    alternating_bar_compliance, one_case)


@pytest.mark.parametrize("cells", (2, 4, 8, 16))
def test_closed_form_matches_piecewise_gauss_work(cells):
    roots, weights = np.polynomial.legendre.leggauss(5)
    density = (-1.)**np.arange(cells)
    total = 0.
    for cell in range(cells):
        stations = (cell+(roots+1)/2)/cells
        # Integrate the load from the current station to the free tip.
        tail = np.sum(density[cell+1:])/cells
        force = tail+density[cell]*((cell+1)/cells-stations)
        total += np.dot(weights, force*force)/(2*cells)
    assert alternating_bar_compliance(cells) == pytest.approx(total, rel=1e-13)


def test_quotient_declines_under_h_minus_half_normalization():
    rows = [one_case(cells) for cells in (2, 4, 8, 16)]
    assert all(0 < row["compliance_quotient_lower"] <=
               row["compliance_quotient_upper"] for row in rows)
    assert all(a["compliance_quotient_lower"] >
               b["compliance_quotient_upper"] for a, b in
               zip(rows, rows[1:]))
