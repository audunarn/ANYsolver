"""Deformable-target contact cycle with a checkpoint at the open state."""

import numpy as np

from anysolver import solve_static_nonlinear
from anysolver.general_contact.core import suspend_contact
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_free_target_press_probe import (
    build_free_target_case,
)


def _case():
    return build_free_target_case(
        4, steps_per_segment=2, four_phase=True,
        enforcement_solver="monolithic_active_set",
    )


def _solve(*, stop=None, checkpoint=None, snapshots=False):
    model, definition, settings, program = _case()
    kwargs = {"max_load_factor": stop} if stop is not None else {}
    return solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True, restart_checkpoint=checkpoint,
        record_increment_snapshots=snapshots,
        **kwargs,
    )


def _check_target_clamp_wrench(model, manager, snapshot, record, support):
    certificate = record["contact"]
    assert certificate["source_pressure_node_ids"] == list(
        manager.law.pressure_mode_ids)
    support_area = np.asarray(certificate["reference_support_m2"])
    pressure = np.asarray(certificate["numerical_pressure_pa"])
    contact = linearize(manager, snapshot.displacements,
                        pressure*support_area, tangent=False)
    np.testing.assert_allclose(contact.state.pressure, pressure,
                               rtol=1e-9, atol=1e-12)
    with suspend_contact():
        internal, _K, _states = _assemble_nonlinear_system(
            model, snapshot.displacements, snapshot.element_states, 5,
            tangent=False, kinematics="von_karman",
            require_full_coordinates=True,
        )
    residual = internal + contact.force
    clamp_force = np.zeros(3)
    clamp_moment = np.zeros(3)
    clamp_components = np.zeros(6)
    for node in (manager.law.target_node_ids[0],
                 manager.law.target_node_ids[-1]):
        dofs = model.mesh.dof_manager.get_node_dofs(node)
        reaction = residual[dofs]
        reference = model.mesh.nodes[node]
        current = (np.array((reference.x, reference.y, reference.z))
                   + snapshot.displacements[dofs[:3]])
        clamp_components += reaction
        clamp_force += reaction[:3]
        clamp_moment += np.cross(current, reaction[:3]) + reaction[3:6]
    np.testing.assert_allclose(clamp_components, support["target_left_clamp"],
                               rtol=0.0, atol=1e-12)
    target_force = np.zeros(3)
    target_moment = np.zeros(3)
    for node in manager.law.target_node_ids:
        dofs = model.mesh.dof_manager.get_node_dofs(node)
        reference = model.mesh.nodes[node]
        current = (np.array((reference.x, reference.y, reference.z))
                   + snapshot.displacements[dofs[:3]])
        physical = -contact.force[dofs]
        target_force += physical[:3]
        target_moment += np.cross(current, physical[:3]) + physical[3:6]
    force_scale = max(np.linalg.norm(target_force), 1e-8)
    moment_scale = max(np.linalg.norm(target_moment),
                       1.3*np.linalg.norm(target_force), 1e-8)
    assert np.linalg.norm(clamp_force + target_force)/force_scale < 1e-6
    assert np.linalg.norm(clamp_moment + target_moment)/moment_scale < 1e-6


def test_free_target_press_slide_open_recontact_split_restart():
    full = _solve(snapshots=True)
    assert full.status == "completed"
    assert len(full.steps) == 8
    model, definition, settings, program = _case()
    manager = GeneralS3PatchManager(model, definition, settings)
    history = full.info["force_displacement_history"]
    assert [snapshot.step_index for snapshot in full.snapshots] == list(range(1, 9))
    assert history[1]["contact"]["integration_force"][2] > 0.0
    assert history[5]["contact"]["active_pressure_dofs"] == 0
    assert history[5]["contact"]["minimum_gap"] > 0.0
    assert history[6]["contact"]["integration_force"][2] > 0.0
    for row in history:
        source = np.asarray(row["contact"]["integration_force"])
        target = np.asarray(row["contact"]["target_force"])
        np.testing.assert_allclose(source+target, 0.0, atol=1e-9)
        source_moment = np.asarray(row["contact"]["integration_moment"])
        target_moment = np.asarray(row["contact"]["target_moment"])
        np.testing.assert_allclose(source_moment+target_moment, 0.0, atol=1e-9)
        assert row["contact"]["gap_tolerance_met"]
        assert row["complementarity_relative_force"] <= 1e-8
        step = int(row["step_index"])
        support = full.steps[step-1].support_reactions
        assert abs(support["target_left_clamp"][2]-source[2]) <= 3e-7
        external_z = float(np.sum(program.force_values_at(step)))
        assert abs(sum(values[2] for values in support.values())
                   + external_z) <= 3e-7
        _check_target_clamp_wrench(model, manager, full.snapshots[step-1],
                                   row, support)

    opened = _solve(stop=0.75, snapshots=True)
    assert opened.status == "completed"
    assert len(opened.steps) == 6
    assert [snapshot.step_index for snapshot in opened.snapshots] == list(range(1, 7))
    assert opened.info["force_displacement_history"][-1]["contact"][
        "active_pressure_dofs"] == 0
    resumed = _solve(checkpoint=opened.to_restart_checkpoint(), snapshots=True)
    assert resumed.status == "completed"
    assert [snapshot.step_index for snapshot in resumed.snapshots] == [7, 8]
    np.testing.assert_array_equal(resumed.snapshots[-1].displacements,
                                  full.snapshots[-1].displacements)
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=0.0, atol=1e-10)
    np.testing.assert_allclose(
        resumed.info["general_contact"]["integration_force"],
        full.info["general_contact"]["integration_force"],
        rtol=0.0, atol=1e-10,
    )
