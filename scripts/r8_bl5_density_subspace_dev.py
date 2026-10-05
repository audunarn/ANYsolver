"""Fixed saved-fixture density coarsening and flat BL5 reference work rows.

Development controls only: no mechanics/profile selection or qualification.
The caller must bind the straight flat identity frames and actual local slots.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse


def density_subspace_embedding(fine_supports=4, coarse_supports=2):
    """Owned E(20,40), coarse constraints=E@fine constraints.

    Channel-major rows: 2*(channel*supports+support)+[constant, affine].
    The exact coarse density on 16 halfcells/span8 embeds in span4 densities.
    Coarse multipliers exert fine dual coefficients E.T@lambda_coarse.
    """
    if (type(fine_supports) is not int or type(coarse_supports) is not int or
            (fine_supports, coarse_supports) != (4, 2)):
        raise ValueError('plain integer fixed support transition4->2 required')
    data, indices, pointer = [], [], [0]
    for channel in range(5):
        for support in range(2):
            left = 2*(channel*4+2*support)
            right = left+2
            indices.extend((left, right))
            data.extend((1., 1.))
            pointer.append(len(data))
            indices.extend((left, left+1, right, right+1))
            data.extend((-.5, .5, .5, .5))
            pointer.append(len(data))
    return sparse.csr_matrix((np.array(data, dtype=np.float64),
        np.array(indices, dtype=np.int64), np.array(pointer, dtype=np.int64)), shape=(20, 40))


def _array(value, shape, name):
    original = np.asarray(value)
    if original.shape != shape or original.dtype.kind not in 'iuf':
        raise ValueError('finite real '+name+' required')
    owned = np.array(original, dtype=np.float64, copy=True)
    if owned.shape != shape or not np.isfinite(owned).all():
        raise ValueError('finite '+name+' of shape'+str(shape)+' required')
    return owned


def _scalar(value, name):
    scalar = np.asarray(value)
    if scalar.shape != () or scalar.dtype.kind not in 'iuf' or not np.isfinite(scalar):
        raise ValueError('finite real scalar '+name+' required')
    return float(scalar)


def _skew(vector):
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def flat_reference_jacobian(shell_alpha, t, reference_director,
                            director_basis, reference_arm, port_lift, w):
    """Owned J(5,21) for the frozen straight flat identity-frame reference.

    Slots: two shell [u3,rotation3] blocks, two beam translation3 blocks,
    then retained physical beam-cell rotation3. No nodal/retained identification.
    This is the reference derivative of actual rotating director/beam-frame gaps,
    not an admission of general poses, an SPD metric or qualification.
    """
    alpha, weight, thickness = (_scalar(shell_alpha, 'shell_alpha'),
        _scalar(w, 'beam weight'), _scalar(t, 'thickness'))
    if not 0. <= alpha <= 1. or not 0. <= weight <= 1. or thickness <= 0.:
        raise ValueError('unit-interval interpolation and positive thickness required')
    d = _array(reference_director, (3,), 'reference director')
    basis = _array(director_basis, (2, 3), 'director basis')
    arm = _array(reference_arm, (3,), 'reference arm')
    lift = _array(port_lift, (3,), 'port lift')
    if not np.array_equal(d, (0., 0., 1.)) or not np.array_equal(
            basis, ((1., 0., 0.), (0., 1., 0.))):
        raise ValueError('frozen flat ez director/ex-ey basis required')
    j = np.zeros((5, 21), dtype=np.float64)
    skew_d = _skew(d)
    for start, shape in ((0, 1.-alpha), (6, alpha)):
        j[:3, start:start+3] = shape*np.eye(3)
        j[:3, start+3:start+6] = -shape*.5*thickness*skew_d
        j[3:, start+3:start+6] = -shape*(basis@skew_d)
    j[:3, 12:15] = -(1.-weight)*np.eye(3)
    j[:3, 15:18] = -weight*np.eye(3)
    j[:3, 18:21] = _skew(lift+arm)
    j[3:, 18:21] = basis@skew_d
    if not np.isfinite(j).all():
        raise ValueError('finite flat reference Jacobian required')
    return j
