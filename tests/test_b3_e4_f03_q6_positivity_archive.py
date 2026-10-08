"""Owned, hash-bound diagnostic input archive for Q6 positivity."""

import numpy as np
import pytest
from scipy import sparse

from scripts._b3_e4_f03_q6_positivity_archive import read_inputs, write_inputs


def _inputs():
    k = sparse.csr_matrix([[4., 1.], [1., 3.]])
    working = k.copy()
    lower = sparse.csr_matrix([[1., 0.], [.25, 1.]])
    return k, working, lower, np.array([4., 2.75]), np.array([0, 1]), np.ones(2)


def _read(path, record):
    return read_inputs(
        path, order=2, k_nnz=4, working_nnz=4, lower_nnz=3,
        archive_sha256=record["sha256"],
        original_sha256=record["original_sha256"],
        working_sha256=record["working_sha256"],
        lower_sha256=record["lower_sha256"])


def test_archive_round_trip_owns_matrices_and_vectors(tmp_path):
    path = tmp_path / "inputs.npz"
    inputs = _inputs()
    record = write_inputs(path, *inputs)
    saved = _read(path, record)
    assert saved[-1] == record["bytes"]
    assert np.array_equal(saved[0].toarray(), inputs[0].toarray())
    inputs[0].data[:] = 0
    inputs[3][:] = 0
    assert saved[0][0, 0] == 4.
    assert saved[3][0] == 4.
    saved[0].data[:] = 0
    assert _read(path, record)[0][0, 0] == 4.


def test_archive_detects_byte_mutation_and_wrong_matrix_hash(tmp_path):
    path = tmp_path / "inputs.npz"
    record = write_inputs(path, *_inputs())
    with pytest.raises(ValueError, match="identity"):
        read_inputs(path, order=2, k_nnz=4, working_nnz=4, lower_nnz=3,
                    archive_sha256=record["sha256"],
                    original_sha256="0"*64,
                    working_sha256=record["working_sha256"],
                    lower_sha256=record["lower_sha256"])
    with path.open("ab") as stream:
        stream.write(b"X")
    with pytest.raises(ValueError, match="hash"):
        _read(path, record)


@pytest.mark.parametrize("index,replacement", [
    (3, np.array([0., 1.])), (4, np.array([0, 0])),
    (5, np.array([1., -1.])),
])
def test_archive_rejects_invalid_vectors(tmp_path, index, replacement):
    inputs = list(_inputs())
    inputs[index] = replacement
    with pytest.raises(ValueError, match="vectors"):
        write_inputs(tmp_path / "invalid.npz", *inputs)
