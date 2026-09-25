"""Physical virtual-work controls for an internal fixed S3 friction pair."""

import numpy as np
import pytest

from anysolver import create_shell_element
from anysolver.fe_core import FEModel
from anysolver.general_contact.friction_point import (
    FrictionPointState, initial_friction_point,
    objective_relative_tangent_increment,
)
from anysolver.general_contact.s3_friction_pair import S3FrictionPointPair
from anysolver.general_contact.s3_friction_point import S3SkinMaterialPoint


def _case(*, maximum_active_columns=72):
    model = FEModel("s3_fixed_material_friction_pair")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    positions = {
        1: (0.4, 0.2, 0.065), 2: (0.9, 0.2, 0.065),
        3: (0.4, 0.7, 0.065), 4: (0.0, 0.0, 0.0),
        5: (1.0, 0.0, 0.0), 6: (0.0, 1.0, 0.0),
    }
    for node, position in positions.items():
        model.add_node(node, *position)
    for element, nodes in ((1, (1, 2, 3)), (2, (4, 5, 6))):
        model.add_element(element, create_shell_element(
            element, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0, 0, 1),
            reference_surface_offset=0.01,
        ))
    source = S3SkinMaterialPoint.from_model(
        model, 1, 1, "bottom", (0.3, 0.3, 0.4),
    )
    target = S3SkinMaterialPoint.from_model(
        model, 2, 2, "top", (0.05, 0.55, 0.4),
    )
    pair = S3FrictionPointPair(
        source, target, reference_weight_m2=0.01,
        friction_coefficient=0.3, tangential_stiffness_Pa_per_m=1.0e9,
        maximum_active_columns=maximum_active_columns,
    )
    committed = np.zeros(model.mesh.dof_manager.total_dofs)
    for node in (1, 2, 3):
        committed[model.mesh.dof_manager.get_node_dofs(node)[2]] = -0.015
    history = initial_friction_point(target.physical_pose(committed).material_frame)
    return model, positions, pair, committed, history


def _translation_mode(model, nodes, component):
    mode = np.zeros(model.mesh.dof_manager.total_dofs)
    for node in nodes:
        mode[model.mesh.dof_manager.get_node_dofs(node)[component]] = 1.0
    return mode


def test_s3_pair_force_is_objective_virtual_work_and_balanced():
    model, positions, pair, committed, history = _case()
    candidate = committed.copy()
    for node in (1, 2, 3):
        candidate[model.mesh.dof_manager.get_node_dofs(node)[0]] += 0.0002
    result = pair.evaluate(committed, candidate, history,
                           normal_pressure_Pa=2.0e6)
    assert result.trial.branch == "stick"
    np.testing.assert_allclose(result.relative_increment,
                               (0.0002, 0.0, 0.0), atol=1e-15)
    np.testing.assert_allclose(result.trial.traction,
                               (-0.2e6, 0.0, 0.0), atol=1e-7)
    source_x = _translation_mode(model, (1, 2, 3), 0)
    target_x = _translation_mode(model, (4, 5, 6), 0)
    assert float(result.structural_force @ source_x) == pytest.approx(-2000.0)
    assert float(result.structural_force @ target_x) == pytest.approx(2000.0)
    for component in range(3):
        common = _translation_mode(model, range(1, 7), component)
        assert abs(float(result.structural_force @ common)) <= 1.0e-8

    direction = np.linspace(-0.03, 0.04, candidate.size)
    old_source = pair.source.physical_pose(committed)
    old_target = pair.target.physical_pose(committed)

    def slip(u):
        new_source = pair.source.physical_pose(u)
        new_target = pair.target.physical_pose(u)
        return np.asarray(objective_relative_tangent_increment(
            source_committed=old_source.position,
            target_committed=old_target.position,
            source_candidate=new_source.position,
            target_candidate=new_target.position,
            target_frame_committed=old_target.material_frame,
            target_frame_candidate=new_target.material_frame,
        ))

    step = 3.0e-6
    finite_work = 0.01 * float(np.asarray(result.trial.traction) @ (
        (slip(candidate + step*direction)
         - slip(candidate - step*direction)) / (2.0*step)
    ))
    assert float(result.structural_force @ direction) == pytest.approx(
        finite_work, rel=1.0e-7, abs=1.0e-7,
    )
    # A common infinitesimal rigid rotation must do no frictional work.
    rotation = np.array((0.0, 0.0, 1.0))
    common_rotation = np.zeros_like(candidate)
    for node, coordinates in positions.items():
        dofs = model.mesh.dof_manager.get_node_dofs(node)
        current_node = np.asarray(coordinates) + candidate[dofs[:3]]
        common_rotation[dofs[:3]] = np.cross(rotation, current_node)
        common_rotation[dofs[3:6]] = rotation
    assert abs(float(result.structural_force @ common_rotation)) <= 1.0e-7
    assert abs(result.structural_force[model.mesh.dof_manager.get_node_dofs(1)[4]]) > 0.0
    drill = np.zeros_like(candidate)
    drill[model.mesh.dof_manager.get_node_dofs(5)[5]] = 1.0
    assert float(result.structural_force @ drill) == 0.0


def test_s3_pair_trials_do_not_commit_and_opening_releases_force():
    model, _, pair, committed, history = _case()
    candidate = committed.copy()
    for node in (1, 2, 3):
        candidate[model.mesh.dof_manager.get_node_dofs(node)[0]] += 0.0002
    first = pair.evaluate(committed, candidate, history,
                          normal_pressure_Pa=2.0e6)
    second = pair.evaluate(committed, candidate, history,
                           normal_pressure_Pa=2.0e6)
    np.testing.assert_array_equal(first.structural_force, second.structural_force)
    assert first.trial.candidate_state == second.trial.candidate_state
    assert history.partner_key is None
    assert history.elastic_slip == (0.0, 0.0, 0.0)
    open_state = pair.evaluate(committed, candidate, history,
                               normal_pressure_Pa=0.0)
    assert open_state.trial.branch == "open"
    np.testing.assert_array_equal(open_state.structural_force,
                                  np.zeros_like(open_state.structural_force))
    assert open_state.trial.candidate_state.partner_key is None
    separated_after_stick = pair.evaluate(
        candidate, candidate, first.trial.candidate_state,
        normal_pressure_Pa=0.0,
    )
    assert separated_after_stick.trial.branch == "open"
    assert separated_after_stick.trial.released_storage_density == pytest.approx(20.0)
    np.testing.assert_array_equal(separated_after_stick.structural_force,
                                  np.zeros_like(separated_after_stick.structural_force))

    wrong = FrictionPointState(
        history.material_frame, history.elastic_slip, partner_key="wrong-pair",
    )
    with pytest.raises(ValueError, match="different material pair"):
        pair.evaluate(committed, candidate, wrong, normal_pressure_Pa=2.0e6)
    with pytest.raises(MemoryError, match="active-column budget"):
        limited = S3FrictionPointPair(
            pair.source, pair.target, 0.01, 0.3, 1.0e9,
            maximum_active_columns=1,
        )
        limited.evaluate(committed, candidate, history,
                         normal_pressure_Pa=2.0e6)
