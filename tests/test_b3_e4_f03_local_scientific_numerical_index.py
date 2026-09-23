import json

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_numerical_index as index_storage
from scripts import _b3_e4_f03_local_scientific_numerical_storage as numerical
from scripts import _b3_e4_f03_local_scientific_port_storage as ports
from scripts import _b3_e4_f03_sparse_trace_binding as trace
from scripts import _b3_e4_f03_sparse_certificate as certificate
from scripts import _b3_e4_f03_sparse_factor_candidate as factor_candidate


CASE = cases.CASES[0]
SOURCE = "a" * 40
N = CASE.physical_dofs
ORDER = CASE.kkt_order


@pytest.fixture(scope="module")
def plan():
    records = cases.preflight_inventory()
    return archive.make_case_plan(records[0], records, SOURCE)


def _root():
    return sparse.csr_matrix((np.ones(3), (np.arange(3), np.arange(3))), shape=(3, N))


def _operators(scale=1.0):
    return numerical.OperatorEvidence(
        sparse.eye(N, format="csr"),
        sparse.diags(np.full(N, 2.0), format="csr"),
        _root(),
        scale * np.arange(N, dtype=np.float64),
    )


def _scaled():
    kbar = sparse.eye(N, format="csr")
    cbar = _root()
    h = sparse.bmat(((kbar, cbar.T), (cbar, None)), format="csc")
    return numerical.ScaledEvidence(
        kbar, cbar, h, kbar.copy(), cbar.copy(), h.copy(),
        np.ones(N), np.ones(3), np.ones(ORDER), np.full(ORDER, 2.0),
        np.arange(ORDER, dtype=np.float64), np.arange(N, dtype=np.float64),
        np.arange(3, dtype=np.float64), np.arange(ORDER, dtype=np.float64) + 1,
    )


def _positivity():
    identity = sparse.eye(N, format="csc")
    order = np.arange(N, dtype=np.int64)
    return numerical.PositivityEvidence(
        sparse.eye(N, format="csr"), identity, identity.copy(), np.ones(N),
        order, order.copy(), order.copy(),
    )


def _ports():
    empty = sparse.csr_matrix((3, N), dtype=np.float64)
    samples = tuple(
        trace.SavedPort(station, order, side, empty.copy(), np.zeros(3))
        for station, order, side in trace.KEYS
    )
    return ports.PortEvidence(
        samples, _root(), _root(),
        sparse.csr_matrix((np.ones(1), ([0], [0])), shape=(1, N)),
    )


def _evidence(alternate_scale=1.0):
    return index_storage.NumericalEvidence(
        _operators(), _operators(alternate_scale), _scaled(), _positivity(), _ports(),
    )


def _write_groups(directory, value):
    directory.mkdir()
    numerical.write_operators(directory / "operators_primary.npz", value.operator_primary, CASE)
    numerical.write_operators(directory / "operators_alternate.npz", value.operator_alternate, CASE)
    numerical.write_scaled(directory / "scaled_state.npz", value.scaled, CASE)
    numerical.write_positivity(directory / "positivity.npz", value.positivity, CASE)
    ports.write_ports(directory / "ports.npz", value.port_evidence, CASE)


def _producers(plan, value):
    return (
        index_storage.successful_kkt_producer(plan, value.scaled.h.nnz),
        index_storage.successful_positivity_producer(value.positivity),
    )


def test_index_is_self_describing_and_saved_only_hashes_replay(plan, tmp_path):
    directory = tmp_path / "complete"
    source = _evidence()
    _write_groups(directory, source)
    index = index_storage.build_index(plan, source, *_producers(plan, source))
    digest = index_storage.write_index(directory / "numerical_index.json", index)
    restored, observed = index_storage.read_index(directory / "numerical_index.json", plan)
    loaded_index, loaded = index_storage.read_saved(directory, plan)
    assert restored == index == loaded_index
    assert observed == digest
    assert loaded_index.port_counts.ports == (0,) * 27
    assert len(loaded_index.objects) == 86
    np.testing.assert_array_equal(loaded.operator_alternate.load, source.operator_alternate.load)
    assert not np.shares_memory(loaded.operator_alternate.load, source.operator_alternate.load)


def test_object_mutation_is_rejected_by_saved_only_replay(plan, tmp_path):
    directory = tmp_path / "mutated"
    source = _evidence()
    _write_groups(directory, source)
    index = index_storage.build_index(plan, source, *_producers(plan, source))
    index_storage.write_index(directory / "numerical_index.json", index)
    (directory / "operators_alternate.npz").unlink()
    numerical.write_operators(directory / "operators_alternate.npz", _operators(2.0), CASE)
    with pytest.raises(ValueError, match="digest"):
        index_storage.read_saved(directory, plan)


def test_noncanonical_or_stale_index_is_rejected(plan, tmp_path):
    directory = tmp_path / "bad-index"
    source = _evidence()
    index = index_storage.build_index(plan, source, *_producers(plan, source))
    path = directory / "numerical_index.json"
    directory.mkdir()
    index_storage.write_index(path, index)
    value = json.loads(path.read_text("ascii"))
    value["objects"].reverse()
    path.write_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
    with pytest.raises(ValueError):
        index_storage.read_index(path, plan)


def test_frozen_producer_settings_and_counts_are_enforced(plan):
    source = _evidence()
    kkt, positivity = _producers(plan, source)
    assert kkt.ordering == "COLAMD"
    assert kkt.certificate_rhs_completed == plan.kkt_order
    assert kkt.certificate_solve_calls == len(plan.inverse_blocks)
    assert positivity.ordering == "MMD_AT_PLUS_A"
    assert positivity.symmetric_mode
    assert positivity.matrix_sha256 == index_storage.factor_candidate._digest_owned(
        source.positivity.kbar,
    )
    with pytest.raises(ValueError):
        index_storage.KKTProducerRecord(
            "NATURAL", 1.0, False, False, "NOREFINE", 1, 1, 1,
            len(plan.inverse_blocks), plan.kkt_order, plan.kkt_order, 0, 0,
            "NOT_QUALIFIED", "SUCCEEDED", "completed",
        )


def test_actual_positivity_candidate_metadata_and_native_hashes_are_preserved():
    matrix = sparse.diags(np.arange(2.0, 6.0), format="csr")
    sparse_budget = certificate.SparseBudget(4, 16, 1, 4096)
    candidate = factor_candidate.produce(
        matrix, factor_candidate.FactorBudget(sparse_budget, 32, 4096),
    )
    value = numerical.PositivityEvidence(
        candidate.matrix, candidate.lower, candidate.upper, candidate.diagonal,
        candidate.row_map, candidate.column_map,
        np.asarray(candidate.permutation, dtype=np.int64),
    )
    record = index_storage.positivity_producer(value, candidate.metadata)
    assert record.ordering == "MMD_AT_PLUS_A"
    assert record.pivot_threshold == 0.0
    assert record.symmetric_mode
    assert record.matrix_sha256 == candidate.metadata["matrix_sha256"]
    assert record.lower_sha256 == candidate.metadata["lower_sha256"]
    assert record.upper_sha256 == candidate.metadata["upper_sha256"]
