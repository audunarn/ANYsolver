"""Independent displacement-BVP and physical controls for affine carriers."""
from fractions import Fraction as F
import math

import numpy as np
import pytest

from scripts.r8_bl5_affine_carrier_reference_dev import solve_affine_carrier


def _displacement_bvp(endpoints, rho):
    """Exact rational quintics; no force-state propagation implementation.

    For affine p, U''''=p. Independently eliminating Timoshenko fields gives
    phi=U'+rho*U'''+rho²*U''''', V=-U'''-rho*U''''',
    M=U''+rho*U''''. These extra fifth-derivative terms matter for affine p.
    """
    endpoints, rho = tuple(map(F, endpoints)), F(rho)
    n, width = len(endpoints)-1, 6
    count = width*n
    def derivative(s, order):
        return [F(0) if k < order else F(math.factorial(k), math.factorial(k-order))*s**(k-order)
                for k in range(width)]
    def fields(s):
        derivatives = [derivative(s, k) for k in range(width)]
        return (derivatives[0],
            [a+rho*b+rho*rho*c for a,b,c in zip(derivatives[1], derivatives[3], derivatives[5])],
            [-a-rho*b for a,b in zip(derivatives[3], derivatives[5])],
            [a+rho*b for a,b in zip(derivatives[2], derivatives[4])])
    matrix, rhs = [], []
    def equation(parts, value=F(0)):
        row = [F(0)]*count
        for interval, values in parts:
            row[width*interval:width*(interval+1)] = values
        matrix.append(row); rhs.append(value)
    for i, (left, right) in enumerate(zip(endpoints[:-1], endpoints[1:])):
        h = right-left
        equation(((i, [h**k/F(k+1) for k in range(width)]),))
        equation(((i, [h**k*F(k,(k+1)*(k+2)) for k in range(width)]),))
        if i < n-1:
            for a,b in zip(fields(h), fields(F(0))):
                equation(((i,a), (i+1,[-v for v in b])))
    equation(((0, fields(F(0))[0]),))
    equation(((0, fields(F(0))[3]),))
    h = endpoints[-1]-endpoints[-2]
    equation(((n-1, fields(h)[0]),))
    equation(((n-1, fields(h)[3]),), F(1))
    for k in range(count):
        pivot = next(i for i in range(k,count) if matrix[i][k])
        matrix[k],matrix[pivot] = matrix[pivot],matrix[k]
        rhs[k],rhs[pivot] = rhs[pivot],rhs[k]
        for i in range(k+1,count):
            factor = matrix[i][k]/matrix[k][k]
            if not factor: continue
            for j in range(k+1,count): matrix[i][j] -= factor*matrix[k][j]
            rhs[i] -= factor*rhs[k]
            matrix[i][k] = F(0)
    solution = [F(0)]*count
    for i in reversed(range(count)):
        solution[i] = (rhs[i]-sum(matrix[i][j]*solution[j] for j in range(i+1,count)))/matrix[i][i]
    def evaluate(x):
        x = F(x)
        i = min(next((i for i in range(n) if x < endpoints[i+1]),n-1),n-1)
        return np.array([float(sum(a*b for a,b in zip(row,solution[width*i:width*(i+1)])))
                         for row in fields(x-endpoints[i])])
    densities = []
    for i in range(n):
        q = solution[width*i:width*(i+1)]
        h = endpoints[i+1]-endpoints[i]
        densities.append((float(24*q[4]+60*h*q[5]), float(60*h*q[5])))
    return evaluate, np.array(densities)


@pytest.mark.parametrize("rho",(F(1,10000),F(1,5),F(20)))
def test_one_support_against_exact_displacement_bvp(rho):
    ref = solve_affine_carrier(1.,1.,1./float(rho),1.,(0.,1.))
    fields, densities = _displacement_bvp((0,1),rho)
    np.testing.assert_allclose(ref.densities,densities,rtol=3e-12,atol=2e-12)
    for x in (F(0),F(1,7),F(1,2),F(6,7),F(1)):
        np.testing.assert_allclose(ref.fields(float(x)),fields(x),rtol=3e-12,atol=2e-12)
    assert abs(ref.densities[0,1]) > 0. # Tests the affine, rather than P0, space.


def test_nonuniform_supports_against_exact_displacement_bvp():
    ends, rho = (F(0),F(1,7),F(3,5),F(1)),F(1,250)
    ref = solve_affine_carrier(1.,1.,250.,1.,tuple(map(float,ends)))
    fields, densities = _displacement_bvp(ends,rho)
    np.testing.assert_allclose(ref.densities,densities,rtol=2e-10,atol=3e-10)
    for x in (F(0),F(1,10),F(1,7),F(2,7),F(3,5),F(7,8),F(1)):
        np.testing.assert_allclose(ref.fields(float(x)),fields(x),rtol=2e-10,atol=2e-11)


def test_physical_derivatives_continuity_transfer_work_and_both_constraints():
    ref = solve_affine_carrier(1.,1.75e6,646153846.1538463,10.,(0.,.12,.4,.7,1.))
    xi, wi = np.polynomial.legendre.leggauss(6)
    transfer = np.zeros(4)
    for left,right in zip(ref.boundaries[:-1],ref.boundaries[1:]):
        x = ref.length*(left+(right-left)*(xi+1)/2)
        weights = ref.length*(right-left)*wi/2
        u = ref.fields(x)[0]
        scale = abs(ref.moment)*ref.length**3/ref.bending*(right-left)
        assert abs(weights@u)/scale < 2e-10
        assert abs(weights@(xi*u))/scale < 2e-10
        for k in range(4): transfer[k] += weights@(x**k*ref.force_density(x))
        at, step = ref.length*(left+.43*(right-left)),ref.length*(right-left)*1e-4
        derivative = (ref.fields(at-2*step)-8*ref.fields(at-step)+8*ref.fields(at+step)-ref.fields(at+2*step))/(12*step)
        u,phi,v,m = ref.fields(at)
        np.testing.assert_allclose(derivative,(phi+v/ref.shear,m/ref.bending,-ref.force_density(at),-v),
                                   rtol=3e-8,atol=2e-10)
    np.testing.assert_allclose(ref.transfer_moments(),transfer,rtol=2e-11,atol=2e-11)
    for boundary in ref.boundaries[1:-1]:
        at = boundary*ref.length
        np.testing.assert_allclose(ref.fields(at-1e-10),ref.fields(at+1e-10),rtol=3e-6,atol=3e-6)
    checks = ref.controls()
    for name in ("scaled_support_mean","scaled_support_affine_mean","energy_work","line_work",
                 "scaled_endpoint_displacement","scaled_endpoint_moment","force_balance","moment_balance"):
        assert checks[name] < 2e-10, (name,checks[name])
    assert checks["energy"] > 0. and checks["work"] > 0.


@pytest.mark.parametrize("n",(8,16,32))
def test_same_partition_counts_equivalent_units_sign_and_owned_arrays(n):
    endpoints = np.linspace(0.,1.,n+1)
    ref = solve_affine_carrier(1.,1.75e6,646153846.1538463,10.,endpoints)
    converted = solve_affine_carrier(1000.,1.75e12,646153846.1538463,-10000.,endpoints*1000.)
    locations = np.array((.13,.51,.97,1.))
    np.testing.assert_allclose(converted.fields(locations*1000.),
                               -ref.fields(locations)*np.array((1000.,1.,1.,1000.))[:,None],rtol=2e-9,atol=1e-8)
    np.testing.assert_allclose(converted.transfer_moments(),
                               -ref.transfer_moments()*1000.**np.arange(4),rtol=2e-9,atol=1e-7)
    np.testing.assert_allclose(converted.densities,ref.densities,rtol=2e-9,atol=1e-7)
    endpoints[:] = 9.
    assert ref.boundaries[0] == 0. and ref.boundaries[-1] == 1.
    for array in (ref.boundaries,ref.starts,ref.densities,ref.coefficients):
        with pytest.raises(ValueError): array.setflags(write=True)
        with pytest.raises(ValueError): array.flat[0] = 0.


@pytest.mark.parametrize("endpoints",((0.,.4,.4,1.),(.1,1.),(0.,.9),
    (0.,float("nan"),1.),(0.,True,1.),((0.,1.),)))
def test_invalid_partition_is_rejected(endpoints):
    with pytest.raises(ValueError): solve_affine_carrier(1.,1.,1.,1.,endpoints)


@pytest.mark.parametrize("values",((0.,1.,1.,1.),(1.,-1.,1.,1.),(1.,1.,0.,1.),
    (1.,1.,1.,0.),(1.,1.,1.,float("inf")),(True,1.,1.,1.)))
def test_invalid_physical_input_is_rejected(values):
    with pytest.raises(ValueError): solve_affine_carrier(*values,(0.,1.))


def test_query_admission():
    ref = solve_affine_carrier(1.,1.,1.,1.,(0.,1.))
    for coordinate in (True,-.1,1.1,float("nan")):
        with pytest.raises(ValueError): ref.fields(coordinate)
        with pytest.raises(ValueError): ref.force_density(coordinate)
    for order in (True,-1,4,1.5):
        with pytest.raises(ValueError): ref.transfer_moments(order)
