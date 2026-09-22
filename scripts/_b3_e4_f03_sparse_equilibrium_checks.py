"""Saved-only sparse numerical equilibrium identities for classical F03.

These checks neither prove the physical operators nor solve a new state.
Six integration/skew comparisons use the candidate's actually rounded scaled
entries as exact real operands. Physical energy uses separate saved shell and
beam entries. The independent binder checks entry and action identities.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import hashlib

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as shared
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_spatial_contract as c


O=F(1);Z=F(0)
INTEGRATION_LIMIT=F.from_float(1e-11)
SKEW_LIMIT=F.from_float(1e-12)
STATIONARITY_LIMIT=F.from_float(1e-10)
ROOT_LIMIT=F.from_float(1e-10)
ENERGY_LIMIT=F.from_float(1e-10)
SCOPE='CLASSICAL_SAVED_SPARSE_NUMERICAL_MECHANICAL_IDENTITIES_ONLY'


@dataclass(frozen=True,slots=True)
class EquilibriumBudget:
    binding_budget:binding.BindingBudget
    max_six_block_nnz:int
    max_fraction_bits:int
    max_total_bits:int
    max_python_work_bytes:int

    def __post_init__(self):
        if type(self.binding_budget) is not binding.BindingBudget or any(
                type(getattr(self,key)) is not int or getattr(self,key)<=0
                for key in ('max_six_block_nnz','max_fraction_bits',
                            'max_total_bits','max_python_work_bytes')):
            raise ValueError('explicit positive equilibrium budgets required')


class _Bits:
    def __init__(self,budget):
        self.budget=budget;self.count=0;self.total=0

    def keep(self,value):
        self.count+=1
        a=value.numerator.bit_length();b=value.denominator.bit_length()
        self.total+=a+b
        if (a>self.budget.max_fraction_bits or b>self.budget.max_fraction_bits
                or self.total>self.budget.max_total_bits):
            raise ValueError('equilibrium rational resource cap exceeded')
        return value


def _hash_sparse(matrix):
    digest=hashlib.sha256(b'F03_EQUILIBRIUM_CSR_V1\0')
    for value,dtype in ((matrix.shape,'<i8'),(matrix.indptr,'<i8'),
                        (matrix.indices,'<i8'),(matrix.data,'<f8')):
        digest.update(np.asarray(value,dtype=dtype).tobytes())
    return digest.hexdigest()


def _sqrt_upper(squared):
    return 0. if squared==0 else shared._sqrt(binding._upper(squared),True)


def _entry(matrix,index,bits):
    return bits.keep(F.from_float(float(matrix.data[index])))


def _norm_squared(matrix,bits):
    total=Z
    for row in range(matrix.shape[0]):
        for index in range(int(matrix.indptr[row]),int(matrix.indptr[row+1])):
            value=_entry(matrix,index,bits)
            total=bits.keep(total+bits.keep(value*value))
    return total


def _difference_squared(first,second,bits):
    total=Z
    for row in range(first.shape[0]):
        i,ie=int(first.indptr[row]),int(first.indptr[row+1])
        j,je=int(second.indptr[row]),int(second.indptr[row+1])
        while i<ie or j<je:
            if j>=je or (i<ie and first.indices[i]<second.indices[j]):
                a=_entry(first,i,bits);b=Z;i+=1
            elif i>=ie or second.indices[j]<first.indices[i]:
                a=Z;b=_entry(second,j,bits);j+=1
            else:
                a=_entry(first,i,bits)
                b=_entry(second,j,bits)
                i+=1;j+=1
            difference=bits.keep(b-a)
            total=bits.keep(total+bits.keep(difference*difference))
    return total


def _skew_squared(matrix,bits):
    transposed=matrix.transpose().tocsr()
    total=Z
    for row in range(matrix.shape[0]):
        i,ie=int(matrix.indptr[row]),int(matrix.indptr[row+1])
        j,je=int(transposed.indptr[row]),int(transposed.indptr[row+1])
        while i<ie or j<je:
            if j>=je or (i<ie and matrix.indices[i]<transposed.indices[j]):
                a=_entry(matrix,i,bits);b=Z;i+=1
            elif i>=ie or transposed.indices[j]<matrix.indices[i]:
                a=Z;b=_entry(transposed,j,bits);j+=1
            else:
                a=_entry(matrix,i,bits)
                b=_entry(transposed,j,bits)
                i+=1;j+=1
            difference=bits.keep(a-b)
            total=bits.keep(total+bits.keep(difference*difference))
    return total


def _quadratic(matrix,q,bits):
    total=Z
    for row in range(matrix.shape[0]):
        action=Z
        for index in range(int(matrix.indptr[row]),int(matrix.indptr[row+1])):
            value=bits.keep(F.from_float(float(matrix.data[index]))*
                            q[int(matrix.indices[index])])
            action=bits.keep(action+value)
        total=bits.keep(total+bits.keep(q[row]*action))
    return total


def _max_residual(matrix,z,b,n,bits):
    maximum=Z
    for row in range(n):
        action=Z
        for index in range(int(matrix.indptr[row]),int(matrix.indptr[row+1])):
            term=bits.keep(F.from_float(float(matrix.data[index]))*
                           z[int(matrix.indices[index])])
            action=bits.keep(action+term)
        maximum=max(maximum,bits.keep(abs(action-b[row])))
    return maximum


def _root_compatibility(root,q,bits):
    r=tuple(F.from_float(float(v)) for v in
            (1/c.U0,1/c.U0,.46/c.U0))
    maximum=Z
    for row in range(3):
        action=Z
        for index in range(int(root.indptr[row]),int(root.indptr[row+1])):
            term=bits.keep(F.from_float(float(root.data[index]))*
                           q[int(root.indices[index])])
            action=bits.keep(action+term)
        maximum=max(maximum,bits.keep(abs(r[row]*action)))
    return maximum


def verify_equilibrium(k_shell,k_beam,k_shell_plus,k_beam_plus,c_root,f,d,h,b,
                       q,eta,z,h_z,*,budget:EquilibriumBudget) -> dict:
    """Bind a complete supplied scaled state and check five numerical gates."""
    if type(budget) is not EquilibriumBudget:
        raise ValueError('explicit equilibrium budget required')
    sb=budget.binding_budget.sparse_budget
    # Validate and cap all six physical blocks before constructing any sum.
    matrices=tuple(shared.validate_sparse(value,sb) for value in
        (k_shell,k_beam,k_shell_plus,k_beam_plus))
    ks,kb,ks2,kb2=matrices
    n=ks.shape[0]
    if any(m.shape!=(n,n) for m in matrices):
        raise ValueError('six matching physical primal blocks required')
    input_nnz=sum(m.nnz for m in matrices)
    # Each derived combined sparse sum has at most the union of its two
    # inputs. Check the complete six-block upper inventory before sums.
    six_upper=2*input_nnz
    if six_upper>budget.max_six_block_nnz:
        raise ValueError('six-block sparse inventory exceeds budget')
    estimate=1024*(6*six_upper+12*(n+3))+2*budget.max_total_bits
    if estimate>budget.max_python_work_bytes:
        raise ValueError('equilibrium Python workspace estimate exceeds budget')
    cc=shared.validate_sparse(c_root,sb,square=False)
    h0=shared.validate_sparse(h,sb)
    f0=shared._vector(f,n,'physical load')
    d0=shared._vector(d,n,'scaling D')
    q0=shared._vector(q,n,'physical q')
    eta0=shared._vector(eta,3,'physical eta')
    z0=shared._vector(z,n+3,'scaled z')
    b0=shared._vector(b,n+3,'scaled b')
    hz0=shared._vector(h_z,n+3,'saved H_z')
    k=ks+kb;k2=ks2+kb2
    six_nnz=input_nnz+k.nnz+k2.nnz
    if six_nnz>six_upper or six_nnz>budget.max_six_block_nnz:
        raise ArithmeticError('sparse sums exceeded preflight six-block inventory')
    # The binder performs its own independent input validation; no cached
    # status dictionary is accepted as authority, and H_z is mandatory here.
    bound=binding.verify_binding(ks,kb,cc,f0,d0,h0,b0,q0,eta0,z0,h_z=hz0,
                                 budget=budget.binding_budget)
    bits=_Bits(budget)
    physical={'shell':(ks,ks2),'beam':(kb,kb2),'combined':(k,k2)}
    blocks={name:(binding._scale(primary,d0,d0,c.E0),
                  binding._scale(alternate,d0,d0,c.E0))
            for name,(primary,alternate) in physical.items()}
    integration={}
    skew={}
    for name,(primary,alternate) in blocks.items():
        base=_norm_squared(primary,bits)
        difference=_difference_squared(primary,alternate,bits)
        ratio=bits.keep(difference/(base if base>0 else O))
        integration[name]={'squared':ratio,'upper':_sqrt_upper(ratio),
                           'within_limit':ratio<=INTEGRATION_LIMIT**2}
        for suffix,matrix in (('',primary),('_plus',alternate)):
            norm=_norm_squared(matrix,bits)
            skew_squared=_skew_squared(matrix,bits)
            relative=bits.keep(skew_squared/(norm if norm>0 else O))
            skew[name+suffix]={'squared':relative,
                               'upper':_sqrt_upper(relative),
                               'within_limit':relative<=SKEW_LIMIT**2}
    zz=tuple(F.from_float(float(value)) for value in z0)
    bb=tuple(F.from_float(float(value)) for value in b0)
    qq=tuple(F.from_float(float(value)) for value in q0)
    primal_residual=_max_residual(h0,zz,bb,n,bits)
    stationarity=bits.keep(primal_residual/
                           max(O,*(abs(v) for v in bb[:n])))
    root_error=_root_compatibility(cc,qq,bits)
    shell_work=_quadratic(ks,qq,bits)
    beam_work=_quadratic(kb,qq,bits)
    strain=bits.keep(shell_work+beam_work)
    combined_work=_quadratic(k,qq,bits)
    work=Z
    for a,v in zip(f0,qq):
        work=bits.keep(work+bits.keep(F.from_float(float(a))*v))
    energy=bits.keep(abs(strain-work)/max(F.from_float(c.E0),abs(strain),abs(work)))
    checks={'integration_energy_relative':max(integration[x]['upper'] for x in blocks),
            'operator_skew_relative':max(value['upper'] for value in skew.values()),
            'stationarity_scaled':binding._upper(stationarity),
            'root_compatibility_scaled':binding._upper(root_error),
            'energy_identity_scaled':binding._upper(energy)}
    failures=[f'integration {name} exceeds 1e-11' for name,value in
              integration.items() if not value['within_limit']]
    failures += [f'{name} scaled skew exceeds 1e-12' for name,value in
                 skew.items() if not value['within_limit']]
    for key,value,limit in (("stationarity_scaled",stationarity,STATIONARITY_LIMIT),
                            ("root_compatibility_scaled",root_error,ROOT_LIMIT),
                            ("energy_identity_scaled",energy,ENERGY_LIMIT)):
        if value>limit:failures.append(f'{key} exceeds frozen numerical limit')
    if bound['status']!='BINDING_PASSED':
        failures.append('physical scaling and saved action binding did not pass')
    return {'scope':SCOPE,
            'status':'NUMERICAL_MECHANICAL_CHECKS_PASSED' if not failures else 'HOLD',
            'failures':tuple(failures),'binding':bound,'checks':checks,
            'integration_blocks':integration,'skew_blocks':skew,
            'raw':{'primal_residual_max_exact':primal_residual,
                   'root_compatibility_max_exact':root_error,
                   'physical_shell_work_exact':shell_work,
                   'physical_beam_work_exact':beam_work,
                   'physical_strain_work_exact':strain,
                   'combined_rounded_work_extra_diagnostic_exact':combined_work,
                   'physical_load_work_exact':work,
                   'energy_identity_ratio_exact':energy},
            'input_sha256':{**bound['input_sha256'],
                            'K_shell_plus':_hash_sparse(ks2),
                            'K_beam_plus':_hash_sparse(kb2)},
            'work':{'physical_dofs':n,'six_block_nnz':int(six_nnz),
                    'six_block_preflight_upper':int(six_upper),
                    'equilibrium_workspace_estimate_bytes':estimate,
                    'exact_rationals_checked':bits.count,
                    'cumulative_integer_bits':bits.total,
                    'new_equilibrium_solves':0,'factorizations':0}}
