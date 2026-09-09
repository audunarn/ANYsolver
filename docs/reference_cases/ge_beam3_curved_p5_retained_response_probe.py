"""Research finite residual/tangent and recovery from retained local coordinates.

No production registration, nonlinear history, serialization/restart authority
or independent qualification. All derivatives use the shared Jet2 kernel.
"""

from dataclasses import dataclass
import hashlib

import numpy as np

from anysolver._ge_beam3_mixed_ad import (
    Jet2, _exp_coefficients, constant_matrix, dot, matmul, matvec,
    skew as jet_skew, so3_exp, so3_log, sqrt, transpose,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES, canonical_bytes
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import (
    LocalStationarityError, _array, _quadratic, _readonly,
)
from docs.reference_cases.ge_beam3_curved_p5_spin_split_probe import CurrentChordSpinProbe


@dataclass(frozen=True)
class RetainedResponse:
    potential: float
    residual: np.ndarray
    tangent: np.ndarray
    parameters: np.ndarray
    rotations: np.ndarray
    increment: np.ndarray
    physical_residual_norm: float
    local_iterations: int
    state_sha256: str


class RetainedFiniteResponseProbe(CurrentChordSpinProbe):
    """Fixed base configuration; increments use one additive external chart.

    Current x=x_base+du and Q=Exp(dtheta) Q_base. Local charts may be rebuilt
    at each trial state, but external derivatives keep the caller's base chart.
    The condensed Hessian includes derivatives of moving chord transport.
    """

    def _functional(self, parameters, *, external=False, origin=None, base_frames=None):
        parameters = _array(parameters, (6,), "retained parameters")
        offset = 18 if external else 0
        size = offset+6
        origin = np.zeros(18) if origin is None else _array(origin, (18,), "increment")
        variables = [Jet2.variable(origin[i] if i < offset else parameters[i-offset], i, size)
                     for i in range(size)]
        zero = Jet2.constant(0., size)
        increments = [variables[i]-origin[i] if external else zero for i in range(18)]
        vertex_frames = []
        for node in range(3):
            if external:
                vertex_frames.append(matmul(so3_exp(variables[node*6+3:node*6+6]),
                                            constant_matrix(base_frames[node], size)))
            else:
                vertex_frames.append(constant_matrix(self.vertices[node], size))
        total = Jet2.constant(0., size)
        rotations, maps, fields = [], [], []
        for cell, (left, right) in enumerate(HALVES):
            b, anchor, lc, ld0, delta0, force, coupling = self.charts[cell]
            by, bz, phi = variables[offset+3*cell:offset+3*cell+3]
            if abs(phi.value) >= np.pi:
                raise ValueError("axial spin left its principal chart; cutback required")
            tilt_square = by*by+bz*bz
            if tilt_square.value >= (.9*np.pi)**2:
                raise ValueError("transverse tilt requires refinement or cutback")
            chord = self.positions[right]-self.positions[left]
            axis = chord/ld0
            change = [increments[6*right+i]-increments[6*left+i] for i in range(3)]
            # Rationalized radial increment: exactly zero at the anchor,
            # without subtracting nearly equal square roots. In real
            # arithmetic ld0^2=chord.chord. No derivative/value override.
            radial_square = dot(change, change)+2*sum((chord[i]*change[i] for i in range(3)), zero)
            radial = radial_square/(sqrt(ld0*ld0+radial_square)+ld0)
            ld = ld0+radial
            delta = delta0+radial
            direction_change = [(change[i]-axis[i]*radial)/ld for i in range(3)]
            cross_vector = matvec(constant_matrix(np.array([[0., -axis[2], axis[1]],
                                                           [axis[2], 0., -axis[0]],
                                                           [-axis[1], axis[0], 0.]]), size),
                                   direction_change)
            cosine = 1+sum((axis[i]*direction_change[i] for i in range(3)), zero)
            if cosine.value <= np.cos(.9*np.pi):
                raise ValueError("moving chord chart requires refinement or cutback")
            cross = jet_skew(cross_vector)
            square = matmul(cross, cross)
            transport = [[(1. if i == j else 0.)+cross[i][j]+square[i][j]/(1+cosine)
                          for j in range(3)] for i in range(3)]
            current = matmul(transport, constant_matrix(anchor, size))
            tilt = so3_exp([zero, by, bz])
            spin = so3_exp([phi, zero, zero])
            u = matmul(matmul(matmul(current, spin), tilt), constant_matrix(b.T, size))
            sinc, cosc = _exp_coefficients(tilt_square)
            z = [delta-ld*cosc*tilt_square, -ld*sinc*bz, ld*sinc*by]
            ell = []
            for node, sign in ((left, -1), (right, 1)):
                frame = matmul(u, constant_matrix(self.base.frames[node], size))
                ell.extend(sign*item for item in so3_log(matmul(transpose(frame), vertex_frames[node])))
            coupled = matvec(constant_matrix(coupling, size), z)
            e = [a+b for a, b in zip(coupled, ell)]
            total += (_quadratic(z, force)+_quadratic(e, self.base.h_inverse[cell]))/2
            for i in range(3):
                for j in range(3):
                    total -= self.base.lift_work[cell, i, j]*(u[i][j]-(1. if i == j else 0.))
            matrix = np.array([[item.value for item in row] for row in u])
            spatial_map = np.empty((3, 3))
            for column in range(3):
                derivative = np.array([[item.gradient[offset+3*cell+column] for item in row] for row in u])
                angular = derivative @ matrix.T
                spatial_map[:, column] = (angular[2, 1]-angular[1, 2],
                                          angular[0, 2]-angular[2, 0],
                                          angular[1, 0]-angular[0, 1])
            rotations.append(matrix)
            maps.append(spatial_map/2)
            fields.append((b @ np.array([item.value for item in z]),
                           self.base.h_inverse[cell] @ np.array([item.value for item in e])))
        for node in range(3):
            for i in range(3):
                total -= self.base.nodal_line_load[node, i]*(
                    self.positions[node, i]-self.base.coordinates[node, i]+increments[6*node+i])
        if not (np.isfinite(total.value) and np.isfinite(total.gradient).all()
                and np.isfinite(total.hessian).all()):
            raise LocalStationarityError("nonfinite retained functional")
        return total, np.array(rotations), np.array(maps), fields

    def jet(self, parameters):
        return self._functional(parameters)[:3]

    def _trial(self, increment):
        _, _, _, x, q = self.base._configuration(self.positions, self.vertices, increment)
        return type(self)(self.base.reference, self.base.section, x, q,
                          order=self.base.order, line_force=self.base.line_force)

    def _fingerprint(self, parameters, increment):
        record = {"schema": "p5-retained-diagnostic-state-v1",
                  "coordinates": self.base.coordinates.tolist(), "frames": self.base.frames.tolist(),
                  "section": self.base.section.tolist(), "positions": self.positions.tolist(),
                  "vertices": self.vertices.tolist(), "line_force": self.base.line_force.tolist(),
                  "order": self.base.order, "parameters": parameters.tolist(), "increment": increment.tolist()}
        return hashlib.sha256(canonical_bytes(record)).hexdigest().upper()

    def evaluate(self, *, increment=None):
        increment = np.zeros(18) if increment is None else _array(increment, (18,), "increment")
        trial = self if not np.any(increment) else self._trial(increment)
        solution = trial.solve()
        jet, rotations, maps, _ = trial._functional(solution.parameters, external=True,
                                                    origin=increment, base_frames=self.vertices)
        local_gradient = jet.gradient[18:]
        torque = np.concatenate([np.linalg.solve(maps[c].T, local_gradient[3*c:3*c+3]) for c in (0, 1)])
        if max(abs(torque)) > 2e-11:
            raise LocalStationarityError("retained external/local stationarity disagreement")
        tangent = jet.hessian[:18, :18]-jet.hessian[:18, 18:] @ np.linalg.solve(
            jet.hessian[18:, 18:], jet.hessian[18:, :18])
        return RetainedResponse(jet.value, _readonly(jet.gradient[:18]), _readonly(tangent),
                                solution.parameters, _readonly(rotations), _readonly(increment),
                                solution.physical_residual_norm, solution.iterations,
                                self._fingerprint(solution.parameters, increment))

    def recover(self, response, *, stations=(.25, .75)):
        if response.state_sha256 != self._fingerprint(response.parameters, response.increment):
            raise ValueError("retained response/configuration fingerprint mismatch")
        trial = self if not np.any(response.increment) else self._trial(response.increment)
        jet, rotations, maps, fields = trial._functional(response.parameters)
        if trial.physical_norm(jet, maps) > 2e-11:
            raise LocalStationarityError("retained recovery is not stationary")
        if not np.allclose(rotations, response.rotations, rtol=0., atol=1e-11):
            raise ValueError("retained response rotations mismatch")
        rows = []
        for cell, (z, endpoint_moment) in enumerate(fields):
            for fraction in stations:
                if not np.isfinite(fraction) or not 0 <= fraction <= 1:
                    raise ValueError("station fraction must be finite in [0,1]")
                xi = cell-1+fraction
                frame = self.base.reference.frame(xi)
                gamma = frame.T @ z/self.base.reference.jacobian(xi)
                m = (1-fraction)*endpoint_moment[:3]+fraction*endpoint_moment[3:]
                kappa = np.linalg.solve(self.base.section[3:, 3:], m-self.base.section[:3, 3:].T @ gamma)
                strain = np.concatenate((gamma, kappa))
                resultant = self.base.section @ strain
                current = rotations[cell] @ frame
                rows.append({"cell": cell, "xi": xi, "strain": strain, "resultant": resultant,
                             "current_frame": current, "spatial_force": current @ resultant[:3],
                             "spatial_moment": current @ resultant[3:]})
        return rows
