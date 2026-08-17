"""Independent exact reference oracle for the open MITC9i paper.

This module is deliberately disconnected from production and candidate code.
It certifies a bounded theory-extraction packet; it does not implement a shell
element and cannot gate or select the HW29 route.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from math import isqrt
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e3_mitc9i_cases.json"
SOURCE_MAP_PATH = ROOT / "docs/reference_cases/e3_mitc9i_source_map.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/e3_mitc9i_contract.json"
CASES_BYTES = 2153
CASES_SHA256 = "B25F0F7787DC8B56B08E4FAA0B1DE6E7AE6D34B80E9BE68E2B202BD4926D33E5"
REFERENCE_ID = "reference_e3_q9.mitc9i_open_theory_extraction_v1"
STATUS = "GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET"
BLOCKED = "BLOCKED_REFERENCE_E3_Q9_MITC9I_SOURCE_IDENTITY"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CONTRACT_INPUTS = [
    "docs/agent_plans/S4_E3_HW29_MITC9I_ROUTE_SELECTION_PLAN.md",
    "docs/E3_MITC9I_REFERENCE.md",
    "docs/reference_cases/e3_baseline.json",
    "docs/reference_cases/e3_environment.json",
    "docs/reference_cases/e3_test_inventory.json",
    "docs/reference_cases/e3_source_registry.json",
    "docs/reference_cases/e3_search_log.json",
    "docs/reference_cases/e3_mitc9i_source_map.json",
    "docs/reference_cases/e3_mitc9i_cases.json",
]


class IdentityError(Exception):
    pass


class ContractError(Exception):
    pass


Poly = dict[tuple[int, int], Fraction]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise IdentityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode(raw: bytes) -> dict[str, object]:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise IdentityError("invalid UTF-8/LF transport")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(IdentityError(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IdentityError(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise IdentityError("JSON is not canonical")
    return value


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _fraction(value: object) -> Fraction:
    if not isinstance(value, (str, int)):
        raise IdentityError(f"not an exact scalar: {value!r}")
    return Fraction(value)


def _load_cases() -> dict[str, object]:
    try:
        raw = CASES_PATH.read_bytes()
    except OSError as exc:
        raise IdentityError(str(exc)) from exc
    if len(raw) != CASES_BYTES or _sha(raw) != CASES_SHA256:
        raise IdentityError("case identity mismatch")
    cases = _decode(raw)
    if cases.get("schema") != "anysolver.e3.mitc9i-cases-v1":
        raise IdentityError("case schema mismatch")
    if cases.get("reference_id") != REFERENCE_ID or cases.get("expected_status") != STATUS:
        raise IdentityError("reference identity mismatch")
    independence = cases.get("hw29_independence")
    if independence != {"affects_hw29": False, "route_gate": "NONE"}:
        raise IdentityError("HW29 independence boundary mismatch")
    return cases


def _clean(poly: Poly) -> Poly:
    return {power: value for power, value in poly.items() if value}


def _add(left: Poly, right: Poly, scale: Fraction = Fraction(1)) -> Poly:
    result = dict(left)
    for power, value in right.items():
        result[power] = result.get(power, Fraction(0)) + scale * value
    return _clean(result)


def _scale(poly: Poly, scale: Fraction) -> Poly:
    return _clean({power: value * scale for power, value in poly.items()})


def _multiply(left: Poly, right: Poly) -> Poly:
    result: Poly = {}
    for (li, lj), lv in left.items():
        for (ri, rj), rv in right.items():
            power = (li + ri, lj + rj)
            result[power] = result.get(power, Fraction(0)) + lv * rv
    return _clean(result)


def _evaluate(poly: Poly, xi: Fraction, eta: Fraction) -> Fraction:
    return sum(value * xi**i * eta**j for (i, j), value in poly.items())


def _restrict(poly: Poly, axis: int, value: Fraction) -> dict[int, Fraction]:
    result: dict[int, Fraction] = {}
    for (i, j), coefficient in poly.items():
        if axis == 0:
            power, term = j, coefficient * value**i
        else:
            power, term = i, coefficient * value**j
        result[power] = result.get(power, Fraction(0)) + term
    return {power: coefficient for power, coefficient in result.items() if coefficient}


def _one_dimensional_multiply(
    left: dict[int, Fraction], right: dict[int, Fraction]
) -> dict[int, Fraction]:
    result: dict[int, Fraction] = {}
    for lp, lv in left.items():
        for rp, rv in right.items():
            result[lp + rp] = result.get(lp + rp, Fraction(0)) + lv * rv
    return {power: coefficient for power, coefficient in result.items() if coefficient}


def _lagrange_1d(node: Fraction, other_a: Fraction, other_b: Fraction) -> dict[int, Fraction]:
    numerator = _one_dimensional_multiply(
        {0: -other_a, 1: Fraction(1)}, {0: -other_b, 1: Fraction(1)}
    )
    denominator = (node - other_a) * (node - other_b)
    return {power: coefficient / denominator for power, coefficient in numerator.items()}


def _corrected_shapes(parameters: dict[str, object]) -> tuple[list[Poly], list[Poly]]:
    alpha = _fraction(parameters["alpha"])
    beta = _fraction(parameters["beta"])
    gamma = _fraction(parameters["gamma"])
    epsilon = _fraction(parameters["epsilon"])
    theta = _fraction(parameters["theta"])
    kappa = _fraction(parameters["kappa"])
    one: Poly = {(0, 0): Fraction(1)}
    xi: Poly = {(1, 0): Fraction(1)}
    eta: Poly = {(0, 1): Fraction(1)}
    one_minus_xi, one_plus_xi = _add(one, xi, -1), _add(one, xi)
    one_minus_eta, one_plus_eta = _add(one, eta, -1), _add(one, eta)
    xi2_minus_one = _add(_multiply(xi, xi), one, -1)
    eta2_minus_one = _add(_multiply(eta, eta), one, -1)

    def corner(
        x_factor: Poly,
        y_factor: Poly,
        first: Fraction,
        second: Fraction,
        y_linear: Poly,
        x_linear: Poly,
    ) -> Poly:
        denominator = first * second
        numerator = _add(
            _add(_scale(one, denominator), _scale(y_linear, first), -1),
            _scale(x_linear, second),
            -1,
        )
        return _scale(_multiply(_multiply(x_factor, y_factor), numerator), Fraction(1, 4) / denominator)

    nbar = [
        corner(one_minus_xi, one_minus_eta, 1 + alpha, 1 + epsilon, one_plus_eta, one_plus_xi),
        corner(one_plus_xi, one_minus_eta, 1 - alpha, 1 + beta, one_plus_eta, one_minus_xi),
        corner(one_plus_xi, one_plus_eta, 1 - gamma, 1 - beta, one_minus_eta, one_minus_xi),
        corner(one_minus_xi, one_plus_eta, 1 + gamma, 1 - epsilon, one_minus_eta, one_plus_xi),
        _scale(_multiply(xi2_minus_one, one_minus_eta), Fraction(1, 2) / (alpha**2 - 1)),
        _scale(_multiply(one_plus_xi, eta2_minus_one), Fraction(1, 2) / (beta**2 - 1)),
        _scale(_multiply(xi2_minus_one, one_plus_eta), Fraction(1, 2) / (gamma**2 - 1)),
        _scale(_multiply(one_minus_xi, eta2_minus_one), Fraction(1, 2) / (epsilon**2 - 1)),
    ]
    n9 = _scale(
        _multiply(xi2_minus_one, eta2_minus_one),
        Fraction(1) / ((theta**2 - 1) * (kappa**2 - 1)),
    )
    shapes = [
        _add(shape, n9, -_evaluate(shape, theta, kappa)) for shape in nbar
    ] + [n9]
    return nbar, shapes


def _shape_certificate(case: dict[str, object]) -> dict[str, object]:
    parameters = case["parameters"]
    nodes = case["nodes"]
    if not isinstance(parameters, dict) or not isinstance(nodes, list) or len(nodes) != 9:
        raise IdentityError("malformed corrected-shape case")
    nbar, shapes = _corrected_shapes(parameters)
    coordinates = [(_fraction(node["xi"]), _fraction(node["eta"])) for node in nodes]
    nodal = [
        [_evaluate(shape, *point) for shape in shapes]
        for point in coordinates
    ]
    identity = [
        [Fraction(int(row == column)) for column in range(9)] for row in range(9)
    ]
    partition: Poly = {}
    for shape in shapes:
        partition = _add(partition, shape)
    q2_checks: dict[str, bool] = {}
    for i, j in case["q2_monomials"]:
        reproduced: Poly = {}
        for shape, (node_xi, node_eta) in zip(shapes, coordinates):
            reproduced = _add(reproduced, shape, node_xi**int(i) * node_eta**int(j))
        q2_checks[f"xi^{i}_eta^{j}"] = reproduced == {(int(i), int(j)): Fraction(1)}

    edge_specs = {
        "bottom": (1, Fraction(-1), [0, 4, 1], [Fraction(-1), _fraction(parameters["alpha"]), Fraction(1)]),
        "right": (0, Fraction(1), [1, 5, 2], [Fraction(-1), _fraction(parameters["beta"]), Fraction(1)]),
        "top": (1, Fraction(1), [3, 6, 2], [Fraction(-1), _fraction(parameters["gamma"]), Fraction(1)]),
        "left": (0, Fraction(-1), [0, 7, 3], [Fraction(-1), _fraction(parameters["epsilon"]), Fraction(1)]),
    }
    edge_checks: dict[str, bool] = {}
    for name, (axis, fixed, active, positions) in edge_specs.items():
        expected = [
            _lagrange_1d(positions[index], positions[(index + 1) % 3], positions[(index + 2) % 3])
            for index in range(3)
        ]
        active_ok = all(_restrict(shapes[node], axis, fixed) == expected[index] for index, node in enumerate(active))
        inactive_ok = all(not _restrict(shapes[node], axis, fixed) for node in range(9) if node not in active)
        edge_checks[name] = active_ok and inactive_ok

    theta, kappa = coordinates[8]
    central_residual = []
    for component in range(2):
        interpolated = sum(
            _evaluate(shape, theta, kappa) * coordinates[index][component]
            for index, shape in enumerate(nbar)
        )
        central_residual.append(coordinates[8][component] - interpolated)
    if nodal != identity or partition != {(0, 0): Fraction(1)}:
        raise AssertionError("corrected Q9 nodal or partition certificate failed")
    if not all(q2_checks.values()) or not all(edge_checks.values()) or central_residual != [0, 0]:
        raise AssertionError("corrected Q9 completeness certificate failed")
    return {
        "central_m1_residual": [str(value) for value in central_residual],
        "edge_restrictions": edge_checks,
        "nodal_kronecker": True,
        "partition_of_unity": True,
        "q2_reproduction": q2_checks,
    }


def _transpose(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    return [list(row) for row in zip(*matrix)]


def _matrix_multiply(
    left: list[list[Fraction]], right: list[list[Fraction]]
) -> list[list[Fraction]]:
    return [
        [sum(left[row][inner] * right[inner][column] for inner in range(2)) for column in range(2)]
        for row in range(2)
    ]


def _inverse2(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if not determinant:
        raise AssertionError("singular Jacobian")
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def _matrix(case: object) -> list[list[Fraction]]:
    if not isinstance(case, list) or len(case) != 2:
        raise IdentityError("malformed matrix")
    return [[_fraction(value) for value in row] for row in case]


def _matrix_strings(matrix: list[list[Fraction]]) -> list[list[str]]:
    return [[str(value) for value in row] for row in matrix]


def _covc_certificate(case: dict[str, object]) -> dict[str, object]:
    strain = _matrix(case["cartesian_strain"])
    center = _matrix(case["center_jacobian"])
    off_center = _matrix(case["off_center_jacobian"])
    covc = _matrix_multiply(_matrix_multiply(_transpose(center), strain), center)
    recovered = _matrix_multiply(
        _matrix_multiply(_transpose(_inverse2(center)), covc), _inverse2(center)
    )
    true_off_center = _matrix_multiply(
        _matrix_multiply(_transpose(off_center), strain), off_center
    )
    if recovered != strain or true_off_center == covc:
        raise AssertionError("COVc category certificate failed")
    return {
        "category":"CENTRE_JACOBIAN_APPROXIMATION_NOT_EXACT_COVARIANCE",
        "covc": _matrix_strings(covc),
        "fixed_center_recovery": _matrix_strings(recovered),
        "off_center_differs": True,
        "true_off_center_covariant": _matrix_strings(true_off_center),
    }


def _sqrt_bounds(value: Fraction, digits: int) -> tuple[Fraction, Fraction]:
    if value < 0:
        raise AssertionError("negative square-root argument")
    scale = 10**digits
    integer = isqrt((value.numerator * scale * scale) // value.denominator)
    lower = Fraction(integer, scale)
    upper = lower if lower * lower == value else Fraction(integer + 1, scale)
    return lower, upper


def _quadratic_value(coefficients: tuple[Fraction, Fraction, Fraction], x: Fraction) -> Fraction:
    a, b, c = coefficients
    return a * x * x + b * x + c


def _speed_squared_coefficients(alpha: Fraction) -> tuple[Fraction, Fraction, Fraction]:
    dx_linear = -Fraction(2) / (1 - alpha * alpha) + Fraction(4) / (1 - alpha)
    dx_constant = Fraction(2)
    dy_linear = -Fraction(4) / (1 - alpha * alpha)
    return (
        dx_linear * dx_linear + dy_linear * dy_linear,
        2 * dx_linear * dx_constant,
        dx_constant * dx_constant,
    )


def _arc_bounds(
    alpha: Fraction, lower: Fraction, upper: Fraction, subdivisions: int, digits: int
) -> tuple[Fraction, Fraction]:
    coefficients = _speed_squared_coefficients(alpha)
    width = (upper - lower) / subdivisions
    vertex = -coefficients[1] / (2 * coefficients[0])
    total_lower = Fraction(0)
    total_upper = Fraction(0)
    for index in range(subdivisions):
        left = lower + index * width
        right = left + width
        values = [_quadratic_value(coefficients, left), _quadratic_value(coefficients, right)]
        if left <= vertex <= right:
            values.append(_quadratic_value(coefficients, vertex))
        speed_lower = _sqrt_bounds(min(values), digits)[0]
        speed_upper = _sqrt_bounds(max(values), digits)[1]
        total_lower += width * speed_lower
        total_upper += width * speed_upper
    return total_lower, total_upper


def _shift_function_bounds(
    alpha: Fraction, subdivisions: int, digits: int
) -> tuple[Fraction, Fraction]:
    partial = _arc_bounds(alpha, Fraction(-1), alpha, subdivisions, digits)
    total = _arc_bounds(alpha, Fraction(-1), Fraction(1), subdivisions, digits)
    target = (alpha + 1) / 2
    return partial[0] / total[1] - target, partial[1] / total[0] - target


def _outward_decimal(value: Fraction, places: int, upper: bool) -> str:
    scale = 10**places
    scaled = value.numerator * scale
    integer = -((-scaled) // value.denominator) if upper else scaled // value.denominator
    sign = "-" if integer < 0 else ""
    digits = str(abs(integer)).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def _shift_certificate(case: dict[str, object], straight: dict[str, object]) -> dict[str, object]:
    lower_alpha, upper_alpha = [_fraction(value) for value in case["root_bracket"]]
    subdivisions = int(case["subdivisions"])
    digits = int(case["sqrt_decimal_digits"])
    if not Fraction(-1) < lower_alpha < upper_alpha < Fraction(1):
        raise AssertionError("curved-side bracket leaves the nonsingular interpolation domain")
    lower_value = _shift_function_bounds(lower_alpha, subdivisions, digits)
    upper_value = _shift_function_bounds(upper_alpha, subdivisions, digits)
    if lower_value[0] <= 0 or upper_value[1] >= 0:
        raise AssertionError("outward curved-side root bracket failed")
    published = Fraction(case["published_decimal"])
    if not lower_alpha < published < upper_alpha:
        raise AssertionError("printed curved-side value is outside certified bracket")
    points = straight["points"]
    left_length = _fraction(points[1][0]) - _fraction(points[0][0])
    total_length = _fraction(points[2][0]) - _fraction(points[0][0])
    exact_alpha = _fraction(straight["alpha"])
    if left_length / total_length != (exact_alpha + 1) / 2:
        raise AssertionError("straight-side exact shift failed")
    return {
        "curved_side": {
            "continuous_nonsingular_bracket": True,
            "f_at_lower_outward": [
                _outward_decimal(lower_value[0], 12, False),
                _outward_decimal(lower_value[1], 12, True),
            ],
            "f_at_upper_outward": [
                _outward_decimal(upper_value[0], 12, False),
                _outward_decimal(upper_value[1], 12, True),
            ],
            "printed_value_inside": True,
            "root_bracket": [str(lower_alpha), str(upper_alpha)],
            "subdivisions": subdivisions,
        },
        "straight_side": {"arc_fraction": str(left_length / total_length), "exact_alpha": str(exact_alpha)},
    }


def _drilling_certificate(case: dict[str, object]) -> dict[str, object]:
    rows = {
        (0, 0): ({"Omega1"}, {"U3", "V2"}),
        (1, 0): ({"Omega2"}, {"U4", "V5"}),
        (0, 1): ({"Omega3"}, {"U6", "V4"}),
        (1, 1): ({"Omega4"}, {"U8", "V7"}),
        (2, 0): ({"Omega5"}, {"U7"}),
        (0, 2): ({"Omega6"}, {"V8"}),
        (1, 2): ({"Omega8"}, {"V9"}),
        (2, 1): ({"Omega7"}, {"U9"}),
        (2, 2): ({"Omega9"}, set()),
    }
    rotation_only = [power for power, (_, displacement) in rows.items() if not displacement]
    functional = [_fraction(value) for value in case["highest_node_functional"]]
    integral = Fraction(2, 5) * Fraction(2, 5)
    if rotation_only != [(2, 2)] or sum(functional) != 0 or integral != Fraction(4, 25):
        raise AssertionError("drilling highest-mode certificate failed")
    return {
        "alternatives": case["source_alternatives"],
        "c9_square_integral_factor": str(integral),
        "complete_monomial_count": len(rows),
        "highest_mode_node_row": [str(value) for value in functional],
        "highest_mode_rigid_row_sum": str(sum(functional)),
        "linked_term_count": len(rows) - len(rotation_only),
        "rotation_only_monomials": [[i, j] for i, j in rotation_only],
    }


def _benchmark_certificate(case: dict[str, object]) -> dict[str, object]:
    membrane = case["membrane_patch"]
    expected = [_fraction(value) for value in membrane["expected_tensor_strain"]]
    derived = [Fraction(1, 1000), Fraction(1, 1000), Fraction(1, 2000)]
    shear = case["transverse_shear_patch"]
    right = _fraction(shear["right_boundary_x"]) / 40
    if expected != derived or right != _fraction(shear["expected_right_displacement"]):
        raise AssertionError("bounded analytical benchmark certificate failed")
    return {
        "membrane_tensor_strain": [str(value) for value in derived],
        "reported_single_element_zero_eigenvalues": {
            "classification": "SOURCE_ATTRIBUTED_NOT_REPRODUCED",
            "value": int(case["reported_single_element_zero_eigenvalues"]),
        },
        "transverse_right_displacement": str(right),
    }


def _certificate(cases: dict[str, object]) -> dict[str, object]:
    certificate = {
        "benchmarks": _benchmark_certificate(cases["benchmark_cases"]),
        "corrected_shapes": _shape_certificate(cases["corrected_shape_case"]),
        "covc": _covc_certificate(cases["covc_case"]),
        "drilling": _drilling_certificate(cases["drilling_case"]),
        "finite_rotation": {
            "conventions": cases["finite_rotation_case"],
            "missing_explicit_details": [
                "first_variation_of_sampled_green_strain_operator",
                "second_variation_and_closed_form_consistent_tangent",
                "incremental_drilling_constraint_linearization_blocks",
                "consistent_mass_and_geometric_stiffness_separation",
                "load_potential_and_follower_load_linearization",
            ],
        },
        "hw29_independence": cases["hw29_independence"],
        "shift_parameters": _shift_certificate(
            cases["curved_side_shift_case"], cases["straight_side_shift_case"]
        ),
    }
    return certificate


def build_contract() -> dict[str, object]:
    _load_cases()
    source_raw = SOURCE_MAP_PATH.read_bytes()
    source_value = _decode(source_raw)
    if not isinstance(source_value, dict) or source_raw != _canonical(source_value):
        raise IdentityError("source map is not canonical")
    identities: dict[str, object] = {}
    for relative in CONTRACT_INPUTS:
        raw = (ROOT / relative).read_bytes()
        identities[relative] = {"bytes": len(raw), "path": relative, "sha256": _sha(raw)}
    oracle_relative = Path(__file__).relative_to(ROOT).as_posix()
    oracle_raw = Path(__file__).read_bytes()
    identities[oracle_relative] = {
        "bytes": len(oracle_raw),
        "path": oracle_relative,
        "sha256": _sha(oracle_raw),
    }
    return {
        "hw29_route_gate": "NONE",
        "input_identities": identities,
        "production_paths": [],
        "reference_id": REFERENCE_ID,
        "schema": "anysolver.s4.e3-mitc9i-contract-v1",
        "scientific_status": STATUS,
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    cases = _load_cases()
    return {
        "certificate": _certificate(cases),
        "contract_sha256": contract_sha256,
        "hw29_route_gate": "NONE",
        "overall_release_terminal": RELEASE,
        "production_changed": False,
        "reference_id": REFERENCE_ID,
        "schema": "anysolver.s4.e3-mitc9i-output-v1",
        "status": STATUS,
    }


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractError("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractError("contract raw hash mismatch")
        value = _decode(raw)
        if not isinstance(value, dict) or raw != _canonical(value):
            raise ContractError("contract is not canonical")
        if value != build_contract():
            raise ContractError("contract semantic mismatch")
    except ContractError:
        raise
    except (OSError, IdentityError) as exc:
        raise ContractError(str(exc)) from exc
    return caller_sha256


def _blocked(detail: str) -> bytes:
    return _canonical(
        {
            "detail": detail,
            "reference_id": REFERENCE_ID,
            "schema": "anysolver.e3.mitc9i-oracle-block-v1",
            "status": BLOCKED,
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    arguments = parser.parse_args(argv)
    try:
        if arguments.emit_contract:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in emit mode")
            sys.stdout.buffer.write(_canonical(build_contract()))
            return 0
        if arguments.contract is None or arguments.contract_sha256 is None:
            raise ContractError("run mode requires caller-bound contract")
        contract_sha = _load_contract(arguments.contract, arguments.contract_sha256)
        sys.stdout.buffer.write(_canonical(build_output(contract_sha)))
        return 0
    except ContractError as exc:
        sys.stdout.buffer.write(_blocked(str(exc)))
        return 2
    except IdentityError as exc:
        sys.stdout.buffer.write(_blocked(str(exc)))
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(_blocked(f"{type(exc).__name__}: {exc}"))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
