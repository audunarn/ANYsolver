"""Incremental CSR updates for impact damage stiffness and mass matrices."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Mapping, Sequence, Tuple

import numpy as np
from scipy import sparse

if TYPE_CHECKING:
    from .fe_core import FEModel


DamageElementTerm = Tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]


class DamageMatrixPlanFallback(ValueError):
    """Signal that a caller must use the exact scalar rebuild for this update."""


def _revision_key(model: "FEModel") -> Tuple[int, int, int, int]:
    revisions = model.mesh.revision_signature()
    return (
        int(revisions.get("topology", 0)),
        int(revisions.get("geometry", 0)),
        int(revisions.get("material", 0)),
        int(revisions.get("mass", 0)),
    )


def _point_mass_diagonal(model: "FEModel", total_dofs: int) -> np.ndarray:
    diagonal = np.zeros(total_dofs, dtype=float)
    for node_id, mass in (getattr(model.mesh, "point_masses", None) or {}).items():
        node = model.mesh.get_node(int(node_id))
        if node is None or float(mass) == 0.0:
            continue
        for axis in range(3):
            diagonal[node.dofs[axis]] += float(mass)
    return diagonal


def _csr_position_map(matrix: sparse.csr_matrix) -> Tuple[Dict[int, int], ...]:
    rows = []
    for row in range(matrix.shape[0]):
        start = int(matrix.indptr[row])
        stop = int(matrix.indptr[row + 1])
        rows.append(
            {
                int(column): position
                for position, column in zip(
                    range(start, stop),
                    matrix.indices[start:stop],
                )
            }
        )
    return tuple(rows)


def _positions(
    row_maps: Sequence[Mapping[int, int]],
    rows: np.ndarray,
    columns: np.ndarray,
) -> np.ndarray:
    return np.fromiter(
        (
            row_maps[int(row)][int(column)]
            for row, column in zip(rows, columns)
        ),
        dtype=np.intp,
        count=int(rows.size),
    )


@dataclass(frozen=True)
class DamageContribution:
    element_id: int
    stiffness_positions: np.ndarray
    mass_positions: np.ndarray
    stiffness_values: np.ndarray
    mass_values: np.ndarray


@dataclass
class DamageMatrixPlan:
    """One bounded matrix pattern with per-element additive contribution maps."""

    revision_key: Tuple[int, int, int, int]
    stiffness: sparse.csr_matrix
    mass: sparse.csr_matrix
    contributions: Tuple[DamageContribution, ...]
    base_stiffness_data: np.ndarray
    base_mass_data: np.ndarray
    point_mass_positions: np.ndarray
    point_mass_values: np.ndarray
    setup_seconds: float
    retained_bytes: int
    last_scales: np.ndarray
    update_count: int = 0
    no_change_count: int = 0
    changed_element_count: int = 0
    update_seconds: float = 0.0
    invalidation_count: int = 0
    fallback_count: int = 0
    fallback_reason: str | None = None
    _id_to_index: Dict[int, int] = field(default_factory=dict, repr=False)
    _active_indices: set[int] = field(default_factory=set, repr=False)

    @classmethod
    def build(
        cls,
        model: "FEModel",
        cached_terms: Tuple[int, Tuple[DamageElementTerm, ...]],
    ) -> "DamageMatrixPlan":
        start = time.perf_counter()
        total_dofs, terms = cached_terms
        if not terms:
            empty_k = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
            empty_m = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
            return cls(
                revision_key=_revision_key(model),
                stiffness=empty_k,
                mass=empty_m,
                contributions=(),
                base_stiffness_data=np.empty(0, dtype=float),
                base_mass_data=np.empty(0, dtype=float),
                point_mass_positions=np.empty(0, dtype=np.intp),
                point_mass_values=np.empty(0, dtype=float),
                setup_seconds=float(time.perf_counter() - start),
                retained_bytes=0,
                last_scales=np.empty(0, dtype=float),
            )

        rows = np.concatenate([term[1] for term in terms])
        columns = np.concatenate([term[2] for term in terms])
        stiffness_values = np.concatenate([term[3] for term in terms])
        mass_values = np.concatenate([term[4] for term in terms])
        stiffness = sparse.coo_matrix(
            (stiffness_values, (rows, columns)),
            shape=(total_dofs, total_dofs),
        ).tocsr()
        # Include point-mass diagonals in the initial COO conversion.  Sparse
        # matrix addition drops explicit zero entries; doing ``M + diag`` here
        # would therefore destroy positions needed by zero-valued element
        # contributions and make later in-place updates unsafe.
        point_mass = _point_mass_diagonal(model, total_dofs)
        point_mass_dofs = np.flatnonzero(point_mass).astype(np.intp, copy=False)
        mass_coo_rows = rows
        mass_coo_columns = columns
        mass_coo_data = mass_values
        if point_mass_dofs.size:
            mass_coo_rows = np.concatenate((mass_coo_rows, point_mass_dofs))
            mass_coo_columns = np.concatenate((mass_coo_columns, point_mass_dofs))
            mass_coo_data = np.concatenate((mass_coo_data, point_mass[point_mass_dofs]))
        mass = sparse.coo_matrix(
            (mass_coo_data, (mass_coo_rows, mass_coo_columns)),
            shape=(total_dofs, total_dofs),
        ).tocsr()
        stiffness.sum_duplicates()
        stiffness.sort_indices()
        mass.sum_duplicates()
        mass.sort_indices()
        stiffness_rows = _csr_position_map(stiffness)
        mass_rows = _csr_position_map(mass)
        point_mass_positions = _positions(mass_rows, point_mass_dofs, point_mass_dofs)
        point_mass_values = point_mass[point_mass_dofs].copy()
        base_stiffness_data = stiffness.data.copy()
        base_mass_data = mass.data.copy()
        contributions = []
        retained_bytes = int(
            stiffness.data.nbytes
            + stiffness.indices.nbytes
            + stiffness.indptr.nbytes
            + mass.data.nbytes
            + mass.indices.nbytes
            + mass.indptr.nbytes
            + base_stiffness_data.nbytes
            + base_mass_data.nbytes
            + point_mass_positions.nbytes
            + point_mass_values.nbytes
        )
        for element_id, row, column, k_flat, m_flat in terms:
            k_positions = _positions(stiffness_rows, row, column)
            m_positions = _positions(mass_rows, row, column)
            k_values = np.asarray(k_flat, dtype=float).copy()
            m_values = np.asarray(m_flat, dtype=float).copy()
            contributions.append(
                DamageContribution(
                    element_id=int(element_id),
                    stiffness_positions=k_positions,
                    mass_positions=m_positions,
                    stiffness_values=k_values,
                    mass_values=m_values,
                )
            )
            retained_bytes += int(
                k_positions.nbytes
                + m_positions.nbytes
                + k_values.nbytes
                + m_values.nbytes
            )
        contribution_tuple = tuple(contributions)
        last_scales = np.ones(len(contribution_tuple), dtype=float)
        retained_bytes += int(last_scales.nbytes)
        return cls(
            revision_key=_revision_key(model),
            stiffness=stiffness,
            mass=mass,
            contributions=contribution_tuple,
            base_stiffness_data=base_stiffness_data,
            base_mass_data=base_mass_data,
            point_mass_positions=point_mass_positions,
            point_mass_values=point_mass_values,
            setup_seconds=float(time.perf_counter() - start),
            retained_bytes=retained_bytes,
            last_scales=last_scales,
            _id_to_index={
                contribution.element_id: index
                for index, contribution in enumerate(contribution_tuple)
            },
        )

    def is_valid(self, model: "FEModel") -> bool:
        return self.revision_key == _revision_key(model)

    def update(
        self,
        model: "FEModel",
        element_scales: Mapping[int, float],
    ) -> Tuple[sparse.csr_matrix, sparse.csr_matrix]:
        if not self.is_valid(model):
            self.invalidation_count += 1
            self.fallback_count += 1
            self.fallback_reason = "model_revision_changed"
            raise DamageMatrixPlanFallback("damage matrix plan is invalid after a model revision")
        start = time.perf_counter()
        raw_scales = {int(element_id): float(scale) for element_id, scale in element_scales.items()}
        if any(not np.isfinite(scale) for scale in raw_scales.values()):
            self.fallback_count += 1
            self.fallback_reason = "nonfinite_element_scale"
            raise DamageMatrixPlanFallback("incremental damage scales must be finite")
        scales = {
            element_id: min(max(scale, 0.0), 1.0)
            for element_id, scale in raw_scales.items()
        }
        candidate_indices = set(self._active_indices)
        candidate_indices.update(
            self._id_to_index[element_id]
            for element_id in scales
            if element_id in self._id_to_index
        )
        changed = 0
        for index in sorted(candidate_indices):
            contribution = self.contributions[index]
            new_scale = float(scales.get(contribution.element_id, 1.0))
            delta = new_scale - float(self.last_scales[index])
            if delta == 0.0:
                continue
            np.add.at(
                self.stiffness.data,
                contribution.stiffness_positions,
                delta * contribution.stiffness_values,
            )
            np.add.at(
                self.mass.data,
                contribution.mass_positions,
                delta * contribution.mass_values,
            )
            self.last_scales[index] = new_scale
            if new_scale == 1.0:
                self._active_indices.discard(index)
            else:
                self._active_indices.add(index)
            changed += 1
        if changed and not self._active_indices:
            # Resetting every omitted/explicit scale to one must not retain
            # roundoff accumulated by a long damage history.
            np.copyto(self.stiffness.data, self.base_stiffness_data)
            np.copyto(self.mass.data, self.base_mass_data)
        elif (
            changed
            and len(self._active_indices) == len(self.contributions)
            and bool(np.all(self.last_scales == 0.0))
        ):
            # The legacy scalar assembly multiplies every local value by
            # exactly zero.  Restore that exact result (plus point masses)
            # instead of leaving subtraction roundoff in shared CSR entries.
            self.stiffness.data.fill(0.0)
            self.mass.data.fill(0.0)
            self.mass.data[self.point_mass_positions] = self.point_mass_values
        self.update_count += 1
        self.changed_element_count += changed
        if changed == 0:
            self.no_change_count += 1
        self.update_seconds += float(time.perf_counter() - start)
        return self.stiffness, self.mass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "fast_path_name": "incremental_damage_csr_updates",
            "eligible_element_count": len(self.contributions),
            "fallback_element_count": 0,
            "fallback_reason": self.fallback_reason,
            "revision_key": list(self.revision_key),
            "setup_seconds": float(self.setup_seconds),
            "retained_bytes": int(self.retained_bytes),
            "update_count": int(self.update_count),
            "no_change_count": int(self.no_change_count),
            "changed_element_count": int(self.changed_element_count),
            "update_seconds": float(self.update_seconds),
            "invalidation_count": int(self.invalidation_count),
            "fallback_count": int(self.fallback_count),
            "active_scaled_element_count": len(self._active_indices),
            "stiffness_nnz": int(self.stiffness.nnz),
            "mass_nnz": int(self.mass.nnz),
        }
