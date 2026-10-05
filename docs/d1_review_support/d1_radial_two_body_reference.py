"""Exact radial two-scalar-membrane contact control, independent of ANYsolver.

Upward displacements satisfy Ds*laplacian(ws)=F-p and Dt*laplacian(wt)=p,
with gap delta+ws-wt>=0, p>=0 and p*gap=0. Write v=ws-wt. In contact
r<=a, v=-delta and p=F*Dt/(Ds+Dt). Outside, p=0. Integrating the radial
Poisson equations, imposing C1 matching at a and ws(R)=wt(R)=0 gives

  wt = F*(r²-a²)/(4*(Ds+Dt)) + F*a²*ln(a/R)/(2*(Ds+Dt)), r<=a;
       F*a²*ln(r/R)/(2*(Ds+Dt)), r>a.
  v  = -delta, r<=a;
       F*(r²-a²-2*a²*ln(r/a))/(4*Ds)-delta, r>a.
  delta = F*(R²-a²-2*a²*ln(R/a))/(4*Ds), ws=wt+v.

The outside gap derivative F*(r-a²/r)/(2*Ds)>=0, so the contact disk is
admissible. C1 matching means no spurious interface line force. Restricting
the disk solution to a source square and containing target rectangle, with
its exact Dirichlet traces and source-only uniform load, preserves the weak
solution: the entire pressure disk is strictly inside both domains. Force is
pi*a²*p; contact moments about the centre vanish by circular symmetry.

For an outside-contact straight boundary segment of length h and minimum
radius rmin>a, linear nodal trace interpolation has sup error <=h²*M/8.
For a radial field Hessian eigenvalues are w'' and w'/r. Put
C=F*a²/(2*(Ds+Dt)), K=F/(2*Ds), B=F*a²*Dt/(2*Ds*(Ds+Dt)). Outside,
wt=C*ln(r/R), ws=K*r²/2-B*ln(r)+constant, hence
Mtarget=C/rmin² and Msource=K+B/rmin². Exact rational arithmetic encloses
the supplied binary-float geometry/coefficient bound; the final float rounds
outward. This bound is geometric interpolation error, not an empirical fit.

Continuum trace-error propagation: the admissible pairs form a lattice under
componentwise min/max since ws-wt>=-delta. The Dirichlet energies are local
and strictly convex. The standard min/max competitor argument therefore
gives componentwise comparison for ordered boundary data, with the same F
and delta. Common constant shifts of both exact fields preserve equations
and gap. If both boundary errors are <=epsilon, shifted exact fields +/-
epsilon bracket the perturbed continuum solution. Each displacement sup
error is <=epsilon. Nonnegative weighted displacement averages inherit that
absolute bound; an unnormalized load-work integral inherits F*area*epsilon.

That comparison does NOT certify contact force/moment error, finite-element
discretization, pressure-space stability, or the production weak mortar gap.
No force-error factor follows from a displacement sup bound alone. Scope is
the frozen guided scalar operators Ds and Dt=phi²*H, not raw H, free director
motion or ordinary bending. The owner must freeze the actual coefficients.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np


@dataclass(frozen=True)
class EdgeTraceErrorBound:
    body: str
    length_m: float
    minimum_radius_m: float
    hessian_upper_per_m: float
    max_error_m: float


@dataclass(frozen=True)
class RadialTwoBodyReference:
    ds: float
    dt: float
    load_pa: float = 0.08
    radius_m: float = 1.0
    contact_radius_m: float = 0.35

    def __post_init__(self):
        values = (self.ds, self.dt, self.load_pa, self.radius_m, self.contact_radius_m)
        if (not all(math.isfinite(value) and value > 0.0 for value in values)
                or not math.isfinite(self.ds+self.dt)
                or self.contact_radius_m >= self.radius_m):
            raise ValueError("positive finite scalar coefficients and 0<a<R are required")

    @property
    def gap_m(self) -> float:
        a, radius = self.contact_radius_m, self.radius_m
        return self.load_pa/(4*self.ds)*(radius**2-a**2-2*a**2*math.log(radius/a))

    @property
    def pressure_pa(self) -> float:
        return self.load_pa*self.dt/(self.ds+self.dt)

    @property
    def force_n(self) -> float:
        return math.pi*self.contact_radius_m**2*self.pressure_pa

    @property
    def contact_moments_nm(self) -> tuple[float, float, float]:
        """Three contact-force moments about the reference centre."""
        return (0.0, 0.0, 0.0)

    def fields_xy(self, points, center=(0.6, 0.6)) -> dict[str, np.ndarray]:
        points = np.asarray(points, dtype=float)
        center = np.asarray(center, dtype=float)
        if (points.shape[-1:] != (2,) or center.shape != (2,)
                or not np.all(np.isfinite(points)) or not np.all(np.isfinite(center))):
            raise ValueError("finite XY points and centre are required")
        r = np.linalg.norm(points-center, axis=-1)
        if np.any(r > self.radius_m):
            raise ValueError("reference points must lie in the radius-R disk")
        a, radius, total = self.contact_radius_m, self.radius_m, self.ds+self.dt
        inside = r <= a
        safe_r = np.maximum(r, a)
        c = self.load_pa*a*a/(2*total)
        target = np.where(inside,
            self.load_pa/(4*total)*(r*r-a*a)+c*math.log(a/radius),
            c*np.log(safe_r/radius))
        q = (safe_r-a)/a
        # q²+2q-2log(1+q) starts at order q². Its Taylor evaluation near
        # zero avoids cancellation; the first omitted term is 2*q^9/9,
        # below binary64 rounding at the fixed evaluation switch q=1e-3.
        series = q*q*(2+q*(-2/3+q*(1/2+q*(-2/5+q*(1/3+q*(-2/7+q/4))))))
        radial_gap = np.where(q < 1.e-3, series, q*(q+2)-2*np.log1p(q))
        gap = np.where(inside, 0.0,
            self.load_pa*a*a/(4*self.ds)*radial_gap)
        return {"source_w": target+gap-self.gap_m, "target_w": target,
                "gap": gap, "pressure": np.where(inside, self.pressure_pa, 0.0)}

    def edge_trace_error_bound(self, first, last, body: str,
                               center=(0.6, 0.6)) -> EdgeTraceErrorBound:
        """Bound the whole segment; no samples establish this inequality."""
        if body not in ("source", "target"):
            raise ValueError("body must be source or target")

        def exact_point(point):
            point = tuple(point)
            if len(point) != 2 or not all(math.isfinite(value) for value in point):
                raise ValueError("finite XY edge coordinates are required")
            return tuple(Fraction(float(value)) for value in point)

        x0, x1, origin = map(exact_point, (first, last, center))
        u = tuple(x-y for x, y in zip(x0, origin))
        edge = tuple(y-x for x, y in zip(x0, x1))
        length_squared = sum(value*value for value in edge)
        if length_squared == 0:
            raise ValueError("trace segment must have positive length")
        station = max(Fraction(0), min(Fraction(1),
            -sum(x*y for x, y in zip(u, edge))/length_squared))
        closest = tuple(x+station*y for x, y in zip(u, edge))
        minimum_squared = sum(value*value for value in closest)
        maximum_squared = max(sum((x-y)**2 for x, y in zip(point, origin))
                              for point in (x0, x1))
        f, ds, dt, a, radius = (Fraction(float(value)) for value in
            (self.load_pa, self.ds, self.dt, self.contact_radius_m, self.radius_m))
        if minimum_squared <= a*a or maximum_squared >= radius*radius:
            raise ValueError("trace edge must be strictly outside contact and inside R")
        if body == "target":
            hessian = f*a*a/(2*(ds+dt)*minimum_squared)
        else:
            hessian = f/(2*ds)+f*a*a*dt/(2*ds*(ds+dt)*minimum_squared)
        bound = length_squared*hessian/8
        return EdgeTraceErrorBound(
            body, math.sqrt(float(length_squared)),
            math.nextafter(math.sqrt(float(minimum_squared)), -math.inf),
            math.nextafter(float(hessian), math.inf),
            math.nextafter(float(bound), math.inf))

    def rectangle_trace_error_bound(self, x_bounds, y_bounds, cells_x: int,
                                    cells_y: int, body: str,
                                    center=(0.6, 0.6)) -> dict[str, float | int | str]:
        """Largest bound for the actual represented uniform boundary segments."""
        if (type(cells_x) is not int or type(cells_y) is not int
                or cells_x <= 0 or cells_y <= 0):
            raise ValueError("positive integer boundary cell counts are required")
        if (len(x_bounds) != 2 or len(y_bounds) != 2
                or x_bounds[0] >= x_bounds[1] or y_bounds[0] >= y_bounds[1]):
            raise ValueError("ordered rectangle bounds are required")
        x = np.linspace(*x_bounds, cells_x+1)
        y = np.linspace(*y_bounds, cells_y+1)
        edges = [((x[i], yy), (x[i+1], yy))
                 for yy in y_bounds for i in range(cells_x)]
        edges += [((xx, y[i]), (xx, y[i+1]))
                  for xx in x_bounds for i in range(cells_y)]
        bounds = [self.edge_trace_error_bound(first, last, body, center)
                  for first, last in edges]
        return {"body": body, "edge_count": len(bounds),
                "max_error_m": max(item.max_error_m for item in bounds),
                "max_edge_length_m": max(item.length_m for item in bounds),
                "minimum_boundary_radius_m": min(item.minimum_radius_m for item in bounds),
                "max_hessian_upper_per_m": max(item.hessian_upper_per_m for item in bounds)}


def continuum_displacement_trace_error_bound(source_bound, target_bound) -> float:
    """Derived common-shift bracket for the exact pointwise continuum problem.

    This bounds both displacements in sup norm. It supplies no contact-force
    bound and no production mortar/finite-element discretization allowance.
    """
    if source_bound["body"] != "source" or target_bound["body"] != "target":
        raise ValueError("complete source and target boundary bounds are required")
    errors = (source_bound["max_error_m"], target_bound["max_error_m"])
    if not all(math.isfinite(value) and value >= 0 for value in errors):
        raise ValueError("finite nonnegative complete boundary errors are required")
    return max(errors)
