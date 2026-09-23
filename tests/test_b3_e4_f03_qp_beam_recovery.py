"""Independent, bounded signed virtual-work checks for Qp beam recovery."""

import math

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0, F0, SECTION
from scripts._b3_e4_f03_qp_beam_recovery import recover_interface
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import (
    PiecewisePadMomentOracle, REPRESENTED_J,
)


CUSTOM_X = (-.5, -.35, -.11, .08, .31, .67, .94, 1.23, 1.5)
CUSTOM_Y = (-.5, -.31, -.09, .11, .31, .5)


@pytest.mark.parametrize("degree,custom,j", [
    (1, True, REPRESENTED_J),
    (2, True, 1.07*REPRESENTED_J),
    (3, True, REPRESENTED_J),
    (1, False, REPRESENTED_J),
    (2, False, REPRESENTED_J),
])
def test_signed_virtual_work_with_physical_endpoint_atoms(degree, custom, j):
    x, y = (CUSTOM_X, CUSTOM_Y) if custom else (None, None)
    trace = FinitePadQpTrace(degree, x=x, y=y, j=j)
    oracle = PiecewisePadMomentOracle(degree, x=x, y=y, j=j)
    rng = np.random.default_rng(1820+10*degree+int(custom))
    q = rng.normal(size=2*trace.n)*2e-4
    w = rng.normal(size=2*trace.n)*3e-4
    # Both fields obey precisely the essential shell-edge values.
    supported = np.setdiff1d(np.arange(2*trace.n), trace.free_columns)
    q[supported] = w[supported] = 0.
    eta = np.array((1.6e5, -2.2e5, 7.1e4))
    q_coeff, w_coeff = oracle.coefficients(q), oracle.coefficients(w)

    # Build a fixed piecewise station rule before evaluating either side of
    # the identity. Every represented interval, including one-ulp ones,
    # retains its own quadrature measure.
    roots, weights = np.polynomial.legendre.leggauss(10)
    stations, station_weights = [], []
    for left, right in trace.station_intervals():
        stations.extend((left+right)/2+(right-left)*roots/2)
        station_weights.extend((right-left)*weights/2)
    stations = np.asarray(stations)
    station_weights = np.asarray(station_weights)
    recovered = recover_interface(trace, q, eta, stations)

    # This route reconstructs local cell polynomials and clips pad moments;
    # it does not multiply the Qp trace's matrices into either virtual field.
    pose_w = np.array([oracle.evaluate(w_coeff, float(s))[0]
                       for s in stations])
    lhs = float(np.einsum("i,ij,ij->", station_weights,
                          recovered["density"], pose_w))
    root_w = oracle.evaluate(w_coeff, 0., side="right")[0]
    tip_w = oracle.evaluate(w_coeff, 1., side="left")[0]
    lhs += recovered["root_atom"]@root_w
    lhs += recovered["tip_atom"]@tip_w

    beam_work = load_work = 0.
    ea, ei, ga = np.diag(SECTION)
    for s, weight in zip(stations, station_weights):
        q_pose, q_first, _ = oracle.evaluate(q_coeff, float(s))
        w_pose, w_first, _ = oracle.evaluate(w_coeff, float(s))
        # Independently evaluated section expressions in physical order.
        n = ea*q_first[0]
        shear = ga*(q_first[1]-q_pose[2])
        moment = ei*q_first[2]
        beam_work += weight*(n*w_first[0] +
                             shear*(w_first[1]-w_pose[2]) +
                             moment*w_first[2])
        load_work += weight*F0*(1.+.25*math.cos(2.*math.pi*s))*w_pose[1]
    rhs = load_work-beam_work-eta@root_w
    # E0=F0*U0 is the declared physical absolute floor. Scale by the two
    # sides of the identity, rather than a potentially cancelling component.
    signed_defect = lhs-rhs
    work_scale = max(E0, abs(lhs), abs(rhs))
    assert abs(signed_defect)/work_scale <= 1e-10, (
        f"p={degree}, custom={custom}, signed defect={signed_defect:.17e}, "
        f"scale={work_scale:.17e}")

    root_q = oracle.evaluate(q_coeff, 0., side="right")
    tip_q = oracle.evaluate(q_coeff, 1., side="left")
    def section(pose, first):
        return np.array((ea*first[0], ga*(first[1]-pose[2]),
                         ei*first[2]))
    root_section = section(*root_q[:2])
    tip_section = section(*tip_q[:2])
    np.testing.assert_allclose(recovered["root_section_resultant"],
                               root_section, rtol=0, atol=2e-5)
    np.testing.assert_allclose(recovered["tip_section_resultant"],
                               tip_section, rtol=0, atol=2e-5)
    np.testing.assert_allclose(recovered["root_atom"], root_section-eta,
                               rtol=0, atol=2e-5)
    np.testing.assert_allclose(recovered["tip_atom"], -tip_section,
                               rtol=0, atol=2e-5)
    np.testing.assert_array_equal(recovered["root_reaction"], -eta)
    assert abs(recovered["root_atom"][2]) > 1e3
    assert abs(recovered["tip_atom"][2]) > 1e3
    assert np.linalg.norm(recovered["root_atom"]) > 1e3
    assert np.linalg.norm(recovered["tip_atom"]) > 1e3

    endpoints = recover_interface(trace, q, eta, np.array([0., 1.]),
                                  sides=("left", "right"))
    for index, (station, side) in enumerate(((0., "right"), (1., "left"))):
        pose, first, second = oracle.evaluate(q_coeff, station, side=side)
        expected = np.array((ea*second[0],
            ga*(second[1]-first[2])+F0*(1.+.25*math.cos(2.*math.pi*station)),
            ei*second[2]+ga*(first[1]-pose[2])))
        np.testing.assert_allclose(endpoints["density"][index], expected,
                                   rtol=0, atol=2e-5)

    # At a crossing, A and A' agree from both sides, while A'' and the
    # ordinary line density may jump. No event delta belongs in this law.
    events = trace.station_breakpoints()[1:-1]
    event = max(events, key=lambda s: np.linalg.norm(
        oracle.evaluate(q_coeff, s, side="left")[2] -
        oracle.evaluate(q_coeff, s, side="right")[2]))
    left = recover_interface(trace, q, eta, np.array([event]), sides="left")
    right = recover_interface(trace, q, eta, np.array([event]), sides="right")
    for side, actual in (("left", left), ("right", right)):
        pose, first, second = oracle.evaluate(q_coeff, event, side=side)
        expected = np.array((ea*second[0],
            ga*(second[1]-first[2])+F0*(1.+.25*math.cos(2.*math.pi*event)),
            ei*second[2]+ga*(first[1]-pose[2])))
        np.testing.assert_allclose(actual["density"][0], expected,
                                   rtol=0, atol=2e-5)
        np.testing.assert_allclose(actual["root_atom"],
                                   recovered["root_atom"], rtol=0, atol=0)
    assert np.linalg.norm(left["density"]-right["density"]) > 1e2


def test_recovery_rejects_invalid_physical_state():
    trace = FinitePadQpTrace(1, x=CUSTOM_X, y=CUSTOM_Y)
    q = np.zeros(2*trace.n)
    eta = np.zeros(3)
    with pytest.raises(ValueError, match="state"):
        recover_interface(trace, q[:-1], eta, np.array([.5]))
    with pytest.raises(ValueError, match="state"):
        recover_interface(trace, q, eta, np.array([float("nan")]))
    with pytest.raises(ValueError, match="side"):
        recover_interface(trace, q, eta, np.array([.5]), sides=("left", "right"))
