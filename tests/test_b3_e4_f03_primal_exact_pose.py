"""Synthetic Fraction identities only: no saved state or equilibrium case."""

from dataclasses import FrozenInstanceError,replace
from fractions import Fraction
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_primal_exact_pose as exact


def _single(n,component,i,j,value=1.):
    m=n*n-1
    q=np.zeros(2*m,dtype=np.float64)
    q[component*m+i*(n+1)+j]=value
    return q


def test_degree_two_vertical_basis_has_independent_exact_moments():
    pose=exact.reconstruct(2,_single(2,1,0,0))
    xi2=exact._moment(exact.DX,exact.A,2)
    eta2=exact._moment(exact.DY,exact.A,2)
    assert pose.legendre[0]==(Fraction(0),)*3
    assert pose.legendre[1]==(Fraction(11,12)-xi2,0,Fraction(-1,6))
    assert pose.legendre[2]==(0,-xi2/exact.HELD_J,0)
    assert pose.J_geom==xi2+eta2
    assert pose.gamma==pose.J_geom/pose.held_J
    assert pose.gamma!=1  # Held rounded J is not the exact moment of its bits.
    assert exact.station_derivatives(pose)==(
        exact.station_derivatives_legendre(pose))
    with pytest.raises(FrozenInstanceError):
        pose.gamma=Fraction(1)


def test_degree_two_horizontal_odd_y_mode_and_zero_translation():
    pose=exact.reconstruct(2,_single(2,0,0,1))
    eta2=exact._moment(exact.DY,exact.A,2)
    assert all(value==0 for value in pose.legendre[0])
    assert all(value==0 for value in pose.legendre[1])
    vertical=exact.reconstruct(2,_single(2,1,0,0))
    assert pose.legendre[2]==tuple(-2*eta2*value/exact.HELD_J
                                    for value in vertical.legendre[1])
    assert exact.station_derivatives(pose)==(
        exact.station_derivatives_legendre(pose))


def test_mixed_degree_three_exact_evaluations_and_input_ownership():
    n=3;q=np.arange(1,2*(n*n-1)+1,dtype=np.float64)/64
    pose=exact.reconstruct(n,q)
    original=pose.legendre
    q[:]=0
    assert pose.legendre==original
    assert pose.q[0]==Fraction(1,64)
    tau=exact.station_derivatives(pose)
    assert tau==exact.station_derivatives_legendre(pose)
    assert len(tau)==3 and all(len(level)==9 for level in tau)
    saved=np.zeros((n+1,3),dtype=np.float64)
    for j in range(n+1):
        for channel in range(3):
            saved[j,channel]=float(pose.legendre[channel][j])
    saved[2,1]+=2**-30
    bound=exact.endpoint_coefficient_bound(saved,pose,1,2,1)
    decomposition=exact.decompose_discrepancy(saved,pose,1,2,8,
                                              0.25,-0.5)
    assert bound.weights[2]==12
    assert decomposition.coefficient_reconstruction==bound.signed
    assert decomposition.total==Fraction(3,4)
    assert (decomposition.floating_polynomial+
            decomposition.coefficient_reconstruction+
            decomposition.direct_action)==decomposition.total
    assert abs(bound.signed)<=bound.triangle


def test_degree_twenty_four_endpoint_weights_and_signed_cancellation():
    n=24
    zeros=(Fraction(0),)*(n+1)
    pose=exact.ExactPose(n,(),exact.DX,exact.DY,exact.A,
        exact.HELD_J,exact.DX**2+exact.DY**2+2*exact.A**2/3,
        (exact.DX**2+exact.DY**2+2*exact.A**2/3)/exact.HELD_J,
        (zeros,zeros,zeros),(zeros,zeros,zeros))
    saved=np.zeros((n+1,3),dtype=np.float64)
    saved[24,0]=2**-40
    saved[23,0]=-2**-40
    right=exact.endpoint_coefficient_bound(saved,pose,0,2,1)
    left=exact.endpoint_coefficient_bound(saved,pose,0,2,0)
    first=exact.endpoint_coefficient_bound(saved,pose,0,1,1)
    assert right.weights[24]==179400
    assert left.weights[24]==179400
    assert left.weights[23]==-right.weights[23]
    assert first.weights[24]==600
    assert right.signed==(right.weights[24]-right.weights[23])*Fraction(1,2**40)
    assert right.triangle>abs(right.signed)


def test_lossless_rational_record_and_bounded_mutation_rejections():
    pose=exact.reconstruct(3,_single(3,1,1,2,.125))
    record=exact.to_record(pose)
    assert exact.from_record(json.loads(json.dumps(record)))==pose
    record['geometry']['gamma'][0]='1'
    with pytest.raises(ValueError,match='inconsistent'):
        exact.from_record(record)
    record=exact.to_record(pose)
    record['q'][0][1]='0'
    with pytest.raises(ValueError,match='denominator'):
        exact.from_record(record)
    record=exact.to_record(pose)
    record['q'][0][0]='01'
    with pytest.raises(ValueError,match='pair'):
        exact.from_record(record)


def test_rational_schema_preflight_precedes_json_allocation(monkeypatch):
    pose=exact.reconstruct(2,_single(2,1,0,0))
    record=exact.to_record(pose)
    record['q'][0][0]='1'*4097
    def forbidden_dump(*args,**kwargs):
        raise AssertionError('unvalidated record was serialized')
    monkeypatch.setattr(exact.json,'dumps',forbidden_dump)
    with pytest.raises(ValueError,match='pair'):
        exact.from_record(record)
    huge=replace(pose,q=(Fraction(10**4097),)+pose.q[1:])
    with pytest.raises(ValueError,match='canonical rational bound'):
        exact.to_record(huge)


@pytest.mark.parametrize('n,q',((1,np.zeros(0,dtype=np.float64)),
                                  (25,np.zeros(0,dtype=np.float64)),
                                  (2,np.zeros(6,dtype=np.float32)),
                                  (2,np.ones(4,dtype=np.float64)),
                                  (2,np.full(6,np.nan,dtype=np.float64))))
def test_invalid_bounded_coefficient_vector(n,q):
    with pytest.raises(ValueError):
        exact.reconstruct(n,q)


def test_external_float_terms_reject_nonfinite_and_boolean_endpoint():
    pose=exact.reconstruct(2,_single(2,1,0,0))
    coefficients=np.zeros((3,3),dtype=np.float64)
    with pytest.raises(ValueError,match='endpoint'):
        exact.endpoint_coefficient_bound(coefficients,pose,1,2,True)
    with pytest.raises(ValueError,match='finite binary64'):
        exact.decompose_discrepancy(coefficients,pose,1,2,8,
                                    float('nan'),0.)
