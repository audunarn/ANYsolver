"""Semantic cross-bindings for saved F03 numerical replay evidence."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_numerical_index as numerical_index
from scripts import _b3_e4_f03_spatial_contract as spatial


@dataclass(frozen=True, slots=True)
class ReplayBinding:
    positivity_candidate_status: str
    positivity_candidate_reason: str | None
    kbar_sha256: str
    permutation_sha256: str
    diagonal_sha256: str
    root_scale_sha256: str

    def __post_init__(self):
        values = (
            self.kbar_sha256, self.permutation_sha256,
            self.diagonal_sha256, self.root_scale_sha256,
        )
        if (
            self.positivity_candidate_status not in ("CANDIDATE_CREATED", "HOLD")
            or (self.positivity_candidate_status == "CANDIDATE_CREATED")
            != (self.positivity_candidate_reason is None)
            or (self.positivity_candidate_reason is not None and (
                type(self.positivity_candidate_reason) is not str
                or not self.positivity_candidate_reason
            ))
            or any(
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in values
            )
        ):
            raise ValueError("canonical F03 numerical replay binding required")


def _identity(label: bytes, arrays: tuple[np.ndarray, ...]) -> str:
    digest = hashlib.sha256(label + b"\0")
    for value in arrays:
        digest.update(np.asarray(value.shape, dtype="<i8").tobytes())
        digest.update(value.dtype.str.encode("ascii") + b"\0")
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def _same_array(first: np.ndarray, second: np.ndarray) -> bool:
    return (
        type(first) is np.ndarray
        and type(second) is np.ndarray
        and first.shape == second.shape
        and first.dtype == second.dtype
        and first.flags.c_contiguous
        and second.flags.c_contiguous
        and first.tobytes(order="C") == second.tobytes(order="C")
    )


def _same_sparse(first: object, second: object) -> bool:
    return (
        type(first) is sparse.csr_matrix
        and type(second) is sparse.csr_matrix
        and first.shape == second.shape
        and _same_array(first.data, second.data)
        and _same_array(first.indices, second.indices)
        and _same_array(first.indptr, second.indptr)
    )


def verify_numerical_binding(
    producer: numerical_index.PositivityProducerRecord,
    value: numerical_index.NumericalEvidence,
) -> ReplayBinding:
    """Close saved factor/scaling semantics without numerical evaluation."""
    if (
        type(producer) is not numerical_index.PositivityProducerRecord
        or type(value) is not numerical_index.NumericalEvidence
    ):
        raise ValueError("factory-read F03 positivity record and numerical evidence required")
    scaled = value.scaled
    proof = value.positivity
    numerical_index._verify_positivity_record(proof, producer)
    if not _same_sparse(proof.kbar, scaled.kbar):
        raise ValueError("F03 positivity matrix disagrees with primary scaled stiffness")
    n = scaled.kbar.shape[0]
    expected = np.arange(n, dtype=np.int64)
    rows, columns, gather = proof.row_map, proof.column_map, proof.inverse_gather
    if not all(
        type(item) is np.ndarray
        and item.dtype == np.dtype(np.int64)
        and item.shape == (n,)
        and item.flags.c_contiguous
        for item in (rows, columns, gather)
    ):
        raise ValueError("complete native int64 F03 positivity permutations required")
    if (
        not np.array_equal(np.sort(rows), expected)
        or not np.array_equal(np.sort(columns), expected)
        or not np.array_equal(gather, np.argsort(columns, kind="stable"))
    ):
        raise ValueError("F03 positivity permutation semantics disagree")
    diagonal = np.ascontiguousarray(proof.upper.diagonal(), dtype=np.float64)
    if not _same_array(proof.diagonal, diagonal):
        raise ValueError("F03 positivity diagonal disagrees with saved upper factor")
    if not _same_array(rows, columns):
        expected_status = "HOLD"
        expected_reason = "native row and column permutations differ"
    elif np.any(proof.diagonal <= 0):
        expected_status = "HOLD"
        expected_reason = "native congruence candidate has nonpositive diagonal"
    else:
        expected_status = "CANDIDATE_CREATED"
        expected_reason = None
    if (producer.status, producer.reason) != (expected_status, expected_reason):
        raise ValueError("F03 positivity producer disposition disagrees with saved factors")
    root = np.asarray(
        (1 / spatial.U0, 1 / spatial.U0, 0.46 / spatial.U0),
        dtype=np.float64,
    )
    if not _same_array(scaled.r, root):
        raise ValueError("F03 saved root scale disagrees with held physical scaling")
    return ReplayBinding(
        expected_status,
        expected_reason,
        _identity(
            b"F03_REPLAY_KBAR_V1",
            (np.asarray(proof.kbar.shape, dtype=np.int64), proof.kbar.data,
             proof.kbar.indices, proof.kbar.indptr),
        ),
        _identity(b"F03_REPLAY_PERMUTATION_V1", (rows, columns, gather)),
        _identity(b"F03_REPLAY_DIAGONAL_V1", (proof.diagonal,)),
        _identity(b"F03_REPLAY_ROOT_SCALE_V1", (scaled.r,)),
    )
