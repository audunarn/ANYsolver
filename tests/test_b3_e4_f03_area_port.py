"""Physical finite-pad pose proofs for a separate classical F03 model."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_area_port as area
import _b3_e4_f03_independent_shell as shell


@pytest.mark.parametrize("topology",("Q4","CST","CST-CB"))
@pytest.mark.parametrize("station,halfwidth",((0.,.02),(.37,.075),(1.,.03)))
def test_rigid_pose_and_resultant_work_across_element_hosts(topology,station,halfwidth):
    model=shell.panel(3,6,topology)
    pose=area.pose(model,station,halfwidth)
    tx,ty,omega=(.00013,-.00008,.00021)
    q=np.array([value for x,y in model.nodes
                for value in (tx-omega*y,ty+omega*(x-station))])
    np.testing.assert_allclose(pose@q,(tx,ty,omega),rtol=2e-11,atol=2e-15)
    force=np.array((123.,-456.,78.))
    nodal=pose.T@force
    np.testing.assert_allclose(np.sum(nodal[0::2]),force[0],rtol=2e-11,atol=2e-9)
    np.testing.assert_allclose(np.sum(nodal[1::2]),force[1],rtol=2e-11,atol=2e-9)
    moment=np.sum((model.nodes[:,0]-station)*nodal[1::2]-
                  model.nodes[:,1]*nodal[0::2])
    assert moment==pytest.approx(force[2],rel=2e-11,abs=2e-9)
    assert q@nodal==pytest.approx(force@np.array((tx,ty,omega)),
                                 rel=2e-11,abs=2e-9)


def test_bilinear_q4_field_and_pad_second_moment():
    model=shell.panel(4,8,"Q4")
    station=.37
    halfwidth=.06
    q=np.array([value for x,y in model.nodes for value in (x*y,0.)])
    actual=area.pose(model,station,halfwidth)@q
    inertia=shell.YAW_DENOMINATOR/4+2*halfwidth**2/3
    y_second=.23**2+halfwidth**2/3
    np.testing.assert_allclose(actual,(0.,0.,-station*y_second/inertia),
                               rtol=1e-12,atol=1e-13)


@pytest.mark.parametrize("topology",("Q4","CST-CB"))
def test_general_affine_field_has_proper_fit_yaw(topology):
    model=shell.panel(3,6,topology)
    station=.37
    halfwidth=.071
    ex,ey,gamma,delta=(.014,-.021,.032,-.025)
    q=np.array([value for x,y in model.nodes
                for value in (ex*x+gamma*y,delta*x+ey*y)])
    x2=.2**2+halfwidth**2/3
    y2=.23**2+halfwidth**2/3
    inertia=x2+y2
    expected=(ex*station,delta*station,(delta*x2-gamma*y2)/inertia)
    np.testing.assert_allclose(area.pose(model,station,halfwidth)@q,
                               expected,rtol=3e-12,atol=3e-14)


@pytest.mark.parametrize("bad",(0.,1e-5,-.01,.201,float("nan")))
def test_invalid_pad_width_rejected(bad):
    model=shell.panel(2,4,"Q4")
    with pytest.raises(ValueError):
        area.pose(model,.5,bad)
