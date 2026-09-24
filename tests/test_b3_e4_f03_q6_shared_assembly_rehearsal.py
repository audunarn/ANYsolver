"""Reject mismatched shared operators before a numerical diagnostic runs."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_conforming_qp_energy import assemble
from scripts._b3_e4_f03_qp_operator_identity import fingerprint
from scripts.b3_e4_f03_q6_full_certificate_feasibility import child as certificate_child
from scripts.b3_e4_f03_q6_positivity_feasibility import child as positivity_child
from scripts.b3_e4_f03_qp_nested_x_pilot import run as physical_run
from scripts.b3_e4_f03_qp_nested_x2_spatial import run as spatial_run
from scripts.b3_e4_f03_q6_x2_shared_assembly_rehearsal import (
    _recovery_source_hashes)


@pytest.mark.parametrize("runner", [certificate_child, positivity_child])
def test_q6_shared_operators_reject_wrong_grid_before_measurement(tmp_path, runner):
    wrong = SimpleNamespace(trace=FinitePadQpTrace(1))
    with pytest.raises(ValueError, match="shared Q6 .* operators"):
        runner(tmp_path, "X0", operators=wrong)
    assert not (tmp_path / "measurement.json").exists()


def test_physical_route_rejects_wrong_shared_operators():
    wrong = SimpleNamespace(trace=FinitePadQpTrace(1))
    with pytest.raises(ValueError, match="shared physical operators"):
        physical_run(6, "x2", operators=wrong)


def test_spatial_route_rejects_wrong_shared_operators(tmp_path):
    state = tmp_path / "state.json"
    state.write_text('{"grid":"x0"}', encoding="utf-8")
    with pytest.raises(ValueError, match="shared Q6 shell operator required"):
        spatial_run(state, operators=SimpleNamespace(trace=FinitePadQpTrace(1)))
    wrong = assemble(FinitePadQpTrace(1))
    with pytest.raises(ValueError, match="does not match spatial trace"):
        spatial_run(state, operators=wrong)


def test_shared_runner_pins_both_recovery_sources():
    hashes = _recovery_source_hashes()
    assert set(hashes) == {"spatial_source_sha256", "nodal_source_sha256"}
    assert all(len(value) == 64 for value in hashes.values())


def test_operator_fingerprint_detects_numerical_mutation():
    trace = FinitePadQpTrace(1)
    operators = assemble(trace)
    before = fingerprint(operators, trace)
    assert fingerprint(operators, trace) == before
    changed_load = operators.load.copy()
    changed_load[0] += 1.
    assert fingerprint(replace(operators, load=changed_load), trace) != before
    changed_shell = operators.shell_stiffness.copy()
    changed_shell.data[0] += 1.
    assert fingerprint(replace(operators, shell_stiffness=changed_shell), trace) != before
    changed_root = operators.root_constraint.copy()
    changed_root[0, 0] += 1.
    assert fingerprint(replace(operators, root_constraint=changed_root), trace) != before


def test_operator_fingerprint_rejects_free_column_change():
    trace = FinitePadQpTrace(1)
    operators = assemble(trace)
    wrong = operators.free_columns.copy()
    wrong[0] += 1
    with pytest.raises(ValueError, match="free-column"):
        fingerprint(replace(operators, free_columns=wrong), trace)


def test_operator_fingerprint_rejects_derived_trace_mutation():
    original = FinitePadQpTrace(1)
    operators = assemble(original)
    independent_expected = FinitePadQpTrace(1)
    fingerprint(operators, independent_expected)
    original._weights[0] += .125
    with pytest.raises(ValueError, match="basis or quadrature"):
        fingerprint(operators, independent_expected)


def test_operator_fingerprint_rejects_basis_mutation():
    original = FinitePadQpTrace(1)
    operators = assemble(original)
    independent_expected = FinitePadQpTrace(1)
    fingerprint(operators, independent_expected)
    original._basis[0][0].c[0] += .125
    with pytest.raises(ValueError, match="basis or quadrature"):
        fingerprint(operators, independent_expected)


@pytest.mark.parametrize("field,change", [("area", 2.), ("ny", 1),
                                          ("nx", 1), ("n", 1)])
def test_operator_fingerprint_rejects_derived_scalar_mutation(field, change):
    original = FinitePadQpTrace(1)
    operators = assemble(original)
    independent_expected = FinitePadQpTrace(1)
    fingerprint(operators, independent_expected)
    setattr(original, field, getattr(original, field)+change)
    with pytest.raises(ValueError, match="derived trace"):
        fingerprint(operators, independent_expected)
