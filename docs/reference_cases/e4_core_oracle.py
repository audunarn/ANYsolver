"""Independent exact oracle for the source-exact E4 WG open core.

Only standard-library integer and rational algebra is used. The certificate
assembles the actual n=7, k=0 WG stress/strain spaces, compatible/MITC map,
mixed stationary block, and Schur complement. No generic Gram surrogate is
used to classify the core.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e4_core_cases.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/e4_core_contract.json"
STUDY_ID = "study_e4_core.wg2020_n7_k0_full_integration_reference_v1"
TERMINAL = "GO_E4_OPEN_CORE_IDENTITY"
BLOCKED = "BLOCKED_E4_CONTRACT_NONDETERMINISM_OR_REVIEW"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CONTRACT_INPUTS = [
    "docs/agent_plans/S4_E4_VARIATIONAL_DRILL_CLOSURE_PLAN.md",
    "docs/E4_OPEN_CORE_IDENTITY.md",
    "docs/reference_cases/e4_baseline.json",
    "docs/reference_cases/e4_environment.json",
    "docs/reference_cases/e4_test_inventory.json",
    "docs/reference_cases/e4_source_registry.json",
    "docs/reference_cases/e4_allowed_extent.json",
    "docs/reference_cases/e4_core_source_map.json",
    "docs/reference_cases/e4_core_cases.json",
]


class EvidenceError(Exception):
    """A frozen input or exact identity is invalid."""


class ContractError(Exception):
    """Caller-bound execution evidence is invalid."""


Matrix = list[list[Fraction]]
Vector = list[Fraction]
Monomial = tuple[int, int]
Polynomial = dict[Monomial, Fraction]
PolynomialMatrix = list[list[Polynomial]]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _load_json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise EvidenceError(f"invalid UTF-8/LF transport: {path}")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(EvidenceError(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise EvidenceError(f"noncanonical JSON: {path}")
    return value


def _fraction(value: object) -> Fraction:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise EvidenceError(f"not an exact scalar: {value!r}")
    return Fraction(value)


def _zeros(rows: int, columns: int) -> Matrix:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = Fraction(1)
    return result


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)] if matrix else []


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise EvidenceError("matrix product dimension mismatch")
    columns = _transpose(right)
    return [[sum(a * b for a, b in zip(row, column)) for column in columns] for row in left]


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    if matrix and len(matrix[0]) != len(vector):
        raise EvidenceError("matrix-vector dimension mismatch")
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def _add(left: Matrix, right: Matrix, scale: Fraction = Fraction(1)) -> Matrix:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise EvidenceError("matrix sum dimension mismatch")
    return [[a + scale * b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(left, right)]


def _scale(matrix: Matrix, factor: Fraction) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def _dot(left: Vector, right: Vector) -> Fraction:
    if len(left) != len(right):
        raise EvidenceError("dot-product dimension mismatch")
    return sum(a * b for a, b in zip(left, right))


def _rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    rows, columns = len(work), len(work[0])
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        value = work[rank][column]
        work[rank] = [entry / value for entry in work[rank]]
        for row in range(rows):
            if row != rank and work[row][column]:
                factor = work[row][column]
                work[row] = [a - factor * b for a, b in zip(work[row], work[rank])]
        rank += 1
    return rank


def _inverse(matrix: Matrix) -> Matrix:
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix):
        raise EvidenceError("inverse requires a nonempty square matrix")
    work = [row[:] + identity for row, identity in zip(matrix, _identity(size))]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise EvidenceError("singular exact matrix")
        work[column], work[pivot] = work[pivot], work[column]
        value = work[column][column]
        work[column] = [entry / value for entry in work[column]]
        for row in range(size):
            if row != column and work[row][column]:
                factor = work[row][column]
                work[row] = [a - factor * b for a, b in zip(work[row], work[column])]
    return [row[size:] for row in work]


def _inverse2(matrix: Matrix) -> Matrix:
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise EvidenceError("expected two-by-two matrix")
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if not determinant:
        raise EvidenceError("singular affine map")
    return [[matrix[1][1] / determinant, -matrix[0][1] / determinant],
            [-matrix[1][0] / determinant, matrix[0][0] / determinant]]


def _ldl_pivots(matrix: Matrix) -> Vector:
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix) or matrix != _transpose(matrix):
        raise EvidenceError("LDL requires a symmetric square matrix")
    lower = _identity(size)
    pivots: Vector = []
    for column in range(size):
        pivot = matrix[column][column] - sum(
            lower[column][k] * lower[column][k] * pivots[k] for k in range(column)
        )
        if not pivot:
            raise EvidenceError("zero exact LDL pivot")
        pivots.append(pivot)
        for row in range(column + 1, size):
            lower[row][column] = (
                matrix[row][column]
                - sum(lower[row][k] * lower[column][k] * pivots[k] for k in range(column))
            ) / pivot
    return pivots


def _poly(value: Fraction = Fraction(0), r_power: int = 0, s_power: int = 0) -> Polynomial:
    return {} if not value else {(r_power, s_power): value}


def _padd(*terms: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for term in terms:
        for monomial, value in term.items():
            result[monomial] = result.get(monomial, Fraction(0)) + value
            if not result[monomial]:
                del result[monomial]
    return result


def _pscale(term: Polynomial, factor: Fraction) -> Polynomial:
    return {monomial: factor * value for monomial, value in term.items() if factor * value}


def _pmultiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for (left_r, left_s), left_value in left.items():
        for (right_r, right_s), right_value in right.items():
            key = (left_r + right_r, left_s + right_s)
            result[key] = result.get(key, Fraction(0)) + left_value * right_value
    return {key: value for key, value in result.items() if value}


def _pintegral(term: Polynomial, determinant: Fraction) -> Fraction:
    result = Fraction(0)
    for (r_power, s_power), value in term.items():
        if r_power % 2 == 0 and s_power % 2 == 0:
            result += value * Fraction(4, (r_power + 1) * (s_power + 1))
    return abs(determinant) * result


def _pevaluate(term: Polynomial, r: Fraction, s: Fraction) -> Fraction:
    return sum(value * r**r_power * s**s_power for (r_power, s_power), value in term.items())


def _pzeros(rows: int, columns: int) -> PolynomialMatrix:
    return [[{} for _ in range(columns)] for _ in range(rows)]


def _transform_columns(target: PolynomialMatrix, row_offset: int, columns: list[int],
                       transform: Matrix, seeds: list[list[Polynomial]]) -> None:
    for local_column, global_column in enumerate(columns):
        for output_row, transform_row in enumerate(transform):
            target[row_offset + output_row][global_column] = _padd(*(
                _pscale(seeds[input_row][local_column], coefficient)
                for input_row, coefficient in enumerate(transform_row)
            ))


def _tensor_transform(j_map: Matrix, a: Fraction, b: Fraction) -> Matrix:
    x_r, x_s = j_map[0]
    y_r, y_s = j_map[1]
    return [[x_r*x_r, y_r*y_r, a*x_r*y_r],
            [x_s*x_s, y_s*y_s, a*x_s*y_s],
            [b*x_r*x_s, b*y_r*y_s, x_r*y_s+x_s*y_r]]


def _source_spaces(j_map: Matrix) -> tuple[PolynomialMatrix, PolynomialMatrix]:
    n_sigma, n_epsilon = _pzeros(8, 14), _pzeros(8, 21)
    for index in range(8):
        n_sigma[index][index] = _poly(Fraction(1))
        n_epsilon[index][index] = _poly(Fraction(1))
    r, s, rs = _poly(Fraction(1), 1, 0), _poly(Fraction(1), 0, 1), _poly(Fraction(1), 1, 1)
    tensor_seed = [[s, {}], [{}, r], [{}, {}]]
    vector_seed = [[s, {}], [{}, r]]
    for target, transform in ((n_sigma, _tensor_transform(j_map, Fraction(2), Fraction(1))),
                              (n_epsilon, _tensor_transform(j_map, Fraction(1), Fraction(2)))):
        _transform_columns(target, 0, [8, 9], transform, tensor_seed)
        _transform_columns(target, 3, [10, 11], transform, tensor_seed)
        _transform_columns(target, 6, [12, 13], j_map, vector_seed)
    enrichment_seed = [[r, {}, {}, {}, rs, {}, {}],
                       [{}, s, {}, {}, {}, rs, {}],
                       [{}, {}, r, s, {}, {}, rs]]
    _transform_columns(n_epsilon, 0, list(range(14, 21)),
                       _tensor_transform(j_map, Fraction(1), Fraction(2)), enrichment_seed)
    return n_sigma, n_epsilon


def _modal_coefficients(field: int) -> list[Vector]:
    signs = [[1,1,1,1],[-1,1,1,-1],[-1,-1,1,1],[1,-1,1,-1]]
    result: list[Vector] = []
    for row in signs:
        vector = [Fraction(0)] * 20
        for node, sign in enumerate(row):
            vector[5*node+field] = Fraction(sign, 4)
        result.append(vector)
    return result


def _linear_combination(vectors: list[Vector], coefficients: list[Polynomial]) -> list[Polynomial]:
    result = [{} for _ in vectors[0]]
    for vector, coefficient in zip(vectors, coefficients):
        for index, value in enumerate(vector):
            if value:
                result[index] = _padd(result[index], _pmultiply(coefficient, value))
    return result


def _vector_add(*vectors: list[Polynomial]) -> list[Polynomial]:
    return [_padd(*(vector[index] for vector in vectors)) for index in range(len(vectors[0]))]


def _vector_scale(vector: list[Polynomial], factor: Fraction) -> list[Polynomial]:
    return [_pscale(value, factor) for value in vector]


def _compatible_map(j_map: Matrix) -> PolynomialMatrix:
    modal = [
        [[_poly(value) for value in coefficient] for coefficient in _modal_coefficients(field)]
        for field in range(5)
    ]
    u0, ur, us, urs = modal[0]
    v0, vr, vs, vrs = modal[1]
    w0, wr, ws, wrs = modal[2]
    rx0, rxr, rxs, rxrs = modal[3]
    ry0, ryr, rys, ryrs = modal[4]
    del u0, v0, w0
    r, s = _poly(Fraction(1), 1, 0), _poly(Fraction(1), 0, 1)
    u_r = _vector_add(ur, _linear_combination([urs], [s]))
    u_s = _vector_add(us, _linear_combination([urs], [r]))
    v_r = _vector_add(vr, _linear_combination([vrs], [s]))
    v_s = _vector_add(vs, _linear_combination([vrs], [r]))
    rx_r = _vector_add(rxr, _linear_combination([rxrs], [s]))
    rx_s = _vector_add(rxs, _linear_combination([rxrs], [r]))
    ry_r = _vector_add(ryr, _linear_combination([ryrs], [s]))
    ry_s = _vector_add(rys, _linear_combination([ryrs], [r]))
    inverse = _inverse2(j_map)

    def physical(natural_r: list[Polynomial], natural_s: list[Polynomial]) -> tuple[list[Polynomial], list[Polynomial]]:
        return (_vector_add(_vector_scale(natural_r, inverse[0][0]),
                            _vector_scale(natural_s, inverse[1][0])),
                _vector_add(_vector_scale(natural_r, inverse[0][1]),
                            _vector_scale(natural_s, inverse[1][1])))

    u_x, u_y = physical(u_r, u_s)
    v_x, v_y = physical(v_r, v_s)
    rx_x, rx_y = physical(rx_r, rx_s)
    ry_x, ry_y = physical(ry_r, ry_s)
    x_r, x_s = j_map[0]
    y_r, y_s = j_map[1]
    tied_r = _vector_add(wr, _linear_combination([wrs], [s]),
                         _vector_scale(_vector_add(ry0, _linear_combination([rys], [s])), x_r),
                         _vector_scale(_vector_add(rx0, _linear_combination([rxs], [s])), -y_r))
    tied_s = _vector_add(ws, _linear_combination([wrs], [r]),
                         _vector_scale(_vector_add(ry0, _linear_combination([ryr], [r])), x_s),
                         _vector_scale(_vector_add(rx0, _linear_combination([rxr], [r])), -y_s))
    gamma_x, gamma_y = physical(tied_r, tied_s)
    return [u_x, v_y, _vector_add(u_y, v_x), ry_x, _vector_scale(rx_y, Fraction(-1)),
            _vector_add(ry_y, _vector_scale(rx_x, Fraction(-1))), gamma_x, gamma_y]


def _assemble_core(record: dict[str, object], constitutive: Matrix) -> dict[str, object]:
    j_map = [[_fraction(value) for value in row] for row in record["j_map"]]
    determinant = j_map[0][0]*j_map[1][1]-j_map[0][1]*j_map[1][0]
    if determinant != _fraction(record["det_j_map"]):
        raise EvidenceError(f"affine determinant mismatch: {record['id']}")
    n_sigma, n_epsilon = _source_spaces(j_map)
    b_map = _compatible_map(j_map)
    f, h, gq = _zeros(21, 14), _zeros(21, 21), _zeros(14, 20)
    for strain_parameter in range(21):
        for stress_parameter in range(14):
            f[strain_parameter][stress_parameter] = -sum(
                _pintegral(_pmultiply(n_epsilon[component][strain_parameter],
                                      n_sigma[component][stress_parameter]), determinant)
                for component in range(8))
        for other_parameter in range(21):
            h[strain_parameter][other_parameter] = sum(
                constitutive[left][right] * _pintegral(
                    _pmultiply(n_epsilon[left][strain_parameter], n_epsilon[right][other_parameter]), determinant)
                for left in range(8) for right in range(8) if constitutive[left][right])
    for stress_parameter in range(14):
        for coordinate in range(20):
            gq[stress_parameter][coordinate] = sum(
                _pintegral(_pmultiply(n_sigma[component][stress_parameter],
                                      b_map[component][coordinate]), determinant)
                for component in range(8))
    d = _zeros(35, 35)
    for stress in range(14):
        for strain in range(21):
            d[stress][14+strain] = d[14+strain][stress] = f[strain][stress]
    for left in range(21):
        for right in range(21):
            d[14+left][14+right] = h[left][right]
    d_inverse = _inverse(d)
    s_matrix = _scale([row[:14] for row in d_inverse[:14]], Fraction(-1))
    coupling = [row + [Fraction(0)]*21 for row in _transpose(gq)]
    k5 = _scale(_multiply(_multiply(coupling, d_inverse), _transpose(coupling)), Fraction(-1))
    coefficient_rows: Matrix = []
    for component in b_map:
        for monomial in sorted({monomial for entry in component for monomial in entry}):
            coefficient_rows.append([entry.get(monomial, Fraction(0)) for entry in component])
    return {"B": b_map, "B_coefficient_rows": coefficient_rows, "D": d,
            "D_inverse": d_inverse, "F": f, "Gq": gq, "H": h, "K5": k5,
            "N_epsilon": n_epsilon, "N_sigma": n_sigma, "Q": coupling, "S": s_matrix}


def _selectors() -> tuple[Matrix, Matrix]:
    t5, qd = _zeros(24, 20), _zeros(24, 4)
    for node in range(4):
        for local in range(5):
            t5[6*node+local][5*node+local] = Fraction(1)
        qd[6*node+5][node] = Fraction(1)
    return t5, qd


def _physical_nodes(record: dict[str, object]) -> list[list[Fraction]]:
    nodes = record.get("physical_nodes")
    if not isinstance(nodes, list) or len(nodes) != 4 or any(not isinstance(node, list) for node in nodes):
        raise EvidenceError("physical-node registry missing")
    return [[_fraction(value) for value in node] for node in nodes]


def _rigid_vectors(nodes: list[list[Fraction]]) -> dict[str, Vector]:
    result = {name: [] for name in ("translation_x", "translation_y", "translation_z",
                                     "rotation_x", "rotation_y", "rotation_z")}
    for x, y in nodes:
        result["translation_x"].extend((1,0,0,0,0))
        result["translation_y"].extend((0,1,0,0,0))
        result["translation_z"].extend((0,0,1,0,0))
        result["rotation_x"].extend((0,0,y,1,0))
        result["rotation_y"].extend((0,0,-x,0,1))
        result["rotation_z"].extend((-y,x,0,0,0))
    return {name: [Fraction(value) for value in vector] for name, vector in result.items()}


def _signature(vector: Vector) -> list[str]:
    return [str(value) for value in vector]


def _matrix_signature(matrix: Matrix) -> list[list[str]]:
    return [_signature(row) for row in matrix]


def _matrix_digest(matrix: Matrix) -> dict[str, object]:
    raw = _canonical(_matrix_signature(matrix))
    return {"bytes": len(raw), "nonzeros": sum(bool(value) for row in matrix for value in row),
            "sha256": _sha(raw), "shape": [len(matrix), len(matrix[0]) if matrix else 0]}


def _validate_cases(cases: dict[str, object]) -> None:
    if cases.get("schema") != "anysolver.e4.core-cases-v2" or cases.get("study_id") != STUDY_ID:
        raise EvidenceError("core case identity mismatch")
    if cases.get("dimensions") != {"core_internal":35,"external":24,"physical":20,
                                     "strain_parameters":21,"stress_parameters":14}:
        raise EvidenceError("core dimensions changed")
    expected = cases.get("expected")
    if not isinstance(expected, dict) or expected.get("terminal") != TERMINAL:
        raise EvidenceError("core expected terminal mismatch")
    affine = cases.get("affine_cases")
    if not isinstance(affine, list) or [row.get("id") for row in affine if isinstance(row, dict)] != [
        "source_exact_normalized_square", "rational_affine"]:
        raise EvidenceError("affine-case registry mismatch")
    source = cases.get("source_exact_operator")
    if not isinstance(source, dict) or source.get("matrices", {}).get("D") != "[[0_14x14,F^T],[F,H]]":
        raise EvidenceError("source-exact mixed block changed")


def build_certificate() -> dict[str, object]:
    cases = _load_json(CASES_PATH)
    _validate_cases(cases)
    constitutive = [[_fraction(value) for value in row] for row in cases["constitutive"]["resultant_matrix"]]
    if constitutive != _transpose(constitutive) or any(pivot <= 0 for pivot in _ldl_pivots(constitutive)):
        raise EvidenceError("registered isotropic resultant matrix is not SPD")
    t5, qd = _selectors()
    t5_t, qd_t = _transpose(t5), _transpose(qd)
    selector_checks = {"QD_T_QD_I4": _multiply(qd_t, qd) == _identity(4),
                       "T5_T_QD_zero": _multiply(t5_t, qd) == _zeros(20,4),
                       "T5_T_T5_I20": _multiply(t5_t, t5) == _identity(20),
                       "complete_I24": _add(_multiply(t5,t5_t), _multiply(qd,qd_t)) == _identity(24)}
    if not all(selector_checks.values()):
        raise EvidenceError("coordinate-split identity failed")
    geometry_results: dict[str, object] = {}
    square_data: dict[str, object] | None = None
    for raw_record in cases["affine_cases"]:
        if not isinstance(raw_record, dict):
            raise EvidenceError("malformed affine case")
        data = _assemble_core(raw_record, constitutive)
        f,h,gq,d,s_matrix,k5 = (data[name] for name in ("F","H","Gq","D","S","K5"))
        ranks = {"D":_rank(d),"F":_rank(f),"Gq":_rank(gq),"H":_rank(h),"K5":_rank(k5)}
        if ranks != {"D":35,"F":14,"Gq":14,"H":21,"K5":14}:
            raise EvidenceError(f"source-exact rank failure: {raw_record['id']}")
        if k5 != _transpose(k5) or any(pivot <= 0 for pivot in _ldl_pivots(s_matrix)):
            raise EvidenceError(f"source-exact PSD factor failure: {raw_record['id']}")
        b_rows = data["B_coefficient_rows"]
        row_equivalence = _rank(b_rows) == 14 and _rank(gq+b_rows) == 14
        if not row_equivalence:
            raise EvidenceError(f"Gq/B row-equivalence failure: {raw_record['id']}")
        rigid = _rigid_vectors(_physical_nodes(raw_record))
        rigid_images = {name:_matvec(k5,vector) for name,vector in rigid.items()}
        if _rank([rigid[name] for name in sorted(rigid)]) != 6 or any(any(image) for image in rigid_images.values()):
            raise EvidenceError(f"source-exact rigid-nullspace failure: {raw_record['id']}")
        geometry_results[str(raw_record["id"])] = {
            "B_polynomial_rank":_rank(b_rows), "Gq_B_row_equivalent":row_equivalence,
            "S_ldl_positive":all(pivot>0 for pivot in _ldl_pivots(s_matrix)),
            "mixed_block_rank":ranks["D"], "nullity":20-ranks["K5"], "ranks":ranks,
            "rigid_images_zero":{name:not any(image) for name,image in rigid_images.items()}}
        if raw_record["id"] == "source_exact_normalized_square":
            square_data = data
            registered = cases.get("rigid_vectors_20")
            if not isinstance(registered, dict):
                raise EvidenceError("registered rigid vectors missing")
            for name, vector in rigid.items():
                if [_fraction(value) for value in registered[name]] != vector:
                    raise EvidenceError(f"registered rigid vector mismatch: {name}")
    if square_data is None:
        raise EvidenceError("source-exact normalized square missing")
    expected_signatures = cases["source_exact_operator"]["square_matrix_signatures"]
    observed_signatures = {name:_matrix_digest(square_data[name]) for name in ("F","H","Gq","D","S","K5")}
    if any(observed_signatures[name] != expected_signatures[name] for name in observed_signatures):
        raise EvidenceError("source-exact normalized-square matrix signature mismatch")
    s_pivots = _ldl_pivots(square_data["S"])
    if s_pivots != [_fraction(value) for value in cases["source_exact_operator"]["square_S_ldl_pivots"]]:
        raise EvidenceError("source-exact S LDL certificate mismatch")
    q = [Fraction(index+1) for index in range(20)]
    d,d_inverse,coupling,k5 = (square_data[name] for name in ("D","D_inverse","Q","K5"))
    z = _scale([_matvec(d_inverse, _matvec(_transpose(coupling), q))], Fraction(-1))[0]
    internal_residual = _add([_matvec(_transpose(coupling),q)], [_matvec(d,z)])[0]
    mixed_residual, condensed_residual = _matvec(coupling,z), _matvec(k5,q)
    mixed_energy = _dot(z,_matvec(d,z))/2 + _dot(q,mixed_residual)
    condensed_energy = _dot(q,condensed_residual)/2
    if any(internal_residual) or mixed_residual != condensed_residual or mixed_energy != condensed_energy:
        raise EvidenceError("actual WG stationary mixed/condensed parity failed")
    k24 = _multiply(_multiply(t5,k5),t5_t)
    if _rank(k24) != 14 or any(any(row) for row in _multiply(k24,qd)):
        raise EvidenceError("24-coordinate source-exact embedding failed")
    q24 = _matvec(t5,q)
    f5 = [Fraction(2*index-7) for index in range(20)]
    f24 = _matvec(t5,f5)
    if _dot(f5,q) != _dot(f24,q24) or any(_matvec(qd_t,f24)):
        raise EvidenceError("physical source-exact load-work embedding failed")
    evaluated = [[_pevaluate(entry,Fraction(1,3),Fraction(-1,4)) for entry in row]
                 for row in square_data["N_sigma"]]
    recovery_5 = _matvec(evaluated,z[:14])
    q_from_24 = _matvec(t5_t,q24)
    z_from_24 = _scale([_matvec(d_inverse,_matvec(_transpose(coupling),q_from_24))],Fraction(-1))[0]
    recovery_24 = _matvec(evaluated,z_from_24[:14])
    if recovery_5 != recovery_24:
        raise EvidenceError("stationary physical-resultant recovery parity failed")
    return {
        "coordinate_split":selector_checks,
        "dimensions":{"core_internal":35,"external":24,"physical":20},
        "embedding":{"direct_drill_load_projection":_signature(_matvec(qd_t,f24)),
                     "embedded_nullity":24-_rank(k24),"embedded_rank":_rank(k24),
                     "physical_load_work":str(_dot(f24,q24)),
                     "physical_load_work_parity":_dot(f5,q)==_dot(f24,q24),
                     "recovery_parity":recovery_5==recovery_24},
        "geometries":geometry_results,
        "mixed_condensed":{"condensed_energy":str(condensed_energy),"energy_parity":mixed_energy==condensed_energy,
                           "internal_block_dimension":len(z),"internal_block_invertible":_rank(d)==35,
                           "internal_stationarity":not any(internal_residual),"residual_parity":mixed_residual==condensed_residual,
                           "tangent_parity":k5==_scale(_multiply(_multiply(coupling,d_inverse),_transpose(coupling)),Fraction(-1)),
                           "virtual_work_parity":mixed_residual==condensed_residual},
        "normalized_square":{"S_ldl_pivots":_signature(s_pivots),"matrix_signatures":observed_signatures},
        "scope":{"core_classification_operator":"SOURCE_EXACT_WG_F_G_H_D_S_K5",
                 "direct_drill_moments":"EXCLUDED","generic_I35_surrogate":"FORBIDDEN_NOT_USED",
                 "mass":"DEFERRED_NOT_RUN","nonlinear_and_buckling":"DEFERRED_NOT_RUN"},
        "study_id":STUDY_ID,"terminal":TERMINAL}


def build_contract() -> dict[str, object]:
    build_certificate()
    identities: dict[str, object] = {}
    for relative in CONTRACT_INPUTS:
        raw = (ROOT/relative).read_bytes()
        identities[relative] = {"bytes":len(raw),"path":relative,"sha256":_sha(raw)}
    oracle_path = Path(__file__).relative_to(ROOT).as_posix()
    oracle_raw = Path(__file__).read_bytes()
    identities[oracle_path] = {"bytes":len(oracle_raw),"path":oracle_path,"sha256":_sha(oracle_raw)}
    return {"input_identities":identities,"production_paths":[],
            "proof_program":["EXACT_20_TO_24_ORTHOGONAL_SPLIT","SOURCE_EXACT_WG_F_G_H_D_ASSEMBLY",
                             "SOURCE_EXACT_S_POSITIVE_K5_RANK14","ACTUAL_35_FIELD_STATIONARY_SCHUR_PARITY",
                             "PHYSICAL_LOAD_WORK_AND_RECOVERY_EMBEDDING"],
            "schema":"anysolver.s4.e4-core-contract-v2","scientific_terminal":TERMINAL,"study_id":STUDY_ID}


def build_output(contract_sha256: str) -> dict[str, object]:
    return {"certificate":build_certificate(),"contract_sha256":contract_sha256,
            "overall_release_terminal":RELEASE,"production_changed":False,
            "schema":"anysolver.s4.e4-core-output-v2","status":"go","study_id":STUDY_ID,"terminal":TERMINAL}


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractError("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractError("contract raw hash mismatch")
        value = json.loads(raw.decode("utf-8"),object_pairs_hook=_pairs,
                           parse_constant=lambda token:(_ for _ in ()).throw(ContractError(token)))
        if not isinstance(value,dict) or raw != _canonical(value):
            raise ContractError("contract is not canonical")
        if value != build_contract():
            raise ContractError("contract semantic mismatch")
    except ContractError:
        raise
    except (OSError,UnicodeDecodeError,json.JSONDecodeError,EvidenceError) as exc:
        raise ContractError(str(exc)) from exc
    return caller_sha256


def _blocked(detail: str) -> bytes:
    return _canonical({"detail":detail,"status":"blocked","terminal":BLOCKED})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--certificate",action="store_true")
    modes.add_argument("--emit-contract",action="store_true")
    modes.add_argument("--run",action="store_true")
    parser.add_argument("--contract",type=Path)
    parser.add_argument("--contract-sha256")
    arguments = parser.parse_args(argv)
    try:
        if arguments.certificate:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in certificate mode")
            sys.stdout.buffer.write(_canonical(build_certificate()))
            return 0
        if arguments.emit_contract:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in emit mode")
            sys.stdout.buffer.write(_canonical(build_contract()))
            return 0
        if arguments.contract is None or arguments.contract_sha256 is None:
            raise ContractError("run mode requires caller-bound contract")
        contract_sha = _load_contract(arguments.contract,arguments.contract_sha256)
        sys.stdout.buffer.write(_canonical(build_output(contract_sha)))
        return 0
    except (EvidenceError,ContractError,OSError,AssertionError,ValueError) as exc:
        sys.stdout.buffer.write(_blocked(str(exc)))
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(_blocked(f"{type(exc).__name__}: {exc}"))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
