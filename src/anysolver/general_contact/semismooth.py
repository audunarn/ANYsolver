"""Fine-Q1 nodal-force equations for the opt-in static active-set route."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class ContactLinearization:
    state: object
    force: np.ndarray
    tangent: sparse.csr_matrix | None
    gap_gradient: np.ndarray
    local_force: np.ndarray
    evaluations: int


def reference_nodal_support(law) -> np.ndarray:
    """Integrate the full reference source surface's nonnegative Q1 basis."""
    node_index = {node: i for i, node in enumerate(law.pressure_mode_ids)}
    support = np.zeros(len(node_index))
    gauss = (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0))
    for face in law.geometry.source_faces:
        if len(face.node_ids) != 4:
            raise ValueError("active-set source requires Q4 faces")
        coordinates = face.reference_positions
        for xi in gauss:
            for eta in gauss:
                n = np.asarray(((1-xi)*(1-eta), (1+xi)*(1-eta),
                                (1+xi)*(1+eta), (1-xi)*(1+eta)))/4.0
                dxi = np.asarray((-(1-eta), (1-eta), (1+eta), -(1+eta)))/4.0
                deta = np.asarray((-(1-xi), -(1+xi), (1+xi), (1-xi)))/4.0
                jac = np.linalg.norm(np.cross(dxi @ coordinates,
                                              deta @ coordinates))
                if not np.isfinite(jac) or jac <= 0.0:
                    raise ValueError("invalid active-set source reference surface")
                for local, node in enumerate(face.node_ids):
                    support[node_index[node]] += n[local]*jac
    if np.any(support <= 0.0) or not np.all(np.isfinite(support)):
        raise ValueError("active-set reference pressure support is not positive")
    return support


def linearize(manager, displacement, nodal_forces, *, tangent=True):
    """Pull the local unprojected force and all gap rows to structural DOFs."""
    source, target = manager._positions(displacement)
    manager.require_d1_coverage(source, target)
    raw = manager.law.nodal_force_linearization(
        source, target, nodal_forces, tangent=tangent,
    )
    force = np.asarray(manager.map.T @ raw.residual).reshape(-1)
    gap_gradient = np.asarray(raw.gap_gradient @ manager.map)
    stiffness = (sparse.csr_matrix(manager.map.T @ raw.tangent @ manager.map)
                 if tangent else None)
    return ContactLinearization(raw.state, force, stiffness, gap_gradient,
                                raw.residual, raw.energy_evaluations)


def complementarity(state, nodal_forces, scales, gap_gradient, *, tangent=True):
    """Return C=z-max(0,z-cg) and one declared generalized Jacobian."""
    z = np.asarray(nodal_forces, dtype=float)
    c = np.asarray(scales, dtype=float)
    gap = np.asarray(state.normalized_gap, dtype=float)
    support = np.asarray(state.reference_support, dtype=float)
    if z.shape != gap.shape or c.shape != gap.shape:
        raise ValueError("active-set pressure space has inconsistent dimensions")
    active = (support > 0.0) & (z-c*gap > 0.0)
    residual = np.where(active, c*gap, z)
    if not tangent:
        return residual, active, None, None
    q_block = np.zeros_like(gap_gradient)
    q_block[active] = c[active, None]*gap_gradient[active]
    z_diagonal = np.ones(len(gap))
    z_diagonal[active] = 0.0
    return residual, active, q_block, z_diagonal


def raw_certificate(manager, displacement, raw, projected):
    """Report the converged nodal-force work, not a projected re-evaluation."""
    source, target = manager._positions(displacement)
    source_count = len(manager.law.source_node_ids)
    physical = -np.asarray(raw.local_force).reshape(-1, 3)
    source_force = np.sum(physical[:source_count], axis=0)
    target_force = np.sum(physical[source_count:], axis=0)
    source_moment = np.sum(np.cross(source, physical[:source_count]), axis=0)
    target_moment = np.sum(np.cross(target, physical[source_count:]), axis=0)
    state = raw.state
    return replace(
        projected,
        integration_force=tuple(map(float, source_force)),
        target_force=tuple(map(float, target_force)),
        integration_moment=tuple(map(float, source_moment)),
        target_moment=tuple(map(float, target_moment)),
        active_pressure_dofs=int(np.count_nonzero(state.pressure > 0.0)),
        normalized_weighted_gap_m=tuple(map(float, state.normalized_gap)),
        numerical_pressure_pa=tuple(map(float, state.pressure)),
        reference_support_m2=tuple(map(float, state.reference_support)),
        energy_evaluations=raw.evaluations,
        pair_geometry_evaluations=raw.evaluations,
        augmented_merit_j=0.0,
        normal_multiplier_estimate_pa=tuple(map(float, manager.normal_multipliers)),
    )
