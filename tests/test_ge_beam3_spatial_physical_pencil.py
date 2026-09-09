from decimal import Decimal as D,localcontext
from copy import deepcopy
import numpy as np
import pytest
from scipy.linalg import eigh
from docs.reference_cases.ge_beam3_spatial_physical_pencil import spectrum,assemble,trace_solve


def packet():
    return dict(left=np.eye(3).tolist(),right=np.eye(3).tolist(),
        geometric=[[-2.,0.,1.],[0.,8.,2.],[1.,2.,4.]],kinetic=[[1.,0.,0.],[0.,2.,0.]],
        free_dofs=[0,1,2],algebraic_dofs=[2])


@pytest.mark.parametrize('digits',(80,100))
def test_exact_schur_and_signed_physical_modes(digits):
    p=packet();before=deepcopy(p)
    with localcontext() as context:
        context.prec=digits;made=assemble(p,digits,lambda:None)
        assert made['reduced']==[[D('-1.2'),D('-.4')],[D('-.4'),D('8.2')]]
        assert made['reduced_mass']==[[D(1),D(0)],[D(0),D(4)]]
        assert made['trace_map']==[[D('.2'),D('.4')]]
    result=spectrum(p,digits,2)
    expected=eigh(np.array([[-1.2,-.4],[-.4,8.2]]),np.diag([1.,4.]))[0]
    np.testing.assert_allclose(result['eigenvalues'],expected,rtol=1e-11,atol=1e-11)
    assert result['eigenvalues'][0]<0 and max(result['original_residuals'])<1e-11
    assert result['mass_orthogonality']<1e-11 and result['original_ritz_error']<1e-11 and p==before


def test_original_factor_cancellation_not_rounded_packet():
    p=dict(left=[[1e8,1.],[0.,1.]],right=np.eye(2).tolist(),
        geometric=[[-1e16,-1e8],[-1e8,0.]],kinetic=np.eye(2).tolist(),free_dofs=[0,1],algebraic_dofs=[])
    result=spectrum(p,80,2)
    assert result['eigenvalues']==[0.,2.]


@pytest.mark.parametrize('kind',('mass','free','trace','nan','shape','type','singular'))
def test_invalid_saved_factors(kind):
    p=packet()
    if kind=='mass':p['kinetic'][0][2]=1.
    elif kind=='free':p['free_dofs']=[0,1,1]
    elif kind=='trace':p['algebraic_dofs']=[3]
    elif kind=='nan':p['geometric'][0][0]=float('nan')
    elif kind=='shape':p['left'][0].pop()
    elif kind=='type':p['right'][0][0]=True
    else:p['geometric'][2][2]=-1.
    with pytest.raises((ValueError,np.linalg.LinAlgError)):spectrum(p,80,2)


def test_trace_solve_original_residual_and_cancellation():
    with localcontext() as context:
        context.prec=80
        a=[[D(3),D(1)],[D(1),D(2)]];b=[[D(1),D(0)],[D(0),D(1)]]
        x,error,pivots=trace_solve(a,b)
        expected=[[D('.4'),D('-.2')],[D('-.2'),D('.6')]]
        assert max(abs(a-b) for row,ref in zip(x,expected) for a,b in zip(row,ref))<D('1e-60')
        assert D(error)<D('1e-60')
        with pytest.raises(ValueError):trace_solve([[D(-1)]],[[D(1)]])
        def stop():raise RuntimeError('cancelled')
        with pytest.raises(RuntimeError):trace_solve(a,b,stop)
