"""Bind saved classical port matrices/actions to exact local trace extraction.

This performs bounded verification preparation, not an equilibrium trial.
The physical shell/beam equations and scientific admission remain separate.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_spatial_contract as c

ZERO=F(0);ONE=F(1);LIMIT=F.from_float(1e-11)
STATIONS=tuple(F(i,8) for i in range(9))
KEYS=tuple((s,order,'left' if s==1 else 'right')
           for order in range(3) for s in STATIONS)


@dataclass(frozen=True,slots=True)
class SavedPort:
    station: F
    order: int
    side: str
    operator: object
    action: np.ndarray


@dataclass(frozen=True,slots=True)
class TraceBindingBudget:
    sparse_budget: common.SparseBudget
    trace_budget: assembly.AssemblyBudget
    max_input_nnz: int
    max_fraction_bits: int
    max_total_bits: int
    max_work_bytes: int

    def __post_init__(self):
        if (type(self.sparse_budget) is not common.SparseBudget or
            type(self.trace_budget) is not assembly.AssemblyBudget or
            any(type(x) is not int or x<=0 for x in (self.max_input_nnz,
                self.max_fraction_bits,self.max_total_bits,self.max_work_bytes))):
            raise ValueError('explicit trace-binding resource budgets required')


class _Exact:
    def __init__(self,budget):self.budget=budget;self.total=0;self.count=0
    def keep(self,value):
        a=value.numerator.bit_length();b=value.denominator.bit_length()
        self.total+=a+b;self.count+=1
        if max(a,b)>self.budget.max_fraction_bits or self.total>self.budget.max_total_bits:
            raise ValueError('trace-binding exact arithmetic budget exceeded')
        return value


def _upper(value):
    out=float(value)
    if not math.isfinite(out):raise ArithmeticError('unrepresentable trace metric')
    if F.from_float(out)<value:out=float(np.nextafter(out,np.inf))
    if not math.isfinite(out):raise ArithmeticError('unrepresentable trace metric')
    return out


def _hash_array(array):
    digest=hashlib.sha256(np.asarray(array.shape,dtype='<i8').tobytes())
    digest.update(np.asarray(array,dtype='<f8').tobytes());return digest.hexdigest()


def _grid_identity(grid):
    digest=hashlib.sha256(b'F03_EXACT_TENSOR_TRACE_GRID_V1\0')
    for label,values in (('x',grid.x_cuts),('y',grid.y_cuts),('s',grid.station_cuts)):
        digest.update(label.encode())
        for value in values:digest.update(f'{value.numerator}/{value.denominator};'.encode())
    digest.update(f'p={grid.p};n={grid.free_dofs};'.encode())
    digest.update(np.asarray(grid.free_to_full,dtype='<i8').tobytes())
    return digest.hexdigest()


def _entries(matrix,row):
    return {int(matrix.indices[j]):F.from_float(float(matrix.data[j]))
            for j in range(int(matrix.indptr[row]),int(matrix.indptr[row+1]))}


def _comparison(matrix,expected,q,d,row_scale,exact):
    difference=norm=ZERO;max_entry=ZERO;observed_action=[];reference_action=[]
    for row,reference in enumerate(expected):
        observed=_entries(matrix,row);a=b=ZERO
        for index in sorted(observed.keys()|reference.keys()):
            v=observed.get(index,ZERO);w=reference.get(index,ZERO)
            delta=exact.keep(v-w);max_entry=max(max_entry,abs(delta))
            scale=exact.keep(row_scale[row]*d[index])
            delta_scaled=exact.keep(delta*scale);ref_scaled=exact.keep(w*scale)
            difference=exact.keep(difference+exact.keep(delta_scaled**2))
            norm=exact.keep(norm+exact.keep(ref_scaled**2))
            a=exact.keep(a+exact.keep(v*q[index]))
            b=exact.keep(b+exact.keep(w*q[index]))
        observed_action.append(exact.keep(a*row_scale[row]))
        reference_action.append(exact.keep(b*row_scale[row]))
    ratio_squared=exact.keep(difference/max(ONE,norm))
    denominator=max((ONE,*map(abs,observed_action),*map(abs,reference_action)))
    action_error=exact.keep(max(abs(a-b) for a,b in zip(observed_action,reference_action))/denominator)
    return ratio_squared,max_entry,tuple(observed_action),tuple(reference_action),action_error


def verify_trace_binding(grid,q,d,samples,root,tip,slope,*,budget):
    """Bind the frozen 9 x 3 observations and root/tip/free-slope operators.

    At internal cuts, right traces are used; at s=1 the left trace is used.
    The second derivative may jump. Samples cannot select another convention.
    """
    if type(grid) is not topology.CompiledGrid or type(budget) is not TraceBindingBudget:
        raise ValueError('compiled exact grid and trace-binding budget required')
    if type(samples) not in (tuple,list) or len(samples)!=len(KEYS):
        raise ValueError('complete frozen nine-station three-derivative inventory required')
    samples=tuple(samples)
    for sample,key in zip(samples,KEYS):
        if (type(sample) is not SavedPort or type(sample.station) is not F or
            type(sample.order) is not int or
            (sample.station,sample.order,sample.side)!=key):
            raise ValueError('ordered exact station, derivative and side inventory required')
    n=grid.free_dofs
    if n>budget.sparse_budget.max_order:raise ValueError('trace coordinates exceed sparse budget')
    # Inventory and workspace preflight precede retaining copied sparse inputs.
    inputs=tuple(sample.operator for sample in samples)+(root,tip,slope)
    nnz=0
    for value in inputs:
        if type(value) not in (sparse.csr_matrix,sparse.csc_matrix):
            raise ValueError('CSR/CSC trace matrices required')
        nnz+=len(value.data)
    if nnz>budget.max_input_nnz:raise ValueError('trace input nnz budget exceeded')
    workspace=(1024*(nnz+32*n)+2*budget.max_total_bits+
               9*budget.trace_budget.max_work_bytes)
    if workspace>budget.max_work_bytes:raise ValueError('trace-binding workspace budget exceeded')
    matrices=tuple(common.validate_sparse(value,budget.sparse_budget,square=False) for value in inputs)
    if any(matrix.shape!=(3,n) for matrix in matrices[:-1]) or matrices[-1].shape!=(1,n):
        raise ValueError('three pose rows and one free-slope row required')
    saved=tuple(common._vector(sample.action,3,'saved trace action') for sample in samples)
    q0=common._vector(q,n,'trace physical state');d0=common._vector(d,n,'trace scaling')
    if np.any(d0<=0):raise ValueError('positive trace coordinate scaling required')
    exact=_Exact(budget)
    qq=tuple(exact.keep(F.from_float(float(v))) for v in q0)
    dd=tuple(exact.keep(F.from_float(float(v))) for v in d0)
    rr=tuple(F.from_float(float(v)) for v in (1/c.U0,1/c.U0,.46/c.U0))
    cache={};endpoint={};checks=[];failures=[]
    for item,(sample,matrix,action) in enumerate(zip(samples,matrices,saved)):
        s=sample.station;index=min(bisect_right(grid.station_cuts,s)-1,len(grid.station_cuts)-2)
        if sample.side=='left' and index>0 and s==grid.station_cuts[index]:index-=1
        if index not in cache:cache[index]=assembly.trace_interval(grid,index,budget.trace_budget)
        trace=cache[index];tau=(s-trace.left)/(trace.right-trace.left)
        values=trace.evaluate_exact(tau,sample.order)
        expected=tuple({int(j):exact.keep(v) for j,v in zip(trace.indices,row) if v} for row in values)
        scale=tuple(exact.keep(v*F.from_float(c.L0)**sample.order) for v in rr)
        ratio,entry,observed,reference,action_error=_comparison(matrix,expected,qq,dd,scale,exact)
        scaled_saved=tuple(exact.keep(F.from_float(float(v))*r) for v,r in zip(action,scale))
        denominator=max((ONE,*map(abs,reference),*map(abs,scaled_saved)))
        saved_error=exact.keep(max(abs(a-b) for a,b in zip(scaled_saved,reference))/denominator)
        if ratio>LIMIT**2:failures.append(f'port {item}: exact trace matrix mismatch')
        if action_error>LIMIT:failures.append(f'port {item}: operator action mismatch')
        if saved_error>LIMIT:failures.append(f'port {item}: saved action mismatch')
        checks.append({'key':KEYS[item],'matrix_scaled_ratio_squared_upper':_upper(ratio),
                       'operator_action_scaled_upper':_upper(action_error),
                       'saved_action_scaled_upper':_upper(saved_error)})
        if (s,sample.order) in ((ZERO,0),(ONE,0),(ZERO,1)):
            endpoint[s,sample.order]=expected
    endpoints={}
    for name,matrix,expected,scale,station_matrix,station_rows in (
        ('root',matrices[-3],endpoint[ZERO,0],ONE,matrices[0],(0,1,2)),
        ('tip',matrices[-2],endpoint[ONE,0],ONE,matrices[8],(0,1,2)),
        ('free_slope',matrices[-1],(endpoint[ZERO,1][1],),F.from_float(c.L0),matrices[9],(1,))):
        # Preserve the original maximum-entry endpoint scaling (all channels).
        _,entry,*_=_comparison(matrix,expected,qq,dd,(ONE,)*len(expected),exact)
        error=exact.keep(entry*max(dd)*scale/F.from_float(c.U0))
        station_expected=tuple(_entries(station_matrix,row) for row in station_rows)
        _,direct_entry,observed,reference,_=_comparison(matrix,station_expected,qq,dd,
                                                        (ONE,)*len(expected),exact)
        direct_error=exact.keep(direct_entry*max(dd)*scale/F.from_float(c.U0))
        direct_action=exact.keep(max(abs(a-b) for a,b in zip(observed,reference))*scale/F.from_float(c.U0))
        endpoints[name]={'exact_operator_scaled_upper':_upper(error),
                         'saved_station_operator_scaled_upper':_upper(direct_error),
                         'saved_station_action_scaled_upper':_upper(direct_action)}
        if error>LIMIT:failures.append(f'{name}: exact endpoint operator mismatch')
        if direct_error>LIMIT:failures.append(f'{name}: saved station operator mismatch')
        if direct_action>LIMIT:failures.append(f'{name}: saved station action mismatch')
    return {'status':'TRACE_BINDING_PASSED' if not failures else 'HOLD',
            'scope':'EXACT_CLASSICAL_TRACE_EXTRACTION_ONLY_NOT_EQUILIBRIUM',
            'failures':tuple(failures),'checks':tuple(checks),'endpoints':endpoints,
            'input_sha256':{'grid':_grid_identity(grid),'q':_hash_array(q0),'D':_hash_array(d0),
                'operators':tuple(binding._hash_sparse(m) for m in matrices),
                'saved_actions':tuple(_hash_array(a) for a in saved)},
            'work':{'exact_intervals_extracted':len(cache),'station_operators':27,
                    'input_nnz':nnz,'workspace_estimate_bytes':workspace,
                    'fraction_checks':exact.count,'cumulative_integer_bits':exact.total,
                    'equilibrium_solves':0,'native_element_evaluations':0}}
