"""Small synthetic checks for the saved-data F03 cross-case comparator."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_functional as green
from scripts import _b3_e4_f03_local_prolongation as transfer
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cross_math as cross
from scripts import _b3_e4_f03_sparse_trace_binding as trace


def _functional(atom=F(0)):
    zero = (F(0),) * 6
    return green.Functional(
        (F(0), F(1)), ((zero, zero, zero),), (F(0),) * 3,
        ((atom, F(0), F(0)), (F(0),) * 3),
    )


def _functional_record(value):
    observations = [green.norm_observation_at_order(value, order) for order in (48, 64)]
    components = tuple(v for item in observations for index in range(3)
                       for name in ("diagonal", "offdiagonal", "atom_cross",
                                    "atom_gram", "sum_abs_terms", "cancellation_ratio")
                       for v in (item[name][index],))
    return receipt.FunctionalRecord(
        "a" * 64,
        tuple(v for item in observations for v in item["channels"]),
        tuple(item["squared_norm"] for item in observations), components,
        tuple(bool(v) for item in observations for name in
              ("channel_finite", "channel_nonnegative", "channel_nonzero_valid")
              for v in item[name]),
        tuple(bool(item[name]) for item in observations
              for name in ("total_finite", "total_nonnegative", "admissible")),
        tuple(bool(item["exact_zero"]) for item in observations),
        tuple(tuple((failure["stage"], failure["channel"], failure["reason"])
                    for failure in item["failures"]) for item in observations),
    )


def _case(case_id, *, scalar=0.0, energy=0.0, atom=F(0), port_scale=1.0):
    values = [0.0] * 45
    values[0] = scalar
    values[14] = energy
    settling = receipt.SettlingRecord(
        tuple(values), tuple(values), tuple(values), receipt.SETTLING_SCALES,
        ("b" * 64,) * 45,
    )
    physical = _functional(atom)
    identity = sparse.identity(2, format="csr", dtype=np.float64)
    root = sparse.csr_matrix(np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]))
    port = sparse.csr_matrix(np.array([[port_scale, 0.0], [0.0, 1.0], [0.0, 0.0]]))
    ports = tuple(trace.SavedPort(s, order, side, port,
                                  np.zeros(3, dtype=np.float64))
                  for s, order, side in trace.KEYS)
    return cross.CaseData(
        case_id, settling, _functional_record(physical), physical,
        np.zeros(2, dtype=np.float64), identity, identity, root,
        np.zeros(2, dtype=np.float64), ports, root, root,
        sparse.csr_matrix(np.array([[1.0, 0.0]])),
    )


def _prolongation(weight=F(1)):
    value = object.__new__(transfer.ExactProlongation)
    for name, item in (
        ("source_dofs", 2), ("target_dofs", 2),
        ("rows", np.array([0, 1], dtype=np.int64)),
        ("columns", np.array([0, 1], dtype=np.int64)),
        ("weights", (weight, F(1))),
        ("integer_bits", sum(x.numerator.bit_length() + x.denominator.bit_length()
                             for x in (weight, F(1)))),
    ):
        object.__setattr__(value, name, item)
    return value


def _pair(source="Q1_L0", target="Q1_L1", **kwargs):
    p = _prolongation()
    return cross.compare_pair(_case(source), _case(target, **kwargs),
                              saved_prolongation=p, rederived_prolongation=p)


def test_nested_identity_and_complete_zero_functional():
    result = _pair()
    assert result.passed
    assert len(result.scalar_relatives) == 45
    assert result.energy_distance == 0
    assert result.energy_defect_relative == 0
    assert len(result.compatibility) == 146
    assert result.functional_difference_norm == 0
    assert dict(result.functional_preflight)["union_intervals"] == 1


def test_nested_comparison_rejects_changed_saved_port_action_alone():
    coarse = _case("Q1_L0")
    fine = _case("Q1_L1")
    first = fine.ports[0]
    altered = trace.SavedPort(
        first.station, first.order, first.side, first.operator,
        np.array([1e-4, 0.0, 0.0], dtype=np.float64),
    )
    fine = replace(fine, ports=(altered, *fine.ports[1:]))
    p = _prolongation()
    result = cross.compare_pair(
        coarse, fine, saved_prolongation=p, rederived_prolongation=p,
    )
    assert not result.passed
    assert any("fine_saved_action" in failure for failure in result.failures)


def test_scalar_signed_floor_and_energy_identity_failures():
    result = _pair(scalar=20_000.0, energy=1.0)
    assert not result.passed
    assert any("root_reaction_x" in reason for reason in result.failures)
    assert any("Ritz energy identity" in reason for reason in result.failures)
    assert result.scalar_relatives[0] > 0.01


def test_wrong_exact_prolongation_is_reported_before_ritz_claim():
    result = cross.compare_pair(_case("Q1_L0"), _case("Q1_L1"),
                                saved_prolongation=_prolongation(F(2)),
                                rederived_prolongation=_prolongation())
    assert not result.passed
    assert result.energy_distance is None
    assert any("prolongation" in reason for reason in result.failures)


def test_saved_trace_action_mismatch_fails_nested_compatibility():
    result = _pair(port_scale=1.01)
    assert not result.passed
    assert any("trace_00" in reason for reason in result.failures)
    assert dict(result.compatibility)["trace_00"] > cross.TRACE_LIMIT


def test_complete_signed_functional_difference_is_not_clipped():
    result = cross.compare_pair(_case("Q1_L2"), _case("Q2_L1", atom=F(100)))
    assert not result.passed
    assert result.functional_difference_norm is not None
    assert result.functional_relative is not None
    assert result.functional_relative > 0.01
    assert result.energy_distance is None


def test_chain_last_changes_and_only_registered_cross_pair():
    pairs = (
        _pair("Q1_L0", "Q1_L1", scalar=1000.0),
        _pair("Q1_L1", "Q1_L2", scalar=2000.0),
        _pair("Q1_L0", "Q2_L0"),
        _pair("Q2_L0", "Q2_L1"),
        cross.compare_pair(_case("Q1_L2"), _case("Q2_L1")),
    )
    summary = cross.compare_chains(pairs)
    assert not summary.passed
    assert any("does not settle" in reason for reason in summary.failures)
    with pytest.raises(ValueError, match="frozen F03 settling pairs"):
        cross.compare_pair(_case("Q1_L1"), _case("Q2_L0"))


def test_invalid_functional_observation_and_union_preflight():
    bad = replace(_case("Q1_L0").functional_record, total_flags=(False,) * 6)
    source = replace(_case("Q1_L0"), functional_record=bad)
    with pytest.raises(ValueError, match="only frozen"):
        cross.compare_pair(source, _case("Q2_L1"))
    result = cross.compare_pair(replace(_case("Q1_L2"), functional_record=bad),
                                _case("Q2_L1"))
    assert not result.passed
    assert any("inadmissible saved" in reason for reason in result.failures)
    cuts = tuple(F(i, 130) for i in range(131))
    zero = (F(0),) * 6
    excessive = green.Functional(cuts, ((zero, zero, zero),) * 130,
                                 (F(0),) * 3, ((F(0),) * 3,) * 2)
    with pytest.raises(ValueError, match="interval cap"):
        cross.compare_pair(replace(_case("Q1_L2"), functional=excessive), _case("Q2_L1"))
