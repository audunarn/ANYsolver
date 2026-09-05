"""Independent analytical references for the private GE-Beam3 P2 gate.

This standard-library program intentionally imports neither ANYsolver nor any
production/legacy beam mechanics.  It validates the frozen case manifest and
reconstructs line-load, reference-mass, modal, recovery, and Euler references.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, getcontext
import hashlib
import json
import math
from pathlib import Path
from typing import Any


getcontext().prec = 80
D = Decimal
PI = D("3.141592653589793238462643383279502884197169399375105820974944592307816406286")
BETA1 = D("1.87510406871196116644530824107821416257011173353106998824541371310567995284")
HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "ge_beam3_mixed_p2_cases.json"


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key {key!r}")
        made[key] = value
    return made


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON value {value!r}")


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _load_cases(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise ValueError("case manifest root must be an object")
    if raw != _canonical_bytes(value):
        raise ValueError("case manifest is not sorted compact canonical JSON with one LF")
    return raw, value


def _dec(value: Any) -> D:
    if not isinstance(value, str):
        raise TypeError(f"authority decimal must be a string, got {type(value).__name__}")
    made = D(value)
    if not made.is_finite():
        raise ValueError("authority decimal must be finite")
    return made


def _fmt(value: D) -> str:
    return "0" if value == 0 else format(value, ".24E")


def _vec(values: Any, size: int = 3) -> list[D]:
    if not isinstance(values, list) or len(values) != size:
        raise ValueError(f"expected a {size}-component vector")
    return [_dec(value) for value in values]


def _matrix(values: Any, size: int = 6) -> list[list[D]]:
    if not isinstance(values, list) or len(values) != size:
        raise ValueError(f"expected a {size}x{size} matrix")
    return [_vec(row, size) for row in values]


def _add(left: list[D], right: list[D]) -> list[D]:
    return [a + b for a, b in zip(left, right)]


def _sub(left: list[D], right: list[D]) -> list[D]:
    return [a - b for a, b in zip(left, right)]


def _scale(vector: list[D], scalar: D) -> list[D]:
    return [scalar * value for value in vector]


def _dot(left: list[D], right: list[D]) -> D:
    return sum((a * b for a, b in zip(left, right)), D(0))


def _cross(left: list[D], right: list[D]) -> list[D]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _unit(vector: list[D]) -> list[D]:
    norm = _dot(vector, vector).sqrt()
    if norm == 0:
        raise ValueError("zero direction")
    return _scale(vector, D(1) / norm)


def _matvec(matrix: list[list[D]], vector: list[D]) -> list[D]:
    return [_dot(row, vector) for row in matrix]


def _transpose(matrix: list[list[D]]) -> list[list[D]]:
    return [list(row) for row in zip(*matrix)]


def _matmul(left: list[list[D]], right: list[list[D]]) -> list[list[D]]:
    columns = _transpose(right)
    return [[_dot(row, column) for column in columns] for row in left]


def _triad(geometry: dict[str, Any]) -> tuple[list[list[D]], D, list[list[D]]]:
    nodes = [_vec(row) for row in geometry["nodes"]]
    if _scale(_add(nodes[0], nodes[2]), D("0.5")) != nodes[1]:
        raise ValueError(f"{geometry['geometry_id']} middle node is not the exact midpoint")
    chord = _sub(nodes[2], nodes[0])
    length = _dot(chord, chord).sqrt()
    e1 = _scale(chord, D(1) / length)
    orientation = _vec(geometry["reference_orientation"])
    e2 = _unit(_sub(orientation, _scale(e1, _dot(orientation, e1))))
    e3 = _cross(e1, e2)
    triad = [[e1[row], e2[row], e3[row]] for row in range(3)]
    axis = _unit(_vec(geometry["reference_axis_direction"]))
    if abs(abs(_dot(axis, e1)) - D(1)) > D("1E-30"):
        raise ValueError(f"{geometry['geometry_id']} axis authority is not parallel to the chord")
    return triad, length, nodes


def _cholesky_positive(matrix: list[list[D]], label: str) -> None:
    size = len(matrix)
    for i in range(size):
        for j in range(size):
            if matrix[i][j] != matrix[j][i]:
                raise ValueError(f"{label} is not exactly symmetric")
    lower = [[D(0) for _ in range(size)] for _ in range(size)]
    for i in range(size):
        for j in range(i + 1):
            residual = matrix[i][j] - sum((lower[i][k] * lower[j][k] for k in range(j)), D(0))
            if i == j:
                if residual <= 0:
                    raise ValueError(f"{label} is not positive definite")
                lower[i][j] = residual.sqrt()
            else:
                lower[i][j] = residual / lower[j][j]


def _block_rotation(triad: list[list[D]]) -> list[list[D]]:
    made = [[D(0) for _ in range(6)] for _ in range(6)]
    for block in (0, 3):
        for row in range(3):
            for column in range(3):
                made[block + row][block + column] = triad[row][column]
    return made


def _assemble_mass(section_mass: list[list[D]], triad: list[list[D]], length: D) -> list[list[D]]:
    rotate = _block_rotation(triad)
    spatial = _matmul(_matmul(rotate, section_mass), _transpose(rotate))
    made = [[D(0) for _ in range(18)] for _ in range(18)]
    cell_length = length / D(2)
    coupling = ((D(1) / D(3), D(1) / D(6)), (D(1) / D(6), D(1) / D(3)))
    for nodes in ((0, 1), (1, 2)):
        for local_i, node_i in enumerate(nodes):
            for local_j, node_j in enumerate(nodes):
                factor = cell_length * coupling[local_i][local_j]
                for row in range(6):
                    for column in range(6):
                        made[6 * node_i + row][6 * node_j + column] += factor * spatial[row][column]
    return made


def _line_load(case: dict[str, Any], geometry: dict[str, Any]) -> tuple[list[D], list[D], list[D]]:
    triad, length, nodes = _triad(geometry)
    forces = [_vec(row) for row in case["force_per_reference_length_at_nodes"]]
    couples = [_vec(row) for row in case["couple_per_reference_length_at_nodes"]]
    if case["classification"] == "MATERIAL_DEAD":
        forces = [_matvec(triad, value) for value in forces]
        couples = [_matvec(triad, value) for value in couples]
    elif case["classification"] != "SPATIAL_DEAD":
        raise ValueError("line-load reference accepts only dead classifications")
    made_forces = [[D(0), D(0), D(0)] for _ in range(3)]
    made_couples = [[D(0), D(0), D(0)] for _ in range(3)]
    cell_length = length / D(2)
    for left, right in ((0, 1), (1, 2)):
        for axis in range(3):
            made_forces[left][axis] += cell_length * (D(2) * forces[left][axis] + forces[right][axis]) / D(6)
            made_forces[right][axis] += cell_length * (forces[left][axis] + D(2) * forces[right][axis]) / D(6)
            made_couples[left][axis] += cell_length * (D(2) * couples[left][axis] + couples[right][axis]) / D(6)
            made_couples[right][axis] += cell_length * (couples[left][axis] + D(2) * couples[right][axis]) / D(6)
    vector = [value for node in range(3) for value in (*made_forces[node], *made_couples[node])]
    force = [sum((made_forces[node][axis] for node in range(3)), D(0)) for axis in range(3)]
    moment = [sum((made_couples[node][axis] for node in range(3)), D(0)) for axis in range(3)]
    for node, position in enumerate(nodes):
        moment = _add(moment, _cross(position, made_forces[node]))
    return vector, force, moment


def _point_load(case: dict[str, Any], geometry: dict[str, Any]) -> tuple[list[D], list[D], list[D]]:
    _triad_value, _length, nodes = _triad(geometry)
    node = int(case["node_local_index"])
    force, couple = _vec(case["force"]), _vec(case["moment"])
    vector = [D(0) for _ in range(18)]
    vector[6 * node : 6 * node + 6] = [*force, *couple]
    return vector, force, _add(couple, _cross(nodes[node], force))


def _work(vector: list[D], virtual: Any) -> D:
    displacement = [value for row in virtual for value in _vec(row, 6)]
    return _dot(vector, displacement)


def _hash_decimals(value: Any) -> str:
    def formatted(item: Any) -> Any:
        if isinstance(item, D):
            return _fmt(item)
        if isinstance(item, list):
            return [formatted(child) for child in item]
        return item
    return hashlib.sha256(_canonical_bytes(formatted(value))).hexdigest().upper()


def _float_vector(values: Any) -> list[float]:
    return [float(value) for value in _vec(values)]


def _so3_exp_float(vector: Any) -> list[list[float]]:
    x, y, z = _float_vector(vector)
    angle2 = x * x + y * y + z * z
    cross = [[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]]
    if angle2 < 1.0e-16:
        a = 1.0 - angle2 / 6.0 + angle2 * angle2 / 120.0
        b = 0.5 - angle2 / 24.0 + angle2 * angle2 / 720.0
    else:
        angle = math.sqrt(angle2)
        a = math.sin(angle) / angle
        b = (1.0 - math.cos(angle)) / angle2
    cross2 = [
        [sum(cross[row][k] * cross[k][column] for k in range(3)) for column in range(3)]
        for row in range(3)
    ]
    return [
        [
            (1.0 if row == column else 0.0) + a * cross[row][column] + b * cross2[row][column]
            for column in range(3)
        ]
        for row in range(3)
    ]


def _matmul_float(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [sum(left[row][k] * right[k][column] for k in range(3)) for column in range(3)]
        for row in range(3)
    ]


def _frob_difference(left: list[list[float]], right: list[list[float]]) -> float:
    return math.sqrt(sum((left[i][j] - right[i][j]) ** 2 for i in range(3) for j in range(3)))


def _validate_solver_state_cases(cases: dict[str, Any], geometry: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    rows = cases["solver_state"]
    by_id = {row["case_id"]: row for row in rows}
    required = {
        "NONZERO_SOLVER_CHART",
        "TWO_NONCOMMUTING_COMMITS",
        "REJECTED_TRIAL_ROLLBACK_AND_CUTBACK",
        "SPLIT_RESTART_IDENTITY",
        "SHARED_NODE_DISTINCT_MATERIAL_TRIADS",
        "CONNECTIVITY_REVERSAL_STATE",
    }
    if set(by_id) != required or len(rows) != len(required):
        raise ValueError("solver/state case IDs are incomplete or duplicated")
    chart = by_id["NONZERO_SOLVER_CHART"]
    committed = [[_dec(value) for value in row] for row in chart["committed_rotation_coordinates"]]
    trial = [[_dec(value) for value in row] for row in chart["trial_rotation_coordinates"]]
    differences = [[trial[i][j] - committed[i][j] for j in range(3)] for i in range(3)]
    if all(value == 0 for row in differences for value in row):
        raise ValueError("solver-chart fixture must have a nonzero rotation increment")
    if chart["expected"]["chart"] != (
        "EXP_TRIAL_MINUS_COMMITTED_PLUS_PERTURBATION_TIMES_COMMITTED_OPERATOR_TIMES_REFERENCE_TRIAD"
    ):
        raise ValueError("solver-chart fixture uses an unexpected chart")
    noncommuting = by_id["TWO_NONCOMMUTING_COMMITS"]
    first, second = noncommuting["increments"]
    q1 = _so3_exp_float(first[0])
    q2 = _so3_exp_float(second[0])
    spread = _frob_difference(_matmul_float(q2, q1), _matmul_float(q1, q2))
    threshold = float(_dec(noncommuting["expected"]["opposite_order_must_differ_by_frobenius_more_than"]))
    if not spread > threshold:
        raise ValueError("noncommuting update fixture does not distinguish multiplication order")
    rollback = by_id["REJECTED_TRIAL_ROLLBACK_AND_CUTBACK"]
    if max(abs(float(value)) for row in rollback["rejected_rotation_coordinates"] for value in row) < 2.9:
        raise ValueError("rollback fixture does not reach the frozen cutback domain")
    split = by_id["SPLIT_RESTART_IDENTITY"]
    if split["restart_after_increment"] != 1 or len(split["increments"]) != 2:
        raise ValueError("split restart fixture is malformed")
    shared = by_id["SHARED_NODE_DISTINCT_MATERIAL_TRIADS"]
    if shared["elements"][0]["node_ids"][-1] != shared["elements"][1]["node_ids"][0]:
        raise ValueError("shared-node fixture does not actually share its declared node")
    frame_a = _triad(geometry[shared["elements"][0]["geometry_id"]])[0]
    frame_b = _triad(geometry[shared["elements"][1]["geometry_id"]])[0]
    if frame_a == frame_b:
        raise ValueError("shared-node fixture must retain distinct material triads")
    reversal = by_id["CONNECTIVITY_REVERSAL_STATE"]
    forward = geometry[reversal["forward_geometry_id"]]
    backward = geometry[reversal["reversed_geometry_id"]]
    if forward["connectivity"] != list(reversed(backward["connectivity"])):
        raise ValueError("reversal-state fixture connectivity is not 1<->3")
    for case_id in sorted(required):
        records.append({"case_id": case_id, "input_sha256": hashlib.sha256(_canonical_bytes(by_id[case_id])).hexdigest().upper()})
    records.append({"case_id": "TWO_NONCOMMUTING_COMMITS_ORDER_SPREAD", "value": format(spread, ".17E")})
    return records


def _validate_recovery_state_cases(cases: dict[str, Any], sections: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    required = {
        "RECOVERY_ZERO_NATIVE_STATE",
        "RECOVERY_UNIFORM_AXIAL_NATIVE_STATE",
        "RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE",
        "RECOVERY_TORSION_SIDED_NATIVE_STATE",
    }
    rows = cases["recovery_states"]
    by_id = {row["case_id"]: row for row in rows}
    if set(by_id) != required or len(rows) != len(required):
        raise ValueError("recovery-state case IDs are incomplete or duplicated")
    stiffness = _matrix(sections["STEEL_DIAGONAL"]["stiffness_matrix"])
    for case_id in ("RECOVERY_ZERO_NATIVE_STATE", "RECOVERY_UNIFORM_AXIAL_NATIVE_STATE", "RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE"):
        case = by_id[case_id]
        translations = [[_dec(value) for value in row] for row in case["nodal_translations"]]
        gamma = [
            D(2) * (translations[1][axis] - translations[0][axis]) for axis in range(3)
        ]
        gamma[0] += D(1)
        gamma[0] -= D(1)
        expected = [_dec(value) for value in case["expected_station_strain"][0]][:3]
        if gamma != expected:
            raise ValueError(f"{case_id} nodal state does not reconstruct its strain")
        resultant = _matvec(stiffness, [*gamma, D(0), D(0), D(0)])
        if [_fmt(value) for value in resultant] != [_fmt(_dec(value)) for value in case["expected_station_resultant"][0]]:
            raise ValueError(f"{case_id} nodal state does not reconstruct its resultant")
        records.append({"case_id": case_id, "station_state_sha256": hashlib.sha256(_canonical_bytes(case)).hexdigest().upper()})
    torsion = by_id["RECOVERY_TORSION_SIDED_NATIVE_STATE"]
    matrices = [[[float(value) for value in row] for row in matrix] for matrix in torsion["absolute_rotation_matrices"]]
    angles = [math.atan2(matrix[2][1], matrix[1][1]) for matrix in matrices]
    curvature = angles[2] - angles[0]
    if abs(curvature - float(_dec(torsion["expected_torsional_curvature"]))) > 1.0e-15:
        raise ValueError("torsion recovery fixture does not reconstruct its curvature")
    records.append({"case_id": torsion["case_id"], "station_state_sha256": hashlib.sha256(_canonical_bytes(torsion)).hexdigest().upper()})
    return records


def _validate_assembly_policy(manifest: dict[str, Any]) -> dict[str, Any]:
    policy = manifest["assembly_policy"]
    required = {
        "buckling_generalized_eigenproblem",
        "buckling_normalization",
        "eigenvalue_filter",
        "macro_chain",
        "modal_generalized_eigenproblem",
        "modal_matching",
        "modal_normalization",
        "reference_coordinates",
        "relative_error_denominator",
        "rigid_mode_count",
    }
    if set(policy) != required:
        raise ValueError("assembled spectral policy keys are incomplete")
    return {"policy_sha256": hashlib.sha256(_canonical_bytes(policy)).hexdigest().upper()}


def build_reference(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema") != "anysolver.ge-beam3-mixed-p2-cases-v1":
        raise ValueError("unexpected case schema")
    cases = manifest["cases"]
    geometry = {item["geometry_id"]: item for item in cases["geometry"]}
    sections = {item["section_id"]: item for item in cases["sections"]}
    if len(geometry) != len(cases["geometry"]) or len(sections) != len(cases["sections"]):
        raise ValueError("duplicate geometry or section ID")
    for item in geometry.values():
        _triad(item)
    for section_id, item in sections.items():
        _cholesky_positive(_matrix(item["stiffness_matrix"]), f"{section_id} stiffness")
        _cholesky_positive(_matrix(item["mass_matrix_per_reference_length"]), f"{section_id} mass")

    solver_state_records = _validate_solver_state_cases(cases, geometry)
    recovery_state_records = _validate_recovery_state_cases(cases, sections)
    assembly_policy_record = _validate_assembly_policy(manifest)

    load_records: list[dict[str, Any]] = []
    for case in cases["loads"]:
        classification = case["classification"]
        if classification in {"CONSERVATIVE_FOLLOWER", "NONCONSERVATIVE_FOLLOWER"}:
            load_records.append({"case_id": case["case_id"], "disposition": case["expected_typed_disposition"]})
            continue
        source_geometry = geometry[case["geometry_id"]]
        if "node_local_index" in case:
            vector, force, moment = _point_load(case, source_geometry)
        else:
            vector, force, moment = _line_load(case, source_geometry)
        expected_vector = [_dec(value) for value in case["expected_element_vector"]]
        expected_force = _vec(case["expected_resultant_force"])
        expected_moment = _vec(case["expected_resultant_moment_about_global_origin"])
        expected_work = _dec(case["expected_virtual_work"])
        if [_fmt(value) for value in vector] != [_fmt(value) for value in expected_vector]:
            raise ValueError(f"{case['case_id']} element vector mismatch")
        if [_fmt(value) for value in force] != [_fmt(value) for value in expected_force]:
            raise ValueError(f"{case['case_id']} force resultant mismatch")
        if [_fmt(value) for value in moment] != [_fmt(value) for value in expected_moment]:
            raise ValueError(f"{case['case_id']} moment resultant mismatch")
        work = _work(vector, case["virtual_nodal_coordinates"])
        if _fmt(work) != _fmt(expected_work):
            raise ValueError(f"{case['case_id']} virtual-work mismatch")
        load_records.append({
            "case_id": case["case_id"],
            "element_vector_sha256": _hash_decimals(vector),
            "resultant_force": [_fmt(value) for value in force],
            "resultant_moment_about_global_origin": [_fmt(value) for value in moment],
            "virtual_work": _fmt(work),
        })

    mass_records: list[dict[str, Any]] = []
    for case in cases["mass"]:
        source_geometry = geometry[case["geometry_id"]]
        triad, length, _nodes = _triad(source_geometry)
        section_mass = _matrix(sections[case["section_id"]]["mass_matrix_per_reference_length"])
        mass = _assemble_mass(section_mass, triad, length)
        local_velocity = _vec(case["uniform_local_generalized_velocity"], 6)
        spatial_velocity = _matvec(_block_rotation(triad), local_velocity)
        nodal_velocity = spatial_velocity * 3
        kinetic = D("0.5") * _dot(nodal_velocity, _matvec(mass, nodal_velocity))
        translational_mass = length * section_mass[0][0]
        if _fmt(kinetic) != _fmt(_dec(case["expected_kinetic_energy"])):
            raise ValueError(f"{case['case_id']} kinetic-energy mismatch")
        if _fmt(translational_mass) != _fmt(_dec(case["expected_total_translational_mass"])):
            raise ValueError(f"{case['case_id']} translational-mass mismatch")
        mass_records.append({
            "case_id": case["case_id"],
            "kinetic_energy": _fmt(kinetic),
            "matrix_sha256": _hash_decimals(mass),
            "total_translational_mass": _fmt(translational_mass),
        })

    steel = sections["STEEL_DIAGONAL"]
    parameters = {key: _dec(value) for key, value in steel["physical_parameters"].items()}
    stiffness = _matrix(steel["stiffness_matrix"])
    inertia = _matrix(steel["mass_matrix_per_reference_length"])
    length = _triad(geometry["COLUMN_X_L3"])[1]
    expected_modal = {
        "AXIAL": D(1) / (D(4) * length) * (stiffness[0][0] / inertia[0][0]).sqrt(),
        "BENDING_STRONG_Y": BETA1**2 / (D(2) * PI * length**2) * (stiffness[4][4] / inertia[0][0]).sqrt(),
        "BENDING_WEAK_Z": BETA1**2 / (D(2) * PI * length**2) * (stiffness[5][5] / inertia[0][0]).sqrt(),
        "TORSION": D(1) / (D(4) * length) * (stiffness[3][3] / inertia[3][3]).sqrt(),
    }
    modal_case = next(item for item in cases["modal"] if item["case_id"] == "CANTILEVER_REFERENCE_LINEAR")
    for key, value in expected_modal.items():
        if _fmt(value) != _fmt(_dec(modal_case["expected_frequencies_hz"][key])):
            raise ValueError(f"modal reference mismatch for {key}")

    expected_buckling = {
        "EULER_PINNED_WEAK_Z": PI**2 * stiffness[5][5] / length**2,
        "EULER_PINNED_STRONG_Y": PI**2 * stiffness[4][4] / length**2,
    }
    for case in cases["buckling"]:
        expected = expected_buckling[case["case_id"]]
        if _fmt(expected) != _fmt(_dec(case["expected_critical_load"])):
            raise ValueError(f"buckling reference mismatch for {case['case_id']}")

    recovery_records: list[dict[str, Any]] = []
    for case in cases["recovery"]:
        strain = _vec(case["expected_constant_strain"], 6)
        resultant = _matvec(stiffness, strain)
        expected = _vec(case["expected_constant_resultant"], 6)
        if [_fmt(value) for value in resultant] != [_fmt(value) for value in expected]:
            raise ValueError(f"recovery constitutive mismatch for {case['case_id']}")
        recovery_records.append({
            "case_id": case["case_id"],
            "resultant": [_fmt(value) for value in resultant],
            "station_order": ["XI_MINUS_1", "XI_ZERO_LEFT", "XI_ZERO_RIGHT", "XI_PLUS_1"],
            "strain": [_fmt(value) for value in strain],
        })

    result: dict[str, Any] = {
        "assembly_policy": assembly_policy_record,
        "buckling": {key: _fmt(value) for key, value in sorted(expected_buckling.items())},
        "cases_schema": manifest["schema"],
        "loads": load_records,
        "mass": mass_records,
        "modal_frequencies_hz": {key: _fmt(value) for key, value in sorted(expected_modal.items())},
        "recovery": recovery_records,
        "recovery_states": recovery_state_records,
        "schema": "anysolver.ge-beam3-mixed-p2-independent-reference-v1",
        "source_policy": "STANDARD_LIBRARY_DECIMAL_NO_PRODUCTION_OR_LEGACY_BEAM_IMPORTS",
        "solver_state": solver_state_records,
        "study_id": manifest["study_id"],
    }
    result["content_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest().upper()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    raw, manifest = _load_cases(arguments.cases)
    result = build_reference(manifest)
    result["cases_bytes"] = len(raw)
    result["cases_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    result["content_sha256"] = hashlib.sha256(
        _canonical_bytes({key: value for key, value in result.items() if key != "content_sha256"})
    ).hexdigest().upper()
    output = _canonical_bytes(result)
    if arguments.output is not None:
        with arguments.output.open("xb") as stream:
            stream.write(output)
    elif arguments.check_only:
        print(json.dumps({"content_sha256": result["content_sha256"], "status": "PASS"}, separators=(",", ":"), sort_keys=True))
    else:
        print(output.decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
