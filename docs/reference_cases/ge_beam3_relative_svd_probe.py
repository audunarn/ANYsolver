"""Relative-SVD numerical probe, no mechanics change or qualification claim.

SciPy v1.16.3 flapack_other.pyf.src maps JOBA='CEFGAR', JOBU='UFWN',
JOBV='VJWN', JOBR 0=N, JOBT 0=N, JOBP 0=N. These exact options avoid
granting the driver's numerical rank truncation/perturbation permissions.
"""

import numpy as np
from scipy.linalg import lapack


def jacobi_svd(matrix):
    a = np.array(matrix, dtype=float, copy=True)
    if a.ndim != 2 or not 1 <= a.shape[1] <= min(a.shape[0], 256) or not np.isfinite(a).all():
        raise ValueError('finite tall bounded matrix required')
    s, u, v, work, iwork, info = lapack.dgejsv(a, joba=3, jobu=0, jobv=1,
        jobr=0, jobt=0, jobp=0, overwrite_a=0)
    if info != 0 or iwork[2] != 0:
        raise ValueError('Jacobi SVD failure or accuracy warning')
    if work[1] <= 0. or not np.isfinite(work[:2]).all():
        raise ValueError('invalid Jacobi scaling')
    s = s*(work[0]/work[1])
    if not np.isfinite(s).all() or np.any(s < 0.) or np.any(np.diff(s) > 0.):
        raise ValueError('invalid ordered singular values')
    if np.linalg.norm((u*s)@v.T-a) > 1e-11*max(1., np.linalg.norm(a)):
        raise ValueError('Jacobi reconstruction failed')
    if np.linalg.norm(v.T@v-np.eye(len(s))) > 1e-11:
        raise ValueError('Jacobi right-vector orthogonality failed')
    return u, s, v.T


def beam_comparison(slenderness):
    from docs.reference_cases.ge_beam3_slender_spectrum_probe import factors
    e, g = factors(slenderness)
    free = tuple(range(6, 24)); a = (9, 10, 11, 15, 16, 17)
    physical = tuple(i for i in free if i not in a)
    q, r = np.linalg.qr(e[:, a], mode='reduced')
    mapping = np.zeros((24, len(physical))); mapping[list(physical)] = np.eye(len(physical))
    mapping[list(a)] = -np.linalg.solve(r, q.T@e[:, physical])
    strain, speed = e@mapping, g@mapping
    _, mass_r = np.linalg.qr(speed, mode='reduced')
    normalized = np.linalg.solve(mass_r.T, strain.T).T
    _, s, _ = jacobi_svd(normalized)
    return s[::-1]**2
