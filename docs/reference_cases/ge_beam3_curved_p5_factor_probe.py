"""Reference-state conditioning diagnostics, not mechanics qualification.

Keep the earlier direct-Schur probe unchanged. This equivalent least-squares
elimination retains the energy factor, avoiding subtraction of large stiffness
blocks. It does not address finite-state geometric stiffness or local Newton
conditioning, and does not establish thin-beam engineering accuracy.
"""

from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import (
    HALVES, metrics, skew, validate_section,
)


@dataclass(frozen=True)
class ReferenceFactors:
    full: np.ndarray
    condensed: np.ndarray
    local_map: np.ndarray

    def energy(self, displacement):
        displacement = np.asarray(displacement, dtype=float)
        if displacement.shape != (18,) or not np.isfinite(displacement).all():
            raise ValueError("finite 18-component displacement required")
        residual = self.condensed @ displacement
        return float(residual @ residual / 2)


def reference_factors(reference, section, order=24):
    """Return B, D, T with min_a ||B [q;a]||^2 = ||D q||^2, a=Tq.

    B has 18 rows (nine per half), 18 external and six local columns.
    For H=L L^T, the complementary energy factor is L^-1 De, not
    L^-T De. Complete QR of the six internal columns performs elimination
    without normal equations. Dense D^T D can still lose small-mode energy
    when subsequently contracted; consumers must retain D for that check.
    """
    section = validate_section(section)
    coordinates, frames = reference.coordinates, reference.nodal_triads
    rows = []
    for cell, (left, right) in enumerate(HALVES):
        data = metrics(reference, section, cell, order)
        dz = np.zeros((3, 24))
        dz[:, 6*left:6*left+3] = -np.eye(3)
        dz[:, 6*right:6*right+3] = np.eye(3)
        local = slice(18+3*cell, 21+3*cell)
        dz[:, local] = skew(coordinates[right]-coordinates[left])
        de = np.zeros((6, 24))
        de[:3, 6*left+3:6*left+6] = -frames[left].T
        de[:3, local] = frames[left].T
        de[3:, 6*right+3:6*right+6] = frames[right].T
        de[3:, local] = -frames[right].T
        de += data.coupling @ dz
        rows.extend((np.linalg.cholesky(data.force).T @ dz,
                     np.linalg.solve(np.linalg.cholesky(data.compliance), de)))
    full = np.vstack(rows)
    orthogonal, triangular = np.linalg.qr(full[:, 18:], mode="complete")
    # A singular internal block is an error, never a pseudoinverse fallback.
    local_map = -np.linalg.solve(triangular[:6], orthogonal[:, :6].T @ full[:, :18])
    condensed = orthogonal[:, 6:].T @ full[:, :18]
    for made in (full, condensed, local_map):
        if not np.isfinite(made).all():
            raise ValueError("nonfinite reference factor")
        made.setflags(write=False)
    return ReferenceFactors(full, condensed, local_map)


def constant_spatial_moment_mode(reference, section, spatial_moment, order=24):
    """Discrete manufactured zero-force mode for a block-diagonal section.

    Endpoint material moments are R0^T M. Thus both cell moment balances
    vanish exactly in real arithmetic. H m gives endpoint relative rotation;
    translations follow theta_cell cross chord so z=0. Expected energy is
    sum(m^T H m)/2, independent of axial/shear stiffness. This is not an
    independent continuum reference or a finite-curvature patch claim.
    """
    section = validate_section(section)
    if np.any(section[:3, 3:] != 0):
        raise ValueError("manufactured mode requires uncoupled section")
    moment = np.asarray(spatial_moment, dtype=float)
    if moment.shape != (3,) or not np.isfinite(moment).all():
        raise ValueError("finite spatial moment required")
    coordinates, frames = reference.coordinates, reference.nodal_triads
    nodal = np.zeros((3, 6))
    internal = np.zeros((2, 3))
    energy = 0.0
    for cell, (left, right) in enumerate(HALVES):
        data = metrics(reference, section, cell, order)
        m = np.concatenate((frames[left].T @ moment, frames[right].T @ moment))
        ell = data.compliance @ m
        if cell == 0:
            nodal[left, 3:] = -frames[left] @ ell[:3]
        else:
            internal[cell] = nodal[left, 3:] + frames[left] @ ell[:3]
        nodal[right, 3:] = internal[cell] + frames[right] @ ell[3:]
        nodal[right, :3] = nodal[left, :3] + np.cross(
            internal[cell], coordinates[right]-coordinates[left])
        energy += float(m @ ell / 2)
    return nodal.ravel(), internal.ravel(), energy
