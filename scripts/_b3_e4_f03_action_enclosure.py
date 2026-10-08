"""Exact rational enclosures of bounded represented-law cosine actions.

Fixed-order Taylor remainders certify real values; decimal_value remains
display-only. This module performs no quadrature, solve or automatic retry.
"""
from __future__ import annotations

from dataclasses import dataclass,replace
from fractions import Fraction as F
import hashlib
import math

import numpy as np

from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_spatial_contract as c

ZERO=F(0);ONE=F(1)


@dataclass(frozen=True,slots=True)
class ActionBudget:
    order: int
    max_intervals: int
    max_fraction_bits: int
    max_total_bits: int
    max_operations: int
    max_work_bytes: int

    def __post_init__(self):
        if (type(self.order) is not int or not 0<=self.order<=128 or
            any(type(x) is not int or x<=0 for x in (self.max_intervals,
                self.max_fraction_bits,self.max_total_bits,self.max_operations,self.max_work_bytes))):
            raise ValueError('explicit bounded Action order and resource limits required')


class _Exact:
    def __init__(self,budget):self.budget=budget;self.count=0;self.total=0
    def keep(self,value):
        self.count+=1
        bits=value.numerator.bit_length()+value.denominator.bit_length()
        self.total+=bits
        if (max(value.numerator.bit_length(),value.denominator.bit_length())>self.budget.max_fraction_bits or
            self.total>self.budget.max_total_bits or self.count>self.budget.max_operations):
            raise ValueError('Action exact arithmetic budget exceeded')
        return value


def _hash_fraction(digest,value):
    digest.update(b'-' if value<0 else b'+')
    for integer in (abs(value.numerator),value.denominator):
        data=integer.to_bytes(max(1,(integer.bit_length()+7)//8),'little')
        digest.update(len(data).to_bytes(8,'little'));digest.update(data)


def _identity(rational,terms):
    digest=hashlib.sha256(b'F03_ACTION_EXACT_V1\0');_hash_fraction(digest,rational)
    digest.update(len(terms).to_bytes(8,'little'))
    for a,b,poly in terms:
        for value in (a,b,*poly):_hash_fraction(digest,value)
    return digest.hexdigest()


def _restrict(poly,offset,width,exact):
    aa=[ONE];bb=[ONE]
    for _ in range(5):
        aa.append(exact.keep(aa[-1]*offset));bb.append(exact.keep(bb[-1]*width))
    output=[ZERO]*6
    for k,value in enumerate(poly):
        if not value:continue
        for j in range(k+1):
            term=exact.keep(exact.keep(value*math.comb(k,j))*exact.keep(aa[k-j]*bb[j]))
            output[j]=exact.keep(output[j]+term)
    return tuple(output)


def _normalize(action,budget,exact):
    # Sweep exact events. No closest-point or floating endpoint comparisons.
    terms=action.cosine_terms
    starts={};ends={}
    for index,(a,b,poly) in enumerate(terms):
        starts.setdefault(a,[]).append(index);ends.setdefault(b,[]).append(index)
    cuts=sorted(starts.keys()|ends.keys())
    intervals=max(0,len(cuts)-1)
    if intervals>budget.max_intervals:
        raise ValueError('Action union interval budget exceeded')
    # Fraction objects and transient scalar products, including hashing.
    workspace=(14*intervals+8*len(terms)+128)*(512+(2*budget.max_fraction_bits+7)//8)
    if workspace>budget.max_work_bytes:
        raise ValueError('Action workspace estimate exceeds budget')
    exact.keep(action.rational)
    for a,b,poly in terms:
        for value in (a,b,*poly):exact.keep(value)
    active={};output=[];visits=0
    for a,b in zip(cuts,cuts[1:]):
        for index in ends.get(a,()):active.pop(index)
        for index in starts.get(a,()):active[index]=terms[index]
        poly=[ZERO]*6
        for lo,hi,p in active.values():
            visits+=1
            local=_restrict(p,exact.keep((a-lo)/(hi-lo)),exact.keep((b-a)/(hi-lo)),exact)
            for j,v in enumerate(local):poly[j]=exact.keep(poly[j]+v)
        if any(poly):output.append((a,b,tuple(poly)))
    return tuple(output),workspace,intervals,visits


def _center(x,order,exact):
    """Taylor polynomials for cos(x), sin(x), plus a common Lagrange bound."""
    cosine=ONE;sine=ZERO;term=ONE
    for k in range(1,order+1):
        term=exact.keep(exact.keep(term*x)/k)
        if k%2: sine=exact.keep(sine+(term if k%4==1 else -term))
        else: cosine=exact.keep(cosine+(term if k%4==0 else -term))
    remainder=exact.keep(abs(exact.keep(term*x))/(order+1))
    return cosine,sine,remainder


def _term_interval(a,b,poly,order,exact):
    h=exact.keep(b-a);x=exact.keep(c.Q_OMEGA*a);delta=exact.keep(c.Q_OMEGA*h)
    cosine,sine,center_error=_center(x,order,exact)
    coefficient=ONE;cos_weight=sin_weight=ZERO
    for k in range(order+1):
        if k:coefficient=exact.keep(exact.keep(coefficient*delta)/k)
        moment=ZERO
        for j,v in enumerate(poly):moment=exact.keep(moment+exact.keep(v/F(j+k+1)))
        term=exact.keep(coefficient*moment)
        if k%2:sin_weight=exact.keep(sin_weight+(term if k%4==3 else -term))
        else:cos_weight=exact.keep(cos_weight+(term if k%4==0 else -term))
    # Integral |p(tau)|*tau^(order+1) <= sum |p_j|/(j+order+2).
    absolute_moment=ZERO
    for j,v in enumerate(poly):
        absolute_moment=exact.keep(absolute_moment+exact.keep(abs(v)/F(j+order+2)))
    local_error=exact.keep(exact.keep(abs(exact.keep(coefficient*delta))/(order+1))*absolute_moment)
    center=exact.keep(h*exact.keep(exact.keep(cos_weight*cosine)+exact.keep(sin_weight*sine)))
    radius=exact.keep(h*exact.keep(exact.keep((abs(cos_weight)+abs(sin_weight))*center_error)+local_error))
    return exact.keep(center-radius),exact.keep(center+radius)


def enclose(action,*,budget):
    """Enclose the complete exact Action at the declared fixed Taylor order."""
    if type(action) is not recovery.Action or type(budget) is not ActionBudget:
        raise ValueError('validated exact Action and explicit enclosure budget required')
    # Revalidate into an immutable snapshot using the existing Action contract.
    action=recovery.Action(action.rational,action.cosine_terms)
    exact=_Exact(budget)
    normalized,workspace,intervals,visits=_normalize(action,budget,exact)
    low=high=action.rational
    for a,b,poly in normalized:
        lo,hi=_term_interval(a,b,poly,budget.order,exact)
        low=exact.keep(low+lo);high=exact.keep(high+hi)
    if low>high:raise ArithmeticError('invalid Action enclosure ordering')
    return {'status':'ENCLOSED','scope':'REPRESENTED_ACTION_REAL_VALUE_ONLY',
            'lower':low,'upper':high,'order':budget.order,
            'input_sha256':_identity(action.rational,action.cosine_terms),
            'normalized_sha256':_identity(action.rational,normalized),
            'work':{'input_terms':len(action.cosine_terms),'union_intervals':intervals,
                    'retained_intervals':len(normalized),'active_interval_visits':visits,
                    'exact_operations':exact.count,'cumulative_integer_bits':exact.total,
                    'workspace_estimate_bytes':workspace,'automatic_retries':0,
                    'quadrature_evaluations':0,'equilibrium_solves':0}}


def action_identity(action):
    """Return the canonical identity of one validated represented Action."""
    if type(action) is not recovery.Action:
        raise ValueError('validated exact Action required')
    owned=recovery.Action(action.rational,action.cosine_terms)
    return _identity(owned.rational,owned.cosine_terms)


def _scalar(value,name):
    if type(value) is F:return recovery._rational(value)
    if type(value) in (float,np.float64) and math.isfinite(value):return F.from_float(float(value))
    raise ValueError(f'{name} must be an exact Fraction or finite binary64 scalar')


def compare_saved(action,saved,scale,limit,*,budget):
    """Admit only if every real value in the enclosure meets the saved limit.

    A bound crossing the limit is HOLD_UNRESOLVED; no precision retry occurs.
    """
    if type(budget) is not ActionBudget:raise ValueError('explicit comparison budget required')
    target=_scalar(saved,'saved value');scale=_scalar(scale,'scale');limit=_scalar(limit,'limit')
    if scale<=0 or limit<0:raise ValueError('positive scale and nonnegative limit required')
    exact=_Exact(budget)
    for value in (target,scale,limit):exact.keep(value)
    if exact.total>=budget.max_total_bits or exact.count>=budget.max_operations:
        raise ValueError('comparison operands exhausted Action budget')
    enclosure=enclose(action,budget=replace(budget,
        max_total_bits=budget.max_total_bits-exact.total,
        max_operations=budget.max_operations-exact.count))
    exact.count+=enclosure['work']['exact_operations'];exact.total+=enclosure['work']['cumulative_integer_bits']
    lo=exact.keep((enclosure['lower']-target)/scale)
    hi=exact.keep((enclosure['upper']-target)/scale)
    upper=max(abs(lo),abs(hi));lower=ZERO if lo<=0<=hi else min(abs(lo),abs(hi))
    status='PASSED' if upper<=limit else 'FAILED' if lower>limit else 'HOLD_UNRESOLVED'
    return {'status':status,'absolute_error_lower':lower,'absolute_error_upper':upper,
            'saved_exact':target,'scale_exact':scale,'limit_exact':limit,'enclosure':enclosure,
            'comparison_work':{'exact_operations':exact.count,'cumulative_integer_bits':exact.total}}
