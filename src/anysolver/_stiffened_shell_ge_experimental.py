"""Experimental sparse reference-linear GE/Q4 point-connected panel.

This is an integration slice, not an accepted G0/G1 formulation.  It retains
all native B3 cell variables and uses the existing objective point operator.
Line coupling, material updates and finite-step equilibrium are separate work.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import warnings

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla

from ._ge_beam3_native_definition import NativeBeamDefinition
from ._ge_beam3_pose_joint import RigidPoseJoint
from ._ge_beam3_generalized_static_boundary import spatial_jacobian
from .corotational import corotational_element_response
from .elements import create_shell_element
from .fe_core import FEModel
from .control import cancellation_safe_point


PROFILE = "B3_GE_E4_PL_STIFFENED_SHELL_V1"
CHECKPOINT = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_LINEAR_V1"


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


@dataclass(frozen=True)
class LinearResult:
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
    index = {node: i for i, node in enumerate(ids)}
    model = FEModel("experimental-stiffened-shell-q4")
    model.add_material("shell", panel.young_pa, panel.poisson,
                       density=panel.density_kg_m3)
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
            raise ValueError("experimental GE point slice admits elastic generalized B3")
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


def _assemble_shell(model, pieces, count):
    rows, columns, data = [], [], []
    residual = np.zeros(count)
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
        np.add.at(residual, slots, force)
        rows.extend(np.repeat(slots, len(slots)))
        columns.extend(np.tile(slots, len(slots)))
        data.extend(np.asarray(tangent).ravel())
    return residual, sparse.coo_matrix((data, (rows, columns)),
                                       shape=(count, count)).tocsr()


def _assemble_beam(pieces, nodes, index, count):
    rows, columns, data = [], [], []
    residual = np.zeros(count)
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
        np.add.at(residual, slots, response.residual)
        rows.extend(np.repeat(slots, 42))
        columns.extend(np.tile(slots, 42))
        data.extend(local.ravel())
    return residual, sparse.coo_matrix((data, (rows, columns)),
                                       shape=(count, count)).tocsr()


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
        beam_ids, beam_index, beam_nodes, beam_parts, beam_count = _beam_reference(
            definition.beams)
        shell_count = 6*len(shell_ids)
        shell_r, shell_k = _assemble_shell(shell_model, shell_parts, shell_count)
        beam_r, beam_k = _assemble_beam(beam_parts, beam_nodes, beam_index,
                                       beam_count)
        if max(np.linalg.norm(shell_r), np.linalg.norm(beam_r)) > 1e-5:
            raise ValueError("reference state must be stress free")
        self._K = sparse.block_diag((shell_k, beam_k), format="csr")
        self._shell_count = shell_count
        self._beam_count = beam_count
        self._shell_ids = shell_ids
        self._beam_ids = beam_ids
        self._shell_index = shell_index
        self._beam_index = beam_index
        self._beam_nodes = beam_nodes
        self._shell_xyz = shell_xyz
        self._definition = definition
        self._identity = sha256(json.dumps({
            "profile": PROFILE, "shell_ids": shell_ids,
            "shell_xyz": shell_xyz.tolist(), "shell_cells": panel.q4_elements,
            "shell_s3_cells": panel.s3_elements,
            "thickness": panel.thickness_m, "E": panel.young_pa,
            "nu": panel.poisson, "density": panel.density_kg_m3,
            "beams": [item.sha256 for item in definition.beams],
            "points": [(v.shell_node, v.beam_node) for v in definition.points],
            "fixed": [(v.domain, v.node, v.component) for v in definition.fixed],
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self._connections = []
        constraint_rows = []
        if not definition.points:
            raise ValueError("at least one explicit native point connection required")
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
            self._connections.append(joint)
        c_row, c_col, c_data = [], [], []
        for i, (slots, jacobian) in enumerate(constraint_rows):
            c_row.extend(np.repeat(np.arange(6*i, 6*i+6), 12))
            c_col.extend(np.tile(slots, 6))
            c_data.extend(jacobian.ravel())
        count = self._K.shape[0]
        self._C = sparse.coo_matrix((c_data, (c_row, c_col)),
                                    shape=(6*len(constraint_rows), count)).tocsr()
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
        self._A = sparse.bmat([
            [self._K[self._free, :][:, self._free], self._C[:, self._free].T],
            [self._C[:, self._free], None]], format="csc")
        if self._A.shape[0] < 1 or self._A.nnz == 0:
            raise ValueError("nonempty constrained mixed operator required")
        self._accepted = None
        self._generation = 0
        self._closed = False

    def _require_open(self):
        if self._closed:
            raise RuntimeError("experimental GE analysis is closed")

    @property
    def capabilities(self):
        return {"profile": PROFILE, "status": "EXPERIMENTAL_NOT_QUALIFIED",
                "shell": "elastic flat Q4/S3", "beam": "generalized B3 retained",
                "attachment": "reference point pose",
                "analysis": ("reference_linear",),
                "excluded": ("nonlinear", "line", "footprint", "modes", "buckling")}

    def preflight(self):
        self._require_open()
        return {"identity": self._identity, "physical_dofs": self._shell_count+
                6*len(self._beam_ids), "retained_dofs": self._beam_count-
                6*len(self._beam_ids), "constraints": self._C.shape[0],
                "matrix_nnz": self._A.nnz, "production_qualified": False}

    def solve_linear(self, actions: tuple[NodalAction, ...], *,
                     cancellation_token=None) -> LinearResult:
        self._require_open()
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
        with warnings.catch_warnings():
            warnings.simplefilter("error", spla.MatrixRankWarning)
            solution = spla.spsolve(self._A, rhs)
        cancellation_safe_point(cancellation_token, "stiffened-shell.linear.solved")
        if not np.isfinite(solution).all():
            raise RuntimeError("finite mixed linear solution required")
        q = np.zeros(self._K.shape[0])
        q[self._free] = solution[:len(self._free)]
        multipliers = solution[len(self._free):]
        equilibrium = self._K@q + self._C.T@multipliers-load
        gap = self._C@q
        relative = float(np.linalg.norm(equilibrium[self._free]) /
                         max(1., np.linalg.norm(load[self._free])))
        constraint = float(np.max(np.abs(gap)))
        if relative > 1e-8 or constraint > 1e-9:
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

    def recover(self) -> LinearResult:
        self._require_open()
        if self._accepted is None:
            raise RuntimeError("no accepted mixed linear result")
        return self._accepted[0]

    def checkpoint(self) -> bytes:
        self._require_open()
        if self._accepted is None:
            raise RuntimeError("no accepted mixed linear result")
        result, load = self._accepted
        payload = {"schema": CHECKPOINT, "model": self._identity,
                   "generation": self._generation,
                   "q": np.r_[result.shell_displacement,
                              result.beam_coordinates].tolist(),
                   "multipliers": result.multipliers.tolist(),
                   "load": load.tolist()}
        return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("ascii")

    def restore(self, raw: bytes) -> LinearResult:
        self._require_open()
        if self._accepted is not None:
            raise RuntimeError("restore requires a fresh experimental GE analysis")
        if type(raw) is not bytes or len(raw) > 2_000_000:
            raise ValueError("bounded mixed linear checkpoint required")
        try:
            value = json.loads(raw.decode("ascii"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid mixed linear checkpoint") from exc
        if (type(value) is not dict or set(value) !=
                {"schema", "model", "generation", "q", "multipliers", "load"} or
                value["schema"] != CHECKPOINT or value["model"] != self._identity or
                type(value["generation"]) is not int or value["generation"] < 1):
            raise ValueError("incompatible mixed linear checkpoint")
        q = _owned(value["q"], (self._K.shape[0],))
        lam = _owned(value["multipliers"], (self._C.shape[0],))
        load = _owned(value["load"], (self._K.shape[0],))
        equilibrium = self._K@q+self._C.T@lam-load
        relative = float(np.linalg.norm(equilibrium[self._free]) /
                         max(1., np.linalg.norm(load[self._free])))
        constraint = float(np.max(np.abs(self._C@q)))
        if (relative > 1e-8 or constraint > 1e-9 or
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
        self._closed = True
