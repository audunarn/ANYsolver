"""Independently authored exact checker for the bounded V3A MiSP3 screen."""

from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v3a_implementation_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V3A_MISP3_HR_FLAT_LINEAR_V1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v3a-implementation-screen-check-v1"
Matrix = list[list[F]]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key!r}")
        value[key] = item
    return value


def load_document(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    if raw != canonical_bytes(value):
        raise ValueError("proof is not canonical JSON")
    return value


def _decode(payload: Mapping[str, Any]) -> np.ndarray:
    values = list(payload["values_hex"])
    if sha256_bytes(canonical_bytes(values)) != payload["sha256"]:
        raise ValueError("array payload hash mismatch")
    return np.asarray([float.fromhex(str(item)) for item in values], dtype=np.float64).reshape(tuple(int(item) for item in payload["shape"]))


def _zeros(rows: int, columns: int) -> Matrix:
    return [[F(0) for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    made = _zeros(size, size)
    for index in range(size):
        made[index][index] = F(1)
    return made


def _transpose(value: Matrix) -> Matrix:
    return [list(row) for row in zip(*value)]


def _add(left: Matrix, right: Matrix) -> Matrix:
    return [[left[i][j] + right[i][j] for j in range(len(left[0]))] for i in range(len(left))]


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    right_t = _transpose(right)
    return [[sum((a * b for a, b in zip(row, column)), F(0)) for column in right_t] for row in left]


def _scale(value: Matrix, factor: F) -> Matrix:
    return [[factor * item for item in row] for row in value]


def _inverse(value: Matrix) -> Matrix:
    size = len(value)
    work = [list(row) + identity for row, identity in zip(value, _identity(size))]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise ValueError("exact matrix is singular")
        work[column], work[pivot] = work[pivot], work[column]
        divisor = work[column][column]
        work[column] = [item / divisor for item in work[column]]
        for row in range(size):
            if row == column or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [item - factor * selected for item, selected in zip(work[row], work[column])]
    return [row[size:] for row in work]


def _rank(value: Matrix) -> int:
    if not value:
        return 0
    work = [list(row) for row in value]
    rows, columns = len(work), len(work[0])
    pivot_row = 0
    for column in range(columns):
        pivot = next((row for row in range(pivot_row, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        divisor = work[pivot_row][column]
        work[pivot_row] = [item / divisor for item in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [item - factor * selected for item, selected in zip(work[row], work[pivot_row])]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def _determinant(value: Matrix) -> F:
    size = len(value)
    work = [list(row) for row in value]
    determinant, sign = F(1), 1
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            return F(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            sign *= -1
        divisor = work[column][column]
        determinant *= divisor
        for row in range(column + 1, size):
            if not work[row][column]:
                continue
            factor = work[row][column] / divisor
            for selected in range(column, size):
                work[row][selected] -= factor * work[column][selected]
    return determinant * sign


def _submatrix(value: Matrix, size: int) -> Matrix:
    return [row[:size] for row in value[:size]]


def _exact_reference() -> dict[str, Matrix]:
    """Reverse equations 2.9 and 3.3-3.14 without producer imports."""

    xy = ((F(0), F(0)), (F(1), F(0)), (F(1, 5), F(9, 10)))
    jacobian = [[xy[1][0] - xy[0][0], xy[2][0] - xy[0][0]], [xy[1][1] - xy[0][1], xy[2][1] - xy[0][1]]]
    determinant = jacobian[0][0] * jacobian[1][1] - jacobian[0][1] * jacobian[1][0]
    inverse_jacobian = [[jacobian[1][1] / determinant, -jacobian[0][1] / determinant], [-jacobian[1][0] / determinant, jacobian[0][0] / determinant]]
    gradients = _multiply([[F(-1), F(-1)], [F(1), F(0)], [F(0), F(1)]], inverse_jacobian)
    area = abs(determinant) / 2

    elastic, poisson, thickness = F(210_000_000_000), F(3, 10), F(1, 100)
    elastic_shape = [[F(1), poisson, F(0)], [poisson, F(1), F(0)], [F(0), F(0), (1 - poisson) / 2]]
    membrane_section = _scale(elastic_shape, elastic * thickness / (1 - poisson**2))
    bending_section = _scale(elastic_shape, elastic * thickness**3 / (12 * (1 - poisson**2)))
    shear_section = F(5, 6) * elastic / (2 * (1 + poisson)) * thickness
    mass = _scale([[F(2), F(1), F(1)], [F(1), F(2), F(1)], [F(1), F(1), F(2)]], area / 12)
    inverse_bending = _inverse(bending_section)
    divergence: list[tuple[F, F]] = []
    for dx, dy in gradients:
        divergence.extend(((dx, F(0)), (F(0), dy), (dy, dx)))
    h_bending, h_shear = _zeros(9, 9), _zeros(9, 9)
    for ni in range(3):
        for nj in range(3):
            for ci in range(3):
                for cj in range(3):
                    h_bending[3 * ni + ci][3 * nj + cj] = mass[ni][nj] * inverse_bending[ci][cj]
                    left, right = divergence[3 * ni + ci], divergence[3 * nj + cj]
                    h_shear[3 * ni + ci][3 * nj + cj] = area / shear_section * (left[0] * right[0] + left[1] * right[1])
    h = _add(h_bending, h_shear)

    edge_matrix, edge_values = _zeros(3, 3), _zeros(3, 9)
    for edge, (first, second) in enumerate(((0, 1), (1, 2), (2, 0))):
        delta = (xy[second][0] - xy[first][0], xy[second][1] - xy[first][1])
        midpoint = ((xy[first][0] + xy[second][0]) / 2, (xy[first][1] + xy[second][1]) / 2)
        edge_matrix[edge] = [delta[0], delta[1], midpoint[1] * delta[0] - midpoint[0] * delta[1]]
        for node in range(3):
            occupancy = F(int(node == first) + int(node == second), 2)
            edge_values[edge][3 * node] = gradients[node][0] * delta[0] + gradients[node][1] * delta[1]
            edge_values[edge][3 * node + 1] = -occupancy * delta[0]
            edge_values[edge][3 * node + 2] = -occupancy * delta[1]
    reduction = _multiply(_inverse(edge_matrix), edge_values)
    center_x, center_y = sum(point[0] for point in xy) / 3, sum(point[1] for point in xy) / 3
    reduced_center = [[reduction[0][column] + center_y * reduction[2][column] for column in range(9)], [reduction[1][column] - center_x * reduction[2][column] for column in range(9)]]
    coupling = _zeros(9, 9)
    for moment_node in range(3):
        for component in range(3):
            row = 3 * moment_node + component
            for flex_node, (dx, dy) in enumerate(gradients):
                coupling[row][3 * flex_node + 1] += area / 3 * (dx, F(0), dy)[component]
                coupling[row][3 * flex_node + 2] += area / 3 * (F(0), dy, dx)[component]
            for column in range(9):
                coupling[row][column] -= area * (divergence[row][0] * reduced_center[0][column] + divergence[row][1] * reduced_center[1][column])
    transfer = _multiply(_inverse(h), coupling)
    condensed_bending = _multiply(_multiply(_transpose(transfer), h_bending), transfer)
    condensed_shear = _multiply(_multiply(_transpose(transfer), h_shear), transfer)
    condensed = _multiply(_transpose(coupling), transfer)

    membrane_operator, plate_embedding, constraint = _zeros(3, 18), _zeros(9, 18), _zeros(3, 18)
    for node, (dx, dy) in enumerate(gradients):
        base = 6 * node
        membrane_operator[0][base], membrane_operator[1][base + 1] = dx, dy
        membrane_operator[2][base], membrane_operator[2][base + 1] = dy, dx
        plate_embedding[3 * node][base + 2] = F(1)
        plate_embedding[3 * node + 1][base + 4] = F(1)
        plate_embedding[3 * node + 2][base + 3] = F(-1)
        for row in range(3):
            constraint[row][base], constraint[row][base + 1] = dy / 2, -dx / 2
        constraint[node][base + 5] = F(1)
    membrane = _scale(_multiply(_multiply(_transpose(membrane_operator), membrane_section), membrane_operator), area)
    shell_bending = _multiply(_multiply(_transpose(plate_embedding), condensed_bending), plate_embedding)
    shell_shear = _multiply(_multiply(_transpose(plate_embedding), condensed_shear), plate_embedding)
    shape_mass = _scale([[F(2), F(1), F(1)], [F(1), F(2), F(1)], [F(1), F(1), F(2)]], area / 12)
    pl = _scale(_multiply(_multiply(_transpose(constraint), shape_mass), constraint), membrane_section[2][2])
    physical = _add(membrane, _add(shell_bending, shell_shear))
    total = _add(physical, pl)
    return {"gradients": gradients, "H_bending": h_bending, "H_shear": h_shear, "H": h, "G": coupling, "reduction": reduction, "moment_transfer": transfer, "bending": condensed_bending, "shear": condensed_shear, "condensed": condensed, "shell_membrane": membrane, "shell_bending": shell_bending, "shell_shear": shell_shear, "shell_physical": physical, "shell_pl": pl, "shell_hourglass": _zeros(18, 18), "shell_total": total}


def _relative_exact_to_binary64(actual: np.ndarray, expected: Matrix) -> float:
    reference = np.asarray([[float(item) for item in row] for row in expected], dtype=np.float64)
    return float(np.linalg.norm(actual - reference, ord=np.inf) / max(np.linalg.norm(reference, ord=np.inf), 1.0))


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != "anysolver.e4-pl-s3-v3a-implementation-screen-proof-v1":
        raise ValueError("unexpected proof schema")
    if proof.get("candidate", {}).get("formulation_id") != FORMULATION_ID:
        raise ValueError("unexpected formulation identity")
    authority_complete = proof.get("contract_sha256") == sha256_bytes(CONTRACT.read_bytes())
    exact = _exact_reference()
    payloads = proof.get("local_payloads", {})
    worst = 0.0
    for name, expected in exact.items():
        if name not in payloads:
            raise ValueError(f"missing local payload {name}")
        worst = max(worst, _relative_exact_to_binary64(_decode(payloads[name]), expected))
    h, coupling = exact["H"], exact["G"]
    physical, total = exact["shell_physical"], exact["shell_total"]
    leading_positive = all(_determinant(_submatrix(h, size)) > 0 for size in range(1, 10))
    rigid = _zeros(18, 6)
    coordinates = ((F(0), F(0)), (F(1), F(0)), (F(1, 5), F(9, 10)))
    for node, (x, y) in enumerate(coordinates):
        base = 6 * node
        rigid[base][0] = rigid[base + 1][1] = rigid[base + 2][2] = F(1)
        rigid[base + 2][3], rigid[base + 3][3] = -y, F(1)
        rigid[base + 2][4], rigid[base + 4][4] = x, F(1)
        rigid[base][5], rigid[base + 1][5], rigid[base + 5][5] = -y, x, F(1)
    rigid_exact = _multiply(total, rigid) == _zeros(18, 6)
    coupling_rank, physical_rank, total_rank = _rank(coupling), _rank(physical), _rank(total)
    local_passed = bool(leading_positive and coupling_rank == 6 and physical_rank == 9 and total_rank == 12 and rigid_exact and total == _transpose(total))
    later_not_run = proof.get("diagnostics", {}).get("later_screen_stages") == "NOT_EXECUTED_LOCAL_GATE_FAILED"
    return {"authority_complete": bool(authority_complete), "exact_coupling_rank": coupling_rank, "exact_physical_rank": physical_rank, "exact_total_rank": total_rank, "local_operator_passed": local_passed, "mixed_interface_passed": bool(not later_not_run and proof.get("development_records")), "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "replacement_required": False, "rigid_modes_exact": bool(rigid_exact), "schema": CHECK_SCHEMA, "source_identity_passed": bool(worst <= 3.0e-13), "source_identity_worst_relative_inf_hex": worst.hex()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = verify(load_document(args.verify_proof))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
