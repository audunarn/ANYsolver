"""Bounded shell line-dual modal oracle, independent of native constraint rows.

Supported x=0, natural x=L/y=W, boundary line y=0. Positive finite modal
sum plus a Loewner tail majorant brackets every admitted P0 action. This is
an auxiliary reference oracle, never a mechanical stiffness or native beta.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info


def p0_shell_bracket(knots, length, width, ell, modes):
    knots = np.asarray(knots, dtype=float)
    if (knots.ndim != 1 or len(knots) < 2 or len(knots) > 129 or
            not np.isfinite(knots).all() or np.any(np.diff(knots) <= 0) or
            knots[0] != 0. or knots[-1] != length or
            min(length, width, ell) <= 0 or modes < len(knots)-1):
        raise ValueError('bounded positive complete P0 line required')
    count = len(knots)-1
    k = (np.arange(modes)+.5)*np.pi/length
    alpha = np.sqrt(1+ell**2*k**2)/ell
    # p_n=(2/L) int p sin(k_n x): exact P0 coefficient integrals.
    coefficient = 2/(length*k[:, None])*(np.cos(k[:, None]*knots[:-1])-
                                        np.cos(k[:, None]*knots[1:]))
    weight = length**2*width/(2*ell**2*alpha*np.tanh(alpha*width))
    lower = coefficient.T@(weight[:, None]*coefficient)
    # Integration by parts: coefficient numerator p0+sum_j jump_j cos(k*xj),
    # cos(k*L)=0. Cauchy gives <=count*||D p||^2. alpha>=k and coth is decreasing.
    difference = np.eye(count)
    for j in range(1, count):
        difference[j, j-1] = -1.
    first = modes+.5
    series_bound = first**-3+1/(2*first**2)
    k_first = first*np.pi/length
    tail_coefficient = (2*width/ell**2/np.tanh(k_first*width)*
                        (length/np.pi)**3*series_bound*count)
    tail = tail_coefficient*(difference.T@difference)
    relative_tail = float(linalg.eigvalsh(tail, lower)[-1])
    return lower, lower+tail, dict(modes=modes, supports=count,
                                   relative_loewner_tail_bound=relative_tail,
                                   lower_min_eigenvalue=float(linalg.eigvalsh(lower)[0]))


def modal_control():
    length, width, ell = 1., .2, .4
    # A single sine mode has a closed-form Riesz dual. A nonuniform P0
    # projection tends to it; the oracle is checked against Q1 separately.
    k = np.pi/(2*length)
    alpha = np.sqrt(1+ell**2*k**2)/ell
    exact_sine = length**2*width/(2*ell**2*alpha*np.tanh(alpha*width))
    out = []
    for supports in (8, 16, 32):
        knots = np.linspace(0., length, supports+1)
        # Exact support-average sine, fixed physically; not quadrature atoms.
        p = (np.cos(k*knots[:-1])-np.cos(k*knots[1:]))/(k*np.diff(knots))
        lower, upper, info = p0_shell_bracket(knots, length, width, ell, 4096)
        value = float(p@lower@p)
        out.append(dict(**info, sine_projection_dual=value, sine_exact_dual=exact_sine,
                        sine_projection_relative_error=abs(value/exact_sine-1.),
                        sine_projection_upper=float(p@upper@p)))
    assert out[1]['sine_projection_relative_error'] < .3*out[0]['sine_projection_relative_error']
    assert out[2]['sine_projection_relative_error'] < .3*out[1]['sine_projection_relative_error']
    assert out[2]['sine_projection_relative_error'] < 1e-3
    # Every P0 vector is bracketed, not just selected loads. Independent sums
    # with four times as many modes must lie inside the lower/tail bracket.
    knots = np.array((0., .07, .21, .49, .76, 1.))
    lower, upper, info = p0_shell_bracket(knots, length, width, ell, 1024)
    finer, _, _ = p0_shell_bracket(knots, length, width, ell, 4096)
    assert np.min(linalg.eigvalsh(finer-lower)) > -1e-12
    assert np.min(linalg.eigvalsh(upper-finer)) > -1e-12
    # Unit conversion for physical density p'=p/scale, x'=scale*x.
    scaled, scaled_upper, _ = p0_shell_bracket(1000*knots, 1000*length,
                                               1000*width, 1000*ell, 1024)
    np.testing.assert_allclose(scaled/1000**2, lower, atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(scaled_upper/1000**2, upper, atol=1e-12, rtol=1e-12)
    return dict(sine_controls=out, nonuniform_bracket=info,
                modes_1024_4096_loewner_checks='passed', equivalent_units='passed')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    pools = threadpool_info()
    assert pools and all(t['num_threads'] == 1 for t in pools)
    result = dict(status='COMPLETED_DEVELOPMENT_ONLY', threads=pools, controls=modal_control())
    with a.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2)
    print(json.dumps(dict(status=result['status'])))
