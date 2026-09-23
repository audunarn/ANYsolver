import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_numerical_storage as saved


CASE = cases.CASES[0]
N = CASE.physical_dofs
ORDER = CASE.kkt_order


def _root():
    return sparse.csr_matrix(
        (np.ones(3), (np.arange(3), np.arange(3))), shape=(3, N),
    )


def _h(kbar, cbar):
    return sparse.bmat(((kbar, cbar.T), (cbar, None)), format="csc")


def _operators():
    return saved.OperatorEvidence(
        sparse.eye(N, format="csr"),
        sparse.diags(np.full(N, 2.0), format="csr"),
        _root(),
        np.arange(N, dtype=np.float64),
    )


def _scaled():
    kbar = sparse.eye(N, format="csr")
    cbar = _root()
    h = _h(kbar, cbar)
    return saved.ScaledEvidence(
        kbar, cbar, h, kbar.copy(), cbar.copy(), h.copy(),
        np.ones(N), np.ones(3), np.ones(ORDER), np.full(ORDER, 2.0),
        np.arange(ORDER, dtype=np.float64), np.arange(N, dtype=np.float64),
        np.arange(3, dtype=np.float64), np.arange(ORDER, dtype=np.float64) + 1,
    )


def _positivity():
    identity = sparse.eye(N, format="csr")
    order = np.arange(N, dtype=np.int64)
    return saved.PositivityEvidence(
        sparse.eye(N, format="csr"), identity, identity.copy(), np.ones(N),
        order, order.copy(), order.copy(),
    )


def _assert_matrix_equal(first, second):
    assert first.format == second.format
    np.testing.assert_array_equal(first.toarray(), second.toarray())


def test_operator_scaled_and_positivity_roundtrip(tmp_path):
    groups = (
        ("operators.npz", _operators(), saved.write_operators, saved.read_operators),
        ("scaled.npz", _scaled(), saved.write_scaled, saved.read_scaled),
        ("positivity.npz", _positivity(), saved.write_positivity, saved.read_positivity),
    )
    for name, source, writer, reader in groups:
        path = tmp_path / name
        counts = writer(path, source, CASE)
        restored = reader(path, CASE, counts)
        for field in source.__dataclass_fields__:
            first, second = getattr(source, field), getattr(restored, field)
            if sparse.issparse(first):
                _assert_matrix_equal(first, second)
                assert not np.shares_memory(first.data, second.data)
            else:
                np.testing.assert_array_equal(first, second)
                assert not np.shares_memory(first, second)


def test_exact_group_shapes_and_formats():
    operators, arrays = saved.operator_specs(CASE, saved.OperatorCounts(N, N, 3))
    assert tuple((spec.name, spec.shape, spec.format) for spec in operators) == (
        ("shell", (N, N), "csr"), ("beam", (N, N), "csr"),
        ("root", (3, N), "csr"),
    )
    assert arrays[0].shape == (N,)
    scaled, arrays = saved.scaled_specs(
        CASE, saved.ScaledCounts(N, 3, N + 6, N, 3, N + 6),
    )
    assert tuple(spec.name for spec in scaled) == (
        "kbar", "cbar", "h", "kbar_alternate", "cbar_alternate", "h_alternate",
    )
    assert arrays[-1].shape == (ORDER,)
    positivity, arrays = saved.positivity_specs(
        CASE, saved.PositivityCounts(N, N, N),
    )
    assert tuple(spec.format for spec in positivity) == ("csr", "csr", "csr")
    assert tuple(spec.dtype for spec in arrays) == (
        np.dtype("<f8"), np.dtype("<i8"), np.dtype("<i8"), np.dtype("<i8"),
    )


def test_topology_and_factor_count_envelopes_rejected_before_storage():
    limits = saved._assembly_limits(CASE)
    invalid = (
        lambda: saved.operator_specs(
            CASE, saved.OperatorCounts(limits["shell_triplets"] + 1, 1, 1),
        ),
        lambda: saved.scaled_specs(
            CASE, saved.ScaledCounts(1, 1, CASE.kkt_nnz + 1, 1, 1, 1),
        ),
        lambda: saved.positivity_specs(
            CASE, saved.PositivityCounts(1, cases.MAX_COMBINED_FACTOR_NNZ, 1),
        ),
    )
    for operation in invalid:
        with pytest.raises(ValueError, match="envelope"):
            operation()


def test_late_invalid_array_precedes_first_sparse_copy(tmp_path, monkeypatch):
    value = _scaled()
    value.eta[0] = np.nan
    monkeypatch.setattr(
        saved.sparse_storage, "encode",
        lambda *a, **k: pytest.fail("all vectors must validate before sparse copies"),
    )
    with pytest.raises(ValueError, match="eta"):
        saved.write_scaled(tmp_path / "bad.npz", value, CASE)


def test_invalid_matrix_precedes_sparse_or_vector_copy(tmp_path, monkeypatch):
    value = _scaled()
    value.h.data[0] = np.nan
    monkeypatch.setattr(
        saved.sparse_storage, "encode",
        lambda *a, **k: pytest.fail("all matrices must validate first"),
    )
    with pytest.raises(ValueError, match="h"):
        saved.write_scaled(tmp_path / "bad.npz", value, CASE)
