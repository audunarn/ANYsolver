"""Author development probe for finite curved P5 mechanics.

Analytic second derivatives of the partially condensed scalar functional,
six-variable local Newton solve, Schur tangent, and elastic station recovery.
No factory, solver, state/restart, independent-review, or qualification API.
The accepted scalar Jet2/SO(3) kernel is shared and is NOT an independent oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from anysolver._ge_beam3_mixed_ad import (
    Jet2, constant_matrix, dot, matmul, matvec, transpose, so3_exp, so3_log,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import (
    HALVES, cell_coordinates, log_rotation, metrics, rotation, validate_section,
)


class LocalStationarityError(RuntimeError):
    """The finite diagnostic did not find an admissible stable local solution."""


def _readonly(value):
    result = np.array(value, dtype=float, copy=True)
    result.setflags(write=False)
    return result


def _array(value, shape, label):
    result = np.array(value, dtype=float, copy=True)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"{label} must be finite with shape {shape}")
    return result


def _frames(value, count, label):
    frames = _array(value, (count, 3, 3), label)
    for frame in frames:
        if np.linalg.norm(frame.T @ frame-np.eye(3)) > 1e-11 or abs(
            np.linalg.det(frame)-1.0
        ) > 1e-11:
            raise ValueError(f"{label} must contain proper rotations")
    return frames


def _quadratic(vector, matrix):
    return dot(vector, matvec(constant_matrix(matrix, vector[0].gradient.size), vector))


@dataclass(frozen=True)
class FiniteResponse:
    potential: float
    residual: np.ndarray
    tangent: np.ndarray
    local_rotations: np.ndarray
    moments: np.ndarray
    full_hessian: np.ndarray
    local_iterations: int
    local_residual_norm: float


class CurvedFiniteProbe:
    """Pure elastic evaluations with explicit base configuration and chart.

    The returned derivatives are in one fixed additive increment chart:
    x=x_base+du, Q=Exp(dtheta) Q_base. At zero increment they are the spatial
    residual and symmetric energy Hessian. Comparing derivatives at nonzero
    increments requires keeping the same base chart.
    """

    def __init__(self, reference, section, *, order=24, line_force=None):
        self.reference = reference
        self.section = _readonly(validate_section(section))
        self.coordinates = _readonly(reference.coordinates)
        self.frames = _readonly(reference.nodal_triads)
        if not isinstance(order, int) or isinstance(order, bool) or not 2 <= order <= 64:
            raise ValueError("diagnostic quadrature order must be an integer from 2 to 64")
        self.order = order
        self.metric = tuple(metrics(reference, self.section, cell, order) for cell in (0, 1))
        self.h_inverse = tuple(_readonly(np.linalg.solve(m.compliance, np.eye(6)))
                               for m in self.metric)
        for metric in self.metric:
            for value in (metric.force, metric.compliance, metric.coupling):
                value.setflags(write=False)
        self.line_force = _readonly(np.zeros(3) if line_force is None else
                                    _array(line_force, (3,), "line force"))
        loads = np.zeros((3, 3))
        lift_work = np.zeros((2, 3, 3))
        stations, weights = np.polynomial.legendre.leggauss(order)
        for cell, (left, right) in enumerate(HALVES):
            for station, weight in zip(stations, weights):
                t = (station+1)/2
                xi = cell-1+t
                measure = weight*reference.jacobian(xi)/2
                offset = reference.position(xi)-((1-t)*self.coordinates[left]+t*self.coordinates[right])
                loads[left] += (1-t)*measure*self.line_force
                loads[right] += t*measure*self.line_force
                lift_work[cell] += measure*np.outer(self.line_force, offset)
        self.nodal_line_load = _readonly(loads)
        self.lift_work = _readonly(lift_work)

    def _configuration(self, positions, vertex_frames, increment):
        positions = _array(positions, (3, 3), "positions")
        vertex_frames = _frames(vertex_frames, 3, "vertex frames")
        increment = np.zeros(18) if increment is None else _array(increment, (18,), "increment")
        current_positions = positions+increment.reshape(3, 6)[:, :3]
        current_frames = np.array([rotation(increment[6*n+3:6*n+6]) @ vertex_frames[n]
                                   for n in range(3)])
        return positions, vertex_frames, increment, current_positions, current_frames

    def _jet(self, positions, vertex_frames, local_rotations, *, external, increment=None):
        external_size = 18 if external else 0
        size = external_size+6
        origin = np.zeros(18) if increment is None else increment
        variables = [Jet2.variable(origin[i] if i < external_size else 0.0, i, size)
                     for i in range(size)]
        made_positions, made_frames = [], []
        for node in range(3):
            made_positions.append([Jet2.constant(positions[node, axis], size)+(
                variables[node*6+axis] if external else 0.0) for axis in range(3)])
            base = constant_matrix(vertex_frames[node], size)
            made_frames.append(matmul(so3_exp(variables[node*6+3:node*6+6]), base)
                               if external else base)
        total = Jet2.constant(0.0, size)
        for cell, (left, right) in enumerate(HALVES):
            start = external_size+3*cell
            u = matmul(so3_exp(variables[start:start+3]), constant_matrix(local_rotations[cell], size))
            current_chord = [made_positions[right][i]-made_positions[left][i] for i in range(3)]
            local_chord = matvec(transpose(u), current_chord)
            z = [local_chord[i]-(self.coordinates[right, i]-self.coordinates[left, i]) for i in range(3)]
            ell = []
            for node, sign in ((left, -1), (right, 1)):
                cell_frame = matmul(u, constant_matrix(self.frames[node], size))
                logarithm = so3_log(matmul(transpose(cell_frame), made_frames[node]))
                ell.extend(sign*item for item in logarithm)
            coupling = matvec(constant_matrix(self.metric[cell].coupling, size), z)
            e = [a+b for a, b in zip(coupling, ell)]
            total += (_quadratic(z, self.metric[cell].force)+_quadratic(e, self.h_inverse[cell]))/2
            # Spatial dead load work from the lifted position, including the
            # internal rotation terms. Reference constants set W=0 at r=r0.
            for i in range(3):
                for j in range(3):
                    total -= self.lift_work[cell, i, j]*(u[i][j]-(1.0 if i == j else 0.0))
        for node in range(3):
            for i in range(3):
                total -= self.nodal_line_load[node, i]*(made_positions[node][i]-self.coordinates[node, i])
        if not (np.isfinite(total.value) and np.isfinite(total.gradient).all()
                and np.isfinite(total.hessian).all()):
            raise LocalStationarityError("nonfinite functional or derivative")
        return total

    def _initial_rotations(self, vertex_frames):
        relatives = vertex_frames @ self.frames.transpose(0, 2, 1)
        result = []
        for left, right in HALVES:
            delta = log_rotation(relatives[left].T @ relatives[right])
            result.append(relatives[left] @ rotation(delta/2))
        return np.array(result)

    def _solve(self, positions, vertex_frames, *, initial=None, max_iterations=25,
               tolerance=1e-11):
        if (not isinstance(max_iterations, int) or isinstance(max_iterations, bool)
                or not 0 <= max_iterations <= 25):
            raise ValueError("local iteration limit must be an integer from 0 to 25")
        # This guard is checked even when an explicit initial state is supplied.
        default = self._initial_rotations(vertex_frames)
        local = default if initial is None else _frames(initial, 2, "initial local rotations")
        for iteration in range(max_iterations+1):
            jet = self._jet(positions, vertex_frames, local, external=False)
            norm = float(np.linalg.norm(jet.gradient, ord=np.inf))
            if norm <= tolerance:
                try:
                    np.linalg.cholesky(jet.hessian)
                except np.linalg.LinAlgError as exc:
                    raise LocalStationarityError("stationary local Hessian is not positive definite") from exc
                return local, iteration, norm
            if iteration == max_iterations:
                break
            try:
                step = np.linalg.solve(jet.hessian, -jet.gradient).reshape(2, 3)
            except np.linalg.LinAlgError as exc:
                raise LocalStationarityError("singular local Hessian") from exc
            if not np.isfinite(step).all():
                raise LocalStationarityError("nonfinite local Newton step")
            accepted = False
            for backtrack in range(12):
                scale = .5**backtrack
                made = np.array([rotation(scale*step[c]) @ local[c] for c in (0, 1)])
                try:
                    trial = self._jet(positions, vertex_frames, made, external=False)
                except ValueError:
                    continue
                if np.linalg.norm(trial.gradient, ord=np.inf) < norm:
                    local = made
                    accepted = True
                    break
            if not accepted:
                raise LocalStationarityError("local line search failed after 12 trials")
        raise LocalStationarityError("local iteration budget exhausted")

    def evaluate(self, positions, vertex_frames, *, increment=None, initial=None,
                 max_iterations=25):
        positions, vertex_frames, increment, current_x, current_q = self._configuration(
            positions, vertex_frames, increment)
        local, iterations, norm = self._solve(current_x, current_q, initial=initial,
                                               max_iterations=max_iterations)
        jet = self._jet(positions, vertex_frames, local, external=True, increment=increment)
        if np.linalg.norm(jet.gradient[18:], ord=np.inf) > 2e-11:
            raise LocalStationarityError("full-chart local stationarity disagrees with local solve")
        hessian = jet.hessian
        tangent = hessian[:18, :18]-hessian[:18, 18:] @ np.linalg.solve(
            hessian[18:, 18:], hessian[18:, :18])
        moments = []
        for cell in (0, 1):
            z, ell = cell_coordinates(self.reference, current_x, current_q, local[cell], cell)
            moments.append((self.h_inverse[cell] @ (self.metric[cell].coupling @ z+ell)).reshape(2, 3))
        return FiniteResponse(float(jet.value), np.array(jet.gradient[:18], copy=True),
                              tangent, np.array(local, copy=True), np.array(moments),
                              np.array(hessian, copy=True), iterations, norm)

    def recover(self, positions, vertex_frames, response, *, stations=(.25, .75)):
        """Physical elastic section fields, separately from jump coordinates.

        Caller supplies the current configuration (not the base plus a hidden
        increment); no committed state or historical section state is implied.
        """
        x = _array(positions, (3, 3), "positions")
        q = _frames(vertex_frames, 3, "vertex frames")
        local = _frames(response.local_rotations, 2, "local rotations")
        residual = self._jet(x, q, local, external=False).gradient
        if np.linalg.norm(residual, ord=np.inf) > 2e-11:
            raise LocalStationarityError("recovery configuration does not match stationary response")
        rows = []
        for cell in (0, 1):
            z, ell = cell_coordinates(self.reference, x, q, local[cell], cell)
            moments = (self.h_inverse[cell] @ (self.metric[cell].coupling @ z+ell)).reshape(2, 3)
            if not np.allclose(moments, response.moments[cell], rtol=0., atol=1e-11):
                raise LocalStationarityError("response moments do not match recovered configuration")
            for fraction in stations:
                if not np.isfinite(fraction) or not 0 <= fraction <= 1:
                    raise ValueError("station fraction must be finite in [0,1]")
                xi = cell-1+fraction
                frame = self.reference.frame(xi)
                gamma = frame.T @ z / self.reference.jacobian(xi)
                m = (1-fraction)*moments[0]+fraction*moments[1]
                kappa = np.linalg.solve(self.section[3:, 3:], m-self.section[:3, 3:].T @ gamma)
                strain = np.concatenate((gamma, kappa))
                resultant = self.section @ strain
                physical_frame = local[cell] @ frame
                rows.append({"cell": cell, "xi": float(xi), "strain": strain,
                             "resultant": resultant, "current_frame": physical_frame,
                             "spatial_force": physical_frame @ resultant[:3],
                             "spatial_moment": physical_frame @ resultant[3:]})
        return rows
