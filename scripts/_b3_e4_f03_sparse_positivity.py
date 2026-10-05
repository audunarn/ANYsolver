"""Exact-residual sparse positive-quadratic-form certificate, synthetic scope.

Consumes independently validated/owned CSR from the shared sparse checker.
The factor L,d is a supplied candidate, never accepted merely because some
LU or LDL routine returned it. No dense conversion or primal solve occurs.
Default use is restricted to independently reviewed tiny synthetic budgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

import numpy as np


Z=F(0);O=F(1)
SKEW_LIMIT=F.from_float(1e-12)


@dataclass(frozen=True,slots=True)
class PositivityBudget:
    sparse_budget:object
    max_product_paths:int
    max_residual_nnz:int
    max_fraction_bits:int
    max_total_bits:int
    max_python_work_bytes:int

    def __post_init__(self):
        for name in ('max_product_paths','max_residual_nnz',
                     'max_fraction_bits','max_total_bits',
                     'max_python_work_bytes'):
            value=getattr(self,name)
            if type(value) is not int or value<=0:
                raise ValueError(f'{name} must be a positive integer')


def _permutation(value,n):
    if (type(value) not in (tuple,list) or len(value)!=n or
            any(type(i) is not int for i in value) or
            set(value)!=set(range(n))):
        raise ValueError('complete symmetric permutation required')
    return tuple(value)


def _diagonal(value,n,resources):
    if (type(value) is not np.ndarray or value.dtype!=np.float64 or
            value.shape!=(n,) or not np.all(np.isfinite(value))):
        raise ValueError('finite float64 factor diagonal required')
    return tuple(resources.check(F.from_float(float(x))) for x in value)


def _python_workspace(n,knnz,lnnz,budget):
    """Deliberately conservative Python-side bound, distinct from peak RSS.

    Covers owned row dictionaries, two skew-pattern sets, column incidence,
    target/product/residual dictionaries, and exact integer objects. The
    declared cumulative bit budget is charged at two *bytes* per bit, well
    above Python integer payload; 1024 bytes per possible dictionary slot
    includes object/hash/pointer overhead. Factor producers remain external.
    """
    slots=3*knnz+2*lnnz+3*budget.max_residual_nnz+4*n
    estimate=1024*slots+2*budget.max_total_bits
    if estimate>budget.max_python_work_bytes:
        raise ValueError('Python rational/pattern workspace cap exceeded')
    return estimate


class _FractionBudget:
    def __init__(self,budget):
        self.budget=budget
        self.cumulative_bits=0
        self.operations=0

    def check(self,value:F) -> F:
        bits=value.numerator.bit_length()+value.denominator.bit_length()
        self.operations+=1
        self.cumulative_bits+=bits
        if (value.numerator.bit_length()>self.budget.max_fraction_bits or
            value.denominator.bit_length()>self.budget.max_fraction_bits or
            self.cumulative_bits>self.budget.max_total_bits):
            raise ValueError('exact rational positivity resource cap exceeded')
        return value


def _rows(matrix,resources):
    n=matrix.shape[0]
    rows=[]
    for i in range(n):
        row={}
        for k in range(int(matrix.indptr[i]),int(matrix.indptr[i+1])):
            j=int(matrix.indices[k])
            value=resources.check(F.from_float(float(matrix.data[k])))
            if value:row[j]=value
        rows.append(row)
    return tuple(rows)


def _skew_check(rows,resources):
    indices={(i,j) for i,row in enumerate(rows) for j in row}
    indices|={(j,i) for i,j in tuple(indices)}
    norm2=Z;skew2=Z
    for i,row in enumerate(rows):
        for value in row.values():
            term=resources.check(value*value)
            norm2=resources.check(norm2+term)
    for i,j in indices:
        diff=resources.check(rows[i].get(j,Z)-rows[j].get(i,Z))
        term=resources.check(diff*diff)
        skew2=resources.check(skew2+term)
    return norm2,skew2


def _factor_columns(rows):
    n=len(rows);columns=[[] for _ in range(n)]
    for i,row in enumerate(rows):
        if row.get(i,Z)!=1 or any(j>i and v for j,v in row.items()):
            raise ValueError('candidate L must be unit lower triangular')
        for j,v in row.items():
            if v:columns[j].append((i,v))
    return tuple(tuple(column) for column in columns)


def _inverse_comparison(rows,columns,resources):
    n=len(rows)
    forward=[Z]*n
    for i,row in enumerate(rows):
        acc=O
        for j,v in row.items():
            if j<i:
                term=resources.check(abs(v)*forward[j])
                acc=resources.check(acc+term)
        forward[i]=acc
    reverse=[Z]*n
    for i in range(n-1,-1,-1):
        acc=O
        for j,v in columns[i]:
            if j>i:
                term=resources.check(abs(v)*reverse[j])
                acc=resources.check(acc+term)
        reverse[i]=acc
    return max(reverse),max(forward)


def certify_positive(kbar,lower,diagonal,permutation,*,budget:PositivityBudget) -> dict:
    """Sufficient positivity of x.T Kbar x for full represented Kbar.

    All residual products and comparison bounds are exact Fractions. A
    nonzero admitted skew remains in R; this does not claim symmetric inertia.
    Preflight/ownership of each CSR is delegated to shared validate_sparse.
    """
    if type(budget) is not PositivityBudget:
        raise ValueError('explicit positivity resource budget required')
    from scripts import _b3_e4_f03_sparse_certificate as common
    if not isinstance(budget.sparse_budget,common.SparseBudget):
        raise ValueError('reviewed shared sparse budget required')
    K=common.validate_sparse(kbar,budget.sparse_budget,square=True)
    L=common.validate_sparse(lower,budget.sparse_budget,square=True)
    n=K.shape[0]
    if L.shape!=(n,n):raise ValueError('candidate factor shape mismatch')
    p=_permutation(permutation,n)
    python_bytes=_python_workspace(n,int(K.nnz),int(L.nnz),budget)
    resources=_FractionBudget(budget)
    d=_diagonal(diagonal,n,resources)
    kr=_rows(K,resources);lr=_rows(L,resources)
    knorm2,skew2=_skew_check(kr,resources)
    work={'order':n,'kbar_nnz':int(K.nnz),'factor_nnz':int(L.nnz),
          'product_paths':0,'residual_pattern_nnz':0,
          'rational_checks':resources.operations,
          'cumulative_integer_bits':resources.cumulative_bits,
          'python_workspace_estimate_bytes':python_bytes,
          'factor_rhs_solves':0}
    raw={'kbar_frobenius_squared':knorm2,
         'stored_skew_frobenius_squared':skew2,
         'skew_limit_squared':SKEW_LIMIT*SKEW_LIMIT}
    if knorm2==0 or skew2>SKEW_LIMIT*SKEW_LIMIT*knorm2:
        return {'status':'HOLD','reason':'stored skew exceeds unchanged gate',
                'raw':raw,'work':work,'residual_entries':()}
    if any(x<=0 for x in d):
        return {'status':'HOLD','reason':'nonpositive supplied congruence diagonal',
                'raw':raw,'work':work,'residual_entries':()}
    columns=_factor_columns(lr)
    paths=sum(len(column)**2 for column in columns)
    work['product_paths']=paths
    if paths>budget.max_product_paths:
        raise ValueError('congruence product-path resource cap exceeded before products')
    l1,li=_inverse_comparison(lr,columns,resources)
    if K.nnz>budget.max_residual_nnz:
        raise ValueError('input residual pattern cap exceeded before products')
    inverse={old:i for i,old in enumerate(p)}
    target={(inverse[i],inverse[j]):v
            for i,row in enumerate(kr) for j,v in row.items()}
    pattern=set(target)
    for column in columns:
        for i,_ in column:
            for j,_ in column:
                pattern.add((i,j))
                if len(pattern)>budget.max_residual_nnz:
                    raise ValueError('residual pattern cap exceeded before products')
    work['residual_pattern_nnz']=len(pattern)
    product={}
    for k,column in enumerate(columns):
        for i,lii in column:
            for j,ljj in column:
                key=(i,j)
                term=resources.check(lii*d[k]*ljj)
                product[key]=resources.check(product.get(key,Z)+term)
    residual={key:resources.check(target.get(key,Z)-product.get(key,Z))
              for key in sorted(pattern)}
    residual={key:value for key,value in residual.items() if value}
    rrows=[Z]*n;rcols=[Z]*n
    for (i,j),value in residual.items():
        rrows[i]=resources.check(rrows[i]+abs(value))
        rcols[j]=resources.check(rcols[j]+abs(value))
    r1=max(rcols);ri=max(rrows)
    dmin=min(d)
    invfactor=resources.check(resources.check(l1*li)/dmin)
    delta2=resources.check(resources.check(
        resources.check(resources.check(invfactor*invfactor)*r1)*ri))
    work.update({'residual_nnz':len(residual),
                 'rational_checks':resources.operations,
                 'cumulative_integer_bits':resources.cumulative_bits})
    raw.update({'dmin':dmin,'lower_inverse_1_upper':l1,
                'lower_inverse_inf_upper':li,'residual_1':r1,
                'residual_inf':ri,'delta_squared':delta2,
                'strict_margin_squared':1-delta2})
    return {'status':'POSITIVE_QUADRATIC_FORM' if delta2<1 else 'HOLD',
            'reason':None if delta2<1 else 'congruence residual bound not contractive',
            'raw':raw,'work':work,
            'residual_entries':tuple((i,j,value) for (i,j),value in sorted(residual.items()))}
