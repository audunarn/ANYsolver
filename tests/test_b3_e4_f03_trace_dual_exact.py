"""Unit checks of the analytic free-end H1 scalar Gram, without equilibrium."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_trace_dual as finite_element
import _b3_e4_f03_trace_dual_exact as exact


@pytest.mark.parametrize("n",(2,4,8,16))
def test_green_endpoint_block_partition_and_cross_integrals(n):
    gram=exact.dual_gram(n,"enriched")
    meta=exact.metadata(n,"enriched")
    measures=np.asarray(meta.row_measures[:n+1])
    endpoint=np.array([[math.cosh(1)/math.sinh(1),1/math.sinh(1)],
                       [1/math.sinh(1),math.cosh(1)/math.sinh(1)]])
    np.testing.assert_allclose(gram[-2:,-2:],endpoint,rtol=2e-13,atol=2e-13)
    assert float(measures@gram[:n+1,:n+1]@measures)==pytest.approx(1,abs=2e-12)
    np.testing.assert_allclose(measures@gram[:n+1,-2:],[1,1],
                               rtol=0,atol=2e-12)
    roots,weights=np.polynomial.legendre.leggauss(12)
    for j in range(n+1):
        expected=np.zeros(2)
        for k in range(n):
            s=(k+(1+roots)/2)/n
            hat=np.maximum(0,1-n*np.abs(s-j/n))
            expected+=np.array([
                np.dot(weights,hat*np.cosh(1-s)/math.sinh(1)),
                np.dot(weights,hat*np.cosh(s)/math.sinh(1))])/(2*n*measures[j])
        np.testing.assert_allclose(gram[j,-2:],expected,rtol=0,atol=2e-12)


@pytest.mark.parametrize("n",(2,4,8,16))
def test_canonical_selection_raw_normalized_symmetry_and_spd(n):
    enriched=exact.dual_gram(n,"enriched")
    raw=exact.dual_gram(n,"enriched",normalized=False)
    measures=np.asarray(exact.metadata(n,"enriched").row_measures)
    np.testing.assert_allclose(raw,measures[:,None]*enriched*measures[None,:],
                               rtol=2e-11,atol=2e-12)
    for family in ("P1","hybrid","enriched"):
        meta=exact.metadata(n,family)
        gram=exact.dual_gram(n,family)
        np.testing.assert_array_equal(gram,
            enriched[np.ix_(meta.selected_enriched_rows,meta.selected_enriched_rows)])
        assert np.max(np.abs(gram-gram.T))<2e-12
        np.linalg.cholesky(gram)
        diagnostic=exact.gram_diagnostics(gram)
        assert math.isfinite(diagnostic["condition_2"])
        assert diagnostic["antisymmetry_max_abs"]<2e-12
    assert exact.metadata(n,"hybrid").selected_enriched_rows==(
        tuple(range(1,n))+(n+1,n+2))
    assert exact.metadata(n,"enriched").series_function_tail_bound<1e-30


@pytest.mark.parametrize("n",(2,4,8,16))
@pytest.mark.parametrize("family",("P1","hybrid","enriched"))
def test_nested_auxiliary_fe_norms_below_analytic(n,family):
    analytical=exact.dual_gram(n,family)
    coarse=finite_element.dual_gram(n,family,32)
    fine=finite_element.dual_gram(n,family,64)
    scale=max(1.,np.linalg.norm(analytical,2))
    # Eigenvalues of differences of near-equal full Grams inherit the FE
    # factorization/subtraction floor (observed <=4e-9 at n=16); this is a
    # numerical unit check, not a certified Loewner proof or physical gate.
    floor=5e-10*scale
    assert np.linalg.eigvalsh(fine-coarse)[0]>=-floor
    assert np.linalg.eigvalsh(analytical-fine)[0]>=-floor


@pytest.mark.parametrize("n,family",((1,"P1"),(17,"hybrid"),(True,"P1"),
                                      (4,"other")))
def test_admission_is_bounded(n,family):
    with pytest.raises(ValueError,match="bounded analytic"):
        exact.dual_gram(n,family)
