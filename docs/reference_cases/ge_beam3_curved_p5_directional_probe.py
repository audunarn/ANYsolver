"""Research directional tangent actions before dense nodal assembly.

The retained scalar functional is unchanged. External direction seeds enter
its analytic Jet2 graph before condensation. No production or review authority.
"""

from dataclasses import dataclass
import math
import numpy as np

from anysolver._ge_beam3_mixed_ad import (
    Jet2, _exp_coefficients, constant_matrix, dot, matmul, matvec,
    skew as jet_skew, so3_exp, so3_log, sqrt, transpose,
)
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import (
    LocalStationarityError, _array, _quadratic, _readonly,
)
from docs.reference_cases.ge_beam3_curved_p5_retained_response_probe import RetainedFiniteResponseProbe


@dataclass(frozen=True)
class DirectionalTangent:
    action: np.ndarray
    directional_stiffness: float


def accurate_products(coefficients, values):
    """Compensated product sum on this Python 3.13 research runtime.

    FMA retains each product's rounding remainder; fsum retains cancellation
    across terms. This changes arithmetic, not the mathematical expression.
    Production compatibility/performance on other runtimes is not qualified.
    """
    if len(coefficients) != len(values):
        raise ValueError("compensated product lengths differ")
    pieces = []
    for a, b in zip(coefficients, values):
        a, b = float(a), float(b)
        product = a*b
        if not math.isfinite(product):
            raise ValueError("nonfinite compensated product")
        pieces.extend((product, math.fma(a, b, -product)))
    return math.fsum(pieces)


def accurate_linear_form(coefficients, entries):
    """Evaluate a constant-coefficient linear form and its analytic jets."""
    size = entries[0].gradient.size
    value = accurate_products(coefficients, [item.value for item in entries])
    gradient = np.array([accurate_products(coefficients, [item.gradient[i] for item in entries])
                         for i in range(size)])
    hessian = np.zeros((size, size))
    if any(np.any(item.hessian) for item in entries):
        for i in range(size):
            for j in range(size):
                hessian[i, j] = accurate_products(coefficients, [item.hessian[i, j] for item in entries])
    return Jet2(value, gradient, hessian)


class DirectionalResponseProbe(RetainedFiniteResponseProbe):
    def _functional(self, parameters, *, external=False, origin=None, base_frames=None, directions=None):
        parameters = _array(parameters, (6,), "retained parameters")
        if directions is not None and not external:
            raise ValueError("directions require external differentiation")
        seed = np.eye(18) if directions is None else np.asarray(directions, dtype=float)
        if (seed.ndim != 2 or seed.shape[0] != 18 or not 1 <= seed.shape[1] <= 19
                or not np.isfinite(seed).all()):
            raise ValueError("finite 18-by-k directional seed required, 1 <= k <= 19")
        offset = seed.shape[1] if external else 0
        size = offset+6
        origin = np.zeros(18) if origin is None else _array(origin, (18,), "increment")
        # Seed external directions before potential evaluation, not after
        # forming the dense physical-coordinate Hessian.
        external_variables = []
        for i in range(18):
            gradient = np.zeros(size)
            if external:
                gradient[:offset] = seed[i]
            external_variables.append(Jet2(origin[i], gradient, np.zeros((size, size))))
        variables = external_variables + [Jet2.variable(parameters[i], offset+i, size) for i in range(6)]
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
            by, bz, phi = variables[18+3*cell:18+3*cell+3]
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
            # Expand (x_R-x_L).(v_R-v_L) before rounding either difference.
            # Keeping exact binary64 input products matters when cancellation
            # is followed by an axial stiffness of order 1e12.
            coefficients, entries = [], []
            for i in range(3):
                coefficients.extend((self.positions[right, i], -self.positions[left, i],
                                     -self.positions[right, i], self.positions[left, i]))
                entries.extend((increments[6*right+i], increments[6*right+i],
                                increments[6*left+i], increments[6*left+i]))
            radial_square = dot(change, change)+2*accurate_linear_form(coefficients, entries)
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

    def tangent_action(self, response, direction):
        direction = _array(direction, (18,), "direction")
        if response.state_sha256 != self._fingerprint(response.parameters, response.increment):
            raise ValueError("retained response/configuration fingerprint mismatch")
        trial = self if not np.any(response.increment) else self._trial(response.increment)
        seed = np.column_stack((np.eye(18), direction))
        jet, rotations, maps, _ = trial._functional(response.parameters, external=True,
                                            origin=response.increment, base_frames=self.vertices,
                                            directions=seed)
        if not np.allclose(rotations, response.rotations, rtol=0., atol=1e-11):
            raise ValueError("retained response rotations mismatch")
        local_gradient = jet.gradient[19:]
        torque = np.concatenate([np.linalg.solve(maps[c].T, local_gradient[3*c:3*c+3])
                                  for c in (0, 1)])
        if max(abs(torque)) > 2e-11:
            raise LocalStationarityError("directional/local stationarity disagreement")
        correction = np.linalg.solve(jet.hessian[19:, 19:], jet.hessian[19:, 18])
        action = jet.hessian[:18, 18]-jet.hessian[:18, 19:] @ correction
        stiffness = jet.hessian[18, 18]-jet.hessian[18, 19:] @ correction
        if not np.isfinite(action).all() or not math.isfinite(float(stiffness)):
            raise LocalStationarityError("nonfinite condensed directional action")
        return DirectionalTangent(_readonly(action), float(stiffness))
