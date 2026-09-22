"""Bounded loaded observables for the independent classical F03 comparator.

This prepares small mechanical oracles. It does not register or execute the
proposed 96-case qualification inventory and is not a native mixed solver.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

import _b3_e4_f03_gap_enclosure as enclosure
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


@dataclass(frozen=True)
class LoadedObservables:
    shell_energy_joule: float
    beam_energy_joule: float
    external_work_joule: float
    interface_work_joule: float
    shell_interface_work_joule: float
    beam_interface_work_joule: float
    energy_identity_joule: float
    free_force_scaled_max: float
    weak_gap_scaled_max: float
    integrated_gap_metre: float  # RMS over the normalized one-metre line.
    motion_rms_metre: float
    fixed_scale_gap: float
    motion_scale_gap: float
    finite_field_component_bounds_metre: tuple[tuple[float,float],...]
    beam_tip_displacement_metre: tuple[float,float,float]
    shell_station_displacements_metre: tuple[tuple[float,float,float],...]
    support_wrenches: tuple[tuple[float,float,float],...]
    applied_resultant: tuple[float,float,float]
    global_balance_scaled: tuple[float,float,float]


def _motion_integrals(model: shell.Panel, n_beam: int, n_mortar: int,
                      qs: np.ndarray, qb: np.ndarray, order: int = 4
                      ) -> tuple[float,float]:
    """Return integrated squared gap and mean squared two-sided motion."""
    if not 4<=order<=8:
        raise ValueError('unadmitted motion quadrature')
    roots,weights=np.polynomial.legendre.leggauss(order)
    gap_squared=motion_squared=0.
    knots=line.overlay(model,n_beam,n_mortar)
    for a,b in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=float((a+b)/2+(b-a)*root/2)
            pb=beam.trace(n_beam,s)@qb
            ps=shell.pose(model,s)@qs
            pb[2]*=line.YAW_LENGTH; ps[2]*=line.YAW_LENGTH
            gap=pb-ps
            quadrature=(b-a)*weight/2
            gap_squared+=quadrature*float(gap@gap)
            motion_squared+=quadrature*float((pb@pb+ps@ps)/2)
    return max(0.,gap_squared),max(0.,motion_squared)


def _wrench(reaction: np.ndarray, nodes: np.ndarray,
            ids: np.ndarray) -> tuple[float,float,float]:
    forces=reaction[np.column_stack((2*ids,2*ids+1))]
    positions=nodes[ids]
    return (float(np.sum(forces[:,0])),float(np.sum(forces[:,1])),
            float(np.sum(positions[:,0]*forces[:,1]-
                         positions[:,1]*forces[:,0])))


def evaluate(n_s: int, n_y: int, n_beam: int, n_mortar: int,
             topology: str, law: str, loading: str,
             *, depth: int = 8) -> LoadedObservables:
    """Solve one support-eliminated signed KKT and recover physical metrics.

    The individual classical operators remain separately implemented. The
    scaling is a symmetric congruence, and all reported metrics use the
    recovered physical solution, not the scaled algebraic unknowns.
    """
    if (loading not in ('smooth','sine') or
            not isinstance(n_s,int) or not 1<=n_s<=4 or
            not isinstance(n_y,int) or not 2<=n_y<=8 or
            not isinstance(n_beam,int) or not 1<=n_beam<=8 or
            not isinstance(n_mortar,int) or not 1<=n_mortar<=4 or
            not isinstance(depth,int) or not 0<=depth<=8):
        raise ValueError('outside bounded classical loaded preflight')
    model=shell.panel(n_s,n_y,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(n_beam)
    cs,cb,_=line.coupling(model,n_beam,n_mortar,law)
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    f=np.r_[np.zeros(model.dof_count),beam.assembled_load(n_beam,loading)]
    fixed=np.r_[model.supported,model.dof_count+beam.root_dofs(n_beam)]
    free=np.setdiff1d(np.arange(k.shape[0]),fixed)
    transformed=scaling.build(k,c,f,free,model.dof_count,n_beam,n_mortar,law)
    solved=splu(transformed.matrix).solve(transformed.rhs)
    qfree,lam=transformed.recover(solved)
    q=np.zeros(k.shape[0]); q[free]=qfree
    qs=q[:model.dof_count]; qb=q[model.dof_count:]
    residual=(k@q+c.T@lam-f)[free]
    full_residual=k@q+c.T@lam-f
    weak=c@q
    moment=transformed.angular_free_mask
    force_scales=np.where(moment,scaling.M0,scaling.F0)
    measure=np.full(n_mortar+(law=='P1'),scaling.L0/n_mortar)
    if law=='P1':
        measure[[0,-1]]*=.5
    weak_scales=scaling.U0*np.repeat(measure,3)
    shell_energy=float(qs@(ks@qs)/2)
    beam_energy=float(qb@(kb@qb)/2)
    external_work=float(f@q)
    interface_work=float(lam@weak)
    shell_interface_work=float(-lam@(cs@qs))
    beam_interface_work=float(lam@(cb@qb))
    if abs(shell_interface_work+beam_interface_work-interface_work)>1e-10*max(
            scaling.E0,abs(shell_interface_work),abs(beam_interface_work)):
        raise ValueError('interface side-work assembly discrepancy')
    integrated=line.integrated_gap(model,n_beam,n_mortar,qs,qb)
    integrated_squared,motion_squared=_motion_integrals(
        model,n_beam,n_mortar,qs,qb)
    # Independent floating quadrature paths must agree for this degree-six
    # continuous FE gap on the exact host/beam/mortar overlay.
    if abs(integrated_squared-integrated**2)>1e-10*max(scaling.U0**2,integrated_squared):
        raise ValueError('independent integrated-gap quadrature mismatch')
    motion_rms=float(np.sqrt(motion_squared/scaling.L0))
    g2=float(np.sqrt(integrated_squared)/(scaling.U0*np.sqrt(scaling.L0)))
    gmotion=float(np.sqrt(integrated_squared)/
                  (max(motion_rms,.1*scaling.U0)*np.sqrt(scaling.L0)))
    bounds=enclosure.gap_bounds(model,n_beam,n_mortar,qs,qb,depth)
    tip_raw=beam.trace(n_beam,1.)@qb
    tip=(float(tip_raw[0]),float(tip_raw[1]),
         float(line.YAW_LENGTH*tip_raw[2]))
    stations=[]
    for s in (.25,.5,.75):
        pose=shell.pose(model,s)@qs
        stations.append((float(pose[0]),float(pose[1]),
                         float(line.YAW_LENGTH*pose[2])))
    nx=2*n_s
    left=np.array([j*(nx+1) for j in range(n_y+1)],dtype=int)
    right=left+nx
    left_wrench=_wrench(full_residual,model.nodes,left)
    right_wrench=_wrench(full_residual,model.nodes,right)
    root=model.dof_count+beam.root_dofs(n_beam)
    beam_wrench=(float(full_residual[root[0]]),
                 float(full_residual[root[1]]),
                 float(full_residual[root[2]]))
    wrenches=(left_wrench,right_wrench,beam_wrench)
    # Rigid translation and rotation test fields recover the resultant of
    # the *consistent assembled* distributed force, including slope work.
    xmode=np.zeros_like(f); ymode=np.zeros_like(f); rotation=np.zeros_like(f)
    xmode[:model.dof_count:2]=1
    ymode[1:model.dof_count:2]=1
    rotation[:model.dof_count:2]=-model.nodes[:,1]
    rotation[1:model.dof_count:2]=model.nodes[:,0]
    u0=model.dof_count; beam_u=2*n_beam+1; beam_v=2*(n_beam+1)
    xmode[u0:u0+beam_u]=1
    ymode[u0+beam_u:u0+beam_u+beam_v:2]=1
    rotation[u0+beam_u:u0+beam_u+beam_v:2]=np.arange(n_beam+1)/n_beam
    rotation[u0+beam_u+1:u0+beam_u+beam_v:2]=1
    rotation[u0+beam_u+beam_v:]=1
    applied=(float(f@xmode),float(f@ymode),float(f@rotation))
    net=np.sum(np.asarray(wrenches),axis=0)+np.asarray(applied)
    balance=(float(net[0]/scaling.F0),float(net[1]/scaling.F0),
             float(net[2]/scaling.M0))
    values=(shell_energy,beam_energy,external_work,interface_work,
            shell_interface_work,beam_interface_work,
            integrated,motion_rms,g2,gmotion,*tip,*applied,*balance,
            *(item for wrench in wrenches for item in wrench),
            *(item for station in stations for item in station))
    if not all(np.isfinite(values)):
        raise ValueError('nonfinite loaded classical observables')
    return LoadedObservables(
        shell_energy_joule=shell_energy,
        beam_energy_joule=beam_energy,
        external_work_joule=external_work,
        interface_work_joule=interface_work,
        shell_interface_work_joule=shell_interface_work,
        beam_interface_work_joule=beam_interface_work,
        energy_identity_joule=2*(shell_energy+beam_energy)+interface_work-external_work,
        free_force_scaled_max=float(np.max(np.abs(residual)/force_scales)),
        weak_gap_scaled_max=float(np.max(np.abs(weak)/weak_scales)),
        integrated_gap_metre=integrated,
        motion_rms_metre=motion_rms,
        fixed_scale_gap=g2,
        motion_scale_gap=gmotion,
        finite_field_component_bounds_metre=bounds,
        beam_tip_displacement_metre=tip,
        shell_station_displacements_metre=tuple(stations),
        support_wrenches=wrenches,
        applied_resultant=applied,
        global_balance_scaled=balance)
