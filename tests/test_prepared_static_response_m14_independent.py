"""Independent represented-binary64 boundary and cancellation controls."""
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np

import prepared_static_response_m14_exact_actions as actions
from prepared_static_response_m10_bounds import contains


def test_upscaling_and_sign_rules_on_extreme_represented_operands():
    maximum = np.finfo(float).max
    tiny = np.nextafter(0., 1.)
    samples = [-maximum, -1., -tiny, -0., 0., tiny, 1., maximum]
    for value in samples:
        for factor in (-2., -1., 0., 1., 2.):
            exact = F(float(value))*F(float(factor))
            admitted = actions.scale_is_exact((F(float(value)),)*2, F(float(factor)))
            with np.errstate(over='ignore'):
                result = np.float64(value)*np.float64(factor)
            if admitted:
                assert np.isfinite(result)
                assert F(float(result)) == exact
            elif abs(exact) > F(float(maximum)):
                assert not admitted


def test_downscaling_preserves_subnormal_counterexamples():
    tiny = np.nextafter(0., 1.)
    normal = np.finfo(float).tiny
    for value in (tiny, 3*tiny, np.nextafter(normal, 0.)):
        point = F(float(value))
        assert not actions.scale_is_exact((point, point), F(1, 2))
        assert F(float(np.float64(value)*.5)) != point/2
    aligned = F(float(2*tiny))
    assert actions.scale_is_exact((aligned, aligned), F(1, 2))
    assert not actions.scale_is_exact((-F(float(normal)), F(float(normal))), F(1, 2))
    # This point cannot be a canonical represented input, so it cannot prove exactness.
    assert not actions.scale_is_exact((F(1, 3), F(1, 3)), F(1, 2))


def test_one_sided_normal_output_interval_proof_for_both_signs():
    normal = F(float(np.finfo(float).tiny))
    assert actions.scale_is_exact((2*normal, 8*normal), F(1, 2))
    assert actions.scale_is_exact((-8*normal, -2*normal), F(1, 2))
    assert not actions.scale_is_exact((normal, 8*normal), F(1, 2))


def graph_with_points(values):
    n = len(values)
    identity = [[F(int(i == j)) for j in range(n)] for i in range(n)]
    graph = actions.Graph(SimpleNamespace(L=identity, U=identity),
                          [F(float(v)) for v in values], [F(0)]*n, [F(0)]*n, [F(0)]*n)
    nodes = []
    for i, value in enumerate(values):
        row = [F(int(i == j)) for j in range(n)]
        nodes.append(graph.new_node(row, {}, (F(float(value)),)*2, F(0), 'input'))
    return graph, nodes


def test_selector_and_zero_addition_need_no_new_rounding_symbol():
    values = np.array([np.nextafter(0., 1.), .5, -1.])
    graph, nodes = graph_with_points(values)
    selector = graph.dot(np.array([0., -1., 0.]), nodes, 'selector')
    interval, contribution = graph.enclose(selector)
    assert contains(interval, np.array([0., -1., 0.]) @ values)
    assert contribution.get('selector', F(0)) == 0
    zero = graph.dot(np.zeros(3), nodes, 'zero_selector')
    added = graph.add(nodes[1], zero, 'zero_addition')
    interval, contribution = graph.enclose(added)
    assert contains(interval, values[1]+0.)
    assert contribution.get('zero_addition', F(0)) == 0


def test_multioperand_dyadic_dot_keeps_cancellation_rounding():
    values = np.array([1e16, 1., -1e16])
    graph, nodes = graph_with_points(values)
    result = graph.dot(np.ones(3), nodes, 'multioperand')
    interval, contribution = graph.enclose(result)
    assert contribution['multioperand'] > 0
    assert sum(F(float(v)) for v in values) == 1
    assert contains(interval, np.ones(3) @ values)
