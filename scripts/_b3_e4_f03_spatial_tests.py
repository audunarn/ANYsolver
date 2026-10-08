"""Frozen low-order physical virtual fields and independent exact pad moments.

The 27 fields are specified in physical x,y monomials with exact represented
binary64 constants. Neither a Ritz basis nor an area-adjoint implementation
is imported. All station traces are direct square-pad moments of these fields.
"""
from __future__ import annotations

from fractions import Fraction
import math

import numpy as np

from scripts import _b3_e4_f03_spatial_contract as c


Poly = tuple[tuple[int,int,Fraction],...]
StationPoly = tuple[Fraction,...]
_ZERO=Fraction(0)
_ONE=Fraction(1)


def _clean(p: dict[tuple[int,int],Fraction]) -> Poly:
    return tuple((i,j,v) for (i,j),v in sorted(p.items()) if v)


def _add(a: Poly,b: Poly) -> Poly:
    p={(i,j):v for i,j,v in a}
    for i,j,v in b: p[i,j]=p.get((i,j),_ZERO)+v
    return _clean(p)


def _scale(a: Poly,k: Fraction) -> Poly:
    return tuple((i,j,v*k) for i,j,v in a if v*k)


def _mul(a: Poly,b: Poly) -> Poly:
    p:dict[tuple[int,int],Fraction]={}
    for i,j,v in a:
        for k,l,w in b: p[i+k,j+l]=p.get((i+k,j+l),_ZERO)+v*w
    return _clean(p)


def _derivative(a: Poly,axis: int) -> Poly:
    if axis==0: return _clean({(i-1,j):i*v for i,j,v in a if i})
    if axis==1: return _clean({(i,j-1):j*v for i,j,v in a if j})
    raise ValueError('polynomial derivative axis must be 0 or 1')


_UNIT=((0,0,_ONE),)
_X=((1,0,_ONE),)
_Y=((0,1,_ONE),)
_CAP_X=_add(_X,((0,0,Fraction(-1,2)),))
_CAP_Y=_scale(_Y,Fraction(2))


def _legendre_low(argument: Poly,index: int) -> Poly:
    if index==0: return _UNIT
    if index==1: return argument
    if index==2:
        return _scale(_add(_scale(_mul(argument,argument),Fraction(3)),
                           _scale(_UNIT,-_ONE)),Fraction(1,2))
    raise ValueError('only the frozen low-order Legendre tests are admitted')


def _field_inventory() -> tuple[tuple[str,Poly,Poly],...]:
    u=c.Q_U0;rot=u/c.Q_L0
    rigid=(("rigid_tx",_scale(_UNIT,u),()),
           ("rigid_ty",(),_scale(_UNIT,u)),
           ("rigid_rz",_scale(_Y,-rot),_scale(_X,rot)))
    result=list(rigid)
    chi_l=_scale(_add(_scale(_X,-_ONE),((0,0,Fraction(3,2)),)),Fraction(1,2))
    chi_r=_scale(_add(_X,((0,0,Fraction(1,2)),)),Fraction(1,2))
    for side,chi in (("left",chi_l),("right",chi_r)):
        for label,ux,uy in rigid:
            result.append((f'{side}_{label[6:]}',_mul(chi,ux),_mul(chi,uy)))
    support=_add(_UNIT,_scale(_mul(_CAP_X,_CAP_X),-_ONE))
    for component in (0,1):
        for i in range(3):
            for j in range(3):
                p=_scale(_mul(_mul(support,_legendre_low(_CAP_X,i)),
                              _legendre_low(_CAP_Y,j)),u)
                result.append((f'supported_{component}_i{i}_j{j}',
                               p if component==0 else (),
                               p if component==1 else ()))
    return tuple(result)


_INVENTORY=_field_inventory()
FIELD_IDS=tuple(row[0] for row in _INVENTORY)
assert len(FIELD_IDS)==27 and len(set(FIELD_IDS))==27


def _symmetric_moment(centre: Fraction,halfwidth: Fraction,order: int
                      ) -> Fraction:
    if order%2: return _ZERO
    return sum(((side*centre+halfwidth)**(order+1)-
                (side*centre-halfwidth)**(order+1)
                for side in (-1,1)),_ZERO)/(4*halfwidth*(order+1))


def _station_poly(a: Poly,extra_xi: int=0,extra_y: int=0) -> StationPoly:
    """Average xi^extra_xi*y^extra_y*a(s+xi,y) over four squares."""
    degree=max((i for i,_,_ in a),default=0)
    result=[_ZERO]*(degree+1)
    for i,j,value in a:
        ym=_symmetric_moment(c.Q_DY,c.Q_A,j+extra_y)
        for k in range(i+1):
            result[i-k]+=value*math.comb(i,k)*ym*_symmetric_moment(
                c.Q_DX,c.Q_A,k+extra_xi)
    return tuple(result)


def _station_derivative(a: StationPoly) -> StationPoly:
    return tuple((k+1)*a[k+1] for k in range(len(a)-1)) or (_ZERO,)


def _station_subtract(a: StationPoly,b: StationPoly) -> StationPoly:
    return tuple((a[k] if k<len(a) else _ZERO)-
                 (b[k] if k<len(b) else _ZERO)
                 for k in range(max(len(a),len(b))))


_TRACE=tuple((_station_poly(ux),_station_poly(uy),
              tuple(v/c.Q_J for v in _station_subtract(
                  _station_poly(uy,extra_xi=1),
                  _station_poly(ux,extra_y=1))))
             for _,ux,uy in _INVENTORY)
_TRACE_D=tuple(tuple(_station_derivative(p) for p in field)
               for field in _TRACE)


def _coord(x: object,y: object) -> tuple[np.ndarray,np.ndarray]:
    xx,yy=np.broadcast_arrays(np.asarray(x,dtype=np.float64),
                              np.asarray(y,dtype=np.float64))
    if not np.all(np.isfinite(xx)) or not np.all(np.isfinite(yy)):
        raise ValueError('nonfinite virtual-field coordinates')
    if np.any(xx<-.5) or np.any(xx>1.5) or np.any(yy<-.5) or np.any(yy>.5):
        raise ValueError('virtual field outside physical panel')
    return xx,yy


def _value(poly: Poly,x: np.ndarray,y: np.ndarray) -> np.ndarray:
    return sum((float(v)*x**i*y**j for i,j,v in poly),
               np.zeros(x.shape,dtype=np.float64))


def fields(x: object,y: object) -> dict[str,np.ndarray]:
    """All values (...,27,2) and engineering strains (...,27,3)."""
    xx,yy=_coord(x,y)
    displacement=np.stack([np.stack((_value(ux,xx,yy),_value(uy,xx,yy)),axis=-1)
                           for _,ux,uy in _INVENTORY],axis=-2)
    strain=np.stack([np.stack((_value(_derivative(ux,0),xx,yy),
                              _value(_derivative(uy,1),xx,yy),
                              _value(_add(_derivative(ux,1),
                                          _derivative(uy,0)),xx,yy)),axis=-1)
                     for _,ux,uy in _INVENTORY],axis=-2)
    if not np.all(np.isfinite(displacement)) or not np.all(np.isfinite(strain)):
        raise ValueError('nonfinite virtual field')
    return {'values':displacement,'strain':strain}


def _station_value(poly: StationPoly,s: np.ndarray) -> np.ndarray:
    result=np.zeros(s.shape,dtype=np.float64)
    for coefficient in reversed(poly): result=result*s+float(coefficient)
    return result


def trace(s: object) -> dict[str,np.ndarray]:
    """Direct exact pad moments and physical-station derivatives of all tests."""
    ss=np.asarray(s,dtype=np.float64)
    if not np.all(np.isfinite(ss)) or np.any(ss<0) or np.any(ss>c.L0):
        raise ValueError('trace outside beam station')
    value=np.stack([np.stack([_station_value(p,ss) for p in row],axis=-1)
                    for row in _TRACE],axis=-2)
    deriv=np.stack([np.stack([_station_value(p,ss) for p in row],axis=-1)
                    for row in _TRACE_D],axis=-2)
    if not np.all(np.isfinite(value)) or not np.all(np.isfinite(deriv)):
        raise ValueError('nonfinite direct trace')
    return {'values':value,'derivative':deriv}


def _pair(v: Fraction) -> list[str]:
    return [str(v.numerator),str(v.denominator)]


def definition_record() -> dict:
    """Lossless, fixed-order definition for immutable source registration."""
    return {
        'schema':'represented_spatial_virtual_fields_v1',
        'field_ids':list(FIELD_IDS),
        'geometry':{'dx':_pair(c.Q_DX),'dy':_pair(c.Q_DY),
                    'a':_pair(c.Q_A),'held_J':_pair(c.Q_J),
                    'gamma':_pair(c.Q_GAMMA)},
        'test_scale':{'translation_m':_pair(c.Q_U0),
                      'rotation':_pair(c.Q_U0/c.Q_L0)},
        'monomial_order':'ascending (x_power,y_power) in physical panel metres',
        'trace_order':'ascending station powers s^k; yaw is physical radians',
        'fields':[
            {'id':name,
             'components':[[[i,j,*_pair(v)] for i,j,v in p]
                           for p in (ux,uy)],
             'trace':[[ _pair(v) for v in p] for p in _TRACE[k]],
             'trace_derivative':[[ _pair(v) for v in p] for p in _TRACE_D[k]]}
            for k,(name,ux,uy) in enumerate(_INVENTORY)],
    }
