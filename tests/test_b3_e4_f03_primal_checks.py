"""Bounded unit checks for the independently assembled Ritz evidence audit."""

import sys
import json
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_primal_checks as checks
import _b3_e4_f03_primal_ritz as ritz


def test_tiny_canonical_crosscheck_and_saved_audit_without_assembly(monkeypatch):
    result,arrays=checks.evaluate_case(3)
    assert set(arrays)==set(checks.expected_shapes(3))
    assert all(v<=checks.LIMITS[name] for name,v in result['checks'].items())
    assert result['observables']['total_energy_j']>0
    assert np.max(np.abs(result['observables']['tip_pose_scaled']))>0
    np.testing.assert_allclose(np.asarray(result['observables']['root_elastic'])+
                               result['observables']['root_atom'],
                               result['observables']['root_reaction'],atol=1e-8)
    np.testing.assert_allclose(np.asarray(result['observables']['tip_elastic'])+
                               result['observables']['tip_atom'],0,atol=1e-8)
    def no_second_case(*args,**kwargs):
        raise AssertionError('saved audit assembled or solved equilibrium')
    monkeypatch.setattr(ritz,'assemble',no_second_case)
    monkeypatch.setattr(ritz,'solve',no_second_case)
    assert checks.verify_saved(arrays,3)==result
    # Actual computed metrics include NumPy real scalars, which JSON reloads
    # as Python floats. The evidence comparison must preserve their value.
    from b3_e4_f03_primal_ritz import bind_metrics
    bind_metrics(json.loads(json.dumps(result,allow_nan=False)),result)


def test_saved_actions_inconsistency_and_strict_owned_inventory():
    _,arrays=checks.evaluate_case(2)
    assert arrays['q'].dtype==np.float64
    assert checks.verify_saved(arrays,2)['checks']['root_slope_rank_violation']==1
    changed={k:v.copy() for k,v in arrays.items()}
    changed['H_z'][0]+=1e-4
    assert checks.verify_saved(changed,2)['checks']['saved_action_parity_scaled']>1e-11
    coherent={k:v.copy() for k,v in arrays.items()}
    coherent['D']*=1.01
    coherent['z'][:-3]/=1.01
    d=coherent['D']
    r=np.diag((1/ritz.U0,1/ritz.U0,ritz.YAW_LENGTH/ritz.U0))
    k=coherent['K_shell']+coherent['K_beam']
    cbar=r@coherent['C_root']@np.diag(d)
    h=np.block([[d[:,None]*k*d[None,:]/ritz.E0,cbar.T],
                [cbar,np.zeros((3,3))]])
    coherent['H_z']=h@coherent['z']
    assert checks.verify_saved(coherent,2)['checks'][
        'scaling_D_parity_relative']>checks.LIMITS['scaling_D_parity_relative']
    invalid={k:v.copy() for k,v in arrays.items()}
    invalid['D'][0]*=-1
    with pytest.raises(ValueError,match='nonpositive saved Ritz'):
        checks.verify_saved(invalid,2)
    for key,index,increment in (('q',0,1e-7),
                                ('b_coefficients',(0,1),1e-7),
                                ('density_coefficients',(0,1),1e5)):
        altered={k:v.copy() for k,v in arrays.items()}
        altered[key][index]+=increment
        if key=='density_coefficients':
            with pytest.raises(ValueError,match='saved Green norm'):
                checks.verify_saved(altered,2)
        else:
            report=checks.verify_saved(altered,2)
            assert any(report['checks'][name]>limit for name,limit in
                       checks.LIMITS.items()),key
    _,varying=checks.evaluate_case(3)
    for key in ('station_A1','station_A2'):
        altered={k:v.copy() for k,v in varying.items()}
        qindex=int(np.argmax(np.abs(varying['q'])))
        altered[key][4,1,qindex]+=1e-4
        altered[key+'_plus'][4,1,qindex]+=1e-4
        assert checks.verify_saved(altered,3)['checks'][
            'saved_action_parity_scaled']>checks.LIMITS['saved_action_parity_scaled']
    bad={k:v.copy() for k,v in arrays.items()}
    bad['eta']=bad['eta'].astype(np.float32)
    with pytest.raises(ValueError,match='invalid primal saved array eta'):
        checks.verify_saved(bad,2)
    bad={k:v.copy() for k,v in arrays.items()}
    bad['A_tip']=bad['station_A'][-1]
    with pytest.raises(ValueError,match='aliased'):
        checks.verify_saved(bad,2)
    with pytest.raises(ValueError,match='inventory'):
        checks.verify_saved({k:v for k,v in arrays.items() if k!='eta'},2)


def test_frozen_inventory_bounds():
    for n in (2,3,4,8,12,16,24):
        expected=checks.expected_shapes(n)
        assert expected['K_shell']==(2*(n*n-1),)*2
        assert expected['virtual_work_defects']==(3,n+3)
    for n in (1,25,2.0,True):
        with pytest.raises(ValueError):
            checks.expected_shapes(n)


def test_undefined_perturbation_bound_is_finite_numerical_failure():
    _,arrays=checks.evaluate_case(3)
    changed={k:v.copy() for k,v in arrays.items()}
    changed['K_shell_plus']+=1e12*np.eye(len(changed['q']))
    report=checks.verify_saved(changed,3)
    assert report['checks']['perturbation_alpha_violation']==1
    assert report['checks']['perturbation_bound_violation']==1
    assert report['details']['perturbation_bound'] is None
    json.dumps(report,allow_nan=False)


def test_negative_green_norm_stays_signed_numerical_failure(monkeypatch):
    original_solve=ritz.solve
    calls=[]
    def counted_solve(operators):
        calls.append(operators.n)
        return original_solve(operators)
    monkeypatch.setattr(ritz,'solve',counted_solve)
    def negative_channels(*args,**kwargs):
        return np.array((-2.,.5,.5))
    monkeypatch.setattr(checks.functional,'green_inner',negative_channels)
    report,arrays=checks.evaluate_case(3)
    assert np.array_equal(arrays['norms_squared'],[-1.,-1.])
    assert np.array_equal(arrays['norms_squared_valid'],[1.,1.])
    assert report['checks']['functional_norm_nonnegative_violation']==1
    assert report['observables']['full_functional_norm_N'] is None
    assert checks.verify_saved(arrays,3)==report
    assert calls==[3]
    json.dumps(report,allow_nan=False)


@pytest.mark.parametrize('nonfinite_route',('returned','raised','overflow'))
def test_unavailable_green_norm_has_typed_nan_only_and_numerical_flag(
        monkeypatch,nonfinite_route):
    original_solve=ritz.solve
    calls=[]
    def counted_solve(operators):
        calls.append(operators.n)
        return original_solve(operators)
    monkeypatch.setattr(ritz,'solve',counted_solve)
    def nonfinite(*args,**kwargs):
        if nonfinite_route=='raised':
            raise checks.functional.NonfiniteGreenResponse(
                'nonfinite Green inner product')
        if nonfinite_route=='overflow':
            return np.array((1e308,1e308,1e308))
        return np.array((np.nan,2.,3.))
    monkeypatch.setattr(checks.functional,'green_inner',nonfinite)
    report,arrays=checks.evaluate_case(3)
    assert calls==[3]
    assert np.all(np.isnan(arrays['norms_squared']))
    assert np.array_equal(arrays['norms_squared_valid'],[0.,0.])
    assert not np.any(np.isinf(arrays['norm_channels_squared']))
    assert report['checks']['functional_norm_nonfinite_violation']==1
    assert report['checks']['functional_norm_resolution_violation']==1
    assert report['observables']['full_functional_norm_N'] is None
    assert report['details']['functional_norm_resolution'] is None
    assert checks.verify_saved(arrays,3)==report
    json.dumps(report,allow_nan=False)


def test_unrelated_green_programming_error_is_not_a_numerical_measurement(
        monkeypatch):
    def broken(*args,**kwargs):
        raise ValueError('unrelated malformed input')
    monkeypatch.setattr(checks.functional,'green_inner',broken)
    with pytest.raises(ValueError,match='unrelated malformed input'):
        checks.evaluate_case(2)
