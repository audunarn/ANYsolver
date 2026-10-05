"""Flat-reference six-channel shell pose work for a bounded material rail.

The rows are integrated P0 shell *pose* variations, not the complete relative
beam/shell constraint or a selected production multiplier space.
"""

import numpy as np

from scripts.b3_e4_f03_l1_physical_rail import transverse_shape_integrals


def flat_rail_p0_shell_pose_action(xs: np.ndarray, ys: np.ndarray,
                                   bounds: tuple[float, float],
                                   thickness: float) -> np.ndarray:
    """Map shell nodal variations to integrated [translation, spatial spin].

    Nodes are y-major, then x-major, with six coordinates per node. The
    result has one six-row block per longitudinal Q4 segment. It is exact
    for a straight flat virgin reference, constant P0 density on each
    segment, and the positive-width rail's piecewise-linear trace.
    """
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if (x.ndim != 1 or y.ndim != 1 or not 2 <= len(x) <= 9 or
            len(y) < 2 or not np.isfinite(x).all() or
            not np.all(np.diff(x) > 0.) or
            not np.isfinite(thickness) or thickness <= 0.):
        raise ValueError("bounded ordered flat rail required")
    weights = transverse_shape_integrals(y, bounds)
    action = np.zeros((len(x)-1, 6, 6*len(x)*len(y)))
    for i, h in enumerate(np.diff(x)):
        for j, weight in enumerate(weights):
            for node, sign in ((i, -1.), (i+1, 1.)):
                base = 6*(j*len(x)+node)
                average = .5*h*weight
                action[i, 0, base] += average
                action[i, 0, base+4] += .5*thickness*average
                action[i, 1, base+1] += average
                action[i, 1, base+3] -= .5*thickness*average
                action[i, 2, base+2] += average
                action[i, 3, base+3] += average
                action[i, 4, base+4] += average
                action[i, 5, base+1] += sign*weight
                action[i, 5, base+3] -= sign*.5*thickness*weight
    action.setflags(write=False)
    return action
