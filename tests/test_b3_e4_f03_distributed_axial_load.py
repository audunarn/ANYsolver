"""Physical line-load identities for the bounded F03 paired-mesh screen."""

import numpy as np
import pytest

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_weak_line_resolution_screen import (
    sinusoidal_axial_density_load)


@pytest.mark.parametrize("native_half_cells", (4, 8, 16, 32))
def test_sine_density_has_analytic_resultant_and_linear_virtual_work(
        native_half_cells):
    beam = build(native_half_cells)
    amplitude = 1e5
    load = sinusoidal_axial_density_load(
        beam, amplitude_n_per_m=amplitude)
    assert load.shape == (beam.context.count,)
    nodal = load[:beam.context.nodal_count].reshape(-1, 6)
    np.testing.assert_allclose(nodal[:, 1:], 0., atol=1e-12)
    np.testing.assert_allclose(load[beam.context.nodal_count:], 0.,
                               atol=1e-12)
    # Analytic integrals of q(s)=amplitude*sin(2*pi*s) over [0,1].
    assert np.sum(nodal[:, 0]) == pytest.approx(0., abs=1e-8)
    stations = np.linspace(0., 1., native_half_cells+1)
    assert stations@nodal[:, 0] == pytest.approx(
        -amplitude/(2*np.pi), rel=1e-12)
    # Independently integrated hat loads for a straight native half-cell.
    h, wave = 1/native_half_cells, 2*np.pi
    expected = np.zeros(native_half_cells+1)
    expected[0] = amplitude*(1/wave-np.sin(wave*h)/(wave*wave*h))
    expected[-1] = -expected[0]
    x = stations[1:-1]
    expected[1:-1] = amplitude*(
        2*np.sin(wave*x)-np.sin(wave*(x-h))-np.sin(wave*(x+h)))/(
            wave*wave*h)
    np.testing.assert_allclose(nodal[:, 0], expected,
                               rtol=2e-14, atol=2e-10)


def test_sine_density_rejects_invalid_amplitudes():
    beam = build(4)
    for amplitude in (0., -1., np.nan, np.inf, True, "1e5"):
        with pytest.raises(ValueError, match="positive finite"):
            sinusoidal_axial_density_load(
                beam, amplitude_n_per_m=amplitude)
