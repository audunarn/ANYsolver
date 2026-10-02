"""Physical mode-matching controls, independent of native/external frequencies."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse
from scipy.optimize import linear_sum_assignment

spec = importlib.util.spec_from_file_location('q4_us3_modal_compare',
    Path(__file__).parents[1]/'scripts/r8_q4_us3_modal_compare_dev.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_permutation_sign_and_scale_match_without_frequency_indices():
    mass = sparse.diags([2.,3.,0.])
    native = np.array([[1.,0.],[0.,1.],[.2,.4]])
    reference = np.array([[0.,5.],[-7.,0.],[90.,-120.]])
    mac, left, right = runner.common_mass_mac(native, reference, mass)
    np.testing.assert_allclose(mac, [[0.,1.],[1.,0.]], atol=1e-15)
    assert list(zip(*linear_sum_assignment(-mac))) == [(0,1),(1,0)]
    np.testing.assert_allclose(np.sum(left*(mass@left),axis=0),1.)
    np.testing.assert_allclose(np.sum(right*(mass@right),axis=0),1.)
    # The comparison intentionally excludes massless-spin disagreement.
    reference[2] *= 1000
    np.testing.assert_allclose(runner.common_mass_mac(native,reference,mass)[0],mac)


def test_oblique_physical_field_is_detected_by_common_mass():
    mass = sparse.diags([2.,3.,0.])
    native = np.array([[1.],[0.],[0.]])
    reference = np.array([[1.],[1.],[10.]])
    assert runner.common_mass_mac(native,reference,mass)[0][0,0] == pytest.approx(2./5.)


@pytest.mark.parametrize('defect',('no-physical-mass','nonfinite','wrong-layout','negative-inertia'))
def test_invalid_common_physical_metric_cannot_match_modes(defect):
    mass = sparse.diags([2.,3.,0.])
    native, reference = np.array([[1.],[0.],[0.]]), np.array([[0.],[1.],[0.]])
    if defect == 'no-physical-mass': reference = np.array([[0.],[0.],[1.]])
    elif defect == 'nonfinite': reference[0,0] = np.nan
    elif defect == 'wrong-layout': reference = np.ones((4,1))
    elif defect == 'negative-inertia': mass = -mass
    with pytest.raises(ValueError): runner.common_mass_mac(native,reference,mass)
