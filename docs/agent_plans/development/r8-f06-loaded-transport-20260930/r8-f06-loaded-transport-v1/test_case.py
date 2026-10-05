"""Loaded point-owner chart transport; prospective coverage, not qualification.

The accepted straight panel is driven by a physical tip force couple and beam
transverse force. This differs from the retained unsuccessful curved-arc case.
The finite owner keeps one immutable dead-load pattern. Actual accepted physical
increments must demonstrate noncommutation; chart shadows are never replayed.
"""

from dataclasses import asdict, is_dataclass, replace
from hashlib import sha256

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver import stiffened_shell
from anysolver._stiffened_shell_ge_checkpoint_binary import CHART_MAGIC
from anysolver.e4_pl_s3_state import canonical_json_bytes
from test_stiffened_shell_ge_experimental import _panel


LENGTH = 2.0
BENDING_FORCE = 400_000.0  # N at the beam tip, in global z.
COUPLE_FORCE = 150_000.0  # Opposite z forces, separated by the 1 m shell width.
FORCE_SCALE = BENDING_FORCE + 2.0 * COUPLE_FORCE
MOMENT_SCALE = FORCE_SCALE * LENGTH
PREFIX_FACTORS = (0.125, 0.5)
FINAL_FACTOR = 1.0
ROTATION_FLOOR = 0.05
COMMUTATOR_FLOOR = 1e-5


def _fixture(triangles):
    base = _panel()
    shell = base.shell
    if triangles:
        shell = replace(shell, q4_elements=(),
                        s3_elements=((1, 2, 5), (1, 5, 4),
                                     (2, 3, 6), (2, 6, 5)))
    return replace(
        base, shell=shell,
        q4_pullback_policy=("historical_corotational" if triangles else
                            stiffened_shell.Q4_ALGORITHMIC_PULLBACK_V1))


def _actions():
    # Translation forces only: no unsupported finite nodal moment is requested.
    # The shell pair supplies a genuine global-x couple; beam force bends in y.
    return (
        stiffened_shell.NodalAction("beam", 105,
                                   (0., 0., BENDING_FORCE, 0., 0., 0.)),
        stiffened_shell.NodalAction("shell", 3,
                                   (0., 0., -COUPLE_FORCE, 0., 0., 0.)),
        stiffened_shell.NodalAction("shell", 6,
                                   (0., 0., COUPLE_FORCE, 0., 0., 0.)),
    )


def _plain(value):
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _snapshot(owner):
    driver, result = owner._finite_driver, owner.recover()
    state = driver._state
    reference = np.asarray(owner._definition.shell.coordinates_m)
    rows = state.q[:owner._shell_count].reshape(-1, 6)
    shell_positions = reference + rows[:, :3]
    # Independent physical reconstruction, not the production chart helper.
    shell_frames = Rotation.from_rotvec(rows[:, 3:].copy()).as_matrix()
    if state.shell_anchors is not None:
        shell_frames = shell_frames @ state.shell_anchors
    beam_reference = np.array([owner._beam_nodes[n][0] for n in owner._beam_ids])
    beam_reference_frames = np.array([owner._beam_nodes[n][1] for n in owner._beam_ids])
    beam_positions = result.beam_positions.copy()
    gaps = []
    for point in owner._definition.points:
        s, b = owner._shell_index[point.shell_node], owner._beam_index[point.beam_node]
        rs, rb = shell_frames[s], result.beam_frames[b]
        translation = rs.T @ (beam_positions[b] - shell_positions[s])
        translation -= beam_reference[b] - reference[s]
        orientation = Rotation.from_matrix(
            beam_reference_frames[b].T @ rs.T @ rb).as_rotvec()
        gaps.append(np.r_[translation, orientation])
    support = result.support_reactions[:owner._shell_count].reshape(-1, 6).copy()
    applied_force, applied_moment, potential = np.zeros(3), np.zeros(3), 0.
    for action in _actions():
        if action.domain == "shell":
            index = owner._shell_index[action.node]
            position, initial = shell_positions[index], reference[index]
        else:
            index = owner._beam_index[action.node]
            position, initial = beam_positions[index], beam_reference[index]
        force = result.load_factor * np.asarray(action.wrench[:3])
        applied_force += force
        applied_moment += np.cross(position, force)
        potential -= float(force @ (position - initial))
    reaction_force = support[:, :3].sum(axis=0)
    reaction_moment = (support[:, 3:] +
                       np.cross(shell_positions, support[:, :3])).sum(axis=0)
    fixed = [owner._shell_index[n] for n in (1, 4)]
    assert result.status == "completed"
    assert result.free_equilibrium_ratio <= 1e-8
    assert result.constraint_max <= 1e-9
    assert np.max(np.abs(gaps) / np.array((LENGTH,) * 3 + (1.,) * 3)) <= 1e-9
    assert np.linalg.norm(reaction_force + applied_force) / FORCE_SCALE <= 1e-8
    assert np.linalg.norm(reaction_moment + applied_moment) / MOMENT_SCALE <= 1e-8
    np.testing.assert_allclose(shell_positions[fixed], reference[fixed], rtol=0., atol=1e-12)
    np.testing.assert_allclose(shell_frames[fixed],
                               np.broadcast_to(np.eye(3), shell_frames[fixed].shape),
                               rtol=0., atol=1e-12)
    for frames in (shell_frames, result.beam_frames, result.cell_frames.reshape(-1, 3, 3)):
        np.testing.assert_allclose(
            frames @ frames.transpose(0, 2, 1),
            np.broadcast_to(np.eye(3), frames.shape), rtol=0., atol=1e-9)
        assert np.all(np.linalg.det(frames) > 0.)
    assert np.max(np.linalg.norm(rows[:, 3:], axis=1)) < .9 * np.pi
    assert len(result.point_wrenches) == len(owner._definition.points)
    materials = canonical_json_bytes(_plain((driver._shell_origins, driver._beam_origins)))
    return dict(
        shell_positions=shell_positions, shell_frames=shell_frames,
        beam_positions=beam_positions, beam_frames=result.beam_frames.copy(),
        cell_frames=result.cell_frames.copy(), resultants=result.cell_resultants.copy(),
        multipliers=result.multipliers.copy(), support=support,
        gaps=np.asarray(gaps), potential=potential,
        point_actions=np.array([record.shell_action + record.beam_action
                                for record in result.point_wrenches]),
        material_sha256=sha256(materials).hexdigest(),
        accepted_factors=result.accepted_factors,
        coordinate_scale=owner._coordinate_scale.copy(),
        constraint_scale=owner._constraint_scale.copy(),
    )


def _assert_same_physical(left, right):
    assert left["accepted_factors"] == right["accepted_factors"]
    assert left["material_sha256"] == right["material_sha256"]
    for name in ("shell_positions", "beam_positions"):
        np.testing.assert_allclose(left[name] / LENGTH, right[name] / LENGTH,
                                   rtol=0., atol=1e-9)
    for name in ("shell_frames", "beam_frames", "cell_frames", "gaps"):
        np.testing.assert_allclose(left[name], right[name], rtol=0., atol=1e-9)
    wrench_scale = np.array((FORCE_SCALE,) * 3 + (MOMENT_SCALE,) * 3)
    for name in ("resultants", "multipliers", "support", "point_actions"):
        np.testing.assert_allclose(left[name].reshape(-1, 6) / wrench_scale,
                                   right[name].reshape(-1, 6) / wrench_scale,
                                   rtol=0., atol=1e-9)
    assert abs(left["potential"] - right["potential"]) / MOMENT_SCALE <= 1e-8
    for name in ("coordinate_scale", "constraint_scale"):
        np.testing.assert_array_equal(left[name], right[name])


def _coverage(history, domain):
    frames = [np.tile(np.eye(3), (len(history[0][domain]), 1, 1))]
    frames.extend(item[domain] for item in history)
    rotation = max(float(np.max(Rotation.from_matrix(
        made @ frames[0].transpose(0, 2, 1)).magnitude())) for made in frames[1:])
    increments = [b @ a.transpose(0, 2, 1) for a, b in zip(frames, frames[1:])]
    commutator = max(float(np.max(Rotation.from_matrix(
        b @ a @ b.transpose(0, 2, 1) @ a.transpose(0, 2, 1)).magnitude()))
        for a, b in zip(increments, increments[1:]))
    return rotation, commutator


@pytest.mark.parametrize("triangles", (False, True), ids=("selected-q4", "all-s3"))
def test_loaded_noncommuting_point_chart_reset_restore_continue(triangles, record_property, request):
    definition = _fixture(triangles)
    control = stiffened_shell.create_analysis(definition=definition)
    request.addfinalizer(control.close)
    history = []
    for factor in PREFIX_FACTORS:
        result = control.solve(_actions(), (factor,), max_iterations=20, max_backtracks=12)
        assert result.accepted_factors == PREFIX_FACTORS[:len(history) + 1]
        history.append(_snapshot(control))
    prefix = control.checkpoint()
    rebased = stiffened_shell.create_analysis(definition=definition)
    request.addfinalizer(rebased.close)
    rebased.restore(prefix)
    before = _snapshot(rebased)
    _assert_same_physical(history[-1], before)
    driver = rebased._finite_driver
    predecessor, origins = driver._state, (driver._shell_origins, driver._beam_origins)
    result = rebased.rebase_rotations(rebased.recover().generation)
    assert result.generation == control.recover().generation + 1
    assert driver._shell_origins is origins[0] and driver._beam_origins is origins[1]
    for name in ("frames", "cells", "resultants", "multipliers"):
        assert getattr(driver._state, name) is getattr(predecessor, name)
    np.testing.assert_array_equal(result.shell_chart_coordinates.reshape(-1, 6)[:, 3:], 0.)
    np.testing.assert_allclose(result.shell_rotation_anchors, before["shell_frames"],
                               rtol=0., atol=1e-12)
    _assert_same_physical(before, _snapshot(rebased))
    anchored = rebased.checkpoint()
    assert anchored.startswith(CHART_MAGIC)
    resumed = stiffened_shell.create_analysis(definition=definition)
    request.addfinalizer(resumed.close)
    resumed.restore(anchored)
    _assert_same_physical(before, _snapshot(resumed))
    assert control.checkpoint() == prefix
    for owner in (control, rebased, resumed):
        result = owner.solve(_actions(), (FINAL_FACTOR,), max_iterations=20, max_backtracks=12)
        assert result.accepted_factors == PREFIX_FACTORS + (FINAL_FACTOR,)
    final = _snapshot(control)
    _assert_same_physical(final, _snapshot(rebased))
    _assert_same_physical(final, _snapshot(resumed))
    for branch, last in (("control", final), ("reset", _snapshot(rebased)),
                         ("restored", _snapshot(resumed))):
        for domain in ("shell_frames", "beam_frames"):
            rotation, commutator = _coverage(history + [last], domain)
            record_property(f"{branch}_{domain}_rotation_rad", rotation)
            record_property(f"{branch}_{domain}_commutator_rad", commutator)
            assert rotation >= ROTATION_FLOOR, (branch, domain, rotation)
            assert commutator >= COMMUTATOR_FLOOR, (branch, domain, commutator)
