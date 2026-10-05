"""Preparatory Qp functional with recovered sub-binary64 density rows.

The ordinary conversion retains one-sided approximations as diagnostics.
This adapter replaces only their rows with independently held-point-checked
high-precision cell-polynomial coefficients. Scientific use still requires
frozen runner/resource evidence and independent mechanical review.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts._b3_e4_f03_qp_functional_conversion import (
    ConversionAudit, NORMALIZATION, from_qp_recovery,
)
from scripts._b3_e4_f03_qp_piecewise_functional import PiecewiseFunctional
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle
from scripts._b3_e4_f03_qp_subulp_density import (
    audit_represented_crossings, exact_endpoint_resultant,
    reconstruct_subulp_polynomial,
)


PRECISION_TOLERANCE = 1e-11
HELD_TOLERANCE = 1e-20
NODAL_TOLERANCE = 1e-10
ENDPOINT_TOLERANCE = 1e-10


@dataclass(frozen=True)
class PreciseFunctionalAudit:
    functional: PiecewiseFunctional
    base: ConversionAudit
    repaired_indices: tuple[int, ...]
    max_precision_defect: float
    max_held_defect: float
    max_nodal_defect: float
    exact_interior_crossings: int
    max_boundary_crossing_shift: float
    max_endpoint_defect: float


def from_qp_recovery_precise(trace, q, eta) -> PreciseFunctionalAudit:
    """Recover measured p+2 coefficients in every unresolved station row."""
    base = from_qp_recovery(trace, q, eta)
    if base.fallback_indices != tuple(i for i, (left, right) in
            enumerate(trace.station_intervals()) if
            np.nextafter(left, np.inf) >= right):
        # A wider interval with insufficient distinct fit/held samples would
        # need an explicit precision route too; never silently leave it as a
        # one-sided constant in a candidate scientific functional.
        raise ArithmeticError("unhandled sub-resolution Qp interval")
    coeff = base.functional.coefficients.copy()
    max_precision = max_held = max_nodal = max_endpoint = 0.
    exact_crossings = 0
    max_boundary_shift = 0.
    if base.fallback_indices:
        oracle = PiecewisePadMomentOracle(trace.p, x=trace.x, y=trace.y,
            offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
        exact_crossings, max_boundary_shift = audit_represented_crossings(oracle)
        if exact_crossings != len(trace.station_breakpoints())-2:
            raise ArithmeticError("represented and exact crossing inventories differ")
        cell_coeff = oracle.coefficients(q)
        reference_root = exact_endpoint_resultant(oracle, cell_coeff, 0.)
        reference_tip = exact_endpoint_resultant(oracle, cell_coeff, 1.)
        max_endpoint = float(max(
            np.max(np.abs(reference_root-(base.functional.atoms[0]+eta))
                   /NORMALIZATION),
            np.max(np.abs(reference_tip+base.functional.atoms[1])
                   /NORMALIZATION)))
        if max_endpoint > ENDPOINT_TOLERANCE:
            raise ArithmeticError("represented endpoint atoms disagree with exact geometry")
        for i in base.fallback_indices:
            left, right = trace.station_intervals()[i]
            coarse, held = reconstruct_subulp_polynomial(oracle, cell_coeff,
                left, right, trace.p+2, precision=90)
            precise, held_precise = reconstruct_subulp_polynomial(
                oracle, cell_coeff, left, right, trace.p+2, precision=120)
            independent, independent_held = reconstruct_subulp_polynomial(
                oracle, cell_coeff, left, right, trace.p+2, precision=120,
                nodal_state=q)
            max_precision = max(max_precision, float(np.max(
                np.abs(coarse-precise)/NORMALIZATION)))
            max_nodal = max(max_nodal, float(np.max(
                np.abs(independent-precise)/NORMALIZATION)))
            max_held = max(max_held, held, held_precise, independent_held)
            if max_precision > PRECISION_TOLERANCE or \
                    max_held/min(NORMALIZATION) > HELD_TOLERANCE or \
                    max_nodal > NODAL_TOLERANCE:
                raise ArithmeticError("sub-ulp coefficient recovery is unstable")
            coeff[i] = precise
    return PreciseFunctionalAudit(PiecewiseFunctional(base.functional.breaks,
        coeff, base.functional.cosine, base.functional.atoms), base,
        base.fallback_indices, max_precision, max_held, max_nodal,
        exact_crossings, max_boundary_shift, max_endpoint)
