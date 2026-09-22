"""Small finite-pad equilibrium checks; no physical convergence claim."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_area_loaded as loaded


@pytest.mark.parametrize("topology",("Q4","CST-CB"))
@pytest.mark.parametrize("law",("P0","P1"))
@pytest.mark.parametrize("history",("smooth","sine"))
def test_small_coupled_pad_energy_balance_and_work(topology,law,history):
    result=loaded.solve(2,4,4,2,topology,law,history,.04)
    assert result.topology==topology and result.law==law
    assert result.shell_energy_j>0 and result.beam_energy_j>0
    assert result.gap_l2_m>=0 and result.kkt_nnz>result.kkt_dimension
    assert result.free_residual_scaled<1e-8
    assert result.weak_gap_scaled<1e-9
    assert max(map(abs,result.balance_scaled))<1e-8
    assert abs(2*(result.shell_energy_j+result.beam_energy_j)+
               result.interface_work_j-result.external_work_j)<1e-7
    assert np.all(np.isfinite(result.displacement_tip_m))


def test_invalid_small_model_is_explicitly_rejected():
    with pytest.raises(ValueError):
        loaded.solve(128,64,512,64,"Q4","P1","smooth",.04)
