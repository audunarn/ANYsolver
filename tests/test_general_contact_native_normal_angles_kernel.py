"""Exact bounded reuse of the pure angular Taylor kernel."""
from decimal import (Decimal, Inexact, InvalidOperation, localcontext,
                     ROUND_DOWN, ROUND_HALF_EVEN)
from math import pi
import pytest
from anysolver.general_contact import native_normal_angles as angles


def _reference_sincos(angle):
    """The original unshared Taylor loop, embedded as the parity oracle."""
    x = Decimal(angle)
    sine = sine_term = x
    cosine = cosine_term = Decimal(1)
    square = -x*x
    for k in range(1, 81):
        sine_term *= square/Decimal(2*k*(2*k+1))
        cosine_term *= square/Decimal((2*k-1)*2*k)
        sine += sine_term
        cosine += cosine_term
    return sine, cosine


def _corpus():
    values = [0.0, 2*pi, -2*pi, pi/2, 0.0491/.05, 1e-20, -1e-20,
              6.283185307179586, 1.5707963267948966, -0.3333333333333333,
              5.0e-324, 0.982, 2.0943951023931953]
    values += [Decimal('1.5'), Decimal('1.50'), Decimal('-0.0491'),
               Decimal('1e-40'), Decimal(pi), Decimal(2)*Decimal(pi)/3,
               Decimal('0.98200000000000000000000000000000000000000000000000')]
    return values


def test_sincos_reuse_is_bit_exact_and_repeats_return_same_tuple():
    angles._sincos_cache.clear()
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        for angle in _corpus():
            first = angles._sincos(angle)
            reference = _reference_sincos(angle)
            assert first[0].as_tuple() == reference[0].as_tuple()
            assert first[1].as_tuple() == reference[1].as_tuple()
            assert angles._sincos(angle) is first


def test_sincos_cache_key_carries_the_effective_context():
    angles._sincos_cache.clear()
    probe = 0.3333333333333333
    with localcontext() as ctx:
        ctx.prec = 50
        base = angles._sincos(probe)
    with localcontext() as ctx:
        ctx.prec = 28
        low = angles._sincos(probe)
        reference = _reference_sincos(probe)
        assert low[0].as_tuple() == reference[0].as_tuple()
        assert low[1].as_tuple() == reference[1].as_tuple()
        assert low[0] != base[0]
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_DOWN
        down = angles._sincos(probe)
        reference = _reference_sincos(probe)
        assert down[0].as_tuple() == reference[0].as_tuple()
        assert down[1].as_tuple() == reference[1].as_tuple()
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.clamp = 1
        clamped = angles._sincos(probe)
        reference = _reference_sincos(probe)
        assert clamped[0].as_tuple() == reference[0].as_tuple()
        assert clamped[1].as_tuple() == reference[1].as_tuple()
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.traps[Inexact] = True
        before = len(angles._sincos_cache)
        with pytest.raises(Inexact):
            angles._sincos(probe)
        assert len(angles._sincos_cache) == before


def test_context_signature_reflects_every_effective_setting():
    with localcontext() as ctx:
        ctx.prec = 50
        base = angles._context_signature()
        ctx.prec = 28
        assert angles._context_signature() != base
        ctx.prec = 50
        ctx.rounding = ROUND_DOWN
        assert angles._context_signature() != base
        ctx.rounding = ROUND_HALF_EVEN
        ctx.clamp = 1
        assert angles._context_signature() != base
        ctx.clamp = 0
        ctx.Emin = -60
        assert angles._context_signature() != base
        ctx.Emin = -999999
        ctx.Emax = 60
        assert angles._context_signature() != base
        ctx.Emax = 999999
        ctx.capitals = 0
        assert angles._context_signature() != base
        ctx.capitals = 1
        ctx.traps[Inexact] = True
        assert angles._context_signature() != base
        ctx.traps[Inexact] = False
        assert angles._context_signature() == base


def test_sincos_cache_stays_bounded_and_survives_clear():
    angles._sincos_cache.clear()
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        for i in range(angles._SINCOS_CACHE_LIMIT + 37):
            angles._sincos(Decimal(i)/Decimal(3))
        assert len(angles._sincos_cache) <= angles._SINCOS_CACHE_LIMIT
        value = angles._sincos(Decimal(7)/Decimal(3))
        reference = _reference_sincos(Decimal(7)/Decimal(3))
        assert value[0].as_tuple() == reference[0].as_tuple()
        assert value[1].as_tuple() == reference[1].as_tuple()


def test_precise_normal_angles_value_parity_with_reference_kernel():
    angles._sincos_cache.clear()
    field = angles.PreciseNormalAngles(.0491, 0., .8, .05, 0.)
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        for angle in (0.3, Decimal(pi)/7, 2*pi, 0.982):
            sine, cosine = _reference_sincos(angle)
            expected = field.offset+field.cosine*cosine+field.sine*sine
            assert field.value(angle).as_tuple() == expected.as_tuple()


def _raised_flags(context):
    return frozenset(flag for flag, value in context.flags.items() if value)


def test_sincos_hit_reproduces_original_context_flags():
    angles._sincos_cache.clear()
    probe = Decimal('0.3333333333333333')
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        ctx.clear_flags()
        warm = angles._sincos(probe)
        warm_flags = _raised_flags(ctx)
        ctx.clear_flags()
        hit = angles._sincos(probe)
        hit_flags = _raised_flags(ctx)
        ctx.clear_flags()
        fresh = _reference_sincos(probe)
        fresh_flags = _raised_flags(ctx)
    assert warm_flags == fresh_flags
    assert hit_flags == fresh_flags
    assert hit_flags
    assert hit is warm
    assert hit[0].as_tuple() == fresh[0].as_tuple()
    assert hit[1].as_tuple() == fresh[1].as_tuple()


def test_sincos_hit_preserves_preexisting_unrelated_flag():
    angles._sincos_cache.clear()
    probe = Decimal('0.982')
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        ctx.clear_flags()
        angles._sincos(probe)
        ctx.clear_flags()
        ctx.flags[InvalidOperation] = True
        hit = angles._sincos(probe)
        hit_flags = _raised_flags(ctx)
        ctx.clear_flags()
        ctx.flags[InvalidOperation] = True
        fresh = _reference_sincos(probe)
        fresh_flags = _raised_flags(ctx)
    assert InvalidOperation in hit_flags
    assert hit_flags == fresh_flags
    assert hit[0].as_tuple() == fresh[0].as_tuple()
    assert hit[1].as_tuple() == fresh[1].as_tuple()


def test_sincos_trapped_raise_preserves_flags_and_stores_no_entry():
    angles._sincos_cache.clear()
    probe = Decimal('0.3333333333333333')
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        ctx.traps[Inexact] = True
        before = len(angles._sincos_cache)
        ctx.clear_flags()
        with pytest.raises(Inexact):
            angles._sincos(probe)
        trapped_flags = _raised_flags(ctx)
        assert Inexact in trapped_flags
        assert len(angles._sincos_cache) == before
        ctx.clear_flags()
        with pytest.raises(Inexact):
            _reference_sincos(probe)
        assert _raised_flags(ctx) == trapped_flags
        ctx.clear_flags()
        with pytest.raises(Inexact):
            angles._sincos(probe)
        assert _raised_flags(ctx) == trapped_flags
        assert len(angles._sincos_cache) == before


def test_sincos_hit_sets_full_loop_flags_after_dirty_warm():
    angles._sincos_cache.clear()
    probe = Decimal('0.3333333333333333')
    with localcontext() as ctx:
        ctx.prec = angles.PRECISION
        ctx.clear_flags()
        fresh = _reference_sincos(probe)
        fresh_flags = _raised_flags(ctx)
        assert fresh_flags
        ctx.clear_flags()
        for flag in fresh_flags:
            ctx.flags[flag] = True
        warm = angles._sincos(probe)
        assert _raised_flags(ctx) == fresh_flags
        ctx.clear_flags()
        hit = angles._sincos(probe)
        hit_flags = _raised_flags(ctx)
    assert hit_flags == fresh_flags
    assert hit is warm
    assert hit[0].as_tuple() == fresh[0].as_tuple()
    assert hit[1].as_tuple() == fresh[1].as_tuple()
