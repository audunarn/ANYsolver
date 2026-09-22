"""Piecewise-analytic floating H1-dual Gram for the finite F03 trace rows.

This independent scalar Riesz calculation uses the full, free-end H1 norm
integral_0^1 (u*v + u'*v') dx, with L0=1 m fixed. It does not assemble a
structural stiffness or certify a continuum structural inf-sup constant.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


_SERIES_TERMS=12


@dataclass(frozen=True)
class NormMetadata:
    """Canonical enriched row indices and physical line measures.

    Boundary hats have measure h/2, interior hats h (metres), and endpoint
    evaluations numerical measure 1. ``series_function_tail_bound`` bounds
    the absolute omitted terms of A and B at this cell width separately;
    it is not a certified bound on the floating Gram or its eigenvalues.
    """

    selected_enriched_rows: tuple[int,...]
    row_measures: tuple[float,...]
    series_terms: int
    series_function_tail_bound: float


def _admitted(n_mortar: int, family: str) -> None:
    if (type(n_mortar) is not int or not 2<=n_mortar<=16 or
            family not in ('P1','hybrid','enriched')):
        raise ValueError('invalid bounded analytic trace-dual layout')


def _series(h: float) -> tuple[float,float,float,float,float,float]:
    """A=cosh(h)-1, B=sinh(h)-h and their 0th/1st cell moments.

    Strictly positive power series avoid subtracting near-equal exponentials.
    The same terms evaluate the cell transfer and exact density integrals.
    """
    a_terms=[]; b_terms=[]
    a0_terms=[]; a1_terms=[]; b0_terms=[]; b1_terms=[]
    for k in range(1,_SERIES_TERMS+1):
        a=h**(2*k)/math.factorial(2*k)
        b=h**(2*k+1)/math.factorial(2*k+1)
        a_terms.append(a); b_terms.append(b)
        a0_terms.append(a*h/(2*k+1))
        a1_terms.append(a*h*h/(2*k+2))
        b0_terms.append(b*h/(2*k+2))
        b1_terms.append(b*h*h/(2*k+3))
    return tuple(math.fsum(items) for items in
                 (a_terms,b_terms,a0_terms,a1_terms,b0_terms,b1_terms))


def metadata(n_mortar: int, family: str) -> NormMetadata:
    """Immutable row map and explicit local Taylor-tail bound."""
    _admitted(n_mortar,family)
    n=n_mortar
    selected=(tuple(range(n+1)) if family=='P1' else
              tuple(range(1,n))+(n+1,n+2) if family=='hybrid' else
              tuple(range(n+3)))
    all_measures=[1/n]*(n+1)+[1.,1.]
    all_measures[0]=all_measures[n]=1/(2*n)
    h=1/n
    k=_SERIES_TERMS+1
    first_a=h**(2*k)/math.factorial(2*k)
    first_b=h**(2*k+1)/math.factorial(2*k+1)
    tail_a=first_a/(1-h*h/((2*k+1)*(2*k+2)))
    tail_b=first_b/(1-h*h/((2*k+2)*(2*k+3)))
    return NormMetadata(selected,tuple(all_measures[i] for i in selected),
                        _SERIES_TERMS,max(tail_a,tail_b))


def _transfer(u: float, derivative: float, a: float, b: float,
              h: float, A: float, B: float) -> tuple[float,float]:
    delta=u-a
    gamma=derivative-b
    return (u+h*derivative+delta*A+gamma*B,
            derivative+delta*(h+B)+gamma*A)


def _canonical_gram(n: int, normalized: bool) -> np.ndarray:
    h=1/n
    A,B,A0,A1,B0,B1=_series(h)
    count=n+3
    nodal=np.eye(n+1)
    cell_a=np.zeros((count,n))
    cell_b=np.zeros((count,n))
    cell_a[:n+1]=nodal[:,:-1]
    cell_b[:n+1]=(nodal[:,1:]-nodal[:,:-1])/h
    if normalized:
        measures=np.full(n+1,h)
        measures[[0,-1]]*=.5
        cell_a[:n+1]/=measures[:,None]
        cell_b[:n+1]/=measures[:,None]
    result=np.empty((count,count))
    for j in range(count):
        source_a=cell_a[j]
        source_b=cell_b[j]
        alpha0=float(j==n+1)
        alpha1=float(j==n+2)
        # Initial displacement zero gives the particular right derivative.
        u=0.; derivative=-alpha0
        for k in range(n):
            u,derivative=_transfer(u,derivative,source_a[k],source_b[k],h,A,B)
        u0=(alpha1-derivative)/math.sinh(1.)
        u=u0; derivative=-alpha0
        column=np.zeros(count)
        for k in range(n):
            test_a=cell_a[:n+1,k]
            test_b=cell_b[:n+1,k]
            column[:n+1]+=(
                u*(test_a*h+test_b*h*h/2)+
                derivative*(test_a*h*h/2+test_b*h**3/3)+
                (u-source_a[k])*(test_a*A0+test_b*A1)+
                (derivative-source_b[k])*(test_a*B0+test_b*B1))
            u,derivative=_transfer(u,derivative,source_a[k],source_b[k],h,A,B)
        column[n+1]=u0
        column[n+2]=u
        result[:,j]=column
    if not np.all(np.isfinite(result)):
        raise ValueError('nonfinite analytic trace-dual Gram')
    return result


def dual_gram(n_mortar: int, family: str, *, normalized: bool = True) -> np.ndarray:
    """Continuous scalar free-end H1 dual Gram, analytic cells in float64.

    Row order matches the existing independent FE norm: P1 all hats;
    hybrid interior hats then root/tip endpoint atoms; enriched all hats
    then both atoms. The unnormalized option retains physical line actions
    (integrals, metres), versus endpoint evaluations. No matrix repair,
    symmetrization, clipping, or structural-space projection is performed.
    """
    _admitted(n_mortar,family)
    if type(normalized) is not bool:
        raise ValueError('normalized must be boolean')
    indices=metadata(n_mortar,family).selected_enriched_rows
    return _canonical_gram(n_mortar,normalized)[np.ix_(indices,indices)]


def gram_diagnostics(gram: np.ndarray) -> dict[str,float]:
    """Roundoff-visible condition and antisymmetry; leaves Gram untouched."""
    value=np.asarray(gram)
    if (value.ndim!=2 or value.shape[0]!=value.shape[1] or
            not np.all(np.isfinite(value))):
        raise ValueError('invalid analytic Gram for diagnostics')
    return {'condition_2':float(np.linalg.cond(value)),
            'antisymmetry_max_abs':float(np.max(np.abs(value-value.T)))}
