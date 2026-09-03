"""Private bounded batches for qualified planar Q4 stress recovery.

The qualified E4-PL Q4 recovery is a stationary mixed calculation.  It must
never enter the legacy MITC4 batch kernel: doing so changes its transverse
shear fields.  This module caches only the exact, geometry- and
material-bound *linear recovery operators* for a deliberately narrow set of
homogeneous planar Q4s.  Every direct batch operation is guarded by the
qualified-Q4 runtime lease; all unsupported or stale cases stay on the public
scalar recovery oracle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np

from .e4_pl_element import (
    DIRECTOR_POLARITY_POLICY_ID,
    DIRECTOR_REVERSAL_TRANSFORM_ID,
    FORMULATION_ID,
    IMPLEMENTATION_ID,
    RECOVERY_POLICY_ID,
    QualifiedE4PLShellElement,
    _GAUSS,
    _coefficients,
    _compatible,
    _global_transform,
    _invalidate_q4_guarded_call_caches as _INVALIDATE_Q4_GUARDED_CACHES,
    _q4_runtime_epoch_manager as _Q4_RUNTIME_EPOCH_MANAGER,
    _require_exact_q4_runtime_authority as _EXACT_Q4_RUNTIME_GUARD,
    _solve_stationary_system,
    _source_fields,
    _stationary_blocks,
    equation7_frame,
)
from .e4_pl_s3_state import (
    require_exact_numpy_runtime_authority as _EXACT_NUMPY_RUNTIME_GUARD,
)
from .materials import is_isotropic_material
from .shell_sections import (
    SHELL_MEMBRANE_VOIGT_ORDER,
    SHELL_TRANSVERSE_SHEAR_ORDER,
)

if TYPE_CHECKING:
    from .fe_core import FEModel


REFERENCE_Q4_FORMULATION_ID = FORMULATION_ID
REFERENCE_Q4_BATCH_POLICY_ID = "QUALIFIED_Q4_PLANAR_EXACT_RECOVERY_PLAN_V1"
# The plan stores one direct stationary kernel per distinct local Q4 geometry.
# For uniform panels that is normally one kernel, so even a 2x2 panel avoids
# rebuilding the same stationary system four times.  Empirical scalar-versus-
# plan measurements show that four elements are already break-even on the
# first call and materially faster on every warm recovery.  Keep singleton
# and paired selections on the low-setup scalar oracle.
MIN_REFERENCE_Q4_RECOVERY_GROUP = 4
_PHYSICAL_EXTERNAL_INDICES = np.asarray(
    tuple(index for node in range(4) for index in range(6 * node, 6 * node + 5)),
    dtype=np.intp,
)


def _readonly(values: np.ndarray) -> np.ndarray:
    made = np.ascontiguousarray(values)
    return np.frombuffer(made.tobytes(order="C"), dtype=made.dtype).reshape(
        made.shape
    )


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
    rows = []
    for name in sorted(str(value) for value in model.materials):
        material = model.get_material(name)
        rows.append(
            (
                name,
                type(material).__module__,
                type(material).__qualname__,
                id(material),
                bool(is_isotropic_material(material)),
                float(getattr(material, "elastic_modulus", math.nan)),
                float(getattr(material, "poisson_ratio", math.nan)),
                id(getattr(material, "hill_yield", None)),
                id(getattr(material, "hardening_curve", None)),
            )
        )
    return tuple(rows)


def _bind_reference_q4_runtime_authority(
    numerical_guard: Any,
    element_guard: Any,
    exact_type: type[Any],
) -> Any:
    def require(model: "FEModel", *, context: str) -> None:
        numerical_guard(context=context)
        for element in tuple(model.mesh.elements.values()):
            if type(element) is exact_type:
                element_guard(element, context=context)

    return require


_REQUIRE_REFERENCE_Q4_RUNTIME_AUTHORITY = _bind_reference_q4_runtime_authority(
    _EXACT_NUMPY_RUNTIME_GUARD,
    _EXACT_Q4_RUNTIME_GUARD,
    QualifiedE4PLShellElement,
)


def _capture_reference_q4_runtime_lease(
    model: "FEModel",
    *,
    context: str,
) -> Any:
    """Capture one non-renewable Q4 generation for a direct batch call."""

    runtime_guard = _REQUIRE_REFERENCE_Q4_RUNTIME_AUTHORITY
    generation = _Q4_RUNTIME_EPOCH_MANAGER.capture_generation()
    runtime_guard(model, context=context)
    _Q4_RUNTIME_EPOCH_MANAGER.require_generation(generation)
    exact_elements = tuple(
        element
        for element in tuple(model.mesh.elements.values())
        if type(element) is QualifiedE4PLShellElement
    )

    def invalidate() -> None:
        for element in exact_elements:
            _INVALIDATE_Q4_GUARDED_CACHES(element)
        namespace = object.__getattribute__(model.mesh, "__dict__")
        if type(namespace) is dict:
            dict.pop(namespace, "_recovery_batch_plan", None)

    def require(expected_model: "FEModel", *, context: str) -> None:
        try:
            if expected_model is not model:
                raise ValueError("qualified Q4 recovery batch model changed")
            _Q4_RUNTIME_EPOCH_MANAGER.require_generation(generation)
            runtime_guard(model, context=context)
            _Q4_RUNTIME_EPOCH_MANAGER.require_generation(generation)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            invalidate()
            raise

    return require


def _run_with_reference_q4_runtime_lease(
    model: "FEModel",
    *,
    context: str,
    operation: Any,
) -> Any:
    lease = _capture_reference_q4_runtime_lease(
        model,
        context=f"{context} preflight",
    )
    try:
        result = operation(lease)
    except BaseException:
        lease(model, context=f"{context} exceptional output")
        raise
    lease(model, context=f"{context} output")
    return result


def _is_exact_qualified_q4(element: Any) -> bool:
    return (
        type(element) is QualifiedE4PLShellElement
        and getattr(element, "formulation_id", None) == REFERENCE_Q4_FORMULATION_ID
    )


def reference_q4_candidate(element: Any) -> bool:
    """Return whether an element has the exact qualified-Q4 class identity."""

    return _is_exact_qualified_q4(element)


def reference_q4_eligibility(
    model: "FEModel",
    element: Any,
) -> Tuple[bool, str]:
    """Classify the narrow homogeneous planar Q4 recovery contract."""

    if not _is_exact_qualified_q4(element):
        return False, "not_exact_qualified_q4"
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
    thickness = float(getattr(element, "thickness", math.nan))
    if not math.isfinite(thickness) or thickness <= 0.0:
        return False, "invalid_thickness"
    coordinates = np.asarray(element.get_node_coordinates(model.mesh), dtype=float)
    if coordinates.shape != (4, 3) or not np.all(np.isfinite(coordinates)):
        return False, "invalid_geometry"
    _frame, _local, warpage = equation7_frame(coordinates)
    if not math.isfinite(warpage) or warpage > float(element.planar_tolerance):
        return False, "warped_geometry"
    return True, "eligible_planar_homogeneous_isotropic_q4"


@dataclass(frozen=True)
class ReferenceQ4RecoveryKernel:
    physical_frame: np.ndarray
    local_transform: np.ndarray
    stationary_solution: np.ndarray
    source_stress: np.ndarray
    source_strain: np.ndarray
    compatible: np.ndarray
    membrane_map: np.ndarray
    curvature_map: np.ndarray
    shear_map: np.ndarray
    thickness: float
    director_sign: int
    physical_director_authoritative: bool

    @property
    def retained_bytes(self) -> int:
        return int(
            self.physical_frame.nbytes
            + self.local_transform.nbytes
            + self.stationary_solution.nbytes
            + self.source_stress.nbytes
            + self.source_strain.nbytes
            + self.compatible.nbytes
            + self.membrane_map.nbytes
            + self.curvature_map.nbytes
            + self.shear_map.nbytes
        )


@dataclass(frozen=True)
class ReferenceQ4RecoveryBatch:
    revision_key: Tuple[int, int, int]
    direct_state_key: Tuple[int, int, int, int]
    material_state_key: Tuple[Tuple[object, ...], ...]
    element_ids: np.ndarray
    index_by_id: Mapping[int, int]
    dof_mappings: np.ndarray
    kernel_index_by_row: np.ndarray
    kernels: Tuple[ReferenceQ4RecoveryKernel, ...]

    @property
    def retained_bytes(self) -> int:
        return int(
            self.element_ids.nbytes
            + self.dof_mappings.nbytes
            + self.kernel_index_by_row.nbytes
            + sum(kernel.retained_bytes for kernel in self.kernels)
        )

    def is_valid(self, model: "FEModel") -> bool:
        return (
            self.revision_key == _revision_key(model)
            and self.direct_state_key == _direct_state_key(model)
            and self.material_state_key == _material_state_key(model)
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


def _build_reference_q4_recovery_batch_under_lease(
    model: "FEModel",
    items: Sequence[Tuple[int, Any, np.ndarray]],
    *,
    minimum_group_size: int,
    _runtime_lease: Any,
) -> Tuple[ReferenceQ4RecoveryBatch | None, Mapping[str, Tuple[int, ...]]]:
    _runtime_lease(model, context="qualified Q4 recovery batch input")
    minimum = max(1, int(minimum_group_size))
    eligible: list[Tuple[int, Any, np.ndarray]] = []
    reasons: Dict[str, list[int]] = {}
    for element_id, element, mapping in items:
        allowed, reason = reference_q4_eligibility(model, element)
        if allowed:
            made_mapping = np.asarray(mapping, dtype=np.intp).reshape(-1)
            if made_mapping.shape != (24,):
                reasons.setdefault("invalid_dof_mapping", []).append(int(element_id))
            else:
                eligible.append((int(element_id), element, made_mapping))
        else:
            reasons.setdefault(reason, []).append(int(element_id))
    if len(eligible) < minimum:
        if eligible:
            reasons.setdefault("below_minimum_group_size", []).extend(
                element_id for element_id, _element, _mapping in eligible
            )
        return None, MappingProxyType(
            {name: tuple(values) for name, values in sorted(reasons.items())}
        )

    element_ids = []
    mappings = []
    kernel_index_by_row = []
    kernels = []
    kernel_indices: Dict[Tuple[object, ...], int] = {}
    for element_id, element, mapping in eligible:
        coordinates = np.asarray(element.get_node_coordinates(model.mesh), dtype=float)
        numbered_frame, local, warpage = equation7_frame(coordinates)
        if warpage > float(element.planar_tolerance):
            raise ValueError("qualified Q4 recovery plan encountered warped geometry")
        coefficients = _coefficients(local)
        constitutive = element._constitutive_and_drill_stiffness(
            model.get_material(element.material_name),
            numbered_frame,
        )[0]
        physical_frame, membrane_map, curvature_map, shear_map, director_sign = (
            element._physical_director_context(numbered_frame)
        )
        kernel_key = (
            np.ascontiguousarray(local, dtype=np.float64).tobytes(order="C"),
            np.ascontiguousarray(numbered_frame, dtype=np.float64).tobytes(
                order="C"
            ),
            np.ascontiguousarray(constitutive, dtype=np.float64).tobytes(order="C"),
            np.ascontiguousarray(physical_frame, dtype=np.float64).tobytes(
                order="C"
            ),
            np.ascontiguousarray(membrane_map, dtype=np.float64).tobytes(order="C"),
            np.ascontiguousarray(curvature_map, dtype=np.float64).tobytes(order="C"),
            np.ascontiguousarray(shear_map, dtype=np.float64).tobytes(order="C"),
            float(element.thickness),
            int(director_sign),
            element.reference_normal is not None,
        )
        kernel_index = kernel_indices.get(kernel_key)
        if kernel_index is None:
            stationary, coupling, _gram = _stationary_blocks(
                local,
                coefficients,
                constitutive,
            )
            solution, _diagnostics = _solve_stationary_system(stationary, coupling)
            source_stress = []
            source_strain = []
            compatible = []
            for r, s in _GAUSS:
                n_sigma, n_epsilon = _source_fields(coefficients, float(r), float(s))
                source_stress.append(n_sigma)
                source_strain.append(n_epsilon)
                compatible.append(
                    _compatible(local, coefficients, float(r), float(s))
                )
            kernel_index = len(kernels)
            kernel_indices[kernel_key] = kernel_index
            kernels.append(
                ReferenceQ4RecoveryKernel(
                    physical_frame=_readonly(np.asarray(physical_frame, dtype=float)),
                    local_transform=_readonly(
                        np.asarray(_global_transform(numbered_frame).T, dtype=float)
                    ),
                    stationary_solution=_readonly(np.asarray(solution, dtype=float)),
                    source_stress=_readonly(np.asarray(source_stress, dtype=float)),
                    source_strain=_readonly(np.asarray(source_strain, dtype=float)),
                    compatible=_readonly(np.asarray(compatible, dtype=float)),
                    membrane_map=_readonly(np.asarray(membrane_map, dtype=float)),
                    curvature_map=_readonly(np.asarray(curvature_map, dtype=float)),
                    shear_map=_readonly(np.asarray(shear_map, dtype=float)),
                    thickness=float(element.thickness),
                    director_sign=int(director_sign),
                    physical_director_authoritative=element.reference_normal is not None,
                )
            )
        element_ids.append(int(element_id))
        mappings.append(mapping)
        kernel_index_by_row.append(kernel_index)
    _runtime_lease(model, context="qualified Q4 recovery kernel observation")
    batch = ReferenceQ4RecoveryBatch(
        revision_key=_revision_key(model),
        direct_state_key=_direct_state_key(model),
        material_state_key=_material_state_key(model),
        element_ids=_readonly(np.asarray(element_ids, dtype=np.int64)),
        index_by_id=MappingProxyType(
            {element_id: index for index, element_id in enumerate(element_ids)}
        ),
        dof_mappings=_readonly(np.asarray(mappings, dtype=np.intp)),
        kernel_index_by_row=_readonly(np.asarray(kernel_index_by_row, dtype=np.intp)),
        kernels=tuple(kernels),
    )
    return batch, MappingProxyType(
        {name: tuple(values) for name, values in sorted(reasons.items())}
    )


def build_reference_q4_recovery_batch(
    model: "FEModel",
    items: Sequence[Tuple[int, Any, np.ndarray]],
    *,
    minimum_group_size: int = MIN_REFERENCE_Q4_RECOVERY_GROUP,
) -> Tuple[ReferenceQ4RecoveryBatch | None, Mapping[str, Tuple[int, ...]]]:
    """Build a qualified-Q4 plan under one direct-call authority lease."""

    frozen_items = tuple(items)
    return _run_with_reference_q4_runtime_lease(
        model,
        context="qualified Q4 recovery batch",
        operation=lambda lease: _build_reference_q4_recovery_batch_under_lease(
            model,
            frozen_items,
            minimum_group_size=minimum_group_size,
            _runtime_lease=lease,
        ),
    )


def _physicalize_fields(
    numbered: np.ndarray,
    kernel: ReferenceQ4RecoveryKernel,
) -> np.ndarray:
    return np.column_stack(
        (
            numbered[:, :3] @ kernel.membrane_map.T,
            numbered[:, 3:6] @ kernel.curvature_map.T,
            numbered[:, 6:] @ kernel.shear_map.T,
        )
    )


def _recover_with_kernel(
    kernel: ReferenceQ4RecoveryKernel,
    element_displacements: np.ndarray,
    *,
    return_global: bool,
) -> Dict[str, Any]:
    vector = np.asarray(element_displacements, dtype=float).reshape(24)
    if not np.all(np.isfinite(vector)):
        raise ValueError("qualified Q4 recovery requires finite displacements")
    local_displacement = kernel.local_transform @ vector
    stationary_parameters = -kernel.stationary_solution @ local_displacement
    stress_parameters = stationary_parameters[:14]
    strain_parameters = stationary_parameters[14:]
    physical_displacement = local_displacement[_PHYSICAL_EXTERNAL_INDICES]
    numbered_independent = np.asarray(
        [source @ strain_parameters for source in kernel.source_strain],
        dtype=float,
    )
    numbered_compatible = np.asarray(
        [operator @ physical_displacement for operator in kernel.compatible],
        dtype=float,
    )
    numbered_resultants = np.asarray(
        [source @ stress_parameters for source in kernel.source_stress],
        dtype=float,
    )
    independent = _physicalize_fields(numbered_independent, kernel)
    compatible = _physicalize_fields(numbered_compatible, kernel)
    resultants = _physicalize_fields(numbered_resultants, kernel)
    station_count = int(resultants.shape[0])
    frame = np.asarray(kernel.physical_frame, dtype=float)
    recovered: Dict[str, Any] = {
        "recovery_scope": (
            "qualified_q4_local_and_global_physical"
            if return_global
            else "qualified_q4_local_physical_only"
        ),
        "physical_stress_available": True,
        "membrane_resultant_order": SHELL_MEMBRANE_VOIGT_ORDER,
        "transverse_shear_resultant_order": SHELL_TRANSVERSE_SHEAR_ORDER,
        "membrane_strain": independent[:, :3].copy(),
        "curvature": independent[:, 3:6].copy(),
        "transverse_shear_strain": independent[:, 6:].copy(),
        "compatible_membrane_strain": compatible[:, :3].copy(),
        "compatible_curvature": compatible[:, 3:6].copy(),
        "compatible_transverse_shear_strain": compatible[:, 6:].copy(),
        "membrane_resultants": resultants[:, :3].copy(),
        "bending_resultants": resultants[:, 3:6].copy(),
        "transverse_shear_resultants": resultants[:, 6:].copy(),
        "numerical_fields_excluded": True,
        "implementation_id": IMPLEMENTATION_ID,
        "recovery_policy_id": RECOVERY_POLICY_ID,
        "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
        "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
        "physical_director_authoritative": (
            kernel.physical_director_authoritative
        ),
        "physical_director": frame[:, 2].copy(),
        "numbered_frame_director_sign": int(kernel.director_sign),
    }
    if return_global:
        global_membrane = np.zeros((station_count, 3, 3), dtype=float)
        global_bending = np.zeros_like(global_membrane)
        global_shear = np.zeros((station_count, 3), dtype=float)
        for index in range(station_count):
            membrane = resultants[index, :3]
            bending = resultants[index, 3:6]
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
            global_membrane[index] = frame @ membrane_tensor @ frame.T
            global_bending[index] = frame @ bending_tensor @ frame.T
            global_shear[index] = (
                resultants[index, 6] * frame[:, 0]
                + resultants[index, 7] * frame[:, 1]
            )
        recovered.update(
            {
                "global_membrane_resultant_tensors": global_membrane,
                "global_bending_resultant_tensors": global_bending,
                "global_transverse_shear_resultants": global_shear,
            }
        )

    thickness = float(kernel.thickness)
    membrane_stress = resultants[:, :3] / thickness
    bending_stress = 6.0 * resultants[:, 3:6] / (thickness * thickness)
    transverse = resultants[:, 6:] / thickness
    recovered.update(
        {
            "membrane_xx": membrane_stress[:, 0].copy(),
            "membrane_yy": membrane_stress[:, 1].copy(),
            "membrane_xy": membrane_stress[:, 2].copy(),
            "bending_xx": bending_stress[:, 0].copy(),
            "bending_yy": bending_stress[:, 1].copy(),
            "bending_xy": bending_stress[:, 2].copy(),
            "shear_xz": transverse[:, 0].copy(),
            "shear_yz": transverse[:, 1].copy(),
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
        * (bottom[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2)
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
            local_tensors[:, 0, 2] = transverse[:, 0]
            local_tensors[:, 2, 0] = transverse[:, 0]
            local_tensors[:, 1, 2] = transverse[:, 1]
            local_tensors[:, 2, 1] = transverse[:, 1]
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
                f"qualified Q4 recovery produced non-finite field {name!r}"
            )
    return recovered


def _recover_reference_q4_under_lease(
    model: "FEModel",
    batch: ReferenceQ4RecoveryBatch,
    selected_indices: np.ndarray,
    displacements: np.ndarray,
    *,
    return_global: bool,
    _runtime_lease: Any,
) -> Mapping[int, Dict[str, Any]]:
    _runtime_lease(model, context="qualified Q4 recovery validity preflight")
    if not batch.is_valid(model):
        raise ValueError("qualified Q4 recovery batch is stale after a model revision")
    _runtime_lease(model, context="qualified Q4 recovery validity observation")
    vector = np.asarray(displacements, dtype=float).reshape(-1)
    indices = np.asarray(selected_indices, dtype=np.intp).reshape(-1)
    recovered: Dict[int, Dict[str, Any]] = {}
    for raw_index in indices:
        index = int(raw_index)
        element_id = int(batch.element_ids[index])
        mapping = np.asarray(batch.dof_mappings[index], dtype=np.intp)
        if (
            mapping.size != 24
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


def recover_reference_q4(
    model: "FEModel",
    batch: ReferenceQ4RecoveryBatch,
    selected_indices: np.ndarray,
    displacements: np.ndarray,
    *,
    return_global: bool,
) -> Mapping[int, Dict[str, Any]]:
    """Recover Q4 rows through frozen formulation-native operators."""

    return _run_with_reference_q4_runtime_lease(
        model,
        context="qualified Q4 recovery",
        operation=lambda lease: _recover_reference_q4_under_lease(
            model,
            batch,
            selected_indices,
            displacements,
            return_global=return_global,
            _runtime_lease=lease,
        ),
    )
