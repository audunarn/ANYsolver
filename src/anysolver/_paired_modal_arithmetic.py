"""Private paired-vector arithmetic; no beam mechanics or public routing."""
from math import fsum, sqrt
import numpy as np
from ._native_relative_factor_chain_modes import mm, dot_terms
from ._dyadic_bilinear import _capture, _multiply, _transpose, _add, _rounded


def orthogonal_coordinates(c, mass, checkpoint=lambda: None):
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


def _pair(high,low,checkpoint):
    if (np.shape(high)!=np.shape(low) or np.ndim(high)!=2
            or not 1<=high.shape[0]<=256 or not 1<=high.shape[1]<=256):
        raise ValueError('bounded matching explicit mode halves required')
    return _add(_capture(high,checkpoint),_capture(low,checkpoint))


def paired_expansion(mapping, coordinates, checkpoint=lambda: None):
    exact=_multiply(_capture(mapping,checkpoint),_capture(coordinates,checkpoint),checkpoint)
    high=_rounded(exact)
    low=_rounded(_add(exact,_capture(-high,checkpoint)))
    return high,low


def paired_map(operator,high,low,checkpoint=lambda:None):
    if np.ndim(operator)!=2 or not 1<=len(operator)<=8192:
        raise ValueError('bounded paired action required')
    return _rounded(_multiply(_capture(operator,checkpoint),_pair(high,low,checkpoint),checkpoint))


def paired_actions(left,right,g,b,high,low,values,checkpoint=lambda:None):
    """Original signed actions/congruences, with no collapsed vector input."""
    def cap(a):return _capture(a,checkpoint)
    def mul(a,b):return _multiply(a,b,checkpoint)
    v=_pair(high,low,checkpoint)
    ll,rr,gg,bb=map(cap,(left,right,g,b))
    strain=mul(ll,mul(rr,v));speed=mul(bb,v)
    material=mul(_transpose(rr),mul(_transpose(ll),strain))
    geometric=mul(gg,v);inertia=mul(_transpose(bb),speed)
    signed=_add(material,geometric)
    h=_rounded(_add(mul(_transpose(strain),strain),mul(_transpose(v),geometric)))
    mass=_rounded(mul(_transpose(speed),speed))
    residual=_rounded(_add(signed,mul(inertia,cap(-np.diag(values)))))
    return h,mass,residual,_rounded(material),_rounded(geometric),_rounded(inertia)
