"""Independent planar Timoshenko reference element for F03 preflight.

This is a classical continuum comparison operator, not the native B3-GE
formulation. Local coordinates are u at ends/midpoint, Hermite v and its
independent nodal slopes at ends, and theta at ends/midpoint. All terms
use the same trial field, including the later interface and line loads.
"""

from __future__ import annotations

import numpy as np


E = 210e9
NU = .3
G = E/(2*(1+NU))
AREA = .01
SHEAR_AREA = .008
INERTIA = 8.333333333333333e-6
SECTION = np.diag((E*AREA, E*INERTIA, G*SHEAR_AREA))


def fields(xi: float, length: float) -> tuple[np.ndarray, np.ndarray]:
    """Return physical [u,v,theta] interpolation and [u',theta',v'-theta]."""
    if not np.isfinite(xi) or not 0 <= xi <= 1 or not np.isfinite(length) or length <= 0:
        raise ValueError('reference beam coordinate or length invalid')
    p = np.array((2*(xi-.5)*(xi-1), 4*xi*(1-xi), 2*xi*(xi-.5)))
    dp = np.array((4*xi-3, 4-8*xi, 4*xi-1))/length
    h = np.array((2*xi**3-3*xi**2+1,
                  length*(xi**3-2*xi**2+xi),
                  -2*xi**3+3*xi**2,
                  length*(xi**3-xi**2)))
    dh = np.array((6*xi**2-6*xi,
                   length*(3*xi**2-4*xi+1),
                   -6*xi**2+6*xi,
                   length*(3*xi**2-2*xi)))/length
    n = np.zeros((3, 10))
    b = np.zeros((3, 10))
    n[0, :3] = p
    n[1, 3:7] = h
    n[2, 7:] = p
    b[0, :3] = dp
    b[1, 7:] = dp
    b[2, 3:7] = dh
    b[2, 7:] = -p
    return n, b


def stiffness(length: float) -> np.ndarray:
    """Exact polynomial stiffness quadrature for one straight element."""
    roots, weights = np.polynomial.legendre.leggauss(3)
    result = np.zeros((10, 10))
    for root, weight in zip(roots, weights):
        _, b = fields(float((root+1)/2), length)
        result += length*weight/2 * b.T @ SECTION @ b
    return (result+result.T)/2


def load(length: float, left: float, kind: str, order: int = 16) -> np.ndarray:
    """Consistent distributed transverse load through the same v field."""
    if (kind not in ('smooth', 'sine') or order < 2 or
            not np.isfinite(left) or left < 0 or left+length > 1+1e-12 or
            not np.isfinite(length) or length <= 0):
        raise ValueError('unsupported reference load or quadrature order')
    roots, weights = np.polynomial.legendre.leggauss(order)
    result = np.zeros(10)
    for root, weight in zip(roots, weights):
        xi = float((root+1)/2)
        s = left+length*xi
        q = 1e6*(1+.25*np.cos(2*np.pi*s)) if kind=='smooth' else 1e6*np.sin(2*np.pi*s)
        n, _ = fields(xi, length)
        result += length*weight/2*q*n[1]
    return result
