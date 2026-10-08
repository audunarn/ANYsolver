"""Norm comparison identities independent of a structural case."""

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_norm_validation as validation


def test_relative_operator_error_is_invariant_under_invertible_congruence():
    b=np.array(((2.,.3),(.3,1.)))
    a=b+np.array(((.001,.0001),(.0001,-.002)))
    t=np.array(((4.,2.),(0.,.2)))
    expected=validation.relative_operator_error(a,b)
    assert validation.relative_operator_error(t@a@t.T,t@b@t.T)==pytest.approx(expected,rel=1e-11)


def test_antisymmetric_error_is_not_silently_discarded():
    b=np.eye(2)
    a=b+np.array(((0.,.003),(-.003,0.)))
    assert validation.relative_operator_error(a,b)==pytest.approx(.003)


def test_norm_inventory_rejects_adaptive_or_structural_inputs():
    with pytest.raises(ValueError,match='registered norm inventory'):
        validation.compare(128)
