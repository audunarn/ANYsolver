"""Experimental sparse reference-linear GE/Q4 point-connected panel.

This is an integration slice, not an accepted G0/G1 formulation.  It retains
all native B3 cell variables and uses the existing objective point operator.
Qualified line coupling and material updates are separate work. The optional
L1 weak-line route is reference-linear and explicitly unqualified.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import warnings

from anymaterial import DNVC208MaterialCurve
import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as spla
from scipy.sparse.csgraph import maximum_bipartite_matching

from ._ge_beam3_native_definition import NativeBeamDefinition
from ._ge_beam3_pose_joint import RigidPoseJoint
from ._ge_beam3_generalized_static_boundary import spatial_jacobian
from .corotational import corotational_element_response
from .elements import create_shell_element
from .fe_core import FEModel
from .control import cancellation_safe_point
from ._stiffened_shell_ge_checkpoint_binary import (
    MAGIC as BINARY_CHECKPOINT_MAGIC, decode as _decode_binary_checkpoint,
    encode as _encode_binary_checkpoint, S3_MAGIC as S3_BINARY_CHECKPOINT_MAGIC,
    S3_SCHEMA as FINITE_S3_MATERIAL_CHECKPOINT,
    decode_s3 as _decode_s3_binary_checkpoint,
)
from ._stiffened_shell_l1_assembly_experimental import (
    ExperimentalL1Line, ExperimentalBL5Line,
    compile_lines as _compile_weak_lines,
    _row_count as _weak_line_row_count,
)


PROFILE = "B3_GE_E4_PL_STIFFENED_SHELL_V1"
CHECKPOINT = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_LINEAR_V1"
FINITE_CHECKPOINT = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_V1"
FINITE_MATERIAL_CHECKPOINT = (
    "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_MATERIAL_V3")
FINITE_SHELL_MATERIAL_CHECKPOINT = (
    "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_SHELL_J2_V4")
MAX_JSON_CHECKPOINT_BYTES = 2_000_000
MAX_JSON_CHECKPOINT_VALUES = 50_000
_MAX_DENSE_CONSTRAINT_ROWS = 48
_MAX_DENSE_CONSTRAINT_VALUES = 16_384


def _require_independent_supported_rows(constraints, free, coordinate_scale,
                                        row_scale, sources=()):
    """Check small numerical ranks; keep large structural checks sparse.

    Structural rank cannot certify numerical independence. The subsequent
    sparse mixed factorization remains the numerical check for large models.
    """
    reduced = constraints[:, free].tocsr()
    rows, columns = reduced.shape
    if sources and len(sources) != rows:
        raise ValueError("complete attachment row provenance required")

    def failure(message, row):
        suffix = f": {sources[row]}" if sources else ""
        raise ValueError(message+suffix)

    if rows > columns:
        failure("independent supported attachment rows required", columns)
    if rows <= _MAX_DENSE_CONSTRAINT_ROWS and rows*columns <= _MAX_DENSE_CONSTRAINT_VALUES:
        scaled = (sparse.diags(1./row_scale) @ reduced @
                  sparse.diags(coordinate_scale[free])).toarray()
        rank = np.linalg.matrix_rank(scaled)
        if rank != rows:
            _, _, pivot = linalg.qr(scaled.T, pivoting=True, mode="economic")
            failure("independent supported attachment rows required",
                    int(pivot[rank]))
        return
    pattern = reduced.copy()
    pattern.eliminate_zeros()
    matching = maximum_bipartite_matching(pattern, perm_type="column")
    if np.any(matching < 0):
        failure("structurally independent supported attachment rows required",
                int(np.flatnonzero(matching < 0)[0]))


@dataclass(frozen=True)
class ShellPanel:
    node_ids: tuple[int, ...]
    coordinates_m: tuple[tuple[float, float, float], ...]
    q4_elements: tuple[tuple[int, int, int, int], ...]
    thickness_m: float
    young_pa: float
    poisson: float
    density_kg_m3: float
    s3_elements: tuple[tuple[int, int, int], ...] = ()
    j2_curve: DNVC208MaterialCurve | None = None


@dataclass(frozen=True)
class PointConnection:
    shell_node: int
    beam_node: int


@dataclass(frozen=True)
class FixedCoordinate:
    domain: str
    node: int
    component: int


@dataclass(frozen=True)
class NodalAction:
    domain: str
    node: int
    wrench: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class LinearDefinition:
    profile: str
    shell: ShellPanel
    beams: tuple[NativeBeamDefinition, ...]
    points: tuple[PointConnection, ...]
    fixed: tuple[FixedCoordinate, ...]
    lines: tuple[ExperimentalL1Line | ExperimentalBL5Line, ...] = ()


@dataclass(frozen=True)
class LinearResult:
    """Experimental linear result with dimensionless work/row-scaled errors."""
    status: str
    shell_displacement: np.ndarray
    beam_coordinates: np.ndarray
    multipliers: np.ndarray
    reactions: np.ndarray
    free_equilibrium_ratio: float
    constraint_max: float
    generation: int
    production_qualified: bool = False


def _owned(values, shape=None):
    result = np.array(values, dtype=float, copy=True)
    if (shape is not None and result.shape != shape) or not np.isfinite(result).all():
        raise ValueError("finite owned stiffened-shell values required")
    return np.frombuffer(result.tobytes(), dtype=float).reshape(result.shape)


def _shell_reference(panel: ShellPanel):
    ids = tuple(panel.node_ids)
    xyz = _owned(panel.coordinates_m, (len(ids), 3))
    if (len(ids) < 6 or len(ids) != len(set(ids)) or
            len(panel.q4_elements)+len(panel.s3_elements) < 2 or
            any(type(v) is not int or v <= 0 for v in ids) or
            not np.allclose(xyz[:, 2], xyz[0, 2], rtol=0., atol=1e-12) or
            not (np.isfinite(panel.thickness_m) and panel.thickness_m > 0. and
                 np.isfinite(panel.young_pa) and panel.young_pa > 0. and
                 np.isfinite(panel.poisson) and -1. < panel.poisson < .5 and
                 np.isfinite(panel.density_kg_m3) and panel.density_kg_m3 > 0.)):
        raise ValueError("experimental connected flat Q4/S3 panel required")
    if panel.j2_curve is not None:
        if (type(panel.j2_curve) is not DNVC208MaterialCurve or
                any(not np.isfinite(value)
                    for value in panel.j2_curve.as_dict().values())):
            raise ValueError("experimental shell J2 requires finite DNVC-C208 data")
    index = {node: i for i, node in enumerate(ids)}
    model = FEModel("experimental-stiffened-shell-q4")
    model.add_material("shell", panel.young_pa, panel.poisson,
                       density=panel.density_kg_m3,
                       yield_stress=(panel.j2_curve.sigma_prop
                                     if panel.j2_curve is not None else 0.),
                       hardening_curve=panel.j2_curve)
    for node, point in zip(ids, xyz):
        model.add_node(node, *map(float, point))
    pieces = []
    cells = (tuple((nodes, "e4-pl") for nodes in panel.q4_elements) +
             tuple((nodes, "e4-pl-s3-v2d") for nodes in panel.s3_elements))
    neighbours = {node: set() for node in ids}
    cell_keys = set()
    for eid, (nodes, formulation) in enumerate(cells, 1):
        if (len(nodes) != (4 if formulation == "e4-pl" else 3) or
                len(set(nodes)) != len(nodes) or
                any(node not in index for node in nodes)):
            raise ValueError("distinct known Q4/S3 nodes required")
        key = (formulation, frozenset(nodes))
        if key in cell_keys:
            raise ValueError("duplicate experimental shell element")
        cell_keys.add(key)
        for node in nodes:
            neighbours[node].update(other for other in nodes if other != node)
        element = create_shell_element(
            eid, list(nodes), "shell", formulation=formulation,
            thickness=panel.thickness_m, reference_normal=(0., 0., 1.))
        model.add_element(eid, element)
        slots = np.array([6*index[node]+axis for node in nodes for axis in range(6)])
        pieces.append((eid, element, slots, formulation))
    seen = {ids[0]}
    pending = [ids[0]]
    while pending:
        for other in neighbours[pending.pop()]-seen:
            seen.add(other)
            pending.append(other)
    if len(seen) != len(ids):
        raise ValueError("connected Q4/S3 shell cells must use every node")
    pieces = [
        (eid, element, slots,
         element.init_model_bound_nonlinear_state(
             model.mesh, model.get_material("shell"), 3)
         if formulation == "e4-pl-s3-v2d" else element.init_nonlinear_state(3))
        for eid, element, slots, formulation in pieces
    ]
    return model, ids, xyz, index, pieces


def _beam_reference(definitions: tuple[NativeBeamDefinition, ...]):
    if len(definitions) < 2 or any(type(v) is not NativeBeamDefinition
                                   for v in definitions):
        raise ValueError("multiple explicit native B3 definitions required")
    elements = []
    nodes = {}
    for definition in definitions:
        element, _inertia = definition.instantiate()
        if type(element.section).__name__ != "EllipsoidalGeneralizedSection":
            raise ValueError("experimental GE point slice admits generalized B3")
        ref = element.operator.reference
        for node, position, frame in zip(element.node_ids, ref.coordinates,
                                         ref.nodal_triads):
            value = (_owned(position, (3,)), _owned(frame, (3, 3)))
            previous = nodes.setdefault(node, value)
            if (not np.array_equal(previous[0], value[0]) or
                    not np.array_equal(previous[1], value[1])):
                raise ValueError("shared B3 node has inconsistent position or frame")
        elements.append(element)
    ids = tuple(sorted(nodes))
    index = {node: i for i, node in enumerate(ids)}
    nodal = 6*len(ids)
    pieces = []
    for i, element in enumerate(elements):
        slots = np.array([6*index[node]+axis for node in element.node_ids
                          for axis in range(6)] + list(range(nodal+24*i,
                                                             nodal+24*(i+1))))
        pieces.append((element, slots, element.operator.cell.virgin()))
    return ids, index, nodes, pieces, nodal+24*len(pieces)


def _assemble_shell(model, pieces, count, coordinate_scale):
    rows, columns, data = [], [], []
    residual = np.zeros(count)
    local_error = 0.
    for eid, element, slots, origin in pieces:
        if len(slots) == 18:
            force, tangent, candidate = element.compute_nonlinear_response(
                model.mesh, model.get_material("shell"), np.zeros(18),
                origin, 3, True)
        else:
            force, tangent, candidate = corotational_element_response(
                model, eid, element, np.zeros(24), True,
                committed_state=origin, num_layers=3,
                tangent_mode="consistent")
        if (force is None or tangent is None or candidate is None or
                not np.isfinite(force).all() or not np.isfinite(tangent).all()):
            raise RuntimeError("finite Q4 reference operator unavailable")
        local_error = max(local_error, _scaled_reference_residual(
            force, tangent, coordinate_scale[slots]))
        np.add.at(residual, slots, force)
        rows.extend(np.repeat(slots, len(slots)))
        columns.extend(np.tile(slots, len(slots)))
        data.extend(np.asarray(tangent).ravel())
    return (residual, sparse.coo_matrix((data, (rows, columns)),
                                        shape=(count, count)).tocsr(), local_error)


def _assemble_beam(pieces, nodes, index, count, coordinate_scale):
    rows, columns, data = [], [], []
    residual = np.zeros(count)
    local_error = 0.
    for element, slots, origin in pieces:
        ref = element.operator.reference
        position = np.array([nodes[node][0] for node in element.node_ids])
        frames = np.array([nodes[node][1] for node in element.node_ids])
        response = element.operator.evaluate(
            position, np.zeros((3, 3)), frames,
            np.tile(np.eye(3), (2, 1, 1)), np.zeros(18),
            origin=origin, check=element.operator.guard)
        local = spatial_jacobian(response.residual,
                                 response.hessian+response.hessian_low)
        if local.shape != (42, 42) or not np.isfinite(local).all():
            raise RuntimeError("finite native B3 reference operator unavailable")
        local_error = max(local_error, _scaled_reference_residual(
            response.residual, local, coordinate_scale[slots]))
        np.add.at(residual, slots, response.residual)
        rows.extend(np.repeat(slots, 42))
        columns.extend(np.tile(slots, 42))
        data.extend(local.ravel())
    return (residual, sparse.coo_matrix((data, (rows, columns)),
                                        shape=(count, count)).tocsr(), local_error)


def _reference_scales(shell_xyz, beam_nodes, beam_parts, shell_count,
                      beam_count):
    """Freeze coordinate scales with their physical units at compilation."""
    positions = np.vstack((shell_xyz, [value[0] for value in beam_nodes.values()]))
    centered = positions-np.mean(positions, axis=0)
    length = float(np.sqrt(np.mean(np.sum(centered*centered, axis=1))))
    if not np.isfinite(length) or length <= np.finfo(float).eps:
        raise ValueError("nondegenerate reference length required")
    pose_scale = np.array((length, length, length, 1., 1., 1.))
    shell_scale = np.tile(pose_scale, shell_count//6)
    nodal_count = beam_count-24*len(beam_parts)
    beam_scale = np.empty(beam_count)
    beam_scale[:nodal_count] = np.tile(pose_scale, nodal_count//6)
    strain_scale = np.array((1., 1., 1., 1./length, 1./length, 1./length))
    for i, (element, _slots, _origin) in enumerate(beam_parts):
        base = nodal_count+24*i
        beam_scale[base:base+6] = 1.
        resultant_scale = np.abs(element.section.elastic)@strain_scale
        beam_scale[base+6:base+24] = np.tile(resultant_scale, 3)
    if not np.isfinite(shell_scale).all() or not np.isfinite(beam_scale).all():
        raise ValueError("finite reference coordinate scales required")
    return length, shell_scale, beam_scale


def _scaled_reference_residual(residual, tangent, coordinate_scale):
    """Compare each covector row with a same-unit tangent action."""
    row_scale = np.asarray(np.abs(tangent)@coordinate_scale).reshape(-1)
    if (not np.isfinite(residual).all() or not np.isfinite(row_scale).all() or
            np.any(row_scale < 0.)):
        raise ValueError("finite stress-free reference operator required")
    error = np.zeros_like(residual)
    np.divide(np.abs(residual), row_scale, out=error, where=row_scale > 0.)
    if np.any((row_scale == 0.) & (residual != 0.)):
        return float("inf")
    return float(np.max(error))


def _relative_equilibrium(residual, applied, coordinate_scale, floor_work):
    """Work-scaled mixed equilibrium ratio with a fixed physical work floor.

    Each covector row is paired with its frozen characteristic coordinate.
    This keeps forces, moments and native retained-variable equations in
    work units and is invariant under a work-conjugate coordinate-unit change.
    ``floor_work`` is one newton times the frozen reference length in SI.
    """
    residual = np.asarray(residual, dtype=float)
    applied = np.asarray(applied, dtype=float)
    coordinate_scale = np.asarray(coordinate_scale, dtype=float)
    if (residual.shape != applied.shape or residual.shape !=
            coordinate_scale.shape or residual.ndim != 1 or
            not np.isfinite(residual).all() or
            not np.isfinite(applied).all() or
            not np.isfinite(coordinate_scale).all() or
            np.any(coordinate_scale <= 0.) or
            not np.isfinite(floor_work) or floor_work <= 0.):
        raise ValueError("finite positive mixed work scales required")
    weighted_residual = residual*coordinate_scale
    weighted_applied = applied*coordinate_scale
    if (not np.isfinite(weighted_residual).all() or
            not np.isfinite(weighted_applied).all()):
        raise ValueError("representable mixed work residual required")
    scale = max(float(floor_work),
                float(np.max(np.abs(weighted_residual), initial=0.)),
                float(np.max(np.abs(weighted_applied), initial=0.)))
    return float(np.linalg.norm(weighted_residual/scale) /
                 max(floor_work/scale,
                     float(np.linalg.norm(weighted_applied/scale))))


def _linear_equilibrium(residual, applied, coordinate_scale):
    """Scale linear equilibrium to its actual load, including quiet load rows.

    A fixed work floor can accept zero response to a small applied load. The
    active-row check also prevents a large load from hiding a missed smaller
    load in a separate physical coordinate. A numerically unresolved mixed
    load fails closed; it is not declared an equilibrium state.
    """
    residual = np.asarray(residual, dtype=float)
    applied = np.asarray(applied, dtype=float)
    coordinate_scale = np.asarray(coordinate_scale, dtype=float)
    if (residual.ndim != 1 or residual.shape != applied.shape or
            residual.shape != coordinate_scale.shape or
            not np.isfinite(residual).all() or
            not np.isfinite(applied).all() or
            not np.isfinite(coordinate_scale).all() or
            np.any(coordinate_scale <= 0.)):
        raise ValueError("finite positive mixed work scales required")
    weighted_residual = residual*coordinate_scale
    weighted_applied = applied*coordinate_scale
    if (not np.isfinite(weighted_residual).all() or
            not np.isfinite(weighted_applied).all()):
        raise ValueError("representable mixed work residual required")
    magnitude = max(float(np.max(np.abs(weighted_residual), initial=0.)),
                    float(np.max(np.abs(weighted_applied), initial=0.)))
    if magnitude == 0.:
        return 0.
    applied_norm = float(np.linalg.norm(weighted_applied/magnitude))
    global_ratio = (float(np.linalg.norm(weighted_residual/magnitude)) /
                    applied_norm if applied_norm else float("inf"))
    active = applied != 0.
    with np.errstate(divide="ignore", over="ignore"):
        active_ratio = float(np.max(np.abs(residual[active]/applied[active]),
                                    initial=0.))
    return max(global_ratio, active_ratio)


def _scaled_constraint_gap(gap, row_scale):
    """Normalize each translation/rotation or weak-line row by fixed work map."""
    gap = np.asarray(gap, dtype=float)
    row_scale = np.asarray(row_scale, dtype=float)
    if (gap.ndim != 1 or gap.shape != row_scale.shape or
            not np.isfinite(gap).all() or
            not np.isfinite(row_scale).all() or
            np.any(row_scale <= 0.)):
        raise ValueError("finite positive constraint row scales required")
    return float(np.max(np.abs(gap)/row_scale, initial=0.))


class ExperimentalGEAnalysis:
    """Owned linear reference slice; no nonlinear or accepted gate claim."""

    def __init__(self, definition: LinearDefinition, resources=None):
        if (type(definition) is not LinearDefinition or
                definition.profile != PROFILE or resources is not None):
            raise ValueError("explicit experimental GE definition required")
        panel = definition.shell
        if type(panel) is not ShellPanel:
            raise ValueError("owned Q4 panel required")
        shell_model, shell_ids, shell_xyz, shell_index, shell_parts = _shell_reference(panel)
        # The compiled owner must not consult caller-owned mutable connectivity
        # when selecting material recovery or decoding a later checkpoint.
        panel = ShellPanel(
            tuple(shell_ids), tuple(map(tuple, shell_xyz.tolist())),
            tuple(tuple(cell) for cell in panel.q4_elements),
            panel.thickness_m, panel.young_pa, panel.poisson,
            panel.density_kg_m3,
            tuple(tuple(cell) for cell in panel.s3_elements), panel.j2_curve)
        definition = LinearDefinition(
            definition.profile, panel, tuple(definition.beams),
            tuple(definition.points), tuple(definition.fixed),
            definition.lines)
        beam_ids, beam_index, beam_nodes, beam_parts, beam_count = _beam_reference(
            definition.beams)
        shell_count = 6*len(shell_ids)
        reference_length, shell_scale, beam_scale = _reference_scales(
            shell_xyz, beam_nodes, beam_parts, shell_count, beam_count)
        shell_r, shell_k, shell_local_error = _assemble_shell(
            shell_model, shell_parts, shell_count, shell_scale)
        beam_r, beam_k, beam_local_error = _assemble_beam(
            beam_parts, beam_nodes, beam_index, beam_count, beam_scale)
        reference_error = max(
            _scaled_reference_residual(shell_r, shell_k, shell_scale),
            _scaled_reference_residual(beam_r, beam_k, beam_scale),
            shell_local_error, beam_local_error)
        if reference_error > 32.*np.finfo(float).eps:
            raise ValueError("reference state must be stress free")
        self._reference_length = reference_length
        self._reference_error = reference_error
        self._K = sparse.block_diag((shell_k, beam_k), format="csr")
        self._coordinate_scale = _owned(np.r_[shell_scale, beam_scale])
        self._shell_count = shell_count
        self._beam_count = beam_count
        self._shell_ids = shell_ids
        self._beam_ids = beam_ids
        self._shell_index = shell_index
        self._beam_index = beam_index
        self._beam_nodes = beam_nodes
        self._shell_xyz = shell_xyz
        self._shell_model = shell_model
        self._shell_parts = tuple(shell_parts)
        self._beam_parts = tuple(beam_parts)
        self._definition = definition
        if (type(definition.lines) is not tuple or
                any(type(line) not in (ExperimentalL1Line, ExperimentalBL5Line)
                    for line in definition.lines)):
            raise ValueError("typed experimental weak lines required")
        identity_payload = {
            "profile": PROFILE, "shell_ids": shell_ids,
            "shell_xyz": shell_xyz.tolist(), "shell_cells": panel.q4_elements,
            "shell_s3_cells": panel.s3_elements,
            "thickness": panel.thickness_m, "E": panel.young_pa,
            "nu": panel.poisson, "density": panel.density_kg_m3,
            "beams": [item.sha256 for item in definition.beams],
            "points": [(v.shell_node, v.beam_node) for v in definition.points],
            "fixed": [(v.domain, v.node, v.component) for v in definition.fixed],
        }
        if panel.j2_curve is not None:
            identity_payload["shell_j2_curve"] = panel.j2_curve.as_dict()
        if definition.lines:
            identity_payload["lines"] = [line.descriptor() for line in
                                         definition.lines]
        self._identity = sha256(json.dumps(
            identity_payload, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        self._connections = []
        self._joint_slots = []
        constraint_rows = []
        row_sources = []
        if not definition.points and not definition.lines:
            raise ValueError("explicit native connection required")
        seen_points = set()
        for tie in definition.points:
            if (type(tie) is not PointConnection or
                    tie.shell_node not in shell_index or tie.beam_node not in beam_index):
                raise ValueError("known point connection nodes required")
            pair = (tie.shell_node, tie.beam_node)
            if pair in seen_points:
                raise ValueError("duplicate experimental point connection")
            seen_points.add(pair)
            shell_slot = 6*shell_index[tie.shell_node]
            beam_slot = shell_count+6*beam_index[tie.beam_node]
            positions = np.array((shell_xyz[shell_index[tie.shell_node]],
                                  beam_nodes[tie.beam_node][0]))
            frames = np.array((np.eye(3), beam_nodes[tie.beam_node][1]))
            joint = RigidPoseJoint(positions, frames)
            evaluation = joint.evaluate(positions, frames, np.zeros(6))
            if np.max(np.abs(evaluation.constraints)) > 1e-10:
                raise ValueError("point connection is not stress free")
            slots = np.r_[np.arange(shell_slot, shell_slot+6),
                          np.arange(beam_slot, beam_slot+6)]
            constraint_rows.append((slots, evaluation.constraint_jacobian))
            row_sources.extend(
                f"point shell={tie.shell_node} beam={tie.beam_node} row={row}"
                for row in range(6))
            self._connections.append(joint)
            self._joint_slots.append(slots)
        c_row, c_col, c_data = [], [], []
        for i, (slots, jacobian) in enumerate(constraint_rows):
            c_row.extend(np.repeat(np.arange(6*i, 6*i+6), 12))
            c_col.extend(np.tile(slots, 6))
            c_data.extend(jacobian.ravel())
        count = self._K.shape[0]
        self._C = sparse.coo_matrix((c_data, (c_row, c_col)),
                                    shape=(6*len(constraint_rows), count)).tocsr()
        if definition.lines:
            line_c, self._line_samples = _compile_weak_lines(
                definition.lines, shell_ids=shell_ids, shell_xyz=shell_xyz,
                shell_cells=panel.q4_elements+panel.s3_elements,
                thickness=panel.thickness_m, beam_ids=beam_ids,
                beam_nodes=beam_nodes, beam_parts=beam_parts,
                shell_count=shell_count, beam_count=beam_count)
            self._C = sparse.vstack((self._C, line_c), format="csr")
            row_sources.extend(
                f"line {index} shell={line.shell_nodes[0]}..{line.shell_nodes[-1]} row={row}"
                for index, line in enumerate(definition.lines)
                for row in range(_weak_line_row_count(line)))
        else:
            self._line_samples = ()
        self._constraint_scale = _owned(
            np.asarray(np.abs(self._C)@self._coordinate_scale).reshape(-1))
        if np.any(self._constraint_scale <= 0.):
            raise ValueError("nonzero physical constraint row scales required")
        fixed = set()
        for support in definition.fixed:
            if (type(support) is not FixedCoordinate or
                    support.domain not in ("shell", "beam") or
                    type(support.component) is not int or
                    not 0 <= support.component < 6):
                raise ValueError("known physical fixed coordinate required")
            index = shell_index if support.domain == "shell" else beam_index
            if support.node not in index:
                raise ValueError("known physical fixed node required")
            start = 0 if support.domain == "shell" else shell_count
            fixed.add(start+6*index[support.node]+support.component)
        self._fixed = np.array(sorted(fixed), dtype=int)
        self._free = np.setdiff1d(np.arange(count), self._fixed)
        if not len(self._fixed) or not len(self._free):
            raise ValueError("physical supports and free coordinates required")
        _require_independent_supported_rows(
            self._C, self._free, self._coordinate_scale,
            self._constraint_scale, tuple(row_sources))
        self._A = sparse.bmat([
            [self._K[self._free, :][:, self._free], self._C[:, self._free].T],
            [self._C[:, self._free], None]], format="csc")
        if self._A.shape[0] < 1 or self._A.nnz == 0:
            raise ValueError("nonempty constrained mixed operator required")
        self._accepted = None
        self._finite_driver = None
        self._generation = 0
        self._closed = False
        self._linear_factor = None
        self._linear_factorizations = 0
        self._linear_refinements = 0

    def _require_open(self):
        if self._closed:
            raise RuntimeError("experimental GE analysis is closed")

    @property
    def capabilities(self):
        attachment = (("reference point pose",) if self._connections else ())
        if self._line_samples:
            attachment += tuple(dict.fromkeys(
                "experimental L1 weak-line candidate"
                if type(line) is ExperimentalL1Line else
                "experimental BL5 director-bond candidate"
                for line in self._definition.lines))
        shell_plastic = self._definition.shell.j2_curve is not None
        excluded = ((("shell J2 plastic",) if not shell_plastic else ()) +
                    ("physical-fibre B3 finite",
                     "nonpositive finite load factors", "line", "footprint",
                     "modes", "buckling")
                    if not self._line_samples else
                    ("shell J2 plastic", "physical-fibre B3 finite",
                     "qualified bonded line", "nonmatching line mapping", "footprint",
                     "modes", "buckling"))
        if self._definition.shell.s3_elements and not self._line_samples:
            excluded += ("S3 corotational finite-rotation response",)
        return {"profile": PROFILE, "status": "EXPERIMENTAL_NOT_QUALIFIED",
                "shell": (("experimental isotropic Q4/S3-V2D J2"
                           if self._definition.shell.s3_elements else
                           "experimental isotropic Q4 J2") if shell_plastic else
                          "elastic flat Q4/S3"),
                "beam": ("generalized B3 retained" if self._line_samples else
                         "generalized B3 retained, including experimental yielding"),
                "attachment": attachment,
                "experimental_line_spaces": tuple(
                    line.multiplier_space for line in self._definition.lines),
                "analysis": (("reference_linear",) if self._line_samples else
                             ("reference_linear", "experimental_elastic_finite_point",
                              "experimental_generalized_plastic_finite_point") +
                             (("experimental_q4_s3_j2_finite_point",)
                              if shell_plastic and self._definition.shell.s3_elements
                              else ("experimental_q4_j2_finite_point",)
                              if shell_plastic
                              else ())),
                "excluded": excluded}

    def preflight(self):
        self._require_open()
        return {"identity": self._identity, "physical_dofs": self._shell_count+
                6*len(self._beam_ids), "retained_dofs": self._beam_count-
                6*len(self._beam_ids), "constraints": self._C.shape[0],
                "matrix_nnz": self._A.nnz,
                "experimental_line_samples": len(self._line_samples),
                "reference_linear_factorizations": self._linear_factorizations,
                "reference_linear_refinements": self._linear_refinements,
                "reference_length_m": self._reference_length,
                "stress_free_scaled_max": self._reference_error,
                "equilibrium_norm": "frozen_work_weighted_l2_plus_active_load_rows",
                "constraint_norm": "reference_row_scaled_max",
                "production_qualified": False}

    def solve_linear(self, actions: tuple[NodalAction, ...], *,
                     cancellation_token=None) -> LinearResult:
        self._require_open()
        if self._finite_driver is not None:
            raise RuntimeError("finite and reference-linear states cannot be mixed")
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.start")
        load = np.zeros(self._K.shape[0])
        for action in actions:
            if type(action) is not NodalAction or action.domain not in ("shell", "beam"):
                raise ValueError("declared shell or beam nodal action required")
            index = self._shell_index if action.domain == "shell" else self._beam_index
            if action.node not in index:
                raise ValueError("action references unknown physical node")
            wrench = _owned(action.wrench, (6,))
            offset = 0 if action.domain == "shell" else self._shell_count
            load[offset+6*index[action.node]:offset+6*index[action.node]+6] += wrench
        rhs = np.r_[load[self._free], np.zeros(self._C.shape[0])]
        if self._linear_factor is None:
            self._linear_factor = spla.splu(self._A)
            self._linear_factorizations += 1
        solution = self._linear_factor.solve(rhs)
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.solved")
        for attempt in range(2):
            if not np.isfinite(solution).all():
                raise RuntimeError("finite mixed linear solution required")
            q = np.zeros(self._K.shape[0])
            q[self._free] = solution[:len(self._free)]
            multipliers = solution[len(self._free):]
            equilibrium = self._K@q + self._C.T@multipliers-load
            gap = self._C@q
            relative = _linear_equilibrium(
                equilibrium[self._free], load[self._free],
                self._coordinate_scale[self._free])
            constraint = _scaled_constraint_gap(gap, self._constraint_scale)
            if np.isfinite(relative) and relative <= 1e-8 and constraint <= 1e-9:
                break
            if attempt == 0:
                # Correct factorization roundoff in retained equations using
                # the same operator; the physical acceptance limits stay fixed.
                correction = self._linear_factor.solve(rhs-self._A@solution)
                self._linear_refinements += 1
                cancellation_safe_point(cancellation_token,
                                        "stiffened-shell.linear.refined")
                solution = solution+correction
        if not np.isfinite(relative) or relative > 1e-8 or constraint > 1e-9:
            raise RuntimeError("mixed reference linear equilibrium failed")
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.commit")
        support = np.zeros_like(equilibrium)
        support[self._fixed] = equilibrium[self._fixed]
        self._generation += 1
        result = LinearResult("completed", _owned(q[:self._shell_count]),
                              _owned(q[self._shell_count:]),
                              _owned(multipliers), _owned(support),
                              relative, constraint, self._generation)
        self._accepted = (result, _owned(load))
        return result

    def solve(self, actions: tuple[NodalAction, ...],
              targets: tuple[float, ...] = (1.,), *, cancellation_token=None,
              max_iterations: int = 12, max_backtracks: int = 8):
        """Advance point-coupled finite trials from one accepted predecessor."""
        self._require_open()
        if self._line_samples:
            raise ValueError("experimental weak line admits reference-linear analysis only")
        if self._accepted is not None:
            raise RuntimeError("finite and reference-linear states cannot be mixed")
        if self._finite_driver is None:
            from ._stiffened_shell_ge_finite_experimental import FinitePointDriver
            driver = FinitePointDriver(self)
        else:
            driver = self._finite_driver
        try:
            return driver.solve(
                actions, targets, cancellation_token=cancellation_token,
                max_iterations=max_iterations, max_backtracks=max_backtracks)
        finally:
            if self._finite_driver is None and driver._accepted is not None:
                self._finite_driver = driver

    def recover(self) -> LinearResult:
        self._require_open()
        if self._finite_driver is not None:
            return self._finite_driver.recover()
        if self._accepted is None:
            raise RuntimeError("no accepted mixed linear result")
        return self._accepted[0]

    def checkpoint(self) -> bytes:
        self._require_open()
        if self._finite_driver is not None:
            return self._finite_driver.checkpoint()
        if self._accepted is None:
            raise RuntimeError("no accepted mixed linear result")
        result, load = self._accepted
        arrays = (("q", np.r_[result.shell_displacement,
                               result.beam_coordinates]),
                  ("multipliers", result.multipliers), ("load", load))
        if sum(value.size for _name, value in arrays) > MAX_JSON_CHECKPOINT_VALUES:
            return _encode_binary_checkpoint(
                "linear", self._identity, self._generation, arrays)
        payload = {"schema": CHECKPOINT, "model": self._identity,
                   "generation": self._generation,
                   "q": arrays[0][1].tolist(),
                   "multipliers": arrays[1][1].tolist(),
                   "load": arrays[2][1].tolist()}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("ascii")
        if len(raw) > MAX_JSON_CHECKPOINT_BYTES:
            return _encode_binary_checkpoint(
                "linear", self._identity, self._generation, arrays)
        return raw

    def restore(self, raw: bytes) -> LinearResult:
        self._require_open()
        if self._finite_driver is not None:
            raise RuntimeError("restore requires a fresh experimental GE analysis")
        if self._accepted is not None:
            raise RuntimeError("restore requires a fresh experimental GE analysis")
        if type(raw) is not bytes:
            raise ValueError("bounded mixed linear checkpoint required")
        if raw.startswith(BINARY_CHECKPOINT_MAGIC):
            def expected_shapes(kind, generation):
                if kind in ("finite", "finite_material", "finite_shell_material") and self._line_samples:
                    raise ValueError(
                        "experimental L1 line admits reference-linear checkpoints only")
                count = self._K.shape[0]
                constraints = self._C.shape[0]
                if kind == "linear":
                    return (("q", (count,)), ("multipliers", (constraints,)),
                            ("load", (count,)))
                members = len(self._beam_parts)
                base = (("q", (count,)),
                        ("frames", (len(self._beam_ids), 3, 3)),
                        ("cells", (members, 2, 3, 3)),
                        ("resultants", (members, 18)),
                        ("multipliers", (constraints,)),
                        ("pattern", (count,)),
                        ("accepted_factors", (generation,)))
                if kind in ("finite_material", "finite_shell_material"):
                    stations = sum(len(part[0].operator.cell.stations)
                                   for part in self._beam_parts)
                    material = base + (("beam_plastic", (stations, 6, 2)),
                                       ("beam_accumulated", (stations, 2)))
                    if kind == "finite_shell_material":
                        if self._definition.shell.j2_curve is None:
                            raise ValueError("shell J2 checkpoint requires matching material")
                        material += (("shell_plastic", (len(self._shell_parts), 12, 3)),
                                     ("shell_alpha", (len(self._shell_parts), 12)))
                    return material
                return base

            kind, generation, arrays = _decode_binary_checkpoint(
                raw, self._identity, expected_shapes)
            schema = (CHECKPOINT if kind == "linear" else
                      FINITE_MATERIAL_CHECKPOINT if kind == "finite_material" else
                      FINITE_SHELL_MATERIAL_CHECKPOINT if kind == "finite_shell_material"
                      else FINITE_CHECKPOINT)
            value = {"schema": schema, "model": self._identity,
                     "generation": generation, **arrays}
            if kind in ("finite", "finite_material", "finite_shell_material"):
                value["accepted_factors"] = arrays["accepted_factors"].tolist()
        elif raw.startswith(S3_BINARY_CHECKPOINT_MAGIC):
            if (self._line_samples or self._definition.shell.j2_curve is None or
                    not self._definition.shell.s3_elements):
                raise ValueError("S3 J2 checkpoint requires matching point model")

            def expected_s3_shapes(generation):
                count = self._K.shape[0]
                members = len(self._beam_parts)
                stations = sum(len(part[0].operator.cell.stations)
                               for part in self._beam_parts)
                q4_count = len(self._definition.shell.q4_elements)
                return (("q", (count,)),
                        ("frames", (len(self._beam_ids), 3, 3)),
                        ("cells", (members, 2, 3, 3)),
                        ("resultants", (members, 18)),
                        ("multipliers", (self._C.shape[0],)),
                        ("pattern", (count,)),
                        ("accepted_factors", (generation,)),
                        ("beam_plastic", (stations, 6, 2)),
                        ("beam_accumulated", (stations, 2)),
                        ("shell_plastic", (q4_count, 12, 3)),
                        ("shell_alpha", (q4_count, 12)))

            generation, arrays, states = _decode_s3_binary_checkpoint(
                raw, self._identity, expected_s3_shapes,
                len(self._definition.shell.s3_elements))
            value = {"schema": FINITE_S3_MATERIAL_CHECKPOINT,
                     "model": self._identity, "generation": generation,
                     **arrays, "s3_states": states,
                     "accepted_factors": arrays["accepted_factors"].tolist()}
        else:
            if len(raw) > MAX_JSON_CHECKPOINT_BYTES:
                raise ValueError("bounded mixed linear checkpoint required")
            try:
                value = json.loads(raw.decode("ascii"))
            except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
                raise ValueError("invalid mixed linear checkpoint") from exc
        if (type(value) is dict and value.get("schema") in
                (FINITE_CHECKPOINT, FINITE_MATERIAL_CHECKPOINT,
                 FINITE_SHELL_MATERIAL_CHECKPOINT,
                 FINITE_S3_MATERIAL_CHECKPOINT)):
            if self._line_samples:
                raise ValueError(
                    "experimental weak line admits reference-linear checkpoints only")
            from ._stiffened_shell_ge_finite_experimental import FinitePointDriver
            driver = FinitePointDriver(self)
            result = driver.restore(value)
            self._finite_driver = driver
            return result
        if (type(value) is not dict or set(value) !=
                {"schema", "model", "generation", "q", "multipliers", "load"} or
                value["schema"] != CHECKPOINT or value["model"] != self._identity or
                type(value["generation"]) is not int or value["generation"] < 1):
            raise ValueError("incompatible mixed linear checkpoint")
        q = _owned(value["q"], (self._K.shape[0],))
        lam = _owned(value["multipliers"], (self._C.shape[0],))
        load = _owned(value["load"], (self._K.shape[0],))
        equilibrium = self._K@q+self._C.T@lam-load
        relative = _linear_equilibrium(
            equilibrium[self._free], load[self._free],
            self._coordinate_scale[self._free])
        constraint = _scaled_constraint_gap(
            self._C@q, self._constraint_scale)
        if (not np.isfinite(relative) or relative > 1e-8 or constraint > 1e-9 or
                np.max(np.abs(q[self._fixed])) > 1e-12):
            raise ValueError("mechanically inconsistent mixed linear checkpoint")
        support = np.zeros_like(equilibrium)
        support[self._fixed] = equilibrium[self._fixed]
        result = LinearResult("completed", _owned(q[:self._shell_count]),
                              _owned(q[self._shell_count:]), lam,
                              _owned(support), relative, constraint,
                              value["generation"])
        self._accepted = (result, load)
        self._generation = value["generation"]
        return result

    def close(self):
        self._accepted = None
        self._finite_driver = None
        self._linear_factor = None
        self._closed = True
