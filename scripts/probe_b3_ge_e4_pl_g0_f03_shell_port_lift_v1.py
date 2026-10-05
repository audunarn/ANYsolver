"""Bounded supported-shell-port trace lift; exploratory F03 mechanics only."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if not os.environ.get('NUMBA_CACHE_DIR'):
    raise RuntimeError('set a writable NUMBA_CACHE_DIR before source import')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import numpy as np
from scipy import linalg

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import assemble, scales
from probe_b3_ge_e4_pl_g0_f03_local_trace_norm_v1 import local_matrices, local_functional
from probe_b3_ge_e4_pl_g0_f03_broken_trace_v1 import graph, trace
from probe_b3_ge_e4_pl_g0_f03_signed_norm_v1 import L0, U, couplings


def port_coordinates(beam, shell):
    """Physical supported nodal fields, free beam positions, retained yaw."""
    n = shell.free_count + len(beam.physical) + len(beam.internal)
    q = np.zeros((n, 3 * beam.n_half_cells + 2))
    nx = 2 * shell.n_s
    x = -.5 + np.arange(nx + 1) / shell.n_s
    p = 2 * (1 - np.abs(x - .5))
    if abs(p[0]) > 1e-14 or abs(p[-1]) > 1e-14:
        raise ValueError('shell port moves supported end edge')
    full = np.zeros((shell.dof_count, 2))
    for row in range(3):
        for i in range(nx + 1):
            for axis in (0, 1):
                full[2 * (row * (nx + 1) + i) + axis, axis] = -p[i]
    if np.max(np.abs(full[np.setdiff1d(np.arange(shell.dof_count), shell.free)])) > 1e-14:
        raise ValueError('shell port violates fixed outer edges')
    q[:shell.free_count, :2] = full[shell.free]
    nbeam = beam.n_half_cells
    for node in range(1, nbeam + 1):
        for axis in (0, 1):
            match = np.flatnonzero(beam.physical == 6 * node + axis)
            if len(match) != 1:
                raise ValueError('missing free native nodal translation')
            q[shell.free_count + match[0], 2 + axis * nbeam + node - 1] = 1
    for cell in range(nbeam):
        yaw = beam.planar_trace_jacobian((cell + .5) / nbeam)[2]
        match = np.flatnonzero(np.abs(yaw) > 1e-14)
        if len(match) != 1 or abs(yaw[match[0]] - 1) > 1e-14:
            raise ValueError('native retained cell yaw is not a single coordinate')
        native = np.flatnonzero(beam.internal == match[0])
        if len(native) != 1:
            raise ValueError('native yaw does not belong to retained state')
        q[shell.free_count + len(beam.physical) + native[0], 2 + 2*nbeam + cell] = 1
    return q


def dual(c, eig, vec, threshold):
    keep = eig > threshold * eig[-1]
    lifted = (c @ vec[:, keep]) / np.sqrt(eig[keep])[None, :]
    return lifted @ lifted.T, keep


def relative(a, b):
    return float(np.linalg.norm(a-b) / max(np.linalg.norm(b), np.finfo(float).tiny))


def measure(topology, n_beam, n_shell):
    beam, shell = build(n_beam), make_shell(n_shell, topology)
    spaces = {s.name: s for s in candidate_spaces(beam, shell)}
    overlay = assemble(beam, shell, spaces['p1-beam']).integration_knots
    r, e, midpoint, jumps = local_matrices(beam, shell, overlay)
    if midpoint > 1e-10 or jumps != n_beam - 1 or len(e) > 2500:
        raise ValueError('bounded overlay/trace admission failed')
    sq, _ = scales(beam, shell, 3*n_beam)
    eh = e * sq[None, :] / U
    g = eh.T @ (r @ eh)
    old, _, _ = graph(beam, shell, overlay)
    oldh = (old * sq[:, None]) * sq[None, :] / (U*U)
    graph_parity = relative(g, oldh)
    if graph_parity > 1e-10:
        raise ValueError(f'local graph pullback mismatch: {graph_parity}')
    eig, vec = linalg.eigh(g)
    if eig[-1] <= 0 or eig[0] < -1e-10 * eig[-1]:
        raise ValueError('reachable graph is not semidefinite')
    q = port_coordinates(beam, shell)
    sh = e @ q / U
    root = trace(beam, shell, 0.)[:2, :] @ q
    root_error = float(np.max(np.abs(root[:, :2] - np.eye(2))))
    root_error = max(root_error, float(np.max(np.abs(root[:, 2:]))))
    if root_error > 1e-12:
        raise ValueError(f'supported shell ports do not span root translation: {root_error}')
    sgram = sh.T @ (r @ sh)
    sgram_eig = linalg.eigvalsh(sgram)
    if sgram_eig[0] <= 1e-12*sgram_eig[-1]:
        raise ValueError('shell-port/native moment lift is rank deficient')
    base = {'topology': topology, 'n_beam': n_beam, 'n_shell': n_shell,
            'overlay_intervals': len(overlay)-1, 'trace_dofs': len(e),
            'riesz_nnz': r.nnz, 'root_port_error': root_error,
            'graph_pullback_parity': graph_parity, 'native_yaw_jumps': jumps,
            'port_norm_squared': [float(sh[:,i] @ (r @ sh[:,i])) for i in (0,1)],
            'spaces': {}, 'status': 'EXPLORATORY_SHELL_PORT_LIFT_NOT_F03_ACCEPTANCE'}
    # A beam-rooted interpolation of a nonzero shell root port must ramp.
    nodal = [float(trace(beam, shell, node/n_beam)[0] @ q[:, 0])
             for node in range(1, n_beam+1)]
    ramp = sh[:, 2:2+n_beam] @ np.asarray(nodal)
    base['beam_only_root_ramp_over_port_energy'] = float(
        (ramp @ (r @ ramp)) / (sh[:,0] @ (r @ sh[:,0])))
    old_c = couplings(beam, shell)
    for name, (c, _) in old_c.items():
        f = local_functional(beam, overlay, name)
        c_parity = relative(f @ e * sq[None, :], c * sq[None, :])
        if c_parity > 1e-10:
            raise ValueError(f'{name} row functional differs from native C')
        fh = f / L0
        ch = fh @ eh
        d = np.vstack((fh @ sh, sh[:2, :]))
        target = np.vstack((ch, eh[:2, :]))
        if d.shape != (3*n_beam+2, 3*n_beam+2):
            raise ValueError('wrong port/moment square system')
        deig = linalg.svdvals(d)
        if deig[-1] <= 1e-12 * deig[0]:
            raise ValueError(f'{name} shell port/moment system deficient')
        coefficients = linalg.solve(d, target)
        lh = sh @ coefficients
        moment_parity = relative(fh @ lh, ch)
        root_parity = relative(lh[:2], eh[:2])
        idempotence = relative(lh @ (q / sq[:,None]), sh)
        if max(moment_parity,root_parity,idempotence) > 1e-9:
            raise ValueError(f'{name} port lift fails moments, root or idempotence')
        b0 = (fh @ sh) @ linalg.solve(sgram, (fh @ sh).T, assume_a='pos')
        b0 = (b0 + b0.T)/2
        b0eig = linalg.eigvalsh(b0)
        if b0eig[0] <= 1e-12*b0eig[-1]:
            raise ValueError(f'{name} projected dual deficient')
        results = {}
        for cutoff in (1e-12, 1e-10, 1e-8):
            b, keep = dual(ch, eig, vec, cutoff)
            be = linalg.eigvalsh(b)
            if be[0] <= 1e-12*be[-1]:
                raise ValueError(f'{name} reachable dual deficient')
            difference = linalg.eigvalsh(b-b0)
            if difference[0] < -1e-8*max(be[-1],b0eig[-1]):
                raise ValueError(f'{name} subspace dual ordering failed')
            eig_ratio = linalg.eigh(b,b0,eigvals_only=True)
            lifted = lh @ vec[:,keep] / np.sqrt(eig[keep])[None,:]
            amplification = linalg.eigvalsh(lifted.T @ (r @ lifted))[-1]
            dropped_action = float(np.linalg.norm(lh @ vec[:,~keep]) /
                                   max(np.linalg.norm(lh),np.finfo(float).tiny))
            if cutoff == 1e-12 and dropped_action > 1e-8:
                raise ValueError(f'{name} lift acts on numerical nullspace')
            results[str(cutoff)] = {'image_rank': int(np.count_nonzero(keep)),
                                    'dropped_subspace_action': dropped_action,
                                    'dual_ordering_min_eigen': float(difference[0]),
                                    'max_reachable_over_port_dual': float(eig_ratio[-1]),
                                    'max_lift_energy_amplification': float(amplification)}
        base['spaces'][name] = {'constraint_parity': c_parity,
                                'moment_parity': moment_parity,
                                'root_parity': root_parity,
                                'idempotence_error': idempotence,
                                'port_moment_singular_ratio': float(deig[-1]/deig[0]),
                                'cutoffs': results}
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology', choices=('Q4','S3-V2D'), required=True)
    parser.add_argument('--n-beam', type=int, required=True)
    parser.add_argument('--n-shell', type=int, required=True)
    args = parser.parse_args()
    if (args.n_beam,args.n_shell) not in ((4,4),(8,8),(16,16),(8,1),(8,64)):
        parser.error('registered bounded mesh only')
    print(json.dumps(measure(args.topology,args.n_beam,args.n_shell),
                     allow_nan=False, sort_keys=True))


if __name__ == '__main__':
    main()
