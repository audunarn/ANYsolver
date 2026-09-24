"""Bounded graph-scaled signed native KKT diagnostic; not F03 acceptance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if not os.environ.get('NUMBA_CACHE_DIR'):
    raise RuntimeError('set a dedicated writable NUMBA_CACHE_DIR')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import numpy as np
from scipy import linalg

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import assemble, scales, supported_stiffness
from probe_b3_ge_e4_pl_g0_f03_local_trace_norm_v1 import local_matrices, local_functional
from probe_b3_ge_e4_pl_g0_f03_broken_trace_v1 import graph, trace
from probe_b3_ge_e4_pl_g0_f03_shell_port_lift_v1 import port_coordinates
from probe_b3_ge_e4_pl_g0_f03_signed_norm_v1 import U, L0, W0, couplings


def relative(a, b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b), np.finfo(float).tiny))


def measure(topology, n_beam, n_shell, *, observe_modes=False):
    beam, shell = build(n_beam), make_shell(n_shell, topology)
    n_p = shell.free_count + len(beam.physical)
    spaces = {s.name:s for s in candidate_spaces(beam, shell)}
    overlay = assemble(beam, shell, spaces['p1-beam']).integration_knots
    r, e, midpoint, jumps = local_matrices(beam, shell, overlay)
    if midpoint > 1e-10 or jumps != n_beam-1 or len(e) > 2500:
        raise ValueError('bounded trace/overlay admission failed')
    sq, _ = scales(beam, shell, 3*n_beam)
    eh = e*sq[None, :]/U
    raw_g = eh.T @ (r @ eh)
    graph_skew = relative(raw_g, raw_g.T)
    old_g, _, _ = graph(beam, shell, overlay)
    graph_parity = relative(raw_g, (sq[:, None]*old_g)*sq[None, :]/U**2)
    if max(graph_skew, graph_parity) > 1e-10:
        raise ValueError(f'broken graph skew/parity: {graph_skew}, {graph_parity}')
    g = (raw_g+raw_g.T)/2
    eg, ug = linalg.eigh(g, check_finite=True)
    if eg[-1] <= 0 or eg[0] < -1e-10*eg[-1]:
        raise ValueError('reachable graph not semidefinite')
    keep = eg > 1e-12*eg[-1]
    if not np.any(keep):
        raise ValueError('empty numerical reachable graph')

    q = port_coordinates(beam, shell)
    sh = e @ q / U
    root = trace(beam, shell, 0.)[:2, :] @ q
    root_error = float(np.max(np.abs(root[:, :2]-np.eye(2))))
    root_error = max(root_error, float(np.max(np.abs(root[:, 2:]))))
    if root_error > 1e-12:
        raise ValueError(f'physical root port identity failed: {root_error}')
    sgram = sh.T @ (r @ sh)
    sgram = (sgram+sgram.T)/2
    sgram_eig = linalg.eigvalsh(sgram)
    if sgram_eig[0] <= 1e-12*sgram_eig[-1]:
        raise ValueError('port subspace norm deficient')

    k = supported_stiffness(beam, shell).toarray()
    if len(k) + 3*n_beam > 1200:
        raise ValueError('bounded dense KKT cap exceeded')
    a = (sq[:, None]*k)*sq[None, :]/W0
    a_skew = relative(a, a.T)
    if a_skew > 1e-10:
        raise ValueError(f'native signed stiffness nonsymmetric: {a_skew}')
    app, apr, arp, arr = (a[:n_p, :n_p], a[:n_p, n_p:],
                          a[n_p:, :n_p], a[n_p:, n_p:])
    er, ur = linalg.eigh(arr, check_finite=True)
    if np.min(np.abs(er)) <= 1e-12*np.max(np.abs(er)):
        raise ValueError('native retained block lacks verified invertibility')
    rp = linalg.solve(arr, arp, assume_a='sym')
    ke = app - apr @ rp
    ep = linalg.eigvalsh(ke, check_finite=True)
    if ep[0] <= 1e-12*ep[-1]:
        raise ValueError('physical Schur block not verified SPD')
    absolute_arr = (ur*np.abs(er)[None, :]) @ ur.T
    transform = np.eye(len(k))
    transform[n_p:, :n_p] = rp
    h0 = transform.T @ linalg.block_diag(ke, absolute_arr) @ transform
    h = h0 + g  # Fixed coefficient one in the frozen work/trace scales.
    h = (h+h.T)/2
    ehh, uhh = linalg.eigh(h, check_finite=True)
    if ehh[0] <= 1e-12*ehh[-1]:
        raise ValueError('graph-augmented primal norm not verified SPD')
    ih = uhh/np.sqrt(ehh)[None, :]
    ah = ih.T @ a @ ih
    ah_norm = float(linalg.svdvals(ah)[0])
    if ah_norm > 1+1e-8:
        raise ValueError(f'signed operator exceeds registered graph norm bound: {ah_norm}')

    out = {'kind':'native', 'topology':topology, 'n_beam':n_beam, 'n_shell':n_shell,
           'primal_count':len(k), 'retained_count':len(arr),
           'overlay_intervals':len(overlay)-1, 'trace_rows':len(e),
           'graph_nnz':r.nnz, 'graph_rank':int(np.count_nonzero(keep)),
           'graph_skew':graph_skew, 'independent_graph_parity':graph_parity,
           'graph_min_eigen':float(eg[0]), 'graph_max_eigen':float(eg[-1]),
           'native_negative_modes':int(np.count_nonzero(er < 0)),
           'native_min_abs_eigen':float(np.min(np.abs(er))),
           'ke_min_eigen':float(ep[0]), 'h_min_eigen':float(ehh[0]),
           'signed_operator_skew':a_skew, 'signed_operator_norm':ah_norm,
           'root_port_error':root_error, 'spaces':{},
           'status':'EXPLORATORY_GRAPH_SIGNED_KKT_NOT_F03_ACCEPTANCE'}
    for name, (c, _) in couplings(beam, shell).items():
        f = local_functional(beam, overlay, name)
        if relative(f @ e * sq[None, :], c * sq[None, :]) > 1e-10:
            raise ValueError(f'{name} native/trace moment mismatch')
        fh = f/L0
        ch = fh @ eh
        fs = fh @ sh
        raw_n = fs @ linalg.solve(sgram, fs.T, assume_a='pos')
        n_skew = relative(raw_n, raw_n.T)
        if n_skew > 1e-10:
            raise ValueError(f'{name} port dual nonsymmetric: {n_skew}')
        n = (raw_n+raw_n.T)/2
        en, un = linalg.eigh(n, check_finite=True)
        if en[0] <= 1e-12*en[-1]:
            raise ValueError(f'{name} port dual norm not verified SPD')
        ins = un/np.sqrt(en)[None, :]
        cutoff_results = {}
        first_b = None
        for cutoff in (1e-12, 1e-10, 1e-8):
            positive = eg > cutoff*eg[-1]
            lifted = (ch @ ug[:, positive])/np.sqrt(eg[positive])[None, :]
            b = lifted @ lifted.T
            discarded = float(np.linalg.norm(ch @ ug[:, ~positive])/
                              max(np.linalg.norm(ch), np.finfo(float).tiny))
            if discarded > 1e-8:
                raise ValueError(f'{name} cutoff {cutoff} discarded constraint action: {discarded}')
            dual_ratio = linalg.eigvalsh(b, n, check_finite=True)
            if dual_ratio[0] < 1-1e-8:
                raise ValueError(f'{name} cutoff {cutoff} port/reachable ordering failed')
            if first_b is None:
                first_b = b
            cutoff_parity = relative(b, first_b)
            if cutoff_parity > 1e-8:
                raise ValueError(f'{name} graph cutoff sensitivity: {cutoff_parity}')
            cutoff_results[str(cutoff)] = {
                'rank':int(np.count_nonzero(positive)),
                'discarded_constraint_action':discarded,
                'dual_min_reachable_over_port':float(dual_ratio[0]),
                'dual_max_reachable_over_port':float(dual_ratio[-1]),
                'dual_parity_to_1e_12':cutoff_parity,
            }

        cb = c*sq[None, :]/(U*L0)
        if relative(cb, ch) > 1e-10:
            raise ValueError(f'{name} scaled constraint/trace parity failed')
        bh = ins.T @ cb @ ih
        beta = float(linalg.svdvals(bh)[-1])
        cp, cr = cb[:, :n_p], cb[:, n_p:]
        cl = cp - cr @ rp
        sc = cl @ linalg.solve(ke, cl.T, assume_a='pos') + cr @ linalg.solve(arr, cr.T, assume_a='sym')
        sf = cb @ linalg.solve(a, cb.T, assume_a='sym')
        schur_parity = relative(sc, sf)
        if schur_parity > 1e-8:
            raise ValueError(f'{name} signed full/condensed Schur mismatch: {schur_parity}')
        sn = ins.T @ sc @ ins
        schur_skew = relative(sn, sn.T)
        if schur_skew > 1e-9:
            raise ValueError(f'{name} signed Schur nonsymmetric: {schur_skew}')
        sn = (sn+sn.T)/2
        es = linalg.eigvalsh(sn, check_finite=True)
        block = np.block([[ah, bh.T], [bh, np.zeros((len(c),len(c)))]])
        block_skew = relative(block, block.T)
        if block_skew > 1e-9:
            raise ValueError(f'{name} signed KKT nonsymmetric: {block_skew}')
        kb = linalg.svdvals(block)
        if observe_modes:
            eb, ub = linalg.eigh(block, check_finite=True)
        else:
            eb = linalg.eigvalsh(block, check_finite=True)
        eig_zero = 1e-10*float(np.max(np.abs(eb)))
        schur_zero = 1e-10*float(np.max(np.abs(es)))
        rhs = np.sin(np.arange(len(block), dtype=float)+1.)
        solved = linalg.solve(block, rhs, assume_a='sym')
        equation_residual = relative(block @ solved, rhs)
        if equation_residual > 1e-8:
            raise ValueError(f'{name} normalized KKT equation residual: {equation_residual}')
        out['spaces'][name] = {
            'rows':len(c), 'constraint_parity':relative(cb, ch),
            'port_dual_skew':n_skew, 'graph_cutoffs':cutoff_results,
            'positive_constraint_beta':beta,
            'positive_constraint_ceiling':float(linalg.svdvals(bh)[0]),
            'signed_schur_min_abs_eigen':float(np.min(np.abs(es))),
            'signed_schur_min_eigen':float(es[0]),
            'signed_schur_max_eigen':float(es[-1]),
            'signed_schur_negative_modes':int(np.count_nonzero(es < -schur_zero)),
            'signed_schur_near_zero_modes':int(np.count_nonzero(np.abs(es) <= schur_zero)),
            'signed_schur_skew':schur_skew,
            'signed_schur_parity':schur_parity,
            'signed_kkt_min_singular':float(kb[-1]),
            'signed_kkt_max_singular':float(kb[0]),
            'signed_kkt_min_eigen':float(eb[0]),
            'signed_kkt_max_eigen':float(eb[-1]),
            'signed_kkt_negative_modes':int(np.count_nonzero(eb < -eig_zero)),
            'signed_kkt_near_zero_modes':int(np.count_nonzero(np.abs(eb) <= eig_zero)),
            'signed_kkt_skew':block_skew,
            'signed_kkt_equation_residual':equation_residual,
        }
        if observe_modes:
            indices = np.argsort(np.abs(eb))[:min(6,len(eb))]
            nearest = int(indices[0])
            mode = ub[:,nearest]
            eigen_residual = float(np.linalg.norm(
                block @ mode - eb[nearest]*mode))
            if (eigen_residual > 1e-9 or
                    abs(abs(eb[nearest])-kb[-1]) > 1e-8*max(kb[-1],1e-15)):
                raise ValueError('signed KKT mode/equation mismatch')
            primal = mode[:len(k)]
            dual = mode[len(k):]
            raw_dual = ins @ dual
            raw_primal = ih @ primal
            factored_primal = transform @ raw_primal
            physical_part = float(factored_primal[:n_p] @ ke @
                                  factored_primal[:n_p])
            retained_absolute_part = float(factored_primal[n_p:] @
                                           absolute_arr @ factored_primal[n_p:])
            retained_signed_part = float(factored_primal[n_p:] @ arr @
                                         factored_primal[n_p:])
            h0_part = float(raw_primal @ h0 @ raw_primal)
            graph_part = float(raw_primal @ g @ raw_primal)
            if (abs(h0_part+graph_part-primal@primal) > 1e-8 or
                    abs(physical_part+retained_absolute_part-h0_part) > 1e-8 or
                    abs(physical_part+retained_signed_part-
                        primal@ah@primal) > 1e-8):
                raise ValueError('signed KKT mode primal-norm decomposition failed')
            nearby_dual = ins @ ub[len(k):,indices]
            channel_subspace_power = np.array([
                np.linalg.norm(nearby_dual[channel*n_beam:
                                           (channel+1)*n_beam])**2
                for channel in range(3)])
            channel_subspace_power /= max(float(np.sum(channel_subspace_power)),
                                          np.finfo(float).tiny)
            largest = max(float(np.max(np.abs(raw_dual))),
                          np.finfo(float).tiny)
            channel_profiles = []
            for channel in range(3):
                coefficients = raw_dual[channel*n_beam:(channel+1)*n_beam]
                normalized = coefficients/largest
                significant = normalized[np.abs(normalized)>1e-8]
                channel_profiles.append({
                    'normalized_coefficients':normalized.tolist(),
                    'normalized_l2':float(np.linalg.norm(normalized)),
                    'sign_changes':int(np.count_nonzero(
                        significant[1:]*significant[:-1]<0)),
                })
            out['spaces'][name]['lowest_mode_observation'] = {
                'signed_eigenvalue':float(eb[nearest]),
                'smallest_absolute_eigenvalues':
                    np.abs(eb[indices]).tolist(),
                'signed_nearby_eigenvalues':eb[indices].tolist(),
                'eigen_equation_residual':eigen_residual,
                'primal_h_coordinate_share':float(primal@primal),
                'multiplier_n_coordinate_share':float(dual@dual),
                'primal_h0_contribution':h0_part,
                'primal_trace_graph_contribution':graph_part,
                'physical_schur_positive_contribution':physical_part,
                'retained_absolute_contribution':retained_absolute_part,
                'retained_signed_contribution':retained_signed_part,
                'signed_primal_operator_rayleigh':float(primal@ah@primal),
                'normalized_constraint_action_l2':float(np.linalg.norm(bh@primal)),
                'six_mode_raw_multiplier_channel_power_shares_x_y_yaw':
                    channel_subspace_power.tolist(),
                'work_scaled_primal_coordinate_l2':{
                    'shell':float(np.linalg.norm(
                        raw_primal[:shell.free_count])),
                    'beam_physical':float(np.linalg.norm(
                        raw_primal[shell.free_count:n_p])),
                    'beam_retained':float(np.linalg.norm(raw_primal[n_p:])),
                },
                'raw_multiplier_row_profiles_x_y_yaw':channel_profiles,
                'interpretation_limit':
                    'single eigenvector is unstable if nearby modes cluster; '
                    'raw coefficient magnitudes are not physical channel norms',
            }
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology', choices=('Q4','S3-V2D'), required=True)
    parser.add_argument('--n-beam', type=int, required=True)
    parser.add_argument('--n-shell', type=int, required=True)
    parser.add_argument('--observe-modes', action='store_true')
    args = parser.parse_args()
    if (args.n_beam,args.n_shell) not in ((4,4),(8,8),(16,16),(8,1),(8,64)):
        parser.error('unregistered native mesh')
    print(json.dumps(measure(args.topology,args.n_beam,args.n_shell,
                             observe_modes=args.observe_modes),
                     sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
