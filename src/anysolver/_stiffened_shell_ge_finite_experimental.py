"""Bounded finite-step trial driver for the experimental GE point panel.

All shell, beam and joint evaluations use one accepted predecessor per load
increment. Q4 shell J2 and generalized B3 yielding are experimental.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from copy import copy, deepcopy
from decimal import localcontext
import json
from math import fsum
import warnings
from types import SimpleNamespace

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla
from scipy.spatial.transform import Rotation

from ._ge_beam3_generalized_static_boundary import spatial_jacobian
from ._ge_beam3_pose_joint import _exp_terms
from ._stiffened_shell_point_recovery import PointTransferWrench, point_record
from ._stiffened_shell_nodal_footprint import require_rotation_triples
from ._ge_beam3_p5.algebra import skew
from ._ge_beam3_retained_generalized_state import Mechanical
from ._stiffened_shell_bl5_local_experimental import BL5TrialDomainError
from ._stiffened_shell_l1_local_experimental import _owned_slots
from ._ge_beam3_generalized_cell import GeneralizedCellHistory
from ._ge_beam3_generalized_ellipsoid_section import GeneralizedHistory
from ._ge_beam3_fibre_section import PhysicalFibreSection
from ._stiffened_shell_beam_history import (
    arrays as native_history_arrays, histories as native_histories,
    shapes as native_history_shapes, observables as native_observables,
)
from ._ge_beam3_p5.algebra import rotation
from ._ge_beam3_p5.compensated_coordinates import split_sum
from ._ge_beam3_variational_shell import response as variational_shell_response
from ._stiffened_shell_s3_algorithmic_pullback import (
    response as s3_algorithmic_response, local_coordinates as s3_local_coordinates,
)
from .control import cancellation_safe_point
from .corotational import corotational_element_response
from ._stiffened_shell_ge_experimental import (
    FINITE_CHECKPOINT, FINITE_MATERIAL_CHECKPOINT,
    FINITE_SHELL_MATERIAL_CHECKPOINT, FINITE_S3_MATERIAL_CHECKPOINT,
    NodalAction, _owned,
    _linear_equilibrium, _scaled_constraint_gap,
)
from ._stiffened_shell_ge_checkpoint_binary import encode as _encode_binary_checkpoint
from ._stiffened_shell_ge_checkpoint_binary import SCHEMAS as _BINARY_SCHEMAS
from ._stiffened_shell_ge_checkpoint_binary import encode_s3 as _encode_s3_checkpoint
from ._stiffened_shell_ge_checkpoint_binary import encode_chart as _encode_chart_checkpoint
from ._stiffened_shell_ge_checkpoint_binary import NATIVE_SHELL_SCHEMA
from ._stiffened_shell_ge_checkpoint_binary import STABLE_NATIVE_SCHEMA
from ._stiffened_shell_increment_control import (
    AdaptiveIncrementControl, IncrementAttempt, FiniteIncrementFailure,
    AdaptiveIncrementExhausted, _AdaptiveState, encode_control,
)
from ._stiffened_shell_rotation_charts import owned_anchors, physical_frames, total_coordinates
from ._stiffened_shell_q4_algorithmic_pullback import (
    POLICY as Q4_ALGORITHMIC_PULLBACK_POLICY, response as q4_algorithmic_response,
)


MAX_JSON_CHECKPOINT_BYTES = 2_000_000
MAX_JSON_CHECKPOINT_VALUES = 50_000
NATIVE_MATERIAL_CHECKPOINT = _BINARY_SCHEMAS["finite_native_material"]


def _require_elastic_footprint_histories(histories, context):
    for history in histories:
        for station in history.stations:
            if (station.accumulated != (0., 0.) or
                    any(value != 0. for pair in station.plastic for value in pair)):
                raise ValueError("experimental nodal rigid footprints admit elastic beam response only: "+context)


def native_shell_checkpoint_shapes(owner, generation):
    """Layout from the compiled model; no dimensions are trusted from a file."""
    count = owner._K.shape[0]
    members = len(owner._beam_parts)
    q4_count = len(owner._definition.shell.q4_elements)
    return (("q", (count,)), ("frames", (len(owner._beam_ids), 3, 3)),
            ("cells", (members, 2, 3, 3)), ("resultants", (members, 18)),
            ("multipliers", (owner._C.shape[0],)),
            ("applied_dead_load" if getattr(owner, "_staged_context", None) is not None else "pattern", (count,)),
            ("accepted_factors", (generation,))) + (
        native_history_shapes(owner._beam_parts, "origin") +
        native_history_shapes(owner._beam_parts, "accepted")) + (
            ("shell_plastic", (q4_count, 12, 3)), ("shell_alpha", (q4_count, 12)),
            ("shell_origin_plastic", (q4_count, 12, 3)),
            ("shell_origin_alpha", (q4_count, 12)),
            ("shell_origin_q", (owner._shell_count,)),
            ("shell_origin_anchors", (len(owner._shell_ids), 3, 3)))


def _position_pair(reference, displacement):
    """Keep the rounded remainder when a physical displacement joins a reference."""
    if reference.shape != displacement.shape:
        raise ValueError("matching finite position coordinates required")
    high = np.empty_like(reference)
    low = np.empty_like(reference)
    for index in np.ndindex(reference.shape):
        high[index], low[index] = split_sum(
            (float(reference[index]), float(displacement[index])))
    return high, low


def _material_arrays(histories):
    stations = tuple(station for history in histories
                     for station in history.stations)
    return (np.asarray([station.plastic for station in stations], dtype=float),
            np.asarray([station.accumulated for station in stations], dtype=float))


def _material_histories(owner, plastic, accumulated):
    histories = []
    index = 0
    for element, _slots, _virgin in owner._beam_parts:
        cell = element.operator.cell
        stations = []
        for _ in cell.stations:
            stations.append(GeneralizedHistory(
                element.section.identity,
                tuple(tuple(map(float, pair)) for pair in plastic[index]),
                tuple(map(float, accumulated[index]))))
            index += 1
        history = GeneralizedCellHistory(cell.identity, tuple(stations))
        with localcontext() as context:
            context.prec = 80
            cell._origins(history)
        histories.append(history)
    return tuple(histories)


def _material_observables(histories):
    return native_observables(histories)


@dataclass(frozen=True)
class BeamFibreStationRecovery:
    """Native accepted station response from its last material predecessor.

    Fibre strains/stresses and plastic increments retain native high/low pairs.
    This record does not label material potential as stored energy/dissipation.
    """
    element_id: int
    cell: int
    station: int
    xi: float
    measure: float
    strain: np.ndarray
    strain_low: np.ndarray
    resultants: np.ndarray
    resultants_low: np.ndarray
    reference_frame: np.ndarray
    current_frame: np.ndarray
    fibres: tuple


@dataclass(frozen=True)
class BeamFibreEnergyRecovery:
    """Paired beam material energy (J) and dissipation of the last increment.

    Stored energy includes elastic background/fibres and recoverable hardening.
    These fields are not global total energy or cumulative dissipation.
    """
    element_id: int
    stored_energy_j: tuple[float, float]
    previous_hardening_energy_j: tuple[float, float]
    incremental_dissipation_j: tuple[float, float]
    incremental_material_potential_j: tuple[float, float]
    energy_recovery_station_updates: int


def _fibre_recovery(owner, state, predecessors, accepted_histories):
    records = []; energies = []
    for i, ((element, _, _), predecessor, accepted) in enumerate(zip(
            owner._beam_parts, predecessors, accepted_histories)):
        if type(element.section) is not PhysicalFibreSection:
            continue
        response = element.operator.recover_material(state.cells[i], state.resultants[i],
                                        origin=predecessor,
                                        check=element.operator.guard)
        rows = response.stations
        if response.history != accepted or tuple(row["history"] for row in rows) != accepted.stations:
            raise ValueError("native accepted fibre recovery history mismatch")
        energies.append(BeamFibreEnergyRecovery(element.element_id,
            response.stored_energy, response.previous_hardening_energy,
            response.incremental_dissipation, response.material_potential,
            response.energy_recovery_station_updates))
        for row in rows:
            records.append(BeamFibreStationRecovery(
                element.element_id, row["cell"], row["station"], row["xi"],
                row["measure"], *(_owned(row[name]) for name in (
                    "strain", "strain_low", "resultants", "resultants_low",
                    "reference_frame", "current_frame")), row["fibres"]))
    return tuple(records), tuple(energies)


def _shell_material_arrays(histories):
    if not histories:
        return _owned(np.empty((0, 12, 3))), _owned(np.empty((0, 12)))
    plastic = np.asarray([state["plastic_strain"] for state in histories],
                         dtype=float)
    alpha = np.asarray([state["alpha"] for state in histories], dtype=float)
    if plastic.shape != (len(histories), 12, 3) or alpha.shape != (len(histories), 12):
        raise ValueError("complete Q4 shell J2 station state required")
    return _owned(plastic), _owned(alpha)


def _shell_material_states(plastic, alpha):
    return tuple({"plastic_strain": _owned(plastic[i], (12, 3)),
                  "alpha": _owned(alpha[i], (12,))}
                 for i in range(len(plastic)))


@dataclass(frozen=True)
class ShellQ4MaterialRecovery:
    """Owned local Q4 plane-stress response, not a full shell stress tensor.

    Rows follow four native Q4 Gauss stations, each with three Lobatto layers
    from bottom to top. Strain columns are (xx, yy, engineering xy); stress
    columns are (xx, yy, tensor xy) in the element frame, in pascals.
    """

    element_id: int
    layer_strain: np.ndarray
    layer_stress: np.ndarray
    plastic_strain: np.ndarray
    alpha: np.ndarray


def _shell_q4_recovery(parts, states):
    if len(parts) != len(states):
        raise ValueError("complete Q4 shell material recovery required")
    return tuple(ShellQ4MaterialRecovery(
        int(part[0]),
        _owned(state["layer_strain"], (12, 3)),
        _owned(state["layer_stress"], (12, 3)),
        _owned(state["plastic_strain"], (12, 3)),
        _owned(state["alpha"], (12,)),
    ) for part, state in zip(parts, states))


@dataclass(frozen=True)
class ShellS3MaterialRecovery:
    """Owned local S3 plane-stress layers and generalized resultants."""

    element_id: int
    layer_strain: np.ndarray
    layer_stress: np.ndarray
    plastic_strain: np.ndarray
    alpha: np.ndarray
    station_generalized_resultant: np.ndarray


def _shell_s3_recovery(parts, states):
    if len(parts) != len(states):
        raise ValueError("complete S3 shell material recovery required")
    return tuple(ShellS3MaterialRecovery(
        int(part[0]),
        _owned(state["layer_strain"], (9, 3)),
        _owned(state["layer_stress"], (9, 3)),
        _owned(state["plastic_strain"], (9, 3)),
        _owned(state["alpha"], (9,)),
        _owned(state["station_generalized_resultant"], (3, 8)),
    ) for part, state in zip(parts, states))


def _require_s3_material_state(state, local_q, *, accepted):
    """Bind native material history to the objective local constitutive chart."""
    expected = np.asarray(local_q, dtype=float)
    constitutive = np.asarray(state["committed_constitutive_u"], dtype=float)
    kinematics = "LINEAR" if accepted else "ELEMENT_LOCAL"
    if (expected.shape != (18,) or constitutive.shape != (18,) or
            not np.array_equal(constitutive, expected) or
            state["solver_kinematics"] != kinematics):
        raise ValueError("S3 material state disagrees with mixed owner coordinates")


def _accepted_shell_material_origins(owner, trial, candidates):
    """Prepare all Q4/S3 histories before the one mixed-state publish point."""
    q4_count = len(owner._definition.shell.q4_elements)
    if len(candidates) != len(owner._shell_parts):
        raise ValueError("complete mixed shell material candidates required")
    q4_plastic, q4_alpha = _shell_material_arrays(candidates[:q4_count])
    origins = list(_shell_material_states(q4_plastic, q4_alpha))
    material = owner._shell_model.get_material("shell")
    for (eid, element, slots, _), candidate in zip(
            owner._shell_parts[q4_count:], candidates[q4_count:]):
        if len(slots) != 18:
            raise ValueError("native S3 material candidate required")
        anchors = None if trial.shell_anchors is None else trial.shell_anchors[slots[::6]//6]
        local_q = s3_local_coordinates(owner._shell_model, element, trial.q[slots],
                                      rotation_anchors=anchors)
        _require_s3_material_state(candidate, local_q, accepted=False)
        origins.append(element.seal_solver_integrated_nonlinear_state(
            owner._shell_model.mesh, material, candidate, 3,
            local_q, kinematics="LINEAR"))
    return tuple(origins)


@dataclass(frozen=True)
class FinitePointResult:
    """Experimental finite result with dimensionless work/row-scaled errors."""
    status: str
    load_factor: float
    shell_displacement: np.ndarray
    beam_positions: np.ndarray
    beam_frames: np.ndarray
    cell_frames: np.ndarray
    cell_resultants: np.ndarray
    multipliers: np.ndarray
    support_reactions: np.ndarray
    free_equilibrium_ratio: float
    constraint_max: float
    iterations: int
    generation: int
    accepted_factors: tuple[float, ...]
    beam_station_accumulated: tuple[tuple[float, ...], ...] = ()
    shell_layer_alpha: tuple[tuple[float, ...], ...] = ()
    shell_q4_material: tuple[ShellQ4MaterialRecovery, ...] = ()
    shell_s3_material: tuple[ShellS3MaterialRecovery, ...] = ()
    production_qualified: bool = False
    shell_frames: np.ndarray | None = None
    shell_rotation_anchors: np.ndarray | None = None
    shell_chart_coordinates: np.ndarray | None = None
    beam_fibre_material: tuple[BeamFibreStationRecovery, ...] = ()
    beam_fibre_energy: tuple[BeamFibreEnergyRecovery, ...] = ()
    increment_attempts: tuple[IncrementAttempt, ...] = ()
    beam_shell_line_work: tuple = ()
    point_wrenches: tuple[PointTransferWrench, ...] = ()
    load_programme_identity: str | None = None
    load_position: float | None = None
    load_stage_cursor: int | None = None
    load_stage_fraction: float | None = None
    load_programme_complete: bool | None = None
    applied_dead_load: np.ndarray | None = None
    body_load: object | None = None


@dataclass(frozen=True)
class FiniteLineStationWork:
    """Accepted physical station action, before any display smoothing.

    The integrated gradient contains two shell endpoint wrenches, two beam
    endpoint forces and the native retained-cell couple. Weak-row multipliers
    are not display moments. Station gap is distinct from integrated row gap.
    """
    physical_slots: np.ndarray
    constraint_rows: np.ndarray
    reference_measure_m: float
    gap: np.ndarray
    multiplier_density: np.ndarray
    integrated_spatial_gradient: np.ndarray


@dataclass(frozen=True)
class _State:
    q: np.ndarray
    frames: np.ndarray
    cells: np.ndarray
    resultants: np.ndarray
    multipliers: np.ndarray
    shell_anchors: np.ndarray | None = None


def _with_shell_chart(result, state, shell_count):
    if state.shell_anchors is None:
        return result
    local = state.q[:shell_count]
    frames = physical_frames(local, state.shell_anchors)
    display = local.copy().reshape(-1, 6)
    display[:, 3:] = Rotation.from_matrix(frames).as_rotvec()
    return replace(result, shell_displacement=_owned(display.ravel()),
                   shell_frames=_owned(frames),
                   shell_rotation_anchors=state.shell_anchors,
                   shell_chart_coordinates=_owned(local))


class _RotationStepTooLarge(ValueError):
    """Candidate update lies outside the admitted local rotation chart."""


class FinitePointDriver:
    """Finite updates with globally retained native B3 coordinates."""

    def __init__(self, owner):
        self.owner = owner
        # Numerical policy is checkpoint-bound. Legacy restored histories keep
        # their original arithmetic rather than changing endpoint validation.
        self._stable_s3 = bool((owner._has_physical_fibre or owner._footprint_stable_s3) and
            owner._definition.shell.s3_elements and
            owner._definition.shell.j2_curve is None)
        beam_ids = owner._beam_ids
        self._beam_nodal = 6*len(beam_ids)
        self._reference_frames = np.array(
            [owner._beam_nodes[node][1] for node in beam_ids], dtype=float)
        self._reference_positions = np.array(
            [owner._beam_nodes[node][0] for node in beam_ids], dtype=float)
        self._state = _State(
            np.zeros(owner._K.shape[0]), self._reference_frames.copy(),
            np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
            np.zeros((len(owner._beam_parts), 18)),
            np.zeros(owner._C.shape[0]))
        self._shell_origins = tuple(part[3] for part in owner._shell_parts)
        if owner._has_physical_fibre and owner._definition.shell.j2_curve is not None:
            material = owner._shell_model.get_material("shell")
            self._shell_origins = tuple(
                element.seal_solver_integrated_nonlinear_state(
                    owner._shell_model.mesh, material, origin, 3,
                    np.zeros(18), kinematics="LINEAR") if len(slots) == 18 else origin
                for (_eid, element, slots, _), origin in zip(owner._shell_parts, self._shell_origins))
        self._shell_predecessors = self._shell_origins
        self._shell_predecessor_q = _owned(self._state.q[:owner._shell_count])
        self._shell_predecessor_anchors = owned_anchors(
            np.tile(np.eye(3), (len(owner._shell_ids), 1, 1)), len(owner._shell_ids))
        self._beam_origins = tuple(part[2] for part in owner._beam_parts)
        self._beam_predecessors = self._beam_origins
        self._pattern = None
        self._body = getattr(owner, "_body_context", None)
        self._body_stable_s3 = bool(self._body is not None and
            owner._definition.shell.s3_elements and owner._definition.shell.j2_curve is None)
        self._stable_s3 = self._stable_s3 or self._body_stable_s3
        if (self._body is not None and owner._definition.shell.q4_elements and
                owner._definition.q4_pullback_policy != Q4_ALGORITHMIC_PULLBACK_POLICY):
            raise ValueError("finite gravity requires the objective Q4 algorithmic pullback")
        self._programme = getattr(owner, "_staged_context", None)
        self._applied_load = None
        self._load_factor = 0.
        self._accepted = None
        self._accepted_factors = ()
        self._adaptive_state = None
        self._adaptive_checkpoint = None
        self._line_trial_recovery = None
        self._point_trial_recovery = None

    def _load(self, actions):
        owner = self.owner
        load = np.zeros(owner._K.shape[0])
        for action in actions:
            if type(action) is not NodalAction or action.domain not in ("shell", "beam"):
                raise ValueError("declared shell or beam nodal action required")
            index = owner._shell_index if action.domain == "shell" else owner._beam_index
            if action.node not in index:
                raise ValueError("action references unknown physical node")
            wrench = _owned(action.wrench, (6,))
            if np.any(wrench[3:] != 0.):
                raise ValueError("finite experimental path admits translation forces only")
            offset = 0 if action.domain == "shell" else owner._shell_count
            load[offset+6*index[action.node]:offset+6*index[action.node]+6] += wrench
        return _owned(load)

    def _checkpoint_identity(self):
        if self._body is not None:
            return self._body.augmented_model_identity
        return (self.owner._identity if self._programme is None else
                self._programme.augmented_model_identity)

    def _prepare_load(self, actions, targets):
        from ._stiffened_shell_staged_load_experimental import StagedDeadLoadProgramme
        from ._stiffened_shell_ge_body_load import GEBodyLoad
        if type(actions) is GEBodyLoad:
            if (self.owner._definition.shell.q4_elements and
                    self.owner._definition.q4_pullback_policy != Q4_ALGORITHMIC_PULLBACK_POLICY):
                raise ValueError("finite gravity requires the objective Q4 algorithmic pullback")
            if self._programme is not None or (self._accepted is not None and
                    (self._body is None or actions.identity != self._body.request.identity)):
                raise ValueError("finite body load changed after first increment")
            if self._body is None:
                self._body = actions.compile(self.owner)
                self._body_stable_s3 = bool(self.owner._definition.shell.s3_elements and
                    self.owner._definition.shell.j2_curve is None)
                self._stable_s3 = self._stable_s3 or self._body_stable_s3
            return _owned(np.zeros(self.owner._K.shape[0])), None
        if self._body is not None:
            raise ValueError("finite body and nodal/programme loads cannot be mixed")
        if type(actions) is StagedDeadLoadProgramme:
            if self.owner._line_samples:
                raise ValueError("staged translation dead loads require the experimental point owner")
            if self._accepted is not None and (self._programme is None or
                    actions.identity != self._programme.identity):
                raise ValueError("finite load programme changed after first increment")
            programme = (self._programme if self._programme is not None else
                         actions.compile(self.owner, self._load))
            programme.validate_targets(self._load_factor, targets)
            return None, programme
        if self._programme is not None:
            raise ValueError("finite programme and legacy pattern modes cannot be mixed")
        pattern = self._load(actions)
        if self._pattern is not None and not np.array_equal(self._pattern, pattern):
            raise ValueError("finite load pattern changed after first increment")
        return pattern, None

    @staticmethod
    def _programme_result(result, programme, position, applied):
        if programme is None:
            return result
        cursor, fraction = programme.progress_at(position)
        return replace(result, load_programme_identity=programme.identity,
            load_position=float(position), load_stage_cursor=cursor,
            load_stage_fraction=fraction,
            load_programme_complete=cursor == len(programme.programme.endpoints),
            applied_dead_load=_owned(applied))

    def _assemble(self, state, factor, shell_origins, beam_origins, *, pattern=None,
                  applied_load=None):
        owner = self.owner
        load_pattern = self._pattern if pattern is None else pattern
        if applied_load is None and self._programme is not None:
            applied_load = self._programme.load_at(factor)
        if applied_load is None and load_pattern is None:
            raise RuntimeError("finite load pattern has not been supplied")
        applied_load = factor*load_pattern if applied_load is None else applied_load
        count = owner._K.shape[0]
        size = count+len(state.multipliers)
        force_terms = [[] for _ in range(size)]
        rows, columns, data = [], [], []
        shell_candidates = []
        beam_candidates = []
        beam_displacement = state.q[
            owner._shell_count:owner._shell_count+self._beam_nodal
        ].reshape(-1, 6)[:, :3]
        beam_positions, beam_low = _position_pair(
            self._reference_positions, beam_displacement)

        def scatter(slots, force, tangent):
            slots = np.asarray(slots, dtype=int)
            force = np.asarray(force, dtype=float)
            tangent = np.asarray(tangent, dtype=float)
            if (force.shape != (len(slots),) or
                    tangent.shape != (len(slots), len(slots)) or
                    not np.isfinite(force).all() or not np.isfinite(tangent).all()):
                raise RuntimeError("finite local mixed trial operator required")
            for slot, value in zip(slots, force):
                force_terms[int(slot)].append(float(value))
            rows.extend(np.repeat(slots, len(slots)))
            columns.extend(np.tile(slots, len(slots)))
            data.extend(tangent.ravel())

        for (eid, element, slots, _), origin in zip(owner._shell_parts, shell_origins):
            anchors = None if state.shell_anchors is None else state.shell_anchors[slots[::6]//6]
            if len(slots) == 18 and owner._definition.shell.j2_curve is None:
                force, tangent, candidate = variational_shell_response(
                    owner._shell_model, element, state.q[slots], origin, 3,
                    rotation_anchors=anchors, stable_translation=self._stable_s3)
            elif len(slots) == 18:
                force, tangent, candidate = s3_algorithmic_response(
                    owner._shell_model, element, state.q[slots], origin, 3,
                    rotation_anchors=anchors)
            elif owner._definition.q4_pullback_policy == Q4_ALGORITHMIC_PULLBACK_POLICY:
                force, tangent, candidate = q4_algorithmic_response(
                    owner._shell_model, element, state.q[slots], origin, 3,
                    rotation_anchors=anchors)
            else:
                total, chart_map = (state.q[slots], None) if anchors is None else total_coordinates(state.q[slots], anchors)
                force, tangent, candidate = corotational_element_response(
                    owner._shell_model, eid, element, total, True,
                    committed_state=origin, num_layers=3,
                    tangent_mode="consistent", centered_shell_reference=True)
                if chart_map is not None:
                    tangent = tangent@chart_map
            scatter(slots, force, tangent)
            shell_candidates.append(candidate)

        for i, ((element, slots, _), origin) in enumerate(
                zip(owner._beam_parts, beam_origins)):
            nodes = np.array([owner._beam_index[node] for node in element.node_ids])
            response = element.operator.evaluate(
                beam_positions[nodes], beam_low[nodes], state.frames[nodes],
                state.cells[i], state.resultants[i], origin=origin,
                check=element.operator.guard)
            tangent = spatial_jacobian(
                response.residual, response.hessian+response.hessian_low)
            scatter(slots+owner._shell_count, response.residual, tangent)
            if getattr(owner, "_finite_bl5", False) and any(
                    station.accumulated != (0., 0.) for station in response.history.stations):
                raise ValueError("experimental finite BL5 admits elastic beam response only")
            if getattr(owner, "_finite_elastic_footprint", False):
                _require_elastic_footprint_histories((response.history,), "candidate")
            beam_candidates.append(response.history)

        point_records = []
        for i, (joint, slots) in enumerate(zip(owner._connections,
                                               owner._joint_slots)):
            shell_node = slots[0]//6
            beam_node = (slots[6]-owner._shell_count)//6
            shell_position, shell_low = _position_pair(
                owner._shell_xyz[shell_node], state.q[slots[:3]])
            positions = np.array((
                shell_position, beam_positions[beam_node]))
            position_low = np.array((shell_low, beam_low[beam_node]))
            anchors = np.array((np.eye(3) if state.shell_anchors is None else
                                state.shell_anchors[shell_node], state.frames[beam_node]))
            coordinates = np.zeros((2, 3))
            coordinates[0] = state.q[slots[3:6]]
            trial = joint.evaluate_ports(
                positions, anchors, state.multipliers[6*i:6*i+6],
                rotation_coordinates=coordinates,
                charted_ports=(True, False), position_low=position_low)
            point_records.append(point_record(
                owner, i, positions, position_low, trial.pose.residual[:12],
                trial.pose.constraints, "current"))
            extended = np.r_[slots, np.arange(count+6*i, count+6*i+6)]
            # Element and load rows are spatial wrenches. Pull only the
            # increment columns through the shell's additive rotation chart;
            # coordinate-pulled joint rows cannot be summed with these rows.
            scatter(extended, trial.pose.residual,
                    trial.pose.spatial_jacobian@trial.coordinate_map)

        line_records = []
        if getattr(owner, "_finite_bl5", False):
            shell_frames = physical_frames(state.q[:owner._shell_count], state.shell_anchors)
            mechanical = Mechanical(beam_positions, beam_low, state.frames,
                                    state.cells, state.resultants)
            point_rows = 6*len(owner._connections)
            for sample, (line_rows, basis) in zip(owner._line_samples, owner._line_terms):
                operator, slots, weight, _edge, _alpha = sample
                rows_at = line_rows+point_rows
                shell_nodes = slots[:12:6]//6
                density = basis@state.multipliers[rows_at]
                local = operator.evaluate_spatial(
                    state.q[slots[:12]].reshape(2, 6), shell_frames[shell_nodes],
                    mechanical, density)
                jacobian = local.hessian.copy()
                column_map = np.eye(21)
                for start in (3, 9, 18):
                    jacobian[start:start+3, start:start+3] -= .5*skew(local.gradient[start:start+3])
                for start, node in zip((3, 9), shell_nodes):
                    left = _exp_terms(state.q[6*node+3:6*node+6])[1]
                    if np.linalg.svd(left, compute_uv=False)[-1] <= 1e-11:
                        raise ValueError("singular BL5 shell chart; owner must rebase")
                    column_map[start:start+3, start:start+3] = left
                mapped = local.gap_jacobian@column_map
                tangent = np.block([[jacobian@column_map, local.gap_jacobian.T@basis],
                                    [basis.T@mapped, np.zeros((len(rows_at),len(rows_at)))]])
                force = np.r_[local.gradient, basis.T@local.gap]
                scatter(np.r_[slots, count+rows_at], weight*force, weight*tangent)
                line_records.append(FiniteLineStationWork(
                    _owned_slots(slots,(21,)), _owned_slots(rows_at,(len(rows_at),)), float(weight), _owned(local.gap),
                    _owned(density), _owned(weight*local.gradient)))

        if self._body is not None:
            body_force, body_jacobian, _ = self._body.evaluate(state)
            applied_load = applied_load+factor*body_force
            external = body_jacobian.tocoo()
            rows.extend(external.row)
            columns.extend(external.col)
            data.extend(-factor*external.data)
        for row, value in enumerate(applied_load):
            force_terms[row].append(-float(value))
        residual = np.fromiter((fsum(terms) for terms in force_terms),
                               dtype=float, count=size)
        matrix = sparse.coo_matrix(
            (data, (rows, columns)), shape=(size, size)).tocsc()
        if not np.isfinite(residual).all() or not np.isfinite(matrix.data).all():
            raise RuntimeError("finite global mixed trial required")
        relative = _linear_equilibrium(
            residual[owner._free], applied_load[owner._free],
            owner._coordinate_scale[owner._free])
        constraint = _scaled_constraint_gap(
            residual[count:], owner._constraint_scale)
        self._line_trial_recovery = (state, tuple(line_records))
        self._point_trial_recovery = (state, tuple(point_records))
        return residual, matrix, relative, constraint, tuple(shell_candidates), tuple(beam_candidates)

    def _point_records(self, state):
        if self._point_trial_recovery is None or self._point_trial_recovery[0] is not state:
            raise ValueError("stale finite point recovery")
        return self._point_trial_recovery[1]

    def _increment_origin(self, state):
        """Detach one footprint Newton chart without publishing or moving history.

        Equivalent accepted charts start the same numerical problem. The anchor
        remains fixed for the whole increment; derivatives and _advance continue
        to use their existing additive-coordinate contract. Empty-footprint
        owners preserve their historical chart and numerical route.
        """
        owner = self.owner
        if not owner._footprint_increment_chart:
            return state
        require_rotation_triples(owner._fixed, len(owner._shell_ids))
        local = state.q[:owner._shell_count]
        if not np.any(local.reshape(-1, 6)[:, 3:] != 0.):
            return state
        anchors = owned_anchors(physical_frames(local, state.shell_anchors),
                                len(owner._shell_ids))
        q = state.q.copy()
        q[:owner._shell_count].reshape(-1, 6)[:, 3:] = 0.
        return replace(state, q=_owned(q), shell_anchors=anchors)

    def _advance(self, state, increment, amount):
        owner = self.owner
        delta = amount*increment
        q = state.q.copy()
        frames = state.frames.copy()
        cells = state.cells.copy()
        resultants = state.resultants.copy()
        q[:owner._shell_count] += delta[:owner._shell_count]
        for node in range(len(owner._beam_ids)):
            slot = owner._shell_count+6*node
            q[slot:slot+3] += delta[slot:slot+3]
            angle = delta[slot+3:slot+6]
            if np.linalg.norm(angle) >= .9*np.pi:
                raise _RotationStepTooLarge("finite beam rotation increment requires cutback")
            frames[node] = rotation(angle)@frames[node]
        retained = owner._shell_count+self._beam_nodal
        for i in range(len(owner._beam_parts)):
            base = retained+24*i
            for cell in range(2):
                angle = delta[base+3*cell:base+3*cell+3]
                if np.linalg.norm(angle) >= .9*np.pi:
                    raise _RotationStepTooLarge("finite cell rotation increment requires cutback")
                cells[i, cell] = rotation(angle)@cells[i, cell]
            resultants[i] += delta[base+6:base+24]
        multipliers = state.multipliers+delta[len(q):]
        return _State(q, frames, cells, resultants, multipliers, state.shell_anchors)

    def solve(self, actions, targets, *, cancellation_token=None,
              max_iterations=12, max_backtracks=8, increment_control=None,
              on_accepted=None):
        if self.owner._footprint_increment_chart:
            require_rotation_triples(self.owner._fixed, len(self.owner._shell_ids))
        pending = self._adaptive_state is not None and not self._adaptive_state.completed
        if increment_control is None:
            if pending:
                raise ValueError("pending adaptive sequence requires matching targets and controls")
            return self._solve_fixed(actions, targets, cancellation_token=cancellation_token,
                                     max_iterations=max_iterations, max_backtracks=max_backtracks,
                                     on_accepted=on_accepted)
        if type(increment_control) is not AdaptiveIncrementControl:
            raise ValueError("typed adaptive increment control required")
        if (type(targets) is not tuple or not targets or
                any(not isinstance(v, (int, float, np.integer, np.floating)) or
                    isinstance(v, (bool, np.bool_)) or not np.isfinite(v) or v <= 0.
                    for v in targets) or
                type(max_iterations) is not int or not 1 <= max_iterations <= 24 or
                type(max_backtracks) is not int or not 0 <= max_backtracks <= 12):
            raise ValueError("finite adaptive targets and Newton controls required")
        targets = tuple(float(v) for v in targets)
        if pending:
            control = self._adaptive_state
            if (targets != control.targets or increment_control != control.control or
                    max_iterations != control.max_iterations or max_backtracks != control.max_backtracks):
                raise ValueError("pending adaptive sequence requires matching targets and controls")
        else:
            if any(a == b for a, b in zip((self._load_factor,)+targets, targets)):
                raise ValueError("adaptive load factors must change")
            control = _AdaptiveState(increment_control, targets, max_iterations,
                                     max_backtracks, 0, float(self._load_factor))
            # Bound metadata before numerical work; no model-size-dependent search.
            encode_control(self.owner._identity, control, b"resource-check")
        pattern, programme = self._prepare_load(actions, targets[control.cursor:])
        while not control.completed:
            if len(control.attempts) >= control.control.max_attempts:
                raise AdaptiveIncrementExhausted("adaptive increment attempt limit", control, self._accepted_factors)
            factor = control.next_factor(self._load_factor)
            if not np.isfinite(factor) or factor <= 0. or factor == self._load_factor:
                raise AdaptiveIncrementExhausted("adaptive increment is not representable", control, self._accepted_factors)

            def accepted(attempt):
                next_control = control.accepted(replace(attempt, target=control.targets[control.cursor]))
                encode_control(self.owner._identity, next_control, b"resource-check")
                return next_control

            try:
                self._solve_fixed(actions, (factor,), cancellation_token=cancellation_token,
                    max_iterations=max_iterations, max_backtracks=max_backtracks,
                    _prepared_pattern=pattern, _prepared_programme=programme,
                    _accepted_hook=accepted)
            except FiniteIncrementFailure as error:
                attempt = replace(error.attempt, target=control.targets[control.cursor])
                rejected = replace(control, attempts=control.attempts+(attempt,))
                if control.depth >= control.control.max_cutbacks:
                    raise AdaptiveIncrementExhausted("adaptive increment cutback limit", rejected,
                                                    self._accepted_factors) from error
                control = control.rejected(attempt)
            else:
                control = self._adaptive_state
                # Outside the candidate-failure handler: even a typed numerical
                # exception raised by an observer must not trigger cutback.
                if on_accepted is not None:
                    on_accepted(deepcopy(self._accepted))
        return self._accepted

    def _solve_fixed(self, actions, targets, *, cancellation_token=None,
              _prepared_pattern=None, _prepared_programme=None, _accepted_hook=None,
              max_iterations=12, max_backtracks=8, on_accepted=None):
        owner = self.owner
        if (type(targets) is not tuple or not targets or
                any(not isinstance(v, (int, float, np.integer, np.floating))
                    or isinstance(v, (bool, np.bool_)) or
                    not np.isfinite(v) or v <= 0.
                    for v in targets) or
                any(a == b for a, b in zip((self._load_factor,)+targets,
                                            targets))):
            raise ValueError("positive finite load factors must change at each increment")
        if (type(max_iterations) is not int or not 1 <= max_iterations <= 24 or
                type(max_backtracks) is not int or not 0 <= max_backtracks <= 12):
            raise ValueError("bounded finite Newton controls required")
        if _prepared_programme is None and _prepared_pattern is None:
            pattern, programme = self._prepare_load(actions, targets)
        else:
            pattern, programme = _prepared_pattern, _prepared_programme
        free = np.r_[owner._free,
                     np.arange(owner._K.shape[0],
                               owner._K.shape[0]+len(self._state.multipliers))]
        for factor in targets:
            applied_load = None if programme is None else programme.load_at(factor)
            cancellation_safe_point(cancellation_token, "stiffened-shell.finite.increment")
            trial = self._increment_origin(self._state)
            counts = {"evaluations": 0, "linear_solves": 0, "rejected_trials": 0}
            accepted_from = float(self._load_factor)
            def evaluated(state):
                counts["evaluations"] += 1
                return self._assemble(state, factor, self._shell_origins,
                                      self._beam_origins, pattern=pattern,
                                      **({} if programme is None else
                                         {"applied_load": applied_load}))
            def attempt(status, iteration, relative, gap, failure=None):
                return IncrementAttempt(float(factor), accepted_from, float(factor),
                    status, iteration, **counts, equilibrium_ratio=float(relative),
                    constraint_max=float(gap), failure=failure)
            for iteration in range(max_iterations+1):
                cancellation_safe_point(cancellation_token, "stiffened-shell.finite.trial")
                residual, matrix, relative, gap, shell_next, beam_next = (
                    evaluated(trial))
                if relative <= 1e-8 and gap <= 1e-9:
                    cancellation_safe_point(cancellation_token,
                                            "stiffened-shell.finite.commit")
                    support = np.zeros(owner._K.shape[0])
                    support[owner._fixed] = residual[owner._fixed]
                    next_factors = self._accepted_factors+(float(factor),)
                    if owner._definition.shell.j2_curve is not None:
                        next_shell_origins = _accepted_shell_material_origins(
                            owner, trial, shell_next)
                    else:
                        next_shell_origins = shell_next
                    q4_count = len(owner._definition.shell.q4_elements)
                    next_result = FinitePointResult(
                        "completed", float(factor),
                        _owned(trial.q[:owner._shell_count]),
                        _owned(self._beam_positions(trial)),
                        _owned(trial.frames), _owned(trial.cells),
                        _owned(trial.resultants), _owned(trial.multipliers),
                        _owned(support), relative, gap, iteration,
                        owner._generation+1, next_factors,
                        _material_observables(beam_next),
                        (tuple(tuple(float(v) for v in state["alpha"])
                               for state in shell_next)
                         if owner._definition.shell.j2_curve is not None else ()),
                        (_shell_q4_recovery(owner._shell_parts[:q4_count],
                                            shell_next[:q4_count])
                         if owner._definition.shell.j2_curve is not None else ()),
                        (_shell_s3_recovery(owner._shell_parts[q4_count:],
                                            shell_next[q4_count:])
                         if owner._definition.shell.j2_curve is not None else ()))
                    cancellation_safe_point(cancellation_token,
                                            "stiffened-shell.finite.publish")
                    next_result = _with_shell_chart(next_result, trial, owner._shell_count)
                    next_result = replace(next_result, point_wrenches=self._point_records(trial))
                    next_result = self._programme_result(next_result, programme, factor, applied_load)
                    next_result = self._body_result(next_result, trial, factor)
                    if getattr(owner, "_finite_bl5", False):
                        if self._line_trial_recovery[0] is not trial:
                            raise ValueError("stale finite BL5 station recovery")
                        next_result = replace(next_result,
                            beam_shell_line_work=self._line_trial_recovery[1])
                    if owner._has_physical_fibre:
                        fibre_records, fibre_energies = _fibre_recovery(
                            owner, trial, self._beam_origins, beam_next)
                        next_result = replace(next_result, beam_fibre_material=fibre_records,
                                              beam_fibre_energy=fibre_energies)
                        cancellation_safe_point(cancellation_token,
                                                "stiffened-shell.finite.material-publish")
                    previous_shell_q = _owned(self._state.q[:owner._shell_count])
                    previous_shell_anchors = (self._shell_predecessor_anchors
                        if self._state.shell_anchors is None else self._state.shell_anchors)
                    next_control = (None if _accepted_hook is None else
                        _accepted_hook(attempt("accepted", iteration, relative, gap)))
                    if next_control is not None:
                        next_result = replace(next_result,
                            status="completed" if next_control.completed else "accepted_prefix",
                            increment_attempts=next_control.attempts)
                    next_checkpoint = (None if next_control is None and programme is None and self._body is None else
                        self._prospective_checkpoint(next_result, _state=trial,
                            _shell_predecessors=self._shell_origins,
                            _shell_predecessor_q=previous_shell_q,
                            _shell_predecessor_anchors=previous_shell_anchors,
                            _shell_origins=next_shell_origins,
                            _beam_predecessors=self._beam_origins, _beam_origins=beam_next,
                            _load_factor=float(factor), _accepted_factors=next_factors,
                            _pattern=pattern, _programme=programme,
                            _applied_load=applied_load, _adaptive_state=next_control))
                    if next_control is not None or programme is not None or self._body is not None:
                        cancellation_safe_point(cancellation_token,
                                                "stiffened-shell.finite.controller-publish")
                    with owner._commit_lock:
                        self._shell_predecessors = self._shell_origins
                        self._shell_predecessor_q = previous_shell_q
                        self._shell_predecessor_anchors = previous_shell_anchors
                        self._state = trial
                        self._shell_origins = next_shell_origins
                        self._beam_predecessors = self._beam_origins
                        self._beam_origins = beam_next
                        self._load_factor = float(factor)
                        self._accepted_factors = next_factors
                        self._pattern = pattern
                        self._programme = programme
                        self._applied_load = applied_load
                        owner._generation += 1
                        self._accepted = next_result
                        self._adaptive_state = next_control
                        self._adaptive_checkpoint = next_checkpoint
                        if owner._finite_driver is None:
                            owner._finite_driver = self
                    if on_accepted is not None:
                        on_accepted(deepcopy(next_result))
                    break
                if iteration == max_iterations:
                    raise FiniteIncrementFailure(attempt("rejected", iteration,
                        relative, gap, "finite mixed Newton iteration limit"))
                with warnings.catch_warnings():
                    warnings.simplefilter("error", spla.MatrixRankWarning)
                    counts["linear_solves"] += 1
                    step = spla.spsolve(matrix[free, :][:, free],
                                       -residual[free])
                if not np.isfinite(step).all():
                    raise RuntimeError("finite mixed Newton correction required")
                full = np.zeros(matrix.shape[0])
                full[free] = step
                old_merit = max(relative, gap)
                for backtrack in range(max_backtracks+1):
                    cancellation_safe_point(
                        cancellation_token, "stiffened-shell.finite.backtrack")
                    try:
                        candidate = self._advance(trial, full, .5**backtrack)
                    except _RotationStepTooLarge:
                        counts["rejected_trials"] += 1
                        continue
                    try:
                        changed = evaluated(candidate)
                    except BL5TrialDomainError:
                        counts["rejected_trials"] += 1
                        continue
                    if max(changed[2], changed[3]) < old_merit:
                        trial = candidate
                        break
                    counts["rejected_trials"] += 1
                else:
                    raise FiniteIncrementFailure(attempt("rejected", iteration+1,
                        relative, gap, "finite mixed backtrack budget exhausted"))
        return self._accepted

    def _beam_positions(self, state):
        positions = self._reference_positions.copy()
        for node in range(len(self.owner._beam_ids)):
            slot = self.owner._shell_count+6*node
            positions[node] += state.q[slot:slot+3]
        return positions

    def recover(self):
        if self._accepted is None:
            raise RuntimeError("no accepted finite mixed increment")
        return self._accepted

    def _body_result(self, result, state, factor):
        if self._body is None:
            return result
        return replace(result, body_load=self._body.evaluate(state)[2].scaled(factor))

    def _prospective_checkpoint(self, result, **changes):
        """Serialize the prepared accepted snapshot before publishing it.

        This read-only view shares immutable compiled data, never owns a
        second analysis or commits a component. No scratch view is retained.
        """
        prepared = copy(self)
        prepared.__dict__.update(changes)
        prepared.owner = SimpleNamespace(**{**self.owner.__dict__,
                                           "_generation": result.generation})
        prepared._accepted = result
        prepared._adaptive_checkpoint = None
        return prepared.checkpoint()

    def rebase_rotations(self, expected_generation, *, cancellation_token=None):
        """Atomic same-load chart event; constitutive histories are untouched."""
        owner = self.owner
        if type(expected_generation) is not int:
            raise ValueError("integer accepted predecessor generation required")
        with owner._commit_lock:
            if self._accepted is None or expected_generation != owner._generation:
                raise ValueError("stale or missing accepted rebase predecessor")
            previous = self._state
        fixed = set(owner._fixed)
        for node in range(len(owner._shell_ids)):
            restrained = [6*node+j in fixed for j in (3, 4, 5)]
            if any(restrained) and not all(restrained):
                raise ValueError("shell anchor reset requires full rotational triples; partial supports need transformed equations")
        cancellation_safe_point(cancellation_token, "stiffened-shell.rebase.prepare")
        local = previous.q[:owner._shell_count]
        if not np.any(local.reshape(-1, 6)[:, 3:] != 0.):
            raise ValueError("no nonzero shell chart coordinates to rebase")
        frames = physical_frames(local, previous.shell_anchors)
        anchors = owned_anchors(frames, len(owner._shell_ids))
        q = previous.q.copy()
        q[:owner._shell_count].reshape(-1, 6)[:, 3:] = 0.
        trial = replace(previous, q=_owned(q), shell_anchors=anchors)
        if not np.allclose(physical_frames(q[:owner._shell_count], anchors), frames,
                           rtol=0., atol=1e-12):
            raise ValueError("rebase changed physical shell orientations")
        residual, _, relative, gap, _, _ = self._assemble(
            trial, self._load_factor, self._shell_origins, self._beam_origins)
        if not np.isfinite(relative) or not np.isfinite(gap) or relative > 1e-8 or gap > 1e-9:
            raise ValueError("mechanically inconsistent shell anchor reset")
        support = np.zeros(owner._K.shape[0]); support[owner._fixed] = residual[owner._fixed]
        result = _with_shell_chart(replace(self._accepted,
            support_reactions=_owned(support), free_equilibrium_ratio=relative,
            constraint_max=gap, generation=expected_generation+1,
            point_wrenches=self._point_records(trial)), trial, owner._shell_count)
        result = self._body_result(result, trial, self._load_factor)
        next_checkpoint = (None if self._adaptive_state is None and self._programme is None and self._body is None else
                           self._prospective_checkpoint(result, _state=trial))
        cancellation_safe_point(cancellation_token, "stiffened-shell.rebase.commit")
        with owner._commit_lock:
            if owner._generation != expected_generation or self._state is not previous:
                raise ValueError("stale accepted rebase predecessor")
            self._state = trial
            self._accepted = result
            self._adaptive_checkpoint = next_checkpoint
            owner._generation += 1
        return result

    def checkpoint(self, *, _encode_anchors=True, _encode_control=True,
                   _encode_programme=True, _encode_body=True):
        if self._accepted is None:
            raise RuntimeError("no accepted finite mixed increment")
        if (self._adaptive_checkpoint is not None and _encode_anchors and
                _encode_control and _encode_programme and _encode_body):
            return self._adaptive_checkpoint
        if self._body is not None and _encode_body:
            from ._stiffened_shell_ge_body_load import encode_checkpoint
            return encode_checkpoint(self._body, self.checkpoint(
                _encode_anchors=_encode_anchors, _encode_control=_encode_control,
                _encode_programme=_encode_programme, _encode_body=False))
        if self._programme is not None and _encode_programme:
            from ._stiffened_shell_staged_load_experimental import encode_checkpoint
            return encode_checkpoint(self._programme, self._load_factor,
                self.checkpoint(_encode_anchors=_encode_anchors,
                    _encode_control=_encode_control, _encode_programme=False))
        if self._adaptive_state is not None and _encode_control:
            return encode_control(self._checkpoint_identity(), self._adaptive_state,
                                  self.checkpoint(_encode_control=False, _encode_programme=False, _encode_body=False))
        state = self._state
        anchored = state.shell_anchors is not None
        if anchored and _encode_anchors:
            return _encode_chart_checkpoint(
                self._checkpoint_identity(), self.owner._generation, state.shell_anchors,
                self._accepted.shell_frames, self.checkpoint(
                    _encode_anchors=False, _encode_control=False, _encode_programme=False, _encode_body=False))
        generation = len(self._accepted_factors) if anchored else self.owner._generation
        def kind(name):
            return name.replace("finite", "finite_chart", 1) if anchored else name
        arrays = (("q", state.q), ("frames", state.frames),
                  ("cells", state.cells), ("resultants", state.resultants),
                  ("multipliers", state.multipliers),
                  ("pattern" if self._programme is None else "applied_dead_load",
                   self._pattern if self._programme is None else self._applied_load),
                  ("accepted_factors", np.asarray(self._accepted_factors)))
        if getattr(self.owner, "_finite_bl5", False):
            return _encode_binary_checkpoint(kind("finite_bl5"),
                self._checkpoint_identity(), generation, arrays)
        if self.owner._has_physical_fibre or self.owner._footprint_stable_s3 or self._body_stable_s3:
            if self.owner._definition.shell.j2_curve is not None:
                owner = self.owner
                q4_count = len(owner._definition.shell.q4_elements)
                plastic, alpha = _shell_material_arrays(self._shell_origins[:q4_count])
                origin_plastic, origin_alpha = _shell_material_arrays(
                    self._shell_predecessors[:q4_count])
                material = owner._shell_model.get_material("shell")
                states = tuple(element.serialize_nonlinear_state(
                    owner._shell_model.mesh, material, origin, 3)
                    for origins in (self._shell_origins, self._shell_predecessors)
                    for (_eid, element, _slots, _), origin in zip(
                        owner._shell_parts[q4_count:], origins[q4_count:]))
                return _encode_s3_checkpoint(self._checkpoint_identity(), generation,
                    arrays + native_history_arrays(owner._beam_parts, self._beam_predecessors, "origin") +
                    native_history_arrays(owner._beam_parts, self._beam_origins, "accepted") + (
                        ("shell_plastic", plastic), ("shell_alpha", alpha),
                        ("shell_origin_plastic", origin_plastic),
                        ("shell_origin_alpha", origin_alpha),
                        ("shell_origin_q", self._shell_predecessor_q),
                        ("shell_origin_anchors", self._shell_predecessor_anchors)),
                    states, anchored=anchored, native_material=True)
            return _encode_binary_checkpoint(kind("finite_native_material_stable"
                if self._stable_s3 else "finite_native_material"),
                self._checkpoint_identity(), generation, arrays +
                native_history_arrays(self.owner._beam_parts,
                                      self._beam_predecessors, "origin") +
                native_history_arrays(self.owner._beam_parts,
                                      self._beam_origins, "accepted"))
        nonmonotone = any(b <= a for a, b in zip(
            self._accepted_factors, self._accepted_factors[1:]))
        if (self.owner._definition.shell.j2_curve is not None and
                self.owner._definition.shell.s3_elements):
            q4_count = len(self.owner._definition.shell.q4_elements)
            beam_plastic, beam_accumulated = _material_arrays(self._beam_origins)
            shell_plastic, shell_alpha = _shell_material_arrays(
                self._shell_origins[:q4_count])
            material = self.owner._shell_model.get_material("shell")
            s3_states = tuple(element.serialize_nonlinear_state(
                self.owner._shell_model.mesh, material, origin, 3)
                for (_eid, element, _slots, _), origin in zip(
                    self.owner._shell_parts[q4_count:],
                    self._shell_origins[q4_count:]))
            return _encode_s3_checkpoint(
                self._checkpoint_identity(), generation,
                arrays + (("beam_plastic", beam_plastic),
                          ("beam_accumulated", beam_accumulated),
                          ("shell_plastic", shell_plastic),
                          ("shell_alpha", shell_alpha)), s3_states, anchored=anchored)
        if self.owner._definition.shell.j2_curve is not None:
            beam_plastic, beam_accumulated = _material_arrays(self._beam_origins)
            shell_plastic, shell_alpha = _shell_material_arrays(self._shell_origins)
            return _encode_binary_checkpoint(
                kind("finite_shell_material"), self._checkpoint_identity(),
                generation,
                arrays + (("beam_plastic", beam_plastic),
                          ("beam_accumulated", beam_accumulated),
                          ("shell_plastic", shell_plastic),
                          ("shell_alpha", shell_alpha)))
        if (nonmonotone or any(station.accumulated != (0., 0.)
               for history in self._beam_origins
               for station in history.stations)):
            plastic, accumulated = _material_arrays(self._beam_origins)
            return _encode_binary_checkpoint(
                kind("finite_material"), self._checkpoint_identity(),
                generation,
                arrays + (("beam_plastic", plastic),
                          ("beam_accumulated", accumulated)))
        if anchored or sum(value.size for _name, value in arrays) > MAX_JSON_CHECKPOINT_VALUES:
            return _encode_binary_checkpoint(
                kind("finite"), self._checkpoint_identity(), generation, arrays)
        payload = {
            "schema": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_V1",
            "model": self._checkpoint_identity(),
            "generation": self.owner._generation,
            "accepted_factors": self._accepted_factors,
            "q": state.q.tolist(),
            "frames": state.frames.tolist(),
            "cells": state.cells.tolist(),
            "resultants": state.resultants.tolist(),
            "multipliers": state.multipliers.tolist(),
            ("pattern" if self._programme is None else "applied_dead_load"):
                (self._pattern if self._programme is None else self._applied_load).tolist(),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("ascii")
        if len(raw) > MAX_JSON_CHECKPOINT_BYTES:
            return _encode_binary_checkpoint(
                "finite", self._checkpoint_identity(), self.owner._generation, arrays)
        return raw

    def restore(self, value, *, rotation_anchors=None, pose_witness=None,
                accepted_generation=None, adaptive_state=None):
        """Restore an accepted endpoint after mechanical consistency checks.

        V3 checks material admissibility and re-evaluation from the saved
        accepted material state at this endpoint. It does not prove that bytes
        came from the recorded loading path; that needs trusted provenance or
        an independent replay of the accepted history.
        """
        owner = self.owner
        load_key = "pattern" if self._programme is None else "applied_dead_load"
        base_keys = {"schema", "model", "generation", "accepted_factors",
                     "q", "frames", "cells", "resultants", "multipliers",
                     load_key}
        if type(value) is not dict:
            raise ValueError("incompatible experimental finite checkpoint")
        if (value.get("schema") == _BINARY_SCHEMAS["finite_bl5"]) != bool(
                getattr(owner, "_finite_bl5", False)):
            raise ValueError("finite BL5 checkpoint requires its matching line policy")
        native_shell = value.get("schema") == NATIVE_SHELL_SCHEMA
        stable_s3 = value.get("schema") == STABLE_NATIVE_SCHEMA
        if (owner._footprint_stable_s3 or self._body_stable_s3) and not stable_s3:
            raise ValueError("nodal footprint S3 checkpoint requires its stable numerical policy")
        if stable_s3 and not self._stable_s3:
            raise ValueError("stable S3 native checkpoint requires elastic S3 fibre model")
        # This driver is still private to restore until all validation passes.
        self._stable_s3 = stable_s3
        native_material = value.get("schema") in (NATIVE_MATERIAL_CHECKPOINT, STABLE_NATIVE_SCHEMA) or native_shell
        s3_material = (value.get("schema") == FINITE_S3_MATERIAL_CHECKPOINT or
                       (native_shell and bool(owner._definition.shell.s3_elements)))
        shell_material = value.get("schema") in (
            FINITE_SHELL_MATERIAL_CHECKPOINT, FINITE_S3_MATERIAL_CHECKPOINT, NATIVE_SHELL_SCHEMA)
        material = value.get("schema") in (
            FINITE_MATERIAL_CHECKPOINT, FINITE_SHELL_MATERIAL_CHECKPOINT,
            FINITE_S3_MATERIAL_CHECKPOINT)
        expected_keys = (base_keys | {"beam_plastic", "beam_accumulated"}
                         if material else base_keys)
        if native_material:
            expected_keys |= {name for prefix in ("origin", "accepted")
                for name, _ in native_history_shapes(owner._beam_parts, prefix)}
        if shell_material:
            expected_keys |= {"shell_plastic", "shell_alpha"}
        if s3_material:
            expected_keys |= {"s3_states"}
        if native_shell:
            expected_keys |= {"shell_origin_plastic", "shell_origin_alpha",
                              "shell_origin_q", "shell_origin_anchors", "s3_states"}
        if (set(value) != expected_keys or
                value["schema"] not in
                (FINITE_CHECKPOINT, _BINARY_SCHEMAS["finite_bl5"], NATIVE_MATERIAL_CHECKPOINT, STABLE_NATIVE_SCHEMA, NATIVE_SHELL_SCHEMA, FINITE_MATERIAL_CHECKPOINT,
                 FINITE_SHELL_MATERIAL_CHECKPOINT,
                 FINITE_S3_MATERIAL_CHECKPOINT) or
                value["model"] != owner._identity or
                type(value["generation"]) is not int or
                value["generation"] < 1 or
                shell_material != (owner._definition.shell.j2_curve is not None) or
                s3_material != bool(owner._definition.shell.j2_curve is not None
                                    and owner._definition.shell.s3_elements)):
            raise ValueError("incompatible experimental finite checkpoint")
        factors = value["accepted_factors"]
        if (type(factors) is not list or len(factors) != value["generation"] or
                not factors or any(type(v) is not float or not np.isfinite(v)
                                   for v in factors) or
                (not material and not native_material and not getattr(owner,"_finite_bl5",False) and (factors[0] <= 0. or
                    any(b <= a for a, b in zip(factors, factors[1:])))) or
                ((material or native_material or getattr(owner,"_finite_bl5",False)) and (factors[0] <= 0. or
                    any(b <= 0. or b == a for a, b in
                        zip(factors, factors[1:]))))):
            raise ValueError("invalid accepted finite load history")
        q = _owned(value["q"], (owner._K.shape[0],))
        if rotation_anchors is not None:
            rotation_anchors = owned_anchors(rotation_anchors, len(owner._shell_ids))
            witness = owned_anchors(pose_witness, len(owner._shell_ids))
            if (type(accepted_generation) is not int or
                    accepted_generation < value["generation"] or
                    (accepted_generation == value["generation"] and not owner._footprint_increment_chart)):
                raise ValueError("shell chart generation is incompatible with its load-step count and chart policy")
            if not np.allclose(physical_frames(q[:owner._shell_count], rotation_anchors),
                               witness, rtol=0., atol=1e-11):
                raise ValueError("shell chart anchor disagrees with physical pose witness")
            fixed = set(owner._fixed)
            for i, anchor in enumerate(rotation_anchors):
                if (any(6*i+j in fixed for j in (3, 4, 5)) and
                        np.linalg.norm(anchor-np.eye(3)) > 1e-12):
                    raise ValueError("anchored partial or fixed shell support is unsupported")
        elif pose_witness is not None or accepted_generation is not None:
            raise ValueError("complete owned shell chart snapshot required")
        frames = _owned(value["frames"], self._reference_frames.shape)
        cells = _owned(value["cells"], self._state.cells.shape)
        resultants = _owned(value["resultants"], self._state.resultants.shape)
        multipliers = _owned(value["multipliers"], self._state.multipliers.shape)
        pattern = _owned(value[load_key], (owner._K.shape[0],))
        if self._programme is not None:
            self._programme.validate_targets(0., tuple(factors))
            if not np.array_equal(pattern, self._programme.load_at(factors[-1])):
                raise ValueError("staged checkpoint applied force disagrees with programme")
        if native_material:
            if not owner._has_physical_fibre and not owner._footprint_stable_s3 and not self._body_stable_s3:
                raise ValueError("native material checkpoint requires fibre model")
            beam_origins = native_histories(owner._beam_parts, value, "origin")
            beam_accepted = native_histories(owner._beam_parts, value, "accepted")
        elif material:
            stations = sum(len(part[0].operator.cell.stations)
                           for part in owner._beam_parts)
            plastic = _owned(value["beam_plastic"], (stations, 6, 2))
            accumulated = _owned(value["beam_accumulated"], (stations, 2))
            beam_origins = _material_histories(owner, plastic, accumulated)
            if not shell_material and not np.any(accumulated) and all(
                    b > a for a, b in zip(factors, factors[1:])):
                raise ValueError("material checkpoint requires yielded or reversed history")
        else:
            beam_origins = self._beam_origins
        if owner._finite_elastic_footprint:
            _require_elastic_footprint_histories(beam_origins, "checkpoint origin")
            if native_material:
                _require_elastic_footprint_histories(beam_accepted, "checkpoint accepted")
        if shell_material:
            q4_count = len(owner._definition.shell.q4_elements)
            shell_count = q4_count if s3_material else len(owner._shell_parts)
            shell_plastic = _owned(value["shell_plastic"], (shell_count, 12, 3))
            shell_alpha = _owned(value["shell_alpha"], (shell_count, 12))
            if np.any(shell_alpha < 0.):
                raise ValueError("nonphysical shell J2 checkpoint state")
            shell_origins = _shell_material_states(shell_plastic, shell_alpha)
            if s3_material and not native_shell:
                blobs = value["s3_states"]
                if (type(blobs) is not tuple or
                        len(blobs) != len(owner._definition.shell.s3_elements)):
                    raise ValueError("complete native S3 checkpoint states required")
                shell_material_def = owner._shell_model.get_material("shell")
                s3_origins = []
                for (_eid, element, slots, _), blob in zip(
                        owner._shell_parts[q4_count:], blobs):
                    anchors = None if rotation_anchors is None else rotation_anchors[slots[::6]//6]
                    local_q = s3_local_coordinates(owner._shell_model, element, q[slots],
                                                  rotation_anchors=anchors)
                    restored = element.deserialize_nonlinear_state(
                        owner._shell_model.mesh, shell_material_def, blob, 3,
                        expected_committed_total_u=local_q)
                    _require_s3_material_state(restored, local_q, accepted=True)
                    s3_origins.append(restored)
                shell_origins += tuple(s3_origins)
        else:
            shell_origins = self._shell_origins
        shell_accepted = shell_origins
        if native_shell:
            origin_plastic = _owned(value["shell_origin_plastic"], (q4_count, 12, 3))
            origin_alpha = _owned(value["shell_origin_alpha"], (q4_count, 12))
            if np.any(origin_alpha < 0.):
                raise ValueError("nonphysical shell J2 predecessor")
            origin_q = _owned(value["shell_origin_q"], (owner._shell_count,))
            origin_anchors = owned_anchors(value["shell_origin_anchors"], len(owner._shell_ids))
            if np.any(origin_q[np.asarray(owner._fixed)[np.asarray(owner._fixed) < owner._shell_count]] != 0.):
                raise ValueError("invalid shell predecessor support coordinates")
            blobs = value["s3_states"]
            s3_count = len(owner._definition.shell.s3_elements)
            if type(blobs) is not tuple or len(blobs) != 2*s3_count:
                raise ValueError("complete accepted and predecessor S3 states required")
            states = []
            material_def = owner._shell_model.get_material("shell")
            for coordinates, anchors, family in ((q, rotation_anchors, blobs[:s3_count]),
                                                 (origin_q, origin_anchors, blobs[s3_count:])):
                made = []
                for (_eid, element, slots, _), blob in zip(owner._shell_parts[q4_count:], family):
                    local_anchors = None if anchors is None else anchors[slots[::6]//6]
                    local_q = s3_local_coordinates(owner._shell_model, element, coordinates[slots],
                                                  rotation_anchors=local_anchors)
                    restored = element.deserialize_nonlinear_state(owner._shell_model.mesh,
                        material_def, blob, 3, expected_committed_total_u=local_q)
                    _require_s3_material_state(restored, local_q, accepted=True)
                    made.append(restored)
                states.append(tuple(made))
            shell_accepted += states[0]
            shell_origins = _shell_material_states(origin_plastic, origin_alpha) + states[1]
        beam_nodal = q[owner._shell_count:
                       owner._shell_count+self._beam_nodal].reshape(-1, 6)
        if (np.any(q[owner._fixed] != 0.) or
                np.any(beam_nodal[:, 3:] != 0.) or
                np.any(q[owner._shell_count+self._beam_nodal:] != 0.) or
                np.any(pattern[owner._shell_count+self._beam_nodal:] != 0.) or
                np.any(pattern[:owner._shell_count+self._beam_nodal]
                       .reshape(-1, 6)[:, 3:] != 0.)):
            raise ValueError("invalid finite checkpoint coordinate or load layout")
        for family in (frames.reshape(-1, 3, 3), cells.reshape(-1, 3, 3)):
            if any(np.linalg.norm(frame.T@frame-np.eye(3)) > 1e-9 or
                   abs(np.linalg.det(frame)-1.) > 1e-9 for frame in family):
                raise ValueError("nonphysical finite checkpoint rotation")
        trial = _State(q, frames, cells, resultants, multipliers, rotation_anchors)
        residual, _, relative, gap, shell_next, beam_next = self._assemble(
            trial, factors[-1], shell_origins, beam_origins,
            pattern=pattern if self._programme is None else None,
            applied_load=None if self._programme is None else pattern)
        if (not np.isfinite(relative) or relative > 1e-8 or gap > 1e-9 or
                (not material and not native_material and any(station.accumulated != (0., 0.)
                    for history in beam_next for station in history.stations))):
            raise ValueError("mechanically inconsistent finite checkpoint")
        if native_material and beam_next != beam_accepted:
            raise ValueError("native material checkpoint update disagrees with accepted history")
        if native_shell and s3_material:
            repeated_origins = _accepted_shell_material_origins(owner, trial, shell_next)
            material_def = owner._shell_model.get_material("shell")
            for (_eid, element, _slots, _), saved_state, repeated_state in zip(
                    owner._shell_parts[q4_count:], shell_accepted[q4_count:],
                    repeated_origins[q4_count:]):
                saved_bytes = element.serialize_nonlinear_state(
                    owner._shell_model.mesh, material_def, saved_state, 3)
                repeated_bytes = element.serialize_nonlinear_state(
                    owner._shell_model.mesh, material_def, repeated_state, 3)
                if saved_bytes != repeated_bytes:
                    raise ValueError("native S3 checkpoint response disagrees with accepted update")
        if material:
            next_plastic, next_accumulated = _material_arrays(beam_next)
            for saved, repeated in ((plastic, next_plastic),
                                    (accumulated, next_accumulated)):
                scale = max(float(np.max(np.abs(saved), initial=0.)),
                            float(np.max(np.abs(repeated), initial=0.)),
                            np.finfo(float).tiny)
                # Paired Decimal updates can alter only low components when
                # an equilibrium state is re-evaluated from its own origin.
                if np.max(np.abs(saved-repeated), initial=0.) > (
                        64.*np.finfo(float).eps*scale):
                    raise ValueError("mechanically inconsistent material checkpoint")
        if shell_material:
            next_plastic, next_alpha = _shell_material_arrays(
                shell_next[:q4_count])
            for saved, repeated in ((shell_plastic, next_plastic),
                                    (shell_alpha, next_alpha)):
                scale = max(float(np.max(np.abs(saved), initial=0.)),
                            float(np.max(np.abs(repeated), initial=0.)),
                            np.finfo(float).tiny)
                if np.max(np.abs(saved-repeated), initial=0.) > (
                        64.*np.finfo(float).eps*scale):
                    raise ValueError("mechanically inconsistent shell J2 checkpoint")
            if s3_material:
                for saved_state, repeated_state in zip(
                        shell_accepted[q4_count:], shell_next[q4_count:]):
                    for name in ("plastic_strain", "alpha"):
                        saved = np.asarray(saved_state[name], dtype=float)
                        repeated = np.asarray(repeated_state[name], dtype=float)
                        scale = max(float(np.max(np.abs(saved), initial=0.)),
                                    float(np.max(np.abs(repeated), initial=0.)),
                                    np.finfo(float).tiny)
                        if np.max(np.abs(saved-repeated), initial=0.) > (
                                64.*np.finfo(float).eps*scale):
                            raise ValueError(
                                "mechanically inconsistent S3 J2 checkpoint")
        support = np.zeros(owner._K.shape[0])
        support[owner._fixed] = residual[owner._fixed]
        result = FinitePointResult(
            "completed", factors[-1], _owned(q[:owner._shell_count]),
            _owned(self._beam_positions(trial)), frames, cells, resultants,
            multipliers, _owned(support), relative, gap, 0,
            value["generation"] if accepted_generation is None else accepted_generation, tuple(factors),
            _material_observables(beam_accepted if native_material else beam_origins),
            (tuple(tuple(float(v) for v in state["alpha"])
                   for state in shell_accepted) if shell_material else ()),
            (_shell_q4_recovery(owner._shell_parts[:q4_count],
                                shell_next[:q4_count])
             if shell_material else ()),
            (_shell_s3_recovery(owner._shell_parts[q4_count:],
                                shell_next[q4_count:])
             if s3_material else ()))
        result = _with_shell_chart(result, trial, owner._shell_count)
        result = replace(result, point_wrenches=self._point_records(trial))
        if getattr(owner, "_finite_bl5", False):
            result = replace(result, beam_shell_line_work=self._line_trial_recovery[1])
        if native_material:
            fibre_records, fibre_energies = _fibre_recovery(
                owner, trial, beam_origins, beam_accepted)
            result = replace(result, beam_fibre_material=fibre_records,
                             beam_fibre_energy=fibre_energies)
        if adaptive_state is not None:
            result = replace(result,
                status="completed" if adaptive_state.completed else "accepted_prefix",
                increment_attempts=adaptive_state.attempts)
        result = self._programme_result(result, self._programme, factors[-1], pattern)
        result = self._body_result(result, trial, factors[-1])
        if self._body is not None and np.any(pattern):
            raise ValueError("body checkpoint contains an undeclared nodal load")
        self._adaptive_state = adaptive_state
        self._state = trial
        self._pattern = pattern if self._programme is None else None
        self._applied_load = None if self._programme is None else pattern
        self._shell_predecessors = shell_origins
        if native_shell:
            self._shell_predecessor_q = origin_q
            self._shell_predecessor_anchors = origin_anchors
        self._shell_origins = shell_accepted if shell_material else shell_next
        self._beam_predecessors = beam_origins
        self._beam_origins = beam_accepted if native_material else beam_origins if material else beam_next
        self._load_factor = factors[-1]
        self._accepted_factors = tuple(factors)
        self._accepted = result
        owner._generation = result.generation
        return result
