"""Bounded cellwise classical shell recovery for the F03 Qp reference.

This is an algebraic integration-by-parts check, not an equilibrium solve or
scientific qualification. The centered polynomial coefficients come from the
independent pad-moment oracle; the shell material law matches the Qp energy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import PLANE, THICKNESS
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle


@dataclass(frozen=True)
class ShellWork:
    volume: float
    support: float
    free: float
    interior: float

    @property
    def total(self) -> float:
        return self.volume + self.support + self.free + self.interior


class PiecewiseQpShellRecovery:
    """Recover Q1--Q3 displacement, resultant and signed cell-edge work."""

    def __init__(self, trace: FinitePadQpTrace):
        if not isinstance(trace, FinitePadQpTrace):
            raise TypeError("a finite-pad Qp trace is required")
        self.trace = trace
        self.oracle = PiecewisePadMomentOracle(
            trace.p, x=trace.x, y=trace.y, offsets=trace.offsets,
            halfwidth=trace.a, j=trace.j)
        self.roots, self.weights = np.polynomial.legendre.leggauss(trace.p+1)

    def coefficients(self, q):
        return self.oracle.coefficients(q)

    def _check_coefficients(self, coefficients):
        c = np.asarray(coefficients, dtype=float)
        expected = (2, len(self.trace.x)-1, len(self.trace.y)-1,
                    self.trace.p+1, self.trace.p+1)
        if c.shape != expected or not np.isfinite(c).all():
            raise ValueError("invalid shell polynomial coefficients")
        return c

    @staticmethod
    def _powers(t, degree):
        order = np.arange(degree+1)
        value = t**order
        first = np.zeros(degree+1)
        first[1:] = order[1:]*t**(order[1:]-1)
        second = np.zeros(degree+1)
        second[2:] = order[2:]*(order[2:]-1)*t**(order[2:]-2)
        return value, first, second

    def state(self, coefficients, i, k, x, y):
        """Return (u, engineering strain, T, div T) on one closed cell."""
        c = self._check_coefficients(coefficients)
        if not (0 <= i < len(self.trace.x)-1 and
                0 <= k < len(self.trace.y)-1):
            raise ValueError("shell cell outside bounded grid")
        xl, xr = self.trace.x[i:i+2]
        yb, yt = self.trace.y[k:k+2]
        if not (xl <= x <= xr and yb <= y <= yt):
            raise ValueError("evaluation point outside selected shell cell")
        hx, hy = xr-xl, yt-yb
        px, dpx, ddpx = self._powers(2*(x-xl)/hx-1, self.trace.p)
        py, dpy, ddpy = self._powers(2*(y-yb)/hy-1, self.trace.p)
        block = c[:, i, k]

        def evaluate(ax, ay):
            return np.einsum("cab,a,b->c", block, ax, ay)

        u = evaluate(px, py)
        ux = (2/hx)*evaluate(dpx, py)
        uy = (2/hy)*evaluate(px, dpy)
        uxx = (2/hx)**2*evaluate(ddpx, py)
        uxy = (4/(hx*hy))*evaluate(dpx, dpy)
        uyy = (2/hy)**2*evaluate(px, ddpy)
        strain = np.array((ux[0], uy[1], uy[0]+ux[1]))
        strain_x = np.array((uxx[0], uxy[1], uxy[0]+uxx[1]))
        strain_y = np.array((uxy[0], uyy[1], uyy[0]+uxy[1]))
        resultant = THICKNESS*(PLANE@strain)
        resultant_x = THICKNESS*(PLANE@strain_x)
        resultant_y = THICKNESS*(PLANE@strain_y)
        tensor = np.array(((resultant[0], resultant[2]),
                           (resultant[2], resultant[1])))
        divergence = np.array((resultant_x[0]+resultant_y[2],
                               resultant_x[2]+resultant_y[1]))
        return u, strain, tensor, divergence

    def _rule(self, low, high):
        return (low+(high-low)*(self.roots+1)/2,
                (high-low)*self.weights/2)

    def outer_traction(self, coefficients, axis, side, segment, coordinate):
        """Physical T n on an outer x/y edge, with outward normal."""
        if axis == "x":
            if side not in (-1, 1) or not 0 <= segment < len(self.trace.y)-1:
                raise ValueError("invalid outer x edge")
            i = 0 if side == -1 else len(self.trace.x)-2
            x = self.trace.x[0] if side == -1 else self.trace.x[-1]
            tensor = self.state(coefficients, i, segment, x, coordinate)[2]
            return side*tensor[:, 0]
        if axis == "y":
            if side not in (-1, 1) or not 0 <= segment < len(self.trace.x)-1:
                raise ValueError("invalid outer y edge")
            k = 0 if side == -1 else len(self.trace.y)-2
            y = self.trace.y[0] if side == -1 else self.trace.y[-1]
            tensor = self.state(coefficients, segment, k, coordinate, y)[2]
            return side*tensor[:, 1]
        raise ValueError("edge axis must be x or y")

    def interior_jump(self, coefficients, axis, edge, segment, coordinate,
                      *, reverse=False):
        """T- n- + T+ n+; reverse exchanges the two normal orientations."""
        if axis == "x":
            if not 1 <= edge < len(self.trace.x)-1:
                raise ValueError("invalid interior x edge")
            x = self.trace.x[edge]
            minus = self.state(coefficients, edge-1, segment, x, coordinate)[2]
            plus = self.state(coefficients, edge, segment, x, coordinate)[2]
            direction = 0
        elif axis == "y":
            if not 1 <= edge < len(self.trace.y)-1:
                raise ValueError("invalid interior y edge")
            y = self.trace.y[edge]
            minus = self.state(coefficients, segment, edge-1, coordinate, y)[2]
            plus = self.state(coefficients, segment, edge, coordinate, y)[2]
            direction = 1
        else:
            raise ValueError("edge axis must be x or y")
        if reverse:
            plus, minus = minus, plus
            return plus[:, direction]-minus[:, direction]
        return minus[:, direction]-plus[:, direction]

    def energy_work(self, q, z):
        """Independent polynomial quadrature for a_s(q,z)."""
        q_coeff, z_coeff = self.coefficients(q), self.coefficients(z)
        total = 0.
        for i, (xl, xr) in enumerate(zip(self.trace.x, self.trace.x[1:])):
            xx, wx = self._rule(xl, xr)
            for k, (yb, yt) in enumerate(zip(self.trace.y, self.trace.y[1:])):
                yy, wy = self._rule(yb, yt)
                for x, weight_x in zip(xx, wx):
                    for y, weight_y in zip(yy, wy):
                        eps = self.state(z_coeff, i, k, x, y)[1]
                        _, _, t, _ = self.state(q_coeff, i, k, x, y)
                        total += weight_x*weight_y*(t[0, 0]*eps[0]
                            +t[1, 1]*eps[1]+t[0, 1]*eps[2])
        return total

    def integration_by_parts(self, q, z):
        """Signed volume, supported/free outer edge, and interior jump work."""
        q_coeff, z_coeff = self.coefficients(q), self.coefficients(z)
        volume = support = free = interior = 0.
        for i, (xl, xr) in enumerate(zip(self.trace.x, self.trace.x[1:])):
            xx, wx = self._rule(xl, xr)
            for k, (yb, yt) in enumerate(zip(self.trace.y, self.trace.y[1:])):
                yy, wy = self._rule(yb, yt)
                for x, weight_x in zip(xx, wx):
                    for y, weight_y in zip(yy, wy):
                        z_value = self.state(z_coeff, i, k, x, y)[0]
                        div = self.state(q_coeff, i, k, x, y)[3]
                        volume -= weight_x*weight_y*(div@z_value)
        for side, i in ((-1, 0), (1, len(self.trace.x)-2)):
            x = self.trace.x[0] if side == -1 else self.trace.x[-1]
            for k, (yb, yt) in enumerate(zip(self.trace.y, self.trace.y[1:])):
                yy, wy = self._rule(yb, yt)
                for y, weight in zip(yy, wy):
                    z_value = self.state(z_coeff, i, k, x, y)[0]
                    support += weight*(self.outer_traction(
                        q_coeff, "x", side, k, y)@z_value)
        for side, k in ((-1, 0), (1, len(self.trace.y)-2)):
            y = self.trace.y[0] if side == -1 else self.trace.y[-1]
            for i, (xl, xr) in enumerate(zip(self.trace.x, self.trace.x[1:])):
                xx, wx = self._rule(xl, xr)
                for x, weight in zip(xx, wx):
                    z_value = self.state(z_coeff, i, k, x, y)[0]
                    free += weight*(self.outer_traction(
                        q_coeff, "y", side, i, x)@z_value)
        for edge in range(1, len(self.trace.x)-1):
            x = self.trace.x[edge]
            for k, (yb, yt) in enumerate(zip(self.trace.y, self.trace.y[1:])):
                yy, wy = self._rule(yb, yt)
                for y, weight in zip(yy, wy):
                    z_value = self.state(z_coeff, edge-1, k, x, y)[0]
                    interior += weight*(self.interior_jump(
                        q_coeff, "x", edge, k, y)@z_value)
        for edge in range(1, len(self.trace.y)-1):
            y = self.trace.y[edge]
            for i, (xl, xr) in enumerate(zip(self.trace.x, self.trace.x[1:])):
                xx, wx = self._rule(xl, xr)
                for x, weight in zip(xx, wx):
                    z_value = self.state(z_coeff, i, edge-1, x, y)[0]
                    interior += weight*(self.interior_jump(
                        q_coeff, "y", edge, i, x)@z_value)
        return ShellWork(volume, support, free, interior)

    def force_moment_channels(self, q):
        """Fx, Fy, Mz of each signed residual channel about the origin."""
        xx, yy = np.meshgrid(self.trace.nodes_x, self.trace.nodes_y,
                             indexing="ij")
        zero = np.zeros(self.trace.n)
        virtual = (np.r_[np.ones(self.trace.n), zero],
                   np.r_[zero, np.ones(self.trace.n)],
                   np.r_[-yy.ravel(), xx.ravel()])
        work = [self.integration_by_parts(q, z) for z in virtual]
        return {name: np.array([getattr(w, name) for w in work])
                for name in ("volume", "support", "free", "interior")}
