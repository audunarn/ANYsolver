"""Coarse projected-density lifting discriminator before a separate native check.

The auxiliary norm is positive kinematics, NOT the mechanical stiffness.
Scalar registration is produced before inspecting a native auxiliary beta.
No old P0 floor, growing-family acceptance, loaded solve or F03 invocation.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info

from scripts.b3_e4_bl5_modal_reference_dev import p0_shell_bracket
from scripts.b3_e4_bl5_riesz_controls_dev import shell_scalar

LENGTH, WIDTH, ELL = 1., .2, .4
NX, NY, CELLS, SUPPORTS = 16, 4, 32, 8
TOL = 1e-10
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def integrated_p1(knots, values, support_knots):
    """Exact independent boundary work; no owner or mechanics imports."""
    out = np.zeros((len(knots), values.shape[1]))
    cuts = np.unique(np.r_[knots, support_knots])
    for left, right in zip(cuts[:-1], cuts[1:]):
        middle = (left+right)/2
        e = int(np.searchsorted(knots, middle)-1)
        j = int(np.searchsorted(support_knots, middle)-1)
        t = (middle-knots[e])/(knots[e+1]-knots[e])
        out[e] += (right-left)*(1-t)*values[j]
        out[e+1] += (right-left)*t*values[j]
    return out


def projection():
    """Independent physical halfcell density coefficients, exact rational means."""
    p = np.zeros((CELLS, 2*SUPPORTS))
    for cell in range(CELLS):
        support = cell//4
        left, right = Fraction(support, SUPPORTS), Fraction(support+1, SUPPORTS)
        midpoint = Fraction(2*cell+1, 2*CELLS)
        p[cell, 2*support] = 1.
        p[cell, 2*support+1] = float(2*(midpoint-left)/(right-left)-1)
    return p


def lower_gram(h, action):
    z = splu(h).solve(action)
    residual = float(np.linalg.norm(h@z-action)/np.linalg.norm(action))
    cross = action.T@z
    gram = cross+cross.T-z.T@(h@z)
    skew = float(np.linalg.norm(gram-gram.T)/np.linalg.norm(gram))
    if max(residual, skew) > TOL:
        raise ArithmeticError('auxiliary inverse/symmetry budget unresolved')
    # Symmetrize only a computed inverse-functional Gram, never mechanical K.
    return (gram+gram.T)/2, residual, skew


def scalar_registration(output):
    p = projection()
    xs, _, h, active = shell_scalar(LENGTH, WIDTH, ELL, NX, NY)
    half_knots = np.linspace(0., LENGTH, CELLS+1)
    boundary = integrated_p1(xs, p, half_knots)
    full = np.zeros(((NX+1)*(NY+1), p.shape[1])); full[:NX+1] = boundary
    t = full[active]
    g, residual, skew = lower_gram(h, t)
    # All reference cross-products are retained; no diagonal or sampled loads.
    preparation = []
    for modes in (4096, 8192, 16384):
        ml, mu, info = p0_shell_bracket(half_knots, LENGTH, WIDTH, ELL, modes)
        lower, upper = p.T@ml@p, p.T@mu@p
        error = float(linalg.eigvalsh(upper-lower, lower)[-1])
        preparation.append(dict(modes=modes, projected_relative_tail=error,
                                full_halfcell_relative_tail=info['relative_loewner_tail_bound']))
        if error <= 1e-3:
            break
    else:
        raise ArithmeticError('preset complete modal reference budget exhausted')
    values, vectors = linalg.eigh(upper, g)
    eig_residual = float(np.linalg.norm(upper@vectors-(g@vectors)*values)/np.linalg.norm(upper@vectors))
    cs2 = float(values[-1])
    rho = np.hypot(.05, .1/2)/ELL
    k = max(2., 1+2*rho*rho)
    product2 = max(2*cs2, k*max(2*cs2, 1+rho*rho))
    floor = 1/np.sqrt(product2)
    safe = floor/np.sqrt(1.001)-1e-6
    condition = dict(discrete=float(np.linalg.cond(g)), reference=float(np.linalg.cond(upper)))
    # Force-density basis is changed reciprocally, without changing work/norm.
    d = np.diag(np.geomspace(.2, 5., p.shape[1]))
    transformed = linalg.eigvalsh(d@upper@d, d@g@d)
    congruence_error = float(np.max(np.abs(transformed-values))/max(1., cs2))
    # Reassemble equivalent length units: geometry and ell scale by a, H is
    # invariant and unit-density action scales by a. Physical density scales
    # reciprocally, preserving the same physical work and dimensionless quotient.
    unit_scale = 1000.
    xu, _, hu, au = shell_scalar(LENGTH*unit_scale, WIDTH*unit_scale,
                                 ELL*unit_scale, NX, NY)
    tu = np.zeros_like(full)
    tu[:NX+1] = integrated_p1(xu, p, half_knots*unit_scale)
    gu, _, _ = lower_gram(hu, tu[au])
    _, mu, _ = p0_shell_bracket(half_knots*unit_scale, LENGTH*unit_scale,
                               WIDTH*unit_scale, ELL*unit_scale, modes)
    unit_values = linalg.eigvalsh(p.T@mu@p, gu)
    unit_error = float(np.max(np.abs(unit_values-values))/max(1., cs2))
    np.testing.assert_allclose(tu/unit_scale, full, rtol=1e-12, atol=1e-13)
    # Duplicate rows are really deficient, rather than removed before assessment.
    duplicate = np.c_[t, t[:, 0]]
    duplicate_rank = np.linalg.matrix_rank(duplicate)
    assert duplicate_rank == t.shape[1] < duplicate.shape[1]
    # Registered scalar checkerboard: [1,-3,3,-1] on each support has
    # zero supported coarse-Q1 work but nonzero continuous reference work.
    checker = np.tile((1.,-3.,3.,-1.), SUPPORTS)
    checker_t = integrated_p1(xs, checker[:, None], half_knots)[:, 0]
    checker_defect = float(np.max(np.abs(checker_t[1:])))
    checker_energy = float(checker@ml@checker)
    assert checker_defect <= 1e-13 and checker_energy > 0.
    # Every endpoint weight and both moments checked against exact rational hats.
    from scripts.r8_bl5_projected_reference_action_dev import integrated_projected_weights
    exact = np.zeros_like(boundary)
    for j in range(SUPPORTS):
        weights, _ = integrated_projected_weights(Fraction(j,SUPPORTS),
            Fraction(j+1,SUPPORTS), NX, CELLS)
        for degree, rows in enumerate(weights):
            for node, weight in rows.items(): exact[node, 2*j+degree] = float(weight)
    endpoint_error = float(np.max(np.abs(exact-boundary)))
    assert endpoint_error <= 1e-13
    # Independently derived near-deficiency: all affine support densities
    # cancel interior shell nodal work, leaving only the physical free endpoint.
    affine = np.tile((0.,1.), SUPPORTS)
    endpoint_only = np.zeros_like(boundary[:, 0]); endpoint_only[0] = -5/(8*CELLS)
    endpoint_only[-1] = 5/(8*CELLS)
    np.testing.assert_allclose(boundary@affine, endpoint_only, atol=1e-13, rtol=0.)
    affine_duals = dict(discrete=float(affine@g@affine),
                        reference_lower=float(affine@lower@affine))
    numerical = dict(reference_error=error<=1e-3, inverse_residual=residual<=TOL,
        eigen_residual=eig_residual<=TOL, gram_symmetry=skew<=TOL,
        gram_condition=max(condition.values())<=1e4,
        positive_all_scalar_eigenvalues=bool(np.all(values>0)),
        unit_and_basis_congruence=max(unit_error,congruence_error)<=TOL)
    result = dict(status='ELIGIBLE_COARSE_DEVELOPMENT_BOUND' if all(numerical.values())
        else 'UNRESOLVED_COARSE_DEVELOPMENT_BOUND', predicates=numerical,
        fixture=dict(nx=NX,ny=NY,halfcells=CELLS,supports=SUPPORTS),
        norm=dict(length=LENGTH,width=WIDTH,ell=ELL,beam_width=.1,beam_arm=[0.,0.,-.05],
                  shell_arm=[0.,0.,.0175]),
        reference_preparation=preparation, cs_squared_upper=cs2,
        product_squared_upper=float(product2), raw_product_floor=float(floor),
        safe_case_floor=float(safe), conditions=condition,
        inverse_residual=residual, eigen_residual=eig_residual,
        all_scalar_generalized_eigenvalues=values.tolist(),
        controls=dict(endpoint_moment_max_abs=endpoint_error, duplicate_rank=int(duplicate_rank),
            duplicate_columns=int(duplicate.shape[1]), checkerboard_coarse_max_abs=checker_defect,
            checkerboard_positive_reference_dual=checker_energy,
            all_affine_endpoint_coefficient=float(endpoint_only[-1]),
            all_affine_duals=affine_duals,
            unit_congruence_error=unit_error,basis_congruence_error=congruence_error),
        limitations='coarse sufficient lifting bound only; no native beta, growing-space floor, mechanical nullspace, locking, transfer or F03 acceptance',
        source_sha256=sha(__file__), helpers={Path(func.__code__.co_filename).name:
            sha(func.__code__.co_filename) for func in (
                p0_shell_bracket, shell_scalar, integrated_projected_weights)})
    np.savez(output.with_suffix('.npz'),projection=p,action=t,discrete_lower=g,
             reference_lower=lower,reference_upper=upper)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix('.npz').exists():
        raise FileExistsError(args.output)
    pools = threadpool_info()
    if not pools or any(p['num_threads'] != 1 for p in pools):
        raise RuntimeError('effective one-thread pools required')
    result = scalar_registration(args.output)
    print(json.dumps({name:result[name] for name in ('status','cs_squared_upper',
        'safe_case_floor','conditions','controls')}))
    raise SystemExit(0 if all(result['predicates'].values()) else 1)
