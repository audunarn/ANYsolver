"""Small elastic multi-Q4/multi-B2 panel with existing F10 point joints.

This is an experimental reference-linear owner. Shell and beam node identities
are explicit and separate. Reference modes require explicit physical mass.
No line, footprint, geometric stiffness, nonlinear state or qualification is
inferred from the point-joint assembly.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Callable, Mapping, Sequence

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, eigs, ArpackError
from scipy.sparse.csgraph import maximum_bipartite_matching

from ._b2_f10_f11_point_attachment import LAW_ID, compile_reference_point
from ._b2_physical_linear_definition import (
    PROFILE_ID, CompiledPhysicalB2Member, PhysicalB2Member,
    PhysicalB2OperatorCache,
)
from ._b2_physical_linear_batch_dev import _load_value_snapshot
from .control import CancellationToken, SolveCancelled
from ._stiffened_shell_physical_q4_mass import physical_mass
from .e4_pl_element import QualifiedE4PLShellElement
from .fe_core import FEModel
from .linalg import MatrixClass, factorize_cached


class ExperimentalB2Q4PanelError(RuntimeError):
    """The experimental panel cannot be prepared or used."""


class _NumericalFailure(RuntimeError):
    """A checked sparse panel solution failed numerically."""


_MAX_DENSE_AUDIT_ROWS = 48
_MAX_DENSE_AUDIT_VALUES = 16_384


def _scaled_point_kkt(reduced_k: sparse.spmatrix,
                      reduced_c: sparse.spmatrix) -> tuple[sparse.csc_matrix, np.ndarray]:
    """Representable congruence for the elastic point-constrained KKT.

    A zero-energy primal coordinate is valid when a constraint anchors it;
    its scale then follows that constraint column. This owner admits no
    negative-energy primal diagonal or unanchored zero-energy coordinate.
    """
    diagonal = reduced_k.diagonal()
    if not np.isfinite(diagonal).all() or np.any(diagonal < 0.):
        raise ExperimentalB2Q4PanelError(
            "panel factorization requires nonnegative finite primal diagonal")
    primal_scale = np.empty(len(diagonal))
    positive = diagonal > 0.
    with np.errstate(over="ignore", under="ignore", divide="ignore",
                     invalid="ignore"):
        primal_scale[positive] = 1./np.sqrt(diagonal[positive])
        if np.any(~positive):
            # For a positive-semidefinite elastic K, a zero diagonal has a
            # zero row. An off-diagonal term instead signals invalid data.
            zero_rows = reduced_k.tocsr()[np.flatnonzero(~positive)]
            if np.any(zero_rows.data != 0.):
                raise ExperimentalB2Q4PanelError(
                    "zero-energy primal row has nonzero stiffness coupling")
            column_max = np.asarray(
                abs(reduced_c).max(axis=0).toarray()).reshape(-1)
            if (not np.isfinite(column_max[~positive]).all() or
                    np.any(column_max[~positive] <= 0.)):
                raise ExperimentalB2Q4PanelError(
                    "unanchored zero-energy primal coordinate")
            primal_scale[~positive] = 1./column_max[~positive]
        if (not np.isfinite(primal_scale).all() or
                np.any(primal_scale <= 0.)):
            raise ExperimentalB2Q4PanelError(
                "panel factorization scaling is not representable")
        scaled_rows = reduced_c @ sparse.diags(primal_scale)
        row_max = np.asarray(abs(scaled_rows).max(axis=1).toarray()).reshape(-1)
        multiplier_scale = 1./row_max
        factor_scale = np.r_[primal_scale, multiplier_scale]
        kkt = sparse.bmat(
            ((reduced_k, reduced_c.T), (reduced_c, None)), format="csc")
        scaling = sparse.diags(factor_scale, format="csc")
        scaled_kkt = (scaling @ kkt @ scaling).tocsc()
    kkt.sort_indices()
    scaled_kkt.sort_indices()
    if (not np.isfinite(factor_scale).all() or
            np.any(factor_scale <= 0.) or
            not np.isfinite(scaled_kkt.data).all() or
            kkt.nnz != scaled_kkt.nnz or
            not np.array_equal(kkt.indptr, scaled_kkt.indptr) or
            not np.array_equal(kkt.indices, scaled_kkt.indices) or
            np.any((kkt.data != 0.) & (scaled_kkt.data == 0.))):
        raise ExperimentalB2Q4PanelError(
            "panel factorization scaling is not representable")
    return scaled_kkt, factor_scale


def _require_independent_supported_point_rows(reduced_c: sparse.spmatrix) -> None:
    """Bound the dense audit; defer large numerical rank to KKT factorization.

    A matching proves only structural rank. The subsequent sparse KKT
    factorization must still reject numerical row dependence for larger models.
    """
    rows, columns = reduced_c.shape
    if rows > columns or not np.isfinite(reduced_c.data).all():
        raise ValueError("independent supported point rows required")
    if rows <= _MAX_DENSE_AUDIT_ROWS and rows*columns <= _MAX_DENSE_AUDIT_VALUES:
        if np.linalg.matrix_rank(reduced_c.toarray()) != rows:
            raise ValueError("independent supported point rows required")
        return
    pattern = reduced_c.tocsr(copy=True)
    pattern.eliminate_zeros()
    matching = maximum_bipartite_matching(pattern, perm_type="column")
    if np.any(matching < 0):
        raise ValueError("structurally independent supported point rows required")


@dataclass(frozen=True)
class Q4PanelShell:
    shell_id: str
    node_ids: tuple[int, int, int, int]
    E: float
    nu: float
    thickness_m: float
    reference_normal: tuple[float, float, float] = (0., 0., 1.)
    density_kg_m3: float | None = None


@dataclass(frozen=True)
class Q4B2Point:
    point_id: str
    shell_id: str
    member_id: str
    station: float
    offset_local_m: tuple[float, float, float] = (0., 0., 0.)


@dataclass(frozen=True)
class ExperimentalB2Q4PanelCapabilities:
    profile_id: str = PROFILE_ID
    point_law_id: str = LAW_ID
    status: str = "experimental"
    production_qualified: bool = False
    shell_domain: str = "multiple flat elastic Q4"
    beam_domain: str = "multiple physical B2 members"
    attachment: str = "F10 reference points only"
    operations: tuple[str, ...] = ("solve_linear", "solve_linear_many", "close")
    spectral_domain: str = "unavailable without explicit physical mass"


@dataclass(frozen=True)
class B2ReferenceModesRequest:
    """Supported elastic reference modes; no prestress or rigid-mode request."""

    count: int = 3
    shift_hz: float = 1.
    max_iterations: int = 600

    def __post_init__(self):
        if (type(self.count) is not int or self.count <= 0 or
                type(self.max_iterations) is not int or self.max_iterations <= 0 or
                isinstance(self.shift_hz, (bool, np.bool_)) or
                not isinstance(self.shift_hz, (int, float, np.floating)) or
                not np.isfinite(self.shift_hz) or self.shift_hz <= 0.):
            raise ValueError("positive finite reference-mode controls required")


@dataclass(frozen=True)
class B2ReferenceModesResult:
    status: str
    frequencies_hz: tuple[float, ...] = ()
    physical_modes: tuple[tuple[float, ...], ...] = ()
    point_multiplier_modes: tuple[tuple[float, ...], ...] = ()
    equation_residuals: tuple[float, ...] = ()
    constraint_residuals: tuple[float, ...] = ()
    factorization_count: int = 0
    solve_count: int = 0
    failure_reason: str | None = None
    production_qualified: bool = False


@dataclass(frozen=True)
class ExperimentalB2Q4PanelResult:
    status: str
    displacements: tuple[float, ...] = ()
    point_multipliers: tuple[tuple[str, tuple[float, ...]], ...] = ()
    affine_reactions: tuple[float, ...] = ()
    point_gaps: tuple[tuple[str, tuple[float, ...]], ...] = ()
    beam_resultants_local: tuple[tuple[str, tuple[tuple[float, ...], ...]], ...] = ()
    internal_strain_energy: float | None = None
    factorization_count: int | None = None
    solve_count: int | None = None
    failure_reason: str | None = None
    production_qualified: bool = False


@dataclass(frozen=True)
class ExperimentalB2Q4PanelSelectedCase:
    case_id: str
    selected_displacements: tuple[float, ...]
    selected_affine_reactions: tuple[float, ...]
    point_multipliers: tuple[tuple[str, tuple[float, ...]], ...]
    point_gaps: tuple[tuple[str, tuple[float, ...]], ...]
    beam_resultants_local: tuple[tuple[str, tuple[tuple[float, ...], ...]], ...]
    internal_strain_energy: float


@dataclass(frozen=True)
class ExperimentalB2Q4PanelBatchResult:
    status: str
    selected_dofs: tuple[int, ...]
    selected_points: tuple[str, ...]
    cases: tuple[ExperimentalB2Q4PanelSelectedCase, ...]
    factorization_count: int
    solve_count: int
    maximum_rhs_chunk: int = 1
    failure_reason: str | None = None
    production_qualified: bool = False


def _unique_ids(items, name):
    ids = [getattr(item, name) for item in items]
    if any(not isinstance(value, str) or not value.strip() for value in ids):
        raise ValueError(f"nonempty {name} required")
    if len(set(ids)) != len(ids):
        raise ValueError(f"unique {name} required")


def _checked_recovery(recover_members, available):
    if recover_members is None:
        return None
    if not isinstance(recover_members, Mapping):
        raise ValueError("selected physical B2 recovery mapping required")
    selected = {}
    for member_id, requested in recover_members.items():
        if member_id not in available:
            raise ValueError("selected physical B2 member is not compiled")
        try:
            stations = np.asarray(requested, dtype=float).copy()
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("finite normalized recovery stations required") from exc
        if (stations.ndim != 1 or not len(stations) or
                not np.isfinite(stations).all() or
                np.any((stations < 0.) | (stations > 1.))):
            raise ValueError("finite normalized recovery stations required")
        selected[member_id] = tuple(float(value) for value in stations)
    return selected


def _flat_vertices(vertices):
    base = vertices[0]
    normal = np.cross(vertices[1]-base, vertices[3]-base)
    diameter = max(np.linalg.norm(a-b) for a in vertices for b in vertices)
    magnitude = np.linalg.norm(normal)
    if (not isfinite(diameter) or diameter <= 0. or
            magnitude <= 1e-12*diameter**2 or
            abs((vertices[2]-base) @ normal) > 1e-10*diameter*magnitude):
        raise ValueError("nondegenerate flat Q4 shell required")


def _require_connected_panel(shells, members, points):
    """Check physical incidence without forming a numerical constraint matrix."""
    neighbours = {(0, shell.shell_id): set() for shell in shells}
    neighbours.update({(1, member.member_id): set() for member in members})

    def join(a, b):
        neighbours[a].add(b)
        neighbours[b].add(a)

    for kind, entities in ((0, shells), (1, members)):
        owners = {}
        for entity in entities:
            key = (kind, entity.shell_id if kind == 0 else entity.member_id)
            if (kind == 0 and (type(entity.node_ids) is not tuple or
                    len(entity.node_ids) != 4 or
                    any(type(node_id) is not int for node_id in entity.node_ids))):
                raise ValueError("four integer Q4 nodes required")
            for node_id in entity.node_ids:
                previous = owners.setdefault(node_id, key)
                join(key, previous)
    for point in points:
        shell_key, member_key = (0, point.shell_id), (1, point.member_id)
        if shell_key not in neighbours or member_key not in neighbours:
            raise ValueError("point host IDs must identify declared elements")
        join(shell_key, member_key)
    first = next(iter(neighbours))
    visited = {first}
    pending = [first]
    while pending:
        for other in neighbours[pending.pop()]-visited:
            visited.add(other)
            pending.append(other)
    if len(visited) != len(neighbours):
        raise ValueError("connected shell/beam point panel required")


class ExperimentalB2Q4PanelAnalysis:
    """Own one connected point-coupled reference-linear panel and factorization.

    The coordinate order is sorted shell node IDs, then sorted beam node IDs,
    six global translations/rotations for each. Affine ``T/u0`` is supplied
    in that order. Reactions are affine reactions; they are support reactions
    only when the affine plan fixes coordinates without other MPCs.
    """

    def __init__(self, shell_nodes_m: Mapping[int, Sequence[float]],
                 shells: Sequence[Q4PanelShell],
                 members: Sequence[PhysicalB2Member | CompiledPhysicalB2Member],
                 points: Sequence[Q4B2Point], *,
                 transformation: sparse.spmatrix, prescribed_offset):
        shells = tuple(shells)
        supplied_members = tuple(members)
        points = tuple(points)
        if (len(shells) < 2 or len(supplied_members) < 2 or not points or
                any(not isinstance(shell, Q4PanelShell) for shell in shells) or
                any(not isinstance(member, (PhysicalB2Member,
                                            CompiledPhysicalB2Member))
                    for member in supplied_members) or
                any(not isinstance(point, Q4B2Point) for point in points)):
            raise ValueError("multi-Q4/multi-B2 physical point panel required")
        _unique_ids(shells, "shell_id")
        _unique_ids(points, "point_id")
        definitions = tuple(member.definition if isinstance(
            member, CompiledPhysicalB2Member) else member
            for member in supplied_members)
        _unique_ids(definitions, "member_id")
        _require_connected_panel(shells, definitions, points)
        cache = PhysicalB2OperatorCache()
        compiled = tuple(
            member if isinstance(member, CompiledPhysicalB2Member)
            else member.compile_local(operator_cache=cache)
            for member in supplied_members)
        shell_ids = tuple(sorted(shell_nodes_m))
        if any(type(node_id) is not int for node_id in shell_ids):
            raise ValueError("integer shell node IDs required")
        positions = {}
        for node_id in shell_ids:
            vector = np.array(shell_nodes_m[node_id], dtype=float, copy=True)
            if vector.shape != (3,) or not np.isfinite(vector).all():
                raise ValueError("finite shell node coordinates required")
            positions[node_id] = vector
        used_shell_nodes = {node_id for shell in shells for node_id in shell.node_ids}
        if used_shell_nodes != set(shell_ids):
            raise ValueError("every declared shell node must belong to a Q4")
        shell_index = {node_id: i for i, node_id in enumerate(shell_ids)}
        beam_positions = {}
        for member in definitions:
            for node_id, point in zip(member.node_ids, member.reference_points_m):
                old = beam_positions.setdefault(node_id, point)
                if old != point:
                    raise ValueError("shared B2 node has inconsistent position")
        beam_ids = tuple(sorted(beam_positions))
        beam_index = {node_id: i+len(shell_ids)
                      for i, node_id in enumerate(beam_ids)}
        total = 6*(len(shell_ids)+len(beam_ids))
        model = FEModel("experimental-multi-Q4-B2-point")
        for node_id in shell_ids:
            model.add_node(node_id, *positions[node_id])
        rows, columns, values = [], [], []
        mass_rows, mass_columns, mass_values = [], [], []
        complete_mass = all(shell.density_kg_m3 is not None for shell in shells)
        complete_mass = complete_mass and all(member.definition.mass is not None
                                             for member in compiled)
        shell_lookup = {}
        for index, shell in enumerate(shells, 1):
            if (len(shell.node_ids) != 4 or len(set(shell.node_ids)) != 4 or
                    any(node_id not in shell_index for node_id in shell.node_ids)):
                raise ValueError("four declared Q4 nodes required")
            vertices = np.array([positions[node_id] for node_id in shell.node_ids])
            _flat_vertices(vertices)
            material_id = f"panel-material-{index}"
            model.add_material(material_id, shell.E, shell.nu)
            element = QualifiedE4PLShellElement(
                index, shell.node_ids, material_id,
                thickness=shell.thickness_m,
                reference_normal=np.asarray(shell.reference_normal, dtype=float))
            model.add_element(index, element)
            local = element.compute_stiffness_matrix(
                model.mesh, model.get_material(material_id))
            if local.shape != (24, 24) or not np.isfinite(local).all():
                raise ExperimentalB2Q4PanelError("finite Q4 stiffness required")
            slots = np.array([6*shell_index[node_id]+component
                              for node_id in shell.node_ids
                              for component in range(6)])
            _scatter(rows, columns, values, slots, local)
            if shell.density_kg_m3 is not None:
                local_mass = physical_mass(
                    vertices, density_kg_m3=shell.density_kg_m3,
                    thickness_m=shell.thickness_m,
                    reference_normal=shell.reference_normal)
                if complete_mass:
                    _scatter(mass_rows, mass_columns, mass_values, slots, local_mass)
            shell_lookup[shell.shell_id] = (vertices, slots)
        member_lookup = {}
        for member in compiled:
            frame = member.local_dof_map()
            local = frame.T @ member.operator.evaluate(np.zeros(12)).tangent @ frame
            if local.shape != (12, 12) or not np.isfinite(local).all():
                raise ExperimentalB2Q4PanelError("finite physical B2 stiffness required")
            slots = np.array([6*beam_index[node_id]+component
                              for node_id in member.definition.node_ids
                              for component in range(6)])
            _scatter(rows, columns, values, slots, local)
            if complete_mass:
                local_mass = frame.T@member.local_candidate_mass_matrix()@frame
                if not np.isfinite(local_mass).all():
                    raise ValueError("physical B2 mass assembly is not representable")
                _scatter(mass_rows, mass_columns, mass_values, slots, local_mass)
            member_lookup[member.definition.member_id] = (member, slots)
        K = sparse.coo_matrix((values, (rows, columns)),
                              shape=(total, total)).tocsr()
        constraint_rows, constraint_cols, constraint_values = [], [], []
        for point_index, point in enumerate(points):
            if (point.shell_id not in shell_lookup or
                    point.member_id not in member_lookup):
                raise ValueError("point host IDs must identify declared elements")
            vertices, shell_slots = shell_lookup[point.shell_id]
            member, beam_slots = member_lookup[point.member_id]
            law = compile_reference_point(
                member.definition, vertices, station=point.station,
                offset_local_m=point.offset_local_m)
            slots = np.r_[shell_slots, beam_slots]
            for local_row in range(6):
                for local_col, slot in enumerate(slots):
                    constraint_rows.append(6*point_index+local_row)
                    constraint_cols.append(int(slot))
                    constraint_values.append(law.constraint[local_row, local_col])
        C = sparse.coo_matrix(
            (constraint_values, (constraint_rows, constraint_cols)),
            shape=(6*len(points), total)).tocsr()
        try:
            T = transformation.tocsr(copy=True)
            u0 = np.array(prescribed_offset, dtype=float, copy=True)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("finite sparse panel affine plan required") from exc
        if (T.shape[0] != total or T.shape[1] <= 6*len(points) or
                u0.shape != (total,) or not np.isfinite(T.data).all() or
                not np.isfinite(u0).all()):
            raise ValueError("finite sparse panel affine plan required")
        reduced_c = (C @ T).tocsc()
        _require_independent_supported_point_rows(reduced_c)
        reduced_k = (T.T @ K @ T).tocsc()
        # Congruence scaling changes factorization coordinates only. The
        # physical displacement and multiplier are both restored after solve.
        # Without this, a valid slender B2 section can leave point gaps above
        # the physical acceptance tolerance despite a sound local operator.
        scaled_kkt, factor_scale = _scaled_point_kkt(reduced_k, reduced_c)
        handle = factorize_cached(
            scaled_kkt, MatrixClass.SYMMETRIC_INDEFINITE)
        if handle.status != "ok":
            raise ExperimentalB2Q4PanelError(
                "panel factorization failed: " + str(handle.failure_reason))
        self.shell_node_ids = shell_ids
        self.beam_node_ids = beam_ids
        self.point_ids = tuple(point.point_id for point in points)
        self._members = tuple(member_lookup.items())
        self._K = K
        self._M = (sparse.coo_matrix((mass_values, (mass_rows, mass_columns)),
                                    shape=(total, total)).tocsr()
                   if complete_mass else None)
        if self._M is not None and not np.isfinite(self._M.data).all():
            raise ValueError("physical panel mass assembly is not representable")
        self._C = C
        self._T = T
        self._Tt = T.T.tocsr()
        self._projection_multi = np.flatnonzero(
            np.diff(self._Tt.indptr) > 1)
        self._projection_single = np.flatnonzero(
            np.diff(self._Tt.indptr) == 1)
        # Reuse the immutable CSR patterns; only the absolute values need
        # separate storage for repeated RHS validation.
        self._abs_K = sparse.csr_matrix(
            (np.abs(K.data), K.indices, K.indptr), shape=K.shape, copy=False)
        self._abs_C = sparse.csr_matrix(
            (np.abs(C.data), C.indices, C.indptr), shape=C.shape, copy=False)
        self._abs_Ct = abs(C.T.tocsr())
        self._abs_Tt = abs(T.T.tocsr())
        self._u0 = u0
        self._ku0 = np.asarray(K @ u0).reshape(-1)
        self._cu0 = np.asarray(C @ u0).reshape(-1)
        self._factor_scale = factor_scale
        self._handle = handle
        self._closed = False

    def _project(self, values: np.ndarray) -> np.ndarray:
        """Affine-transpose work with exact stored-input dots on cancellation.

        Ordinary selection columns retain the sparse fast path. Only rows
        whose rounded dot cannot meet the panel's 1e-9 work resolution use
        exact products of the stored binary64 operands.
        """
        rows = self._Tt
        if not np.isfinite(values).all():
            raise _NumericalFailure("finite panel affine projection required")
        result = np.asarray(rows @ values).reshape(-1)
        eps = np.finfo(float).eps
        for row in self._projection_multi:
            start, stop = rows.indptr[row:row+2]
            terms = [(float(a), float(values[j])) for a, j in zip(
                rows.data[start:stop], rows.indices[start:stop])]
            magnitude = sum(abs(a*v) for a, v in terms)
            uncertainty = (2*len(terms)+2)*eps*magnitude
            if (not isfinite(float(result[row])) or
                    not isfinite(magnitude) or
                    (result[row] == 0. and
                     any(a != 0. and v != 0. for a, v in terms)) or
                    uncertainty > 1e-9*abs(float(result[row]))):
                exact = sum((Fraction(a)*Fraction(v) for a, v in terms),
                            Fraction(0))
                try:
                    result[row] = float(exact)
                except OverflowError as exc:
                    raise _NumericalFailure(
                        "panel affine projection is not representable") from exc
                if exact != 0 and result[row] == 0.:
                    raise _NumericalFailure(
                        "panel affine projection is not representable")
        # Single-product underflow must not erase a nonzero applied work row.
        singles = self._projection_single
        for row in singles[result[singles] == 0.]:
            slot = rows.indptr[row]
            a = float(rows.data[slot])
            v = float(values[rows.indices[slot]])
            if a != 0. and v != 0.:
                raise _NumericalFailure(
                    "panel affine projection is not representable")
        # Subnormal output cannot meet a 1e-9 relative work resolution.
        if np.any((result != 0.) &
                  (np.abs(result) < np.finfo(float).tiny)):
            raise _NumericalFailure(
                "panel affine projection is not representable")
        if not np.isfinite(result).all():
            raise _NumericalFailure("finite panel affine projection required")
        return result

    @property
    def capabilities(self) -> ExperimentalB2Q4PanelCapabilities:
        if self._M is None:
            return ExperimentalB2Q4PanelCapabilities()
        return ExperimentalB2Q4PanelCapabilities(
            operations=("solve_linear", "solve_linear_many", "modes", "close"),
            spectral_domain="experimental reference B2/Q4 finite pairs with coordinate supports; completeness unqualified")

    def modes(self, request: B2ReferenceModesRequest, *,
              cancellation: CancellationToken | None = None) -> B2ReferenceModesResult:
        """Sparse descriptor modes with physical inertia and massless multipliers.

        Reuse compiled K/C/T and mass, never a global nullspace or dense inverse.
        A shifted general inverse-product is not Euclidean symmetric, so use
        eigs rather than eigsh. The static route still requires supported KKT;
        free-free and loaded/prestressed modes are outside this initial route.
        """
        if self._closed:
            raise ExperimentalB2Q4PanelError("experimental panel is closed")
        if type(request) is not B2ReferenceModesRequest:
            raise ValueError("typed reference-mode request required")
        if self._M is None:
            raise ValueError("explicit shell density and beam physical mass required")
        selector = self._T.copy()
        selector.eliminate_zeros()
        if (np.any(np.diff(selector.tocsc().indptr) != 1) or
                np.any(np.diff(selector.indptr) > 1)):
            raise ValueError("reference modes currently require coordinate supports without MPCs")
        if cancellation is not None and not isinstance(cancellation, CancellationToken):
            raise ValueError("CancellationToken required")
        n = self._T.shape[1]
        rows = self._C.shape[0]
        if request.count >= min(n-rows, n+rows-1):
            raise ValueError("reference mode count exceeds supported sparse spectrum")
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            sigma = -float(np.square(2.*np.pi*np.float64(request.shift_hz)))
        if not np.isfinite(sigma) or sigma == 0.:
            raise ValueError("reference mode shift is not representable")

        def safe_point(stage):
            if cancellation is not None:
                cancellation.checkpoint(stage)

        handle = None
        try:
            safe_point("reference modes before factorization")
            k = (self._T.T@self._K@self._T).tocsc()
            m = (self._T.T@self._M@self._T).tocsc()
            c = (self._C@self._T).tocsc()
            a = sparse.bmat(((k, c.T), (c, None)), format="csc")
            b = sparse.block_diag((m, sparse.csc_matrix((rows, rows))), format="csc")
            try:
                shifted, scale = _scaled_point_kkt(k-sigma*m, c)
            except ExperimentalB2Q4PanelError as exc:
                raise _NumericalFailure("reference modal scaling failed: "+str(exc)) from exc
            scaling = sparse.diags(scale, format="csc")
            bs = (scaling@b@scaling).tocsc()
            b.eliminate_zeros(); b.sort_indices()
            bs.eliminate_zeros(); bs.sort_indices()
            if (not np.isfinite(bs.data).all() or b.nnz != bs.nnz or
                    not np.array_equal(b.indptr, bs.indptr) or
                    not np.array_equal(b.indices, bs.indices) or
                    np.any((b.data != 0.) & (bs.data == 0.))):
                raise _NumericalFailure("reference modal mass scaling is not representable")
            handle = factorize_cached(shifted, MatrixClass.GENERAL)
            safe_point("reference modes after factorization")
            if handle.status != "ok":
                raise _NumericalFailure("reference modal factorization failed: "+str(handle.failure_reason))

            def action(vector):
                safe_point("reference modal iteration")
                try:
                    answer = handle.solve(bs@vector)
                except RuntimeError as exc:
                    # These are explicit numerical failures of the shared
                    # backend. Unclassified/programming errors still propagate.
                    if (str(exc) == "Sparse solve produced NaN/Inf values" or
                            str(exc).startswith("Cannot solve with failed factorization:")):
                        raise _NumericalFailure("reference modal sparse solve failed: "+str(exc)) from exc
                    raise
                safe_point("reference modal iteration completed")
                return answer

            operator = LinearOperator(a.shape, matvec=action, dtype=float)
            values, vectors = eigs(operator, k=request.count, which="LM",
                                  v0=np.sin(np.arange(a.shape[0])+.23),
                                  tol=1e-11, maxiter=request.max_iterations)
            safe_point("reference modes after eigensolve")
            abs_a, abs_b, abs_c = abs(a), abs(b), abs(c)
            recovered = []
            for mu, y in zip(values, vectors.T):
                if (not np.isfinite(mu) or abs(mu.imag) > 1e-9*abs(mu.real) or
                        mu.real <= 0. or not np.isfinite(y).all() or
                        np.linalg.norm(y.imag) > 1e-9*np.linalg.norm(y.real)):
                    raise _NumericalFailure("nonphysical or unresolved finite modal pair")
                lam = sigma+1./mu.real
                x = scale*y.real
                mass_norm = float(x@b@x)
                if not np.isfinite(lam) or lam <= 0. or not np.isfinite(mass_norm) or mass_norm <= 0.:
                    raise _NumericalFailure("positive finite supported mode and physical inertia required")
                x /= np.sqrt(mass_norm)
                physical = np.asarray(self._T@x[:n])
                if not np.isfinite(x).all() or not np.isfinite(physical).all():
                    raise _NumericalFailure("physical mode normalization is not representable")
                residual = a@x-lam*(b@x)
                bound = abs_a@abs(x)+abs(lam)*(abs_b@abs(x))
                equation = _modal_scaled_residual(residual, bound, scale)
                constraint = _modal_scaled_residual(c@x[:n], abs_c@abs(x[:n]), scale[n:])
                physical_gap = _modal_scaled_residual(
                    self._C@physical, abs(self._C)@abs(physical), scale[n:])
                physical_balance = self._K@physical+self._C.T@x[n:]-lam*(self._M@physical)
                physical_bound = (abs(self._K)@abs(physical)+abs(self._C.T)@abs(x[n:])+
                                  abs(lam)*(abs(self._M)@abs(physical)))
                physical_equation = _modal_scaled_residual(
                    self._project(physical_balance), abs(self._T.T)@physical_bound, scale[:n])
                equation = max(equation, physical_equation)
                constraint = max(constraint, physical_gap)
                if equation > 1e-8 or constraint > 1e-9:
                    raise _NumericalFailure("reference modal equation or constraint residual failed")
                recovered.append((float(np.sqrt(lam)/(2.*np.pi)),
                                  tuple(physical), tuple(x[n:]),
                                  equation, constraint))
            recovered.sort(key=lambda mode: mode[0])
            primal = np.array([mode[1] for mode in recovered]).T
            modal_gram = primal.T@self._M@primal
            if (not np.isfinite(modal_gram).all() or
                    np.max(abs(modal_gram-np.eye(request.count))) > 1e-7):
                raise _NumericalFailure("modal physical-mass orthogonality failed")
            safe_point("reference modes before publication")
            return B2ReferenceModesResult(
                "ok", tuple(mode[0] for mode in recovered),
                tuple(mode[1] for mode in recovered), tuple(mode[2] for mode in recovered),
                tuple(mode[3] for mode in recovered), tuple(mode[4] for mode in recovered),
                handle.factorization_count, handle.solve_count)
        except SolveCancelled as exc:
            return B2ReferenceModesResult(
                "cancelled", factorization_count=handle.factorization_count if handle else 0,
                solve_count=handle.solve_count if handle else 0, failure_reason=str(exc))
        except (ArpackError, _NumericalFailure) as exc:
            return B2ReferenceModesResult(
                "failed", factorization_count=handle.factorization_count if handle else 0,
                solve_count=handle.solve_count if handle else 0, failure_reason=str(exc))

    def solve_linear(self, load, *, recover_members=None
                     ) -> ExperimentalB2Q4PanelResult:
        if self._closed:
            raise ExperimentalB2Q4PanelError("experimental panel is closed")
        recovery = _checked_recovery(
            recover_members, {member_id for member_id, _ in self._members})
        try:
            applied = np.array(load, dtype=float, copy=True)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("finite panel load vector required") from exc
        if applied.shape != self._u0.shape or not np.isfinite(applied).all():
            raise ValueError("finite panel load vector required")
        try:
            rhs = np.r_[self._project(applied-self._ku0), -self._cu0]
        except _NumericalFailure as exc:
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            scaled_rhs = self._factor_scale*rhs
        if (not np.isfinite(scaled_rhs).all() or
                np.any((rhs != 0.) & (scaled_rhs == 0.))):
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count,
                failure_reason="panel right-hand side scaling is not representable")
        try:
            answer = self._factor_scale*np.asarray(
                self._handle.solve(scaled_rhs), dtype=float)
        except RuntimeError as exc:
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        try:
            if answer.shape != rhs.shape or not np.isfinite(answer).all():
                raise _NumericalFailure("finite panel solution required")
            q, lam = answer[:-len(self._cu0)], answer[-len(self._cu0):]
            u = np.asarray(self._T @ q).reshape(-1)+self._u0
            if not np.isfinite(u).all():
                raise _NumericalFailure("finite panel solution required")
            gap = np.asarray(self._C @ u).reshape(-1)
            force = np.asarray(self._K @ u).reshape(-1)
            constraint_force = np.asarray(self._C.T @ lam).reshape(-1)
            reaction = force+constraint_force-applied
            projected = self._project(reaction)
            # Each row uses the absolute contribution sum in its own physical
            # work unit. A 1 N floor would mask a failed micro-/nano-load;
            # a single mixed force/moment norm would depend on chosen units.
            gap_scale = np.asarray(self._abs_C @ np.abs(u)).reshape(-1)
            physical_force_scale = np.asarray(
                self._abs_K @ np.abs(u)+self._abs_Ct @ np.abs(lam)+
                np.abs(applied)).reshape(-1)
            equilibrium_scale = np.asarray(
                self._abs_Tt @ physical_force_scale).reshape(-1)
            # Sparse factorization can leave roundoff in a locally quiet DOF.
            # Its allowance follows the current force and moment magnitudes,
            # separately, then maps through the affine transpose; it has no
            # fixed N, Nm, m or rad floor.
            by_node = physical_force_scale.reshape(-1, 6)
            force_roundoff = float(np.max(by_node[:, :3]))
            moment_roundoff = float(np.max(by_node[:, 3:]))
            physical_roundoff = np.tile(
                (force_roundoff,)*3+(moment_roundoff,)*3,
                len(by_node))
            projected_roundoff = np.asarray(
                self._abs_Tt @ physical_roundoff).reshape(-1)
            roundoff_fraction = len(rhs)*np.finfo(float).eps
            if roundoff_fraction >= 1e-9:
                raise _NumericalFailure("panel equilibrium resolution insufficient")
            explicit_rhs = np.abs(self._project(applied))
            resolution_floor = roundoff_fraction*projected_roundoff
            # Prescribed offsets can induce reduced loads much smaller than
            # the model-wide reaction scale. Their physical effect is checked
            # by the full equilibrium/compatibility test below. This extra
            # small-load resolution guard applies to explicit applied work,
            # so a superposed tiny external load cannot disappear silently.
            active = explicit_rhs > 0.
            if np.any(resolution_floor[active] >
                      1e-9*explicit_rhs[active]):
                raise _NumericalFailure("panel mixed-load resolution insufficient")
            equilibrium_tolerance = (1e-9*equilibrium_scale+
                                     roundoff_fraction*projected_roundoff)
            if (not np.isfinite(reaction).all() or
                    not np.isfinite(gap).all() or not np.isfinite(projected).all() or
                    not np.isfinite(gap_scale).all() or
                    not np.isfinite(equilibrium_tolerance).all() or
                    np.any(np.abs(gap) > 1e-9*gap_scale) or
                    np.any(np.abs(projected) > equilibrium_tolerance)):
                raise _NumericalFailure("panel point gap or equilibrium failed")
        except _NumericalFailure as exc:
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        recovered = []
        for member_id, (member, slots) in self._members:
            if recovery is not None and member_id not in recovery:
                continue
            local = member.local_dof_map() @ u[slots]
            if not np.isfinite(local).all():
                return ExperimentalB2Q4PanelResult(
                    "failed", factorization_count=self._handle.factorization_count,
                    solve_count=self._handle.solve_count,
                    failure_reason="finite physical B2 recovery coordinates required")
            result = member.operator.recover_sections(
                local, stations=(0., .5, 1.) if recovery is None
                else recovery[member_id])
            if (not np.isfinite(result.resultants).all() or
                    not np.isfinite(result.strains).all()):
                return ExperimentalB2Q4PanelResult(
                    "failed", factorization_count=self._handle.factorization_count,
                    solve_count=self._handle.solve_count,
                    failure_reason="finite physical B2 recovery required")
            recovered.append((member_id, tuple(
                tuple(map(float, row)) for row in result.resultants)))
        energy = .5*float(u @ force)
        if not isfinite(energy):
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count,
                failure_reason="finite panel strain energy required")
        return ExperimentalB2Q4PanelResult(
            "completed", tuple(map(float, u)),
            tuple((point_id, tuple(map(float, lam[6*i:6*i+6])))
                  for i, point_id in enumerate(self.point_ids)),
            tuple(map(float, reaction)),
            tuple((point_id, tuple(map(float, gap[6*i:6*i+6])))
                  for i, point_id in enumerate(self.point_ids)),
            tuple(recovered), energy, self._handle.factorization_count,
            self._handle.solve_count)

    def solve_linear_many(
            self, cases: Sequence[tuple[str, object]], *,
            selected_dofs: Sequence[int],
            selected_points: Sequence[str] = (),
            recover_members: Mapping[str, Sequence[float]] | None = None,
            cancellation_token: CancellationToken | None = None,
            on_case: Callable[[str], None] | None = None,
            ) -> ExperimentalB2Q4PanelBatchResult:
        """Solve ordered cases with one factorization and bounded case storage.

        Each result is complete before it joins the returned prefix. Numerical
        failure or cooperative cancellation stops further cases; callbacks and
        programming errors propagate. This development route uses one RHS at a
        time, avoiding full displacement/reaction batches for large panels.
        """
        if self._closed:
            raise ExperimentalB2Q4PanelError("experimental panel is closed")
        try:
            chosen = tuple(selected_dofs)
            chosen_points = tuple(selected_points)
            submitted = tuple(cases)
        except TypeError as exc:
            raise ValueError("ordered B2 panel cases and selection required") from exc
        if (not chosen or any(type(value) is not int or
                              not 0 <= value < len(self._u0)
                              for value in chosen) or
                len(set(chosen)) != len(chosen)):
            raise ValueError("unique selected panel coordinate indices required")
        if (any(type(point_id) is not str or
                point_id not in self.point_ids for point_id in chosen_points) or
                len(set(chosen_points)) != len(chosen_points)):
            raise ValueError("unique selected panel point IDs required")
        if (not submitted or
                any(type(item) not in (tuple, list) or len(item) != 2 or
                    type(item[0]) is not str or not item[0].strip()
                    for item in submitted) or
                len({item[0] for item in submitted}) != len(submitted)):
            raise ValueError("unique nonempty ordered B2 panel case IDs required")
        if cancellation_token is not None and not isinstance(
                cancellation_token, CancellationToken):
            raise TypeError("B2 panel cancellation token required")
        if on_case is not None and not callable(on_case):
            raise TypeError("B2 panel case callback required")
        recovery = _checked_recovery(
            {} if recover_members is None else recover_members,
            {member_id for member_id, _ in self._members})
        fingerprints = []
        for _case_id, load in submitted:
            if cancellation_token is not None and cancellation_token.is_cancelled:
                break
            snapshot, fingerprint = _load_value_snapshot(load, self._u0.shape)
            fingerprints.append(fingerprint)
            del snapshot
        completed = []
        for index, (case_id, load) in enumerate(submitted):
            if cancellation_token is not None and cancellation_token.is_cancelled:
                break
            snapshot, fingerprint = _load_value_snapshot(load, self._u0.shape)
            if fingerprint != fingerprints[index]:
                raise ValueError("B2 panel load case changed after submission")
            result = self.solve_linear(snapshot, recover_members=recovery)
            if result.status != "completed":
                return ExperimentalB2Q4PanelBatchResult(
                    "failed", chosen, chosen_points, tuple(completed),
                    self._handle.factorization_count, self._handle.solve_count,
                    failure_reason=f"{case_id}: {result.failure_reason}")
            point_multipliers = dict(result.point_multipliers)
            point_gaps = dict(result.point_gaps)
            completed.append(ExperimentalB2Q4PanelSelectedCase(
                case_id,
                tuple(result.displacements[index] for index in chosen),
                tuple(result.affine_reactions[index] for index in chosen),
                tuple((point_id, point_multipliers[point_id])
                      for point_id in chosen_points),
                tuple((point_id, point_gaps[point_id])
                      for point_id in chosen_points),
                result.beam_resultants_local,
                result.internal_strain_energy))
            if on_case is not None:
                on_case(case_id)
        return ExperimentalB2Q4PanelBatchResult(
            "cancelled" if len(completed) != len(submitted) else "completed",
            chosen, chosen_points, tuple(completed),
            self._handle.factorization_count,
            self._handle.solve_count)

    def close(self) -> None:
        self._closed = True
        self._handle = None


def _scatter(rows, columns, values, slots, local):
    width = len(slots)
    rows.extend(np.repeat(slots, width))
    columns.extend(np.tile(slots, width))
    values.extend(np.asarray(local).ravel())


def _modal_scaled_residual(residual, bound, row_scale):
    """Infinity backward error in the fixed congruence row representation.

    Near-zero components of an uncoupled mode are not separate relative-error
    denominators. Scaling the rows before the norm keeps their units consistent
    with the factorization coordinates without an arbitrary physical floor.
    """
    residual, bound = np.asarray(residual), np.asarray(bound)
    if not np.isfinite(residual).all() or not np.isfinite(bound).all():
        return float("inf")
    numerator = np.max(abs(residual)*row_scale, initial=0.)
    denominator = np.max(bound*row_scale, initial=0.)
    if not np.isfinite(numerator) or not np.isfinite(denominator):
        return float("inf")
    if denominator == 0.:
        return 0. if numerator == 0. else float("inf")
    return float(numerator/denominator)


def create_experimental_b2_q4_panel_analysis(*args, **kwargs):
    return ExperimentalB2Q4PanelAnalysis(*args, **kwargs)
