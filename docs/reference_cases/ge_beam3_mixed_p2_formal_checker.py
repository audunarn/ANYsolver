"""Independently check raw GE-Beam3 P2 proof packets.

This program must remain independent of the production element and all legacy
beam mechanics.  It reconstructs comparisons from the raw proof values and the
frozen P2 case/correction authority; producer predicates are never trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np


REFERENCE = Path(__file__).resolve().parent
STUDY_ID = "study_ge_beam3.mixed_straight_solver_parity_v1"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
PROOF_SCHEMA = "anysolver.ge-beam3-mixed-p2-proof-v1"
CHECK_SCHEMA = "anysolver.ge-beam3-mixed-p2-check-v1"
PROOF_TERMINAL = "NONCLASSIFYING_GE_BEAM3_P2_PROOF_COMPLETE"
PASS = "NONCLASSIFYING_GE_BEAM3_P2_CHECK_PASS"
FINDING = "NONCLASSIFYING_GE_BEAM3_P2_CHECK_SCIENTIFIC_FINDING"
MALFORMED = "NONCLASSIFYING_GE_BEAM3_P2_CHECK_MALFORMED_EVIDENCE"

BOUND_INPUTS = (
    "ge_beam3_mixed_p2_baseline.json",
    "ge_beam3_mixed_p2_cases.json",
    "ge_beam3_mixed_p2_contract.json",
    "ge_beam3_mixed_p2_independent_reference.py",
    "ge_beam3_mixed_p2_plan_review.json",
    "ge_beam3_mixed_p2_state_schema.json",
    "ge_beam3_mixed_p2_recovery_correction.json",
    "ge_beam3_mixed_p2_recovery_correction_contract.json",
    "ge_beam3_mixed_p2_recovery_correction_reference.py",
    "ge_beam3_mixed_p2_recovery_correction_review.json",
)
TOP_FIELDS = {
    "bindings",
    "candidate_id",
    "content_sha256",
    "counts",
    "effective_recovery_case_ids",
    "predicates",
    "records",
    "schema",
    "study_id",
    "terminal",
}
GROUP_ORDER = (
    "SOLVER_CHART_OR_STATE",
    "LOAD_MASS_OR_RECOVERY",
    "MODAL_OR_BUCKLING",
)
RECORD_GROUPS = {
    "solver_chart_state": "SOLVER_CHART_OR_STATE",
    "load_mass_recovery": "LOAD_MASS_OR_RECOVERY",
    "modal_buckling": "MODAL_OR_BUCKLING",
}
DOF = {name: index for index, name in enumerate(("ux", "uy", "uz", "rx", "ry", "rz"))}


class MalformedProof(ValueError):
    pass


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise MalformedProof(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _reject_constant(token: str) -> None:
    raise MalformedProof(f"nonfinite JSON token: {token}")


def _decode(raw: bytes) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MalformedProof("invalid UTF-8 JSON") from exc


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise MalformedProof("nonfinite canonical value")
    if isinstance(value, Mapping):
        for child in value.values():
            _finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _finite(child)


def canonical_bytes(value: Any) -> bytes:
    _finite(value)
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _load_authority(name: str) -> tuple[bytes, dict[str, Any]]:
    raw = (REFERENCE / name).read_bytes()
    value = _decode(raw)
    if not isinstance(value, dict):
        raise MalformedProof(f"authority {name} is not an object")
    return raw, value


def _array(value: Any, *, name: str) -> np.ndarray:
    if not isinstance(value, dict) or set(value) != {"data_hex", "dtype", "shape"}:
        raise MalformedProof(f"{name} typed-array schema")
    if value["dtype"] != "<f8":
        raise MalformedProof(f"{name} dtype")
    shape = value["shape"]
    if (
        not isinstance(shape, list)
        or any(type(item) is not int or item < 0 for item in shape)
        or len(shape) > 3
    ):
        raise MalformedProof(f"{name} shape")
    data_hex = value["data_hex"]
    if not isinstance(data_hex, str) or data_hex != data_hex.upper():
        raise MalformedProof(f"{name} hex encoding")
    try:
        raw = bytes.fromhex(data_hex)
    except ValueError as exc:
        raise MalformedProof(f"{name} hex encoding") from exc
    count = math.prod(shape)
    if len(raw) != 8 * count:
        raise MalformedProof(f"{name} byte count")
    made = np.frombuffer(raw, dtype="<f8").reshape(tuple(shape)).copy()
    if not np.all(np.isfinite(made)):
        raise MalformedProof(f"{name} contains nonfinite values")
    return made


def _array_shape(value: Any, shape: tuple[int, ...], *, name: str) -> np.ndarray:
    made = _array(value, name=name)
    if made.shape != shape:
        raise MalformedProof(f"{name} semantic shape")
    return made


def _fields(value: Mapping[str, Any], expected: set[str], *, name: str) -> None:
    if set(value) != expected:
        raise MalformedProof(f"{name} field set")


def _hex_float(value: Any, *, name: str) -> float:
    if not isinstance(value, str):
        raise MalformedProof(f"{name} is not a float hex string")
    try:
        made = float.fromhex(value)
    except ValueError as exc:
        raise MalformedProof(f"{name} float hex") from exc
    if not math.isfinite(made) or made.hex() != value:
        raise MalformedProof(f"{name} noncanonical float hex")
    return made


def _normalized(left: Any, right: Any) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    def magnitude(value: np.ndarray) -> float:
        if value.ndim <= 2:
            return float(np.linalg.norm(value, ord=np.inf))
        return float(np.max(np.abs(value), initial=0.0))

    return magnitude(a - b) / max(1.0, magnitude(a), magnitude(b))


def _relative_scalar(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-30)


def _rotation_exp(vector: np.ndarray) -> np.ndarray:
    theta = float(np.linalg.norm(vector))
    skew = np.asarray(
        ((0.0, -vector[2], vector[1]), (vector[2], 0.0, -vector[0]), (-vector[1], vector[0], 0.0))
    )
    if theta < 1.0e-8:
        a = 1.0 - theta * theta / 6.0 + theta**4 / 120.0
        b = 0.5 - theta * theta / 24.0 + theta**4 / 720.0
    else:
        a = math.sin(theta) / theta
        b = (1.0 - math.cos(theta)) / (theta * theta)
    return np.eye(3) + a * skew + b * (skew @ skew)


def _triad(geometry: Mapping[str, Any]) -> np.ndarray:
    nodes = np.asarray(geometry["nodes"], dtype=float)
    axis = nodes[2] - nodes[0]
    axis /= np.linalg.norm(axis)
    orientation = np.asarray(geometry["reference_orientation"], dtype=float)
    second = orientation - float(orientation @ axis) * axis
    second /= np.linalg.norm(second)
    third = np.cross(axis, second)
    return np.column_stack((axis, second, third))


def _state_bytes(value: Any, *, name: str, state_schema: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, str) or value != value.upper():
        raise MalformedProof(f"{name} state hex")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise MalformedProof(f"{name} state hex") from exc
    state = _decode(raw)
    if not isinstance(state, dict) or raw != canonical_bytes(state):
        raise MalformedProof(f"{name} state is not canonical")
    if set(state) != set(state_schema["state_exact_keys"]):
        raise MalformedProof(f"{name} state field set")
    if state.get("state_schema") != state_schema["state_schema"]:
        raise MalformedProof(f"{name} state schema")
    if state.get("candidate_id") != CANDIDATE_ID or state.get("formulation_id") != CANDIDATE_ID:
        raise MalformedProof(f"{name} state candidate")
    digest = state.get("state_integrity_sha256")
    body = dict(state)
    body.pop("state_integrity_sha256", None)
    if digest != _sha(canonical_bytes(body)):
        raise MalformedProof(f"{name} state integrity")
    return state


class _Findings:
    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def require(self, condition: bool, *, group: str, case_id: str, check: str) -> None:
        if not condition:
            self.items.append({"case_id": case_id, "check": check, "group": group})


def _exact_ids(records: Any, expected: tuple[str, ...], group: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise MalformedProof(f"{group} records")
    ids = tuple(item.get("case_id") for item in records)
    if ids != expected or len(set(ids)) != len(ids):
        raise MalformedProof(f"{group} record order")
    return {str(item["case_id"]): item for item in records}


def _check_solver(
    records: Any,
    cases: Mapping[str, Any],
    state_schema: Mapping[str, Any],
    findings: _Findings,
) -> None:
    group = "SOLVER_CHART_OR_STATE"
    expected = (
        "NONZERO_SOLVER_CHART",
        "TWO_NONCOMMUTING_COMMITS",
        "REJECTED_TRIAL_ROLLBACK_AND_CUTBACK",
        "SPLIT_RESTART_IDENTITY",
        "SHARED_NODE_DISTINCT_MATERIAL_TRIADS",
        "CONNECTIVITY_REVERSAL_STATE",
    )
    by_id = _exact_ids(records, expected, "solver_chart_state")
    authority = {item["case_id"]: item for item in cases["cases"]["solver_state"]}

    item = by_id[expected[0]]
    _fields(item, {"analytic_directional_force", "base_force", "case_id", "direction", "minus_force", "plus_force", "step", "tangent"}, name=expected[0])
    step = _hex_float(item["step"], name="solver step")
    plus = _array_shape(item["plus_force"], (18,), name="plus force")
    minus = _array_shape(item["minus_force"], (18,), name="minus force")
    analytic = _array_shape(item["analytic_directional_force"], (18,), name="analytic force")
    tangent = _array_shape(item["tangent"], (18, 18), name="solver tangent")
    direction = _array_shape(item["direction"], (18,), name="solver direction")
    _array_shape(item["base_force"], (18,), name="base force")
    finite = (plus - minus) / (2.0 * step)
    limit = float(authority[expected[0]]["expected"]["directional_tangent_relative_max"])
    findings.require(_normalized(finite, analytic) <= limit, group=group, case_id=expected[0], check="DIRECTIONAL_TANGENT")
    findings.require(abs(np.linalg.norm(direction) - 1.0) <= 2.0e-15, group=group, case_id=expected[0], check="DIRECTION_NORMALIZED")
    registered_direction = np.asarray(authority[expected[0]]["direction"], dtype=float).reshape(18)
    registered_direction /= np.linalg.norm(registered_direction)
    findings.require(_normalized(direction, registered_direction) <= 2.0e-15 and step == 2.0e-6, group=group, case_id=expected[0], check="REGISTERED_DIFFERENCE_PROBE")
    findings.require(_normalized(tangent, tangent.T) <= float(cases["tolerances"]["matrix_symmetry_normalized"]), group=group, case_id=expected[0], check="TANGENT_SYMMETRY")

    item = by_id[expected[1]]
    _fields(item, {"case_id", "continuous", "increments", "initial", "opposite", "split"}, name=expected[1])
    initial = _array(item["initial"], name="initial rotations")
    increments = [_array(value, name="increment") for value in item["increments"]]
    registered_initial = np.asarray(authority[expected[1]]["initial_spatial_operators"], dtype=float)
    registered_increments = [np.asarray(value, dtype=float) for value in authority[expected[1]]["increments"]]
    findings.require(_normalized(initial, registered_initial) == 0.0 and all(_normalized(left, right) == 0.0 for left, right in zip(increments, registered_increments)), group=group, case_id=expected[1], check="REGISTERED_ROTATION_INPUTS")
    wanted = np.asarray([
        _rotation_exp(increments[1][node]) @ _rotation_exp(increments[0][node]) @ initial[node]
        for node in range(3)
    ])
    continuous = _array(item["continuous"], name="continuous rotations")
    split = _array(item["split"], name="split rotations")
    opposite = _array(item["opposite"], name="opposite rotations")
    findings.require(_normalized(continuous, wanted) <= 2.0e-15, group=group, case_id=expected[1], check="NONCOMMUTING_COMPOSITION")
    findings.require(continuous.tobytes() == split.tobytes(), group=group, case_id=expected[1], check="SPLIT_ROTATION_BITWISE")
    lower = float(authority[expected[1]]["expected"]["opposite_order_must_differ_by_frobenius_more_than"])
    findings.require(np.linalg.norm(opposite - continuous) > lower, group=group, case_id=expected[1], check="ORDER_NONCOMMUTATIVITY")

    item = by_id[expected[2]]
    _fields(item, {"after_operators", "after_state_hex", "after_u", "before_operators", "before_state_hex", "before_u", "case_id", "cutback_base", "cutback_increment", "exception_class"}, name=expected[2])
    before_u = _array(item["before_u"], name="rollback before u")
    after_u = _array(item["after_u"], name="rollback after u")
    before_q = _array(item["before_operators"], name="rollback before operators")
    after_q = _array(item["after_operators"], name="rollback after operators")
    cutback_q = _array(item["cutback_base"], name="cutback base")
    cutback_increment = _array(item["cutback_increment"], name="cutback increment")
    _state_bytes(item["before_state_hex"], name="rollback before", state_schema=state_schema)
    _state_bytes(item["after_state_hex"], name="rollback after", state_schema=state_schema)
    case = authority[expected[2]]
    accepted_r = np.asarray(case["accepted_rotation_coordinates"], dtype=float)
    rejected_r = np.asarray(case["rejected_rotation_coordinates"], dtype=float)
    findings.require(before_u.tobytes() == after_u.tobytes(), group=group, case_id=expected[2], check="DISCARD_U_BITWISE")
    findings.require(before_q.tobytes() == after_q.tobytes() == cutback_q.tobytes(), group=group, case_id=expected[2], check="DISCARD_OPERATOR_BITWISE")
    findings.require(item["before_state_hex"] == item["after_state_hex"], group=group, case_id=expected[2], check="DISCARD_STATE_BYTE_IDENTICAL")
    findings.require(_normalized(cutback_increment, 0.05 * (rejected_r - accepted_r)) <= 2.0e-15, group=group, case_id=expected[2], check="CUTBACK_FROM_COMMITTED")
    findings.require(item["exception_class"] in {"GeBeam3MixedLocalSolveError", "RotationDomainError"}, group=group, case_id=expected[2], check="TYPED_REJECTION")

    item = by_id[expected[3]]
    _fields(item, {"case_id", "checkpoint_hex", "continuous_final_hex", "continuous_force", "continuous_tangent", "roundtrip_hex", "split_final_hex", "split_force", "split_tangent"}, name=expected[3])
    _state_bytes(item["checkpoint_hex"], name="checkpoint", state_schema=state_schema)
    _state_bytes(item["roundtrip_hex"], name="roundtrip", state_schema=state_schema)
    _state_bytes(item["continuous_final_hex"], name="continuous final", state_schema=state_schema)
    _state_bytes(item["split_final_hex"], name="split final", state_schema=state_schema)
    findings.require(item["checkpoint_hex"] == item["roundtrip_hex"], group=group, case_id=expected[3], check="CHECKPOINT_BYTE_IDENTICAL")
    findings.require(item["continuous_final_hex"] == item["split_final_hex"], group=group, case_id=expected[3], check="SPLIT_FINAL_BYTE_IDENTICAL")
    findings.require(_normalized(_array(item["continuous_force"], name="continuous force"), _array(item["split_force"], name="split force")) <= 1.0e-11, group=group, case_id=expected[3], check="SPLIT_FORCE")
    findings.require(_normalized(_array(item["continuous_tangent"], name="continuous tangent"), _array(item["split_tangent"], name="split tangent")) <= 1.0e-11, group=group, case_id=expected[3], check="SPLIT_TANGENT")

    item = by_id[expected[4]]
    _fields(item, {"absolute_frame_first", "absolute_frame_second", "case_id", "shared_operator_first", "shared_operator_second"}, name=expected[4])
    operator_a = _array(item["shared_operator_first"], name="shared operator first")
    operator_b = _array(item["shared_operator_second"], name="shared operator second")
    frame_a = _array(item["absolute_frame_first"], name="absolute frame first")
    frame_b = _array(item["absolute_frame_second"], name="absolute frame second")
    shared_case = authority[expected[4]]
    geometry_by_id = {value["geometry_id"]: value for value in cases["cases"]["geometry"]}
    first_reference = _triad(geometry_by_id[shared_case["elements"][0]["geometry_id"]])
    second_reference = _triad(geometry_by_id[shared_case["elements"][1]["geometry_id"]])
    findings.require(operator_a.tobytes() == operator_b.tobytes(), group=group, case_id=expected[4], check="SHARED_OPERATOR_BITWISE")
    findings.require(not np.array_equal(frame_a, frame_b), group=group, case_id=expected[4], check="DISTINCT_MATERIAL_FRAMES")
    findings.require(_normalized(frame_a, operator_a @ first_reference) <= 2.0e-15 and _normalized(frame_b, operator_b @ second_reference) <= 2.0e-15, group=group, case_id=expected[4], check="MATERIAL_FRAME_RECONSTRUCTION")

    item = by_id[expected[5]]
    _fields(item, {"case_id", "forward_energy", "forward_force", "forward_resultant", "forward_strain", "forward_tangent", "permutation", "reverse_energy", "reverse_force", "reverse_resultant", "reverse_strain", "reverse_tangent", "strain_map"}, name=expected[5])
    permutation = _array(item["permutation"], name="reversal permutation")
    strain_map = _array(item["strain_map"], name="reversal strain map")
    ff = _array(item["forward_force"], name="forward force")
    fr = _array(item["reverse_force"], name="reverse force")
    kf = _array(item["forward_tangent"], name="forward tangent")
    kr = _array(item["reverse_tangent"], name="reverse tangent")
    sf = _array(item["forward_strain"], name="forward strain")
    sr = _array(item["reverse_strain"], name="reverse strain")
    rf = _array(item["forward_resultant"], name="forward resultant")
    rr = _array(item["reverse_resultant"], name="reverse resultant")
    energy_f = _hex_float(item["forward_energy"], name="forward energy")
    energy_r = _hex_float(item["reverse_energy"], name="reverse energy")
    expected_permutation = np.zeros((18, 18))
    for reverse_node, forward_node in enumerate((2, 1, 0)):
        expected_permutation[6 * reverse_node : 6 * reverse_node + 6, 6 * forward_node : 6 * forward_node + 6] = np.eye(6)
    findings.require(np.array_equal(permutation, expected_permutation), group=group, case_id=expected[5], check="REVERSAL_PERMUTATION_AUTHORITY")
    findings.require(np.array_equal(strain_map, np.diag((1.0, -1.0, 1.0, 1.0, -1.0, 1.0))), group=group, case_id=expected[5], check="REVERSAL_STRAIN_MAP_AUTHORITY")
    findings.require(abs(energy_f - energy_r) / max(1.0, abs(energy_f), abs(energy_r)) <= 1.0e-11, group=group, case_id=expected[5], check="REVERSAL_ENERGY")
    findings.require(_normalized(permutation.T @ fr, ff) <= 1.0e-11, group=group, case_id=expected[5], check="REVERSAL_FORCE")
    findings.require(_normalized(permutation.T @ kr @ permutation, kf) <= 1.0e-11, group=group, case_id=expected[5], check="REVERSAL_TANGENT")
    findings.require(_normalized(sr[::-1] @ strain_map, sf) <= 1.0e-11, group=group, case_id=expected[5], check="REVERSAL_STRAIN")
    findings.require(_normalized(rr[::-1] @ strain_map, rf) <= 1.0e-11, group=group, case_id=expected[5], check="REVERSAL_RESULTANT")


def _expected_line_vector(case: Mapping[str, Any], geometry: Mapping[str, Any]) -> np.ndarray:
    if case["case_id"] == "TIP_NODAL_SPATIAL_DEAD":
        made = np.zeros(18)
        node = int(case["node_local_index"])
        made[6 * node : 6 * node + 3] = np.asarray(case["force"], dtype=float)
        made[6 * node + 3 : 6 * node + 6] = np.asarray(case["moment"], dtype=float)
        return made
    force = np.asarray(case["force_per_reference_length_at_nodes"], dtype=float)
    couple = np.asarray(case["couple_per_reference_length_at_nodes"], dtype=float)
    if case["classification"] == "MATERIAL_DEAD":
        frame = _triad(geometry)
        force = force @ frame.T
        couple = couple @ frame.T
    length = float(np.linalg.norm(np.asarray(geometry["nodes"], dtype=float)[2] - np.asarray(geometry["nodes"], dtype=float)[0]))
    made = np.zeros((3, 6))
    coefficient = np.asarray(((2.0, 1.0), (1.0, 2.0))) / 6.0
    for left, right in ((0, 1), (1, 2)):
        for local_i, node_i in enumerate((left, right)):
            for local_j, node_j in enumerate((left, right)):
                made[node_i, :3] += 0.5 * length * coefficient[local_i, local_j] * force[node_j]
                made[node_i, 3:] += 0.5 * length * coefficient[local_i, local_j] * couple[node_j]
    return made.reshape(18)


def _expected_mass(case: Mapping[str, Any], geometry: Mapping[str, Any], section: Mapping[str, Any]) -> np.ndarray:
    frame = _triad(geometry)
    transform = np.zeros((6, 6))
    transform[:3, :3] = frame
    transform[3:, 3:] = frame
    local = np.asarray(section["mass_matrix_per_reference_length"], dtype=float)
    spatial = transform @ local @ transform.T
    nodes = np.asarray(geometry["nodes"], dtype=float)
    cell = 0.5 * float(np.linalg.norm(nodes[2] - nodes[0]))
    coefficient = np.asarray(((1.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 3.0)))
    made = np.zeros((18, 18))
    for left, right in ((0, 1), (1, 2)):
        for i, node_i in enumerate((left, right)):
            for j, node_j in enumerate((left, right)):
                made[6 * node_i : 6 * node_i + 6, 6 * node_j : 6 * node_j + 6] += cell * coefficient[i, j] * spatial
    return made


def _check_load_mass_recovery(
    records: Any,
    cases: Mapping[str, Any],
    correction: Mapping[str, Any],
    findings: _Findings,
) -> None:
    group = "LOAD_MASS_OR_RECOVERY"
    expected = (
        "TIP_NODAL_SPATIAL_DEAD",
        "UNIFORM_LINE_SPATIAL_DEAD",
        "LINEAR_LINE_MATERIAL_DEAD_SKEW",
        "CONSERVATIVE_FOLLOWER_REJECT",
        "NONCONSERVATIVE_FOLLOWER_REJECT",
        "REFERENCE_MASS_DIAGONAL_UNIT",
        "REFERENCE_MASS_COUPLED_SKEW",
        "RECOVERY_ZERO_NATIVE_STATE",
        "RECOVERY_UNIFORM_AXIAL_NATIVE_STATE",
        "RECOVERY_MANUFACTURED_UNIFORM_SHEAR_Y_NATIVE_STATE",
        "RECOVERY_TORSION_SIDED_NATIVE_STATE",
    )
    by_id = _exact_ids(records, expected, "load_mass_recovery")
    data = cases["cases"]
    geometry = {item["geometry_id"]: item for item in data["geometry"]}
    sections = {item["section_id"]: item for item in data["sections"]}
    loads = {item["case_id"]: item for item in data["loads"]}
    masses = {item["case_id"]: item for item in data["mass"]}
    recovery = {item["case_id"]: item for item in data["recovery_states"]}
    replacement = correction["replacement"]
    recovery[replacement["case_id"]] = replacement
    recovery.pop("RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE", None)

    load_limit = float(cases["tolerances"]["dead_load_work_normalized"])
    for case_id in expected[:3]:
        item = by_id[case_id]
        _fields(item, {"case_id", "classification", "coordinates", "element_vector", "resultant_force", "resultant_moment", "route", "virtual_coordinates", "virtual_work"}, name=case_id)
        case = loads[case_id]
        actual = _array(item["element_vector"], name=f"{case_id} vector")
        coordinates = _array(item["coordinates"], name=f"{case_id} coordinates")
        wanted = _expected_line_vector(case, geometry[case["geometry_id"]])
        nodal = actual.reshape(3, 6)
        force = np.sum(nodal[:, :3], axis=0)
        moment = np.sum(nodal[:, 3:], axis=0) + np.sum(np.cross(coordinates, nodal[:, :3]), axis=0)
        virtual = _array(item["virtual_coordinates"], name=f"{case_id} virtual")
        work = _hex_float(item["virtual_work"], name=f"{case_id} work")
        findings.require(_normalized(actual, wanted) <= load_limit, group=group, case_id=case_id, check="ELEMENT_LOAD")
        findings.require(_normalized(coordinates, np.asarray(geometry[case["geometry_id"]]["nodes"], dtype=float)) == 0.0 and _normalized(virtual, np.asarray(case["virtual_nodal_coordinates"], dtype=float).reshape(18)) == 0.0, group=group, case_id=case_id, check="REGISTERED_LOAD_INPUTS")
        findings.require(_normalized(force, _array(item["resultant_force"], name="reported force")) <= load_limit, group=group, case_id=case_id, check="RESULTANT_FORCE_RECOMPUTED")
        findings.require(_normalized(moment, _array(item["resultant_moment"], name="reported moment")) <= load_limit, group=group, case_id=case_id, check="RESULTANT_MOMENT_RECOMPUTED")
        findings.require(abs(work - float(actual @ virtual)) / max(1.0, abs(work)) <= load_limit, group=group, case_id=case_id, check="WORK_RECOMPUTED")
        findings.require(_normalized(actual, np.asarray(case["expected_element_vector"], dtype=float)) <= load_limit, group=group, case_id=case_id, check="FROZEN_LOAD_REFERENCE")

    for case_id in expected[3:5]:
        item = by_id[case_id]
        _fields(item, {"case_id", "classification", "exception_class", "mechanics_entry_count"}, name=case_id)
        findings.require(item.get("exception_class") == "GeBeam3MixedStateError", group=group, case_id=case_id, check="FOLLOWER_TYPED_REJECTION")
        findings.require(item.get("mechanics_entry_count") == 0, group=group, case_id=case_id, check="FOLLOWER_BEFORE_MECHANICS")

    mass_limit = float(cases["tolerances"]["mass_energy_normalized"])
    for case_id in expected[5:7]:
        item = by_id[case_id]
        _fields(item, {"case_id", "mass_matrix", "nodal_velocity", "reference_triad", "section_mass"}, name=case_id)
        case = masses[case_id]
        actual = _array(item["mass_matrix"], name=f"{case_id} mass")
        wanted = _expected_mass(case, geometry[case["geometry_id"]], sections[case["section_id"]])
        velocity = _array(item["nodal_velocity"], name=f"{case_id} velocity")
        recorded_triad = _array_shape(item["reference_triad"], (3, 3), name=f"{case_id} triad")
        recorded_section = _array_shape(item["section_mass"], (6, 6), name=f"{case_id} section mass")
        kinetic = 0.5 * float(velocity @ actual @ velocity)
        findings.require(_normalized(actual, wanted) <= mass_limit, group=group, case_id=case_id, check="CONSISTENT_MASS")
        findings.require(_normalized(recorded_triad, _triad(geometry[case["geometry_id"]])) <= 2.0e-15 and _normalized(recorded_section, np.asarray(sections[case["section_id"]]["mass_matrix_per_reference_length"], dtype=float)) == 0.0, group=group, case_id=case_id, check="REGISTERED_MASS_INPUTS")
        findings.require(_normalized(actual, actual.T) <= mass_limit, group=group, case_id=case_id, check="MASS_SYMMETRY")
        findings.require(float(np.linalg.eigvalsh(actual)[0]) > 0.0, group=group, case_id=case_id, check="MASS_POSITIVE")
        findings.require(_relative_scalar(kinetic, float(case["expected_kinetic_energy"])) <= mass_limit, group=group, case_id=case_id, check="KINETIC_ENERGY")

    recovery_limit = float(cases["tolerances"]["constitutive_recovery_normalized"])
    for case_id in expected[7:]:
        item = by_id[case_id]
        _fields(item, {"absolute_rotations", "candidate_id", "case_id", "fibre_stress_available", "local_resultant", "local_strain", "station_frames", "station_order"}, name=case_id)
        case = recovery[case_id]
        strain = _array(item["local_strain"], name=f"{case_id} strain")
        resultant = _array(item["local_resultant"], name=f"{case_id} resultant")
        rotations = _array_shape(item["absolute_rotations"], (3, 3, 3), name=f"{case_id} rotations")
        frames = _array_shape(item["station_frames"], (4, 3, 3), name=f"{case_id} frames")
        section_id = case.get("section_id", case.get("section", {}).get("section_id"))
        stiffness = np.asarray(sections[section_id]["stiffness_matrix"], dtype=float)
        findings.require(_normalized(resultant, strain @ stiffness.T) <= recovery_limit, group=group, case_id=case_id, check="CONSTITUTIVE_RECOVERY")
        findings.require(tuple(item["station_order"]) == tuple(case["station_order"]), group=group, case_id=case_id, check="SIDED_STATION_ORDER")
        findings.require(item.get("candidate_id") == CANDIDATE_ID and item.get("fibre_stress_available") is False, group=group, case_id=case_id, check="RECOVERY_PROVENANCE")
        proper = all(_normalized(frame.T @ frame, np.eye(3)) <= 1.0e-12 and np.linalg.det(frame) > 0.0 for frame in np.concatenate((rotations, frames), axis=0))
        findings.require(proper, group=group, case_id=case_id, check="RECOVERY_FRAMES_PROPER")
        if "expected_station_strain" in case:
            findings.require(_normalized(strain, np.asarray(case["expected_station_strain"], dtype=float)) <= recovery_limit, group=group, case_id=case_id, check="FROZEN_STRAIN")
            findings.require(_normalized(resultant, np.asarray(case["expected_station_resultant"], dtype=float)) <= recovery_limit, group=group, case_id=case_id, check="FROZEN_RESULTANT")
        elif "expected" in case and "station_signs" in case:
            signs = np.asarray(case["station_signs"], dtype=float)
            wanted_strain = np.zeros((4, 6))
            wanted_resultant = np.zeros((4, 6))
            for target, key, column in (
                (wanted_strain, "force_strain_gamma_y", 1),
                (wanted_strain, "moment_curvature_z_abs", 5),
                (wanted_resultant, "shear_resultant_y", 1),
                (wanted_resultant, "bending_moment_z_abs", 5),
            ):
                rational = case["expected"][key]
                values = float(rational["numerator"] / rational["denominator"])
                target[:, column] = values * (signs if column == 5 else 1.0)
            findings.require(_normalized(strain, wanted_strain) <= recovery_limit, group=group, case_id=case_id, check="CORRECTED_STRAIN")
            findings.require(_normalized(resultant, wanted_resultant) <= recovery_limit, group=group, case_id=case_id, check="CORRECTED_RESULTANT")
        else:
            wanted = float(case["expected_torsional_curvature"])
            findings.require(_normalized(strain[:, 3], np.full(4, wanted)) <= recovery_limit, group=group, case_id=case_id, check="TORSION_CURVATURE")


def _check_modal_buckling(records: Any, cases: Mapping[str, Any], findings: _Findings) -> None:
    group = "MODAL_OR_BUCKLING"
    expected = (
        "CANTILEVER_REFERENCE_LINEAR",
        "EULER_PINNED_WEAK_Z",
        "EULER_PINNED_STRONG_Y",
        "UNSUPPORTED_PRIVATE_ROUTES",
    )
    by_id = _exact_ids(records, expected, "modal_buckling")
    data = cases["cases"]
    modal = {item["case_id"]: item for item in data["modal"]}
    buckling = {item["case_id"]: item for item in data["buckling"]}
    item = by_id[expected[0]]
    _fields(item, {"case_id", "samples"}, name=expected[0])
    authority = modal[expected[0]]
    samples = item.get("samples")
    if not isinstance(samples, list) or [sample.get("macro_count") for sample in samples] != authority["macro_element_counts"]:
        raise MalformedProof("modal sample coverage")
    rigid_limit = float(cases["tolerances"]["free_body_normalized_eigenvalue"])
    for sample in samples:
        _fields(sample, {"family_frequencies_hz", "family_mass_scores", "free_body_eigenvalues", "macro_count"}, name=f"{expected[0]} sample")
        values = _array(sample["free_body_eigenvalues"], name="free-body eigenvalues")
        scale = max(float(np.max(np.abs(values))), 1.0)
        count = int(np.count_nonzero(np.abs(values) <= rigid_limit * scale))
        findings.require(count == 6, group=group, case_id=expected[0], check=f"SIX_FREE_MODES_N{sample['macro_count']}")
        scores = sample.get("family_mass_scores")
        frequencies = sample.get("family_frequencies_hz")
        if not isinstance(scores, dict) or not isinstance(frequencies, dict):
            raise MalformedProof("modal family maps")
        findings.require(set(scores) == set(authority["expected_frequencies_hz"]), group=group, case_id=expected[0], check=f"MODAL_FAMILY_COVERAGE_N{sample['macro_count']}")
        for family, value in scores.items():
            findings.require(_hex_float(value, name=f"{family} mass score") > 0.99, group=group, case_id=expected[0], check=f"MODAL_FAMILY_SCORE_{family}_N{sample['macro_count']}")
    finest = samples[-1]["family_frequencies_hz"]
    for family, reference in authority["expected_frequencies_hz"].items():
        actual = _hex_float(finest[family], name=f"{family} frequency")
        findings.require(_relative_scalar(actual, float(reference)) <= float(cases["tolerances"]["modal_reference_relative"]), group=group, case_id=expected[0], check=f"MODAL_REFERENCE_{family}")

    for case_id in expected[1:3]:
        item = by_id[case_id]
        _fields(item, {"case_id", "samples"}, name=case_id)
        authority = buckling[case_id]
        samples = item.get("samples")
        if not isinstance(samples, list) or [sample.get("macro_count") for sample in samples] != authority["macro_element_counts"]:
            raise MalformedProof(f"{case_id} sample coverage")
        for sample in samples:
            _fields(sample, {"critical_load", "macro_count"}, name=f"{case_id} sample")
            actual = _hex_float(sample["critical_load"], name=f"{case_id} critical load")
            findings.require(actual > 0.0, group=group, case_id=case_id, check=f"POSITIVE_CRITICAL_N{sample['macro_count']}")
        finest_value = _hex_float(samples[-1]["critical_load"], name=f"{case_id} finest")
        findings.require(_relative_scalar(finest_value, float(authority["expected_critical_load"])) <= float(cases["tolerances"]["buckling_reference_relative"]), group=group, case_id=case_id, check="EULER_REFERENCE")

    item = by_id[expected[3]]
    _fields(item, {"case_id", "routes"}, name=expected[3])
    route_records = item.get("routes")
    if not isinstance(route_records, list) or [record.get("route") for record in route_records] != cases["unsupported_routes"]:
        raise MalformedProof("unsupported route coverage")
    for record in route_records:
        findings.require(record.get("exception_class") == "GeBeam3MixedStateError", group=group, case_id=expected[3], check=f"FAIL_CLOSED_{record['route']}")


def verify_payload(proof_raw: bytes) -> dict[str, Any]:
    proof_sha = _sha(proof_raw)
    proof = _decode(proof_raw)
    if not isinstance(proof, dict) or set(proof) != TOP_FIELDS:
        raise MalformedProof("proof top-level schema")
    if canonical_bytes(proof) != proof_raw:
        raise MalformedProof("proof is not canonical")
    if proof["schema"] != PROOF_SCHEMA or proof["study_id"] != STUDY_ID or proof["candidate_id"] != CANDIDATE_ID or proof["terminal"] != PROOF_TERMINAL:
        raise MalformedProof("proof identity")
    body = dict(proof)
    digest = body.pop("content_sha256")
    if digest != _sha(canonical_bytes(body)):
        raise MalformedProof("proof content hash")
    expected_bindings = {}
    authorities: dict[str, dict[str, Any]] = {}
    for name in BOUND_INPUTS:
        raw, value = _load_authority(name) if name.endswith(".json") else ((REFERENCE / name).read_bytes(), {})
        expected_bindings[name] = {"bytes": len(raw), "sha256": _sha(raw)}
        if value:
            authorities[name] = value
    if proof["bindings"] != expected_bindings:
        raise MalformedProof("proof authority bindings")
    if proof["predicates"] != {
        "producer_scientific_adjudication_present": False,
        "raw_binary64_values_encoded_little_endian": True,
    }:
        raise MalformedProof("producer boundary predicates")
    if proof["counts"] != {
        "load_mass_recovery": 11,
        "modal_buckling": 4,
        "solver_chart_state": 6,
        "total": 21,
    }:
        raise MalformedProof("proof counts")
    cases = authorities["ge_beam3_mixed_p2_cases.json"]
    correction = authorities["ge_beam3_mixed_p2_recovery_correction.json"]
    state_schema = authorities["ge_beam3_mixed_p2_state_schema.json"]
    effective = sorted(
        [
            item["case_id"]
            for item in cases["cases"]["recovery_states"]
            if item["case_id"] != "RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE"
        ]
        + [correction["replacement"]["case_id"]]
    )
    if proof["effective_recovery_case_ids"] != effective:
        raise MalformedProof("effective correction overlay")
    records = proof["records"]
    if not isinstance(records, dict) or set(records) != set(RECORD_GROUPS):
        raise MalformedProof("proof record groups")
    findings = _Findings()
    _check_solver(records["solver_chart_state"], cases, state_schema, findings)
    _check_load_mass_recovery(records["load_mass_recovery"], cases, correction, findings)
    _check_modal_buckling(records["modal_buckling"], cases, findings)
    finding_groups = [group for group in GROUP_ORDER if any(item["group"] == group for item in findings.items)]
    group_pass = {group: group not in finding_groups for group in GROUP_ORDER}
    terminal = FINDING if finding_groups else PASS
    return {
        "bindings": expected_bindings,
        "candidate_id": CANDIDATE_ID,
        "counts": {
            "finding_count": len(findings.items),
            "proof_record_count": int(proof["counts"]["total"]),
        },
        "finding_groups": finding_groups,
        "findings": findings.items,
        "group_pass": group_pass,
        "predicates": {
            "evidence_valid": True,
            "independent_recomputation_complete": True,
        },
        "proof_sha256": proof_sha,
        "schema": CHECK_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": terminal,
    }


def malformed_record(proof_raw: bytes, exc: BaseException) -> dict[str, Any]:
    return {
        "bindings": {},
        "candidate_id": CANDIDATE_ID,
        "counts": {"finding_count": 0, "proof_record_count": 0},
        "error_class": type(exc).__name__,
        "finding_groups": [],
        "findings": [],
        "group_pass": {group: False for group in GROUP_ORDER},
        "predicates": {
            "evidence_valid": False,
            "independent_recomputation_complete": False,
        },
        "proof_sha256": _sha(proof_raw),
        "schema": CHECK_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": MALFORMED,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"check output already exists: {args.output}")
    raw = args.proof.read_bytes()
    try:
        record = verify_payload(raw)
    except (MalformedProof, KeyError, TypeError, ValueError, IndexError) as exc:
        record = malformed_record(raw, exc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(record))
    return 0 if record["terminal"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
