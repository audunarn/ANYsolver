"""Analytical identities for the independent Decimal Green-kernel oracle."""

from decimal import Decimal,localcontext
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_trace_green_oracle as oracle


def test_high_precision_quadrature_integrates_polynomials_independently():
    with localcontext() as context:
        context.prec=70
        rule=oracle._gauss(12,70)
        for power in (0,1,8,23):
            observed=sum(weight*x**power for x,weight in rule)
            assert abs(observed-Decimal(1)/(power+1))<Decimal('1e-58')


def test_green_endpoints_and_partition_unity():
    n=4
    gram=oracle.green_gram(n,12,70)
    expected=((1/np.tanh(1.),1/np.sinh(1.)),(1/np.sinh(1.),1/np.tanh(1.)))
    np.testing.assert_allclose(gram[-2:,-2:],expected,rtol=2e-15,atol=2e-15)
    measure=np.full(n+1,1/n); measure[[0,-1]]*=.5
    assert measure@gram[:n+1,:n+1]@measure==pytest.approx(1.,rel=2e-15)
    np.testing.assert_allclose(measure@gram[:n+1,-2:],1.,rtol=2e-15)
    np.testing.assert_allclose(gram,gram.T,rtol=0,atol=0)
    assert np.linalg.eigvalsh(gram)[0]>0


@pytest.mark.parametrize('args',((1,12,70),(4,10,70),(4,12,20)))
def test_invalid_oracle_request_is_rejected(args):
    with pytest.raises(ValueError):
        oracle.green_gram(*args)
