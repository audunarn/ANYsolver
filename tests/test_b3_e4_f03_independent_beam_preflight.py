"""Analytical patch checks for the independent F03 reference beam."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam


def test_axial_shear_and_bending_energy_patches():
    length=.37
    axial=1.7e-4
    shear=-2.3e-4
    theta=.8e-4
    q=np.zeros(10)
    q[:3]=axial*np.array((0,.5*length,length))
    q[3:7]=[0,shear,shear*length,shear]
    q[7:]=theta
    k=beam.stiffness(length)
    for xi in (0,.13,.5,.87,1):
        _, b=beam.fields(xi,length)
        np.testing.assert_allclose(b@q,[axial,0,shear-theta],rtol=1e-12,atol=1e-18)
    expected=length*(beam.E*beam.AREA*axial**2+
                     beam.G*beam.SHEAR_AREA*(shear-theta)**2)
    np.testing.assert_allclose(q@k@q,expected,rtol=1e-12)

    curvature=.41e-3
    q[:]=0
    q[3:7]=[0,0,curvature*length**2/2,curvature*length]
    q[7:]=[0,curvature*length/2,curvature*length]
    for xi in (0,.13,.5,.87,1):
        n,b=beam.fields(xi,length)
        np.testing.assert_allclose(b@q,[0,curvature,0],rtol=1e-12,atol=1e-17)
        np.testing.assert_allclose(n[1]@q,curvature*(xi*length)**2/2,rtol=1e-12,atol=1e-18)
    np.testing.assert_allclose(q@k@q,length*beam.E*beam.INERTIA*curvature**2,rtol=1e-12)
    np.testing.assert_allclose(k,k.T,rtol=0,atol=1e-7)


def test_distributed_load_resultants_and_quadrature():
    for kind,force,moment in (('smooth',1e6,5e5),('sine',0.,-1e6/(2*np.pi))):
        assembled=np.zeros(4)
        fine=np.zeros(4)
        for i in range(8):
            f=beam.load(1/8,i/8,kind,order=16)
            g=beam.load(1/8,i/8,kind,order=24)
            assembled += [f[3]+f[5], f[3]*i/8+f[5]*(i+1)/8+f[4]+f[6],
                          f[0]+f[1]+f[2], f[7]+f[8]+f[9]]
            fine += [g[3]+g[5], g[3]*i/8+g[5]*(i+1)/8+g[4]+g[6],
                     g[0]+g[1]+g[2], g[7]+g[8]+g[9]]
        np.testing.assert_allclose(assembled[:2],[force,moment],rtol=0,atol=1e-7)
        np.testing.assert_allclose(assembled,fine,rtol=0,atol=1e-7)
        np.testing.assert_allclose(assembled[2:],0,rtol=0,atol=1e-10)


def test_axial_sine_density_has_independent_resultant_and_moment():
    for elements in (2, 4, 8, 16):
        load=beam.assembled_load(elements,'axial_sine')
        load_fine=beam.assembled_load(elements,'axial_sine',order=24)
        axial_count=2*elements+1
        np.testing.assert_allclose(load,load_fine,rtol=0,atol=1e-8)
        np.testing.assert_allclose(load[axial_count:],0,rtol=0,atol=1e-11)
        np.testing.assert_allclose(np.sum(load[:axial_count]),0,
                                   rtol=0,atol=1e-8)
        stations=np.linspace(0.,1.,axial_count)
        np.testing.assert_allclose(stations@load[:axial_count],
                                   -1e5/(2*np.pi),rtol=1e-12)


def test_quadratic_shear_virtual_work_and_rigid_nullspace():
    length=.43
    k=beam.stiffness(length)
    q=np.array((.2,-.7,.5,-.1,.31,.4,-.3,.12,-.23,.51))*1e-4
    p=np.array((-.4,.3,.2,.7,-.61,.8,.23,-.19,.33,.52))*1e-4
    roots,weights=np.polynomial.legendre.leggauss(6)
    energy=work=0.
    for root,weight in zip(roots,weights):
        _,b=beam.fields(float((root+1)/2),length)
        strain_q=b@q
        energy+=length*weight/2*(strain_q@beam.SECTION@strain_q)
        work+=length*weight/2*((b@p)@beam.SECTION@strain_q)
    np.testing.assert_allclose(q@k@q,energy,rtol=1e-12)
    np.testing.assert_allclose(p@k@q,work,rtol=1e-12)
    step=1e-3
    derivative=(((q+step*p)@k@(q+step*p))-
                ((q-step*p)@k@(q-step*p)))/(4*step)
    np.testing.assert_allclose(derivative,p@k@q,rtol=1e-10)

    axial=np.zeros(10); axial[:3]=1
    transverse=np.zeros(10); transverse[[3,5]]=1
    rotation=np.zeros(10)
    rotation[3:7]=[0,1,length,1]
    rotation[7:]=1
    for mode in (axial,transverse,rotation):
        assert np.linalg.norm(k@mode)/(np.linalg.norm(k)*np.linalg.norm(mode))<1e-14
    eig=np.linalg.eigvalsh(k)
    assert np.count_nonzero(np.abs(eig)<=1e-10*eig[-1])==3


def test_multielement_continuity_root_and_global_load_work():
    elements=8
    count=beam.dof_count(elements)
    u=2*elements+1
    v=2*(elements+1)
    translation=np.zeros(count)
    translation[u+0:u+v:2]=1
    rotation=np.zeros(count)
    rotation[u+0:u+v:2]=np.arange(elements+1)/elements
    rotation[u+1:u+v:2]=1
    rotation[u+v:]=1
    axial=np.zeros(count); axial[:u]=1
    np.testing.assert_array_equal(beam.root_dofs(elements),[0,u,u+v])
    k=beam.assembled_stiffness(elements)
    scale=np.sqrt(k.multiply(k).sum())
    for mode in (translation,rotation,axial):
        assert np.linalg.norm(k@mode)/(scale*np.linalg.norm(mode))<1e-14
    for boundary in range(1,elements):
        s=boundary/elements
        left=beam.trace(elements,s-1e-10)
        exact=beam.trace(elements,s)
        right=beam.trace(elements,s+1e-10)
        np.testing.assert_allclose(exact@rotation,[0,s,1],rtol=1e-12,atol=1e-12)
        assert np.linalg.norm((left-right)@rotation)<1e-9
    for kind,force,moment in (('smooth',1e6,5e5),('sine',0.,-1e6/(2*np.pi))):
        f=beam.assembled_load(elements,kind)
        np.testing.assert_allclose(translation@f,force,rtol=0,atol=1e-7)
        np.testing.assert_allclose(rotation@f,moment,rtol=0,atol=1e-7)
