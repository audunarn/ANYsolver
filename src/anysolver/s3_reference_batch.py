"""Private bounded batches for the qualified S3 reference-elastic path.

The qualified companion must never enter the legacy TRI3 or qualified-Q4
kernels.  This module therefore provides a deliberately small optimization:
translation-equivalent S3 elements share one formulation-native component
construction while every element retains its own copied, revision-bound
cache.  Recovery continues through the element's public native recovery
routine, so its quality, rank, bubble and provenance guards remain the
numerical authority.

Only homogeneous, isotropic, reference-elastic, zero-reference-offset,
positive-winding candidates are admitted.  Generalized sections,
anisotropy/Hill data, material history, nonzero reference-surface offsets,
non-positive winding and small groups remain on the scalar path.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np

from .materials import is_isotropic_material
from .shell_sections import (
    SHELL_MEMBRANE_VOIGT_ORDER,
    SHELL_TRANSVERSE_SHEAR_ORDER,
)

if TYPE_CHECKING:
    from .fe_core import FEModel


REFERENCE_S3_FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V1"
REFERENCE_S3_BATCH_POLICY_ID = (
    "QUALIFIED_S3_REFERENCE_ELASTIC_EXACT_TRANSLATION_GROUP_V1"
)
MIN_REFERENCE_S3_STIFFNESS_GROUP = 8
MIN_REFERENCE_S3_RECOVERY_GROUP = 128


def _readonly(values: np.ndarray) -> np.ndarray:
    made = np.ascontiguousarray(values)
    made.setflags(write=False)
    return made


def _revision_key(model: "FEModel") -> Tuple[int, int, int]:
    revisions = model.mesh.revision_signature()
    return (
        int(revisions.get("topology", 0)),
        int(revisions.get("geometry", 0)),
        int(revisions.get("material", 0)),
    )


def _is_exact_qualified_s3(element: Any) -> bool:
    # Import lazily: the formulation imports ShellElement and must not become a
    # dependency of generic model construction.
    from .e4_pl_s3_element import QualifiedE4PLS3ShellElement

    return (
        type(element) is QualifiedE4PLS3ShellElement
        and getattr(element, "formulation_id", None)
        == REFERENCE_S3_FORMULATION_ID
    )


def reference_s3_candidate(element: Any) -> bool:
    """Return whether an element belongs to the exact qualified S3 class."""

    return _is_exact_qualified_s3(element)


def reference_s3_eligibility(
    model: "FEModel",
    element: Any,
) -> Tuple[bool, str]:
    """Classify the narrow reference-elastic S3 batch contract."""

    if not _is_exact_qualified_s3(element):
        return False, "not_exact_qualified_s3"
    if bool(getattr(element, "legacy_stiffness_batch_eligible", True)):
        return False, "legacy_stiffness_flag_not_false"
    if bool(getattr(element, "legacy_nonlinear_batch_eligible", True)):
        return False, "legacy_nonlinear_flag_not_false"
    if getattr(element, "shell_section", None) is not None:
        return False, "generalized_section"
    material = model.get_material(element.material_name)
    if not is_isotropic_material(material):
        return False, "orthotropic_or_anisotropic_material"
    if getattr(material, "hill_yield", None) is not None:
        return False, "hill_material"
    if getattr(material, "hardening_curve", None) is not None:
        return False, "material_history"
    if getattr(element, "material_direction", None) is not None:
        return False, "oriented_material"
    if float(getattr(element, "material_angle_deg", 0.0)) != 0.0:
        return False, "material_angle"
    reference_surface_offset = float(
        getattr(element, "reference_surface_offset", 0.0)
    )
    if not math.isfinite(reference_surface_offset):
        return False, "invalid_reference_surface_offset"
    if reference_surface_offset != 0.0:
        return False, "nonzero_reference_surface_offset"
    thickness = float(getattr(element, "thickness", math.nan))
    if not math.isfinite(thickness) or thickness <= 0.0:
        return False, "invalid_thickness"

    coordinates = np.asarray(
        element.get_node_coordinates(model.mesh), dtype=float
    )
    normal = np.asarray(getattr(element, "reference_normal", ()), dtype=float)
    if (
        coordinates.shape != (3, 3)
        or normal.shape != (3,)
        or not np.all(np.isfinite(coordinates))
        or not np.all(np.isfinite(normal))
    ):
        return False, "invalid_geometry_or_reference_normal"
    signed_area_twice = float(
        np.dot(
            np.cross(coordinates[1] - coordinates[0], coordinates[2] - coordinates[0]),
            normal,
        )
    )
    if not math.isfinite(signed_area_twice) or signed_area_twice <= 0.0:
        return False, "nonpositive_winding"
    return True, "eligible_reference_elastic_isotropic_positive_winding"


def _component_key(model: "FEModel", element: Any) -> Tuple[Any, ...]:
    """Return the formulation's own exact, revision-bound component key."""

    material = model.get_material(element.material_name)
    coordinates = np.asarray(
        element.get_node_coordinates(model.mesh), dtype=float
    )
    # ``True`` is the public production path's positive-winding guard and is
    # part of the QualifiedE4PLS3ShellElement cache identity.
    return (*element._cache_key(model.mesh, material, coordinates), True)


def _copy_components(components: Mapping[str, Any]) -> Dict[str, Any]:
    copied: Dict[str, Any] = {}
    for name, value in components.items():
        if isinstance(value, np.ndarray):
            copied[name] = value.copy()
        else:
            copied[name] = copy.deepcopy(value)
    return copied


def _adopt_components(
    element: Any,
    cache_key: Tuple[Any, ...],
    components: Mapping[str, Any],
) -> np.ndarray:
    copied = _copy_components(components)
    element._qualified_components = copied
    element._qualified_cache_key = cache_key
    element._hourglass_stiffness_matrix = np.asarray(
        copied["hourglass"], dtype=float
    )
    element._stiffness_matrix = np.asarray(copied["total"], dtype=float)
    return element._stiffness_matrix


@dataclass(frozen=True)
class PreparedReferenceS3Components:
    matrices: Mapping[int, np.ndarray]
    batched_element_ids: Tuple[int, ...]
    group_element_ids: Tuple[Tuple[int, ...], ...]
    candidate_element_ids: Tuple[int, ...]
    fallback_reasons: Mapping[str, Tuple[int, ...]]
    component_evaluation_count: int
    revision_key: Tuple[int, int, int]
    minimum_group_size: int

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "policy_id": REFERENCE_S3_BATCH_POLICY_ID,
            "formulation_id": REFERENCE_S3_FORMULATION_ID,
            "scope": "reference_elastic_isotropic_positive_winding",
            "path": "formulation_native_shared_components",
            "candidate_element_count": len(self.candidate_element_ids),
            "element_count": len(self.batched_element_ids),
            "exact_translation_group_count": len(self.group_element_ids),
            "component_evaluation_count": int(self.component_evaluation_count),
            "element_ids": list(self.batched_element_ids),
            "group_element_ids": [list(group) for group in self.group_element_ids],
            "fallback_reasons": {
                reason: list(element_ids)
                for reason, element_ids in self.fallback_reasons.items()
            },
            "revision_key": list(self.revision_key),
            "parallel_kernel": False,
            "legacy_stiffness_batch_eligible": False,
            "legacy_nonlinear_batch_eligible": False,
            "speedup_claimed": False,
        }


def prepare_reference_s3_components(
    model: "FEModel",
    items: Sequence[Tuple[int, Any]],
    *,
    minimum_group_size: int = MIN_REFERENCE_S3_STIFFNESS_GROUP,
) -> PreparedReferenceS3Components:
    """Prepare one validated component evaluation per exact cache-key group."""

    minimum = max(1, int(minimum_group_size))
    candidate_ids: list[int] = []
    groups: Dict[Tuple[Any, ...], list[Tuple[int, Any]]] = {}
    fallback: Dict[str, list[int]] = {}
    for raw_element_id, element in items:
        element_id = int(raw_element_id)
        if not reference_s3_candidate(element):
            continue
        candidate_ids.append(element_id)
        eligible, reason = reference_s3_eligibility(model, element)
        if not eligible:
            fallback.setdefault(reason, []).append(element_id)
            continue
        groups.setdefault(_component_key(model, element), []).append(
            (element_id, element)
        )

    matrices: Dict[int, np.ndarray] = {}
    admitted_groups: list[Tuple[int, ...]] = []
    evaluation_count = 0
    for cache_key, group in groups.items():
        ordered_group = tuple(int(element_id) for element_id, _element in group)
        if len(group) < minimum:
            fallback.setdefault("group_below_minimum_size", []).extend(ordered_group)
            continue
        first_id, first = group[0]
        material = model.get_material(first.material_name)
        components = first.compute_stiffness_components(model.mesh, material)
        evaluation_count += 1
        if (
            components.get("formulation_id") != REFERENCE_S3_FORMULATION_ID
            or bool(components.get("legacy_fallback", True))
        ):
            raise ValueError(
                "qualified S3 reference batch received incompatible component provenance"
            )
        if tuple(first._qualified_cache_key) != tuple(cache_key):
            raise ValueError(
                "qualified S3 reference batch component cache identity changed during evaluation"
            )
        matrices[int(first_id)] = np.asarray(components["total"], dtype=float)
        for element_id, element in group[1:]:
            current = getattr(element, "_qualified_components", None)
            current_key = getattr(element, "_qualified_cache_key", None)
            if current is not None and current_key == cache_key:
                matrices[int(element_id)] = np.asarray(
                    current["total"], dtype=float
                )
            else:
                matrices[int(element_id)] = _adopt_components(
                    element,
                    cache_key,
                    components,
                )
        admitted_groups.append(ordered_group)

    frozen_matrices = MappingProxyType(
        {
            int(element_id): np.asarray(matrix, dtype=float)
            for element_id, matrix in matrices.items()
        }
    )
    frozen_fallback = MappingProxyType(
        {
            reason: tuple(sorted(int(element_id) for element_id in element_ids))
            for reason, element_ids in sorted(fallback.items())
        }
    )
    return PreparedReferenceS3Components(
        matrices=frozen_matrices,
        batched_element_ids=tuple(
            int(element_id)
            for element_id, _element in items
            if int(element_id) in frozen_matrices
        ),
        group_element_ids=tuple(admitted_groups),
        candidate_element_ids=tuple(candidate_ids),
        fallback_reasons=frozen_fallback,
        component_evaluation_count=int(evaluation_count),
        revision_key=_revision_key(model),
        minimum_group_size=minimum,
    )


def get_reference_s3_stiffness_components(
    model: "FEModel",
    items: Sequence[Tuple[int, Any]],
    *,
    minimum_group_size: int = MIN_REFERENCE_S3_STIFFNESS_GROUP,
) -> Tuple[PreparedReferenceS3Components, bool]:
    """Return a mesh-owned admitted plan and whether it was reused."""

    candidate_ids = tuple(int(element_id) for element_id, _element in items)
    revision = _revision_key(model)
    minimum = max(1, int(minimum_group_size))
    cached = getattr(
        model.mesh,
        "_qualified_s3_reference_stiffness_plan",
        None,
    )
    if (
        isinstance(cached, PreparedReferenceS3Components)
        and cached.revision_key == revision
        and cached.minimum_group_size == minimum
        and cached.candidate_element_ids == candidate_ids
        and bool(cached.batched_element_ids)
    ):
        return cached, True
    prepared = prepare_reference_s3_components(
        model,
        items,
        minimum_group_size=minimum,
    )
    if prepared.batched_element_ids:
        model.mesh._qualified_s3_reference_stiffness_plan = prepared
    elif hasattr(model.mesh, "_qualified_s3_reference_stiffness_plan"):
        delattr(model.mesh, "_qualified_s3_reference_stiffness_plan")
    return prepared, False


@dataclass(frozen=True)
class ReferenceS3RecoveryKernel:
    frame: np.ndarray
    local_transform: np.ndarray
    bubble_map: np.ndarray
    strain_operators: np.ndarray
    constitutive: np.ndarray
    membrane_material: np.ndarray
    shear_material: np.ndarray
    thickness: float
    director_polarity: int

    @property
    def retained_bytes(self) -> int:
        return int(
            self.frame.nbytes
            + self.local_transform.nbytes
            + self.bubble_map.nbytes
            + self.strain_operators.nbytes
            + self.constitutive.nbytes
            + self.membrane_material.nbytes
            + self.shear_material.nbytes
        )


@dataclass(frozen=True)
class ReferenceS3RecoveryBatch:
    revision_key: Tuple[int, int, int]
    element_ids: np.ndarray
    index_by_id: Mapping[int, int]
    dof_mappings: np.ndarray
    kernel_index_by_row: np.ndarray
    kernels: Tuple[ReferenceS3RecoveryKernel, ...]
    group_element_ids: Tuple[Tuple[int, ...], ...]
    component_evaluation_count: int

    @property
    def retained_bytes(self) -> int:
        return int(
            self.element_ids.nbytes
            + self.dof_mappings.nbytes
            + self.kernel_index_by_row.nbytes
            + sum(kernel.retained_bytes for kernel in self.kernels)
        )

    def is_valid(self, model: "FEModel") -> bool:
        return self.revision_key == _revision_key(model)

    def select_indices(self, element_ids: Iterable[int]) -> np.ndarray:
        return np.asarray(
            [
                self.index_by_id[int(element_id)]
                for element_id in element_ids
                if int(element_id) in self.index_by_id
            ],
            dtype=np.intp,
        )

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "policy_id": REFERENCE_S3_BATCH_POLICY_ID,
            "formulation_id": REFERENCE_S3_FORMULATION_ID,
            "scope": "reference_elastic_isotropic_positive_winding",
            "path": "formulation_native_shared_components_recovery",
            "element_count": int(self.element_ids.size),
            "exact_translation_group_count": len(self.group_element_ids),
            "component_evaluation_count": int(self.component_evaluation_count),
            "element_ids": [int(value) for value in self.element_ids],
            "group_element_ids": [list(group) for group in self.group_element_ids],
            "revision_key": list(self.revision_key),
            "parallel_kernel": False,
            "legacy_stiffness_batch_eligible": False,
            "legacy_nonlinear_batch_eligible": False,
            "speedup_claimed": False,
        }


def build_reference_s3_recovery_batch(
    model: "FEModel",
    items: Sequence[Tuple[int, Any, np.ndarray]],
    *,
    minimum_group_size: int = MIN_REFERENCE_S3_RECOVERY_GROUP,
) -> Tuple[ReferenceS3RecoveryBatch | None, PreparedReferenceS3Components]:
    """Build an immutable recovery layout for admitted large S3 groups."""

    element_items = tuple(
        (int(element_id), element)
        for element_id, element, _mapping in items
    )
    prepared = prepare_reference_s3_components(
        model,
        element_items,
        minimum_group_size=minimum_group_size,
    )
    if not prepared.batched_element_ids:
        return None, prepared
    item_by_id = {
        int(element_id): (element, np.asarray(mapping, dtype=np.intp).reshape(-1))
        for element_id, element, mapping in items
    }
    ordered_ids = tuple(prepared.batched_element_ids)
    mappings = np.asarray(
        [item_by_id[element_id][1] for element_id in ordered_ids],
        dtype=np.intp,
    )
    if mappings.shape != (len(ordered_ids), 18):
        raise ValueError("qualified S3 recovery batch requires 18 DOFs per element")
    from .e4_pl_s3_element import TRIANGLE_QUADRATURE, _kinematic_matrix
    from .elements import _shell_material_matrices

    row_by_id = {element_id: index for index, element_id in enumerate(ordered_ids)}
    kernel_index_by_row = np.empty(len(ordered_ids), dtype=np.intp)
    kernels: list[ReferenceS3RecoveryKernel] = []
    for kernel_index, group_ids in enumerate(prepared.group_element_ids):
        first = item_by_id[int(group_ids[0])][0]
        components = getattr(first, "_qualified_components", None)
        if not isinstance(components, Mapping):
            raise ValueError("qualified S3 recovery batch lacks validated components")
        frame = np.asarray(components["frame"], dtype=float)
        generalized_transform = first._director_generalized_transform()
        strain_operators = np.asarray(
            [
                generalized_transform
                @ _kinematic_matrix(
                    components["local_nodes"],
                    r,
                    s,
                    components["assumed_shear_samples"],
                )
                for r, s, _weight in TRIANGLE_QUADRATURE
            ],
            dtype=float,
        )
        material = model.get_material(first.material_name)
        membrane, shear, _strain_transform, _stress_transform = (
            _shell_material_matrices(material, first._material_angle(frame))
        )
        kernels.append(
            ReferenceS3RecoveryKernel(
                frame=_readonly(frame),
                local_transform=_readonly(first._local_dof_transform(frame)),
                bubble_map=_readonly(
                    np.asarray(components["bubble_map"], dtype=float)
                ),
                strain_operators=_readonly(strain_operators),
                constitutive=_readonly(
                    np.asarray(components["constitutive"], dtype=float)
                ),
                membrane_material=_readonly(np.asarray(membrane, dtype=float)),
                shear_material=_readonly(np.asarray(shear, dtype=float)),
                thickness=float(first.thickness),
                director_polarity=int(first.director_polarity),
            )
        )
        for element_id in group_ids:
            kernel_index_by_row[row_by_id[int(element_id)]] = kernel_index
    batch = ReferenceS3RecoveryBatch(
        revision_key=_revision_key(model),
        element_ids=_readonly(np.asarray(ordered_ids, dtype=np.int64)),
        index_by_id=MappingProxyType(
            {element_id: index for index, element_id in enumerate(ordered_ids)}
        ),
        dof_mappings=_readonly(mappings),
        kernel_index_by_row=_readonly(kernel_index_by_row),
        kernels=tuple(kernels),
        group_element_ids=prepared.group_element_ids,
        component_evaluation_count=prepared.component_evaluation_count,
    )
    return batch, prepared


def _recover_with_kernel(
    kernel: ReferenceS3RecoveryKernel,
    element_displacements: np.ndarray,
    *,
    return_global: bool,
) -> Dict[str, Any]:
    """Evaluate the frozen homogeneous reference-elastic S3 recovery map."""

    from .e4_pl_s3_element import (
        HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID,
        PHYSICAL_EXTERNAL_INDICES,
        REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID,
    )
    from .e4_pl_s3_state import REFERENCE_SURFACE_OFFSET_POLICY_ID

    vector = np.asarray(element_displacements, dtype=float).reshape(18)
    if not np.all(np.isfinite(vector)):
        raise ValueError("qualified S3 recovery requires finite displacements")
    frame = np.asarray(kernel.frame, dtype=float)
    local_external = np.asarray(kernel.local_transform, dtype=float) @ vector
    physical_external = local_external[PHYSICAL_EXTERNAL_INDICES]
    bubble = np.asarray(kernel.bubble_map, dtype=float) @ physical_external
    coordinates = np.concatenate((physical_external, bubble))
    station_count = int(kernel.strain_operators.shape[0])
    strains = np.zeros((station_count, 8), dtype=float)
    resultants = np.zeros_like(strains)
    for station in range(station_count):
        strains[station] = kernel.strain_operators[station] @ coordinates
        resultants[station] = kernel.constitutive @ strains[station]

    recovered: Dict[str, Any] = {
        "recovery_scope": (
            "qualified_s3_local_and_global_physical"
            if return_global
            else "qualified_s3_local_physical_only"
        ),
        "physical_stress_available": True,
        "membrane_resultant_order": SHELL_MEMBRANE_VOIGT_ORDER,
        "transverse_shear_resultant_order": SHELL_TRANSVERSE_SHEAR_ORDER,
        "membrane_strain": strains[:, :3],
        "curvature": strains[:, 3:6],
        "transverse_shear_strain": strains[:, 6:],
        "membrane_resultants": resultants[:, :3],
        "bending_resultants": resultants[:, 3:6],
        "transverse_shear_resultants": resultants[:, 6:],
        "bubble_rotations": bubble.copy(),
        "numerical_fields_excluded": True,
        # Eligibility rejects nonzero reference-surface offsets.  Preserve the
        # scalar qualified-S3 recovery schema exactly for the admitted zero-
        # offset path so batching never changes provenance or key order.
        "reference_surface_offset": 0.0,
        "reference_surface_offset_policy_id": REFERENCE_SURFACE_OFFSET_POLICY_ID,
        "section_origin_offset_from_reference": 0.0,
        "physical_bottom_offset_from_reference": -0.5 * kernel.thickness,
        "physical_top_offset_from_reference": 0.5 * kernel.thickness,
        "bubble_linearization_policy": REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID,
        "through_thickness_stress_profile": HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID,
    }
    polarity = float(kernel.director_polarity)
    if return_global:
        global_membrane = np.zeros((station_count, 3, 3), dtype=float)
        global_bending = np.zeros_like(global_membrane)
        global_shear = np.zeros((station_count, 3), dtype=float)
        for station in range(station_count):
            membrane = resultants[station, :3]
            bending = resultants[station, 3:6]
            membrane_tensor = np.asarray(
                (
                    (membrane[0], membrane[2], 0.0),
                    (membrane[2], membrane[1], 0.0),
                    (0.0, 0.0, 0.0),
                ),
                dtype=float,
            )
            bending_tensor = np.asarray(
                (
                    (bending[0], bending[2], 0.0),
                    (bending[2], bending[1], 0.0),
                    (0.0, 0.0, 0.0),
                ),
                dtype=float,
            )
            global_membrane[station] = frame @ membrane_tensor @ frame.T
            global_bending[station] = polarity * (
                frame @ bending_tensor @ frame.T
            )
            global_shear[station] = polarity * (
                resultants[station, 6] * frame[:, 0]
                + resultants[station, 7] * frame[:, 1]
            )
        recovered.update(
            {
                "global_membrane_resultant_tensors": global_membrane,
                "global_bending_resultant_tensors": global_bending,
                "global_transverse_shear_resultants": global_shear,
            }
        )

    membrane_stress = strains[:, :3] @ kernel.membrane_material.T
    moment = resultants[:, 3:6]
    bending_stress = 6.0 * moment / (kernel.thickness * kernel.thickness)
    transverse = strains[:, 6:] @ ((5.0 / 6.0) * kernel.shear_material).T
    recovered.update(
        {
            "membrane_xx": membrane_stress[:, 0],
            "membrane_yy": membrane_stress[:, 1],
            "membrane_xy": membrane_stress[:, 2],
            "bending_xx": bending_stress[:, 0],
            "bending_yy": bending_stress[:, 1],
            "bending_xy": bending_stress[:, 2],
            "shear_xz": transverse[:, 0],
            "shear_yz": transverse[:, 1],
        }
    )
    top = membrane_stress + bending_stress
    bottom = membrane_stress - bending_stress
    vm_top = np.sqrt(
        top[:, 0] ** 2
        - top[:, 0] * top[:, 1]
        + top[:, 1] ** 2
        + 3.0
        * (top[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2)
    )
    vm_bottom = np.sqrt(
        bottom[:, 0] ** 2
        - bottom[:, 0] * bottom[:, 1]
        + bottom[:, 1] ** 2
        + 3.0
        * (
            bottom[:, 2] ** 2
            + transverse[:, 0] ** 2
            + transverse[:, 1] ** 2
        )
    )
    recovered["von_mises"] = np.maximum(vm_top, vm_bottom)
    recovered["hill_utilization"] = np.zeros(station_count, dtype=float)
    recovered["equivalent_stress"] = recovered["von_mises"].copy()
    recovered["equivalent_stress_measure"] = "von_mises"
    if return_global:
        for surface, values in (("top", top), ("bot", bottom)):
            local_tensors = np.zeros((station_count, 3, 3), dtype=float)
            local_tensors[:, 0, 0] = values[:, 0]
            local_tensors[:, 1, 1] = values[:, 1]
            local_tensors[:, 0, 1] = values[:, 2]
            local_tensors[:, 1, 0] = values[:, 2]
            owner_shear = polarity * transverse
            local_tensors[:, 0, 2] = owner_shear[:, 0]
            local_tensors[:, 2, 0] = owner_shear[:, 0]
            local_tensors[:, 1, 2] = owner_shear[:, 1]
            local_tensors[:, 2, 1] = owner_shear[:, 1]
            global_tensors = np.asarray(
                [frame @ tensor @ frame.T for tensor in local_tensors],
                dtype=float,
            )
            for first, second, label in (
                (0, 0, "xx"),
                (1, 1, "yy"),
                (2, 2, "zz"),
                (0, 1, "xy"),
                (1, 2, "yz"),
                (0, 2, "xz"),
            ):
                recovered[f"local_{label}_{surface}"] = local_tensors[
                    :, first, second
                ].copy()
                recovered[f"global_{label}_{surface}"] = global_tensors[
                    :, first, second
                ].copy()
    for name, values in recovered.items():
        if isinstance(values, np.ndarray) and not np.all(np.isfinite(values)):
            raise ValueError(
                f"qualified S3 recovery produced non-finite field {name!r}"
            )
    return recovered


def recover_reference_s3(
    model: "FEModel",
    batch: ReferenceS3RecoveryBatch,
    selected_indices: np.ndarray,
    displacements: np.ndarray,
    *,
    return_global: bool,
) -> Mapping[int, Dict[str, Any]]:
    """Recover selected S3 rows through the frozen formulation-native kernel."""

    if not batch.is_valid(model):
        raise ValueError("qualified S3 recovery batch is stale after a model revision")
    vector = np.asarray(displacements, dtype=float).reshape(-1)
    indices = np.asarray(selected_indices, dtype=np.intp).reshape(-1)
    recovered: Dict[int, Dict[str, Any]] = {}
    for raw_index in indices:
        index = int(raw_index)
        element_id = int(batch.element_ids[index])
        mapping = np.asarray(batch.dof_mappings[index], dtype=np.intp)
        if (
            mapping.size != 18
            or int(mapping.min()) < 0
            or int(mapping.max()) >= vector.size
        ):
            raise ValueError(
                "fail-closed element recovery requires a complete in-range DOF mapping"
            )
        kernel_index = int(batch.kernel_index_by_row[index])
        recovered[element_id] = _recover_with_kernel(
            batch.kernels[kernel_index],
            vector[mapping],
            return_global=bool(return_global),
        )
    return recovered
