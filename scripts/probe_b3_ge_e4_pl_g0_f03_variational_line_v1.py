"""Independent classical beam/membrane line-law pilot, not F03 acceptance.

The beam is a conforming exact-static Timoshenko trial space on subcells.
Distributed loads and P0 multiplier traction both act through its *same*
interior trial field. Refining subcells resolves their omitted particular
response; no q-only bubble is added to a continuously constrained solve.
The shell is independent classical plane-stress Q4/CST, not E4-PL.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

import numpy as np
from scipy import linalg,sparse
from scipy.sparse.linalg import spsolve

import probe_b3_ge_e4_pl_g0_f03_resolved_continuum as reference
from probe_b3_ge_e4_pl_g0_f03_resolved_sparse_v5 import shell_trace


def coupling(topology,n_shell,n_y,n_beam,n_mortar,kind,law,order=4):
    points,ks,sf=reference.panel(n_shell,n_y,topology)
    kb,bf=reference.beam(n_beam)
    fs=np.zeros(ks.shape[0])
    fb=reference.load_vector(n_beam,kind)
    n_basis=n_mortar+1 if law=='weak-p1' else n_mortar
    shell_groups=[sparse.csr_matrix((3,ks.shape[0])) for _ in range(n_basis)]
    beam_groups=[np.zeros((3,kb.shape[0])) for _ in range(n_basis)]
    knots=np.unique(np.r_[reference.gap_knots(n_shell,n_y,n_beam,topology),
                           np.arange(n_mortar+1)/n_mortar])
    if not np.all(np.diff(knots)>0):
        raise ValueError('invalid common beam/shell/reference overlay')
    roots,weights=np.polynomial.legendre.leggauss(order)
    for a,b in zip(knots[:-1],knots[1:]):
        cell=min(int((a+b)*.5*n_mortar),n_mortar-1)
        for root,weight in zip(roots,weights):
            s=float((a+b)/2+(b-a)*root/2)
            w=(b-a)*weight/2
            shell=shell_trace(s,n_shell,n_y,topology,len(points))
            beam=reference.beam_trace(s,n_beam)
            if law=='weak-p1':
                xi=s*n_mortar-cell
                tests=((cell,1-xi),(cell+1,xi))
            else:
                tests=((cell,1.),)
            for index,test in tests:
                shell_groups[index]+=w*test*shell
                beam_groups[index]+=w*test*beam
    return (points,ks,sf,kb,bf,fs,fb,
            sparse.vstack(shell_groups,format='csr'),
            sparse.csr_matrix(np.vstack(beam_groups)),len(knots)-1)


def station_coupling(topology,n_shell,n_y,n_beam,n_mortar,points,ks,kb,
                     include_root):
    stations=np.arange(0 if include_root else 1,n_mortar+1)/n_mortar
    cs=sparse.vstack([shell_trace(float(s),n_shell,n_y,topology,len(points))
                      for s in stations],format='csr')
    cb=sparse.csr_matrix(np.vstack([reference.beam_trace(float(s),n_beam)
                                    for s in stations]))
    return cs,cb


def solve(topology,n_shell,n_y,n_mortar,subcells,kind,law):
    if n_shell<1 or n_y<2 or n_mortar<2 or subcells<1:
        raise ValueError('bounded positive mesh resolution required')
    n_beam=n_mortar*subcells
    (points,ks,sf,kb,bf,fs,fb,integral_shell,integral_beam,
     overlay_count)=coupling(topology,n_shell,n_y,n_beam,n_mortar,kind,law)
    if law in ('weak-p0','weak-p1'):
        cs,cb=integral_shell,integral_beam
    elif law in ('station','station-no-root'):
        cs,cb=station_coupling(topology,n_shell,n_y,n_beam,n_mortar,
                               points,ks,kb,law=='station')
    else:
        raise ValueError('unknown line law')
    c=sparse.hstack((-cs[:,sf],cb[:,bf]),format='csr')
    c.eliminate_zeros()
    row_norm=np.sqrt(np.asarray(c.multiply(c).sum(axis=1)).ravel())
    if np.any(row_norm<=0):
        raise ValueError('zero constrained row')
    gram=(c@c.T).toarray()/row_norm[:,None]/row_norm[None,:]
    eigen=linalg.eigvalsh(gram)
    if eigen[0]<=1e-12*eigen[-1]:
        raise ValueError('independent comparator constraints lack full row rank')
    k=sparse.block_diag((ks[sf,:][:,sf],kb[bf,:][:,bf]),format='csr')
    load=np.r_[fs[sf],fb[bf]]
    coord_scale=1e-5
    work_scale=10.
    gap_scale=1e-5
    system=sparse.bmat(((k*coord_scale**2/work_scale,
                         c.T*coord_scale/gap_scale),
                        (c*coord_scale/gap_scale,None)),format='csc')
    solution=spsolve(system,np.r_[load*coord_scale/work_scale,
                                  np.zeros(c.shape[0])])
    if not np.all(np.isfinite(solution)):
        raise ValueError('nonfinite independent line result')
    u=solution[:len(load)]*coord_scale
    lam=solution[len(load):]*work_scale/gap_scale
    us=np.zeros(ks.shape[0]); us[sf]=u[:len(sf)]
    ub=np.zeros(kb.shape[0]); ub[bf]=u[len(sf):]
    shell_reaction=ks@us-cs.T@lam-fs
    beam_reaction=kb@ub+cb.T@lam-fb
    shell_fixed=np.setdiff1d(np.arange(ks.shape[0]),sf)
    support_x=float(shell_reaction[shell_fixed[0::2]].sum()+beam_reaction[0])
    support_y=float(shell_reaction[shell_fixed[1::2]].sum()+beam_reaction[1])
    support_moment=float(sum(points[i,0]*shell_reaction[2*i+1]
                             -points[i,1]*shell_reaction[2*i]
                             for i in range(len(points)) if 2*i in shell_fixed)
                         +beam_reaction[2])
    external_moment=float(sum((i/n_beam)*fb[3*i+1]+fb[3*i+2]
                              for i in range(n_beam+1)))
    expected_force,expected_moment=(
        (1e6,5e5) if kind=='smooth' else (0.,-1e6/(2*np.pi)))
    if (abs(float(fb[1::3].sum())-expected_force)>1e-6 or
        abs(external_moment-expected_moment)>1e-6):
        raise ValueError('distributed-load force or moment quadrature mismatch')
    shell_work=float(lam@(cs@us))
    beam_work=float(-lam@(cb@ub))
    work=float(load@u)
    shell_energy=float(us@ks@us/2)
    beam_energy=float(ub@kb@ub/2)
    eq=k@u+c.T@lam-load
    weak_gap=c@u
    displacement_scale=1e6/(reference.E*.07)
    length_scale=1.
    weak_gap_scale=displacement_scale*(length_scale if law.startswith('weak-') else 1.)
    physical_weak_gap=weak_gap.reshape(-1,3)*np.array((1.,1.,.46))
    sample_knots=np.unique(np.r_[reference.gap_knots(
        n_shell,n_y,n_beam,topology),np.arange(n_mortar+1)/n_mortar])
    sampled=np.unique(np.concatenate([
        np.linspace(a,b,17) for a,b in zip(sample_knots[:-1],sample_knots[1:])]))
    max_gap=np.zeros(3)
    probes=[]
    for s in sampled:
        shell=shell_trace(float(s),n_shell,n_y,topology,len(points))@us
        beam=reference.beam_trace(float(s),n_beam)@ub
        max_gap=np.maximum(max_gap,np.abs(beam-shell))
    for s in (0.,.125,.25,.5,.75,.875,1.):
        shell=shell_trace(s,n_shell,n_y,topology,len(points))@us
        beam=reference.beam_trace(s,n_beam)@ub
        probes.append({'s':s,'shell':[float(v) for v in shell],
                       'beam':[float(v) for v in beam],
                       'gap':[float(v) for v in beam-shell]})
    return {'model':'INDEPENDENT_CLASSICAL_BEAM_MEMBRANE_VARIATIONAL_PILOT',
            'topology':topology,'n_shell':n_shell,'n_y':n_y,
            'n_beam':n_beam,'n_mortar':n_mortar,'subcells':subcells,
            'load':kind,'law':law,'shell_nodes':len(points),
            'physical_unknowns':len(load),'multiplier_rows':c.shape[0],
            'matrix_nnz':system.nnz,'overlay_intervals':overlay_count,
            'row_normalized_gram_ratio':float(eigen[0]/eigen[-1]),
            'external_force_y_n':float(fb[1::3].sum()),
            'external_moment_z_nm':external_moment,
            'load_resultant_force_error_n':float(fb[1::3].sum()-expected_force),
            'load_resultant_moment_error_nm':external_moment-expected_moment,
            'support_force_x_n':support_x,'support_force_y_n':support_y,
            'support_moment_z_nm':support_moment,
            'force_balance_relative':float(abs(support_y+fb[1::3].sum())/
                                           max(np.linalg.norm(fb),1)),
            'force_x_balance_relative':float(abs(support_x)/
                                             max(np.linalg.norm(fb),1)),
            'moment_balance_relative':float(abs(support_moment+external_moment)/
                                            max(abs(external_moment),1)),
            'shell_energy_j':shell_energy,'beam_energy_j':beam_energy,
            'external_work_j':work,'shell_interface_work_j':shell_work,
            'beam_interface_work_j':beam_work,
            'work_balance_relative':float(abs(work-2*(shell_energy+beam_energy))
                                           /max(abs(work),1)),
            'interface_work_discrepancy_j':shell_work+beam_work,
            'free_equilibrium_relative':float(np.linalg.norm(eq)/
                                              max(np.linalg.norm(load),1)),
            'assembled_weak_gap_max':float(np.max(np.abs(weak_gap))),
            'assembled_weak_gap_units':'m^2 and m*rad for weak rows; m and rad for station rows',
            'normalized_weak_gap_max':float(np.max(np.abs(physical_weak_gap))/weak_gap_scale),
            'fixed_displacement_scale_m':displacement_scale,
            'fixed_length_scale_m':length_scale,
            'sampled_pointwise_gap_lower_bound':
                [float(v) for v in max_gap],
            'sampled_scaled_gap_lower_bound_over_u':float(
                max(max_gap[0],max_gap[1],.46*max_gap[2])/displacement_scale),
            'station_probes':probes,
            'status':'CLASSICAL_FALSIFICATION_NOT_NATIVE_F03_REFERENCE'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology',choices=('Q4','S3-V2D'),required=True)
    parser.add_argument('--n-shell',type=int,required=True)
    parser.add_argument('--n-y',type=int,required=True)
    parser.add_argument('--n-mortar',type=int,required=True)
    parser.add_argument('--subcells',type=int,required=True)
    parser.add_argument('--load',choices=('smooth','sine'),required=True)
    parser.add_argument('--law',choices=('weak-p0','weak-p1','station',
                                         'station-no-root'),required=True)
    args=parser.parse_args()
    if not (1<=args.n_shell<=64 and 2<=args.n_y<=64 and
            2<=args.n_mortar<=64 and 1<=args.subcells<=16 and
            args.n_mortar*args.subcells<=512):
        parser.error('bounded independent pilot inventory required')
    reference.self_check()
    print(json.dumps(solve(args.topology,args.n_shell,args.n_y,args.n_mortar,
                           args.subcells,args.load,args.law),
                     allow_nan=False,sort_keys=True))


if __name__=='__main__':
    main()
