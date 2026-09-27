"""Bounded F06 chart-coordinate derivative of the native generalized B3 operator."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver._ge_beam3_p5.chart import exp_chart_terms
from anysolver._ge_beam3_retained_fibre_state import Context as FibreContext
from anysolver._ge_beam3_retained_generalized_state import (
    Context as GeneralizedContext, Program as GeneralizedProgram,
)
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_seeded_load_program import ForceProgram
from anysolver._stiffened_shell_b3_chart import pullback_sparse_trial
from anysolver._stiffened_shell_b3_local_adapter import evaluate_sparse_trial
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from test_ge_beam3_retained_fibre import make_model


def _rotation_blocks(context):
    blocks = [6 * i + 3 for i in range(len(context.node_ids))]
    for i in range(len(context.elements)):
        blocks.extend((context.nodal_count + 24 * i,
                       context.nodal_count + 24 * i + 3))
    return blocks


def _chart_map(context, q, residual):
    chart = np.eye(context.count)
    curvature = np.zeros((context.count, context.count))
    for start in _rotation_blocks(context):
        block = slice(start, start + 3)
        a, da = exp_chart_terms(q[block])
        chart[block, block] = a
        for k in range(3):
            curvature[block, start + k] = da[:, :, k].T @ residual[block]
    return chart, curvature


def _advance_from_chart(context, base_state, base_q, target_q):
    step = target_q - base_q
    for start in _rotation_blocks(context):
        block = slice(start, start + 3)
        relative = (Rotation.from_rotvec(target_q[block])
                    * Rotation.from_rotvec(base_q[block]).inv())
        step[block] = relative.as_rotvec()
    return context.advance(base_state, step)


@pytest.mark.parametrize("distributed_load", (False, True))
def test_native_generalized_chart_tangent_includes_residual_curvature(
        distributed_load):
    fixture = build(4, z_offset=.0675,
                    torsion_constant=square_torsion_constant())
    context = fixture.context
    if distributed_load:
        load = DistributedPattern(
            LinePattern(((1, .09, -.03, .02),)),
            ((1, .07, -.04, .05),))
        context = GeneralizedContext(
            fixture.model, GeneralizedProgram((1.,), load))
    state, origin = context.initial.mechanical, context.initial.origins
    q = np.zeros(context.count)
    free_node = context.nodal_count - 6
    q[free_node:free_node + 6] = (.0004, -.0003, .0002, .16, -.11, .13)
    q[context.nodal_count:context.nodal_count + 7] = (
        .09, -.07, .06, -.05, .08, .04, .0001)
    q[np.asarray(context.fixed, dtype=int)] = 0.
    state = context.advance(state, q)

    direction = np.zeros(context.count)
    direction[free_node:free_node + 6] = (.4, -.3, .2, .15, -.1, .12)
    direction[context.nodal_count:context.nodal_count + 7] = (
        .11, -.09, .07, .05, -.04, .03, .015)
    direction[np.asarray(context.fixed, dtype=int)] = 0.

    base = evaluate_sparse_trial(context, state, origin, .25,
                                 family="generalized")
    chart, curvature = _chart_map(context, q, base.residual)
    transformed = pullback_sparse_trial(context, base, q)
    np.testing.assert_allclose(transformed.residual, chart.T@base.residual,
                               rtol=2e-14, atol=2e-12)
    np.testing.assert_allclose(
        transformed.tangent.toarray(),
        chart.T@base.tangent.toarray()@chart+curvature,
        rtol=2e-13, atol=2e-11)
    assert transformed.candidate_histories is base.candidate_histories
    assert not np.shares_memory(transformed.residual, base.residual)
    assert not np.shares_memory(transformed.tangent.data, base.tangent.data)
    uncorrected = chart.T @ (base.tangent @ (chart @ direction))
    expected = transformed.tangent @ direction
    assert np.linalg.norm(curvature @ direction) > 1e-7
    errors = []
    for h in (1e-5, 3e-6, 1e-6):
        trial = []
        for sign in (1., -1.):
            target_q = q + sign * h * direction
            target_state = _advance_from_chart(context, state, q, target_q)
            response = evaluate_sparse_trial(context, target_state, origin, .25,
                                             family="generalized")
            trial.append(pullback_sparse_trial(
                context, response, target_q).residual)
        actual = (trial[0] - trial[1]) / (2 * h)
        errors.append(np.linalg.norm(actual - expected)
                      / max(1., np.linalg.norm(expected)))
    assert sum(error <= 1e-6 for error in errors) >= 2, errors
    uncorrected_error = (np.linalg.norm(actual - uncorrected)
                         / max(1., np.linalg.norm(expected)))
    assert uncorrected_error > 10 * errors[-1]
    with pytest.raises(ValueError, match="finite native B3 chart"):
        pullback_sparse_trial(context, base, np.full(context.count, np.nan))
    outside_chart = q.copy()
    outside_chart[free_node+3] = .9*np.pi
    with pytest.raises(ValueError, match="cutback"):
        pullback_sparse_trial(context, base, outside_chart)


def test_native_physical_fibre_elastic_chart_tangent_uses_same_sparse_contract():
    context = FibreContext(
        make_model(contrast=1.),
        ForceProgram((.25,), ((5, .4, -.005, 0.),), max_iterations=24))
    layout = context.layout
    state, origin = context.initial.mechanical, context.initial.origins
    direction = np.zeros(layout.count)
    free_node = layout.nodal_count-6
    direction[free_node:free_node+6] = (.4, -.3, .2, .15, -.1, .12)
    direction[layout.nodal_count:layout.nodal_count+7] = (
        .11, -.09, .07, .05, -.04, .03, .015)
    direction[np.asarray(layout.fixed, dtype=int)] = 0.
    q = 1e-3*direction
    state = layout.advance(state, q)
    base = evaluate_sparse_trial(context, state, origin, .25,
                                 family="physical_fibre")
    chart, curvature = _chart_map(layout, q, base.residual)
    pulled = pullback_sparse_trial(layout, base, q)
    np.testing.assert_allclose(pulled.residual, chart.T@base.residual,
                               rtol=2e-14, atol=2e-12)
    np.testing.assert_allclose(
        pulled.tangent.toarray(),
        chart.T@base.tangent.toarray()@chart+curvature,
        rtol=2e-13, atol=2e-11)
    expected = pulled.tangent@direction
    errors = []
    for h in (1e-5, 3e-6, 1e-6):
        residuals = []
        for sign in (1., -1.):
            target_q = q+sign*h*direction
            target_state = _advance_from_chart(layout, state, q, target_q)
            trial = evaluate_sparse_trial(context, target_state, origin, .25,
                                          family="physical_fibre")
            residuals.append(pullback_sparse_trial(
                layout, trial, target_q).residual)
        actual = (residuals[0]-residuals[1])/(2*h)
        errors.append(np.linalg.norm(actual-expected)
                      / max(1., np.linalg.norm(expected)))
    assert sum(error <= 1e-6 for error in errors) >= 2, errors
