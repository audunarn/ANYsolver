"""Physical round station on a retained, two-cell native B3-GE beam.

This is a local C3 geometry/work map. It owns no nonlinear analysis and does
not condense the cell rotations or admit the native beam to generic FEModel.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, fsum, isfinite, sin, tau

import numpy as np

from anysolver._ge_beam3_centered_reference import (
    CenteredCurvedBeam3ReferenceGeometry,
)
from anysolver._ge_beam3_p5.arrays import _array, _frames
from anysolver._ge_beam3_p5.compensated_coordinates import validate_pair
from anysolver._ge_beam3_p5_seeded.core import sha


def _cross_matrix(value: np.ndarray) -> np.ndarray:
    x, y, z = map(float, value)
    return np.array(((0.0, -z, y), (z, 0.0, -x), (-y, x, 0.0)))


def _readonly(value: np.ndarray) -> np.ndarray:
    result = np.array(value, dtype=float, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class NativeRetainedRoundStationState:
    """Position and virtual-work maps before structural/contact assembly."""

    centerline_position: np.ndarray
    surface_position: np.ndarray
    centerline_geometric_jacobian: np.ndarray
    surface_geometric_jacobian: np.ndarray

    def generalized_surface_jacobian(self) -> np.ndarray:
        """The final 18 constitutive/resultant coordinates carry no position."""
        result = np.zeros((3, 42))
        result[:, :24] = self.surface_geometric_jacobian
        return result

    def generalized_surface_work(self, physical_force: np.ndarray) -> np.ndarray:
        force = _array(physical_force, (3,), "native station physical force")
        return self.generalized_surface_jacobian().T @ force


class NativeRetainedRoundStation:
    """One owned interior material station and declared circular section point."""

    def __init__(self, element_id: int,
                 reference: CenteredCurvedBeam3ReferenceGeometry,
                 xi: float, radius: float, angle: float):
        if type(element_id) is not int or element_id <= 0:
            raise ValueError("native contact station needs positive element identity")
        if type(reference) is not CenteredCurvedBeam3ReferenceGeometry:
            raise TypeError("native contact station needs exact centered B3-GE reference")
        parameters = (xi, radius, angle)
        if any(type(item) not in (int, float) or not isfinite(item)
               for item in parameters):
            raise ValueError("native contact station needs finite binary64 geometry")
        xi, radius, angle = map(float, parameters)
        if not (-1.0 < xi < 0.0 or 0.0 < xi < 1.0):
            raise ValueError("native contact station must be interior to one half-cell")
        if radius <= 0.0 or not 0.0 <= angle < tau:
            raise ValueError("native round station needs positive radius and angle in [0, 2pi)")
        self.element_id = element_id
        self.reference = reference
        self.xi = xi
        self.radius = radius
        self.angle = angle
        self.cell = 0 if xi < 0.0 else 1
        self.t = xi + 1.0 if self.cell == 0 else xi
        self._reference_digest = sha(reference.canonical_data())
        self.identity = sha(dict(
            policy="NATIVE_RETAINED_ROUND_STATION_GEOMETRY_DEV_V0",
            element_id=element_id, reference=self._reference_digest,
            xi=xi, radius=radius, angle=angle, cell=self.cell,
        ))

    def evaluate(self, positions: np.ndarray, position_low: np.ndarray,
                 cell_rotations: np.ndarray) -> NativeRetainedRoundStationState:
        if sha(self.reference.canonical_data()) != self._reference_digest:
            raise ValueError("native contact station reference identity changed")
        high = _array(positions, (3, 3), "native contact nodal positions")
        low = _array(position_low, (3, 3), "native contact nodal low parts")
        rotations = _frames(cell_rotations, 2, "native contact cell rotations")
        for first, second in zip(high.flat, low.flat):
            validate_pair(float(first), float(second))
        lift = self.reference.half_cell_lift(self.cell, self.t)
        frame = self.reference.frame(self.xi)
        radial_reference = self.radius*(
            cos(self.angle)*frame[:, 1]+sin(self.angle)*frame[:, 2]
        )
        rotation = rotations[self.cell]
        curved_lift = rotation @ lift
        surface_lift = rotation @ (lift+radial_reference)
        left, right = self.cell, self.cell+1
        weights = (1.0-self.t, self.t)
        base = np.array([
            fsum((weights[0]*float(high[left, axis]),
                  weights[0]*float(low[left, axis]),
                  weights[1]*float(high[right, axis]),
                  weights[1]*float(low[right, axis])))
            for axis in range(3)
        ])
        centerline = base+curved_lift
        surface = base+surface_lift
        centerline_jacobian = np.zeros((3, 24))
        surface_jacobian = np.zeros((3, 24))
        for node, weight in ((left, weights[0]), (right, weights[1])):
            centerline_jacobian[:, 6*node:6*node+3] = weight*np.eye(3)
            surface_jacobian[:, 6*node:6*node+3] = weight*np.eye(3)
        angular = slice(18+3*self.cell, 21+3*self.cell)
        centerline_jacobian[:, angular] = -_cross_matrix(curved_lift)
        surface_jacobian[:, angular] = -_cross_matrix(surface_lift)
        return NativeRetainedRoundStationState(
            _readonly(centerline), _readonly(surface),
            _readonly(centerline_jacobian), _readonly(surface_jacobian),
        )
