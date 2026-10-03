"""Prescribed virgin torsion using saved native mixed operators; no loaded solve.

Compare exact broken-trace affine moments with an independent scalar reduction.
Only the beam's stationary torsion energy is used; the full indefinite mixed
matrix is not assigned an energy norm. This is development, not F03 acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from threadpoolctl import threadpool_info


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def patch(root):
    data = json.loads((root/'native/inputs.json').read_text())
    nx = data['layout']['nx']
    ns = len(data['layout']['shell_node_ids'])
    physical = data['layout']['counts']['physical_dofs']
    endpoints = np.asarray(data['policy']['support_endpoints_m'])
    supports = len(endpoints)-1
    m = 2*nx//supports
    assert nx == 32 and supports in (8, 16) and m in (4, 8)
    assert physical == 6*(ns+2*nx+1)
    np.testing.assert_array_equal(endpoints, np.linspace(0., 1., supports+1))
    with np.load(root/'native/operators.npz', allow_pickle=False) as z:
        matrices = {name: sparse.csr_matrix((z[name+'_data'], z[name+'_indices'],
            z[name+'_indptr']), shape=tuple(z[name+'_shape'])) for name in ('K', 'C')}
        fixed = z['fixed'].copy()
    k, c = matrices['K'], matrices['C']
    assert k.shape == (physical+24*nx,)*2 and c.shape == (10*supports, len(k.indptr)-1)
    stiffness = np.asarray(data['beams'][0]['section']['elastic'])
    torsion = float(stiffness[3, 3]); kappa = 1e-4
    assert torsion > 0. and np.count_nonzero(stiffness-np.diag(np.diag(stiffness))) == 0
    xyz = np.asarray(data['xyz_m'])
    assert xyz.shape == (ns+2*nx+1, 3)
    nodal = np.zeros(k.shape[0]); shell = nodal[:6*ns].reshape(-1, 6)
    shell[:, 3] = kappa*xyz[:ns, 0]
    shell[:, 1] = shell[:, 3]*(.0675-xyz[:ns, 2])
    shell[:, 2] = shell[:, 3]*xyz[:ns, 1]
    nodal[6*ns:physical].reshape(-1, 6)[:, 3] = kappa*xyz[ns:, 0]
    np.testing.assert_array_equal(nodal[fixed], 0.)
    psi = np.array([physical+24*b+3*h for b in range(nx) for h in (0, 1)])
    moments = np.array([physical+24*b+12+3*j for b in range(nx) for j in range(4)])
    unknown = np.r_[psi, moments]
    block = k[unknown][:, unknown].tocsc()
    rhs = -(k@nodal)[unknown]
    natural = nodal.copy(); natural[unknown] = spsolve(block, rhs)
    expected_psi = kappa*(np.arange(2*nx)+.5)/(2*nx)
    np.testing.assert_allclose(natural[psi], expected_psi, rtol=1e-11, atol=1e-14)
    np.testing.assert_allclose(natural[moments], torsion*kappa, rtol=1e-11, atol=1e-10)
    # Last BL5 channel is common physical Rx. Actual rows retain both moments.
    rows = np.arange(8*supports, 10*supports)
    d = c[rows][:, unknown]
    augmented = sparse.bmat([[block, d.T], [d, None]], format='csc')
    value = spsolve(augmented, np.r_[rhs, -(c@nodal)[rows]])
    constrained = nodal.copy(); constrained[unknown] = value[:len(unknown)]
    reaction = value[len(unknown):]
    h = 1./(2*nx); H = 1./supports
    raw = (c@natural)[rows].reshape(-1, 2)
    expected_moment = -kappa*H**2/(6*m*m)
    np.testing.assert_allclose(raw[:, 0], 0., rtol=0., atol=1e-14)
    np.testing.assert_allclose(raw[:, 1], expected_moment, rtol=1e-9, atol=1e-14)
    # Recover beam energy after stationary moment elimination, excluding shell.
    beam_k = k[6*ns:, 6*ns:]
    energy = lambda q: float(.5*q[6*ns:]@(beam_k@q[6*ns:]))
    continuum = .5*torsion*kappa*kappa
    natural_energy, constrained_energy = energy(natural), energy(constrained)
    predicted_ratio = 1.+1./(m*m-1.)
    np.testing.assert_allclose(natural_energy, continuum, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(constrained_energy/continuum, predicted_ratio, rtol=1e-10, atol=1e-12)
    equilibrium = block@value[:len(unknown)] + d.T@reaction-rhs
    assert np.linalg.norm(equilibrium)/max(1., np.linalg.norm(rhs)) <= 1e-10
    complete_gap = c@constrained
    assert np.max(np.abs(complete_gap)) <= 1e-12
    # Scalar energy from the independently eliminated complementary law.
    midpoint = expected_psi
    scalar_energy = continuum + float(np.sum(6*torsion/h*(constrained[psi]-midpoint)**2))
    np.testing.assert_allclose(scalar_energy, constrained_energy, rtol=1e-10, atol=1e-12)
    return dict(m=m, supports=supports, native_halfcells=2*nx,
        natural_affine_gap=raw.tolist(), expected_affine_gap=expected_moment,
        natural_energy_J=natural_energy, constrained_energy_J=constrained_energy,
        continuum_energy_J=continuum, energy_ratio=constrained_energy/continuum,
        predicted_ratio=predicted_ratio, independent_scalar_energy_J=scalar_energy,
        complete_gap_max=float(np.max(np.abs(complete_gap))),
        restricted_mixed_equilibrium=float(np.linalg.norm(equilibrium)/max(1., np.linalg.norm(rhs))),
        source_files={name: sha(root/'native'/name) for name in ('inputs.json', 'operators.npz')})


def main():
    p = argparse.ArgumentParser(); p.add_argument('--fixed', type=Path, required=True)
    p.add_argument('--growing', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    pools = threadpool_info(); assert pools and all(v['num_threads'] == 1 for v in pools)
    result = dict(status='COMPLETED_DEVELOPMENT_ONLY',
        scope='prescribed supported virgin torsion patch; no loaded accuracy, uniform stability or F03 acceptance',
        source_sha256=sha(__file__), pools=pools, cases=[patch(a.fixed), patch(a.growing)])
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({str(v['m']):v['energy_ratio'] for v in result['cases']}))


if __name__ == '__main__':
    main()
