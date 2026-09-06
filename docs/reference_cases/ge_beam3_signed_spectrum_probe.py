"""Research signed-spectrum reduction; not a qualified eigensolver.

The supplied split is K=F.T F+G. Keep G separate throughout trace elimination
and mass whitening. Only the positive material factor is passed to Jacobi
SVD; the signed correction is neither clipped nor square-rooted.

Shifted congruence/inertia bracketing below is a binary64 diagnostic, NOT a
certified interval or an assertion of forward accuracy for arbitrary inputs.
"""

import numpy as np
from scipy import linalg
from anysolver._relative_reference_svd import relative_reference_svd


def reduce_signed_split(factor, geometric, mass, free_dofs, algebraic_dofs):
    f, g, m = (np.array(x, dtype=float, copy=True) for x in (factor, geometric, mass))
    if (f.ndim != 2 or not 1 <= f.shape[1] <= 256 or f.shape[0] > 8192
            or g.shape != (f.shape[1],)*2 or m.shape != g.shape
            or not all(np.isfinite(x).all() for x in (f, g, m))):
        raise ValueError('bounded finite signed split required')
    for a in (g, m):
        if np.linalg.norm(a-a.T) > 1e-11*max(1., np.linalg.norm(a)):
            raise ValueError('symmetric split required')
    for slots in (free_dofs, algebraic_dofs):
        if (type(slots) is not tuple or len(set(slots)) != len(slots)
                or any(type(i) is not int or not 0 <= i < f.shape[1] for i in slots)):
            raise ValueError('exact distinct in-range DOFs required')
    if not set(algebraic_dofs) <= set(free_dofs):
        raise ValueError('algebraic DOFs must be free')
    if np.any(m[:, algebraic_dofs] != 0.) or np.any(m[algebraic_dofs, :] != 0.):
        raise ValueError('algebraic inertia must be exactly zero')
    physical = tuple(i for i in free_dofs if i not in algebraic_dofs)
    if not physical: raise ValueError('physical coordinates required')
    mapping = np.zeros((f.shape[1], len(physical)))
    mapping[list(physical)] = np.eye(len(physical))
    strain = f[:, physical]
    if algebraic_dofs:
        count = len(algebraic_dofs)
        q, r = linalg.qr(f[:, algebraic_dofs], mode='full')
        r = r[:count]
        if r.shape != (count, count): raise ValueError('insufficient trace rows')
        singular = linalg.svdvals(r)
        if singular[-1] <= np.finfo(float).eps*count*singular[0]:
            raise ValueError('unresolved material trace rank')
        mapping[list(algebraic_dofs)] = -linalg.solve_triangular(r, q[:, :count].T@strain)
        # Use orthogonal rows, not a subtraction of large normal equations.
        strain = q[:, count:].T@strain
        trace = r.T@r+g[np.ix_(algebraic_dofs, algebraic_dofs)]
        cholesky = linalg.cho_factor(trace)
        cross = g[list(algebraic_dofs)]@mapping
        correction = linalg.cho_solve(cholesky, cross)
        reduced_g = mapping.T@g@mapping-cross.T@correction
        mapping[list(algebraic_dofs)] -= correction
    else:
        reduced_g = mapping.T@g@mapping
    mass_r = linalg.cholesky(m[np.ix_(physical, physical)], lower=False)
    normalized = linalg.solve_triangular(mass_r.T, strain.T, lower=True).T
    left_g = linalg.solve_triangular(mass_r.T, reduced_g, lower=True)
    normalized_g = linalg.solve_triangular(mass_r.T, left_g.T, lower=True).T
    _, singular, right = relative_reference_svd(normalized)
    with np.errstate(over='raise', invalid='raise', under='raise'):
        diagonal = singular**2
    signed = right@normalized_g@right.T
    vectors = mapping@linalg.solve_triangular(mass_r, right.T)
    return diagonal, signed, vectors


def shifted_inertia(diagonal, correction, shift):
    """Return negative count only when the congruently scaled signs resolve."""
    d, g = np.asarray(diagonal), np.asarray(correction)
    if (d.ndim != 1 or not 1 <= len(d) <= 256 or g.shape != (len(d), len(d))
            or not np.isfinite(d).all() or not np.isfinite(g).all()
            or not np.isfinite(shift) or np.any(d < 0.)):
        raise ValueError('finite positive-factor diagonal and signed correction required')
    if np.linalg.norm(g-g.T) > 1e-11*max(1., np.linalg.norm(g)):
        raise ValueError('symmetric signed correction required')
    # Form the shift before summing the stress correction. No global stiffness
    # scale enters the sign threshold; congruence preserves inertia, not roots.
    delta = d-shift
    # Diagonal-based congruence matters: using the largest off-diagonal entry
    # in each row can bury a small Schur root even after a valid congruence.
    # Off-diagonal row scale is used only for an exactly absent diagonal.
    size = np.maximum(np.abs(delta), np.abs(np.diag(g)))
    size = np.where(size == 0., np.max(np.abs(g), axis=1), size)
    scale = np.sqrt(size)
    if np.any(scale == 0.): raise ValueError('unresolved shifted sign')
    scaled = (g/scale[:, None])/scale[None, :]
    scaled[np.diag_indices(len(d))] += (delta/scale)/scale
    values = linalg.eigvalsh(scaled)
    margin = 64*np.finfo(float).eps*len(d)*max(1., np.max(np.abs(values)))
    if np.min(np.abs(values)) <= margin: raise ValueError('unresolved shifted sign')
    return int(np.count_nonzero(values < 0.))


def bracket_lowest(diagonal, correction, bounds, count, *, width=1e-10):
    """Bounded same-author numerical search; caller freezes the search bounds."""
    if (type(count) is not int or not 1 <= count <= len(diagonal)
            or len(bounds) != 2 or not np.isfinite(bounds).all()
            or not bounds[0] < bounds[1] or not np.isfinite(width) or width <= 0.):
        raise ValueError('finite ordered search bounds and positive width required')
    low_count = shifted_inertia(diagonal, correction, bounds[0])
    high_count = shifted_inertia(diagonal, correction, bounds[1])
    if low_count != 0 or high_count < count: raise ValueError('bounds do not enclose lowest requested roots')
    result = []
    for index in range(count):
        lo, hi = bounds
        for _ in range(96):
            if hi-lo <= width: break
            middle = lo+(hi-lo)/2
            try:
                negative = shifted_inertia(diagonal, correction, middle)
            except ValueError as exc:
                if str(exc) != 'unresolved shifted sign': raise
                left, right = max(lo, middle-width/4), min(hi, middle+width/4)
                a = shifted_inertia(diagonal, correction, left)
                b = shifted_inertia(diagonal, correction, right)
                if a <= index < b:
                    lo, hi = left, right
                    break
                raise ValueError('shifted signs unresolved at requested root width') from exc
            if negative <= index: lo = middle
            else: hi = middle
        else: raise ValueError('signed search iteration limit')
        if hi-lo > width: raise ValueError('signed search width not achieved')
        result.append((lo, hi))
    return np.array(result)
