"""Bounded saved scaled-KKT input for an eventual Q6 certificate replay."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_sparse_storage as sparse_storage
from scripts import _b3_e4_f03_local_scientific_storage as storage
from scripts._b3_e4_f03_conforming_qp_energy import _kkt_sha256


MAX_SYSTEM_ARCHIVE_BYTES = 64*1024**2


def _specs(order: int, nnz: int):
    if (type(order) is not int or type(nnz) is not int or
            order <= 3 or nnz <= 0 or nnz > order*order):
        raise ValueError("invalid Q6 scaled-system inventory")
    matrix = sparse_storage.SparseSpec("h", (order, order), nnz, "csc")
    arrays = sparse_storage.array_specs((matrix,)) + (
        storage.ArraySpec("rhs", (order,), np.dtype("<f8")),
        storage.ArraySpec("displacement_scale", (order-3,), np.dtype("<f8")),
        storage.ArraySpec("multiplier_scale", (3,), np.dtype("<f8")),
    )
    storage._validate_specs(arrays, MAX_SYSTEM_ARCHIVE_BYTES)
    return matrix, arrays


def _sha256(path: Path) -> str:
    size = Path(path).stat().st_size
    if not 0 < size <= MAX_SYSTEM_ARCHIVE_BYTES:
        raise ValueError("Q6 scaled-system archive exceeds byte bound")
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_system(path: Path, matrix, rhs: np.ndarray,
                 displacement_scale: np.ndarray,
                 multiplier_scale: np.ndarray) -> dict:
    order = int(matrix.shape[0])
    spec, arrays_spec = _specs(order, int(matrix.nnz))
    if (matrix.shape != (order, order) or type(rhs) is not np.ndarray or
            rhs.dtype != np.float64 or rhs.shape != (order,) or
            not np.isfinite(rhs).all() or
            type(displacement_scale) is not np.ndarray or
            displacement_scale.dtype != np.float64 or
            displacement_scale.shape != (order-3,) or
            not np.isfinite(displacement_scale).all() or
            np.any(displacement_scale <= 0) or
            type(multiplier_scale) is not np.ndarray or
            multiplier_scale.dtype != np.float64 or
            multiplier_scale.shape != (3,) or
            not np.isfinite(multiplier_scale).all() or
            np.any(multiplier_scale <= 0)):
        raise ValueError("invalid Q6 scaled-system RHS or physical scales")
    arrays = sparse_storage.encode({"h": matrix}, (spec,))
    arrays["rhs"] = np.asarray(rhs, dtype="<f8").copy()
    arrays["displacement_scale"] = np.asarray(
        displacement_scale, dtype="<f8").copy()
    arrays["multiplier_scale"] = np.asarray(
        multiplier_scale, dtype="<f8").copy()
    storage.write_group(path, arrays, arrays_spec,
                        max_raw_bytes=MAX_SYSTEM_ARCHIVE_BYTES)
    return {"bytes": Path(path).stat().st_size,
            "sha256": _sha256(path),
            "kkt_rhs_sha256": _kkt_sha256(matrix, rhs)}


def read_system(path: Path, *, order: int, nnz: int,
                archive_sha256: str, kkt_rhs_sha256: str):
    spec, arrays_spec = _specs(order, nnz)
    payload = storage._snapshot(Path(path), MAX_SYSTEM_ARCHIVE_BYTES)
    if hashlib.sha256(payload).hexdigest() != archive_sha256:
        raise ValueError("Q6 scaled-system archive hash mismatch")
    arrays = storage.read_group_payload(
        payload, arrays_spec, max_raw_bytes=MAX_SYSTEM_ARCHIVE_BYTES)
    matrix = sparse_storage.decode({name: arrays[name] for name in
                                    ("h_data", "h_indices", "h_indptr")},
                                   (spec,))["h"]
    rhs = np.asarray(arrays["rhs"], dtype=np.float64).copy()
    displacement_scale = np.asarray(
        arrays["displacement_scale"], dtype=np.float64).copy()
    multiplier_scale = np.asarray(
        arrays["multiplier_scale"], dtype=np.float64).copy()
    if (np.any(displacement_scale <= 0) or np.any(multiplier_scale <= 0)):
        raise ValueError("invalid Q6 saved physical scales")
    if _kkt_sha256(matrix, rhs) != kkt_rhs_sha256:
        raise ValueError("Q6 saved KKT matrix/RHS identity mismatch")
    return matrix, rhs, displacement_scale, multiplier_scale, len(payload)
