"""Bounded Q1 finite-pad trace preflight for the independent F03 reference.

This is a small dense *trace* oracle only. It assembles no shell or beam
stiffness, solves no equilibrium problem, and selects no native line law.
The four material pads have fixed reference correspondence.
"""

from __future__ import annotations

import math

import numpy as np


PANEL_X = (-.5, 1.5)
PANEL_Y = (-.5, .5)
OFFSETS = ((-.2, -.23), (.2, -.23), (.2, .23), (-.2, .23))
HALFWIDTH = .05
J = .2**2 + .23**2 + 2*HALFWIDTH**2/3
ROOTS = (-1/math.sqrt(3), 1/math.sqrt(3))


class FinitePadQ1Trace:
    """Exact-degree Q1 pad quadrature and independent Leibniz derivatives."""

    def __init__(self, x=None, y=None, offsets=OFFSETS, halfwidth=HALFWIDTH, j=J):
        self.offsets = tuple((float(dx), float(dy)) for dx, dy in offsets)
        self.a, self.j = float(halfwidth), float(j)
        if x is None:
            x = sorted({*PANEL_X, *(station+dx+sign*self.a
                for station in (0., 1.) for dx, _ in self.offsets
                for sign in (-1., 1.))})
        if y is None:
            y = sorted({*PANEL_Y, *(dy+sign*self.a
                for _, dy in self.offsets for sign in (-1., 1.))})
        self.x = tuple(float(v) for v in x)
        self.y = tuple(float(v) for v in y)
        if (len(self.x) < 2 or len(self.y) < 2 or len(self.offsets) != 4 or
                any(not math.isfinite(v) for v in (*self.x, *self.y,
                    *(v for pair in self.offsets for v in pair), self.a, self.j)) or
                any(b <= a for a, b in zip(self.x, self.x[1:])) or
                any(b <= a for a, b in zip(self.y, self.y[1:])) or
                self.a <= 0 or self.j <= 0):
            raise ValueError("invalid bounded Q1 finite-pad geometry")
        for dx, dy in self.offsets:
            if (dx-self.a < PANEL_X[0] or 1+dx+self.a > PANEL_X[-1] or
                    dy-self.a < PANEL_Y[0] or dy+self.a > PANEL_Y[-1] or
                    dx-self.a < self.x[0] or 1+dx+self.a > self.x[-1] or
                    dy-self.a < self.y[0] or dy+self.a > self.y[-1]):
                raise ValueError("finite pad leaves the shell reference domain")
        self.n = len(self.x)*len(self.y)
        self.area = len(self.offsets)*(2*self.a)**2

    def station_breakpoints(self):
        """Represented pad-side/cell-edge crossings inside the beam span."""
        events = {0., 1.}
        for edge in self.x:
            for dx, _ in self.offsets:
                for sign in (-1., 1.):
                    station = edge-(dx+sign*self.a)
                    if 0. < station < 1.:
                        events.add(station)
        return tuple(sorted(events))

    def _snap_x(self, value):
        """Resolve one-ulp cancellation at a represented crossing."""
        index = int(np.searchsorted(self.x, value))
        for candidate in (index-1, index):
            if 0 <= candidate < len(self.x):
                edge = self.x[candidate]
                if abs(value-edge) <= 8*np.finfo(float).eps*max(1., abs(value), abs(edge)):
                    return edge
        return value

    def _host(self, values, coordinate, side):
        if side not in ("left", "right"):
            raise ValueError("one-sided cell selection required")
        index = int(np.searchsorted(values, coordinate,
            side="left" if side == "left" else "right")-1)
        if index < 0 or index >= len(values)-1:
            raise ValueError("trace point outside reference domain")
        return index

    def _shape(self, x, y, *, side="right"):
        i, k = self._host(self.x, x, side), self._host(self.y, y, "right")
        hx, hy = self.x[i+1]-self.x[i], self.y[k+1]-self.y[k]
        tx, ty = (x-self.x[i])/hx, (y-self.y[k])/hy
        indices = np.array((i*len(self.y)+k, (i+1)*len(self.y)+k,
            i*len(self.y)+k+1, (i+1)*len(self.y)+k+1), dtype=int)
        values = np.array(((1-tx)*(1-ty), tx*(1-ty),
            (1-tx)*ty, tx*ty))
        dx = np.array((-(1-ty)/hx, (1-ty)/hx, -ty/hx, ty/hx))
        return indices, values, dx

    def _rows(self, x, y, *, side="right"):
        indices, values, dx = self._shape(x, y, side=side)
        vx, vy, dxx, dxy = (np.zeros(2*self.n) for _ in range(4))
        vx[indices], vy[self.n+indices] = values, values
        dxx[indices], dxy[self.n+indices] = dx, dx
        return vx, vy, dxx, dxy

    @staticmethod
    def _intervals(edges, low, high):
        for left, right in zip(edges, edges[1:]):
            l, r = max(left, low), min(right, high)
            if r > l:
                yield l, r

    def _area_rows(self, low, high, bottom, top):
        """Q1 area moments; two Gauss points exactly integrate yaw products."""
        tx, ty, moment = (np.zeros(2*self.n) for _ in range(3))
        for xl, xr in self._intervals(self.x, low, high):
            for yl, yr in self._intervals(self.y, bottom, top):
                weight = (xr-xl)*(yr-yl)/4
                for gx in ROOTS:
                    xx = (xl+xr+(xr-xl)*gx)/2
                    for gy in ROOTS:
                        yy = (yl+yr+(yr-yl)*gy)/2
                        vx, vy, _, _ = self._rows(xx, yy)
                        tx += weight*vx
                        ty += weight*vy
                        moment += weight*(xx*vy-yy*vx)
        return tx, ty, moment

    def _edge_rows(self, x, bottom, top, *, side):
        vx, vy, dxx, dxy = (np.zeros(2*self.n) for _ in range(4))
        etax = np.zeros(2*self.n)
        for yl, yr in self._intervals(self.y, bottom, top):
            for root in ROOTS:
                yy = (yl+yr+(yr-yl)*root)/2
                weight = (yr-yl)/2
                a, b, da, db = self._rows(x, yy, side=side)
                vx += weight*a
                vy += weight*b
                dxx += weight*da
                dxy += weight*db
                etax += weight*yy*a
        return vx, vy, dxx, dxy, etax

    def matrices(self, s, *, side="right"):
        """A, A', A'' at a station; A'' is one-sided at cell crossings."""
        if not math.isfinite(s) or not 0 <= s <= 1:
            raise ValueError("station outside bounded reference beam")
        if side not in ("left", "right"):
            raise ValueError("one-sided derivative choice required")
        a0 = np.zeros((3, 2*self.n))
        a1 = np.zeros_like(a0)
        a2 = np.zeros_like(a0)
        for ox, oy in self.offsets:
            l, r = ox-self.a, ox+self.a
            bottom, top = oy-self.a, oy+self.a
            # Only a declared represented event receives one-ulp closure.
            # Nearby ordinary stations retain their actual moving limits.
            low, high = s+l, s+r
            if s in self.station_breakpoints():
                low, high = self._snap_x(low), self._snap_x(high)
            ix, iy, moment = self._area_rows(low, high, bottom, top)
            lx, ly, ldx, ldy, leta = self._edge_rows(low, bottom, top,
                side=side)
            rx, ry, rdx, rdy, reta = self._edge_rows(high, bottom, top,
                side=side)
            a0[0] += ix
            a0[1] += iy
            a0[2] += (moment-s*iy)/self.j
            a1[0] += rx-lx
            a1[1] += ry-ly
            a1[2] += (r*ry-l*ly-iy-reta+leta)/self.j
            a2[0] += rdx-ldx
            a2[1] += rdy-ldy
            a2[2] += (r*rdy-l*ldy-ry+ly-
                # eta*u_x part: derivative of its edge difference.
                self._edge_eta_dx(high, bottom, top, side)+
                self._edge_eta_dx(low, bottom, top, side))/self.j
        return tuple(matrix/self.area for matrix in (a0, a1, a2))

    def _edge_eta_dx(self, x, bottom, top, side):
        out = np.zeros(2*self.n)
        for yl, yr in self._intervals(self.y, bottom, top):
            for root in ROOTS:
                yy = (yl+yr+(yr-yl)*root)/2
                _, _, dx, _ = self._rows(x, yy, side=side)
                out += (yr-yl)/2*yy*dx
        return out

    @property
    def free_columns(self):
        ny = len(self.y)
        nodes = [i*ny+k for i in range(1, len(self.x)-1)
            for k in range(ny)]
        return np.array(nodes+[self.n+v for v in nodes], dtype=int)
