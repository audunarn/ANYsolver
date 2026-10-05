"""Exact local Qp pad moments on axis-aligned rational rectangles (p=1..3).

The pad and material constants are the frozen represented-binary64 classical
fixture. Distinct rational station events remain distinct even when they
convert to the same binary64 number. This is a pure local operator, not a
mesh, shell/beam assembly, equilibrium solve or native product element.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np

from scripts import _b3_e4_f03_spatial_contract as c


ZERO=Fraction(0)
ONE=Fraction(1)
Poly=tuple[Fraction,...]
COORDINATE_BITS=256
TRACE_COEFFICIENT_BITS=8192
TRACE_TOTAL_BITS=2_000_000


def _coordinate(value):
    return (type(value) is Fraction and
            value.numerator.bit_length()<=COORDINATE_BITS and
            value.denominator.bit_length()<=COORDINATE_BITS)


def _add(a: Poly,b: Poly) -> Poly:
    return tuple((a[k] if k<len(a) else ZERO)+
                 (b[k] if k<len(b) else ZERO)
                 for k in range(max(len(a),len(b))))


def _scale(a: Poly,value: Fraction) -> Poly:
    return tuple(value*v for v in a)


def _sub(a: Poly,b: Poly) -> Poly:
    return _add(a,_scale(b,-ONE))


def _mul(a: Poly,b: Poly) -> Poly:
    result=[ZERO]*(len(a)+len(b)-1)
    for i,v in enumerate(a):
        for j,w in enumerate(b): result[i+j]+=v*w
    return tuple(result)


def _primitive(a: Poly) -> Poly:
    return (ZERO,)+tuple(v/(i+1) for i,v in enumerate(a))


def _at(a: Poly,value: Fraction) -> Fraction:
    total=ZERO
    for coefficient in reversed(a): total=total*value+coefficient
    return total


def _compose(a: Poly,affine: Poly) -> Poly:
    total=(ZERO,)
    for coefficient in reversed(a):
        total=_add(_mul(total,affine),(coefficient,))
    while len(total)>1 and total[-1]==0:
        total=total[:-1]
    return total


def _integral_poly(poly: Poly,low: Fraction,high: Fraction) -> Fraction:
    primitive=_primitive(poly)
    return _at(primitive,high)-_at(primitive,low)


def _lagrange(a: Fraction,b: Fraction,p: int) -> tuple[Poly,...]:
    nodes=tuple(a+(b-a)*Fraction(i,p) for i in range(p+1))
    result=[]
    for j,node in enumerate(nodes):
        polynomial=(ONE,)
        for k,other in enumerate(nodes):
            if k!=j:
                polynomial=_mul(polynomial,
                                (-other/(node-other),ONE/(node-other)))
        result.append(polynomial)
    return tuple(result)


@dataclass(frozen=True,slots=True)
class Rectangle:
    x0: Fraction
    x1: Fraction
    y0: Fraction
    y1: Fraction

    def __post_init__(self) -> None:
        if (any(not _coordinate(v) for v in
                (self.x0,self.x1,self.y0,self.y1)) or
            not Fraction(-1,2)<=self.x0<self.x1<=Fraction(3,2) or
            not Fraction(-1,2)<=self.y0<self.y1<=Fraction(1,2)):
            raise ValueError('positive physical Fraction rectangle required')


def station_events(rect: Rectangle) -> tuple[Fraction,...]:
    """Exact deduplicated beam events, including both endpoints 0 and 1."""
    if not isinstance(rect,Rectangle): raise ValueError('invalid rectangle')
    events={ZERO,c.Q_L0}
    for x in (rect.x0,rect.x1):
        for l,r,_,_ in c.PADS:
            for edge in (l,r):
                value=x-edge
                if ZERO<value<c.Q_L0:
                    if not _coordinate(value):
                        raise ValueError('derived exact station exceeds coordinate bit bound')
                    events.add(value)
    return tuple(sorted(events))


@dataclass(frozen=True,slots=True)
class LocalTrace:
    rect: Rectangle
    p: int
    s0: Fraction
    s1: Fraction
    # channel(translation-x, translation-y, physical yaw), then
    # component/y-index/x-index, then ascending powers of local tau.
    coefficients: tuple[tuple[Poly,...],...]

    def __post_init__(self) -> None:
        if (not isinstance(self.rect,Rectangle) or type(self.p) is not int or
                self.p not in (1,2,3) or not _coordinate(self.s0) or
                not _coordinate(self.s1) or
                not ZERO<=self.s0<self.s1<=c.Q_L0):
            raise ValueError('invalid immutable local trace domain')
        if any(self.s0<event<self.s1 for event in station_events(self.rect)):
            raise ValueError('interior exact pad/cell event in local trace')
        source=self.coefficients
        if type(source) not in (tuple,list) or len(source)!=3:
            raise ValueError('invalid local trace channel layout')
        copied=[];total_bits=0
        for channel in source:
            if type(channel) not in (tuple,list) or len(channel)!=self.dof_count:
                raise ValueError('invalid local trace DOF layout')
            rows=[]
            for polynomial in channel:
                if (type(polynomial) not in (tuple,list) or
                        len(polynomial)!=self.p+3 or
                        any(type(v) is not Fraction for v in polynomial)):
                    raise ValueError('invalid exact local trace coefficients')
                for value in polynomial:
                    bits=(value.numerator.bit_length(),value.denominator.bit_length())
                    total_bits+=sum(bits)
                    if max(bits)>TRACE_COEFFICIENT_BITS or total_bits>TRACE_TOTAL_BITS:
                        raise ValueError('local trace rational storage bound exceeded')
                rows.append(tuple(polynomial))
            copied.append(tuple(rows))
        object.__setattr__(self,'coefficients',tuple(copied))

    @property
    def dof_count(self) -> int:
        return 2*(self.p+1)**2

    def evaluate_exact(self,tau: Fraction,order: int=0
                       ) -> tuple[tuple[Fraction,...],...]:
        if (not _coordinate(tau) or not ZERO<=tau<=ONE or
                type(order) is not int or order not in (0,1,2)):
            raise ValueError('local tau Fraction and derivative order 0..2 required')
        h=self.s1-self.s0
        return tuple(tuple(sum((coefficient[k]*
                       Fraction(math.factorial(k),math.factorial(k-order))*
                       tau**(k-order) for k in range(order,len(coefficient))),ZERO)
                       /h**order for coefficient in row)
                     for row in self.coefficients)

    def evaluate(self,tau: object,order: int=0) -> np.ndarray:
        """Owned finite (...,3,dof) physical-station derivative array."""
        if type(order) is not int or order not in (0,1,2):
            raise ValueError('local derivative order must be integer 0..2')
        value=np.asarray(tau,dtype=np.float64)
        if not np.all(np.isfinite(value)) or np.any(value<0) or np.any(value>1):
            raise ValueError('evaluation needs finite local tau in [0,1]')
        h=self.s1-self.s0
        result=np.empty(value.shape+(3,self.dof_count),dtype=np.float64)
        for channel,row in enumerate(self.coefficients):
            for dof,poly in enumerate(row):
                derivative=tuple(poly[k]*
                    Fraction(math.factorial(k),math.factorial(k-order))/h**order
                    for k in range(order,len(poly)))
                acc=np.zeros(value.shape,dtype=np.float64)
                for coefficient in reversed(derivative):
                    try: converted=float(coefficient)
                    except OverflowError as exc:
                        raise ValueError('unrepresentable local moment coefficient') from exc
                    acc=acc*value+converted
                result[...,channel,dof]=acc
        if not np.all(np.isfinite(result)):
            raise ValueError('unrepresentable local moment evaluation')
        return result


def trace_segment(rect: Rectangle,p: int,s0: Fraction,s1: Fraction) -> LocalTrace:
    """Exact square-pad pose restricted to one unbroken station interval."""
    if (not isinstance(rect,Rectangle) or type(p) is not int or p not in (1,2,3)
            or not _coordinate(s0) or not _coordinate(s1) or
            not ZERO<=s0<s1<=c.Q_L0):
        raise ValueError('invalid bounded local cell, degree or station interval')
    if any(s0<event<s1 for event in station_events(rect)):
        raise ValueError('interior exact pad/cell event requires interval split')
    h=s1-s0;mid=(s0+s1)/2
    px=_lagrange(rect.x0,rect.x1,p)
    py=_lagrange(rect.y0,rect.y1,p)
    dof=2*(p+1)**2;degree=p+3
    coefficients=[[[ZERO]*degree for _ in range(dof)] for _ in range(3)]
    def accumulate(channel: int,index: int,poly: Poly,factor: Fraction) -> None:
        for power,value in enumerate(poly):
            if power>=degree:
                if value: raise ArithmeticError('local pad moment exceeds proven degree')
                continue
            coefficients[channel][index][power]+=value*factor
    for l,r,yl,yh in c.PADS:
        y0=max(rect.y0,yl);y1=min(rect.y1,yh)
        if y0>=y1: continue
        if max(rect.x0,mid+l)>=min(rect.x1,mid+r): continue
        lo=(rect.x0,) if rect.x0>mid+l else (s0+l,h)
        hi=(rect.x1,) if rect.x1<mid+r else (s0+r,h)
        for j,yp in enumerate(py):
            yint=_integral_poly(yp,y0,y1)
            ymom=_integral_poly(_mul(yp,(ZERO,ONE)),y0,y1)
            for i,xp in enumerate(px):
                xint=_sub(_compose(_primitive(xp),hi),
                          _compose(_primitive(xp),lo))
                xmom=_sub(_compose(_primitive(_mul(xp,(ZERO,ONE))),hi),
                          _compose(_primitive(_mul(xp,(ZERO,ONE))),lo))
                xrelative=_sub(xmom,_mul((s0,h),xint))
                index=j*(p+1)+i
                accumulate(0,index,xint,yint/c.Q_AREA)
                accumulate(2,index,xint,-ymom/(c.Q_J*c.Q_AREA))
                index+=(p+1)**2
                accumulate(1,index,xint,yint/c.Q_AREA)
                accumulate(2,index,xrelative,yint/(c.Q_J*c.Q_AREA))
    frozen=tuple(tuple(tuple(v for v in poly) for poly in row)
                 for row in coefficients)
    return LocalTrace(rect,p,s0,s1,frozen)
