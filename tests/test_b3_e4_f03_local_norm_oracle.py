"""Synthetic identities only; no saved state or production norm is imported."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, Inexact, ROUND_UP, localcontext
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import _b3_e4_f03_local_norm_oracle as oracle


ZERO = (F(0),) * 6
ATOM_ZERO = ((F(0),) * 3,) * 2


def record(cuts=(F(0), F(1)), cells=None, cosine=(F(0),) * 3, atoms=ATOM_ZERO):
    if cells is None:
        cells = ((ZERO, ZERO, ZERO),) * (len(cuts) - 1)
    return {'cuts': cuts, 'coefficients': cells, 'cosine': cosine, 'atoms': atoms}


def padded(values):
    values = tuple(F(x) for x in values)
    return values + (F(0),) * (6 - len(values))


def decimal(value):
    return Decimal(value.numerator) / Decimal(value.denominator)


def energy(z, width):
    """Exact polynomial energy from local coefficients, independently of kernel."""
    derivative = tuple(F(i) * z[i] / width for i in range(1, len(z)))
    return width * sum((a * b / (i + j + 1)
                        for values in (z, derivative)
                        for i, a in enumerate(values) for j, b in enumerate(values)), F(0))


@pytest.mark.parametrize('order', (16, 24))
def test_independent_decimal_rule_is_degree_exact(order):
    with localcontext() as context:
        context.prec = 70
        rule = oracle._gauss(order)
        assert all(type(x) is Decimal and type(w) is Decimal for x, w in rule)
        for power in (0, 1, 5, 2 * order - 2, 2 * order - 1):
            actual = sum((w * x ** power for x, w in rule), Decimal(0))
            assert abs(actual - Decimal(1) / (power + 1)) < Decimal('1e-62')


@pytest.mark.parametrize('order', (16, 24))
def test_constant_density_and_physical_moment_scaling(order):
    # A constant has constant Riesz representer, so its full squared norm is c^2.
    values = (F(2), F(-3), F(5) * oracle.ELL)
    functional = record(cells=(tuple(padded((x,)) for x in values),))
    result = oracle.norm_squared(functional, order=order)
    with localcontext() as context:
        context.prec = 70
        for actual, expected in zip(result.channels, (4, 9, 25)):
            assert abs(actual - expected) < Decimal('1e-38')
        assert abs(result.total - 38) < Decimal('1e-38')


@pytest.mark.parametrize('order', (16, 24))
def test_analytic_endpoint_gram_and_negative_bilinear(order):
    root = record(atoms=((F(2), F(-3), F(5) * oracle.ELL), (F(0),) * 3))
    tip = record(atoms=((F(0),) * 3, (F(-7), F(11), F(-13) * oracle.ELL)))
    with localcontext() as context:
        context.prec = 70
        expone = Decimal(1).exp()
        sinh = (expone - 1 / expone) / 2
        coth = (expone + 1 / expone) / (2 * sinh)
        cross = oracle.green_inner(root, tip, order=order)
        for actual, coefficient in zip(cross, (-14, -33, -65)):
            assert actual < 0
            assert abs(actual - Decimal(coefficient) / sinh) < Decimal('1e-64')
        squared = oracle.norm_squared(root, order=order)
        for actual, coefficient in zip(squared.channels, (4, 9, 25)):
            assert abs(actual - coefficient * coth) < Decimal('1e-64')


@pytest.mark.parametrize('order', (16, 24))
def test_manufactured_polynomial_riesz_energy_with_both_atoms(order):
    # z=1+2s+3s²+s³; f=z-z'', a0=-z'(0), a1=z'(1).
    z = tuple(map(F, (1, 2, 3, 1)))
    density = tuple(map(F, (-5, -4, 3, 1)))
    scales = (F(1), F(-2), F(3) * oracle.ELL)
    functional = record(
        cells=(tuple(padded(tuple(x * scale for x in density)) for scale in scales),),
        atoms=(tuple(-2 * scale for scale in scales), tuple(11 * scale for scale in scales)))
    with localcontext() as context:
        context.prec = 70
        expected = decimal(energy(z, F(1)))
        result = oracle.norm_squared(functional, order=order)
        for actual, factor in zip(result.channels, (1, 4, 9)):
            assert abs(actual - factor * expected) < Decimal('1e-34')


def test_piecewise_c1_riesz_energy_has_no_internal_atom():
    # z=s+(s-1/2)_+³ is C1. Its density jumps in derivative, without an atom.
    cuts = (F(0), F(1, 2), F(1))
    z0 = (F(0), F(1, 2))
    z1 = (F(1, 2), F(1, 2), F(0), F(1, 8))
    functional = record(cuts=cuts, cells=((padded(z0), ZERO, ZERO),
                                        (padded((F(1, 2), F(-5, 2), 0, F(1, 8))), ZERO, ZERO)),
                        atoms=((F(-1), F(0), F(0)), (F(7, 4), F(0), F(0))))
    with localcontext() as context:
        context.prec = 70
        expected = decimal(energy(z0, F(1, 2)) + energy(z1, F(1, 2)))
        low = oracle.norm_squared(functional, order=16)
        high = oracle.norm_squared(functional, order=24)
        assert abs(low.total - expected) < Decimal('1e-35')
        assert abs(high.total - expected) < Decimal('1e-50')
        assert abs(low.total - high.total) < Decimal('1e-35')


def test_different_partitions_exact_restriction_and_symmetric_cross_form():
    # The same physical affine density is encoded in three distinct charts.
    whole = record(cells=((padded((1, 2)), ZERO, ZERO),))
    split = record(cuts=(F(0), F(1, 3), F(3, 4), F(1)), cells=(
        (padded((1, F(2, 3))), ZERO, ZERO),
        (padded((F(5, 3), F(5, 6))), ZERO, ZERO),
        (padded((F(5, 2), F(1, 2))), ZERO, ZERO)))
    with localcontext() as context:
        context.prec = 70
        baseline = oracle.norm_squared(whole, order=24).total
        forward = oracle.green_inner(whole, split, order=24)
        backward = oracle.green_inner(split, whole, order=24)
        assert forward == backward
        assert abs(forward[0] - baseline) < Decimal('1e-50')
        assert abs(oracle.norm_squared(split, order=24).total - baseline) < Decimal('1e-50')


def test_positive_rational_interval_survives_coincident_float_endpoints():
    left = F(1, 2)
    right = left + F(1, 2 ** 60)
    assert float(left) == float(right)
    width = right - left
    # A narrow constant pulse has unit total action; its norm approaches K(.5,.5).
    functional = record(cuts=(F(0), left, right, F(1)), cells=(
        (ZERO, ZERO, ZERO), (padded((1 / width,)), ZERO, ZERO), (ZERO, ZERO, ZERO)))
    with localcontext() as context:
        context.prec = 70
        exp_half = Decimal('.5').exp()
        cosh_half = (exp_half + 1 / exp_half) / 2
        exp_one = Decimal(1).exp()
        sinh_one = (exp_one - 1 / exp_one) / 2
        low = oracle.norm_squared(functional, order=16).total
        high = oracle.norm_squared(functional, order=24).total
        assert low > 0
        assert abs(high - cosh_half ** 2 / sinh_one) < Decimal('1e-17')
        assert abs(high - low) < Decimal('1e-55')


def test_cosine_held_frequency_and_two_fixed_orders():
    functional = record(cuts=(F(0), F(2, 5), F(1)), cells=(
        (padded((3, -2, 1, 0, 0, 1)), ZERO, ZERO),
        (padded((-2, 3, -4, 1)), ZERO, ZERO)),
        cosine=(F(7), F(-5), F(2) * oracle.ELL),
        atoms=((F(-3), F(1), F(2) * oracle.ELL), (F(4), F(-2), -oracle.ELL)))
    assert oracle.OMEGA == F.from_float(2 * 3.141592653589793)
    assert oracle.ELL == F.from_float(.46)
    with localcontext() as context:
        context.prec = 70
        low = oracle.norm_squared(functional, order=16)
        high = oracle.norm_squared(functional, order=24)
        for a, b in zip(low.channels, high.channels):
            assert abs(a - b) < Decimal('1e-24')


def test_input_ownership_and_immutable_result():
    raw = record()
    owned = oracle.validate_functional(raw)
    raw['cosine'] = (F(9),) * 3
    assert owned.cosine == (F(0),) * 3
    with pytest.raises(FrozenInstanceError):
        owned.cuts = (F(0), F(1))
    result = oracle.norm_squared(owned)
    assert result.channels == (Decimal(0),) * 3 and result.total == 0
    with pytest.raises(FrozenInstanceError):
        result.total = Decimal(1)


def test_arithmetic_is_independent_of_callers_decimal_context():
    functional = record(atoms=((F(1), F(2), F(3)), (F(4), F(5), F(6))))
    expected = oracle.norm_squared(functional)
    with localcontext() as context:
        context.prec = 9
        context.rounding = ROUND_UP
        context.traps[Inexact] = True
        assert oracle.norm_squared(functional) == expected


def test_negative_raw_norm_is_preserved_and_nonfinite_total_is_rejected(monkeypatch):
    # A caller can classify a negative raw measurement; the oracle never repairs it.
    monkeypatch.setattr(oracle, 'green_inner', lambda *args, **kwargs:
                        (Decimal('-1e-65'), Decimal(0), Decimal(0)))
    result = oracle.norm_squared(record())
    assert result.channels[0] == result.total == Decimal('-1e-65')
    monkeypatch.setattr(oracle, 'green_inner', lambda *args, **kwargs:
                        (Decimal('Infinity'), Decimal(0), Decimal(0)))
    with pytest.raises(ArithmeticError, match='nonfinite'):
        oracle.norm_squared(record())


@pytest.mark.parametrize('change', (
    {'cuts': (F(0), F(0), F(1))},
    {'cuts': (F(0), .5, F(1))},
    {'cuts': tuple(F(i, 9) for i in range(10))},
    {'cuts': (F(0), F(1, 2 ** 4096), F(1))},
    {'cosine': (F(0), True, F(0))},
    {'cosine': (F(0), F(2 ** 4096), F(0))},
    {'cosine': [F(0)] * 3},
    {'atoms': ATOM_ZERO + ((F(0),) * 3,)},
    {'coefficients': ((ZERO + (F(0),), ZERO, ZERO),)},
    {'extra': F(0)},
))
def test_malformed_or_unbounded_input_rejected_before_quadrature(change, monkeypatch):
    raw = record()
    raw.update(change)
    monkeypatch.setattr(oracle, '_gauss', lambda _: pytest.fail('rule generation reached'))
    with pytest.raises(ValueError):
        oracle.norm_squared(raw)


@pytest.mark.parametrize('order', (True, 16., 12, 32, None))
def test_no_unregistered_order_or_hidden_retry(order):
    with pytest.raises(ValueError):
        oracle.norm_squared(record(), order=order)
