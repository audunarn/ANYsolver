"""Preparatory full H1-dual Green norm for represented classical F03 Qp lines.

Each row holds physical Legendre coefficients on one *local* interval,
X=2(s-left)/(right-left)-1. The explicit cosine and endpoint atoms remain
separate. A recovery-to-coefficient audit and scientific gate are separate.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial import Polynomial
from numpy.polynomial.legendre import leg2poly, leggauss, legvander, poly2leg


ELL = .46
MAX_INTERVALS = 128
MAX_DEGREE = 8
CHECK_FLOOR = (1000.)**2
CHECK_TOLERANCE = 1e-10
# The prescribed squared-term floor permits up to 1e-4 absolute 48/64
# disagreement when both compared terms are near zero. Passing this check
# alone is not a scientific error bound on a recovered Qp functional.


class GreenQuadratureDisagreement(ArithmeticError):
    """The mandatory orders 48 and 64 disagree for a line contribution."""


class NonfiniteGreenResponse(ArithmeticError):
    """A nonfinite response is invalid, rather than a vanishing norm."""


class NegativeGreenResponse(ArithmeticError):
    """A negative squared dual norm is retained as a numerical failure."""


def _array(value, shape, label):
    result = np.array(value, dtype=np.float64, copy=True)
    if result.shape != shape or not np.all(np.isfinite(result)):
        raise ValueError(f"invalid {label}")
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class PiecewiseFunctional:
    """Signed physical line density and root/tip atoms for three pose channels."""

    breaks: np.ndarray
    coefficients: np.ndarray
    cosine: np.ndarray
    atoms: np.ndarray

    def __post_init__(self):
        breaks = np.asarray(self.breaks)
        coeff = np.asarray(self.coefficients)
        if (breaks.ndim != 1 or not 2 <= len(breaks) <= MAX_INTERVALS+1 or
                coeff.ndim != 3 or coeff.shape[0] != len(breaks)-1 or
                not 1 <= coeff.shape[1] <= MAX_DEGREE+1 or coeff.shape[2] != 3):
            raise ValueError("outside bounded piecewise functional shape")
        breaks = _array(breaks, (len(breaks),), "breakpoints")
        if (breaks[0] != 0. or breaks[-1] != 1. or
                np.any(np.diff(breaks) <= 0.)):
            raise ValueError("breakpoints must partition the unit beam exactly")
        object.__setattr__(self, "breaks", breaks)
        object.__setattr__(self, "coefficients", _array(
            coeff, coeff.shape, "density coefficients"))
        object.__setattr__(self, "cosine", _array(self.cosine, (3,), "cosine amplitudes"))
        object.__setattr__(self, "atoms", _array(self.atoms, (2, 3), "endpoint atoms"))

    def refine(self, breaks):
        """Restrict local polynomials algebraically to an exact refinement."""
        target = np.asarray(breaks, dtype=np.float64)
        if (target.ndim != 1 or len(target) < 2 or target[0] != 0. or
                target[-1] != 1. or not np.isfinite(target).all() or
                np.any(np.diff(target) <= 0.) or
                not np.isin(self.breaks, target).all()):
            raise ValueError("target must retain every represented breakpoint")
        if np.array_equal(target, self.breaks):
            return self
        if len(target)-1 > MAX_INTERVALS:
            raise ValueError("outside bounded piecewise functional intervals")
        result = np.empty((len(target)-1, *self.coefficients.shape[1:]))
        for i, (left, right) in enumerate(zip(target[:-1], target[1:])):
            source = int(np.searchsorted(self.breaks, left, side="right")-1)
            old_left, old_right = self.breaks[source:source+2]
            alpha = (right-left)/(old_right-old_left)
            beta = (left-old_left)/(old_right-old_left) + (right-old_right)/(old_right-old_left)
            for channel in range(3):
                old = Polynomial(leg2poly(self.coefficients[source, :, channel]))
                transformed = poly2leg(old(Polynomial((beta, alpha))).coef)
                result[i, :, channel] = 0.
                result[i, :len(transformed), channel] = transformed
        return PiecewiseFunctional(target, result, self.cosine, self.atoms)

    def difference(self, other):
        """Subtract coefficients, cosine amplitudes and atoms before integration."""
        if not isinstance(other, PiecewiseFunctional):
            raise TypeError("a piecewise functional is required")
        merged = np.unique(np.r_[self.breaks, other.breaks])
        first, second = self.refine(merged), other.refine(merged)
        degree_count = max(first.coefficients.shape[1], second.coefficients.shape[1])
        result = np.zeros((len(merged)-1, degree_count, 3))
        result[:, :first.coefficients.shape[1]] += first.coefficients
        result[:, :second.coefficients.shape[1]] -= second.coefficients
        return PiecewiseFunctional(merged, result,
                                   first.cosine-second.cosine,
                                   first.atoms-second.atoms)

    def exactly_zero(self):
        return (not np.any(self.coefficients) and not np.any(self.cosine)
                and not np.any(self.atoms))


@dataclass(frozen=True)
class GreenNorm:
    squared_channels: np.ndarray
    squared_total: float
    density_density: np.ndarray
    density_atoms: np.ndarray
    atom_atoms: np.ndarray
    density_order_discrepancy: np.ndarray
    cross_order_discrepancy: np.ndarray

    def __post_init__(self):
        # A frozen dataclass does not freeze ndarray storage. Own every
        # diagnostic so a caller cannot mutate a reported result in place.
        for field in ("squared_channels", "density_density", "density_atoms",
                      "atom_atoms", "density_order_discrepancy",
                      "cross_order_discrepancy"):
            value = np.array(getattr(self, field), dtype=np.float64, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, field, value)


def _rule(order):
    nodes, weights = leggauss(order)
    return (nodes+1.)/2., weights/2.


def _terms(functional, order):
    x, w = _rule(order)
    breaks = functional.breaks
    coeff = functional.coefficients * np.array((1., 1., 1./ELL))
    cosine = functional.cosine * np.array((1., 1., 1./ELL))
    basis = legvander(2*x-1, coeff.shape[1]-1)
    density = np.einsum("qm,imc->iqc", basis, coeff)
    density_density = np.zeros(3)
    a = np.zeros((len(coeff), 3))
    b = np.zeros_like(a)
    sinh = np.sinh(1.)
    for i, (left, right) in enumerate(zip(breaks[:-1], breaks[1:])):
        width = right-left  # A one-ulp interval retains its positive measure.
        s = left+width*x
        ds = density[i]+np.cos(2*np.pi*s)[:, None]*cosine
        a[i] = width*np.einsum("q,qc->c", w*np.cosh(s), ds)
        b[i] = width*np.einsum("q,qc->c", w*np.cosh(1-s), ds)

        # t <= s. Add the transposed half explicitly; no diagonal strip is
        # omitted or counted twice, including on tiny represented intervals.
        local_t = x[:, None]*x[None, :]
        t = left+width*local_t
        tbasis = legvander((2*local_t-1).ravel(), coeff.shape[1]-1)
        dt = (tbasis@coeff[i]).reshape(order, order, 3)
        dt += np.cos(2*np.pi*t)[..., None]*cosine
        weight = (width*width)*w[:, None]*w[None, :]*x[:, None]
        kernel = np.cosh(t)*np.cosh(1-s[:, None])/sinh
        density_density += np.einsum("ij,ijc->c", weight*kernel,
                                     2*ds[:, None, :]*dt)
    prefix = np.zeros(3)
    for ai, bi in zip(a, b):
        density_density += 2*prefix*bi/sinh
        prefix += ai
    atoms = functional.atoms*np.array((1., 1., 1./ELL))
    cross = 2*(atoms[0]*b.sum(axis=0)+atoms[1]*a.sum(axis=0))/sinh
    gram = np.array(((np.cosh(1.), 1.), (1., np.cosh(1.))))/sinh
    atom_term = np.einsum("ic,ij,jc->c", atoms, gram, atoms)
    return density_density, cross, atom_term


def _discrepancy(first, second):
    return np.abs(first-second)/np.maximum.reduce((
        np.abs(first), np.abs(second), np.full(3, CHECK_FLOOR)))


def norm_squared(functional: PiecewiseFunctional):
    """Mandatory 48/64 check; return signed terms and the accepted 64 result."""
    if not isinstance(functional, PiecewiseFunctional):
        raise TypeError("a piecewise functional is required")
    if functional.exactly_zero():
        zeros = np.zeros(3)
        return GreenNorm(zeros.copy(), 0., zeros.copy(), zeros.copy(),
                         zeros.copy(), zeros.copy(), zeros.copy())
    low = _terms(functional, 48)
    high = _terms(functional, 64)
    if not all(np.isfinite(term).all() for term in (*low, *high)):
        raise NonfiniteGreenResponse("nonfinite Green contribution")
    dd = _discrepancy(low[0], high[0])
    cross = _discrepancy(low[1], high[1])
    if np.any(dd > CHECK_TOLERANCE) or np.any(cross > CHECK_TOLERANCE):
        raise GreenQuadratureDisagreement("48/64 Green density or atom cross mismatch")
    channels = high[0]+high[1]+high[2]
    if not np.isfinite(channels).all():
        raise NonfiniteGreenResponse("nonfinite squared Green channels")
    if np.any(channels < 0.):
        raise NegativeGreenResponse("negative squared Green channel")
    total = float(np.sum(channels))
    if not np.isfinite(total):
        raise NonfiniteGreenResponse("nonfinite total squared Green norm")
    return GreenNorm(channels, total, *high, dd, cross)


def comparison(first: PiecewiseFunctional, second: PiecewiseFunctional):
    """Retain both operand norms and the coefficient-space difference norm."""
    return norm_squared(first), norm_squared(second), norm_squared(first.difference(second))
