"""Independent exact small controls for signed output actions and stage noise."""
from fractions import Fraction as F
from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu

import prepared_static_response_m13_output_actions as actions
from prepared_static_response_m10_bounds import contains


@pytest.mark.parametrize('stage', ['forward', 'backward'])
def test_signed_output_annihilates_correlated_factor_error(stage):
    identity = [[F(1), F(0)], [F(0), F(1)]]
    small = F(1, 10**18)
    if stage == 'forward':
        owner = SimpleNamespace(L=[[F(1), F(0)], [F(1), F(1)]], U=identity)
        rl, ru = [F(1), small], [F(0), F(0)]
    else:
        owner = SimpleNamespace(L=identity, U=[[F(1), F(1)], [F(0), F(1)]])
        rl, ru = [F(0), F(0)], [small, F(1)]
    graph = actions.Graph(owner, [F(0), F(0)], [F(0), F(0)], rl, ru)
    a = graph.new_node([F(1), F(0)], {}, (F(-2), F(2)), F(0), 'input')
    b = graph.new_node([F(0), F(1)], {}, (F(-2), F(2)), F(0), 'input')
    output = graph.add(a, b, 'canonical_sum')
    interval, contributions = graph.enclose(output)
    assert contributions['native_' + stage] == small
    # Independent closed-form physical combinations, not transpose_action.
    for first, second in product((-1, 1), repeat=2):
        if stage == 'forward':
            q = [F(first), F(second)*small-F(first)]
        else:
            q = [F(first)*small-F(second), F(second)]
        value = q[0]+q[1]
        assert interval[0] <= value <= interval[1]


def test_shared_stage_noise_cancels_but_separate_noise_does_not():
    owner = SimpleNamespace(L=[[F(1)]], U=[[F(1)]])
    graph = actions.Graph(owner, [F(0)], [F(0)], [F(0)], [F(0)])
    original = graph.new_node([F(1)], {}, (F(-1), F(1)), F(1, 8), 'stage_rounding')
    shared = graph.add(original, graph.negate(original), 'subtract_shared')
    _, shared_contributions = graph.enclose(shared)
    assert shared_contributions.get('stage_rounding', F(0)) == 0
    independent = graph.new_node([F(1)], {}, (F(-1), F(1)), F(1, 8), 'stage_rounding')
    separate = graph.add(original, graph.negate(independent), 'subtract_separate')
    _, separate_contributions = graph.enclose(separate)
    assert separate_contributions['stage_rounding'] == F(1, 4)


def test_actual_permuted_resident_signed_output_after_bound():
    matrix = sparse.csc_matrix([[0., 0., 3., 0.], [4., 0., 0., 5.],
                               [0., 6., 0., 0.], [7., 0., 0., 8.]])
    solver = splu(matrix); d = np.array([.5, 2., .25, 4.]); rhs = np.array([1., -2., 3., -4.])
    owner = actions.OutputActions(solver, matrix, d)
    graph, nodes = owner.prepare(rhs)
    weights = np.array([1., -2., .5, 3.])
    output = graph.dot(weights, nodes, 'canonical_dot')
    interval, _ = graph.enclose(output)
    # Native solve and recovery happen only after the interval is available.
    actual = weights @ (d*solver.solve(d*rhs))
    assert contains(interval, actual)


def test_selected_helper_mutation_before_enclose_is_detected(monkeypatch):
    owner = SimpleNamespace(L=[[F(1)]], U=[[F(1)]])
    graph = actions.Graph(owner, [F(0)], [F(0)], [F(0)], [F(0)])
    node = graph.new_node([F(1)], {}, (F(0), F(0)), F(0), 'input')
    monkeypatch.setattr(actions, 'transpose_action', lambda *args: [F(0)])
    with pytest.raises(actions.ResidentRefusal, match='source_authority'):
        graph.enclose(node)
