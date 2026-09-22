"""Bounded algebraic checks for the unselected classical P0 axial norm."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import linalg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _b3_e4_f03_p0_axial_screen import screen  # noqa: E402
from _b3_e4_f03_p0_dual_norm import p0_dual_gram  # noqa: E402
import _b3_e4_f03_p0_axial_screen as axial  # noqa: E402


@pytest.mark.parametrize("topology", ["Q4", "CST-CB"])
def test_bounded_axial_schur_matches_independent_dense_primal(topology):
    result, blocks = screen(1, 2, 2, 3, topology, last_mode=255,
                            retain_matrices=True)
    primal = blocks["primal"].toarray()
    coupling = blocks["coupling_axial"].toarray()
    dense_schur = coupling @ linalg.solve(primal, coupling.T,
                                           assume_a="sym")
    assert np.allclose(blocks["schur"], dense_schur, rtol=1e-10, atol=1e-9)
    true_proxy, _ = p0_dual_gram(3, 1.0, 8191)
    eig = linalg.eigh(dense_schur, true_proxy, eigvals_only=True)[0]
    assert result["axial_beta_lower"]**2 <= eig * (1 + 1e-10)
    assert eig <= result["axial_beta_upper"]**2 * (1 + 1e-10)
    assert result["maximum_stiffness_solve_residual"] < 1e-10
    assert result["axial_eigen_residual"] < 1e-10
    assert result["supported_energy_screen"]["status"] == "no_negative_found"


def test_nested_p0_work_has_same_action_for_fixed_primal_mesh():
    _, coarse = screen(2, 2, 4, 4, "Q4", retain_matrices=True)
    _, fine = screen(2, 2, 4, 8, "Q4", retain_matrices=True)
    repeat = np.kron(np.eye(4), np.ones((2, 1)))
    assert np.allclose(repeat.T @ fine["schur"] @ repeat, coarse["schur"],
                       rtol=1e-11, atol=1e-7)
    assert np.allclose(repeat.T @ fine["dual_lower"] @ repeat,
                       coarse["dual_lower"], rtol=1e-12, atol=1e-14)


def test_rejects_outside_bounded_mesh_and_unresolved_spectral_modes():
    with pytest.raises(ValueError, match="bounded"):
        screen(17, 2, 2, 2, "Q4")
    with pytest.raises(ValueError, match="last_mode"):
        screen(1, 2, 2, 5, "Q4", last_mode=3)


def test_inconclusive_supported_energy_does_not_produce_beta(monkeypatch):
    monkeypatch.setattr(axial, "screen_supported_energy",
                        lambda *_: {"status": "inconclusive"})
    with pytest.raises(ValueError, match="supported primal energy"):
        screen(1, 2, 2, 3, "Q4")
