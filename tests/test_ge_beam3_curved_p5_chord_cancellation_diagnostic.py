"""Exact-rational audit of saved scalar inputs; no beam solve or qualification."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-force-accuracy32-20260906-36548b8a32f14e16bc114dc80e3b48ef/force-accuracy32')
INPUTS = {
    'initial.json': (1135374, 'a223046766c5fdac047060d324a55e769ac2a487d3793a31285b98157265bc59'),
    'failed_last.json': (1185545, '5c64284e318acb894ff2251ce61b6ba2b2a6ce3db9ee432b814cae686dabe6ce'),
}


def left_sum(values):
    # Match Jet2's left-to-right additions, rather than relying on a Python
    # version's specialized built-in floating-point summation implementation.
    result = 0
    for value in values:
        result += value
    return result


def direct(u, chord, reference, i):
    return left_sum(u[k][i]*chord[k] for k in range(3))-reference[i]


def rearranged(u, chord, reference, i):
    return (left_sum((u[k][i]-(1 if k == i else 0))*reference[k] for k in range(3))
            +left_sum(u[k][i]*(chord[k]-reference[k]) for k in range(3)))


@pytest.fixture(scope='module')
def components():
    raw = {}
    for name, (size, sha) in INPUTS.items():
        data = (ROOT/name).read_bytes()
        assert len(data) == size and hashlib.sha256(data).hexdigest() == sha
        raw[name] = json.loads(data)
    reference = raw['initial.json']['assembly']['positions']
    snapshot = raw['failed_last.json']
    assert snapshot['disposition'] == 'UNCOMMITTED_DIAGNOSTIC_ONLY'
    actual = snapshot['positions']
    rows = []
    for index, element in enumerate(snapshot['response']['elements']):
        for cell, (left, right) in enumerate(((0, 1), (1, 2))):
            left += 2*index; right += 2*index
            chord = [actual[right][k]-actual[left][k] for k in range(3)]
            base = [reference[right][k]-reference[left][k] for k in range(3)]
            u = element['local_rotations'][cell]
            # Exact interpretation of the existing binary64 chord and matrix
            # inputs, not an assertion of exact physical geometry or solution.
            exact_u = [[Fraction.from_float(v) for v in row] for row in u]
            exact_d = list(map(Fraction.from_float, chord))
            exact_r = list(map(Fraction.from_float, base))
            for i in range(3):
                truth = direct(exact_u, exact_d, exact_r, i)
                assert truth == rearranged(exact_u, exact_d, exact_r, i)
                old = abs(Fraction.from_float(direct(u, chord, base, i))-truth)
                new = abs(Fraction.from_float(rearranged(u, chord, base, i))-truth)
                rows.append((old, new, index, cell, i))
    return rows


def test_rearrangement_is_exact_for_all_saved_scalar_component_inputs(components):
    assert len(components) == 32*2*3


def test_cancellation_reduction_on_saved_inputs_is_not_assembly_acceptance(components):
    old = max(row[0] for row in components)
    new = max(row[1] for row in components)
    assert old > Fraction('4e-18')
    assert new < Fraction('2e-19')
    assert old > 20*new
    assert max(components, key=lambda row: row[0])[2:] == (21, 1, 0)
