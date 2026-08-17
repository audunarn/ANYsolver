"""Exact, standard-library identity oracle for Candidate E2-A.

The source gate precedes mechanics.  This oracle therefore certifies the
non-uniqueness of the displacement lift and reproduces the immutable E1-A
hostile rank theorem; it intentionally does not calculate an E2-A rank.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/s4_e2_a_cases.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/s4_e2_a_contract.json"
CANDIDATE_ID = "candidate_e2_a.wg2020_n7_k0_displacement_allman_q4_kinematic_v1"
TERMINAL = "BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY"
REASON = "RANK_SUFFICIENT_DISPLACEMENT_ENRICHMENT_NONUNIQUE"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"

# The coordinator supplies one final content-address rebind after all common
# inputs freeze.  Negative byte counts are deliberately fail-closed and keep
# --emit-contract/--run unavailable before that authority barrier closes.
STATIC_INPUTS = {
    "plan": (
        "docs/agent_plans/S4_E2_A_SOURCE_KINEMATICS_PLAN.md",
        5679,
        "D8F39F3C75D19AF3C26A69845216AF9A7C948EE1F6CCB3E3BBFCF0A21C8131F4",
    ),
    "baseline": (
        "docs/reference_cases/s4_e2_a_baseline.json",
        1891,
        "EF62A7F2F40089A47237A17C03A1FC3C7D3BA5A9AA696D4C326CA4DB2A994A92",
    ),
    "environment": (
        "docs/reference_cases/s4_e2_a_environment.json",
        912,
        "2A0E7D3B568F5ACC912A7897E3B4787F7AC9BBA57739BFD346A1D5DB68B82C99",
    ),
    "test_inventory": (
        "docs/reference_cases/s4_e2_a_test_inventory.json",
        1582,
        "8DD67A8940FB65601CFA43455558724E507014F327C047AF1E56A21D21A2CBA9",
    ),
    "source_registry": (
        "docs/reference_cases/s4_e2_a_source_registry.json",
        5509,
        "15AFFE358D5551EB08359267B6B0FD3FAAF6F15198C22475B37DF8AD4C014D2E",
    ),
    "identity": (
        "docs/reference_cases/s4_e2_a_identity.json",
        4111,
        "1D68C16149F0368E883CCD1611107068DF662C794A6D58541665A5F99472421D",
    ),
    "derivation": (
        "docs/S4_E2_A_FORMULATION_DERIVATION.md",
        10061,
        "E7CE3A36E895238E1E31734E81CEB99A1A804E8D6B08101DBC2EA5452DE3B16F",
    ),
    "extension": (
        "docs/S4_E2_A_EXTENSION_CLOSURE.md",
        2351,
        "F6CC6AD38AEA8FCC6C402301F58CA47AFF03B738CFC2E44E1F23A6F8CD19BACA",
    ),
    "cases": (
        "docs/reference_cases/s4_e2_a_cases.json",
        2352,
        "61ED18EDB32B0DAF288E3EB66FEA522D5D4588542F11D8881B5B7762FCAC3729",
    ),
}

ALLOWED_NEW_PATHS = [
    "docs/agent_plans/S4_E2_A_SOURCE_KINEMATICS_PLAN.md",
    "docs/S4_E2_A_FORMULATION_DERIVATION.md",
    "docs/S4_E2_A_EXTENSION_CLOSURE.md",
    "docs/S4_E2_A_QUALIFICATION_REPORT.md",
    "docs/S4_E2_A_INDEPENDENT_REVIEW.md",
    "docs/reference_cases/s4_e2_a_baseline.json",
    "docs/reference_cases/s4_e2_a_environment.json",
    "docs/reference_cases/s4_e2_a_test_inventory.json",
    "docs/reference_cases/s4_e2_a_source_registry.json",
    "docs/reference_cases/s4_e2_a_identity.json",
    "docs/reference_cases/s4_e2_a_cases.json",
    "docs/reference_cases/s4_e2_a_oracle.py",
    "docs/reference_cases/s4_e2_a_contract.json",
    "docs/reference_cases/s4_e2_a_output.json",
    "docs/reference_cases/s4_e2_a_status.json",
    "tests/test_s4_e2_a_exact_kinematics.py",
    "tests/test_s4_e2_a_qualification.py",
    "tests/test_s4_e2_a_closeout.py",
]


class BaselineMismatch(Exception):
    pass


class ContractViolation(Exception):
    pass


Poly = dict[tuple[int, int], Fraction]
VectorPoly = tuple[Poly, Poly]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise BaselineMismatch(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode(raw: bytes) -> object:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise BaselineMismatch("invalid UTF-8/LF transport")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(BaselineMismatch(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BaselineMismatch(str(exc)) from exc


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _verified_raw(path: str, size: int, sha256: str) -> bytes:
    if size < 0 or sha256 == "PENDING":
        raise BaselineMismatch(f"unfrozen input identity: {path}")
    try:
        raw = (ROOT / path).read_bytes()
    except OSError as exc:
        raise BaselineMismatch(f"missing input: {path}") from exc
    if len(raw) != size or _sha(raw) != sha256:
        raise BaselineMismatch(f"identity mismatch: {path}")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise BaselineMismatch(f"transport mismatch: {path}")
    return raw


def _verified_json(path: str, size: int, sha256: str) -> dict[str, object]:
    raw = _verified_raw(path, size, sha256)
    value = _decode(raw)
    if not isinstance(value, dict) or raw != _canonical(value):
        raise BaselineMismatch(f"noncanonical JSON: {path}")
    return value


def _fraction(value: object) -> Fraction:
    if not isinstance(value, (str, int)):
        raise AssertionError(f"not an exact scalar: {value!r}")
    return Fraction(value)


def _poly(terms: object) -> Poly:
    if not isinstance(terms, list):
        raise AssertionError("polynomial terms must be a list")
    result: Poly = {}
    for term in terms:
        if not isinstance(term, list) or len(term) != 3:
            raise AssertionError("malformed polynomial term")
        coefficient, r_power, s_power = term
        key = (int(r_power), int(s_power))
        result[key] = result.get(key, Fraction(0)) + _fraction(coefficient)
    return {key: value for key, value in result.items() if value}


def _add(left: Poly, right: Poly, scale: Fraction = Fraction(1)) -> Poly:
    result = dict(left)
    for key, value in right.items():
        result[key] = result.get(key, Fraction(0)) + scale * value
        if not result[key]:
            del result[key]
    return result


def _scale(poly: Poly, factor: Fraction) -> Poly:
    return {key: factor * value for key, value in poly.items() if factor * value}


def _multiply(left: Poly, right: Poly) -> Poly:
    result: Poly = {}
    for (lr, ls), lv in left.items():
        for (rr, rs), rv in right.items():
            key = (lr + rr, ls + rs)
            result[key] = result.get(key, Fraction(0)) + lv * rv
    return {key: value for key, value in result.items() if value}


def _derivative(poly: Poly, axis: int) -> Poly:
    result: Poly = {}
    for (r_power, s_power), value in poly.items():
        powers = [r_power, s_power]
        if powers[axis]:
            coefficient = value * powers[axis]
            powers[axis] -= 1
            result[(powers[0], powers[1])] = coefficient
    return result


def _evaluate(poly: Poly, r: Fraction, s: Fraction) -> Fraction:
    return sum(value * r**rp * s**sp for (rp, sp), value in poly.items())


def _restrict(poly: Poly, axis: int, value: Fraction) -> dict[int, Fraction]:
    result: dict[int, Fraction] = {}
    for (r_power, s_power), coefficient in poly.items():
        if axis == 0:
            key, contribution = s_power, coefficient * value**r_power
        else:
            key, contribution = r_power, coefficient * value**s_power
        result[key] = result.get(key, Fraction(0)) + contribution
    return {key: coefficient for key, coefficient in result.items() if coefficient}


def _substitute_signed_permutation(poly: Poly, matrix: list[list[int]]) -> Poly:
    locations: list[tuple[int, int]] = []
    for row in matrix:
        nonzero = [(column, value) for column, value in enumerate(row) if value]
        if len(nonzero) != 1 or abs(nonzero[0][1]) != 1:
            raise AssertionError("D4 matrix is not a signed permutation")
        locations.append(nonzero[0])
    result: Poly = {}
    for (r_power, s_power), coefficient in poly.items():
        powers = [0, 0]
        sign = 1
        for source_power, (target_axis, target_sign) in zip((r_power, s_power), locations):
            powers[target_axis] += source_power
            sign *= target_sign**source_power
        key = (powers[0], powers[1])
        result[key] = result.get(key, Fraction(0)) + coefficient * sign
    return {key: value for key, value in result.items() if value}


def _strain(displacement: VectorPoly) -> tuple[Poly, Poly, Poly]:
    u, v = displacement
    return _derivative(u, 0), _derivative(v, 1), _add(_derivative(u, 1), _derivative(v, 0))


def _integrate_square(poly: Poly) -> Fraction:
    total = Fraction(0)
    for (r_power, s_power), coefficient in poly.items():
        if r_power % 2 == 0 and s_power % 2 == 0:
            total += coefficient * Fraction(2, r_power + 1) * Fraction(2, s_power + 1)
    return total


def _strain_energy(displacement: VectorPoly) -> Fraction:
    return sum(_integrate_square(_multiply(row, row)) for row in _strain(displacement))


def _rank(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    row_count, column_count = len(work), len(work[0])
    rank = 0
    for column in range(column_count):
        pivot = next((row for row in range(rank, row_count) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        scale = work[rank][column]
        work[rank] = [value / scale for value in work[rank]]
        for row in range(row_count):
            if row != rank and work[row][column]:
                factor = work[row][column]
                work[row] = [left - factor * right for left, right in zip(work[row], work[rank])]
        rank += 1
    return rank


def _det2(matrix: list[list[int]]) -> int:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _matrix2(value: object) -> list[list[Fraction]]:
    if not isinstance(value, list) or len(value) != 2 or any(not isinstance(row, list) or len(row) != 2 for row in value):
        raise AssertionError("expected exact 2 by 2 matrix")
    return [[_fraction(entry) for entry in row] for row in value]


def _matrix_det(matrix: list[list[Fraction]]) -> Fraction:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _matrix_transpose(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    return [[matrix[column][row] for column in range(2)] for row in range(2)]


def _matrix_inverse(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    determinant = _matrix_det(matrix)
    if not determinant:
        raise AssertionError("singular affine map")
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def _matrix_multiply(
    left: list[list[Fraction]], right: list[list[Fraction]]
) -> list[list[Fraction]]:
    return [
        [sum(left[row][inner] * right[inner][column] for inner in range(2)) for column in range(2)]
        for row in range(2)
    ]


def _matrix_vector(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [sum(matrix[row][column] * vector[column] for column in range(2)) for row in range(2)]


def _vector_poly_transform(displacement: VectorPoly, matrix: list[list[Fraction]]) -> VectorPoly:
    return (
        _add(_scale(displacement[0], matrix[0][0]), _scale(displacement[1], matrix[0][1])),
        _add(_scale(displacement[0], matrix[1][0]), _scale(displacement[1], matrix[1][1])),
    )


def _cofactor_map(affine: list[list[Fraction]], chi: int) -> list[list[Fraction]]:
    determinant = _matrix_det(affine)
    if chi not in (-1, 1) or not determinant:
        raise AssertionError("invalid oriented affine map")
    inverse_transpose = _matrix_transpose(_matrix_inverse(affine))
    return [[Fraction(chi) * abs(determinant) * value for value in row] for row in inverse_transpose]


def _physical_displacement(
    natural: VectorPoly, affine: list[list[Fraction]], chi: int
) -> VectorPoly:
    return _vector_poly_transform(natural, _cofactor_map(affine, chi))


def _physical_strain(
    displacement: VectorPoly, affine: list[list[Fraction]]
) -> tuple[Poly, Poly, Poly]:
    inverse = _matrix_inverse(affine)
    u, v = displacement
    natural_gradient = [
        [_derivative(u, 0), _derivative(u, 1)],
        [_derivative(v, 0), _derivative(v, 1)],
    ]
    gradient: list[list[Poly]] = [[{}, {}], [{}, {}]]
    for row in range(2):
        for column in range(2):
            for inner in range(2):
                gradient[row][column] = _add(
                    gradient[row][column],
                    natural_gradient[row][inner],
                    inverse[inner][column],
                )
    return gradient[0][0], gradient[1][1], _add(gradient[0][1], gradient[1][0])


def _physical_strain_energy(displacement: VectorPoly, affine: list[list[Fraction]]) -> Fraction:
    jacobian = abs(_matrix_det(affine))
    return jacobian * sum(
        _integrate_square(_multiply(row, row)) for row in _physical_strain(displacement, affine)
    )


def _center_eta(
    nodes: list[list[int]],
    state: list[Fraction],
    affine: list[list[Fraction]],
    a3_sign: int,
) -> Fraction:
    if a3_sign not in (-1, 1):
        raise AssertionError("invalid normal orientation")
    displacement = _q1_displacement(nodes, state)
    natural_gradient = [
        [_evaluate(_derivative(displacement[row], axis), Fraction(0), Fraction(0)) for axis in range(2)]
        for row in range(2)
    ]
    physical_gradient = _matrix_multiply(natural_gradient, _matrix_inverse(affine))
    omega = Fraction(a3_sign, 2) * (physical_gradient[1][0] - physical_gradient[0][1])
    mean_drill = sum(state[3 * node + 2] for node in range(4)) / 4
    return mean_drill - omega


def _physical_nodes(
    nodes: list[list[int]], affine: list[list[Fraction]], origin: list[Fraction]
) -> list[list[Fraction]]:
    return [
        [left + right for left, right in zip(origin, _matrix_vector(affine, [Fraction(r), Fraction(s)]))]
        for r, s in nodes
    ]


def _rigid_states(
    nodes: list[list[int]], affine: list[list[Fraction]], a3_sign: int
) -> dict[str, list[Fraction]]:
    states = {
        "pure_common_drill_g": [],
        "translation_spin_s": [],
        "combined_rigid_r": [],
    }
    for r, s in nodes:
        offset = _matrix_vector(affine, [Fraction(r), Fraction(s)])
        spin_translation = [-offset[1], offset[0]]
        g = [Fraction(0), Fraction(0), Fraction(a3_sign)]
        spin = [spin_translation[0], spin_translation[1], Fraction(0)]
        states["pure_common_drill_g"].extend(g)
        states["translation_spin_s"].extend(spin)
        states["combined_rigid_r"].extend(left + right for left, right in zip(g, spin))
    return states


def _q1_displacement(nodes: list[list[int]], state: list[Fraction]) -> VectorPoly:
    u: Poly = {}
    v: Poly = {}
    for node, (r_i, s_i) in enumerate(nodes):
        shape: Poly = {
            (0, 0): Fraction(1, 4),
            (1, 0): Fraction(r_i, 4),
            (0, 1): Fraction(s_i, 4),
            (1, 1): Fraction(r_i * s_i, 4),
        }
        u = _add(u, shape, state[3 * node])
        v = _add(v, shape, state[3 * node + 1])
    return u, v


def _transform_state(
    nodes: list[list[int]], state: list[Fraction], matrix: list[list[int]]
) -> tuple[list[int], list[Fraction]]:
    index = {tuple(node): position for position, node in enumerate(nodes)}
    permutation: list[int] = []
    transformed = [Fraction(0) for _ in state]
    determinant = _det2(matrix)
    for old, (r, s) in enumerate(nodes):
        target = (
            matrix[0][0] * r + matrix[0][1] * s,
            matrix[1][0] * r + matrix[1][1] * s,
        )
        new = index[target]
        permutation.append(new)
        u, v, theta = state[3 * old : 3 * old + 3]
        transformed[3 * new] = matrix[0][0] * u + matrix[0][1] * v
        transformed[3 * new + 1] = matrix[1][0] * u + matrix[1][1] * v
        transformed[3 * new + 2] = determinant * theta
    return permutation, transformed


def _poly_signature(poly: Poly) -> list[list[object]]:
    return [[str(value), r_power, s_power] for (r_power, s_power), value in sorted(poly.items())]


def _validate_cases(cases: dict[str, object]) -> None:
    if cases.get("schema") != "anysolver.s4.e2-a-cases-v2":
        raise BaselineMismatch("case schema mismatch")
    if cases.get("candidate_id") != CANDIDATE_ID:
        raise BaselineMismatch("candidate identity mismatch")
    terminal = cases.get("terminal")
    if terminal != {"reason": REASON, "value": TERMINAL}:
        raise BaselineMismatch("terminal identity mismatch")
    gates = cases.get("downstream_gates")
    if not isinstance(gates, dict) or set(gates.values()) != {"NOT_RUN_IDENTITY_AMBIGUOUS"}:
        raise BaselineMismatch("downstream stop boundary mismatch")
    geometries = cases.get("affine_geometries")
    if not isinstance(geometries, list) or [record.get("id") for record in geometries if isinstance(record, dict)] != ["square", "skew_rational"]:
        raise BaselineMismatch("affine geometry registry mismatch")
    family = cases.get("nonuniqueness_family")
    if not isinstance(family, dict):
        raise BaselineMismatch("nonuniqueness family missing")
    if family.get("mapping") != "P_physical=chi*abs(det(A))*A_inverse_transpose*P_natural":
        raise BaselineMismatch("oriented cofactor convention mismatch")
    factor = family.get("common_factor")
    if not isinstance(factor, dict) or factor.get("omega_definition") != (
        "omega_D_center=a3_sign*(G_21-G_12)/2; G=U_xi*A_inverse"
    ):
        raise BaselineMismatch("physical center-curl convention mismatch")
    d4 = cases.get("d4_matrices")
    if not isinstance(d4, list) or len(d4) != 8:
        raise BaselineMismatch("D4 registry is not total")
    signatures = {
        tuple(tuple(int(value) for value in row) for row in matrix)
        for matrix in d4
        if isinstance(matrix, list)
    }
    if len(signatures) != 8:
        raise BaselineMismatch("D4 registry contains duplicate or malformed maps")


def _load_inputs() -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {}
    for name, (path, size, sha256) in STATIC_INPUTS.items():
        if path.endswith(".json"):
            values[name] = _verified_json(path, size, sha256)
        else:
            _verified_raw(path, size, sha256)
    _validate_cases(values["cases"])
    return values


def _load_cases_for_exact_test() -> dict[str, object]:
    """Load only the frozen scientific cases while common inputs are freezing."""
    path, size, sha256 = STATIC_INPUTS["cases"]
    cases = _verified_json(path, size, sha256)
    _validate_cases(cases)
    return cases


def _certificate(cases: dict[str, object]) -> dict[str, object]:
    family = cases["nonuniqueness_family"]
    if not isinstance(family, dict):
        raise AssertionError("missing nonuniqueness family")
    boundary_record = family["shared_boundary_lift"]
    interior_record = family["interior_mode"]
    if not isinstance(boundary_record, dict) or not isinstance(interior_record, dict):
        raise AssertionError("malformed displacement family")
    boundary = (_poly(boundary_record["u"]), _poly(boundary_record["v"]))
    interior = (_poly(interior_record["u"]), _poly(interior_record["v"]))
    members: dict[str, VectorPoly] = {}
    for record in family["members"]:
        if not isinstance(record, dict):
            raise AssertionError("malformed family member")
        alpha = _fraction(record["alpha"])
        members[str(record["id"])] = (
            _add(boundary[0], interior[0], alpha),
            _add(boundary[1], interior[1], alpha),
        )
    if len(members) != 2:
        raise AssertionError("exactly two witness members are required")

    nodes = cases["reference_nodes"]
    if not isinstance(nodes, list):
        raise AssertionError("missing nodes")
    boundary_zero: dict[str, bool] = {}
    for axis, axis_name in ((0, "r"), (1, "s")):
        for value in (Fraction(-1), Fraction(1)):
            key = f"{axis_name}={value}"
            boundary_zero[key] = not _restrict(interior[0], axis, value) and not _restrict(interior[1], axis, value)
    if not all(boundary_zero.values()):
        raise AssertionError("interior witness changed a boundary trace")

    covariance = cases["covariance_cases"]
    if not isinstance(covariance, dict):
        raise AssertionError("missing covariance cases")
    frame_rotation = _matrix2(covariance["frame_rotation"])
    if _matrix_det(frame_rotation) != 1 or _matrix_multiply(frame_rotation, _matrix_transpose(frame_rotation)) != [[1, 0], [0, 1]]:
        raise AssertionError("frame rotation is not exact proper orthogonal")
    origin_translation = [_fraction(value) for value in covariance["origin_translation"]]
    unit_scale = _fraction(covariance["unit_scale"])
    if unit_scale <= 0 or _fraction(covariance["normal_reversal"]) != -1:
        raise AssertionError("invalid covariance witness")

    sample = (Fraction(1, 2), Fraction(1, 3))
    geometry_records: dict[str, object] = {}
    for geometry in cases["affine_geometries"]:
        if not isinstance(geometry, dict):
            raise AssertionError("malformed affine geometry")
        geometry_id = str(geometry["id"])
        affine = _matrix2(geometry["A"])
        origin = [_fraction(value) for value in geometry["origin"]]
        determinant = _matrix_det(affine)
        if determinant <= 0:
            raise AssertionError("registered base affine maps must be positively oriented")
        a3_sign = 1
        chi = a3_sign * (1 if determinant > 0 else -1)
        cofactor = _cofactor_map(affine, chi)
        cofactor_pairing = _matrix_multiply(_matrix_transpose(affine), cofactor)
        expected_pairing = [
            [Fraction(chi) * abs(determinant), Fraction(0)],
            [Fraction(0), Fraction(chi) * abs(determinant)],
        ]
        if cofactor_pairing != expected_pairing:
            raise AssertionError("oriented cofactor did not map reference normals physically")
        mapped_members = {
            member_id: _physical_displacement(displacement, affine, chi)
            for member_id, displacement in members.items()
        }
        mapped_interior = _physical_displacement(interior, affine, chi)
        mapped_boundary_zero: dict[str, bool] = {}
        for axis, axis_name in ((0, "r"), (1, "s")):
            for value in (Fraction(-1), Fraction(1)):
                key = f"{axis_name}={value}"
                mapped_boundary_zero[key] = not _restrict(
                    mapped_interior[0], axis, value
                ) and not _restrict(mapped_interior[1], axis, value)
        if mapped_boundary_zero != boundary_zero:
            raise AssertionError("physical cofactor mapping changed the common boundary trace")

        states = _rigid_states(nodes, affine, a3_sign)
        if states["combined_rigid_r"] != [
            left + right
            for left, right in zip(states["translation_spin_s"], states["pure_common_drill_g"])
        ]:
            raise AssertionError("r=s+g identity failed")
        eta_values = {
            name: _center_eta(nodes, state, affine, a3_sign)
            for name, state in states.items()
        }
        if eta_values != {
            "combined_rigid_r": Fraction(0),
            "pure_common_drill_g": Fraction(1),
            "translation_spin_s": Fraction(-1),
        }:
            raise AssertionError("physical center-curl relative spin mismatch")

        vertex_values: dict[str, list[list[str]]] = {}
        member_energies: dict[str, dict[str, str]] = {}
        for member_id, displacement in mapped_members.items():
            values = [
                [
                    str(_evaluate(displacement[0], Fraction(r), Fraction(s))),
                    str(_evaluate(displacement[1], Fraction(r), Fraction(s))),
                ]
                for r, s in nodes
            ]
            if any(value != ["0", "0"] for value in values):
                raise AssertionError("mapped enrichment changed a vertex translation")
            vertex_values[member_id] = values
            state_energy: dict[str, str] = {}
            for state_name, state in states.items():
                base = _q1_displacement(nodes, state)
                eta_value = eta_values[state_name]
                total = (
                    _add(base[0], displacement[0], eta_value),
                    _add(base[1], displacement[1], eta_value),
                )
                state_energy[state_name] = str(_physical_strain_energy(total, affine))
            if Fraction(state_energy["pure_common_drill_g"]) <= 0:
                raise AssertionError("common drill did not activate affine witness")
            if Fraction(state_energy["translation_spin_s"]) <= 0:
                raise AssertionError("translation spin did not activate affine witness")
            if Fraction(state_energy["combined_rigid_r"]) != 0:
                raise AssertionError("matching affine rigid state was not null")
            member_energies[member_id] = state_energy

        affine_activation: list[str] = []
        for raw_gradient in family["affine_gradient_witnesses"]:
            values = [_fraction(value) for value in raw_gradient]
            gradient = [[values[0], values[1]], [values[2], values[3]]]
            theta = Fraction(a3_sign, 2) * (gradient[1][0] - gradient[0][1])
            state: list[Fraction] = []
            for r, s in nodes:
                offset = _matrix_vector(affine, [Fraction(r), Fraction(s)])
                translation = _matrix_vector(gradient, offset)
                state.extend((translation[0], translation[1], theta))
            affine_activation.append(str(_center_eta(nodes, state, affine, a3_sign)))
        if affine_activation != ["0"] * len(family["affine_gradient_witnesses"]):
            raise AssertionError("affine field activated ambiguous lift")

        difference_energy = _physical_strain_energy(mapped_interior, affine)
        difference_strain = [
            str(_evaluate(row, *sample)) for row in _physical_strain(mapped_interior, affine)
        ]
        if difference_energy <= 0 or difference_strain == ["0", "0", "0"]:
            raise AssertionError("affine witness strain maps are equivalent")

        generic_state = [Fraction(value) for value in range(1, 13)]
        eta_generic = _center_eta(nodes, generic_state, affine, a3_sign)
        index = {tuple(node): position for position, node in enumerate(nodes)}
        d4_records: list[dict[str, object]] = []
        for raw_matrix in cases["d4_matrices"]:
            matrix_int = [[int(value) for value in row] for row in raw_matrix]
            determinant_q = _det2(matrix_int)
            if determinant_q not in (-1, 1):
                raise AssertionError("invalid D4 determinant")
            matrix = [[Fraction(value) for value in row] for row in matrix_int]
            affine_new = _matrix_multiply(affine, matrix)
            a3_sign_new = determinant_q * a3_sign
            chi_new = a3_sign_new * (1 if _matrix_det(affine_new) > 0 else -1)
            if chi_new != chi:
                raise AssertionError("oriented cofactor sign drifted under D4 reparameterization")

            transformed = [Fraction(0) for _ in generic_state]
            permutation: list[int] = []
            for new, (r, s) in enumerate(nodes):
                old_coordinate = _matrix_vector(matrix, [Fraction(r), Fraction(s)])
                old = index[(int(old_coordinate[0]), int(old_coordinate[1]))]
                permutation.append(old)
                transformed[3 * new] = generic_state[3 * old]
                transformed[3 * new + 1] = generic_state[3 * old + 1]
                transformed[3 * new + 2] = determinant_q * generic_state[3 * old + 2]
            eta_new = _center_eta(nodes, transformed, affine_new, a3_sign_new)
            if eta_new != determinant_q * eta_generic:
                raise AssertionError("physical center curl did not transform as a pseudoscalar")

            for natural in members.values():
                old_physical = _physical_displacement(natural, affine, chi)
                old_composed = (
                    _substitute_signed_permutation(old_physical[0], matrix_int),
                    _substitute_signed_permutation(old_physical[1], matrix_int),
                )
                new_physical = _physical_displacement(natural, affine_new, chi_new)
                expected_new = (
                    _scale(old_composed[0], Fraction(determinant_q)),
                    _scale(old_composed[1], Fraction(determinant_q)),
                )
                if new_physical != expected_new:
                    raise AssertionError("oriented cofactor lift failed D4 reparameterization")
                if (
                    _scale(new_physical[0], eta_new),
                    _scale(new_physical[1], eta_new),
                ) != (
                    _scale(old_composed[0], eta_generic),
                    _scale(old_composed[1], eta_generic),
                ):
                    raise AssertionError("physical displacement lift changed under D4 reparameterization")
            d4_records.append(
                {
                    "a3_sign": a3_sign_new,
                    "chi": chi_new,
                    "determinant": determinant_q,
                    "eta_pseudoscalar": True,
                    "physical_lift_invariant": True,
                    "reparameterized_node_sources": permutation,
                }
            )

        reversed_state = generic_state[:]
        for node in range(4):
            reversed_state[3 * node + 2] *= -1
        eta_reversed = _center_eta(nodes, reversed_state, affine, -a3_sign)
        if eta_reversed != -eta_generic:
            raise AssertionError("normal reversal did not reverse relative spin")
        for natural in members.values():
            original = _physical_displacement(natural, affine, chi)
            reversed_lift = _physical_displacement(natural, affine, -chi)
            if reversed_lift != (_scale(original[0], Fraction(-1)), _scale(original[1], Fraction(-1))):
                raise AssertionError("normal reversal did not reverse oriented cofactor")
            if (
                _scale(reversed_lift[0], eta_reversed),
                _scale(reversed_lift[1], eta_reversed),
            ) != (
                _scale(original[0], eta_generic),
                _scale(original[1], eta_generic),
            ):
                raise AssertionError("normal reversal changed physical lift")

        affine_rotated = _matrix_multiply(frame_rotation, affine)
        rotated_state: list[Fraction] = []
        for node in range(4):
            translated = _matrix_vector(
                frame_rotation,
                [generic_state[3 * node], generic_state[3 * node + 1]],
            )
            rotated_state.extend((translated[0], translated[1], generic_state[3 * node + 2]))
        eta_rotated = _center_eta(nodes, rotated_state, affine_rotated, a3_sign)
        if eta_rotated != eta_generic:
            raise AssertionError("proper frame rotation changed relative spin")
        for natural in members.values():
            original = _physical_displacement(natural, affine, chi)
            rotated = _physical_displacement(natural, affine_rotated, chi)
            if rotated != _vector_poly_transform(original, frame_rotation):
                raise AssertionError("proper frame rotation changed physical cofactor lift")

        translated_state = generic_state[:]
        for node in range(4):
            translated_state[3 * node] += origin_translation[0]
            translated_state[3 * node + 1] += origin_translation[1]
        if _center_eta(nodes, translated_state, affine, a3_sign) != eta_generic:
            raise AssertionError("origin/translation shift changed relative spin")
        shifted_origin = [left + right for left, right in zip(origin, origin_translation)]
        old_nodes = _physical_nodes(nodes, affine, origin)
        new_nodes = _physical_nodes(nodes, affine, shifted_origin)
        if any(
            [new_value - old_value for new_value, old_value in zip(new_node, old_node)] != origin_translation
            for new_node, old_node in zip(new_nodes, old_nodes)
        ):
            raise AssertionError("origin shift identity failed")

        affine_scaled = [[unit_scale * value for value in row] for row in affine]
        scaled_state = generic_state[:]
        for node in range(4):
            scaled_state[3 * node] *= unit_scale
            scaled_state[3 * node + 1] *= unit_scale
        eta_scaled = _center_eta(nodes, scaled_state, affine_scaled, a3_sign)
        if eta_scaled != eta_generic:
            raise AssertionError("unit scaling changed relative spin")
        for natural in members.values():
            original = _physical_displacement(natural, affine, chi)
            scaled = _physical_displacement(natural, affine_scaled, chi)
            expected_scaled = (
                _scale(original[0], unit_scale),
                _scale(original[1], unit_scale),
            )
            if scaled != expected_scaled:
                raise AssertionError("unit scaling did not scale displacement lift")
            if _physical_strain(scaled, affine_scaled) != _physical_strain(original, affine):
                raise AssertionError("unit scaling changed physical strain")

        geometry_records[geometry_id] = {
            "affine_patch_lift_activation": affine_activation,
            "a3_sign": a3_sign,
            "chi": chi,
            "cofactor_map": [[str(value) for value in row] for row in cofactor],
            "cofactor_pairing": [
                [str(value) for value in row] for row in cofactor_pairing
            ],
            "covariance": {
                "d4_reparameterizations": d4_records,
                "frame_rotation": True,
                "normal_reversal": True,
                "origin_shift": True,
                "unit_scale": str(unit_scale),
            },
            "determinant": str(determinant),
            "difference_engineering_strain_at_r_1_2_s_1_3": difference_strain,
            "difference_strain_energy": str(difference_energy),
            "eta_states": {name: str(value) for name, value in eta_values.items()},
            "member_state_strain_energies": member_energies,
            "same_boundary_trace": mapped_boundary_zero,
            "same_vertices": vertex_values,
        }

    hostile = cases["hostile_e1_a"]
    if not isinstance(hostile, dict):
        raise AssertionError("missing hostile control")
    incidence = [[_fraction(value) for value in row] for row in hostile["cyclic_incidence"]]
    common = [_fraction(value) for value in hostile["expected_common_kernel"]]
    common_image = [sum(left * right for left, right in zip(row, common)) for row in incidence]
    incidence_rank = _rank(incidence)
    full_rank_upper = int(hostile["core_rank_upper_bound"]) + incidence_rank
    if incidence_rank != hostile["expected_drill_rank"] or common_image != [0, 0, 0, 0]:
        raise AssertionError("hostile cyclic-incidence theorem changed")
    if full_rank_upper != hostile["expected_full_rank_upper_bound"] or full_rank_upper > 17:
        raise AssertionError("hostile rank upper bound changed")
    immutable = hostile["immutable_output"]
    if not isinstance(immutable, dict):
        raise AssertionError("missing immutable E1-A output")
    e1_output = _verified_json(str(immutable["path"]), int(immutable["bytes"]), str(immutable["sha256"]))
    if e1_output.get("candidate_terminal") != immutable["terminal"]:
        raise AssertionError("immutable E1-A terminal changed")

    return {
        "affine_geometry_witnesses": geometry_records,
        "hostile_e1_a": {
            "common_image": [str(value) for value in common_image],
            "drill_rank": incidence_rank,
            "full_rank_upper_bound": full_rank_upper,
            "immutable_terminal": e1_output["candidate_terminal"],
        },
        "nonuniqueness": {
            "boundary_trace_difference_zero": boundary_zero,
            "interior_mode": {"u": _poly_signature(interior[0]), "v": _poly_signature(interior[1])},
            "members": list(members),
            "status": "TWO_NON_EQUIVALENT_AFFINE_COVARIANT_DISPLACEMENT_LIFTS",
        },
        "scope_invariants": {
            "center_curl": "EXACT_U_XI_TIMES_A_INVERSE",
            "physical_mapping": "CHI_J_A_A_G_INVERSE_EQ_CHI_ABS_DET_A_A_INVERSE_TRANSPOSE",
            "production_mechanics": "NOT_RUN_IDENTITY_AMBIGUOUS",
        },
    }


def build_contract() -> dict[str, object]:
    values = _load_inputs()
    del values
    oracle_raw = Path(__file__).read_bytes()
    identities = {
        name: {"bytes": size, "path": path, "sha256": sha256}
        for name, (path, size, sha256) in STATIC_INPUTS.items()
    }
    identities["oracle"] = {
        "bytes": len(oracle_raw),
        "path": Path(__file__).relative_to(ROOT).as_posix(),
        "sha256": _sha(oracle_raw),
    }
    return {
        "allowed_extent": {
            "modified": [".gitattributes"],
            "new_paths": ALLOWED_NEW_PATHS,
            "production_paths": [],
        },
        "candidate_id": CANDIDATE_ID,
        "input_identities": identities,
        "mechanics_execution": "FORBIDDEN_AFTER_SOURCE_IDENTITY_BLOCK",
        "production_paths": [],
        "proof_program": [
            "TWO_DISPLACEMENT_LIFT_WITNESSES",
            "SQUARE_AND_RATIONAL_SKEW_AFFINE_MAPS",
            "IDENTICAL_BOUNDARY_TRACE",
            "NON_EQUIVALENT_INTERIOR_STRAIN",
            "VERTEX_AND_AFFINE_COMPLETENESS",
            "PHYSICAL_CENTER_CURL",
            "ORIENTED_COFACTOR_PHYSICAL_NORMAL_MAP",
            "RELATIVE_SPIN_G_S_R",
            "D4_REVERSAL_FRAME_ORIGIN_UNIT_COVARIANCE",
            "IMMUTABLE_E1_A_HOSTILE_RANK_THEOREM",
        ],
        "schema": "anysolver.s4.e2-a-contract-v1",
        "scientific_terminal": {"reason": REASON, "value": TERMINAL},
        "terminal_precedence": [
            "BLOCKED_E2_A_BASELINE_IDENTITY",
            TERMINAL,
            "BLOCKED_E2_A_ORACLE_OR_REVIEW",
            "NO_GO_E2_A_KINEMATIC_FEASIBILITY",
            "NO_GO_E2_A_EXTENSION_CLOSURE",
            "UNCLASSIFIED_E2_A_SOURCE_AND_KINEMATICS",
            "PROVISIONAL_GO_E2_A_LINEAR_REFERENCE_IMPLEMENTATION_PLAN",
        ],
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    values = _load_inputs()
    cases = values["cases"]
    certificate = _certificate(cases)
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_terminal": TERMINAL,
        "certificate": certificate,
        "contract_sha256": contract_sha256,
        "downstream_gates": cases["downstream_gates"],
        "e1_rh": "DEFERRED_NOT_RUN",
        "overall_release_terminal": RELEASE,
        "production": {
            "legacy_shell_default": True,
            "public_api_changed": False,
            "selector_available": False,
            "serialization_changed": False,
        },
        "reason": REASON,
        "schema": "anysolver.s4.e2-a-output-v1",
        "status": "blocked",
    }


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractViolation("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractViolation("contract raw hash mismatch")
    except ContractViolation:
        raise
    except OSError as exc:
        raise ContractViolation(str(exc)) from exc
    try:
        value = _decode(raw)
    except BaselineMismatch as exc:
        raise ContractViolation(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise ContractViolation("contract is not canonical")
    if value != build_contract():
        raise ContractViolation("contract semantic mismatch")
    return caller_sha256


def _blocked(terminal: str, detail: str) -> bytes:
    return _canonical(
        {
            "detail": detail,
            "schema": "anysolver.s4.e2-a-execution-block-v1",
            "status": "blocked",
            "terminal": terminal,
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    args = parser.parse_args(argv)
    try:
        if args.emit_contract:
            if args.contract is not None or args.contract_sha256 is not None:
                raise ContractViolation("contract arguments forbidden in emit mode")
            sys.stdout.buffer.write(_canonical(build_contract()))
            return 0
        if args.contract is None or args.contract_sha256 is None:
            raise ContractViolation("run mode requires caller-bound contract")
        contract_sha = _load_contract(args.contract, args.contract_sha256)
        sys.stdout.buffer.write(_canonical(build_output(contract_sha)))
        return 0
    except BaselineMismatch as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_E2_A_BASELINE_IDENTITY", str(exc)))
        return 2
    except ContractViolation as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_E2_A_ORACLE_OR_REVIEW", str(exc)))
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_E2_A_ORACLE_OR_REVIEW", f"{type(exc).__name__}: {exc}"))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
