"""Independent algebra and work checks for the exploratory segmented shell."""

import math

import numpy as np
import pytest
from numpy.polynomial import legendre

from scripts._b3_e4_f03_segmented_y import SegmentedYBasis
from scripts import b3_e4_f03_spectral_axial_reference as spectral


@pytest.mark.parametrize("subdivisions",(1,2))
def test_segmented_basis_is_continuous_complete_and_owns_results(subdivisions):
    degrees=(1,2,4,8,16,20,24) if subdivisions==1 else (1,2,4,8,12)
    for degree in degrees:
        basis = SegmentedYBasis(degree,subdivisions)
        nodes = np.asarray(basis.nodes)
        np.testing.assert_allclose(
            np.array([basis.values(y) for y in nodes]), np.eye(basis.size),
            atol=2e-13)
        for y in np.r_[np.linspace(-.5, .5, 23), basis.breaks]:
            values = basis.values(float(y))
            np.testing.assert_allclose(values.sum(), 1., atol=3e-14)
            np.testing.assert_allclose(values@nodes, y, atol=3e-14)
        for y in basis.breaks[1:-1]:
            np.testing.assert_allclose(basis.values(y-1e-12),
                                       basis.values(y+1e-12), atol=2e-9)
        borrowed = basis.values(0.)
        borrowed[:] = 42.
        assert not np.any(basis.values(0.) == 42.)


@pytest.mark.parametrize("subdivisions",(1,2))
def test_segmented_mass_and_gradient_match_independent_physical_quadrature(subdivisions):
    basis = SegmentedYBasis(5,subdivisions)
    rng = np.random.default_rng(4)
    a, b = rng.normal(size=(2, basis.size))
    mass, gradient, mixed = basis.matrices()
    roots, weights = legendre.leggauss(40)
    integrals = np.zeros(3)
    # Differentiate the scalar interpolant numerically within each smooth
    # segment; this avoids using the basis's derivative implementation.
    for lo, hi in zip(basis.breaks[:-1], basis.breaks[1:]):
        for root, weight in zip(roots, weights):
            y = (lo+hi)/2+(hi-lo)*root/2
            measure = (hi-lo)*weight/2
            av = a@basis.values(y)
            bv = b@basis.values(y)
            step = 2e-6*min(y-lo, hi-y, hi-lo)
            ad = a@(basis.values(y+step)-basis.values(y-step))/(2*step)
            bd = b@(basis.values(y+step)-basis.values(y-step))/(2*step)
            integrals += measure*np.array((av*bv, ad*bd, av*bd))
    np.testing.assert_allclose(
        (a@mass@b, a@gradient@b, a@mixed@b), integrals, rtol=2e-7,
        atol=2e-8)
    left, right = basis.values(-.5), basis.values(.5)
    np.testing.assert_allclose(mixed+mixed.T,
                               np.outer(right, right)-np.outer(left, left),
                               atol=5e-13)
    assert np.linalg.eigvalsh(mass)[0] > 0.


@pytest.mark.parametrize("subdivisions",(1,2))
def test_segmented_shell_energy_matches_direct_strain_integration(subdivisions):
    nx = 3
    basis = SegmentedYBasis(3,subdivisions)
    ny = basis.size
    rng = np.random.default_rng(7)
    q = rng.normal(size=2*nx*ny)*.01
    u, v = q[:nx*ny].reshape(nx, ny), q[nx*ny:].reshape(nx, ny)
    roots_x, weights_x = legendre.leggauss(32)
    roots_y, weights_y = legendre.leggauss(20)
    energy = 0.
    for tx, wx in zip(roots_x, weights_x):
        x = tx+1.
        k = np.arange(1, nx+1)
        sx = np.sin(k*math.pi*x/2)
        dx = k*math.pi/2*np.cos(k*math.pi*x/2)
        for lo, hi in zip(basis.breaks[:-1], basis.breaks[1:]):
            for ty, wy in zip(roots_y, weights_y):
                y = (lo+hi)/2+(hi-lo)*ty/2
                py = basis.values(y)
                step = 1e-6*(hi-lo)
                dpy = (basis.values(y+step)-basis.values(y-step))/(2*step)
                strain = np.array((dx@u@py, sx@v@dpy,
                                   sx@u@dpy+dx@v@py))
                energy += (.5*spectral.THICKNESS*wx*wy*(hi-lo)/2
                           *float(strain@spectral.D@strain))
    assembled = .5*q@spectral.shell_stiffness(nx,ny,basis)@q
    np.testing.assert_allclose(assembled, energy, rtol=2e-9)


@pytest.mark.parametrize("subdivisions",(1,2))
def test_segmented_pose_samples_shared_interfaces_and_edge_moments(subdivisions):
    basis = SegmentedYBasis(2,subdivisions)
    nx, ny = 2, basis.size
    q = np.zeros(2*nx*ny)
    # A linear-y field at every x mode must yield the direct four-sample law.
    q[:ny] = basis.nodes
    station = .37
    observed = spectral.shell_pose(nx,ny,station,basis)@q
    sampled = [(dx,dy,math.sin(math.pi*(station+dx+.5)/2)*dy)
               for dx,dy in spectral.OFFSETS]
    expected = np.array((sum(value for _,_,value in sampled)/4, 0.,
                         sum(-dy*value for _,dy,value in sampled)
                         /spectral.YAW_DENOMINATOR))
    np.testing.assert_allclose(observed,expected,atol=2e-16)
    constant,first = basis.moments()
    np.testing.assert_allclose(constant.sum(), 1., atol=2e-15)
    np.testing.assert_allclose(first@basis.nodes, 1/12, atol=2e-15)


@pytest.mark.parametrize("subdivisions",(1,2))
def test_segmented_line_virtual_work_matches_direct_sample_integration(subdivisions):
    nx = 3
    basis = SegmentedYBasis(2,subdivisions)
    ny = basis.size
    n_beam, n_mortar = 4, 3
    rng = np.random.default_rng(11)
    qs = rng.normal(size=2*nx*ny)*1e-6
    lam = rng.normal(size=3*(n_mortar+1))
    cs, _ = spectral.coupling(nx,ny,n_beam,n_mortar,y_basis=basis)
    assembled = float(lam@(cs@qs))
    knots = np.unique(np.r_[np.linspace(0,1,n_beam+1),
                            np.linspace(0,1,n_mortar+1)])
    roots, weights = legendre.leggauss(36)
    direct = 0.
    u = qs[:nx*ny].reshape(nx,ny)
    v = qs[nx*ny:].reshape(nx,ny)
    for left,right in zip(knots[:-1],knots[1:]):
        for root, weight in zip(roots,weights):
            s = (left+right)/2+(right-left)*root/2
            cell = min(int(s*n_mortar),n_mortar-1)
            xi = s*n_mortar-cell
            multiplier = ((1-xi)*lam[3*cell:3*cell+3]
                          +xi*lam[3*(cell+1):3*(cell+1)+3])
            fields = []
            for dx,dy in spectral.OFFSETS:
                sx = np.sin(np.arange(1,nx+1)*math.pi*(s+dx+.5)/2)
                py = basis.values(dy)
                fields.append((dx,dy,float(sx@u@py),float(sx@v@py)))
            pose = np.array((sum(f[2] for f in fields)/4,
                             sum(f[3] for f in fields)/4,
                             sum(-f[1]*f[2]+f[0]*f[3] for f in fields)
                             /spectral.YAW_DENOMINATOR))
            direct += ((right-left)*weight/2
                       *float(multiplier@(pose*np.array((1.,1.,
                                                          spectral.YAW_LENGTH)))))
    np.testing.assert_allclose(assembled,direct,rtol=2e-13,atol=1e-18)
