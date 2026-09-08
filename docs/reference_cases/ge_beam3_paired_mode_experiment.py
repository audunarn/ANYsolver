"""Saved-factor numerical experiment; no production modal API or qualification."""
from math import fsum, sqrt
import numpy as np
from anysolver._native_relative_factor_chain_modes import mm, dot_terms
from anysolver._dyadic_bilinear import _capture, _multiply, _transpose, _add, _rounded


def orthogonal_coordinates(c, mass, checkpoint=lambda: None):
    """Ordered twice-reorthogonalized kinetic-metric Gram-Schmidt.

    No root replacement, subspace truncation or change of physical inertia.
    The complete resulting family must pass original-chain work checks.
    """
    result=np.array(c, copy=True)
    for j in range(result.shape[1]):
        v=result[:, j].copy()
        for _ in range(2):
            for i in range(j):
                checkpoint()
                mv=mm(mass, v[:, None], checkpoint)[:, 0]
                projection=fsum(dot_terms(result[:, i], mv))
                v=np.array([fsum([float(x), *dot_terms([-projection], [y])])
                            for x,y in zip(v,result[:, i])])
        mv=mm(mass, v[:, None], checkpoint)[:, 0]
        norm=fsum(dot_terms(v,mv))
        if not np.isfinite(norm) or norm<=0:
            raise ValueError('positive independent kinetic coordinate required')
        result[:, j]=v/sqrt(norm)
    return result


def paired_expansion(mapping, coordinates, checkpoint=lambda: None):
    exact=_multiply(_capture(mapping,checkpoint),_capture(coordinates,checkpoint),checkpoint)
    high=_rounded(exact)
    low=_rounded(_add(exact,_capture(-high,checkpoint)))
    return high,low


def audit_pair(data, high, low, checkpoint=lambda: None):
    def cap(a):return _capture(a,checkpoint)
    def mul(a,b):return _multiply(a,b,checkpoint)
    v=_add(cap(high),cap(low))
    strain=mul(cap(data['left']),mul(cap(data['right']),v))
    speed=mul(cap(data['b']),v)
    h=_rounded(_add(mul(_transpose(strain),strain),mul(_transpose(v),mul(cap(data['g']),v))))
    m=_rounded(mul(_transpose(speed),speed))
    values=data['values']
    scale=np.maximum(1.,np.sqrt(abs(values))[:,None]*np.sqrt(abs(values))[None,:])
    return dict(energy=h,kinetic_gram=m,
        mass_error=float(np.linalg.norm(m-np.eye(len(values)))),
        original_ritz_error=float(np.max(abs(h-m*values[None,:])/scale)))


def experiment(data, checkpoint=lambda: None):
    c=orthogonal_coordinates(data['c'],data['mass'],checkpoint)
    high,low=paired_expansion(data['mapping'],c,checkpoint)
    paired=audit_pair(data,high,low,checkpoint)
    rounded=audit_pair(data,high,np.zeros_like(low),checkpoint)
    return dict(coordinates=c,high=high,low=low,eigenvalues=data['values'],
                paired=paired,rounded_only=rounded,production_qualified=False,
                independent_review='PENDING')
