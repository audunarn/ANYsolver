"""Outward interval enclosure for the Q1H K/H quotient campaign.

The implementation encloses the frozen 35-field stationary system rather than
inverting an interval matrix directly.  A midpoint inverse plus a Banach
perturbation bound encloses the condensed core.  Positivity is certified by a
fixed numeric congruence whose interval Gershgorin margin is strictly positive.
The congruence matrix consists only of binary64 constants and is therefore an
exact rational matrix for purposes of the outward enclosure.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Iterable, Mapping, Sequence

import numpy as np


ALPHA_STAR = 1.0e-6
EPSILON = np.finfo(float).eps


def _down(value: np.ndarray | float) -> np.ndarray:
    return np.nextafter(np.asarray(value, dtype=float), -np.inf)


def _up(value: np.ndarray | float) -> np.ndarray:
    return np.nextafter(np.asarray(value, dtype=float), np.inf)


@dataclass(frozen=True)
class IA:
    lo: np.ndarray
    hi: np.ndarray
    centre: np.ndarray | None = None
    coefficients: np.ndarray | None = None
    remainder: np.ndarray | None = None

    def __post_init__(self) -> None:
        lo = np.asarray(self.lo, dtype=float)
        hi = np.asarray(self.hi, dtype=float)
        if np.any(~np.isfinite(lo)) or np.any(~np.isfinite(hi)) or np.any(lo > hi):
            raise ValueError("invalid finite interval")
        object.__setattr__(self, "lo", lo)
        object.__setattr__(self, "hi", hi)
        if self.centre is not None:
            centre = np.asarray(self.centre, dtype=float)
            coefficients = np.asarray(self.coefficients, dtype=float)
            remainder = np.asarray(self.remainder, dtype=float)
            if coefficients.shape != (4,) + centre.shape or remainder.shape != centre.shape:
                raise ValueError("invalid affine interval representation")
            object.__setattr__(self, "centre", centre)
            object.__setattr__(self, "coefficients", coefficients)
            object.__setattr__(self, "remainder", remainder)

    @classmethod
    def affine(cls, centre: object, coefficients: object, remainder: object) -> "IA":
        centre_array = np.asarray(centre, dtype=float)
        coefficient_array = np.asarray(coefficients, dtype=float)
        remainder_array = np.maximum(np.asarray(remainder, dtype=float), 0.0)
        radius = np.sum(np.abs(coefficient_array), axis=0) + remainder_array
        rounding = 16.0 * EPSILON * np.maximum(np.abs(centre_array) + radius, 1.0)
        remainder_array = _up(remainder_array + rounding)
        radius = np.sum(np.abs(coefficient_array), axis=0) + remainder_array
        return cls(
            _down(centre_array - radius),
            _up(centre_array + radius),
            centre_array,
            coefficient_array,
            remainder_array,
        )

    @classmethod
    def point(cls, value: object) -> "IA":
        array = np.asarray(value, dtype=float)
        return cls.affine(array, np.zeros((4,) + array.shape, dtype=float), np.zeros_like(array))

    @property
    def is_affine(self) -> bool:
        return self.centre is not None

    @property
    def mid(self) -> np.ndarray:
        return self.centre if self.centre is not None else self.lo + 0.5 * (self.hi - self.lo)

    @property
    def rad(self) -> np.ndarray:
        if self.centre is not None:
            assert self.coefficients is not None and self.remainder is not None
            return np.sum(np.abs(self.coefficients), axis=0) + self.remainder
        return 0.5 * (self.hi - self.lo)

    @property
    def T(self) -> "IA":
        if self.is_affine:
            assert self.coefficients is not None and self.remainder is not None
            return IA.affine(
                self.centre.T,
                np.transpose(self.coefficients, (0, 2, 1)),
                self.remainder.T,
            )
        return IA(self.lo.T, self.hi.T)

    def __getitem__(self, key: object) -> "IA":
        if self.is_affine:
            assert self.coefficients is not None and self.remainder is not None
            return IA.affine(
                self.centre[key],
                self.coefficients[(slice(None),) + (key if isinstance(key, tuple) else (key,))],
                self.remainder[key],
            )
        return IA(self.lo[key], self.hi[key])

    def _broadcast_affine(self, shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        assert self.centre is not None and self.coefficients is not None and self.remainder is not None
        pad = len(shape) - self.centre.ndim
        centre = np.broadcast_to(self.centre.reshape((1,) * pad + self.centre.shape), shape)
        coefficients = np.broadcast_to(
            self.coefficients.reshape((4,) + (1,) * pad + self.centre.shape),
            (4,) + shape,
        )
        remainder = np.broadcast_to(self.remainder.reshape((1,) * pad + self.centre.shape), shape)
        return centre, coefficients, remainder

    def __neg__(self) -> "IA":
        if self.is_affine:
            assert self.coefficients is not None and self.remainder is not None
            return IA.affine(-self.centre, -self.coefficients, self.remainder)
        return IA(_down(-self.hi), _up(-self.lo))

    def __add__(self, other: object) -> "IA":
        right = as_interval(other)
        if self.is_affine and right.is_affine:
            shape = np.broadcast_shapes(self.centre.shape, right.centre.shape)
            lc, la, lr = self._broadcast_affine(shape)
            rc, ra, rr = right._broadcast_affine(shape)
            return IA.affine(lc + rc, la + ra, lr + rr)
        return IA(_down(self.lo + right.lo), _up(self.hi + right.hi))

    def __radd__(self, other: object) -> "IA":
        return self + other

    def __sub__(self, other: object) -> "IA":
        right = as_interval(other)
        if self.is_affine and right.is_affine:
            shape = np.broadcast_shapes(self.centre.shape, right.centre.shape)
            lc, la, lr = self._broadcast_affine(shape)
            rc, ra, rr = right._broadcast_affine(shape)
            return IA.affine(lc - rc, la - ra, lr + rr)
        return IA(_down(self.lo - right.hi), _up(self.hi - right.lo))

    def __rsub__(self, other: object) -> "IA":
        return as_interval(other) - self

    def __mul__(self, other: object) -> "IA":
        right = as_interval(other)
        if self.is_affine and right.is_affine:
            shape = np.broadcast_shapes(self.centre.shape, right.centre.shape)
            lc, la, lr = self._broadcast_affine(shape)
            rc, ra, rr = right._broadcast_affine(shape)
            left_linear = np.sum(np.abs(la), axis=0)
            right_linear = np.sum(np.abs(ra), axis=0)
            coefficients = lc[None, ...] * ra + rc[None, ...] * la
            remainder = (
                np.abs(lc) * rr
                + np.abs(rc) * lr
                + left_linear * right_linear
                + left_linear * rr
                + right_linear * lr
                + lr * rr
            )
            return IA.affine(lc * rc, coefficients, remainder)
        products = np.stack(
            (
                self.lo * right.lo,
                self.lo * right.hi,
                self.hi * right.lo,
                self.hi * right.hi,
            )
        )
        return IA(_down(np.min(products, axis=0)), _up(np.max(products, axis=0)))

    def __rmul__(self, other: object) -> "IA":
        return self * other

    def reciprocal(self) -> "IA":
        if np.any((self.lo <= 0.0) & (self.hi >= 0.0)):
            raise ZeroDivisionError("interval contains zero")
        if self.is_affine:
            assert self.coefficients is not None and self.remainder is not None
            centre = 1.0 / self.centre
            coefficients = -self.coefficients / (self.centre[None, ...] ** 2)
            linear_radius = np.sum(np.abs(coefficients), axis=0)
            actual_lo = np.minimum(1.0 / self.lo, 1.0 / self.hi)
            actual_hi = np.maximum(1.0 / self.lo, 1.0 / self.hi)
            remainder = np.maximum.reduce(
                (
                    np.zeros_like(centre),
                    actual_hi - (centre + linear_radius),
                    (centre - linear_radius) - actual_lo,
                )
            )
            return IA.affine(centre, coefficients, remainder)
        values = np.stack((1.0 / self.lo, 1.0 / self.hi))
        return IA(_down(np.min(values, axis=0)), _up(np.max(values, axis=0)))

    def __truediv__(self, other: object) -> "IA":
        return self * as_interval(other).reciprocal()

    def __rtruediv__(self, other: object) -> "IA":
        return as_interval(other) / self

    def __pow__(self, exponent: int) -> "IA":
        if not isinstance(exponent, int):
            return NotImplemented
        if exponent == 0:
            return IA.point(np.ones_like(self.mid))
        if exponent < 0:
            return (self.reciprocal()) ** (-exponent)
        result = IA.point(np.ones_like(self.mid))
        factor = self
        power = exponent
        while power:
            if power & 1:
                result = result * factor
            power >>= 1
            if power:
                factor = factor * factor
        return result

    def __matmul__(self, other: object) -> "IA":
        right = as_interval(other)
        if self.is_affine and right.is_affine:
            assert self.coefficients is not None and self.remainder is not None
            assert right.coefficients is not None and right.remainder is not None
            centre = self.centre @ right.centre
            coefficients = np.stack(
                tuple(
                    self.coefficients[index] @ right.centre
                    + self.centre @ right.coefficients[index]
                    for index in range(4)
                )
            )
            left_linear = np.sum(np.abs(self.coefficients), axis=0)
            right_linear = np.sum(np.abs(right.coefficients), axis=0)
            remainder = (
                np.abs(self.centre) @ right.remainder
                + self.remainder @ np.abs(right.centre)
                + left_linear @ right_linear
                + left_linear @ right.remainder
                + self.remainder @ right_linear
                + self.remainder @ right.remainder
            )
            inner = self.centre.shape[-1]
            magnitude = (np.abs(self.centre) + self.rad) @ (np.abs(right.centre) + right.rad)
            remainder += 16.0 * EPSILON * max(inner, 1) * np.maximum(magnitude, 1.0)
            return IA.affine(centre, coefficients, remainder)
        left_mid, left_rad = self.mid, self.rad
        right_mid, right_rad = right.mid, right.rad
        centre = left_mid @ right_mid
        radius = (
            np.abs(left_mid) @ right_rad
            + left_rad @ np.abs(right_mid)
            + left_rad @ right_rad
        )
        inner = left_mid.shape[-1]
        magnitude = (np.abs(left_mid) + left_rad) @ (np.abs(right_mid) + right_rad)
        rounding = 16.0 * EPSILON * max(inner, 1) * np.maximum(magnitude, 1.0)
        return IA(_down(centre - radius - rounding), _up(centre + radius + rounding))


def as_interval(value: object) -> IA:
    return value if isinstance(value, IA) else IA.point(value)


def interval(
    lower: float | Fraction,
    upper: float | Fraction | None = None,
    *,
    variable: int | None = None,
) -> IA:
    upper = lower if upper is None else upper
    lo = float(lower)
    hi = float(upper)
    if Fraction.from_float(lo) > Fraction(lower):
        lo = math.nextafter(lo, -math.inf)
    if Fraction.from_float(hi) < Fraction(upper):
        hi = math.nextafter(hi, math.inf)
    centre = lo + 0.5 * (hi - lo)
    radius = 0.5 * (hi - lo)
    coefficients = np.zeros(4, dtype=float)
    remainder = 0.0
    if variable is None:
        remainder = radius
    else:
        coefficients[variable] = radius
    return IA.affine(np.asarray(centre), coefficients, np.asarray(remainder))


def zeros(shape: tuple[int, ...]) -> IA:
    return IA.point(np.zeros(shape, dtype=float))


def stack(values: Iterable[IA], axis: int = 0) -> IA:
    rows = tuple(values)
    if all(row.is_affine for row in rows):
        return IA.affine(
            np.stack([row.centre for row in rows], axis=axis),
            np.stack([row.coefficients for row in rows], axis=axis + 1),
            np.stack([row.remainder for row in rows], axis=axis),
        )
    return IA(np.stack([row.lo for row in rows], axis=axis), np.stack([row.hi for row in rows], axis=axis))


def vstack(values: Iterable[IA]) -> IA:
    rows = tuple(values)
    if all(row.is_affine for row in rows):
        return IA.affine(
            np.vstack([row.centre for row in rows]),
            np.concatenate([row.coefficients for row in rows], axis=1),
            np.vstack([row.remainder for row in rows]),
        )
    return IA(np.vstack([row.lo for row in rows]), np.vstack([row.hi for row in rows]))


def outer(left: IA, right: IA) -> IA:
    return left[:, None] @ right[None, :]


def assign(target: IA, key: object, value: object) -> None:
    source = as_interval(value)
    target.lo[key] = source.lo
    target.hi[key] = source.hi
    if target.is_affine and source.is_affine:
        target.centre[key] = source.centre
        coefficient_key = (slice(None),) + (key if isinstance(key, tuple) else (key,))
        target.coefficients[coefficient_key] = source.coefficients
        target.remainder[key] = source.remainder


def add_block(target: IA, block: IA, row: int, column: int) -> None:
    key = (slice(row, row + block.lo.shape[0]), slice(column, column + block.lo.shape[1]))
    current = target[key] + block
    assign(target, key, current)


def _sqrt_third_interval() -> IA:
    scale = 1 << 60
    numerator = math.isqrt((scale * scale) // 3)
    while (numerator + 1) * (numerator + 1) * 3 <= scale * scale:
        numerator += 1
    while numerator * numerator * 3 > scale * scale:
        numerator -= 1
    return interval(Fraction(numerator, scale), Fraction(numerator + 1, scale))


G = _sqrt_third_interval()
GAUSS = ((-G, -G), (G, -G), (G, G), (-G, G))


def _shape(r: IA, s: IA) -> tuple[IA, IA, IA, IA]:
    one = IA.point(1.0)
    four = 4.0
    n = stack(
        (
            (one - r) * (one - s) / four,
            (one + r) * (one - s) / four,
            (one + r) * (one + s) / four,
            (one - r) * (one + s) / four,
        )
    )
    nr = stack((-(one - s) / four, (one - s) / four, (one + s) / four, -(one + s) / four))
    ns = stack((-(one - r) / four, -(one + r) / four, (one + r) / four, (one - r) / four))
    nrs = IA.point(np.asarray((1.0, -1.0, 1.0, -1.0)) / 4.0)
    return n, nr, ns, nrs


def _jacobian(
    p: IA,
    q: IA,
    u: IA,
    v: IA,
    r: IA,
    s: IA,
    *,
    variation: tuple[IA, IA] | None = None,
) -> tuple[IA, IA, IA, IA, IA]:
    xr = 1.0 + u * s
    xs = p + u * r
    yr = v * s
    ys = q + v * r
    if variation is None:
        determinant = xr * ys - xs * yr
    else:
        a, b = variation
        determinant = q * (1.0 + a * s + b * r)
    return xr, xs, yr, ys, determinant


def _physical_gradients(
    p: IA,
    q: IA,
    u: IA,
    v: IA,
    r: IA,
    s: IA,
    nr: IA,
    ns: IA,
    *,
    variation: tuple[IA, IA] | None = None,
) -> tuple[IA, IA, IA]:
    xr, xs, yr, ys, determinant = _jacobian(
        p, q, u, v, r, s, variation=variation
    )
    nx = (ys * nr - yr * ns) / determinant
    ny = (-xs * nr + xr * ns) / determinant
    return nx, ny, determinant


def _natural_shear(
    p: IA, q: IA, u: IA, v: IA, r: IA, s: IA, direction: int
) -> IA:
    n, nr, ns, _nrs = _shape(r, s)
    derivative = nr if direction == 0 else ns
    # Gauge coefficients give x=r+p*s+u*r*s, y=q*s+v*r*s.
    x_nodes = stack((-1.0 - p + u, 1.0 - p - u, 1.0 + p + u, -1.0 + p - u))
    y_nodes = stack((-q + v, -q - v, q + v, q - v))
    x_derivative = (x_nodes[None, :] @ derivative[:, None])[0, 0]
    y_derivative = (y_nodes[None, :] @ derivative[:, None])[0, 0]
    result = zeros((20,))
    for node in range(4):
        base = 5 * node
        assign(result, base + 2, derivative[node])
        assign(result, base + 3, -y_derivative * n[node])
        assign(result, base + 4, x_derivative * n[node])
    return result


def _compatible(
    p: IA,
    q: IA,
    u: IA,
    v: IA,
    r: IA,
    s: IA,
    *,
    variation: tuple[IA, IA] | None = None,
) -> tuple[IA, IA]:
    _n, nr, ns, _nrs = _shape(r, s)
    nx, ny, determinant = _physical_gradients(
        p, q, u, v, r, s, nr, ns, variation=variation
    )
    result = zeros((8, 20))
    for node in range(4):
        base = 5 * node
        assign(result, (0, base), nx[node])
        assign(result, (1, base + 1), ny[node])
        assign(result, (2, base), ny[node])
        assign(result, (2, base + 1), nx[node])
        assign(result, (3, base + 4), nx[node])
        assign(result, (4, base + 3), -ny[node])
        assign(result, (5, base + 4), ny[node])
        assign(result, (5, base + 3), -nx[node])
    zero, one = IA.point(0.0), IA.point(1.0)
    gr_a = _natural_shear(p, q, u, v, zero, -one, 0)
    gr_c = _natural_shear(p, q, u, v, zero, one, 0)
    gs_b = _natural_shear(p, q, u, v, one, zero, 1)
    gs_d = _natural_shear(p, q, u, v, -one, zero, 1)
    gr = 0.5 * (one - s) * gr_a + 0.5 * (one + s) * gr_c
    gs = 0.5 * (one + r) * gs_b + 0.5 * (one - r) * gs_d
    xr, xs, yr, ys, _det = _jacobian(p, q, u, v, r, s, variation=variation)
    assign(result, 6, (ys * gr - yr * gs) / determinant)
    assign(result, 7, (-xs * gr + xr * gs) / determinant)
    return result, determinant


def _tensor(xr: IA, xs: IA, yr: IA, ys: IA, a: float, b: float) -> IA:
    return vstack(
        (
            stack((xr * xr, xs * xs, a * xr * xs))[None, :],
            stack((yr * yr, ys * ys, a * yr * ys))[None, :],
            stack((b * xr * yr, b * xs * ys, xr * ys + yr * xs))[None, :],
        )
    )


def _interpolations(p: IA, q: IA, u: IA, v: IA, r: IA, s: IA, determinant: IA) -> tuple[IA, IA]:
    r_bar = u / 3.0
    s_bar = (u * q - p * v) / (3.0 * q)
    t_sigma = _tensor(IA.point(1.0), p, IA.point(0.0), q, 2.0, 1.0)
    t_epsilon = _tensor(IA.point(1.0), p, IA.point(0.0), q, 1.0, 2.0)
    shear = vstack((stack((IA.point(1.0), p))[None, :], stack((IA.point(0.0), q))[None, :]))
    n_sigma = zeros((8, 14))
    n_epsilon = zeros((8, 21))
    assign(n_sigma, (slice(None), slice(0, 8)), np.eye(8))
    assign(n_epsilon, (slice(None), slice(0, 8)), np.eye(8))
    seed = vstack(
        (
            stack((s - s_bar, IA.point(0.0)))[None, :],
            stack((IA.point(0.0), r - r_bar))[None, :],
            zeros((1, 2)),
        )
    )
    stress_vary = t_sigma @ seed
    strain_vary = t_epsilon @ seed
    for row, column in ((0, 8), (3, 10)):
        assign(n_sigma, (slice(row, row + 3), slice(column, column + 2)), stress_vary)
        assign(n_epsilon, (slice(row, row + 3), slice(column, column + 2)), strain_vary)
    shear_seed = vstack(
        (
            stack((s - s_bar, IA.point(0.0)))[None, :],
            stack((IA.point(0.0), r - r_bar))[None, :],
        )
    )
    assign(n_sigma, (slice(6, 8), slice(12, 14)), shear @ shear_seed)
    assign(n_epsilon, (slice(6, 8), slice(12, 14)), shear @ shear_seed)
    enrichment = zeros((3, 7))
    for key, value in {
        (0, 0): r, (0, 4): r * s, (1, 1): s, (1, 5): r * s,
        (2, 2): r, (2, 3): s, (2, 6): r * s,
    }.items():
        assign(enrichment, key, value)
    assign(n_epsilon, (slice(0, 3), slice(14, 21)), (q / determinant) * (t_epsilon @ enrichment))
    return n_sigma, n_epsilon


def _constitutive() -> IA:
    value = np.zeros((8, 8), dtype=float)
    value[:3, :3] = np.asarray(((32 / 3, 8 / 3, 0), (8 / 3, 32 / 3, 0), (0, 0, 4)))
    value[3:6, 3:6] = np.asarray(((32 / 81, 8 / 81, 0), (8 / 81, 32 / 81, 0), (0, 0, 4 / 27)))
    value[6:, 6:] = np.asarray(((10 / 3, 0), (0, 10 / 3)))
    return IA.point(value)


def _constitutive_inverse() -> IA:
    return IA.point(np.linalg.inv(_constitutive().mid))


def _constitutive_lower_factor() -> IA:
    constitutive = _constitutive().mid
    lower = np.linalg.cholesky(constitutive)
    factor = (1.0 - 1.0e-8) * lower.T
    residual = 0.5 * (constitutive - factor.T @ factor + (constitutive - factor.T @ factor).T)
    rounding = 4096.0 * EPSILON * constitutive.shape[0] * max(
        float(np.linalg.norm(constitutive, ord=2)), 1.0
    )
    if float(np.linalg.eigvalsh(residual)[0]) <= rounding:
        raise RuntimeError("constitutive lower factor is not certified")
    return IA.point(factor)


def _centre_taylor(p: IA, q: IA, u: IA, v: IA) -> IA:
    f0 = IA.point(np.ones(4) / 4.0)
    fr = IA.point(np.asarray((-1, 1, 1, -1)) / 4.0)
    fs = IA.point(np.asarray((-1, -1, 1, 1)) / 4.0)
    frs = IA.point(np.asarray((1, -1, 1, -1)) / 4.0)
    result = zeros((3, 24))
    jr, js = v, u * q - p * v
    for coordinate in range(24):
        node, component = divmod(coordinate, 6)
        ur = fr[node] if component == 0 else IA.point(0.0)
        us = fs[node] if component == 0 else IA.point(0.0)
        urs = frs[node] if component == 0 else IA.point(0.0)
        vr = fr[node] if component == 1 else IA.point(0.0)
        vs = fs[node] if component == 1 else IA.point(0.0)
        vrs = frs[node] if component == 1 else IA.point(0.0)
        d0 = f0[node] if component == 5 else IA.point(0.0)
        dr = fr[node] if component == 5 else IA.point(0.0)
        ds = fs[node] if component == 5 else IA.point(0.0)
        n0 = -p * ur + us - q * vr
        nr = -u * ur + urs - v * vr
        ns = -p * urs + u * us - q * vrs + v * vs
        assign(result, (0, coordinate), d0 + n0 / (2.0 * q))
        assign(result, (1, coordinate), dr + (nr * q - n0 * jr) / (2.0 * q * q))
        assign(result, (2, coordinate), ds + (ns * q - n0 * js) / (2.0 * q * q))
    return result


def _residual_mode(p: IA, q: IA, u: IA, v: IA) -> IA:
    x = stack((-1.0 - p + u, 1.0 - p - u, 1.0 + p + u, -1.0 + p - u))
    y = stack((-q + v, -q - v, q + v, q - v))
    xi = IA.point(np.asarray((-1, 1, 1, -1), dtype=float))
    eta = IA.point(np.asarray((-1, -1, 1, 1), dtype=float))
    alternating = IA.point(np.asarray((1, -1, 1, -1), dtype=float))
    area = 4.0 * q
    eta_y = (eta[None, :] @ y[:, None])[0, 0]
    xi_y = (xi[None, :] @ y[:, None])[0, 0]
    eta_x = (eta[None, :] @ x[:, None])[0, 0]
    xi_x = (xi[None, :] @ x[:, None])[0, 0]
    b1 = (eta_y * xi - xi_y * eta) / (4.0 * area)
    b2 = (-eta_x * xi + xi_x * eta) / (4.0 * area)
    alt_x = (alternating[None, :] @ x[:, None])[0, 0]
    alt_y = (alternating[None, :] @ y[:, None])[0, 0]
    return (alternating - alt_x * b1 - alt_y * b2) / 4.0


def _shape_hessian(
    p: IA,
    q: IA,
    u: IA,
    v: IA,
    r: IA,
    s: IA,
    node: int,
    *,
    variation: tuple[IA, IA] | None = None,
) -> tuple[IA, IA, IA, IA, IA]:
    _n, nr, ns, nrs = _shape(r, s)
    xr, xs, yr, ys, determinant = _jacobian(
        p, q, u, v, r, s, variation=variation
    )
    nx = (ys * nr[node] - yr * ns[node]) / determinant
    ny = (-xs * nr[node] + xr * ns[node]) / determinant
    # J_r=[[0,u],[0,v]], J_s=[[u,0],[v,0]].
    rhs_r0 = IA.point(0.0)
    rhs_r1 = nrs[node] - u * nx - v * ny
    rhs_s0 = nrs[node] - u * nx - v * ny
    rhs_s1 = IA.point(0.0)
    nx_r = (ys * rhs_r0 - yr * rhs_r1) / determinant
    ny_r = (-xs * rhs_r0 + xr * rhs_r1) / determinant
    nx_s = (ys * rhs_s0 - yr * rhs_s1) / determinant
    ny_s = (-xs * rhs_s0 + xr * rhs_s1) / determinant
    nxx = nx_r * (ys / determinant) + nx_s * (-yr / determinant)
    nxy = nx_r * (-xs / determinant) + nx_s * (xr / determinant)
    nyx = ny_r * (ys / determinant) + ny_s * (-yr / determinant)
    nyy = ny_r * (-xs / determinant) + ny_s * (xr / determinant)
    return nx, ny, nxx, (nxy + nyx) / 2.0, nyy


def _assemble_parameters(
    p: IA,
    q: IA,
    u: IA,
    v: IA,
    *,
    variation: tuple[IA, IA] | None = None,
) -> dict[str, IA]:
    constitutive = _constitutive()
    constitutive_inverse = _constitutive_inverse()
    constitutive_factor = _constitutive_lower_factor()
    f_matrix = zeros((21, 14))
    gq = zeros((14, 20))
    h_strain = zeros((21, 21))
    stress_dual_gram = zeros((14, 14))
    gram = zeros((3, 3))
    norm_rows: list[tuple[IA, IA, IA, IA]] = []
    strain_rows: list[IA] = []
    determinants: list[IA] = []
    area = IA.point(0.0)
    for gauss_index, (r, s) in enumerate(GAUSS):
        n, _nr, _ns, _nrs = _shape(r, s)
        compatible, determinant = _compatible(
            p, q, u, v, r, s, variation=variation
        )
        n_sigma, n_epsilon = _interpolations(p, q, u, v, r, s, determinant)
        strain_rows.append(constitutive_factor @ n_epsilon)
        determinants.append(determinant)
        f_matrix = f_matrix - determinant * (n_epsilon.T @ n_sigma)
        h_strain = h_strain + determinant * (n_epsilon.T @ constitutive @ n_epsilon)
        stress_dual_gram = stress_dual_gram + determinant * (
            n_sigma.T @ constitutive_inverse @ n_sigma
        )
        gq = gq + determinant * (n_sigma.T @ compatible)
        polynomial = stack((IA.point(1.0), r, s))
        gram = gram + (2.0 / 3.0) * determinant * outer(polynomial, polynomial)

        compatible24 = zeros((8, 24))
        for node in range(4):
            assign(
                compatible24,
                (slice(None), slice(6 * node, 6 * node + 5)),
                compatible[:, 5 * node : 5 * node + 5],
            )
        delta = zeros((1, 24))
        delta_gradient = zeros((2, 24))
        for node in range(4):
            nx, ny, nxx, nxy, nyy = _shape_hessian(
                p, q, u, v, r, s, node, variation=variation
            )
            base = 6 * node
            assign(delta, (0, base), 0.5 * ny)
            assign(delta, (0, base + 1), -0.5 * nx)
            assign(delta, (0, base + 5), n[node])
            assign(delta_gradient, (0, base), 0.5 * nxy)
            assign(delta_gradient, (0, base + 1), -0.5 * nxx)
            assign(delta_gradient, (0, base + 5), nx)
            assign(delta_gradient, (1, base), 0.5 * nyy)
            assign(delta_gradient, (1, base + 1), -0.5 * nxy)
            assign(delta_gradient, (1, base + 5), ny)
        norm_rows.append((determinant, compatible24, delta, delta_gradient))
        area = area + determinant

    stationary = zeros((35, 35))
    assign(stationary, (slice(0, 14), slice(14, 35)), f_matrix.T)
    assign(stationary, (slice(14, 35), slice(0, 14)), f_matrix)
    assign(stationary, (slice(14, 35), slice(14, 35)), h_strain)
    coupling = zeros((24, 35))
    coupling20 = zeros((20, 35))
    assign(coupling20, (slice(None), slice(0, 14)), gq.T)
    for node in range(4):
        assign(
            coupling,
            (slice(6 * node, 6 * node + 5), slice(None)),
            coupling20[5 * node : 5 * node + 5, :],
        )

    centre = _centre_taylor(p, q, u, v)
    pl = 6.0 * (centre.T @ gram @ centre)
    gamma = _residual_mode(p, q, u, v)
    gamma24 = zeros((24,))
    for node in range(4):
        assign(gamma24, 6 * node + 5, gamma[node])
    residual_coefficient = 2.0 * (1.0 / 1000.0) * 6.0 * (2.0 / 3.0) * (4.0 * q)
    residual = residual_coefficient * outer(gamma24, gamma24)

    norm = zeros((24, 24))
    for determinant, compatible24, delta, delta_gradient in norm_rows:
        norm = norm + determinant * (
            compatible24.T @ constitutive @ compatible24
            + 4.0 * (delta.T @ delta)
            + area * (delta_gradient.T @ delta_gradient)
        )
    return {
        "stationary": stationary,
        "coupling": coupling,
        "pl": pl,
        "residual": residual,
        "gram": gram,
        "centre": centre,
        "gamma": gamma24,
        "area": area,
        "residual_coefficient": residual_coefficient,
        "strain_operator": vstack(strain_rows),
        "stress_dual_gram": stress_dual_gram,
        "determinants": stack(determinants),
        "norm": norm,
    }


def assemble_intervals(bounds: Mapping[str, tuple[Fraction, Fraction]]) -> dict[str, IA]:
    """Assemble an enclosure in the original ``p,q,u,v`` coordinates."""

    p = interval(*bounds["p"], variable=0)
    q = interval(*bounds["q"], variable=1)
    u = interval(*bounds["u"], variable=2)
    v = interval(*bounds["v"], variable=3)
    return _assemble_parameters(p, q, u, v)


def assemble_variation_intervals(
    bounds: Mapping[str, tuple[Fraction, Fraction]],
) -> dict[str, IA]:
    """Assemble using the exact Q1F relative-variation coordinates.

    ``a=(u*q-p*v)/q`` and ``b=v/q`` turn the frozen relative-Jacobian
    predicate into ``a**2+b**2 <= 1/8``.  Reconstructing ``u=a+p*b`` and
    ``v=q*b`` here preserves the correlations that independent ``u,v``
    interval boxes otherwise discard.
    """

    p = interval(*bounds["p"], variable=0)
    q = interval(*bounds["q"], variable=1)
    a = interval(*bounds["a"], variable=2)
    b = interval(*bounds["b"], variable=3)
    u = a + p * b
    v = q * b
    result = _assemble_parameters(p, q, u, v, variation=(a, b))
    result["variation_parameters"] = stack((p, q, a, b))
    return result


def _exact_variation_control_inverse(parameters: IA) -> IA:
    """Evaluate the independently derived rational inverse with outward IA."""

    from e4_pl_q1h_symbolic_kernel import variation_control_inverse_evaluator

    values = variation_control_inverse_evaluator()(
        parameters[0], parameters[1], parameters[2], parameters[3]
    )
    entries = tuple(as_interval(value) for value in values)
    return vstack(
        tuple(stack(entries[18 * row : 18 * (row + 1)])[None, :] for row in range(18))
    )


def norm_bound(interval_matrix: IA, centre: np.ndarray) -> float:
    radius = np.maximum(np.abs(interval_matrix.lo - centre), np.abs(interval_matrix.hi - centre))
    one = float(np.max(np.sum(radius, axis=0)))
    infinity = float(np.max(np.sum(radius, axis=1)))
    return math.sqrt(max(one * infinity, 0.0))


def absolute_norm_bound(interval_matrix: IA) -> float:
    magnitude = np.maximum(np.abs(interval_matrix.lo), np.abs(interval_matrix.hi))
    one = float(np.max(np.sum(magnitude, axis=0)))
    infinity = float(np.max(np.sum(magnitude, axis=1)))
    return math.sqrt(max(one * infinity, 0.0))


def _congruence_gershgorin_margin(centre: np.ndarray, perturbation: float) -> float:
    symmetric = 0.5 * (centre + centre.T)
    try:
        lower = np.linalg.cholesky(symmetric)
    except np.linalg.LinAlgError:
        return -math.inf
    transform = np.linalg.solve(lower.T, np.eye(lower.shape[0]))
    congruent = transform.T @ symmetric @ transform
    column_norms = np.linalg.norm(transform, axis=0)
    perturbation_entries = perturbation * np.outer(column_norms, column_norms)
    rounding = (
        4096.0
        * EPSILON
        * max(centre.shape[0], 1)
        * (np.abs(transform).T @ np.maximum(np.abs(symmetric), 1.0) @ np.abs(transform))
    )
    entry_bounds = np.abs(congruent) + perturbation_entries + rounding
    diagonal_lower = np.diag(congruent) - np.diag(perturbation_entries) - np.diag(rounding)
    off_diagonal = np.sum(entry_bounds, axis=1) - np.diag(entry_bounds)
    return float(np.min(diagonal_lower - off_diagonal))


def _interval_congruence_gershgorin_margin(matrix: IA) -> float:
    """Entrywise Gershgorin margin after midpoint Cholesky normalization."""

    midpoint = 0.5 * (matrix.mid + matrix.mid.T)
    try:
        lower = np.linalg.cholesky(midpoint)
    except np.linalg.LinAlgError:
        return -math.inf
    transform = np.linalg.solve(lower.T, np.eye(lower.shape[0]))
    congruent = IA.point(transform.T) @ matrix @ IA.point(transform)
    magnitude = np.maximum(np.abs(congruent.lo), np.abs(congruent.hi))
    diagonal_lower = np.diag(congruent.lo)
    off_diagonal = np.sum(magnitude, axis=1) - np.diag(magnitude)
    return float(np.min(diagonal_lower - off_diagonal))


def _eigenvalue_lower_bound(matrix: IA) -> float:
    centre = 0.5 * (matrix.mid + matrix.mid.T)
    perturbation = norm_bound(matrix, matrix.mid)
    scale = max(float(np.linalg.norm(centre, ord=2)), 1.0)
    rounding = 4096.0 * EPSILON * max(centre.shape[0], 1) * scale
    return float(np.linalg.eigvalsh(centre)[0]) - perturbation - rounding


def _rectangular_singular_lower(matrix: IA) -> tuple[float, float]:
    centre = matrix.mid
    singular_values = np.linalg.svd(centre, compute_uv=False)
    direct_delta = norm_bound(matrix, centre)
    rounding = 4096.0 * EPSILON * max(centre.shape) * max(float(singular_values[0]), 1.0)
    direct_lower = float(singular_values[-1]) - direct_delta - rounding
    try:
        left_inverse = np.linalg.solve(centre.T @ centre, centre.T)
    except np.linalg.LinAlgError:
        return direct_lower, math.inf
    preconditioned = IA.point(left_inverse) @ (matrix - IA.point(centre))
    eta = absolute_norm_bound(preconditioned)
    if not math.isfinite(eta) or eta >= 1.0:
        return direct_lower, eta
    inverse_one = float(np.linalg.norm(left_inverse, ord=1))
    inverse_infinity = float(np.linalg.norm(left_inverse, ord=np.inf))
    inverse_two_upper = math.sqrt(inverse_one * inverse_infinity) * (1.0 + 1024.0 * EPSILON)
    return max(direct_lower, (1.0 - eta) / inverse_two_upper), eta


def _enclose_solve(matrix: IA, right: IA) -> tuple[np.ndarray, IA, float]:
    matrix0, right0 = matrix.mid, right.mid
    try:
        inverse0 = np.linalg.inv(matrix0)
    except np.linalg.LinAlgError as exc:
        raise ValueError("midpoint solve matrix is singular") from exc
    solution0 = inverse0 @ right0
    matrix_delta = matrix - IA.point(matrix0)
    right_delta = right - IA.point(right0)
    preconditioned_delta = IA.point(inverse0) @ matrix_delta
    absolute_delta = np.maximum(
        np.abs(preconditioned_delta.lo), np.abs(preconditioned_delta.hi)
    )
    eta = float(np.max(np.sum(absolute_delta, axis=1)))
    if not math.isfinite(eta) or eta >= 1.0:
        raise ValueError(f"solve perturbation is not contractive: {eta}")
    residual = right_delta - matrix_delta @ IA.point(solution0)
    preconditioned_residual = IA.point(inverse0) @ residual
    residual_absolute = np.maximum(
        np.abs(preconditioned_residual.lo), np.abs(preconditioned_residual.hi)
    )
    radius = np.linalg.solve(np.eye(absolute_delta.shape[0]) - absolute_delta, residual_absolute)
    if np.any(radius < -1.0e-14) or np.any(~np.isfinite(radius)):
        raise ValueError("componentwise solve enclosure is invalid")
    radius = _up(np.maximum(radius, 0.0) * (1.0 + 128.0 * EPSILON))
    if matrix.is_affine and right.is_affine:
        assert matrix.coefficients is not None and right.coefficients is not None
        coefficients = np.stack(
            tuple(
                inverse0
                @ (
                    right.coefficients[index]
                    - matrix.coefficients[index] @ solution0
                )
                for index in range(4)
            )
        )
        linear_radius = np.sum(np.abs(coefficients), axis=0)
        remainder = np.maximum(radius - linear_radius, 0.0)
        return solution0, IA.affine(solution0, coefficients, remainder), eta
    return solution0, IA(_down(solution0 - radius), _up(solution0 + radius)), eta


def _certify_matrices(matrices: Mapping[str, IA]) -> dict[str, float | str | bool]:
    stationary = matrices["stationary"]
    coupling = matrices["coupling"]
    f_matrix = stationary[14:35, 0:14]
    strain_matrix = stationary[14:35, 14:35]
    g_matrix = coupling[:, 0:14]
    strain_singular_lower, strain_operator_eta = _rectangular_singular_lower(
        matrices["strain_operator"]
    )
    determinant_lower = float(np.min(matrices["determinants"].lo))
    strain_lower = determinant_lower * strain_singular_lower**2
    if not math.isfinite(strain_lower) or strain_lower <= 0.0:
        return {
            "classification": "UNRESOLVED",
            "reason": "STRAIN_GRAM_NOT_INTERVAL_POSITIVE",
            "strain_lower_bound": strain_lower,
            "strain_operator_eta": strain_operator_eta,
            "determinant_lower_bound": determinant_lower,
        }
    f_upper = absolute_norm_bound(f_matrix)
    if not math.isfinite(f_upper) or f_upper <= 0.0:
        return {"classification": "UNRESOLVED", "reason": "F_NORM_BOUND_INVALID"}
    f_singular_lower, f_operator_eta = _rectangular_singular_lower(f_matrix)
    if not math.isfinite(f_singular_lower) or f_singular_lower <= 0.0:
        return {
            "classification": "UNRESOLVED",
            "reason": "F_FULL_COLUMN_RANK_NOT_CERTIFIED",
            "f_singular_lower_bound": f_singular_lower,
            "f_operator_eta": f_operator_eta,
        }
    try:
        _solution0, strain_inverse_f, strain_solve_eta = _enclose_solve(
            strain_matrix, f_matrix
        )
    except ValueError as exc:
        return {
            "classification": "UNRESOLVED",
            "reason": "STRAIN_SOLVE_NOT_INTERVAL_CONTRACTIVE",
            "detail": str(exc),
        }
    schur_metric = f_matrix.T @ strain_inverse_f
    schur_metric_upper = absolute_norm_bound(schur_metric)
    if not math.isfinite(schur_metric_upper) or schur_metric_upper <= 0.0:
        return {"classification": "UNRESOLVED", "reason": "SCHUR_METRIC_BOUND_INVALID"}
    core_coefficient = math.nextafter(1.0 / schur_metric_upper, -math.inf)
    if core_coefficient <= 0.0:
        return {"classification": "UNRESOLVED", "reason": "CORE_LOWER_BOUND_NONPOSITIVE"}

    gram_lower = _eigenvalue_lower_bound(matrices["gram"])
    residual_coefficient_lower = float(np.min(matrices["residual_coefficient"].lo))
    pl_coefficient_lower = 6.0 * gram_lower
    coefficient_lower = min(core_coefficient, pl_coefficient_lower, residual_coefficient_lower)
    if coefficient_lower <= 0.0:
        return {
            "classification": "UNRESOLVED",
            "reason": "POSITIVE_FORM_COEFFICIENT_NOT_CERTIFIED",
            "core_coefficient_lower_bound": core_coefficient,
            "gram_lower_bound": gram_lower,
            "residual_coefficient_lower_bound": residual_coefficient_lower,
        }

    weight_safety = 1.0 - 1.0e-10
    core_weight = weight_safety * math.sqrt(core_coefficient)
    pl_weight = weight_safety * math.sqrt(pl_coefficient_lower)
    residual_weight = weight_safety * math.sqrt(residual_coefficient_lower)
    operator = vstack(
        (
            core_weight * g_matrix.T,
            pl_weight * matrices["centre"],
            residual_weight * matrices["gamma"][None, :],
        )
    )
    operator_q = operator[:, 6:24]
    operator0 = operator_q.mid
    try:
        operator_inverse0 = np.linalg.inv(operator0)
    except np.linalg.LinAlgError:
        return {"classification": "UNRESOLVED", "reason": "MIDPOINT_CONTROL_OPERATOR_SINGULAR"}
    preconditioned = IA.point(operator_inverse0) @ (operator_q - IA.point(operator0))
    operator_eta = absolute_norm_bound(preconditioned)
    inverse_one = float(np.linalg.norm(operator_inverse0, ord=1))
    inverse_infinity = float(np.linalg.norm(operator_inverse0, ord=np.inf))
    inverse_two_upper = math.sqrt(inverse_one * inverse_infinity) * (1.0 + 1024.0 * EPSILON)
    direct_singular_values = np.linalg.svd(operator0, compute_uv=False)
    direct_operator_delta = norm_bound(operator_q, operator0)
    direct_rounding = (
        4096.0
        * EPSILON
        * max(operator0.shape)
        * max(float(direct_singular_values[0]), 1.0)
    )
    preconditioned_lower = (
        (1.0 - operator_eta) / inverse_two_upper
        if math.isfinite(operator_eta) and operator_eta < 1.0
        else -math.inf
    )
    singular_lower = max(
        preconditioned_lower,
        float(direct_singular_values[-1]) - direct_operator_delta - direct_rounding,
    )
    if singular_lower <= 0.0:
        return {
            "classification": "UNRESOLVED",
            "reason": "CONTROL_OPERATOR_SINGULAR_VALUE_NOT_CERTIFIED",
            "operator_eta": operator_eta,
            "operator_direct_delta": direct_operator_delta,
        }
    h_upper = absolute_norm_bound(matrices["norm"])
    coercivity_lower = singular_lower * singular_lower / h_upper
    positive = singular_lower > 0.0 and coercivity_lower >= ALPHA_STAR
    return {
        "classification": "POSITIVE" if positive else "UNRESOLVED",
        "reason": "QUOTIENT_CONGRUENCE_POSITIVE" if positive else "SUBDIVIDE",
        "strain_lower_bound": strain_lower,
        "strain_operator_eta": strain_operator_eta,
        "determinant_lower_bound": determinant_lower,
        "f_norm_upper_bound": f_upper,
        "f_singular_lower_bound": f_singular_lower,
        "f_operator_eta": f_operator_eta,
        "strain_solve_eta": strain_solve_eta,
        "schur_metric_norm_upper_bound": schur_metric_upper,
        "core_coefficient_lower_bound": core_coefficient,
        "gram_lower_bound": gram_lower,
        "pl_coefficient_lower_bound": pl_coefficient_lower,
        "residual_coefficient_lower_bound": residual_coefficient_lower,
        "positive_form_coefficient_lower_bound": coefficient_lower,
        "operator_eta": operator_eta,
        "operator_singular_lower_bound": singular_lower,
        "h_norm_upper_bound": h_upper,
        "coercivity_ratio_lower_bound": coercivity_lower,
        "h_kernel_certified": singular_lower > 0.0,
        "coercivity_certified": coercivity_lower >= ALPHA_STAR,
    }


def _certify_direct_matrices(matrices: Mapping[str, IA]) -> dict[str, float | str | bool]:
    """Certify the actual anchored ``K-alpha*H`` Schur complement.

    The two interval solves mirror the exact nested Schur representation
    ``S=F.T*Hstrain^-1*F`` and ``Kcore=G*S^-1*G.T``.  A fixed midpoint
    Cholesky congruence then proves positive definiteness of the complete
    anchored 18-dimensional quotient matrix on the whole parameter box.
    """

    stationary = matrices["stationary"]
    coupling = matrices["coupling"]
    f_matrix = stationary[14:35, 0:14]
    strain_matrix = stationary[14:35, 14:35]
    g_matrix = coupling[:, 0:14]
    try:
        _strain_solution0, strain_inverse_f, strain_eta = _enclose_solve(
            strain_matrix, f_matrix
        )
    except ValueError as exc:
        return {
            "classification": "UNRESOLVED",
            "reason": "STRAIN_SOLVE_NOT_INTERVAL_CONTRACTIVE",
            "detail": str(exc),
        }
    schur = 0.5 * (f_matrix.T @ strain_inverse_f + strain_inverse_f.T @ f_matrix)
    try:
        _schur_solution0, schur_inverse_g, schur_eta = _enclose_solve(
            schur, g_matrix.T
        )
    except ValueError as exc:
        return {
            "classification": "UNRESOLVED",
            "reason": "SCHUR_SOLVE_NOT_INTERVAL_CONTRACTIVE",
            "detail": str(exc),
            "strain_solve_eta": strain_eta,
        }
    core = 0.5 * (g_matrix @ schur_inverse_g + schur_inverse_g.T @ g_matrix.T)
    stiffness = core + matrices["pl"] + matrices["residual"]
    delta = 0.5 * (
        stiffness - ALPHA_STAR * matrices["norm"]
        + (stiffness - ALPHA_STAR * matrices["norm"]).T
    )
    quotient = delta[6:24, 6:24]
    midpoint = 0.5 * (quotient.mid + quotient.mid.T)
    perturbation = norm_bound(quotient, midpoint)
    margin = _interval_congruence_gershgorin_margin(quotient)
    positive = math.isfinite(margin) and margin > 0.0
    return {
        "classification": "POSITIVE" if positive else "UNRESOLVED",
        "reason": "DIRECT_SCHUR_QUOTIENT_POSITIVE" if positive else "SUBDIVIDE",
        "strain_solve_eta": strain_eta,
        "schur_solve_eta": schur_eta,
        "quotient_perturbation_bound": perturbation,
        "quotient_congruence_margin": margin,
        "coercivity_certified": positive,
    }


def _certify_control_matrices(matrices: Mapping[str, IA]) -> dict[str, float | str | bool]:
    """Certify coercivity in the exact 14+3+1 control coordinates."""

    g_matrix = matrices["coupling"][:, 0:14]
    schur_upper = absolute_norm_bound(matrices["stress_dual_gram"])
    if not math.isfinite(schur_upper) or schur_upper <= 0.0:
        return {"classification": "UNRESOLVED", "reason": "SCHUR_METRIC_BOUND_INVALID"}
    core_lower = math.nextafter(1.0 / schur_upper, -math.inf)

    try:
        control_inverse = _exact_variation_control_inverse(matrices["variation_parameters"])
    except (ArithmeticError, ValueError, ZeroDivisionError) as exc:
        return {
            "classification": "UNRESOLVED",
            "reason": "EXACT_CONTROL_INVERSE_NOT_ENCLOSED",
            "detail": str(exc),
        }

    norm_q = matrices["norm"][6:24, 6:24]
    norm_control = control_inverse.T @ norm_q @ control_inverse
    energy_control = zeros((18, 18))
    assign(energy_control, (slice(0, 14), slice(0, 14)), core_lower * np.eye(14))
    assign(energy_control, (slice(14, 17), slice(14, 17)), 6.0 * matrices["gram"])
    assign(energy_control, (17, 17), matrices["residual_coefficient"])
    delta_control = 0.5 * (
        energy_control - ALPHA_STAR * norm_control
        + (energy_control - ALPHA_STAR * norm_control).T
    )
    margin = _interval_congruence_gershgorin_margin(delta_control)
    positive = math.isfinite(margin) and margin > 0.0
    return {
        "classification": "POSITIVE" if positive else "UNRESOLVED",
        "reason": "CONTROL_COORDINATE_COERCIVITY_POSITIVE" if positive else "SUBDIVIDE",
        "schur_metric_projection_upper_bound": schur_upper,
        "core_coefficient_lower_bound": core_lower,
        "control_inverse_exact_dag": True,
        "control_congruence_margin": margin,
        "h_kernel_certified_by_symbolic_factor_minors": True,
        "coercivity_certified": positive,
    }


def certify_box(bounds: Mapping[str, tuple[Fraction, Fraction]]) -> dict[str, float | str | bool]:
    return _certify_matrices(assemble_intervals(bounds))


def certify_variation_box(
    bounds: Mapping[str, tuple[Fraction, Fraction]],
) -> dict[str, float | str | bool]:
    return _certify_matrices(assemble_variation_intervals(bounds))


def certify_variation_box_direct(
    bounds: Mapping[str, tuple[Fraction, Fraction]],
) -> dict[str, float | str | bool]:
    return _certify_direct_matrices(assemble_variation_intervals(bounds))


def certify_variation_box_control(
    bounds: Mapping[str, tuple[Fraction, Fraction]],
) -> dict[str, float | str | bool]:
    return _certify_control_matrices(assemble_variation_intervals(bounds))


__all__ = [
    "ALPHA_STAR",
    "IA",
    "assemble_intervals",
    "assemble_variation_intervals",
    "certify_box",
    "certify_variation_box",
    "certify_variation_box_direct",
    "certify_variation_box_control",
    "interval",
]
