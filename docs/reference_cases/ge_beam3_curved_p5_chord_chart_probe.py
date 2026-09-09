"""Research-only local finite solve with retained chord-adapted coordinates.

This is not a production element, external tangent, independent oracle or
qualified state/restart representation. The prior finite probe is unchanged.
"""

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_mixed_ad import (
    Jet2, _exp_coefficients, constant_matrix, matmul, matvec, transpose,
    so3_exp, so3_log,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES, skew
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import (
    CurvedFiniteProbe, LocalStationarityError, _quadratic, _readonly,
)


@dataclass(frozen=True)
class LocalChartResponse:
    potential: float
    parameters: np.ndarray
    rotations: np.ndarray
    physical_residual_norm: float
    iterations: int


class ChordChartLocalProbe:
    """Six local unknowns: two transverse tilts and one axial spin per half.

    U = D Exp([0,beta_y,beta_z]) Exp([phi,0,0]) B^T, where B and D
    align their first axes with reference and current chords. Keep beta/phi
    as authoritative diagnostic coordinates; rebuilding them from rounded U
    discards precisely the small information this experiment preserves.
    """

    def __init__(self, reference, section, positions, vertex_frames, *, order=24, line_force=None):
        self.base = CurvedFiniteProbe(reference, section, order=order, line_force=line_force)
        x, q, _, _, _ = self.base._configuration(positions, vertex_frames, None)
        self.positions, self.vertices = _readonly(x), _readonly(q)
        initial = self.base._initial_rotations(q)
        self.charts = []
        for cell, (left, right) in enumerate(HALVES):
            c = self.base.coordinates[right]-self.base.coordinates[left]
            d = x[right]-x[left]
            lc, ld = float(np.linalg.norm(c)), float(np.linalg.norm(d))
            if not np.isfinite(ld) or ld <= 0:
                raise ValueError("nonzero finite current chord required")
            axis = c/lc
            candidates = [self.base.frames[left][:, i]-axis*(axis @ self.base.frames[left][:, i])
                          for i in (1, 2)]
            second = max(candidates, key=np.linalg.norm)
            second = second/np.linalg.norm(second)
            b = np.column_stack((axis, second, np.cross(axis, second)))
            start = initial[cell] @ b
            target = d/ld
            cosine = float(start[:, 0] @ target)
            if cosine <= np.cos(.9*np.pi):
                raise ValueError("chord chart requires refinement or cutback")
            cross = skew(np.cross(start[:, 0], target))
            transport = np.eye(3)+cross+cross@cross/(1+cosine)
            current = transport @ start
            # Compute the length difference as a difference of squared norms,
            # avoiding subtraction of two separately rounded square roots.
            delta = float(np.dot(d-c, d+c)/(ld+lc))
            self.charts.append((_readonly(b), _readonly(current), lc, ld, delta,
                                _readonly(b.T @ self.base.metric[cell].force @ b),
                                _readonly(self.base.metric[cell].coupling @ b)))

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
            zero = Jet2.constant(0., 6)
            tilt_square = by*by+bz*bz
            if tilt_square.value >= (.9*np.pi)**2:
                raise ValueError("transverse tilt requires refinement or cutback")
            sinc, cosc = _exp_coefficients(tilt_square)
            tilt = so3_exp([zero, by, bz])
            spin = so3_exp([phi, zero, zero])
            u = matmul(matmul(matmul(constant_matrix(current, 6), tilt), spin),
                       constant_matrix(b.T, 6))
            # Exact chord identity evaluated without U^T d - c cancellation.
            z_tilt = [delta-ld*cosc*tilt_square, -ld*sinc*bz, ld*sinc*by]
            z = matvec(transpose(spin), z_tilt)
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

    @staticmethod
    def physical_norm(jet, maps):
        torques = [np.linalg.solve(maps[c].T, jet.gradient[3*c:3*c+3]) for c in (0, 1)]
        return float(np.max(np.abs(torques)))

    def solve(self, *, initial=None, max_iterations=25):
        if (not isinstance(max_iterations, int) or isinstance(max_iterations, bool)
                or not 0 <= max_iterations <= 25):
            raise ValueError("local iteration limit must be an integer from 0 to 25")
        parameters = np.zeros(6) if initial is None else np.array(initial, dtype=float, copy=True)
        for iteration in range(max_iterations+1):
            jet, rotations, maps = self.jet(parameters)
            norm = self.physical_norm(jet, maps)
            if norm <= 1e-11:
                try:
                    np.linalg.cholesky(jet.hessian)
                except np.linalg.LinAlgError as exc:
                    raise LocalStationarityError("stationary chart Hessian not positive definite") from exc
                return LocalChartResponse(jet.value, _readonly(parameters), _readonly(rotations), norm, iteration)
            if iteration == max_iterations:
                break
            # Diagonal congruence scales the solve; it does not modify stiffness.
            scale = np.sqrt(np.abs(np.diag(jet.hessian)))
            if np.any(scale == 0):
                raise LocalStationarityError("zero local chart scaling")
            try:
                step = np.linalg.solve(jet.hessian/scale[:, None]/scale[None, :],
                                       -jet.gradient/scale)/scale
            except np.linalg.LinAlgError as exc:
                raise LocalStationarityError("singular local chart Hessian") from exc
            accepted = False
            for backtrack in range(12):
                trial_parameters = parameters+(.5**backtrack)*step
                try:
                    trial, _, trial_maps = self.jet(trial_parameters)
                    trial_norm = self.physical_norm(trial, trial_maps)
                except ValueError:
                    continue
                if trial_norm < norm:
                    parameters = trial_parameters
                    accepted = True
                    break
            if not accepted:
                raise LocalStationarityError("chart line search failed after 12 trials")
        raise LocalStationarityError("chart iteration budget exhausted")
