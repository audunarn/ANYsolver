"""Saved-state Q4 variational attribution for nested classical finite pads.

The physical beam prolongation evaluates its P2 axial/yaw fields and
Hermite transverse field plus independent derivative at every fine DOF.
This is a matrix-action diagnostic, with no equilibrium or Schur solve.
Only Q4 nesting is asserted; CST-CB is outside this construction.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import sparse

import _b3_e4_f03_area_hybrid as hybrid
import _b3_e4_f03_area_line as line
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


def _bounded(n_s: int, n_y: int, n_beam: int) -> None:
    if (any(type(n) is not int for n in (n_s,n_y,n_beam)) or
            not 1<=n_s<=8 or not 2<=n_y<=16 or not 1<=n_beam<=16):
        raise ValueError('outside bounded nested Q4 physical spaces')


def _shell_prolongation(n_s: int, n_y: int) -> sparse.csr_matrix:
    coarse_nx=2*n_s
    fine_nx=2*coarse_nx
    n_coarse=(coarse_nx+1)*(n_y+1)
    n_fine=(fine_nx+1)*(2*n_y+1)
    rows=[]; cols=[]; values=[]
    for jf in range(2*n_y+1):
        jc=min(jf//2,n_y-1)
        ty=(jf-2*jc)/2
        for ifine in range(fine_nx+1):
            ic=min(ifine//2,coarse_nx-1)
            tx=(ifine-2*ic)/2
            bl=jc*(coarse_nx+1)+ic
            corners=((bl,(1-tx)*(1-ty)),(bl+1,tx*(1-ty)),
                     (bl+coarse_nx+2,tx*ty),(bl+coarse_nx+1,(1-tx)*ty))
            fine_node=jf*(fine_nx+1)+ifine
            for coarse_node,weight in corners:
                if weight:
                    for axis in (0,1):
                        rows.append(2*fine_node+axis)
                        cols.append(2*coarse_node+axis)
                        values.append(weight)
    matrix=sparse.coo_matrix((values,(rows,cols)),shape=(2*n_fine,2*n_coarse)).tocsr()
    matrix.sum_duplicates()
    return matrix


def _beam_prolongation(n_beam: int) -> sparse.csr_matrix:
    fine_elements=2*n_beam
    coarse_count=beam.dof_count(n_beam)
    fine_count=beam.dof_count(fine_elements)
    fine_u=2*fine_elements+1
    fine_v=2*(fine_elements+1)
    rows=[]; cols=[]; values=[]

    def add(row: int, indices: np.ndarray, weights: np.ndarray) -> None:
        for index,weight in zip(indices,weights):
            if weight:
                rows.append(row); cols.append(int(index)); values.append(float(weight))

    for k in range(2*fine_elements+1):
        coarse_element=min(k//4,n_beam-1)
        xi=(k-4*coarse_element)/4
        ids=beam.element_dofs(n_beam,coarse_element)
        field,_=beam.fields(xi,1/n_beam)
        add(k,ids[:3],field[0,:3])
        add(fine_u+fine_v+k,ids[7:],field[2,7:])
    for k in range(fine_elements+1):
        coarse_element=min(k//2,n_beam-1)
        xi=(k-2*coarse_element)/2
        ids=beam.element_dofs(n_beam,coarse_element)
        field,strain=beam.fields(xi,1/n_beam)
        add(fine_u+2*k,ids[3:7],field[1,3:7])
        # The Hermite derivative is an independent physical nodal slope.
        # Strain row 2 also has -theta, hence restrict to columns 3:7.
        add(fine_u+2*k+1,ids[3:7],strain[2,3:7])
    matrix=sparse.coo_matrix((values,(rows,cols)),
                             shape=(fine_count,coarse_count)).tocsr()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    return matrix


def nested_q4_prolongation(n_s: int, n_y: int, n_beam: int) -> sparse.csr_matrix:
    """Sparse physical q map to the exactly doubled Q4/beam mesh.

    Displacement values and beam v slopes are interpolated as their own
    physical functionals. Fine supports map only to coarse supported DOFs;
    the beam's independent root v slope is not clamped.
    """
    _bounded(n_s,n_y,n_beam)
    p=sparse.block_diag((_shell_prolongation(n_s,n_y),
                         _beam_prolongation(n_beam)),format='csr')
    coarse=shell.panel(n_s,n_y,'Q4')
    fine=shell.panel(2*n_s,2*n_y,'Q4')
    fixed_c=np.r_[coarse.supported,coarse.dof_count+beam.root_dofs(n_beam)]
    fixed_f=np.r_[fine.supported,fine.dof_count+beam.root_dofs(2*n_beam)]
    free_c=np.setdiff1d(np.arange(p.shape[1]),fixed_c)
    leakage=p[fixed_f,:][:,free_c].tocsr()
    leakage.eliminate_zeros()
    if leakage.nnz:
        raise ValueError('nested Q4 prolongation violates physical supports')
    return p


def _fine_constraint(model: shell.Panel, n_beam: int, n_mortar: int,
                     family: str, halfwidth: float) -> sparse.csr_matrix:
    cs,cb,_=line.coupling(model,n_beam,n_mortar,'P1',halfwidth)
    if family=='P1':
        pass
    elif family=='hybrid':
        operators=hybrid.assemble(model,n_beam,n_mortar,halfwidth)
        cs,cb=operators.cs,operators.cb
    elif family=='enriched':
        yaw=sparse.diags((1.,1.,original.YAW_LENGTH),format='csr')
        ends=sparse.vstack((yaw@port.pose(model,0.,halfwidth),
                            yaw@port.pose(model,1.,halfwidth)),format='csr')
        beam_ends=sparse.vstack((yaw@beam.trace(n_beam,0.),
                                 yaw@beam.trace(n_beam,1.)),format='csr')
        cs=sparse.vstack((cs,ends),format='csr')
        cb=sparse.vstack((cb,beam_ends),format='csr')
    else:
        raise ValueError('invalid finite-pad multiplier family')
    return sparse.hstack((-cs,cb),format='csr')


def _owned_state(value: np.ndarray, size: int, name: str) -> np.ndarray:
    if (not isinstance(value,np.ndarray) or value.dtype!=np.float64 or
            value.shape!=(size,) or not np.all(np.isfinite(value))):
        raise ValueError(f'invalid saved physical {name}')
    return value.copy()


def attribute_saved_states(n_s: int, n_y: int, n_beam: int, n_mortar: int,
                           family: str, q_middle: np.ndarray, q_fine: np.ndarray,
                           lambda_fine: np.ndarray, *, halfwidth: float = .05
                           ) -> tuple[dict,dict[str,np.ndarray | sparse.csr_matrix]]:
    """Return potential-energy attribution and owned matrix/action evidence.

    On the fine mesh r=Kf*qf+Cf.T*lambda_f-ff, v=P*qm, e=v-qf, and
    Pi_f(v)-Pi_f(qf)=.5*e.T*Kf*e-lambda_f.T*Cf*e+e.T*r.
    No equilibrium factorization, multiplier solve or acceptance test occurs.
    """
    _bounded(n_s,n_y,n_beam)
    if (type(n_mortar) is not int or not 2<=n_mortar<=8 or
            family not in ('P1','hybrid','enriched') or
            not math.isfinite(halfwidth) or not 1e-4<=halfwidth<=.2):
        raise ValueError('outside bounded Q4 attribution case')
    coarse=shell.panel(n_s,n_y,'Q4')
    fine=shell.panel(2*n_s,2*n_y,'Q4')
    kc=sparse.block_diag((shell.stiffness(coarse),
                          beam.assembled_stiffness(n_beam)),format='csr')
    kf=sparse.block_diag((shell.stiffness(fine),
                          beam.assembled_stiffness(2*n_beam)),format='csr')
    fc=np.r_[np.zeros(coarse.dof_count),beam.assembled_load(n_beam,'smooth')]
    ff=np.r_[np.zeros(fine.dof_count),beam.assembled_load(2*n_beam,'smooth')]
    cf=_fine_constraint(fine,2*n_beam,2*n_mortar,family,halfwidth)
    p=nested_q4_prolongation(n_s,n_y,n_beam)
    qm=_owned_state(q_middle,kc.shape[0],'middle q')
    qf=_owned_state(q_fine,kf.shape[0],'fine q')
    lam=_owned_state(lambda_fine,cf.shape[0],'fine multiplier')
    fixed_c=np.r_[coarse.supported,coarse.dof_count+beam.root_dofs(n_beam)]
    fixed_f=np.r_[fine.supported,fine.dof_count+beam.root_dofs(2*n_beam)]
    if np.any(qm[fixed_c]!=0.) or np.any(qf[fixed_f]!=0.):
        raise ValueError('saved physical state violates existing supports')
    v=np.asarray(p@qm)
    e=v-qf
    kfe=np.asarray(kf@e)
    cfe=np.asarray(cf@e)
    cfq=np.asarray(cf@qf)
    cfv=np.asarray(cf@v)
    cftlam=np.asarray(cf.T@lam)
    kfq=np.asarray(kf@qf)
    kcq=np.asarray(kc@qm)
    r=kfq+cftlam-ff
    nsc=coarse.dof_count
    nsf=fine.dof_count
    shell_distance=float(.5*e[:nsf]@kfe[:nsf])
    beam_distance=float(.5*e[nsf:]@kfe[nsf:])
    mismatch=float(-lam@cfe)
    residual_work=float(e@r)
    kfv=np.asarray(kf@v)
    middle_shell=float(.5*qm[:nsc]@kcq[:nsc])
    middle_beam=float(.5*qm[nsc:]@kcq[nsc:])
    prolonged_shell=float(.5*v[:nsf]@kfv[:nsf])
    prolonged_beam=float(.5*v[nsf:]@kfv[nsf:])
    fine_shell=float(.5*qf[:nsf]@kfq[:nsf])
    fine_beam=float(.5*qf[nsf:]@kfq[nsf:])
    middle_energy=middle_shell+middle_beam
    prolonged_energy=prolonged_shell+prolonged_beam
    fine_energy=fine_shell+fine_beam
    middle_load=float(fc@qm)
    prolonged_load=float(ff@v)
    fine_load=float(ff@qf)
    direct=(prolonged_energy-prolonged_load)-(fine_energy-fine_load)
    attributed=shell_distance+beam_distance+mismatch+residual_work
    potential_v=prolonged_energy-prolonged_load
    potential_f=fine_energy-fine_load
    identity_error=direct-attributed
    identity_denominator=max(scaling.E0,abs(potential_v)+abs(potential_f)+
                             abs(shell_distance+beam_distance)+abs(mismatch)+
                             abs(residual_work))
    observed=np.array((shell_distance,beam_distance,mismatch,residual_work,
                       middle_energy,prolonged_energy,fine_energy,
                       middle_load,prolonged_load,fine_load,direct,attributed))
    if (not np.all(np.isfinite(observed)) or
            any(not np.all(np.isfinite(a)) for a in (r,cfe,cfq,cfv,cftlam,kfe))):
        raise ValueError('nonfinite Q4 saved-state attribution action')
    metrics={
        'family':family,
        'middle_mesh':[n_s,n_y,n_beam,n_mortar],
        'fine_mesh':[2*n_s,2*n_y,2*n_beam,2*n_mortar],
        'halfwidth_m':halfwidth,
        'shell_dofs_coarse':nsc,
        'shell_dofs_fine':nsf,
        'shell_distance_j':shell_distance,
        'beam_distance_j':beam_distance,
        'constraint_mismatch_work_j':mismatch,
        'residual_work_j':residual_work,
        'direct_potential_change_j':direct,
        'attributed_potential_change_j':attributed,
        'prolonged_fine_potential_j':potential_v,
        'fine_potential_j':potential_f,
        'identity_error_j':identity_error,
        'identity_denominator_j':identity_denominator,
        'identity_defect_scaled':abs(identity_error)/identity_denominator,
        'middle_elastic_energy_j':middle_energy,
        'prolonged_fine_elastic_energy_j':prolonged_energy,
        'fine_elastic_energy_j':fine_energy,
        'middle_shell_energy_j':middle_shell,
        'middle_beam_energy_j':middle_beam,
        'prolonged_fine_shell_energy_j':prolonged_shell,
        'prolonged_fine_beam_energy_j':prolonged_beam,
        'fine_shell_energy_j':fine_shell,
        'fine_beam_energy_j':fine_beam,
        'shell_energy_preservation_error_j':prolonged_shell-middle_shell,
        'beam_energy_preservation_error_j':prolonged_beam-middle_beam,
        'elastic_energy_preservation_error_j':prolonged_energy-middle_energy,
        'middle_load_work_j':middle_load,
        'prolonged_fine_load_work_j':prolonged_load,
        'fine_load_work_j':fine_load,
        'load_work_preservation_error_j':prolonged_load-middle_load,
        'fixed_dof_count_coarse':len(fixed_c),
        'fixed_dof_count_fine':len(fixed_f),
        'prolonged_fixed_max_abs':float(np.max(np.abs(v[fixed_f]))),
        'fine_free_residual_max':float(np.max(np.abs(r[
            np.setdiff1d(np.arange(len(r)),fixed_f)]))),
        'fine_constraint_max_abs_mixed_units':float(np.max(np.abs(cfq))),
    }
    actions={'P':p.copy(),'K_coarse':kc.copy(),'K_fine':kf.copy(),
             'C_fine':cf.copy(),'f_coarse':fc.copy(),'f_fine':ff.copy(),
             'q_middle':qm.copy(),'q_fine':qf.copy(),
             'lambda_fine':lam.copy(),'prolonged_q':v.copy(),'e':e.copy(),
             'Kf_e':kfe.copy(),'Cf_e':cfe.copy(),'r_fine':np.asarray(r).copy(),
             'Kc_qmiddle':kcq.copy(),'Kf_qfine':kfq.copy(),
             'Kf_prolonged_q':kfv.copy(),'Cf_qfine':cfq.copy(),
             'Cf_prolonged_q':cfv.copy(),'CfT_lambda':cftlam.copy()}
    return metrics,actions
