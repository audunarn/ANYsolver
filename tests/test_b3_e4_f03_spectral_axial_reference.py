"""Independent modal-energy and trace checks for the exploratory shell."""

import math

import numpy as np
from numpy.polynomial import legendre

from scripts import b3_e4_f03_spectral_axial_reference as spectral


def test_supported_fourier_legendre_shell_has_classical_modal_energies():
    nx=2
    ny=2
    k=spectral.shell_stiffness(nx,ny)
    m=nx*ny
    wave=(math.pi/2)**2
    np.testing.assert_allclose(k[0,0],spectral.THICKNESS*spectral.D[0,0]*wave,
                               rtol=2e-13)
    np.testing.assert_allclose(k[m,m],spectral.THICKNESS*spectral.D[2,2]*wave,
                               rtol=2e-13)
    np.testing.assert_allclose(
        k[1,1],spectral.THICKNESS*(spectral.D[0,0]*wave/3
                                    +4*spectral.D[2,2]),rtol=2e-13)
    assert np.linalg.eigvalsh(k)[0]>0


def test_four_sample_trace_matches_direct_material_field():
    nx=2
    ny=2
    station=.37
    q=np.zeros(2*nx*ny)
    q[1]=1.  # u=sin(pi(x+0.5)/2)*P1(2y)
    actual=spectral.shell_pose(nx,ny,station)@q
    samples=[]
    for dx,dy in spectral.OFFSETS:
        samples.append((dx,dy,math.sin(math.pi*(station+dx+.5)/2)*2*dy))
    expected=np.array((sum(u for _,_,u in samples)/4,0.,
                       sum(-dy*u for _,dy,u in samples)
                       /spectral.YAW_DENOMINATOR))
    np.testing.assert_allclose(actual,expected,rtol=2e-15,atol=2e-16)


def test_mixed_modal_energy_matches_direct_two_dimensional_strain_integral():
    nx=3
    ny=3
    q=np.array((.07,-.03,.11,.02,.05,-.09,.04,-.08,.06,
                -.05,.12,.03,-.07,.09,.01,-.02,.08,-.04))
    u=q[:nx*ny].reshape(nx,ny)
    v=q[nx*ny:].reshape(nx,ny)
    roots_x,weights_x=legendre.leggauss(24)
    roots_y,weights_y=legendre.leggauss(12)
    integrated=0.
    for tx,wx in zip(roots_x,weights_x):
        x=tx+.5
        sx=np.array([math.sin(k*math.pi*(x+.5)/2)
                     for k in range(1,nx+1)])
        dsx=np.array([k*math.pi/2*math.cos(k*math.pi*(x+.5)/2)
                      for k in range(1,nx+1)])
        for ty,wy in zip(roots_y,weights_y):
            py=np.array([legendre.Legendre.basis(j)(ty) for j in range(ny)])
            dpy=np.array([2*legendre.Legendre.basis(j).deriv()(ty)
                          for j in range(ny)])
            ux=float(dsx@u@py)
            uy=float(sx@u@dpy)
            vx=float(dsx@v@py)
            vy=float(sx@v@dpy)
            strain=np.array((ux,vy,uy+vx))
            integrated+=.5*spectral.THICKNESS*wx*wy/2*float(
                strain@spectral.D@strain)
    assembled=float(.5*q@spectral.shell_stiffness(nx,ny)@q)
    np.testing.assert_allclose(assembled,integrated,rtol=2e-13)


def test_integrated_line_wrench_uses_physical_force_and_first_moment():
    n=8
    lam=np.tile(np.array((2.,-3.,5.)),n+1)
    actual=spectral._interface_wrench(lam,n)
    expected=np.array((2.,-3.,-3./2+5*spectral.YAW_LENGTH))
    np.testing.assert_allclose(actual,expected,rtol=0,atol=2e-15)
