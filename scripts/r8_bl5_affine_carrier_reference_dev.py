"""Independent continuous Timoshenko reference with finite affine carriers.

Development only: straight uncoupled normal-spin bending, not Saint-Venant
torsion or qualification. Both endpoint translations are fixed; root moment
is zero (root spin free), and tip moment is prescribed. On each actual support
p=a+b*xi, xi=2*(x-center)/width, and BOTH integral(u) and integral(xi*u)
vanish. Physical signs are V'=-p, M'=-V, phi'=M/EI, u'=phi+V/kGA.

The normalized state (u,phi,V,M) is propagated by exact polynomial integration.
Two carrier coefficients per support plus root spin/shear form a 2*N+2 system.
No native mechanical operator or attachment implementation is used.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
from numbers import Real

import numpy as np


def _real(value, label):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError("finite real "+label+" required")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("finite real "+label+" required")
    return value


def _owned(value):
    array = np.asarray(value, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError("reference array is not representable")
    return np.frombuffer(array.tobytes(), dtype=float).reshape(array.shape)


def _representable(value):
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError("physical section/length scales are not representable") from exc
    if not math.isfinite(result) or (value and result == 0.):
        raise ValueError("physical section/length scales are not representable")
    return result


def _field_scales(length, bending, moment):
    length, bending, moment = map(Fraction, (length, bending, moment))
    return np.array(tuple(_representable(v) for v in
        (moment*length**2/bending, moment*length/bending, moment/length, moment)))


def _polynomials(state, c, d, rho):
    """Ascending local powers, with p=c+d*s in normalized t=x/L."""
    u, phi, v, m = state
    zero = np.zeros_like(u)
    return np.array((
        (u, phi+rho*v, (m-rho*c)/2, (-v-rho*d)/6, c/24, d/120),
        (phi, m, -v/2, c/6, d/24, zero),
        (v, -c, -d/2, zero, zero, zero),
        (m, -v, c/2, d/6, zero, zero)))


@dataclass(frozen=True)
class AffineCarrierReference:
    length: float
    bending: float
    shear: float
    moment: float
    boundaries: np.ndarray
    starts: np.ndarray
    densities: np.ndarray
    coefficients: np.ndarray
    rho: float
    scaled_condition: float
    backward_error: float

    def __post_init__(self):
        for name in ("boundaries", "starts", "densities", "coefficients"):
            object.__setattr__(self, name, _owned(getattr(self, name)))

    def _coordinates(self, x):
        original = np.asarray(x, dtype=object)
        if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, Real) for v in original.flat):
            raise ValueError("finite in-member coordinate required")
        x = np.asarray(x, dtype=float)
        if not np.isfinite(x).all() or np.any(x < 0.) or np.any(x > self.length):
            raise ValueError("finite in-member coordinate required")
        t = x/self.length
        i = np.clip(np.searchsorted(self.boundaries, t, side="right")-1,
                    0, len(self.densities)-1)
        return i, t-self.boundaries[i]

    def fields(self, x):
        """Physical u, phi, V, M; continuous at support boundaries."""
        i, s = self._coordinates(x)
        powers = np.stack([s**k for k in range(6)], axis=-1)
        normalized = np.sum(self.coefficients[i]*powers[..., None, :], axis=-1)
        scales = _field_scales(self.length, self.bending, self.moment)
        result = np.moveaxis(normalized*scales, -1, 0)
        if not np.isfinite(result).all():
            raise ValueError("physical reference fields are not representable")
        return result

    def force_density(self, x):
        """Physical beam-side p; right-sided at interior support boundaries."""
        i, s = self._coordinates(x)
        h = np.diff(self.boundaries)[i]
        density_scale = _representable(Fraction(self.moment)/Fraction(self.length)**2)
        result = (self.densities[i, 0]+self.densities[i, 1]*(2*s/h-1))*density_scale
        if not np.isfinite(result).all():
            raise ValueError("physical force density is not representable")
        return result

    def transfer_moments(self, highest=3):
        """Analytic integral(x**k*p dx), k=0..3, about the beam root."""
        if type(highest) is not int or not 0 <= highest <= 3:
            raise ValueError("transfer moment order must be an integer from zero through three")
        result = []
        for k in range(highest+1):
            total = Fraction(0)
            for left, right, (a, b) in zip(self.boundaries[:-1], self.boundaries[1:], self.densities):
                left, right, a, b = map(lambda v: Fraction(float(v)), (left, right, a, b))
                h = right-left
                c, d = a-b, 2*b/h
                total += sum(math.comb(k, j)*left**(k-j)*(c*h**(j+1)/(j+1)+d*h**(j+2)/(j+2))
                             for j in range(k+1))
            physical = total*Fraction(self.moment)*Fraction(self.length)**(k-1)
            try:
                value = float(physical)
            except OverflowError as exc:
                raise ValueError("transfer moment is not representable") from exc
            if not math.isfinite(value) or (physical and value == 0.):
                raise ValueError("transfer moment is not representable")
            result.append(value)
        return np.array(result)

    def controls(self):
        """P0-compatible work controls: energy denotes twice strain energy."""
        # Five-point Gauss integrates degree-six M² and p*u exactly.
        xi, wi = np.polynomial.legendre.leggauss(5)
        a, b = self.boundaries[:-1], self.boundaries[1:]
        h = b-a
        x = self.length*(a[:, None]+h[:, None]*(xi+1)/2)
        u, phi, v, m = self.fields(x)
        weights = self.length*h[:, None]*wi/2
        means = np.sum(weights*u, axis=1)
        first = np.sum(weights*xi*u, axis=1)
        energy = float(np.sum(weights*(v*v/self.shear+m*m/self.bending)))
        end = self.fields(np.array((0., self.length)))
        work = float(self.moment*end[1, 1])
        line_work = float(np.sum(weights*self.force_density(x)*u))
        displacement_scale = abs(_field_scales(self.length, self.bending, self.moment)[0])
        moment_scale = abs(self.moment)
        transfer = self.transfer_moments(1)
        root, tip = -float(end[2, 0]), float(end[2, 1])
        denominator = abs(work)
        return dict(
            scaled_support_mean=float(np.max(abs(means)/(self.length*h*displacement_scale))),
            scaled_support_affine_mean=float(np.max(abs(first)/(self.length*h*displacement_scale))),
            scaled_endpoint_displacement=float(np.max(abs(end[0]))/displacement_scale),
            scaled_endpoint_moment=float(max(abs(end[3, 0]), abs(end[3, 1]-self.moment))/moment_scale),
            energy_work=abs(energy-work)/denominator if denominator else float("inf"),
            line_work=abs(line_work)/denominator if denominator else float("inf"),
            force_balance=abs(root+tip+transfer[0])*self.length/moment_scale,
            moment_balance=abs(tip*self.length+transfer[1]+self.moment)/moment_scale,
            energy=energy, work=work, endpoint_reactions=[root, tip],
            scaled_condition=self.scaled_condition, backward_error=self.backward_error)


def solve_affine_carrier(length, bending, shear, moment, support_endpoints):
    """Independent 2*N+2 propagation solve on the supplied physical partition.

    With t=x/L, u=Mtip*L²/EI*v, phi=Mtip*L/EI*theta,
    V=Mtip/L*s, p=Mtip/L²*w, rho=EI/(kGA*L²). Unknowns are
    theta(0), s(0), and each support's (a,b). Initial v=m=0;
    final v=0,m=1 and both support displacement moments determine them.
    """
    length, bending, shear, moment = tuple(_real(v, n) for v, n in
        zip((length, bending, shear, moment), ("length", "bending", "shear", "moment")))
    if min(length, bending, shear) <= 0. or moment == 0.:
        raise ValueError("positive section/length and nonzero moment required")
    raw = np.asarray(support_endpoints, dtype=object)
    if raw.ndim != 1 or len(raw) < 2:
        raise ValueError("complete strictly increasing physical support partition required")
    endpoints = np.array([_real(v, "support endpoint") for v in raw])
    if endpoints[0] != 0. or endpoints[-1] != length or np.any(np.diff(endpoints) <= 0.):
        raise ValueError("complete strictly increasing physical support partition required")
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        t = endpoints/length
    rho = _representable(Fraction(bending)/Fraction(shear)/Fraction(length)**2)
    scales = _field_scales(length, bending, moment)
    _representable(Fraction(moment)/Fraction(length)**2)
    if (not math.isfinite(rho) or rho <= 0. or not np.isfinite(scales).all() or
            np.any(scales == 0.) or np.any(np.diff(t) <= 0.)):
        raise ValueError("physical section/length scales are not representable")
    n, count = len(t)-1, 2*(len(t)-1)+2
    state = np.zeros((4, count))
    state[1, 0], state[2, 1] = 1., 1.
    rows, starts = [], []
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        for i, h in enumerate(np.diff(t)):
            starts.append(state.copy())
            a, b = np.zeros(count), np.zeros(count)
            a[2+2*i], b[3+2*i] = 1., 1.
            polys = _polynomials(state, a-b, 2*b/h, rho)
            powers = np.array([h**k for k in range(6)])
            rows.append(np.sum(polys[0]*(powers/(np.arange(6)+1))[:, None], axis=0))
            rows.append(np.sum(polys[0]*(powers*np.arange(6)/((np.arange(6)+1)*(np.arange(6)+2)))[:, None], axis=0))
            state = np.sum(polys*powers[None, :, None], axis=1)
    matrix = np.array(rows+[state[0], state[3]])
    rhs = np.zeros(count); rhs[-1] = 1.
    if not np.isfinite(matrix).all():
        raise ValueError("reference propagation is not representable")
    row_scale = np.max(abs(matrix), axis=1)
    if np.any(row_scale == 0.):
        raise ValueError("reference has an unsupported equation")
    scaled = matrix/row_scale[:, None]
    column_scale = np.max(abs(scaled), axis=0)
    if np.any(column_scale == 0.):
        raise ValueError("reference has an unsupported variable")
    scaled /= column_scale[None, :]
    unknowns = np.linalg.solve(scaled, rhs/row_scale)/column_scale
    backward = float(np.max(abs(matrix@unknowns-rhs))/
                     (np.linalg.norm(matrix, ord=np.inf)*np.max(abs(unknowns))+1.))
    start_values = np.array(starts)@unknowns
    densities = unknowns[2:].reshape(n, 2)
    coefficients = np.array([_polynomials(state, a-b, 2*b/h, rho)
        for state, (a, b), h in zip(start_values, densities, np.diff(t))])
    result = AffineCarrierReference(length, bending, shear, moment, t, start_values,
        densities, coefficients, rho, float(np.linalg.cond(scaled)), backward)
    checks = result.controls()
    names = ("scaled_support_mean", "scaled_support_affine_mean", "scaled_endpoint_displacement",
             "scaled_endpoint_moment", "energy_work", "line_work", "force_balance", "moment_balance", "backward_error")
    if any(not math.isfinite(checks[name]) or checks[name] > 1e-8 for name in names):
        raise ValueError("reference physical/numerical controls failed: "+str(checks))
    if checks["work"] <= 0. or checks["energy"] <= 0. or not math.isfinite(result.scaled_condition):
        raise ValueError("reference work/energy and condition must be finite and positive")
    return result
