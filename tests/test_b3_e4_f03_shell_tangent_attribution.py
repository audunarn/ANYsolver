"""Check the bounded shell-block diagnostic against the unchanged native solve."""

import numpy as np
import pytest

from scripts.b3_e4_f03_shell_tangent_attribution import sensitivity
from scripts.b3_e4_f03_weak_line_resolution_screen import one_case


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_unmodified_branch_recovers_native_weak_line_solution(topology):
    attribution = sensitivity(topology, 4, 2)
    reference = one_case(
        topology, 4, "continuous_linear", load_kind="sinusoidal_axial_density",
        n_s=4, native_half_cells=16, n_y=2,
        shell_support_policy="both_xy_edges")
    for diagnostic, oracle in (("beam_tip_ux_m", "beam_tip_ux_m"),
                               ("shell_reaction_fx_n", "shell_reaction_fx_n"),
                               ("shell_energy_j", "shell_energy_j")):
        np.testing.assert_allclose(attribution["native"][diagnostic],
                                   reference[oracle], rtol=1e-12, atol=1e-12)
    assert attribution["native"]["scaled_residual"] < 1e-12
    assert attribution["substituted"]["scaled_residual"] < 1e-12
    assert attribution["full_block_relative_difference"] > 0.05
    assert abs(attribution["tip_change_fraction"]) > 0.01


@pytest.mark.parametrize("args", (("Q4", 2, 2), ("Q4", 4, 3),
                                  ("bad", 4, 2)))
def test_sensitivity_is_bounded(args):
    with pytest.raises(ValueError, match="bounded shell-block"):
        sensitivity(*args)
