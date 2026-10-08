"""Actual multi-element Q4/S3 material trials feeding one F03 shell pose."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_trace import make_shell


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_virgin_multi_element_trial_and_rejected_candidate_are_repeatable(topology):
    fixture = FlatE4TrialPanel(make_shell(1, topology))
    total = np.zeros(6*fixture.panel.node_count)
    before = fixture._origin_bytes
    virgin = fixture.evaluate(total, .37)
    assert len(virgin.candidate_states) == fixture.panel.element_count
    np.testing.assert_allclose(virgin.residual, 0., rtol=0, atol=1e-5)
    np.testing.assert_allclose(virgin.position, (.37, 0., 0.),
                               rtol=0, atol=2e-15)
    np.testing.assert_allclose(virgin.frame, np.eye(3), rtol=0, atol=2e-15)
    nodes = reference_nodes(fixture.panel)
    rotation = Rotation.from_rotvec((.18, -.11, .09)).as_matrix()
    moved = np.zeros((fixture.panel.node_count, 6))
    moved[:, :3] = nodes@rotation.T-nodes
    moved[:, 3:] = Rotation.from_matrix(rotation).as_rotvec()
    moved[4, 0] += .001
    trial = fixture.evaluate(moved.ravel(), .37)
    again = fixture.evaluate(moved.ravel(), .37)
    expected_position, expected_frame = pose_from_e4_total(
        fixture.panel, .37, moved.ravel())
    np.testing.assert_array_equal(trial.position, expected_position)
    np.testing.assert_array_equal(trial.frame, expected_frame)
    np.testing.assert_array_equal(trial.residual, again.residual)
    np.testing.assert_array_equal(trial.tangent, again.tangent)
    assert trial.candidate_states == again.candidate_states
    assert fixture._origin_bytes == before
    fixture.guard()
    np.testing.assert_allclose(fixture.evaluate(total, .37).residual,
                               virgin.residual, rtol=0, atol=1e-5)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_trial_definition_and_total_coordinate_validation(topology):
    fixture = FlatE4TrialPanel(make_shell(1, topology))
    size = 6*fixture.panel.node_count
    with pytest.raises(ValueError, match="complete flat E4"):
        fixture.evaluate(np.zeros(size-1), .37)
    invalid = np.zeros(size)
    invalid[6] = np.nan
    with pytest.raises(ValueError, match="complete flat E4"):
        fixture.evaluate(invalid, .37)
    fixture.model.mesh.nodes[2].x += .001
    with pytest.raises(ValueError, match="definition or predecessor"):
        fixture.evaluate(np.zeros(size), .37)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_assembled_material_tangent_follows_same_predecessor(topology):
    fixture = FlatE4TrialPanel(make_shell(1, topology))
    base = np.zeros((fixture.panel.node_count, 6))
    base[4, :6] = (.0008, -.0005, .0003, .001, -.0015, .0007)
    base[7, :3] = (-.0004, .0006, -.0002)
    rng = np.random.default_rng(5206)
    direction = rng.normal(size=base.size)
    direction /= np.linalg.norm(direction)
    reference = fixture.evaluate(base.ravel(), .37)
    step = 2e-7
    plus = fixture.evaluate(base.ravel()+step*direction, .37)
    minus = fixture.evaluate(base.ravel()-step*direction, .37)
    numerical = (plus.residual-minus.residual)/(2*step)
    predicted = reference.tangent@direction
    relative = np.linalg.norm(predicted-numerical)/max(
        np.linalg.norm(numerical), 1.)
    assert relative < 3e-6


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("change", (
    lambda fixture: setattr(fixture.panel, "node_count",
                            fixture.panel.node_count+1),
    lambda fixture: setattr(fixture.panel, "element_count",
                            fixture.panel.element_count+1),
    lambda fixture: setattr(fixture.elements[0][2], "material_name", "other"),
    lambda fixture: setattr(fixture.elements[0][2], "node_ids",
                            tuple(reversed(fixture.elements[0][2].node_ids))),
    lambda fixture: setattr(fixture.model.get_material("steel"),
                            "yield_stress", 1e6),
    lambda fixture: setattr(fixture.model.get_material("steel"),
                            "hardening_curve", object()),
    lambda fixture: setattr(fixture.model.get_material("steel"),
                            "hill_yield", object()),
))
def test_consumed_definition_changes_invalidate_trial(topology, change):
    fixture = FlatE4TrialPanel(make_shell(1, topology))
    change(fixture)
    with pytest.raises(ValueError, match="definition or predecessor"):
        fixture.guard()


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_two_step_panel_real_element_inventory(topology):
    fixture = FlatE4TrialPanel(make_shell(2, topology))
    response = fixture.evaluate(np.zeros(6*fixture.panel.node_count), .37)
    assert len(response.candidate_states) == fixture.panel.element_count
    assert response.tangent.shape == (6*fixture.panel.node_count,)*2
    np.testing.assert_allclose(response.position, (.37, 0., 0.),
                               rtol=0, atol=2e-15)
