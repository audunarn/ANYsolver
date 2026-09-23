from dataclasses import replace

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_port_factory as factory
from scripts import _b3_e4_f03_local_scientific_port_storage as storage
from scripts import _b3_e4_f03_sparse_trace_binding as trace


CASE = cases.CASES[0]


def test_factory_produces_ordered_owned_ports_and_independent_replay(tmp_path):
    grid = cases.compile_case(CASE)
    q = np.arange(grid.free_dofs, dtype=np.float64) / grid.free_dofs
    source = q.copy()
    value = factory.produce_port_evidence(
        grid, q, budget=budgets.make_scientific_budgets().trace,
    )
    q[:] = -99.0
    assert tuple((item.station, item.order, item.side) for item in value.samples) == trace.KEYS
    assert len(value.samples) == 27
    for item in value.samples:
        np.testing.assert_array_equal(item.action, item.operator @ source)
        assert not np.shares_memory(item.action, q)
    np.testing.assert_array_equal(value.root.toarray(), value.samples[0].operator.toarray())
    np.testing.assert_array_equal(value.tip.toarray(), value.samples[8].operator.toarray())
    np.testing.assert_array_equal(
        value.free_slope.toarray(), value.samples[9].operator[1:2].toarray(),
    )
    path = tmp_path / "ports.npz"
    counts = storage.write_ports(path, value, CASE)
    restored = storage.read_ports(path, CASE, counts)
    checked = trace.verify_trace_binding(
        grid, source, np.ones(grid.free_dofs), restored.samples,
        restored.root, restored.tip, restored.free_slope,
        budget=budgets.make_scientific_budgets().trace,
    )
    assert checked["status"] == "TRACE_BINDING_PASSED"
    assert checked["work"]["equilibrium_solves"] == 0


def test_factory_caches_each_trace_interval_once(monkeypatch):
    grid = cases.compile_case(CASE)
    calls = []
    original = assembly.trace_interval

    def observed(value, index, budget):
        calls.append(index)
        return original(value, index, budget)

    monkeypatch.setattr(factory.assembly, "trace_interval", observed)
    factory.produce_port_evidence(
        grid, np.zeros(grid.free_dofs),
        budget=budgets.make_scientific_budgets().trace,
    )
    assert calls == sorted(set(calls))
    assert 0 < len(calls) <= CASE.station_intervals


def test_factory_resource_failure_precedes_trace_extraction(monkeypatch):
    grid = cases.compile_case(CASE)
    budget = budgets.make_scientific_budgets().trace
    rejected = replace(budget, max_input_nnz=1)
    monkeypatch.setattr(
        factory.assembly, "trace_interval",
        lambda *args: pytest.fail("trace extraction preceded resource preflight"),
    )
    with pytest.raises(ValueError, match="resource budget"):
        factory.produce_port_evidence(
            grid, np.zeros(grid.free_dofs), budget=rejected,
        )


def test_factory_rejects_workspace_just_below_frozen_envelope_before_trace(monkeypatch):
    grid = cases.compile_case(CASE)
    budget = budgets.make_scientific_budgets().trace
    input_nnz = 88 * grid.free_dofs
    required = (
        1024 * (input_nnz + 32 * grid.free_dofs)
        + 2 * budget.max_total_bits
        + 9 * budget.trace_budget.max_work_bytes
    )
    rejected = replace(budget, max_work_bytes=required - 1)
    monkeypatch.setattr(
        factory.assembly, "trace_interval",
        lambda *args: pytest.fail("trace extraction preceded workspace preflight"),
    )
    with pytest.raises(ValueError, match="resource budget"):
        factory.produce_port_evidence(
            grid, np.zeros(grid.free_dofs), budget=rejected,
        )


@pytest.mark.parametrize("mutation", ("dtype", "shape", "nonfinite", "strided"))
def test_factory_rejects_noncanonical_state_before_work(monkeypatch, mutation):
    grid = cases.compile_case(CASE)
    q = np.zeros(grid.free_dofs)
    if mutation == "dtype":
        q = q.astype(np.float32)
    elif mutation == "shape":
        q = q[:-1]
    elif mutation == "nonfinite":
        q[0] = np.nan
    else:
        q = np.zeros(2 * grid.free_dofs)[::2]
    monkeypatch.setattr(
        factory.assembly, "trace_interval",
        lambda *args: pytest.fail("invalid state reached trace extraction"),
    )
    with pytest.raises(ValueError, match="physical state"):
        factory.produce_port_evidence(
            grid, q, budget=budgets.make_scientific_budgets().trace,
        )
