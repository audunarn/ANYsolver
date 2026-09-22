"""Bounded independent Green integration for the classical primal diagnostic.

Physical line densities are Legendre polynomials on X=2s-1 plus a declared
cos(2*pi*s) term. Endpoint atoms retain their separate measure. This module
does not assemble or solve a structural problem, use a FE multiplier space,
or establish reference convergence on its own.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.polynomial.legendre import leggauss, legval, legvander, legint, legmul

ELL = .46


class NonfiniteGreenResponse(ValueError):
    """Identified nonfinite quadrature response, never malformed input."""


class NegativeGreenResponse(ValueError):
    """Identified negative squared norm, retained as a numerical failure."""


def _owned(value, shape, name):
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f'invalid {name}')
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class Functional:
    """Physical residual-side force/moment density and root/tip atoms."""

    coefficients: np.ndarray
    cosine: np.ndarray
    atoms: np.ndarray

    def __post_init__(self):
        shape = np.shape(self.coefficients)
        if len(shape) != 2 or not 1 <= shape[0] <= 25 or shape[1] != 3:
            raise ValueError('density degree must be between zero and 24')
        object.__setattr__(self, 'coefficients', _owned(self.coefficients, shape, 'density coefficients'))
        object.__setattr__(self, 'cosine', _owned(self.cosine, (3,), 'cosine amplitudes'))
        object.__setattr__(self, 'atoms', _owned(self.atoms, (2, 3), 'endpoint atoms'))

    def density(self, s):
        s = np.asarray(s, dtype=np.float64)
        if not np.all(np.isfinite(s)) or np.any(s < 0) or np.any(s > 1):
            raise ValueError('station outside unit beam')
        polynomial = np.moveaxis(legval(2*s-1, self.coefficients), 0, -1)
        return polynomial + np.cos(2*np.pi*s)[..., None]*self.cosine

    def difference(self, other):
        n = max(len(self.coefficients), len(other.coefficients))
        coefficients = np.zeros((n, 3))
        coefficients[:len(self.coefficients)] += self.coefficients
        coefficients[:len(other.coefficients)] -= other.coefficients
        return Functional(coefficients, self.cosine-other.cosine, self.atoms-other.atoms)


def _quadrature(order):
    if type(order) is not int or not 2 <= order <= 96:
        raise ValueError('bounded Gaussian order must be an integer in [2,96]')
    x, w = leggauss(order)
    return (x+1)/2, w/2


def green_inner(first: Functional, second: Functional, *, order=48):
    """Channelwise full H1 dual inner product, force-conjugate gap units.

The square's diagonal is split explicitly into two smooth triangles.
Third physical moments are divided by ELL exactly once per operand.
No positivity clipping or post-hoc symmetrization is performed.
"""
    s, w = _quadrature(order)
    t = s[:, None]*s[None, :]
    weights = w[:, None]*w[None, :]*s[:, None]
    scale = np.array([1., 1., 1/ELL])
    fs, gs = first.density(s)*scale, second.density(s)*scale
    ft, gt = first.density(t)*scale, second.density(t)*scale
    kernel = np.cosh(t)*np.cosh(1-s[:, None])/np.sinh(1.)
    density_term = np.einsum('ij,ijk->k', weights*kernel,
        fs[:, None, :]*gt+gs[:, None, :]*ft)
    fa, ga = first.atoms*scale, second.atoms*scale
    edge_kernel = np.stack((np.cosh(1-s), np.cosh(s)))/np.sinh(1.)
    f_edge = np.einsum('is,s,sk->ik', edge_kernel, w, fs)
    g_edge = np.einsum('is,s,sk->ik', edge_kernel, w, gs)
    atom_kernel = np.array([[np.cosh(1.), 1.], [1., np.cosh(1.)]])/np.sinh(1.)
    cross = np.sum(fa*g_edge+ga*f_edge, axis=0)
    atom_term = np.einsum('ik,ij,jk->k', fa, atom_kernel, ga)
    result = density_term+cross+atom_term
    if not np.all(np.isfinite(result)):
        raise NonfiniteGreenResponse('nonfinite Green inner product')
    return result


def norm_squared(functional: Functional, *, order=48):
    channels = green_inner(functional, functional, order=order)
    if np.any(channels < 0):
        raise NegativeGreenResponse('negative squared Green norm; no clipping permitted')
    total = float(channels.sum())
    if not np.isfinite(total):
        raise NonfiniteGreenResponse('nonfinite total squared Green norm')
    return total


def band_wrench(functional: Functional, left, right, *, order=48):
    """Residual-side (Fx,Fy,Mz) about global (0,0), atoms included once.

The centreline is (s,0); physical intrinsic moments add s*Fy. Root/tip
atoms belong only to intervals containing the corresponding endpoint.
"""
    if not np.isfinite([left, right]).all() or not 0 <= left < right <= 1:
        raise ValueError('invalid physical band')
    x, w = _quadrature(order)
    s = left+(right-left)*x
    density = functional.density(s)
    density[:, 2] += s*density[:, 1]
    result = (right-left)*np.einsum('i,ij->j', w, density)
    if left == 0:
        result += functional.atoms[0]
    if right == 1:
        result += functional.atoms[1]
        result[2] += functional.atoms[1, 1]
    if not np.all(np.isfinite(result)):
        raise ValueError('nonfinite physical band wrench')
    return result


def from_gauss_density(degree, samples, cosine, atoms):
    """Project a known degree-bounded polynomial remainder at GL degree+1.

    Caller supplies samples of the full physical density on the exact
    ordered unit-interval Gaussian nodes. The declared cosine is removed
    before polynomial projection; no cosine is approximated by a polynomial.
    """
    if type(degree) is not int or not 0 <= degree <= 24:
        raise ValueError('density degree outside bounded reference')
    x, w = leggauss(degree+1)
    samples = _owned(samples, (degree+1, 3), 'density samples')
    cosine = _owned(cosine, (3,), 'cosine amplitudes')
    remainder = samples-np.cos(np.pi*(x+1))[:, None]*cosine
    coefficients = (legvander(x, degree).T*w)@remainder
    coefficients *= ((2*np.arange(degree+1)+1)/2)[:, None]
    return Functional(coefficients, cosine, atoms)


def band_wrench_analytic(functional: Functional, left, right):
    """Independent polynomial and sine/cosine antiderivative band route."""
    if not np.isfinite([left, right]).all() or not 0 <= left < right <= 1:
        raise ValueError('invalid physical band')
    coefficients = functional.coefficients
    moment = np.zeros(len(coefficients)+1)
    lever_arm = legmul([.5, .5], coefficients[:, 1])
    moment[:len(lever_arm)] = lever_arm
    moment[:len(coefficients)] += coefficients[:, 2]
    channels = (coefficients[:, 0], coefficients[:, 1], moment)
    result = np.empty(3)
    for channel, coef in enumerate(channels):
        primitive = legint(coef)
        result[channel] = .5*(legval(2*right-1, primitive)-legval(2*left-1, primitive))
    omega = 2*np.pi
    cosine_integral = (np.sin(omega*right)-np.sin(omega*left))/omega
    cosine_moment = ((right*np.sin(omega*right)-left*np.sin(omega*left))/omega
                    +(np.cos(omega*right)-np.cos(omega*left))/omega**2)
    result += cosine_integral*functional.cosine
    result[2] += cosine_moment*functional.cosine[1]
    if left == 0:
        result += functional.atoms[0]
    if right == 1:
        result += functional.atoms[1]
        result[2] += functional.atoms[1, 1]
    if not np.all(np.isfinite(result)):
        raise ValueError('nonfinite physical band wrench')
    return result
