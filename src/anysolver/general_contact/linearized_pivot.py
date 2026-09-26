"""Disposable constrained gap responses for augmented shell pressure proposals.

These local linearizations propose algorithmic iterates. The coupled path must
re-equilibrate each proposal and apply its independent contact acceptance gates.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy import sparse

from anysolver.linalg import MatrixClass, factorize

from .augmentation import ActiveSetPivot, propose_active_set_pivot
from .overlap import PlanarFace
from .q4_source_overlap import projected_q4_source_face
from .supported_schur import SupportedSchurProposal, propose_supported_schur_step


def _projected_clip_signature(geometry, source, target) -> tuple[int, ...] | None:
    """Reject clipping edge changes hidden by equal polygon vertex counts."""
    if not hasattr(geometry, "source_face_indices"):
        return ()  # Analytical response controls have no face topology.
    signatures: list[int] = []
    for source_nodes in geometry.source_face_indices:
        source_positions = source[source_nodes]
        if len(source_positions) == 4:
            first, normal = projected_q4_source_face(source_positions)
        else:
            first = PlanarFace((1, 1), source_positions)
            normal = np.cross(first.corners[1]-first.corners[0],
                              first.corners[-1]-first.corners[0])
            normal /= np.linalg.norm(normal)
        tangent = first.corners[1]-first.corners[0]
        tangent /= np.linalg.norm(tangent)
        binormal = np.cross(normal, tangent)
        origin = first.corners[0]
        for target_nodes in geometry.target_face_indices:
            target_positions = target[target_nodes]
            projected = target_positions-((target_positions-origin) @ normal)[:, None]*normal
            second = PlanarFace((2, 1), projected)
            polygons = tuple(np.column_stack(((face.corners-origin) @ tangent,
                                              (face.corners-origin) @ binormal))
                             for face in (first, second))
            scale = max(float(np.max(np.linalg.norm(p-p[0], axis=1)))
                        for p in polygons)
            threshold = 1.0e-10*scale
            for vertices, edges in ((polygons[0], polygons[1]),
                                    (polygons[1], polygons[0])):
                for point in vertices:
                    for start, end in zip(edges, np.roll(edges, -1, axis=0)):
                        edge = end-start
                        along = float(np.dot(point-start, edge)/np.dot(edge, edge))
                        if along < -1.0e-10 or along > 1.0+1.0e-10:
                            signatures.append(0)  # Distant supporting-line extension.
                            continue
                        distance = (edge[0]*(point[1]-start[1])
                                    - edge[1]*(point[0]-start[0]))/np.linalg.norm(edge)
                        if abs(distance) <= threshold:
                            return None
                        signatures.append(1 if distance > 0.0 else -1)
    return tuple(signatures)


def _constrained_gap_response(manager, displacement, tangent, transform,
                              control_rows, selected: np.ndarray,
                              active: np.ndarray, *, difference_step: float,
                              check_cancel: Callable[[], None] | None = None
                              ) -> np.ndarray | None:
    """Return d(g_selected)/d(lambda_active) from one constrained factorization."""
    source, target = manager._positions(displacement)
    geometry = manager.law.geometry
    base = geometry.evaluate(source, target)
    clip_signature = _projected_clip_signature(geometry, source, target)
    if clip_signature is None:
        return None
    if np.any(base.reference_support[selected] <= 0.0):
        return None
    if not len(active):
        return np.zeros((len(selected), 0))
    coordinates = np.concatenate((source, target)).reshape(-1)
    count = len(coordinates)
    pair_count = len(getattr(geometry, "pair_laws", (1,)))
    if (2*count + 1)*pair_count > manager.settings.maximum_general_s3_energy_evaluations:
        raise ValueError("pressure response geometry evaluation budget exceeded")
    weighted = np.zeros((len(selected), count))
    support = np.zeros_like(weighted)
    source_count = len(source)
    for coordinate in range(count):
        if check_cancel is not None:
            check_cancel()
        shifted = coordinates.copy()
        shifted[coordinate] += difference_step
        plus = geometry.evaluate(
            shifted[:3*source_count].reshape(-1, 3),
            shifted[3*source_count:].reshape(-1, 3),
        )
        shifted[coordinate] -= 2*difference_step
        minus = geometry.evaluate(
            shifted[:3*source_count].reshape(-1, 3),
            shifted[3*source_count:].reshape(-1, 3),
        )
        plus_source = (coordinates.copy())
        plus_source[coordinate] += difference_step
        minus_source = (coordinates.copy())
        minus_source[coordinate] -= difference_step
        plus_clip = _projected_clip_signature(
            geometry, plus_source[:3*source_count].reshape(-1, 3),
            plus_source[3*source_count:].reshape(-1, 3),
        )
        minus_clip = _projected_clip_signature(
            geometry, minus_source[:3*source_count].reshape(-1, 3),
            minus_source[3*source_count:].reshape(-1, 3),
        )
        if (plus.overlap_signature != base.overlap_signature
                or minus.overlap_signature != base.overlap_signature
                or plus_clip != clip_signature
                or minus_clip != clip_signature
                or np.any(plus.reference_support[selected] <= 0.0)
                or np.any(minus.reference_support[selected] <= 0.0)):
            return None
        weighted[:, coordinate] = (
            plus.reference_weighted_gap[selected]
            - minus.reference_weighted_gap[selected]
        )/(2*difference_step)
        support[:, coordinate] = (
            plus.reference_support[selected]
            - minus.reference_support[selected]
        )/(2*difference_step)
    area = base.reference_support[selected, None]
    selected_gap = base.normalized_gap[selected]
    gap_derivative = (weighted-selected_gap[:, None]*support)/area
    active_positions = np.searchsorted(selected, active)
    if np.any(selected[active_positions] != active):
        raise ValueError("active pressure mode lacks positive reference support")
    gap_variation_active = (
        weighted[active_positions]
        - selected_gap[active_positions, None]*support[active_positions]
    )
    variations = manager.map @ transform
    # Contact residual is -sum_i p_i(dW_i-g_i dS_i); held-multiplier
    # coupling therefore contains the moving-support term.
    force_derivative = -np.asarray(variations.T @ gap_variation_active.T)
    gap_reduced = np.asarray(variations.T @ gap_derivative.T).T
    reduced_tangent = (transform.T @ tangent @ transform).tocsr()
    rows = np.asarray(control_rows, dtype=float)
    matrix = sparse.bmat([
        [reduced_tangent, sparse.csr_matrix(-rows.T)],
        [sparse.csr_matrix(rows),
         sparse.csr_matrix((len(rows), len(rows)))],
    ], format="csr")
    right = np.vstack((-force_derivative,
                       np.zeros((len(rows), len(active)))))
    factor = factorize(matrix, MatrixClass.GENERAL,
                       signature="contact_path:pressure_response")
    response = np.column_stack([
        np.asarray(factor.solve(right[:, column])).reshape(-1)[:transform.shape[1]]
        for column in range(len(active))
    ])
    schur = gap_reduced @ response
    return schur if np.all(np.isfinite(schur)) else None


def refined_patch_pivot(manager, displacement, tangent, transform, control_rows,
                        *, difference_step: float, maximum_pressure: float,
                        pressure_tolerance: float,
                        check_cancel: Callable[[], None] | None = None,
                        ) -> ActiveSetPivot | None:
    """Preserve the historical two-to-four-active-mode pivot route."""
    source, target = manager._positions(displacement)
    pressure = manager.normal_multipliers
    state = manager.law.evaluate(source, target, pressure)
    active = np.flatnonzero(state.pressure > 0.0)
    if not 2 <= len(active) <= 4:
        return None
    schur = _constrained_gap_response(
        manager, displacement, tangent, transform, control_rows,
        active, active, difference_step=difference_step,
        check_cancel=check_cancel,
    )
    if schur is None:
        return None
    return propose_active_set_pivot(
        pressure, state.normalized_gap, active, schur,
        maximum_pressure=maximum_pressure,
        gap_consistency=pressure_tolerance/manager.stiffness,
    )


def refined_patch_supported_schur(
    manager, displacement, tangent, transform, control_rows, *,
    difference_step: float, maximum_pressure: float,
    maximum_pressure_step: float, maximum_modes: int,
    check_cancel: Callable[[], None] | None = None,
    diagnostics: dict[str, object] | None = None,
) -> SupportedSchurProposal | None:
    """Propose a bounded projected-root correction for every supported mode."""
    source, target = manager._positions(displacement)
    pressure = manager.normal_multipliers
    state = manager.law.evaluate(source, target, pressure)
    supported = state.reference_support > 0.0
    selected = np.flatnonzero(supported)
    if len(selected) > maximum_modes:
        raise MemoryError("supported pressure modes exceed the declared Schur cap")
    active = np.flatnonzero(state.pressure > 0.0)
    if not len(active):
        if diagnostics is not None:
            diagnostics["schur_ineligible"] = "no_active_pressure_modes"
        return None
    response_active = _constrained_gap_response(
        manager, displacement, tangent, transform, control_rows,
        selected, active, difference_step=difference_step,
        check_cancel=check_cancel,
    )
    if response_active is None:
        if diagnostics is not None:
            diagnostics["schur_ineligible"] = "projection_branch_or_nonfinite_response"
        return None
    response = np.zeros((len(selected), len(selected)))
    response[:, np.searchsorted(selected, active)] = response_active
    return propose_supported_schur_step(
        pressure, state.normalized_gap, supported, response,
        normal_stiffness=manager.stiffness,
        maximum_pressure=maximum_pressure,
        maximum_pressure_step=maximum_pressure_step,
        maximum_modes=maximum_modes,
        diagnostics=diagnostics,
    )
