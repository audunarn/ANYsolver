"""Exact ordered storage for the 27 F03 trace ports and endpoint operators."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_sparse_storage as sparse_storage
from scripts import _b3_e4_f03_local_scientific_storage as storage
from scripts import _b3_e4_f03_sparse_trace_binding as trace


PORTS = len(trace.KEYS)


@dataclass(frozen=True, slots=True)
class PortCounts:
    ports: tuple[int, ...]
    root: int
    tip: int
    free_slope: int

    def __post_init__(self):
        if (
            type(self.ports) is not tuple
            or len(self.ports) != PORTS
            or any(type(value) is not int or value < 0 for value in self.ports)
            or any(type(value) is not int or value <= 0 for value in (
                self.root, self.tip, self.free_slope,
            ))
        ):
            raise ValueError("complete nonnegative F03 trace-port counts required")


@dataclass(frozen=True, slots=True)
class PortEvidence:
    samples: tuple[trace.SavedPort, ...]
    root: object
    tip: object
    free_slope: object


def _case(value: cases.ScientificCase) -> cases.ScientificCase:
    if type(value) is not cases.ScientificCase or value not in cases.CASES:
        raise ValueError("frozen F03 scientific case required")
    return value


def port_specs(
    case: cases.ScientificCase, counts: PortCounts,
) -> tuple[tuple[sparse_storage.SparseSpec, ...], tuple[storage.ArraySpec, ...]]:
    case = _case(case)
    if type(counts) is not PortCounts:
        raise ValueError("exact F03 trace-port counts required")
    port_limit = 3 * case.max_active_trace_dofs
    if (
        any(value > port_limit for value in counts.ports)
        or counts.root > port_limit
        or counts.tip > port_limit
        or counts.free_slope > case.max_active_trace_dofs
    ):
        raise ValueError("F03 trace-port count exceeds topology envelope")
    n = case.physical_dofs
    matrices = tuple(
        sparse_storage.SparseSpec(f"port_{index:02d}", (3, n), count, "csr")
        for index, count in enumerate(counts.ports)
    ) + (
        sparse_storage.SparseSpec("root", (3, n), counts.root, "csr"),
        sparse_storage.SparseSpec("tip", (3, n), counts.tip, "csr"),
        sparse_storage.SparseSpec("free_slope", (1, n), counts.free_slope, "csr"),
    )
    return matrices, (storage.ArraySpec("actions", (PORTS, 3), np.dtype("<f8")),)


def _validate(value: PortEvidence) -> tuple[dict[str, object], np.ndarray]:
    if (
        type(value) is not PortEvidence
        or type(value.samples) is not tuple
        or len(value.samples) != PORTS
    ):
        raise ValueError("typed complete F03 trace-port evidence required")
    actions = []
    matrices = {}
    for index, (sample, key) in enumerate(zip(value.samples, trace.KEYS)):
        if (
            type(sample) is not trace.SavedPort
            or (sample.station, sample.order, sample.side) != key
            or type(sample.action) is not np.ndarray
            or sample.action.dtype != np.float64
            or sample.action.shape != (3,)
            or not sample.action.flags.c_contiguous
            or not np.isfinite(sample.action).all()
        ):
            raise ValueError("ordered finite F03 trace-port action inventory required")
        matrices[f"port_{index:02d}"] = sample.operator
        actions.append(sample.action)
    matrices.update(root=value.root, tip=value.tip, free_slope=value.free_slope)
    return matrices, np.stack(actions)


def write_ports(
    path: Path, value: PortEvidence, case: cases.ScientificCase,
) -> PortCounts:
    matrices, actions = _validate(value)
    counts = PortCounts(
        tuple(matrices[f"port_{index:02d}"].nnz for index in range(PORTS)),
        matrices["root"].nnz, matrices["tip"].nnz, matrices["free_slope"].nnz,
    )
    sparse_specs, array_specs = port_specs(case, counts)
    for spec in sparse_specs:
        sparse_storage._check_matrix(matrices[spec.name], spec)
    encoded = sparse_storage.encode(matrices, sparse_specs)
    encoded["actions"] = np.asarray(actions, dtype="<f8").copy()
    specs = sparse_storage.array_specs(sparse_specs) + array_specs
    bound = sum(spec.nbytes + storage.MAX_ZIP_MEMBER_OVERHEAD for spec in specs)
    storage.write_group(path, encoded, specs, max_raw_bytes=bound)
    return counts


def read_ports(
    path: Path, case: cases.ScientificCase, counts: PortCounts,
) -> PortEvidence:
    sparse_specs, array_specs = port_specs(case, counts)
    specs = sparse_storage.array_specs(sparse_specs) + array_specs
    bound = sum(spec.nbytes + storage.MAX_ZIP_MEMBER_OVERHEAD for spec in specs)
    encoded = storage.read_group(path, specs, max_raw_bytes=bound)
    matrix_names = {spec.name for spec in sparse_storage.array_specs(sparse_specs)}
    matrices = sparse_storage.decode(
        {name: item for name, item in encoded.items() if name in matrix_names}, sparse_specs,
    )
    actions = np.asarray(encoded["actions"], dtype=np.float64).copy()
    samples = tuple(
        trace.SavedPort(station, order, side, matrices[f"port_{index:02d}"], actions[index].copy())
        for index, (station, order, side) in enumerate(trace.KEYS)
    )
    return PortEvidence(samples, matrices["root"], matrices["tip"], matrices["free_slope"])
