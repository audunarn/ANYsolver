"""Descriptor-system utilities for declared massless element coordinates.

Qualified shell formulations may retain numerical coordinates with stiffness
and exactly zero inertia.  Their finite free-vibration spectrum is obtained
without invented mass.  Small systems use the swapped symmetric pencil

    M x = mu (K + sigma M) x,

where ``mu = 1 / (lambda + sigma)`` for every finite eigenvalue of
``K x = lambda M x``.  Pure algebraic modes have ``mu = 0`` and therefore do
not enter the requested largest-``mu`` spectrum.  Large systems apply the
equivalent original-pencilled operator ``(K - sigma M)^-1 M`` so SciPy is not
asked to treat singular ``M`` as a positive-definite generalized metric.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import warnings
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as sparse_linalg

from .linalg import FactorizationCache, MatrixClass, factorize_cached

if TYPE_CHECKING:
    from .fe_core import FEModel


DESCRIPTOR_MODAL_POLICY_ID = "SWAPPED_MASSLESS_ALGEBRAIC_PENCIL_V1"
DESCRIPTOR_SHIFT_RATIO = 1.0e-6
DESCRIPTOR_COORDINATE_SHEAR_LIMIT = 256.0
DESCRIPTOR_DENSE_CONDENSATION_LIMIT = 512


class AlgebraicDynamicsError(ValueError):
    """Raised when a declared descriptor system cannot be safely reduced."""


@dataclass(frozen=True)
class DescriptorSpectrum:
    """Finite candidates recovered from the massless descriptor pencil."""

    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    diagnostics: Dict[str, Any]


@dataclass(frozen=True)
class DeclaredAlgebraicBasis:
    """Constraint-compatible assembled basis for declared mass-null modes."""

    full_basis: sparse.csr_matrix
    reduced_basis: sparse.csr_matrix
    diagnostics: Dict[str, Any]


def declared_algebraic_mass_elements(model: "FEModel") -> Tuple[int, ...]:
    """Return stable IDs of elements declaring exact massless coordinates."""

    declared = []
    for element_id, element in sorted(model.mesh.elements.items()):
        try:
            raw = getattr(element, "dynamic_algebraic_nullity", 0)
            value = int(raw)
        except Exception as error:
            raise AlgebraicDynamicsError(
                f"element {int(element_id)} has an invalid algebraic nullity declaration"
            ) from error
        if isinstance(raw, bool) or value < 0 or value != raw:
            raise AlgebraicDynamicsError(
                f"element {int(element_id)} has an invalid algebraic nullity declaration"
            )
        if value > 0:
            declared.append(int(element_id))
    return tuple(declared)


def uses_declared_algebraic_mass(model: "FEModel") -> bool:
    """Return whether the model requires descriptor modal handling."""

    return bool(declared_algebraic_mass_elements(model))


def _canonical_unit_direction(value: np.ndarray) -> np.ndarray:
    direction = np.asarray(value, dtype=float).reshape(3)
    norm = float(np.linalg.norm(direction))
    if not np.isfinite(norm) or norm <= 0.0:
        raise AlgebraicDynamicsError("declared algebraic direction is not finite and nonzero")
    direction = direction / norm
    significant = np.flatnonzero(np.abs(direction) > 1.0e-14)
    if significant.size and direction[int(significant[0])] < 0.0:
        direction = -direction
    return direction


def _local_declarations(
    model: "FEModel", declared_ids: Tuple[int, ...]
) -> tuple[list[Dict[str, Any]], dict[int, list[np.ndarray]]]:
    records: list[Dict[str, Any]] = []
    by_node: dict[int, list[np.ndarray]] = {}
    for element_id in declared_ids:
        element = model.mesh.elements[element_id]
        expected = int(getattr(element, "dynamic_algebraic_nullity", 0))
        getter = getattr(element, "dynamic_algebraic_directions", None)
        if getter is None:
            raise AlgebraicDynamicsError(
                f"element {element_id} declares algebraic mass without directions"
            )
        material = model.get_material(element.material_name)
        directions = np.asarray(getter(model.mesh, material), dtype=float)
        dof_mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        dof_count = len(dof_mapping)
        if directions.shape != (dof_count, expected):
            raise AlgebraicDynamicsError(
                f"element {element_id} algebraic direction shape {directions.shape} "
                f"does not match {(dof_count, expected)}"
            )
        gram = directions.T @ directions
        if not np.allclose(gram, np.eye(expected), rtol=0.0, atol=2.0e-13):
            raise AlgebraicDynamicsError(
                f"element {element_id} algebraic directions are not orthonormal"
            )
        components_getter = getattr(element, "compute_mass_components", None)
        if components_getter is None:
            raise AlgebraicDynamicsError(
                f"element {element_id} has no auditable mass components"
            )
        components = components_getter(model.mesh, material)
        mass = np.asarray(components["global"], dtype=float)
        if mass.shape != (dof_count, dof_count):
            raise AlgebraicDynamicsError(
                f"element {element_id} returned an incompatible mass matrix"
            )
        if float(components.get("mass_per_area", 0.0)) <= 0.0 or float(
            components.get("rotary_inertia_per_area", 0.0)
        ) <= 0.0:
            raise AlgebraicDynamicsError(
                f"element {element_id} descriptor modal analysis requires positive "
                "areal mass and rotary inertia"
            )
        witness = str(getattr(element, "dynamic_algebraic_mass_witness", ""))
        zero_indices = tuple(
            int(value)
            for value in getattr(
                element, "dynamic_algebraic_local_zero_indices", ()
            )
        )
        local_mass = np.asarray(components.get("condensed_local"), dtype=float)
        if (
            witness != "S3_LOCAL_DRILL_ROWS_EXACT_ZERO_V1"
            or zero_indices != tuple(6 * index + 5 for index in range(expected))
            or local_mass.shape != (dof_count, dof_count)
            or components.get("zero_drill_inertia") is not True
            or np.any(local_mass[np.asarray(zero_indices, dtype=np.intp), :] != 0.0)
            or np.any(local_mass[:, np.asarray(zero_indices, dtype=np.intp)] != 0.0)
        ):
            raise AlgebraicDynamicsError(
                f"element {element_id} lacks an exact local zero-inertia witness"
            )
        residual = float(
            np.linalg.norm(mass @ directions, ord=np.inf)
            / max(float(np.linalg.norm(mass, ord=np.inf)), np.finfo(float).tiny)
        )
        if residual > 2.0e-12:
            raise AlgebraicDynamicsError(
                f"element {element_id} advertised directions carry nonzero inertia"
            )
        full_rank = int(components.get("condensed_rank", -1))
        if full_rank != dof_count - expected:
            raise AlgebraicDynamicsError(
                f"element {element_id} mass rank {full_rank} does not match declared "
                f"nullity {expected}"
            )
        node_ids = tuple(int(node_id) for node_id in getattr(element, "node_ids", ()))
        if expected != len(node_ids) or dof_count != 6 * len(node_ids):
            raise AlgebraicDynamicsError(
                f"element {element_id} algebraic directions are not one-per-node shell drills"
            )
        for column, node_id in enumerate(node_ids):
            allowed = np.arange(6 * column + 3, 6 * column + 6, dtype=np.intp)
            outside = np.ones(dof_count, dtype=bool)
            outside[allowed] = False
            if float(np.linalg.norm(directions[outside, column])) > 2.0e-13:
                raise AlgebraicDynamicsError(
                    f"element {element_id} algebraic direction {column} is not node-local"
                )
            node = model.mesh.get_node(node_id)
            if node is None:
                raise AlgebraicDynamicsError(
                    f"element {element_id} algebraic direction references missing node {node_id}"
                )
            expected_dofs = np.asarray(node.dofs[3:6], dtype=np.intp)
            if not np.array_equal(dof_mapping[allowed], expected_dofs):
                raise AlgebraicDynamicsError(
                    f"element {element_id} algebraic direction ordering is incompatible"
                )
            by_node.setdefault(node_id, []).append(
                _canonical_unit_direction(directions[allowed, column])
            )
        records.append(
            {
                "element_id": int(element_id),
                "formulation_id": str(getattr(element, "formulation_id", "")),
                "declared_nullity": expected,
                "mass_rank": full_rank,
                "null_residual": residual,
                "policy": str(getattr(element, "dynamic_algebraic_policy", "")),
            }
        )
    return records, by_node


def _nondeclared_incident_mass_action(
    model: "FEModel",
    node_id: int,
    direction: np.ndarray,
    declared_ids: set[int],
    incident_elements: tuple[tuple[int, Any], ...],
    mass_cache: dict[int, tuple[np.ndarray, np.ndarray]],
) -> tuple[bool, list[int]]:
    """Return whether an undeclared incident element gives a drill finite mass.

    Declared S3 null directions are trusted through their formulation contract;
    their transformed floating matrices can contain roundoff-sized entries.
    Every other incident element is structural counter-evidence: any nonzero
    computed action, however small, makes the candidate a finite-inertia mode.
    This deliberately avoids a magnitude threshold that could erase a very
    high but finite physical frequency.
    """

    node = model.mesh.get_node(int(node_id))
    if node is None:
        raise AlgebraicDynamicsError(
            f"declared algebraic direction references missing node {int(node_id)}"
        )
    rotational_dofs = np.asarray(node.dofs[3:6], dtype=np.intp)
    carrying: list[int] = []
    for element_id, element in incident_elements:
        made_id = int(element_id)
        if made_id in declared_ids:
            continue
        cached = mass_cache.get(made_id)
        if cached is None:
            material = model.get_material(element.material_name)
            mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
            try:
                local_mass = np.asarray(
                    element.compute_mass_matrix(model.mesh, material), dtype=float
                )
            except Exception as error:
                raise AlgebraicDynamicsError(
                    f"could not audit incident mass for element {made_id}"
                ) from error
            if local_mass.shape != (mapping.size, mapping.size) or np.any(
                ~np.isfinite(local_mass)
            ):
                raise AlgebraicDynamicsError(
                    f"element {made_id} returned an incompatible incident mass matrix"
                )
            mass_cache[made_id] = (mapping, local_mass)
        else:
            mapping, local_mass = cached
        trial = np.zeros(mapping.size, dtype=float)
        for global_dof, component in zip(rotational_dofs, direction):
            positions = np.flatnonzero(mapping == int(global_dof))
            if positions.size != 1:
                raise AlgebraicDynamicsError(
                    f"element {made_id} has an incompatible nodal rotation mapping"
                )
            trial[int(positions[0])] = float(component)
        action = local_mass @ trial
        if np.any(~np.isfinite(action)):
            raise AlgebraicDynamicsError(
                f"element {made_id} returned a non-finite incident mass action"
            )
        if np.any(action != 0.0):
            carrying.append(made_id)
    return bool(carrying), carrying


def _sparse_nullspace_basis(
    matrix: sparse.spmatrix, *, tolerance: float = 2.0e-12
) -> sparse.csr_matrix:
    """Return a deterministic sparse RREF nullspace basis."""

    made = sparse.csr_matrix(matrix, dtype=float)
    column_count = int(made.shape[1])
    if column_count == 0:
        return sparse.csr_matrix((0, 0), dtype=float)
    rows: list[dict[int, float]] = []
    for row_index in range(made.shape[0]):
        start, stop = int(made.indptr[row_index]), int(made.indptr[row_index + 1])
        row = {
            int(column): float(value)
            for column, value in zip(made.indices[start:stop], made.data[start:stop])
            if float(value) != 0.0
        }
        if row:
            scale = max(abs(value) for value in row.values())
            normalized = {
                column: value / scale for column, value in row.items()
            }
            if any(0.0 < abs(value) <= tolerance for value in normalized.values()):
                raise AlgebraicDynamicsError(
                    "constraint intersection contains an ambiguous nonzero coefficient"
                )
            row = {
                column: value
                for column, value in normalized.items()
                if value != 0.0
            }
        if row:
            rows.append(row)

    active = set(range(len(rows)))
    pivots: dict[int, int] = {}
    versions = [0 for _row in rows]
    column_rows: dict[int, set[int]] = {}
    for index, row in enumerate(rows):
        for column in row:
            column_rows.setdefault(column, set()).add(index)
    queue: list[tuple[float, int, int, int, int]] = []

    def _queue_row(index: int) -> None:
        row = rows[index]
        if not row:
            return
        column = min(row, key=lambda candidate: (-abs(row[candidate]), candidate))
        heapq.heappush(
            queue,
            (-abs(row[column]), len(row), column, index, versions[index]),
        )

    for index in sorted(active):
        _queue_row(index)
    while active:
        selected = -1
        column = -1
        while queue:
            _negative_magnitude, _fill, candidate, index, version = heapq.heappop(
                queue
            )
            if index in active and version == versions[index] and rows[index]:
                selected = index
                column = candidate
                break
        if selected < 0:
            break
        pivot_row = rows[selected]
        pivot_value = pivot_row[column]
        pivot_row = {
            key: value / pivot_value for key, value in pivot_row.items()
        }
        if any(not np.isfinite(value) for value in pivot_row.values()):
            raise AlgebraicDynamicsError(
                "constraint intersection elimination produced a non-finite pivot"
            )
        rows[selected] = pivot_row
        active.remove(selected)
        affected = sorted(column_rows.get(column, set()) - {selected})
        for index in affected:
            row = rows[index]
            factor = row.get(column, 0.0)
            if factor == 0.0:
                continue
            for key in row:
                column_rows.get(key, set()).discard(index)
            updated = dict(row)
            for key, value in pivot_row.items():
                updated[key] = updated.get(key, 0.0) - factor * value
            scale = max((abs(value) for value in updated.values()), default=0.0)
            if not np.isfinite(scale):
                raise AlgebraicDynamicsError(
                    "constraint intersection elimination produced a non-finite row"
                )
            if scale <= 0.0:
                rows[index] = {}
            elif index in active:
                rows[index] = {
                    key: value / scale
                    for key, value in updated.items()
                    if value != 0.0
                }
            else:
                rows[index] = {
                    key: value for key, value in updated.items() if value != 0.0
                }
            for key in rows[index]:
                column_rows.setdefault(key, set()).add(index)
            versions[index] += 1
            if index in active:
                _queue_row(index)
        pivots[column] = selected

    free = [column for column in range(column_count) if column not in pivots]
    if not free:
        return sparse.csr_matrix((column_count, 0), dtype=float)
    free_index = {column: index for index, column in enumerate(free)}
    output_rows: list[int] = []
    output_columns: list[int] = []
    output_data: list[float] = []
    for column, index in free_index.items():
        output_rows.append(column)
        output_columns.append(index)
        output_data.append(1.0)
    for pivot, row_index in pivots.items():
        row = rows[row_index]
        for column, index in free_index.items():
            coefficient = -float(row.get(column, 0.0))
            if coefficient != 0.0:
                output_rows.append(pivot)
                output_columns.append(index)
                output_data.append(coefficient)
    basis = sparse.csr_matrix(
        (output_data, (output_rows, output_columns)),
        shape=(column_count, len(free)),
        dtype=float,
    )
    residual = made @ basis
    relative = float(
        sparse_linalg.norm(residual)
        / max(sparse_linalg.norm(made) * sparse_linalg.norm(basis), 1.0)
    )
    if not np.isfinite(relative) or relative > 2.0e-10:
        raise AlgebraicDynamicsError("constraint intersection nullspace residual is too large")
    return basis


def build_declared_algebraic_basis(
    model: "FEModel",
    full_mass: sparse.spmatrix,
    reduced_mass: sparse.spmatrix,
    transformation: sparse.spmatrix,
    independent_dofs: np.ndarray,
    *,
    dense_size_limit: int,
) -> DeclaredAlgebraicBasis:
    """Build and prove the complete compatible assembled mass-null basis."""

    declared_ids = declared_algebraic_mass_elements(model)
    records, by_node = _local_declarations(model, declared_ids)
    full_mass = _symmetric(full_mass)
    total_dofs = int(full_mass.shape[0])
    candidate_nodes: list[int] = []
    candidate_directions: list[np.ndarray] = []
    noncoplanar_nodes: list[int] = []
    mass_removed_nodes: list[int] = []
    mass_carrying_incident_elements: dict[str, list[int]] = {}
    declared_set = set(declared_ids)
    incident_by_node: dict[int, list[tuple[int, Any]]] = {}
    incident_mass_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for element_id, element in sorted(model.mesh.elements.items()):
        for node_id in getattr(element, "node_ids", ()):
            incident_by_node.setdefault(int(node_id), []).append(
                (int(element_id), element)
            )
    for node_id in sorted(by_node):
        directions = by_node[node_id]
        reference = directions[0]
        aligned = []
        compatible = True
        for direction in directions:
            dot = float(reference @ direction)
            signed = direction if dot >= 0.0 else -direction
            coplanar_roundoff = 256.0 * np.finfo(float).eps
            if float(np.linalg.norm(reference - signed)) > coplanar_roundoff:
                compatible = False
                break
            # Collapse roundoff-equivalent normals to the first authoritative
            # direction so independently normalized coplanar facets share one
            # structural algebraic coordinate.
            aligned.append(reference)
        if not compatible:
            noncoplanar_nodes.append(int(node_id))
            continue
        direction = _canonical_unit_direction(np.sum(aligned, axis=0))
        carries_mass, carrying_ids = _nondeclared_incident_mass_action(
            model,
            int(node_id),
            direction,
            declared_set,
            tuple(incident_by_node.get(int(node_id), ())),
            incident_mass_cache,
        )
        if carries_mass:
            mass_removed_nodes.append(int(node_id))
            mass_carrying_incident_elements[str(int(node_id))] = carrying_ids
            continue
        candidate_nodes.append(int(node_id))
        candidate_directions.append(direction)

    rows: list[int] = []
    columns: list[int] = []
    data: list[float] = []
    for column, (node_id, direction) in enumerate(
        zip(candidate_nodes, candidate_directions)
    ):
        node = model.mesh.get_node(node_id)
        assert node is not None
        for dof, value in zip(node.dofs[3:6], direction):
            if value != 0.0:
                rows.append(int(dof))
                columns.append(column)
                data.append(float(value))
    node_basis = sparse.csr_matrix(
        (data, (rows, columns)),
        shape=(total_dofs, len(candidate_nodes)),
        dtype=float,
    )
    independent = np.asarray(independent_dofs, dtype=np.intp)
    reduced_seed = node_basis[independent, :].tocsr()
    compatible_residual = (
        sparse.csr_matrix(transformation) @ reduced_seed - node_basis
    ).tocsr()
    coefficient_basis = _sparse_nullspace_basis(compatible_residual)
    full_basis = (node_basis @ coefficient_basis).tocsr()
    reduced_basis = (reduced_seed @ coefficient_basis).tocsr()
    if reduced_basis.shape[1]:
        norms = np.sqrt(np.asarray(reduced_basis.power(2).sum(axis=0)).reshape(-1))
        if np.any(~np.isfinite(norms)) or np.any(norms <= 0.0):
            raise AlgebraicDynamicsError("compatible algebraic basis is rank deficient")
        scaling = sparse.diags(1.0 / norms, format="csr")
        reduced_basis = (reduced_basis @ scaling).tocsr()
        full_basis = (full_basis @ scaling).tocsr()

    transform_error = sparse.csr_matrix(transformation) @ reduced_basis - full_basis
    transform_relative = float(
        sparse_linalg.norm(transform_error)
        / max(sparse_linalg.norm(full_basis), 1.0)
    )
    mass_action = sparse.csr_matrix(reduced_mass) @ reduced_basis
    mass_relative = float(
        sparse_linalg.norm(mass_action)
        / max(
            sparse_linalg.norm(reduced_mass) * max(sparse_linalg.norm(reduced_basis), 1.0),
            np.finfo(float).tiny,
        )
    )
    if transform_relative > 2.0e-11 or mass_relative > 2.0e-11:
        raise AlgebraicDynamicsError("declared assembled algebraic basis failed validation")

    mass_scale = max(float(sparse_linalg.norm(reduced_mass)), np.finfo(float).tiny)
    augmented_mass = _symmetric(
        sparse.csr_matrix(reduced_mass)
        + mass_scale * (reduced_basis @ reduced_basis.T)
    )
    minimum, spd_method = _certify_spd(
        augmented_mass,
        dense_size_limit=dense_size_limit,
        label="mass plus declared algebraic projector",
    )
    diagnostics = {
        "element_count": len(records),
        "declared_element_ids": list(declared_ids),
        "declared_local_nullity": int(
            sum(record["declared_nullity"] for record in records)
        ),
        "candidate_node_count": len(candidate_nodes),
        "candidate_node_ids": candidate_nodes,
        "noncoplanar_node_ids": noncoplanar_nodes,
        "mass_removed_node_ids": mass_removed_nodes,
        "mass_carrying_incident_elements": mass_carrying_incident_elements,
        "compatible_global_nullity": int(reduced_basis.shape[1]),
        "constraint_intersection_residual": transform_relative,
        "mass_null_residual": mass_relative,
        "augmented_mass_minimum_eigenvalue": minimum,
        "augmented_mass_spd_method": spd_method,
        "elements": records,
    }
    return DeclaredAlgebraicBasis(full_basis, reduced_basis, diagnostics)


def _symmetric(matrix: sparse.spmatrix) -> sparse.csr_matrix:
    return (0.5 * (matrix + matrix.T)).tocsr()


def _descriptor_shift(
    K: sparse.spmatrix,
    M: sparse.spmatrix,
    algebraic_basis: Optional[sparse.spmatrix] = None,
) -> tuple[float, Dict[str, float]]:
    stiffness_norm = float(sparse_linalg.norm(K))
    mass_norm = float(sparse_linalg.norm(M))
    if not np.isfinite(stiffness_norm) or not np.isfinite(mass_norm):
        raise AlgebraicDynamicsError("descriptor matrices must be finite")
    if mass_norm <= 0.0:
        raise AlgebraicDynamicsError("descriptor modal analysis requires non-zero mass")
    mass_square = float(M.multiply(M).sum())
    stiffness_mass_inner = float(K.multiply(M).sum())
    raw_scale = (
        abs(stiffness_mass_inner) / mass_square
        if np.isfinite(mass_square) and mass_square > 0.0
        else 1.0
    )
    scale = raw_scale
    scale_method = "stiffness_mass_frobenius_inner_product"
    static_correction_ratio = 0.0
    basis = (
        None
        if algebraic_basis is None
        else sparse.csc_matrix(algebraic_basis, dtype=float)
    )
    if basis is not None and basis.shape[1]:
        gram = (basis.T @ basis).tocsc()
        algebraic_stiffness = (basis.T @ K @ basis).tocsc()
        try:
            gram_factor = sparse_linalg.splu(gram)
        except Exception as error:
            raise AlgebraicDynamicsError(
                "declared assembled algebraic basis Gram matrix is not positive definite"
            ) from error
        try:
            stiffness_factor = sparse_linalg.splu(algebraic_stiffness)
        except Exception as error:
            raise AlgebraicDynamicsError(
                "algebraic stiffness block is not positive definite"
            ) from error
        sample_count = min(8, max(1, K.shape[0] - basis.shape[1]))
        trials = _deterministic_block(int(K.shape[0]), sample_count)
        gram_coefficients = gram_factor.solve(
            np.asarray(basis.T @ trials, dtype=float)
        )
        complement = trials - np.asarray(basis @ gram_coefficients, dtype=float)
        algebraic_rhs = np.asarray(basis.T @ (K @ complement), dtype=float)
        corrections = stiffness_factor.solve(algebraic_rhs)
        static_correction = np.asarray(basis @ corrections, dtype=float)
        equilibrated = complement - static_correction
        static_correction_ratio = float(
            np.linalg.norm(static_correction)
            / max(np.linalg.norm(complement), np.finfo(float).tiny)
        )
        quotients: list[float] = []
        for vector in equilibrated.T:
            made = np.asarray(vector, dtype=float).reshape(-1)
            modal_mass = float(made @ (M @ made))
            modal_stiffness = float(made @ (K @ made))
            if (
                np.isfinite(modal_mass)
                and np.isfinite(modal_stiffness)
                and modal_mass > 0.0
            ):
                quotients.append(abs(modal_stiffness / modal_mass))
        if not quotients:
            raise AlgebraicDynamicsError(
                "could not determine a mass-carrying descriptor scale"
            )
        scale = float(np.median(np.asarray(quotients, dtype=float)))
        scale_method = "algebraic_equilibrated_deterministic_rayleigh_median"
    if not np.isfinite(scale) or scale <= 0.0:
        scale = 1.0
    shift = max(scale * DESCRIPTOR_SHIFT_RATIO, np.finfo(float).tiny)
    return float(shift), {
        "stiffness_frobenius_norm": stiffness_norm,
        "mass_frobenius_norm": mass_norm,
        "mass_frobenius_norm_squared": mass_square,
        "stiffness_mass_frobenius_inner_product": stiffness_mass_inner,
        "unprojected_stiffness_mass_scale": float(raw_scale),
        "stiffness_mass_scale": float(scale),
        "stiffness_mass_scale_method": scale_method,
        "algebraic_static_correction_ratio": static_correction_ratio,
    }


def _deterministic_start(size: int) -> np.ndarray:
    if size <= 0:
        return np.zeros(0, dtype=float)
    vector = 1.0 + np.arange(size, dtype=float) / max(size, 1)
    return vector / np.linalg.norm(vector)


def _deterministic_block(size: int, columns: int) -> np.ndarray:
    """Return a deterministic full-rank block for repeated eigenspaces."""

    if size <= 0 or columns <= 0 or columns > size:
        raise AlgebraicDynamicsError("descriptor block start has invalid dimensions")
    rows = np.arange(1, size + 1, dtype=float)[:, None]
    modes = np.arange(1, columns + 1, dtype=float)[None, :]
    trial = (
        np.sin(np.sqrt(2.0) * rows * modes)
        + np.cos(np.sqrt(3.0) * rows * (modes + 0.5))
    )
    basis, _upper = np.linalg.qr(trial, mode="reduced")
    if basis.shape != (size, columns) or np.any(~np.isfinite(basis)):
        raise AlgebraicDynamicsError("descriptor block start is rank deficient")
    return np.asarray(basis, dtype=float)


def _certify_spd(
    matrix: sparse.spmatrix,
    *,
    dense_size_limit: int,
    label: str,
) -> tuple[float, str]:
    made = _symmetric(matrix)
    size = int(made.shape[0])
    if size == 0:
        return float("inf"), "empty"
    if size <= int(dense_size_limit):
        dense = np.asarray(made.toarray(), dtype=float)
        diagonal = np.asarray(np.diag(dense), dtype=float)
        if np.any(~np.isfinite(diagonal)) or np.any(diagonal <= 0.0):
            raise AlgebraicDynamicsError(f"{label} is not positive definite")
        inverse_root = 1.0 / np.sqrt(diagonal)
        dense = inverse_root[:, None] * dense * inverse_root[None, :]
        dense = 0.5 * (dense + dense.T)
        try:
            linalg.cholesky(dense, lower=True, check_finite=True)
        except Exception as error:
            raise AlgebraicDynamicsError(f"{label} is not positive definite") from error
        minimum = float(linalg.eigvalsh(dense, subset_by_index=(0, 0))[0])
        minimum_floor = float(
            4096.0
            * np.finfo(float).eps
            * max(np.sqrt(float(size)), 1.0)
        )
        if not np.isfinite(minimum) or minimum <= minimum_floor:
            raise AlgebraicDynamicsError(f"{label} is not positive definite")
        return minimum, "dense_scaled_cholesky_and_smallest_eigenvalue"
    diagonal = np.asarray(made.diagonal(), dtype=float).reshape(-1)
    if np.any(~np.isfinite(diagonal)) or np.any(diagonal <= 0.0):
        raise AlgebraicDynamicsError(f"{label} is not positive definite")
    scaling = sparse.diags(1.0 / np.sqrt(diagonal), format="csc")
    balanced = _symmetric(scaling @ made @ scaling).tocsc()
    try:
        decomposition = sparse_linalg.splu(
            balanced,
            permc_spec="MMD_AT_PLUS_A",
            diag_pivot_thresh=0.0,
            options={"SymmetricMode": True, "Equil": False},
        )
    except Exception as error:
        raise AlgebraicDynamicsError(f"{label} is not positive definite") from error
    row_permutation = np.asarray(decomposition.perm_r, dtype=np.intp)
    column_permutation = np.asarray(decomposition.perm_c, dtype=np.intp)
    if not np.array_equal(row_permutation, column_permutation):
        raise AlgebraicDynamicsError(
            f"could not certify positive definiteness of {label} without pivoting"
        )
    pivots = np.asarray(decomposition.U.diagonal(), dtype=float).reshape(-1)
    pivot_floor = float(
        4096.0
        * np.finfo(float).eps
        * max(np.sqrt(float(size)), 1.0)
    )
    if np.any(~np.isfinite(pivots)) or np.any(pivots <= pivot_floor):
        raise AlgebraicDynamicsError(f"{label} is not positive definite")

    lower = sparse.csr_matrix(decomposition.L)
    upper = sparse.csr_matrix(decomposition.U)
    diagonal_factor = sparse.diags(pivots, format="csr")
    ldl_error = upper - diagonal_factor @ lower.T
    ldl_relative = float(
        sparse_linalg.norm(ldl_error)
        / max(sparse_linalg.norm(upper), np.finfo(float).tiny)
    )
    inverse_permutation = np.argsort(row_permutation)
    permuted = balanced[inverse_permutation, :][:, inverse_permutation]
    factor_error = lower @ upper - permuted
    factor_relative = float(
        sparse_linalg.norm(factor_error)
        / max(sparse_linalg.norm(permuted), np.finfo(float).tiny)
    )
    if (
        not np.isfinite(ldl_relative)
        or not np.isfinite(factor_relative)
        or ldl_relative > 2.0e-10
        or factor_relative > 2.0e-10
    ):
        raise AlgebraicDynamicsError(
            f"could not certify symmetric LDL reconstruction of {label}"
        )
    inverse = sparse_linalg.LinearOperator(
        balanced.shape,
        matvec=lambda value: np.asarray(decomposition.solve(value), dtype=float),
        matmat=lambda value: np.asarray(decomposition.solve(value), dtype=float),
        dtype=float,
    )
    try:
        near_values, near_vectors = sparse_linalg.eigsh(
            balanced,
            k=1,
            sigma=0.0,
            which="LM",
            OPinv=inverse,
            v0=_deterministic_start(size),
            tol=2.0e-12,
            maxiter=max(1000, 20 * size),
        )
    except Exception as error:
        raise AlgebraicDynamicsError(
            f"could not certify the smallest eigenvalue of {label}"
        ) from error
    smallest = float(near_values[0])
    vector = np.asarray(near_vectors[:, 0], dtype=float)
    spectral_residual = float(
        np.linalg.norm(np.asarray(balanced @ vector) - smallest * vector)
    )
    certified_lower = smallest - spectral_residual
    if (
        not np.isfinite(certified_lower)
        or certified_lower <= pivot_floor
    ):
        raise AlgebraicDynamicsError(f"{label} is not positive definite")
    return certified_lower, "sparse_scaled_ldl_and_shift_invert_lower_bound"


def _rayleigh_values(
    K: sparse.spmatrix,
    M: sparse.spmatrix,
    swapped_values: np.ndarray,
    vectors: np.ndarray,
    *,
    algebraic_nullity: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    values = np.asarray(swapped_values, dtype=float).reshape(-1)
    modes = np.asarray(vectors, dtype=float)
    if modes.ndim != 2 or modes.shape[1] != values.size:
        raise AlgebraicDynamicsError("descriptor eigensolver returned incompatible vectors")
    nullity = int(algebraic_nullity)
    if nullity < 0 or nullity > values.size:
        raise AlgebraicDynamicsError("declared assembled algebraic nullity is incompatible")
    order = np.argsort(values)[::-1]
    values = values[order]
    modes = modes[:, order]
    retained = values.size - nullity
    values = values[:retained]
    modes = modes[:, :retained]
    finite_values = []
    finite_vectors = []
    excluded = nullity
    for swapped, vector in zip(values, modes.T):
        if not np.isfinite(swapped) or swapped <= 0.0:
            raise AlgebraicDynamicsError(
                "finite descriptor candidate is not positive in the swapped pencil"
            )
        made = np.asarray(vector, dtype=float).reshape(-1)
        mass = float(made @ (M @ made))
        if not np.isfinite(mass) or mass <= 0.0:
            raise AlgebraicDynamicsError("finite descriptor candidate has non-positive mass")
        stiffness = float(made @ (K @ made))
        finite_values.append(stiffness / mass)
        # The swapped solver normalizes in ``K + sigma M``.  High-frequency
        # physical candidates can consequently carry a very small raw modal
        # mass and would be mistaken for algebraic modes by downstream guards.
        # Return unit-M candidates while retaining the Rayleigh value above.
        finite_vectors.append(made / np.sqrt(mass))
    if not finite_vectors:
        return np.zeros(0), np.zeros((modes.shape[0], 0)), excluded
    return (
        np.asarray(finite_values, dtype=float),
        np.column_stack(finite_vectors),
        excluded,
    )


def _validate_physical_candidates(
    K: sparse.spmatrix,
    M: sparse.spmatrix,
    eigenvalues: np.ndarray,
    vectors: np.ndarray,
    *,
    stiffness_mass_scale: float,
    descriptor_shift: float,
    transformed_values: Optional[np.ndarray] = None,
    preserve_input_eigenvalues: bool = False,
) -> tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """Certify residuals, signs, transformed values, and M orthogonality."""

    values = np.asarray(eigenvalues, dtype=float).reshape(-1)
    modes = np.asarray(vectors, dtype=float)
    if modes.ndim != 2 or modes.shape[1] != values.size:
        raise AlgebraicDynamicsError("descriptor candidates have incompatible shapes")
    swapped = None
    if transformed_values is not None:
        swapped = np.asarray(transformed_values, dtype=float).reshape(-1)
        if swapped.size != values.size:
            raise AlgebraicDynamicsError(
                "descriptor transformed candidates have incompatible shapes"
            )
    certified_values: list[float] = []
    certified_modes: list[np.ndarray] = []
    backward_errors: list[float] = []
    transform_errors: list[float] = []
    sign_tolerances: list[float] = []
    rayleigh_disagreements: list[float] = []
    absolute_stiffness = abs(sparse.csr_matrix(K))
    absolute_mass = abs(sparse.csr_matrix(M))
    for index, vector in enumerate(modes.T):
        made = np.asarray(vector, dtype=float).reshape(-1)
        modal_mass = float(made @ (M @ made))
        if not np.isfinite(modal_mass) or modal_mass <= 0.0:
            raise AlgebraicDynamicsError(
                "descriptor eigensolver returned a non-physical candidate"
            )
        made = made / np.sqrt(modal_mass)
        rayleigh = float(made @ (K @ made))
        if not np.isfinite(rayleigh):
            raise AlgebraicDynamicsError(
                "descriptor eigensolver returned a non-finite Rayleigh value"
            )
        candidate_value = (
            float(values[index]) if preserve_input_eigenvalues else rayleigh
        )
        if not np.isfinite(candidate_value):
            raise AlgebraicDynamicsError(
                "descriptor eigensolver returned a non-finite eigenvalue"
            )
        rayleigh_disagreements.append(
            abs(rayleigh - candidate_value)
            / max(abs(rayleigh), abs(candidate_value), 1.0)
        )
        # Use the independently constructed finite-spectrum scale for the
        # sign decision.  A componentwise ``|x|^T |K| |x|`` bound is useful
        # for backward error, but it is not a sound sign threshold: an
        # arbitrary mixing of a physical coordinate with a stiff algebraic
        # coordinate can make that quantity unbounded while leaving the
        # descriptor spectrum unchanged.
        sign_tolerance = float(
            4096.0
            * np.finfo(float).eps
            * max(float(stiffness_mass_scale), abs(candidate_value), 1.0)
        )
        sign_tolerances.append(sign_tolerance)
        if candidate_value < -sign_tolerance:
            raise AlgebraicDynamicsError(
                "descriptor eigensolver found a negative physical eigenvalue"
            )
        certified = (
            0.0 if abs(candidate_value) <= sign_tolerance else candidate_value
        )
        stiffness_action = np.asarray(K @ made, dtype=float).reshape(-1)
        mass_action = np.asarray(M @ made, dtype=float).reshape(-1)
        residual = stiffness_action - candidate_value * mass_action
        # A local action denominator collapses to the residual itself for a
        # numerically represented rigid vector.  The componentwise backward
        # error is the appropriate coordinate-local certificate: it accepts
        # cancellation at roundoff scale while still rejecting a vector that
        # is not an eigenvector of the represented pencil.
        componentwise_scale = np.asarray(
            absolute_stiffness @ np.abs(made)
            + abs(candidate_value) * (absolute_mass @ np.abs(made)),
            dtype=float,
        ).reshape(-1)
        denominator = max(
            float(np.linalg.norm(componentwise_scale)),
            np.finfo(float).tiny,
        )
        backward = float(np.linalg.norm(residual) / denominator)
        if not np.isfinite(backward) or backward > 2.0e-8:
            raise AlgebraicDynamicsError(
                "descriptor eigensolver candidate failed the backward-error gate"
            )
        backward_errors.append(backward)
        if swapped is not None:
            expected = 1.0 / (candidate_value + descriptor_shift)
            transform_error = float(
                abs(float(swapped[index]) - expected)
                / max(abs(expected), abs(float(swapped[index])), np.finfo(float).tiny)
            )
            if not np.isfinite(transform_error) or transform_error > 2.0e-8:
                raise AlgebraicDynamicsError(
                    "descriptor eigensolver candidate failed transformed-value consistency"
                )
            transform_errors.append(transform_error)
        significant = np.flatnonzero(np.abs(made) > 1.0e-14)
        if significant.size and made[int(significant[0])] < 0.0:
            made = -made
        certified_values.append(certified)
        certified_modes.append(made)

    output_modes = (
        np.column_stack(certified_modes)
        if certified_modes
        else np.zeros((modes.shape[0], 0), dtype=float)
    )
    if certified_modes:
        gram = np.asarray(output_modes.T @ (M @ output_modes), dtype=float)
        orthogonality_error = float(
            np.linalg.norm(gram - np.eye(len(certified_modes)), ord=np.inf)
        )
        if not np.isfinite(orthogonality_error) or orthogonality_error > 1.0e-7:
            raise AlgebraicDynamicsError(
                "descriptor eigensolver candidates failed M-orthogonality"
            )
    else:
        orthogonality_error = 0.0
    return (
        np.asarray(certified_values, dtype=float),
        output_modes,
        {
            "candidate_max_backward_error": max(backward_errors, default=0.0),
            "candidate_max_transformed_value_error": max(transform_errors, default=0.0),
            "candidate_mass_orthogonality_error": orthogonality_error,
            "negative_eigenvalue_tolerance": max(sign_tolerances, default=0.0),
            "candidate_max_full_rayleigh_disagreement": max(
                rayleigh_disagreements, default=0.0
            ),
        },
    )


def _dense_static_condensed_spectrum(
    K: sparse.spmatrix,
    M: sparse.spmatrix,
    algebraic_basis: sparse.spmatrix,
    *,
    num_modes: int,
    target_shift: Optional[float],
    descriptor_shift: float,
    stiffness_mass_scale: float,
) -> DescriptorSpectrum:
    """Solve a strongly sheared small descriptor through exact block form.

    A harmless re-expression ``q_a <- q_a + C q_p`` can make the full
    swapped metric arbitrarily ill-conditioned even though its finite
    spectrum is unchanged.  For bounded systems, select a deterministic
    coordinate complement to the certified mass-null basis, statically solve
    only the algebraic block, and solve the resulting positive-mass pencil.
    This is the same index-one descriptor, expressed without the artificial
    coordinate shear.
    """

    size = int(K.shape[0])
    basis = np.asarray(sparse.csc_matrix(algebraic_basis).toarray(), dtype=float)
    nullity = int(basis.shape[1])
    finite_dimension = size - nullity
    if nullity <= 0 or finite_dimension <= 0:
        raise AlgebraicDynamicsError(
            "descriptor system has no finite static-condensation dimension"
        )
    try:
        _q, _upper, row_order = linalg.qr(
            basis.T,
            mode="economic",
            pivoting=True,
            check_finite=True,
        )
    except Exception as error:
        raise AlgebraicDynamicsError(
            "could not construct the algebraic coordinate complement"
        ) from error
    pivot_rows = np.asarray(row_order[:nullity], dtype=np.intp)
    pivot_block = basis[pivot_rows, :]
    pivot_singular = linalg.svdvals(pivot_block, check_finite=True)
    pivot_floor = float(
        4096.0
        * np.finfo(float).eps
        * max(float(pivot_singular[0]), np.finfo(float).tiny)
        * max(nullity, 1)
    )
    if (
        pivot_singular.size != nullity
        or np.any(~np.isfinite(pivot_singular))
        or float(pivot_singular[-1]) <= pivot_floor
    ):
        raise AlgebraicDynamicsError(
            "algebraic coordinate complement is numerically rank deficient"
        )
    is_pivot = np.zeros(size, dtype=bool)
    is_pivot[pivot_rows] = True
    physical_rows = np.flatnonzero(~is_pivot).astype(np.intp, copy=False)

    dense_stiffness = np.asarray(K.toarray(), dtype=float)
    dense_mass = np.asarray(M.toarray(), dtype=float)
    algebraic_stiffness = basis.T @ dense_stiffness @ basis
    coupling = dense_stiffness[np.ix_(physical_rows, np.arange(size))] @ basis
    physical_stiffness = dense_stiffness[np.ix_(physical_rows, physical_rows)]
    physical_mass = dense_mass[np.ix_(physical_rows, physical_rows)]
    algebraic_stiffness = 0.5 * (
        algebraic_stiffness + algebraic_stiffness.T
    )
    physical_mass = 0.5 * (physical_mass + physical_mass.T)
    _certify_spd(
        sparse.csr_matrix(algebraic_stiffness),
        dense_size_limit=nullity,
        label="algebraic stiffness block",
    )
    try:
        back_substitution = linalg.solve(
            algebraic_stiffness,
            coupling.T,
            assume_a="pos",
            check_finite=True,
        )
    except Exception as error:
        raise AlgebraicDynamicsError(
            "could not solve the algebraic stiffness block"
        ) from error
    condensed_stiffness = physical_stiffness - coupling @ back_substitution
    condensed_stiffness = 0.5 * (
        condensed_stiffness + condensed_stiffness.T
    )
    condensed_metric = condensed_stiffness + descriptor_shift * physical_mass
    _certify_spd(
        sparse.csr_matrix(physical_mass),
        dense_size_limit=finite_dimension,
        label="statically condensed physical mass",
    )
    metric_minimum, metric_method = _certify_spd(
        sparse.csr_matrix(condensed_metric),
        dense_size_limit=finite_dimension,
        label="statically condensed K + descriptor_shift*M",
    )
    try:
        values, physical_vectors = linalg.eigh(
            condensed_stiffness,
            physical_mass,
            check_finite=True,
            driver="gvd",
        )
    except Exception as error:
        raise AlgebraicDynamicsError(
            "dense statically condensed descriptor eigensolver failed"
        ) from error
    if target_shift is None:
        selected_count = min(
            max(int(num_modes) + 8, int(num_modes)),
            finite_dimension,
        )
        selected = np.argsort(values, kind="stable")[:selected_count]
    else:
        target = float(target_shift)
        if not np.isfinite(target):
            raise AlgebraicDynamicsError("descriptor target shift must be finite")
        selected = np.lexsort((values, np.abs(values - target)))[
            : min(int(num_modes), finite_dimension)
        ]
    values = np.asarray(values[selected], dtype=float)
    physical_vectors = np.asarray(physical_vectors[:, selected], dtype=float)
    algebraic_coordinates = -back_substitution @ physical_vectors
    vectors = basis @ algebraic_coordinates
    vectors[physical_rows, :] += physical_vectors
    values, vectors, candidate_diagnostics = _validate_physical_candidates(
        K,
        M,
        values,
        vectors,
        stiffness_mass_scale=stiffness_mass_scale,
        descriptor_shift=descriptor_shift,
        preserve_input_eigenvalues=True,
    )
    return DescriptorSpectrum(
        values,
        vectors,
        {
            "solver": "dense_algebraic_static_condensation_eigh",
            "sparse_mode": "coordinate_invariant_static_condensation_fallback",
            "descriptor_candidate_count": int(values.size),
            "excluded_algebraic_candidates": nullity,
            "metric_minimum_eigenvalue": metric_minimum,
            "metric_spd_method": metric_method,
            "static_condensation_pivot_rows": pivot_rows.tolist(),
            "target_excluded_algebraic_ritz_vectors": (
                nullity if target_shift is not None else 0
            ),
            **candidate_diagnostics,
        },
    )


def solve_descriptor_spectrum(
    K: sparse.spmatrix,
    M: sparse.spmatrix,
    *,
    num_modes: int,
    dense_size_limit: int,
    algebraic_nullity: int,
    algebraic_basis: Optional[sparse.spmatrix] = None,
    target_shift: Optional[float] = None,
    factorization_cache: Optional[FactorizationCache] = None,
) -> DescriptorSpectrum:
    """Return finite modal candidates for a symmetric index-one descriptor.

    ``K + sigma M`` must be positive definite.  Failure of that condition is
    intentionally terminal: it identifies a mechanism common to stiffness and
    mass, an unstable tangent outside the free-vibration contract, or an
    undeclared descriptor defect.
    """

    K_sym = _symmetric(sparse.csr_matrix(K))
    M_sym = _symmetric(sparse.csr_matrix(M))
    if K_sym.shape != M_sym.shape or K_sym.shape[0] != K_sym.shape[1]:
        raise AlgebraicDynamicsError("descriptor K and M must be square and shape-compatible")
    if num_modes <= 0:
        raise ValueError("num_modes must be positive")
    size = int(K_sym.shape[0])
    nullity = int(algebraic_nullity)
    if nullity < 0 or nullity > size:
        raise AlgebraicDynamicsError("declared assembled algebraic nullity is incompatible")
    finite_dimension = size - nullity
    resolved_algebraic_basis: Optional[sparse.csc_matrix] = None
    if nullity:
        if algebraic_basis is not None:
            resolved_algebraic_basis = sparse.csc_matrix(
                algebraic_basis, dtype=float
            )
            if resolved_algebraic_basis.shape != (size, nullity):
                raise AlgebraicDynamicsError(
                    "declared assembled algebraic basis has an incompatible shape"
                )
        elif size <= 512:
            dense_mass = np.asarray(M_sym.toarray(), dtype=float)
            mass_values, mass_vectors = linalg.eigh(
                0.5 * (dense_mass + dense_mass.T), check_finite=True
            )
            selected_null = np.argsort(np.abs(mass_values), kind="stable")[:nullity]
            resolved_algebraic_basis = sparse.csc_matrix(
                mass_vectors[:, selected_null]
            )
        else:
            raise AlgebraicDynamicsError(
                "sparse descriptor solve requires the certified algebraic basis"
            )
        if np.any(~np.isfinite(resolved_algebraic_basis.data)):
            raise AlgebraicDynamicsError(
                "declared assembled algebraic basis contains non-finite values"
            )
        basis_gram = (
            resolved_algebraic_basis.T @ resolved_algebraic_basis
        ).tocsc()
        _certify_spd(
            basis_gram,
            dense_size_limit=max(int(dense_size_limit), int(nullity)),
            label="declared assembled algebraic basis Gram matrix",
        )
        basis_action = M_sym @ resolved_algebraic_basis
        basis_relative = float(
            sparse_linalg.norm(basis_action)
            / max(
                sparse_linalg.norm(M_sym)
                * max(sparse_linalg.norm(resolved_algebraic_basis), 1.0),
                np.finfo(float).tiny,
            )
        )
        if basis_relative > 2.0e-11:
            raise AlgebraicDynamicsError(
                "declared assembled algebraic basis is not mass-null"
            )
    shift, scales = _descriptor_shift(
        K_sym,
        M_sym,
        resolved_algebraic_basis,
    )
    metric = _symmetric(K_sym + shift * M_sym)
    diagnostics: Dict[str, Any] = {
        "policy_id": DESCRIPTOR_MODAL_POLICY_ID,
        "descriptor_shift": float(shift),
        "descriptor_shift_ratio": DESCRIPTOR_SHIFT_RATIO,
        "requested_modes": int(num_modes),
        "declared_assembled_algebraic_nullity": nullity,
        **scales,
    }

    if size == 0:
        return DescriptorSpectrum(
            np.zeros(0),
            np.zeros((0, 0)),
            {**diagnostics, "solver": "empty", "excluded_algebraic_candidates": 0},
        )

    coordinate_shear = float(scales["algebraic_static_correction_ratio"])
    if nullity and size <= DESCRIPTOR_DENSE_CONDENSATION_LIMIT:
        assert resolved_algebraic_basis is not None
        condensed = _dense_static_condensed_spectrum(
            K_sym,
            M_sym,
            resolved_algebraic_basis,
            num_modes=num_modes,
            target_shift=target_shift,
            descriptor_shift=shift,
            stiffness_mass_scale=float(scales["stiffness_mass_scale"]),
        )
        return DescriptorSpectrum(
            condensed.eigenvalues,
            condensed.eigenvectors,
            {**diagnostics, **condensed.diagnostics},
        )
    if coordinate_shear > DESCRIPTOR_COORDINATE_SHEAR_LIMIT:
        raise AlgebraicDynamicsError(
            "descriptor algebraic coordinate shear exceeds the bounded "
            "coordinate-invariant solver limit"
        )

    metric_minimum, metric_spd_method = _certify_spd(
        metric,
        dense_size_limit=dense_size_limit,
        label="K + descriptor_shift*M",
    )
    diagnostics["metric_minimum_eigenvalue"] = metric_minimum
    diagnostics["metric_spd_method"] = metric_spd_method

    if size <= int(dense_size_limit) or size <= int(num_modes) + 1:
        dense_mass = np.asarray(M_sym.toarray(), dtype=float)
        dense_metric = np.asarray(metric.toarray(), dtype=float)
        dense_metric = 0.5 * (dense_metric + dense_metric.T)
        try:
            swapped, vectors = linalg.eigh(
                dense_mass,
                dense_metric,
                check_finite=True,
                driver="gvd",
            )
        except Exception as error:
            raise AlgebraicDynamicsError(
                "K + descriptor_shift*M is not positive definite"
            ) from error
        eigenvalues, eigenvectors, excluded = _rayleigh_values(
            K_sym,
            M_sym,
            swapped,
            vectors,
            algebraic_nullity=nullity,
        )
        if target_shift is not None and eigenvalues.size:
            target = float(target_shift)
            if not np.isfinite(target):
                raise AlgebraicDynamicsError("descriptor target shift must be finite")
            selected = np.lexsort((eigenvalues, np.abs(eigenvalues - target)))[
                :num_modes
            ]
            eigenvalues = eigenvalues[selected]
            eigenvectors = eigenvectors[:, selected]
        eigenvalues, eigenvectors, candidate_diagnostics = (
            _validate_physical_candidates(
                K_sym,
                M_sym,
                eigenvalues,
                eigenvectors,
                stiffness_mass_scale=float(scales["stiffness_mass_scale"]),
                descriptor_shift=shift,
            )
        )
        diagnostics.update(
            {
                "solver": "dense_scipy_swapped_eigh",
                "swapped_candidate_count": int(swapped.size),
                "excluded_algebraic_candidates": int(excluded),
                **candidate_diagnostics,
            }
        )
        return DescriptorSpectrum(eigenvalues, eigenvectors, diagnostics)

    candidate_count = min(
        max(int(num_modes) + 8, int(num_modes)),
        finite_dimension,
        size - 1,
    )
    if candidate_count <= 0:
        raise AlgebraicDynamicsError("descriptor system has no finite candidate dimension")
    cache = factorization_cache or FactorizationCache(
        name="descriptor_modal_metric", max_entries=2
    )
    start = _deterministic_start(size)
    if target_shift is None:
        handle = factorize_cached(
            metric,
            MatrixClass.SPD,
            cache=cache,
        )
        if handle.status != "ok":
            raise AlgebraicDynamicsError(
                f"could not factor descriptor metric: {handle.failure_reason}"
            )
        inverse = sparse_linalg.LinearOperator(
            metric.shape,
            matvec=lambda value: np.asarray(handle.solve(value), dtype=float),
            matmat=lambda value: np.asarray(handle.solve_many(value), dtype=float),
            dtype=float,
        )
        try:
            if size <= 5 * candidate_count:
                all_transformed, all_vectors = linalg.eigh(
                    np.asarray(M_sym.toarray(), dtype=float),
                    np.asarray(metric.toarray(), dtype=float),
                    check_finite=True,
                    driver="gvd",
                )
                selected = np.argsort(all_transformed, kind="stable")[-candidate_count:]
                transformed = all_transformed[selected]
                vectors = all_vectors[:, selected]
                sparse_mode = "lowest_dense_requested_fraction_swapped_eigh"
            else:
                # SciPy reports best-iterate convergence with a warning even
                # when every returned Ritz pair passes our stricter explicit
                # full-pencil certificate below.  Keep diagnostics stable and
                # let that certificate, rather than backend prose, adjudicate.
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    transformed, vectors = sparse_linalg.lobpcg(
                        M_sym,
                        _deterministic_block(size, candidate_count),
                        B=metric,
                        M=inverse,
                        largest=True,
                        tol=2.0e-11,
                        maxiter=max(200, min(2000, 5 * size)),
                    )
                sparse_mode = "lowest_symmetric_swapped_block_lobpcg"
        except Exception as error:
            raise AlgebraicDynamicsError(
                "sparse descriptor eigensolver failed"
            ) from error
        factorization_diagnostics = handle.diagnostics()
    else:
        target = float(target_shift)
        if not np.isfinite(target):
            raise AlgebraicDynamicsError("descriptor target shift must be finite")
        target_regularization = float(
            256.0
            * np.finfo(float).eps
            * max(abs(target), float(scales["stiffness_mass_scale"]), 1.0)
        )
        factor_target = target + target_regularization
        target_swapped = 1.0 / (factor_target + shift)
        if not np.isfinite(target_swapped) or target_swapped == 0.0:
            raise AlgebraicDynamicsError(
                "descriptor target shift is incompatible with the swapped pencil"
            )
        shifted_original = _symmetric(K_sym - factor_target * M_sym)
        handle = factorize_cached(
            shifted_original,
            MatrixClass.SYMMETRIC_INDEFINITE,
            cache=cache,
        )
        if handle.status != "ok":
            raise AlgebraicDynamicsError(
                f"could not factor descriptor target shift: {handle.failure_reason}"
            )
        def _target_solve(value: np.ndarray) -> np.ndarray:
            made = np.asarray(value, dtype=float)
            if made.ndim == 1:
                return (
                    -np.asarray(handle.solve(made), dtype=float) / target_swapped
                )
            return -np.asarray(handle.solve_many(made), dtype=float) / target_swapped

        algebraic_metric_factor = None
        if resolved_algebraic_basis is not None:
            algebraic_metric_gram = (
                resolved_algebraic_basis.T @ metric @ resolved_algebraic_basis
            ).tocsc()
            try:
                algebraic_metric_factor = sparse_linalg.splu(
                    algebraic_metric_gram
                )
            except Exception as error:
                raise AlgebraicDynamicsError(
                    "could not factor the targeted algebraic projection metric"
                ) from error

        target_operator_inverse = sparse_linalg.LinearOperator(
            shifted_original.shape,
            matvec=_target_solve,
            matmat=_target_solve,
            dtype=float,
        )
        try:
            target_candidate_count = min(
                max(
                    int(num_modes) + 8 + nullity,
                    2 * int(num_modes) + nullity,
                ),
                size - 1,
            )
            side_values: list[np.ndarray] = []
            side_vectors: list[np.ndarray] = []
            # In shift-invert mode LA and SA select the nearest transformed
            # values on opposite sides of the target.  Running both sides is
            # necessary because distance in mu=1/(lambda+sigma) is nonlinear
            # in lambda and one side can otherwise crowd out the truly nearest
            # physical eigenvalue.
            for side in ("LA", "SA"):
                made_values, made_vectors = sparse_linalg.eigsh(
                    M_sym.tocsc(),
                    k=target_candidate_count,
                    M=metric.tocsc(),
                    sigma=target_swapped,
                    which=side,
                    OPinv=target_operator_inverse,
                    v0=start,
                    tol=2.0e-11,
                    maxiter=max(1000, 20 * size),
                )
                side_values.append(np.asarray(made_values, dtype=float))
                side_vectors.append(np.asarray(made_vectors, dtype=float))
            transformed = np.concatenate(side_values)
            vectors = np.column_stack(side_vectors)
        except Exception as error:
            raise AlgebraicDynamicsError(
                "sparse descriptor eigensolver failed"
            ) from error

        # Algebraic Ritz vectors have mu=0.  Remove them with the invariant
        # (K+sigma M)-metric projector, and clean roundoff contamination from
        # every physical Ritz vector before the full-pencil certificate.  A
        # coordinate-wise or Euclidean test would change under a harmless
        # re-expression of the massless coordinates.
        retained_values: list[float] = []
        retained_vectors: list[np.ndarray] = []
        excluded_target_algebraic = 0
        for vector in np.asarray(vectors, dtype=float).T:
            made = np.asarray(vector, dtype=float).reshape(-1)
            metric_action = np.asarray(metric @ made, dtype=float).reshape(-1)
            metric_norm = float(made @ metric_action)
            if not np.isfinite(metric_norm) or metric_norm <= 0.0:
                raise AlgebraicDynamicsError(
                    "targeted descriptor candidate has invalid metric norm"
                )
            if (
                resolved_algebraic_basis is not None
                and algebraic_metric_factor is not None
            ):
                rhs = np.asarray(
                    resolved_algebraic_basis.T @ metric_action,
                    dtype=float,
                ).reshape(-1)
                coefficients = algebraic_metric_factor.solve(rhs)
                projection = np.asarray(
                    resolved_algebraic_basis @ coefficients,
                    dtype=float,
                ).reshape(-1)
                projection_energy = float(rhs @ coefficients)
                remaining_fraction = max(
                    0.0,
                    1.0 - projection_energy / metric_norm,
                )
                if remaining_fraction <= 8192.0 * np.finfo(float).eps:
                    excluded_target_algebraic += 1
                    continue
                made = made - projection
                metric_action = np.asarray(metric @ made, dtype=float).reshape(-1)
                metric_norm = float(made @ metric_action)
            modal_mass = float(made @ (M_sym @ made))
            if (
                not np.isfinite(metric_norm)
                or not np.isfinite(modal_mass)
                or metric_norm <= 0.0
                or modal_mass <= 0.0
            ):
                excluded_target_algebraic += 1
                continue
            made = made / np.sqrt(metric_norm)
            transformed_value = modal_mass / metric_norm
            # LA and SA can overlap when one side contains fewer requested
            # values.  Remove only duplicate vectors, never repeated physical
            # eigenvalues with independent eigendirections.
            duplicate = False
            for prior in retained_vectors:
                correlation = abs(float(prior @ (metric @ made)))
                if correlation >= 1.0 - 2.0e-9:
                    duplicate = True
                    break
            if duplicate:
                continue
            retained_values.append(float(transformed_value))
            retained_vectors.append(made)
        if len(retained_vectors) < min(int(num_modes), finite_dimension):
            raise AlgebraicDynamicsError(
                "targeted descriptor solve returned too few physical candidates"
            )
        transformed = np.asarray(retained_values, dtype=float)
        vectors = np.column_stack(retained_vectors)
        factorization_diagnostics = handle.diagnostics()
        sparse_mode = "targeted_two_sided_projected_swapped_eigsh"
        diagnostics["target_factorization_shift"] = factor_target
        diagnostics["target_factorization_regularization"] = target_regularization
        diagnostics["target_excluded_algebraic_ritz_vectors"] = int(
            excluded_target_algebraic
        )

    raw_values = np.asarray(transformed, dtype=float).reshape(-1)
    raw_vectors = np.asarray(vectors, dtype=float)
    eigenvalues, eigenvectors, candidate_diagnostics = _validate_physical_candidates(
        K_sym,
        M_sym,
        np.zeros(raw_values.size, dtype=float),
        raw_vectors,
        stiffness_mass_scale=float(scales["stiffness_mass_scale"]),
        descriptor_shift=shift,
        transformed_values=raw_values,
    )
    if target_shift is not None and eigenvalues.size:
        selected = np.lexsort(
            (eigenvalues, np.abs(eigenvalues - float(target_shift)))
        )[:num_modes]
        eigenvalues = eigenvalues[selected]
        eigenvectors = eigenvectors[:, selected]
    elif eigenvalues.size:
        selected = np.argsort(eigenvalues, kind="stable")
        eigenvalues = eigenvalues[selected]
        eigenvectors = eigenvectors[:, selected]
    diagnostics.update(
        {
            "solver": "sparse_scipy_descriptor_eigsh",
            "sparse_mode": sparse_mode,
            "descriptor_candidate_count": int(raw_values.size),
            "excluded_algebraic_candidates": int(nullity),
            "factorization": factorization_diagnostics,
            "factorization_cache": cache.diagnostics(),
            **candidate_diagnostics,
        }
    )
    return DescriptorSpectrum(eigenvalues, eigenvectors, diagnostics)


__all__ = [
    "AlgebraicDynamicsError",
    "DESCRIPTOR_COORDINATE_SHEAR_LIMIT",
    "DESCRIPTOR_DENSE_CONDENSATION_LIMIT",
    "DESCRIPTOR_MODAL_POLICY_ID",
    "DESCRIPTOR_SHIFT_RATIO",
    "DeclaredAlgebraicBasis",
    "DescriptorSpectrum",
    "build_declared_algebraic_basis",
    "declared_algebraic_mass_elements",
    "solve_descriptor_spectrum",
    "uses_declared_algebraic_mass",
]
