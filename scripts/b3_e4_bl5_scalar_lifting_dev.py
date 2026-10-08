"""Independent finite-domain scalar lifting constants; no GE matrix or beta.

The full P0 action space is compared with the independently defined supported
bulk H1 norm. Modal upper reference and variational lower inverse functional
give a conservative analytic bound, evaluated in ordinary binary64 arithmetic.
This is not an interval certificate or mechanical KKT acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info

from scripts.b3_e4_bl5_modal_reference_dev import p0_shell_bracket
from scripts.b3_e4_bl5_riesz_controls_dev import shell_scalar


def lifting_case(nx, ny, halfcells, coefficient):
    length, width, ell = 1., .2, .4
    span = max(1, int(np.ceil(coefficient*halfcells/nx)))
    if halfcells % span:
        raise ValueError('complete uniform supports required')
    supports = halfcells//span
    knots = np.linspace(0., length, supports+1)
    xs, ys, h, active = shell_scalar(length, width, ell, nx, ny)
    # Independent exact Q1 boundary-line integration, split at both boundaries.
    action_full = np.zeros(((nx+1)*(ny+1), supports))
    for j, (a, b) in enumerate(zip(knots[:-1], knots[1:])):
        cuts = np.unique(np.r_[a, xs[(xs > a) & (xs < b)], b])
        for left, right in zip(cuts[:-1], cuts[1:]):
            midpoint = (left+right)/2
            e = min(nx-1, int(np.searchsorted(xs, midpoint)-1))
            t = (midpoint-xs[e])/(xs[e+1]-xs[e])
            action_full[e, j] += (right-left)*(1-t)
            action_full[e+1, j] += (right-left)*t
    action = action_full[active]
    z = splu(h).solve(action)
    residual = h@z-action
    scaled_residual = np.linalg.norm(residual)/np.linalg.norm(action)
    if scaled_residual > 1e-10:
        raise ArithmeticError('scalar inverse residual failed')
    # For any computed z this functional is analytically <= exact discrete Gram.
    cross = action.T@z
    lower_discrete = cross+cross.T-z.T@(h@z)
    lower_discrete = (lower_discrete+lower_discrete.T)/2
    minimum = float(linalg.eigvalsh(lower_discrete)[0])
    if minimum <= 0:
        raise ArithmeticError('scalar moment action is deficient')
    for modes in (4096, 8192, 16384):
        modal_lower, modal_upper, modal_info = p0_shell_bracket(knots, length, width, ell, modes)
        if modal_info['relative_loewner_tail_bound'] <= 1e-3:
            break
    if modal_info['relative_loewner_tail_bound'] > 1e-3:
        raise ArithmeticError('preset modal reference budget exceeded')
    values, vectors = linalg.eigh(modal_upper, lower_discrete)
    cs_squared = float(values[-1])
    eigen_residual = np.linalg.norm(modal_upper@vectors-
        (lower_discrete@vectors)*values[None, :])/max(np.linalg.norm(modal_upper@vectors), 1e-30)
    if eigen_residual > 1e-10 or not np.isfinite(cs_squared):
        raise ArithmeticError('lifting eigen residual failed')
    # Finite-domain product bound, checked independently before any GE beta.
    # Max surface arm includes the declared symmetric .1m transverse width.
    rho = np.hypot(.05, .1/2)/ell
    k = max(2., 1+2*rho*rho)
    product_squared = max(2*cs_squared, k*max(2*cs_squared, 1+rho*rho))
    alignment = np.max(np.abs(knots/(length/nx)-np.rint(knots/(length/nx))))
    return dict(nx=nx, ny=ny, beam_halfcells=halfcells, coefficient=coefficient,
        span=span, supports=supports, shell_intervals_per_support=nx/supports,
        alignment_error=alignment, scalar_rows=h.shape[0], scalar_nnz=h.nnz,
        inverse_relative_residual=float(scaled_residual),
        eigen_relative_residual=float(eigen_residual),
        discrete_gram_min_eigenvalue=minimum,
        discrete_gram_condition=float(np.linalg.cond(lower_discrete)),
        modal_reference=modal_info, cs_squared_upper=cs_squared,
        product_squared_upper=product_squared,
        prospective_product_floor=1/np.sqrt(product_squared))


def evaluate():
    rows = []
    # Ratios mean native HALF-CELLS:shell trace segments. Start at nx=16 so
    # 1:8 still has two halfcells, the minimum native BL5 admission.
    for nx, ny in ((16, 4), (32, 8), (64, 16)):
        for numerator, denominator in ((1, 8), (1, 4), (1, 2), (1, 1), (2, 1), (4, 1), (8, 1)):
            halfcells = nx*numerator//denominator
            row = lifting_case(nx, ny, halfcells, 2)
            assert row['alignment_error'] < 1e-12
            assert row['shell_intervals_per_support'] >= 2
            row['ratio'] = f'{numerator}:{denominator}'
            rows.append(row)
    # Predeclared deficient-resolution comparison, not candidate tuning.
    deficient = [lifting_case(nx, ny, nx, 1) for nx, ny in ((16, 4), (32, 8), (64, 16))]
    assert deficient[2]['cs_squared_upper'] > deficient[1]['cs_squared_upper'] > deficient[0]['cs_squared_upper']
    return dict(status='COMPLETED_DEVELOPMENT_ONLY', cases=rows,
        # Saved 40-action fixture uses c_lambda=1 (span2/eight supports),
        # outside the c_lambda=2 admission family; never assign its c2 floor.
        saved_work_map_anchor=lifting_case(8, 2, 16, 1),
        deficient_one_interval_controls=deficient,
        finite_family_floor=min(row['prospective_product_floor'] for row in rows),
        scope='flat rectangle, boundary line, common root support, constant arms, P0; not GE beta/KKT/F03 acceptance',
        arithmetic='analytic Loewner formulas evaluated in binary64; no outward-rounded interval certificate')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    pools = threadpool_info()
    assert pools and all(pool['num_threads'] == 1 for pool in pools)
    start = time.monotonic()
    result = evaluate()
    result.update(threads=pools, elapsed_seconds=time.monotonic()-start)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
    print(json.dumps(dict(status=result['status'], cases=len(result['cases']),
        finite_family_floor=result['finite_family_floor'])))
