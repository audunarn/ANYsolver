"""Small independent scalar/3x3 checks; no production or global beam solve."""

import ast
from decimal import Decimal as D, localcontext
from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_saved_force_precision as p


def eye():
    return [[D(i == j) for j in range(3)] for i in range(3)]


def mm(a, b):
    return [[p.dot(row, col) for col in p.transpose(b)] for row in a]


@pytest.mark.parametrize('precision', [60, 90])
def test_independent_eight_point_rule_all_polynomial_moments(precision):
    with localcontext() as ctx:
        ctx.prec = precision
        rule = p.gauss8()
        assert len(rule) == 8 and all(-1 < x < 1 and w > 0 for x, w in rule)
        for degree in range(16):
            exact = D(0) if degree % 2 else D(2)/D(degree+1)
            assert abs(sum(w*x**degree for x, w in rule)-exact) < D(10)**(-precision+10)


def test_straight_reference_force_and_directional_energy_derivative():
    with localcontext() as ctx:
        ctx.prec = 70
        reference = [[D(-1), D(0), D(0)], [D(0)]*3, [D(1), D(0), D(0)]]
        actual = [row.copy() for row in reference]
        actual[1] = [D('.03'), D('.02'), D('-.01')]
        force = p.half_force(reference, actual, eye(), 0, p.gauss8())
        assert max(abs(a-b) for a, b in zip(force, map(D, ('30', '8', '-4')))) < D('1e-60')
        direction = list(map(D, ('.2', '-.4', '.3')));epsilon = D('1e-20')
        energy = lambda x: (1000*x[0]**2+400*x[1]**2+400*x[2]**2)/2
        plus = [a+epsilon*b for a, b in zip(actual[1], direction)]
        minus = [a-epsilon*b for a, b in zip(actual[1], direction)]
        assert abs((energy(plus)-energy(minus))/(2*epsilon)-p.dot(force, direction)) < D('1e-45')


def test_exact_rational_rigid_motion_and_connectivity_reversal():
    with localcontext() as ctx:
        ctx.prec = 70
        reference = [list(map(D, row)) for row in (('-1', '.1', '.02'), ('0', '.2', '0'), ('1', '.1', '-.03'))]
        turn = [list(map(D, row)) for row in (('.6', '-.8', '0'), ('.8', '.6', '0'), ('0', '0', '1'))]
        shift = list(map(D, ('2', '-3', '4')))
        actual = [[v+shift[i] for i, v in enumerate(p.matvec(turn, row))] for row in reference]
        for cell in (0, 1):
            assert max(abs(v) for v in p.half_force(reference, actual, turn, cell, p.gauss8())) < D('1e-60')
        actual[1][1] += D('.01')
        forward = p.half_force(reference, actual, turn, 1, p.gauss8())
        reverse = p.half_force(reference[::-1], actual[::-1], turn, 0, p.gauss8())
        assert max(abs(a+b) for a, b in zip(forward, reverse)) < D('1e-60')


def test_superposed_rigid_motion_and_reference_reexpression_covariance():
    with localcontext() as ctx:
        ctx.prec = 70
        ref = [list(map(D, row)) for row in (('-1', '0', '0'), ('0', '.2', '0'), ('1', '0', '.1'))]
        actual = [row.copy() for row in ref];actual[1][2] += D('.03')
        turn = [list(map(D, row)) for row in (('.6', '-.8', '0'), ('.8', '.6', '0'), ('0', '0', '1'))]
        f = p.half_force(ref, actual, eye(), 0, p.gauss8())
        rotated_actual = [p.matvec(turn, row) for row in actual]
        rigid_f = p.half_force(ref, rotated_actual, turn, 0, p.gauss8())
        rotated_ref = [p.matvec(turn, row) for row in ref]
        reexpressed_f = p.half_force(rotated_ref, rotated_actual, mm(mm(turn, eye()), p.transpose(turn)), 0, p.gauss8())
        for result in (rigid_f, reexpressed_f):
            assert max(abs(a-b) for a, b in zip(result, p.matvec(turn, f))) < D('1e-60')


def test_real_saved_state_diagnostic_and_deterministic_serialization():
    one, two = p.audit(), p.audit()
    assert p.canonical(one) == p.canonical(two)
    assert one['production_qualified'] is one['independent_equilibrium_proof'] is False
    assert D(one['stored_translation_norm']) == D(one['exact_scatter_translation_norm']) > D('1e-11')
    assert D(one['independent_90_translation_norm']) > D('1e-11')
    assert D(one['max_60_90_difference']) < D('1e-50')
    assert D(one['max_scatter_rounding']) == 0
    assert D(one['max_independent_stored_difference']) < D('2e-13')


@pytest.mark.parametrize('mutation', ['plastic', 'coupling', 'modulus'])
def test_inapplicable_section_rejected(mutation):
    reference, saved = p.saved_inputs()
    response = saved['response']['elements'][0]['stations'][0]['response']
    if mutation == 'plastic': response['plastic_active'] = True
    if mutation == 'coupling': response['tangent'][0][4] = D(1)
    if mutation == 'modulus': response['tangent'][0][0] = D(999)
    with pytest.raises(ValueError, match='uncoupled elastic'):
        p.independent_translations(reference, saved, 60)


def test_input_mutation_fails_before_reconstruction(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    (tmp_path/'initial.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError, match='immutable saved state'): p.audit()


def test_standard_library_only_and_no_hidden_mechanics_imports():
    tree = ast.parse(Path(p.__file__).read_text())
    allowed = {'decimal', 'fractions', 'hashlib', 'json', 'pathlib'}
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    for node in imports:
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module]
        assert all(name.split('.')[0] in allowed for name in names)
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in
                   ('__import__', 'eval', 'exec', 'compile') for n in ast.walk(tree))
