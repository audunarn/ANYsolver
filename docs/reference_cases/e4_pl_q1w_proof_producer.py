"""Emit one bounded Q1W Q0/D4 exact recovery proof.

The producer performs no 38-field assembly.  It binds a preserved Q1V
reference wrapper, extracts the registered exact recovery rows, and constructs
the frozen Q0 frame, D4 maps, patch vector, expected transported fields, and
residuals using standard-library rational arithmetic.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from e4_pl_q1w_common import (
    PROOF_SCHEMA,
    PROOF_WRAPPER_SCHEMA,
    Q1WError,
    canonical_bytes,
    read_json,
    sha256,
    validate_contract,
    verify_file,
    write_exclusive,
)


ROOT = Path(__file__).resolve().parents[2]
GAUSS = ("GP_MM", "GP_PM", "GP_PP", "GP_MP")
PATCH_IDS = ("MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH")


def F(value: Any = 0) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise Q1WError(f"cannot parse rational value: {value!r}")


def fs(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def matvec(matrix: Sequence[Sequence[Fraction]], vector: Sequence[Fraction]) -> list[Fraction]:
    return [sum((a * b for a, b in zip(row, vector, strict=True)), Fraction()) for row in matrix]


def transpose(matrix: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    return [list(row) for row in zip(*matrix, strict=True)]


def inverse(matrix: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    n = len(matrix)
    work = [list(row) + [Fraction(int(i == j)) for j in range(n)] for i, row in enumerate(matrix)]
    for column in range(n):
        pivot = next((row for row in range(column, n) if work[row][column]), None)
        if pivot is None:
            raise Q1WError("singular frozen D4 field map")
        work[column], work[pivot] = work[pivot], work[column]
        scale = work[column][column]
        work[column] = [value / scale for value in work[column]]
        for row in range(n):
            if row == column:
                continue
            factor = work[row][column]
            work[row] = [a - factor * b for a, b in zip(work[row], work[column], strict=True)]
    return [row[n:] for row in work]


def matrix_tokens(matrix: Sequence[Sequence[Fraction]]) -> list[list[str]]:
    return [[fs(value) for value in row] for row in matrix]


def vector_tokens(vector: Iterable[Fraction]) -> list[str]:
    return [fs(value) for value in vector]


def _progress(case_id: str, phase: str, started: float, **extra: Any) -> None:
    row = {
        "case_id": case_id,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "phase": phase,
        **extra,
    }
    sys.stderr.buffer.write(canonical_bytes(row))
    sys.stderr.buffer.flush()


def _rational_token(value: Any) -> Fraction:
    if not isinstance(value, list) or not value:
        raise Q1WError("historical algebraic value is not a tower token")
    coefficients = [F(item) for item in value]
    if any(coefficients[1:]):
        raise Q1WError("Q0 bounded proof unexpectedly requires a nonrational recovery token")
    return coefficients[0]


def _normalise_recovery_row(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("station_id") not in GAUSS:
        raise Q1WError("historical recovery station ID mismatch")
    result: dict[str, Any] = {"station_id": row["station_id"]}
    for key, length in (("compatible", 8), ("independent", 8), ("N", 3), ("M", 3), ("Q", 2)):
        values = row.get(key)
        if not isinstance(values, list) or len(values) != length:
            raise Q1WError(f"historical recovery {key} shape mismatch")
        result[key] = vector_tokens(_rational_token(item) for item in values)
    return result


def _operation(frame_contract: dict[str, Any], operation_id: str) -> dict[str, Any]:
    rows = frame_contract["d4"]["operations"]
    row = next((item for item in rows if item["id"] == operation_id), None)
    if row is None:
        raise Q1WError(f"operation not frozen: {operation_id}")
    return row


def _field_maps(operation: dict[str, Any]) -> dict[str, list[list[Fraction]]]:
    (a, b), (c, d) = [[F(value) for value in row] for row in operation["A"]]
    det = F(operation["det"])
    c_eng = [
        [a * a, b * b, a * b],
        [c * c, d * d, c * d],
        [2 * a * c, 2 * b * d, a * d + b * c],
    ]
    c_res = [
        [a * a, b * b, 2 * a * b],
        [c * c, d * d, 2 * c * d],
        [a * c, b * d, a * d + b * c],
    ]
    pseudo = [[det * a, det * b], [det * c, det * d]]
    multiplier = [[det, 0, 0], [0, det * a, det * b], [0, det * c, det * d]]
    return {"C_eng": c_eng, "C_res": c_res, "pseudo_vector": pseudo, "multiplier": multiplier}


def _base_patch_vector() -> list[Fraction]:
    coordinates = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    result: list[Fraction] = []
    for x_i, y_i in coordinates:
        x, y = F(x_i), F(y_i)
        u = 2 * x + y / 3
        v = -2 * x / 5 + 4 * y / 3
        w = -x * x / 5 + y * y / 6 - 3 * x * y / 14
        tx = y / 3 - 3 * x / 14 + F("1/4")
        ty = 2 * x / 5 + 3 * y / 14 + F("2/3")
        result.extend((u, v, w, tx, ty, F("-11/30")))
    return result


def _numbered_patch_vector(base: Sequence[Fraction], operation: dict[str, Any]) -> list[Fraction]:
    (a, b), (c, d) = [[F(value) for value in row] for row in operation["A"]]
    det = F(operation["det"])
    ahat = [[a, b, 0], [c, d, 0], [0, 0, det]]
    to_local = transpose(ahat)
    result: list[Fraction] = []
    for old_node in operation["node_tuple"]:
        block = list(base[6 * (int(old_node) - 1) : 6 * int(old_node)])
        result.extend(matvec(to_local, block[:3]) + matvec(to_local, block[3:]))
    return result


def _expected(operation: dict[str, Any], material: dict[str, Any]) -> dict[str, list[Fraction]]:
    maps = _field_maps(operation)
    det = F(operation["det"])
    eps0 = [F(2), F("4/3"), F("-1/15")]
    kap0 = [F("2/5"), F("-1/3"), F("3/7")]
    shr0 = [F("2/3"), F("-1/4")]
    eps = matvec(inverse(maps["C_eng"]), eps0)
    kap = [det * value for value in matvec(inverse(maps["C_eng"]), kap0)]
    shear = matvec(inverse(maps["pseudo_vector"]), shr0)
    constitutive = material["constitutive"]
    a_mat = [[F(value) for value in row] for row in constitutive["membrane_A"]]
    d_mat = [[F(value) for value in row] for row in constitutive["bending_D"]]
    as_mat = [[F(value) for value in row] for row in constitutive["transverse_shear_A_s"]]
    return {
        "strain": eps + kap + shear,
        "N": matvec(a_mat, eps),
        "M": matvec(d_mat, kap),
        "Q": matvec(as_mat, shear),
    }


def _legacy_expected(material: dict[str, Any]) -> dict[str, list[Fraction]]:
    identity = {"A": [[1, 0], [0, 1]], "det": 1}
    return _expected(identity, material)


def _residuals(row: dict[str, Any], expected: dict[str, list[Fraction]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, expected_key in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q")):
        actual = [F(value) for value in row[key]]
        result[key] = vector_tokens(a - b for a, b in zip(actual, expected[expected_key], strict=True))
    return result


def _nonzero_paths(stations: Sequence[dict[str, Any]], residual_key: str) -> list[str]:
    result: list[str] = []
    for station in stations:
        residuals = station[residual_key]
        for field, values in residuals.items():
            for index, value in enumerate(values):
                if F(value):
                    result.append(f"{station['station_id']}.{field}[{index}]")
    return result


def emit_proof(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    historical_reference: Path,
    historical_reference_sha256: str,
    case_id: str,
) -> dict[str, Any]:
    started = time.monotonic()
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    if case_id not in contract["shards"]:
        raise Q1WError("case ID is outside the frozen bounded shard set")
    _progress(case_id, "AUTHORITY_VALIDATED", started)
    historical = contract["historical_reference"]
    raw = verify_file(
        historical_reference,
        size=int(historical["bytes"]),
        digest=historical_reference_sha256,
    )
    if historical_reference_sha256.upper() != historical["sha256"]:
        raise Q1WError("historical reference caller hash is not frozen")
    wrapper = read_json(historical_reference)[1]
    if wrapper.get("certificate_payload_sha256") != historical["certificate_payload_sha256"]:
        raise Q1WError("historical certificate payload hash mismatch")
    if sha256(canonical_bytes(wrapper["certificate_payload"])) != historical["certificate_payload_sha256"]:
        raise Q1WError("historical certificate payload bytes mismatch")
    _progress(case_id, "HISTORICAL_INPUT_BOUND", started)

    root = repository_root.resolve(strict=True)
    geometry = read_json(root / "docs/reference_cases/e4_pl_q1r_geometry_contract.json")[1]
    frame = read_json(root / "docs/reference_cases/e4_pl_q1r_frame_contract.json")[1]
    material = read_json(root / "docs/reference_cases/e4_pl_q1r_material_contract.json")[1]
    q0 = next(row for row in geometry["geometries"] if row["id"] == "Q0_SQUARE")
    if q0["nodes"] != [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]]:
        raise Q1WError("Q0 geometry changed")
    operation_id = case_id.split("::", 1)[1]
    operation = _operation(frame, operation_id)
    maps = _field_maps(operation)
    a = [[F(value) for value in row] for row in operation["A"]]
    det = F(operation["det"])
    ahat = [[a[0][0], a[0][1], 0], [a[1][0], a[1][1], 0], [0, 0, det]]
    _progress(case_id, "FIELD_AND_FRAME_CONSTRUCTED", started)

    cases = wrapper["implementation_diagnostics"]["cases"]
    base_case = next((row for row in cases if row.get("id") == "Q0_SQUARE::E"), None)
    target_case = next((row for row in cases if row.get("id") == case_id), None)
    if base_case is None or target_case is None:
        raise Q1WError("historical reference lacks the selected Q0 cases")
    if target_case["recovery"]["station_count"] != 4:
        raise Q1WError("historical target station count mismatch")
    rows = [_normalise_recovery_row(row) for row in target_case["recovery"]["rows"]]
    if [row["station_id"] for row in rows] != list(GAUSS):
        raise Q1WError("historical station order mismatch")
    expected = _expected(operation, material)
    legacy = _legacy_expected(material)
    stations: list[dict[str, Any]] = []
    signs = {"GP_MM": (-1, -1), "GP_PM": (1, -1), "GP_PP": (1, 1), "GP_MP": (-1, 1)}
    for index, row in enumerate(rows):
        sr, ss = signs[row["station_id"]]
        mapped = (int(a[0][0]) * sr + int(a[0][1]) * ss, int(a[1][0]) * sr + int(a[1][1]) * ss)
        station = {
            **row,
            "numbered_natural_coordinates": [f"{sr}*sqrt(3)/3", f"{ss}*sqrt(3)/3"],
            "base_natural_coordinates": [f"{mapped[0]}*sqrt(3)/3", f"{mapped[1]}*sqrt(3)/3"],
            "expected_transported": {key: vector_tokens(values) for key, values in expected.items()},
        }
        station["transport_residuals"] = _residuals(row, expected)
        station["legacy_untransformed_residuals"] = _residuals(row, legacy)
        stations.append(station)
        _progress(case_id, "STATION_COMPLETED", started, station_index=index, station_id=row["station_id"])

    base_patch = _base_patch_vector()
    target_patch = _numbered_patch_vector(base_patch, operation)
    numbered_nodes = [q0["nodes"][int(old) - 1] for old in operation["node_tuple"]]
    transport_nonzero = _nonzero_paths(stations, "transport_residuals")
    legacy_nonzero = _nonzero_paths(stations, "legacy_untransformed_residuals")
    proof = {
        "schema": PROOF_SCHEMA,
        "candidate_id": contract["candidate_id"],
        "study_id": contract["study_id"],
        "case_id": case_id,
        "geometry_id": "Q0_SQUARE",
        "operation_id": operation_id,
        "historical_reference": {
            "bytes": len(raw),
            "sha256": sha256(raw),
            "certificate_payload_sha256": wrapper["certificate_payload_sha256"],
            "role": historical["role"],
        },
        "frozen_inputs": contract["frozen_inputs"],
        "field_generators": [
            {"id": "g1", "expression": "sqrt(8)", "reduced": "2*sqrt(2)"},
            {"id": "g2", "expression": "sqrt(8)", "reduced": "2*sqrt(2)"},
            {"id": "g3", "expression": "sqrt(4)", "reduced": "2"},
            {"id": "g4", "expression": "sqrt(64)", "reduced": "8"},
            {"id": "g5", "expression": "sqrt(3)", "reduced": "sqrt(3)"},
        ],
        "nodes": {"base": q0["nodes"], "numbered": numbered_nodes, "node_tuple": operation["node_tuple"]},
        "frames": {
            "base": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
            "numbered": matrix_tokens(ahat),
            "Ahat": matrix_tokens(ahat),
        },
        "field_maps": {key: matrix_tokens(value) for key, value in maps.items()},
        "patch_vector": {"field_id": "COMBINED_PHYSICAL_PATCH", "base_local": vector_tokens(base_patch), "numbered_local": vector_tokens(target_patch)},
        "stations": stations,
        "exact_nonzero_transport_residuals": transport_nonzero,
        "legacy_untransformed_nonzero_residuals": legacy_nonzero,
        "producer_scope": {
            "assembled_38_field_system": False,
            "full_56_case_certificate": False,
            "global_kkt": False,
            "registered_cases": 1,
            "stations": 4,
        },
    }
    proof_raw = canonical_bytes(proof)
    result = {"schema": PROOF_WRAPPER_SCHEMA, "proof": proof, "proof_sha256": sha256(proof_raw)}
    _progress(case_id, "PROOF_COMPLETED", started, proof_sha256=result["proof_sha256"])
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--proof-contract", type=Path, required=True)
    parser.add_argument("--proof-contract-sha256", required=True)
    parser.add_argument("--historical-reference", type=Path, required=True)
    parser.add_argument("--historical-reference-sha256", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = emit_proof(
            repository_root=args.repository_root,
            contract_path=args.proof_contract,
            contract_sha256=args.proof_contract_sha256,
            historical_reference=args.historical_reference,
            historical_reference_sha256=args.historical_reference_sha256,
            case_id=args.case_id,
        )
        write_exclusive(args.output, canonical_bytes(result))
        return 0
    except (Q1WError, KeyError, ValueError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1W_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
