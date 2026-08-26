"""Produce bounded mixed-Q4/S3 structural diagnostics.

The producer executes real production assembly, solve and recovery operations.
It keeps representative coverage distinct from complete manifest coverage: a
representative success can never close a formal gate, while a reproducible
threshold violation is still retained as a contradiction.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

from e4_pl_s3_mixed_structural_common import (
    BLOCKED,
    COMPLETE,
    FAIL,
    PARTIAL,
    PRODUCTION_RESTRICTION,
    SHARD_IDS,
    SHARD_SCHEMA,
    StructuralEvidenceError,
    canonical_bytes,
    case_spec,
    find_record,
    load_authorities,
    percentile_nearest_rank,
    record_id,
    sha256,
    slope,
    validate_shard,
    write_exclusive,
)


IMPLEMENTATION_ID = "E4_PL_S3_MIXED_STRUCTURAL_PRODUCER_V1"
np: Any = None


def activate_numerics(authorities: Any) -> None:
    """Import numerical/mechanics dependencies only after authority validation."""

    global np
    if not authorities.program_raw or not authorities.program_paths:
        raise StructuralEvidenceError("program authorities were not validated before mechanics")
    if np is None:
        import numpy as numpy_module

        np = numpy_module


def _progress(phase: str, **extra: Any) -> None:
    sys.stderr.buffer.write(canonical_bytes({"phase": phase, **extra}))
    sys.stderr.buffer.flush()


def _threshold(authorities: Any, *keys: str) -> float:
    value: Any = authorities.contract["acceptance_gates"]
    for key in keys:
        value = value[key]
    return float(value)


def audit_manifest(authorities: Any) -> dict[str, Any]:
    """Regenerate every registered connectivity digest from the source rules."""

    regenerated = authorities.manifest_generator.build_manifest()
    regenerated_raw = canonical_bytes(regenerated)
    exact = regenerated_raw == authorities.manifest_raw
    rows = authorities.manifest["records"]
    observed = {
        "diagonals": sorted({str(row["diagonal"]) for row in rows}),
        "fractions_percent": sorted({int(row["s3_area_fraction_percent"]) for row in rows}),
        "levels": sorted({int(row["level"]) for row in rows}),
        "masks": sorted(
            {str(row["mask"]) for row in rows if int(row["s3_area_fraction_percent"]) > 0}
        ),
    }
    required = authorities.input["coverage"]
    coverage_exact = (
        observed["diagonals"] == sorted(required["required_diagonals"])
        and observed["fractions_percent"] == sorted(required["required_fractions_percent"])
        and observed["levels"] == sorted(required["required_levels"])
        and observed["masks"] == sorted(required["required_masks"])
    )
    return {
        "coverage_exact": coverage_exact,
        "gated_record_count": len(rows),
        "manifest_regeneration_byte_identical": exact,
        "observed": observed,
        "research_control_record_count": len(authorities.manifest["research_control"]["records"]),
    }


def _smoke_authorities(authorities: Any) -> Any:
    return authorities.smoke_runner.load_authorities(authorities.smoke_input_path)


def _patch_basis(authorities: Any, *, quick: bool) -> list[dict[str, Any]]:
    smoke_authorities = _smoke_authorities(authorities)
    specifications = authorities.input["coverage"]["patch_basis_cases"]
    if quick:
        specifications = specifications[:2]
    rows: list[dict[str, Any]] = []
    for index, specification in enumerate(specifications, start=1):
        record = find_record(
            authorities,
            level=int(specification["level"]),
            fraction=int(specification["fraction_percent"]),
            mask=str(specification["mask"]),
            diagonal=str(specification["diagonal"]),
        )
        _progress("PATCH_BASIS_CASE_INITIALIZED", index=index, record_id=record_id(record))
        result = authorities.smoke_runner._run_case(
            smoke_authorities,
            case_spec(record, prefix="STRUCTURAL_PATCH"),
        )
        force_patch = result["force_loaded_in_plane_shear_patch"]
        patch_rows = result["patches"]
        rows.append(
            {
                "connectivity_sha256": record["connectivity_sha256"],
                "covariance_residual": result["covariance"]["relative_frobenius_residual"],
                "force_loaded_in_plane": {
                    key: force_patch[key]
                    for key in (
                        "action_reaction_residual",
                        "edge_work_residual",
                        "force_residual",
                        "moment_residual",
                        "patch_residual",
                    )
                },
                "patch_residuals": {
                    name: patch_rows[name]["patch_residual"]
                    for name in ("bending", "membrane", "shear")
                },
                "pl_participation": {
                    name: force_patch["pl_participation"][name]
                    for name in ("Q4_PL", "S3_PL")
                },
                "q4_residual_hourglass_participation": force_patch["pl_participation"][
                    "Q4_RESIDUAL_HOURGLASS"
                ],
                "record_id": record_id(record),
                "symmetry_residual": result["symmetry_relative_frobenius_residual"],
                "transverse_shear_classification": patch_rows["shear"][
                    "diagnostic_classification"
                ],
            }
        )
        _progress("PATCH_BASIS_CASE_COMPLETED", index=index, record_id=record_id(record))
    return rows


def produce_patch(authorities: Any, *, quick: bool) -> tuple[dict[str, Any], dict[str, str]]:
    manifest = audit_manifest(authorities)
    basis = _patch_basis(authorities, quick=quick)
    patch_limit = _threshold(
        authorities, "patch_and_equilibrium", "patch_residual_maximum"
    )
    equilibrium_limits = {
        key: _threshold(authorities, "patch_and_equilibrium", f"{key}_maximum")
        for key in (
            "action_reaction_residual",
            "edge_work_residual",
            "force_residual",
            "moment_residual",
        )
    }
    covariance_limit = _threshold(
        authorities, "symmetry_and_covariance_residual_maximum"
    )
    patch_contradictions: list[str] = []
    covariance_contradictions: list[str] = []
    for row in basis:
        force = row["force_loaded_in_plane"]
        if force["patch_residual"] > patch_limit:
            patch_contradictions.append(f"{row['record_id']}:PATCH")
        for name in ("bending", "membrane"):
            if row["patch_residuals"][name] > patch_limit:
                patch_contradictions.append(
                    f"{row['record_id']}:{name.upper()}_PATCH"
                )
        for name, limit in equilibrium_limits.items():
            if force[name] > limit:
                patch_contradictions.append(f"{row['record_id']}:{name.upper()}")
        if row["symmetry_residual"] > covariance_limit:
            covariance_contradictions.append(f"{row['record_id']}:SYMMETRY")
        if row["covariance_residual"] > covariance_limit:
            covariance_contradictions.append(f"{row['record_id']}:COVARIANCE")
    complete_basis = len(basis) == len(authorities.input["coverage"]["patch_basis_cases"])
    authority_ok = bool(
        manifest["coverage_exact"] and manifest["manifest_regeneration_byte_identical"]
    )
    contradictions = sorted(set(patch_contradictions + covariance_contradictions))
    if quick:
        patch_status = covariance_status = PARTIAL
    elif not authority_ok:
        patch_status = covariance_status = BLOCKED
    else:
        # Membrane, bending, and in-plane force/equilibrium diagnostics are real.
        # The smoke authority explicitly lacks a frozen force-loaded transverse
        # shear protocol, so it cannot be promoted into complete patch evidence.
        patch_status = FAIL if patch_contradictions else PARTIAL
        # Covariance remains partial until all six D3 numberings and physical
        # director reversal have been constructed and executed.
        covariance_status = FAIL if covariance_contradictions else PARTIAL
    payload = {
        "basis": basis,
        "basis_complete": complete_basis,
        "contradictions": contradictions,
        "contradictions_classifying": bool(contradictions and not quick),
        "manifest_audit": manifest,
        "scope": {
            "all_registered_topology_hashes": "EXECUTED",
            "bending_patch": "EXECUTED",
            "d3_numberings": "UNEXECUTED_ALL_SIX_REQUIRED",
            "force_loaded_in_plane_patch": "EXECUTED",
            "membrane_patch": "EXECUTED",
            "physical_director_reversal": "UNEXECUTED_REQUIRED",
            "transverse_force_loaded_shear_patch": (
                "UNEXECUTED_NO_HASH_BOUND_LOAD_AND_RESTRAINT_PROTOCOL"
            ),
            "translation_equivalence": (
                "REGULAR_CELL_BASIS_DIAGNOSTIC_NOT_A_SUBSTITUTE_FOR_D3_OR_REVERSAL"
            ),
        },
    }
    return payload, {
        "patch_and_equilibrium": patch_status,
        "symmetry_and_covariance": covariance_status,
    }


def _mindlin_modes(
    *,
    length: float,
    width: float,
    thickness: float,
    pressure: float,
    elastic_modulus: float,
    poisson_ratio: float,
    terms: int = 99,
) -> list[tuple[int, int, float, float, float, float, float, float]]:
    """Return independent Reissner-Mindlin amplitudes ``W, X, Y``.

    ``theta_x=X cos(ax)sin(by)`` and ``theta_y=Y sin(ax)cos(by)`` use the
    production-compatible convention ``gamma=grad(w)+theta``.  The three
    continuum stationarity equations are assembled directly for every mode;
    no ANYsolver matrix or result is used by this reference.
    """

    rigidity = elastic_modulus * thickness**3 / (12.0 * (1.0 - poisson_ratio**2))
    shear = (
        (5.0 / 6.0)
        * elastic_modulus
        / (2.0 * (1.0 + poisson_ratio))
        * thickness
    )
    transverse = 0.5 * (1.0 - poisson_ratio)
    coupling = 0.5 * (1.0 + poisson_ratio)
    modes: list[tuple[int, int, float, float, float, float, float, float]] = []
    for m in range(1, int(terms) + 1, 2):
        for n in range(1, int(terms) + 1, 2):
            a = m * math.pi / length
            b = n * math.pi / width
            qmn = 16.0 * pressure / (math.pi**2 * m * n)
            matrix = np.asarray(
                (
                    (shear * (a * a + b * b), shear * a, shear * b),
                    (
                        shear * a,
                        shear + rigidity * (a * a + transverse * b * b),
                        rigidity * coupling * a * b,
                    ),
                    (
                        shear * b,
                        rigidity * coupling * a * b,
                        shear + rigidity * (b * b + transverse * a * a),
                    ),
                ),
                dtype=float,
            )
            amplitudes = np.linalg.solve(matrix, np.asarray((qmn, 0.0, 0.0)))
            modes.append(
                (
                    m,
                    n,
                    a,
                    b,
                    qmn,
                    float(amplitudes[0]),
                    float(amplitudes[1]),
                    float(amplitudes[2]),
                )
            )
    return modes


def _mindlin_plate_reference(
    *,
    length: float,
    width: float,
    thickness: float,
    pressure: float,
    elastic_modulus: float,
    poisson_ratio: float,
    terms: int = 99,
) -> dict[str, Any]:
    modes = _mindlin_modes(
        length=length,
        width=width,
        thickness=thickness,
        pressure=pressure,
        elastic_modulus=elastic_modulus,
        poisson_ratio=poisson_ratio,
        terms=terms,
    )
    displacement = sum(
        mode[5]
        * math.sin(mode[0] * math.pi / 2.0)
        * math.sin(mode[1] * math.pi / 2.0)
        for mode in modes
    )
    strain_energy = sum(
        mode[4] * mode[5] * length * width / 8.0 for mode in modes
    )
    return {
        "center_displacement": abs(float(displacement)),
        "modes": modes,
        "strain_energy": float(strain_energy),
    }


def _mindlin_moments(
    x: float,
    y: float,
    *,
    length: float,
    width: float,
    thickness: float,
    elastic_modulus: float,
    poisson_ratio: float,
    modes: Sequence[tuple[int, int, float, float, float, float, float, float]],
) -> np.ndarray:
    rigidity = elastic_modulus * thickness**3 / (12.0 * (1.0 - poisson_ratio**2))
    moment_x = 0.0
    moment_y = 0.0
    moment_xy = 0.0
    for m, n, a, b, _qmn, _w, rotation_x, rotation_y in modes:
        sin_x = math.sin(m * math.pi * x / length)
        cos_x = math.cos(m * math.pi * x / length)
        sin_y = math.sin(n * math.pi * y / width)
        cos_y = math.cos(n * math.pi * y / width)
        curvature_x = -a * rotation_x * sin_x * sin_y
        curvature_y = -b * rotation_y * sin_x * sin_y
        curvature_xy = (b * rotation_x + a * rotation_y) * cos_x * cos_y
        moment_x += rigidity * (curvature_x + poisson_ratio * curvature_y)
        moment_y += rigidity * (curvature_y + poisson_ratio * curvature_x)
        moment_xy += 0.5 * rigidity * (1.0 - poisson_ratio) * curvature_xy
    return np.asarray((moment_x, moment_y, moment_xy), dtype=float)


def _plate_boundaries(model: Any, level: int) -> None:
    from anysolver.boundary import BoundaryCondition

    edge = [
        node.id
        for node in model.mesh.nodes.values()
        if (
            int(node.id) <= level + 1
            or int(node.id) > level * (level + 1)
            or (int(node.id) - 1) % (level + 1) in (0, level)
        )
    ]
    model.boundary_conditions = [
        BoundaryCondition(
            "simply_supported_edge_translations",
            [int(value) for value in edge],
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        )
    ]
    model.constraint_equations = []


def _interface_cells(
    generator: Any,
    *,
    level: int,
    mask: str,
    split_count: int,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    base = () if split_count == 0 else generator.selected_base_cells(mask, split_count)
    split = set(generator.expanded_split_cells(base, level))
    band = set(split)
    for i, j in tuple(split):
        for candidate in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if 0 <= candidate[0] < level and 0 <= candidate[1] < level:
                band.add(candidate)
    return split, band


def _plate_case(
    authorities: Any,
    record: Mapping[str, Any],
    *,
    recover_interface: bool,
) -> tuple[dict[str, Any], dict[tuple[int, int], float]]:
    from anysolver.assembly import solve_linear
    from anysolver.boundary import LoadCase

    smoke = authorities.smoke_runner
    smoke_authorities = _smoke_authorities(authorities)
    built = smoke.build_case_model(
        smoke_authorities,
        case_spec(record, prefix="STRUCTURAL_CONVERGENCE"),
        include_auxiliary_inputs=False,
    )
    level = int(record["level"])
    _plate_boundaries(built.model, level)
    reference_spec = authorities.input["coverage"]["convergence_reference"]
    load = LoadCase("uniform_pressure_mindlin_reference")
    pressure = float(reference_spec["pressure"])
    for element_id in built.model.mesh.elements:
        load.add_pressure_load(int(element_id), pressure)
    built.model.load_cases = [load]
    displacement, solver_info = solve_linear(
        built.model,
        load,
        constraint_mode="transformation",
    )
    solver_status = str((solver_info.get("convergence_info") or {}).get("status", "unknown"))
    if solver_status != "converged":
        raise RuntimeError(f"pressure plate solve ended {solver_status!r}")
    center_id = (level // 2) * (level + 1) + level // 2 + 1
    center_w = abs(float(displacement[built.model.mesh.nodes[center_id].dofs[2]]))
    model_spec = smoke_authorities.input_payload["model"]
    material_spec = model_spec["material"]
    thickness = float(model_spec["section"]["thickness"])
    if (
        thickness != float(reference_spec["thickness"])
        or float(model_spec["coordinates"]["length_x"]) != float(reference_spec["length"])
        or float(model_spec["coordinates"]["length_y"]) != float(reference_spec["width"])
    ):
        raise StructuralEvidenceError("pressure-plate model and independent reference differ")
    reference = _mindlin_plate_reference(
        length=float(reference_spec["length"]),
        width=float(reference_spec["width"]),
        thickness=thickness,
        pressure=pressure,
        elastic_modulus=float(material_spec["elastic_modulus"]),
        poisson_ratio=float(material_spec["poisson_ratio"]),
        terms=int(reference_spec["series_max_odd_index"]),
    )
    moment_modes = _mindlin_modes(
        length=float(reference_spec["length"]),
        width=float(reference_spec["width"]),
        thickness=thickness,
        pressure=pressure,
        elastic_modulus=float(material_spec["elastic_modulus"]),
        poisson_ratio=float(material_spec["poisson_ratio"]),
        terms=int(reference_spec["interface_series_max_odd_index"]),
    )
    material = built.model.get_material(str(material_spec["name"]))
    energies = {
        "Q4_PL": 0.0,
        "Q4_RESIDUAL_HOURGLASS": 0.0,
        "S3_PL": 0.0,
        "TOTAL": 0.0,
    }
    cell_errors: dict[tuple[int, int], list[float]] = {}
    split, band = _interface_cells(
        authorities.manifest_generator,
        level=level,
        mask=str(record["mask"]),
        split_count=int(record["split_base_cell_count"]),
    )
    if recover_interface and not split:
        # The all-Q4 row is the spatial baseline for every possible mixed
        # interface band at this level.
        band = {(i, j) for j in range(level) for i in range(level)}
    element_id = 0
    for j in range(level):
        for i in range(level):
            connectivities = smoke._cell_connectivity(
                i,
                j,
                level,
                split=(i, j) in split,
                diagonal=str(record["diagonal"]),
            )
            for kind, _nodes in connectivities:
                element_id += 1
                element = built.model.mesh.elements[element_id]
                mapping = np.asarray(element.get_dof_mapping(built.model.mesh), dtype=np.intp)
                local = displacement[mapping]
                components = element.compute_stiffness_components(built.model.mesh, material)
                energies["TOTAL"] += 0.5 * float(local @ components["total"] @ local)
                if kind == "S3":
                    energies["S3_PL"] += 0.5 * float(local @ components["pl"] @ local)
                else:
                    energies["Q4_PL"] += 0.5 * float(local @ components["pl"] @ local)
                    energies["Q4_RESIDUAL_HOURGLASS"] += 0.5 * float(
                        local @ components["hourglass"] @ local
                    )
                if recover_interface and (i, j) in band:
                    recovery = element.compute_stresses(
                        built.model.mesh,
                        local,
                        material,
                        return_global=True,
                    )
                    moments = []
                    for component in ("xx", "yy", "xy"):
                        top = np.asarray(recovery[f"global_{component}_top"], dtype=float)
                        bottom = np.asarray(recovery[f"global_{component}_bot"], dtype=float)
                        moments.append(float(np.mean(top - bottom)) * thickness**2 / 12.0)
                    coordinates = np.asarray(element.get_node_coordinates(built.model.mesh), dtype=float)
                    centroid = np.mean(coordinates, axis=0)
                    expected = _mindlin_moments(
                        float(centroid[0]),
                        float(centroid[1]),
                        length=float(reference_spec["length"]),
                        width=float(reference_spec["width"]),
                        thickness=thickness,
                        elastic_modulus=float(material_spec["elastic_modulus"]),
                        poisson_ratio=float(material_spec["poisson_ratio"]),
                        modes=moment_modes,
                    )
                    scale = max(float(np.linalg.norm(expected)), pressure * 1.0e-12)
                    error = float(np.linalg.norm(np.asarray(moments) - expected) / scale)
                    cell_errors.setdefault((i, j), []).append(error)
    energy = energies["TOTAL"]
    energy_defect = abs(energy - reference["strain_energy"]) / max(
        abs(reference["strain_energy"]), np.finfo(float).tiny
    )
    denominator = max(abs(energy), np.finfo(float).tiny)
    return (
        {
            "center_displacement": center_w,
            "center_displacement_relative_error": abs(
                center_w - reference["center_displacement"]
            )
            / max(reference["center_displacement"], np.finfo(float).tiny),
            "connectivity_sha256": record["connectivity_sha256"],
            "energy_defect_proxy": math.sqrt(max(energy_defect, 0.0)),
            "finite_element_strain_energy": energy,
            "level": level,
            "mindlin_center_displacement": reference["center_displacement"],
            "mindlin_strain_energy": reference["strain_energy"],
            "pl_participation": {
                key: energies[key] / denominator for key in ("Q4_PL", "S3_PL")
            },
            "q4_residual_hourglass_participation": energies[
                "Q4_RESIDUAL_HOURGLASS"
            ]
            / denominator,
            "record_id": record_id(record),
            "solver_status": solver_status,
        },
        {cell: max(values) for cell, values in cell_errors.items()},
    )


def _ratio_or_unresolved(numerator: float, denominator: float) -> float | None:
    if denominator <= 64.0 * np.finfo(float).eps:
        return None
    return float(numerator / denominator)


def produce_convergence(
    authorities: Any,
    *,
    quick: bool,
) -> tuple[dict[str, Any], dict[str, str]]:
    levels = list(authorities.input["coverage"]["required_levels"])
    sequences = list(authorities.input["coverage"]["convergence_sequences"])
    if quick:
        levels = levels[:2]
        sequences = sequences[:2]
    rows: list[dict[str, Any]] = []
    baseline_errors: dict[int, dict[tuple[int, int], float]] = {}
    interface_rows: list[dict[str, Any]] = []
    convergence_contradictions: list[str] = []
    interface_contradictions: list[str] = []
    pl_contradictions: list[str] = []
    for sequence in sequences:
        sequence_rows: list[dict[str, Any]] = []
        for level in levels:
            record = find_record(
                authorities,
                level=level,
                fraction=int(sequence["fraction_percent"]),
                mask=str(sequence["mask"]),
                diagonal=str(sequence["diagonal"]),
            )
            _progress("CONVERGENCE_CASE_INITIALIZED", record_id=record_id(record))
            row, errors = _plate_case(authorities, record, recover_interface=True)
            sequence_rows.append(row)
            if int(sequence["fraction_percent"]) == 0:
                baseline_errors[level] = errors
            elif errors:
                baseline = baseline_errors.get(level, {})
                shared = sorted(set(errors) & set(baseline))
                mixed_values = [errors[cell] for cell in shared]
                baseline_values = [baseline[cell] for cell in shared]
                mixed_l2 = math.sqrt(sum(value * value for value in mixed_values) / len(mixed_values))
                base_l2 = math.sqrt(
                    sum(value * value for value in baseline_values) / len(baseline_values)
                )
                mixed_p99 = percentile_nearest_rank(mixed_values, 0.99)
                base_p99 = percentile_nearest_rank(baseline_values, 0.99)
                interface_rows.append(
                    {
                        "all_q4_l2_error": base_l2,
                        "all_q4_p99_error": base_p99,
                        "band_cell_count": len(shared),
                        "l2_ratio_to_all_q4": _ratio_or_unresolved(mixed_l2, base_l2),
                        "mixed_l2_error": mixed_l2,
                        "mixed_p99_error": mixed_p99,
                        "p99_ratio_to_all_q4": _ratio_or_unresolved(mixed_p99, base_p99),
                        "record_id": row["record_id"],
                    }
                )
            _progress("CONVERGENCE_CASE_COMPLETED", record_id=record_id(record))
        response_errors = [row["center_displacement_relative_error"] for row in sequence_rows]
        energy_proxies = [row["energy_defect_proxy"] for row in sequence_rows]
        rows.append(
            {
                "energy_defect_proxy_slope": slope(energy_proxies, levels),
                "records": sequence_rows,
                "response_error_slope": slope(response_errors, levels),
                "sequence": sequence,
            }
        )

    convergence_gate = authorities.contract["acceptance_gates"]["convergence"]
    interface_gate = authorities.contract["acceptance_gates"]["interface_resultants"]
    for sequence in rows:
        records = sequence["records"]
        for first, second in zip(records, records[1:]):
            if second["center_displacement_relative_error"] > (
                float(convergence_gate["successive_error_factor_maximum"])
                * first["center_displacement_relative_error"]
                + 1.0e-13
            ):
                convergence_contradictions.append(
                    f"{second['record_id']}:SUCCESSIVE_RESPONSE_ERROR"
                )
    for row in interface_rows:
        fraction = int(row["record_id"].split(":")[1].removesuffix("PCT"))
        l2_limit = float(
            interface_gate[
                "l2_ratio_at_25_percent" if fraction == 25 else "l2_ratio_through_10_percent"
            ]
        )
        p99_limit = float(
            interface_gate[
                "p99_ratio_at_25_percent" if fraction == 25 else "p99_ratio_through_10_percent"
            ]
        )
        if row["l2_ratio_to_all_q4"] is not None and row["l2_ratio_to_all_q4"] > l2_limit:
            interface_contradictions.append(f"{row['record_id']}:INTERFACE_L2")
        if row["p99_ratio_to_all_q4"] is not None and row["p99_ratio_to_all_q4"] > p99_limit:
            interface_contradictions.append(f"{row['record_id']}:INTERFACE_P99")

    pl_limit = float(
        authorities.contract["acceptance_gates"]["pl_participation"][
            "finest_fraction_maximum"
        ]
    )
    for sequence in rows:
        records = sequence["records"]
        # Q4 residual/hourglass energy is reported separately and is not PL.
        for component in ("Q4_PL", "S3_PL"):
            values = [float(row["pl_participation"][component]) for row in records]
            if values and values[-1] > pl_limit:
                pl_contradictions.append(
                    f"{records[-1]['record_id']}:{component}:FINEST_PARTICIPATION"
                )
            if any(second > first + 1.0e-14 for first, second in zip(values, values[1:])):
                pl_contradictions.append(
                    f"{records[-1]['record_id']}:{component}:NOT_NONINCREASING"
                )

    complete_sequence_count = 3 + 4 * 5 * 3
    selected_sequence_count = len(authorities.input["coverage"]["convergence_sequences"])
    full_levels = levels == list(authorities.input["coverage"]["required_levels"])
    complete_scope = selected_sequence_count == complete_sequence_count and full_levels
    convergence_status = (
        FAIL
        if convergence_contradictions and not quick
        else PARTIAL
        # A total-energy defect is not a proven energy-norm error and the
        # calculated slope is not a lower 95% confidence bound.
    )
    interface_unresolved = any(
        row["l2_ratio_to_all_q4"] is None or row["p99_ratio_to_all_q4"] is None
        for row in interface_rows
    )
    interface_status = (
        FAIL
        if interface_contradictions and not quick
        else COMPLETE
        if complete_scope and not interface_unresolved
        else PARTIAL
    )
    pl_status = (
        FAIL
        if pl_contradictions and not quick
        else COMPLETE
        if complete_scope
        else PARTIAL
    )
    all_contradictions = sorted(
        set(convergence_contradictions + interface_contradictions + pl_contradictions)
    )
    payload = {
        "complete_registered_sequence_count": complete_sequence_count,
        "contradictions": all_contradictions,
        "contradictions_classifying": bool(all_contradictions and not quick),
        "energy_scope": (
            "MINDLIN_TOTAL_ENERGY_DEFECT_PROXY_NOT_A_PROVEN_ENERGY_NORM_ERROR"
        ),
        "executed_levels": levels,
        "executed_sequence_count": len(sequences),
        "interface_rows": interface_rows,
        "rows": rows,
        "selected_sequence_count": selected_sequence_count,
        "scope_complete": complete_scope,
        "unresolved_interface_ratio_count": sum(
            row["l2_ratio_to_all_q4"] is None or row["p99_ratio_to_all_q4"] is None
            for row in interface_rows
        ),
    }
    return payload, {
        "convergence": convergence_status,
        "interface_resultants": interface_status,
        "pl_participation": pl_status,
    }


def _strip_split_cells(nx: int, ny: int, fraction_percent: int) -> set[tuple[int, int]]:
    count = nx * ny * int(fraction_percent) // 100
    if count * 100 != nx * ny * int(fraction_percent):
        raise StructuralEvidenceError("locking strip cannot represent the requested exact fraction")
    # A deterministic low-discrepancy ordering; it is a fixture diagnostic and
    # is deliberately not identified with any square-campaign mask hash.
    cells = [(i, j) for j in range(ny) for i in range(nx)]
    cells.sort(key=lambda cell: (((cell[0] * 37 + cell[1] * 17) % (nx * ny)), cell[1], cell[0]))
    return set(cells[:count])


def _locking_strip_case(
    authorities: Any,
    *,
    nx: int,
    ny: int,
    fraction_percent: int,
    diagonal: str,
    length: float,
    tip_force: float,
    thickness: float,
    width: float,
) -> dict[str, Any]:
    from anysolver.assembly import solve_linear
    from anysolver.boundary import FixedSupport, LoadCase
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEModel

    smoke_authorities = _smoke_authorities(authorities)
    model_spec = smoke_authorities.input_payload["model"]
    material_spec = model_spec["material"]
    factories = smoke_authorities.input_payload["factories"]
    section = model_spec["section"]
    model = FEModel(f"mixed_locking_strip_{nx}_{fraction_percent}_{thickness:.1e}")
    model.add_material(
        str(material_spec["name"]),
        float(material_spec["elastic_modulus"]),
        float(material_spec["poisson_ratio"]),
        density=float(material_spec["density"]),
    )
    for i in range(nx + 1):
        for j in range(ny + 1):
            node_id = i * (ny + 1) + j + 1
            model.add_node(node_id, length * i / nx, width * j / ny, 0.0)

    def node_id(i: int, j: int) -> int:
        return i * (ny + 1) + j + 1

    split = _strip_split_cells(nx, ny, fraction_percent)
    element_id = 0
    for i in range(nx):
        for j in range(ny):
            n00, n10 = node_id(i, j), node_id(i + 1, j)
            n11, n01 = node_id(i + 1, j + 1), node_id(i, j + 1)
            if (i, j) not in split:
                connectivities = (("Q4", (n00, n10, n11, n01)),)
            else:
                made = diagonal
                if made == "alternating":
                    made = "backslash" if (i + j) % 2 == 0 else "slash"
                connectivities = (
                    (("S3", (n00, n10, n11)), ("S3", (n00, n11, n01)))
                    if made == "backslash"
                    else (("S3", (n00, n10, n01)), ("S3", (n10, n11, n01)))
                )
            for kind, nodes in connectivities:
                element_id += 1
                if kind == "Q4":
                    element = create_shell_element(
                        element_id,
                        list(nodes),
                        str(material_spec["name"]),
                        formulation=str(factories["q4"]["selector"]),
                        thickness=thickness,
                        drilling_stabilization=float(section["q4_drilling_stabilization"]),
                        hourglass_stabilization=float(section["q4_hourglass_stabilization"]),
                        pl_stabilization=float(section["q4_pl_stabilization"]),
                        planar_tolerance=float(section["q4_planar_tolerance"]),
                        warped_formulation=str(section["q4_warped_formulation"]),
                    )
                else:
                    element = create_shell_element(
                        element_id,
                        list(nodes),
                        str(material_spec["name"]),
                        formulation=str(factories["s3"]["selector"]),
                        thickness=thickness,
                        reference_normal=np.asarray((0.0, 0.0, 1.0)),
                        director_polarity=1,
                    )
                model.add_element(element_id, element)
    fixed = [node_id(0, j) for j in range(ny + 1)]
    model.add_boundary_condition(FixedSupport("clamped", fixed))
    load = LoadCase("tip_force")
    for j in range(ny + 1):
        weight = 0.5 / ny if j in (0, ny) else 1.0 / ny
        load.add_nodal_load(node_id(nx, j), forces=np.asarray((0.0, 0.0, tip_force * weight)))
    model.add_load_case(load)
    displacement, info = solve_linear(model, load, constraint_mode="transformation")
    status = str((info.get("convergence_info") or {}).get("status", "unknown"))
    if status != "converged":
        raise RuntimeError(f"locking strip solve ended {status!r}")
    tip = float(
        sum(
            (0.5 if j in (0, ny) else 1.0)
            * displacement[model.mesh.nodes[node_id(nx, j)].dofs[2]]
            for j in range(ny + 1)
        )
        / ny
    )
    elastic_modulus = float(material_spec["elastic_modulus"])
    reference = tip_force * length**3 / (
        3.0 * elastic_modulus * width * thickness**3 / 12.0
    )
    return {
        "fraction_percent": int(fraction_percent),
        "nx": int(nx),
        "ny": int(ny),
        "reference_displacement": reference,
        "relative_error": abs(abs(tip) - reference) / reference,
        "response_ratio": abs(tip) / reference,
        "solver_status": status,
        "thickness_ratio": thickness / length,
        "tip_displacement": tip,
    }


def produce_locking(authorities: Any, *, quick: bool) -> tuple[dict[str, Any], dict[str, str]]:
    fixture = authorities.input["coverage"]["locking_fixture"]
    thickness_tokens = list(
        authorities.contract["acceptance_gates"]["locking"]["thickness_over_length"]
    )
    nx = int(fixture["longitudinal_divisions"])
    ny = int(fixture["transverse_divisions"])
    fractions = list(fixture["fractions_percent"])
    if quick:
        nx, ny = 20, 2
        thickness_tokens = thickness_tokens[:2]
        fractions = fractions[:2]
    rows: list[dict[str, Any]] = []
    contradictions: list[str] = []
    for fraction in fractions:
        fraction_rows: list[dict[str, Any]] = []
        for token in thickness_tokens:
            _progress(
                "LOCKING_CASE_INITIALIZED",
                fraction_percent=int(fraction),
                thickness_ratio=token,
            )
            row = _locking_strip_case(
                authorities,
                nx=nx,
                ny=ny,
                fraction_percent=int(fraction),
                diagonal=str(fixture["diagonal"]),
                length=float(fixture["length"]),
                tip_force=float(fixture["tip_force"]),
                thickness=float(token) * float(fixture["length"]),
                width=float(fixture["width"]),
            )
            fraction_rows.append(row)
            _progress(
                "LOCKING_CASE_COMPLETED",
                fraction_percent=int(fraction),
                thickness_ratio=token,
            )
        thin = [
            row["response_ratio"]
            for row in fraction_rows
            if row["thickness_ratio"] <= 1.0e-4
        ]
        spread = (
            (max(thin) - min(thin)) / max(sum(thin) / len(thin), np.finfo(float).tiny)
            if len(thin) >= 2
            else None
        )
        rows.append(
            {
                "fraction_percent": int(fraction),
                "rows": fraction_rows,
                "thin_range_response_spread": spread,
            }
        )
    error_limit = _threshold(authorities, "locking", "finest_response_error_maximum")
    spread_limit = _threshold(authorities, "locking", "thin_range_response_spread_maximum")
    for group in rows:
        for row in group["rows"]:
            if row["relative_error"] > error_limit:
                contradictions.append(
                    f"LOCKING:{group['fraction_percent']}PCT:{row['thickness_ratio']:.0e}"
                )
        spread = group["thin_range_response_spread"]
        if spread is not None and spread > spread_limit:
            contradictions.append(f"LOCKING_SPREAD:{group['fraction_percent']}PCT")
    full_fixture = (
        not quick
        and fractions == list(fixture["fractions_percent"])
        and thickness_tokens
        == list(authorities.contract["acceptance_gates"]["locking"]["thickness_over_length"])
    )
    # Even a complete strip is one independently referenced fixture, not all
    # 63 registered topology sequences.  It is therefore representative.
    locking_status = FAIL if contradictions and not quick else PARTIAL
    special_statuses = {
        name: "UNEXECUTED_NO_DEDICATED_FIXTURE_CONSTRUCTED"
        for name in authorities.input["coverage"]["special_fixtures"]
    }
    payload = {
        "analytical_reference": (
            "EULER_BERNOULLI_CANTILEVER_TIP_FORCE_P_L3_OVER_3_E_I"
        ),
        "contradictions": sorted(set(contradictions)),
        "contradictions_classifying": bool(contradictions and not quick),
        "locking_strip_protocol_complete": full_fixture,
        "fixture_mask": str(fixture["mask"]),
        "rows": rows,
        "scope": (
            "INDEPENDENT_LOCKING_STRIP_REPRESENTATIVE_NOT_THE_COMPLETE_"
            "REGISTERED_SQUARE_MASK_CAMPAIGN"
        ),
        "special_fixtures": special_statuses,
    }
    return payload, {
        "locking": locking_status,
        "special_fixtures": PARTIAL,
    }


def produce(authorities: Any, shard_id: str, *, quick: bool = False) -> dict[str, Any]:
    activate_numerics(authorities)
    if shard_id == SHARD_IDS[0]:
        diagnostic, statuses = produce_patch(authorities, quick=quick)
    elif shard_id == SHARD_IDS[1]:
        diagnostic, statuses = produce_convergence(authorities, quick=quick)
    elif shard_id == SHARD_IDS[2]:
        diagnostic, statuses = produce_locking(authorities, quick=quick)
    else:
        raise StructuralEvidenceError(f"unknown structural shard {shard_id!r}")
    terminal = (
        "BLOCKED"
        if any(value == BLOCKED for value in statuses.values())
        else "CONTRADICTION"
        if any(value == FAIL for value in statuses.values())
        else "COMPLETE_PROCESS_STATE"
    )
    coverage = {
        "executed_gate_count": sum(value not in {BLOCKED} for value in statuses.values()),
        "gate_count": len(statuses),
        "representative_only_gate_count": sum(value == PARTIAL for value in statuses.values()),
    }
    made = {
        "authority_sha256": sha256(authorities.input_raw),
        "coverage": coverage,
        "diagnostic_payload": diagnostic,
        "diagnostic_payload_sha256": sha256(canonical_bytes(diagnostic)),
        "execution_commit": authorities.execution_commit,
        "execution_tier": "QUICK_NONCLASSIFYING" if quick else "FORMAL_BOUNDED",
        "execution_tree": authorities.execution_tree,
        "gate_status": statuses,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": SHARD_SCHEMA,
        "shard_id": shard_id,
        "terminal_status": terminal,
    }
    return validate_shard(made, shard_id, authorities=authorities)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-structural-shard", action="store_true", required=True)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--shard-id", choices=SHARD_IDS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--quick-smoke", action="store_true")
    args = parser.parse_args(argv)
    try:
        authorities = load_authorities(args.input) if args.input else load_authorities()
        value = produce(authorities, args.shard_id, quick=bool(args.quick_smoke))
        write_exclusive(args.output, value)
        # A contradiction is a valid terminal scientific result, not a
        # process failure.  Only malformed/failed execution returns nonzero.
        return 0
    except (StructuralEvidenceError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
        print(f"mixed structural producer blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
