"""Exact supplied-binary64 factor-chain congruence, rounded once per entry."""
import numpy as np
from ._dyadic_bilinear import _capture, _multiply, _transpose, _add, _rounded


def reassemble_chain_exact_binary64(left,right,g,b,mapping,checkpoint=lambda:None):
    if (np.ndim(mapping)!=2 or not 1<=mapping.shape[0]<=256 or not 1<=mapping.shape[1]<=256
            or np.ndim(left)!=2 or not 1<=len(left)<=8192
            or np.ndim(right)!=2 or not 1<=len(right)<=512 or left.shape[1]!=len(right)
            or right.shape[1]!=mapping.shape[0] or np.ndim(b)!=2 or not 1<=len(b)<=8192
            or b.shape[1]!=mapping.shape[0] or np.shape(g)!=(mapping.shape[0],)*2):
        raise ValueError('bounded matching factor-chain dimensions')
    ll,rr,gg,bb,v=(_capture(x,checkpoint) for x in (left,right,g,b,mapping))
    strain=_multiply(ll,_multiply(rr,v,checkpoint),checkpoint)
    speed=_multiply(bb,v,checkpoint)
    material=_multiply(_transpose(strain),strain,checkpoint)
    geometric=_multiply(_transpose(v),_multiply(gg,v,checkpoint),checkpoint)
    mass=_multiply(_transpose(speed),speed,checkpoint)
    checkpoint()
    return _rounded(_add(material,geometric)),_rounded(mass)
