"""Bounded F06 chart-coordinate derivative of the native generalized B3 operator."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver._ge_beam3_p5.chart import exp_chart_terms
from anysolver._ge_beam3_retained_generalized_state import (
    Context as GeneralizedContext, Program as GeneralizedProgram,
)
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._stiffened_shell_b3_local_adapter import evaluate_sparse_trial
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


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
    uncorrected = chart.T @ (base.tangent @ (chart @ direction))
    expected = uncorrected + curvature @ direction
    assert np.linalg.norm(curvature @ direction) > 1e-7
    errors = []
    for h in (1e-5, 3e-6, 1e-6):
        trial = []
        for sign in (1., -1.):
            target_q = q + sign * h * direction
            target_state = _advance_from_chart(context, state, q, target_q)
            response = evaluate_sparse_trial(context, target_state, origin, .25,
                                             family="generalized")
            target_chart, _ = _chart_map(context, target_q, response.residual)
            trial.append(target_chart.T @ response.residual)
        actual = (trial[0] - trial[1]) / (2 * h)
        errors.append(np.linalg.norm(actual - expected)
                      / max(1., np.linalg.norm(expected)))
    assert sum(error <= 1e-6 for error in errors) >= 2, errors
    uncorrected_error = (np.linalg.norm(actual - uncorrected)
                         / max(1., np.linalg.norm(expected)))
    assert uncorrected_error > 10 * errors[-1]
