"""Bounded exact-multiplier line work for a distinct finite-pad F03 model.

Pad halfwidth is fixed in physical metres; this preflight does not select
a production interface, admit all material states, or qualify convergence.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import sparse

import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


def overlay(model: shell.Panel, n_beam: int, n_mortar: int,
            halfwidth: float) -> np.ndarray:
    """Split moving pad edges at shell cell and triangle-diagonal events."""
    beam.dof_count(n_beam)
    if not isinstance(n_mortar,int) or not 1<=n_mortar<=16:
        raise ValueError("bounded mortar count required")
    if not math.isfinite(halfwidth) or not 1e-4<=halfwidth<=.2:
        raise ValueError("fixed physical pad halfwidth required")
    knots=[0.,1.]
    knots.extend(i/n_beam for i in range(1,n_beam))
    knots.extend(i/n_mortar for i in range(1,n_mortar))
    for dx,dy in shell.OFFSETS:
        for side in (-1,1):
            edge=dx+side*halfwidth
            knots.extend(-.5+i/model.n_s-edge
                         for i in range(2*model.n_s+1))
            if model.topology in ("CST","CST-CB"):
                for yedge in (dy-halfwidth,dy+halfwidth):
                    for j in range(model.n_y):
                        y0=-.5+j/model.n_y
                        fraction=(yedge-y0)*model.n_y
                        if not 0<=fraction<=1:
                            continue
                        for i in range(2*model.n_s):
                            position=(1-fraction if model.topology=="CST-CB"
                                      and (i+j)%2 else fraction)
                            diagonal=-.5+(i+position)/model.n_s
                            knots.append(diagonal-edge)
    ordered=sorted(min(max(float(k),0.),1.) for k in knots
                   if math.isfinite(k) and -1e-12<=k<=1+1e-12)
    result=[0.]
    for point in ordered:
        if point-result[-1]>1e-12:
            result.append(point)
    if 1-result[-1]>1e-12:
        result.append(1.)
    else:
        result[-1]=1.
    values=np.asarray(result)
    if np.any(np.diff(values)<=0):
        raise ValueError("invalid pad line overlay")
    return values


def coupling(model: shell.Panel, n_beam: int, n_mortar: int,
             law: str, halfwidth: float, order: int = 6
             ) -> tuple[sparse.csr_matrix,sparse.csr_matrix,np.ndarray]:
    """Assemble ∫ N_lambda (T_beam−T_pad) ds with consistent adjoints."""
    if law not in ("P0","P1") or not isinstance(order,int) or not 4<=order<=10:
        raise ValueError("unadmitted pad line law or integration order")
    knots=overlay(model,n_beam,n_mortar,halfwidth)
    basis=n_mortar+(law=="P1")
    rows_s=[]; cols_s=[]; values_s=[]
    rows_b=[]; cols_b=[]; values_b=[]
    roots,weights=np.polynomial.legendre.leggauss(order)
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            station=(left+right)/2+(right-left)*root/2
            measure=(right-left)*weight/2
            ps=port.pose(model,station,halfwidth)
            pb=beam.trace(n_beam,station)
            for index,test in original.mortar_tests(n_mortar,law,station):
                factor=measure*test
                for channel,scale in enumerate((1.,1.,original.YAW_LENGTH)):
                    row=3*index+channel
                    st=ps.getrow(channel).tocoo()
                    bt=pb.getrow(channel).tocoo()
                    rows_s.extend([row]*st.nnz)
                    cols_s.extend(st.col)
                    values_s.extend(factor*scale*st.data)
                    rows_b.extend([row]*bt.nnz)
                    cols_b.extend(bt.col)
                    values_b.extend(factor*scale*bt.data)
    cs=sparse.coo_matrix((values_s,(rows_s,cols_s)),
                         shape=(3*basis,model.dof_count)).tocsr()
    cb=sparse.coo_matrix((values_b,(rows_b,cols_b)),
                         shape=(3*basis,beam.dof_count(n_beam))).tocsr()
    cs.sum_duplicates(); cb.sum_duplicates()
    return cs,cb,knots
