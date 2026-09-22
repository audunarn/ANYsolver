"""Bounded exact-Gram admission of three root rows and a free slope row.

Only three/four-by-N port rows and their at-most-four-by-four Gram matrix
are dense. No model-wide dense square matrix, nullspace or inverse occurs.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

import numpy as np

from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_spatial_contract as c


ZERO=F(0); ONE=F(1)
RATIO=F.from_float(1e-10)


@dataclass(frozen=True, slots=True)
class RankBudget:
    sparse_budget: common.SparseBudget
    max_fraction_bits: int
    max_total_bits: int
    max_eigen_steps: int
    max_work_bytes: int

    def __post_init__(self):
        if (type(self.sparse_budget) is not common.SparseBudget or
                any(type(x) is not int or x <= 0 for x in
                    (self.max_fraction_bits, self.max_total_bits,
                     self.max_eigen_steps, self.max_work_bytes))):
            raise ValueError('explicit root-rank resource budgets required')


class _Exact:
    def __init__(self, budget):
        self.budget=budget; self.bits=0; self.count=0

    def keep(self, value):
        a=value.numerator.bit_length(); b=value.denominator.bit_length()
        self.bits+=a+b; self.count+=1
        if (a>self.budget.max_fraction_bits or b>self.budget.max_fraction_bits
                or self.bits>self.budget.max_total_bits):
            raise ValueError('root-rank exact arithmetic budget exceeded')
        return value


def _determinant(matrix, exact):
    # Bounded n<=4 rational elimination; row exchanges preserve determinant.
    a=[list(row) for row in matrix]; n=len(a); determinant=ONE
    for k in range(n):
        pivot=next((i for i in range(k,n) if a[i][k]), None)
        if pivot is None: return ZERO
        if pivot!=k: a[k],a[pivot]=a[pivot],a[k]; determinant=-determinant
        value=a[k][k]; determinant=exact.keep(determinant*value)
        for i in range(k+1,n):
            multiplier=exact.keep(a[i][k]/value)
            for j in range(k+1,n):
                a[i][j]=exact.keep(a[i][j]-exact.keep(multiplier*a[k][j]))
            a[i][k]=ZERO
    return determinant


def _positive(matrix, exact):
    # Sylvester's criterion is exact for these real symmetric Gram shifts.
    return all(_determinant(tuple(tuple(row[:k]) for row in matrix[:k]),exact)>0
               for k in range(1,len(matrix)+1))


def _gram(rows, exact):
    rational=tuple(tuple(exact.keep(F.from_float(float(x))) for x in row)
                   for row in rows)
    output=[]
    for a in rational:
        line=[]
        for b in rational:
            value=ZERO
            for x,y in zip(a,b):
                value=exact.keep(value+exact.keep(x*y))
            line.append(value)
        output.append(tuple(line))
    return tuple(output)


def _shift(gram, value, upper, exact):
    return tuple(tuple(exact.keep((value if i==j else ZERO)-x) if upper else
                       exact.keep(x-(value if i==j else ZERO))
                       for j,x in enumerate(row)) for i,row in enumerate(gram))


def _ratio_proof(gram, exact, steps):
    size=len(gram)
    if not _positive(gram,exact):
        return {'status':'HOLD','reason':'exact port rows are rank deficient',
                'full_row_rank':False,'steps':0,'ratio_squared_lower':ZERO,
                'ratio_squared_upper':None}
    diagonal=tuple(gram[i][i] for i in range(size))
    if all(gram[i][j]==0 for i in range(size) for j in range(size) if i!=j):
        ratio=exact.keep(min(diagonal)/max(diagonal))
        return {'status':'PASSED' if ratio>=RATIO**2 else 'HOLD',
                'reason':None if ratio>=RATIO**2 else 'scaled ratio below frozen threshold',
                'full_row_rank':True,'steps':0,'ratio_squared_lower':ratio,
                'ratio_squared_upper':ratio}
    # Rayleigh/induced-norm endpoints contain the extremal Gram eigenvalues.
    min_low=ZERO; min_high=min(diagonal)
    max_low=max(diagonal); max_high=max(sum(map(abs,row),ZERO) for row in gram)
    lower=ZERO; upper=exact.keep(min_high/max_low)
    for step in range(1,steps+1):
        mid=exact.keep((min_low+min_high)/2)
        if _positive(_shift(gram,mid,False,exact),exact): min_low=mid
        else: min_high=mid
        mid=exact.keep((max_low+max_high)/2)
        if _positive(_shift(gram,mid,True,exact),exact): max_high=mid
        else: max_low=mid
        lower=exact.keep(min_low/max_high); upper=exact.keep(min_high/max_low)
        if lower>=RATIO**2 or upper<RATIO**2:
            return {'status':'PASSED' if lower>=RATIO**2 else 'HOLD',
                    'reason':None if lower>=RATIO**2 else 'scaled ratio below frozen threshold',
                    'full_row_rank':True,'steps':step,
                    'ratio_squared_lower':lower,'ratio_squared_upper':upper}
    return {'status':'HOLD','reason':'ratio enclosure unresolved at declared step budget',
            'full_row_rank':True,'steps':steps,
            'ratio_squared_lower':lower,'ratio_squared_upper':upper}


def verify_root_rank(root, slope, diagonal, *, budget):
    """Check Cbar=R C D and [Cbar;(L0/U0) A1_y(0) D].

    slope is the physical derivative port, never an imposed constraint.
    The caller must separately bind this port to its exact trace extraction.
    """
    if type(budget) is not RankBudget: raise ValueError('explicit rank budget required')
    root=common.validate_sparse(root,budget.sparse_budget,square=False)
    slope=common.validate_sparse(slope,budget.sparse_budget,square=False)
    n=root.shape[1]
    if root.shape!=(3,n) or slope.shape!=(1,n) or n<4:
        raise ValueError('three root rows, one slope row and at least four coordinates required')
    d=common._vector(diagonal,n,'D')
    if np.any(d<=0): raise ValueError('positive rank coordinate scaling required')
    workspace=4096*n+2*budget.max_total_bits+4096*budget.max_fraction_bits
    if workspace>budget.max_work_bytes:
        raise ValueError('root-rank workspace estimate exceeds budget')
    rows=np.zeros((4,n)); r=(1/c.U0,1/c.U0,.46/c.U0,c.L0/c.U0)
    for i in range(4):
        matrix=root if i<3 else slope; row=i if i<3 else 0
        lo,hi=matrix.indptr[row:row+2]; indices=matrix.indices[lo:hi]
        original=matrix.data[lo:hi]
        values=(original*r[i])*d[indices]
        if (not np.isfinite(values).all() or np.any((original!=0)&(values==0))):
            raise ArithmeticError('nonfinite or underflowed nonzero scaled rank entry')
        rows[i,indices]=values
    exact=_Exact(budget)
    gram=_gram(rows,exact)
    root_proof=_ratio_proof(tuple(tuple(row[:3]) for row in gram[:3]),exact,budget.max_eigen_steps)
    slope_proof=_ratio_proof(gram,exact,budget.max_eigen_steps)
    return {'status':'PORT_RANK_PASSED' if root_proof['status']==slope_proof['status']=='PASSED' else 'HOLD',
            'scope':'SCALED_PORT_RANK_ONLY_NOT_TRACE_BINDING',
            'threshold':RATIO,'root':root_proof,'root_and_free_slope':slope_proof,
            'exact_gram':gram,'scaled_rows':np.frombuffer(rows.tobytes(),dtype=np.float64).reshape(4,n),
            'work':{'port_rows':4,'coordinates':n,'dense_square_order':4,
                    'fraction_checks':exact.count,'cumulative_integer_bits':exact.bits,
                    'workspace_estimate_bytes':workspace,'eigensolves':0,'equilibrium_solves':0}}
