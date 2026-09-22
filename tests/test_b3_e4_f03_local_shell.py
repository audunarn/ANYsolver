"""Synthetic exact patches and separately integrated classical membrane oracle."""
from fractions import Fraction as F
import math

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_shell as local
from scripts import _b3_e4_f03_local_moments as moments
from scripts import _b3_e4_f03_spatial_contract as c


RECT=moments.Rectangle(F(-3,10),F(7,10),F(-2,5),F(1,5))


def direct_shapes(p,z):
    nodes=np.linspace(0,1,p+1);values=[];derivatives=[]
    for i,ni in enumerate(nodes):
        values.append(math.prod((z-nj)/(ni-nj) for j,nj in enumerate(nodes) if j!=i))
        derivatives.append(sum(1/(ni-nodes[k])*math.prod((z-nj)/(ni-nj)
            for j,nj in enumerate(nodes) if j not in (i,k))
            for k in range(p+1) if k!=i))
    return np.array(values),np.array(derivatives)


def quadrature_stiffness(rect,p):
    nodes,weights=np.polynomial.legendre.leggauss(p+2)
    nodes=(nodes+1)/2;weights=weights/2
    hx=float(rect.x1-rect.x0);hy=float(rect.y1-rect.y0)
    nc=(p+1)**2;result=np.zeros((2*nc,2*nc))
    for x,wx in zip(nodes,weights):
        vx,dx=direct_shapes(p,x)
        for y,wy in zip(nodes,weights):
            vy,dy=direct_shapes(p,y)
            gradx=np.outer(vy,dx).ravel()/hx
            grady=np.outer(dy,vx).ravel()/hy
            b=np.zeros((3,2*nc))
            b[0,:nc]=gradx;b[1,nc:]=grady
            b[2,:nc]=grady;b[2,nc:]=gradx
            result+=wx*wy*hx*hy*c.THICKNESS*(b.T@c.PLANE@b)
    return result


def coordinates(rect,p):
    return tuple((rect.x0+(rect.x1-rect.x0)*F(i,p),
                  rect.y0+(rect.y1-rect.y0)*F(j,p))
                 for j in range(p+1) for i in range(p+1))


@pytest.mark.parametrize('p',[1,2,3])
def test_exact_stiffness_against_independent_gauss_and_rigid_modes(p):
    exact=local.stiffness_exact(RECT,p);k=local.stiffness(RECT,p)
    oracle=quadrature_stiffness(RECT,p)
    assert np.linalg.norm(k-oracle)/np.linalg.norm(k)<3e-15
    assert all(exact[i][j]==exact[j][i] for i in range(len(exact)) for j in range(len(exact)))
    xy=coordinates(RECT,p);n=len(xy)
    modes=((F(1),)*n+(F(0),)*n,(F(0),)*n+(F(1),)*n,
           tuple(-y for x,y in xy)+tuple(x for x,y in xy))
    for q in modes:
        assert all(sum(a*b for a,b in zip(row,q))==0 for row in exact)
    eigenvalues=np.linalg.eigvalsh(k)
    assert np.max(np.abs(eigenvalues[:3]))/eigenvalues[-1]<1e-14
    assert eigenvalues[3]>1e-4*eigenvalues[-1]
    k[0,0]=0
    assert local.stiffness(RECT,p)[0,0]!=0


@pytest.mark.parametrize('p',[1,2,3])
def test_affine_patch_energy_and_exact_physical_derivatives(p):
    xy=coordinates(RECT,p)
    # ux=2+3x-5y, uy=-4+7x+11y: engineering shear is 2.
    q=tuple(2+3*x-5*y for x,y in xy)+tuple(-4+7*x+11*y for x,y in xy)
    exact=local.stiffness_exact(RECT,p)
    computed=sum(q[i]*v*q[j] for i,row in enumerate(exact) for j,v in enumerate(row))
    strain=(F(3),F(11),F(2))
    expected=(RECT.x1-RECT.x0)*(RECT.y1-RECT.y0)*c.Q_THICKNESS*sum(
        strain[i]*c.Q_PLANE[i][j]*strain[j] for i in range(3) for j in range(3))
    assert computed==expected
    for order,expected_gradient in (((0,0),None),((1,0),(3,7)),((0,1),(-5,11)),((2,0),(0,0)),((1,1),(0,0)),((0,2),(0,0))):
        b=local.basis_exact(RECT,p,F(2,7),F(3,8),dx=order[0],dy=order[1])
        assert sum(b)==(1 if order==(0,0) else 0)
        numeric=local.basis(RECT,p,2/7,3/8,dx=order[0],dy=order[1])
        np.testing.assert_allclose(numeric,np.array(b,dtype=float),rtol=2e-14,atol=2e-14)
        if expected_gradient:
            assert tuple(sum(a*v for a,v in zip(b,part)) for part in (q[:len(xy)],q[len(xy):]))==expected_gradient


def test_second_derivatives_reproduce_quadratic_and_broadcast_owned_output():
    p=2;xy=coordinates(RECT,p);q=tuple(x*x+3*x*y-2*y*y for x,y in xy)
    for (dx,dy),expected in (((2,0),2),((1,1),3),((0,2),-4)):
        b=local.basis_exact(RECT,p,F(1,3),F(4,9),dx=dx,dy=dy)
        assert sum(a*v for a,v in zip(b,q))==expected
    x=np.array([[.1],[.7]]);y=np.array([.2,.4,.8])
    value=local.basis(RECT,p,x,y)
    assert value.shape==(2,3,9) and value.flags.owndata
    x[:]=0;y[:]=0
    assert value[0,0,0]!=1


def test_local_chart_preserves_tiny_positive_cell_and_rejects_bad_inputs():
    a=F(1,2);b=a+F(1,2**55)
    assert float(a)==float(b)
    rect=moments.Rectangle(a,b,F(-1,4),F(1,4))
    basis=local.basis_exact(rect,1,F(1,3),F(1,2),dx=1)
    assert basis==(-F(1,2)/(b-a),F(1,2)/(b-a))*2
    np.testing.assert_array_equal(local.basis(rect,1,1/3,.5,dx=1),np.array(basis,dtype=float))
    assert np.isfinite(local.stiffness(rect,1)).all()
    for p in (True,0,4):
        with pytest.raises(ValueError): local.stiffness(RECT,p)
    with pytest.raises(ValueError): local.basis(RECT,1,float('nan'),.5)
    with pytest.raises(ValueError): local.basis(RECT,1,.5,.5,dx=3)
    with pytest.raises(ValueError): local.basis_exact(RECT,1,.5,F(1,2))
