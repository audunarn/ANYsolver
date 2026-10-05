"""Exact-shape storage adapters for the three saved F03 component inputs.

The adapters serialize already-produced observations.  Reconstruction uses
only the frozen topology contract and performs no assembly, factorization, or
equilibrium solve.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_storage as storage
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_work_checks as work


MAX_NORM_FAILURE_BYTES = 64 * 1024


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
        storage.ArraySpec(
            "failures_json", (MAX_NORM_FAILURE_BYTES,), np.dtype("|u1"), finite=False,
        ),
        storage.ArraySpec("failures_length", (1,), np.dtype("<i8")),
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
        if spec.dtype.kind == "f" and np.isinf(arrays[spec.name]).any():
            raise ValueError(f"infinite saved F03 component array: {spec.name}")
    return {
        spec.name: _native_copy(arrays[spec.name], spec)
        for spec in specs
    }


def _native_copy(value: np.ndarray, spec: storage.ArraySpec) -> np.ndarray:
    return np.asarray(
        value, dtype=np.float64 if spec.dtype.kind == "f" else spec.dtype,
    ).copy()


def _failure_payload(failures: tuple) -> bytes:
    try:
        payload = (
            json.dumps(failures, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            + "\n"
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("invalid saved F03 norm failure metadata") from exc
    if len(payload) > MAX_NORM_FAILURE_BYTES:
        raise ValueError("saved F03 norm failure metadata exceeds bound")
    return payload


def _failure_arrays(failures: tuple) -> dict[str, np.ndarray]:
    # The SavedNorm constructor is the authority for record shape and bounds.
    probe = norm.SavedNorm(
        np.zeros((2, 3)), np.zeros(2), np.zeros((2, 3, 6)),
        np.zeros((2, 3, 3), dtype=np.bool_), np.zeros((2, 3), dtype=np.bool_),
        np.zeros(2, dtype=np.bool_), failures,
    )
    payload = _failure_payload(probe.failures)
    buffer = np.zeros(MAX_NORM_FAILURE_BYTES, dtype=np.uint8)
    buffer[:len(payload)] = np.frombuffer(payload, dtype=np.uint8)
    return {
        "failures_json": buffer,
        "failures_length": np.array([len(payload)], dtype="<i8"),
    }


def _decode_failures(arrays: dict[str, np.ndarray]) -> tuple:
    length = arrays["failures_length"]
    data = arrays["failures_json"]
    if (
        length.shape != (1,)
        or type(length[0].item()) is not int
        or not 0 < int(length[0]) <= MAX_NORM_FAILURE_BYTES
        or np.any(data[int(length[0]):] != 0)
    ):
        raise ValueError("invalid saved F03 norm failure envelope")
    payload = data[:int(length[0])].tobytes()
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid saved F03 norm failure JSON") from exc
    failures = tuple(tuple(tuple(record) for record in group) for group in value)
    if _failure_payload(failures) != payload:
        raise ValueError("noncanonical saved F03 norm failure metadata")
    return failures


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
    base_specs = specs[:-2]
    arrays = _canonical_arrays(value, base_specs)
    arrays.update(_failure_arrays(value.failures))
    storage.write_group(
        path, arrays, specs, max_raw_bytes=group_bound(specs),
    )


def read_norm(path: Path) -> norm.SavedNorm:
    specs = norm_specs()
    arrays = _native_arrays(
        storage.read_group(path, specs, max_raw_bytes=group_bound(specs)), specs,
    )
    failures = _decode_failures(arrays)
    return norm.SavedNorm(
        **{spec.name: arrays[spec.name] for spec in specs[:-2]}, failures=failures,
    )
