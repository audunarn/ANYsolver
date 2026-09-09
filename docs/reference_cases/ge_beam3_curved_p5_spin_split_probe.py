"""Research successor: axial spin about the current chord precedes tilt.

Keep the prior chord-coordinate experiment unchanged. This parameterization
makes force strain independent of spin exactly, including anisotropic F.
It is not an independent implementation or a production element.
"""

import numpy as np

from anysolver._ge_beam3_mixed_ad import (
    Jet2, _exp_coefficients, constant_matrix, matmul, matvec, transpose,
    so3_exp, so3_log,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES
from docs.reference_cases.ge_beam3_curved_p5_chord_chart_probe import ChordChartLocalProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import LocalStationarityError, _quadratic


class CurrentChordSpinProbe(ChordChartLocalProbe):
    """U = D Exp(phi e1) Exp(beta_y e2 + beta_z e3) B^T.

    Because D^T d=ld e1 and spin preserves e1, z does not depend on phi.
    The scalar potential and all physical section coupling remain unchanged.
    Only six local diagnostic coordinates, not external/state APIs, exist.
    """

    def jet(self, parameters):
        parameters = np.asarray(parameters, dtype=float)
        if parameters.shape != (6,) or not np.isfinite(parameters).all():
            raise ValueError("finite six-component chart parameters required")
        variables = [Jet2.variable(value, i, 6) for i, value in enumerate(parameters)]
        total = Jet2.constant(0., 6)
        rotations, maps = [], []
        for cell, (left, right) in enumerate(HALVES):
            b, current, lc, ld, delta, force, coupling = self.charts[cell]
            by, bz, phi = variables[3*cell:3*cell+3]
            # A local chart must not jump through multiple 2*pi periods and
            # silently appear admissible at its endpoint. The endpoint logs
            # retain their separate, unchanged 0.9*pi relative-rotation guard.
            if abs(phi.value) >= np.pi:
                raise ValueError("axial spin left its principal chart; cutback required")
            zero = Jet2.constant(0., 6)
            tilt_square = by*by+bz*bz
            if tilt_square.value >= (.9*np.pi)**2:
                raise ValueError("transverse tilt requires refinement or cutback")
            sinc, cosc = _exp_coefficients(tilt_square)
            tilt = so3_exp([zero, by, bz])
            spin = so3_exp([phi, zero, zero])
            u = matmul(matmul(matmul(constant_matrix(current, 6), spin), tilt),
                       constant_matrix(b.T, 6))
            z = [delta-ld*cosc*tilt_square, -ld*sinc*bz, ld*sinc*by]
            ell = []
            for node, sign in ((left, -1), (right, 1)):
                frame = matmul(u, constant_matrix(self.base.frames[node], 6))
                ell.extend(sign*item for item in so3_log(matmul(
                    transpose(frame), constant_matrix(self.vertices[node], 6))))
            coupled = matvec(constant_matrix(coupling, 6), z)
            e = [a+b for a, b in zip(coupled, ell)]
            total += (_quadratic(z, force)+_quadratic(e, self.base.h_inverse[cell]))/2
            for i in range(3):
                for j in range(3):
                    total -= self.base.lift_work[cell, i, j]*(u[i][j]-(1. if i == j else 0.))
            matrix = np.array([[item.value for item in row] for row in u])
            spatial_map = np.empty((3, 3))
            for column in range(3):
                derivative = np.array([[item.gradient[3*cell+column] for item in row] for row in u])
                angular = derivative @ matrix.T
                spatial_map[:, column] = (angular[2, 1]-angular[1, 2],
                                          angular[0, 2]-angular[2, 0],
                                          angular[1, 0]-angular[0, 1])
            maps.append(spatial_map/2)
            rotations.append(matrix)
        total -= float(np.sum(self.base.nodal_line_load*(self.positions-self.base.coordinates)))
        if not (np.isfinite(total.value) and np.isfinite(total.gradient).all()
                and np.isfinite(total.hessian).all()):
            raise LocalStationarityError("nonfinite chart functional")
        return total, np.array(rotations), np.array(maps)
