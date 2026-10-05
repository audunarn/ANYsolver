"""Preparatory coefficient-space finite-pad line integration for Q6 audits.

This removes repeated trace recovery from area quadrature without changing
the physical area projection. The original trace quadrature remains an
independent comparator at selected station windows.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.polynomial.legendre import legint, legmul, legval

from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_piecewise_functional import PiecewiseFunctional


class PreciseLineAreaAdjoint(FinitePadAreaAdjoint):
    """Use saved-state polynomial density for many area-force queries."""

    def __init__(self, trace, q, eta, functional: PiecewiseFunctional):
        super().__init__(trace, q, eta)
        if not isinstance(functional, PiecewiseFunctional) or not np.array_equal(
                functional.breaks, np.asarray(trace.station_breakpoints())):
            raise ValueError("functional partition does not match trace")
        self.functional = functional
        if np.max(np.abs(functional.atoms-np.asarray(self.atoms))) > 1e-8:
            raise ValueError("functional endpoint atoms do not match trace")
        self._primitive = np.array([[legint(functional.coefficients[i, :, j])
            for j in range(3)] for i in range(len(functional.breaks)-1)])
        self._s_primitive = [[legint(legmul(
            functional.coefficients[i, :, j], np.array((0., 1.))))
            for j in range(3)] for i in range(len(functional.breaks)-1)]

    def integrated_line(self, left: float, right: float) -> np.ndarray:
        if (not math.isfinite(left) or not math.isfinite(right) or
                left < 0. or right > 1. or left > right):
            raise ValueError("invalid bounded station interval")
        total = np.zeros(5)
        if left == right:
            return total
        for i, (lo, hi) in enumerate(zip(self.functional.breaks,
                                          self.functional.breaks[1:])):
            a, b = max(lo, left), min(hi, right)
            if b <= a:
                continue
            half = (hi-lo)/2
            mid = lo+half
            ta, tb = 2*(a-lo)/(hi-lo)-1, 2*(b-lo)/(hi-lo)-1
            integrals = np.array([half*(legval(tb, poly)-legval(ta, poly))
                for poly in self._primitive[i]])
            moments = np.array([mid*integrals[j]+half*half*(
                legval(tb, self._s_primitive[i][j])-
                legval(ta, self._s_primitive[i][j])) for j in range(3)])
            total[:3] += integrals
            total[3:] += moments[1:]
        width = right-left
        if width < 1e-8:
            midpoint = left+width/2
            cosine = np.cos(2*np.pi*midpoint)*width
            cosine_s = midpoint*cosine
        else:
            omega = 2*np.pi
            cosine = (np.sin(omega*right)-np.sin(omega*left))/omega
            cosine_s = (right*np.sin(omega*right)-
                        left*np.sin(omega*left))/omega + (
                        np.cos(omega*right)-np.cos(omega*left))/omega**2
        total[:3] += self.functional.cosine*cosine
        total[3:] += self.functional.cosine[1:]*cosine_s
        return total
