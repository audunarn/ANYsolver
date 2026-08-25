"""Bounded, revision-aware plans for deterministic stress recovery chunks.

The scalar element recovery routines remain the numerical oracle.  This module
removes per-call topology work and partitions that oracle into a small number
of formulation-aware chunks, avoiding one ``Future`` allocation per element.
The plan is stored as one mesh-owned entry and therefore cannot grow with
selection masks or result-output cadence.
"""

from __future__ import annotations

import math
import time
from collections import OrderedDict
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np

from .elements import (
    BeamElement,
    QuadraticBeamElement,
    ShellElement,
    _shell_material_matrices,
)
from .materials import is_isotropic_material
from .materials import elastic_compliance_matrix, material_symmetry
from .s3_reference_batch import (
    MIN_REFERENCE_S3_RECOVERY_GROUP,
    ReferenceS3RecoveryBatch,
    build_reference_s3_recovery_batch,
    reference_s3_candidate,
)

if TYPE_CHECKING:
    from .fe_core import FEModel


def _readonly(array: np.ndarray) -> np.ndarray:
    result = np.ascontiguousarray(array)
    return np.frombuffer(
        result.tobytes(order="C"), dtype=result.dtype
    ).reshape(result.shape)


def _revision_key(model: "FEModel") -> Tuple[int, int, int]:
    revisions = model.mesh.revision_signature()
    return (
        int(revisions.get("topology", 0)),
        int(revisions.get("geometry", 0)),
        int(revisions.get("material", 0)),
    )


def _direct_state_key(model: "FEModel") -> Tuple[int, int, int, int]:
    token = getattr(model.mesh, "_qualified_direct_state_token", (-1,))
    return (
        id(model.mesh.nodes),
        id(model.mesh.elements),
        id(token),
        int(token[0]),
    )


def _material_state_key(model: "FEModel") -> Tuple[Tuple[object, ...], ...]:
    names = sorted(str(name) for name in model.materials)
    rows = []
    for name in names:
        material = model.get_material(name)
        if is_isotropic_material(material):
            elastic = (
                "isotropic",
                float(material.elastic_modulus),
                float(material.poisson_ratio),
            )
        else:
            compliance = np.ascontiguousarray(
                np.asarray(elastic_compliance_matrix(material), dtype=np.float64)
            )
            elastic = (
                str(material_symmetry(material)),
                compliance.shape,
                compliance.tobytes(order="C"),
            )
        hill = getattr(material, "hill_yield", None)
        hardening = getattr(material, "hardening_curve", None)
        rows.append(
            (
                name,
                type(material).__module__,
                type(material).__qualname__,
                id(material),
                bool(is_isotropic_material(material)),
                elastic,
                hill is None,
                id(hill),
                hardening is None,
                id(hardening),
            )
        )
    return tuple(rows)


def _formulation_name(model: "FEModel", element: object) -> str:
    if isinstance(element, ShellElement):
        node_count = len(element.node_ids)
        topology = {3: "t3", 4: "s4", 6: "t6", 8: "q8"}.get(
            node_count, f"shell{node_count}"
        )
        if bool(getattr(element, "reduced_integration", False)):
            topology += "r"
        if getattr(element, "shell_section", None) is not None:
            constitutive = "generalized"
        else:
            material = model.get_material(element.material_name)
            if is_isotropic_material(material):
                constitutive = (
                    "isotropic_hill"
                    if getattr(material, "hill_yield", None) is not None
                    else "isotropic"
                )
            else:
                constitutive = "orthotropic"
        return f"shell_{topology}_{constitutive}"
    if isinstance(element, QuadraticBeamElement):
        return "beam3"
    if isinstance(element, BeamElement):
        return "beam2"
    return f"scalar_{type(element).__name__}"


@dataclass(frozen=True)
class RecoveryPlanItem:
    element_id: int
    formulation: str
    dof_mapping: np.ndarray


@dataclass(frozen=True)
class RecoveryBatchPlan:
    """Immutable layout shared by repeated recovery calls for one mesh."""

    revision_key: Tuple[int, int, int]
    direct_state_key: Tuple[int, int, int, int]
    material_state_key: Tuple[Tuple[object, ...], ...]
    items: Tuple[RecoveryPlanItem, ...]
    item_by_id: Mapping[int, RecoveryPlanItem]
    setup_seconds: float
    retained_bytes: int
    isotropic_s4: "RecoveryS4Batch | None"
    reference_s3: "ReferenceS3RecoveryBatch | None"
    reference_s3_candidate_ids: Tuple[int, ...]
    reference_s3_fallback_reasons: Mapping[str, Tuple[int, ...]]

    @classmethod
    def build(cls, model: "FEModel") -> "RecoveryBatchPlan":
        from .fe_core import _ensure_qualified_state_mappings

        # A wholesale public mapping replacement invalidates the prior plan
        # by identity.  Normalize the replacement before capturing a new key
        # so subsequent direct node/element mutations remain observable.
        _ensure_qualified_state_mappings(model.mesh)
        start = time.perf_counter()
        items = []
        s4_element_ids = []
        s4_coords = []
        s4_dof_mappings = []
        s4_q_local = []
        s4_g_local = []
        s4_thickness = []
        reference_s3_items = []
        retained_bytes = 0
        for element_id, element in model.mesh.elements.items():
            mapping = _readonly(
                np.asarray(
                    element.get_dof_mapping(model.mesh), dtype=np.intp
                ).reshape(-1)
            )
            retained_bytes += int(mapping.nbytes)
            items.append(
                RecoveryPlanItem(
                    element_id=int(element_id),
                    formulation=_formulation_name(model, element),
                    dof_mapping=mapping,
                )
            )
            if reference_s3_candidate(element):
                reference_s3_items.append(
                    (int(element_id), element, mapping)
                )
            if items[-1].formulation in {"shell_s4_isotropic", "shell_s4r_isotropic"}:
                material = model.get_material(element.material_name)
                q_local, g_local, _strain_transform, _stress_transform = (
                    _shell_material_matrices(material, 0.0)
                )
                s4_element_ids.append(int(element_id))
                s4_coords.append(
                    np.asarray(element.get_node_coordinates(model.mesh), dtype=float)
                )
                s4_dof_mappings.append(mapping)
                s4_q_local.append(np.asarray(q_local, dtype=float))
                s4_g_local.append(np.asarray(g_local, dtype=float))
                s4_thickness.append(float(element.thickness))
        item_tuple = tuple(items)
        isotropic_s4 = None
        if s4_element_ids:
            isotropic_s4 = RecoveryS4Batch(
                element_ids=_readonly(np.asarray(s4_element_ids, dtype=np.int64)),
                index_by_id=MappingProxyType({
                    int(element_id): index
                    for index, element_id in enumerate(s4_element_ids)
                }),
                coords=_readonly(np.asarray(s4_coords, dtype=float)),
                dof_mappings=_readonly(np.asarray(s4_dof_mappings, dtype=np.intp)),
                q_local=_readonly(np.asarray(s4_q_local, dtype=float)),
                g_local=_readonly(np.asarray(s4_g_local, dtype=float)),
                thickness=_readonly(np.asarray(s4_thickness, dtype=float)),
                gauss_points=_readonly(
                    np.asarray(ShellElement.GAUSS_POINTS_2x2, dtype=float)
                ),
            )
            retained_bytes += isotropic_s4.retained_bytes
        reference_s3 = None
        reference_s3_candidate_ids: Tuple[int, ...] = ()
        reference_s3_fallback_reasons: Mapping[str, Tuple[int, ...]] = (
            MappingProxyType({})
        )
        # Keep small selections on the existing scalar oracle with no retained
        # batch state.  This is intentionally checked before component
        # preparation so ordinary small models pay no S3 batch setup cost.
        if len(reference_s3_items) >= MIN_REFERENCE_S3_RECOVERY_GROUP:
            reference_s3, prepared_s3 = build_reference_s3_recovery_batch(
                model,
                reference_s3_items,
            )
            reference_s3_candidate_ids = prepared_s3.candidate_element_ids
            reference_s3_fallback_reasons = prepared_s3.fallback_reasons
            if reference_s3 is not None:
                retained_bytes += reference_s3.retained_bytes
        return cls(
            revision_key=_revision_key(model),
            direct_state_key=_direct_state_key(model),
            material_state_key=_material_state_key(model),
            items=item_tuple,
            item_by_id=MappingProxyType(
                {item.element_id: item for item in item_tuple}
            ),
            setup_seconds=float(time.perf_counter() - start),
            retained_bytes=int(retained_bytes),
            isotropic_s4=isotropic_s4,
            reference_s3=reference_s3,
            reference_s3_candidate_ids=reference_s3_candidate_ids,
            reference_s3_fallback_reasons=reference_s3_fallback_reasons,
        )

    def is_valid(self, model: "FEModel") -> bool:
        return (
            self.revision_key == _revision_key(model)
            and self.direct_state_key == _direct_state_key(model)
            and self.material_state_key == _material_state_key(model)
        )

    def select(self, element_ids: Iterable[int]) -> Tuple[RecoveryPlanItem, ...]:
        wanted = {int(element_id) for element_id in element_ids}
        return tuple(item for item in self.items if item.element_id in wanted)


def get_recovery_batch_plan(model: "FEModel") -> Tuple[RecoveryBatchPlan, bool]:
    """Return the mesh-owned plan and whether it was reused."""

    cached = getattr(model.mesh, "_recovery_batch_plan", None)
    if isinstance(cached, RecoveryBatchPlan) and cached.is_valid(model):
        return cached, True
    plan = RecoveryBatchPlan.build(model)
    model.mesh._recovery_batch_plan = plan
    return plan, False


@dataclass(frozen=True)
class RecoveryS4Batch:
    element_ids: np.ndarray
    index_by_id: Mapping[int, int]
    coords: np.ndarray
    dof_mappings: np.ndarray
    q_local: np.ndarray
    g_local: np.ndarray
    thickness: np.ndarray
    gauss_points: np.ndarray

    @property
    def retained_bytes(self) -> int:
        return int(
            self.element_ids.nbytes
            + self.coords.nbytes
            + self.dof_mappings.nbytes
            + self.q_local.nbytes
            + self.g_local.nbytes
            + self.thickness.nbytes
            + self.gauss_points.nbytes
        )

    def select_indices(self, element_ids: Iterable[int]) -> np.ndarray:
        return np.asarray(
            [
                self.index_by_id[int(element_id)]
                for element_id in element_ids
                if int(element_id) in self.index_by_id
            ],
            dtype=np.intp,
        )


def clear_recovery_batch_plan(model: "FEModel") -> None:
    if hasattr(model.mesh, "_recovery_batch_plan"):
        delattr(model.mesh, "_recovery_batch_plan")


def formulation_counts(
    items: Sequence[RecoveryPlanItem],
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        counts[item.formulation] = counts.get(item.formulation, 0) + 1
    return counts


def _split_evenly(
    items: Sequence[RecoveryPlanItem], chunk_count: int
) -> Tuple[Tuple[RecoveryPlanItem, ...], ...]:
    if not items:
        return ()
    count = max(1, min(int(chunk_count), len(items)))
    chunk_size = int(math.ceil(len(items) / count))
    return tuple(
        tuple(items[start : start + chunk_size])
        for start in range(0, len(items), chunk_size)
    )


def build_recovery_chunks(
    items: Sequence[RecoveryPlanItem],
    worker_count: int,
    *,
    chunks_per_worker: int = 3,
) -> Tuple[Tuple[RecoveryPlanItem, ...], ...]:
    """Build coarse formulation-homogeneous chunks in deterministic order."""

    if not items:
        return ()
    groups: "OrderedDict[str, list[RecoveryPlanItem]]" = OrderedDict()
    for item in items:
        groups.setdefault(item.formulation, []).append(item)
    target = min(
        len(items),
        max(len(groups), max(int(worker_count), 1) * int(chunks_per_worker)),
    )
    chunks = []
    total = len(items)
    for group_items in groups.values():
        proportional = max(
            1,
            int(round(target * len(group_items) / total)),
        )
        chunks.extend(_split_evenly(group_items, proportional))
    return tuple(chunks)
