"""Independent analytical H1-dual oracles; no structural case execution."""

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import linalg

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_trace_dual as dual


@pytest.mark.parametrize('family',('P1','hybrid','enriched'))
def test_functional_rows_reproduce_constant_and_affine_actions(family):
    n=4
    b,measures=dual.functional_rows(n,family,8)
    x=np.linspace(0.,1.,b.shape[1])
    np.testing.assert_allclose(b@np.ones_like(x),measures,rtol=2e-15,atol=1e-15)
    if family!='hybrid':
        expected=np.array((1/(6*n*n),1/n**2,2/n**2,3/n**2,
                           1/(2*n)-1/(6*n*n)))
        if family=='enriched':
            expected=np.r_[expected,0.,1.]
    else:
        expected=np.array((1/n**2,2/n**2,3/n**2,0.,1.))
    np.testing.assert_allclose(b@x,expected,rtol=2e-15,atol=1e-15)


def test_constant_density_has_exact_unit_dual_norm():
    gram=dual.dual_gram(4,'P1',16,normalized=False)
    assert np.sum(gram)==pytest.approx(1.,rel=3e-12)


def test_endpoint_gram_converges_to_independent_neumann_green_function():
    expected=np.array(((1/np.tanh(1.),1/np.sinh(1.)),
                       (1/np.sinh(1.),1/np.tanh(1.))))
    coarse=dual.dual_gram(4,'hybrid',8,normalized=False)[-2:,-2:]
    fine=dual.dual_gram(4,'hybrid',32,normalized=False)[-2:,-2:]
    assert np.linalg.norm(fine-expected)<np.linalg.norm(coarse-expected)/10
    np.testing.assert_allclose(fine,expected,rtol=1e-5,atol=1e-6)


@pytest.mark.parametrize('family',('P1','hybrid','enriched'))
def test_auxiliary_norm_is_positive_and_increases_under_nested_refinement(family):
    coarse=dual.dual_gram(4,family,4)
    fine=dual.dual_gram(4,family,8)
    assert np.linalg.norm(fine-fine.T)<1e-11
    assert np.linalg.eigvalsh(fine)[0]>0
    # Galerkin Riesz approximation is from below as the trace space grows.
    ratios=linalg.eigvalsh(fine,coarse)
    assert min(ratios)>1-1e-10
    assert np.all(np.isfinite(ratios))


@pytest.mark.parametrize('args',((1,'P1',8),(4,'P0',8),(4,'hybrid',1),
                                (4,'P1',129),(True,'P1',8)))
def test_invalid_dual_layout_is_rejected(args):
    with pytest.raises(ValueError):
        dual.dual_gram(*args)
