"""Bounded sparse classical membrane / exact area-trace beam assembly.

This is an operator experiment, not a native element, equilibrium driver or
scientific execution registration. Required budgets are explicit. Local
trace cliques can grow under refinement; sparse storage implies no linear
complexity claim. No inverse, factorization or global dense matrix is made.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import math
from types import MappingProxyType

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_moments as moments
from scripts import _b3_e4_f03_local_shell as membrane
from scripts import _b3_e4_f03_spatial_contract as c


@dataclass(frozen=True,slots=True)
class AssemblyBudget:
    max_trace_dofs: int
    max_triplets: int
    max_work_bytes: int
    max_trace_integer_bits: int

    def __post_init__(self):
        if any(type(v) is not int or v<=0 for v in
               (self.max_trace_dofs,self.max_triplets,self.max_work_bytes,
                self.max_trace_integer_bits)):
            raise ValueError('positive integer assembly budgets are required')


@dataclass(frozen=True,slots=True,init=False)
class ExactTrace:
    left: F
    right: F
    degree: int
    indices: np.ndarray
    coefficients: tuple
    integer_bits: int

    def __init__(self,*args,**kwargs):
        raise TypeError('ExactTrace requires the validated trace_interval factory')

    def derivative_coefficients(self,order=0):
        if type(order) is not int or order not in (0,1,2):
            raise ValueError('physical derivative order 0..2 required')
        width=self.right-self.left
        return tuple(tuple(tuple(poly[k]*F(math.factorial(k),math.factorial(k-order))
            /width**order for k in range(order,len(poly))) for poly in channel)
            for channel in self.coefficients)

    def evaluate_exact(self,tau,order=0):
        if not moments._coordinate(tau) or not F(0)<=tau<=F(1):
            raise ValueError('bounded exact local tau in [0,1] required')
        return tuple(tuple(sum((v*tau**k for k,v in enumerate(poly)),F(0))
                     for poly in channel) for channel in self.derivative_coefficients(order))

    def evaluate(self,tau,order=0):
        value=np.asarray(tau,dtype=float)
        if not np.isfinite(value).all() or np.any(value<0) or np.any(value>1):
            raise ValueError('finite local tau in [0,1] required')
        exact=self.derivative_coefficients(order)
        try: coefficients=np.asarray(exact,dtype=float)
        except OverflowError as exc:
            raise ValueError('unrepresentable assembled trace coefficients') from exc
        if (not np.isfinite(coefficients).all() or
                any(v!=0 and converted==0 for row,converted_row in zip(exact,coefficients)
                    for poly,converted_poly in zip(row,converted_row)
                    for v,converted in zip(poly,converted_poly))):
            raise ValueError('unrepresentable assembled trace coefficients')
        result=np.zeros(value.shape+(3,len(self.indices)))
        for k in reversed(range(coefficients.shape[-1])):
            result=result*value[...,None,None]+coefficients[:,:,k]
        if not np.isfinite(result).all():
            raise ValueError('nonfinite assembled trace evaluation')
        return result


def _bits(value):
    return value.numerator.bit_length()+value.denominator.bit_length()


def trace_interval(grid,index,budget):
    """Assemble exact free-coordinate pose polynomials on one station interval."""
    if (not isinstance(grid,topology.CompiledGrid) or not isinstance(budget,AssemblyBudget)
            or type(index) is not int or not 0<=index<len(grid.trace_incidence)):
        raise ValueError('validated grid, interval and assembly budget required')
    indices=grid.trace_incidence[index];n=len(indices);degree=grid.p+2
    if n>budget.max_trace_dofs:
        raise ValueError('active trace DOFs exceed declared budget')
    total=3*n*(degree+1)  # Each exact zero has a one-bit denominator.
    if total>budget.max_trace_integer_bits:
        raise ValueError('initial trace rational storage exceeds declared budget')
    # The full assembly preflight covers this bounded scratch. This local
    # factory also checks it when used directly in synthetic operator tests.
    scratch=768*3*n*(degree+1)+budget.max_trace_integer_bits//8
    if scratch>budget.max_work_bytes:
        raise ValueError('local trace scratch exceeds declared work budget')
    coefficients=[[[F(0)]*(degree+1) for _ in range(n)] for _ in range(3)]
    positions={int(v):i for i,v in enumerate(indices)}
    a,b=grid.station_cuts[index:index+2];middle=(a+b)/2
    for rect,gather in zip(grid.rectangles,grid.free_gathers):
        if not any(max(rect.x0,middle+l)<min(rect.x1,middle+r) and
                   max(rect.y0,yl)<min(rect.y1,yr) for l,r,yl,yr in c.PADS):
            continue
        local=moments.trace_segment(rect,grid.p,a,b)
        for j,dof in enumerate(gather):
            if dof<0: continue
            dest=positions[int(dof)]
            for channel in range(3):
                for k,value in enumerate(local.coefficients[channel][j]):
                    if not value: continue
                    old=coefficients[channel][dest][k];new=old+value
                    nb=max(new.numerator.bit_length(),new.denominator.bit_length())
                    total+=_bits(new)-_bits(old)
                    if nb>moments.TRACE_COEFFICIENT_BITS or total>budget.max_trace_integer_bits:
                        raise ValueError('assembled trace rational storage exceeds declared budget')
                    coefficients[channel][dest][k]=new
    result=object.__new__(ExactTrace)
    values=(a,b,degree,topology._readonly_int(indices),
            tuple(tuple(tuple(p) for p in row) for row in coefficients),total)
    for name,value in zip(('left','right','degree','indices','coefficients','integer_bits'),values):
        object.__setattr__(result,name,value)
    return result


def _positive_width(trace):
    width=float(trace.right-trace.left)
    if not math.isfinite(width) or width<=0:
        raise ValueError('unrepresentable positive trace interval')
    return width


def beam_interval(trace,*,extra_order=False):
    """Integrated native-independent Timoshenko beam energy Hessian.

    p+3 Gauss points integrate degree 2p+4 exactly in exact arithmetic.
    The p+4 option is an independent integration-order check, not fallback.
    """
    if not isinstance(trace,ExactTrace) or type(extra_order) is not bool:
        raise ValueError('owned exact trace and boolean order control required')
    order=trace.degree+1+int(extra_order)
    z,w=np.polynomial.legendre.leggauss(order);z=(z+1)/2;w=w/2
    b=trace.evaluate(z);db=trace.evaluate(z,1)
    strains=np.stack((db[:,0,:],db[:,1,:]-b[:,2,:],db[:,2,:]),axis=1)
    measure=_positive_width(trace)*w
    if np.any(measure<np.finfo(float).tiny):
        raise ValueError('beam quadrature measure is not normal binary64')
    constitutive=np.array((c.EA,c.GAS,c.EI))
    result=np.einsum('gci,gc,gcj->ij',strains,measure[:,None]*constitutive[None,:],
                     strains,optimize=False)
    if not np.isfinite(result).all():
        raise ValueError('nonfinite local beam energy Hessian')
    return result


def load_interval(trace,order=48):
    """Held physical transverse line load pulled back through this same trace."""
    if not isinstance(trace,ExactTrace) or type(order) is not int or order not in (48,64):
        raise ValueError('owned exact trace and fixed load order 48/64 required')
    z,w=np.polynomial.legendre.leggauss(order);z=(z+1)/2;w=w/2
    width=_positive_width(trace);measure=width*w
    if np.any(measure<np.finfo(float).tiny):
        raise ValueError('load quadrature measure is not normal binary64')
    # Retain the local shift even when the two global endpoints round equal.
    phase=c.OMEGA*float(trace.left);shift=c.OMEGA*width*z
    cosine=np.cos(phase)*np.cos(shift)-np.sin(phase)*np.sin(shift)
    load=c.F0/c.L0*(1+cosine/4)
    result=np.einsum('g,gi->i',measure*load,trace.evaluate(z)[:,1,:],optimize=False)
    if not np.isfinite(result).all():
        raise ValueError('nonfinite local pulled-back load')
    return result


def _rank(rows):
    matrix=[list(row) for row in rows];pivot=0
    for column in range(len(matrix[0])):
        chosen=next((j for j in range(pivot,len(matrix)) if matrix[j][column]),None)
        if chosen is None: continue
        matrix[pivot],matrix[chosen]=matrix[chosen],matrix[pivot]
        divisor=matrix[pivot][column];matrix[pivot]=[v/divisor for v in matrix[pivot]]
        for j in range(pivot+1,len(matrix)):
            factor=matrix[j][column]
            matrix[j]=[v-factor*w for v,w in zip(matrix[j],matrix[pivot])]
        pivot+=1
        if pivot==len(matrix): break
    return pivot


def root_operator(trace,physical_dofs):
    """Three exact root restrictions, with an independently free v'(0)."""
    if not isinstance(trace,ExactTrace) or trace.left!=0:
        raise ValueError('root interval required')
    if type(physical_dofs) is not int or physical_dofs<=0 or np.any(trace.indices>=physical_dofs):
        raise ValueError('valid full physical free-coordinate count required')
    root=trace.evaluate_exact(F(0));slope=trace.evaluate_exact(F(0),1)[1]
    if _rank(root)!=3 or _rank((*root,slope))!=4:
        raise ValueError('root pose rank3 and independent transverse slope rank4 required')
    n=len(trace.indices)
    result=sparse.coo_matrix((np.asarray(root,dtype=float).ravel(),
        (np.repeat(np.arange(3),n),np.tile(trace.indices,3))),shape=(3,physical_dofs)).tocsr()
    result.eliminate_zeros()
    if not np.isfinite(result.data).all(): raise ValueError('nonfinite root operator')
    return result


def preflight(grid,budget):
    if not isinstance(grid,topology.CompiledGrid) or not isinstance(budget,AssemblyBudget):
        raise ValueError('validated grid and explicit assembly budget required')
    active=max(map(len,grid.trace_incidence),default=0)
    if active>budget.max_trace_dofs: raise ValueError('active trace DOFs exceed declared budget')
    shell=sum(int(np.count_nonzero(g>=0))**2 for g in grid.free_gathers)
    beam=sum(len(v)**2 for v in grid.trace_incidence)
    root=6*len(grid.trace_incidence[0])
    total=shell+beam+root
    if total>budget.max_triplets: raise ValueError('assembly triplets exceed declared budget')
    # Conservative implementation envelope, not a factor workspace or RSS
    # certificate. Numerical run admission must also monitor actual memory.
    work=(160*total+128*(grid.free_dofs+4)+128*active**2+
          768*3*active*(grid.p+3)+budget.max_trace_integer_bits//8+64*64*active)
    if work>budget.max_work_bytes: raise ValueError('assembly workspace estimate exceeds declared budget')
    return {'shell_triplets':shell,'beam_triplets':beam,'root_triplets_envelope':root,
            'triplets_envelope':total,'workspace_estimate_bytes':work,
            'max_active_trace_dofs':active,'station_intervals':len(grid.trace_incidence),
            'physical_dofs':grid.free_dofs,'root_multipliers':3,
            'scope':'bounded assembly preflight; no factorization or RSS guarantee'}


@dataclass(frozen=True,slots=True,init=False)
class AssembledPrimal:
    """Factory-owned operator; public matrix/vector access returns fresh copies."""
    _shell: sparse.csr_matrix
    _beam: sparse.csr_matrix
    _root: sparse.csr_matrix
    _load: np.ndarray
    _diagnostics: object

    def __init__(self,*args,**kwargs):
        raise TypeError('AssembledPrimal requires the validated assemble factory')

    @property
    def shell(self): return self._shell.copy()

    @property
    def beam(self): return self._beam.copy()

    @property
    def root(self): return self._root.copy()

    @property
    def load(self): return self._load.copy()

    @property
    def diagnostics(self): return self._diagnostics

    def stiffness(self): return self._shell+self._beam

    def kkt(self):
        return sparse.bmat(((self.stiffness(),self._root.T),(self._root,None)),format='csc')


def assemble(grid,budget,*,extra_beam_order=False,load_order=48):
    """Stream local blocks into sparse matrices. Does not solve any equation."""
    if type(extra_beam_order) is not bool or type(load_order) is not int or load_order not in (48,64):
        raise ValueError('fixed assembly quadrature controls required')
    info=preflight(grid,budget)
    first=trace_interval(grid,0,budget);root=root_operator(first,grid.free_dofs)
    def allocate(count): return (np.empty(count,dtype=np.int64),np.empty(count,dtype=np.int64),np.empty(count))
    shell_data=allocate(info['shell_triplets']);beam_data=allocate(info['beam_triplets'])
    def insert(arrays,offset,indices,block):
        n=len(indices);end=offset+n*n
        arrays[0][offset:end]=np.repeat(indices,n);arrays[1][offset:end]=np.tile(indices,n)
        arrays[2][offset:end]=block.ravel()
        return end
    offset=0
    for rect,gather in zip(grid.rectangles,grid.free_gathers):
        keep=np.flatnonzero(gather>=0);indices=gather[keep]
        block=membrane.stiffness(rect,grid.p)[np.ix_(keep,keep)]
        offset=insert(shell_data,offset,indices,block)
    if offset!=info['shell_triplets']: raise ArithmeticError('shell incidence inventory mismatch')
    force=np.zeros(grid.free_dofs);offset=0;max_bits=0
    for i in range(len(grid.trace_incidence)):
        trace=first if i==0 else trace_interval(grid,i,budget)
        block=beam_interval(trace,extra_order=extra_beam_order)
        offset=insert(beam_data,offset,trace.indices,block)
        np.add.at(force,trace.indices,load_interval(trace,load_order))
        max_bits=max(max_bits,trace.integer_bits)
    if offset!=info['beam_triplets']: raise ArithmeticError('beam incidence inventory mismatch')
    def finish(arrays):
        r,col,data=arrays
        result=sparse.coo_matrix((data,(r,col)),shape=(grid.free_dofs,grid.free_dofs)).tocsr()
        result.sum_duplicates();result.eliminate_zeros()
        if not np.isfinite(result.data).all(): raise ValueError('nonfinite assembled matrix')
        return result
    shell=finish(shell_data);beam=finish(beam_data)
    if not np.isfinite(force).all(): raise ValueError('nonfinite assembled physical load')
    info.update(shell_nnz=shell.nnz,beam_nnz=beam.nnz,root_nnz=root.nnz,
        shell_evaluations=len(grid.rectangles),trace_evaluations=len(grid.trace_incidence),
        beam_evaluations=len(grid.trace_incidence),load_evaluations=len(grid.trace_incidence),
        max_trace_integer_bits=max_bits,beam_order=grid.p+3+int(extra_beam_order),load_order=load_order,
        factorization_count=0,equilibrium_count=0)
    result=object.__new__(AssembledPrimal)
    # Matrices were created here and have no external aliases. Keep their
    # storage private; all public accessors return independently owned copies.
    owned_force=np.frombuffer(force.tobytes(),dtype=np.float64)
    for name,value in zip(('_shell','_beam','_root','_load','_diagnostics'),
                          (shell,beam,root,owned_force,MappingProxyType(dict(info)))):
        object.__setattr__(result,name,value)
    return result
