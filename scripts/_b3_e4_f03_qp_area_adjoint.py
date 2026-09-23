"""Bounded physical finite-pad adjoint for the classical F03 Qp reference.

This evaluates the area force induced by the recovered beam distribution.
It is preparatory recovery, not a native line attachment or qualification.
"""

from __future__ import annotations

import math

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0
from scripts._b3_e4_f03_qp_beam_recovery import recover_interface


class FinitePadAreaAdjoint:
    """Push a beam line density and endpoint atoms onto four physical pads."""

    def __init__(self, trace: FinitePadQpTrace, q: np.ndarray,
                 eta: np.ndarray):
        if not isinstance(trace, FinitePadQpTrace):
            raise TypeError("a finite-pad Qp trace is required")
        self.trace = trace
        self.q = np.array(q, dtype=float, copy=True)
        self.eta = np.array(eta, dtype=float, copy=True)
        endpoints = recover_interface(trace, self.q, self.eta,
                                      np.empty(0))
        self.q.setflags(write=False)
        self.eta.setflags(write=False)
        self.atoms = (endpoints["root_atom"].copy(),
                      endpoints["tip_atom"].copy())
        for atom in self.atoms:
            atom.setflags(write=False)
        self.intervals = trace.station_intervals()
        self._roots, self._weights = np.polynomial.legendre.leggauss(
            trace.p+4)

    def integrated_line(self, left: float, right: float) -> np.ndarray:
        """Integrate (d_x,d_y,d_theta,s*d_y,s*d_theta) on [left,right]."""
        if (not math.isfinite(left) or not math.isfinite(right) or
                left < 0. or right > 1. or left > right):
            raise ValueError("invalid bounded station interval")
        total = np.zeros(5)
        if left == right:
            return total
        for lo, hi in self.intervals:
            a, b = max(lo, left), min(hi, right)
            if b <= a:
                continue
            stations = (a+b)/2 + (b-a)/2*self._roots
            density = recover_interface(
                self.trace, self.q, self.eta, stations)["density"]
            # Integrate the non-polynomial dead load analytically. The
            # remaining density and its first station moment are polynomial
            # on each represented interval.
            density[:, 1] -= F0*(1.+.25*np.cos(2.*np.pi*stations))
            scale = (b-a)/2
            total[:3] += scale*(self._weights@density)
            total[3] += scale*(self._weights@(stations*density[:, 1]))
            total[4] += scale*(self._weights@(stations*density[:, 2]))
            total[1] += F0*((b-a)+.25*(math.sin(2.*math.pi*b)
                          -math.sin(2.*math.pi*a))/(2.*math.pi))
            total[3] += F0*((b*b-a*a)/2 + .25*(
                (b*math.sin(2.*math.pi*b)-a*math.sin(2.*math.pi*a))
                /(2.*math.pi) + (math.cos(2.*math.pi*b)
                                  -math.cos(2.*math.pi*a))
                /(2.*math.pi)**2))
        return total

    def _area_force(self, x: float, y: float,
                    line_cache: dict[tuple[float, float], np.ndarray]) -> np.ndarray:
        force = np.zeros(2)
        for ox, oy in self.trace.offsets:
            if not oy-self.trace.a <= y <= oy+self.trace.a:
                continue
            low = max(0., x-ox-self.trace.a)
            high = min(1., x-ox+self.trace.a)
            if high > low:
                key = (low, high)
                if key not in line_cache:
                    line_cache[key] = self.integrated_line(low, high)
                ix, iy, itheta, _, sitheta = line_cache[key]
                force += (ix-y*itheta/self.trace.j,
                          iy+(x*itheta-sitheta)/self.trace.j)
            for endpoint, atom in enumerate(self.atoms):
                if endpoint+ox-self.trace.a <= x <= endpoint+ox+self.trace.a:
                    force += (atom[0]-y*atom[2]/self.trace.j,
                              atom[1]+(x-endpoint)*atom[2]/self.trace.j)
        return force/self.trace.area

    def area_force(self, x: float, y: float) -> np.ndarray:
        """Physical force per shell reference area at one interior point."""
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("nonfinite shell point")
        return self._area_force(float(x), float(y), {})

    def area_forces(self, points: np.ndarray) -> np.ndarray:
        """Evaluate a bounded batch, sharing station integrals within it."""
        xy = np.asarray(points, dtype=float)
        if (xy.ndim != 2 or xy.shape[1] != 2 or len(xy) > 8192 or
                not np.isfinite(xy).all()):
            raise ValueError("invalid bounded shell-point batch")
        cache: dict[tuple[float, float], np.ndarray] = {}
        return np.array([self._area_force(float(x), float(y), cache)
                         for x, y in xy], dtype=float).reshape((-1, 2))

    def band_wrench(self, left: float, right: float, *,
                    include_atoms: bool = True) -> np.ndarray:
        """Signed beam-station Fx, Fy, origin Mz, with endpoint atoms once."""
        if (not 0. <= left < right <= 1. or
                not isinstance(include_atoms, bool)):
            raise ValueError("invalid physical station band")
        ix, iy, itheta, sidy, _ = self.integrated_line(left, right)
        geometric_j = sum(ox*ox+oy*oy+2*self.trace.a**2/3
                          for ox, oy in self.trace.offsets)/len(self.trace.offsets)
        gamma = geometric_j/self.trace.j
        mean_x = sum(ox for ox, _ in self.trace.offsets)/len(self.trace.offsets)
        mean_y = sum(oy for _, oy in self.trace.offsets)/len(self.trace.offsets)
        wrench = np.array((ix, iy,
                           sidy+mean_x*iy-mean_y*ix+gamma*itheta))
        if include_atoms:
            for endpoint, atom in enumerate(self.atoms):
                if (endpoint == 0 and left != 0.) or (
                        endpoint == 1 and right != 1.):
                    continue
                wrench += (atom[0], atom[1],
                           (endpoint+mean_x)*atom[1]-mean_y*atom[0]
                           +gamma*atom[2])
        return wrench

    def line_wrench(self) -> np.ndarray:
        """Integrated physical Fx, Fy, and origin Mz before the area push."""
        return self.band_wrench(0., 1.)
