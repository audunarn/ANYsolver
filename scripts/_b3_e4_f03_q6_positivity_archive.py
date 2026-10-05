"""Bounded saved inputs for replaying the experimental Q6 positivity proof."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_sparse_storage as sparse_storage
from scripts import _b3_e4_f03_local_scientific_storage as storage
from scripts._b3_e4_f03_sparse_factor_candidate import _digest_owned


MAX_ARCHIVE_BYTES = 64*1024**2


def _specs(order: int, k_nnz: int, working_nnz: int, lower_nnz: int):
    if (any(type(value) is not int for value in
            (order, k_nnz, working_nnz, lower_nnz)) or
            not 1 <= order <= 10_000 or
            any(not 0 < value <= order*order for value in
                (k_nnz, working_nnz, lower_nnz))):
        raise ValueError("invalid Q6 positivity archive inventory")
    matrices = tuple(sparse_storage.SparseSpec(name, (order, order), nnz, "csr")
                     for name, nnz in (("k", k_nnz), ("working", working_nnz),
                                       ("lower", lower_nnz)))
    arrays = sparse_storage.array_specs(matrices) + (
        storage.ArraySpec("diagonal", (order,), np.dtype("<f8")),
        storage.ArraySpec("permutation", (order,), np.dtype("<i8")),
        storage.ArraySpec("displacement_scale", (order,), np.dtype("<f8")),
    )
    storage._validate_specs(arrays, MAX_ARCHIVE_BYTES)
    return matrices, arrays


def _owned_vectors(diagonal, permutation, displacement_scale, order):
    if (type(diagonal) is not np.ndarray or diagonal.dtype != np.float64 or
            diagonal.shape != (order,) or not np.isfinite(diagonal).all() or
            np.any(diagonal <= 0) or
            type(permutation) is not np.ndarray or
            permutation.dtype not in (np.dtype("int32"), np.dtype("int64")) or
            permutation.shape != (order,) or
            not np.array_equal(np.sort(permutation), np.arange(order)) or
            type(displacement_scale) is not np.ndarray or
            displacement_scale.dtype != np.float64 or
            displacement_scale.shape != (order,) or
            not np.isfinite(displacement_scale).all() or
            np.any(displacement_scale <= 0)):
        raise ValueError("invalid Q6 positivity vectors")
    return (np.asarray(diagonal, dtype="<f8").copy(),
            np.asarray(permutation, dtype="<i8").copy(),
            np.asarray(displacement_scale, dtype="<f8").copy())


def write_inputs(path: Path, original, working, lower, diagonal,
                 permutation, displacement_scale) -> dict:
    order = int(original.shape[0])
    matrices, arrays_spec = _specs(
        order, int(original.nnz), int(working.nnz), int(lower.nnz))
    arrays = sparse_storage.encode(
        {"k": original, "working": working, "lower": lower}, matrices)
    d, p, scale = _owned_vectors(diagonal, permutation, displacement_scale,
                                  order)
    arrays.update(diagonal=d, permutation=p, displacement_scale=scale)
    storage.write_group(path, arrays, arrays_spec,
                        max_raw_bytes=MAX_ARCHIVE_BYTES)
    with Path(path).open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "bytes": Path(path).stat().st_size,
        "sha256": archive_hash,
        "original_sha256": _digest_owned(original),
        "working_sha256": _digest_owned(working),
        "lower_sha256": _digest_owned(lower),
    }


def read_inputs(path: Path, *, order: int, k_nnz: int, working_nnz: int,
                lower_nnz: int, archive_sha256: str,
                original_sha256: str, working_sha256: str,
                lower_sha256: str):
    matrices, arrays_spec = _specs(order, k_nnz, working_nnz, lower_nnz)
    payload = storage._snapshot(Path(path), MAX_ARCHIVE_BYTES)
    if hashlib.sha256(payload).hexdigest() != archive_sha256:
        raise ValueError("Q6 positivity archive hash mismatch")
    arrays = storage.read_group_payload(
        payload, arrays_spec, max_raw_bytes=MAX_ARCHIVE_BYTES)
    saved = sparse_storage.decode(
        {name: arrays[name] for spec in matrices for name in
         (spec.name+"_data", spec.name+"_indices", spec.name+"_indptr")},
        matrices)
    d, p, scale = _owned_vectors(
        arrays["diagonal"], arrays["permutation"],
        arrays["displacement_scale"], order)
    if (original_sha256 != _digest_owned(saved["k"]) or
            working_sha256 != _digest_owned(saved["working"]) or
            lower_sha256 != _digest_owned(saved["lower"])):
        raise ValueError("Q6 positivity saved matrix identity mismatch")
    return saved["k"], saved["working"], saved["lower"], d, p, scale, len(payload)
