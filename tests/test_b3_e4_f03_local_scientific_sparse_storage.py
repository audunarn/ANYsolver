import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_sparse_storage as storage


SPECS = (
    storage.SparseSpec("shell", (3, 3), 4, "csr"),
    storage.SparseSpec("root", (2, 3), 3, "csc"),
)


@pytest.fixture
def matrices():
    shell = sparse.csr_matrix(np.array([[2., 0., 1.], [0., 3., 0.], [1., 0., 0.]]))
    root = sparse.csc_matrix(np.array([[1., 0., 2.], [0., 3., 0.]]))
    return {"shell": shell, "root": root}


def test_sparse_encode_decode_roundtrip_and_owned_arrays(matrices):
    arrays = storage.encode(matrices, SPECS)
    restored = storage.decode(arrays, SPECS)
    for name in matrices:
        np.testing.assert_array_equal(restored[name].toarray(), matrices[name].toarray())
        assert not np.shares_memory(restored[name].data, arrays[name + "_data"])
        assert not np.shares_memory(restored[name].indices, arrays[name + "_indices"])
        assert not np.shares_memory(restored[name].indptr, arrays[name + "_indptr"])


def test_empty_outer_rows_or_columns_do_not_wrap_previous_slice():
    shell = sparse.csr_matrix(np.array([
        [0., 0., 0.], [1., 2., 0.], [0., 0., 3.],
    ]))
    root = sparse.csc_matrix(np.array([
        [0., 4., 0.], [0., 0., 5.],
    ]))
    specs = (
        storage.SparseSpec("shell", (3, 3), 3, "csr"),
        storage.SparseSpec("root", (2, 3), 2, "csc"),
    )
    arrays = storage.encode({"shell": shell, "root": root}, specs)
    restored = storage.decode(arrays, specs)
    np.testing.assert_array_equal(restored["shell"].toarray(), shell.toarray())
    np.testing.assert_array_equal(restored["root"].toarray(), root.toarray())


def test_sparse_specs_expand_to_exact_array_schema():
    values = storage.array_specs(SPECS)
    assert tuple(spec.name for spec in values) == (
        "shell_data", "shell_indices", "shell_indptr",
        "root_data", "root_indices", "root_indptr",
    )
    assert tuple(spec.shape for spec in values) == ((4,), (4,), (4,), (3,), (3,), (4,))


def test_missing_extra_wrong_format_shape_nnz_nonfinite_and_duplicate_rejected(matrices):
    invalid = []
    missing = dict(matrices); missing.pop("root"); invalid.append(missing)
    invalid.append(dict(matrices, extra=sparse.eye(1)))
    wrong_format = dict(matrices); wrong_format["shell"] = matrices["shell"].tocsc(); invalid.append(wrong_format)
    wrong_shape = dict(matrices); wrong_shape["shell"] = sparse.csr_matrix((3, 4)); invalid.append(wrong_shape)
    wrong_nnz = dict(matrices); wrong_nnz["shell"] = sparse.eye(3, format="csr"); invalid.append(wrong_nnz)
    nonfinite = dict(matrices); nonfinite["shell"] = matrices["shell"].copy(); nonfinite["shell"].data[0] = np.nan; invalid.append(nonfinite)
    duplicate = dict(matrices); duplicate["shell"] = matrices["shell"].copy(); duplicate["shell"].indices[1] = duplicate["shell"].indices[0]; invalid.append(duplicate)
    for value in invalid:
        with pytest.raises(ValueError):
            storage.encode(value, SPECS)


def test_decode_rejects_pointer_index_and_order_mutations(matrices):
    arrays = storage.encode(matrices, SPECS)
    mutations = []
    pointer = {name: value.copy() for name, value in arrays.items()}; pointer["shell_indptr"][-1] -= 1; mutations.append(pointer)
    index = {name: value.copy() for name, value in arrays.items()}; index["shell_indices"][0] = 99; mutations.append(index)
    order = {name: value.copy() for name, value in arrays.items()}; order["shell_indices"][:2] = order["shell_indices"][1::-1]; mutations.append(order)
    missing = dict(arrays); missing.pop("root_data"); mutations.append(missing)
    for value in mutations:
        with pytest.raises(ValueError):
            storage.decode(value, SPECS)


def test_all_matrix_validation_precedes_first_ownership_copy(matrices, monkeypatch):
    bad = dict(matrices)
    bad["root"] = bad["root"].copy()
    bad["root"].data[0] = np.nan
    original = np.frombuffer
    monkeypatch.setattr(np, "frombuffer", lambda *a, **k: pytest.fail("must validate all first"))
    with pytest.raises(ValueError, match="root"):
        storage.encode(bad, SPECS)
    monkeypatch.setattr(np, "frombuffer", original)


def test_all_saved_structures_validate_before_first_matrix_construction(matrices, monkeypatch):
    arrays = storage.encode(matrices, SPECS)
    arrays["root_indptr"][-1] -= 1
    monkeypatch.setattr(
        storage, "_construct_matrix",
        lambda *a, **k: pytest.fail("must validate the complete group first"),
    )
    with pytest.raises(ValueError, match="root"):
        storage.decode(arrays, SPECS)


def test_float_serialization_converts_values_to_little_endian_owned_storage():
    source = np.array([1.25, -3.5], dtype=">f8")
    result = storage._little_float_copy(source)
    assert result.dtype == np.dtype("<f8")
    assert result.flags.owndata
    np.testing.assert_array_equal(result, np.array([1.25, -3.5], dtype="<f8"))


def test_float_reconstruction_converts_canonical_values_to_native_owned_storage():
    opposite = ">f8" if np.little_endian else "<f8"
    source = np.array([1.25, -3.5], dtype=opposite)
    result = storage._native_float_copy(source)
    assert result.dtype == np.dtype(np.float64)
    assert result.flags.owndata
    np.testing.assert_array_equal(result, np.array([1.25, -3.5], dtype=np.float64))


@pytest.mark.parametrize("name,shape,nnz,fmt", [
    ("Bad", (1, 1), 0, "csr"),
    ("good", (0, 1), 0, "csr"),
    ("good", (1, 1), 2, "csr"),
    ("good", (1, 1), 0, "coo"),
])
def test_invalid_sparse_specs_rejected(name, shape, nnz, fmt):
    with pytest.raises(ValueError):
        storage.SparseSpec(name, shape, nnz, fmt)
