from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "docs/reference_cases/s4_candidate_a_open_a1_certificate.json"
EXPECTED_CERTIFICATE_SHA256 = "2198458DCDC7EFB4684B5CC59ADAF6E9A0EECF381951CBDD21B286D6DB11097C"


def _fraction(token: str) -> Fraction:
    if not isinstance(token, str):
        raise TypeError("exact scalar must be encoded as a string")
    return Fraction(token)


def _matrix_rank(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    reduced = [row[:] for row in matrix]
    row = 0
    for column in range(len(reduced[0])):
        pivot = next(
            (index for index in range(row, len(reduced)) if reduced[index][column]),
            None,
        )
        if pivot is None:
            continue
        reduced[row], reduced[pivot] = reduced[pivot], reduced[row]
        scale = reduced[row][column]
        reduced[row] = [value / scale for value in reduced[row]]
        for index in range(len(reduced)):
            if index == row or not reduced[index][column]:
                continue
            scale = reduced[index][column]
            reduced[index] = [
                reduced[index][entry] - scale * reduced[row][entry]
                for entry in range(len(reduced[index]))
            ]
        row += 1
        if row == len(reduced):
            break
    return row


def _determinant(matrix: list[list[Fraction]]) -> Fraction:
    work = [row[:] for row in matrix]
    determinant = Fraction(1)
    for column in range(len(work)):
        pivot = next(index for index in range(column, len(work)) if work[index][column])
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            determinant = -determinant
        pivot_value = work[column][column]
        determinant *= pivot_value
        for row in range(column + 1, len(work)):
            scale = work[row][column] / pivot_value
            for entry in range(column + 1, len(work)):
                work[row][entry] -= scale * work[column][entry]
    return determinant


def _load() -> tuple[bytes, dict[str, object]]:
    raw = CERTIFICATE.read_bytes()
    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    data = json.loads(raw.decode("utf-8"))
    canonical = (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return raw, data


def _canonical_git_lf(raw: bytes) -> bytes:
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf:
        raise AssertionError("accepted text input contains a lone CR")
    if b"\r\n" in raw and b"\n" in without_crlf:
        raise AssertionError("accepted text input mixes CRLF and LF line endings")
    return raw.replace(b"\r\n", b"\n")


def test_certificate_is_canonical_and_binds_accepted_inputs() -> None:
    raw, data = _load()
    assert _canonical_git_lf(b"a\nb\n") == b"a\nb\n"
    assert _canonical_git_lf(b"a\r\nb\r\n") == b"a\nb\n"
    for hostile in (b"a\rb", b"a\r\nb\n"):
        try:
            _canonical_git_lf(hostile)
        except AssertionError:
            pass
        else:
            raise AssertionError("lone or mixed CR input was accepted")

    assert hashlib.sha256(raw).hexdigest().upper() == EXPECTED_CERTIFICATE_SHA256
    assert data["schema"] == "anysolver.s4.candidate-a.open-a1-rank-certificate-v1"
    assert data["candidate"]["basis_id"] == "candidate_a.d4.span_r_s"
    assert data["accepted_inputs"]["text_identity"] == "canonical_git_lf"

    for record in data["accepted_inputs"].values():
        if not isinstance(record, dict):
            continue
        path = ROOT / record["path"]
        source = _canonical_git_lf(path.read_bytes())
        assert len(source) == record["size_bytes"]
        assert hashlib.sha256(source).hexdigest().upper() == record["raw_sha256"]


def test_a1_annihilates_the_complete_accepted_B_kernel_exactly() -> None:
    _, data = _load()
    rows = [
        [_fraction(value) for value in data["exact_constraint_rows_raw"][mode]]
        for mode in data["candidate"]["basis_order"]
    ]
    witnesses = data["witnesses"]
    witness_ids = data["premises"]["accepted_B_kernel_witness_ids"]
    columns = [[_fraction(value) for value in witnesses[name]] for name in witness_ids]

    assert _matrix_rank(rows) == 2
    witness_matrix = [[column[row] for column in columns] for row in range(24)]
    assert _matrix_rank(witness_matrix) == 8

    selected = [int(value) for value in data["exact_identities"]["kernel_witness_minor"]["selected_coordinate_indices"]]
    minor = [[witness_matrix[row][column] for column in range(8)] for row in selected]
    assert _determinant(minor) == _fraction(
        data["exact_identities"]["kernel_witness_minor"]["determinant"]
    ) == 4

    for name, column in zip(witness_ids, columns, strict=True):
        action = [sum(row[index] * column[index] for index in range(24)) for row in rows]
        expected = [_fraction(value) for value in data["exact_identities"]["constraint_actions"][name]]
        assert action == expected == [Fraction(0), Fraction(0)]


def test_exact_rank_consequence_is_a_proven_failure() -> None:
    _, data = _load()
    rows = [
        [_fraction(value) for value in data["exact_constraint_rows_raw"][mode]]
        for mode in data["candidate"]["basis_order"]
    ]
    raw_columns = [int(value) for value in data["exact_identities"]["raw_constraint_minor"]["column_indices"]]
    raw_minor = [[row[column] for column in raw_columns] for row in rows]
    raw_determinant = _determinant(raw_minor)
    assert raw_determinant == _fraction(
        data["exact_identities"]["raw_constraint_minor"]["determinant"]
    ) == Fraction(-1, 9)

    scale_squared = _fraction(data["candidate"]["normalization_scale_squared"])
    assert scale_squared > 0
    assert raw_determinant * scale_squared == _fraction(
        data["exact_identities"]["normalized_constraint_minor"]["determinant"]
    ) == Fraction(-1, 12)

    ambient = int(data["dimensions"]["ambient"])
    rank_b = int(data["dimensions"]["accepted_rank_B"])
    nullity_b = int(data["dimensions"]["accepted_nullity_B"])
    rank_c = _matrix_rank(rows)
    assert ambient - rank_b == nullity_b == 8
    assert data["result"]["ker_B_subset_ker_C"] is True

    rank_stacked = ambient - nullity_b
    rank_bt = (ambient - rank_c) - nullity_b
    assert rank_stacked == int(data["result"]["rank_stacked_B_C"]) == 16
    assert rank_bt == int(data["result"]["rank_BT"]) == 14
    assert rank_c == int(data["result"]["rank_C"]) == 2
    assert data["result"]["candidate_terminal"] == "PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK"
    assert data["result"]["pair_gate_result"] == "PROVEN_FAIL"
