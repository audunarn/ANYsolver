"""Piecewise physical interface functional and full-H1 Green dual norm.

This pure postprocessor has no equilibrium, mesh, element or old norm helper.
The three density channels are local-station polynomials plus a common
represented-frequency cosine; endpoint atoms are independent measures.
Physical yaw moment is divided by held ell exactly once for the norm.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import _b3_e4_f03_spatial_contract as c


ZERO=Fraction(0)
ONE=Fraction(1)
ELL=Fraction.from_float(.46)
INPUT_INTERVALS=2048
UNION_INTERVALS=4095
INPUT_INTEGER_BITS=4096
DERIVED_INTEGER_BITS=8192
TOTAL_INTEGER_BITS=32_000_000
POLY_LENGTH=6
RESOLUTION_LIMIT=1e-10
NORM_FLOOR_SQUARED=1000.**2


def _copy_validate(cuts,coefficients,cosine,atoms,max_intervals,bit_limit):
    if (type(cuts) not in (tuple,list) or not 2<=len(cuts)<=max_intervals+1 or
            type(coefficients) not in (tuple,list) or
            len(coefficients)!=len(cuts)-1 or
            type(cosine) not in (tuple,list) or len(cosine)!=3 or
            type(atoms) not in (tuple,list) or len(atoms)!=2):
        raise ValueError('invalid bounded piecewise functional inventory')
    total_bits=0
    def rational(v):
        nonlocal total_bits
        if type(v) is not Fraction:
            raise ValueError('piecewise functional needs exact Fraction values')
        numerator=v.numerator.bit_length();denominator=v.denominator.bit_length()
        if numerator>bit_limit or denominator>bit_limit:
            raise ValueError('piecewise functional rational integer bit cap exceeded')
        total_bits+=numerator+denominator
        if total_bits>TOTAL_INTEGER_BITS:
            raise ValueError('piecewise functional aggregate bit cap exceeded')
        return v
    cc=tuple(rational(v) for v in cuts)
    if cc[0]!=ZERO or cc[-1]!=ONE or any(a>=b for a,b in zip(cc,cc[1:])):
        raise ValueError('positive exact station partition 0..1 required')
    rows=[]
    for interval in coefficients:
        if type(interval) not in (tuple,list) or len(interval)!=3:
            raise ValueError('piecewise density channel layout')
        channels=[]
        for poly in interval:
            if type(poly) not in (tuple,list) or len(poly)!=POLY_LENGTH:
                raise ValueError('piecewise density polynomial layout')
            channels.append(tuple(rational(v) for v in poly))
        rows.append(tuple(channels))
    ff=tuple(rational(v) for v in cosine)
    aa=[]
    for endpoint in atoms:
        if type(endpoint) not in (tuple,list) or len(endpoint)!=3:
            raise ValueError('physical endpoint atom layout')
        aa.append(tuple(rational(v) for v in endpoint))
    return cc,tuple(rows),ff,tuple(aa)


@dataclass(frozen=True,slots=True)
class Functional:
    cuts: tuple[Fraction,...]
    coefficients: tuple[tuple[tuple[Fraction,...],...],...]
    cosine: tuple[Fraction,Fraction,Fraction]
    atoms: tuple[tuple[Fraction,Fraction,Fraction],...]

    def __post_init__(self):
        values=_copy_validate(self.cuts,self.coefficients,self.cosine,self.atoms,
                              INPUT_INTERVALS,INPUT_INTEGER_BITS)
        for field,value in zip(('cuts','coefficients','cosine','atoms'),values):
            object.__setattr__(self,field,value)

    @property
    def exact_zero(self) -> bool:
        return (all(v==0 for interval in self.coefficients
                    for poly in interval for v in poly) and
                all(v==0 for v in self.cosine) and
                all(v==0 for atom in self.atoms for v in atom))


@dataclass(frozen=True,slots=True)
class _DerivedFunctional(Functional):
    """Validated union output; only difference constructs this larger class."""
    def __post_init__(self):
        values=_copy_validate(self.cuts,self.coefficients,self.cosine,self.atoms,
                              UNION_INTERVALS,DERIVED_INTEGER_BITS)
        for field,value in zip(('cuts','coefficients','cosine','atoms'),values):
            object.__setattr__(self,field,value)


def _restrict(poly,offset: Fraction,scale: Fraction):
    result=[ZERO]*POLY_LENGTH
    for k,value in enumerate(poly):
        for j in range(k+1):
            result[j]+=value*math.comb(k,j)*offset**(k-j)*scale**j
    return tuple(result)


def difference(first: Functional,second: Functional) -> Functional:
    """Subtract complete measures, admitting each derived interval before storage.

    Restriction holds at most one interval's two 3x6 polynomial blocks
    transiently; no unvalidated global coefficient collection is retained.
    """
    if not isinstance(first,Functional) or not isinstance(second,Functional):
        raise ValueError('difference requires two bounded physical functionals')
    union=tuple(sorted(set(first.cuts+second.cuts)))
    if len(union)-1>UNION_INTERVALS:
        raise ValueError('piecewise union exceeds 4095 positive intervals')
    cosine=tuple(x-y for x,y in zip(first.cosine,second.cosine))
    atoms=tuple(tuple(x-y for x,y in zip(a,b))
                for a,b in zip(first.atoms,second.atoms))
    total_bits=0
    def admit(value: Fraction) -> None:
        nonlocal total_bits
        numerator=value.numerator.bit_length()
        denominator=value.denominator.bit_length()
        if numerator>DERIVED_INTEGER_BITS or denominator>DERIVED_INTEGER_BITS:
            raise ValueError('piecewise functional rational integer bit cap exceeded')
        total_bits+=numerator+denominator
        if total_bits>TOTAL_INTEGER_BITS:
            raise ValueError('piecewise functional aggregate bit cap exceeded')
    for value in (*union,*cosine,*(v for atom in atoms for v in atom)):
        admit(value)
    coefficients=[]
    for a,b in zip(union,union[1:]):
        rows=[]
        for f in (first,second):
            k=bisect_right(f.cuts,a)-1
            if not 0<=k<len(f.coefficients) or b>f.cuts[k+1]:
                raise ArithmeticError('exact union interval containment failed')
            A,B=f.cuts[k:k+2]
            rows.append(tuple(_restrict(poly,(a-A)/(B-A),(b-a)/(B-A))
                              for poly in f.coefficients[k]))
        derived=tuple(tuple(x-y for x,y in zip(rows[0][channel],
                                                rows[1][channel]))
                      for channel in range(3))
        for polynomial in derived:
            for value in polynomial:
                admit(value)
        coefficients.append(derived)
    return _DerivedFunctional(union,tuple(coefficients),cosine,atoms)


class _Compensated:
    __slots__=('total','correction')
    def __init__(self): self.total=0.;self.correction=0.
    def add(self,value: float):
        t=self.total+value
        if abs(self.total)>=abs(value):
            self.correction+=(self.total-t)+value
        else:
            self.correction+=(value-t)+self.total
        self.total=t
    @property
    def value(self): return self.total+self.correction


def _phase(a: float,delta: float,u: np.ndarray) -> np.ndarray:
    """Cosine at a+delta*u without rounding away positive local width."""
    start=c.OMEGA*a;shift=c.OMEGA*delta*u
    return np.cos(start)*np.cos(shift)-np.sin(start)*np.sin(shift)


def _cosh_local(a: float,delta: float,u: np.ndarray) -> np.ndarray:
    shift=delta*u
    return np.cosh(a)*np.cosh(shift)+np.sinh(a)*np.sinh(shift)


def _cosh_right(a: float,delta: float,u: np.ndarray) -> np.ndarray:
    shift=delta*u
    return np.cosh(1-a)*np.cosh(shift)-np.sinh(1-a)*np.sinh(shift)


def _density(poly,amplitude: Fraction,a: float,delta: float,u: np.ndarray
             ) -> np.ndarray:
    try:
        coeff=np.asarray([float(v) for v in poly],dtype=np.float64)
        amp=float(amplitude)
    except OverflowError as exc:
        raise ValueError('unrepresentable exact density coefficient') from exc
    if (not np.all(np.isfinite(coeff)) or not math.isfinite(amp) or
            any(v!=0 and converted==0 for v,converted in zip(poly,coeff)) or
            (amplitude!=0 and amp==0)):
        raise ValueError('nonfinite or underflowed exact density coefficient')
    return np.polynomial.polynomial.polyval(u,coeff)+amp*_phase(a,delta,u)


def _checked_float(value: Fraction,name: str) -> float:
    try: result=float(value)
    except OverflowError as exc:
        raise ValueError(f'unrepresentable {name}') from exc
    if not math.isfinite(result) or (value!=0 and result==0):
        raise ValueError(f'nonfinite or underflowed {name}')
    return result


class _ObservationArithmetic(ArithmeticError):
    """An identified floating observation failed after valid input admission."""

    def __init__(self,stage: str,reason: str,channel: int|None=None):
        super().__init__(reason)
        self.stage=stage
        self.reason=reason
        self.channel=channel


def _observed_fsum(values,stage: str,reason: str,channel: int|None=None) -> float:
    """Sum one admitted observation without hiding an unavailable result."""
    terms=tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in terms):
        raise _ObservationArithmetic(stage,reason,channel)
    try:
        result=math.fsum(terms)
    except OverflowError as exc:
        raise _ObservationArithmetic(stage,reason,channel) from exc
    # The finite precheck deliberately excludes fsum's mixed-infinity
    # ValueError.  Such a ValueError therefore remains an unexpected error.
    if not math.isfinite(result):
        raise _ObservationArithmetic(stage,reason,channel)
    return result


def _failure(exc: _ObservationArithmetic) -> dict:
    return {'stage':exc.stage,'reason':exc.reason,'channel':exc.channel}


def norm_observation_at_order(functional: Functional,order: int=48) -> dict:
    """Raw signed full-H1 Green observation at one fixed quadrature order.

    Valid input/geometry errors still raise.  Identified floating failures are
    reported per channel so completed peer measurements remain available.
    Missing numerical values are ``None``; no replacement value is invented.
    """
    if not isinstance(functional,Functional) or type(order) is not int or order not in (48,64):
        raise ValueError('functional and fixed Green quadrature order required')
    if functional.exact_zero:
        zeros=[0.]*3
        return {'order':order,'squared_norm':0.,'channels':zeros.copy(),
                'diagonal':zeros.copy(),'offdiagonal':zeros.copy(),
                'atom_cross':zeros.copy(),'atom_gram':zeros.copy(),
                'sum_abs_terms':zeros.copy(),'cancellation_ratio':zeros.copy(),
                'exact_zero':True,'intervals':len(functional.coefficients),
                'channel_finite':(True,True,True),
                'channel_nonnegative':(True,True,True),
                'channel_nonzero_valid':(True,True,True),
                'total_finite':True,'total_nonnegative':True,
                'admissible':True,'failures':()}
    nodes,weights=leggauss(order)
    u=(nodes+1)/2;w=weights/2
    uv=u[:,None]*u[None,:]
    sinh1=math.sinh(1.);cosh1=math.cosh(1.)
    diagonal=[[] for _ in range(3)]
    offdiag=[[] for _ in range(3)]
    ps=[[] for _ in range(3)];qs=[[] for _ in range(3)]
    prefixes=[_Compensated() for _ in range(3)]
    channel_available=[True]*3
    failures=[]
    scale=(ONE,ONE,ONE/ELL)
    for a_exact,b_exact,rows in zip(functional.cuts,functional.cuts[1:],
                                    functional.coefficients):
        a=_checked_float(a_exact,'exact cut')
        delta=_checked_float(b_exact-a_exact,'positive interval width')
        if delta<=0:
            raise ValueError('positive exact interval underflows binary64')
        active=(any(v!=0 for poly in rows for v in poly) or
                any(v!=0 for v in functional.cosine))
        if delta*delta==0 and active:
            raise ValueError('positive interval Green area underflows binary64')
        p_kernel=_cosh_local(a,delta,u)
        q_kernel=_cosh_right(a,delta,u)
        # Diagonal Duffy triangle: s=a+delta*u, t=a+delta*u*v.
        green=_cosh_local(a,delta,uv)*_cosh_right(a,delta,u[:,None])/sinh1
        jac=2*delta*delta*u[:,None]*w[:,None]*w[None,:]
        if not (np.all(np.isfinite(green)) and np.all(np.isfinite(jac))):
            raise ValueError('nonfinite local Green geometry')
        if active and np.any(jac<np.finfo(np.float64).tiny):
            raise ValueError('active Duffy weighted Jacobian underflows or is subnormal')
        for channel in range(3):
            if not channel_available[channel]:
                continue
            amp=functional.cosine[channel]*scale[channel]
            poly=tuple(v*scale[channel] for v in rows[channel])
            fu=_density(poly,amp,a,delta,u)
            fuv=_density(poly,amp,a,delta,uv)
            if not np.all(np.isfinite(fu)) or not np.all(np.isfinite(fuv)):
                exc=_ObservationArithmetic('density_evaluation',
                                           'nonfinite local density',channel)
                failures.append(_failure(exc));channel_available[channel]=False
                continue
            try:
                p_i=delta*_observed_fsum(w*fu*p_kernel,'density_interaction',
                                         'nonfinite Green density interaction',channel)
                q_i=delta*_observed_fsum(w*fu*q_kernel,'density_interaction',
                                         'nonfinite Green density interaction',channel)
                d_i=_observed_fsum((jac*green*fu[:,None]*fuv).flat,
                                   'density_interaction',
                                   'nonfinite Green density interaction',channel)
                o_i=2*q_i*prefixes[channel].value/sinh1
                if not all(math.isfinite(v) for v in (p_i,q_i,d_i,o_i)):
                    raise _ObservationArithmetic('density_interaction',
                                                 'nonfinite Green density interaction',
                                                 channel)
            except _ObservationArithmetic as exc:
                failures.append(_failure(exc));channel_available[channel]=False
                continue
            diagonal[channel].append(d_i);offdiag[channel].append(o_i)
            ps[channel].append(p_i);qs[channel].append(q_i)
            prefixes[channel].add(p_i)
            if not math.isfinite(prefixes[channel].value):
                exc=_ObservationArithmetic('density_interaction',
                                           'nonfinite Green density interaction',channel)
                failures.append(_failure(exc));channel_available[channel]=False
    diag=[None]*3;off=[None]*3;cross=[None]*3;gram=[None]*3
    totals=[None]*3;abs_terms=[None]*3;ratios=[None]*3
    channel_finite=[False]*3
    channel_nonnegative=[False]*3
    channel_nonzero_valid=[False]*3
    for channel in range(3):
        if not channel_available[channel]:
            continue
        root=_checked_float(functional.atoms[0][channel]*scale[channel],
                            'root atom')
        tip=_checked_float(functional.atoms[1][channel]*scale[channel],
                           'tip atom')
        if (root!=0 and root*root==0) or (tip!=0 and tip*tip==0):
            exc=_ObservationArithmetic('atom_gram',
                                       'endpoint Green atom square underflows binary64',
                                       channel)
            failures.append(_failure(exc));continue
        try:
            p=_observed_fsum(ps[channel],'channel_reduction',
                             'nonfinite Green channel norm',channel)
            q=_observed_fsum(qs[channel],'channel_reduction',
                             'nonfinite Green channel norm',channel)
            d=_observed_fsum(diagonal[channel],'channel_reduction',
                             'nonfinite Green channel norm',channel)
            o=_observed_fsum(offdiag[channel],'channel_reduction',
                             'nonfinite Green channel norm',channel)
            ac=2*(root*q+tip*p)/sinh1
            ag=((root*root+tip*tip)*cosh1+2*root*tip)/sinh1
            total=_observed_fsum((d,o,ac,ag),'channel_total',
                                 'nonfinite Green channel norm',channel)
            if not all(math.isfinite(v) for v in (d,o,ac,ag)):
                raise _ObservationArithmetic('channel_total',
                                             'nonfinite Green channel norm',channel)
        except _ObservationArithmetic as exc:
            failures.append(_failure(exc));continue
        diag[channel]=d;off[channel]=o;cross[channel]=ac;gram[channel]=ag
        totals[channel]=total;channel_finite[channel]=True
        channel_nonnegative[channel]=total>=0
        if total<0:
            failures.append({'stage':'channel_nonnegative',
                             'reason':'negative Green channel squared norm',
                             'channel':channel})
        exact_nonzero=(functional.cosine[channel]!=0 or
                any(v!=0 for row in functional.coefficients
                    for v in row[channel]) or
                any(atom[channel]!=0 for atom in functional.atoms))
        channel_nonzero_valid[channel]=not (total==0 and exact_nonzero)
        if not channel_nonzero_valid[channel]:
            failures.append({'stage':'channel_nonzero',
                             'reason':'nonzero exact channel has zero computed Green norm',
                             'channel':channel})
        try:
            magnitude=(_observed_fsum((abs(v) for v in diagonal[channel]),
                                      'cancellation_metadata',
                                      'nonfinite Green cancellation metadata',channel)+
                       _observed_fsum((abs(v) for v in offdiag[channel]),
                                      'cancellation_metadata',
                                      'nonfinite Green cancellation metadata',channel)+
                       abs(ac)+abs(ag))
            ratio=magnitude/max(total,NORM_FLOOR_SQUARED)
            if not math.isfinite(magnitude) or not math.isfinite(ratio):
                raise _ObservationArithmetic('cancellation_metadata',
                                             'nonfinite Green cancellation metadata',
                                             channel)
        except _ObservationArithmetic as exc:
            failures.append(_failure(exc));continue
        abs_terms[channel]=magnitude;ratios[channel]=ratio
    squared=None;total_finite=False;total_nonnegative=False
    if all(channel_finite):
        try:
            squared=_observed_fsum(totals,'total_sum',
                                   'invalid Green total squared norm',None)
            total_finite=True;total_nonnegative=squared>=0
            if not total_nonnegative:
                failures.append({'stage':'total_nonnegative',
                                 'reason':'invalid Green total squared norm',
                                 'channel':None})
        except _ObservationArithmetic as exc:
            failures.append(_failure(exc))
    admissible=(not failures and all(channel_finite) and
                all(channel_nonnegative) and all(channel_nonzero_valid) and
                total_finite and total_nonnegative)
    return {'order':order,'squared_norm':squared,'channels':totals,
            'diagonal':diag,'offdiagonal':off,'atom_cross':cross,
            'atom_gram':gram,'sum_abs_terms':abs_terms,
            'cancellation_ratio':ratios,'exact_zero':False,
            'intervals':len(functional.coefficients),
            'channel_finite':tuple(channel_finite),
            'channel_nonnegative':tuple(channel_nonnegative),
            'channel_nonzero_valid':tuple(channel_nonzero_valid),
            'total_finite':total_finite,'total_nonnegative':total_nonnegative,
            'admissible':admissible,'failures':tuple(failures)}


def norm_at_order(functional: Functional,order: int=48) -> dict:
    """Strict historical wrapper around the signed raw observation."""
    raw=norm_observation_at_order(functional,order)
    if not raw['admissible']:
        raise ValueError(raw['failures'][0]['reason'])
    return {'order':raw['order'],'squared_norm':raw['squared_norm'],
            'channels':raw['channels'],'diagonal':raw['diagonal'],
            'offdiagonal':raw['offdiagonal'],'atom_cross':raw['atom_cross'],
            'atom_gram':raw['atom_gram'],'sum_abs_terms':raw['sum_abs_terms'],
            'cancellation_ratio':raw['cancellation_ratio'],
            'exact_zero':raw['exact_zero'],'intervals':raw['intervals']}


def squared_norm(functional: Functional) -> dict:
    """Two fixed-order checks; unresolved norms fail without a repair."""
    q48=norm_at_order(functional,48)
    q64=norm_at_order(functional,64)
    discrepancies=[abs(a-b)/max(abs(a),abs(b),NORM_FLOOR_SQUARED)
                   for a,b in zip(q48['channels']+[q48['squared_norm']],
                                  q64['channels']+[q64['squared_norm']])]
    resolution=max(discrepancies)
    if not math.isfinite(resolution) or resolution>RESOLUTION_LIMIT:
        raise ValueError('unresolved 48/64 full-H1 Green norm')
    return {'squared_norm':q64['squared_norm'],
            'norm':math.sqrt(q64['squared_norm']),
            'q48':q48,'q64':q64,'resolution':resolution,
            'exact_zero':functional.exact_zero,
            'ell_m':float(ELL),'floor_squared_N2':NORM_FLOOR_SQUARED}
