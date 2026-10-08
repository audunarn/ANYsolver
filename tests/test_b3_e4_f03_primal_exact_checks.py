"""Small synthetic arithmetic/ownership tests; no frozen Ritz state is read."""
import copy
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_primal_exact_pose as exact
import _b3_e4_f03_primal_exact_checks as checks


def fixture():
    n=2;d=6;q=np.zeros(d);q[3]=2.**-8
    pose=exact.reconstruct(n,q)
    coefficients=np.array(pose.legendre,dtype=np.float64).T.copy()
    # Independent closed-form n2, uy_(0,0) action. Unused columns are
    # zero synthetic data, not a complete element/pose operator.
    m2=exact.DX**2+exact.A**2/3
    arrays={'q':q,'b_coefficients':coefficients}
    for order,key in enumerate(('station_A','station_A1','station_A2')):
        actions=np.zeros((9,3,d))
        for index,s in enumerate(exact.STATIONS):
            tau=s-Fraction(1,2)
            v=(1-tau*tau-m2,-2*tau,Fraction(-2))[order]
            theta=(-2*tau*m2/exact.HELD_J,-2*m2/exact.HELD_J,Fraction(0))[order]
            actions[index,1,3]=float(v)
            actions[index,2,3]=float(theta)
        arrays[key]=actions
    original={'status':'FAILED_NUMERICAL_SCREEN','reproduced_decision':{
        'metrics':{'checks':{'saved_action_parity_scaled':2e-11}}}}
    return n,arrays,original


def test_exact_identities_do_not_erase_original_failure(monkeypatch):
    n,arrays,original=fixture()
    def forbidden(*args,**kwargs):
        raise AssertionError('no assembly, projection or numeric verifier')
    monkeypatch.setattr(checks.constants,'assemble',forbidden)
    monkeypatch.setattr(checks.constants,'pose_operators',forbidden)
    import _b3_e4_f03_primal_checks as old
    monkeypatch.setattr(old,'verify_saved',forbidden)
    monkeypatch.setattr(old,'_project_b',forbidden)
    before={k:v.copy() for k,v in arrays.items()}
    record=checks.evaluate_saved(n,arrays,original)
    assert record['diagnostic_status']=='PASSED_REPRESENTATION_DIAGNOSTIC'
    assert all(record['checks'].values())
    assert record['original_full_saved_action']['value']==2e-11
    assert record['original_full_saved_action']['case_status']=='FAILED_NUMERICAL_SCREEN'
    assert record['derivative_binding']['value']!=2e-11
    for key in arrays:
        np.testing.assert_array_equal(arrays[key],before[key])
    for order in record['terms']:
        for station in order:
            for row in station:
                values=[Fraction(int(p[0]),int(p[1])) for p in row]
                assert values[0]==sum(values[1:],Fraction(0))
    # JSON round-trip reproduces exact bits/types, including lossless fractions.
    reloaded=json.loads(json.dumps(record,allow_nan=False))
    assert checks.verify_saved_record(reloaded,n,arrays,original)==record
    saved=json.dumps(record,sort_keys=True)
    arrays['q'][3]=0.
    assert json.dumps(record,sort_keys=True)==saved


def test_coefficient_error_and_endpoint_triangle_are_separate():
    n,arrays,original=fixture()
    arrays['b_coefficients'][2,1]+=2.**-30
    record=checks.evaluate_saved(n,arrays,original)
    assert record['diagnostic_status']=='PASSED_REPRESENTATION_DIAGNOSTIC'
    assert not record['derivative_binding']['passes_original_limit']
    terms=record['terms'][2][8][1]
    coefficient=checks._parse_pair(terms[2])
    signed,triangle=map(checks._parse_pair,record['endpoint_bounds'][1][1][1])
    assert coefficient==signed and abs(signed)<=triangle
    assert abs(float(coefficient))>1e-9
    assert record['endpoint_weights'][1][1][2]==['12','1']


@pytest.mark.parametrize('pair',[
    ['00','1'],['-0','1'],['0','2'],['1','0'],['1','-2'],['+1','2'],['2','4'],
    ['1'*4097,'1']])
def test_malformed_rational_precedes_serialization(pair,monkeypatch):
    n,arrays,original=fixture()
    record=checks.evaluate_saved(n,arrays,original)
    record['terms'][0][0][0][0]=pair
    def forbidden(*args,**kwargs):
        raise AssertionError('must preflight before allocating JSON')
    monkeypatch.setattr(checks.json,'dumps',forbidden)
    with pytest.raises(ValueError,match='rational'):
        checks.validate_payload(record,n)


def test_whole_case_counts_and_exact_recomputation(monkeypatch):
    n,arrays,original=fixture()
    record=checks.evaluate_saved(n,arrays,original)
    with monkeypatch.context() as patch:
        patch.setattr(checks,'MAX_RATIONAL_PAIRS',10)
        with pytest.raises(ValueError,match='rational count'):
            checks.validate_payload(record,n)
    changed=copy.deepcopy(record)
    changed['terms'][0][0][0][0]=['1','2']
    with pytest.raises(ValueError,match='value changed'):
        checks.verify_saved_record(changed,n,arrays,original)
    changed=copy.deepcopy(record)
    changed['floating']['normalizers'][0]=True
    with pytest.raises(ValueError,match='display'):
        checks.verify_saved_record(changed,n,arrays,original)
    changed=copy.deepcopy(record);changed['extra']=0
    with pytest.raises(ValueError,match='inventory'):
        checks.validate_payload(changed,n)
    changed=copy.deepcopy(record);changed['diagnostic_status']='FAILED_DIAGNOSTIC_IDENTITY'
    with pytest.raises(ValueError,match='contradictory'):
        checks.validate_payload(changed,n)


def test_sub_ulp_geometry_corruption_is_not_an_exact_identity(monkeypatch):
    n,arrays,original=fixture()
    pose=exact.reconstruct(n,arrays['q'])
    wrong=replace(pose,held_J=pose.held_J+Fraction(1,2**300))
    assert float(wrong.held_J)==float(pose.held_J)
    monkeypatch.setattr(exact,'reconstruct',lambda degree,q:wrong)
    record=checks.evaluate_saved(n,arrays,original)
    assert not record['checks']['held_source_geometry']
    assert record['diagnostic_status']=='FAILED_DIAGNOSTIC_IDENTITY'
