"""Preparatory Qp beam recovery to represented piecewise Green coefficients.

The independent pad-moment oracle supplies the polynomial density samples.
Direct trace recovery checks held samples and endpoint atoms. Intervals too
small to contain the required distinct binary64 samples use a *one-sided
constant approximation*, retain their actual width, and are counted. Their
unresolved higher-order contribution is a limitation, not a certified error
bound or an exact coefficient recovery.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.legendre import leggauss, legval, legvander

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0, SECTION
from scripts._b3_e4_f03_qp_beam_recovery import recover_interface
from scripts._b3_e4_f03_qp_piecewise_functional import (
    ELL, MAX_INTERVALS, PiecewiseFunctional,
)
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle


NORMALIZATION = np.array((F0, F0, F0*ELL))
FIT_TOLERANCE = 1e-10
HELD_FRACTIONS = np.array((.137, .359, .641, .863))


class PolynomialDegreeMismatch(ArithmeticError):
    """The declared degree p+2 did not reproduce held density samples."""


class DirectRecoveryMismatch(ArithmeticError):
    """The independent oracle and direct trace recovery disagree."""


@dataclass(frozen=True)
class ConversionAudit:
    functional: PiecewiseFunctional
    max_oracle_fit_defect: float
    max_direct_recovery_defect: float
    max_atom_defect: float
    fallback_intervals: int
    no_binary64_interior_intervals: int
    fallback_total_width: float
    max_fallback_endpoint_spread: float
    # This count marks an approximation, never an exactness certificate.


def _section_density(oracle, coefficients, station, side):
    pose, first, second = oracle.evaluate(coefficients, station, side=side)
    ea, ei, ga = np.diag(SECTION)
    q_shear = ga*(first[1]-pose[2])
    return np.array((ea*second[0],
        ga*(second[1]-first[2])+F0*(1.+.25*np.cos(2*np.pi*station)),
        ei*second[2]+q_shear))


def _section_resultant(oracle, coefficients, station, side):
    pose, first, _ = oracle.evaluate(coefficients, station, side=side)
    ea, ei, ga = np.diag(SECTION)
    return np.array((ea*first[0], ga*(first[1]-pose[2]), ei*first[2]))


def _fit_stations(left, right, nodes):
    stations = left+(right-left)*nodes
    return (stations if np.all((stations > left) & (stations < right)) and
            len(np.unique(stations)) == len(nodes) else None)


def from_qp_recovery(trace: FinitePadQpTrace, q, eta) -> ConversionAudit:
    """Fit degree p+2 and validate on held points; reject degree disagreement.

    The return value separates measured defects on sampleable intervals from
    the counted one-sided constant approximations on sub-resolution intervals.
    The caller must not treat the latter as exact physical density recovery.
    """
    if not isinstance(trace, FinitePadQpTrace):
        raise TypeError("a finite-pad Qp trace is required")
    intervals = trace.station_intervals()
    if (len(intervals) > MAX_INTERVALS or 2*trace.n > 896 or
            len(trace.free_columns) > 832):
        raise ValueError("outside bounded Qp functional conversion")
    q = np.asarray(q, dtype=np.float64)
    eta = np.asarray(eta, dtype=np.float64)
    if (q.shape != (2*trace.n,) or eta.shape != (3,) or
            not np.isfinite(q).all() or not np.isfinite(eta).all()):
        raise ValueError("invalid physical Qp conversion state")
    oracle = PiecewisePadMomentOracle(trace.p, x=trace.x, y=trace.y,
        offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
    cell_coefficients = oracle.coefficients(q)
    degree = trace.p+2
    roots, _ = leggauss(degree+1)
    fit_nodes = (roots+1.)/2.
    cosine = np.array((0., .25*F0, 0.))
    breaks = np.array(trace.station_breakpoints(), dtype=np.float64)
    line_coefficients = np.zeros((len(intervals), degree+1, 3))
    max_fit = max_direct = max_spread = 0.
    fallback = no_interior = 0
    fallback_width = 0.
    for i, (left, right) in enumerate(intervals):
        # Even a one-ulp represented interval occupies its own row and width.
        if np.nextafter(left, np.inf) >= right:
            no_interior += 1
        stations = _fit_stations(left, right, fit_nodes)
        if stations is None:
            fallback += 1
            fallback_width += right-left
            first = _section_density(oracle, cell_coefficients, left, "right")
            last = _section_density(oracle, cell_coefficients, right, "left")
            max_spread = max(max_spread,
                float(np.max(np.abs(first-last)/NORMALIZATION)))
            direct_limits = recover_interface(trace, q, eta,
                np.array((left, right)), sides=("right", "left"))["density"]
            max_direct = max(max_direct, float(np.max(np.abs(
                np.stack((first, last))-direct_limits)/NORMALIZATION)))
            # The right-hand limit at the left endpoint is the stated
            # approximation; no polynomial order is invented from duplicate
            # floating-point samples.
            line_coefficients[i, 0] = first-np.cos(2*np.pi*left)*cosine
            continue
        sampled = np.array([_section_density(oracle, cell_coefficients,
                           float(s), "right") for s in stations])
        remainder = sampled-np.cos(2*np.pi*stations)[:, None]*cosine
        line_coefficients[i] = np.linalg.solve(
            legvander(2*fit_nodes-1, degree), remainder)
        held = _fit_stations(left, right, HELD_FRACTIONS)
        if held is None:
            # Independent degree validation is unavailable. Replace the
            # solved fit with the declared one-sided approximation.
            fallback += 1
            fallback_width += right-left
            first = _section_density(oracle, cell_coefficients, left, "right")
            last = _section_density(oracle, cell_coefficients, right, "left")
            max_spread = max(max_spread,
                float(np.max(np.abs(first-last)/NORMALIZATION)))
            line_coefficients[i] = 0.
            line_coefficients[i, 0] = first-np.cos(2*np.pi*left)*cosine
            continue
        predicted = np.moveaxis(legval(2*HELD_FRACTIONS-1,
            line_coefficients[i]), 0, -1)
        predicted += np.cos(2*np.pi*held)[:, None]*cosine
        expected = np.array([_section_density(oracle, cell_coefficients,
                             float(s), "right") for s in held])
        max_fit = max(max_fit, float(np.max(
            np.abs(predicted-expected)/NORMALIZATION)))
        direct = recover_interface(trace, q, eta, held)["density"]
        max_direct = max(max_direct, float(np.max(
            np.abs(predicted-direct)/NORMALIZATION)))
    if max_fit > FIT_TOLERANCE:
        raise PolynomialDegreeMismatch(
            f"degree p+2 held-point defect {max_fit:.17e} exceeds {FIT_TOLERANCE:.1e}")
    root = _section_resultant(oracle, cell_coefficients, 0., "right")
    tip = _section_resultant(oracle, cell_coefficients, 1., "left")
    atoms = np.stack((root-eta, -tip))
    direct_ends = recover_interface(trace, q, eta, np.array((0., 1.)))
    max_atom = float(max(np.max(np.abs(atoms[0]-direct_ends["root_atom"])/
                            NORMALIZATION),
                         np.max(np.abs(atoms[1]-direct_ends["tip_atom"])/
                            NORMALIZATION)))
    if max_direct > FIT_TOLERANCE or max_atom > FIT_TOLERANCE:
        raise DirectRecoveryMismatch(
            f"direct density/atom defects {max_direct:.17e}/{max_atom:.17e} "
            f"exceed {FIT_TOLERANCE:.1e}")
    return ConversionAudit(PiecewiseFunctional(breaks, line_coefficients,
        cosine, atoms), max_fit, max_direct, max_atom, fallback,
        no_interior, fallback_width, max_spread)
