"""Private B2 sparse affine batch feasibility; no public mixed-profile dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np
from scipy import sparse

from ._b2_physical_linear_definition import CompiledPhysicalB2Member
from .control import CancellationToken
from .linalg import FactorizationCache, MatrixClass, factorize_cached


@dataclass(frozen=True)
class SelectedMemberRecovery:
    member_id: str
    stations: tuple[float, ...]
    resultants_local: tuple[tuple[float, ...], ...]
    strains_local: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class SelectedCase:
    case_id: str
    values: tuple[float, ...]
    members: tuple[SelectedMemberRecovery, ...] = ()


@dataclass(frozen=True)
class BatchResult:
    status: str
    cases: tuple[SelectedCase, ...]
    factorization_count: int
    solve_count: int
    maximum_rhs_chunk: int
    production_qualified: bool = False


class CompiledB2AffineBatch:
    """Bounded graph/affine prototype with one owned sparse factorization."""

    def __init__(self, members: Sequence[CompiledPhysicalB2Member],
                 transformation: sparse.spmatrix, prescribed_offset,
                 selected_dofs, *, max_chunk: int = 8,
                 factorization_cache: FactorizationCache | None = None):
        compiled = tuple(members)
        if not compiled or any(not isinstance(m, CompiledPhysicalB2Member)
                               for m in compiled):
            raise ValueError("compiled physical B2 members required")
        if type(max_chunk) is not int or max_chunk <= 0:
            raise ValueError("positive bounded RHS chunk required")
        if factorization_cache is not None and not isinstance(
                factorization_cache, FactorizationCache):
            raise ValueError("local factorization cache required")
        ids = [m.definition.member_id for m in compiled]
        if len(set(ids)) != len(ids):
            raise ValueError("unique physical B2 member IDs required")
        points = {}
        for member in compiled:
            for node_id, point in zip(member.definition.node_ids,
                                      member.definition.reference_points_m):
                old = points.setdefault(node_id, point)
                if old != point:
                    raise ValueError("shared B2 node has inconsistent position")
        ordered = tuple(sorted(points))
        node_index = {node_id: i for i, node_id in enumerate(ordered)}
        size = 6*len(ordered)
        try:
            T = transformation.tocsr(copy=True)
            u0 = np.asarray(prescribed_offset, dtype=float).copy()
            selected_input = np.asarray(selected_dofs)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("finite sparse affine plan and selection required") from exc
        if selected_input.dtype.kind not in "iu":
            raise ValueError("integer selected DOFs required")
        selected = selected_input.astype(int, copy=True)
        if (T.shape[0] != size or T.shape[1] == 0 or
                u0.shape != (size,) or selected.ndim != 1 or
                np.any(selected < 0) or np.any(selected >= size) or
                not np.isfinite(T.data).all() or not np.isfinite(u0).all()):
            raise ValueError("finite sparse affine plan and selection required")
        rows, cols, values = [], [], []
        for member in compiled:
            local = member.operator.evaluate(np.zeros(12)).tangent
            frame = member.local_dof_map()
            stiffness = frame.T@local@frame
            dofs = [6*node_index[node]+j for node in member.definition.node_ids
                    for j in range(6)]
            for i, row in enumerate(dofs):
                for j, col in enumerate(dofs):
                    rows.append(row); cols.append(col); values.append(stiffness[i, j])
        K = sparse.coo_matrix((values, (rows, cols)),
                              shape=(size, size)).tocsr()
        reduced = (T.T@K@T).tocsc()
        diagonal = reduced.diagonal()
        if not np.isfinite(diagonal).all() or np.any(diagonal <= 0.):
            raise RuntimeError(
                "physical B2 batch factorization failed: positive finite diagonal required")
        with np.errstate(over="ignore", under="ignore", divide="ignore",
                         invalid="ignore"):
            scaling = 1./np.sqrt(diagonal)
            scaled = (sparse.diags(scaling)@reduced@sparse.diags(scaling)).tocsc()
        if (not np.isfinite(scaling).all() or np.any(scaling == 0.) or
                not np.isfinite(scaled.data).all() or
                np.any(scaled.diagonal() <= 0.)):
            raise RuntimeError(
                "physical B2 batch factorization failed: diagonal scaling is not representable")
        handle = factorize_cached(
            scaled, MatrixClass.SPD, cache=factorization_cache)
        if handle.status != "ok":
            raise RuntimeError("physical B2 batch factorization failed: " +
                               str(handle.failure_reason))
        self._K = K
        self._reduced = reduced
        self._T = T
        self._u0 = u0
        self._ku0 = np.asarray(K@u0).reshape(-1)
        self._selected = selected
        self._handle = handle
        scaling.setflags(write=False)
        self._scaling = scaling
        self._max_chunk = max_chunk
        self._closed = False
        self.node_ids = ordered
        self.members = compiled
        self._member_layout = {
            member.definition.member_id: (
                member,
                np.array([6*node_index[node]+j
                          for node in member.definition.node_ids
                          for j in range(6)], dtype=int),
                member.local_dof_map(),
            ) for member in compiled
        }

    @property
    def full_stiffness(self) -> sparse.csr_matrix:
        if self._closed:
            raise RuntimeError("physical B2 batch is closed")
        return self._K.copy()

    def close(self) -> None:
        self._closed = True
        self._handle = None

    def solve_many(self, cases: Sequence[tuple[str, np.ndarray]], *,
                   cancellation_token: CancellationToken | None = None,
                   on_case: Callable[[str], None] | None = None,
                   recover_members: Mapping[str, Sequence[float]] | None = None,
                   ) -> BatchResult:
        if self._closed:
            raise RuntimeError("physical B2 batch is closed")
        ids = [identity for identity, _ in cases]
        if (any(not isinstance(identity, str) or not identity.strip()
                for identity in ids) or len(set(ids)) != len(ids)):
            raise ValueError("unique nonempty ordered B2 case IDs required")
        recovery = []
        if recover_members is not None:
            if not isinstance(recover_members, Mapping):
                raise ValueError("selected B2 recovery mapping required")
            for member_id, requested in recover_members.items():
                if member_id not in self._member_layout:
                    raise ValueError("selected B2 member ID is not compiled")
                try:
                    stations = np.asarray(requested, dtype=float).copy()
                except (TypeError, ValueError, OverflowError) as exc:
                    raise ValueError("finite normalized B2 recovery stations required") from exc
                if (stations.ndim != 1 or stations.size == 0 or
                        not np.isfinite(stations).all() or
                        np.any(stations < 0.) or np.any(stations > 1.)):
                    raise ValueError("finite normalized B2 recovery stations required")
                recovery.append((member_id, tuple(float(x) for x in stations)))
        completed = []
        largest = 0
        for start in range(0, len(cases), self._max_chunk):
            if cancellation_token is not None and cancellation_token.is_cancelled:
                break
            block = cases[start:start+self._max_chunk]
            loads = []
            for _identity, value in block:
                load = np.asarray(value, dtype=float)
                if load.shape != self._u0.shape or not np.isfinite(load).all():
                    raise ValueError("finite B2 load vector required")
                loads.append(load.copy())
            largest = max(largest, len(loads))
            rhs = self._T.T@(np.column_stack(loads)-self._ku0[:, None])
            with np.errstate(over="ignore", invalid="ignore"):
                scaled_rhs = self._scaling[:, None]*rhs
            if not np.isfinite(scaled_rhs).all():
                raise RuntimeError("physical B2 scaled load is not representable")
            solved = np.asarray(self._handle.solve_many(scaled_rhs), dtype=float)
            with np.errstate(over="ignore", invalid="ignore"):
                solved = self._scaling[:, None]*solved
            if not np.isfinite(solved).all():
                raise RuntimeError("physical B2 solution is not representable")
            with np.errstate(over="ignore", invalid="ignore"):
                defect = np.asarray(self._reduced@solved-rhs)
                row_scale = (np.abs(self._reduced)@np.abs(solved) +
                             np.abs(rhs))
            if (not np.isfinite(defect).all() or
                    not np.isfinite(row_scale).all() or
                    np.any(np.abs(defect) > 1e-9*row_scale)):
                raise RuntimeError("physical B2 batch solve residual failed")
            selected = self._T[self._selected]@solved
            selected = np.asarray(selected)+self._u0[self._selected, None]
            if not np.isfinite(selected).all():
                raise RuntimeError("physical B2 selected solution is not finite")
            for j, (identity, _value) in enumerate(block):
                if cancellation_token is not None and cancellation_token.is_cancelled:
                    break
                member_results = []
                for member_id, stations in recovery:
                    member, dofs, frame = self._member_layout[member_id]
                    physical = np.asarray(self._T[dofs]@solved[:, j]).reshape(-1)
                    physical += self._u0[dofs]
                    response = member.operator.recover_sections(
                        frame@physical, stations=stations)
                    member_results.append(SelectedMemberRecovery(
                        member_id, stations,
                        tuple(tuple(float(value) for value in row)
                              for row in response.resultants),
                        tuple(tuple(float(value) for value in row)
                              for row in response.strains)))
                    if cancellation_token is not None and cancellation_token.is_cancelled:
                        break
                if cancellation_token is not None and cancellation_token.is_cancelled:
                    break
                completed.append(SelectedCase(
                    identity, tuple(float(v) for v in selected[:, j]),
                    tuple(member_results)))
                if on_case is not None:
                    on_case(identity)
            if cancellation_token is not None and cancellation_token.is_cancelled:
                break
        return BatchResult(
            "cancelled" if cancellation_token is not None and
            cancellation_token.is_cancelled else "completed",
            tuple(completed), self._handle.factorization_count,
            self._handle.solve_count, largest)
