"""Independent checks for the exploratory supported x spectral elements."""

import numpy as np
from numpy.polynomial import legendre

from scripts._b3_e4_f03_segmented_x import BREAKS, SegmentedXBasis
from scripts._b3_e4_f03_segmented_y import SegmentedYBasis
from scripts import b3_e4_f03_spectral_axial_reference as spectral


def test_segmented_longitudinal_basis_has_shared_nodes_and_fixed_edges():
    for degree in (1,2,4,8,16,24):
        basis=SegmentedXBasis(degree)
        nodes=np.asarray(basis.nodes)
        np.testing.assert_allclose(
            np.array([basis.values(float(x)) for x in nodes]),
            np.eye(basis.size),atol=5e-13)
        np.testing.assert_allclose(basis.values(-.5),0.,atol=5e-14)
        np.testing.assert_allclose(basis.values(1.5),0.,atol=5e-14)
        for x in BREAKS[1:-1]:
            np.testing.assert_allclose(basis.values(x-1e-12),
                                       basis.values(x+1e-12),atol=5e-9)
        original=basis.values(.5)
        original[:]=99.
        assert not np.any(basis.values(.5)==99.)
    np.testing.assert_allclose(
        SegmentedXBasis(4).crossing_stations(spectral.OFFSETS),(.4,.6),
        atol=2e-16)


def test_segmented_longitudinal_matrices_match_direct_quadrature():
    basis=SegmentedXBasis(5)
    rng=np.random.default_rng(9)
    a,b=rng.normal(size=(2,basis.size))
    mass,gradient,mixed=basis.matrices()
    roots,weights=legendre.leggauss(40)
    direct=np.zeros(3)
    for lo,hi in zip(BREAKS[:-1],BREAKS[1:]):
        for root,weight in zip(roots,weights):
            x=(lo+hi)/2+(hi-lo)*root/2
            h=2e-6*min(x-lo,hi-x,hi-lo)
            v=basis.values(x)
            dv=(basis.values(x+h)-basis.values(x-h))/(2*h)
            direct+=(hi-lo)*weight/2*np.array((a@v*b@v,a@dv*b@dv,
                                                a@dv*b@v))
    np.testing.assert_allclose((a@mass@b,a@gradient@b,a@mixed@b),
                               direct,rtol=2e-7,atol=2e-8)
    np.testing.assert_allclose(mixed+mixed.T,0.,atol=5e-13)
    assert np.linalg.eigvalsh(mass)[0]>0
    assert np.linalg.eigvalsh(gradient)[0]>0


def test_double_segmented_shell_energy_matches_direct_strain_integration():
    xb=SegmentedXBasis(2)
    yb=SegmentedYBasis(2)
    nx,ny=xb.size,yb.size
    rng=np.random.default_rng(15)
    q=rng.normal(size=2*nx*ny)*.01
    u=q[:nx*ny].reshape(nx,ny)
    v=q[nx*ny:].reshape(nx,ny)
    roots,weights=legendre.leggauss(10)
    energy=0.
    for xl,xr in zip(BREAKS[:-1],BREAKS[1:]):
        for yl,yr in zip((-.5,-.23,.23),(-.23,.23,.5)):
            for tx,wx in zip(roots,weights):
                x=(xl+xr)/2+(xr-xl)*tx/2
                sx=xb.values(x)
                hx=1e-6*(xr-xl)
                dx=(xb.values(x+hx)-xb.values(x-hx))/(2*hx)
                for ty,wy in zip(roots,weights):
                    y=(yl+yr)/2+(yr-yl)*ty/2
                    sy=yb.values(y)
                    hy=1e-6*(yr-yl)
                    dy=(yb.values(y+hy)-yb.values(y-hy))/(2*hy)
                    strain=np.array((dx@u@sy,sx@v@dy,
                                     sx@u@dy+dx@v@sy))
                    energy+=(.5*spectral.THICKNESS*wx*wy*(xr-xl)*(yr-yl)/4
                             *float(strain@spectral.D@strain))
    assembled=.5*q@spectral.shell_stiffness(nx,ny,yb,xb)@q
    np.testing.assert_allclose(assembled,energy,rtol=2e-9)


def test_segmented_longitudinal_coupling_splits_crossing_stations():
    xb=SegmentedXBasis(3)
    yb=SegmentedYBasis(2)
    nx,ny=xb.size,yb.size
    n_beam,n_mortar=3,2
    rng=np.random.default_rng(21)
    qs=rng.normal(size=2*nx*ny)*1e-6
    lam=rng.normal(size=3*(n_mortar+1))
    cs,_=spectral.coupling(nx,ny,n_beam,n_mortar,y_basis=yb,x_basis=xb)
    assembled=float(lam@(cs@qs))
    knots=np.unique(np.r_[np.linspace(0,1,n_beam+1),
                          np.linspace(0,1,n_mortar+1),
                          xb.crossing_stations(spectral.OFFSETS)])
    roots,weights=legendre.leggauss(36)
    direct=0.
    u=qs[:nx*ny].reshape(nx,ny)
    v=qs[nx*ny:].reshape(nx,ny)
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=(left+right)/2+(right-left)*root/2
            cell=min(int(s*n_mortar),n_mortar-1)
            xi=s*n_mortar-cell
            multiplier=((1-xi)*lam[3*cell:3*cell+3]
                        +xi*lam[3*(cell+1):3*(cell+1)+3])
            fields=[]
            for ox,oy in spectral.OFFSETS:
                sx=xb.values(s+ox)
                sy=yb.values(oy)
                fields.append((ox,oy,float(sx@u@sy),float(sx@v@sy)))
            pose=np.array((sum(f[2] for f in fields)/4,
                           sum(f[3] for f in fields)/4,
                           sum(-f[1]*f[2]+f[0]*f[3] for f in fields)
                           /spectral.YAW_DENOMINATOR))
            direct+=((right-left)*weight/2
                     *float(multiplier@(pose*np.array((1.,1.,
                                                        spectral.YAW_LENGTH)))))
    np.testing.assert_allclose(assembled,direct,rtol=3e-13,atol=1e-18)
