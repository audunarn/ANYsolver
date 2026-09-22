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
    energy_identity_joule: float
    free_force_scaled_max: float
    weak_gap_scaled_max: float
    integrated_gap_metre: float
    finite_field_component_bounds_metre: tuple[tuple[float,float],...]
    beam_tip_displacement_metre: tuple[float,float,float]


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
    integrated=line.integrated_gap(model,n_beam,n_mortar,qs,qb)
    bounds=enclosure.gap_bounds(model,n_beam,n_mortar,qs,qb,depth)
    tip_raw=beam.trace(n_beam,1.)@qb
    tip=(float(tip_raw[0]),float(tip_raw[1]),
         float(line.YAW_LENGTH*tip_raw[2]))
    values=(shell_energy,beam_energy,external_work,interface_work,
            integrated,*tip)
    if not all(np.isfinite(values)):
        raise ValueError('nonfinite loaded classical observables')
    return LoadedObservables(
        shell_energy_joule=shell_energy,
        beam_energy_joule=beam_energy,
        external_work_joule=external_work,
        interface_work_joule=interface_work,
        energy_identity_joule=2*(shell_energy+beam_energy)+interface_work-external_work,
        free_force_scaled_max=float(np.max(np.abs(residual)/force_scales)),
        weak_gap_scaled_max=float(np.max(np.abs(weak)/weak_scales)),
        integrated_gap_metre=integrated,
        finite_field_component_bounds_metre=bounds,
        beam_tip_displacement_metre=tip)
