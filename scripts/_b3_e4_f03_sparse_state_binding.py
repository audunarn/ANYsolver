"""Bounded physical-to-scaled state binding for the classical candidate.

This verifies supplied binary64 operands, not their physical assembly or a
scientific solution. The entry comparison fixes the candidate's left-then-
right arithmetic and does not silently admit a different scaling order.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as shared
from scripts import _b3_e4_f03_spatial_contract as c


O=F(1)
D_LIMIT=F.from_float(1e-12)
STATE_LIMIT=F.from_float(1e-11)
ACTION_LIMIT=F.from_float(1e-11)
SCOPE='CLASSICAL_SPARSE_PHYSICAL_SCALING_AND_SAVED_STATE_ONLY'


@dataclass(frozen=True,slots=True)
class BindingBudget:
    sparse_budget:shared.SparseBudget
    max_combined_nnz:int
    max_fraction_bits:int
    max_total_bits:int
    max_python_work_bytes:int

    def __post_init__(self):
        if type(self.sparse_budget) is not shared.SparseBudget or any(
                type(getattr(self,key)) is not int or getattr(self,key)<=0
                for key in ('max_combined_nnz','max_fraction_bits',
                            'max_total_bits','max_python_work_bytes')):
            raise ValueError('explicit positive sparse state-binding budgets required')


class _Bits:
    def __init__(self,budget):
        self.budget=budget
        self.count=0
        self.total=0

    def keep(self,value):
        self.count+=1
        numerator=value.numerator.bit_length()
        denominator=value.denominator.bit_length()
        self.total+=numerator+denominator
        if (numerator>self.budget.max_fraction_bits or
                denominator>self.budget.max_fraction_bits or
                self.total>self.budget.max_total_bits):
            raise ValueError('state-binding exact rational resource cap exceeded')
        return value


def _upper(value):
    if value<0:
        raise ValueError('nonnegative enclosure required')
    try:
        result=float(value)
    except OverflowError as exc:
        raise ArithmeticError('nonfinite state-binding bound') from exc
    if not math.isfinite(result):
        raise ArithmeticError('nonfinite state-binding bound')
    if F.from_float(result)<value:
        result=math.nextafter(result,math.inf)
    if not math.isfinite(result) or F.from_float(result)<value:
        raise ArithmeticError('outward state-binding conversion failed')
    return result


def _hash_sparse(matrix):
    digest=hashlib.sha256(b'F03_STATE_BINDING_CSR_V1\0')
    for value,dtype in ((matrix.shape,'<i8'),(matrix.indptr,'<i8'),
                        (matrix.indices,'<i8'),(matrix.data,'<f8')):
        digest.update(np.asarray(value,dtype=dtype).tobytes())
    return digest.hexdigest()


def _hash_vector(value):
    digest=hashlib.sha256(b'F03_STATE_BINDING_VECTOR_V1\0')
    digest.update(np.asarray(value.shape,dtype='<i8').tobytes())
    digest.update(np.asarray(value,dtype='<f8').tobytes())
    return digest.hexdigest()


def _scale(matrix,left,right,denominator=1.):
    result=matrix.copy()
    for row in range(result.shape[0]):
        lo,hi=result.indptr[row:row+2]
        old=result.data[lo:hi].copy()
        result.data[lo:hi]=((old*left[row])*right[result.indices[lo:hi]])/denominator
        if (not np.isfinite(result.data[lo:hi]).all() or
                np.any((old!=0)&(result.data[lo:hi]==0))):
            raise ArithmeticError('nonfinite or underflowed physical scaling entry')
    return result


def _compare_entries(observed,expected,bits):
    """Complete sparse union; zero storage and signed zero are immaterial."""
    count=0
    maximum=F(0)
    for row in range(observed.shape[0]):
        i,end_i=int(observed.indptr[row]),int(observed.indptr[row+1])
        j,end_j=int(expected.indptr[row]),int(expected.indptr[row+1])
        while i<end_i or j<end_j:
            if j>=end_j or (i<end_i and observed.indices[i]<expected.indices[j]):
                a=float(observed.data[i]);b=0.;i+=1
            elif i>=end_i or expected.indices[j]<observed.indices[i]:
                a=0.;b=float(expected.data[j]);j+=1
            else:
                a=float(observed.data[i]);b=float(expected.data[j]);i+=1;j+=1
            if a!=b:
                count+=1
                difference=bits.keep(abs(F.from_float(a)-F.from_float(b)))
                maximum=max(maximum,difference)
    return count,maximum


def _max_action(matrix,state,target,bits):
    maximum=F(0)
    for row in range(matrix.shape[0]):
        actual=F(0)
        for index in range(int(matrix.indptr[row]),int(matrix.indptr[row+1])):
            product=bits.keep(F.from_float(float(matrix.data[index]))*
                              F.from_float(float(state[int(matrix.indices[index])])))
            actual=bits.keep(actual+product)
        difference=bits.keep(abs(actual-F.from_float(float(target[row]))))
        maximum=max(maximum,difference)
    return maximum


def verify_binding(k_shell,k_beam,c_root,f,d,h,b,q,eta,z,*,h_z=None,
                   budget:BindingBudget) -> dict:
    """Verify owned physical blocks, fixed scaling, and supplied saved actions.

    `h_z=None` returns PARTIAL_ACTION_NOT_PROVIDED even if every available
    check passes. This helper never produces a fresh equilibrium or factor.
    """
    if type(budget) is not BindingBudget:
        raise ValueError('explicit state-binding budget required')
    sb=budget.sparse_budget
    ks=shared.validate_sparse(k_shell,sb)
    kb=shared.validate_sparse(k_beam,sb)
    cc=shared.validate_sparse(c_root,sb,square=False)
    n=ks.shape[0]
    if (kb.shape!=(n,n) or cc.shape!=(3,n) or n+3>sb.max_order):
        raise ValueError('matching primal blocks and exactly three root rows required')
    # Check the complete upper allocation envelope before native sparse sum,
    # transpose or block construction. This is a working-set estimate, not RSS.
    envelope=int(ks.nnz+kb.nnz+2*cc.nnz)
    shared._workspace(n+3,n+3,envelope,1,sb)
    observed=shared.validate_sparse(h,sb)
    if observed.shape!=(n+3,n+3):
        raise ValueError('supplied scaled KKT inventory exceeds budget')
    estimate=1024*(observed.nnz+envelope+10*(n+3))+2*budget.max_total_bits
    if estimate>budget.max_python_work_bytes:
        raise ValueError('state-binding Python workspace estimate exceeds budget')
    f0=shared._vector(f,n,'physical force')
    d0=shared._vector(d,n,'physical displacement scaling')
    q0=shared._vector(q,n,'physical state')
    eta0=shared._vector(eta,3,'physical root multiplier')
    z0=shared._vector(z,n+3,'scaled state')
    b0=shared._vector(b,n+3,'scaled right-hand side')
    hz0=None if h_z is None else shared._vector(h_z,n+3,'saved H_z action')
    if np.any(d0<=0):
        raise ValueError('positive finite displacement scaling required')
    stiffness=ks+kb
    if stiffness.nnz>envelope:
        raise ArithmeticError('sparse sum exceeded preflight inventory')
    actual_envelope=stiffness.nnz+2*cc.nnz
    if actual_envelope>min(sb.max_nnz,budget.max_combined_nnz):
        raise ValueError('physical sparse KKT envelope exceeds budget')
    if observed.nnz+actual_envelope>budget.max_combined_nnz:
        raise ValueError('supplied scaled KKT inventory exceeds budget')
    diagonal=stiffness.diagonal()
    if not np.isfinite(diagonal).all() or np.any(diagonal<=0):
        raise ValueError('positive finite physical stiffness diagonal required')
    root=np.array((1/c.U0,1/c.U0,.46/c.U0),dtype=np.float64)
    if not np.isfinite(root).all() or np.any(root<=0):
        raise ArithmeticError('finite positive root scaling required')
    kbar=_scale(stiffness,d0,d0,c.E0)
    cbar=_scale(cc,root,d0)
    expected=sparse.bmat(((kbar,cbar.T),(cbar,None)),format='csr')
    if expected.nnz>envelope:
        raise ArithmeticError('scaled sparse KKT exceeded preflight inventory')
    fbar=d0*f0/c.E0
    if (not np.isfinite(fbar).all() or np.any((f0!=0)&(fbar==0))):
        raise ArithmeticError('nonfinite or underflowed scaled physical load')
    expected_b=np.r_[fbar,np.zeros(3)]
    bits=_Bits(budget)
    wrong_h,h_difference=_compare_entries(observed,expected,bits)
    wrong_b=int(np.count_nonzero(b0!=expected_b))
    b_difference=F(0)
    for a,v in zip(b0,expected_b):
        if a!=v:
            b_difference=max(b_difference,bits.keep(abs(F.from_float(float(a))-
                                                      F.from_float(float(v)))))
    d_deviation=F(0)
    d_good=True
    q_deviation=eta_deviation=F(0)
    e0=F.from_float(c.E0);u0=F.from_float(c.U0);force=F.from_float(c.F0)
    for index in range(n):
        val=bits.keep(F.from_float(float(d0[index]))**2*
                      F.from_float(float(diagonal[index]))/e0)
        d_deviation=max(d_deviation,bits.keep(abs(val-O)))
        d_good=d_good and (O-D_LIMIT)**2<=val<=(O+D_LIMIT)**2
        diff=bits.keep(abs(F.from_float(float(q0[index]))-
                           F.from_float(float(d0[index]))*
                           F.from_float(float(z0[index])))/u0)
        q_deviation=max(q_deviation,diff)
    for index in range(3):
        diff=bits.keep(abs(F.from_float(float(eta0[index]))-
                           e0*F.from_float(float(root[index]))*
                           F.from_float(float(z0[n+index])))/force)
        eta_deviation=max(eta_deviation,diff)
    action=None if hz0 is None else _max_action(observed,z0,hz0,bits)
    checks={'D_relative_within_1e_12':d_good,
            'q_scaled_max_upper':_upper(q_deviation),
            'eta_scaled_max_upper':_upper(eta_deviation),
            'H_z_absolute_max_upper':None if action is None else _upper(action),
            'H_entry_bit_mismatch_count':wrong_h,
            'b_entry_bit_mismatch_count':wrong_b}
    failures=[]
    if not d_good:failures.append('D differs from the held positive diagonal scaling')
    if q_deviation>STATE_LIMIT:failures.append('physical q and scaled z mismatch')
    if eta_deviation>STATE_LIMIT:failures.append('physical eta and scaled z mismatch')
    if wrong_h:failures.append('full scaled KKT entry bit parity failed')
    if wrong_b:failures.append('full scaled right-hand-side bit parity failed')
    if action is not None and action>ACTION_LIMIT:
        failures.append('saved full H_z action exceeds absolute 1e-11')
    status=('HOLD' if failures else
            'PARTIAL_ACTION_NOT_PROVIDED' if action is None else 'BINDING_PASSED')
    vectors={'f':f0,'D':d0,'q':q0,'eta':eta0,'z':z0,'b':b0}
    if hz0 is not None:vectors['H_z']=hz0
    action_binding=('NOT_PROVIDED' if action is None else
                    'FAILED' if action>ACTION_LIMIT else 'VERIFIED')
    return {'scope':SCOPE,'status':status,'failures':tuple(failures),
            'action_binding':action_binding,
            'checks':checks,
            'raw':{'D_squared_ratio_deviation_upper':_upper(d_deviation),
                   'q_scaled_max_exact':q_deviation,
                   'eta_scaled_max_exact':eta_deviation,
                   'H_z_absolute_max_exact':action,
                   'H_entry_max_abs_difference_upper':_upper(h_difference),
                   'b_entry_max_abs_difference_upper':_upper(b_difference)},
            'input_sha256':{**{name:_hash_sparse(matrix) for name,matrix in
                                (('K_shell',ks),('K_beam',kb),('C_root',cc),
                                 ('H',observed))},
                            **{name:_hash_vector(value) for name,value in vectors.items()}},
            'work':{'physical_primal_dofs':n,'root_rows':3,
                    'physical_pattern_envelope':envelope,
                    'expected_H_nnz':int(expected.nnz),
                    'observed_H_nnz':int(observed.nnz),
                    'python_workspace_estimate_bytes':estimate,
                    'exact_rationals_checked':bits.count,
                    'cumulative_integer_bits':bits.total,
                    'equilibrium_solves':0,'factorizations':0}}
