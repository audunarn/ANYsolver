"""Preparatory conforming Qp finite-pad trace for the independent F03 reference.

Only the physical pose and its station derivatives are built here. No energy,
load, equilibrium, or scientific qualification is assembled or solved.
"""

from __future__ import annotations

import math
import numbers

import numpy as np


PANEL_X = (-.5, 1.5)
PANEL_Y = (-.5, .5)
OFFSETS = ((-.2, -.23), (.2, -.23), (.2, .23), (-.2, .23))
HALFWIDTH = .05
# Preserve the represented physical normalization used by the Q1 reference.
J = .2**2 + .23**2 + 2*HALFWIDTH**2/3


class FinitePadQpTrace:
    """Dense, bounded trace oracle for shared tensor Qp nodes, p in 1..5."""

    def __init__(self, p, x=None, y=None, offsets=OFFSETS,
                 halfwidth=HALFWIDTH, j=J):
        if isinstance(p, bool) or not isinstance(p, numbers.Integral) or p not in (1, 2, 3, 4, 5):
            raise ValueError("Qp degree must be in 1..5")
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
        self.x = tuple(float(v) for v in x)
        self.y = tuple(float(v) for v in y)
        if (len(self.x) < 2 or len(self.y) < 2 or len(self.offsets) != 4 or
                any(not math.isfinite(v) for v in (*self.x, *self.y,
                    *(v for pair in self.offsets for v in pair), self.a, self.j)) or
                any(b <= a for a, b in zip(self.x, self.x[1:])) or
                any(b <= a for a, b in zip(self.y, self.y[1:])) or
                self.a <= 0 or self.j <= 0):
            raise ValueError("invalid bounded Qp finite-pad geometry")
        for dx, dy in self.offsets:
            if (dx-self.a < PANEL_X[0] or 1+dx+self.a > PANEL_X[-1] or
                    dy-self.a < PANEL_Y[0] or dy+self.a > PANEL_Y[-1] or
                    dx-self.a < self.x[0] or 1+dx+self.a > self.x[-1] or
                    dy-self.a < self.y[0] or dy+self.a > self.y[-1]):
                raise ValueError("finite pad leaves the shell reference domain")
        self.nx = (len(self.x)-1)*self.p+1
        self.ny = (len(self.y)-1)*self.p+1
        self.n = self.nx*self.ny
        self.area = len(self.offsets)*(2*self.a)**2
        self.nodes_x = tuple(self.x[i]+(self.x[i+1]-self.x[i])*a/self.p
            for i in range(len(self.x)-1) for a in range(self.p))+(self.x[-1],)
        self.nodes_y = tuple(self.y[k]+(self.y[k+1]-self.y[k])*b/self.p
            for k in range(len(self.y)-1) for b in range(self.p))+(self.y[-1],)
        nodes = np.arange(self.n).reshape(self.nx, self.ny)[1:-1, :].ravel()
        # Exactly the two supported x edges are removed, for both components.
        self.free_columns = np.r_[nodes, self.n+nodes]
        self._basis = []
        for a in range(self.p+1):
            poly = np.poly1d([1.])
            for b in range(self.p+1):
                if a != b:
                    poly *= np.poly1d([1., -b/self.p])/((a-b)/self.p)
            self._basis.append((poly, np.polyder(poly)))
        self._roots, self._weights = np.polynomial.legendre.leggauss(self.p+2)
        self._events = self._make_events()

    def _make_events(self):
        events = {0., 1.}
        for edge in self.x:
            for dx, _ in self.offsets:
                for sign in (-1., 1.):
                    station = edge-(dx+sign*self.a)
                    if 0. < station < 1.:
                        events.add(station)
        return tuple(sorted(events))

    def station_breakpoints(self):
        """All distinct represented crossings; no tolerance-based coalescing."""
        return self._events

    def station_intervals(self):
        """Keep even one-ulp positive intervals as physical measure."""
        return tuple(zip(self._events, self._events[1:]))

    @staticmethod
    def _host(edges, point, side):
        if side not in ("left", "right"):
            raise ValueError("one-sided cell selection required")
        i = int(np.searchsorted(edges, point, side=side)-1)
        if point == edges[0]:
            i = 0
        elif point == edges[-1]:
            i = len(edges)-2
        if i < 0 or i >= len(edges)-1:
            raise ValueError("trace point outside reference domain")
        return i

    @staticmethod
    def _intervals(edges, low, high):
        for i, (left, right) in enumerate(zip(edges, edges[1:])):
            l, r = max(left, low), min(right, high)
            if r > l:
                yield i, l, r

    def _shape(self, x, y, *, side="right", cell=None):
        i, k = cell if cell is not None else (
            self._host(self.x, x, side), self._host(self.y, y, "right"))
        hx, hy = self.x[i+1]-self.x[i], self.y[k+1]-self.y[k]
        tx, ty = (x-self.x[i])/hx, (y-self.y[k])/hy
        bx = np.array([basis(tx) for basis, _ in self._basis])
        by = np.array([basis(ty) for basis, _ in self._basis])
        dbx = np.array([derivative(tx)/hx for _, derivative in self._basis])
        indices = np.array([(i*self.p+a)*self.ny+k*self.p+b
            for a in range(self.p+1) for b in range(self.p+1)], dtype=int)
        return indices, np.outer(bx, by).ravel(), np.outer(dbx, by).ravel()

    def _area_rows(self, low, high, bottom, top, station):
        pose = np.zeros((3, 2*self.n))
        for i, xl, xr in self._intervals(self.x, low, high):
            for k, yl, yr in self._intervals(self.y, bottom, top):
                jac = (xr-xl)*(yr-yl)/4
                for gx, wx in zip(self._roots, self._weights):
                    xx = (xl+xr+(xr-xl)*gx)/2
                    for gy, wy in zip(self._roots, self._weights):
                        yy = (yl+yr+(yr-yl)*gy)/2
                        ids, shape, _ = self._shape(xx, yy, cell=(i, k))
                        weight = jac*wx*wy
                        pose[0, ids] += weight*shape
                        pose[1, self.n+ids] += weight*shape
                        pose[2, ids] -= weight*yy*shape/self.j
                        pose[2, self.n+ids] += weight*(xx-station)*shape/self.j
        return pose

    def _edge_rows(self, x, bottom, top, side):
        # x-edge integrals of u, u_x, eta*u, eta*u_x, separately by component.
        rows = np.zeros((6, 2*self.n))
        for _, yl, yr in self._intervals(self.y, bottom, top):
            for gy, wy in zip(self._roots, self._weights):
                yy = (yl+yr+(yr-yl)*gy)/2
                ids, shape, dx = self._shape(x, yy, side=side)
                weight = (yr-yl)*wy/2
                rows[0, ids] += weight*shape
                rows[1, self.n+ids] += weight*shape
                rows[2, ids] += weight*dx
                rows[3, self.n+ids] += weight*dx
                rows[4, ids] += weight*yy*shape
                rows[5, ids] += weight*yy*dx
        return rows

    def _crossing_limit(self, value, station, boundary):
        # Close only the *corresponding* represented crossing. Adjacent
        # near-duplicate events of other pad sides keep their actual limits.
        for edge in self.x:
            if edge-boundary == station:
                return edge
        return value

    def matrices(self, station, *, side="right"):
        """Return A, A', A''; at crossings A'' uses the requested side."""
        s = float(station)
        if not math.isfinite(s) or not 0 <= s <= 1:
            raise ValueError("station outside bounded reference beam")
        if side not in ("left", "right"):
            raise ValueError("one-sided derivative choice required")
        pose, first, second = (np.zeros((3, 2*self.n)) for _ in range(3))
        for ox, oy in self.offsets:
            l, r = ox-self.a, ox+self.a
            bottom, top = oy-self.a, oy+self.a
            low = self._crossing_limit(s+l, s, l)
            high = self._crossing_limit(s+r, s, r)
            pad_pose = self._area_rows(low, high, bottom, top, s)
            pose += pad_pose
            left = self._edge_rows(low, bottom, top, side)
            right = self._edge_rows(high, bottom, top, side)
            first[0] += right[0]-left[0]
            first[1] += right[1]-left[1]
            first[2] += (r*right[1]-l*left[1]-pad_pose[1]
                -right[4]+left[4])/self.j
            second[0] += right[2]-left[2]
            second[1] += right[3]-left[3]
            second[2] += (r*right[3]-l*left[3]-right[1]+left[1]
                -right[5]+left[5])/self.j
        return tuple(row/self.area for row in (pose, first, second))
