"""Independent, bounded polynomial-moment reference for the F03 finite pads.

This module reconstructs a tensor polynomial from shared nodal values by a
Vandermonde solve on each cell. It then integrates monomials over clipped
physical pad rectangles. Station derivatives use polynomial edge values and
Leibniz identities. It contains no shell energy or equilibrium calculation.
"""

from __future__ import annotations

import math
import numbers

import numpy as np


PANEL_X = (-.5, 1.5)
PANEL_Y = (-.5, .5)
OFFSETS = ((-.2, -.23), (.2, -.23), (.2, .23), (-.2, .23))
HALFWIDTH = .05
REPRESENTED_J = .2**2 + .23**2 + 2*HALFWIDTH**2/3


class PiecewisePadMomentOracle:
    """Physical pad moments of a shared-node Qp field, for p=1,2,3."""

    def __init__(self, p, x=None, y=None, offsets=OFFSETS,
                 halfwidth=HALFWIDTH, j=REPRESENTED_J):
        if isinstance(p, bool) or not isinstance(p, numbers.Integral) or p not in (1, 2, 3):
            raise ValueError("degree must be 1, 2, or 3")
        self.p = int(p)
        self.offsets = tuple((float(dx), float(dy)) for dx, dy in offsets)
        self.a, self.j = float(halfwidth), float(j)
        if x is None:
            x = sorted({*PANEL_X, *(s+dx+sign*self.a
                for s in (0., 1.) for dx, _ in self.offsets
                for sign in (-1., 1.))})
        if y is None:
            y = sorted({*PANEL_Y, *(dy+sign*self.a
                for _, dy in self.offsets for sign in (-1., 1.))})
        self.x = tuple(float(value) for value in x)
        self.y = tuple(float(value) for value in y)
        if (len(self.offsets) != 4 or len(self.x) < 2 or len(self.y) < 2 or
                (len(self.x)-1)*(len(self.y)-1) > 256 or
                any(not math.isfinite(value) for value in
                    (*self.x, *self.y, self.a, self.j,
                     *(value for pair in self.offsets for value in pair))) or
                any(right <= left for left, right in zip(self.x, self.x[1:])) or
                any(right <= left for left, right in zip(self.y, self.y[1:])) or
                self.a <= 0 or self.j <= 0):
            raise ValueError("invalid bounded pad geometry")
        for dx, dy in self.offsets:
            if (dx-self.a < max(self.x[0], PANEL_X[0]) or
                    1+dx+self.a > min(self.x[-1], PANEL_X[-1]) or
                    dy-self.a < max(self.y[0], PANEL_Y[0]) or
                    dy+self.a > min(self.y[-1], PANEL_Y[-1])):
                raise ValueError("pad leaves shell domain")
        self.nx = (len(self.x)-1)*self.p+1
        self.ny = (len(self.y)-1)*self.p+1
        self.n = self.nx*self.ny
        self.area = len(self.offsets)*(2*self.a)**2
        # Centered local coordinates keep the Q3 tensor Vandermonde well
        # conditioned; they still give exact polynomial cell moments.
        local = 2*np.arange(self.p+1, dtype=float)/self.p-1
        vandermonde = np.array([
            [(tx**i)*(ty**k)
             for i in range(self.p+1) for k in range(self.p+1)]
            for tx in local for ty in local], dtype=float)
        if np.linalg.cond(vandermonde) > 1e5:
            raise ArithmeticError("local polynomial reconstruction is ill conditioned")
        self._vandermonde = vandermonde

    def coefficients(self, q):
        """Return component/cell/local-monomial coefficients from global q."""
        values = np.asarray(q, dtype=float)
        if values.shape != (2*self.n,) or not np.isfinite(values).all():
            raise ValueError("q must contain two finite shared nodal fields")
        fields = values.reshape(2, self.nx, self.ny)
        result = np.empty((2, len(self.x)-1, len(self.y)-1,
                           self.p+1, self.p+1))
        for i in range(len(self.x)-1):
            for k in range(len(self.y)-1):
                block = fields[:, i*self.p:i*self.p+self.p+1,
                               k*self.p:k*self.p+self.p+1]
                solved = np.linalg.solve(self._vandermonde,
                                         block.reshape(2, -1).T)
                result[:, i, k] = solved.T.reshape(2, self.p+1, self.p+1)
        return result

    @staticmethod
    def _moment(low, high, degree):
        # Local centered coordinates remain in [-1,1].
        return np.array([(high**(order+1)-low**(order+1))/(order+1)
                         for order in range(degree+1)])

    def _area(self, coeff, low, high, bottom, top, station):
        total = np.zeros(3)
        for i, (xl, xr) in enumerate(zip(self.x, self.x[1:])):
            left, right = max(low, xl), min(high, xr)
            if right <= left:
                continue
            hx = xr-xl
            tx = self._moment(2*(left-xl)/hx-1, 2*(right-xl)/hx-1, self.p+1)
            for k, (yb, yt) in enumerate(zip(self.y, self.y[1:])):
                down, up = max(bottom, yb), min(top, yt)
                if up <= down:
                    continue
                hy = yt-yb
                ty = self._moment(2*(down-yb)/hy-1, 2*(up-yb)/hy-1, self.p+1)
                cx, cy = coeff[:, i, k]
                scale = hx*hy/4
                ux = scale*np.einsum("ik,i,k->", cx, tx[:-1], ty[:-1])
                uy = scale*np.einsum("ik,i,k->", cy, tx[:-1], ty[:-1])
                yu = scale*((yb+hy/2)*np.einsum("ik,i,k->", cx, tx[:-1], ty[:-1])
                    + (hy/2)*np.einsum("ik,i,k->", cx, tx[:-1], ty[1:]))
                xv = scale*((xl+hx/2-station)*np.einsum("ik,i,k->", cy, tx[:-1], ty[:-1])
                    + (hx/2)*np.einsum("ik,i,k->", cy, tx[1:], ty[:-1]))
                total += (ux, uy, (xv-yu)/self.j)
        return total

    def _edge(self, coeff, x, bottom, top, side):
        i = int(np.searchsorted(self.x, x, side=side)-1)
        if x == self.x[0]:
            i = 0
        elif x == self.x[-1]:
            i = len(self.x)-2
        if i < 0 or i >= len(self.x)-1:
            raise ValueError("pad edge outside shell domain")
        hx = self.x[i+1]-self.x[i]
        t = 2*(x-self.x[i])/hx-1
        powers = t**np.arange(self.p+1)
        derivative = np.zeros(self.p+1)
        derivative[1:] = 2*np.arange(1, self.p+1)*t**np.arange(self.p)/hx
        # ux, uy, ux,x, uy,x, y*ux, y*ux,x, all integrated along the edge.
        result = np.zeros(6)
        for k, (yb, yt) in enumerate(zip(self.y, self.y[1:])):
            down, up = max(bottom, yb), min(top, yt)
            if up <= down:
                continue
            hy = yt-yb
            my = self._moment(2*(down-yb)/hy-1, 2*(up-yb)/hy-1, self.p+1)
            cx, cy = coeff[:, i, k]
            for row, polynomial, xp, weighted in (
                (0, cx, powers, False), (1, cy, powers, False),
                (2, cx, derivative, False), (3, cy, derivative, False),
                (4, cx, powers, True), (5, cx, derivative, True)):
                ym = (yb+hy/2)*my[:-1]+(hy/2)*my[1:] if weighted else my[:-1]
                result[row] += (hy/2)*np.einsum("ik,i,k->", polynomial, xp, ym)
        return result

    def _closed_limit(self, value, station, offset):
        # Match a represented crossing only for its own pad side. Distinct
        # nearby binary64 events retain their own measure and limiting cell.
        for edge in self.x:
            if edge-offset == station:
                return edge
        return value

    def evaluate(self, coefficients, station, *, side="right"):
        """Return physical pose and first/second one-sided station derivatives."""
        s = float(station)
        if not math.isfinite(s) or not 0 <= s <= 1:
            raise ValueError("station outside reference beam")
        if side not in ("left", "right"):
            raise ValueError("one-sided cell selection required")
        coeff = np.asarray(coefficients, dtype=float)
        expected = (2, len(self.x)-1, len(self.y)-1,
                    self.p+1, self.p+1)
        if coeff.shape != expected or not np.isfinite(coeff).all():
            raise ValueError("invalid local polynomial coefficients")
        pose, first, second = (np.zeros(3) for _ in range(3))
        for ox, oy in self.offsets:
            l, r = ox-self.a, ox+self.a
            low = self._closed_limit(s+l, s, l)
            high = self._closed_limit(s+r, s, r)
            bottom, top = oy-self.a, oy+self.a
            area = self._area(coeff, low, high, bottom, top, s)
            left = self._edge(coeff, low, bottom, top, side)
            right = self._edge(coeff, high, bottom, top, side)
            pose += area
            first += (right[0]-left[0], right[1]-left[1],
                      (r*right[1]-l*left[1]-area[1]-right[4]+left[4])/self.j)
            second += (right[2]-left[2], right[3]-left[3],
                       (r*right[3]-l*left[3]-right[1]+left[1]
                        -right[5]+left[5])/self.j)
        return pose/self.area, first/self.area, second/self.area

    def moments(self, q, station, *, side="right"):
        return self.evaluate(self.coefficients(q), station, side=side)
