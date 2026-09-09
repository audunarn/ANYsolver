from fractions import Fraction as F
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_piecewise_physical_reference as ref


@pytest.mark.parametrize('order',(4,8,12))
def test_clamps_interface_continuity_and_nested_fields(order):
    for x in (-1.,1.):assert not ref.basis(x,1.,order)[0].any()
    for segment in range(3):
        left=ref.local_basis(segment,1.,1.,order)[0]
        right=ref.local_basis(segment+1,-1.,1.,order)[0]
        np.testing.assert_array_equal(left,right)
        assert np.linalg.matrix_rank(left)==6
    slots=ref.indices(order)
    for segment in range(4):
        q,dq=ref.local_basis(segment,.271,1.3,order)
        big,dbig=ref.local_basis(segment,.271,1.3,12)
        np.testing.assert_array_equal(q,big[:,slots]);np.testing.assert_array_equal(dq,dbig[:,slots])


def test_derivatives_all_components_and_domains():
    for segment in range(4):
        t=.137;jac=1.2;h=1e-6
        q,dq=ref.local_basis(segment,t,jac,12)
        numerical=(ref.local_basis(segment,t+h,jac,12)[0]-ref.local_basis(segment,t-h,jac,12)[0])/(2*h)*4/jac
        np.testing.assert_allclose(dq,numerical,rtol=1e-7,atol=1e-7)
        assert q.shape==(6,306) and np.linalg.matrix_rank(q)==6
    for args in ((-1,0.,1.,4),(0,2.,1.,4),(0,0.,0.,4),(0,0.,1.,True)):
        with pytest.raises(ValueError):ref.local_basis(*args)


def legendre(n):
    polynomials=[[F(1)],[F(0),F(1)]]
    for k in range(1,n):
        a=[F(0)]+[F(2*k+1,k+1)*x for x in polynomials[k]]
        for j,x in enumerate(polynomials[k-1]):a[j]-=F(k,k+1)*x
        polynomials.append(a)
    return polynomials[:n]


@pytest.mark.parametrize('order',(4,8,12))
def test_exact_local_polynomial_completeness_and_bending_compatibility(order):
    # Fraction coefficient algebra, independent of the numerical basis routine.
    columns=[[F(1,2),F(-1,2)],[F(1,2),F(1,2)]]
    for polynomial in legendre(order):
        b=polynomial+[F(0),F(0)]
        for k,x in enumerate(polynomial):b[k+2]-=x
        assert sum(b)==0 and sum(v*(-1)**i for i,v in enumerate(b))==0
        columns.append(b)
    size=order+2;a=[[col[i] if i<len(col) else F(0) for col in columns] for i in range(size)]
    augmented=[row+[F(i==j) for j in range(size)] for i,row in enumerate(a)]
    for j in range(size):
        pivot=next(i for i in range(j,size) if augmented[i][j]);augmented[j],augmented[pivot]=augmented[pivot],augmented[j]
        v=augmented[j][j];augmented[j]=[x/v for x in augmented[j]]
        for i in range(size):
            if i!=j:
                v=augmented[i][j];augmented[i]=[x-v*y for x,y in zip(augmented[i],augmented[j])]
    inverse=[row[size:] for row in augmented]
    # w=(1-t^2)^2 and theta=dw/dt share the exact trial span; this is a straight
    # compatibility test, not an assumed finite curved exact patch.
    for polynomial in ([F(1),F(0),F(-2),F(0),F(1)],[F(0),F(-4),F(0),F(4)]):
        coeff=polynomial+[F(0)]*(size-len(polynomial))
        coordinates=[sum((x*y for x,y in zip(row,coeff)),F(0)) for row in inverse]
        assert [sum((x*y for x,y in zip(row,coordinates)),F(0)) for row in a]==coeff
        # Independently reconstructed coefficients must agree with the actual
        # numerical basis, not only with a second symbolic description.
        for t in (F(-2,3),F(1,7),F(3,4)):
            q,dq=ref.local_basis(1,float(t),1.,order);width=3+4*order
            x=np.zeros(6*width);x[0]=float(coordinates[0]);x[1]=float(coordinates[1])
            x[3+order:3+2*order]=list(map(float,coordinates[2:]))
            expected=sum((v*t**k for k,v in enumerate(polynomial)),F(0))
            derivative=4*sum((k*v*t**(k-1) for k,v in enumerate(polynomial) if k),F(0))
            assert abs(float(q[0]@x)-float(expected))<1e-11
            assert abs(float(dq[0]@x)-float(derivative))<1e-11


def profile():
    return dict(profiles=[dict(quadrature=q,bubbles_per_segment=n,result=dict(eigenvalues=[-4.,1.,9.,16.,25.,36.])) for q,n in ref.PROFILES])


@pytest.mark.parametrize('kind',('inventory','sign','refinement','quadrature','zero'))
def test_unchanged_reference_acceptance_and_mutations(kind):
    value=profile();assert ref.validate(value)==(0.,0.)
    if kind=='inventory':value['profiles'].pop()
    elif kind=='sign':value['profiles'][0]['result']['eigenvalues'][0]=4.
    elif kind=='refinement':value['profiles'][1]['result']['eigenvalues'][1]=1.1
    elif kind=='quadrature':value['profiles'][3]['result']['eigenvalues'][1]=1.001
    else:value['profiles'][0]['result']['eigenvalues'][1]=0.
    with pytest.raises(ValueError):ref.validate(value)


@pytest.mark.parametrize('sign',('plus','minus'))
def test_saved_native_spectra_not_recomputed(sign,tmp_path):
    from docs.reference_cases.ge_beam3_piecewise_physical_worker import native_source
    value=native_source(sign)
    assert value['eigenvalues'][0]<0 and value['digits']==100 and len(value['full_modes'])==6
    (tmp_path/'manifest.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError):native_source(sign,tmp_path)
