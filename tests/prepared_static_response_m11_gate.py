"""Conditional enclosure of every positive-RHS solve admitted by the native gate.

No observed direct solution is an input. Frozen M10 actions supply beta.
"""
from fractions import Fraction as Q
import hashlib
import numpy as np
from scipy import sparse
from prepared_static_response_m10_bounds import (
    SignedActionBound,ZERO,ONE,UNIT,TINY,rational,vector,upward)

class GateRefusal(ValueError): pass

def gamma(count):
    if count*UNIT>=ONE:raise GateRefusal('operation_count')
    return count*UNIT/(ONE-count*UNIT)

def arithmetic_residual_parameters(A,b,tau=1e-10):
    if type(A) is not sparse.csr_matrix or not A.has_canonical_format:
        raise GateRefusal('canonical_CSR_required')
    b=np.asarray(b)
    if A.dtype!=np.dtype('float64') or b.dtype!=np.dtype('float64'):
        raise GateRefusal('represented_binary64_required')
    if b.ndim!=1 or A.shape!=(len(b),len(b)) or len(b)==0:
        raise GateRefusal('shape')
    if not np.all(np.isfinite(A.data)) or not np.all(np.isfinite(b)):
        raise GateRefusal('nonfinite_input')
    if not np.isfinite(tau) or tau<=0:raise GateRefusal('threshold')
    B=max(abs(rational(x)) for x in b)
    # A positive RHS norm keeps the finite checker denominator positive.
    # Zero RHS/nonpositive-denominator branch is deliberately not certified.
    if B==0:raise GateRefusal('zero_RHS_nonpositive_denominator_scope')
    with np.errstate(over='ignore',invalid='ignore'):
        row_values=np.asarray(abs(A).sum(axis=1)).ravel()
    if not np.all(np.isfinite(row_values)):raise GateRefusal('row_sum_overflow')
    exact_rows=[]
    for i,value in enumerate(row_values):
        entries=A.data[A.indptr[i]:A.indptr[i+1]]
        exact=sum((abs(rational(x)) for x in entries),ZERO)
        count=max(1,2*len(entries))
        allowance=gamma(count)*exact+count*TINY/(ONE-count*UNIT)
        if abs(rational(value)-exact)>allowance:
            raise GateRefusal('row_sum_arithmetic_model')
        exact_rows.append(exact)
    normA=max(exact_rows);mhat=rational(max(row_values))
    count=2*max(np.diff(A.indptr))+1
    count=int(count);g=gamma(count)
    acc=count*TINY/(ONE-count*UNIT)
    gd=gamma(2);denadd=2*TINY/(ONE-2*UNIT)
    division=(rational(tau)+TINY)/(ONE-UNIT)
    alpha=division*(ONE+gd)*mhat+g*normA
    zeta=division*((ONE+gd)*B+denadd)+g*B+acc
    return dict(alpha=alpha,zeta=zeta,B=B,normA=normA,mhat=mhat,
                residual_operation_count=count,division_admission=division)

def gate_enclosure(A,b,reconstructed,tau=1e-10):
    # Bind this diagnostic to owned represented arrays. A later checker must use
    # this same operator/RHS and row-sum reduction under stable execution authority.
    if type(A) is not sparse.csr_matrix:raise GateRefusal('canonical_CSR_required')
    A=A.copy();b=np.array(b,copy=True)
    binding=hashlib.sha256()
    for value in (np.array(A.shape,dtype=np.int64),A.indptr,A.indices,A.data,b):
        binding.update(str(value.dtype).encode());binding.update(value.tobytes())
    parameters=arithmetic_residual_parameters(A,b,tau)
    candidate=np.asarray(reconstructed)
    if candidate.shape!=np.asarray(b).shape or not np.all(np.isfinite(candidate)):
        raise GateRefusal('candidate')
    factor=SignedActionBound(A.toarray())
    if not factor.accepted:raise GateRefusal('factor_defect_contraction')
    beta=max(factor.apply([ONE]*len(b)))/(ONE-factor.eta)
    contraction=beta*parameters['alpha']
    result=dict(parameters,eta=factor.eta,beta=beta,contraction=contraction,
                uses_observed_direct=False,represented_input_sha256=binding.hexdigest(),
                row_norm_binding='actual represented CSR absolute-row reduction; same execution identity required')
    if contraction>=ONE:
        result.update(status='INCONCLUSIVE_GATE_CONTRACTION')
        return result
    X=beta*(parameters['B']+parameters['zeta'])/(ONE-contraction)
    exact_residual=max(abs(rational(rhs)-sum((a*rational(x) for a,x in zip(row,candidate)),ZERO)) for row,rhs in zip(factor.A,b))
    radius=beta*(exact_residual+parameters['alpha']*X+parameters['zeta'])
    result.update(status='CONDITIONAL_ENCLOSURE',unknown_solution_norm_upper=X,
                  exact_candidate_residual=exact_residual,radius=radius)
    return result

def report(result):
    return {key:upward(value) if isinstance(value,Q) else value for key,value in result.items()}
