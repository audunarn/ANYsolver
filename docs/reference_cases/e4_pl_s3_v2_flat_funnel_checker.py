"""Independent scientific checker for the S3 V2A Stage-4A funnel.

The checker does not import the producer or ANYsolver mechanics.  It validates
one diagonal shard, reconstructs the frozen Mindlin reference with a local
three-by-three solver, recomputes every stored quadratic-form identity and all
classifying sequence metrics, and writes a deterministic canonical result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


PROOF_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-shard-scientific-v1"
PAYLOAD_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-production-payload-v1"
PLAN_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1"
ASSIGNMENT_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-assignment-v1"
RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-checker-result-v1"
SELECTOR = "e4-pl-s3-v2"
DIAGONALS = ("slash", "backslash", "alternating")
LEVELS = (20, 40, 80)
MASKS = ("dispersed", "chain")
FRACTIONS = (1, 5, 10, 25)
FORMAL_THRESHOLDS = {
    "energy_norm_slope_lower_95_percent": 0.90,
    "finest_error_ratio_at_25_percent": 1.50,
    "finest_error_ratio_through_10_percent": 1.25,
    "response_slope_lower_bound": 1.80,
    "response_slope_maximum_deficit_from_all_q4": 0.15,
    "successive_error_factor_maximum": 1.02,
}
ADVISORY_THRESHOLDS = {
    "finest_error_ratio_at_25_percent": 1.35,
    "finest_error_ratio_through_10_percent": 1.15,
}
REFERENCE = {
    "elastic_modulus": 210_000_000_000.0,
    "length": 1.0,
    "poisson_ratio": 0.3,
    "pressure": 1000.0,
    "series_max_odd_index": 99,
    "thickness": 0.01,
    "width": 1.0,
}
SUPPORT_ID = "HARD_NAVIER_TRANSLATIONS_PLUS_TANGENTIAL_ROTATIONS_V2"
REFERENCE_ID = "INDEPENDENT_NAVIER_REISSNER_MINDLIN_UNIFORM_PRESSURE_V2"
ENERGY_ID = "DISCRETE_STIFFNESS_ENERGY_NORM_OF_UH_MINUS_NODAL_MINDLIN_REFERENCE_V1"
LOAD_ID = "UNIFORM_REFERENCE_NORMAL_DEAD_PRESSURE_1000_PA_V1"
BLOCKED = "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE"
PASS = "PASS_E4_PL_S3_V2A_FLAT_FUNNEL_PHASE_4A"
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
_Z_ONE_SIDED_95 = 1.6448536269514722


class CheckerError(RuntimeError):
    """Raised when a proof is not valid classifying evidence."""


def _reject_constant(value: str) -> None:
    raise CheckerError(f"non-finite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise CheckerError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, CheckerError):
            raise
        raise CheckerError(f"{label} is not strict UTF-8 JSON: {exc}") from exc


def strict_json_load(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CheckerError(f"cannot read {path}: {exc}") from exc
    return strict_json_bytes(raw, str(path)), raw


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any, location: str) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise CheckerError(f"non-finite number at {location}")
            return
        if isinstance(item, list):
            for index, member in enumerate(item):
                visit(member, f"{location}[{index}]")
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise CheckerError(f"non-string key at {location}")
                visit(member, f"{location}.{key}")
            return
        raise CheckerError(f"unsupported canonical value at {location}")

    visit(value, "$")
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _exact(value: Any, keys: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise CheckerError(
            f"{location} keys differ: expected={sorted(keys)} actual={actual}"
        )
    return value


def _finite(value: Any, location: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CheckerError(f"{location} must be a finite real scalar")
    made = float(value)
    if not math.isfinite(made) or (nonnegative and made < 0.0):
        raise CheckerError(f"{location} must be finite and valid")
    return made


def _integer(value: Any, location: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise CheckerError(f"{location} must be an integer >= {minimum}")
    return value


def _digest(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise CheckerError(f"{location} must be an uppercase SHA-256")
    return value


def _close(first: float, second: float, *, ulps: float = 256.0) -> bool:
    scale = max(1.0, abs(first), abs(second))
    return abs(first - second) <= ulps * math.ulp(1.0) * scale


def _solve3(matrix: Sequence[Sequence[float]], rhs: Sequence[float]) -> tuple[float, float, float]:
    made = [list(map(float, row)) + [float(value)] for row, value in zip(matrix, rhs)]
    for pivot in range(3):
        selected = max(range(pivot, 3), key=lambda row: abs(made[row][pivot]))
        if selected != pivot:
            made[pivot], made[selected] = made[selected], made[pivot]
        divisor = made[pivot][pivot]
        if divisor == 0.0 or not math.isfinite(divisor):
            raise CheckerError("independent Mindlin mode system is singular")
        for column in range(pivot, 4):
            made[pivot][column] /= divisor
        for row in range(3):
            if row == pivot:
                continue
            factor = made[row][pivot]
            for column in range(pivot, 4):
                made[row][column] -= factor * made[pivot][column]
    return made[0][3], made[1][3], made[2][3]


_REFERENCE_DOCUMENT_CACHE: dict[int, tuple[dict[str, Any], float]] = {}


def reference_vector_document(level: int) -> tuple[dict[str, Any], float]:
    """Reconstruct the frozen field independently, including its byte encoding.

    NumPy is used only for the independent continuum series.  No producer or
    ANYsolver module is imported.  Keeping the registered vector encoding
    byte-exact lets the checker bind the reference input rather than trusting
    the producer's digest claim.
    """

    cached = _REFERENCE_DOCUMENT_CACHE.get(level)
    if cached is not None:
        return cached
    import numpy as np

    odd = np.arange(1, int(REFERENCE["series_max_odd_index"]) + 1, 2, dtype=float)
    m, n = np.meshgrid(odd, odd, indexing="ij")
    a = math.pi * m / REFERENCE["length"]
    b = math.pi * n / REFERENCE["width"]
    load = 16.0 * REFERENCE["pressure"] / (math.pi**2 * m * n)
    e = REFERENCE["elastic_modulus"]
    nu = REFERENCE["poisson_ratio"]
    thickness = REFERENCE["thickness"]
    rigidity = e * thickness**3 / (12.0 * (1.0 - nu**2))
    shear = (5.0 / 6.0) * e / (2.0 * (1.0 + nu)) * thickness
    transverse = 0.5 * (1.0 - nu)
    coupling = 0.5 * (1.0 + nu)
    matrices = np.empty(m.shape + (3, 3), dtype=float)
    matrices[..., 0, 0] = shear * (a * a + b * b)
    matrices[..., 0, 1] = matrices[..., 1, 0] = shear * a
    matrices[..., 0, 2] = matrices[..., 2, 0] = shear * b
    matrices[..., 1, 1] = shear + rigidity * (a * a + transverse * b * b)
    matrices[..., 2, 2] = shear + rigidity * (b * b + transverse * a * a)
    matrices[..., 1, 2] = matrices[..., 2, 1] = rigidity * coupling * a * b
    right = np.zeros(m.shape + (3,), dtype=float)
    right[..., 0] = load
    solved = np.linalg.solve(matrices, right[..., None])[..., 0]
    coordinates = np.linspace(0.0, 1.0, level + 1)
    angles = math.pi * np.outer(coordinates, odd)
    sine = np.sin(angles)
    cosine = np.cos(angles)
    w = np.einsum("mn,im,jn->ji", solved[..., 0], sine, sine, optimize=True)
    theta_x = np.einsum(
        "mn,im,jn->ji", solved[..., 1], cosine, sine, optimize=True
    )
    theta_y = np.einsum(
        "mn,im,jn->ji", solved[..., 2], sine, cosine, optimize=True
    )
    vector = np.zeros(((level + 1) ** 2, 6), dtype=float)
    vector[:, 2] = w.reshape(-1)
    vector[:, 3] = theta_x.reshape(-1)
    vector[:, 4] = theta_y.reshape(-1)
    for j in range(level + 1):
        for i in range(level + 1):
            row = j * (level + 1) + i
            if i in (0, level) or j in (0, level):
                vector[row, :3] = 0.0
            if i in (0, level):
                vector[row, 4] = 0.0
            if j in (0, level):
                vector[row, 3] = 0.0
    document = {
        "dof_order": ["ux", "uy", "uz", "theta_x", "theta_y", "theta_d"],
        "level": level,
        "values": [float(value) for value in vector.reshape(-1)],
    }
    center = float(vector[(level // 2) * (level + 1) + level // 2, 2])
    made = (document, center)
    _REFERENCE_DOCUMENT_CACHE[level] = made
    return made


def _positive_log_slope(values: Sequence[float]) -> tuple[float, float]:
    if len(values) != len(LEVELS) or any(value <= 0.0 for value in values):
        raise CheckerError("slope values must be three strictly positive numbers")
    x = [math.log(float(level)) for level in LEVELS]
    y = [-math.log(float(value)) for value in values]
    mean_x = sum(x) / 3.0
    mean_y = sum(y) / 3.0
    sxx = sum((value - mean_x) ** 2 for value in x)
    slope = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / sxx
    intercept = mean_y - slope * mean_x
    residual = sum((b - (intercept + slope * a)) ** 2 for a, b in zip(x, y))
    standard_error = math.sqrt(max(residual, 0.0) / sxx)
    return slope, slope - _Z_ONE_SIDED_95 * standard_error


def _validate_record(
    raw_record: Any,
    expected: Mapping[str, Any],
    *,
    diagnostic_v1: bool = False,
) -> dict[str, Any]:
    keys = {
        "classification",
        "connectivity_sha256",
        "diagonal",
        "element_counts",
        "energy_norm",
        "formulation_counts",
        "level",
        "manifest_index",
        "mask",
        "node_count",
        "participation",
        "quadratic_forms",
        "record_id",
        "reference",
        "response",
        "s3_area_fraction_percent",
        "solution_energies",
        "solver",
        "support_counts",
    }
    if diagnostic_v1:
        keys.add("formulation_id")
    record = _exact(
        raw_record,
        keys,
        "$.scientific_payload.classifying_records[]",
    )
    if diagnostic_v1:
        if (
            record["classification"] != "NONCLASSIFYING_V1_COMPARATOR_ONLY"
            or record["formulation_id"] != "E4_PL_QUALIFIED_S3_COMPANION_V1"
        ):
            raise CheckerError("V1 diagnostic identity differs")
    elif record["classification"] != "CLASSIFYING_Q4_V2A_PRODUCTION_MECHANICS":
        raise CheckerError("V2A classifying record identity differs")
    if (
        record["record_id"] != expected["record_id"]
        or record["manifest_index"] != expected["manifest_index"]
        or record["connectivity_sha256"]
        != expected["record"]["connectivity_sha256"]
        or record["level"] != expected["record"]["level"]
        or record["mask"] != expected["record"]["mask"]
        or record["diagonal"] != expected["record"]["diagonal"]
        or record["s3_area_fraction_percent"]
        != expected["record"]["s3_area_fraction_percent"]
    ):
        raise CheckerError("classifying record differs from its frozen assignment")
    level = _integer(record["level"], "$.record.level", minimum=1)
    if level not in LEVELS:
        raise CheckerError("classifying record level is outside Phase 4A")
    node_count = _integer(record["node_count"], "$.record.node_count", minimum=1)
    if node_count != (level + 1) ** 2:
        raise CheckerError("classifying node count differs from the regular grid")
    counts = _exact(record["element_counts"], {"Q4", "S3"}, "$.record.element_counts")
    if counts != {
        "Q4": expected["record"]["q4_element_count"],
        "S3": expected["record"]["s3_element_count"],
    }:
        raise CheckerError("element counts differ from the frozen manifest")
    formulation = _exact(
        record["formulation_counts"],
        {"qualified_q4", "v1_s3", "v2a_s3"},
        "$.record.formulation_counts",
    )
    expected_formulation = {
        "qualified_q4": counts["Q4"],
        "v1_s3": counts["S3"] if diagnostic_v1 else 0,
        "v2a_s3": 0 if diagnostic_v1 else counts["S3"],
    }
    if formulation != expected_formulation:
        raise CheckerError("formulation counts permit a fallback element")
    supports = _exact(
        record["support_counts"],
        {
            "edge_nodes",
            "theta_x_y_edge_constraints",
            "theta_y_x_edge_constraints",
            "translation_constraints",
        },
        "$.record.support_counts",
    )
    expected_edge_nodes = 4 * level
    if supports != {
        "edge_nodes": expected_edge_nodes,
        "theta_x_y_edge_constraints": 2 * (level + 1),
        "theta_y_x_edge_constraints": 2 * (level + 1),
        "translation_constraints": 3 * expected_edge_nodes,
    }:
        raise CheckerError("hard-Navier support counts differ")
    solver = _exact(
        record["solver"],
        {"free_dofs", "residual_relative", "status", "total_dofs"},
        "$.record.solver",
    )
    if solver["status"] != "CONVERGED_DIRECT_SPARSE" or solver["total_dofs"] != 6 * node_count:
        raise CheckerError("record is not a converged full six-DOF solve")
    _integer(solver["free_dofs"], "$.record.solver.free_dofs", minimum=1)
    residual = _finite(solver["residual_relative"], "$.record.solver.residual_relative", nonnegative=True)
    if residual > 1.0e-8:
        raise CheckerError("record residual is too large for scientific inspection")
    reference = _exact(
        record["reference"],
        {
            "center_transverse_displacement",
            "dof_order",
            "nodal_input_encoding",
            "reference_nodal_input_sha256",
            "series_max_odd_index",
        },
        "$.record.reference",
    )
    if reference["series_max_odd_index"] != int(REFERENCE["series_max_odd_index"]):
        raise CheckerError("Mindlin series authority differs")
    reference_document, expected_center = reference_vector_document(level)
    stored_center = _finite(reference["center_transverse_displacement"], "$.record.reference.center")
    if not _close(stored_center, expected_center, ulps=4096.0):
        raise CheckerError("independent Mindlin centre displacement differs")
    if reference["dof_order"] != reference_document["dof_order"] or (
        reference["nodal_input_encoding"]
        != "CANONICAL_JSON_ROW_MAJOR_NODAL_6DOF_V1"
    ):
        raise CheckerError("Mindlin nodal-vector encoding differs")
    expected_reference_hash = sha256(canonical_bytes(reference_document))
    if _digest(reference["reference_nodal_input_sha256"], "$.record.reference.hash") != expected_reference_hash:
        raise CheckerError("independent Mindlin nodal-vector hash differs")
    response = _exact(
        record["response"],
        {"center_transverse_displacement", "relative_error"},
        "$.record.response",
    )
    center = _finite(response["center_transverse_displacement"], "$.record.response.center")
    relative_error = _finite(response["relative_error"], "$.record.response.relative_error", nonnegative=True)
    recomputed_response_error = abs(center - stored_center) / abs(stored_center)
    if not _close(relative_error, recomputed_response_error):
        raise CheckerError("centre-displacement relative error was not recomputed")
    quadratic = _exact(
        record["quadratic_forms"],
        {"error_total", "reference_total", "solution_reference_cross", "solution_total"},
        "$.record.quadratic_forms",
    )
    solution_total = _finite(quadratic["solution_total"], "$.quadratic.solution_total", nonnegative=True)
    reference_total = _finite(quadratic["reference_total"], "$.quadratic.reference_total", nonnegative=True)
    cross = _finite(quadratic["solution_reference_cross"], "$.quadratic.cross")
    error_total = _finite(quadratic["error_total"], "$.quadratic.error_total", nonnegative=True)
    recomputed_error_total = max(solution_total + reference_total - 2.0 * cross, 0.0)
    if not _close(error_total, recomputed_error_total, ulps=4096.0):
        raise CheckerError("energy error quadratic form was not recomputed")
    if reference_total <= 0.0:
        raise CheckerError("reference stiffness energy is not positive")
    energy = _exact(record["energy_norm"], {"absolute", "relative"}, "$.record.energy_norm")
    absolute = _finite(energy["absolute"], "$.record.energy.absolute", nonnegative=True)
    relative = _finite(energy["relative"], "$.record.energy.relative", nonnegative=True)
    if not _close(absolute, math.sqrt(recomputed_error_total), ulps=4096.0):
        raise CheckerError("absolute energy norm was not recomputed")
    if not _close(relative, math.sqrt(recomputed_error_total / reference_total), ulps=4096.0):
        raise CheckerError("relative energy norm was not recomputed")
    energies = _exact(
        record["solution_energies"],
        {"physical", "q4_hourglass", "q4_pl", "s3_pl", "total"},
        "$.record.solution_energies",
    )
    values = {key: _finite(value, f"$.record.solution_energies.{key}", nonnegative=True) for key, value in energies.items()}
    if not _close(
        values["total"],
        values["physical"] + values["q4_hourglass"] + values["q4_pl"] + values["s3_pl"],
        ulps=4096.0,
    ):
        raise CheckerError("solution energy components do not sum to total")
    participation = _exact(
        record["participation"],
        {"q4_hourglass", "q4_pl", "s3_pl"},
        "$.record.participation",
    )
    denominator = max(values["total"], math.ulp(1.0))
    for key in participation:
        stored = _finite(participation[key], f"$.record.participation.{key}", nonnegative=True)
        if not _close(stored, values[key] / denominator, ulps=4096.0):
            raise CheckerError(f"{key} participation was not recomputed")
    return {
        "energy_relative": relative,
        "level": level,
        "mask": record["mask"],
        "fraction": record["s3_area_fraction_percent"],
        "record_id": record["record_id"],
        "response_error": relative_error,
    }


def _sequence_result(
    rows: Sequence[Mapping[str, Any]], baseline: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if [row["level"] for row in rows] != list(LEVELS):
        raise CheckerError("mixed sequence does not have ordered N20/N40/N80 coverage")
    response_values = [float(row["response_error"]) for row in rows]
    energy_values = [float(row["energy_relative"]) for row in rows]
    baseline_values = [float(row["response_error"]) for row in baseline]
    response_slope, _response_lower = _positive_log_slope(response_values)
    q4_slope, _q4_lower = _positive_log_slope(baseline_values)
    energy_slope, energy_lower = _positive_log_slope(energy_values)
    if baseline_values[-1] <= 0.0:
        raise CheckerError("all-Q4 finest response error cannot define a ratio")
    ratio = response_values[-1] / baseline_values[-1]
    fraction = int(rows[0]["fraction"])
    formal_ratio_limit = (
        FORMAL_THRESHOLDS["finest_error_ratio_at_25_percent"]
        if fraction == 25
        else FORMAL_THRESHOLDS["finest_error_ratio_through_10_percent"]
    )
    advisory_ratio_limit = (
        ADVISORY_THRESHOLDS["finest_error_ratio_at_25_percent"]
        if fraction == 25
        else ADVISORY_THRESHOLDS["finest_error_ratio_through_10_percent"]
    )
    failures = []
    if response_slope < FORMAL_THRESHOLDS["response_slope_lower_bound"]:
        failures.append("RESPONSE_SLOPE")
    if q4_slope - response_slope > FORMAL_THRESHOLDS["response_slope_maximum_deficit_from_all_q4"]:
        failures.append("RESPONSE_SLOPE_DEFICIT")
    if energy_lower < FORMAL_THRESHOLDS["energy_norm_slope_lower_95_percent"]:
        failures.append("ENERGY_SLOPE_LOWER_95")
    for coarse, fine in zip(response_values, response_values[1:]):
        if fine > FORMAL_THRESHOLDS["successive_error_factor_maximum"] * coarse:
            failures.append("SUCCESSIVE_RESPONSE_ERROR")
            break
    if ratio > formal_ratio_limit:
        failures.append("FINEST_RESPONSE_ERROR_RATIO")
    return {
        "advisory_triggered": ratio > advisory_ratio_limit,
        "all_q4_response_slope": q4_slope,
        "energy_norm_slope": energy_slope,
        "energy_norm_slope_lower_95_percent": energy_lower,
        "energy_norm_values": energy_values,
        "failed_subgates": failures,
        "finest_error_ratio_to_all_q4": ratio,
        "fraction_percent": fraction,
        "mask": rows[0]["mask"],
        "record_ids": [row["record_id"] for row in rows],
        "response_error_slope": response_slope,
        "response_errors": response_values,
        "slope_deficit_from_all_q4": q4_slope - response_slope,
        "successive_refinement_passed": "SUCCESSIVE_RESPONSE_ERROR" not in failures,
    }


def verify_shard(proof_path: Path, plan_path: Path) -> dict[str, Any]:
    proof, proof_raw = strict_json_load(proof_path)
    plan, plan_raw = strict_json_load(plan_path)
    if proof_raw != canonical_bytes(proof) or plan_raw != canonical_bytes(plan):
        raise CheckerError("proof and plan must both be canonical JSON")
    plan = _exact(
        plan,
        {
            "advisory_review_triggers",
            "formal_thresholds",
            "manifest_sha256",
            "phase",
            "prerequisites",
            "record_count",
            "schema",
            "selector",
            "shards",
            "scope",
        },
        "$plan",
    )
    if (
        plan["schema"] != PLAN_SCHEMA
        or plan["phase"] != "4A"
        or plan["scope"] != "full"
        or plan["selector"] != SELECTOR
        or plan["record_count"] != 81
        or plan["formal_thresholds"]
        != {key: f"{value:.2f}" for key, value in FORMAL_THRESHOLDS.items()}
        or plan["advisory_review_triggers"]
        != {key: f"{value:.2f}" for key, value in ADVISORY_THRESHOLDS.items()}
    ):
        raise CheckerError("Stage 4A plan identity or thresholds differ")
    proof = _exact(
        proof,
        {
            "assignment_sha256",
            "plan_sha256",
            "record_count",
            "record_ids",
            "record_ids_sha256",
            "schema",
            "scientific_payload",
            "scientific_payload_sha256",
            "selector",
            "terminal",
        },
        "$proof",
    )
    if (
        proof["schema"] != PROOF_SCHEMA
        or proof["selector"] != SELECTOR
        or proof["terminal"] != "ACCEPTED_FOR_AGGREGATION"
        or proof["plan_sha256"] != sha256(plan_raw)
        or proof["record_count"] != 27
    ):
        raise CheckerError("proof outer identity differs")
    if _digest(proof["record_ids_sha256"], "$.proof.record_ids_sha256") != sha256(canonical_bytes(proof["record_ids"])):
        raise CheckerError("proof record IDs hash differs")
    if _digest(proof["scientific_payload_sha256"], "$.proof.payload_hash") != sha256(canonical_bytes(proof["scientific_payload"])):
        raise CheckerError("proof scientific payload hash differs")
    payload = _exact(
        proof["scientific_payload"],
        {
            "assignment_id",
            "classifying_records",
            "diagonal",
            "phase",
            "protocol",
            "schema",
            "scope",
            "v1_comparator_diagnostics",
            "v1_comparator_disposition",
        },
        "$.scientific_payload",
    )
    if (
        payload["schema"] != PAYLOAD_SCHEMA
        or payload["phase"] != "4A"
        or payload["scope"] != "full"
        or payload["diagonal"] not in DIAGONALS
        or payload["v1_comparator_disposition"]
        != "NONCLASSIFYING_V1_COMPARATOR_NEVER_FALLBACK"
    ):
        raise CheckerError("scientific payload identity differs")
    protocol = _exact(
        payload["protocol"],
        {"classification", "energy_norm_id", "load_id", "reference_id", "support_id"},
        "$.scientific_payload.protocol",
    )
    if protocol != {
        "classification": "CLASSIFYING_Q4_V2A_PRODUCTION_MECHANICS",
        "energy_norm_id": ENERGY_ID,
        "load_id": LOAD_ID,
        "reference_id": REFERENCE_ID,
        "support_id": SUPPORT_ID,
    }:
        raise CheckerError("scientific protocol differs")
    shards = plan["shards"]
    matching = [item for item in shards if item.get("assignment_id") == payload["assignment_id"]]
    if len(matching) != 1:
        raise CheckerError("payload assignment is not unique in the plan")
    assignment = _exact(
        matching[0],
        {
            "assignment_id",
            "assignment_sha256",
            "diagonal",
            "manifest_sha256",
            "phase",
            "records",
            "schema",
            "selector",
            "scope",
        },
        "$assignment",
    )
    if (
        assignment["schema"] != ASSIGNMENT_SCHEMA
        or assignment["diagonal"] != payload["diagonal"]
        or assignment["assignment_sha256"] != proof["assignment_sha256"]
        or assignment["assignment_id"] != payload["assignment_id"]
    ):
        raise CheckerError("proof assignment binding differs")
    expected_ids = [item["record_id"] for item in assignment["records"]]
    if proof["record_ids"] != expected_ids:
        raise CheckerError("proof record ordering differs from the assignment")
    classifying = payload["classifying_records"]
    diagnostics = payload["v1_comparator_diagnostics"]
    if not isinstance(classifying, list) or len(classifying) != 27:
        raise CheckerError("shard must contain exactly 27 classifying records")
    if not isinstance(diagnostics, list) or len(diagnostics) != 24:
        raise CheckerError("shard must contain exactly 24 V1 diagnostics")
    checked = [
        _validate_record(record, expected)
        for record, expected in zip(classifying, assignment["records"])
    ]
    mixed_assignments = [
        item for item in assignment["records"] if item["record"]["s3_element_count"] > 0
    ]
    for diagnostic, expected in zip(diagnostics, mixed_assignments):
        _validate_record(diagnostic, expected, diagnostic_v1=True)
    diagnostic_coordinates = {
        (item["level"], item["mask"], item["s3_area_fraction_percent"])
        for item in diagnostics
    }
    expected_diagnostic_coordinates = {
        (level, mask, fraction)
        for level in LEVELS
        for mask in MASKS
        for fraction in FRACTIONS
    }
    if diagnostic_coordinates != expected_diagnostic_coordinates:
        raise CheckerError("V1 comparator diagnostic coverage differs")
    baseline = [row for row in checked if row["fraction"] == 0 and row["mask"] == "none"]
    baseline.sort(key=lambda row: row["level"])
    if len(baseline) != 3:
        raise CheckerError("shard must contain three all-Q4 baseline records")
    sequences = []
    for mask in MASKS:
        for fraction in FRACTIONS:
            rows = [
                row
                for row in checked
                if row["mask"] == mask and row["fraction"] == fraction
            ]
            rows.sort(key=lambda row: row["level"])
            sequences.append(_sequence_result(rows, baseline))
    failures = sorted(
        f"{item['mask']}:{item['fraction_percent']}:{failure}"
        for item in sequences
        for failure in item["failed_subgates"]
    )
    advisory = any(item["advisory_triggered"] for item in sequences)
    terminal = NO_GO if failures else PASS
    return {
        "advisory_review_required": bool(advisory and not failures),
        "assignment_id": payload["assignment_id"],
        "assignment_sha256": proof["assignment_sha256"],
        "classifying_record_count": 27,
        "diagonal": payload["diagonal"],
        "formal_failures": failures,
        "plan_sha256": sha256(plan_raw),
        "production_restriction": PRODUCTION_RESTRICTION,
        "proof_sha256": sha256(proof_raw),
        "schema": RESULT_SCHEMA,
        "sequence_results": sequences,
        "successor_expansion_authorized": bool(not failures and not advisory),
        "terminal": terminal,
        "v1_diagnostic_record_count": 24,
    }


def write_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(dict(value))
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise CheckerError(f"refusing to overwrite checker output: {path}") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = verify_shard(args.proof.resolve(), args.plan.resolve())
    write_exclusive(args.output.resolve(), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
