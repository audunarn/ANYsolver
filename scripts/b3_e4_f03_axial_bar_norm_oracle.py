"""Independent axial-bar comparator for the F03 multiplier norm.

This exactly solves a unit-length, unit-EA bar with u(0)=0 and a free tip
under alternating P0 axial line force. It explains one norm trend; it is not
a beam/shell reference or a multiplier-space qualification.
"""

from __future__ import annotations

import json

import numpy as np

from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram


def alternating_bar_compliance(cells: int, *, amplitude: float = 1.,
                               axial_rigidity: float = 1.) -> float:
    """Exact load work for alternating P0 density on a unit axial bar.

    On every cell the cumulative load is a triangle of height ``a/cells``.
    The complementary energy/work is the integral of its square over EA.
    """
    if (type(cells) is not int or cells < 2 or cells > 128 or cells % 2 or
            not np.isfinite(amplitude) or amplitude == 0. or
            not np.isfinite(axial_rigidity) or axial_rigidity <= 0.):
        raise ValueError("even bounded axial-bar inventory required")
    return float(amplitude*amplitude/(3*axial_rigidity*cells*cells))


def one_case(cells: int, *, last_mode: int = 4095) -> dict:
    density = (-1.)**np.arange(cells)
    lower, upper = p0_dual_gram(cells, 1., last_mode)
    norm_lower = float(density@lower@density)
    norm_upper = float(density@upper@density)
    compliance = alternating_bar_compliance(cells)
    if not 0 < norm_lower <= norm_upper:
        raise ArithmeticError("axial-bar dual-norm enclosure invalid")
    return {
        "cells": cells,
        "exact_unit_ea_compliance": compliance,
        "h_minus_half_norm_squared_lower": norm_lower,
        "h_minus_half_norm_squared_upper": norm_upper,
        "compliance_quotient_lower": compliance/norm_upper,
        "compliance_quotient_upper": compliance/norm_lower,
    }


def main() -> None:
    print(json.dumps({
        "status": "UNREGISTERED_INDEPENDENT_AXIAL_BAR_NORM_DIAGNOSTIC",
        "boundary": "u(0)=0, free tip",
        "length_m": 1.,
        "axial_rigidity_n": 1.,
        "density_amplitude_n_per_m": 1.,
        "last_neumann_mode": 4095,
        "cases": [one_case(cells) for cells in (2, 4, 8, 16, 32, 64)],
        "scientific_registration": False,
    }, indent=2))


if __name__ == "__main__":
    main()
