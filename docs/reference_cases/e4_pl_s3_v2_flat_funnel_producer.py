"""Stage-4A production-mechanics producer for the flat S3 V2 funnel.

The command validates the frozen 252-record manifest and a canonical Phase-4A
plan before importing NumPy, SciPy, or ANYsolver.  One invocation owns exactly
one diagonal shard: 27 classifying Q4/V2A records and, for the 24 mixed rows,
one separately labelled V1 comparator diagnostic.  A V1 result is never used
as a fallback for a missing or failed V2A result.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

from e4_pl_s3_v2_flat_funnel import (
    ENERGY_NORM_IDENTITY,
    MANIFEST_SHA256,
    REFERENCE_IDENTITY,
    SELECTOR,
    SHARD_SCIENTIFIC_SCHEMA,
    SUPPORT_IDENTITY,
    FlatFunnelError,
    append_progress,
    canonical_bytes,
    progress_record,
    sha256,
    strict_json_load,
    validate_manifest,
    validate_phase_plan,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
)
MANIFEST_GENERATOR_PATH = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_manifest.py"
)

PAYLOAD_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-production-payload-v1"
LOAD_IDENTITY = "UNIFORM_REFERENCE_NORMAL_DEAD_PRESSURE_1000_PA_V1"
CLASSIFICATION = "CLASSIFYING_Q4_V2A_PRODUCTION_MECHANICS"
V1_DISPOSITION = "NONCLASSIFYING_V1_COMPARATOR_NEVER_FALLBACK"
REFERENCE_VECTOR_ENCODING = "CANONICAL_JSON_ROW_MAJOR_NODAL_6DOF_V1"
REFERENCE_DOF_ORDER = ("ux", "uy", "uz", "theta_x", "theta_y", "theta_d")
Q4_FORMULATION_ID = "E4_PL_QUALIFIED_Q4_HYBRID_V2"
V2A_FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1"
V1_FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V1"

LENGTH = 1.0
WIDTH = 1.0
THICKNESS = 0.01
PRESSURE = 1000.0
ELASTIC_MODULUS = 210_000_000_000.0
POISSON_RATIO = 0.3
DENSITY = 7850.0
SHEAR_CORRECTION = 5.0 / 6.0
SERIES_MAX_ODD_INDEX = 99


def _load_manifest_generator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "_s3_v2_phase4a_manifest_generator",
        MANIFEST_GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise FlatFunnelError("cannot load the frozen connectivity generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_assignment(
    plan_path: Path,
    *,
    shard_index: int,
    selector: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any], str]:
    """Validate and return one exact Phase-4A diagonal assignment."""

    manifest_value, manifest_raw = strict_json_load(MANIFEST_PATH)
    records = validate_manifest(manifest_value, manifest_raw)
    plan_value, plan_raw = strict_json_load(Path(plan_path))
    plan = validate_phase_plan(plan_value, plan_raw, records, "4A")
    if (
        selector != SELECTOR
        or plan["selector"] != SELECTOR
        or plan["phase"] != "4A"
        or plan["scope"] != "full"
        or plan["record_count"] != 81
    ):
        raise FlatFunnelError("producer accepts only the exact Phase-4A V2A plan")
    if isinstance(shard_index, bool) or shard_index not in range(3):
        raise FlatFunnelError("shard-index must be 0, 1, or 2")
    shard = plan["shards"][shard_index]
    if len(shard["records"]) != 27:
        raise FlatFunnelError("Phase-4A diagonal assignment must contain 27 records")
    return plan, shard, sha256(plan_raw)


def _node_id(i: int, j: int, level: int) -> int:
    return int(j) * (int(level) + 1) + int(i) + 1


def _hard_navier_supports(model: Any, level: int) -> dict[str, int]:
    """Apply the frozen translation-plus-tangential-rotation support."""

    from anysolver.boundary import BoundaryCondition

    n = int(level)
    x_edges = sorted(
        {_node_id(0, j, n) for j in range(n + 1)}
        | {_node_id(n, j, n) for j in range(n + 1)}
    )
    y_edges = sorted(
        {_node_id(i, 0, n) for i in range(n + 1)}
        | {_node_id(i, n, n) for i in range(n + 1)}
    )
    all_edges = sorted(set(x_edges) | set(y_edges))
    model.add_boundary_condition(
        BoundaryCondition(
            "hard_navier_edge_translations",
            all_edges,
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        )
    )
    model.add_boundary_condition(
        BoundaryCondition(
            "hard_navier_theta_y_on_x_edges",
            x_edges,
            {"ry": 0.0},
        )
    )
    model.add_boundary_condition(
        BoundaryCondition(
            "hard_navier_theta_x_on_y_edges",
            y_edges,
            {"rx": 0.0},
        )
    )
    return {
        "edge_nodes": len(all_edges),
        "theta_x_y_edge_constraints": len(y_edges),
        "theta_y_x_edge_constraints": len(x_edges),
        "translation_constraints": 3 * len(all_edges),
    }


def _build_model(
    record: Mapping[str, Any],
    *,
    s3_selector: str,
) -> tuple[Any, dict[int, str], dict[str, int], dict[str, int]]:
    """Build one exact manifest topology with Q4 plus the requested S3."""

    import numpy as np
    from anysolver.boundary import LoadCase
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEModel

    generator = _load_manifest_generator()
    level = int(record["level"])
    split_count = int(record["split_base_cell_count"])
    mask = str(record["mask"])
    diagonal = str(record["diagonal"])
    base_cells = () if split_count == 0 else generator.selected_base_cells(mask, split_count)
    split_cells = set(generator.expanded_split_cells(base_cells, level))
    if len(split_cells) != int(record["split_refined_cell_count"]):
        raise FlatFunnelError("refined split cells differ from the frozen manifest")

    model = FEModel(f"S3_V2_PHASE4A_{s3_selector}_{level}_{mask}_{diagonal}")
    model.add_material(
        "phase4a_steel",
        ELASTIC_MODULUS,
        POISSON_RATIO,
        density=DENSITY,
    )
    for j in range(level + 1):
        for i in range(level + 1):
            model.add_node(
                _node_id(i, j, level),
                LENGTH * i / level,
                WIDTH * j / level,
                0.0,
            )

    kinds: dict[int, str] = {}
    formulation_counts = {"qualified_q4": 0, "v2a_s3": 0, "v1_s3": 0}
    element_id = 0
    for j in range(level):
        for i in range(level):
            for kind, nodes in generator._cell_connectivity(
                i,
                j,
                level,
                split=(i, j) in split_cells,
                diagonal=diagonal,
            ):
                element_id += 1
                if kind == "Q4":
                    element = create_shell_element(
                        element_id,
                        list(nodes),
                        "phase4a_steel",
                        formulation="e4-pl",
                        thickness=THICKNESS,
                        drilling_stabilization=0.001,
                        hourglass_stabilization=0.001,
                        pl_stabilization=1.0,
                        planar_tolerance=1.0e-10,
                        warped_formulation="varying_frame",
                    )
                    if str(getattr(element, "formulation_id", "")) != Q4_FORMULATION_ID:
                        raise FlatFunnelError("Q4 factory did not return the qualified Q4")
                    formulation_counts["qualified_q4"] += 1
                else:
                    kwargs: dict[str, Any] = {
                        "formulation": s3_selector,
                        "thickness": THICKNESS,
                        "reference_normal": np.asarray((0.0, 0.0, 1.0)),
                    }
                    if s3_selector == "e4-pl-s3":
                        kwargs["director_polarity"] = 1
                    element = create_shell_element(
                        element_id,
                        list(nodes),
                        "phase4a_steel",
                        **kwargs,
                    )
                    expected = (
                        V2A_FORMULATION_ID
                        if s3_selector == SELECTOR
                        else V1_FORMULATION_ID
                    )
                    if str(getattr(element, "formulation_id", "")) != expected:
                        raise FlatFunnelError(
                            f"S3 factory returned {getattr(element, 'formulation_id', None)!r}, "
                            f"expected {expected!r}"
                        )
                    formulation_counts["v2a_s3" if s3_selector == SELECTOR else "v1_s3"] += 1
                model.add_element(element_id, element)
                kinds[element_id] = kind

    topology_digest = generator.connectivity_sha256(level, frozenset(split_cells), diagonal)
    if topology_digest != record["connectivity_sha256"]:
        raise FlatFunnelError("constructed connectivity differs from the manifest")
    element_counts = {
        "Q4": sum(kind == "Q4" for kind in kinds.values()),
        "S3": sum(kind == "S3" for kind in kinds.values()),
    }
    if element_counts != {
        "Q4": int(record["q4_element_count"]),
        "S3": int(record["s3_element_count"]),
    }:
        raise FlatFunnelError("constructed element counts differ from the manifest")
    supports = _hard_navier_supports(model, level)
    load = LoadCase("phase4a_uniform_dead_pressure")
    for registered_id in model.mesh.elements:
        load.add_pressure_load(int(registered_id), PRESSURE)
    model.add_load_case(load)
    return model, kinds, element_counts, formulation_counts | supports


def _mindlin_amplitudes() -> tuple[Any, Any, Any, Any, Any]:
    """Independently solve the continuum modal stationarity equations."""

    import numpy as np

    odd = np.arange(1, SERIES_MAX_ODD_INDEX + 1, 2, dtype=float)
    m, n = np.meshgrid(odd, odd, indexing="ij")
    a = math.pi * m / LENGTH
    b = math.pi * n / WIDTH
    load = 16.0 * PRESSURE / (math.pi**2 * m * n)
    rigidity = ELASTIC_MODULUS * THICKNESS**3 / (
        12.0 * (1.0 - POISSON_RATIO**2)
    )
    shear = (
        SHEAR_CORRECTION
        * ELASTIC_MODULUS
        / (2.0 * (1.0 + POISSON_RATIO))
        * THICKNESS
    )
    transverse = 0.5 * (1.0 - POISSON_RATIO)
    coupling = 0.5 * (1.0 + POISSON_RATIO)
    matrices = np.empty(m.shape + (3, 3), dtype=float)
    matrices[..., 0, 0] = shear * (a * a + b * b)
    matrices[..., 0, 1] = matrices[..., 1, 0] = shear * a
    matrices[..., 0, 2] = matrices[..., 2, 0] = shear * b
    matrices[..., 1, 1] = shear + rigidity * (a * a + transverse * b * b)
    matrices[..., 2, 2] = shear + rigidity * (b * b + transverse * a * a)
    matrices[..., 1, 2] = matrices[..., 2, 1] = rigidity * coupling * a * b
    right = np.zeros(m.shape + (3,), dtype=float)
    right[..., 0] = load
    # NumPy 2 treats a stacked ``(..., M)`` right-hand side as matrices rather
    # than stacked vectors.  Retain the explicit singleton column so the
    # batched solve has an unambiguous ``(..., M, 1)`` signature.
    solved = np.linalg.solve(matrices, right[..., None])[..., 0]
    return odd, solved[..., 0], solved[..., 1], solved[..., 2], load


_REFERENCE_CACHE: dict[int, tuple[Any, str, float]] = {}


def mindlin_nodal_reference(level: int) -> tuple[Any, str, float]:
    """Return the frozen independent Mindlin field in global nodal DOF order."""

    import numpy as np

    nlevel = int(level)
    cached = _REFERENCE_CACHE.get(nlevel)
    if cached is not None:
        vector, digest, center = cached
        return vector.copy(), digest, center
    odd, w_amplitude, theta_x_amplitude, theta_y_amplitude, _load = (
        _mindlin_amplitudes()
    )
    coordinates = np.linspace(0.0, 1.0, nlevel + 1)
    angles = math.pi * np.outer(coordinates, odd)
    sine = np.sin(angles)
    cosine = np.cos(angles)
    transverse = np.einsum("mn,im,jn->ji", w_amplitude, sine, sine, optimize=True)
    theta_x = np.einsum(
        "mn,im,jn->ji", theta_x_amplitude, cosine, sine, optimize=True
    )
    theta_y = np.einsum(
        "mn,im,jn->ji", theta_y_amplitude, sine, cosine, optimize=True
    )
    vector = np.zeros(((nlevel + 1) ** 2, 6), dtype=float)
    vector[:, 2] = transverse.reshape(-1)
    vector[:, 3] = theta_x.reshape(-1)
    vector[:, 4] = theta_y.reshape(-1)
    # Enforce the exact discrete hard-Navier trace, avoiding sine(pi) roundoff
    # in a reference input that is compared in assembled discrete energy.
    for j in range(nlevel + 1):
        for i in range(nlevel + 1):
            row = _node_id(i, j, nlevel) - 1
            if i in (0, nlevel) or j in (0, nlevel):
                vector[row, :3] = 0.0
            if i in (0, nlevel):
                vector[row, 4] = 0.0
            if j in (0, nlevel):
                vector[row, 3] = 0.0
    made = np.asarray(vector.reshape(-1), dtype=np.float64)
    reference_document = {
        "dof_order": list(REFERENCE_DOF_ORDER),
        "level": nlevel,
        "values": [float(value) for value in made],
    }
    digest = sha256(canonical_bytes(reference_document))
    center_id = _node_id(nlevel // 2, nlevel // 2, nlevel) - 1
    center = float(vector[center_id, 2])
    stored = (made.copy(), digest, center)
    _REFERENCE_CACHE[nlevel] = stored
    return made.copy(), digest, center


def _solve_and_measure(
    model: Any,
    kinds: Mapping[int, str],
    reference: Any,
) -> tuple[dict[str, Any], dict[str, float], Any]:
    """Assemble once, solve free DOFs, and compute raw energy forms."""

    import numpy as np
    from scipy.sparse.linalg import spsolve
    from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix

    stiffness, _assembly = assemble_stiffness_matrix(model)
    load, _load_info = assemble_load_vector(model, model.load_cases[0])
    model.apply_boundary_conditions()
    fixed = np.asarray(sorted(model.mesh.dof_manager._constrained_dofs), dtype=np.intp)
    free_mask = np.ones(stiffness.shape[0], dtype=bool)
    free_mask[fixed] = False
    free = np.flatnonzero(free_mask)
    if reference.shape != (stiffness.shape[0],):
        raise FlatFunnelError("Mindlin nodal reference size differs from assembled DOFs")
    solution = np.zeros(stiffness.shape[0], dtype=float)
    solution[free] = spsolve(stiffness[free][:, free], load[free])
    if not np.all(np.isfinite(solution)):
        raise FlatFunnelError("Phase-4A linear solution contains nonfinite values")
    residual = stiffness[free] @ solution - load[free]
    residual_relative = float(
        np.linalg.norm(residual) / max(np.linalg.norm(load[free]), np.finfo(float).tiny)
    )

    stiffness_solution = stiffness @ solution
    stiffness_reference = stiffness @ reference
    solution_total = float(solution @ stiffness_solution)
    reference_total = float(reference @ stiffness_reference)
    cross = float(solution @ stiffness_reference)
    error_total_raw = solution_total + reference_total - 2.0 * cross
    rounding_scale = max(abs(solution_total), abs(reference_total), abs(cross), 1.0)
    if error_total_raw < -256.0 * np.finfo(float).eps * rounding_scale:
        raise FlatFunnelError("assembled energy-error quadratic form is negative")
    error_total = max(error_total_raw, 0.0)

    component_quadratics = {
        "physical": 0.0,
        "q4_pl": 0.0,
        "s3_pl": 0.0,
        "q4_hourglass": 0.0,
    }
    material = model.get_material("phase4a_steel")
    for element_id, element in model.mesh.elements.items():
        mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        local = solution[mapping]
        components = element.compute_stiffness_components(model.mesh, material)
        component_quadratics["physical"] += float(local @ components["physical"] @ local)
        if kinds[int(element_id)] == "Q4":
            component_quadratics["q4_pl"] += float(local @ components["pl"] @ local)
            component_quadratics["q4_hourglass"] += float(
                local @ components["hourglass"] @ local
            )
        else:
            component_quadratics["s3_pl"] += float(local @ components["pl"] @ local)
    reconstruction = sum(component_quadratics.values())
    if abs(reconstruction - solution_total) > 2.0e-10 * max(abs(solution_total), 1.0):
        raise FlatFunnelError("component energies do not reconstruct total stiffness energy")
    strain_energies = {
        name: 0.5 * value for name, value in component_quadratics.items()
    }
    strain_energies["total"] = 0.5 * solution_total
    denominator = max(solution_total, np.finfo(float).tiny)
    participation = {
        "q4_hourglass": component_quadratics["q4_hourglass"] / denominator,
        "q4_pl": component_quadratics["q4_pl"] / denominator,
        "s3_pl": component_quadratics["s3_pl"] / denominator,
    }
    return (
        {
            "free_dofs": int(free.size),
            "residual_relative": residual_relative,
            "status": "CONVERGED_DIRECT_SPARSE",
            "total_dofs": int(stiffness.shape[0]),
        },
        {
            "error_total": error_total,
            "reference_total": reference_total,
            "solution_reference_cross": cross,
            "solution_total": solution_total,
        }
        | {
            "energy_absolute": math.sqrt(error_total),
            "energy_relative": math.sqrt(
                error_total / max(reference_total, np.finfo(float).tiny)
            ),
        }
        | {f"strain_{key}": value for key, value in strain_energies.items()}
        | {f"participation_{key}": value for key, value in participation.items()},
        solution,
    )


def produce_case(
    member: Mapping[str, Any],
    *,
    s3_selector: str = SELECTOR,
) -> dict[str, Any]:
    """Execute one manifest member with either V2A or diagnostic V1 S3."""

    import numpy as np

    record = member["record"]
    model, kinds, element_counts, combined_counts = _build_model(
        record,
        s3_selector=s3_selector,
    )
    reference, reference_digest, reference_center = mindlin_nodal_reference(
        int(record["level"])
    )
    solver, measured, solution = _solve_and_measure(model, kinds, reference)
    center_node = model.mesh.nodes[
        _node_id(int(record["level"]) // 2, int(record["level"]) // 2, int(record["level"]))
    ]
    center_solution = float(solution[center_node.dofs[2]])
    formulation_counts = {
        key: int(combined_counts[key])
        for key in ("qualified_q4", "v2a_s3", "v1_s3")
    }
    support_counts = {
        key: int(combined_counts[key])
        for key in (
            "edge_nodes",
            "theta_x_y_edge_constraints",
            "theta_y_x_edge_constraints",
            "translation_constraints",
        )
    }
    made = {
        "connectivity_sha256": str(record["connectivity_sha256"]),
        "diagonal": str(record["diagonal"]),
        "element_counts": element_counts,
        "energy_norm": {
            "absolute": measured["energy_absolute"],
            "relative": measured["energy_relative"],
        },
        "formulation_counts": formulation_counts,
        "level": int(record["level"]),
        "manifest_index": int(member["manifest_index"]),
        "mask": str(record["mask"]),
        "node_count": int(record["node_count"]),
        "participation": {
            "q4_hourglass": measured["participation_q4_hourglass"],
            "q4_pl": measured["participation_q4_pl"],
            "s3_pl": measured["participation_s3_pl"],
        },
        "quadratic_forms": {
            key: measured[key]
            for key in (
                "error_total",
                "reference_total",
                "solution_reference_cross",
                "solution_total",
            )
        },
        "record_id": str(member["record_id"]),
        "reference": {
            "center_transverse_displacement": reference_center,
            "dof_order": list(REFERENCE_DOF_ORDER),
            "nodal_input_encoding": REFERENCE_VECTOR_ENCODING,
            "reference_nodal_input_sha256": reference_digest,
            "series_max_odd_index": SERIES_MAX_ODD_INDEX,
        },
        "response": {
            "center_transverse_displacement": center_solution,
            "relative_error": abs(center_solution - reference_center)
            / max(abs(reference_center), np.finfo(float).tiny),
        },
        "s3_area_fraction_percent": int(record["s3_area_fraction_percent"]),
        "solution_energies": {
            "physical": measured["strain_physical"],
            "q4_hourglass": measured["strain_q4_hourglass"],
            "q4_pl": measured["strain_q4_pl"],
            "s3_pl": measured["strain_s3_pl"],
            "total": measured["strain_total"],
        },
        "solver": solver,
        "support_counts": support_counts,
    }
    if s3_selector == SELECTOR:
        made["classification"] = CLASSIFICATION
    else:
        made["classification"] = "NONCLASSIFYING_V1_COMPARATOR_ONLY"
        made["formulation_id"] = V1_FORMULATION_ID
    return made


def run_assignment(
    plan_path: Path,
    *,
    shard_index: int,
    selector: str,
    output: Path,
    progress: Path,
) -> dict[str, Any]:
    """Run one exact diagonal shard and exclusively publish canonical JSON."""

    plan, shard, plan_digest = load_assignment(
        plan_path,
        shard_index=shard_index,
        selector=selector,
    )
    output = Path(output)
    progress = Path(progress)
    if output.exists() or progress.exists():
        raise FlatFunnelError("scientific and progress outputs must be exclusive")
    records = shard["records"]
    sequence = 0
    append_progress(
        progress,
        progress_record(
            str(shard["assignment_id"]),
            sequence=sequence,
            phase="4A_PRODUCTION_INITIALIZED",
            completed=0,
            total=len(records),
        ),
    )
    classifying: list[dict[str, Any]] = []
    comparators: list[dict[str, Any]] = []
    for completed, member in enumerate(records, start=1):
        # V2A always executes first.  Its failure aborts the shard; V1 is never
        # substituted for the missing classifying evidence.
        classifying.append(produce_case(member, s3_selector=SELECTOR))
        if int(member["record"]["s3_element_count"]) > 0:
            comparators.append(produce_case(member, s3_selector="e4-pl-s3"))
        sequence += 1
        append_progress(
            progress,
            progress_record(
                str(shard["assignment_id"]),
                sequence=sequence,
                phase="4A_PRODUCTION_RECORD_COMPLETED",
                completed=completed,
                total=len(records),
            ),
        )
    if len(classifying) != 27 or len(comparators) != 24:
        raise FlatFunnelError("Phase-4A shard coverage must be 27 V2A plus 24 V1 diagnostics")
    scientific_payload = {
        "assignment_id": str(shard["assignment_id"]),
        "classifying_records": classifying,
        "diagonal": str(shard["diagonal"]),
        "phase": "4A",
        "protocol": {
            "classification": CLASSIFICATION,
            "energy_norm_id": ENERGY_NORM_IDENTITY,
            "load_id": LOAD_IDENTITY,
            "reference_id": REFERENCE_IDENTITY,
            "support_id": SUPPORT_IDENTITY,
        },
        "schema": PAYLOAD_SCHEMA,
        "scope": "full",
        "v1_comparator_diagnostics": comparators,
        "v1_comparator_disposition": V1_DISPOSITION,
    }
    record_ids = [str(member["record_id"]) for member in records]
    document = {
        "assignment_sha256": str(shard["assignment_sha256"]),
        "plan_sha256": plan_digest,
        "record_count": len(record_ids),
        "record_ids": record_ids,
        "record_ids_sha256": sha256(canonical_bytes(record_ids)),
        "schema": SHARD_SCIENTIFIC_SCHEMA,
        "scientific_payload": scientific_payload,
        "scientific_payload_sha256": sha256(canonical_bytes(scientific_payload)),
        "selector": SELECTOR,
        "terminal": "ACCEPTED_FOR_AGGREGATION",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(canonical_bytes(document))
        stream.flush()
        os.fsync(stream.fileno())
    sequence += 1
    append_progress(
        progress,
        progress_record(
            str(shard["assignment_id"]),
            sequence=sequence,
            phase="4A_PRODUCTION_OUTPUT_COMPLETED",
            completed=len(records),
            total=len(records),
        ),
    )
    return document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-flat-assignment", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--selector", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    run_assignment(
        arguments.run_flat_assignment,
        shard_index=arguments.shard_index,
        selector=arguments.selector,
        output=arguments.output,
        progress=arguments.progress,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
