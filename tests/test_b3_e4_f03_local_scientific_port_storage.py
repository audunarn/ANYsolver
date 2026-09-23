from bisect import bisect_right

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_port_storage as saved
from scripts import _b3_e4_f03_sparse_trace_binding as trace


CASE = cases.CASES[0]


def _evidence():
    grid = cases.compile_case(CASE)
    traces = {}
    samples = []
    q = np.arange(grid.free_dofs, dtype=np.float64) / grid.free_dofs
    for station, order, side in trace.KEYS:
        index = min(bisect_right(grid.station_cuts, station) - 1, len(grid.station_cuts) - 2)
        if side == "left" and index > 0 and station == grid.station_cuts[index]:
            index -= 1
        if index not in traces:
            traces[index] = assembly.trace_interval(grid, index, cases.ASSEMBLY_BUDGET)
        local = traces[index]
        exact = local.evaluate_exact((station - local.left) / (local.right - local.left), order)
        values = np.asarray(exact, dtype=np.float64)
        operator = sparse.coo_matrix(
            (
                values.ravel(),
                (np.repeat(np.arange(3), len(local.indices)), np.tile(local.indices, 3)),
            ),
            shape=(3, grid.free_dofs),
        ).tocsr()
        operator.eliminate_zeros()
        samples.append(trace.SavedPort(station, order, side, operator, operator @ q))
    root = samples[0].operator.copy()
    tip = samples[8].operator.copy()
    slope = samples[9].operator[1:2].copy()
    return saved.PortEvidence(tuple(samples), root, tip, slope)


def test_complete_port_roundtrip_and_owned_actions(tmp_path):
    source = _evidence()
    path = tmp_path / "ports.npz"
    counts = saved.write_ports(path, source, CASE)
    restored = saved.read_ports(path, CASE, counts)
    assert len(restored.samples) == 27
    for first, second, key in zip(source.samples, restored.samples, trace.KEYS):
        assert (second.station, second.order, second.side) == key
        np.testing.assert_array_equal(first.operator.toarray(), second.operator.toarray())
        np.testing.assert_array_equal(first.action, second.action)
        assert not np.shares_memory(first.action, second.action)
    np.testing.assert_array_equal(source.root.toarray(), restored.root.toarray())
    np.testing.assert_array_equal(source.tip.toarray(), restored.tip.toarray())
    np.testing.assert_array_equal(source.free_slope.toarray(), restored.free_slope.toarray())


def test_exact_order_and_count_envelope():
    source = _evidence()
    counts = saved.PortCounts(
        tuple(sample.operator.nnz for sample in source.samples),
        source.root.nnz, source.tip.nnz, source.free_slope.nnz,
    )
    matrices, arrays = saved.port_specs(CASE, counts)
    assert len(matrices) == 30
    assert tuple(spec.name for spec in matrices[:3]) == ("port_00", "port_01", "port_02")
    assert tuple(spec.name for spec in matrices[-3:]) == ("root", "tip", "free_slope")
    assert arrays[0].shape == (27, 3)
    invalid = saved.PortCounts(
        (3 * CASE.max_active_trace_dofs + 1,) + counts.ports[1:],
        counts.root, counts.tip, counts.free_slope,
    )
    with pytest.raises(ValueError, match="envelope"):
        saved.port_specs(CASE, invalid)


def test_missing_reordered_metadata_and_late_nonfinite_action_rejected_before_sparse_copy(
    tmp_path, monkeypatch,
):
    source = _evidence()
    with pytest.raises(ValueError, match="complete"):
        saved.write_ports(
            tmp_path / "missing.npz",
            saved.PortEvidence(source.samples[:-1], source.root, source.tip, source.free_slope),
            CASE,
        )
    reordered = list(source.samples)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    with pytest.raises(ValueError, match="ordered"):
        saved.write_ports(
            tmp_path / "reordered.npz",
            saved.PortEvidence(tuple(reordered), source.root, source.tip, source.free_slope),
            CASE,
        )
    source.samples[-1].action[0] = np.nan
    monkeypatch.setattr(
        saved.sparse_storage, "encode",
        lambda *a, **k: pytest.fail("all actions must validate before sparse copies"),
    )
    with pytest.raises(ValueError, match="ordered"):
        saved.write_ports(tmp_path / "nonfinite.npz", source, CASE)
