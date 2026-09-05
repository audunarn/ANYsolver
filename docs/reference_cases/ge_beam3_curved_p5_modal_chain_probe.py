"""Full-inertia curved-chain modal development; no production dynamic API."""

from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _readonly
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import reference_kinetic_factors


@dataclass(frozen=True)
class FullInertiaChain:
    full_stiffness: np.ndarray
    full_mass: np.ndarray
    map: np.ndarray
    stiffness: np.ndarray
    mass: np.ndarray


def clamped_full_inertia_chain(references, section, section_mass):
    """Assemble before eliminating shared, exactly zero-inertia vertex traces.

    Clamped first vertex; all six internal cell-spin variables per macro are
    retained dynamically. The largest diagnostic has 150 full coordinates,
    48 free algebraic traces, and 96 dynamic coordinates. No spectral mode
    filtering, inertia modification or automatic mesh refinement is used.
    """
    references = tuple(references)
    if len(references) not in (1, 2, 4, 8):
        raise ValueError("one, two, four or eight research macros required")
    for previous, current in zip(references, references[1:]):
        if (not np.array_equal(previous.coordinates[-1], current.coordinates[0])
                or not np.array_equal(previous.nodal_triads[-1], current.nodal_triads[0])):
            raise ValueError("identical shared reference node/frame required")
    nodal = 6*(2*len(references)+1)
    total = nodal+6*len(references)
    stiffness, mass = np.zeros((total, total)), np.zeros((total, total))
    for index, reference in enumerate(references):
        factors = reference_kinetic_factors(reference, section, section_mass)
        slots = np.r_[np.arange(12*index, 12*index+18), np.arange(nodal+6*index, nodal+6*index+6)]
        stiffness[np.ix_(slots, slots)] += factors.uncondensed_stiffness_factor.T @ factors.uncondensed_stiffness_factor
        mass[np.ix_(slots, slots)] += factors.full.T @ factors.full
    trace = np.array([6*i+j for i in range(1, 2*len(references)+1) for j in (3, 4, 5)])
    dynamic = np.r_[[6*i+j for i in range(1, 2*len(references)+1) for j in (0, 1, 2)], np.arange(nodal, total)]
    if np.any(mass[:, trace] != 0):
        raise ValueError("algebraic vertex traces must have exactly zero inertia")
    algebraic = stiffness[np.ix_(trace, trace)]
    np.linalg.cholesky(algebraic)
    mapping = np.zeros((total, len(dynamic)))
    mapping[dynamic] = np.eye(len(dynamic))
    mapping[trace] = -np.linalg.solve(algebraic, stiffness[np.ix_(trace, dynamic)])
    # These moderate-section diagnostics use direct congruence. They do not
    # claim high-contrast cancellation safety or replace retained force factors.
    reduced_k = mapping.T @ stiffness @ mapping
    reduced_m = mapping.T @ mass @ mapping
    return FullInertiaChain(*(_readonly(array) for array in (stiffness, mass, mapping, reduced_k, reduced_m)))
