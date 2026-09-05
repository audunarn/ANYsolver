"""Small linear tip-compliance development checks, not a qualification runner."""

import numpy as np

from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import skew
from docs.reference_cases.ge_beam3_curved_p5_flexibility_probe import reference_flexibility


def parabolic_references(height, count):
    if (not isinstance(count, int) or isinstance(count, bool) or count not in (1, 2, 4, 8)
            or not np.isfinite(height) or not 0 <= height <= .75):
        raise ValueError("bounded parabolic reference family required")
    stations = np.linspace(-1., 1., 2*count+1)
    nodes = np.array([[t, height*(1-t*t), 0.] for t in stations])
    frames = []
    for t in stations:
        axis = np.array([1., -2*height*t, 0.])
        axis /= np.linalg.norm(axis)
        second = np.array([0., 0., 1.])
        frames.append(np.column_stack((axis, second, np.cross(axis, second))))
    return tuple(CurvedBeam3ReferenceGeometry(nodes[i:i+3], np.array(frames[i:i+3]))
                 for i in range(0, 2*count, 2))


def discrete_tip_compliance(references, section):
    """Statically determinate tip compliance from the discrete half-cell law.

    Known tip loads fix every cell force/moment by equilibrium. Summing
    complementary work avoids a large global matrix; this is the same
    discrete law, not fitting to the continuum reference.
    """
    references = tuple(references)
    if len(references) not in (1, 2, 4, 8):
        raise ValueError("one, two, four or eight macro elements required")
    for previous, current in zip(references, references[1:]):
        if (not np.array_equal(previous.coordinates[-1], current.coordinates[0])
                or not np.array_equal(previous.nodal_triads[-1], current.nodal_triads[0])):
            raise ValueError("identical shared reference node and frame required")
    result = np.zeros((6, 6))
    tip = references[-1].coordinates[-1]
    for ref in references:
        factors = reference_flexibility(ref, section)
        for cell, law in enumerate(factors.cells):
            left = ref.coordinates[cell]
            mapping = np.zeros((6, 6))
            mapping[:3, :3] = law.basis.T
            mapping[3:, :3] = law.basis.T @ skew(tip-left)
            mapping[3:, 3:] = law.basis.T
            factor = law.scale[:, None]*law.cholesky
            result += (factor.T @ mapping).T @ (factor.T @ mapping)
    if not np.isfinite(result).all():
        raise ValueError("finite tip compliance required")
    return result
