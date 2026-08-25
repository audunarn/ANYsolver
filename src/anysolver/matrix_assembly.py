"""Explicit stiffness, mass and load assembly APIs.

This module is the step-3 public assembly interface.  It keeps K, M and F
assembly separate so modal, buckling and nonlinear solvers can choose exactly
which matrices they need without side effects.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy import sparse

if TYPE_CHECKING:
    from .boundary import LoadCase
    from .fe_core import FEModel


class AssemblyError(ValueError):
    """Raised when an element returns an invalid matrix or load contribution."""


def _element_activity(model: "FEModel") -> Any | None:
    return getattr(model.mesh, "element_activity", None)


def _activity_scales(
    model: "FEModel", quantity: str
) -> tuple[Any | None, Dict[int, float], Dict[str, Any] | None]:
    activity = _element_activity(model)
    if activity is None:
        return None, {}, None
    element_ids = tuple(int(element_id) for element_id in model.mesh.elements)
    try:
        values = np.asarray(
            activity.scales(quantity, element_ids), dtype=float
        ).reshape(-1)
    except Exception as error:
        raise AssemblyError(
            f"element activity cannot provide {quantity} scales for the FE mesh: {error}"
        ) from error
    if values.shape != (len(element_ids),) or not np.all(np.isfinite(values)):
        raise AssemblyError(f"element activity returned invalid {quantity} scales")
    scales = dict(zip(element_ids, (float(value) for value in values)))
    return activity, scales, {
        "quantity": str(quantity),
        "sequence": int(getattr(activity, "sequence", 0)),
        "element_count": len(element_ids),
        "scaled_element_count": int(np.count_nonzero(values != 1.0)),
        "zero_contribution_count": int(np.count_nonzero(values == 0.0)),
        "minimum_scale": float(np.min(values)) if len(values) else 1.0,
        "maximum_scale": float(np.max(values)) if len(values) else 1.0,
    }


def _base_info(model: "FEModel", matrix_type: str) -> Dict[str, Any]:
    mesh = model.mesh
    return {
        "matrix_type": matrix_type,
        "num_elements": 0,
        "num_nodes": mesh.num_nodes,
        "total_dofs": mesh.dof_manager.total_dofs,
        "assembly_time": 0.0,
        "element_times": {},
        "skipped_elements": [],
        "diagnostics": {},
        "revision_signature": getattr(mesh, "revision_signature", lambda: {})(),
    }


def _check_element_matrix_shape(element_id: int, matrix_name: str, matrix: np.ndarray, expected_size: int) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    expected_shape = (expected_size, expected_size)
    if matrix.shape != expected_shape:
        raise AssemblyError(
            f"Element {element_id} returned {matrix_name} with shape {matrix.shape}; "
            f"expected {expected_shape}."
        )
    if not np.all(np.isfinite(matrix)):
        raise AssemblyError(f"Element {element_id} returned non-finite values in {matrix_name}.")
    return matrix


def _relative_symmetry_error(matrix: sparse.spmatrix | np.ndarray) -> float:
    if sparse.issparse(matrix):
        diff = matrix - matrix.T
        numerator = float(sparse.linalg.norm(diff))
        denominator = max(float(sparse.linalg.norm(matrix)), 1.0)
        return numerator / denominator
    dense = np.asarray(matrix, dtype=float)
    return float(np.linalg.norm(dense - dense.T) / max(np.linalg.norm(dense), 1.0))


def _topology_signature(mesh: Any, matrix_type: str) -> str:
    revisions = getattr(mesh, "revision_signature", lambda: {})()
    cache_key = (
        str(matrix_type),
        int(revisions.get("topology", 0)),
        int(revisions.get("mpc", 0)),
    )
    cache = getattr(mesh, "_topology_signature_cache", None)
    if cache is None:
        cache = {}
        mesh._topology_signature_cache = cache
    cached = cache.get(cache_key)
    if cached is not None:
        return str(cached)

    payload = {
        "matrix_type": matrix_type,
        "topology_revision": revisions.get("topology", 0),
        "mpc_revision": revisions.get("mpc", 0),
        "elements": [
            {
                "id": int(elem_id),
                "class": element.__class__.__name__,
                "node_ids": [int(node_id) for node_id in getattr(element, "node_ids", [])],
                "dofs": [int(dof) for dof in element.get_dof_mapping(mesh)],
            }
            for elem_id, element in mesh.elements.items()
        ],
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signature = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cache[cache_key] = signature
    return signature


def _scatter_element_matrix(
    element_matrix: np.ndarray,
    dof_mapping: np.ndarray,
    rows: list,
    cols: list,
    data: list,
) -> None:
    """Append element matrix entries to COO triplet buffers (vectorized)."""
    n_local = dof_mapping.size
    values = element_matrix.ravel()
    mask = values != 0.0
    if not np.any(mask):
        return
    rows.append(np.repeat(dof_mapping, n_local)[mask])
    cols.append(np.tile(dof_mapping, n_local)[mask])
    data.append(values[mask])


def _triplets_to_csr(rows: list, cols: list, data: list, total_dofs: int) -> sparse.csr_matrix:
    """Build a CSR matrix from COO triplet buffers; duplicates are summed."""
    if not data:
        return sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
    coo = sparse.coo_matrix(
        (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
        shape=(total_dofs, total_dofs),
        dtype=float,
    )
    return coo.tocsr()


def _get_cached_sparsity_pattern(mesh: "FEMesh", matrix_type: str) -> Tuple[np.ndarray, np.ndarray]:
    """Retrieve or build the cached row and column indices for global matrix COO assembly."""
    if not hasattr(mesh, "_sparsity_cache"):
        mesh._sparsity_cache = {}

    signature = _topology_signature(mesh, matrix_type)

    if matrix_type in mesh._sparsity_cache:
        cached = mesh._sparsity_cache[matrix_type]
        if cached.get("signature") == signature:
            return cached["rows"], cached["cols"]

    rows_list = []
    cols_list = []
    for _, element in mesh.elements.items():
        dof_mapping = np.asarray(element.get_dof_mapping(mesh), dtype=np.intp)
        if dof_mapping.size == 0:
            continue
        n_local = dof_mapping.size
        rows_list.append(np.repeat(dof_mapping, n_local))
        cols_list.append(np.tile(dof_mapping, n_local))

    rows_concat = np.concatenate(rows_list) if rows_list else np.empty(0, dtype=np.intp)
    cols_concat = np.concatenate(cols_list) if cols_list else np.empty(0, dtype=np.intp)

    mesh._sparsity_cache[matrix_type] = {
        "rows": rows_concat,
        "cols": cols_concat,
        "signature": signature,
    }
    return rows_concat, cols_concat


def _assemble_element_matrix(
    model: "FEModel",
    matrix_type: str,
    element_matrix_getter: Callable[[Any, Any, Any], np.ndarray],
    *,
    activity_quantity: str | None = None,
) -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    mesh = model.mesh
    total_dofs = mesh.dof_manager.total_dofs
    info = _base_info(model, matrix_type)
    start_time = time.time()
    quantity = activity_quantity or (
        "stiffness" if matrix_type == "geometric_stiffness" else matrix_type
    )
    _activity, activity_scales, activity_info = _activity_scales(model, quantity)
    if activity_info is not None:
        info["diagnostics"]["element_activity"] = activity_info

    # Precompute shell matrices in a JIT-compiled batch for stiffness and mass assembly
    precomputed = {}
    vectorized_shell_groups = []
    if matrix_type in {"stiffness", "mass"}:
        from .elements import ShellElement
        from .jit_compiler import JIT_ENABLED, JIT_DISABLED_REASON, jit_diagnostics
        from .materials import is_isotropic_material
        from .vectorized_stiffness import compute_shell_mass_matrices_jit, compute_shell_stiffness_matrices_jit
        from .vectorized_generalized_shell import (
            prepare_s4_generalized_stiffness_batch,
            prepare_s4_section_mass_batch,
        )
        from .s3_reference_batch import (
            get_reference_s3_stiffness_components,
            reference_s3_candidate,
        )

        groups = {}
        reference_s3_items = []
        qualified_stiffness_items = []
        advanced_stiffness_items = []
        section_mass_items = []
        constitutive_fallback_ids = []
        generalized_section_fallback_ids = []
        generalized_mass_fallback_ids = []
        for elem_id, element in mesh.elements.items():
            material = model.get_material(element.material_name)
            shell_section = getattr(element, "shell_section", None)
            has_section_mass = bool(
                shell_section is not None
                and (
                    getattr(shell_section, "mass_per_area", None) is not None
                    or getattr(shell_section, "rotary_inertia_per_area", None) is not None
                )
            )
            if (
                matrix_type == "stiffness"
                and reference_s3_candidate(element)
            ):
                # Qualified S3 has a formulation-native reference-elastic
                # batch.  It must never enter either the legacy TRI3 or the
                # qualified-Q4 kernels below, including on scalar fallback.
                reference_s3_items.append((int(elem_id), element))
                continue
            if (
                matrix_type == "stiffness"
                and isinstance(element, ShellElement)
                and not bool(getattr(element, "legacy_stiffness_batch_eligible", True))
                and hasattr(element, "_qualified_stiffness_cache_key")
                and hasattr(element, "_adopt_qualified_components")
            ):
                qualified_stiffness_items.append((int(elem_id), element))
                continue
            if (
                matrix_type == "stiffness"
                and isinstance(element, ShellElement)
                and bool(getattr(element, "legacy_stiffness_batch_eligible", True))
                and bool(getattr(element, "_is_4node", False))
                and (
                    shell_section is not None
                    or not is_isotropic_material(material)
                )
            ):
                advanced_stiffness_items.append((int(elem_id), element))
                continue
            if (
                matrix_type == "mass"
                and isinstance(element, ShellElement)
                and bool(getattr(element, "_is_4node", False))
                and has_section_mass
            ):
                section_mass_items.append((int(elem_id), element))
                continue
            if (
                isinstance(element, ShellElement)
                and getattr(element, "_is_quadrilateral", False)
                and not (getattr(element, "_is_8node", False) and bool(getattr(element, "reduced_integration", False)))
                and (
                    (matrix_type == "mass" and not has_section_mass)
                    or (
                        matrix_type == "stiffness"
                        and bool(getattr(element, "legacy_stiffness_batch_eligible", True))
                        and shell_section is None
                        and is_isotropic_material(material)
                    )
                )
            ):
                key = (
                    element.num_nodes,
                    element.thickness,
                    element.drilling_stabilization,
                    element.reduced_integration,
                    element.hourglass_stabilization,
                    element.material_name,
                )
                if key not in groups:
                    groups[key] = []
                groups[key].append((elem_id, element))
            elif (
                matrix_type == "stiffness"
                and isinstance(element, ShellElement)
                and shell_section is None
                and not is_isotropic_material(material)
            ):
                constitutive_fallback_ids.append(int(elem_id))
            elif (
                matrix_type == "stiffness"
                and isinstance(element, ShellElement)
                and shell_section is not None
            ):
                generalized_section_fallback_ids.append(int(elem_id))
            elif (
                matrix_type == "mass"
                and isinstance(element, ShellElement)
                and has_section_mass
            ):
                generalized_mass_fallback_ids.append(int(elem_id))

        if constitutive_fallback_ids:
            info["diagnostics"]["constitutive_fallback"] = {
                "path": "general_element",
                "reason": "orthotropic_material",
                "element_ids": sorted(constitutive_fallback_ids),
            }
        if generalized_section_fallback_ids:
            info["diagnostics"]["generalized_shell_section_fallback"] = {
                "path": "general_element",
                "reason": "preintegrated_generalized_shell_section",
                "element_ids": sorted(generalized_section_fallback_ids),
            }
        if generalized_mass_fallback_ids:
            info["diagnostics"]["generalized_shell_section_mass_fallback"] = {
                "path": "general_element",
                "reason": "unsupported_shell_topology",
                "element_ids": sorted(generalized_mass_fallback_ids),
            }

        if reference_s3_items:
            prepared_s3, s3_plan_reused = get_reference_s3_stiffness_components(
                model,
                reference_s3_items,
            )
            precomputed.update(prepared_s3.matrices)
            s3_diagnostics = prepared_s3.diagnostics()
            s3_diagnostics["plan_reused"] = bool(s3_plan_reused)
            info["diagnostics"]["qualified_s3_reference_elastic_stiffness"] = (
                s3_diagnostics
            )
            if prepared_s3.batched_element_ids:
                vectorized_shell_groups.append(
                    {
                        "shell_order": "S3",
                        "num_elements": len(prepared_s3.batched_element_ids),
                        "kernel": (
                            "qualified_s3_reference_elastic_shared_components"
                        ),
                        "parallel_kernel": False,
                        "unique_geometry_count": len(
                            prepared_s3.group_element_ids
                        ),
                        "component_evaluation_count": (
                            prepared_s3.component_evaluation_count
                        ),
                        "formulation_id": s3_diagnostics["formulation_id"],
                        "speedup_claimed": False,
                    }
                )

        if qualified_stiffness_items:
            shared_components = {}
            for element_id, element in qualified_stiffness_items:
                material = model.get_material(element.material_name)
                cache_key = element._qualified_stiffness_cache_key(mesh, material)
                current_components = getattr(element, "_qualified_components", None)
                if (
                    current_components is not None
                    and getattr(element, "_qualified_cache_key", None) == cache_key
                ):
                    shared_components.setdefault(cache_key, current_components)
                    precomputed[element_id] = np.asarray(
                        current_components["total"], dtype=float
                    )
                    continue
                components = shared_components.get(cache_key)
                if components is None:
                    precomputed[element_id] = element.compute_stiffness_matrix(
                        mesh, material
                    )
                    components = element._qualified_components
                    if components is None:
                        raise RuntimeError(
                            "Qualified E4-PL stiffness did not populate its component cache"
                        )
                    shared_components[cache_key] = components
                else:
                    precomputed[element_id] = element._adopt_qualified_components(
                        cache_key,
                        components,
                    )
            vectorized_shell_groups.append(
                {
                    "shell_order": "S4",
                    "num_elements": int(len(qualified_stiffness_items)),
                    "kernel": "e4_pl_shared_geometry_cache",
                    "parallel_kernel": False,
                    "unique_geometry_count": int(len(shared_components)),
                }
            )
            info["diagnostics"]["qualified_e4_pl_stiffness"] = {
                "path": "shared_geometry_cache",
                "element_count": int(len(qualified_stiffness_items)),
                "unique_geometry_count": int(len(shared_components)),
            }

        for key, elem_list in groups.items():
            num_nodes, thickness, drilling_stabilization, _reduced_integration, _hourglass_stabilization, material_name = key
            material = model.get_material(material_name)

            n_elem = len(elem_list)
            coords_all = np.zeros((n_elem, num_nodes, 3))
            for idx, (elem_id, element) in enumerate(elem_list):
                coords_all[idx] = element.get_node_coordinates(mesh)

            first_element = elem_list[0][1]
            is_4node = first_element._is_4node
            gauss_points = first_element.gauss_points
            gauss_weights = first_element.gauss_weights

            if matrix_type == "mass":
                kernel_name = "compute_shell_mass_matrices_jit"
                batched = compute_shell_mass_matrices_jit(
                    coords_all,
                    is_4node,
                    thickness,
                    float(material.density),
                    gauss_points,
                    gauss_weights,
                )
            else:
                kernel_name = "compute_shell_stiffness_matrices_jit"
                E = float(material.elastic_modulus)
                nu = float(material.poisson_ratio)
                G = float(material.shear_modulus)
                if is_4node:
                    shear_points = np.empty((0, 2))
                    shear_weights = np.empty(0)
                else:
                    shear_points = first_element.shear_gauss_points
                    shear_weights = first_element.shear_gauss_weights
                batched = compute_shell_stiffness_matrices_jit(
                    coords_all,
                    is_4node,
                    thickness,
                    drilling_stabilization,
                    E,
                    nu,
                    G,
                    gauss_points,
                    gauss_weights,
                    shear_points,
                    shear_weights,
                )

            for idx, (elem_id, element) in enumerate(elem_list):
                precomputed[elem_id] = batched[idx]
            jit_info = jit_diagnostics()
            vectorized_shell_groups.append(
                {
                    "shell_order": "S4" if is_4node else "Q8",
                    "num_elements": int(n_elem),
                    "num_nodes": int(num_nodes),
                    "material": str(material_name),
                    "thickness": float(thickness),
                    "jit_enabled": bool(JIT_ENABLED),
                    "jit_disabled_reason": JIT_DISABLED_REASON,
                    "kernel": kernel_name,
                    "parallel_kernel": True,
                    "parallel_threads": jit_info.get("num_threads"),
                    "backend": jit_info.get("backend"),
                }
            )

        if advanced_stiffness_items:
            advanced_start = time.perf_counter()
            advanced_matrices, advanced_counts = (
                prepare_s4_generalized_stiffness_batch(
                    model,
                    [element for _element_id, element in advanced_stiffness_items],
                )
            )
            advanced_seconds = time.perf_counter() - advanced_start
            for index, (element_id, _element) in enumerate(
                advanced_stiffness_items
            ):
                precomputed[element_id] = advanced_matrices[index]
            jit_info = jit_diagnostics()
            vectorized_shell_groups.append(
                {
                    "shell_order": "S4",
                    "num_elements": int(len(advanced_stiffness_items)),
                    "jit_enabled": bool(JIT_ENABLED),
                    "jit_disabled_reason": JIT_DISABLED_REASON,
                    "kernel": "compute_s4_generalized_stiffness_matrices_jit",
                    "parallel_kernel": True,
                    "parallel_threads": jit_info.get("num_threads"),
                    "backend": jit_info.get("backend"),
                    "kernel_seconds": float(advanced_seconds),
                    **advanced_counts,
                }
            )
            info["diagnostics"]["advanced_s4_stiffness"] = {
                "path": "compiled_batch",
                **advanced_counts,
            }

        if section_mass_items:
            section_mass_start = time.perf_counter()
            section_mass_matrices = prepare_s4_section_mass_batch(
                model,
                [element for _element_id, element in section_mass_items],
            )
            section_mass_seconds = time.perf_counter() - section_mass_start
            for index, (element_id, _element) in enumerate(section_mass_items):
                precomputed[element_id] = section_mass_matrices[index]
            jit_info = jit_diagnostics()
            vectorized_shell_groups.append(
                {
                    "shell_order": "S4",
                    "num_elements": int(len(section_mass_items)),
                    "jit_enabled": bool(JIT_ENABLED),
                    "jit_disabled_reason": JIT_DISABLED_REASON,
                    "kernel": "compute_s4_section_mass_matrices_jit",
                    "parallel_kernel": True,
                    "parallel_threads": jit_info.get("num_threads"),
                    "backend": jit_info.get("backend"),
                    "kernel_seconds": float(section_mass_seconds),
                    "generalized_section_mass_element_count": int(
                        len(section_mass_items)
                    ),
                }
            )
            info["diagnostics"]["generalized_s4_section_mass"] = {
                "path": "compiled_batch",
                "element_count": int(len(section_mass_items)),
            }

    # Retrieve or build cached sparsity pattern
    rows_concat, cols_concat = _get_cached_sparsity_pattern(mesh, matrix_type)

    data_list = []
    for elem_id, element in mesh.elements.items():
        elem_start = time.time()
        material = model.get_material(element.material_name)
        dof_mapping = np.asarray(element.get_dof_mapping(mesh), dtype=np.intp)
        if dof_mapping.size == 0:
            info["skipped_elements"].append(int(elem_id))
            continue

        if elem_id in precomputed:
            element_matrix = precomputed[elem_id]
        else:
            element_matrix = element_matrix_getter(element, mesh, material)

        element_matrix = _check_element_matrix_shape(
            int(elem_id),
            matrix_type,
            element_matrix,
            int(dof_mapping.size),
        )
        if matrix_type in {"stiffness", "mass", "geometric_stiffness"}:
            local_symmetry = _relative_symmetry_error(element_matrix)
            if local_symmetry > 1.0e-8:
                raise AssemblyError(
                    f"Element {elem_id} returned nonsymmetric {matrix_type}; "
                    f"relative symmetry error {local_symmetry:.3e}."
                )
        scale = activity_scales.get(int(elem_id), 1.0)
        data_list.append(
            (scale * np.asarray(element_matrix, dtype=float)).ravel()
        )

        info["element_times"][int(elem_id)] = time.time() - elem_start
        info["num_elements"] += 1

    if not data_list:
        matrix = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
        info["diagnostics"]["assembled_symmetry_error"] = 0.0
        info["sparsity_signature"] = _topology_signature(mesh, matrix_type)
        info["assembly_time"] = time.time() - start_time
        return matrix, info

    data_concat = np.concatenate(data_list)
    coo = sparse.coo_matrix(
        (data_concat, (rows_concat, cols_concat)),
        shape=(total_dofs, total_dofs),
        dtype=float,
    )
    matrix = coo.tocsr()
    if activity_info is not None and activity_info["zero_contribution_count"]:
        matrix.eliminate_zeros()
    info["diagnostics"]["assembled_symmetry_error"] = _relative_symmetry_error(matrix)
    if matrix_type in {"stiffness", "mass"}:
        info["diagnostics"]["vectorized_shell_groups"] = vectorized_shell_groups
        info["diagnostics"]["vectorized_shell_element_count"] = int(len(precomputed))
        info["diagnostics"]["scalar_shell_element_count"] = int(info["num_elements"] - len(precomputed))
    info["sparsity_signature"] = _topology_signature(mesh, matrix_type)
    info["assembly_time"] = time.time() - start_time
    return matrix, info


def assemble_stiffness_matrix(model: "FEModel") -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    """Assemble the global stiffness matrix K only."""
    return _assemble_element_matrix(
        model,
        "stiffness",
        lambda element, mesh, material: element.compute_stiffness_matrix(mesh, material),
    )


def assemble_mass_matrix(model: "FEModel") -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    """Assemble the global mass matrix M only, including any added point masses."""
    matrix, info = _assemble_element_matrix(
        model,
        "mass",
        lambda element, mesh, material: element.compute_mass_matrix(mesh, material),
    )
    matrix = _add_point_masses_to_matrix(model, matrix)
    info["diagnostics"]["point_mass_count"] = int(len(getattr(model.mesh, "point_masses", {}) or {}))
    return matrix, info


def _add_point_masses_to_matrix(model: "FEModel", matrix: sparse.csr_matrix) -> sparse.csr_matrix:
    """Add lumped point masses to the translational-DOF diagonal of ``matrix``."""
    point_masses = getattr(model.mesh, "point_masses", None)
    if not point_masses:
        return matrix
    total_dofs = model.mesh.dof_manager.total_dofs
    diagonal = np.zeros(total_dofs, dtype=float)
    for node_id, mass in point_masses.items():
        node = model.mesh.get_node(int(node_id))
        if node is None or float(mass) == 0.0:
            continue
        for axis in range(3):
            diagonal[node.dofs[axis]] += float(mass)
    if not diagonal.any():
        return matrix
    return (matrix + sparse.diags(diagonal, 0, shape=(total_dofs, total_dofs), format="csr")).tocsr()


def _get_element_state(element_states: Optional[Any], element_id: int, element: Any) -> Any:
    if element_states is None:
        return None
    if callable(element_states):
        try:
            return element_states(element_id, element)
        except TypeError:
            return element_states(element_id)
    if isinstance(element_states, Mapping):
        if element_id in element_states:
            return element_states[element_id]
        element_id_text = str(element_id)
        if element_id_text in element_states:
            return element_states[element_id_text]
    return None


def assemble_geometric_stiffness_matrix(
    model: "FEModel",
    element_states: Optional[Any] = None,
) -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    """Assemble the global geometric stiffness matrix KG only.

    ``element_states`` supplies the reference stress/resultant state for each
    element.  Beams accept a numeric value or a mapping with
    ``axial_compression`` positive in compression.  Shell resultants act
    through the Mindlin field ``[u+z*ry, v-z*rx, w]``; drilling rotation and
    stress components normal to the midsurface are outside this operator.
    """
    mesh = model.mesh
    total_dofs = mesh.dof_manager.total_dofs
    info = _base_info(model, "geometric_stiffness")
    start_time = time.time()
    _activity, activity_scales, activity_info = _activity_scales(
        model, "stiffness"
    )
    if activity_info is not None:
        info["diagnostics"]["element_activity"] = activity_info

    # Retrieve or build cached sparsity pattern
    rows_concat, cols_concat = _get_cached_sparsity_pattern(mesh, "geometric_stiffness")

    # S4 geometric stiffness is especially expensive in the scalar element
    # loop because every element repeatedly reconstructs the same reference
    # derivatives and coordinate transforms.  Keep the stress/resultant
    # sampling in the element contract, but evaluate the common matrix
    # operator in one compiled batch and cache its immutable geometry.
    from .elements import ShellElement
    from .jit_compiler import JIT_ENABLED, JIT_DISABLED_REASON, jit_diagnostics
    from .vectorized_stiffness import (
        compute_s4_geometric_stiffness_matrices_jit,
        prepare_s4_geometric_kinematics_jit,
    )

    eligible_groups: Dict[Tuple[bytes, bytes], list[Tuple[int, Any]]] = {}
    for elem_id, element in mesh.elements.items():
        if isinstance(element, ShellElement) and bool(getattr(element, "_is_4node", False)):
            points = np.ascontiguousarray(element.gauss_points, dtype=float)
            weights = np.ascontiguousarray(element.gauss_weights, dtype=float)
            key = (points.tobytes(), weights.tobytes())
            eligible_groups.setdefault(key, []).append((int(elem_id), element))

    precomputed: Dict[int, np.ndarray] = {}
    geometry_cache = getattr(mesh, "_s4_geometric_kinematics_cache", None)
    if geometry_cache is None:
        geometry_cache = {}
        mesh._s4_geometric_kinematics_cache = geometry_cache
    revisions = getattr(mesh, "revision_signature", lambda: {})()
    geometry_revision = (
        int(revisions.get("topology", 0)),
        int(revisions.get("geometry", 0)),
    )
    stale_geometry_keys = [
        key for key in geometry_cache if not key or key[0] != geometry_revision
    ]
    for stale_key in stale_geometry_keys:
        del geometry_cache[stale_key]
    geometry_setup_seconds = 0.0
    kernel_seconds = 0.0
    cache_hits = 0
    batched_ids: list[int] = []
    for group_index, elem_list in enumerate(eligible_groups.values()):
        first = elem_list[0][1]
        points = np.ascontiguousarray(first.gauss_points, dtype=float)
        weights = np.ascontiguousarray(first.gauss_weights, dtype=float)
        element_ids = tuple(elem_id for elem_id, _element in elem_list)
        cache_key = (geometry_revision, element_ids, points.tobytes(), weights.tobytes())
        geometry = geometry_cache.get(cache_key)
        if geometry is None:
            coords = np.ascontiguousarray(
                [element.get_node_coordinates(mesh) for _elem_id, element in elem_list],
                dtype=float,
            )
            geometry_start = time.perf_counter()
            geometry = prepare_s4_geometric_kinematics_jit(coords, points, weights)
            geometry_setup_seconds += time.perf_counter() - geometry_start
            geometry_cache[cache_key] = geometry
        else:
            cache_hits += 1

        count = len(elem_list)
        gp_count = points.shape[0]
        membrane = np.zeros((count, gp_count, 3), dtype=float)
        bending = np.zeros_like(membrane)
        second_moment = np.zeros_like(membrane)
        for index, (elem_id, element) in enumerate(elem_list):
            state = _get_element_state(element_states, elem_id, element)
            membrane[index] = element._membrane_compression_samples(state, gp_count)
            bending[index] = element._bending_compression_samples(state, gp_count)
            second_moment[index] = element._stress_second_moment_samples(
                state,
                gp_count,
                membrane[index],
                element.thickness,
            )
        kernel_start = time.perf_counter()
        matrices = compute_s4_geometric_stiffness_matrices_jit(
            *geometry,
            membrane,
            bending,
            second_moment,
        )
        kernel_seconds += time.perf_counter() - kernel_start
        for index, (elem_id, _element) in enumerate(elem_list):
            precomputed[elem_id] = matrices[index]
            batched_ids.append(elem_id)

    info["diagnostics"]["vectorized_s4_geometric_stiffness"] = {
        "element_count": len(batched_ids),
        "group_count": len(eligible_groups),
        "element_ids": sorted(batched_ids),
        "geometry_cache_hits": cache_hits,
        "geometry_setup_seconds": geometry_setup_seconds,
        "kernel_seconds": kernel_seconds,
        "jit_enabled": bool(JIT_ENABLED),
        "jit_disabled_reason": JIT_DISABLED_REASON,
        "jit": jit_diagnostics(),
    }

    data_list = []
    for elem_id, element in mesh.elements.items():
        elem_start = time.time()
        material = model.get_material(element.material_name)
        dof_mapping = np.asarray(element.get_dof_mapping(mesh), dtype=np.intp)
        if dof_mapping.size == 0:
            info["skipped_elements"].append(int(elem_id))
            continue

        if int(elem_id) in precomputed:
            element_matrix = precomputed[int(elem_id)]
        else:
            state = _get_element_state(element_states, int(elem_id), element)
            getter = getattr(element, "compute_geometric_stiffness_matrix", None)
            if getter is None:
                element_matrix = np.zeros((dof_mapping.size, dof_mapping.size), dtype=float)
            else:
                element_matrix = getter(mesh, material, state)
        element_matrix = _check_element_matrix_shape(
            int(elem_id),
            "geometric_stiffness",
            element_matrix,
            int(dof_mapping.size),
        )
        scale = activity_scales.get(int(elem_id), 1.0)
        data_list.append(
            (scale * np.asarray(element_matrix, dtype=float)).ravel()
        )

        info["element_times"][int(elem_id)] = time.time() - elem_start
        info["num_elements"] += 1

    info["state_source"] = "none" if element_states is None else type(element_states).__name__
    info["diagnostics"]["scalar_element_count"] = int(info["num_elements"] - len(batched_ids))
    info["diagnostics"]["shell_initial_stress_scope"] = (
        "mindlin_translations_and_director_gradients; no_drilling_or_transverse_normal_stress_terms"
    )

    if not data_list:
        matrix = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
        info["diagnostics"]["assembled_symmetry_error"] = 0.0
        info["sparsity_signature"] = _topology_signature(mesh, "geometric_stiffness")
        info["assembly_time"] = time.time() - start_time
        return matrix, info

    data_concat = np.concatenate(data_list)
    coo = sparse.coo_matrix(
        (data_concat, (rows_concat, cols_concat)),
        shape=(total_dofs, total_dofs),
        dtype=float,
    )
    matrix = coo.tocsr()
    if activity_info is not None and activity_info["zero_contribution_count"]:
        matrix.eliminate_zeros()
    info["diagnostics"]["assembled_symmetry_error"] = _relative_symmetry_error(matrix)
    info["sparsity_signature"] = _topology_signature(mesh, "geometric_stiffness")
    info["assembly_time"] = time.time() - start_time
    return matrix, info


def _qualified_s3_pressure_surface_records(
    model: "FEModel",
    load_case: Optional["LoadCase"],
) -> list[Dict[str, Any]]:
    """Identify the exact surface carrying qualified-S3 pressure work.

    The S3 section origin may be offset from its nodal interpolation surface.
    Pressure is intentionally conjugate to the latter; reporting that choice
    prevents force/reaction post-processing from silently treating the material
    midsurface as the pressure surface.  Other shell formulations retain their
    existing diagnostics unchanged.
    """

    if load_case is None:
        return []
    records: list[Dict[str, Any]] = []
    for raw_element_id in getattr(load_case, "pressure_loads", {}):
        element_id = int(raw_element_id)
        element = model.mesh.get_element(element_id)
        if (
            element is None
            or str(getattr(element, "formulation_id", ""))
            != "E4_PL_QUALIFIED_S3_COMPANION_V1"
        ):
            continue
        offset = float(getattr(element, "reference_surface_offset", 0.0))
        if not np.isfinite(offset):
            raise AssemblyError(
                f"Qualified S3 element {element_id} has a non-finite reference-surface offset."
            )
        records.append(
            {
                "element_id": element_id,
                "pressure_surface_id": "ELEMENT_NODAL_REFERENCE_SURFACE_V1",
                "reference_surface_offset": offset,
                "resultant_and_reaction_reference": (
                    "GLOBAL_NODAL_REFERENCE_COORDINATES"
                ),
                "section_origin_offset_from_reference": -offset,
                "virtual_work": "TRANSLATIONAL_NODAL_REFERENCE_SURFACE_ONLY",
            }
        )
    return records


def assemble_load_vector(
    model: "FEModel",
    load_case: Optional["LoadCase"] = None,
    displacements: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Assemble the global external load vector ``F_external``.

    ``displacements`` is ignored by ordinary dead loads.  A load case with
    ``follower_pressure=True`` uses it to evaluate pressure on the current
    shell nodal interpolation surface.
    """
    total_dofs = model.mesh.dof_manager.total_dofs
    start_time = time.time()
    if displacements is not None:
        displacements = np.asarray(displacements, dtype=float).reshape(-1)
        if displacements.shape != (total_dofs,):
            raise AssemblyError(
                f"Displacement vector shape {displacements.shape} does not match total DOFs {(total_dofs,)}."
            )
        if not np.all(np.isfinite(displacements)):
            raise AssemblyError("Displacement vector contains non-finite values.")
    if load_case is None:
        load_vector = np.zeros(total_dofs, dtype=float)
        load_name = None
    else:
        load_vector = load_case.get_load_vector(
            model.mesh,
            model.mesh.dof_manager,
            model.get_material,
            displacements=displacements,
            element_activity=_element_activity(model),
        )
        load_vector = np.asarray(load_vector, dtype=float).reshape(-1)
        load_name = load_case.name

    if load_vector.shape != (total_dofs,):
        raise AssemblyError(f"Load vector shape {load_vector.shape} does not match total DOFs {(total_dofs,)}.")
    if not np.all(np.isfinite(load_vector)):
        raise AssemblyError(f"Load case {load_name!r} produced non-finite load vector values.")

    activity = _element_activity(model)
    info = {
        "vector_type": "load",
        "load_case": load_name,
        "num_nodes": model.mesh.num_nodes,
        "total_dofs": total_dofs,
        "assembly_time": time.time() - start_time,
        "load_norm": float(np.linalg.norm(load_vector)),
        "pressure_configuration": (
            "current"
            if load_case is not None and bool(getattr(load_case, "follower_pressure", False))
            else "reference"
        ),
        "element_activity": (
            None
            if activity is None
            else {
                "quantity": "load",
                "sequence": int(getattr(activity, "sequence", 0)),
            }
        ),
    }
    pressure_surfaces = _qualified_s3_pressure_surface_records(model, load_case)
    if pressure_surfaces:
        info["qualified_s3_pressure_surfaces"] = pressure_surfaces
    return load_vector, info


def assemble_external_load_tangent(
    model: "FEModel",
    load_case: Optional["LoadCase"],
    displacements: Optional[np.ndarray] = None,
) -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    """Assemble ``dF_external / du`` for current-area follower pressure.

    Dead loads return an exact zero matrix.  The follower tangent is generally
    nonsymmetric for an open pressure patch; callers must therefore use a
    general sparse factorization for ``K_internal - K_external``.
    """
    total_dofs = model.mesh.dof_manager.total_dofs
    start_time = time.time()
    u = np.zeros(total_dofs, dtype=float) if displacements is None else np.asarray(displacements, dtype=float).reshape(-1)
    if u.shape != (total_dofs,):
        raise AssemblyError(f"Displacement vector shape {u.shape} does not match total DOFs {(total_dofs,)}.")
    if not np.all(np.isfinite(u)):
        raise AssemblyError("Displacement vector contains non-finite values.")

    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    data: list[np.ndarray] = []
    element_ids: list[int] = []
    _activity, activity_scales, activity_info = _activity_scales(model, "load")
    if load_case is not None and bool(getattr(load_case, "follower_pressure", False)):
        for raw_element_id, pressure in getattr(load_case, "pressure_loads", {}).items():
            element_id = int(raw_element_id)
            element = model.mesh.get_element(element_id)
            if element is None:
                continue
            if not hasattr(element, "node_ids"):
                raise AssemblyError(f"Follower pressure element {element_id} has no nodal interpolation.")
            dof_mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
            coords = load_case._current_element_coordinates(element, model.mesh, u)
            try:
                element_tangent = load_case._consistent_pressure_tangent(
                    element,
                    model.mesh,
                    float(pressure),
                    coords,
                )
            except ValueError as exc:
                raise AssemblyError(str(exc)) from exc
            element_tangent = _check_element_matrix_shape(
                element_id,
                "external_load_tangent",
                element_tangent,
                int(dof_mapping.size),
            )
            element_tangent = (
                activity_scales.get(element_id, 1.0) * element_tangent
            )
            row_grid, col_grid = np.meshgrid(dof_mapping, dof_mapping, indexing="ij")
            rows.append(row_grid.ravel())
            cols.append(col_grid.ravel())
            data.append(element_tangent.ravel())
            element_ids.append(element_id)

    if data:
        tangent = sparse.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(total_dofs, total_dofs),
            dtype=float,
        ).tocsr()
        tangent.eliminate_zeros()
    else:
        tangent = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)

    info = {
        "matrix_type": "external_load_tangent",
        "load_case": None if load_case is None else load_case.name,
        "total_dofs": total_dofs,
        "num_pressure_elements": len(element_ids),
        "pressure_element_ids": element_ids,
        "pressure_configuration": (
            "current"
            if load_case is not None and bool(getattr(load_case, "follower_pressure", False))
            else "reference"
        ),
        "diagnostics": {
            "assembled_symmetry_error": _relative_symmetry_error(tangent),
            "element_activity": activity_info,
        },
        "assembly_time": time.time() - start_time,
    }
    pressure_surfaces = _qualified_s3_pressure_surface_records(model, load_case)
    if pressure_surfaces:
        info["qualified_s3_pressure_surfaces"] = pressure_surfaces
    return tangent, info


def assemble_external_load_system(
    model: "FEModel",
    load_case: Optional["LoadCase"],
    displacements: Optional[np.ndarray] = None,
    *,
    tangent: bool = True,
) -> Tuple[np.ndarray, Optional[sparse.csr_matrix], Dict[str, Any]]:
    """Assemble external force and, optionally, its configuration tangent."""
    vector, vector_info = assemble_load_vector(model, load_case, displacements)
    if tangent:
        load_tangent, tangent_info = assemble_external_load_tangent(model, load_case, displacements)
    else:
        load_tangent = None
        tangent_info = None
    return vector, load_tangent, {"load": vector_info, "external_load_tangent": tangent_info}


def assemble_load_matrix(
    model: "FEModel",
    load_cases: Sequence[Optional["LoadCase"]],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Assemble a dense load matrix with one column per load case."""
    start = time.time()
    vectors = []
    infos = []
    names = []
    for load_case in load_cases:
        vector, info = assemble_load_vector(model, load_case)
        vectors.append(vector)
        infos.append(info)
        names.append(None if load_case is None else load_case.name)
    total_dofs = model.mesh.dof_manager.total_dofs
    matrix = np.column_stack(vectors) if vectors else np.zeros((total_dofs, 0), dtype=float)
    return matrix, {
        "vector_type": "load_matrix",
        "load_cases": names,
        "num_load_cases": len(names),
        "total_dofs": total_dofs,
        "assembly_time": time.time() - start,
        "columns": infos,
        "load_norms": [float(np.linalg.norm(matrix[:, idx])) for idx in range(matrix.shape[1])],
        "revision_signature": getattr(model.mesh, "revision_signature", lambda: {})(),
    }


def assemble_damping_matrix(
    model: "FEModel",
    rayleigh_alpha: float = 0.0,
    rayleigh_beta: float = 0.0,
) -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    """Assemble Rayleigh damping C = alpha M + beta K."""
    start = time.time()
    if _element_activity(model) is None:
        M, mass_info = assemble_mass_matrix(model)
        K, stiffness_info = assemble_stiffness_matrix(model)
    else:
        M, mass_info = _assemble_element_matrix(
            model,
            "mass",
            lambda element, mesh, material: element.compute_mass_matrix(
                mesh, material
            ),
            activity_quantity="damping",
        )
        M = _add_point_masses_to_matrix(model, M)
        K, stiffness_info = _assemble_element_matrix(
            model,
            "stiffness",
            lambda element, mesh, material: element.compute_stiffness_matrix(
                mesh, material
            ),
            activity_quantity="damping",
        )
    C = (float(rayleigh_alpha) * M + float(rayleigh_beta) * K).tocsr()
    return C, {
        "matrix_type": "damping",
        "rayleigh_alpha": float(rayleigh_alpha),
        "rayleigh_beta": float(rayleigh_beta),
        "mass": mass_info,
        "stiffness": stiffness_info,
        "assembly_time": time.time() - start,
        "diagnostics": {"assembled_symmetry_error": _relative_symmetry_error(C)},
        "revision_signature": getattr(model.mesh, "revision_signature", lambda: {})(),
    }


def assemble_system(
    model: "FEModel",
    load_case: Optional["LoadCase"] = None,
    include_mass: bool = False,
) -> Tuple[sparse.csr_matrix, np.ndarray, Dict[str, Any]]:
    """Compatibility wrapper returning K, F and assembly metadata.

    The mass matrix is assembled separately and returned in info["mass_matrix"]
    only when include_mass is true.  It is never added to stiffness.
    """
    start_time = time.time()
    K, stiffness_info = assemble_stiffness_matrix(model)
    F, load_info = assemble_load_vector(model, load_case)

    info: Dict[str, Any] = {
        "num_elements": stiffness_info["num_elements"],
        "num_nodes": model.mesh.num_nodes,
        "total_dofs": model.mesh.dof_manager.total_dofs,
        "includes_mass_matrix": bool(include_mass),
        "assembly_time": 0.0,
        "stiffness": stiffness_info,
        "load": load_info,
        # Backwards-compatible keys used by older diagnostics/tests.
        "element_times": stiffness_info.get("element_times", {}),
    }

    if include_mass:
        M, mass_info = assemble_mass_matrix(model)
        info["mass_matrix"] = M
        info["mass"] = mass_info

    info["assembly_time"] = time.time() - start_time
    return K, F, info
