"""Exploratory loaded-interior correction for the classical comparator.

This remains classical plane stress plus a conventional exact-static
Timoshenko beam with ties only at its nodes, not the E4-PL/native B3 or
production mortar operator. Historical v5 source and evidence stay intact.
"""

from __future__ import annotations

import argparse
import json
import numpy as np
from functools import lru_cache
from scipy import sparse
from scipy.sparse.linalg import spsolve

import probe_b3_ge_e4_pl_g0_f03_resolved_continuum as reference


def _load(s: float, kind: str) -> float:
    if kind == 'constant':
        return 1e6
    if kind == 'smooth':
        return 1e6*(1+.25*np.cos(2*np.pi*s))
    if kind == 'sine':
        return 1e6*np.sin(2*np.pi*s)
    raise ValueError('unknown load')


_STATIONS,_WEIGHTS=np.polynomial.legendre.leggauss(24)


def _integral(i: int,n: int,kind: str,length: float,power: int) -> float:
    t=(_STATIONS+1)*length/2
    return float(length/2*np.dot(_WEIGHTS,
        (length-t)**power*_load(i/n+t,kind)))


@lru_cache(maxsize=1024)
def _end_forces(i: int,n: int,kind: str) -> tuple[float,float]:
    h=1/n
    ei=reference.E*reference.INERTIA
    kga=reference.G*reference.SHEAR_AREA
    a=np.array(((h,-h*h/2),(h*h/(2*ei),h/kga-h**3/(6*ei))))
    b=np.array((-_integral(i,n,kind,h,2)/2,
                -_integral(i,n,kind,h,3)/(6*ei)+_integral(i,n,kind,h,1)/kga))
    return tuple(np.linalg.solve(a,b))


def loaded_bubble(s: float, n: int, kind: str) -> np.ndarray:
    """Zero-endpoint particular of EI theta''=-V, V'=-q, v'=theta+V/kGA.

    Loads and constraints act at beam nodes. Thus the exact local response
    to the distributed load has zero nodal pose and is energy-orthogonal to
    the homogeneous exact-static nodal field. The 24-point quadrature is a
    diagnostic approximation to the trigonometric convolution integrals.
    """
    h=1/n
    i=min(int(np.floor(s*n+1e-11)),n-1)
    x=s-i*h
    # theta= M0*x/EI - V0*x^2/(2EI) + I2/(2EI),
    # v= M0*x^2/(2EI) + V0*(x/kGA-x^3/(6EI))
    #    + I3/(6EI) - I1/kGA. Both vanish at the right node.
    ei=reference.E*reference.INERTIA
    kga=reference.G*reference.SHEAR_AREA
    m0,v0=_end_forces(i,n,kind)
    theta=(m0*x-v0*x*x/2+_integral(i,n,kind,x,2)/2)/ei
    v=(m0*x*x/(2*ei)+v0*(x/kga-x**3/(6*ei))
       +_integral(i,n,kind,x,3)/(6*ei)-_integral(i,n,kind,x,1)/kga)
    return np.array((0.,v,theta))


def bubble_energy_work(n: int,kind: str) -> tuple[float,float]:
    work=0.
    strain_energy=0.
    ei=reference.E*reference.INERTIA
    kga=reference.G*reference.SHEAR_AREA
    for i in range(n):
        m0,v0=_end_forces(i,n,kind)
        for xi,w in zip(_STATIONS,_WEIGHTS):
            s=(i+(xi+1)/2)/n
            x=(xi+1)/(2*n)
            work+=w*_load(s,kind)*loaded_bubble(s,n,kind)[1]/(2*n)
            curvature=(m0-v0*x+_integral(i,n,kind,x,1))/ei
            shear=v0-_integral(i,n,kind,x,0)
            strain_energy+=w*(ei*curvature**2+shear**2/kga)/(4*n)
    if not np.isclose(work,2*strain_energy,rtol=5e-10,atol=1e-12):
        raise AssertionError('independent particular strain/load work mismatch')
    return strain_energy,work


def shell_trace(s: float, n: int, n_y: int, topology: str, node_count: int):
    """Same four-sample pose, assembled directly into three sparse rows."""
    entries={}
    for ox,y in reference.OFFSETS:
        ids,weights=reference._host(s+ox,y,n,n_y,topology)
        for node,weight in zip(ids,weights):
            contributions=((0,2*node,weight/4),
                           (1,2*node+1,weight/4),
                           (2,2*node,-y*weight/reference.YAW_DENOMINATOR),
                           (2,2*node+1,ox*weight/reference.YAW_DENOMINATOR))
            for row,col,value in contributions:
                entries[row,col]=entries.get((row,col),0.)+value
    keys=sorted(entries)
    result=sparse.csr_matrix(([entries[k] for k in keys],
                              ([k[0] for k in keys],[k[1] for k in keys])),
                             shape=(3,2*node_count))
    result.eliminate_zeros()
    return result


def self_check():
    reference.self_check()
    for topology in ('Q4','S3-V2D'):
        for n,n_y in ((2,4),(4,8),(8,8)):
            points,_,_=reference.panel(n,n_y,topology)
            for s in (0.,.125,.35,.875,1.):
                actual=shell_trace(s,n,n_y,topology,len(points)).toarray()
                expected=reference.shell_trace(s,n,n_y,topology,len(points))
                if not np.allclose(actual,expected,rtol=0.,atol=2e-15):
                    raise AssertionError('sparse four-sample pose differs')
    for kind in ('constant','smooth','sine'):
        for n in (1,2,8):
            for i in range(n+1):
                if np.linalg.norm(loaded_bubble(i/n,n,kind))>2e-13:
                    raise AssertionError('loaded particular has nonzero nodal pose')
            energy,work=bubble_energy_work(n,kind)
            if energy < 0 or not np.isclose(2*energy,work,rtol=5e-10,atol=1e-12):
                raise AssertionError('loaded particular work identity')
    ei=reference.E*reference.INERTIA
    kga=reference.G*reference.SHEAR_AREA
    for n in (1,2,8):
        h=1/n
        for fraction in (.2,.5,.8):
            x=h*fraction
            actual=loaded_bubble(x,n,'constant')
            expected=np.array((0.,1e6*(x*x*(h-x)**2/(24*ei)
                                      +x*(h-x)/(2*kga)),
                               1e6*x*(h-x)*(h-2*x)/(12*ei)))
            if not np.allclose(actual,expected,rtol=2e-12,atol=2e-16):
                raise AssertionError('constant-load analytic field mismatch')


def solve(topology: str, n_shell: int, n_beam: int, kind: str, n_y: int):
    points,ks,sf=reference.panel(n_shell,n_y,topology)
    kb,bf=reference.beam(n_beam)
    fs=np.zeros(ks.shape[0])
    fb=reference.load_vector(n_beam,kind)
    matrices=sparse.block_diag((ks[sf,:][:,sf],kb[bf,:][:,bf]),format='csr')
    loads=np.r_[fs[sf],fb[bf]]
    cs=[]
    cb=[]
    for i in range(n_beam+1):
        s=i/n_beam
        cs.append(shell_trace(s,n_shell,n_y,topology,len(points)))
        cb.append(sparse.csr_matrix(reference.beam_trace(s,n_beam)))
    c_shell=sparse.vstack(cs,format='csr')
    c_beam=sparse.vstack(cb,format='csr')
    c=sparse.hstack((-c_shell[:,sf],c_beam[:,bf]),format='csr')
    c.eliminate_zeros()
    gram=(c@c.T).toarray()
    row_norm=np.sqrt(np.diag(gram))
    if np.any(row_norm<=0):
        raise ValueError('zero supported constraint row')
    gram /= row_norm[:,None]*row_norm[None,:]
    spectrum=np.linalg.eigvalsh(gram)
    row_gram_ratio=float(max(0.,spectrum[0])/spectrum[-1])
    coordinate_scale=1e-5
    work_scale=10.
    gap_scale=1e-5
    full=sparse.bmat(((matrices*(coordinate_scale**2/work_scale),
                       c.T*(coordinate_scale/gap_scale)),
                      (c*(coordinate_scale/gap_scale),None)),format='csc')
    rhs=np.r_[loads*(coordinate_scale/work_scale),np.zeros(c.shape[0])]
    solution=spsolve(full,rhs)
    if not np.all(np.isfinite(solution)):
        raise AssertionError('singular or nonfinite coupled result')
    u=solution[:len(loads)]*coordinate_scale
    lam=solution[len(loads):]*(work_scale/gap_scale)
    us=np.zeros(ks.shape[0])
    ub=np.zeros(kb.shape[0])
    us[sf],ub[bf]=u[:len(sf)],u[len(sf):]
    eq=matrices@u+c.T@lam-loads
    gap=c@u
    reaction_shell=ks@us-c_shell.T@lam-fs
    reaction_beam=kb@ub+c_beam.T@lam-fb
    shell_interface_work=float(lam@(c_shell@us))
    beam_interface_work=float(-lam@(c_beam@ub))
    shell_fixed=np.setdiff1d(np.arange(ks.shape[0]),sf)
    beam_fixed=np.setdiff1d(np.arange(kb.shape[0]),bf)
    shell_force=np.array([reaction_shell[shell_fixed[axis::2]].sum()
                          for axis in (0,1)])
    beam_force=reaction_beam[:2]
    support_force=shell_force+beam_force
    shell_moment=sum(points[i,0]*reaction_shell[2*i+1]-
                     points[i,1]*reaction_shell[2*i]
                     for i in range(len(points)) if 2*i in shell_fixed)
    support_moment=shell_moment+reaction_beam[2]
    external_moment=sum((i/n_beam)*fb[3*i+1]+fb[3*i+2]
                        for i in range(n_beam+1))
    work=float(loads@u)
    se=float(us@ks@us/2)
    be=float(ub@kb@ub/2)
    bubble_se,bubble_work=bubble_energy_work(n_beam,kind)
    work+=bubble_work
    be+=bubble_se
    probes=[]
    continuous_gap=np.zeros(3)
    breaks=reference.gap_knots(n_shell,n_y,n_beam,topology)
    search_stations=np.unique(np.concatenate((breaks,
        np.concatenate([np.linspace(a,b,17) for a,b in
                        zip(breaks[:-1],breaks[1:])]))))

    def gap_at(s):
        pose=shell_trace(float(s),n_shell,n_y,topology,len(points))@us
        return (reference.beam_trace(float(s),n_beam)@ub+
                loaded_bubble(float(s),n_beam,kind)-pose)
    for s in search_stations:
        continuous_gap=np.maximum(continuous_gap,np.abs(gap_at(s)))
    for s in (0.,.125,.25,.375,.5,.625,.75,.875,1.):
        pose=shell_trace(s,n_shell,n_y,topology,len(points))@us
        beam_pose=reference.beam_trace(s,n_beam)@ub+loaded_bubble(s,n_beam,kind)
        probes.append(dict(s=s,shell=[float(v) for v in pose],
                           beam=[float(v) for v in beam_pose],
                           gap=[float(v) for v in beam_pose-pose]))
    return dict(topology=topology,n_shell=n_shell,n_y=n_y,
                n_beam=n_beam,load=kind,
                model='CLASSICAL_PLANE_STRESS_LOADED_TIMOSHENKO_FINITE_NODE_TIES',
                beam_interior_idealization='HOMOGENEOUS_PLUS_ZERO_ENDPOINT_LOAD_PARTICULAR',
                coordinate_scale=coordinate_scale,gap_scale=gap_scale,
                work_scale_j=work_scale,shell_nodes=len(points),
                beam_nodes=n_beam+1,multiplier_rows=c.shape[0],
                matrix_nnz=full.nnz,
                row_normalized_constraint_gram_eigen_ratio=row_gram_ratio,
                load_y_total=float(fb[1::3].sum()),
                load_moment_z_nm=float(external_moment),
                support_force_n=[float(v) for v in support_force],
                support_moment_z_nm=float(support_moment),
                shell_energy_j=se,beam_energy_j=be,external_work_j=work,
                load_particular_energy_j=bubble_se,
                load_particular_work_j=bubble_work,
                shell_interface_work_j=shell_interface_work,
                beam_interface_work_j=beam_interface_work,
                energy_balance_relative=float(abs(work-2*(se+be))/max(abs(work),1)),
                equilibrium_relative=float(np.linalg.norm(eq)/max(np.linalg.norm(loads),1)),
                constraint_absolute=float(np.max(np.abs(gap))),
                discrete_gap_knots=len(breaks),
                gap_search_stations=len(search_stations),
                sampled_max_gap_lower_bound_components=[float(v) for v in continuous_gap],
                gap_bound_status='SAMPLED_LOWER_BOUND_ONLY_TRIGONOMETRIC_FIELD',
                station_probes=probes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology',choices=('Q4','S3-V2D'),required=True)
    parser.add_argument('--n-shell',type=int,required=True)
    parser.add_argument('--n-y',type=int,required=True)
    parser.add_argument('--n-beam',type=int,required=True)
    parser.add_argument('--load',choices=('smooth','sine'),required=True)
    args=parser.parse_args()
    if not (1 <= args.n_shell <= 128 and 2 <= args.n_y <= 128
            and 1 <= args.n_beam <= 128):
        parser.error('bounded mesh inventory required')
    self_check()
    result=solve(args.topology,args.n_shell,args.n_beam,args.load,args.n_y)
    print(json.dumps(result,allow_nan=False,sort_keys=True))


if __name__=='__main__':
    main()
