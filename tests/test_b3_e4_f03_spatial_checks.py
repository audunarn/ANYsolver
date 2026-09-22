"""Manufactured integration and corrupted raw-integral adversarial checks."""
from copy import deepcopy

import numpy as np
import pytest

from scripts import _b3_e4_f03_primal_exact_pose as exact
from scripts import _b3_e4_f03_spatial_checks as checks
from scripts import _b3_e4_f03_spatial_contract as c


@pytest.fixture(scope='module')
def raw():
    n=3;m=n*n-1
    q=np.zeros(2*m,dtype=np.float64)
    q[1]=1e-6;q[m]=2e-6;q[m+5]=-7e-7
    arrays={'q':q,'eta':np.array((31.,-23.,17.)),
            'density_coefficients':np.zeros((n+1,3)),
            'atoms':np.zeros((2,3)),'edge_route1':np.zeros((2,3))}
    return checks.evaluate_saved(n,arrays,exact.to_record(exact.reconstruct(n,q)))


def test_all_three_work_routes_and_reactions_on_manufactured_state(raw):
    decision=checks.adjudicate_record(raw,3)
    assert decision['status']=='PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC',decision['failures']
    assert len(decision['metrics'])==42
    assert max(decision['metrics'].values())<1e-11
    # These fields are deliberately not an equilibrium: nonzero spatial
    # defects are legitimate diagnostic data, never an accuracy pass.
    summary=decision['summaries']['64']
    assert sum(summary['cell_residual_squared_scaled'])>0
    assert sum(summary['free_traction_squared_scaled'])>0
    assert summary['shell_energy']>0 and summary['beam_energy']>0
    assert raw['work']['equilibrium_solves']==0
    assert raw['work']['fixed_rule_integrations']==2
    for key in checks.RULE_SHAPES:
        np.testing.assert_array_equal(
            decision['summaries']['signed_quadrature_differences'][key],
            np.array(raw['rules']['48'][key])-np.array(raw['rules']['64'][key]))


@pytest.mark.parametrize('field,index',[
    ('cell_load_work',(10,4,1)),
    ('cell_strain_work',(0,9)),
    ('cell_volume_work',(0,9)),
    ('free_work',(0,9)),
    ('support_work',(0,3)),
    ('trace_work',(4,2)),
    ('beam_weak_work_parts',(4,1)),
    ('cell_load_wrenches',(10,1,2)),
    ('cell_residual_wrenches',(10,1)),
])
def test_each_independent_integral_route_detects_damage(raw,field,index):
    record=deepcopy(raw)
    for order in ('48','64'):
        entry=record['rules'][order][field]
        for i in index[:-1]: entry=entry[i]
        entry[index[-1]]+=c.F0
    decision=checks.adjudicate_record(record,3)
    assert decision['status']=='FAILED_NUMERICAL_IDENTITY'
    assert decision['failures']


def test_quadrature_squares_are_compared_without_physical_size_threshold(raw):
    record=deepcopy(raw)
    record['rules']['48']['cell_residual_squares'][0]+=c.F0**2
    decision=checks.adjudicate_record(record,3)
    assert 'quadrature_cell_residual_squares' in decision['failures']


@pytest.mark.parametrize('damage',[
    lambda r:r['rules']['48']['free_work'][0].__setitem__(0,float('nan')),
    lambda r:r['rules']['48']['free_work'][0].__setitem__(0,True),
    lambda r:r['rules']['48']['free_work'].pop(),
    lambda r:r['rules']['48']['cell_residual_squares'].__setitem__(0,-1.),
    lambda r:r['functional']['density'][0].__setitem__(0,['02','1']),
    lambda r:r['functional']['atoms'][0].__setitem__(0,['1','0']),
    lambda r:r['functional']['gamma'].__setitem__(0,'1'),
    lambda r:r['work'].__setitem__('saved_state_compilations',True),
    lambda r:r['rules']['48']['beam_energy_load_root_work'].__setitem__(0,-1.),
    lambda r:r['rules']['48']['free_work'][0].__setitem__(0,10**500),
    lambda r:r['one_sided']['coordinates'][0][0][0].__setitem__(0,.1),
])
def test_malformed_evidence_is_not_a_numerical_failure(raw,damage):
    record=deepcopy(raw);damage(record)
    with pytest.raises(ValueError): checks.adjudicate_record(record,3)


def test_pose_coefficients_are_validated_before_field_construction(monkeypatch):
    q=np.zeros(6,dtype=np.float64)
    pose=exact.to_record(exact.reconstruct(2,q))
    pose['legendre'][0][0]=['1','1']
    def forbidden(*args,**kwargs):
        raise AssertionError('must reject altered pose before field compilation')
    monkeypatch.setattr(checks.physical,'model_from_saved',forbidden)
    with pytest.raises(ValueError): checks.evaluate_saved(2,{'q':q},pose)


def test_one_sided_samples_keep_distinct_atom_branches(raw):
    value=np.array(raw['one_sided']['load_channels'])
    # At x=-dx-a in the lower pad strip, the left cell and right cell
    # report their own root-atom continuation, including both corners.
    assert np.linalg.norm(value[9,1,:,1]-value[10,0,:,1])>0


def test_opposite_cell_wrench_corruption_cannot_cancel_globally(raw):
    record=deepcopy(raw)
    for order in ('48','64'):
        record['rules'][order]['cell_load_wrenches'][10][1][0]+=c.F0
        record['rules'][order]['cell_load_wrenches'][11][1][0]-=c.F0
    result=checks.adjudicate_record(record,3)
    assert 'order_64_cell_load_wrench_work' in result['failures']


def test_finite_raw_overflow_is_evidence_failure(raw):
    record=deepcopy(raw)
    for order in ('48','64'):
        for row in record['rules'][order]['cell_volume_work']:
            row[0]=1e308
    with np.errstate(over='ignore',invalid='ignore'):
        with pytest.raises(ValueError,match='nonfinite|overflow'):
            checks.adjudicate_record(record,3)


def test_physical_wrench_scale_is_fixed_for_large_resultants():
    left=np.array((1e12,1e12,1e12))
    right=left+1
    assert checks._scaled_error(left,right,checks.WRENCH_SCALE)==1e-6


def test_functional_parent_and_pose_binding_detects_damage(raw):
    n=3;m=n*n-1;q=np.zeros(2*m,dtype=np.float64)
    q[1]=1e-6;q[m]=2e-6;q[m+5]=-7e-7
    arrays={'q':q,'eta':np.array((31.,-23.,17.)),
            'density_coefficients':np.zeros((n+1,3)),
            'atoms':np.zeros((2,3)),'edge_route1':np.zeros((2,3))}
    pose=exact.to_record(exact.reconstruct(n,q))
    checks.validate_saved_binding(raw,n,arrays,pose)
    record=deepcopy(raw);record['functional']['density'][0][0]=['1','1']
    with pytest.raises(ValueError): checks.validate_saved_binding(record,n,arrays,pose)
    record=deepcopy(raw);record['descriptive_parent']['old_reactions'][0][0]=1.
    with pytest.raises(ValueError): checks.validate_saved_binding(record,n,arrays,pose)
    record=deepcopy(raw);record['descriptive_parent']['atom_difference'][0][0]+=1.
    with pytest.raises(ValueError): checks.validate_saved_binding(record,n,arrays,pose)
