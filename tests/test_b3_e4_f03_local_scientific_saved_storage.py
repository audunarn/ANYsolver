import numpy as np
import pytest

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_saved_storage as saved
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_work_checks as work


def _interface(case):
    ni = case.station_intervals
    grid = cases.compile_case(case)
    return interface.SavedInterface(
        grid.station_cuts,
        np.arange(ni * 18, dtype=np.float64).reshape(ni, 3, 6),
        np.arange(3, dtype=np.float64),
        np.arange(6, dtype=np.float64).reshape(2, 3),
        np.arange(24, dtype=np.float64).reshape(8, 3),
        np.arange(24, dtype=np.float64).reshape(8, 3) + 1,
        np.arange(24, dtype=np.float64).reshape(8, 3) + 2,
        np.arange(24, dtype=np.float64).reshape(8, 3) + 3,
    )


def _work(case):
    ni = case.station_intervals
    count = ni * (case.degree + 2) + 1
    grid = cases.compile_case(case)
    family = "Q1_EDGE_ROTATION" if case.degree == 1 else "Q2_Q3_CLASSICAL_ROTATION"
    return work.SavedWork(
        case.degree,
        grid.station_cuts,
        family,
        np.zeros((6, ni, 3, 6)),
        *(np.arange(6, dtype=np.float64) + shift for shift in range(4)),
        np.arange(2, dtype=np.float64),
        np.arange(2, dtype=np.float64) + 2,
        np.arange(3 * count * 4, dtype=np.float64).reshape(3, count, 4),
        np.arange(3 * count, dtype=np.float64).reshape(3, count),
    )


def _norm():
    components = np.arange(36, dtype=np.float64).reshape(2, 3, 6)
    components[1, 2, 5] = np.nan
    return norm.SavedNorm(
        np.arange(6, dtype=np.float64).reshape(2, 3),
        np.array([1.0, np.nan]),
        components,
        np.ones((2, 3, 3), dtype=np.bool_),
        np.ones((2, 3), dtype=np.bool_),
        np.array([False, True]),
        ((), (("total", None, "unavailable"),)),
    )


@pytest.mark.parametrize("case", cases.CASES)
def test_exact_saved_component_schemas_cover_every_case(case):
    assert saved.interface_specs(case)[0].shape == (case.station_intervals, 3, 6)
    count = case.station_intervals * (case.degree + 2) + 1
    assert saved.work_specs(case)[-1].shape == (3, count)
    assert saved.group_bound(saved.interface_specs(case)) > sum(
        spec.nbytes for spec in saved.interface_specs(case)
    )


@pytest.mark.parametrize("case", (cases.CASES[0], cases.CASES[-1]))
def test_interface_and_work_roundtrip_from_frozen_topology(case, tmp_path):
    source_interface = _interface(case)
    source_work = _work(case)
    saved.write_interface(tmp_path / "saved_interface.npz", source_interface, case)
    saved.write_work(tmp_path / "saved_work.npz", source_work, case)
    restored_interface = saved.read_interface(tmp_path / "saved_interface.npz", case)
    restored_work = saved.read_work(tmp_path / "saved_work.npz", case)
    assert restored_interface.cuts == source_interface.cuts
    assert restored_work.cuts == source_work.cuts
    for spec in saved.interface_specs(case):
        np.testing.assert_array_equal(
            getattr(restored_interface, spec.name), getattr(source_interface, spec.name),
        )
    for spec in saved.work_specs(case):
        np.testing.assert_array_equal(
            getattr(restored_work, spec.name), getattr(source_work, spec.name),
        )


def test_norm_roundtrip_preserves_nan_flags_and_explicit_failures(tmp_path):
    source = _norm()
    saved.write_norm(tmp_path / "saved_norm.npz", source)
    restored = saved.read_norm(tmp_path / "saved_norm.npz")
    for spec in saved.norm_specs()[:-2]:
        observed = getattr(restored, spec.name)
        expected = getattr(source, spec.name)
        if spec.dtype.kind == "f":
            assert np.array_equal(observed, expected, equal_nan=True)
        else:
            np.testing.assert_array_equal(observed, expected)
    assert restored.failures == source.failures


def test_norm_failure_metadata_changes_archive_and_needs_no_caller_input(tmp_path):
    first = _norm()
    second = _norm()
    object.__setattr__(second, "failures", ((), (("other", 1, "different"),)))
    one = tmp_path / "one.npz"
    two = tmp_path / "two.npz"
    saved.write_norm(one, first)
    saved.write_norm(two, second)
    assert one.read_bytes() != two.read_bytes()
    assert saved.read_norm(two).failures == second.failures


def test_topology_mismatch_alias_and_infinity_rejected_before_storage(tmp_path):
    first, second = cases.CASES[:2]
    with pytest.raises(ValueError, match="topology"):
        saved.write_interface(tmp_path / "bad.npz", _interface(first), second)
    value = _norm()
    object.__setattr__(value, "totals", value.channels.reshape(-1)[:2])
    with pytest.raises(ValueError, match="aliased"):
        saved.write_norm(tmp_path / "alias.npz", value)
    value = _norm()
    channels = value.channels.copy()
    channels[0, 0] = np.inf
    object.__setattr__(value, "channels", channels)
    with pytest.raises(ValueError, match="array"):
        saved.write_norm(tmp_path / "infinite.npz", value)


def test_canonical_and_native_conversion_are_value_preserving():
    specs = saved.norm_specs()[:-2]
    source = _norm()
    arrays = saved._canonical_arrays(source, specs)
    assert all(value.dtype == spec.dtype for spec, value in zip(specs, arrays.values()))
    native = saved._native_arrays(arrays, specs)
    assert all(
        value.dtype == (np.dtype(np.float64) if spec.dtype.kind == "f" else spec.dtype)
        for spec, value in zip(specs, native.values())
    )


def test_hostile_infinity_rejected_before_first_native_copy(tmp_path, monkeypatch):
    source = _norm()
    specs = saved.norm_specs()
    arrays = saved._canonical_arrays(source, specs[:-2])
    arrays.update(saved._failure_arrays(source.failures))
    arrays["channels"][0, 0] = np.inf
    from scripts import _b3_e4_f03_local_scientific_storage as raw
    raw.write_group(
        tmp_path / "hostile.npz", arrays, specs, max_raw_bytes=saved.group_bound(specs),
    )
    monkeypatch.setattr(
        saved, "_native_copy", lambda *a, **k: pytest.fail("must reject before copy"),
    )
    with pytest.raises(ValueError, match="infinite"):
        saved.read_norm(tmp_path / "hostile.npz")
