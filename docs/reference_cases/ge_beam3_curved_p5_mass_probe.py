"""Reference kinetic-field/Guyan diagnostics, not a qualified dynamic policy.

The P5 lift has local cell angular velocities and no direct inertia on the
hybrid vertex rotations. Its statically reduced mass need not be full rank.
Do not add trace inertia or silently substitute the accepted P3 nodal mass.
"""

from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES, skew, validate_section
from docs.reference_cases.ge_beam3_curved_p5_factor_probe import reference_factors
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly


@dataclass(frozen=True)
class ReferenceKineticFactors:
    full: np.ndarray
    reduced: np.ndarray
    static_map: np.ndarray
    stiffness_factor: np.ndarray
    uncondensed_stiffness_factor: np.ndarray

    def kinetic_energy(self, velocity):
        velocity = _array(velocity, (18,), "external velocity")
        field = self.reduced @ velocity
        return float(field @ field/2)

    @property
    def mass(self):
        return self.reduced.T @ self.reduced

    @property
    def stiffness(self):
        return self.stiffness_factor.T @ self.stiffness_factor


def reference_kinetic_factors(reference, section, section_mass, *, order=24):
    """Integrate reference kinetic energy, then use the static local map.

    v=I(v_node)+omega_cell cross (r0-I(X)); angular velocity=omega_cell.
    At each station express both spatial velocities in the physical R0 frame
    before applying the symmetric positive-definite 6x6 section inertia.
    The full vector has external18 + local6 coordinates. Its static map is
    [I;T], using exactly the existing elastic local elimination. This is a
    Guyan approximation to dynamics, NOT exact elimination of local inertia.
    """
    if not isinstance(order, int) or isinstance(order, bool) or not 2 <= order <= 64:
        raise ValueError("mass quadrature order must be an integer from 2 to 64")
    section_mass = validate_section(section_mass)
    inertia_factor = np.linalg.cholesky(section_mass).T
    elastic = reference_factors(reference, section, order)
    mapping = np.vstack((np.eye(18), elastic.local_map))
    nodes = reference.coordinates
    points, weights = np.polynomial.legendre.leggauss(order)
    rows = []
    for cell, (left, right) in enumerate(HALVES):
        for point, weight in zip(points, weights):
            t = (point+1)/2
            xi = cell-1+t
            frame = reference.frame(xi)
            offset = reference.position(xi)-((1-t)*nodes[left]+t*nodes[right])
            velocity = np.zeros((6, 24))
            velocity[:3, 6*left:6*left+3] = (1-t)*frame.T
            velocity[:3, 6*right:6*right+3] = t*frame.T
            local = slice(18+3*cell, 21+3*cell)
            velocity[:3, local] = -frame.T @ skew(offset)
            velocity[3:, local] = frame.T
            measure = weight*reference.jacobian(xi)/2
            rows.append(np.sqrt(measure)*inertia_factor @ velocity)
    full = np.vstack(rows)
    return ReferenceKineticFactors(_readonly(full), _readonly(full @ mapping),
                                    _readonly(mapping), elastic.condensed, elastic.full)


def full_inertia_pencil(factors, *, clamped=False):
    """Retain cell rotational inertia, eliminating only zero-inertia traces.

    This reference diagnostic is exact algebraic elimination within the
    uncondensed semidiscrete model. It is distinct from imposing the static
    cell-rotation map before kinetic-energy evaluation (Guyan approximation).
    It does not implement a production dynamic solver or 18x18 mass API.
    """
    if not isinstance(clamped, bool):
        raise ValueError("explicit boolean clamped boundary required")
    first = 1 if clamped else 0
    trace = np.array([6*i+j for i in range(first, 3) for j in (3, 4, 5)])
    physical = np.array([6*i+j for i in range(first, 3) for j in (0, 1, 2)]+list(range(18, 24)))
    if np.any(factors.full[:, trace] != 0):
        raise ValueError("trace kinetic energy must be exactly absent")
    stiffness = factors.uncondensed_stiffness_factor.T @ factors.uncondensed_stiffness_factor
    algebraic = stiffness[np.ix_(trace, trace)]
    np.linalg.cholesky(algebraic)
    mapping = np.zeros((24, len(physical)))
    mapping[physical] = np.eye(len(physical))
    mapping[trace] = -np.linalg.solve(algebraic, stiffness[np.ix_(trace, physical)])
    k_factor = factors.uncondensed_stiffness_factor @ mapping
    m_factor = factors.full @ mapping
    return _readonly(mapping), _readonly(k_factor.T @ k_factor), _readonly(m_factor.T @ m_factor)


def eliminate_trace_mass_kernel(factors):
    """Eliminate three algebraic trace modes of one free reference macro.

    Zero kinetic energy implies zero nodal translations and zero cell spins.
    Thus the mass kernel is the kernel of T_theta (6x9). A complete QR gives
    three trace basis vectors without filtering small eigenvalues of M.
    Solve their stiffness equations exactly in this reduced model. No mass
    floor, penalty, pseudoinverse or discarded finite eigenvalue is used.
    """
    rotational = np.array([6*i+j for i in range(3) for j in (3, 4, 5)])
    t_theta = factors.static_map[18:, rotational]
    orthogonal, triangular = np.linalg.qr(t_theta.T, mode='complete')
    if np.linalg.matrix_rank(triangular[:6]) != 6:
        raise ValueError("six independent local angular maps required")
    null = np.zeros((18, 3))
    null[rotational] = orthogonal[:, 6:]
    complete, _ = np.linalg.qr(null, mode='complete')
    retained = complete[:, 3:]
    stiffness = factors.stiffness
    algebraic = null.T @ stiffness @ null
    np.linalg.cholesky(algebraic)
    mapping = retained-null @ np.linalg.solve(algebraic, null.T @ stiffness @ retained)
    mass = (factors.reduced @ mapping).T @ (factors.reduced @ mapping)
    elastic = (factors.stiffness_factor @ mapping).T @ (factors.stiffness_factor @ mapping)
    np.linalg.cholesky(mass)
    return _readonly(null), _readonly(mapping), _readonly(elastic), _readonly(mass)


def symmetric_modes(stiffness, mass):
    """Return all eigenvalues/vectors of a small SPD-mass research pencil.

    Negative and near-zero eigenvalues are returned, never clipped or hidden.
    This helper does not classify rigid modes or authorize an analysis.
    """
    stiffness = np.asarray(stiffness, dtype=float)
    mass = np.asarray(mass, dtype=float)
    if (stiffness.ndim != 2 or stiffness.shape[0] != stiffness.shape[1]
            or not 1 <= len(stiffness) <= 102 or mass.shape != stiffness.shape
            or not np.isfinite(stiffness).all() or not np.isfinite(mass).all()):
        raise ValueError("finite equal square matrices of order 1 through 102 required")
    for matrix in (stiffness, mass):
        if np.linalg.norm(matrix-matrix.T) > 1e-11*max(1., np.linalg.norm(matrix)):
            raise ValueError("symmetric modal matrices required")
    factor = np.linalg.cholesky(mass)
    normalized = np.linalg.solve(factor, np.linalg.solve(factor, stiffness).T).T
    eigenvalues, vectors = np.linalg.eigh(normalized)
    return _readonly(eigenvalues), _readonly(np.linalg.solve(factor.T, vectors))


def reference_chain_pencil(references, section, section_mass):
    """Assemble only 1/2/4/8 reference macros; no constraints or mode filtering."""
    references = tuple(references)
    if len(references) not in (1, 2, 4, 8):
        raise ValueError("one, two, four or eight research macros required")
    for previous, current in zip(references, references[1:]):
        if (not np.array_equal(previous.coordinates[-1], current.coordinates[0])
                or not np.array_equal(previous.nodal_triads[-1], current.nodal_triads[0])):
            raise ValueError("identical shared reference node/frame required")
    size = 6*(2*len(references)+1)
    stiffness, mass = np.zeros((size, size)), np.zeros((size, size))
    for index, reference in enumerate(references):
        factors = reference_kinetic_factors(reference, section, section_mass)
        slots = np.arange(12*index, 12*index+18)
        stiffness[np.ix_(slots, slots)] += factors.stiffness
        mass[np.ix_(slots, slots)] += factors.mass
    return _readonly(stiffness), _readonly(mass)
