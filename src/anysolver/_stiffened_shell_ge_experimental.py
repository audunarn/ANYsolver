"""Experimental sparse reference-linear GE/Q4 point-connected panel.

This is an integration slice, not an accepted G0/G1 formulation.  It retains
all native B3 cell variables and uses the existing objective point operator.
Qualified line coupling and material updates are separate work. The optional
L1 weak-line route is reference-linear and explicitly unqualified.
The BL5 finite route admits elastic response only and remains unqualified.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from copy import copy
from hashlib import sha256
from functools import wraps
from threading import RLock
import json
import warnings

from anymaterial import DNVC208MaterialCurve
import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as spla
from scipy.sparse.csgraph import maximum_bipartite_matching

from ._ge_beam3_native_definition import NativeBeamDefinition
from ._ge_beam3_fibre_section import PhysicalFibreSection
from ._ge_beam3_pose_joint import RigidPoseJoint
from ._stiffened_shell_point_recovery import PointTransferWrench, reference_point_records
from ._stiffened_shell_nodal_footprint import (
    NodalRigidFootprint, NodalRigidFootprintSelection, NodalRigidFootprintWrench,
    validate_footprints, selected_wrenches, stable_s3_policy_descriptor,
    retained_scale_policy_descriptor, chart_admission_policy_descriptor,
    require_rotation_triples,
    CHART_ADMISSION_POLICY, INCREMENT_ORIGIN_CHART_POLICY,
)
from ._ge_beam3_generalized_static_boundary import spatial_jacobian
from ._stiffened_shell_s3_algorithmic_pullback import POLICY as S3_J2_PULLBACK_POLICY
from ._stiffened_shell_q4_algorithmic_pullback import (
    POLICY as Q4_ALGORITHMIC_PULLBACK_V1, HISTORICAL_POLICY as Q4_HISTORICAL_POLICY,
    response as q4_algorithmic_response,
)
from .corotational import corotational_element_response
from .elements import create_shell_element
from .fe_core import FEModel
from .control import cancellation_safe_point
from ._stiffened_shell_ge_checkpoint_binary import (
    MAGIC as BINARY_CHECKPOINT_MAGIC, decode as _decode_binary_checkpoint,
    encode as _encode_binary_checkpoint, S3_MAGIC as S3_BINARY_CHECKPOINT_MAGIC,
    S3_SCHEMA as FINITE_S3_MATERIAL_CHECKPOINT,
    decode_s3 as _decode_s3_binary_checkpoint,
    CHART_MAGIC as CHART_CHECKPOINT_MAGIC, decode_chart as _decode_chart_checkpoint,
    NATIVE_SHELL_MAGIC, NATIVE_SHELL_SCHEMA, STABLE_NATIVE_SCHEMA,
    SCHEMAS as _BINARY_SCHEMAS,
)
from ._stiffened_shell_increment_control import (
    MAGIC as INCREMENT_CONTROL_MAGIC, decode_control, validate_control,
)
from ._stiffened_shell_l1_assembly_experimental import (
    ExperimentalL1Line, ExperimentalBL5Line,
    compile_lines as _compile_weak_lines,
    _row_count as _weak_line_row_count,
)


PROFILE = "B3_GE_E4_PL_STIFFENED_SHELL_V1"
BL5_GENERALIZED_MATERIAL_V1 = "BL5_GENERALIZED_MATERIAL_V1_DEV"
BL5_COUPLED_J2_MATERIAL_V1 = "BL5_COUPLED_J2_MATERIAL_V1_DEV"
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


def _state_writer(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._operation_lock:
            if self._writing:
                raise RuntimeError("reentrant mixed state mutation is not permitted")
            self._writing = True
            try:
                return method(self, *args, **kwargs)
            finally:
                self._writing = False
    return call


def _accepted_snapshot(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._commit_lock:
            return method(self, *args, **kwargs)
    return call


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
    q4_pullback_policy: str = Q4_HISTORICAL_POLICY
    footprints: tuple[NodalRigidFootprint, ...] = ()
    modal_boundary_policy: str = "supported"
    footprint_chart_policy: str = CHART_ADMISSION_POLICY
    bl5_material_policy: str = "elastic"


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
    point_wrenches: tuple[PointTransferWrench, ...] = ()
    body_load: object | None = None
    distributed_load: object | None = None
    pressure_load: object | None = None


def _owned(values, shape=None):
    result = np.array(values, dtype=float, copy=True)
    if (shape is not None and result.shape != shape) or not np.isfinite(result).all():
        raise ValueError("finite owned stiffened-shell values required")
    return np.frombuffer(result.tobytes(), dtype=float).reshape(result.shape)


def _shell_reference(panel: ShellPanel):
    ids = tuple(panel.node_ids)
    xyz = _owned(panel.coordinates_m, (len(ids), 3))
    if (len(ids) < 3 or len(ids) != len(set(ids)) or
            len(panel.q4_elements)+len(panel.s3_elements) < 1 or
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
    if len(definitions) < 1 or any(type(v) is not NativeBeamDefinition
                                   for v in definitions):
        raise ValueError("explicit native B3 definition required")
    elements = []
    inertias = []
    nodes = {}
    for definition in definitions:
        element, _inertia = definition.instantiate()
        inertias.append(_inertia)
        if (type(element.section).__name__ != "EllipsoidalGeneralizedSection" and
                type(element.section) is not PhysicalFibreSection):
            raise ValueError("explicit native generalized or physical-fibre section required")
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
    return ids, index, nodes, pieces, nodal+24*len(pieces), tuple(inertias)


def _assemble_shell(model, pieces, count, coordinate_scale,
                    q4_pullback_policy=Q4_HISTORICAL_POLICY):
    rows, columns, data = [], [], []
    residual = np.zeros(count)
    local_error = 0.
    for eid, element, slots, origin in pieces:
        if len(slots) == 18:
            force, tangent, candidate = element.compute_nonlinear_response(
                model.mesh, model.get_material("shell"), np.zeros(18),
                origin, 3, True)
        elif q4_pullback_policy == Q4_ALGORITHMIC_PULLBACK_V1:
            force, tangent, candidate = q4_algorithmic_response(
                model, element, np.zeros(24), origin, 3)
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


def _reference_section_tangent(section):
    """Virgin elastic derivative for compilation scales, never a trial cache."""
    if type(section) is PhysicalFibreSection:
        response = section.response(np.zeros(6), section.virgin())
        return response.tangent + response.tangent_low
    return section.elastic


def _reference_scales(shell_xyz, beam_nodes, beam_parts, shell_count,
                      beam_count, *, footprint_retained_roles=False):
    """Freeze compilation scales; selected new profiles use native retained roles.

    Legacy owners retain their historical arrangement exactly. The footprint and
    coupled-J2 BL5 policies select native retained force/moment work pairing.
    """
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
        resultant_scale = np.abs(_reference_section_tangent(element.section))@strain_scale
        # Native p consists of six independent force coordinates followed by
        # twelve moment coordinates, not three recovered station wrenches.
        # Preserve the historical arrangement for policies that have not selected
        # the native retained-role scaling contract.
        if footprint_retained_roles:
            beam_scale[base+6:base+24] = np.r_[np.tile(resultant_scale[:3], 2),
                                             np.tile(resultant_scale[3:], 4)]
        else:
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
    work units when supplied scales match the actual coordinate roles; unit
    invariance assumes that same correctly packed work-conjugate pairing.
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
        from ._stiffened_shell_ge_reference_modal import GE_FREE_FREE_MODAL_ONLY_V1
        if (type(definition.modal_boundary_policy) is not str or
                definition.modal_boundary_policy not in ("supported", GE_FREE_FREE_MODAL_ONLY_V1)):
            raise ValueError("explicit admitted GE modal boundary policy required")
        self._modal_only = definition.modal_boundary_policy == GE_FREE_FREE_MODAL_ONLY_V1
        if self._modal_only and (definition.fixed or definition.lines or definition.footprints):
            raise ValueError("free-free modal-only policy requires empty supports and six-pose points only")
        if (type(definition.bl5_material_policy) is not str or
                definition.bl5_material_policy not in ("elastic", BL5_GENERALIZED_MATERIAL_V1, BL5_COUPLED_J2_MATERIAL_V1)):
            raise ValueError("explicit admitted BL5 material policy required")
        self._bl5_shell_material = definition.bl5_material_policy == BL5_COUPLED_J2_MATERIAL_V1
        self._bl5_material = definition.bl5_material_policy != "elastic"
        if self._bl5_material and (not definition.lines or definition.footprints or
                definition.q4_pullback_policy != Q4_ALGORITHMIC_PULLBACK_V1):
            raise ValueError("BL5 material policy requires objective Q4 line model")
        panel = definition.shell
        if type(panel) is not ShellPanel:
            raise ValueError("owned Q4 panel required")
        if (type(definition.q4_pullback_policy) is not str or
                definition.q4_pullback_policy not in (Q4_HISTORICAL_POLICY, Q4_ALGORITHMIC_PULLBACK_V1)):
            raise ValueError("explicit admitted Q4 pullback policy required")
        if definition.footprints and definition.lines:
            raise ValueError("experimental nodal rigid footprints require point-owner-only attachment scope")
        if definition.q4_pullback_policy == Q4_ALGORITHMIC_PULLBACK_V1 and (
                not panel.q4_elements or (definition.lines and (
                    panel.s3_elements or (panel.j2_curve is not None and not self._bl5_shell_material) or
                    any(type(line) is not ExperimentalBL5Line for line in definition.lines)))):
            raise ValueError("algorithmic Q4 pullback requires a Q4-containing point or explicitly admitted Q4 BL5 model")
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
            definition.lines, definition.q4_pullback_policy, definition.footprints,
            definition.modal_boundary_policy, definition.footprint_chart_policy,
            definition.bl5_material_policy)
        beam_ids, beam_index, beam_nodes, beam_parts, beam_count, beam_inertias = _beam_reference(
            definition.beams)
        self._reference_modal_inertias = beam_inertias
        self._reference_modal_mass = None
        self._has_physical_fibre = any(type(element.section) is PhysicalFibreSection
                                      for element, _, _ in beam_parts)
        if definition.footprints:
            if (panel.q4_elements and
                    definition.q4_pullback_policy != Q4_ALGORITHMIC_PULLBACK_V1):
                raise ValueError("nodal rigid footprints require explicitly selected full-map Q4")
            if panel.j2_curve is not None or self._has_physical_fibre:
                raise ValueError("experimental nodal rigid footprints admit elastic shell and generalized beam response only")
            if (any(type(v) is not PointConnection for v in definition.points) or
                    type(definition.lines) is not tuple or
                    any(type(v) not in (ExperimentalL1Line, ExperimentalBL5Line)
                        for v in definition.lines)):
                raise ValueError("typed explicit point/line attachment declarations required")
        definition = replace(definition, footprints=validate_footprints(
            definition.footprints, shell_index, shell_xyz,
            panel.q4_elements+panel.s3_elements, beam_index,
            definition.points, definition.lines))
        chart_admission_policy_descriptor(definition.footprint_chart_policy)
        if (definition.footprint_chart_policy == INCREMENT_ORIGIN_CHART_POLICY and
                (not definition.footprints or definition.lines)):
            raise ValueError("increment-origin chart policy requires an elastic nodal footprint model without lines")
        self._footprint_increment_chart = bool(
            definition.footprints and definition.footprint_chart_policy == INCREMENT_ORIGIN_CHART_POLICY)
        self._finite_elastic_footprint = bool(definition.footprints)
        self._footprint_stable_s3 = bool(definition.footprints and panel.s3_elements
                                        and not definition.lines)
        self._beam_families = tuple(dict.fromkeys(
            "PHYSICAL_AXIAL_BIAXIAL_FIBRE" if type(element.section) is PhysicalFibreSection
            else "RESULTANT_ELLIPSOID" for element, _, _ in beam_parts))
        if self._has_physical_fibre and definition.lines:
            raise ValueError("physical-fibre mixed owner currently admits point attachments only")
        shell_count = 6*len(shell_ids)
        reference_length, shell_scale, beam_scale = _reference_scales(
            shell_xyz, beam_nodes, beam_parts, shell_count, beam_count,
            footprint_retained_roles=(self._finite_elastic_footprint or self._bl5_shell_material))
        shell_r, shell_k, shell_local_error = _assemble_shell(
            shell_model, shell_parts, shell_count, shell_scale,
            definition.q4_pullback_policy)
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
        self._finite_bl5 = bool(definition.lines) and all(
            type(line) is ExperimentalBL5Line for line in definition.lines
        ) and (panel.j2_curve is None or self._bl5_shell_material) and not self._has_physical_fibre
        if definition.lines and definition.q4_pullback_policy == Q4_ALGORITHMIC_PULLBACK_V1 and not self._finite_bl5:
            raise ValueError("algorithmic Q4 line pullback requires admitted generalized BL5 beams")
        if self._bl5_material and not self._finite_bl5:
            raise ValueError("BL5 material policy requires admitted Q4 shells and generalized beams")
        if self._bl5_shell_material and panel.j2_curve is None:
            raise ValueError("coupled BL5 material policy requires shell J2")
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
        if self._bl5_shell_material:
            identity_payload["bl5_retained_scale_policy"] = "native_force_moment_roles_v1"
        if self._bl5_material:
            identity_payload["bl5_material_policy"] = definition.bl5_material_policy
        if panel.j2_curve is not None:
            identity_payload["shell_j2_curve"] = panel.j2_curve.as_dict()
            if panel.s3_elements:
                # Experimental direct-coordinate histories must not silently
                # resume with the new objective local constitutive map.
                identity_payload["shell_s3_material_policy"] = S3_J2_PULLBACK_POLICY
        if definition.q4_pullback_policy != Q4_HISTORICAL_POLICY:
            identity_payload["shell_q4_pullback_policy"] = definition.q4_pullback_policy
        if definition.lines:
            identity_payload["lines"] = [line.descriptor() for line in
                                         definition.lines]
        if definition.footprints:
            identity_payload["nodal_rigid_footprints"] = [
                group.descriptor() for group in definition.footprints]
            identity_payload["footprint_retained_scale_policy"] = retained_scale_policy_descriptor()
            identity_payload["footprint_chart_admission_policy"] = chart_admission_policy_descriptor(definition.footprint_chart_policy)
        if self._footprint_stable_s3:
            identity_payload["footprint_finite_numerical_policy"] = stable_s3_policy_descriptor()
        if self._modal_only:
            identity_payload["modal_boundary_policy"] = definition.modal_boundary_policy
        self._identity = sha256(json.dumps(
            identity_payload, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        self._connections = []
        self._joint_slots = []
        incidence = list(definition.points)
        bindings = []
        footprint_sources = {}
        for group in definition.footprints:
            indices = tuple(range(len(incidence), len(incidence)+len(group.shell_nodes)))
            bindings.append((group, indices))
            for index, node in zip(indices, group.shell_nodes):
                incidence.append(PointConnection(node, group.beam_node))
                footprint_sources[index] = f"footprint={group.footprint_id} "
        self._point_incidence = tuple(incidence)
        self._footprint_bindings = tuple(bindings)
        constraint_rows = []
        row_sources = []
        if not self._point_incidence and not definition.lines:
            raise ValueError("explicit native connection required")
        seen_points = set()
        for point_index, tie in enumerate(self._point_incidence):
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
                footprint_sources.get(point_index, "")+
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
            line_c, self._line_samples, self._line_terms = _compile_weak_lines(
                definition.lines, shell_ids=shell_ids, shell_xyz=shell_xyz,
                shell_cells=panel.q4_elements+panel.s3_elements,
                thickness=panel.thickness_m, beam_ids=beam_ids,
                beam_nodes=beam_nodes, beam_parts=beam_parts,
                shell_count=shell_count, beam_count=beam_count, with_terms=True)
            self._C = sparse.vstack((self._C, line_c), format="csr")
            row_sources.extend(
                f"line {index} shell={line.shell_nodes[0]}..{line.shell_nodes[-1]} row={row}"
                for index, line in enumerate(definition.lines)
                for row in range(_weak_line_row_count(line)))
        else:
            self._line_samples = ()
            self._line_terms = ()
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
        if (not len(self._fixed) and not self._modal_only) or not len(self._free):
            raise ValueError("physical supports and free coordinates required")
        # This exact five-row layout cannot restrain all six rigid motions
        # of an otherwise free native beam. Other lines or beam supports may
        # supply the missing restraint and are not classified here.
        self._unsupported_modes = (
            ("single-support BL5 leaves a free native beam rigid mode",)
            if (len(definition.lines) == 1 and
                type(definition.lines[0]) is ExperimentalBL5Line and
                definition.lines[0].basis == "p0" and
                len(definition.lines[0].beam_halfcells) ==
                definition.lines[0].multiplier_span and
                not self._connections and
                not any(support.domain == "beam" for support in definition.fixed))
            else ())
        _require_independent_supported_rows(
            self._C, self._free, self._coordinate_scale,
            self._constraint_scale, tuple(row_sources))
        self._A = sparse.bmat([
            [self._K[self._free, :][:, self._free], self._C[:, self._free].T],
            [self._C[:, self._free], None]], format="csc")
        if self._A.shape[0] < 1 or self._A.nnz == 0:
            raise ValueError("nonempty constrained mixed operator required")
        self._operation_lock = RLock()
        self._writing = False
        self._commit_lock = RLock()
        self._accepted = None
        self._finite_driver = None
        self._generation = 0
        self._closed = False
        self._linear_factor = None
        self._linear_factorizations = 0
        self._linear_refinements = 0
        if self._modal_only:
            from ._stiffened_shell_ge_reference_modal import _admit
            _admit(self)

    def _require_open(self):
        if self._closed:
            raise RuntimeError("experimental GE analysis is closed")

    def _require_stateful_scope(self):
        if self._modal_only:
            raise ValueError("free-free modal-only policy does not admit static, finite, restore or chart state writes")

    @property
    def capabilities(self):
        from ._stiffened_shell_ge_distributed_load import admits_owner as admits_distributed
        if self._modal_only:
            return dict(self.reference_modal_capabilities, profile=PROFILE,
                        modal_boundary_policy=self._definition.modal_boundary_policy,
                        accepted_state_writes=False)
        attachment = (("reference point pose",) if self._connections else ())
        if self._line_samples:
            attachment += tuple(dict.fromkeys(
                "experimental L1 weak-line candidate"
                if type(line) is ExperimentalL1Line else
                "experimental BL5 director-bond candidate"
                for line in self._definition.lines))
        shell_plastic = self._definition.shell.j2_curve is not None
        line_limits = tuple(dict.fromkeys(
            "nonmatching L1 line mapping" if type(line) is ExperimentalL1Line
            else "curved/reversed BL5 line mapping"
            for line in self._definition.lines))
        excluded = ((("shell J2 plastic",) if not shell_plastic else ()) +
                    ("nonpositive finite load factors", "line", "footprint",
                     "modes", "buckling")
                    if not self._line_samples else
                    ((() if self._bl5_shell_material else ("shell J2 plastic",)) + ("physical-fibre B3 finite",
                     "qualified bonded line", "footprint",
                     "modes", "buckling"))+line_limits)
        if self._finite_bl5 and not self._bl5_material:
            excluded += ("generalized B3 plastic finite BL5",)
        if (self._definition.shell.s3_elements and shell_plastic and
                not self._line_samples):
            excluded += ("qualified S3 J2 finite-rotation response",)
        capabilities = {"profile": PROFILE, "status": "EXPERIMENTAL_NOT_QUALIFIED",
                "shell": (("experimental isotropic Q4/S3-V2D J2"
                           if self._definition.shell.s3_elements else
                           "experimental isotropic Q4 J2") if shell_plastic else
                          "elastic flat Q4/S3"),
                "beam": ("native B3 retained, experimental physical-fibre histories"
                         if self._has_physical_fibre else
                         "generalized B3 retained" if self._line_samples else
                         "generalized B3 retained, including experimental yielding"),
                "beam_section_families": self._beam_families,
                "attachment": attachment,
                "point_recovery": "accepted global spatial connection actions; reference-linear or current ports",
                "body_acceleration": (() if self._line_samples or self._definition.footprints else
                    ("experimental uniform spatial acceleration; explicit physical beam inertia and shell density; reference-linear or conservative finite work with objective Q4 pullback; GEBodyLoad",)),
                "beam_distributed_loads": (() if not admits_distributed(self) else
                    ("experimental element-addressed fixed-spatial force/couple per reference arclength; native quadrature; couples nonconservative; GEBeamDistributedLoad",)),
                "staged_beam_distributed_loads": (() if not admits_distributed(self) else
                    ("experimental GEBeamDistributedProgramme; absolute signed force/couple densities at positive forward positions; point or objective elastic Q4 BL5 owner; zero-load convergence unresolved under current equilibrium assessment; not qualified",)),
                "shell_pressure_loads": (() if self._line_samples or self._definition.footprints else
                    ("experimental GEShellPressureLoad; shell IDs are Q4 then S3, one-based; reference-linear native dead pressure; finite Q4 dead and Q4/S3 interpolation-surface current-area follower pressure; finite native reference_dead S3 is unsupported; explicit reference_dead_director_v2 admits a distinct virgin-elastic S3 director-enhanced dead surface with relative tilt below 0.9*pi, not qualified",)),
                "staged_dead_loads": (() if self._line_samples and not (
                    self._finite_bl5 and self._definition.q4_pullback_policy == Q4_ALGORITHMIC_PULLBACK_V1) else
                    ("experimental immutable piecewise-affine translation forces; forward programme position",)),
                "experimental_line_spaces": tuple(
                    line.multiplier_space for line in self._definition.lines),
                "q4_force_map": self._definition.q4_pullback_policy,
                "bl5_material_policy": self._definition.bl5_material_policy,
                "increment_control": (() if self._line_samples and not self._finite_bl5 else
                    ("fixed", "experimental_adaptive_halving")),
                "rotation_chart": ("unchanged reference-linear chart"
                                   if self._line_samples and not self._finite_bl5 else
                                   "experimental owned shell anchors; full fixed/free rotational triples only"),
                "analysis": (("reference_linear", "experimental_coupled_j2_material_bl5" if self._bl5_shell_material else "experimental_generalized_material_bl5" if self._bl5_material else "experimental_elastic_finite_bl5")
                             if self._finite_bl5 else
                             ("reference_linear",) if self._line_samples else
                             ("reference_linear", "experimental_native_fibre_finite_point")
                             if self._has_physical_fibre else
                             ("reference_linear", "experimental_elastic_finite_point",
                              "experimental_generalized_plastic_finite_point") +
                             (("experimental_q4_s3_j2_finite_point",)
                              if shell_plastic and self._definition.shell.s3_elements
                              else ("experimental_q4_j2_finite_point",)
                              if shell_plastic
                              else ())),
                "excluded": excluded}
        if self._definition.footprints:
            capabilities["attachment"] = (
                (("reference point pose",) if self._definition.points else ())+
                ("experimental selected-node rigid footprint (six-channel pose)",)+
                tuple(v for v in attachment if "line" in v))
            capabilities["excluded"] = tuple(v for v in excluded if v != "footprint")+(
                "plastic footprint", "physical-fibre footprint", "distributing footprint",
                "continuous-area footprint", "qualified footprint", "off-node beam footprint station")
            capabilities["analysis"] = (
                ("reference_linear", "experimental_elastic_finite_nodal_footprint")
                if not self._line_samples or self._finite_bl5 else ("reference_linear",))
            capabilities["footprint_retained_scale_policy"] = retained_scale_policy_descriptor()
            capabilities["footprint_chart_admission_policy"] = chart_admission_policy_descriptor(self._definition.footprint_chart_policy)
            capabilities["excluded"] += (("nodal-footprint finite charts with partial rotational supports",)
                if self._footprint_increment_chart else ("nodal-footprint chart rebase and rebased checkpoint restore",))
        if self._footprint_stable_s3:
            capabilities["footprint_finite_numerical_policy"] = stable_s3_policy_descriptor()
        if self._bl5_shell_material:
            capabilities["displacement_control"] = "experimental_nodal_translation_seeded_v1"
            capabilities["selected_finite_recovery"] = "experimental_cached_nodes_material_v1"
        return capabilities

    def preflight(self):
        self._require_open()
        details = {"identity": self._identity, "physical_dofs": self._shell_count+
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
                "unsupported_modes": self._unsupported_modes,
                "production_qualified": False}
        if self._definition.footprints:
            details["nodal_rigid_footprints"] = tuple(
                dict(group.descriptor(), point_indices=indices)
                for group, indices in self._footprint_bindings)
            details["footprint_retained_scale_policy"] = retained_scale_policy_descriptor()
            details["footprint_chart_admission_policy"] = chart_admission_policy_descriptor(self._definition.footprint_chart_policy)
        if self._footprint_stable_s3:
            details["footprint_finite_numerical_policy"] = stable_s3_policy_descriptor()
        if self._modal_only:
            details["modal_boundary_policy"] = self._definition.modal_boundary_policy
        return details

    @property
    def reference_modal_capabilities(self):
        """Explicit experimental descriptor route; legacy capability schema stays fixed."""
        from ._stiffened_shell_ge_reference_modal import capabilities
        with self._operation_lock:
            return capabilities(self)

    @_state_writer
    def modes(self, request, *, cancellation_token=None):
        """Supported virgin Q4/native-GE point modes with explicit physical mass."""
        from ._stiffened_shell_ge_reference_modal import solve
        return solve(self, request, cancellation_token=cancellation_token)

    @_state_writer
    def solve_linear(self, actions: tuple[NodalAction, ...], *,
                     cancellation_token=None) -> LinearResult:
        self._require_open()
        self._require_stateful_scope()
        if self._finite_driver is not None:
            raise RuntimeError("finite and reference-linear states cannot be mixed")
        if self._unsupported_modes:
            raise ValueError(self._unsupported_modes[0])
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.start")
        from ._stiffened_shell_ge_body_load import GEBodyLoad
        from ._stiffened_shell_ge_distributed_load import GEBeamDistributedLoad
        from ._stiffened_shell_ge_distributed_programme import GEBeamDistributedProgramme
        if type(actions) is GEBeamDistributedProgramme:
            raise ValueError('distributed programmes require the finite solve operation')
        from ._stiffened_shell_ge_pressure_load import GEShellPressureLoad
        body = None
        if type(actions) in (GEBodyLoad, GEBeamDistributedLoad, GEShellPressureLoad):
            cached = getattr(self, "_external_context", None)
            body = (cached if cached is not None and cached.request.identity == actions.identity
                    else actions.compile(self))
        load = (np.array(body.reference_gradient, copy=True) if body is not None else
                np.zeros(self._K.shape[0]))
        for action in (() if body is not None else actions):
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
        from ._b2_physical_linear_batch_dev import (
            B2NumericalSolveFailure, _accurate_sparse_residual,
        )

        def refine(value):
            if not np.isfinite(value).all():
                raise RuntimeError("finite mixed linear solution required")
            try:
                defect = _accurate_sparse_residual(
                    self._A, value[:, None], rhs[:, None])[:, 0]
            except B2NumericalSolveFailure as exc:
                raise RuntimeError(
                    "mixed reference linear residual is not representable") from exc
            correction = self._linear_factor.solve(-defect)
            self._linear_refinements += 1
            cancellation_safe_point(cancellation_token,
                                    "stiffened-shell.linear.refined")
            return value+correction

        # A rounded sparse residual can pass the physical gates while losing
        # retained forces or multipliers. One accurate correction uses this
        # owner's unchanged matrix and cached factor, not a comparison oracle.
        solution = refine(solution)
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
                solution = refine(solution)
        if not np.isfinite(relative) or relative > 1e-8 or constraint > 1e-9:
            raise RuntimeError("mixed reference linear equilibrium failed")
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.commit")
        support = np.zeros_like(equilibrium)
        support[self._fixed] = equilibrium[self._fixed]
        point_wrenches = reference_point_records(self, q, multipliers)
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.publish")
        with self._commit_lock:
            self._generation += 1
            result = LinearResult("completed", _owned(q[:self._shell_count]),
                                  _owned(q[self._shell_count:]),
                                  _owned(multipliers), _owned(support),
                                  relative, constraint, self._generation,
                                  point_wrenches=point_wrenches,
                                  **({} if body is None else {body.result_field: body.reference_recovery}))
            self._external_context = body
            self._accepted = (result, _owned(load))
        return result

    @_state_writer
    def solve(self, actions: tuple[NodalAction, ...],
              targets: tuple[float, ...] = (1.,), *, cancellation_token=None,
              max_iterations: int = 12, max_backtracks: int = 8,
              increment_control=None, on_accepted=None, displacement_control=None):
        """Advance finite trials; optionally observe each committed increment.

        ``on_accepted(result)`` receives a detached result after state and
        controller publication. Recovery/checkpoint reads are allowed; reentrant
        mutation is rejected. Observer errors propagate with the accepted prefix
        intact. The observer is ephemeral and is not stored in checkpoints.
        """
        self._require_open()
        self._require_stateful_scope()
        if on_accepted is not None and not callable(on_accepted):
            raise TypeError("on_accepted must be callable or None")
        if displacement_control is not None:
            if self._unsupported_modes:
                raise ValueError(self._unsupported_modes[0])
            if increment_control is not None:
                from ._stiffened_shell_displacement_adaptive import solve as adaptive_solve
                return adaptive_solve(self,actions,targets,displacement_control,increment_control,
                    max_iterations=max_iterations,max_backtracks=max_backtracks,
                    cancellation_token=cancellation_token,on_accepted=on_accepted)
            from ._stiffened_shell_displacement_control import solve
            return solve(self,actions,targets,displacement_control,
                max_iterations=max_iterations,max_backtracks=max_backtracks,
                cancellation_token=cancellation_token,on_accepted=on_accepted)
        if getattr(self,"_displacement_snapshot",None) is not None or getattr(self,"_displacement_adaptive",None) is not None:
            raise ValueError("displacement history requires explicit displacement control")
        if self._unsupported_modes:
            raise ValueError(self._unsupported_modes[0])
        if self._line_samples and not self._finite_bl5:
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
                max_iterations=max_iterations, max_backtracks=max_backtracks,
                increment_control=increment_control, on_accepted=on_accepted)
        finally:
            if self._finite_driver is None and driver._accepted is not None:
                self._finite_driver = driver

    @_accepted_snapshot
    def recover(self, *, selection=None):
        self._require_open()
        if self._finite_driver is not None:
            result = self._finite_driver.recover()
        else:
            if self._accepted is None:
                raise RuntimeError("no accepted mixed linear result")
            result = self._accepted[0]
        from ._stiffened_shell_selected_recovery import GERecoverySelection, recover
        if type(selection) is GERecoverySelection:
            return recover(self, result, selection)
        return result if selection is None else selected_wrenches(self, result, selection)

    @_state_writer
    def rebase_rotations(self, expected_generation: int, *, cancellation_token=None):
        """Issue an experimental physical shell-anchor reset at the same load."""
        self._require_open()
        if getattr(self,"_displacement_snapshot",None) is not None or getattr(self,"_displacement_adaptive",None) is not None:
            from ._stiffened_shell_displacement_control import rebase
            return rebase(self,expected_generation,cancellation_token=cancellation_token)
        self._require_stateful_scope()
        if self._definition.footprints and not self._footprint_increment_chart:
            raise ValueError("experimental nodal footprint chart rebase is unsupported: continuation parity not established")
        if self._finite_driver is None:
            raise RuntimeError("shell rebase requires an accepted finite point state")
        return self._finite_driver.rebase_rotations(
            expected_generation, cancellation_token=cancellation_token)

    @_accepted_snapshot
    def checkpoint(self) -> bytes:
        self._require_open()
        if getattr(self,"_displacement_adaptive",None) is not None:
            return self._displacement_adaptive[1]
        if getattr(self,"_displacement_snapshot",None) is not None:
            return self._displacement_snapshot[0]
        if self._finite_driver is not None:
            return self._finite_driver.checkpoint()
        if self._accepted is None:
            raise RuntimeError("no accepted mixed linear result")
        body = getattr(self, "_external_context", None)
        if body is not None:
            prepared = copy(self)
            prepared._external_context = None
            prepared._identity = body.augmented_model_identity
            return body.checkpoint(prepared.checkpoint())
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

    @_state_writer
    @_accepted_snapshot
    def restore(self, raw: bytes) -> LinearResult:
        self._require_open()
        self._require_stateful_scope()
        if self._unsupported_modes:
            raise ValueError(self._unsupported_modes[0])
        if self._finite_driver is not None:
            raise RuntimeError("restore requires a fresh experimental GE analysis")
        if self._accepted is not None:
            raise RuntimeError("restore requires a fresh experimental GE analysis")
        if type(raw) is not bytes:
            raise ValueError("bounded mixed linear checkpoint required")
        from ._stiffened_shell_displacement_adaptive import MAGIC as DISPLACEMENT_ADAPTIVE_MAGIC, EVENT_MAGIC
        if raw.startswith((DISPLACEMENT_ADAPTIVE_MAGIC,EVENT_MAGIC)):
            from ._stiffened_shell_displacement_adaptive import decode,validate_progress
            context,inner=decode(self,raw)
            prepared=copy(self);prepared._commit_lock=RLock();prepared._writing=False
            prepared._displacement_adaptive=None
            result=prepared.restore(inner)
            validate_progress(prepared,context)
            if getattr(prepared,"_displacement_snapshot",None) is not None:
                result=replace(result,status="completed" if context.state.completed else "accepted_prefix",
                               increment_attempts=context.state.attempts)
                prepared._finite_driver._accepted=result
            with self._commit_lock:
                self._finite_driver=prepared._finite_driver
                self._finite_driver.owner=self
                self._generation=prepared._generation
                self._displacement_snapshot=getattr(prepared,"_displacement_snapshot",None)
                self._displacement_adaptive=(context,raw)
            return result
        from ._stiffened_shell_displacement_checkpoint import MAGIC as DISPLACEMENT_MAGIC
        if raw.startswith(DISPLACEMENT_MAGIC):
            from ._stiffened_shell_displacement_control import publish
            return publish(self,raw,expected_driver=None,expected_generation=self._generation)
        from ._stiffened_shell_ge_body_load import MAGIC as BODY_MAGIC
        from ._stiffened_shell_ge_distributed_load import MAGIC as DISTRIBUTED_MAGIC
        from ._stiffened_shell_ge_pressure_load import MAGIC as PRESSURE_MAGIC
        from ._stiffened_shell_ge_distributed_programme import MAGIC as DISTRIBUTED_PROGRAMME_MAGIC
        if raw.startswith((BODY_MAGIC, DISTRIBUTED_MAGIC, PRESSURE_MAGIC, DISTRIBUTED_PROGRAMME_MAGIC)):
            if getattr(self, "_external_context", None) is not None or getattr(self, "_staged_context", None) is not None:
                raise ValueError("nested external-load checkpoint is unsupported")
            if raw.startswith(BODY_MAGIC):
                from ._stiffened_shell_ge_body_load import decode_checkpoint
            elif raw.startswith(DISTRIBUTED_MAGIC):
                from ._stiffened_shell_ge_distributed_load import decode_checkpoint
            elif raw.startswith(DISTRIBUTED_PROGRAMME_MAGIC):
                from ._stiffened_shell_ge_distributed_programme import decode_checkpoint
            else:
                from ._stiffened_shell_ge_pressure_load import decode_checkpoint
            request, inner = decode_checkpoint(raw)
            compiled = request.compile(self)
            prepared = copy(self)
            prepared._identity = compiled.augmented_model_identity
            prepared._external_context = compiled
            prepared._commit_lock = RLock()
            prepared._writing = False
            result = prepared.restore(inner)
            driver = prepared._finite_driver
            if driver is None:
                if hasattr(compiled, 'evaluate_at'):
                    raise ValueError('distributed programme requires a finite checkpoint')
                if not np.array_equal(prepared._accepted[1], compiled.reference_gradient):
                    raise ValueError("checkpoint load disagrees with its declared external request")
                result = replace(result, **{compiled.result_field: compiled.reference_recovery})
                prepared._accepted = (result, prepared._accepted[1])
            elif hasattr(compiled, 'evaluate_at') and driver._adaptive_state is not None and not driver._adaptive_state.completed:
                controller = driver._adaptive_state
                compiled.validate_targets(driver._load_factor, controller.targets[controller.cursor:])
            checkpoint = prepared.checkpoint()
            if driver is not None:
                driver.owner = self
                driver._adaptive_checkpoint = checkpoint
            with self._commit_lock:
                self._external_context = compiled
                self._finite_driver = driver
                self._accepted = prepared._accepted
                self._generation = result.generation
            return result
        from ._stiffened_shell_staged_load_experimental import (
            MAGIC as STAGED_MAGIC, decode_checkpoint,
        )
        if raw.startswith(STAGED_MAGIC):
            if ((self._line_samples and not (self._finite_bl5 and
                    self._definition.q4_pullback_policy == Q4_ALGORITHMIC_PULLBACK_V1)) or
                    getattr(self, "_staged_context", None) is not None or
                    getattr(self, "_external_context", None) is not None):
                raise ValueError("staged checkpoint requires a fresh point or admitted elastic BL5 owner")
            from ._stiffened_shell_ge_finite_experimental import FinitePointDriver
            programme, position, inner = decode_checkpoint(raw)
            compiled = programme.compile(self, FinitePointDriver(self)._load)
            # Validate in a private view; neither model identity nor accepted
            # state on the live owner changes before every check passes.
            prepared = copy(self)
            prepared._identity = compiled.augmented_model_identity
            prepared._staged_context = compiled
            prepared._commit_lock = RLock()
            prepared._writing = False
            result = prepared.restore(inner)
            driver = prepared._finite_driver
            if driver is None or result.load_position != position:
                raise ValueError("staged checkpoint progress disagrees with accepted state")
            if driver._adaptive_state is not None and not driver._adaptive_state.completed:
                controller = driver._adaptive_state
                compiled.validate_targets(driver._load_factor,
                                          controller.targets[controller.cursor:])
            # Prepare the durable representation before the single publish.
            checkpoint = driver.checkpoint()
            driver.owner = self
            with self._commit_lock:
                self._finite_driver = driver
                self._generation = result.generation
                driver._adaptive_checkpoint = checkpoint
            return result
        load_key = ("applied_dead_load" if getattr(self, "_staged_context", None)
                    is not None else "pattern")
        adaptive = None
        if raw.startswith(INCREMENT_CONTROL_MAGIC):
            adaptive, raw = decode_control(raw, self._identity)
        chart = None
        if self._has_physical_fibre and raw.startswith(S3_BINARY_CHECKPOINT_MAGIC):
            raise ValueError("physical-fibre mixed owner admits reference-linear checkpoints only")
        if raw.startswith(CHART_CHECKPOINT_MAGIC):
            if self._definition.footprints:
                if not self._footprint_increment_chart:
                    raise ValueError("experimental nodal footprint chart checkpoint restore is unsupported: continuation parity not established")
                require_rotation_triples(self._fixed, len(self._shell_ids))
            if self._line_samples and not self._finite_bl5:
                raise ValueError("owned shell charts require a supported finite model")
            event_generation, anchors, witness, raw = _decode_chart_checkpoint(
                raw, self._identity, len(self._shell_ids))
            chart = (event_generation, anchors, witness)
        if raw.startswith(BINARY_CHECKPOINT_MAGIC):
            def expected_shapes(kind, generation):
                if ("_chart" in kind) != (chart is not None):
                    raise ValueError("numeric shell chart snapshot requires matching outer policy")
                kind = kind.replace("_chart", "")
                stable_kind = kind == "finite_native_material_stable"
                body_stable = bool(getattr(self, "_external_context", None) is not None and
                    self._definition.shell.s3_elements and self._definition.shell.j2_curve is None)
                if body_stable and kind not in ("linear", "finite_native_material_stable"):
                    raise ValueError("body S3 checkpoint requires its stable numerical policy")
                if self._footprint_stable_s3 and kind not in ("linear", "finite_native_material_stable"):
                    raise ValueError("nodal footprint S3 checkpoint requires its stable numerical policy")
                if (kind == "finite_bl5_coupled") != self._bl5_shell_material and kind != "linear":
                    raise ValueError("matching coupled BL5 material checkpoint required")
                if kind == "finite_bl5_material" and not self._bl5_material:
                    raise ValueError("BL5 material checkpoint requires selected material policy")
                if kind == "finite_bl5" and self._bl5_material:
                    raise ValueError("BL5 material checkpoint must retain histories")
                if kind == "finite_bl5" and not self._finite_bl5:
                    raise ValueError("finite BL5 checkpoint requires elastic BL5 line model")
                if self._line_samples and kind not in ("linear", "finite_bl5", "finite_bl5_material", "finite_bl5_coupled"):
                    raise ValueError("experimental weak line requires its finite BL5 checkpoint identity"
                                     if self._finite_bl5 else
                                     "experimental weak line admits reference-linear checkpoints only")
                if kind == "finite_native_material_stable":
                    if not self._definition.shell.s3_elements:
                        raise ValueError("stable S3 native checkpoint requires S3 elements")
                    kind = "finite_native_material"
                if kind not in ("linear", "finite_native_material") and self._has_physical_fibre:
                    raise ValueError("physical-fibre mixed owner admits reference-linear checkpoints only")
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
                        (load_key, (count,)),
                        ("accepted_factors", (generation,)))
                if kind == "finite_native_material":
                    if ((not self._has_physical_fibre and not
                         ((self._footprint_stable_s3 or body_stable) and stable_kind)) or
                            self._definition.shell.j2_curve is not None):
                        raise ValueError("native material checkpoint requires elastic-shell fibre model")
                    from ._stiffened_shell_beam_history import shapes
                    return base + shapes(self._beam_parts, "origin") + shapes(self._beam_parts, "accepted")
                if kind in ("finite_material", "finite_shell_material", "finite_bl5_material", "finite_bl5_coupled"):
                    stations = sum(len(part[0].operator.cell.stations)
                                   for part in self._beam_parts)
                    material = base + (("beam_plastic", (stations, 6, 2)),
                                       ("beam_accumulated", (stations, 2)))
                    if kind in ("finite_bl5_material", "finite_bl5_coupled"):
                        material += (("beam_origin_plastic", (stations, 6, 2)),
                                     ("beam_origin_accumulated", (stations, 2)))
                    if kind == "finite_bl5_coupled":
                        shells = len(self._shell_parts)
                        material += (("shell_plastic", (shells, 12, 3)),
                                     ("shell_alpha", (shells, 12)),
                                     ("shell_origin_plastic", (shells, 12, 3)),
                                     ("shell_origin_alpha", (shells, 12)))
                    if kind == "finite_shell_material":
                        if self._definition.shell.j2_curve is None:
                            raise ValueError("shell J2 checkpoint requires matching material")
                        material += (("shell_plastic", (len(self._shell_parts), 12, 3)),
                                     ("shell_alpha", (len(self._shell_parts), 12)))
                    return material
                return base

            kind, generation, arrays = _decode_binary_checkpoint(
                raw, self._identity, expected_shapes)
            kind = kind.replace("_chart", "")
            schema = (CHECKPOINT if kind == "linear" else
                      _BINARY_SCHEMAS[kind] if kind in ("finite_bl5", "finite_bl5_material", "finite_bl5_coupled") else
                      STABLE_NATIVE_SCHEMA if kind == "finite_native_material_stable" else
                      "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_MATERIAL_V7"
                      if kind == "finite_native_material" else
                      FINITE_MATERIAL_CHECKPOINT if kind == "finite_material" else
                      FINITE_SHELL_MATERIAL_CHECKPOINT if kind == "finite_shell_material"
                      else FINITE_CHECKPOINT)
            value = {"schema": schema, "model": self._identity,
                     "generation": generation, **arrays}
            if kind in ("finite", "finite_bl5", "finite_bl5_material", "finite_bl5_coupled", "finite_material", "finite_shell_material", "finite_native_material", "finite_native_material_stable"):
                value["accepted_factors"] = arrays["accepted_factors"].tolist()
        elif raw.startswith(NATIVE_SHELL_MAGIC):
            if (self._line_samples or not self._has_physical_fibre or
                    self._definition.shell.j2_curve is None):
                raise ValueError("native shell J2 checkpoint requires matching fibre point model")
            from ._stiffened_shell_ge_finite_experimental import native_shell_checkpoint_shapes
            generation, arrays, states = _decode_s3_binary_checkpoint(
                raw, self._identity, lambda generation: native_shell_checkpoint_shapes(self, generation),
                2*len(self._definition.shell.s3_elements), anchored=chart is not None,
                native_material=True)
            value = {"schema": NATIVE_SHELL_SCHEMA, "model": self._identity,
                     "generation": generation, **arrays, "s3_states": states,
                     "accepted_factors": arrays["accepted_factors"].tolist()}
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
                        (load_key, (count,)),
                        ("accepted_factors", (generation,)),
                        ("beam_plastic", (stations, 6, 2)),
                        ("beam_accumulated", (stations, 2)),
                        ("shell_plastic", (q4_count, 12, 3)),
                        ("shell_alpha", (q4_count, 12)))

            generation, arrays, states = _decode_s3_binary_checkpoint(
                raw, self._identity, expected_s3_shapes,
                len(self._definition.shell.s3_elements), anchored=chart is not None)
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
            if (type(value) is dict and value.get("schema") in (
                    "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_MATERIAL_V7", NATIVE_SHELL_SCHEMA, STABLE_NATIVE_SCHEMA)):
                raise ValueError("native material checkpoint requires binary framing")
            if (type(value) is dict and value.get("schema") in (
                    _BINARY_SCHEMAS["finite_bl5"], _BINARY_SCHEMAS["finite_chart_bl5"],
                    _BINARY_SCHEMAS["finite_bl5_material"], _BINARY_SCHEMAS["finite_chart_bl5_material"],
                    _BINARY_SCHEMAS["finite_bl5_coupled"], _BINARY_SCHEMAS["finite_chart_bl5_coupled"])):
                raise ValueError("finite BL5 checkpoint requires binary framing")
        if (type(value) is dict and value.get("schema") in
                (FINITE_CHECKPOINT, FINITE_MATERIAL_CHECKPOINT,
                 _BINARY_SCHEMAS["finite_bl5"], _BINARY_SCHEMAS["finite_bl5_material"], _BINARY_SCHEMAS["finite_bl5_coupled"],
                 FINITE_SHELL_MATERIAL_CHECKPOINT,
                 FINITE_S3_MATERIAL_CHECKPOINT,
                  NATIVE_SHELL_SCHEMA,
                  STABLE_NATIVE_SCHEMA,
                 "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_MATERIAL_V7")):
            if self._has_physical_fibre and value["schema"] not in (
                    NATIVE_SHELL_SCHEMA, STABLE_NATIVE_SCHEMA, "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_MATERIAL_V7"):
                raise ValueError("physical-fibre mixed owner admits reference-linear checkpoints only")
            if (bool(self._finite_bl5) != (value["schema"] in (
                    _BINARY_SCHEMAS["finite_bl5"], _BINARY_SCHEMAS["finite_bl5_material"], _BINARY_SCHEMAS["finite_bl5_coupled"])) or
                    self._bl5_material != (value["schema"] in (_BINARY_SCHEMAS["finite_bl5_material"], _BINARY_SCHEMAS["finite_bl5_coupled"])) or
                    self._bl5_shell_material != (value["schema"] == _BINARY_SCHEMAS["finite_bl5_coupled"])):
                raise ValueError("finite checkpoint requires matching BL5 mechanics identity")
            if self._line_samples and not self._finite_bl5:
                raise ValueError(
                    "experimental weak line admits reference-linear checkpoints only")
            from ._stiffened_shell_ge_finite_experimental import FinitePointDriver
            if adaptive is not None:
                validate_control(adaptive, value["accepted_factors"])
            driver = FinitePointDriver(self)
            result = (driver.restore(value, adaptive_state=adaptive) if chart is None else
                      driver.restore(value, rotation_anchors=chart[1],
                                     pose_witness=chart[2], accepted_generation=chart[0],
                                     adaptive_state=adaptive))
            self._finite_driver = driver
            return result
        if adaptive is not None:
            raise ValueError("adaptive checkpoint requires a finite point state")
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
                              value["generation"],
                              point_wrenches=reference_point_records(self, q, lam))
        self._accepted = (result, load)
        self._generation = value["generation"]
        return result

    @_state_writer
    @_accepted_snapshot
    def close(self):
        self._accepted = None
        self._finite_driver = None
        self._linear_factor = None
        self._external_context = None
        self._displacement_snapshot = None
        self._displacement_adaptive = None
        self._closed = True
