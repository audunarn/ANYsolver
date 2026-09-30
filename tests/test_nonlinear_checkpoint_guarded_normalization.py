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


def test_exact_dictionary_avoids_redundant_observation_checks():
    observed = []
    payload = {"nested": {"values": [1, 0.0, -0.0, True, None, "value"]}}
    normalized = _normalize_json(payload, _exact_guard=lambda *a, **k: observed.append(k),
                                 _guard_model=object())
    assert normalized == payload and normalized is not payload
    assert normalized["nested"] is not payload["nested"]
    assert observed == []


@pytest.mark.parametrize("member_kind", ["mapping", "scalar", "sequence"])
def test_exact_dictionary_retains_nested_effectful_member_boundary(member_kind):
    observed = []

    class ChangingMapping(dict):
        def items(self):
            observed.append("mapping")
            return super().items()

    class ChangingInteger(int):
        def __int__(self):
            observed.append("scalar")
            return super().__int__()

    class ChangingSequence(list):
        def __iter__(self):
            observed.append("sequence")
            return super().__iter__()

    members = {"mapping": ChangingMapping(value=1), "scalar": ChangingInteger(3),
               "sequence": ChangingSequence([1.0])}

    def guard(_model, *, context):
        if observed:
            raise RuntimeError(context)

    with pytest.raises(RuntimeError, match=member_kind + " observation"):
        _normalize_json({"plain": {"effectful": members[member_kind]}},
                        _exact_guard=guard, _guard_model=object())
    assert observed == [member_kind]


def test_nonexact_dictionary_key_retains_mapping_check():
    class StringKey(str):
        pass

    observed = []
    _normalize_json({StringKey("value"): 1},
                    _exact_guard=lambda *a, **k: observed.append(k["context"]),
                    _guard_model=object())
    assert len(observed) == 1 and "mapping observation" in observed[0]
