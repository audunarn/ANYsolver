"""Exact-shape storage adapters for the three saved F03 component inputs.

The adapters serialize already-produced observations.  Reconstruction uses
only the frozen topology contract and performs no assembly, factorization, or
equilibrium solve.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_storage as storage
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_work_checks as work


def _case(value: cases.ScientificCase) -> cases.ScientificCase:
    if type(value) is not cases.ScientificCase or value not in cases.CASES:
        raise ValueError("frozen F03 scientific case required")
    return value


def interface_specs(case: cases.ScientificCase) -> tuple[storage.ArraySpec, ...]:
    ni = _case(case).station_intervals
    return (
        storage.ArraySpec("density", (ni, 3, 6), np.dtype("<f8")),
        storage.ArraySpec("cosine", (3,), np.dtype("<f8")),
        storage.ArraySpec("atoms", (2, 3), np.dtype("<f8")),
        storage.ArraySpec("band_analytic", (8, 3), np.dtype("<f8")),
        storage.ArraySpec("band48", (8, 3), np.dtype("<f8")),
        storage.ArraySpec("band64", (8, 3), np.dtype("<f8")),
        storage.ArraySpec("line_band_analytic", (8, 3), np.dtype("<f8")),
    )


def work_specs(case: cases.ScientificCase) -> tuple[storage.ArraySpec, ...]:
    case = _case(case)
    ni = case.station_intervals
    count = ni * (case.degree + 2) + 1
    return (
        storage.ArraySpec("lift_coefficients", (6, ni, 3, 6), np.dtype("<f8")),
        storage.ArraySpec("shell_work", (6,), np.dtype("<f8")),
        storage.ArraySpec("interface_work", (6,), np.dtype("<f8")),
        storage.ArraySpec("edge_route1", (6,), np.dtype("<f8")),
        storage.ArraySpec("edge_route2", (6,), np.dtype("<f8")),
        storage.ArraySpec("first_free", (2,), np.dtype("<f8")),
        storage.ArraySpec("shift_delta", (2,), np.dtype("<f8")),
        storage.ArraySpec("virtual_terms", (3, count, 4), np.dtype("<f8")),
        storage.ArraySpec("virtual_defects", (3, count), np.dtype("<f8")),
    )


def norm_specs() -> tuple[storage.ArraySpec, ...]:
    return (
        storage.ArraySpec("channels", (2, 3), np.dtype("<f8"), finite=False),
        storage.ArraySpec("totals", (2,), np.dtype("<f8"), finite=False),
        storage.ArraySpec("components", (2, 3, 6), np.dtype("<f8"), finite=False),
        storage.ArraySpec("channel_flags", (2, 3, 3), np.dtype("|b1"), finite=False),
        storage.ArraySpec("total_flags", (2, 3), np.dtype("|b1"), finite=False),
        storage.ArraySpec("exact_zero", (2,), np.dtype("|b1"), finite=False),
    )


def group_bound(specs: tuple[storage.ArraySpec, ...]) -> int:
    if type(specs) is not tuple or not specs:
        raise ValueError("exact F03 saved group schema required")
    return sum(spec.nbytes + storage.MAX_ZIP_MEMBER_OVERHEAD for spec in specs)


def _canonical_arrays(value: object, specs: tuple[storage.ArraySpec, ...]) -> dict[str, np.ndarray]:
    observed = []
    for spec in specs:
        item = getattr(value, spec.name, None)
        native = np.dtype(np.float64) if spec.dtype.kind == "f" else spec.dtype
        if (
            type(item) is not np.ndarray
            or item.shape != spec.shape
            or item.dtype != native
            or not item.flags.c_contiguous
            or (
                spec.dtype.kind == "f"
                and spec.finite
                and not np.isfinite(item).all()
            )
            or (spec.dtype.kind == "f" and np.isinf(item).any())
        ):
            raise ValueError(f"invalid saved F03 component array: {spec.name}")
        observed.append(item)
    if any(
        np.shares_memory(first, second)
        for index, first in enumerate(observed)
        for second in observed[index + 1:]
    ):
        raise ValueError("aliased saved F03 component arrays")
    return {
        spec.name: np.asarray(item, dtype=spec.dtype).copy()
        for spec, item in zip(specs, observed)
    }


def _native_arrays(
    arrays: dict[str, np.ndarray], specs: tuple[storage.ArraySpec, ...],
) -> dict[str, np.ndarray]:
    if type(arrays) is not dict or set(arrays) != {spec.name for spec in specs}:
        raise ValueError("invalid saved F03 component inventory")
    for spec in specs:
        storage._check_array(arrays[spec.name], spec)
    return {
        spec.name: np.asarray(
            arrays[spec.name],
            dtype=np.float64 if spec.dtype.kind == "f" else spec.dtype,
        ).copy()
        for spec in specs
    }


def write_interface(path: Path, value: interface.SavedInterface, case: cases.ScientificCase) -> None:
    case = _case(case)
    grid = cases.compile_case(case)
    if type(value) is not interface.SavedInterface or value.cuts != grid.station_cuts:
        raise ValueError("saved interface does not match frozen F03 topology")
    specs = interface_specs(case)
    storage.write_group(
        path, _canonical_arrays(value, specs), specs, max_raw_bytes=group_bound(specs),
    )


def read_interface(path: Path, case: cases.ScientificCase) -> interface.SavedInterface:
    case = _case(case)
    specs = interface_specs(case)
    arrays = _native_arrays(
        storage.read_group(path, specs, max_raw_bytes=group_bound(specs)), specs,
    )
    return interface.SavedInterface(cases.compile_case(case).station_cuts, **arrays)


def write_work(path: Path, value: work.SavedWork, case: cases.ScientificCase) -> None:
    case = _case(case)
    grid = cases.compile_case(case)
    expected = "Q1_EDGE_ROTATION" if case.degree == 1 else "Q2_Q3_CLASSICAL_ROTATION"
    if (
        type(value) is not work.SavedWork
        or value.p != case.degree
        or value.cuts != grid.station_cuts
        or value.lift_family != expected
    ):
        raise ValueError("saved work does not match frozen F03 topology")
    specs = work_specs(case)
    storage.write_group(
        path, _canonical_arrays(value, specs), specs, max_raw_bytes=group_bound(specs),
    )


def read_work(path: Path, case: cases.ScientificCase) -> work.SavedWork:
    case = _case(case)
    specs = work_specs(case)
    arrays = _native_arrays(
        storage.read_group(path, specs, max_raw_bytes=group_bound(specs)), specs,
    )
    family = "Q1_EDGE_ROTATION" if case.degree == 1 else "Q2_Q3_CLASSICAL_ROTATION"
    return work.SavedWork(
        case.degree, cases.compile_case(case).station_cuts, family, **arrays,
    )


def write_norm(path: Path, value: norm.SavedNorm) -> None:
    if type(value) is not norm.SavedNorm:
        raise ValueError("validated saved F03 norm required")
    specs = norm_specs()
    storage.write_group(
        path, _canonical_arrays(value, specs), specs, max_raw_bytes=group_bound(specs),
    )


def read_norm(path: Path, failures: tuple) -> norm.SavedNorm:
    specs = norm_specs()
    arrays = _native_arrays(
        storage.read_group(path, specs, max_raw_bytes=group_bound(specs)), specs,
    )
    return norm.SavedNorm(**arrays, failures=failures)
