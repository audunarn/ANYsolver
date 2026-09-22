"""Segmented classical beam/plane-stress variational line for F03 preflight.

This is an independent small-strain reference operator, not the native
B3-GE/E4-PL connection or a qualified multiplier-space selection.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell


YAW_LENGTH = .46


def overlay(model: shell.Panel, n_beam: int, n_mortar: int) -> np.ndarray:
    """Reference breaks of beam, multiplier and every shell sample host."""
    beam.dof_count(n_beam)
    if not isinstance(n_mortar,int) or not 1<=n_mortar<=128:
        raise ValueError('unsupported mortar resolution')
    knots=[0.,1.]
    knots.extend(i/n_beam for i in range(1,n_beam))
    knots.extend(i/n_mortar for i in range(1,n_mortar))
    nx=2*model.n_s
    for dx,dy in shell.OFFSETS:
        for i in range(nx+1):
            knots.append(-.5+i/model.n_s-dx)
        if model.topology in ('CST','CST-CB'):
            # At fixed sample y, every BL→TR diagonal is one x crossing.
            j=min(max(int(np.floor((dy+.5)*model.n_y-1e-12)),0),model.n_y-1)
            y0=-.5+j/model.n_y
            fraction=(dy-y0)*model.n_y
            for i in range(nx):
                diagonal=(1-fraction if model.topology=='CST-CB' and (i+j)%2
                          else fraction)
                knots.append(-.5+(i+diagonal)/model.n_s-dx)
    ordered=sorted(min(max(float(value),0.),1.) for value in knots
                   if np.isfinite(value) and -1e-12<=value<=1+1e-12)
    result=[0.]
    for value in ordered:
        if value-result[-1]>1e-12:
            result.append(value)
    if 1-result[-1]>1e-12:
        result.append(1.)
    else:
        result[-1]=1.
    positions=np.asarray(result)
    if np.any(np.diff(positions)<=0):
        raise ValueError('invalid reference overlay intervals')
    for a,b in zip(positions[:-1],positions[1:]):
        left=a+(b-a)/4
        right=a+3*(b-a)/4
        for dx,dy in shell.OFFSETS:
            if shell.sample(model,left+dx,dy)[0]!=shell.sample(model,right+dx,dy)[0]:
                raise ValueError('overlay misses a shell sample host change')
        if min(int(left*n_beam),n_beam-1)!=min(int(right*n_beam),n_beam-1):
            raise ValueError('overlay misses a beam boundary')
        if min(int(left*n_mortar),n_mortar-1)!=min(int(right*n_mortar),n_mortar-1):
            raise ValueError('overlay misses a mortar boundary')
    return positions


def mortar_tests(n_mortar: int, law: str, s: float) -> tuple[tuple[int,float],...]:
    if law not in ('P0','P1') or not 0<=s<=1:
        raise ValueError('unadmitted reference mortar row')
    cell=min(int(s*n_mortar),n_mortar-1)
    if law=='P0':
        return ((cell,1.),)
    xi=s*n_mortar-cell
    return ((cell,1-xi),(cell+1,xi))


def coupling(model: shell.Panel, n_beam: int, n_mortar: int,
             law: str, order: int = 4) -> tuple[sparse.csr_matrix,sparse.csr_matrix,np.ndarray]:
    """Return shell/beam positive trace matrices; the gap is Cb qb-Cs qs."""
    if law not in ('P0','P1') or not 3<=order<=8:
        raise ValueError('unadmitted mortar law or quadrature')
    knots=overlay(model,n_beam,n_mortar)
    basis=n_mortar+(1 if law=='P1' else 0)
    rows_s=[]; cols_s=[]; values_s=[]
    rows_b=[]; cols_b=[]; values_b=[]
    roots,weights=np.polynomial.legendre.leggauss(order)
    for a,b in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=float((a+b)/2+(b-a)*root/2)
            measure=(b-a)*weight/2
            ps=shell.pose(model,s)
            pb=beam.trace(n_beam,s)
            for index,test in mortar_tests(n_mortar,law,s):
                factor=measure*test
                for channel,scale in enumerate((1.,1.,YAW_LENGTH)):
                    row=3*index+channel
                    st=ps.getrow(channel).tocoo()
                    bt=pb.getrow(channel).tocoo()
                    rows_s.extend([row]*st.nnz)
                    cols_s.extend(st.col)
                    values_s.extend(factor*scale*st.data)
                    rows_b.extend([row]*bt.nnz)
                    cols_b.extend(bt.col)
                    values_b.extend(factor*scale*bt.data)
    shape_s=(3*basis,model.dof_count)
    shape_b=(3*basis,beam.dof_count(n_beam))
    cs=sparse.coo_matrix((values_s,(rows_s,cols_s)),shape=shape_s).tocsr()
    cb=sparse.coo_matrix((values_b,(rows_b,cols_b)),shape=shape_b).tocsr()
    cs.sum_duplicates(); cb.sum_duplicates()
    return cs,cb,knots


def integrated_gap(model: shell.Panel, n_beam: int, n_mortar: int,
                   qs: np.ndarray, qb: np.ndarray, order: int = 4) -> float:
    """Physical L2 gap of the *continuous fields*, not weak row residuals."""
    if (np.shape(qs)!=(model.dof_count,) or
            np.shape(qb)!=(beam.dof_count(n_beam),) or
            not np.all(np.isfinite(qs)) or not np.all(np.isfinite(qb)) or
            not 4<=order<=8):
        raise ValueError('invalid finite reference gap fields or quadrature')
    knots=overlay(model,n_beam,n_mortar)
    roots,weights=np.polynomial.legendre.leggauss(order)
    squared=0.
    for a,b in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=float((a+b)/2+(b-a)*root/2)
            gap=beam.trace(n_beam,s)@qb-shell.pose(model,s)@qs
            gap[2]*=YAW_LENGTH
            squared+=(b-a)*weight/2*float(gap@gap)
    return float(np.sqrt(max(squared,0.)))
