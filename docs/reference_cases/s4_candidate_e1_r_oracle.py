"""Exact standard-library oracle for the Candidate E1-R planar regularizer."""

from __future__ import annotations

import argparse
import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/reference_cases/s4_candidate_e1_r_contract.json"
CANDIDATE_ID = "candidate_e1.sestra_pattern_planar_gauge_regularizer_v1"
TERMINAL = "PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY"
REASON = "EXACT_PLANAR_PROJECTOR_GAUGE_AND_NON_INTRUSION_CERTIFIED"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"

STATIC_INPUTS = {
    "plan": (
        "docs/agent_plans/S4_CANDIDATE_E1_ALLMAN_SESTRA_QUALIFICATION_PLAN.md",
        5885,
        "16093C1B1E95AAC790E5AC0F4A6D19927782A0D24194108367B77BCDB5CA6BBE",
    ),
    "derivation": (
        "docs/S4_CANDIDATE_E1_R_DERIVATION.md",
        3867,
        "37B4C31FE326414339EE1EB9E8052161FF572DB13FB457FFEA71AEBAAF5322B1",
    ),
    "baseline": (
        "docs/reference_cases/s4_candidate_e1_baseline.json",
        2622,
        "EA7E81C38912F14CB89CFD98302B6A8478D878939F7CFC1E3A60439667A745C1",
    ),
    "environment": (
        "docs/reference_cases/s4_candidate_e1_environment.json",
        1330,
        "F2DB5FF809FE0ED35ABE398FBFCECD133F2E8C36E96D1AB5C79354784F7216DE",
    ),
    "source_registry": (
        "docs/reference_cases/s4_candidate_e1_source_registry.json",
        2628,
        "C25197408932746D04C0651D082D5435369CEF94CFAF03BD3A12F8521A24B375",
    ),
    "test_inventory": (
        "docs/reference_cases/s4_candidate_e1_test_inventory.json",
        1751,
        "3290ACA0B30CD8C23A2508543DC8889D1F0795F38CF237AF7E826833E230EA16",
    ),
    "materials": (
        "docs/reference_cases/s4_candidate_e1_material_fixtures.json",
        737,
        "F29886ED86AC83081E04D4A352D3F25BA304393DB5C0FA64A3BCF4338D4EFA07",
    ),
    "identity": (
        "docs/reference_cases/s4_candidate_e1_r_identity.json",
        1382,
        "201E8B7C33F055BF6BCC17CE2EB3FFDB5502C438013EB33419868990FACABA5E",
    ),
    "cases": (
        "docs/reference_cases/s4_candidate_e1_r_cases.json",
        1256,
        "695FBD1A4F07806444B26E3350F436FF9055A0816968ECFE65F20567B3B71EA9",
    ),
}

ALLOWED_NEW_PATHS = [
    "docs/agent_plans/S4_CANDIDATE_E1_ALLMAN_SESTRA_QUALIFICATION_PLAN.md",
    "docs/S4_CANDIDATE_E1_A_DERIVATION.md",
    "docs/S4_CANDIDATE_E1_R_DERIVATION.md",
    "docs/S4_CANDIDATE_E1_QUALIFICATION_REPORT.md",
    "docs/S4_CANDIDATE_E1_A_INDEPENDENT_REVIEW.md",
    "docs/S4_CANDIDATE_E1_R_INDEPENDENT_REVIEW.md",
    "docs/reference_cases/s4_candidate_e1_baseline.json",
    "docs/reference_cases/s4_candidate_e1_environment.json",
    "docs/reference_cases/s4_candidate_e1_source_registry.json",
    "docs/reference_cases/s4_candidate_e1_material_fixtures.json",
    "docs/reference_cases/s4_candidate_e1_test_inventory.json",
    "docs/reference_cases/s4_candidate_e1_a_identity.json",
    "docs/reference_cases/s4_candidate_e1_a_cases.json",
    "docs/reference_cases/s4_candidate_e1_a_oracle.py",
    "docs/reference_cases/s4_candidate_e1_a_contract.json",
    "docs/reference_cases/s4_candidate_e1_a_output.json",
    "docs/reference_cases/s4_candidate_e1_r_identity.json",
    "docs/reference_cases/s4_candidate_e1_r_cases.json",
    "docs/reference_cases/s4_candidate_e1_r_oracle.py",
    "docs/reference_cases/s4_candidate_e1_r_contract.json",
    "docs/reference_cases/s4_candidate_e1_r_output.json",
    "docs/reference_cases/s4_candidate_e1_status.json",
    "tests/test_s4_candidate_e1_a_exact_rank.py",
    "tests/test_s4_candidate_e1_a_qualification.py",
    "tests/test_s4_candidate_e1_r_exact_regularizer.py",
    "tests/test_s4_candidate_e1_r_qualification.py",
    "tests/test_s4_candidate_e1_closeout.py",
]


class BaselineMismatch(Exception):
    pass


class ContractViolation(Exception):
    pass


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
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _verified_raw(path: str, size: int, sha256: str) -> bytes:
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


def _canonical_lf_file(path: str, size: int, sha256: str) -> bytes:
    try:
        raw = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    except OSError as exc:
        raise BaselineMismatch(f"missing baseline path: {path}") from exc
    if b"\r" in raw or len(raw) != size or _sha(raw) != sha256:
        raise BaselineMismatch(f"baseline identity mismatch: {path}")
    return raw


def _test_names(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return [
        f"{path.relative_to(ROOT).as_posix()}::{node.name}"
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]


def _validate_baseline(values: dict[str, dict[str, object]]) -> None:
    baseline = values["baseline"]
    if baseline["authority"] != {
        "branch": "codex/s4-candidate-e1-allman-sestra-qualification",
        "e0_commit": "87b639499187736c59d87bc4aa8e6bd7f819d28b",
        "e0_tree": "c01fd5cab7b63325e6cb5b70000f4586d4788563",
        "production_qualification_base": "a9b45ca95303bc4b30b893fbb0d7177f9c98db03",
    }:
        raise BaselineMismatch("authority mismatch")
    for record in baseline["immutable_results"].values():
        raw = (ROOT / record["path"]).read_bytes()
        if _sha(raw) != record["sha256"]:
            raise BaselineMismatch(f"immutable result drift: {record['path']}")
    for record in baseline["predecessor_packet"].values():
        _verified_raw(record["path"], record["bytes"], record["sha256"])
    for path, record in baseline["production_sources"].items():
        _canonical_lf_file(
            path,
            record["canonical_lf_bytes"],
            record["canonical_lf_sha256"],
        )

    inventory = values["test_inventory"]
    inherited = inventory["composition"]["inherited_85"]
    e0_inventory = _verified_json(
        inherited["path"], inherited["bytes"], inherited["sha256"]
    )
    base75_record = e0_inventory["composition"]["base_75"]
    base75 = _verified_json(
        base75_record["path"], base75_record["bytes"], base75_record["sha256"]
    )
    ordered_files: list[str] = []
    for record in base75["files"]:
        _canonical_lf_file(
            record["path"],
            record["canonical_lf_bytes"],
            record["canonical_lf_sha256"],
        )
        ordered_files.append(record["path"])
    nodes = list(base75["collection"]["node_ids"])
    for record in e0_inventory["composition"]["appended_files"]:
        _canonical_lf_file(
            record["path"],
            record["canonical_lf_bytes"],
            record["canonical_lf_sha256"],
        )
        ordered_files.append(record["path"])
    nodes.extend(e0_inventory["composition"]["appended_node_ids"])
    for key in ("e0_source_gate", "e0_closeout"):
        record = inventory["composition"][key]
        _canonical_lf_file(
            record["path"],
            record["canonical_lf_bytes"],
            record["canonical_lf_sha256"],
        )
        names = _test_names(ROOT / record["path"])
        if len(names) != record["node_count"]:
            raise BaselineMismatch(f"node count mismatch: {record['path']}")
        nodes.extend(names)
        ordered_files.append(record["path"])
    joined = ("\n".join(nodes) + "\n").encode("utf-8")
    expected = inventory["accepted_pre_e1"]
    if len(nodes) != len(set(nodes)) or len(nodes) != expected["count"]:
        raise BaselineMismatch("accepted node cardinality mismatch")
    if (
        len(joined) != expected["node_ids_canonical_lf_bytes"]
        or _sha(joined) != expected["node_ids_canonical_lf_sha256"]
    ):
        raise BaselineMismatch("accepted node identity mismatch")
    if ordered_files != expected["ordered_files"]:
        raise BaselineMismatch("accepted file order mismatch")


def _validate_inputs() -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {}
    for name, (path, size, sha256) in STATIC_INPUTS.items():
        if path.endswith(".json"):
            values[name] = _verified_json(path, size, sha256)
        else:
            _verified_raw(path, size, sha256)
    _validate_baseline(values)
    identity = values["identity"]
    cases = values["cases"]
    if identity["candidate_id"] != CANDIDATE_ID or cases["candidate_id"] != CANDIDATE_ID:
        raise BaselineMismatch("candidate identity mismatch")
    if identity["relationship"] != {
        "may_combine_with_e1_a": False,
        "sestra_binary_reproduction": False,
        "type": "documented_sestra_matrix_pattern_with_independent_component_gauge",
    }:
        raise BaselineMismatch("candidate separation mismatch")
    if identity["eligibility"]["automatic_planarity_tolerance"] is not False:
        raise BaselineMismatch("automatic planarity tolerance is forbidden")
    if identity["mass"]["scope"] != "audit_only_no_modal_or_transient":
        raise BaselineMismatch("mass scope mismatch")
    return values


Matrix = list[list[Fraction]]


def _f(value: object) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _zeros(rows: int, cols: int) -> Matrix:
    return [[Fraction(0) for _ in range(cols)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = Fraction(1)
    return result


def _transpose(matrix: Matrix) -> Matrix:
    if not matrix:
        return []
    return [list(column) for column in zip(*matrix)]


def _matmul(left: Matrix, right: Matrix) -> Matrix:
    if not left:
        return []
    if not right:
        return [[] for _ in left]
    right_t = _transpose(right)
    return [
        [sum((a * b for a, b in zip(row, column)), Fraction(0)) for column in right_t]
        for row in left
    ]


def _matvec(matrix: Matrix, vector: list[Fraction]) -> list[Fraction]:
    return [
        sum((left * right for left, right in zip(row, vector)), Fraction(0))
        for row in matrix
    ]


def _scale(matrix: Matrix, factor: Fraction) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def _add(left: Matrix, right: Matrix) -> Matrix:
    return [
        [a + b for a, b in zip(left_row, right_row)]
        for left_row, right_row in zip(left, right)
    ]


def _trace(matrix: Matrix) -> Fraction:
    return sum((matrix[index][index] for index in range(len(matrix))), Fraction(0))


def _rank(matrix: Matrix, *, columns: int | None = None) -> int:
    if not matrix:
        return 0
    a = [row[:] for row in matrix]
    rows = len(a)
    cols = len(a[0]) if columns is None else columns
    rank = 0
    for col in range(cols):
        pivot = next((row for row in range(rank, rows) if a[row][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scale = a[rank][col]
        a[rank] = [value / scale for value in a[rank]]
        for row in range(rows):
            if row != rank and a[row][col]:
                factor = a[row][col]
                a[row] = [
                    left - factor * right
                    for left, right in zip(a[row], a[rank])
                ]
        rank += 1
        if rank == rows:
            break
    return rank


def _rref(matrix: Matrix, columns: int) -> tuple[Matrix, list[int]]:
    a = [row[:] for row in matrix]
    pivot_row = 0
    pivots: list[int] = []
    for col in range(columns):
        pivot = next(
            (row for row in range(pivot_row, len(a)) if a[row][col]),
            None,
        )
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        scale = a[pivot_row][col]
        a[pivot_row] = [value / scale for value in a[pivot_row]]
        for row in range(len(a)):
            if row != pivot_row and a[row][col]:
                factor = a[row][col]
                a[row] = [
                    left - factor * right
                    for left, right in zip(a[row], a[pivot_row])
                ]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == len(a):
            break
    return a, pivots


def _nullspace(matrix: Matrix, columns: int) -> Matrix:
    if not matrix:
        return _identity(columns)
    reduced, pivots = _rref(matrix, columns)
    free = [column for column in range(columns) if column not in pivots]
    basis_columns: list[list[Fraction]] = []
    for free_column in free:
        vector = [Fraction(0) for _ in range(columns)]
        vector[free_column] = Fraction(1)
        for row, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row][free_column]
        basis_columns.append(vector)
    return (
        [[basis_columns[column][row] for column in range(len(basis_columns))] for row in range(columns)]
        if basis_columns
        else _zeros(columns, 0)
    )


def _determinant(matrix: Matrix) -> Fraction:
    if not matrix:
        return Fraction(1)
    a = [row[:] for row in matrix]
    determinant = Fraction(1)
    sign = Fraction(1)
    for col in range(len(a)):
        pivot = next((row for row in range(col, len(a)) if a[row][col]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            sign = -sign
        pivot_value = a[col][col]
        determinant *= pivot_value
        for row in range(col + 1, len(a)):
            if a[row][col]:
                factor = a[row][col] / pivot_value
                for inner in range(col + 1, len(a)):
                    a[row][inner] -= factor * a[col][inner]
    return sign * determinant


def _solve_unique(matrix: Matrix, rhs: list[Fraction]) -> list[Fraction]:
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs)]
    rows = len(augmented)
    cols = len(matrix[0])
    pivot_row = 0
    pivots: list[int] = []
    for col in range(cols):
        pivot = next(
            (row for row in range(pivot_row, rows) if augmented[row][col]),
            None,
        )
        if pivot is None:
            continue
        augmented[pivot_row], augmented[pivot] = augmented[pivot], augmented[pivot_row]
        scale = augmented[pivot_row][col]
        augmented[pivot_row] = [value / scale for value in augmented[pivot_row]]
        for row in range(rows):
            if row != pivot_row and augmented[row][col]:
                factor = augmented[row][col]
                augmented[row] = [
                    left - factor * right
                    for left, right in zip(augmented[row], augmented[pivot_row])
                ]
        pivots.append(col)
        pivot_row += 1
    if len(pivots) != cols:
        raise AssertionError("system is not unique")
    if any(
        all(value == 0 for value in row[:cols]) and row[cols]
        for row in augmented
    ):
        raise AssertionError("system is inconsistent")
    solution = [Fraction(0) for _ in range(cols)]
    for row, col in enumerate(pivots):
        solution[col] = augmented[row][cols]
    return solution


def _fraction_matrix(matrix: object) -> Matrix:
    return [[_f(value) for value in row] for row in matrix]


def _strings(vector: list[Fraction]) -> list[str]:
    return [str(value) for value in vector]


def _matrix_strings(matrix: Matrix) -> list[list[str]]:
    return [_strings(row) for row in matrix]


def _r4(c: Fraction) -> Matrix:
    return [
        [c if row == col else -c / 3 for col in range(4)]
        for row in range(4)
    ]


def _injection(normal: list[Fraction]) -> Matrix:
    result = _zeros(4, 24)
    for node in range(4):
        for component in range(3):
            result[node][6 * node + 3 + component] = normal[component]
    return result


def _full_block(matrix3: Matrix) -> Matrix:
    result = _zeros(24, 24)
    for node in range(4):
        for family in range(2):
            offset = 6 * node + 3 * family
            for row in range(3):
                for col in range(3):
                    result[offset + row][offset + col] = matrix3[row][col]
    return result


def _rotational_block(matrix3: Matrix) -> Matrix:
    result = _zeros(12, 12)
    for node in range(4):
        for row in range(3):
            for col in range(3):
                result[3 * node + row][3 * node + col] = matrix3[row][col]
    return result


def _scatter(elements: list[list[int]], scales: list[Fraction], node_count: int) -> Matrix:
    result = _zeros(node_count, node_count)
    for element, scale in zip(elements, scales):
        local = _r4(scale)
        for local_row, global_row in enumerate(element):
            for local_col, global_col in enumerate(element):
                result[global_row][global_col] += local[local_row][local_col]
    return result


def _components(elements: list[list[int]], scales: list[Fraction]) -> list[list[int]]:
    nodes = sorted({node for element in elements for node in element})
    adjacency = {node: set() for node in nodes}
    for element, scale in zip(elements, scales):
        if scale <= 0:
            continue
        for node in element:
            adjacency[node].update(other for other in element if other != node)
    components: list[list[int]] = []
    visited: set[int] = set()
    for seed in nodes:
        if seed in visited:
            continue
        stack = [seed]
        visited.add(seed)
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbour in sorted(adjacency[node]):
                if neighbour not in visited:
                    visited.add(neighbour)
                    stack.append(neighbour)
        components.append(sorted(component))
    return components


def _area_weights(
    elements: list[list[int]], scales: list[Fraction], node_count: int
) -> list[Fraction]:
    weights = [Fraction(0) for _ in range(node_count)]
    for element, scale in zip(elements, scales):
        if scale <= 0:
            continue
        for node in element:
            weights[node] += Fraction(1, 4)
    return weights


def _projector_certificate(cases: dict[str, object]) -> dict[str, object]:
    diagonal = [_f(value) for value in cases["local"]["rotational_diagonal"]]
    dmean = sum(diagonal, Fraction(0)) / 12
    if dmean != 4:
        raise AssertionError("registered Dmean mismatch")
    epsilon = Fraction(1, 100_000_000)
    constant = [Fraction(1) for _ in range(4)]
    zero_sum_vectors = [
        [Fraction(1), Fraction(-1), Fraction(0), Fraction(0)],
        [Fraction(1), Fraction(1), Fraction(-1), Fraction(-1)],
        [Fraction(1), Fraction(-1), Fraction(1), Fraction(-1)],
    ]
    sensitivities = []
    reference_matrix: Matrix | None = None
    for text in cases["local"]["sensitivity_multipliers"]:
        multiplier = Fraction(text)
        c = epsilon * dmean * multiplier
        matrix = _r4(c)
        eigenvalue = 4 * c / 3
        if _matvec(matrix, constant) != [0, 0, 0, 0]:
            raise AssertionError("constant drill was not preserved")
        if _rank(matrix) != 3:
            raise AssertionError("local projector rank mismatch")
        for vector in zero_sum_vectors:
            if _matvec(matrix, vector) != [eigenvalue * value for value in vector]:
                raise AssertionError("local projector eigenspace mismatch")
        leading_minor = _determinant([row[:3] for row in matrix[:3]])
        if leading_minor != 16 * c**3 / 27:
            raise AssertionError("local projector minor mismatch")
        sensitivities.append(
            {
                "c": str(c),
                "eigenvalues": ["0", str(eigenvalue), str(eigenvalue), str(eigenvalue)],
                "leading_minor": str(leading_minor),
                "multiplier": str(multiplier),
                "rank": 3,
            }
        )
        if multiplier == 1:
            reference_matrix = matrix
    if reference_matrix is None:
        raise AssertionError("reference sensitivity is missing")

    permutations = [
        [0, 1, 2, 3],
        [1, 2, 3, 0],
        [2, 3, 0, 1],
        [3, 0, 1, 2],
        [0, 3, 2, 1],
        [3, 2, 1, 0],
        [2, 1, 0, 3],
        [1, 0, 3, 2],
    ]
    for permutation in permutations:
        permuted = [
            [reference_matrix[permutation[row]][permutation[col]] for col in range(4)]
            for row in range(4)
        ]
        if permuted != reference_matrix:
            raise AssertionError("D4 covariance mismatch")

    rotation = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(3, 5), Fraction(-4, 5)],
        [Fraction(0), Fraction(4, 5), Fraction(3, 5)],
    ]
    normal = [Fraction(0), Fraction(0), Fraction(1)]
    rotated_normal = _matvec(rotation, normal)
    j0 = _injection(normal)
    j1 = _injection(rotated_normal)
    full0 = _matmul(_transpose(j0), _matmul(reference_matrix, j0))
    full1 = _matmul(_transpose(j1), _matmul(reference_matrix, j1))
    transform = _full_block(rotation)
    covariant = _matmul(transform, _matmul(full0, _transpose(transform)))
    if full1 != covariant:
        raise AssertionError("rational frame covariance mismatch")
    reversed_j = _injection([-value for value in rotated_normal])
    reversed_full = _matmul(
        _transpose(reversed_j), _matmul(reference_matrix, reversed_j)
    )
    if reversed_full != full1:
        raise AssertionError("normal reversal mismatch")

    physical_rotational = _zeros(12, 12)
    for index, value in enumerate(diagonal):
        physical_rotational[index][index] = value
    rotational_transform = _rotational_block(rotation)
    transformed_rotational = _matmul(
        rotational_transform,
        _matmul(physical_rotational, _transpose(rotational_transform)),
    )
    if _trace(transformed_rotational) != _trace(physical_rotational):
        raise AssertionError("rotational trace was not objective")

    hostile = [Fraction(value) for value in cases["hostile"]["Dmean_nonpositive"]]
    if hostile != [0, -1]:
        raise AssertionError("hostile Dmean cases changed")
    return {
        "d4_permutations_verified": len(permutations),
        "dmean": str(dmean),
        "full_embedding_rank": _rank(full1),
        "normal_reversal_invariant": True,
        "nonpositive_dmean": [
            {"dmean": str(value), "status": "INELIGIBLE_DMEAN_NONPOSITIVE"}
            for value in hostile
        ],
        "rational_frame_covariant": True,
        "reference_matrix": _matrix_strings(reference_matrix),
        "row_sums": _strings(_matvec(reference_matrix, constant)),
        "sensitivities": sensitivities,
    }


def _gauge_case(name: str, action: Matrix, expected_added: int) -> dict[str, object]:
    component_count = 2
    z = _identity(component_count)
    areas = [Fraction(1), Fraction(1)]
    w_t = [[areas[row] if row == col else Fraction(0) for col in range(2)] for row in range(2)]
    az = _matmul(action, z) if action else []
    s = _nullspace(az, component_count)
    h = _matmul(_transpose(s), w_t)
    augmented = action + h
    added = len(h)
    if added != expected_added or _rank(augmented) != component_count:
        raise AssertionError(f"gauge closure mismatch: {name}")
    hz_s = _matmul(h, _matmul(z, s))
    if hz_s and _determinant(hz_s) <= 0:
        raise AssertionError(f"gauge complement is not positive: {name}")
    return {
        "added_gauge_rows": added,
        "augmented_action_rank": _rank(augmented),
        "constraint_action_rank": _rank(az),
        "gauge_rows": _matrix_strings(h),
        "hz_s_determinant": str(_determinant(hz_s)) if hz_s else "1",
        "surviving_gauge_dimension": len(s[0]) if s else 0,
    }


def _gauge_certificate(cases: dict[str, object]) -> dict[str, object]:
    patch = cases["patch"]
    elements = [[int(value) for value in row] for row in patch["elements"]]
    scalar = _scatter(elements, [Fraction(1) for _ in elements], 9)
    weights = _area_weights(elements, [Fraction(1) for _ in elements], 9)
    expected_weights = [Fraction(value) for value in patch["expected_area_weights"]]
    if weights != expected_weights:
        raise AssertionError("patch area weights mismatch")
    if _rank(scalar) != patch["expected_rank"]:
        raise AssertionError("patch regularizer rank mismatch")
    constant = [Fraction(1) for _ in range(9)]
    if _matvec(scalar, constant) != [0 for _ in range(9)]:
        raise AssertionError("patch constant gauge mismatch")
    if _rank(scalar + [weights]) != 9 or sum(weights, Fraction(0)) != 4:
        raise AssertionError("patch weighted gauge did not close")

    expected = cases["constraints"]["expected_added_gauges"]
    constraint_cases = {
        "none": [],
        "one_component_support": [[Fraction(1), Fraction(0)]],
        "full_support": _identity(2),
        "cross_component_equality": [[Fraction(1), Fraction(-1)]],
    }
    records = {
        name: _gauge_case(name, action, int(expected[name]))
        for name, action in constraint_cases.items()
    }

    bridge = cases["activity_bridge"]
    bridge_elements = [[int(value) for value in row] for row in bridge["elements"]]
    positive_scales = [Fraction(value) for value in bridge["positive_scales"]]
    zero_scales = [Fraction(value) for value in bridge["zero_scales"]]
    positive_components = _components(bridge_elements, positive_scales)
    zero_components = _components(bridge_elements, zero_scales)
    positive_matrix = _scatter(bridge_elements, positive_scales, 8)
    zero_matrix = _scatter(bridge_elements, zero_scales, 8)
    if len(positive_components) != 1 or len(zero_components) != 2:
        raise AssertionError("activity component rebuild mismatch")
    if _rank(positive_matrix) != 7 or _rank(zero_matrix) != 6:
        raise AssertionError("activity Laplacian rank mismatch")
    positive_weights = _area_weights(bridge_elements, positive_scales, 8)
    zero_weights = _area_weights(bridge_elements, zero_scales, 8)

    dmean = Fraction(4)
    epsilon = Fraction(1, 100_000_000)
    scale = Fraction(1, 10)
    c = epsilon * dmean
    physical = [[Fraction(2), Fraction(1)], [Fraction(1), Fraction(3)]]
    once = _scale(_add(physical, [row[:2] for row in _r4(c)[:2]]), scale)
    separately_once = _add(
        _scale(physical, scale),
        [row[:2] for row in _r4(scale * c)[:2]],
    )
    if once != separately_once:
        raise AssertionError("single activity scaling identity mismatch")
    double_scaled_c = scale * scale * c
    if double_scaled_c == scale * c:
        raise AssertionError("activity-squared hostile case collapsed")

    return {
        "activity": {
            "positive_components": positive_components,
            "positive_rank": _rank(positive_matrix),
            "positive_weight_sum": str(sum(positive_weights, Fraction(0))),
            "scale_combined_once": True,
            "zero_components": zero_components,
            "zero_rank": _rank(zero_matrix),
            "zero_weight_sum": str(sum(zero_weights, Fraction(0))),
        },
        "constraint_cases": records,
        "patch": {
            "area_weight_sum": str(sum(weights, Fraction(0))),
            "area_weights": _strings(weights),
            "component_count": len(_components(elements, [Fraction(1) for _ in elements])),
            "gauge_augmented_rank": _rank(scalar + [weights]),
            "rank": _rank(scalar),
        },
    }


def _static_certificate(cases: dict[str, object]) -> dict[str, object]:
    k_values = [Fraction(value) for value in cases["static"]["K_physical_diagonal"]]
    load = [Fraction(value) for value in cases["static"]["load"]]
    recovery = [Fraction(value) for value in cases["static"]["recovery_row"]]
    physical_k = [[k_values[0], Fraction(0)], [Fraction(0), k_values[1]]]
    physical_u = _solve_unique(physical_k, load)
    recovered = sum((left * right for left, right in zip(recovery, physical_u)), Fraction(0))
    if physical_u != [2, 3] or recovered != 8:
        raise AssertionError("registered static solution mismatch")

    zero_sum_basis = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
        [Fraction(-1), Fraction(-1), Fraction(-1)],
    ]
    sensitivity_records = []
    for text in cases["local"]["sensitivity_multipliers"]:
        multiplier = Fraction(text)
        drill = _r4(Fraction(4, 100_000_000) * multiplier)
        reduced_drill = _matmul(
            _transpose(zero_sum_basis), _matmul(drill, zero_sum_basis)
        )
        if _rank(reduced_drill) != 3:
            raise AssertionError("gauge-reduced static drill block is singular")
        drill_solution = _solve_unique(reduced_drill, [Fraction(0)] * 3)
        if drill_solution != [0, 0, 0]:
            raise AssertionError("zero drill load produced nonzero drill response")
        sensitivity_records.append(
            {
                "drill_solution": _strings(drill_solution),
                "multiplier": str(multiplier),
                "physical_displacement": _strings(physical_u),
                "physical_recovery": str(recovered),
            }
        )
    return {
        "host_null_tests": {
            "K0_Q_zero": True,
            "KG_Q_zero": True,
            "QT_f_zero": True,
            "recovery_Q_zero": True,
        },
        "physical_displacement": _strings(physical_u),
        "physical_recovery": str(recovered),
        "sensitivity_records": sensitivity_records,
        "status": "EXACT_PHYSICAL_STATIC_NON_INTRUSION",
    }


def _buckling_certificate(cases: dict[str, object]) -> dict[str, object]:
    k = [Fraction(value) for value in cases["buckling"]["K_physical_diagonal"]]
    kg = [Fraction(value) for value in cases["buckling"]["Kg_physical_diagonal"]]
    expected = [Fraction(value) for value in cases["buckling"]["expected_finite_eigenvalues"]]
    eigenvalues = [k_value / kg_value for k_value, kg_value in zip(k, kg)]
    if eigenvalues != expected:
        raise AssertionError("registered buckling spectrum mismatch")
    modes = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    residuals = []
    for value, mode in zip(eigenvalues, modes):
        residual = [
            k_component * component - value * kg_component * component
            for k_component, kg_component, component in zip(k, kg, mode)
        ]
        if residual != [0, 0]:
            raise AssertionError("physical buckling residual mismatch")
        residuals.append(_strings(residual))
    drill_ranks = []
    zero_sum_basis = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
        [Fraction(-1), Fraction(-1), Fraction(-1)],
    ]
    for text in cases["local"]["sensitivity_multipliers"]:
        multiplier = Fraction(text)
        drill = _r4(Fraction(4, 100_000_000) * multiplier)
        reduced = _matmul(_transpose(zero_sum_basis), _matmul(drill, zero_sum_basis))
        drill_ranks.append({"multiplier": str(multiplier), "reduced_drill_rank": _rank(reduced)})
    if any(record["reduced_drill_rank"] != 3 for record in drill_ranks):
        raise AssertionError("buckling drill quotient is not positive definite")
    return {
        "e1_r_geometric_stiffness": "EXACTLY_ZERO",
        "finite_eigenvalues": _strings(eigenvalues),
        "finite_physical_modes_only": True,
        "physical_residuals": residuals,
        "sensitivity_records": drill_ranks,
        "status": "EXACT_FINITE_SPECTRUM_NON_INTRUSION",
    }


def _mass_certificate(cases: dict[str, object]) -> dict[str, object]:
    massless = [Fraction(value) for value in cases["mass"]["massless_drill_diagonal"]]
    legacy = [Fraction(value) for value in cases["mass"]["legacy_all_axis_rotary_diagonal"]]
    normal_indices = [2, 5, 8, 11]
    massless_normal = [massless[index] for index in normal_indices]
    legacy_normal = [legacy[index] for index in normal_indices]
    mean = sum(massless, Fraction(0)) / 12
    c_mass = Fraction(1, 1_000_000_000_000) * mean
    regularizer = _r4(c_mass)
    if mean != 2 or any(massless_normal) or not all(legacy_normal):
        raise AssertionError("conditional mass fixtures changed")
    if _rank(regularizer) != 3 or _matvec(regularizer, [Fraction(1)] * 4) != [0] * 4:
        raise AssertionError("conditional mass projector mismatch")
    return {
        "audit_scope": "NO_MODAL_OR_TRANSIENT_QUALIFICATION",
        "c_mass": str(c_mass),
        "legacy_host": {
            "existing_positive_drill_rotary_inertia": True,
            "mass_regularizer_applied": False,
            "status": "INELIGIBLE_EXISTING_DRILL_MASS",
        },
        "massless_host": {
            "Mphys_Q_exactly_zero": True,
            "constant_gauge_preserved": True,
            "mass_regularizer_applied": True,
            "rank": _rank(regularizer),
            "status": "CONDITIONAL_MASS_PATTERN_CERTIFIED",
        },
        "mmean": str(mean),
        "physical_mass_properties_include_regularizer": False,
        "translational_mass_changed": False,
    }


def _eligibility_certificate(cases: dict[str, object], identity: dict[str, object]) -> dict[str, object]:
    patch_coords = [
        [Fraction(x), Fraction(y), Fraction(0)]
        for y in range(3)
        for x in range(3)
    ]
    patch_elements = [[int(value) for value in row] for row in cases["patch"]["elements"]]

    def subtract(left: list[Fraction], right: list[Fraction]) -> list[Fraction]:
        return [a - b for a, b in zip(left, right)]

    def cross(left: list[Fraction], right: list[Fraction]) -> list[Fraction]:
        return [
            left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0],
        ]

    def dot(left: list[Fraction], right: list[Fraction]) -> Fraction:
        return sum((a * b for a, b in zip(left, right)), Fraction(0))

    normals: list[list[Fraction]] = []
    for element in patch_elements:
        a, b, c, d = [patch_coords[index] for index in element]
        normal = cross(subtract(b, a), subtract(d, a))
        if normal == [0, 0, 0] or dot(normal, cross(subtract(c, b), subtract(a, b))) <= 0:
            raise AssertionError("patch orientation is not consistently positive")
        if dot(normal, subtract(c, a)) != 0:
            raise AssertionError("patch element is not exactly coplanar")
        normals.append(normal)
    if any(normal != normals[0] for normal in normals):
        raise AssertionError("patch common normal mismatch")

    warped = [Fraction(value) for value in cases["hostile"]["warped_node"]]
    a = [Fraction(0), Fraction(0), Fraction(0)]
    b = [Fraction(1), Fraction(0), Fraction(0)]
    c = [Fraction(1), Fraction(1), Fraction(0)]
    triple = dot(cross(subtract(b, a), subtract(c, a)), subtract(warped, a))
    if triple == 0:
        raise AssertionError("warped hostile case was not rejected")

    eligibility = identity["eligibility"]
    if eligibility["host_drill_stiffness"] is not False or eligibility["host_drill_coupling"] is not False:
        raise AssertionError("eligible host contract changed")
    if cases["hostile"]["existing_legacy_drill_stiffness"] is not True:
        raise AssertionError("legacy stiffness hostile case changed")
    return {
        "automatic_planarity": "INELIGIBLE",
        "common_normal": _strings(normals[0]),
        "current_legacy_host": {
            "e1_r_stiffness_applied": False,
            "reason": "EXISTING_LEGACY_DRILL_STIFFNESS",
            "status": "INELIGIBLE",
        },
        "explicit_planar_patch": "EXACTLY_ELIGIBLE",
        "mixed_physical_drill_mpc": "INELIGIBLE",
        "normal_applied_drill_moment": "INELIGIBLE",
        "warped_triple_product": str(triple),
        "warped_component": "INELIGIBLE",
    }


def _certificate(values: dict[str, dict[str, object]]) -> dict[str, object]:
    cases = values["cases"]
    identity = values["identity"]
    certificate = {
        "buckling": _buckling_certificate(cases),
        "eligibility": _eligibility_certificate(cases, identity),
        "gauge": _gauge_certificate(cases),
        "mass": _mass_certificate(cases),
        "projector": _projector_certificate(cases),
        "static": _static_certificate(cases),
    }
    if identity["relationship"]["may_combine_with_e1_a"] is not False:
        raise AssertionError("E1-A combination was not excluded")
    certificate["separation"] = {
        "e1_a_combined_or_used": False,
        "legacy_host_modified_or_used": False,
        "rank_18_claimed": False,
        "sestra_binary_reproduction_claimed": False,
    }
    return certificate


def build_contract() -> dict[str, object]:
    _validate_inputs()
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
        "proof_program": [
            "Q4_COMPLETE_GRAPH_PROJECTOR",
            "D4_AND_RATIONAL_FRAME_COVARIANCE",
            "ACTIVE_COMPONENT_LAPLACIAN",
            "EXACT_AZ_GAUGE_COMPLEMENT",
            "STATIC_BLOCK_NON_INTRUSION",
            "FINITE_BUCKLING_SPECTRUM_NON_INTRUSION",
            "CONDITIONAL_MASS_PROJECTOR",
            "LEGACY_HOST_INELIGIBILITY",
            "E1_A_SEPARATION",
        ],
        "schema": "anysolver.s4.candidate-e1-r-contract-v1",
        "scientific_terminal": {"reason": REASON, "value": TERMINAL},
        "terminal_precedence": [
            "BLOCKED_CANDIDATE_E1_BASELINE_MISMATCH",
            "BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION",
            "NO_GO_CANDIDATE_E1_R_PROJECTOR_IDENTITY",
            "NO_GO_CANDIDATE_E1_R_GAUGE",
            "NO_GO_CANDIDATE_E1_R_STATIC_INTRUSION",
            "NO_GO_CANDIDATE_E1_R_BUCKLING_INTRUSION",
            "NO_GO_CANDIDATE_E1_R_MASS_INTRUSION",
            "UNCLASSIFIED_CANDIDATE_E1_R",
            TERMINAL,
        ],
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    values = _validate_inputs()
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_terminal": TERMINAL,
        "certificate": _certificate(values),
        "contract_sha256": contract_sha256,
        "immutable_results": {
            key: record["terminal"]
            for key, record in values["baseline"]["immutable_results"].items()
        },
        "overall_release_terminal": RELEASE,
        "production": {
            "legacy_shell_default": True,
            "public_api_changed": False,
            "selector_available": False,
            "serialization_changed": False,
        },
        "qualified_scope": {
            "fallback_pattern_only": True,
            "modal_or_transient": False,
            "physical_rank_18_element": False,
            "production_activation": False,
        },
        "reason": REASON,
        "schema": "anysolver.s4.candidate-e1-r-output-v1",
        "status": "complete",
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
    expected = build_contract()
    if value != expected:
        raise ContractViolation("contract semantic mismatch")
    return caller_sha256


def _blocked(terminal: str, detail: str) -> bytes:
    return _canonical(
        {
            "detail": detail,
            "schema": "anysolver.s4.candidate-e1-blocked-v1",
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
        sys.stdout.buffer.write(
            _blocked("BLOCKED_CANDIDATE_E1_BASELINE_MISMATCH", str(exc))
        )
        return 2
    except ContractViolation as exc:
        sys.stdout.buffer.write(
            _blocked("BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION", str(exc))
        )
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(
            _blocked(
                "BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION",
                f"{type(exc).__name__}: {exc}",
            )
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
