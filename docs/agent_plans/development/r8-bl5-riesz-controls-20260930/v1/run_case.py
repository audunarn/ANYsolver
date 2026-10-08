"""Independent positive trace-norm controls; no candidate beta or F03 run.

Continuous P1 axis translations, fixed cellconstant directors and Q1 bulk
shell fields discretize the reviewed reference norm. Mechanical K is absent.
All analytical targets and tolerances are fixed before this script is run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info


def skew(a):
    x, y, z = a
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def scalar_1d(knots):
    rows, cols, mass, grad = [], [], [], []
    for i, dx in enumerate(np.diff(knots)):
        for a in range(2):
            for b in range(2):
                rows.append(i+a); cols.append(i+b)
                mass.append(dx*(2. if a == b else 1.)/6.)
                grad.append((1. if a == b else -1.)/dx)
    n = len(knots)
    return (sparse.coo_matrix((mass, (rows, cols)), shape=(n, n)).tocsc(),
            sparse.coo_matrix((grad, (rows, cols)), shape=(n, n)).tocsc())


def force_load(knots, force):
    """Physical work integral, independent of any native constraint rows."""
    out = np.zeros((len(knots), 3))
    xi, wi = np.polynomial.legendre.leggauss(8)
    for i, (a, b) in enumerate(zip(knots[:-1], knots[1:])):
        for x, w in zip((a+b)/2+(b-a)*xi/2, wi*(b-a)/2):
            t = (x-a)/(b-a)
            out[i] += w*(1-t)*force(x)
            out[i+1] += w*t*force(x)
    return out.reshape(-1)


def beam_norm(length, ell, cells, subdivisions, arm, width=0.):
    """Sparse full coupled auxiliary form, retaining all cell directors."""
    knots = np.linspace(0., length, cells*subdivisions+1)
    mass, grad = scalar_1d(knots)
    translation = sparse.kron((mass+ell**2*grad)/length, sparse.eye(3), format='csc')
    mean_a = skew(arm)
    # Symmetric uniform transverse-width average of A.T A.
    gram = mean_a.T@mean_a + width**2/12*np.diag((1., 0., 1.))
    h = length/cells
    c = (h/length)*(gram+ell**2*np.eye(3))
    rr, cc, vv = [], [], []
    dx = length/(cells*subdivisions)
    for j in range(cells):
        for e in range(j*subdivisions, (j+1)*subdivisions):
            for node in (e, e+1):
                for a in range(3):
                    for b in range(3):
                        rr.append(3*j+a); cc.append(3*node+b)
                        vv.append(dx/(2*length)*mean_a.T[a, b])
    d = sparse.coo_matrix((vv, (rr, cc)), shape=(3*cells, 3*len(knots))).tocsc()
    rotation = sparse.kron(sparse.eye(cells), sparse.csc_matrix(c), format='csc')
    h_full = sparse.bmat(((translation, -d.T), (-d, rotation)), format='csc')
    active = np.arange(3, h_full.shape[0])  # U(0)=0, no Theta root support.
    return knots, h_full[active][:, active], active, c


def dual(h, action):
    factor = splu(h)
    z = factor.solve(action)
    residual = np.linalg.norm(h@z-action)/max(np.linalg.norm(action), 1e-30)
    energy = float(action@z)
    if residual > 1e-10 or not np.isfinite(energy) or energy <= 0:
        raise ArithmeticError('positive auxiliary inverse action failed')
    return energy, float(residual), z


def beam_controls():
    length, ell, cells = 1., .4, 4
    vector = np.array((.3, -.2, .1))
    arm, width = np.array((0., 0., -.05)), .1
    a = skew(arm)
    gram = a.T@a+width**2/12*np.diag((1., 0., 1.))
    k = np.pi/(2*length)
    theta = np.array(((.2, -.1, .3), (-.1, .2, .1), (.3, .1, -.2), (.1, -.3, .2)))
    hcell = length/cells
    borders = np.linspace(0., length, cells+1)
    sin_int = (np.cos(k*borders[:-1])-np.cos(k*borders[1:]))/k
    c = hcell/length*(gram+ell**2*np.eye(3))
    moments = np.array([c@t-sin_int[j]/length*a.T@vector for j, t in enumerate(theta)])
    manufactured_energy = ((1+ell**2*k**2)*float(vector@vector)/2
                           -2*sum(sin_int[j]*float(vector@a@t)/length for j, t in enumerate(theta))
                           +sum(float(t@c@t) for t in theta))
    exact = {'constant': length*(length-ell*np.tanh(length/ell)),
             'ramp': length*(length**3/3-ell**2*length+ell**3*np.tanh(length/ell)),
             'endpoint': length/ell*np.tanh(length/ell),
             'moment': sum(length*float(t@t)/(hcell*ell**2) for t in theta),
             'coupled_manufactured': manufactured_energy}
    records = []
    for subdivisions in (4, 8, 16):
        row = {'subdivisions_per_cell': subdivisions, 'controls': {}}
        for name in exact:
            coupled = name == 'coupled_manufactured'
            knots, h, active, _ = beam_norm(length, ell, cells, subdivisions,
                                           arm if coupled else np.zeros(3), width if coupled else 0.)
            if name == 'constant':
                load = force_load(knots, lambda x: np.array((1., 0., 0.)))
                m = np.zeros((cells, 3))
            elif name == 'ramp':
                load = force_load(knots, lambda x: np.array((x, 0., 0.)))
                m = np.zeros((cells, 3))
            elif name == 'endpoint':
                load = np.zeros(3*len(knots)); load[-3] = 1.
                m = np.zeros((cells, 3))
            elif name == 'moment':
                load = np.zeros(3*len(knots)); m = theta
            else:
                def manufactured_force(x):
                    j = min(int(x/hcell), cells-1)
                    return ((1+ell**2*k**2)*vector*np.sin(k*x)-a@theta[j])/length
                load = force_load(knots, manufactured_force); m = moments
            action = np.r_[load, m.reshape(-1)][active]
            energy, residual, z = dual(h, action)
            error = abs(energy/exact[name]-1.)
            if name == 'moment':
                # Root cell rotation is free, even though U(0) is supported.
                assert np.allclose(z[-3*cells:].reshape(cells, 3), theta*length/(hcell*ell**2), rtol=1e-12)
            row['controls'][name] = dict(dual=energy, exact=exact[name], relative_error=error,
                                          inverse_residual=residual)
        records.append(row)
    # P1 Galerkin dual approaches the independent target from below; O(h^2).
    for name in exact:
        errors = [r['controls'][name]['relative_error'] for r in records]
        if name == 'moment':
            assert max(errors) < 1e-12
        else:
            assert errors[1] < .35*errors[0] and errors[2] < .35*errors[1]
            assert errors[2] < 1e-3
            assert all(r['controls'][name]['dual'] <= exact[name]*(1+1e-12) for r in records)
    return records


def shell_scalar(length, width, ell, nx, ny):
    xs, ys = np.linspace(0., length, nx+1), np.linspace(0., width, ny+1)
    mx, kx = scalar_1d(xs); my, ky = scalar_1d(ys)
    h = (sparse.kron(my, mx)+ell**2*(sparse.kron(my, kx)+sparse.kron(ky, mx)))/(length*width)
    active = np.array([j*(nx+1)+i for j in range(ny+1) for i in range(1, nx+1)])
    return xs, ys, h.tocsc()[active][:, active], active


def shell_controls():
    length, width, ell = 1., .2, .4
    k = np.pi/(2*length)
    decay = np.sqrt(1+ell**2*k**2)/ell
    # y=0 boundary line, natural boundary y=width; root x=0 Dirichlet.
    scalar_exact = length*width*length/2/(ell**2*decay*np.tanh(decay*width))
    a = skew((0., 0., .0175))
    force, direct = np.array((.3, -.4, .2)), np.array((.1, -.2))
    moment = (-a.T@force)[:2]+direct
    targets = {'force': float(force@force)*scalar_exact,
               'director': float(direct@direct)/ell**2*scalar_exact,
               'eccentric': (float(force@force)+float(moment@moment)/ell**2)*scalar_exact}
    records = []
    for nx, ny in ((16, 4), (32, 8), (64, 16)):
        xs, ys, h, active = shell_scalar(length, width, ell, nx, ny)
        line = force_load(xs, lambda x: np.array((np.sin(k*x), 0., 0.)))[::3]
        action = np.zeros((ny+1)*(nx+1)); action[:nx+1] = line
        h5 = sparse.block_diag((h, h, h, ell**2*h, ell**2*h), format='csc')
        all_records = {}
        for name, target in targets.items():
            physical = {'force': np.r_[force, np.zeros(2)],
                        'director': np.r_[np.zeros(3), direct],
                        'eccentric': np.r_[force, moment]}[name]
            work = np.concatenate([component*action[active] for component in physical])
            value, residual, _ = dual(h5, work)
            all_records[name] = dict(dual=value, exact=target, relative_error=abs(value/target-1.),
                                     inverse_residual=residual)
        # Independent volume control: y-uniform loading, exact 1D reduction.
        my, _ = scalar_1d(ys)
        volume = np.kron(np.asarray(my@np.ones(len(ys))).reshape(-1), line)[active]
        volume_energy, volume_residual, _ = dual(h, volume)
        # Functional p sin(kx) dxdy, area-normalized H gives |Omega|*W*L/2.
        volume_exact = length**2*width**2/(2*(1+ell**2*k**2))
        all_records['volume'] = dict(dual=volume_energy, exact=volume_exact,
                                     relative_error=abs(volume_energy/volume_exact-1.), inverse_residual=volume_residual)
        records.append(dict(nx=nx, ny=ny, rows=h.shape[0], controls=all_records))
    for name in records[0]['controls']:
        errors = [r['controls'][name]['relative_error'] for r in records]
        assert errors[1] < .35*errors[0] and errors[2] < .35*errors[1]
        assert errors[2] < 1e-3
    return records


def evaluate():
    pools = threadpool_info()
    if not pools or any(p['num_threads'] != 1 for p in pools):
        raise RuntimeError('development controls require effective single-thread BLAS')
    start = time.perf_counter()
    return dict(status='COMPLETED_DEVELOPMENT_ONLY', threads=pools,
                beam=beam_controls(), shell=shell_controls(),
                elapsed_seconds=time.perf_counter()-start,
                scope='positive auxiliary inverse actions only; no candidate beta, F03, mechanics condensation or acceptance')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2)
    print(json.dumps(dict(status=result['status'], elapsed_seconds=result['elapsed_seconds'])))
