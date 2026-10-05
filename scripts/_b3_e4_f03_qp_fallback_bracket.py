"""Endpoint-choice sensitivity of unresolved Qp one-ulp density rows.

This is a two-choice diagnostic, not a mathematical enclosure. In particular,
an unsampled degree p+2 polynomial may exceed both endpoint constants inside
the interval. The protocol's physical comparison scale is one percent of the
larger operand norm or 1000 N, whichever is larger.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from scripts._b3_e4_f03_qp_functional_conversion import ConversionAudit
from scripts._b3_e4_f03_qp_piecewise_functional import GreenNorm, norm_squared


@dataclass(frozen=True)
class SingleFallbackBracket:
    left: GreenNorm
    right: GreenNorm
    endpoint_choice_distance: GreenNorm
    signed_norm_change_n: float
    absolute_norm_change_n: float
    endpoint_choice_distance_n: float
    physical_floor_n: float
    distance_fraction_of_floor: float


@dataclass(frozen=True)
class PairFallbackBracket:
    left_left: GreenNorm
    right_right: GreenNorm
    left_right: GreenNorm
    right_left: GreenNorm
    signed_same_choice_change_n: float
    absolute_distance_range_n: float
    physical_floor_n: float
    range_fraction_of_floor: float


def single_bracket(audit: ConversionAudit) -> SingleFallbackBracket:
    """Evaluate both full 48/64 norms and their coefficient-space distance."""
    if not isinstance(audit, ConversionAudit):
        raise TypeError("a Qp conversion audit is required")
    left = norm_squared(audit.functional)
    right = norm_squared(audit.right_limit_functional)
    difference = norm_squared(audit.functional.difference(
        audit.right_limit_functional))
    left_n, right_n, delta_n = (sqrt(item.squared_total) for item in
                                  (left, right, difference))
    physical_floor = .01*max(left_n, right_n, 1000.)
    return SingleFallbackBracket(left, right, difference,
        right_n-left_n, abs(right_n-left_n), delta_n, physical_floor,
        delta_n/physical_floor)


def pair_bracket(first: ConversionAudit,
                 second: ConversionAudit) -> PairFallbackBracket:
    """Evaluate four cross-level endpoint choices; this is not an enclosure."""
    if not isinstance(first, ConversionAudit) or not isinstance(second, ConversionAudit):
        raise TypeError("two Qp conversion audits are required")
    a, ar = first.functional, first.right_limit_functional
    b, br = second.functional, second.right_limit_functional
    norms = (norm_squared(a.difference(b)),
             norm_squared(ar.difference(br)),
             norm_squared(a.difference(br)),
             norm_squared(ar.difference(b)))
    distances = [sqrt(item.squared_total) for item in norms]
    operand_norms = [sqrt(norm_squared(item).squared_total) for item in
                     (a, ar, b, br)]
    physical_floor = .01*max(1000., *operand_norms)
    spread = max(distances)-min(distances)
    return PairFallbackBracket(*norms, distances[1]-distances[0],
                               spread, physical_floor, spread/physical_floor)
