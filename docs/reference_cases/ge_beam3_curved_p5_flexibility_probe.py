"""Research-only reference flexibility, equivalent to the P5 mixed potential.

Equilibrated force/moment coordinates separate rigid motion before solving.
Neither this calculation nor its metric inputs are independent qualification.
No finite-state tangent, mass, history or production integration is supplied.
"""

from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import (
    HALVES, metrics, skew, validate_section,
)


@dataclass(frozen=True)
class CellFlexibility:
    basis: np.ndarray
    length: float
    cholesky: np.ndarray
    scale: np.ndarray
    moment_map: np.ndarray

    def deformation(self, left, right):
        translation = self.basis.T @ (right[:3]-left[:3])
        theta_right = self.basis.T @ right[3:]
        return np.concatenate((translation + self.length*skew((1., 0., 0.)) @ theta_right,
                               self.basis.T @ (right[3:]-left[3:])))

    def energy(self, deformation):
        amplitude = np.linalg.solve(self.cholesky, deformation/self.scale)
        return float(amplitude @ amplitude / 2)

    def stresses(self, deformation):
        scaled = np.linalg.solve(self.cholesky, deformation/self.scale)
        return np.linalg.solve(self.cholesky.T, scaled)/self.scale


@dataclass(frozen=True)
class ReferenceFlexibility:
    cells: tuple

    def energy(self, displacement):
        displacement = np.asarray(displacement, dtype=float)
        if displacement.shape != (18,) or not np.isfinite(displacement).all():
            raise ValueError("finite 18-component displacement required")
        nodal = displacement.reshape(3, 6)
        return sum(cell.energy(cell.deformation(nodal[left], nodal[right]))
                   for cell, (left, right) in zip(self.cells, HALVES))


def reference_flexibility(reference, section, order=24):
    """Condense by exact linear equilibrium before complementary inversion.

    p is force, t is left spatial moment in a chord-aligned proper basis.
    Right moment is t - chord cross p. Work coordinates are
    [du + chord cross theta_right, theta_right-theta_left].
    With m=W[p;t], the dual compliance is
    S = ([E,0]-J^T W)^T F^-1 ([E,0]-J^T W) + W^T H W.
    Diagonal equilibration precedes Cholesky. No penalty, threshold, spectral
    truncation or pseudoinverse is used. Keep the hierarchical deformation
    evaluation: forming a dense nodal stiffness loses its low-energy benefit.
    """
    section = validate_section(section)
    coordinates, frames = reference.coordinates, reference.nodal_triads
    cells = []
    for index, (left, right) in enumerate(HALVES):
        data = metrics(reference, section, index, order)
        chord = coordinates[right]-coordinates[left]
        length = float(np.linalg.norm(chord))
        axis = chord/length
        # Choose an existing physical frame direction only as a numerical
        # basis. The choice does not change the physical reference frame.
        transverse = [frames[left][:, i]-axis*(axis @ frames[left][:, i]) for i in (1, 2)]
        second = max(transverse, key=np.linalg.norm)
        second = second/np.linalg.norm(second)
        basis = np.column_stack((axis, second, np.cross(axis, second)))
        cross = length*skew((1., 0., 0.))
        moment_map = np.zeros((6, 6))
        moment_map[:3, 3:] = np.linalg.solve(frames[left], basis)
        moment_map[3:, 3:] = np.linalg.solve(frames[right], basis)
        # The axial force column is structurally zero; do not generate it
        # by subtracting nearly equal global cross-product components.
        moment_map[3:, :3] = -moment_map[3:, 3:] @ cross
        force_map = np.hstack((basis, np.zeros((3, 3))))-data.coupling.T @ moment_map
        compliance = force_map.T @ np.linalg.solve(data.force, force_map)
        compliance += moment_map.T @ data.compliance @ moment_map
        scale = np.sqrt(np.diag(compliance))
        if not np.isfinite(scale).all() or np.any(scale <= 0):
            raise ValueError("positive finite flexibility scale required")
        normalized = compliance/scale[:, None]/scale[None, :]
        cholesky = np.linalg.cholesky(normalized)
        for made in (basis, scale, cholesky, moment_map):
            made.setflags(write=False)
        cells.append(CellFlexibility(basis, length, cholesky, scale, moment_map))
    return ReferenceFlexibility(tuple(cells))
