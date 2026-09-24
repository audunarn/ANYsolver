"""Bounded cross-operator axial diagnostic, not F03 qualification."""

import numpy as np
import pytest

from scripts.b3_e4_f03_matched_axial_reference_screen import compare


def test_s3_cst_same_support_comparison_is_balanced_and_finite():
    result = compare("S3-V2D", 4, 2)
    native, classical = result["native"], result["classical"]
    assert native["shell_support_policy"] == "both_xy_edges"
    assert native["beam_tip_ux_m"] < 0.
    assert classical["axial_tip_m"] < 0.
    assert native["shell_full_minus_physical_inplane_energy_j"] > 0.
    assert native["shell_energy_j"] == pytest.approx(
        native["shell_physical_inplane_energy_j"]+
        native["shell_full_minus_physical_inplane_energy_j"], abs=1e-14)
    assert np.isfinite(result["tip_relative_difference"])
    assert result["tip_relative_difference"] < .02
    assert abs(native["global_axial_balance_n"]) < 1e-7
    assert abs(classical["global_axial_balance_n"]) < 1e-7
    assert native["scaled_equilibrium_residual"] < 1e-12
    assert classical["algebraic_residual_ratio"] < 1e-12


def test_comparator_rejects_unsupported_grid():
    with pytest.raises(ValueError, match="bounded axial comparison grid"):
        compare("S3-V2D", 2, 2)
