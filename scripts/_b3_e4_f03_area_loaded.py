"""Small coupled elastic solve for the separate finite-pad F03 preflight.

This path establishes algebraic and physical balance on bounded meshes.
It is neither a converged classical reference nor native B3-GE/E4-PL.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

import _b3_e4_f03_area_line as area
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


@dataclass(frozen=True)
class PreflightResult:
    topology: str
    law: str
    loading: str
    halfwidth_m: float
    displacement_tip_m: tuple[float,float,float]
    shell_energy_j: float
    beam_energy_j: float
    external_work_j: float
    interface_work_j: float
    gap_l2_m: float
    free_residual_scaled: float
    weak_gap_scaled: float
    balance_scaled: tuple[float,float,float]
    support_wrenches: tuple[tuple[float,float,float],...]
    kkt_dimension: int
    kkt_nnz: int


def _edge_wrench(model: shell.Panel, residual: np.ndarray,
                 nodes: np.ndarray) -> tuple[float,float,float]:
    force_x=float(np.sum(residual[2*nodes]))
    force_y=float(np.sum(residual[2*nodes+1]))
    moment=float(np.sum(model.nodes[nodes,0]*residual[2*nodes+1]-
                        model.nodes[nodes,1]*residual[2*nodes]))
    return force_x,force_y,moment


def _gap(model: shell.Panel, n_beam: int, n_mortar: int,
         halfwidth: float, qs: np.ndarray, qb: np.ndarray,
         order: int = 8) -> float:
    knots=area.overlay(model,n_beam,n_mortar,halfwidth)
    roots,weights=np.polynomial.legendre.leggauss(order)
    squared=0.
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=(left+right)/2+(right-left)*root/2
            g=beam.trace(n_beam,s)@qb-port.pose(model,s,halfwidth)@qs
            g[2]*=original.YAW_LENGTH
            squared+=(right-left)*weight/2*float(g@g)
    return math.sqrt(max(squared,0.))


def solve(n_s: int, n_y: int, n_beam: int, n_mortar: int,
          topology: str, law: str, loading: str,
          halfwidth: float) -> PreflightResult:
    if (not 1<=n_s<=4 or not 2<=n_y<=8 or
            not 1<=n_beam<=8 or not 1<=n_mortar<=4 or
            loading not in ("smooth","sine")):
        raise ValueError("outside finite-pad loaded preflight envelope")
    model=shell.panel(n_s,n_y,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(n_beam)
    cs,cb,_=area.coupling(model,n_beam,n_mortar,law,halfwidth)
    k=sparse.block_diag((ks,kb),format="csr")
    c=sparse.hstack((-cs,cb),format="csr")
    f=np.r_[np.zeros(model.dof_count),beam.assembled_load(n_beam,loading)]
    fixed=np.r_[model.supported,model.dof_count+beam.root_dofs(n_beam)]
    free=np.setdiff1d(np.arange(len(f)),fixed)
    scaled=scaling.build(k,c,f,free,model.dof_count,n_beam,n_mortar,law)
    qfree,lam=scaled.recover(splu(scaled.matrix).solve(scaled.rhs))
    q=np.zeros(len(f)); q[free]=qfree
    qs=q[:model.dof_count]; qb=q[model.dof_count:]
    residual=k@q+c.T@lam-f
    weak=c@q
    shell_energy=float(.5*qs@(ks@qs))
    beam_energy=float(.5*qb@(kb@qb))
    work=float(f@q)
    interface=float(lam@weak)
    nx=2*n_s
    left=np.array([j*(nx+1) for j in range(n_y+1)],dtype=int)
    right=left+nx
    beam_reaction=residual[model.dof_count+beam.root_dofs(n_beam)]
    wrenches=(_edge_wrench(model,residual,left),
              _edge_wrench(model,residual,right),
              tuple(map(float,beam_reaction)))
    applied=(0.,scaling.F0,scaling.M0/2) if loading=="smooth" else (
        0.,0.,-scaling.M0/(2*math.pi))
    balance=np.sum(np.asarray(wrenches),axis=0)+applied
    balance=(float(balance[0]/scaling.F0),
             float(balance[1]/scaling.F0),
             float(balance[2]/scaling.M0))
    moment_mask=np.zeros(len(f),dtype=bool)
    u=2*n_beam+1
    v=2*(n_beam+1)
    moment_mask[model.dof_count+u+v:]=True
    moment_mask[model.dof_count+u+1:model.dof_count+u+v:2]=True
    free_scale=np.where(moment_mask[free],scaling.M0,scaling.F0)
    multiplier_measure=np.full(n_mortar+(law=="P1"),1/n_mortar)
    if law=="P1":
        multiplier_measure[[0,-1]]*=.5
    weak_scale=scaling.U0*np.repeat(multiplier_measure,3)
    free_error=float(np.max(np.abs(residual[free])/free_scale))
    weak_error=float(np.max(np.abs(weak)/weak_scale))
    gap=_gap(model,n_beam,n_mortar,halfwidth,qs,qb)
    tip=beam.trace(n_beam,1.)@qb
    tip=(float(tip[0]),float(tip[1]),
         float(original.YAW_LENGTH*tip[2]))
    all_values=(shell_energy,beam_energy,work,interface,gap,free_error,
                weak_error,*balance,*tip,*(v for group in wrenches for v in group))
    if not np.all(np.isfinite(all_values)):
        raise ValueError("nonfinite finite-pad preflight result")
    if abs(2*(shell_energy+beam_energy)+interface-work)>1e-8*scaling.E0:
        raise ValueError("finite-pad energy identity failed")
    return PreflightResult(topology,law,loading,halfwidth,tip,shell_energy,
                           beam_energy,work,interface,gap,free_error,
                           weak_error,balance,wrenches,scaled.matrix.shape[0],
                           scaled.matrix.nnz)
