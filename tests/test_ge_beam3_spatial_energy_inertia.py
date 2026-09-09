from fractions import Fraction as F
from decimal import Decimal as D
import pytest
from docs.reference_cases.ge_beam3_spatial_energy_inertia import exact_energy_matrix, audit
from docs.reference_cases.ge_beam3_sparse_inertia_audit import audit as original


@pytest.mark.parametrize('x', ((1,2,3),(-3,5,9),(F(1,3),F(-7,13),F(17,31))))
def test_exact_polarization_preserves_all_terms(x):
    h=[[.2,.7,.1],[.7000000000000001,-.3,.2],[.10000000000000002,.2,4.]]
    s=exact_energy_matrix(h)
    def quadratic(a):return sum(F(x[i])*F(a[i][j])*F(x[j]) for i in range(3) for j in range(3))
    assert quadratic(h)==quadratic(s)
    assert s[0][1]==s[1][0] and F(h[0][1])!=F(h[1][0])
    changed=[row[:] for row in s];changed[0][1]+=F(1,100)
    assert quadratic(changed)!=quadratic(h)


def factors(h):
    return ([[1.,0.],[0.,1.]],[[1.,0.],[0.,1.]],h,[[1.,0.],[0.,1.]],(0,1),(),(0.,))


@pytest.mark.parametrize('digits',(80,100))
def test_roundoff_asymmetry_and_original_rejection(digits):
    h=[[0.,.3],[.30000000000000004,0.]]
    with pytest.raises(ValueError,match='symmetric geometric'):original(*factors(h),digits=digits)
    before=[row[:] for row in h];result=audit(*factors(h),digits=digits)
    assert h==before and result['rows'][0]['negative']==0
    assert result['quadratic_form_preserved'] and not result['raw_geometric_symmetric']
    assert D(result['raw_skew_normalized'])>0 and not result['certified_intervals']
    assert result['rows'][0]['positive']==2


def test_true_negative_energy_and_large_skew_rejection():
    assert audit(*factors([[-2.,.3],[.30000000000000004,0.]]))['rows'][0]['negative']==1
    with pytest.raises(ValueError,match='conservative symmetry'):
        audit(*factors([[0.,.3],[.31,0.]]))


def test_symmetric_original_result_unchanged():
    args=factors([[0.,.3],[.3,0.]])
    assert audit(*args)['rows']==original(*args)['rows']
