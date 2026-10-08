"""Independent classical membrane Qp operators for the bounded F03 research.

These operators use exact local tensor polynomials and held plane-stress
constants. They do not call an E4-PL element, assemble a global matrix, or
establish physical convergence of the reference problem.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
import math

import numpy as np

from scripts import _b3_e4_f03_local_moments as poly
from scripts import _b3_e4_f03_spatial_contract as c


ZERO=Fraction(0)
ONE=Fraction(1)


def _validate(rect,p):
    if not isinstance(rect,poly.Rectangle) or type(p) is not int or p not in (1,2,3):
        raise ValueError('exact rectangle and integer degree 1..3 required')


def _derivative(values,order):
    return tuple(values[k]*Fraction(math.factorial(k),math.factorial(k-order))
                 for k in range(order,len(values))) or (ZERO,)


@lru_cache(maxsize=3)
def _basis(p):
    return poly._lagrange(ZERO,ONE,p)


@lru_cache(maxsize=3)
def _gram(p):
    basis=_basis(p)
    derivative=tuple(_derivative(row,1) for row in basis)
    def matrix(left,right):
        return tuple(tuple(poly._integral_poly(poly._mul(a,b),ZERO,ONE)
                           for b in right) for a in left)
    return matrix(basis,basis),matrix(derivative,derivative),matrix(derivative,basis)


def stiffness_exact(rect,p):
    """Owned immutable coordinate Hessian, DOF order component/y-node/x-node."""
    _validate(rect,p)
    mass,derivative,mixed=_gram(p)
    hx=rect.x1-rect.x0;hy=rect.y1-rect.y0
    nc=(p+1)**2;result=[[ZERO]*(2*nc) for _ in range(2*nc)]
    plane=c.Q_PLANE;thickness=c.Q_THICKNESS
    for j in range(p+1):
        for i in range(p+1):
            a=j*(p+1)+i
            for l in range(p+1):
                for k in range(p+1):
                    b=l*(p+1)+k
                    xx=hy/hx*derivative[i][k]*mass[j][l]
                    yy=hx/hy*mass[i][k]*derivative[j][l]
                    xy=mixed[i][k]*mixed[l][j]
                    yx=mixed[k][i]*mixed[j][l]
                    result[a][b]=thickness*(plane[0][0]*xx+plane[2][2]*yy)
                    result[a+nc][b+nc]=thickness*(plane[1][1]*yy+plane[2][2]*xx)
                    result[a][b+nc]=thickness*(plane[0][1]*xy+plane[2][2]*yx)
                    result[a+nc][b]=thickness*(plane[1][0]*yx+plane[2][2]*xy)
    return tuple(tuple(row) for row in result)


def stiffness(rect,p):
    """Fresh finite binary64 copy of the exactly integrated local Hessian."""
    try: result=np.asarray(stiffness_exact(rect,p),dtype=np.float64)
    except OverflowError as exc:
        raise ValueError('unrepresentable local membrane stiffness') from exc
    if not np.all(np.isfinite(result)):
        raise ValueError('unrepresentable local membrane stiffness')
    return result


def _orders(dx,dy):
    if (type(dx) is not int or type(dy) is not int or dx<0 or dy<0 or dx+dy>2):
        raise ValueError('physical derivative multi-index of total order 0..2 required')


def basis_exact(rect,p,xi,eta,*,dx=0,dy=0):
    """Scalar shape functions or physical derivatives in the exact local chart."""
    _validate(rect,p);_orders(dx,dy)
    if (not poly._coordinate(xi) or not poly._coordinate(eta) or
            not ZERO<=xi<=ONE or not ZERO<=eta<=ONE):
        raise ValueError('exact local coordinates in [0,1] required')
    hx=rect.x1-rect.x0;hy=rect.y1-rect.y0
    bx=tuple(poly._at(_derivative(v,dx),xi)/hx**dx for v in _basis(p))
    by=tuple(poly._at(_derivative(v,dy),eta)/hy**dy for v in _basis(p))
    return tuple(y*x for y in by for x in bx)


def basis(rect,p,xi,eta,*,dx=0,dy=0):
    """Owned (...,(p+1)^2) scalar shapes/physical derivatives, local coordinates."""
    _validate(rect,p);_orders(dx,dy)
    x,y=np.broadcast_arrays(np.asarray(xi,dtype=np.float64),np.asarray(eta,dtype=np.float64))
    if not (np.isfinite(x).all() and np.isfinite(y).all()) or np.any(x<0) or np.any(x>1) or np.any(y<0) or np.any(y>1):
        raise ValueError('finite local coordinates in [0,1] required')
    def axis(value,width,order):
        rows=[]
        for polynomial in _basis(p):
            derivative=tuple(v/width**order for v in _derivative(polynomial,order))
            out=np.zeros(value.shape)
            for coefficient in reversed(derivative):
                try: v=float(coefficient)
                except OverflowError as exc:
                    raise ValueError('unrepresentable local membrane derivative') from exc
                out=out*value+v
            rows.append(out)
        return rows
    bx=axis(x,rect.x1-rect.x0,dx);by=axis(y,rect.y1-rect.y0,dy)
    result=np.stack([a*b for a in by for b in bx],axis=-1)
    if not np.isfinite(result).all():
        raise ValueError('unrepresentable local membrane derivative')
    return result
