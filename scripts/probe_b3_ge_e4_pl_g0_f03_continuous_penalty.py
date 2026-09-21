"""Independent continuous-trace penalty comparator; never a production tie.

This diagnostic integrates the classical membrane/conventional beam trace
misfit over the complete material line, splitting at every host and beam
breakpoint. It cannot qualify the exact multiplier law required by F03.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from probe_b3_ge_e4_pl_g0_f03_resolved_continuum import (
    beam, beam_trace, gap_knots, load_vector, panel, self_check, shell_trace,
)


POSE_LENGTH = np.sqrt(.2**2+.23**2)


def _quadrature(n_shell, n_y, n_beam, topology, shell_nodes, shell_free, beam_free,
                penalty_translation, order=4):
    """Sparse integrated C.T H C and trace table for independent recovery."""
    scales = np.array((penalty_translation, penalty_translation,
                       penalty_translation*POSE_LENGTH**2))
    knots = gap_knots(n_shell, n_y, n_beam, topology)
    stations, weights = np.polynomial.legendre.leggauss(order)
    n = len(shell_free)+len(beam_free)
    rows, cols, values, trace = [], [], [], []
    for left, right in zip(knots[:-1], knots[1:]):
        for xi, weight in zip(stations, weights):
            s = (left+right)/2 + (right-left)*xi/2
            ds = (right-left)*weight/2
            cs = shell_trace(s, n_shell, n_y, topology, shell_nodes)
            cb = beam_trace(s, n_beam)
            local_shell = np.flatnonzero(np.any(np.abs(cs[:, shell_free])>1e-14,axis=0))
            local_beam = np.flatnonzero(np.any(np.abs(cb[:, beam_free])>1e-14,axis=0))
            shell_columns = shell_free[local_shell]
            beam_columns = beam_free[local_beam]
            cs_local = cs[:, shell_columns].copy()
            cb_local = cb[:, beam_columns].copy()
            # The supported stiffness uses only free columns, but physical
            # reactions require the fixed trace columns as well.
            full_shell = np.flatnonzero(np.any(np.abs(cs)>1e-14,axis=0))
            full_beam = np.flatnonzero(np.any(np.abs(cb)>1e-14,axis=0))
            active = np.r_[local_shell, len(shell_free)+local_beam]
            local = np.column_stack((-cs_local, cb_local))
            block = ds*local.T@(scales[:, None]*local)
            for i, global_i in enumerate(active):
                for j, global_j in enumerate(active):
                    rows.append(global_i)
                    cols.append(global_j)
                    values.append(block[i, j])
            trace.append((s, ds, full_shell, cs[:,full_shell].copy(),
                          full_beam, cb[:,full_beam].copy()))
    stiffness = sparse.coo_matrix((values, (rows, cols)), shape=(n, n)).tocsr()
    stiffness.eliminate_zeros()
    return stiffness, trace, knots, scales


def self_check_penalty():
    """Independent 4/5-point parity and penalty-energy derivative."""
    self_check()
    for topology in ('Q4', 'S3-V2D'):
        points, _, sf = panel(2, 4, topology)
        _, bf = beam(4)
        k4, trace, knots, scales = _quadrature(
            2, 4, 4, topology, len(points), sf, bf, 1e11)
        k5, _, _, _ = _quadrature(
            2, 4, 4, topology, len(points), sf, bf, 1e11, order=5)
        if sparse.linalg.norm(k4-k5)/sparse.linalg.norm(k5) > 2e-13:
            raise AssertionError('segmented four-point penalty quadrature')
        rng = np.random.default_rng(114)
        u = rng.normal(size=k4.shape[0])*1e-5
        d = rng.normal(size=k4.shape[0])*1e-5
        explicit = 0.
        us = np.zeros(2*len(points))
        ub = np.zeros(3*5)
        us[sf], ub[bf] = u[:len(sf)], u[len(sf):]
        for _, ds, si, cs, bi, cb in trace:
            c = cb@ub[bi]-cs@us[si]
            explicit += ds*.5*float(c@(scales*c))
        matrix_energy = .5*float(u@k4@u)
        if not np.isclose(explicit, matrix_energy, rtol=1e-12):
            raise AssertionError('integrated penalty energy != sparse operator')
        step = 1e-4
        e_plus = .5*float((u+step*d)@k4@(u+step*d))
        e_minus = .5*float((u-step*d)@k4@(u-step*d))
        if not np.isclose((e_plus-e_minus)/(2*step), float(d@k4@u), rtol=1e-9):
            raise AssertionError('penalty directional derivative')
        response = solve(topology, 2, 4, 4, 'smooth', 1e12)
        if (max(abs(response['support_force_n'][0]),
                abs(response['support_force_n'][1]+1e6),
                abs(response['support_moment_balance_nm'])) > 1e-6):
            raise AssertionError('fixed-column interface reaction recovery')


def solve(topology, n_shell, n_y, n_beam, load, penalty_translation):
    if (topology not in ('Q4','S3-V2D') or load not in ('smooth','sine') or
        not 1 <= n_shell <= 64 or not 2 <= n_y <= 64 or
        not 2 <= n_beam <= 64 or not np.isfinite(penalty_translation) or
        penalty_translation <= 0):
        raise ValueError('bounded physical mesh and positive finite penalty required')
    points, ks, sf = panel(n_shell, n_y, topology)
    kb, bf = beam(n_beam)
    fb = load_vector(n_beam, load)
    base = sparse.block_diag((ks[sf, :][:, sf], kb[bf, :][:, bf]), format='csr')
    force = np.r_[np.zeros(len(sf)), fb[bf]]
    kp, quadrature, knots, scales = _quadrature(
        n_shell, n_y, n_beam, topology, len(points), sf, bf, penalty_translation)
    total = base+kp
    coordinate_scale, work_scale = 1e-5, 10.
    u = coordinate_scale*spsolve(total.tocsc()*(coordinate_scale**2/work_scale),
                                force*(coordinate_scale/work_scale))
    if not np.isfinite(u).all():
        raise AssertionError('nonfinite penalty comparator solution')
    us = np.zeros(ks.shape[0])
    ub = np.zeros(kb.shape[0])
    us[sf], ub[bf] = u[:len(sf)], u[len(sf):]
    shell_traction = np.zeros_like(us)
    beam_traction = np.zeros_like(ub)
    penalty_energy, shell_work, beam_work = 0., 0., 0.
    for _, ds, si, cs, bi, cb in quadrature:
        shell_pose = cs@us[si]
        beam_pose = cb@ub[bi]
        gap = beam_pose-shell_pose
        dual = ds*scales*gap
        shell_traction[si] += cs.T@dual
        beam_traction[bi] -= cb.T@dual
        penalty_energy += .5*float(dual@gap)
        shell_work += float(dual@shell_pose)
        beam_work -= float(dual@beam_pose)
    reaction_shell = ks@us-shell_traction
    reaction_beam = kb@ub-beam_traction-fb
    nx = 2*n_shell
    fixed_shell = np.array([2*(j*(nx+1)+i)+axis
                            for j in range(n_y+1) for i in (0,nx)
                            for axis in (0,1)])
    support_force = np.array((reaction_shell[fixed_shell[0::2]].sum()+reaction_beam[0],
                              reaction_shell[fixed_shell[1::2]].sum()+reaction_beam[1]))
    support_moment = (sum(points[i,0]*reaction_shell[2*i+1]
                          -points[i,1]*reaction_shell[2*i]
                          for i in range(len(points)) if 2*i in fixed_shell)
                      +reaction_beam[2])
    external_moment = sum((i/n_beam)*fb[3*i+1]+fb[3*i+2]
                          for i in range(n_beam+1))
    shell_energy = float(us@ks@us/2)
    beam_energy = float(ub@kb@ub/2)
    work = float(fb@ub)
    extrema = np.zeros(3)
    for a,b in zip(knots[:-1],knots[1:]):
        for s in np.linspace(a,b,17):
            gap = beam_trace(s,n_beam)@ub - shell_trace(s,n_shell,n_y,topology,len(points))@us
            extrema=np.maximum(extrema,np.abs(gap))
    return dict(topology=topology, n_shell=n_shell, n_y=n_y, n_beam=n_beam,
                load=load, penalty_translation_n_per_m2=penalty_translation,
                penalty_rotation_n=penalty_translation*POSE_LENGTH**2,
                characteristic_pose_length_m=POSE_LENGTH,
                shell_energy_j=shell_energy, beam_energy_j=beam_energy,
                penalty_energy_j=penalty_energy, external_work_j=work,
                energy_balance_relative=float(abs(work-2*(shell_energy+beam_energy+penalty_energy))
                                              /max(abs(work),1)),
                shell_interface_work_j=shell_work, beam_interface_work_j=beam_work,
                interface_work_plus_twice_penalty_j=float(shell_work+beam_work+2*penalty_energy),
                free_equilibrium_relative=float(np.linalg.norm(total@u-force)/max(np.linalg.norm(force),1)),
                support_force_n=[float(x) for x in support_force],
                support_moment_balance_nm=float(support_moment+external_moment),
                tip_pose=[float(x) for x in ub[-3:]],
                sampled_max_gap_lower_bound_components=[float(x) for x in extrema],
                quadrature_points=len(quadrature), trace_knots=len(knots),
                penalty_matrix_nnz=kp.nnz, matrix_nnz=total.nnz)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology', choices=('Q4','S3-V2D'), required=True)
    parser.add_argument('--n-shell', type=int, required=True)
    parser.add_argument('--n-y', type=int, required=True)
    parser.add_argument('--n-beam', type=int, required=True)
    parser.add_argument('--load', choices=('smooth','sine'), required=True)
    parser.add_argument('--penalty-translation', type=float, required=True)
    args=parser.parse_args()
    self_check_penalty()
    print(json.dumps(solve(args.topology,args.n_shell,args.n_y,args.n_beam,
                           args.load,args.penalty_translation),sort_keys=True,allow_nan=False))


if __name__=='__main__':
    main()
