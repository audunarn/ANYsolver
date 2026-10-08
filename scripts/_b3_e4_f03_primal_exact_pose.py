"""Pure rational reconstruction of the classical four-pad Ritz pose.

This diagnostic integrates the mathematical polynomial defined by exact
lifts of saved binary64 bits. It neither mimics floating Gauss arithmetic
nor constructs a shell/beam operator or solves an equilibrium problem.
Only the represented binary64 geometry stream is admitted here.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import math
import re

import numpy as np


DX=Fraction.from_float(.2)
DY=Fraction.from_float(.23)
A=Fraction.from_float(.05)
_HELD_J_FLOAT=.2**2+.23**2+2*.05**2/3
HELD_J=Fraction.from_float(_HELD_J_FLOAT)
SCHEMA='represented_binary64_exact_pose_v1'
STATIONS=tuple(Fraction(k,8) for k in range(9))
_ZERO=Fraction(0)
_ONE=Fraction(1)


@dataclass(frozen=True)
class ExactPose:
    n: int
    q: tuple[Fraction,...]
    dx: Fraction
    dy: Fraction
    a: Fraction
    held_J: Fraction
    J_geom: Fraction
    gamma: Fraction
    tau_power: tuple[tuple[Fraction,...],...]
    legendre: tuple[tuple[Fraction,...],...]


@dataclass(frozen=True)
class CoefficientBound:
    signed: Fraction
    triangle: Fraction
    weights: tuple[Fraction,...]


@dataclass(frozen=True)
class Discrepancy:
    total: Fraction
    floating_polynomial: Fraction
    coefficient_reconstruction: Fraction
    direct_action: Fraction


def _degree(n: int) -> int:
    if type(n) is not int or not 2<=n<=24:
        raise ValueError('exact pose degree must be integer 2..24')
    return n


def _binary64(value: object) -> Fraction:
    if type(value) not in (float,np.float64) or not math.isfinite(value):
        raise ValueError('exact lift requires finite binary64 scalar')
    return Fraction.from_float(float(value))


def _q(n: int,q: np.ndarray) -> tuple[Fraction,...]:
    if (not isinstance(q,np.ndarray) or q.dtype!=np.float64 or
            q.shape!=(2*(n*n-1),) or not np.all(np.isfinite(q))):
        raise ValueError('invalid finite binary64 Ritz coefficient vector')
    return tuple(Fraction.from_float(float(value)) for value in q)


def _add(first: tuple[Fraction,...],second: tuple[Fraction,...]
         ) -> tuple[Fraction,...]:
    result=[_ZERO]*max(len(first),len(second))
    for i,value in enumerate(first): result[i]+=value
    for i,value in enumerate(second): result[i]+=value
    return tuple(result)


def _scale(poly: tuple[Fraction,...],number: Fraction
           ) -> tuple[Fraction,...]:
    return tuple(number*value for value in poly)


def _multiply(first: tuple[Fraction,...],second: tuple[Fraction,...]
              ) -> tuple[Fraction,...]:
    result=[_ZERO]*(len(first)+len(second)-1)
    for i,a in enumerate(first):
        for j,b in enumerate(second): result[i+j]+=a*b
    return tuple(result)


def _legendre_powers(n: int) -> tuple[tuple[Fraction,...],...]:
    result=[(_ONE,),(_ZERO,_ONE)]
    for i in range(1,n):
        numerator=_add(_scale((_ZERO,)+result[i],Fraction(2*i+1)),
                       _scale(result[i-1],Fraction(-i)))
        result.append(_scale(numerator,Fraction(1,i+1)))
    return tuple(result[:n+1])


def _moment(centre: Fraction,halfwidth: Fraction,power: int) -> Fraction:
    if power%2: return _ZERO
    total=_ZERO
    for centre_signed in (-centre,centre):
        left=centre_signed-halfwidth;right=centre_signed+halfwidth
        total+=(right**(power+1)-left**(power+1))
    return total/(4*halfwidth*(power+1))


def _average_shift(poly: tuple[Fraction,...],centre: Fraction,
                   halfwidth: Fraction,extra_power: int
                   ) -> tuple[Fraction,...]:
    return tuple(sum((poly[r]*math.comb(r,k)*
                     _moment(centre,halfwidth,r-k+extra_power)
                     for r in range(k,len(poly))),_ZERO)
                 for k in range(len(poly)))


def _power_to_legendre(tau: tuple[Fraction,...],
                       polynomials: tuple[tuple[Fraction,...],...]
                       ) -> tuple[Fraction,...]:
    # Beam x=2s-1=2*tau; triangular elimination avoids any sampled fit.
    residual=[value/Fraction(2**k) for k,value in enumerate(tau)]
    result=[_ZERO]*len(tau)
    for degree in range(len(tau)-1,-1,-1):
        polynomial=polynomials[degree]
        coefficient=residual[degree]/polynomial[degree]
        result[degree]=coefficient
        for k,value in enumerate(polynomial):
            residual[k]-=coefficient*value
    if any(residual):
        raise ArithmeticError('exact Legendre elimination did not close')
    return tuple(result)


def reconstruct(n: int,q: np.ndarray) -> ExactPose:
    """Integrate four represented binary64 pads in exact rational arithmetic."""
    _degree(n);values=_q(n,q)
    polynomials=_legendre_powers(n)
    vertical=[sum((coefficient*2**r*_moment(DY,A,r)
                   for r,coefficient in enumerate(polynomials[j])),_ZERO)
              for j in range(n+1)]
    vertical_first=[sum((coefficient*2**r*_moment(DY,A,r+1)
                         for r,coefficient in enumerate(polynomials[j])),_ZERO)
                    for j in range(n+1)]
    b=[];c=[]
    for i in range(n-1):
        scalar=_multiply((_ONE,_ZERO,-_ONE),polynomials[i])
        b.append(_average_shift(scalar,DX,A,0))
        c.append(_average_shift(scalar,DX,A,1))
    m=n*n-1
    channels=[[_ZERO]*(n+1) for _ in range(3)]
    for i in range(n-1):
        for j in range(n+1):
            index=i*(n+1)+j
            ux=values[index];uy=values[m+index]
            for power in range(len(b[i])):
                channels[0][power]+=ux*vertical[j]*b[i][power]
                channels[1][power]+=uy*vertical[j]*b[i][power]
                channels[2][power]+=(uy*vertical[j]*c[i][power]-
                                      ux*vertical_first[j]*b[i][power])/HELD_J
    tau=tuple(tuple(channel) for channel in channels)
    legendre=tuple(_power_to_legendre(channel,polynomials)
                   for channel in tau)
    j_geom=_moment(DX,A,2)+_moment(DY,A,2)
    return ExactPose(n,values,DX,DY,A,HELD_J,j_geom,j_geom/HELD_J,
                     tau,legendre)


def _derivative(poly: tuple[Fraction,...],order: int
                ) -> tuple[Fraction,...]:
    for _ in range(order):
        poly=tuple((i+1)*poly[i+1] for i in range(len(poly)-1))
    return poly


def _value(poly: tuple[Fraction,...],at: Fraction) -> Fraction:
    result=_ZERO
    for coefficient in reversed(poly): result=result*at+coefficient
    return result


def station_derivatives(pose: ExactPose
                        ) -> tuple[tuple[tuple[Fraction,...],...],...]:
    """Orders 0,1,2; nine rational stations; channels u,v,theta."""
    return tuple(tuple(tuple(_value(_derivative(pose.tau_power[channel],order),
                                    station-Fraction(1,2))
                             for channel in range(3))
                       for station in STATIONS)
                 for order in range(3))


def station_derivatives_legendre(pose: ExactPose
                                 ) -> tuple[tuple[tuple[Fraction,...],...],...]:
    """Independently differentiate the exact x=2s-1 Legendre expansion."""
    if not isinstance(pose,ExactPose):
        raise ValueError('invalid exact pose')
    powers=_legendre_powers(pose.n)
    return tuple(tuple(tuple(sum((pose.legendre[channel][j]*2**order*
            _value(_derivative(powers[j],order),2*station-1)
            for j in range(pose.n+1)),_ZERO)
            for channel in range(3)) for station in STATIONS)
        for order in range(3))


def _saved_coefficients(n: int,coefficients: np.ndarray
                        ) -> tuple[tuple[Fraction,...],...]:
    if (not isinstance(coefficients,np.ndarray) or
            coefficients.dtype!=np.float64 or
            coefficients.shape!=(n+1,3) or
            not np.all(np.isfinite(coefficients))):
        raise ValueError('invalid saved binary64 Legendre coefficients')
    return tuple(tuple(Fraction.from_float(float(coefficients[j,channel]))
                       for j in range(n+1)) for channel in range(3))


def _arguments(pose: ExactPose,channel: int,order: int,station: int) -> None:
    if (not isinstance(pose,ExactPose) or type(channel) is not int or
            not 0<=channel<3 or type(order) is not int or
            not 0<=order<=2 or type(station) is not int or
            not 0<=station<=8):
        raise ValueError('invalid bounded pose channel, derivative or station')


def _endpoint_weight(degree: int,order: int,endpoint: int) -> Fraction:
    if order==0: return Fraction((-1)**degree if endpoint==0 else 1)
    if order==1:
        return Fraction(degree*(degree+1)*(
            (-1)**(degree+1) if endpoint==0 else 1))
    if degree<2: return _ZERO
    return Fraction((degree-1)*degree*(degree+1)*(degree+2),2)*(
        (-1)**degree if endpoint==0 else 1)


def endpoint_coefficient_bound(coefficients: np.ndarray,pose: ExactPose,
                               channel: int,order: int,endpoint: int
                               ) -> CoefficientBound:
    """Exact signed endpoint coefficient term and its triangle enclosure.

    Physical s derivatives use L=1 m. Theta stays angular; a caller
    converting its discrepancy to a length multiplies by ell=.46 once.
    """
    if type(endpoint) is not int or endpoint not in (0,1):
        raise ValueError('endpoint must be 0 or 1')
    _arguments(pose,channel,order,8*endpoint)
    saved=_saved_coefficients(pose.n,coefficients)[channel]
    weights=tuple(_endpoint_weight(j,order,endpoint)
                  for j in range(pose.n+1))
    terms=tuple(weights[j]*(saved[j]-pose.legendre[channel][j])
                for j in range(pose.n+1))
    return CoefficientBound(sum(terms,_ZERO),sum(map(abs,terms),_ZERO),
                            weights)


def _saved_polynomial_derivative(coefficients: tuple[Fraction,...],
                                 order: int,station: int) -> Fraction:
    polynomials=_legendre_powers(len(coefficients)-1)
    x=2*STATIONS[station]-1
    return sum((coefficient*2**order*
                _value(_derivative(polynomials[j],order),x)
                for j,coefficient in enumerate(coefficients)),_ZERO)


def decompose_discrepancy(coefficients: np.ndarray,pose: ExactPose,
                          channel: int,order: int,station: int,
                          floating_polynomial: float,
                          floating_direct: float) -> Discrepancy:
    """Three exact signed terms from externally preserved floating outputs.

    This does not evaluate the original floating algorithm or replace its
    subtraction, angular scaling and normalization in a future audit.
    """
    _arguments(pose,channel,order,station)
    saved=_saved_coefficients(pose.n,coefficients)[channel]
    p_float=_binary64(floating_polynomial)
    d_float=_binary64(floating_direct)
    p_saved=_saved_polynomial_derivative(saved,order,station)
    p_oracle=_value(_derivative(pose.tau_power[channel],order),
                    STATIONS[station]-Fraction(1,2))
    terms=(p_float-p_saved,p_saved-p_oracle,p_oracle-d_float)
    total=p_float-d_float
    if sum(terms,_ZERO)!=total:
        raise ArithmeticError('exact three-term discrepancy did not close')
    return Discrepancy(total,*terms)


def _pair(value: Fraction) -> list[str]:
    return [str(value.numerator),str(value.denominator)]


def to_record(pose: ExactPose) -> dict:
    """Lossless pose subset (8MiB); whole attribution case cap is 16MiB."""
    if (not isinstance(pose,ExactPose) or type(pose.n) is not int or
            not 2<=pose.n<=24 or len(pose.q)!=2*(pose.n*pose.n-1) or
            len(pose.tau_power)!=3 or len(pose.legendre)!=3 or
            any(len(row)!=pose.n+1 for row in
                (*pose.tau_power,*pose.legendre))):
        raise ValueError('invalid exact pose record dimensions')
    values=(*pose.q,*pose.tau_power[0],*pose.tau_power[1],
            *pose.tau_power[2],*pose.legendre[0],*pose.legendre[1],
            *pose.legendre[2],pose.dx,pose.dy,pose.a,pose.held_J,
            pose.J_geom,pose.gamma)
    if (len(values)>2048 or any(type(value) is not Fraction or
            len(str(value.numerator))>4096 or
            len(str(value.denominator))>4096 for value in values)):
        raise ValueError('exact pose record exceeds canonical rational bound')
    record={'schema':SCHEMA,'n':pose.n,
        'geometry':{key:_pair(getattr(pose,key)) for key in
                    ('dx','dy','a','held_J','J_geom','gamma')},
        'q':[_pair(value) for value in pose.q],
        'tau_power':[[_pair(value) for value in row]
                     for row in pose.tau_power],
        'legendre':[[_pair(value) for value in row]
                    for row in pose.legendre]}
    if len(json.dumps(record,allow_nan=False).encode('utf-8'))>8*1024**2:
        raise ValueError('exact pose subset exceeds 8MiB')
    return record


def from_record(record: dict) -> ExactPose:
    """Parse canonical decimal fraction pairs, then reconstruct and compare."""
    if (type(record) is not dict or
            set(record)!={'schema','n','geometry','q','tau_power','legendre'} or
            record['schema']!=SCHEMA):
        raise ValueError('invalid represented exact pose record')
    n=_degree(record['n'])
    def parse(pair: object) -> Fraction:
        if (type(pair) not in (list,tuple) or len(pair)!=2 or
                any(type(part) is not str or len(part)>4096 or
                    re.fullmatch(r'(?:0|-?[1-9][0-9]*)',part) is None
                    for part in pair)):
            raise ValueError('invalid exact rational pair')
        denominator=int(pair[1]);numerator=int(pair[0])
        if denominator<=0:
            raise ValueError('nonpositive exact rational denominator')
        value=Fraction(numerator,denominator)
        if _pair(value)!=list(pair):
            raise ValueError('noncanonical exact rational pair')
        return value
    raw_q=record['q']
    if type(raw_q) is not list or len(raw_q)!=2*(n*n-1):
        raise ValueError('invalid exact pose coefficient count')
    geometry=record['geometry']
    if (type(geometry) is not dict or set(geometry)!=
            {'dx','dy','a','held_J','J_geom','gamma'}):
        raise ValueError('invalid exact pose geometry inventory')
    for pair in geometry.values(): parse(pair)
    for key in ('tau_power','legendre'):
        rows=record[key]
        if (type(rows) is not list or len(rows)!=3 or
                any(type(row) is not list or len(row)!=n+1 for row in rows)):
            raise ValueError(f'invalid exact pose {key} dimensions')
        for row in rows:
            for pair in row: parse(pair)
    if len(raw_q)+6+6*(n+1)>2048:
        raise ValueError('too many exact pose rational pairs')
    fractions=[parse(pair) for pair in raw_q]
    if len(json.dumps(record,allow_nan=False).encode('utf-8'))>8*1024**2:
        raise ValueError('exact pose subset exceeds 8MiB')
    try:
        q=np.array([float(value) for value in fractions],dtype=np.float64)
    except OverflowError as exc:
        raise ValueError('invalid binary64 exact pose coefficients') from exc
    if (not np.all(np.isfinite(q)) or
            any(Fraction.from_float(float(q[i]))!=value
                for i,value in enumerate(fractions))):
        raise ValueError('exact pose coefficient was not a binary64 lift')
    oracle=reconstruct(n,q)
    if record!=to_record(oracle):
        raise ValueError('inconsistent represented exact pose record')
    return oracle
