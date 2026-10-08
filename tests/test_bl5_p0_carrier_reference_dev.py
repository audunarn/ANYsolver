"""Independent physical/algebraic controls for the finite-P0 reference."""
import numpy as np
import pytest

from scripts.r8_bl5_p0_carrier_reference_dev import solve_p0_carrier


def test_single_support_independent_closed_solution():
    # Eliminating V0=p/2-1 from endpoint/mean constraints gives p=5/(1+10rho).
    for rho in (.0001, .2, 20.):
        ref = solve_p0_carrier(1., 1., 1./rho, 1., (0., 1.))
        p = 5./(1.+10.*rho)
        theta0 = p/24.-1./6.+rho
        np.testing.assert_allclose(ref.densities, [p], rtol=2e-13)
        np.testing.assert_allclose(ref.fields(0.), [0., theta0, p/2.-1., 0.], atol=2e-13)
        np.testing.assert_allclose(ref.fields(1.)[1], 1./3.+rho-p/24., rtol=2e-13)


def test_physical_equations_continuity_and_work():
    ref = solve_p0_carrier(1., 1.75e6, 646153846.1538463, 10., (0., .12, .4, .7, 1.))
    for i, (a, b) in enumerate(zip(ref.boundaries[:-1], ref.boundaries[1:])):
        x, h = (a+b)/2, (b-a)*1e-4
        f = ref.fields(x)
        derivative = (ref.fields(x-2*h)-8*ref.fields(x-h)+8*ref.fields(x+h)-ref.fields(x+2*h))/(12*h)
        p = ref.densities[i]*ref.moment/ref.length**2
        expected = [f[1]+f[2]/ref.shear, f[3]/ref.bending, -p, -f[2]]
        np.testing.assert_allclose(derivative, expected, rtol=2e-8, atol=1e-11)
    for b in ref.boundaries[1:-1]:
        np.testing.assert_allclose(ref.fields(b-1e-10), ref.fields(b+1e-10), rtol=1e-6, atol=2e-6)
    checks = ref.controls()
    assert checks['energy_work'] < 1e-10
    assert checks['scaled_support_mean'] < 1e-10
    assert checks['force_balance'] < 1e-10
    assert checks['moment_balance'] < 1e-10


def test_equivalent_units_negative_moment_and_owned_inputs():
    endpoints = np.linspace(0., 1., 17)
    ref = solve_p0_carrier(1., 1.75e6, 646153846.1538463, 10., endpoints)
    converted = solve_p0_carrier(1000., 1.75e12, 646153846.1538463, -10000., endpoints*1000.)
    a, b = ref.fields(np.array((.2, .55, 1.))), converted.fields(np.array((200., 550., 1000.)))
    np.testing.assert_allclose(b, -a*np.array((1000., 1., 1., 1000.))[:, None], rtol=2e-10, atol=1e-8)
    endpoints[:] = 9.
    assert ref.boundaries[0] == 0. and ref.boundaries[-1] == 1.


@pytest.mark.parametrize('ends', [(0., .4, .4, 1.), (.1, 1.), (0., .9), (0., float('nan'), 1.)])
def test_invalid_reference_is_rejected(ends):
    with pytest.raises(ValueError): solve_p0_carrier(1., 1., 1., 1., ends)


def test_finest_reference_against_independent_decimal_displacement_polynomials():
    # Separate formulation: one quartic displacement per support, phi=u'+rho*u''',
    # V=-u''', M=u''+rho*u''''. Enforce four continuous fields at each join.
    # This checks forward precision; it is not a second physical idealization.
    from decimal import Decimal as D, localcontext
    with localcontext() as context:
        context.prec = 60
        n = 32
        h, rho = D(1)/n, D('1750000')/D('646153846.1538463')
        count = 5*n
        def local_rows(s):
            return (
                [D(1), s, s*s, s**3, s**4],
                [D(0), D(1), 2*s, 3*s*s+6*rho, 4*s**3+24*rho*s],
                [D(0), D(0), D(0), D(-6), -24*s],
                [D(0), D(0), D(2), 6*s, 12*s*s+24*rho])
        matrix, rhs = [], []
        def equation(parts, value=D(0)):
            row = [D(0)]*count
            for interval, coeffs in parts:
                row[5*interval:5*interval+5] = coeffs
            matrix.append(row); rhs.append(value)
        for i in range(n):
            equation(((i, [h, h*h/2, h**3/3, h**4/4, h**5/5]),))
        for i in range(n-1):
            for left, right in zip(local_rows(h), local_rows(D(0))):
                equation(((i, left), (i+1, [-v for v in right])))
        equation(((0, local_rows(D(0))[0]),))
        equation(((0, local_rows(D(0))[3]),))
        equation(((n-1, local_rows(h)[0]),))
        equation(((n-1, local_rows(h)[3]),), D(1))
        # Bounded dense independent oracle, no native mechanical matrix involved.
        for k in range(count):
            pivot = max(range(k, count), key=lambda j: abs(matrix[j][k]))
            matrix[k], matrix[pivot] = matrix[pivot], matrix[k]
            rhs[k], rhs[pivot] = rhs[pivot], rhs[k]
            assert matrix[k][k]
            for i in range(k+1, count):
                if not matrix[i][k]: continue
                factor = matrix[i][k]/matrix[k][k]
                for j in range(k+1, count): matrix[i][j] -= factor*matrix[k][j]
                rhs[i] -= factor*rhs[k]
                matrix[i][k] = D(0)
        solution = [D(0)]*count
        for i in reversed(range(count)):
            solution[i] = (rhs[i]-sum(matrix[i][j]*solution[j] for j in range(i+1,count)))/matrix[i][i]
        theta_tip = sum(v*c for v,c in zip(local_rows(h)[1],solution[-5:]))
        densities = np.array([float(24*solution[5*i+4]) for i in range(n)])
        ref = solve_p0_carrier(1., 1750000., 646153846.1538463, 10., np.linspace(0.,1.,n+1))
        np.testing.assert_allclose(ref.densities, densities, rtol=1e-8, atol=2e-11)
        np.testing.assert_allclose(ref.fields(1.)[1], float(theta_tip)*10./1750000., rtol=1e-11)
        root_reaction = float(6*solution[3])*10.
        np.testing.assert_allclose(ref.controls()['endpoint_reactions'][0], root_reaction, rtol=1e-7, atol=1e-12)
