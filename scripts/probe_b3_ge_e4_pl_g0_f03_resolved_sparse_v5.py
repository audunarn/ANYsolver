"""Sparse trace assembly for the independent finite-station comparator.

This remains classical plane stress plus a conventional exact-static
Timoshenko beam, not the E4-PL/native B3 or production mortar operator.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

import probe_b3_ge_e4_pl_g0_f03_resolved_continuum as reference


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
    probes=[]
    continuous_gap=np.zeros(3)
    breaks=reference.gap_knots(n_shell,n_y,n_beam,topology)
    search_stations=np.unique(np.concatenate((breaks,
        np.concatenate([np.linspace(a,b,17) for a,b in
                        zip(breaks[:-1],breaks[1:])]))))

    def gap_at(s):
        pose=shell_trace(float(s),n_shell,n_y,topology,len(points))@us
        return reference.beam_trace(float(s),n_beam)@ub-pose

    nodes=np.array((0.,1/3,2/3,1.))
    vandermonde=np.vander(nodes,4,increasing=True)
    extrema_stations=list(breaks)
    interpolation_error=0.
    for a,b in zip(breaks[:-1],breaks[1:]):
        coefficients=np.linalg.solve(vandermonde,np.array(
            [gap_at(a+(b-a)*t) for t in nodes]))
        interpolation_error=max(interpolation_error,float(np.max(np.abs(
            gap_at((a+b)/2)-np.array((1.,.5,.25,.125))@coefficients))))
        for component in range(3):
            polynomial=coefficients[:,component]
            for root in np.roots((3*polynomial[3],
                                  2*polynomial[2],polynomial[1])):
                if abs(root.imag)<1e-10 and 0<root.real<1:
                    extrema_stations.append(float(a+(b-a)*root.real))
    for s in search_stations:
        continuous_gap=np.maximum(continuous_gap,np.abs(gap_at(s)))
    extrema_gap=np.max(np.abs([gap_at(s) for s in extrema_stations]),axis=0)
    for s in (0.,.125,.25,.375,.5,.625,.75,.875,1.):
        pose=shell_trace(s,n_shell,n_y,topology,len(points))@us
        beam_pose=reference.beam_trace(s,n_beam)@ub
        probes.append(dict(s=s,shell=[float(v) for v in pose],
                           beam=[float(v) for v in beam_pose],
                           gap=[float(v) for v in beam_pose-pose]))
    return dict(topology=topology,n_shell=n_shell,n_y=n_y,
                n_beam=n_beam,load=kind,
                model='CLASSICAL_PLANE_STRESS_EXACT_STATIC_TIMOSHENKO_FINITE_COLLOCATION',
                beam_interior_idealization='HOMOGENEOUS_EXACT_STATIC_TEST_FIELD',
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
                shell_interface_work_j=shell_interface_work,
                beam_interface_work_j=beam_interface_work,
                energy_balance_relative=float(abs(work-2*(se+be))/max(abs(work),1)),
                equilibrium_relative=float(np.linalg.norm(eq)/max(np.linalg.norm(loads),1)),
                constraint_absolute=float(np.max(np.abs(gap))),
                discrete_gap_knots=len(breaks),
                gap_search_stations=len(search_stations),
                sampled_max_gap_lower_bound_components=[float(v) for v in continuous_gap],
                polynomial_extrema_station_count=len(extrema_stations),
                polynomial_gap_extrema_estimate_components=[float(v) for v in extrema_gap],
                max_polynomial_fit_midpoint_error=float(interpolation_error),
                station_probes=probes)
