"""Sparse, verified numerical integration perturbation diagnostics.

Every input is a primary-scaled binary64 operand; this helper binds its raw
canonical arrays but does not prove the physical D/R scaling construction.
It independently re-verifies the complete primary inverse-column evidence.
No factorization, second equilibrium solve, or dense global conversion.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math

import numpy as np

from scripts import _b3_e4_f03_sparse_certificate as shared


Z=F(0);O=F(1)
BLOCK_LIMIT=F.from_float(1e-11)
PERTURBATION_LIMIT=F.from_float(1e-6)
SCOPE='NUMERICAL_PERTURBATION_ONLY_NOT_SCALING_ADMISSION'


@dataclass(frozen=True,slots=True)
class IntegrationBudget:
    sparse_budget:shared.SparseBudget
    max_union_nnz:int
    max_fraction_bits:int
    max_total_bits:int
    max_python_work_bytes:int

    def __post_init__(self):
        if not isinstance(self.sparse_budget,shared.SparseBudget) or any(
            type(getattr(self,key)) is not int or getattr(self,key)<=0 for key in
            ('max_union_nnz','max_fraction_bits','max_total_bits',
             'max_python_work_bytes')):
            raise ValueError('explicit positive integration budgets required')


class _Bits:
    def __init__(self,budget):
        self.budget=budget;self.count=0;self.bits=0

    def keep(self,x:F) -> F:
        self.count+=1
        a=x.numerator.bit_length();b=x.denominator.bit_length()
        self.bits+=a+b
        if a>self.budget.max_fraction_bits or b>self.budget.max_fraction_bits or self.bits>self.budget.max_total_bits:
            raise ValueError('integration exact rational resource cap exceeded')
        return x


def _python_workspace(n,nnz,plus_nnz,budget):
    # Intentionally over-count integer payload, numerical CSR copies,
    # two-pointer cursors, four exact running block sums, and vector buffers.
    estimate=1024*(nnz+plus_nnz+budget.max_union_nnz+8*n)+2*budget.max_total_bits
    if estimate>budget.max_python_work_bytes:
        raise ValueError('integration Python workspace estimate exceeds budget')
    return estimate


def _hash_sparse(matrix):
    digest=hashlib.sha256()
    digest.update(np.asarray(matrix.shape,dtype='<i8').tobytes())
    digest.update(np.asarray(matrix.indptr,dtype='<i8').tobytes())
    digest.update(np.asarray(matrix.indices,dtype='<i8').tobytes())
    digest.update(np.asarray(matrix.data,dtype='<f8').tobytes())
    return digest.hexdigest()


def _hash_vector(vector):
    digest=hashlib.sha256()
    digest.update(np.asarray(vector.shape,dtype='<i8').tobytes())
    digest.update(np.asarray(vector,dtype='<f8').tobytes())
    return digest.hexdigest()


def _float_upper(x:F) -> float:
    if x<0:raise ValueError('nonnegative exact bound required')
    try:v=float(x)
    except OverflowError as exc:raise ArithmeticError('nonfinite integration bound') from exc
    if not math.isfinite(v):raise ArithmeticError('nonfinite integration bound')
    if F.from_float(v)<x:v=math.nextafter(v,math.inf)
    if not math.isfinite(v) or F.from_float(v)<x:
        raise ArithmeticError('outward integration upper failed')
    return v


def _float_lower(x:F) -> float:
    if x<0:raise ValueError('nonnegative exact bound required')
    try:v=float(x)
    except OverflowError as exc:raise ArithmeticError('nonfinite integration bound') from exc
    if not math.isfinite(v):raise ArithmeticError('nonfinite integration bound')
    if F.from_float(v)>x:v=math.nextafter(v,-math.inf)
    if v<0 or F.from_float(v)>x:
        raise ArithmeticError('outward integration lower failed')
    return v


def _sqrt_upper(x:F) -> float:
    # First enclose the exact rational squared norm, then invoke the shared
    # scalar sqrt whose candidate is checked by an exact squared inequality.
    if x==0:return 0.
    return shared._sqrt(_float_upper(x),True)


def _union_preflight(h,g,n,budget):
    if h.nnz+g.nnz>budget.max_union_nnz:
        raise ValueError('integration union upper inventory exceeds budget')
    count=0
    for i in range(n):
        ia,ea=int(h.indptr[i]),int(h.indptr[i+1])
        ib,eb=int(g.indptr[i]),int(g.indptr[i+1])
        while ia<ea or ib<eb:
            if ib>=eb or (ia<ea and h.indices[ia]<g.indices[ib]):ia+=1
            elif ia>=ea or g.indices[ib]<h.indices[ia]:ib+=1
            else:ia+=1;ib+=1
            count+=1
    return count


def _block(i,j,primal):
    if i<primal:
        return 'K' if j<primal else 'C_upper'
    return 'C_lower' if j<primal else 'multiplier_zero'


def _difference_squares(h,g,primal,bits):
    n=h.shape[0]
    diff={name:Z for name in ('H','K','C_lower','C_upper')}
    base={name:Z for name in ('K','C_lower','C_upper')}
    count=only_primary=only_plus=0
    for i in range(n):
        ia,ea=int(h.indptr[i]),int(h.indptr[i+1])
        ib,eb=int(g.indptr[i]),int(g.indptr[i+1])
        while ia<ea or ib<eb:
            if ib>=eb or (ia<ea and h.indices[ia]<g.indices[ib]):
                j=int(h.indices[ia]);a=bits.keep(F.from_float(float(h.data[ia])));b=Z
                ia+=1;only_primary+=1
            elif ia>=ea or g.indices[ib]<h.indices[ia]:
                j=int(g.indices[ib]);a=Z;b=bits.keep(F.from_float(float(g.data[ib])))
                ib+=1;only_plus+=1
            else:
                j=int(h.indices[ia]);a=bits.keep(F.from_float(float(h.data[ia])))
                b=bits.keep(F.from_float(float(g.data[ib])))
                ia+=1;ib+=1
            channel=_block(i,j,primal)
            if channel=='multiplier_zero':
                if a or b:raise ValueError('KKT multiplier-zero block must remain exact zero')
                count+=1;continue
            delta=bits.keep(b-a)
            squared=bits.keep(delta*delta)
            diff[channel]=bits.keep(diff[channel]+squared)
            diff['H']=bits.keep(diff['H']+squared)
            base[channel]=bits.keep(base[channel]+bits.keep(a*a))
            count+=1
    return diff,base,dict(union_entries=count,primary_only=only_primary,plus_only=only_plus)


def _ratio(d2:F,b2:F,bits,*,floor_at_one=False):
    # The frozen C comparison uses max(1, ||C||F); K uses its own nonzero
    # Frobenius norm, with an absolute comparison only when K is zero.
    denom=max(O,b2) if floor_at_one else (b2 if b2>0 else O)
    quotient=bits.keep(d2/denom)
    return {'squared':quotient,'upper':_sqrt_upper(quotient),
            'within_limit':quotient<=BLOCK_LIMIT*BLOCK_LIMIT}


def _vector_squares(a,b,bits):
    primary=diff=base_inf=diff_inf=Z
    for av,bv in zip(a,b):
        x=bits.keep(F.from_float(float(av)))
        y=bits.keep(F.from_float(float(bv)))
        base_inf=max(base_inf,abs(x))
        primary=bits.keep(primary+bits.keep(x*x))
        delta=bits.keep(y-x)
        diff_inf=max(diff_inf,abs(delta))
        diff=bits.keep(diff+bits.keep(delta*delta))
    return primary,diff,base_inf,diff_inf


def _load_ratio(base_inf,diff_inf,bits):
    # Frozen load comparison: ||fplus-f||inf/max(1,||f||inf).
    quotient=bits.keep(diff_inf/max(O,base_inf))
    return {'squared':bits.keep(quotient*quotient),
            'upper':_float_upper(quotient),
            'within_limit':quotient<=BLOCK_LIMIT}


def verify_integration(h,hplus,b,bplus,z,inverse_blocks,primal_order,*,budget:IntegrationBudget) -> dict:
    """Bind complete primary evidence and verify full sparse perturbations.

    The future owner must separately bind physical K/C/f and D/R scaling to
    these hashed primary-scaled arrays; this helper cannot infer that law.
    """
    if type(budget) is not IntegrationBudget or type(primal_order) is not int or primal_order<1:
        raise ValueError('explicit integration budget and primal order required')
    H=shared.validate_sparse(h,budget.sparse_budget,square=True)
    G=shared.validate_sparse(hplus,budget.sparse_budget,square=True)
    n=primal_order+3
    if H.shape!=(n,n) or G.shape!=(n,n):
        raise ValueError('exact three-root KKT order required')
    b0=shared._vector(b,n,'primary b');b1=shared._vector(bplus,n,'alternate b')
    state=shared._vector(z,n,'primary z')
    if np.any(b0[primal_order:]!=0) or np.any(b1[primal_order:]!=0):
        raise ValueError('three-root KKT right-hand-side zero block required')
    workspace=_python_workspace(n,int(H.nnz),int(G.nnz),budget)
    union=_union_preflight(H,G,n,budget)
    hashes={'primary_H':_hash_sparse(H),'alternate_H':_hash_sparse(G),
            'primary_b':_hash_vector(b0),'alternate_b':_hash_vector(b1),
            'primary_z':_hash_vector(state)}
    bits=_Bits(budget)
    differences,base,counts=_difference_squares(H,G,primal_order,bits)
    if counts['union_entries']!=union:
        raise ArithmeticError('independent sparse union inventory changed')
    primary_f2,df2,base_f_inf,diff_f_inf=(
        _vector_squares(b0[:primal_order],b1[:primal_order],bits))
    db2=bits.keep(df2)  # exact root right-hand sides have already been checked zero
    blocks={'K':_ratio(differences['K'],base['K'],bits),
            'C_lower':_ratio(differences['C_lower'],base['C_lower'],bits,
                             floor_at_one=True),
            'C_upper':_ratio(differences['C_upper'],base['C_upper'],bits,
                             floor_at_one=True)}
    blocks['f']=_load_ratio(base_f_inf,diff_f_inf,bits)
    dH=_sqrt_upper(differences['H']);db=_sqrt_upper(db2)
    # Structural and resource preflight above cannot consume inverse blocks.
    primary=shared.certificate_a(H,inverse_blocks,budget.sparse_budget,b=b0,z=state)
    with np.errstate(over='raise',invalid='raise',divide='raise',under='ignore'):
        shared.check_arithmetic()
        low,high=shared._product_bounds(G,state[:,None])
        residual_abs=shared._residual_abs(low,high,b1[:,None])
        alternate_residual=shared._norm2(residual_abs)[1]
        zlow,zu=shared._norm2(state)
    raw={'H_difference_frobenius_squared':differences['H'],
         'b_difference_two_squared':db2,
         'primary_load_two_squared':primary_f2,
         'primary_load_infinity':base_f_inf,
         'load_difference_infinity':diff_f_inf,
         'H_difference_frobenius_upper':dH,'b_difference_two_upper':db,
         'alternate_residual_two_upper':alternate_residual,
         'z_two_lower':zlow,'z_two_upper':zu}
    work={'union_entries':union,**counts,'exact_rationals_checked':bits.count,
          'cumulative_integer_bits':bits.bits,
          'python_workspace_estimate_bytes':workspace,
          'alternate_equilibrium_solves':0,
          'primary_inverse_columns_verified':primary['inverse_columns']}
    failures=[f'{name} relative scaled integration difference exceeds 1e-11'
              for name,result in blocks.items() if not result['within_limit']]
    sigma=alpha=original_delta=full_delta=original_final=full_final=None
    inverse=primary.get('inverse_two_upper')
    if inverse is None or not math.isfinite(inverse) or inverse<=0:
        failures.append('primary inverse certificate unresolved')
    else:
        sigma=_float_lower(O/F.from_float(float(inverse)))
        if sigma<=0 or zlow<=0:
            failures.append('positive inverse singular bound and state norm lower required')
        else:
            alpha=_float_upper(F.from_float(dH)/F.from_float(sigma))
            original_numerator=F.from_float(dH)*F.from_float(zu)+F.from_float(db)
            denominator=F.from_float(sigma)*F.from_float(zlow)
            original_delta=_float_upper(original_numerator/denominator)
            residual=primary.get('residual_two_upper')
            if residual is None or not math.isfinite(residual) or residual<0:
                failures.append('primary residual enclosure unavailable for full alternate error')
            else:
                full_delta=_float_upper((original_numerator+F.from_float(float(residual)))/
                                        denominator)
            if alpha>=1:
                failures.append('integration perturbation alpha is at least one')
            else:
                original_final=_float_upper(F.from_float(original_delta)/
                                            (O-F.from_float(alpha)))
                if F.from_float(original_final)>PERTURBATION_LIMIT:
                    failures.append('original integration sensitivity exceeds 1e-6')
                if full_delta is not None:
                    full_final=_float_upper(F.from_float(full_delta)/
                                            (O-F.from_float(alpha)))
                    if F.from_float(full_final)>PERTURBATION_LIMIT:
                        failures.append('full saved-state alternate error exceeds 1e-6')
    if primary['status']!='CERTIFIED_WITHIN_LIMIT':
        failures.append('primary numerical certificate has not passed')
    return {'scope':SCOPE,'input_sha256':hashes,'primary_certificate':primary,
            'blocks':blocks,'raw':raw,
            'perturbation':{'sigma_lower':sigma,'alpha_upper':alpha,
                            'original_integration_delta_upper':original_delta,
                            'full_saved_state_delta_upper':full_delta,
                            'original_integration_sensitivity_upper':original_final,
                            'full_saved_state_alternate_error_upper':full_final,
                            'alpha_violation':int(alpha is None or alpha>=1),
                            'original_integration_sensitivity_violation':int(
                                original_final is None or
                                F.from_float(original_final)>PERTURBATION_LIMIT),
                            'full_saved_state_error_violation':int(
                                full_final is None or
                                F.from_float(full_final)>PERTURBATION_LIMIT)},
            'work':work,'status':'NUMERICAL_PERTURBATION_PASSED' if not failures else 'HOLD',
            'failures':tuple(failures)}
