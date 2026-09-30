"""Independent positive reference-dual error brackets; no native spectra.

Modal shell boundary-line oracle and equilibrated continuous beam flux.
Bounded reference basis matrices are verification quantities, not mechanical
assembly/inverses. The native cell partition remains fixed during enrichment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info

from scripts.b3_e4_bl5_modal_reference_dev import p0_shell_bracket
from scripts.b3_e4_bl5_riesz_controls_dev import beam_norm, skew


class AuxiliaryInverseAccuracyError(ArithmeticError):
    """Only the declared auxiliary inverse residual budget was unresolved."""

    def __init__(self, history):
        self.history = history
        super().__init__(f'auxiliary inverse action failed: {history}')


def compensated_residual(h, z, b):
    """Accurately evaluate B-HZ on the SAME binary64 sparse entries.

    Each rounded product plus its FMA error is summed with fsum. This avoids
    cancellation in fine H1 grids; it neither rescales nor changes the norm.
    Private development fallback requires the recorded Python3.14 runtime.
    """
    if not hasattr(math, 'fma'):
        raise ArithmeticError('compensated reference residual requires math.fma')
    csr = h.tocsr()
    result = np.empty_like(b)
    for row in range(csr.shape[0]):
        indices = csr.indices[csr.indptr[row]:csr.indptr[row+1]]
        data = csr.data[csr.indptr[row]:csr.indptr[row+1]]
        for column in range(b.shape[1]):
            terms = [float(b[row, column])]
            for index, value in zip(indices, data):
                x, y = float(value), float(z[index, column])
                product = x*y
                terms.extend((-product, -math.fma(x, y, -product)))
            result[row, column] = math.fsum(terms)
    return result


def beam_bracket(force, moments, *, length, ell, arm, width, subdivisions):
    """All-column variational lower bound and equilibrated residual majorant."""
    force = np.asarray(force, dtype=float); moments = np.asarray(moments, dtype=float)
    if force.ndim != 3 or force.shape[1] != 3 or moments.shape != force.shape:
        raise ValueError('cell forces and INTEGRATED cell moments, three spatial components required')
    cells, _, columns = force.shape
    knots, h, active, _ = beam_norm(length, ell, cells, subdivisions, arm, width)
    dx = length/(cells*subdivisions)
    u_action = np.zeros((len(knots), 3, columns))
    for e in range(len(knots)-1):
        f = force[e//subdivisions]
        u_action[e:e+2] += dx*f/2
    full_action = np.concatenate((u_action.reshape(-1, columns), moments.reshape(-1, columns)))
    b = full_action[active]
    factor = splu(h)
    z = factor.solve(b)
    residual = np.linalg.norm(h@z-b, axis=0)/np.maximum(np.linalg.norm(b, axis=0), 1e-30)
    residual_history = [dict(evaluation='sparse_matmul', iteration=0,
                             max_relative_residual=float(np.max(residual)))]
    evaluation = 'sparse_matmul'
    if np.max(residual) > 1e-10:
        for iteration in range(4):
            correction_rhs = compensated_residual(h, z, b)
            residual = np.linalg.norm(correction_rhs, axis=0)/np.maximum(np.linalg.norm(b, axis=0), 1e-30)
            residual_history.append(dict(evaluation='fma_fsum', iteration=iteration,
                max_relative_residual=float(np.max(residual)),
                sparse_matmul_relative_residual=float(np.max(
                    np.linalg.norm(h@z-b, axis=0)/np.maximum(np.linalg.norm(b, axis=0), 1e-30)))))
            evaluation = 'fma_fsum'
            if np.max(residual) <= 1e-10:
                break
            if iteration < 3:
                z += factor.solve(correction_rhs)
    if np.max(residual) > 1e-10:
        raise AuxiliaryInverseAccuracyError(residual_history)
    if evaluation == 'fma_fsum':
        # Same variational functional: HZ=B-R. Preserve the recovered residual
        # precision in both its quadratic term and the local moment majorant.
        lower = b.T@z+z.T@correction_rhs
        final_residual = correction_rhs
    else:
        lower = b.T@z+z.T@b-z.T@(h@z)
        final_residual = b-h@z
    u = np.zeros((len(knots), 3, columns)); u[1:] = z[:3*(len(knots)-1)].reshape(-1, 3, columns)
    theta = z[3*(len(knots)-1):].reshape(cells, 3, columns)
    a = skew(arm)
    flux = np.zeros((3, columns))  # actual natural boundary sigma(L)=0
    error = np.zeros((columns, columns))
    roots, weights = np.polynomial.legendre.leggauss(3)
    for e in reversed(range(len(knots)-1)):
        j = e//subdivisions
        r0 = (u[e]-a@theta[j])/length-force[j]
        r1 = (u[e+1]-u[e])/(length*dx)
        left_flux = flux-dx*r0-dx**2*r1/2
        constant = left_flux-ell**2/length*(u[e+1]-u[e])/dx
        for t, w in zip((roots+1)*dx/2, weights*dx/2):
            mismatch = constant+t*r0+t**2*r1/2
            error += length/ell**2*w*(mismatch.T@mismatch)
        flux = left_flux
    local_residual = final_residual[3*(len(knots)-1):].reshape(cells, 3, columns)
    for r in local_residual:
        error += length/(ell**2*(length/cells))*(r.T@r)
    return lower, lower+error, dict(rows=h.shape[0], subdivisions=subdivisions,
                                    inverse_residual_max=float(np.max(residual)),
                                    inverse_residual_evaluation=evaluation,
                                    inverse_residual_history=residual_history,
                                    relative_loewner_error_bound=float(linalg.eigvalsh(error, lower)[-1]))


def beam_controls():
    length, ell, cells = 1., .4, 4
    results = []
    for arm, width, name in ((np.zeros(3), 0., 'constant_force'),
                             (np.array((0., 0., -.05)), .1, 'coupled_manufactured')):
        a = skew(arm); vector = np.array((.3, -.2, .1))
        theta = (np.zeros((cells, 3)) if name == 'constant_force' else
                 np.array(((.2, -.1, .3), (-.1, .2, .1), (.3, .1, -.2), (.1, -.3, .2))))
        borders = np.linspace(0., length, cells+1); hcell = length/cells
        b_integral = hcell-ell*(np.sinh((length-borders[:-1])/ell)-
                                     np.sinh((length-borders[1:])/ell))/np.cosh(length/ell)
        gram = a.T@a+width**2/12*np.diag((1., 0., 1.))+ell**2*np.eye(3)
        c = hcell/length*gram
        moments = np.array([c@t-b_integral[j]/length*a.T@vector for j, t in enumerate(theta)])
        forces = np.array([(vector-a@t)/length for t in theta])
        exact = (float(vector@vector)*(1-ell/length*np.tanh(length/ell))
                 -2*sum(b_integral[j]/length*float(vector@a@t) for j, t in enumerate(theta))
                 +sum(float(t@c@t) for t in theta))
        rows = []
        for subdivision in (2, 4, 8):
            lo, hi, info = beam_bracket(forces[:, :, None], moments[:, :, None], length=length,
                                       ell=ell, arm=arm, width=width, subdivisions=subdivision)
            assert lo[0, 0] <= exact*(1+1e-12) and hi[0, 0] >= exact*(1-1e-12)
            rows.append(dict(**info, lower=float(lo[0, 0]), exact=exact, upper=float(hi[0, 0])))
        assert rows[1]['relative_loewner_error_bound'] < .35*rows[0]['relative_loewner_error_bound']
        assert rows[2]['relative_loewner_error_bound'] < .35*rows[1]['relative_loewner_error_bound']
        results.append(dict(name=name, levels=rows))
    return results


def saved_action_comparison(previous):
    old = json.loads(previous.read_text())
    # Exact original source/case binding; no geometry inference from outputs.
    expected = Path(__file__).resolve().with_name('b3_e4_bl5_reference_actions_dev.py')
    if not expected.exists():
        raise FileNotFoundError('original frozen reference-action source required')
    assert old['source_sha256'] == hashlib.sha256(expected.read_bytes()).hexdigest()
    if (old['status'] != 'COMPLETED_DEVELOPMENT_ONLY' or old['policy']['shell_trace_segments'] != 8 or
            old['policy']['beam_halfcells'] != 16 or old['policy']['span_halfcells'] != 2 or
            old['ell_m'] != .4 or old['shell_width_m'] != .2 or old['beam_norm_width_m'] != .1):
        raise ValueError('unchanged flat boundary-line saved reference required')
    length, width, ell, cells, supports = 1., .2, .4, 16, 8
    q = np.array((1., 1., 1., ell, ell))
    coefficients = np.eye(5*supports).reshape(5, supports, 5*supports)
    density = coefficients*q[:, None, None]
    # Independent flat-frame exerted-work map, including the actual surface arms.
    fb = density[:3].transpose(1, 0, 2)
    mb = np.zeros_like(fb)
    mb[:, 0] = .05*density[1]-density[4]
    mb[:, 1] = -.05*density[0]+density[3]
    shell = np.zeros_like(density)
    shell[:3] = -density[:3]
    shell[3] = .0175*density[1]+density[4]
    shell[4] = -.0175*density[0]-density[3]
    scalar_lo, scalar_hi, shell_info = p0_shell_bracket(np.linspace(0., length, supports+1),
                                                       length, width, ell, 4096)
    ms_lo = np.zeros((5*supports, 5*supports)); ms_hi = np.zeros_like(ms_lo)
    for channel in range(5):
        weight = 1. if channel < 3 else 1/ell**2
        load = shell[channel]
        ms_lo += weight*(load.T@scalar_lo@load)
        ms_hi += weight*(load.T@scalar_hi@load)
    force_cells = np.repeat(fb, 2, axis=0)
    moment_cells = np.repeat(mb, 2, axis=0)/cells  # integrated moments, no /h thereafter
    refinements = []
    for subdivision in (8, 16, 32):
        mb_lo, mb_hi, beam_info = beam_bracket(force_cells, moment_cells, length=length, ell=ell,
                                              arm=np.array((0., 0., -.05)), width=.1,
                                              subdivisions=subdivision)
        lo, hi = mb_lo+ms_lo, mb_hi+ms_hi
        error = float(linalg.eigvalsh(hi-lo, lo)[-1])
        refinements.append(dict(beam=beam_info, total_relative_loewner_error_bound=error))
        if error <= 1e-3:  # reference-only preset; no native beta value is inspected.
            break
    actions = np.array(old['force_equivalent_mu']).transpose(0, 2, 1).reshape(7, 5*supports).T
    shell_lower = np.einsum('ij,ij->j', actions, ms_lo@actions)
    shell_upper = np.einsum('ij,ij->j', actions, ms_hi@actions)
    total_lower = np.einsum('ij,ij->j', actions, lo@actions)
    total_upper = np.einsum('ij,ij->j', actions, hi@actions)
    old_shell = np.array(old['reference_levels'][-1]['shell_dual'])
    old_total = np.array(old['reference_levels'][-1]['total_dual'])
    assert np.all(old_shell <= shell_upper*(1+1e-11))
    assert np.all(old_total <= total_upper*(1+1e-11))
    return dict(previous_sha256=hashlib.sha256(previous.read_bytes()).hexdigest(),
                full_basis_columns=5*supports, shell=shell_info, beam_refinements=refinements,
                reference_budget_passed=refinements[-1]['total_relative_loewner_error_bound'] <= 1e-3,
                action_names=old['action_names'], shell_lower=shell_lower.tolist(), shell_upper=shell_upper.tolist(),
                total_lower=total_lower.tolist(), total_upper=total_upper.tolist(),
                old_shell_relative_error_lower=(1-old_shell/shell_lower).tolist(),
                old_shell_relative_error_upper=(1-old_shell/shell_upper).tolist(),
                old_total_relative_error_lower=(1-old_total/total_lower).tolist(),
                old_total_relative_error_upper=(1-old_total/total_upper).tolist(),
                norm_basis_lower=lo.tolist(), norm_basis_upper=hi.tolist())


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--previous', type=Path); a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    pools = threadpool_info(); assert pools and all(t['num_threads'] == 1 for t in pools)
    started = time.perf_counter()
    result = dict(status='COMPLETED_DEVELOPMENT_ONLY', threads=pools, python=sys.version,
                  numpy=np.__version__, controls=beam_controls())
    if a.previous:
        result['comparison'] = saved_action_comparison(a.previous)
    result['elapsed_seconds'] = time.perf_counter()-started
    with a.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2)
    print(json.dumps(dict(status=result['status'], elapsed_seconds=result['elapsed_seconds'],
                         reference_budget_passed=result.get('comparison', {}).get('reference_budget_passed'))))
