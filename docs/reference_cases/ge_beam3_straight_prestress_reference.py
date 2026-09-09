"""Separate continuum reconstruction; same-author, NOT a certified oracle.

No element, SO(3), AD, mixed interpolation, production mass or state imports.
See GE_BEAM3_STRAIGHT_PRESTRESS_REFERENCE.md for the variational derivation.
All lengths and integrals use stress-free reference arclength. N is positive
in tension. Shooting brackets are caller supplied; no eigenvalue counting,
automatic root search, high-precision certification or branch following.
"""

from dataclasses import dataclass
import math

import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq


@dataclass(frozen=True)
class StraightPrestress:
    length: float
    axial: float
    shear: float
    bending: float
    line_mass: float
    rotary_mass: float
    tension: float = 0.

    def __post_init__(self):
        values = (self.length, self.axial, self.shear, self.bending,
                  self.line_mass, self.rotary_mass, self.tension)
        if any(type(v) is not float or not math.isfinite(v) for v in values):
            raise ValueError('finite float continuum parameters required')
        if min(values[:-1]) <= 0. or self.shear > self.axial:
            raise ValueError('positive parameters and shear <= axial required')
        if not math.isfinite(self.stretch) or self.stretch <= 0.:
            raise ValueError('positive straight equilibrium stretch required')

    @property
    def stretch(self):
        return 1.+self.tension/self.axial

    @property
    def coefficients(self):
        # density = .5*(S*v_x**2 + 2*C*v_x*theta + D*theta**2
        #                + B*theta_x**2). Stable form for D-C*C/S below.
        c = self.tension-self.shear*self.stretch
        return self.shear, c, -self.stretch*c

    def system(self, squared_frequency):
        if type(squared_frequency) is not float or not math.isfinite(squared_frequency):
            raise ValueError('finite signed squared frequency required')
        s, c, _ = self.coefficients
        n = self.tension
        reduced = n*(self.stretch-n/s)
        matrix = np.array([[0., -c/s, 1./s, 0.],
                           [0., 0., 0., 1./self.bending],
                           [-squared_frequency*self.line_mass, 0., 0., 0.],
                           [0., reduced-squared_frequency*self.rotary_mass, c/s, 0.]])
        if not np.isfinite(matrix).all():
            raise ValueError('continuum system overflow')
        return matrix

    def boundary_matrix(self, squared_frequency):
        # y=(v,theta,T,M); v(0)=theta(0)=T(L)=M(L)=0.
        propagation = expm(self.length*self.system(squared_frequency))
        if not np.isfinite(propagation).all():
            raise ValueError('shooting propagation overflow')
        return propagation[2:, 2:]

    def bracketed_squared_frequency(self, bracket):
        if (type(bracket) is not tuple or len(bracket) != 2
                or any(type(v) is not float or not math.isfinite(v) for v in bracket)
                or bracket[0] >= bracket[1]):
            raise ValueError('explicit finite ordered two-float bracket required')
        def determinant(value):
            return float(np.linalg.det(self.boundary_matrix(float(value))))
        value = brentq(determinant, *bracket, xtol=1e-13, rtol=1e-13, maxiter=80)
        boundary = self.boundary_matrix(float(value))
        singular = np.linalg.svd(boundary, compute_uv=False)
        if singular[-1] > 1e-11*max(1., singular[0]):
            raise ValueError('unresolved shooting boundary residual')
        return float(value)

    def critical_compression(self):
        # At omega=0, T=0 and B*theta_xx = -P*(1+a*P)*theta.
        # theta(0)=theta_x(L)=0 gives first kL=pi/2. Stable quadratic root.
        euler = self.bending*(math.pi/(2*self.length))**2
        a = 1./self.shear-1./self.axial
        pressure = 2*euler/(1+math.sqrt(1+4*a*euler))
        if not math.isfinite(pressure) or not 0. < pressure < self.axial:
            raise ValueError('critical point outside positive-stretch branch')
        return pressure


def ritz_squared_frequencies(reference, *, terms=12):
    """Separate conforming two-field weak form; refinement is not a proof bound.

    Direct symmetric generalized eigenproblem retains signed eigenvalues.
    No shooting matrix or native beam matrices are used in this construction.
    """
    if type(reference) is not StraightPrestress or type(terms) is not int or terms not in (8, 12, 16):
        raise ValueError('owned continuum reference and 8/12/16 terms required')
    from scipy.linalg import eigh
    points, weights = np.polynomial.legendre.leggauss(40)
    p = np.polynomial.legendre.legvander(points, terms-1)
    dp = np.empty_like(p)
    for j in range(terms):
        coefficients = np.zeros(terms); coefficients[j] = 1.
        dp[:, j] = np.polynomial.legendre.legval(points, np.polynomial.legendre.legder(coefficients))
    shape = (points[:, None]+1)*p
    slope = 2*(p+(points[:, None]+1)*dp)/reference.length
    s, c, d = reference.coefficients
    stiffness = np.zeros((2*terms, 2*terms)); mass = np.zeros_like(stiffness)
    for v, dv, w in zip(shape, slope, weights*reference.length/2):
        vv, dd, dvv = np.outer(v, v), np.outer(dv, dv), np.outer(dv, v)
        stiffness[:terms, :terms] += w*s*dd
        stiffness[:terms, terms:] += w*c*dvv
        stiffness[terms:, :terms] += w*c*dvv.T
        stiffness[terms:, terms:] += w*(d*vv+reference.bending*dd)
        mass[:terms, :terms] += w*reference.line_mass*vv
        mass[terms:, terms:] += w*reference.rotary_mass*vv
    return eigh(stiffness, mass, eigvals_only=True)
