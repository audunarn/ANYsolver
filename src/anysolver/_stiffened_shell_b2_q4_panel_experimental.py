"""Small elastic multi-Q4/multi-B2 panel with existing F10 point joints.

This is an experimental reference-linear owner. Shell and beam node identities
are explicit and separate. No line, footprint, inertia, geometric stiffness,
nonlinear state or qualification is inferred from the point-joint assembly.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Mapping, Sequence

import numpy as np
from scipy import sparse

from ._b2_f10_f11_point_attachment import LAW_ID, compile_reference_point
from ._b2_physical_linear_definition import (
    PROFILE_ID, CompiledPhysicalB2Member, PhysicalB2Member,
    PhysicalB2OperatorCache,
)
from .e4_pl_element import QualifiedE4PLShellElement
from .fe_core import FEModel
from .linalg import MatrixClass, factorize_cached


class ExperimentalB2Q4PanelError(RuntimeError):
    """The experimental panel cannot be prepared or used."""


class _NumericalFailure(RuntimeError):
    """A checked sparse panel solution failed numerically."""


@dataclass(frozen=True)
class Q4PanelShell:
    shell_id: str
    node_ids: tuple[int, int, int, int]
    E: float
    nu: float
    thickness_m: float
    reference_normal: tuple[float, float, float] = (0., 0., 1.)


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
    operations: tuple[str, ...] = ("solve_linear", "close")


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


def _unique_ids(items, name):
    ids = [getattr(item, name) for item in items]
    if any(not isinstance(value, str) or not value.strip() for value in ids):
        raise ValueError(f"nonempty {name} required")
    if len(set(ids)) != len(ids):
        raise ValueError(f"unique {name} required")


def _flat_vertices(vertices):
    base = vertices[0]
    normal = np.cross(vertices[1]-base, vertices[3]-base)
    diameter = max(np.linalg.norm(a-b) for a in vertices for b in vertices)
    magnitude = np.linalg.norm(normal)
    if (not isfinite(diameter) or diameter <= 0. or
            magnitude <= 1e-12*diameter**2 or
            abs((vertices[2]-base) @ normal) > 1e-10*diameter*magnitude):
        raise ValueError("nondegenerate flat Q4 shell required")


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
        if np.linalg.matrix_rank(reduced_c.toarray()) != 6*len(points):
            raise ValueError("independent supported point rows required")
        reduced_k = (T.T @ K @ T).tocsc()
        kkt = sparse.bmat(
            ((reduced_k, reduced_c.T), (reduced_c, None)), format="csc")
        handle = factorize_cached(kkt, MatrixClass.SYMMETRIC_INDEFINITE)
        if handle.status != "ok":
            raise ExperimentalB2Q4PanelError(
                "panel factorization failed: " + str(handle.failure_reason))
        self.shell_node_ids = shell_ids
        self.beam_node_ids = beam_ids
        self.point_ids = tuple(point.point_id for point in points)
        self._members = tuple(member_lookup.items())
        self._K = K
        self._C = C
        self._T = T
        self._u0 = u0
        self._ku0 = np.asarray(K @ u0).reshape(-1)
        self._cu0 = np.asarray(C @ u0).reshape(-1)
        self._handle = handle
        self._closed = False

    @property
    def capabilities(self) -> ExperimentalB2Q4PanelCapabilities:
        return ExperimentalB2Q4PanelCapabilities()

    def solve_linear(self, load) -> ExperimentalB2Q4PanelResult:
        if self._closed:
            raise ExperimentalB2Q4PanelError("experimental panel is closed")
        try:
            applied = np.array(load, dtype=float, copy=True)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("finite panel load vector required") from exc
        if applied.shape != self._u0.shape or not np.isfinite(applied).all():
            raise ValueError("finite panel load vector required")
        rhs = np.r_[np.asarray(self._T.T @ (applied-self._ku0)).reshape(-1),
                    -self._cu0]
        try:
            answer = np.asarray(self._handle.solve(rhs), dtype=float)
        except RuntimeError as exc:
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        try:
            if answer.shape != rhs.shape or not np.isfinite(answer).all():
                raise _NumericalFailure("finite panel solution required")
            q, lam = answer[:-len(self._cu0)], answer[-len(self._cu0):]
            u = np.asarray(self._T @ q).reshape(-1)+self._u0
            gap = np.asarray(self._C @ u).reshape(-1)
            reaction = np.asarray(self._K @ u+self._C.T @ lam-applied).reshape(-1)
            force = np.asarray(self._K @ u).reshape(-1)
            projected = np.asarray(self._T.T @ reaction).reshape(-1)
            force_scale = max(1., hypot(*applied), hypot(*force))
            motion_scale = max(1., hypot(*u))
            if (not np.isfinite(u).all() or not np.isfinite(reaction).all() or
                    not np.isfinite(gap).all() or not np.isfinite(projected).all() or
                    not isfinite(force_scale) or not isfinite(motion_scale) or
                    hypot(*gap) > 1e-9*motion_scale or
                    hypot(*projected) > 1e-9*force_scale):
                raise _NumericalFailure("panel point gap or equilibrium failed")
        except _NumericalFailure as exc:
            return ExperimentalB2Q4PanelResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        recovered = []
        for member_id, (member, slots) in self._members:
            local = member.local_dof_map() @ u[slots]
            if not np.isfinite(local).all():
                return ExperimentalB2Q4PanelResult(
                    "failed", factorization_count=self._handle.factorization_count,
                    solve_count=self._handle.solve_count,
                    failure_reason="finite physical B2 recovery coordinates required")
            result = member.operator.recover_sections(
                local, stations=(0., .5, 1.))
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

    def close(self) -> None:
        self._closed = True
        self._handle = None


def _scatter(rows, columns, values, slots, local):
    width = len(slots)
    rows.extend(np.repeat(slots, width))
    columns.extend(np.tile(slots, width))
    values.extend(np.asarray(local).ravel())


def create_experimental_b2_q4_panel_analysis(*args, **kwargs):
    return ExperimentalB2Q4PanelAnalysis(*args, **kwargs)
