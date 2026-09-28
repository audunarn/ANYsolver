"""Adversarial checkpoint observations retain their authority boundary."""

import pytest

from anysolver.nonlinear_restart import _normalize_json


def test_custom_sequence_iteration_is_guarded_after_observation():
    observed = []

    class ChangingSequence(list):
        def __iter__(self):
            observed.append("iteration")
            return super().__iter__()

    def guard(_model, *, context):
        if observed:
            raise RuntimeError(context)

    with pytest.raises(RuntimeError, match="sequence observation"):
        _normalize_json(ChangingSequence([1.0]), _exact_guard=guard,
                        _guard_model=object())
    assert observed == ["iteration"]


def test_custom_scalar_conversion_is_guarded_after_observation():
    observed = []

    class ChangingInteger(int):
        def __int__(self):
            observed.append("conversion")
            return super().__int__()

    def guard(_model, *, context):
        if observed:
            raise RuntimeError(context)

    with pytest.raises(RuntimeError, match="scalar observation"):
        _normalize_json(ChangingInteger(3), _exact_guard=guard,
                        _guard_model=object())
    assert observed == ["conversion"]
