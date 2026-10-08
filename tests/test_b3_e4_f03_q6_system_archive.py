"""Saved-only KKT input boundary for the unregistered Q6 replay route."""

import numpy as np
import pytest
from scipy import sparse

from scripts._b3_e4_f03_q6_system_archive import read_system, write_system
from scripts.b3_e4_f03_q6_saved_certificate_replay import _check_parent_source_identity


def test_scaled_system_roundtrip_and_hash_rejection(tmp_path):
    matrix = sparse.diags([2., 3., 4., 5., 6.], format="csc")
    rhs = np.array([1., -2., 0., 0., 0.])
    displacement_scale = np.array([2., 3.])
    multiplier_scale = np.array([4., 5., 6.])
    path = tmp_path / "system.npz"
    saved = write_system(path, matrix, rhs, displacement_scale, multiplier_scale)
    restored, load, d, eta_scale, archive_bytes = read_system(
        path, order=5, nnz=5, archive_sha256=saved["sha256"],
        kkt_rhs_sha256=saved["kkt_rhs_sha256"])
    assert np.array_equal(restored.toarray(), matrix.toarray())
    assert np.array_equal(load, rhs)
    assert np.array_equal(d, displacement_scale)
    assert np.array_equal(eta_scale, multiplier_scale)
    assert archive_bytes == saved["bytes"]
    restored.data[0] = 0.
    load[0] = 0.
    d[0] = 0.
    eta_scale[0] = 0.
    assert matrix.data[0] == 2.
    assert rhs[0] == 1.
    assert displacement_scale[0] == 2.
    assert multiplier_scale[0] == 4.
    with pytest.raises(ValueError, match="archive hash mismatch"):
        read_system(path, order=5, nnz=5, archive_sha256="0"*64,
                    kkt_rhs_sha256=saved["kkt_rhs_sha256"])
    with pytest.raises(ValueError, match="identity mismatch"):
        read_system(path, order=5, nnz=5, archive_sha256=saved["sha256"],
                    kkt_rhs_sha256="0"*64)
    with pytest.raises(FileExistsError):
        write_system(path, matrix, rhs, displacement_scale, multiplier_scale)
    with pytest.raises(ValueError, match="physical scales"):
        write_system(tmp_path / "bad-scale.npz", matrix, rhs,
                     np.array([0., 3.]), multiplier_scale)


def test_replay_attempt_and_child_must_name_same_source(tmp_path):
    result = tmp_path / "measurement.json"
    result.write_text('{"source_measurement_sha256":"abc"}', encoding="utf-8")
    _check_parent_source_identity("abc", result)
    with pytest.raises(ArithmeticError, match="attempt/child"):
        _check_parent_source_identity("def", result)
