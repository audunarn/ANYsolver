from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_numerical_index as numerical_index
from scripts import _b3_e4_f03_local_scientific_numerical_storage as numerical
from scripts import _b3_e4_f03_local_scientific_port_storage as ports
from scripts import _b3_e4_f03_local_scientific_replay_binding as replay
from scripts import _b3_e4_f03_sparse_trace_binding as trace
from scripts import _b3_e4_f03_spatial_contract as spatial


CASE = cases.CASES[0]
N = CASE.physical_dofs
ORDER = CASE.kkt_order


def _root():
    return sparse.csr_matrix((np.ones(3), (np.arange(3), np.arange(3))), shape=(3, N))


def _evidence():
    kbar = sparse.eye(N, format='csr')
    cbar = _root()
    h = sparse.bmat(((kbar, cbar.T), (cbar, None)), format='csc')
    root_scale = np.asarray((1 / spatial.U0, 1 / spatial.U0, 0.46 / spatial.U0))
    scaled = numerical.ScaledEvidence(
        kbar, cbar, h, kbar.copy(), cbar.copy(), h.copy(),
        np.ones(N), root_scale, np.ones(ORDER), np.ones(ORDER),
        np.zeros(ORDER), np.zeros(N), np.zeros(3), np.zeros(ORDER),
    )
    permutation = np.arange(N, dtype=np.int64)
    positivity = numerical.PositivityEvidence(
        kbar.copy(), kbar.copy(), kbar.copy(), np.ones(N),
        permutation, permutation.copy(), permutation.copy(),
    )
    operators = numerical.OperatorEvidence(
        kbar.copy(), kbar.copy(), cbar.copy(), np.zeros(N),
    )
    empty = sparse.csr_matrix((3, N), dtype=np.float64)
    samples = tuple(
        trace.SavedPort(station, order, side, empty.copy(), np.zeros(3))
        for station, order, side in trace.KEYS
    )
    port = ports.PortEvidence(
        samples, cbar.copy(), cbar.copy(),
        sparse.csr_matrix((np.ones(1), ([0], [0])), shape=(1, N)),
    )
    return numerical_index.NumericalEvidence(
        operators, operators, scaled, positivity, port,
    )


def _producer(value):
    return numerical_index.successful_positivity_producer(value.positivity)


def test_saved_numerical_semantics_bind_exact_factor_and_scaling_routes():
    value = _evidence()
    checked = replay.verify_numerical_binding(_producer(value), value)
    assert checked.positivity_candidate_status == 'CANDIDATE_CREATED'
    assert checked.positivity_candidate_reason is None
    assert len({checked.kbar_sha256, checked.permutation_sha256,
                checked.diagonal_sha256, checked.root_scale_sha256}) == 4


@pytest.mark.parametrize('mutation,reason', (
    ('kbar', 'positivity matrix'),
    ('row_map', 'producer disposition'),
    ('duplicate_map', 'permutation semantics'),
    ('inverse_gather', 'permutation semantics'),
    ('diagonal', 'positivity diagonal'),
    ('root_scale', 'root scale'),
))
def test_saved_numerical_semantics_reject_cross_binding_mutations(mutation, reason):
    value = _evidence()
    proof = value.positivity
    scaled = value.scaled
    if mutation == 'kbar':
        changed = proof.kbar.copy(); changed.data[0] += 1.0
        proof = replace(proof, kbar=changed)
    elif mutation == 'row_map':
        changed = proof.row_map.copy(); changed[[0, 1]] = changed[[1, 0]]
        proof = replace(proof, row_map=changed)
    elif mutation == 'duplicate_map':
        changed = proof.column_map.copy(); changed[0] = changed[1]
        proof = replace(proof, column_map=changed)
    elif mutation == 'inverse_gather':
        changed = proof.inverse_gather.copy(); changed[[0, 1]] = changed[[1, 0]]
        proof = replace(proof, inverse_gather=changed)
    elif mutation == 'diagonal':
        changed = proof.diagonal.copy(); changed[0] += 1.0
        proof = replace(proof, diagonal=changed)
    else:
        changed = scaled.r.copy(); changed[2] = np.nextafter(changed[2], np.inf)
        scaled = replace(scaled, r=changed)
    changed_value = replace(value, positivity=proof, scaled=scaled)
    producer = _producer(changed_value) if mutation == 'kbar' else _producer(value)
    with pytest.raises(ValueError, match=reason):
        replay.verify_numerical_binding(producer, changed_value)


def test_valid_saved_hold_candidate_is_preserved_for_numerical_adjudication():
    value = _evidence()
    changed = value.positivity.row_map.copy()
    changed[[0, 1]] = changed[[1, 0]]
    proof = replace(value.positivity, row_map=changed)
    value = replace(value, positivity=proof)
    producer = replace(
        numerical_index.successful_positivity_producer(proof),
        status='HOLD', reason='native row and column permutations differ',
    )
    checked = replay.verify_numerical_binding(producer, value)
    assert checked.positivity_candidate_status == 'HOLD'
    assert checked.positivity_candidate_reason == producer.reason


def test_valid_nonpositive_diagonal_hold_is_preserved_for_adjudication():
    value = _evidence()
    upper = value.positivity.upper.copy(); upper.data[0] = -1.0
    diagonal = value.positivity.diagonal.copy(); diagonal[0] = -1.0
    proof = replace(value.positivity, upper=upper, diagonal=diagonal)
    value = replace(value, positivity=proof)
    producer = replace(
        numerical_index.successful_positivity_producer(proof),
        status='HOLD', reason='native congruence candidate has nonpositive diagonal',
    )
    checked = replay.verify_numerical_binding(producer, value)
    assert checked.positivity_candidate_status == 'HOLD'
    assert checked.positivity_candidate_reason == producer.reason


@pytest.mark.parametrize('factor', ('lower', 'upper'))
def test_saved_factor_structure_is_rechecked_after_producer_rebinding(factor):
    value = _evidence()
    proof = value.positivity
    if factor == 'lower':
        changed = proof.lower.tolil()
        changed[0, 1] = 0.25
        proof = replace(proof, lower=changed.tocsr())
        reason = 'lower factor'
    else:
        changed = proof.upper.tolil()
        changed[1, 0] = 0.25
        proof = replace(proof, upper=changed.tocsr())
        reason = 'upper factor'
    changed_value = replace(value, positivity=proof)
    with pytest.raises(ValueError, match=reason):
        replay.verify_numerical_binding(_producer(changed_value), changed_value)


def test_replay_binding_result_rejects_mutable_or_noncanonical_hashes():
    with pytest.raises(ValueError, match='canonical'):
        replay.ReplayBinding('CANDIDATE_CREATED', None, *(['ab' * 32] * 3), ['ab' * 32])
    with pytest.raises(ValueError, match='canonical'):
        replay.ReplayBinding('CANDIDATE_CREATED', None, 'G' * 64, *(['ab' * 32] * 3))
