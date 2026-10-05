"""Small manufactured polynomial and pad-adjoint checks; no saved cases."""
from fractions import Fraction

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss

from scripts import _b3_e4_f03_primal_exact_pose as exact
from scripts import _b3_e4_f03_spatial_contract as c
from scripts import _b3_e4_f03_spatial_fields as fields


def _model(n=2, index=None, value=1., eta=(0.,0.,0.)):
    q=np.zeros(2*(n*n-1),dtype=np.float64)
    if index is not None: q[index]=value
    e=np.asarray(eta,dtype=np.float64)
    return fields.model_from_saved(n,q,e,exact.reconstruct(n,q))


@pytest.mark.parametrize('n',[2,3])
def test_manufactured_shell_stress_divergence_and_support(n):
    # ux=(1-X²), uy=0, an exact low polynomial in every admitted space.
    model=_model(n,index=0)
    x=np.array([-.5,.1,.75,1.5]);y=np.array([-.3,.15,0.,.4])
    f=fields.shell_fields(model,x,y)
    X=x-.5
    assert f['displacement'].shape==(4,2)
    np.testing.assert_allclose(f['displacement'][:,0],1-X*X,atol=1e-15)
    np.testing.assert_array_equal(f['displacement'][:,1],0)
    np.testing.assert_allclose(f['strain'][:,0],-2*X,atol=1e-15)
    np.testing.assert_array_equal(f['strain'][:,1:],0)
    np.testing.assert_allclose(f['stress'][:,0],-2*X*c.THICKNESS*c.PLANE[0,0],rtol=1e-15)
    np.testing.assert_allclose(f['stress'][:,1],-2*X*c.THICKNESS*c.PLANE[1,0],rtol=1e-15)
    np.testing.assert_array_equal(f['stress'][:,2],0)
    np.testing.assert_allclose(f['divergence'][:,0],-2*c.THICKNESS*c.PLANE[0,0],rtol=1e-15)
    np.testing.assert_array_equal(f['divergence'][:,1],0)
    np.testing.assert_array_equal(f['displacement'][[0,-1]],0)


def test_independent_mixed_derivative_and_rigid_zero_strain():
    # ux=(1-X²)*Y; inspect analytic engineering shear and div_y.
    model=_model(3,index=1)
    x=np.array([-.27,.56,1.2]);y=np.array([-.35,.11,.3])
    f=fields.shell_fields(model,x,y);X=x-.5;Y=2*y
    np.testing.assert_allclose(f['strain'][:,0],-2*X*Y,atol=1e-15)
    np.testing.assert_allclose(f['strain'][:,2],2*(1-X*X),atol=1e-15)
    np.testing.assert_allclose(f['divergence'][:,0],
                               -2*Y*c.THICKNESS*c.PLANE[0,0],rtol=1e-14)
    np.testing.assert_allclose(f['divergence'][:,1],
                               -4*X*c.THICKNESS*(c.PLANE[2,2]+c.PLANE[1,0]),rtol=1e-14)
    # The independent tensor derivative path annihilates planar rigidity;
    # these manufactured tensors are not a supported Ritz displacement.
    zero=((Fraction(0),Fraction(0)),(Fraction(0),Fraction(0)))
    one=((Fraction(1),Fraction(0)),(Fraction(0),Fraction(0)))
    y_tensor=((Fraction(0),Fraction(1)),(Fraction(0),Fraction(0)))
    x_tensor=((Fraction(1,2),Fraction(0)),(Fraction(1),Fraction(0)))
    rigid_ux=fields._tensor_scale(y_tensor,Fraction(-1,2))
    rigid_uy=x_tensor
    xx=fields._tensor_dx(rigid_ux)
    yy=fields._tensor_dy(rigid_uy)
    shear=fields._tensor_add(fields._tensor_dy(rigid_ux),fields._tensor_dx(rigid_uy))
    assert xx==yy==shear==zero
    assert one != zero


def test_beam_polynomial_resultants_density_and_atoms():
    # For ux phi_00, pose b_u=E_pad[1-(s+xi-.5)^2].
    m=_model(2,index=0,eta=(11.,-7.,13.))
    s=np.array([0.,.3,.8,1.]);t=s-.5
    N=-2*c.EA*t
    np.testing.assert_allclose(fields.section_resultants(m,s)[:,0],N,rtol=1e-15)
    np.testing.assert_allclose(fields.line_density(m,s)[:,0],-2*c.EA,rtol=1e-15)
    np.testing.assert_allclose(m.atoms[0,0],c.EA-11.)
    np.testing.assert_allclose(m.atoms[1,0],c.EA)
    np.testing.assert_allclose(m.atoms[0,1:],(7.,-13.))
    assert m.atom_coefficients[0][0]==c.Q_EA-Fraction(11)
    assert m.held_J==c.Q_J and m.gamma==c.Q_GAMMA
    assert m.gamma!=1


def test_clipped_area_adjoint_root_once_and_rigid_gamma():
    model=_model(2,eta=(10.,-20.,30.))
    nodes,weights=leggauss(24)
    force=np.zeros(2);moment=0.;channels=np.zeros((3,2))
    for cell,(xl,xh,yl,yh) in enumerate(c.CELLS):
        xx=(float(xl+xh)+float(xh-xl)*nodes)/2
        yy=(float(yl+yh)+float(yh-yl)*nodes)/2
        xg,yg=np.meshgrid(xx,yy,indexing='xy')
        w=np.outer(weights,weights)*float((xh-xl)*(yh-yl))/4
        loads=fields.area_load(model,xg,yg,cell)
        channels+=np.einsum('ij,ijab->ab',w,loads)
        force+=np.einsum('ij,ija->a',w,loads.sum(axis=-2))
        moment+=np.sum(w*(xg*loads.sum(axis=-2)[...,1]-
                          yg*loads.sum(axis=-2)[...,0]))
    omega=c.OMEGA
    expected_fy=c.F0+c.F0/4*np.sin(omega*c.L0)/omega+20.
    expected_m=c.F0*c.L0/2+c.F0/4*(
        c.L0*np.sin(omega*c.L0)/omega+(np.cos(omega*c.L0)-1)/omega**2)
    expected_m-=30*float(c.Q_GAMMA)
    np.testing.assert_allclose(channels[1],(-10.,20.),atol=1e-8)
    np.testing.assert_array_equal(channels[2],0)
    np.testing.assert_allclose(force,(-10.,expected_fy),atol=1e-7)
    np.testing.assert_allclose(moment,expected_m,atol=1e-7)
    # The selected branch is one-sided at a translated pad edge.
    left=fields.area_load(model,-.25,-.23,9)
    right=fields.area_load(model,-.25,-.23,10)
    assert np.linalg.norm(left-right)>0


def test_nonconstant_line_yaw_and_both_atoms_rigid_work():
    n=3;m=n*n-1
    q=np.zeros(2*m,dtype=np.float64)
    q[1]=1e-6                # ux=(1-X²)Y gives nonconstant yaw.
    q[m+0]=2e-6              # uy=(1-X²) gives a second yaw contribution.
    eta=np.array([31.,-23.,17.])
    model=fields.model_from_saved(n,q,eta,exact.reconstruct(n,q))
    assert model.density_coefficients[2][1:] != (Fraction(0),)*(len(model.density_coefficients[2])-1)
    nodes,weights=leggauss(24)
    integrated=np.zeros(3)
    for cell,(xl,xh,yl,yh) in enumerate(c.CELLS):
        xx=(float(xl+xh)+float(xh-xl)*nodes)/2
        yy=(float(yl+yh)+float(yh-yl)*nodes)/2
        xg,yg=np.meshgrid(xx,yy,indexing='xy')
        w=np.outer(weights,weights)*float((xh-xl)*(yh-yl))/4
        total=fields.area_load(model,xg,yg,cell).sum(axis=-2)
        integrated+=np.array([np.sum(w*total[...,0]),np.sum(w*total[...,1]),
                              np.sum(w*(xg*total[...,1]-yg*total[...,0]))])
    ss=(nodes+1)*c.L0/2
    ds=weights*c.L0/2
    d=fields.line_density(model,ss)
    atoms=model.atoms
    expected=np.array([np.dot(ds,d[:,0])+atoms[:,0].sum(),
                       np.dot(ds,d[:,1])+atoms[:,1].sum(),
                       np.dot(ds,ss*d[:,1]+float(model.gamma)*d[:,2])+
                       atoms[1,1]+float(model.gamma)*atoms[:,2].sum()])
    np.testing.assert_allclose(integrated,expected,rtol=3e-13,atol=3e-7)


def test_binding_ownership_invalid_inputs_and_cell_closure():
    q=np.zeros(6,dtype=np.float64);eta=np.array([3.,4.,5.])
    pose=exact.reconstruct(2,q)
    model=fields.model_from_saved(2,q,eta,pose)
    q[0]=1.;eta[0]=99.
    assert model.q[0]==0 and model.eta[0]==3
    atoms=model.atoms
    assert not atoms.flags.writeable
    with pytest.raises(ValueError): atoms.setflags(write=True)
    with pytest.raises(ValueError,match='mismatch'):
        fields.model_from_saved(2,q,eta,pose)
    with pytest.raises(ValueError):
        fields.area_load(model,0.,0.,45)
    with pytest.raises(ValueError,match='closure'):
        fields.area_load(model,1.,0.,0)
    with pytest.raises(ValueError):
        fields.shell_fields(model,np.nan,0.)
    with pytest.raises(ValueError):
        fields.line_density(model,1.01)
