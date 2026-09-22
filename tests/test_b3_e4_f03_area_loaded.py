"""Small finite-pad equilibrium checks; no physical convergence claim."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_area_loaded as loaded
import _b3_e4_f03_area_line as area
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell


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
    assert result.fixed_scale_gap==pytest.approx(result.gap_l2_m/loaded.scaling.U0)
    assert result.motion_scale_gap==pytest.approx(
        result.gap_l2_m/max(result.motion_rms_m,.1*loaded.scaling.U0))
    assert result.motion_rms_m>0
    assert len(result.shell_station_displacements_m)==3
    assert np.all(np.isfinite(result.shell_station_displacements_m))
    assert np.allclose(
        np.array(result.beam_root_elastic_wrench)+
        np.array(result.beam_root_port_wrench)-
        np.array(result.beam_root_load_wrench),result.support_wrenches[2],
        rtol=1e-10,atol=1e-5)
    assert np.shape(result.beam_port_quarter_wrenches)==(4,3)
    assert np.all(np.isfinite(result.beam_port_quarter_wrenches))


@pytest.mark.parametrize("law",("P0","P1"))
def test_quarter_wrenches_integrate_analytic_multiplier_density(law):
    n=4
    if law=="P0":
        # A constant physical force and yaw couple per unit beam coordinate.
        lam=np.tile([3.,-5.,7.],n)
    else:
        # Linear physical force and yaw couple densities, exactly represented.
        lam=np.array([[3.+2.*i/n,-5.+4.*i/n,7.-6.*i/n]
                      for i in range(n+1)]).ravel()
    actual=np.array(loaded._port_quarters(lam,n,law))
    for i in range(4):
        a,b=i/4,(i+1)/4
        midpoint=(a+b)/2
        if law=="P0":
            expected=(3.*(b-a),-5.*(b-a),
                      -5.*(b*b-a*a)/2+loaded.original.YAW_LENGTH*7.*(b-a))
        else:
            expected=((3.+2*midpoint)*(b-a),
                      (-5.+4*midpoint)*(b-a),
                      (-5.)*(b*b-a*a)/2+4*(b**3-a**3)/3+
                      loaded.original.YAW_LENGTH*(7.-6*midpoint)*(b-a))
        assert actual[i]==pytest.approx(expected,abs=1e-12)


def test_quarter_sum_equals_independent_beam_rigid_virtual_work():
    cells,mortar=4,4
    model=shell.panel(2,4,"CST-CB")
    _,cb,_=area.coupling(model,cells,mortar,"P1",.05)
    lam=np.arange(3*(mortar+1),dtype=float)/7-1.
    total=np.sum(loaded._port_quarters(lam,mortar,"P1"),axis=0)
    u=2*cells+1
    theta=u+2*(cells+1)
    for tx,ty,omega in ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)):
        q=np.zeros(beam.dof_count(cells))
        q[:u]=tx
        q[theta:]=omega
        for node in range(cells+1):
            q[u+2*node]=ty+omega*node/cells
            q[u+2*node+1]=omega
        assert (cb.T@lam)@q==pytest.approx(
            total@np.array((tx,ty,omega)),rel=1e-9,abs=1e-9)


def test_invalid_small_model_is_explicitly_rejected():
    with pytest.raises(ValueError):
        loaded.solve(128,64,512,64,"Q4","P1","smooth",.04)
