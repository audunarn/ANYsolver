"""Bounded local space-design tests; not a formal F03 qualification run."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_space_design import (
    action_matrix, build_macroelement, design_report, reference_gap_jacobian,
    sampled_dual_spaces,
)


@pytest.mark.parametrize("segments", (2, 4))
def test_growing_six_channel_spaces_and_biorthogonal_work(segments):
    macro = build_macroelement(segments)
    spaces = sampled_dual_spaces(macro)
    assert len(macro.connections) == 2*segments
    assert np.all(np.diff(macro.stations) > 0.)
    np.testing.assert_allclose(sum(macro.weights), .5, atol=2e-16)
    assert spaces["P1_translation_twist_P0_pitch_normal"].shape == (
        12*segments, 6*segments+4)
    assert spaces["P0_translation_twist_pair_P0_pitch_normal"].shape == (
        12*segments, 5*segments)
    consistent = spaces["P1_consistent_biorthogonal_dual"]
    assert consistent.shape == (12*segments, 6*(segments+1))

    # Consistent dual is an exact discrete work dual to the nodal P1 trace;
    # it is the same full-P1 span and thus cannot stabilize it by itself.
    hat = np.zeros((2*segments, segments+1))
    for sample, station in enumerate(macro.stations):
        edge = sample//2
        alpha = (station-macro.cuts[edge])/(macro.cuts[edge+1]-macro.cuts[edge])
        hat[sample, edge:edge+2] = (1.-alpha, alpha)
    for channel in range(6):
        begin = channel*(segments+1)
        dual = consistent[channel::6, begin:begin+segments+1]
        np.testing.assert_allclose(dual.T@(macro.weights[:, None]*hat),
                                   np.eye(segments+1), atol=2e-15)


@pytest.mark.parametrize("segments", (2, 4))
def test_predicted_normal_checkerboard_and_physical_work(segments):
    macro = build_macroelement(segments)
    report = design_report(macro)
    assert report["reference_gap_checked"]
    physical = report["physical_response"]
    ownership = report["trace_ownership"]
    assert ownership["supported_native_active"] > 0
    assert ownership["fixed_native_action_norm"] == 0.
    assert ownership["retained_resultant_action_norm"] == 0.
    np.testing.assert_allclose(physical["shear_gap_y"], -1., atol=2e-14)
    np.testing.assert_allclose(physical["native_twist_gap_x"], 1., atol=2e-14)
    np.testing.assert_allclose(physical["normal_row_pair_difference"], 0.,
                               atol=2e-14)
    assert physical["shell_drill_gap_norm"] < 2e-14

    a, b, c = report["candidates"].values()
    assert a["action_rank"] == a["dual_dimension"]
    assert b["action_rank"] == b["dual_dimension"]
    assert c["action_rank"] == c["dual_dimension"]-1
    assert a["zero_action_mode"] is None
    assert b["zero_action_mode"] is None
    assert c["zero_action_mode"]["channel_energy_fraction"][5] > 1.-1e-12
    assert c["zero_action_mode"]["normal_nodal_alternation_correlation"] > 1.-1e-12
    assert c["zero_action_mode"]["action_norm"] < 1e-12
    for candidate in (a, b, c):
        assert candidate["work_map_error"] < 2e-13
        np.testing.assert_allclose(candidate["physical_work"]["shear"], -.5,
                                   atol=2e-13)
        np.testing.assert_allclose(candidate["physical_work"]["twist_torque"], .5,
                                   atol=2e-13)
        assert abs(candidate["physical_work"]["shell_drill"]) < 2e-13
    # B eliminates the edgewise pitch/normal checkerboard by having one dual
    # coefficient per two-edge patch. This also omits that alternating action.
    assert b["alternating_cell_projection_error"]["normal_alternation"] > .999
    assert b["alternating_cell_projection_error"]["pitch_alternation"] > .999
    assert a["alternating_cell_projection_error"]["normal_alternation"] < 1e-12


@pytest.mark.parametrize("segments", (2, 4))
def test_all_candidate_weak_work_maps_match_actual_native_updates(segments):
    macro = build_macroelement(segments)
    state = macro.fixture.context.initial.mechanical
    gap_jacobian = reference_gap_jacobian(macro)
    spaces = sampled_dual_spaces(macro)
    rng = np.random.default_rng(954+segments)
    direction = rng.normal(size=macro.coordinate_count)*.02
    direction[6*(segments+1)+np.asarray(macro.fixture.context.fixed,
                                      dtype=int)] = 0.
    # Use one native retained cell spin explicitly, not merely nodal motion.
    first = macro.connections[0].port
    column = first.context.nodal_count+24*first.element_index+3*first.cell
    direction[6*(segments+1)+column:6*(segments+1)+column+3] = (.03, -.02, .04)

    def actual_work(samples, coefficients, scale):
        shell = scale*direction[:6*(segments+1)].reshape(segments+1, 6)
        native = macro.fixture.context.advance(
            state, scale*direction[6*(segments+1):])
        work = 0.
        for sample, connection in enumerate(macro.connections):
            edge = sample//2
            gap, _ = connection.evaluate(shell[edge:edge+2], native)
            work += macro.weights[sample]*(samples@coefficients)[
                6*sample:6*sample+6]@gap
        return work

    step = 2e-6
    for samples in spaces.values():
        coefficients = rng.normal(size=samples.shape[1])
        action = action_matrix(macro, samples, gap_jacobian)
        predicted = float(coefficients@action@direction)
        measured = (actual_work(samples, coefficients, step)-
                    actual_work(samples, coefficients, -step))/(2*step)
        np.testing.assert_allclose(measured, predicted, rtol=2e-8, atol=2e-8)
