"""Independent D1 radial observables; no solver/contact/AD dependencies.

Disk clipping integrates vertical strips of a disk. With u=r*sin(theta),
sqrt(r**2-u**2)=r*cos(theta), so even strips ending at a tangent have smooth
integrands. Breakpoints include every intersection of a horizontal rectangle
edge with the circle. Each strip integrates height, u*height, and
(upper**2-lower**2)/2. Full disk and contained rectangles use analytic values.
QUADPACK error estimates plus a floating arithmetic allowance are returned;
these are numerical uncertainty estimates, NOT certified interval bounds.

Q1 pressure uses exact separable polynomial antiderivatives on a fixed
reference rectangle [0.1,1.1]**2. These are NUMERICAL REFERENCE-PRESSURE
integrals: they are not the production current-area traction or physical
reaction wrench. The owner must bound that difference before using them as
physical force bins. Neither helper establishes D1 acceptance (representative
response remains 2%; nodal pressure L2 remains diagnostic only).

Positive pressure acts along +world-z. About (ox,oy,0), moments are
(integral((y-oy)*p), -integral((x-ox)*p), 0). Opening keeps the measured force
and moments; centroid is None when abs(force)<=material_force_threshold_n.
No normalized centroid/relative force error is invented at opening.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.integrate import quad

SOURCE_RECTANGLE = (0.1, 1.1, 0.1, 1.1)
PRINCIPAL_BIN_EDGES = (0.1, 0.6, 1.1)
DIAGNOSTIC_BIN_EDGES = (0.1, 0.35, 0.6, 0.85, 1.1)
_EPS = np.finfo(float).eps


@dataclass(frozen=True)
class AreaMoments:
    area_m2: float
    first_x_m3: float
    first_y_m3: float
    estimated_absolute_error: tuple[float, float, float]


@dataclass(frozen=True)
class VerticalPressureResult:
    force_n: float
    first_x_nm: float
    first_y_nm: float
    moment_nm: tuple[float, float, float]
    resultant_xy_m: tuple[float, float] | None
    estimated_absolute_error: tuple[float, float, float]
    estimated_moment_error_nm: tuple[float, float, float]


@dataclass(frozen=True)
class BinnedPressureResult:
    integration_measure: str
    total: VerticalPressureResult
    # bins[iy][ix]; x varies fastest. Totals are independently integrated.
    bins: tuple[tuple[VerticalPressureResult, ...], ...]
    x_bin_edges: tuple[float, ...]
    y_bin_edges: tuple[float, ...]
    material_force_threshold_n: float


def _rectangle(rectangle):
    values = tuple(map(float, rectangle))
    if (len(values) != 4 or not all(map(math.isfinite, values))
            or values[1] < values[0] or values[3] < values[2]):
        raise ValueError("finite ordered (xmin,xmax,ymin,ymax) required")
    return values


def disk_rectangle_area_moments(rectangle, *, center=(0.6, 0.6),
                                radius_m=0.35, epsrel=2.e-13):
    """Area and world first moments of disk intersect rectangle.

    Requested absolute quadrature tolerance is 2e-14*r**2 for area and
    2e-14*r**3 for centred first moments, divided among the smooth strips.
    Thin intersections receive this absolute (not relative) uncertainty.
    Tangent/zero-width/outside rectangles have zero area and moments.
    """
    x0, x1, y0, y1 = _rectangle(rectangle)
    cx, cy = map(float, center)
    r = float(radius_m)
    if (not all(map(math.isfinite, (cx, cy, r, epsrel)))
            or r <= 0 or epsrel < 50*_EPS or epsrel > 1.e-4):
        raise ValueError("finite center, positive radius and controlled epsrel required")
    zero = AreaMoments(0., 0., 0., (0., 0., 0.))
    if x0 == x1 or y0 == y1:
        return zero
    left, right = max(-r, x0-cx), min(r, x1-cx)
    low, high = max(-r, y0-cy), min(r, y1-cy)
    if left >= right or low >= high:
        return zero
    nearest_x = max(left, min(0., right))
    nearest_y = max(low, min(0., high))
    if math.hypot(nearest_x, nearest_y) >= r:
        return zero
    if x0 <= cx-r and x1 >= cx+r and y0 <= cy-r and y1 >= cy+r:
        area = math.pi*r*r
        ex = 64*_EPS*area
        return AreaMoments(area, cx*area, cy*area,
                           (ex, ex*(abs(cx)+r), ex*(abs(cy)+r)))
    if max(math.hypot(x-cx, y-cy) for x in (x0,x1) for y in (y0,y1)) <= r:
        area = (x1-x0)*(y1-y0)
        mx, my = area*(x0+x1)/2, area*(y0+y1)/2
        ex = 64*_EPS*area
        return AreaMoments(area, mx, my,
                           (ex, ex*max(abs(x0),abs(x1)), ex*max(abs(y0),abs(y1))))
    breaks = {left, right}
    for y in (low, high):
        if abs(y) < r:
            crossing = math.sqrt(max(0., (r-y)*(r+y)))
            for x in (-crossing, crossing):
                if left < x < right:
                    breaks.add(x)
    breaks = sorted(breaks)
    values, errors = [[], [], []], [[], [], []]
    count = len(breaks)-1
    for a, b in zip(breaks[:-1], breaks[1:]):
        ta, tb = math.asin(a/r), math.asin(b/r)
        if ta == tb:
            continue
        def integrand(theta, component):
            u = r*math.sin(theta)
            height = r*max(0., math.cos(theta))
            upper, lower = min(high, height), max(low, -height)
            if upper <= lower:
                return 0.
            h = upper-lower
            moment = (h, u*h, .5*h*(upper+lower))[component]
            return moment*height
        for k in range(3):
            scale = r**(2 if k == 0 else 3)
            value, error = quad(integrand, ta, tb, args=(k,),
                                epsabs=2.e-14*scale/count, epsrel=epsrel, limit=50)
            values[k].append(value)
            errors[k].append(error)
    area, ux, uy = map(math.fsum, values)
    error = [math.fsum(e)+128*_EPS*r**(2 if k == 0 else 3)
             for k, e in enumerate(errors)]
    return AreaMoments(area, cx*area+ux, cy*area+uy,
                       (error[0], abs(cx)*error[0]+error[1],
                        abs(cy)*error[0]+error[2]))


def disk_rectangle_area(rectangle, **kwargs):
    """Convenience scalar area; use area_moments for uncertainty estimates."""
    return disk_rectangle_area_moments(rectangle, **kwargs).area_m2


def _edges(values, name):
    array = np.asarray(values, dtype=float)
    if (array.ndim != 1 or len(array) < 2 or not np.all(np.isfinite(array))
            or np.any(np.diff(array) <= 0)
            or array[0] != 0.1 or array[-1] != 1.1):
        raise ValueError(name+" must strictly partition fixed [0.1,1.1]")
    return tuple(map(float, array))


def _result(force, first_x, first_y, error, origin, threshold):
    ox, oy = origin
    centroid = ((first_x/force, first_y/force)
                if abs(force) > threshold else None)
    return VerticalPressureResult(force, first_x, first_y,
        (first_y-oy*force, ox*force-first_x, 0.), centroid, tuple(error),
        (error[2]+abs(oy)*error[0], error[1]+abs(ox)*error[0], 0.))


def _settings(x_bin_edges, y_bin_edges, moment_origin_xy, threshold):
    xbins, ybins = _edges(x_bin_edges, "x bins"), _edges(y_bin_edges, "y bins")
    origin = tuple(map(float, moment_origin_xy))
    if (len(origin) != 2 or not all(map(math.isfinite, origin))
            or not math.isfinite(threshold) or threshold < 0):
        raise ValueError("finite moment origin and nonnegative force threshold required")
    return xbins, ybins, origin


def uniform_disk_pressure_observables(pressure_pa, *, center=(0.6,0.6),
        radius_m=0.35, x_bin_edges=PRINCIPAL_BIN_EDGES,
        y_bin_edges=PRINCIPAL_BIN_EDGES, moment_origin_xy=(0.6,0.6),
        material_force_threshold_n=0.):
    """Exact uniform-pressure model: bin vertical force = p*disk-bin area.

    Geometry is evaluated numerically with returned uncertainty. Pressure may
    be zero for opening; negative pressure is rejected for this contact model.
    """
    p = float(pressure_pa)
    if not math.isfinite(p) or p < 0:
        raise ValueError("nonnegative finite contact pressure required")
    xbins, ybins, origin = _settings(x_bin_edges, y_bin_edges,
                                   moment_origin_xy, material_force_threshold_n)
    def integrate(rect):
        area = disk_rectangle_area_moments(rect, center=center, radius_m=radius_m)
        return _result(p*area.area_m2, p*area.first_x_m3, p*area.first_y_m3,
                       [p*e for e in area.estimated_absolute_error], origin,
                       material_force_threshold_n)
    bins = tuple(tuple(integrate((xa,xb,ya,yb)) for xa,xb in zip(xbins[:-1],xbins[1:]))
                 for ya,yb in zip(ybins[:-1],ybins[1:]))
    return BinnedPressureResult("uniform analytic disk pressure on reference area",
        integrate(SOURCE_RECTANGLE), bins, xbins, ybins, material_force_threshold_n)


def _basis_integrals(lo, hi, cell_lo, cell_hi):
    """Exact integrals of (N0,N1) and x*(N0,N1) on a clipped cell interval."""
    h = cell_hi-cell_lo
    a, b = (lo-cell_lo)/h, (hi-cell_lo)/h
    width, mean = b-a, .5*(a+b)
    base = np.array((h*width*(1-mean), h*width*mean))
    t1 = width*mean
    t2 = width*(a*a+a*b+b*b)/3
    first = cell_lo*base+h*h*np.array((t1-t2, t2))
    return base, first


def q1_reference_pressure_observables(x_nodes, y_nodes, nodal_pressure_pa, *,
        x_bin_edges=PRINCIPAL_BIN_EDGES, y_bin_edges=PRINCIPAL_BIN_EDGES,
        moment_origin_xy=(0.6,0.6), material_force_threshold_n=0.):
    """Integrate numerical Q1 pressure p over fixed REFERENCE area exactly.

    nodal_pressure_pa shape is (len(y_nodes),len(x_nodes)), indexed [iy,ix].
    Grids may be nonuniform but must span [0.1,1.1] in each direction.
    Signed nodal coefficients are allowed to expose negative-pressure defects.
    Polynomial integration is exact mathematically; returned error estimates
    account only for floating arithmetic, not geometry/current-area effects.
    """
    xs, ys = _edges(x_nodes, "x grid"), _edges(y_nodes, "y grid")
    p = np.asarray(nodal_pressure_pa, dtype=float)
    if p.shape != (len(ys),len(xs)) or not np.all(np.isfinite(p)):
        raise ValueError("finite pressure array shaped (ny,nx) required")
    xbins, ybins, origin = _settings(x_bin_edges, y_bin_edges,
                                   moment_origin_xy, material_force_threshold_n)
    def integrate(rect):
        x0,x1,y0,y1 = rect
        terms = [[], [], []]
        for j, (ya,yb) in enumerate(zip(ys[:-1],ys[1:])):
            lo_y, hi_y = max(y0,ya), min(y1,yb)
            if lo_y >= hi_y:
                continue
            by, my = _basis_integrals(lo_y,hi_y,ya,yb)
            for i, (xa,xb) in enumerate(zip(xs[:-1],xs[1:])):
                lo_x, hi_x = max(x0,xa), min(x1,xb)
                if lo_x >= hi_x:
                    continue
                bx, mx = _basis_integrals(lo_x,hi_x,xa,xb)
                coefficients = p[j:j+2,i:i+2]
                for k, weights in enumerate((np.outer(by,bx), np.outer(by,mx),
                                              np.outer(my,bx))):
                    terms[k].extend(map(float, (coefficients*weights).ravel()))
        totals = [math.fsum(t) for t in terms]
        errors = [256*_EPS*math.fsum(map(abs,t)) for t in terms]
        return _result(*totals, errors, origin, material_force_threshold_n)
    bins = tuple(tuple(integrate((xa,xb,ya,yb)) for xa,xb in zip(xbins[:-1],xbins[1:]))
                 for ya,yb in zip(ybins[:-1],ybins[1:]))
    return BinnedPressureResult("numerical Q1 reference-pressure integral over reference area",
        integrate(SOURCE_RECTANGLE), bins, xbins, ybins, material_force_threshold_n)
