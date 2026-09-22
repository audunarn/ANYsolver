"""Exact sparse interpolation between nested conforming classical Qp spaces.

This proves inclusion of complete finite-dimensional spaces. It does not
declare convergence, choose a mesh hierarchy, solve equilibrium or silently
project a nonnested comparison. No dense global transfer matrix is made.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction as F
import math

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_grid as topology


MAX_WEIGHT_BITS=8192


def _weight_bits(value):
    n=value.numerator.bit_length();d=value.denominator.bit_length()
    if max(n,d)>MAX_WEIGHT_BITS:
        raise ValueError('exact interpolation weight exceeds individual bit bound')
    return n+d


@dataclass(frozen=True,slots=True,init=False)
class ExactProlongation:
    source_dofs: int
    target_dofs: int
    rows: np.ndarray
    columns: np.ndarray
    weights: tuple
    integer_bits: int

    def __init__(self,*args,**kwargs):
        raise TypeError('ExactProlongation requires the validated prolongation factory')

    def matrix(self):
        try: values=np.array(self.weights,dtype=float)
        except OverflowError as exc:
            raise ValueError('unrepresentable exact interpolation weight') from exc
        if not np.isfinite(values).all() or np.any(values==0):
            raise ValueError('nonfinite or underflowed exact interpolation weight')
        return sparse.coo_matrix((values,(self.rows,self.columns)),
            shape=(self.target_dofs,self.source_dofs)).tocsr()

    def apply_exact(self,source):
        if (type(source) not in (tuple,list) or len(source)!=self.source_dofs or
                any(type(v) is not F or max(v.numerator.bit_length(),v.denominator.bit_length())>4096
                    for v in source)):
            raise ValueError('bounded exact source vector required')
        out=[F(0)]*self.target_dofs
        for row,col,weight in zip(self.rows,self.columns,self.weights):
            value=out[row]+weight*source[col]
            _weight_bits(value)
            out[row]=value
        return tuple(out)


def prolongation(source,target,*,max_entries,max_integer_bits,max_work_bytes):
    """Build exact nodal interpolation only after full-space nesting admission."""
    if not isinstance(source,topology.CompiledGrid) or not isinstance(target,topology.CompiledGrid):
        raise ValueError('validated source and target grids required')
    if any(type(v) is not int or v<=0 for v in (max_entries,max_integer_bits,max_work_bytes)):
        raise ValueError('positive integer interpolation budgets required')
    if (target.p<source.p or not set(source.x_cuts).issubset(target.x_cuts) or
            not set(source.y_cuts).issubset(target.y_cuts)):
        raise ValueError('complete conforming spaces are not nested')
    envelope=target.free_dofs*(source.p+1)**2
    if envelope>max_entries:
        raise ValueError('interpolation entry envelope exceeds declared budget')
    if 256*envelope+max_integer_bits//8+32*(target.free_dofs+source.free_dofs)>max_work_bytes:
        raise ValueError('interpolation workspace estimate exceeds declared budget')
    rows=[];columns=[];weights=[];total=0
    sx=len(source.x_nodes);sy=len(source.y_nodes)
    tx=len(target.x_nodes);ty=len(target.y_nodes)
    p=source.p;nodes=tuple(F(i,p) for i in range(p+1))
    def values(coordinate):
        return tuple(math.prod(((coordinate-nodes[k])/(nodes[j]-nodes[k])
                                for k in range(p+1) if k!=j),start=F(1))
                     for j in range(p+1))
    for dest,full_target in enumerate(target.free_to_full):
        component,node=divmod(int(full_target),tx*ty)
        j,i=divmod(node,tx);x=target.x_nodes[i];y=target.y_nodes[j]
        cell_x=min(bisect_right(source.x_cuts,x)-1,len(source.x_cuts)-2)
        cell_y=min(bisect_right(source.y_cuts,y)-1,len(source.y_cuts)-2)
        left,right=source.x_cuts[cell_x:cell_x+2];bottom,top=source.y_cuts[cell_y:cell_y+2]
        if not left<=x<=right or not bottom<=y<=top:
            raise ArithmeticError('target node lies outside its exact source cell')
        bx=values((x-left)/(right-left));by=values((y-bottom)/(top-bottom))
        for lj,vy in enumerate(by):
            for li,vx in enumerate(bx):
                weight=vx*vy
                if not weight: continue
                full=component*sx*sy+(cell_y*p+lj)*sx+cell_x*p+li
                origin=int(source.full_to_free[full])
                if origin<0: continue  # The source value is prescribed exactly zero.
                total+=_weight_bits(weight)
                if total>max_integer_bits:
                    raise ValueError('interpolation aggregate weight storage exceeds declared budget')
                rows.append(dest);columns.append(origin);weights.append(weight)
    result=object.__new__(ExactProlongation)
    vals=(source.free_dofs,target.free_dofs,topology._readonly_int(rows),
          topology._readonly_int(columns),tuple(weights),total)
    for name,value in zip(('source_dofs','target_dofs','rows','columns','weights','integer_bits'),vals):
        object.__setattr__(result,name,value)
    return result
