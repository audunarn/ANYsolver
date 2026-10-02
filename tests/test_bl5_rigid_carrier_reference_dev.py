"""Independent continuum equilibrium/work controls for the new diagnostic."""
import math
import numpy as np
import pytest
from scipy.integrate import quad
from scripts.r8_bl5_rigid_carrier_dev import carrier_reference


def test_continuous_free_spin_end_conditions_and_energy():
    length, bending, shear, moment = 1., 1.75e6, 210e9/(2*1.3)*.008, 10.
    start = carrier_reference(length,bending,shear,moment,0.)
    end = carrier_reference(length,bending,shear,moment,length)
    assert start[1] == start[3] == 0.
    np.testing.assert_allclose(end[3],moment,rtol=1e-14)
    energy=quad(lambda x: .5*(bending*carrier_reference(length,bending,shear,moment,x)[1]**2+
                             shear*carrier_reference(length,bending,shear,moment,x)[0]**2),
                0.,length,epsabs=1e-16,epsrel=1e-12)[0]
    np.testing.assert_allclose(2.*energy,moment*end[0],rtol=1e-12)
    resultant=quad(lambda x: shear*carrier_reference(length,bending,shear,moment,x)[1],
                   0.,length,epsabs=1e-11,epsrel=1e-12)[0]
    np.testing.assert_allclose(resultant+end[2]-start[2],0.,atol=1e-11)
    for x in (.1,.7,.99):
        dx=1e-6
        lower=carrier_reference(length,bending,shear,moment,x-dx)
        upper=carrier_reference(length,bending,shear,moment,x+dx)
        middle=carrier_reference(length,bending,shear,moment,x)
        np.testing.assert_allclose((upper[3]-lower[3])/(2*dx),-middle[2],rtol=1e-8)


def test_reference_units_sign_and_slender_evaluation():
    a=carrier_reference(1.,1.75e6,6.46e8,10.,1.)
    b=carrier_reference(1000.,1.75e12,6.46e8,10000.,1000.)
    np.testing.assert_allclose(b,a*np.array((1.,.001,1.,1000.)),rtol=1e-14)
    np.testing.assert_array_equal(carrier_reference(1.,1.75e6,6.46e8,-10.,1.),-a)
    assert np.isfinite(carrier_reference(100.,1.,1e8,10.,100.)).all()
    for args in ((0.,1.,1.,1.,0.),(1.,-1.,1.,1.,0.),(1.,1.,math.inf,1.,0.)):
        with pytest.raises(ValueError): carrier_reference(*args)
