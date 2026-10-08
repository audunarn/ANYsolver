"""Small, unregistered checks of the standalone classical energy screen."""

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import _b3_e4_f03_supported_energy as energy


def test_far_negative_mode_is_found_despite_near_zero_positive_mode():
    # The 2x2 block has eigenvalues 1e-8 and 2-1e-8; the third is -2.
    k = sparse.csr_matrix(np.array([
        [0., 0., 0., 0.],
        [0., 1., 1.-1e-8, 0.],
        [0., 1.-1e-8, 1., 0.],
        [0., 0., 0., -2.],
    ]))
    result = energy.screen_supported_energy(k, np.array([0]))
    assert result["status"] == "negative_or_zero_diagonal"
    # Positive diagonals can still conceal a negative off-diagonal mode.
    hidden = sparse.csr_matrix(np.array([
        [0., 0., 0., 0., 0.],
        [0., 1., 1.-1e-8, 0., 0.],
        [0., 1.-1e-8, 1., 0., 0.],
        [0., 0., 0., 1., 2.],
        [0., 0., 0., 2., 1.],
    ]))
    result = energy.screen_supported_energy(hidden, np.array([0]))
    assert result["status"] == "negative_witness"
    assert result["rayleigh_quotient"] == pytest.approx(-1., abs=1e-7)
    assert result["residual_norm"] < 1e-7


@pytest.mark.parametrize("topology", ["Q4", "CST-CB"])
def test_small_classical_supported_assembly_has_no_negative_found(topology):
    result = energy.screen_f03(2, 4, 2, topology)
    assert result["status"] == "no_negative_found"
    assert result["free_count"] > 0
    assert result["rayleigh_quotient"] > 0


def test_asymmetry_rejected():
    k = sparse.csr_matrix(np.array([[1., 2., 0.], [0., 2., 0.],
                                    [0., 0., 3.]]))
    with pytest.raises(ValueError, match="asymmetric"):
        energy.screen_supported_energy(k, np.array([], dtype=int))


def test_near_singular_positive_energy_is_inconclusive_not_certified():
    k = sparse.csr_matrix(np.array([[0., 0., 0.],
                                    [0., 1., 1.-1e-12],
                                    [0., 1.-1e-12, 1.]]))
    result = energy.screen_supported_energy(k, np.array([0]))
    assert result["status"] == "inconclusive"
    assert result["rayleigh_quotient"] > 0


def test_unrepresentable_congruence_fails_explicitly():
    k = sparse.csr_matrix(np.array([[1e-320, 1., 0.],
                                    [1., 1e-320, 0.],
                                    [0., 0., 1.]]))
    with pytest.raises(ValueError, match="representable"):
        energy.screen_supported_energy(k, np.array([], dtype=int))
