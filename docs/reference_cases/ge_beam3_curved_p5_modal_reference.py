"""Standalone conforming continuum Ritz reference, same-author research.

No P5/P3/P4 mechanics, frames, matrices, recovery or eigen helpers imported.
Spatial infinitesimal displacement and rotation are independently expanded
in clamped-left polynomial fields on the analytic parabola. This is not
an independently authored or certified continuum frequency oracle.
"""

from dataclasses import dataclass

import numpy as np


def _spd(value):
    matrix = np.array(value, dtype=float, copy=True)
    if matrix.shape != (6, 6) or not np.isfinite(matrix).all():
        raise ValueError("finite six-by-six continuum matrix required")
    if not np.array_equal(matrix, matrix.T):
        raise ValueError("symmetric continuum matrix required")
    np.linalg.cholesky(matrix)
    return matrix


@dataclass(frozen=True)
class ContinuumRitz:
    stiffness: np.ndarray
    mass: np.ndarray
    squared_frequencies: np.ndarray
    coefficients: np.ndarray


def parabolic_modal_reference(height, section, section_mass, *, terms=12, order=64):
    """Clamped-free linear Simo-Reissner continuum, all six spatial fields.

    r(t)=(t,h*(1-t^2),0), R=(tangent,global-z,tangent cross global-z).
    gamma=R^T(u_s + tangent cross theta), kappa=R^T theta_s.
    Kinetic velocities are R^T u_dot and R^T theta_dot. There are no
    independent cell rotations, static condensation, mixed jumps or fitted
    stiffness/mass terms. Natural free-tip force/moment conditions follow
    from the weak potential. Trial functions are (t+1)*P_j(t), j=0..terms-1.
    """
    if not np.isfinite(height) or not 0 <= height <= .75:
        raise ValueError("finite reference height in [0,0.75] required")
    if not isinstance(terms, int) or isinstance(terms, bool) or terms not in (4, 8, 12, 16):
        raise ValueError("four, eight, twelve or sixteen polynomial terms required")
    if not isinstance(order, int) or isinstance(order, bool) or order not in (48, 64, 96):
        raise ValueError("48, 64 or 96 continuum quadrature points required")
    elastic = np.linalg.cholesky(_spd(section)).T
    inertia = np.linalg.cholesky(_spd(section_mass)).T
    points, weights = np.polynomial.legendre.leggauss(order)
    values = np.polynomial.legendre.legvander(points, terms-1)
    derivatives = np.empty_like(values)
    for j in range(terms):
        polynomial = np.zeros(terms)
        polynomial[j] = 1.
        derivatives[:, j] = np.polynomial.legendre.legval(
            points, np.polynomial.legendre.legder(polynomial))
    strain_rows, velocity_rows = [], []
    for index, (t, weight) in enumerate(zip(points, weights)):
        tangent = np.array([1., -2*height*t, 0.])
        jacobian = np.linalg.norm(tangent)
        tangent /= jacobian
        frame = np.column_stack((tangent, [0., 0., 1.], np.cross(tangent, [0., 0., 1.])))
        cross = np.column_stack([np.cross(tangent, axis) for axis in np.eye(3)])
        basis = (t+1)*values[index]
        slope = (values[index]+(t+1)*derivatives[index])/jacobian
        strain = np.zeros((6, 6*terms))
        velocity = np.zeros_like(strain)
        for j in range(terms):
            strain[:3, 6*j:6*j+3] = slope[j]*frame.T
            strain[:3, 6*j+3:6*j+6] = basis[j]*frame.T @ cross
            strain[3:, 6*j+3:6*j+6] = slope[j]*frame.T
            velocity[:3, 6*j:6*j+3] = basis[j]*frame.T
            velocity[3:, 6*j+3:6*j+6] = basis[j]*frame.T
        strain_rows.append(np.sqrt(weight*jacobian)*elastic @ strain)
        velocity_rows.append(np.sqrt(weight*jacobian)*inertia @ velocity)
    strain_factor, velocity_factor = np.vstack(strain_rows), np.vstack(velocity_rows)
    stiffness, mass = strain_factor.T @ strain_factor, velocity_factor.T @ velocity_factor
    # Retain both energy factors rather than squaring their condition numbers
    # before extracting the smallest eigenvalues. QR makes mass coordinates
    # orthonormal; singular values of the transformed strain factor are omega.
    _, mass_upper = np.linalg.qr(velocity_factor, mode='reduced')
    normalized_strain = np.linalg.solve(mass_upper.T, strain_factor.T).T
    _, singular, right = np.linalg.svd(normalized_strain, full_matrices=False)
    squared = singular[::-1]**2
    coefficients = np.linalg.solve(mass_upper, right.T[:, ::-1])
    if not np.isfinite(squared).all() or np.any(squared <= 0):
        raise ValueError("continuum clamped spectrum must be finite and positive")
    for array in (stiffness, mass, squared, coefficients):
        array.setflags(write=False)
    return ContinuumRitz(stiffness, mass, squared, coefficients)
