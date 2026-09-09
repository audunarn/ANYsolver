"""Produce deterministic raw evidence for the private GE-Beam3 P2 gate.

The producer deliberately makes no scientific pass/fail decision.  It executes
the frozen production candidate and serializes raw binary64 values so the
separately authored checker can reconstruct every comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from scipy.linalg import eig, eigh

from anysolver._native_rotation_state import (
    NativeRotationStateStore,
    create_native_rotation_state_store,
    rotation_exponential,
)
from anysolver.beam_sections import GeneralizedBeamSection
from anysolver.fe_core import FEModel
from anysolver.ge_beam3_mixed_element import (
    GE_BEAM3_MIXED_CANDIDATE_ID,
    GeometricallyExactBeam3D3NElement,
)
from anysolver.ge_beam3_mixed_state import (
    deserialize_ge_beam3_mixed_state,
    serialize_ge_beam3_mixed_state,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = Path(__file__).resolve().parent
STUDY_ID = "study_ge_beam3.mixed_straight_solver_parity_v1"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
SCHEMA = "anysolver.ge-beam3-mixed-p2-proof-v1"
TERMINAL = "NONCLASSIFYING_GE_BEAM3_P2_PROOF_COMPLETE"
CASES_PATH = REFERENCE / "ge_beam3_mixed_p2_cases.json"
CORRECTION_PATH = REFERENCE / "ge_beam3_mixed_p2_recovery_correction.json"

BOUND_INPUTS = (
    "ge_beam3_mixed_p2_baseline.json",
    "ge_beam3_mixed_p2_cases.json",
    "ge_beam3_mixed_p2_contract.json",
    "ge_beam3_mixed_p2_independent_reference.py",
    "ge_beam3_mixed_p2_plan_review.json",
    "ge_beam3_mixed_p2_state_schema.json",
    "ge_beam3_mixed_p2_recovery_correction.json",
    "ge_beam3_mixed_p2_recovery_correction_contract.json",
    "ge_beam3_mixed_p2_recovery_correction_reference.py",
    "ge_beam3_mixed_p2_recovery_correction_review.json",
)
DOF = {name: index for index, name in enumerate(("ux", "uy", "uz", "rx", "ry", "rz"))}


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _reject_constant(token: str) -> None:
    raise ValueError(f"nonfinite JSON token: {token}")


def _load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return raw, value


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite value in canonical record")
    if isinstance(value, Mapping):
        for child in value.values():
            _finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _finite(child)


def canonical_bytes(value: Any) -> bytes:
    _finite(value)
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _typed(value: Any) -> dict[str, Any]:
    array = np.ascontiguousarray(np.asarray(value, dtype="<f8"))
    return {
        "data_hex": array.tobytes().hex().upper(),
        "dtype": "<f8",
        "shape": list(array.shape),
    }


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _floats(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=np.float64)


def _records_by_id(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(record[key]): record for record in records}


def _pack(translations: Any, rotations: Any) -> np.ndarray:
    made = np.empty((3, 6), dtype=np.float64)
    made[:, :3] = _floats(translations)
    made[:, 3:] = _floats(rotations)
    return made.reshape(18)


class _Context:
    def __init__(self, cases: dict[str, Any], correction: dict[str, Any]) -> None:
        self.manifest = cases
        self.correction = correction
        groups = cases["cases"]
        self.groups = groups
        self.geometry = _records_by_id(groups["geometry"], "geometry_id")
        self.sections = _records_by_id(groups["sections"], "section_id")
        self.solver = _records_by_id(groups["solver_state"], "case_id")
        self.loads = _records_by_id(groups["loads"], "case_id")
        self.mass = _records_by_id(groups["mass"], "case_id")
        self.modal = _records_by_id(groups["modal"], "case_id")
        self.buckling = _records_by_id(groups["buckling"], "case_id")
        self.recovery = _records_by_id(groups["recovery_states"], "case_id")
        replacement = correction["replacement"]
        self.recovery[str(replacement["case_id"])] = replacement
        self.recovery.pop("RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE", None)

    def section(self, section_id: str, *, with_mass: bool = True) -> GeneralizedBeamSection:
        record = self.sections[section_id]
        return GeneralizedBeamSection(
            stiffness=_floats(record["stiffness_matrix"]),
            mass_matrix=(
                _floats(record["mass_matrix_per_reference_length"])
                if with_mass
                else None
            ),
            name=section_id,
        )

    def element(
        self,
        geometry_id: str,
        section_id: str = "STEEL_DIAGONAL",
        *,
        with_mass: bool = True,
        element_id: int = 1,
    ) -> tuple[FEModel, GeometricallyExactBeam3D3NElement]:
        geometry = self.geometry[geometry_id]
        model = FEModel(f"ge-beam3-p2-proof-{geometry_id.lower()}")
        model.add_material("mat", 210.0e9, 0.3, density=7850.0)
        for node_id, coordinates in zip(geometry["connectivity"], geometry["nodes"]):
            model.add_node(int(node_id), *map(float, coordinates))
        element = GeometricallyExactBeam3D3NElement(
            element_id,
            geometry["connectivity"],
            "mat",
            section=self.section(section_id, with_mass=with_mass),
            reference_orientation=_floats(geometry["reference_orientation"]),
            reference_axis_direction=_floats(geometry["reference_axis_direction"]),
        )
        return model, element


def _store(
    element: GeometricallyExactBeam3D3NElement,
    model: FEModel,
    committed_u: np.ndarray,
    operators: Any,
) -> NativeRotationStateStore:
    nodes = tuple(int(node) for node in element.node_ids)
    reference = element.get_node_coordinates(model.mesh)
    total = np.asarray(committed_u, dtype=np.float64).reshape(3, 6)
    made = create_native_rotation_state_store(
        nodes,
        rotational_dofs={node: (6 * row + 3, 6 * row + 4, 6 * row + 5) for row, node in enumerate(nodes)},
        coordinate_rows={node: row for row, node in enumerate(nodes)},
        committed_full_displacement=total.reshape(18),
        committed_full_coordinates=reference + total[:, :3],
        committed_rotation_matrices=np.asarray(operators, dtype=np.float64),
        coordinate_node_ids=nodes,
    )
    if not isinstance(made, NativeRotationStateStore):
        raise TypeError("native rotation store was not constructed")
    return made


def _trial_coordinates(
    element: GeometricallyExactBeam3D3NElement,
    model: FEModel,
    trial_u: np.ndarray,
) -> np.ndarray:
    return element.get_node_coordinates(model.mesh) + trial_u.reshape(3, 6)[:, :3]


def _evaluate_trial(
    element: GeometricallyExactBeam3D3NElement,
    model: FEModel,
    store: NativeRotationStateStore,
    state: Mapping[str, Any],
    trial_u: np.ndarray,
    *,
    tangent: bool,
) -> tuple[np.ndarray, np.ndarray | None, dict[str, Any]]:
    coordinates = _trial_coordinates(element, model, trial_u)
    with store.candidate(trial_u, coordinates) as candidate:
        view = candidate.element_view(
            int(element.element_id),
            element.node_ids,
            element.native_reference_directors(model.mesh),
        )
        force, matrix, trial_state = element.compute_nonlinear_response(
            model.mesh,
            model.get_material("mat"),
            trial_u,
            state,
            1,
            tangent,
            native_rotation_trial=view,
        )
    return np.asarray(force), None if matrix is None else np.asarray(matrix), trial_state


def _commit_trial(
    element: GeometricallyExactBeam3D3NElement,
    model: FEModel,
    store: NativeRotationStateStore,
    state: Mapping[str, Any],
    trial_u: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    coordinates = _trial_coordinates(element, model, trial_u)
    with store.candidate(trial_u, coordinates) as candidate:
        view = candidate.element_view(
            int(element.element_id),
            element.node_ids,
            element.native_reference_directors(model.mesh),
        )
        force, matrix, trial_state = element.compute_nonlinear_response(
            model.mesh,
            model.get_material("mat"),
            trial_u,
            state,
            1,
            True,
            native_rotation_trial=view,
        )
        if matrix is None:
            raise RuntimeError("trial tangent missing")
        candidate.commit(trial_u, coordinates)
    return np.asarray(force), np.asarray(matrix), trial_state


def _solver_chart_record(context: _Context) -> dict[str, Any]:
    case = context.solver["NONZERO_SOLVER_CHART"]
    model, element = context.element(case["geometry_id"], case["section_id"])
    committed_u = _pack(case["committed_translations"], case["committed_rotation_coordinates"])
    trial_u = _pack(case["trial_translations"], case["trial_rotation_coordinates"])
    operators = _floats(case["committed_spatial_operators"])
    state = element._state_from_configuration(model.mesh, committed_u, operators)
    store = _store(element, model, committed_u, operators)
    force, tangent, _trial = _evaluate_trial(element, model, store, state, trial_u, tangent=True)
    if tangent is None:
        raise RuntimeError("solver-chart tangent missing")
    direction = _floats(case["direction"]).reshape(18)
    direction /= np.linalg.norm(direction)
    step = 2.0e-6
    plus, _, _ = _evaluate_trial(element, model, store, state, trial_u + step * direction, tangent=False)
    minus, _, _ = _evaluate_trial(element, model, store, state, trial_u - step * direction, tangent=False)
    return {
        "case_id": case["case_id"],
        "analytic_directional_force": _typed(tangent @ direction),
        "base_force": _typed(force),
        "direction": _typed(direction),
        "minus_force": _typed(minus),
        "plus_force": _typed(plus),
        "step": step.hex(),
        "tangent": _typed(tangent),
    }


def _rotation_composition_record(context: _Context) -> dict[str, Any]:
    case = context.solver["TWO_NONCOMMUTING_COMMITS"]
    model, element = context.element(case["geometry_id"], case["section_id"])
    zero = np.zeros(18)
    initial = _floats(case["initial_spatial_operators"])
    increments = [_floats(value) for value in case["increments"]]

    def committed(order: tuple[int, int]) -> np.ndarray:
        store = _store(element, model, zero, initial)
        accumulated = np.zeros((3, 3))
        for index in order:
            accumulated += increments[index]
            u = _pack(np.zeros((3, 3)), accumulated)
            coordinates = _trial_coordinates(element, model, u)
            with store.candidate(u, coordinates) as candidate:
                candidate.commit(u, coordinates)
        return np.asarray(store.committed_rotation_matrices)

    continuous = committed((0, 1))
    split = _store(element, model, _pack(np.zeros((3, 3)), increments[0]), np.asarray([
        rotation_exponential(increments[0][node]) @ initial[node] for node in range(3)
    ]))
    final_u = _pack(np.zeros((3, 3)), increments[0] + increments[1])
    coordinates = _trial_coordinates(element, model, final_u)
    with split.candidate(final_u, coordinates) as candidate:
        candidate.commit(final_u, coordinates)
    return {
        "case_id": case["case_id"],
        "continuous": _typed(continuous),
        "increments": [_typed(value) for value in increments],
        "initial": _typed(initial),
        "opposite": _typed(committed((1, 0))),
        "split": _typed(split.committed_rotation_matrices),
    }


def _rollback_record(context: _Context) -> dict[str, Any]:
    case = context.solver["REJECTED_TRIAL_ROLLBACK_AND_CUTBACK"]
    model, element = context.element(case["geometry_id"], case["section_id"])
    identity = np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    zero = np.zeros(18)
    store = _store(element, model, zero, identity)
    state = element.init_model_bound_nonlinear_state(model.mesh, model.get_material("mat"), 1)
    accepted = _pack(case["accepted_translations"], case["accepted_rotation_coordinates"])
    _, _, accepted_state = _commit_trial(element, model, store, state, accepted)
    before_u = np.array(store.committed_full_displacement, copy=True)
    before_q = np.array(store.committed_rotation_matrices, copy=True)
    before_state = serialize_ge_beam3_mixed_state(accepted_state)
    rejected = _pack(case["rejected_translations"], case["rejected_rotation_coordinates"])
    exception = "NONE"
    try:
        _evaluate_trial(element, model, store, accepted_state, rejected, tangent=True)
    except Exception as exc:  # execution fact, adjudicated independently
        exception = type(exc).__name__
    after_state = serialize_ge_beam3_mixed_state(accepted_state)
    cutback = accepted + 0.05 * (rejected - accepted)
    coordinates = _trial_coordinates(element, model, cutback)
    with store.candidate(cutback, coordinates) as candidate:
        view = candidate.element_view(
            int(element.element_id), element.node_ids, element.native_reference_directors(model.mesh)
        )
        cutback_increment = np.asarray(view.rotation_coordinate_increment)
        cutback_base = np.asarray(view.committed_rotation_matrices)
    return {
        "after_operators": _typed(store.committed_rotation_matrices),
        "after_state_hex": after_state.hex().upper(),
        "after_u": _typed(store.committed_full_displacement),
        "before_operators": _typed(before_q),
        "before_state_hex": before_state.hex().upper(),
        "before_u": _typed(before_u),
        "case_id": case["case_id"],
        "cutback_base": _typed(cutback_base),
        "cutback_increment": _typed(cutback_increment),
        "exception_class": exception,
    }


def _restart_record(context: _Context) -> dict[str, Any]:
    case = context.solver["SPLIT_RESTART_IDENTITY"]
    model, element = context.element(case["geometry_id"], case["section_id"])
    identity = np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    zero = np.zeros(18)
    increments = [_pack(item["translations"], item["rotations"]) for item in case["increments"]]
    first_u = increments[0]
    final_u = increments[0] + increments[1]

    continuous_store = _store(element, model, zero, identity)
    continuous_state = element.init_model_bound_nonlinear_state(model.mesh, model.get_material("mat"), 1)
    _, _, continuous_state = _commit_trial(element, model, continuous_store, continuous_state, first_u)
    continuous_force, continuous_tangent, continuous_final = _commit_trial(
        element, model, continuous_store, continuous_state, final_u
    )

    split_store = _store(element, model, zero, identity)
    split_state = element.init_model_bound_nonlinear_state(model.mesh, model.get_material("mat"), 1)
    _, _, split_state = _commit_trial(element, model, split_store, split_state, first_u)
    checkpoint = serialize_ge_beam3_mixed_state(split_state)
    restarted_state = deserialize_ge_beam3_mixed_state(checkpoint)
    restarted_store = _store(
        element,
        model,
        np.asarray(restarted_state["committed_total_u"]),
        np.asarray(restarted_state["committed_nodal_rotation_matrices"]),
    )
    split_force, split_tangent, split_final = _commit_trial(
        element, model, restarted_store, restarted_state, final_u
    )
    return {
        "case_id": case["case_id"],
        "checkpoint_hex": checkpoint.hex().upper(),
        "continuous_final_hex": serialize_ge_beam3_mixed_state(continuous_final).hex().upper(),
        "continuous_force": _typed(continuous_force),
        "continuous_tangent": _typed(continuous_tangent),
        "roundtrip_hex": serialize_ge_beam3_mixed_state(restarted_state).hex().upper(),
        "split_final_hex": serialize_ge_beam3_mixed_state(split_final).hex().upper(),
        "split_force": _typed(split_force),
        "split_tangent": _typed(split_tangent),
    }


def _shared_node_record(context: _Context) -> dict[str, Any]:
    case = context.solver["SHARED_NODE_DISTINCT_MATERIAL_TRIADS"]
    model = FEModel("ge-beam3-p2-proof-shared")
    model.add_material("mat", 210.0e9, 0.3, density=7850.0)
    for node, x in enumerate((0.0, 0.5, 1.0, 1.5, 2.0), start=1):
        model.add_node(node, x, 0.0, 0.0)
    section = context.section(case["section_id"])
    first = GeometricallyExactBeam3D3NElement(
        1, case["elements"][0]["node_ids"], "mat", section=section,
        reference_orientation=(0.0, 1.0, 0.0), reference_axis_direction=(1.0, 0.0, 0.0),
    )
    second = GeometricallyExactBeam3D3NElement(
        2, case["elements"][1]["node_ids"], "mat", section=section,
        reference_orientation=(0.0, 0.0, 1.0), reference_axis_direction=(1.0, 0.0, 0.0),
    )
    nodes = (1, 2, 3, 4, 5)
    zero = np.zeros(30)
    coordinates = np.asarray([model.mesh.get_node(node).coords() for node in nodes])
    store = create_native_rotation_state_store(
        nodes,
        rotational_dofs={node: (6 * row + 3, 6 * row + 4, 6 * row + 5) for row, node in enumerate(nodes)},
        coordinate_rows={node: row for row, node in enumerate(nodes)},
        committed_full_displacement=zero,
        committed_full_coordinates=coordinates,
        committed_rotation_matrices=np.repeat(np.eye(3)[None, :, :], 5, axis=0),
        coordinate_node_ids=nodes,
    )
    increment = _floats(case["shared_node_increment"])
    trial = zero.copy()
    trial[12 + 3 : 12 + 6] = increment
    with store.candidate(trial, coordinates) as candidate:
        view_a = candidate.element_view(1, first.node_ids, first.native_reference_directors(model.mesh))
        view_b = candidate.element_view(2, second.node_ids, second.native_reference_directors(model.mesh))
        shared_a = np.asarray(view_a.trial_rotation_matrices)[2]
        shared_b = np.asarray(view_b.trial_rotation_matrices)[0]
        absolute_a = shared_a @ first.reference_triad(model.mesh)
        absolute_b = shared_b @ second.reference_triad(model.mesh)
    return {
        "absolute_frame_first": _typed(absolute_a),
        "absolute_frame_second": _typed(absolute_b),
        "case_id": case["case_id"],
        "shared_operator_first": _typed(shared_a),
        "shared_operator_second": _typed(shared_b),
    }


def _reversal_record(context: _Context) -> dict[str, Any]:
    case = context.solver["CONNECTIVITY_REVERSAL_STATE"]
    model_f, forward = context.element(case["forward_geometry_id"], case["section_id"])
    model_r, reverse = context.element(case["reversed_geometry_id"], case["section_id"])
    uf = _pack(case["forward_translations"], case["forward_rotation_coordinates"])
    ur = uf.reshape(3, 6)[::-1].reshape(18)
    identity = np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    def evaluate(
        model: FEModel,
        element: GeometricallyExactBeam3D3NElement,
        displacement: np.ndarray,
    ) -> tuple[float, np.ndarray, np.ndarray, dict[str, Any]]:
        store = _store(element, model, np.zeros(18), identity)
        coordinates = _trial_coordinates(element, model, displacement)
        with store.candidate(displacement, coordinates) as candidate:
            view = candidate.element_view(
                int(element.element_id),
                element.node_ids,
                element.native_reference_directors(model.mesh),
            )
            energy, force, tangent, fields, _total = element._evaluate_solver_chart(
                model.mesh, displacement, view, tangent=True
            )
        if tangent is None:
            raise RuntimeError("reversal tangent missing")
        return energy, force, tangent, fields

    energy_f, ff, kf, state_f = evaluate(model_f, forward, uf)
    energy_r, fr, kr, state_r = evaluate(model_r, reverse, ur)
    permutation = np.zeros((18, 18))
    for reverse_node, forward_node in enumerate((2, 1, 0)):
        permutation[6 * reverse_node : 6 * reverse_node + 6, 6 * forward_node : 6 * forward_node + 6] = np.eye(6)
    return {
        "case_id": case["case_id"],
        "forward_energy": float(energy_f).hex(),
        "forward_force": _typed(ff),
        "forward_strain": _typed(state_f["generalized_strain"]),
        "forward_resultant": _typed(state_f["generalized_resultant"]),
        "forward_tangent": _typed(kf),
        "permutation": _typed(permutation),
        "reverse_force": _typed(fr),
        "reverse_energy": float(energy_r).hex(),
        "reverse_strain": _typed(state_r["generalized_strain"]),
        "reverse_resultant": _typed(state_r["generalized_resultant"]),
        "reverse_tangent": _typed(kr),
        "strain_map": _typed(forward.REVERSAL_STRAIN_MAP),
    }


def _solver_records(context: _Context) -> list[dict[str, Any]]:
    return [
        _solver_chart_record(context),
        _rotation_composition_record(context),
        _rollback_record(context),
        _restart_record(context),
        _shared_node_record(context),
        _reversal_record(context),
    ]


def _load_record(context: _Context, case: dict[str, Any]) -> dict[str, Any]:
    geometry = context.geometry[case["geometry_id"]]
    coordinates = _floats(geometry["nodes"])
    if case["case_id"] == "TIP_NODAL_SPATIAL_DEAD":
        vector = np.zeros(18)
        index = int(case["node_local_index"])
        vector[6 * index : 6 * index + 3] = _floats(case["force"])
        vector[6 * index + 3 : 6 * index + 6] = _floats(case["moment"])
        route = "EXISTING_NODAL_SPATIAL_DEAD_INPUT"
    elif "FOLLOWER" in case["classification"]:
        model, element = context.element(case["geometry_id"])
        mechanics_entries = 0
        original = element.evaluate_candidate
        def counted(*args: Any, **kwargs: Any) -> Any:
            nonlocal mechanics_entries
            mechanics_entries += 1
            return original(*args, **kwargs)
        element.evaluate_candidate = counted  # type: ignore[method-assign]
        exception = "NONE"
        try:
            element.compute_reference_line_load(
                model.mesh,
                {
                    "classification": case["classification"],
                    "force_per_reference_length_at_nodes": (0.0, 1.0, 0.0),
                    "couple_per_reference_length_at_nodes": (0.0, 0.0, 0.0),
                },
            )
        except Exception as exc:
            exception = type(exc).__name__
        return {
            "case_id": case["case_id"],
            "classification": case["classification"],
            "exception_class": exception,
            "mechanics_entry_count": mechanics_entries,
        }
    else:
        model, element = context.element(case["geometry_id"])
        descriptor = {
            key: case[key]
            for key in (
                "classification",
                "force_per_reference_length_at_nodes",
                "couple_per_reference_length_at_nodes",
            )
        }
        vector = np.asarray(element.compute_reference_line_load(model.mesh, descriptor))
        route = "PRIVATE_REFERENCE_LINE_LOAD"
    nodal = vector.reshape(3, 6)
    resultant_force = np.sum(nodal[:, :3], axis=0)
    resultant_moment = np.sum(nodal[:, 3:], axis=0) + np.sum(np.cross(coordinates, nodal[:, :3]), axis=0)
    virtual = _floats(case["virtual_nodal_coordinates"]).reshape(18)
    return {
        "case_id": case["case_id"],
        "classification": case["classification"],
        "coordinates": _typed(coordinates),
        "element_vector": _typed(vector),
        "resultant_force": _typed(resultant_force),
        "resultant_moment": _typed(resultant_moment),
        "route": route,
        "virtual_coordinates": _typed(virtual),
        "virtual_work": float(vector @ virtual).hex(),
    }


def _mass_record(context: _Context, case: dict[str, Any]) -> dict[str, Any]:
    model, element = context.element(case["geometry_id"], case["section_id"])
    matrix = np.asarray(element.compute_mass_matrix(model.mesh, None))
    frame = element.reference_triad(model.mesh)
    block = np.zeros((6, 6))
    block[:3, :3] = frame
    block[3:, 3:] = frame
    velocity = block @ _floats(case["uniform_local_generalized_velocity"])
    nodal_velocity = np.tile(velocity, 3)
    return {
        "case_id": case["case_id"],
        "mass_matrix": _typed(matrix),
        "nodal_velocity": _typed(nodal_velocity),
        "reference_triad": _typed(frame),
        "section_mass": _typed(context.sections[case["section_id"]]["mass_matrix_per_reference_length"]),
    }


def _recovery_record(context: _Context, case: dict[str, Any]) -> dict[str, Any]:
    section_id = case.get("section_id", case.get("section", {}).get("section_id"))
    model, element = context.element(case["geometry_id"], str(section_id))
    displacement = np.zeros((3, 6))
    displacement[:, :3] = _floats(case["nodal_translations"])
    if "vertex_rotation" in case:
        rotation = case["vertex_rotation"]
        angle = float(rotation["radians"]["numerator"] / rotation["radians"]["denominator"])
        vector = _floats(rotation["axis"]) * angle
        rotations = np.repeat(rotation_exponential(vector)[None, :, :], 3, axis=0)
    else:
        rotations = _floats(case["absolute_rotation_matrices"])
    fields = element.recover_native_fields(
        model.mesh, displacement.reshape(18), rotation_matrices=rotations
    )
    return {
        "absolute_rotations": _typed(rotations),
        "candidate_id": fields["candidate_id"],
        "case_id": case["case_id"],
        "fibre_stress_available": fields["fibre_stress_available"],
        "local_strain": _typed(fields["local_generalized_strain"]),
        "local_resultant": _typed(fields["local_generalized_resultant"]),
        "station_frames": _typed(fields["station_frames"]),
        "station_order": list(fields["station_order"]),
    }


def _load_mass_recovery_records(context: _Context) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in context.groups["loads"]:
        records.append(_load_record(context, case))
    for case in context.groups["mass"]:
        records.append(_mass_record(context, case))
    for case_id in (
        "RECOVERY_ZERO_NATIVE_STATE",
        "RECOVERY_UNIFORM_AXIAL_NATIVE_STATE",
        "RECOVERY_MANUFACTURED_UNIFORM_SHEAR_Y_NATIVE_STATE",
        "RECOVERY_TORSION_SIDED_NATIVE_STATE",
    ):
        records.append(_recovery_record(context, context.recovery[case_id]))
    return records


def _chain(context: _Context, macro_count: int) -> tuple[FEModel, list[GeometricallyExactBeam3D3NElement]]:
    model = FEModel(f"ge-beam3-p2-proof-chain-{macro_count}")
    model.add_material("mat", 210.0e9, 0.3, density=7850.0)
    for index in range(2 * macro_count + 1):
        model.add_node(index + 1, index * 3.0 / (2 * macro_count), 0.0, 0.0)
    elements = [
        GeometricallyExactBeam3D3NElement(
            index + 1,
            (2 * index + 1, 2 * index + 2, 2 * index + 3),
            "mat",
            section=context.section("STEEL_DIAGONAL"),
            reference_orientation=(0.0, 1.0, 0.0),
            reference_axis_direction=(1.0, 0.0, 0.0),
        )
        for index in range(macro_count)
    ]
    return model, elements


def _scatter(model: FEModel, elements: list[GeometricallyExactBeam3D3NElement], kind: str) -> np.ndarray:
    made = np.zeros((6 * len(model.mesh.nodes),) * 2)
    for element in elements:
        if kind == "stiffness":
            local = element.compute_candidate_stiffness_matrix(model.mesh)
        elif kind == "mass":
            local = element.compute_mass_matrix(model.mesh, None)
        elif kind == "geometric":
            local = element.compute_reference_geometric_stiffness(model.mesh, axial_compression=1.0)
        else:
            raise ValueError(kind)
        indices = np.asarray([6 * (node - 1) + dof for node in element.node_ids for dof in range(6)])
        made[np.ix_(indices, indices)] += local
    return made


def _modal_record(context: _Context) -> dict[str, Any]:
    case = context.modal["CANTILEVER_REFERENCE_LINEAR"]
    samples: list[dict[str, Any]] = []
    family_dofs = {
        "AXIAL": ("ux",),
        "BENDING_STRONG_Y": ("uz", "ry"),
        "BENDING_WEAK_Z": ("uy", "rz"),
        "TORSION": ("rx",),
    }
    for macro_count in case["macro_element_counts"]:
        model, elements = _chain(context, int(macro_count))
        stiffness = _scatter(model, elements, "stiffness")
        mass = _scatter(model, elements, "mass")
        node_count = 2 * int(macro_count) + 1
        free_values = eigh(stiffness, mass, eigvals_only=True, check_finite=True)
        fixed = set(range(6))
        free = np.asarray([index for index in range(6 * node_count) if index not in fixed])
        values, vectors = eigh(stiffness[np.ix_(free, free)], mass[np.ix_(free, free)], check_finite=True)
        candidates: dict[str, tuple[float, float]] = {}
        for value, reduced in zip(values, vectors.T):
            if value <= 1.0e-12 * max(float(np.max(np.abs(values))), 1.0):
                continue
            full = np.zeros(node_count * 6)
            full[free] = reduced
            full /= math.sqrt(float(full @ mass @ full))
            scores: dict[str, float] = {}
            for family, names in family_dofs.items():
                indices = [6 * node + DOF[name] for node in range(node_count) for name in names]
                part = np.zeros_like(full)
                part[indices] = full[indices]
                scores[family] = float(part @ mass @ part)
            family = max(sorted(scores), key=lambda name: scores[name])
            frequency = math.sqrt(float(value)) / (2.0 * math.pi)
            previous = candidates.get(family)
            if previous is None or frequency < previous[0]:
                candidates[family] = (frequency, scores[family])
        samples.append(
            {
                "family_frequencies_hz": {key: value[0].hex() for key, value in sorted(candidates.items())},
                "family_mass_scores": {key: value[1].hex() for key, value in sorted(candidates.items())},
                "free_body_eigenvalues": _typed(free_values),
                "macro_count": int(macro_count),
            }
        )
    return {"case_id": case["case_id"], "samples": samples}


def _buckling_record(context: _Context, case: dict[str, Any]) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    for macro_count in case["macro_element_counts"]:
        model, elements = _chain(context, int(macro_count))
        stiffness = _scatter(model, elements, "stiffness")
        geometric = _scatter(model, elements, "geometric")
        node_count = 2 * int(macro_count) + 1
        fixed: set[int] = set()
        for node in range(node_count):
            fixed.update(6 * node + DOF[name] for name in case["support"]["fixed_all_nodes"])
        fixed.update(DOF[name] for name in case["support"]["end_1"])
        fixed.update(6 * (node_count - 1) + DOF[name] for name in case["support"]["end_2"])
        free = np.asarray([index for index in range(6 * node_count) if index not in fixed])
        values, _vectors = eig(
            stiffness[np.ix_(free, free)], geometric[np.ix_(free, free)], check_finite=True
        )
        admitted = sorted(
            float(value.real)
            for value in values
            if np.isfinite(value.real)
            and abs(value.imag) <= 1.0e-9 * max(abs(value.real), 1.0)
            and value.real > 0.0
        )
        samples.append({"critical_load": admitted[0].hex(), "macro_count": int(macro_count)})
    return {"case_id": case["case_id"], "samples": samples}


def _route_record(context: _Context) -> dict[str, Any]:
    model, element = context.element("UNIT_X")
    del model
    records = []
    for route in context.manifest["unsupported_routes"]:
        exception = "NONE"
        try:
            element.require_private_analysis_route(route)
        except Exception as exc:
            exception = type(exc).__name__
        records.append({"exception_class": exception, "route": route})
    return {"case_id": "UNSUPPORTED_PRIVATE_ROUTES", "routes": records}


def _modal_buckling_records(context: _Context) -> list[dict[str, Any]]:
    return [
        _modal_record(context),
        *[_buckling_record(context, case) for case in context.groups["buckling"]],
        _route_record(context),
    ]


def build_proof() -> dict[str, Any]:
    cases_raw, cases = _load(CASES_PATH)
    correction_raw, correction = _load(CORRECTION_PATH)
    if cases.get("schema") != "anysolver.ge-beam3-mixed-p2-cases-v1":
        raise ValueError("unexpected P2 case schema")
    if correction.get("schema") != "anysolver.ge-beam3-mixed-p2-recovery-correction-v1":
        raise ValueError("unexpected recovery correction schema")
    if GE_BEAM3_MIXED_CANDIDATE_ID != CANDIDATE_ID:
        raise ValueError("production candidate identity mismatch")
    context = _Context(cases, correction)
    records = {
        "load_mass_recovery": _load_mass_recovery_records(context),
        "modal_buckling": _modal_buckling_records(context),
        "solver_chart_state": _solver_records(context),
    }
    bindings = {}
    for name in BOUND_INPUTS:
        raw = (REFERENCE / name).read_bytes()
        bindings[name] = {"bytes": len(raw), "sha256": _sha(raw)}
    counts = {key: len(value) for key, value in records.items()}
    counts["total"] = sum(counts.values())
    payload = {
        "bindings": bindings,
        "candidate_id": CANDIDATE_ID,
        "counts": counts,
        "effective_recovery_case_ids": sorted(context.recovery),
        "predicates": {
            "producer_scientific_adjudication_present": False,
            "raw_binary64_values_encoded_little_endian": True,
        },
        "records": records,
        "schema": SCHEMA,
        "study_id": STUDY_ID,
        "terminal": TERMINAL,
    }
    payload["content_sha256"] = _sha(canonical_bytes(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"proof output already exists: {args.output}")
    proof = build_proof()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(proof))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
