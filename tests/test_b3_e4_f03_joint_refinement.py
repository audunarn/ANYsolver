"""Independent arithmetic and evidence checks; no registered case execution."""

from pathlib import Path
import math
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_joint_refinement as runner
import _b3_e4_f03_joint_refinement_checks as checks
import _b3_e4_f03_joint_refinement_observables as obs


def functional(n,density=0.,atoms=None):
    return {'physical_line_coefficients':np.full((n+1,3),density),
            'endpoint_atoms':np.zeros((2,3)) if atoms is None else np.asarray(atoms)}


def test_constant_and_affine_density_are_exactly_same_functional_after_embedding():
    for field in ('constant','affine'):
        a=functional(4); b=functional(8)
        for n,row in ((4,a),(8,b)):
            x=np.linspace(0.,1.,n+1)
            row['physical_line_coefficients'][:,0]=2. if field=='constant' else 1+3*x
        got=checks.functional_difference(a,b)
        assert got['difference_N']==0.
        if field=='constant':
            assert got['first_norm_N']==pytest.approx(2.,rel=1e-12)


def test_endpoint_green_cross_term_and_no_second_yaw_scaling():
    atoms=np.array([[0.,0.,2.],[0.,0.,-1.]])
    a=functional(4,atoms=atoms); b=functional(8)
    expected=math.sqrt(5/math.tanh(1)-4/math.sinh(1))
    got=checks.functional_difference(a,b)
    assert got['difference_N']==pytest.approx(expected,rel=1e-12)
    assert checks.functional_difference(a,functional(8,atoms=atoms))['difference_N']==0.


def test_line_atom_cancellation_is_included():
    a=functional(4)
    a['physical_line_coefficients'][:,0]=1.
    a['endpoint_atoms'][0,0]=-1.
    got=checks.functional_difference(a,functional(8))
    assert got['difference_N']**2==pytest.approx(1/math.tanh(1)-1,rel=1e-12)


def test_functional_negative_quadratic_is_not_repaired(monkeypatch):
    import _b3_e4_f03_trace_dual_exact as exact
    monkeypatch.setattr(exact,'dual_gram',lambda n,f:-np.eye(n+3))
    with pytest.raises(ValueError,match='quadratic'):
        checks.functional_difference(functional(4,1.),functional(8))


def test_band_force_and_moment_integrals_and_atoms():
    density=np.tile([2.,3.,4.],(5,1))
    atoms=np.array([[10.,20.,30.],[40.,50.,60.]])
    bands=obs.fixed_bands(density,atoms)
    for index,(a,b) in enumerate(obs.BANDS):
        expected=np.array([2*(b-a),3*(b-a),1.5*(b*b-a*a)+.46*4*(b-a)])
        np.testing.assert_allclose(bands[index]['line_wrench'],expected,rtol=1e-14)
        if a==0:
            expected+=atoms[0]*[1,1,.46]
        if b==1:
            expected+=atoms[1]*[1,1,.46]+[0,0,50]
        np.testing.assert_allclose(bands[index]['total_wrench'],expected,rtol=1e-14)


def test_rms_gap_is_actual_motion_normalized(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(obs.line,'overlay',lambda *a:np.array([0.,.4,1.]))
    monkeypatch.setattr(obs.beam,'trace',lambda *a:np.eye(3))
    monkeypatch.setattr(obs.port,'pose',lambda *a:np.eye(3))
    got=obs.gap_metrics(SimpleNamespace(dof_count=3),4,4,np.array([1.,2.,3.,2.,4.,6.]))
    expected=np.array([1.,2.,.46*3])
    np.testing.assert_allclose(got['gap_channel_rms_m'],expected,rtol=1e-14)
    assert got['gap_rms_m']==pytest.approx(np.linalg.norm(expected),rel=1e-14)
    assert got['motion_rms_m']==pytest.approx(math.sqrt(2.5)*np.linalg.norm(expected),rel=1e-14)


def test_inventory_reuses_middle_and_does_not_drop_baseline_family():
    assert len(runner.CASES)==6
    assert len(runner.PARENT_STATES)==2
    assert set(runner.PARENT_STATES)=={'q4_middle','cst_cb_middle'}
    assert runner.FAMILIES==('P1','hybrid','enriched')
    assert {v[1:] for v in runner.CASES.values()}=={(4,8,8,4),(8,16,16,8),(16,32,32,16)}


def test_saved_parent_change_never_falls_back_to_new_solve(monkeypatch):
    monkeypatch.setattr(runner,'parent_states',lambda name:{'q':np.array([1.])})
    with pytest.raises(ValueError,match='altered'):
        runner.parent_parity('q4_middle',{'q':np.array([2.])})


def test_premature_adjudication_keeps_canonical_output_unconsumed(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'prerequisites',lambda:None)
    monkeypatch.setattr(runner.common,'_registered',lambda root:{'cases':{'missing':{}}})
    with pytest.raises(ValueError,match='complete supervisor inventory'):
        runner.adjudicate(tmp_path)
    assert not (tmp_path/'adjudication.json').exists()


def test_scientific_status_precedence_and_unresolved_exit(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'prerequisites',lambda:None)
    cases={'a':{},'b':{}}
    monkeypatch.setattr(runner.common,'_registered',lambda root:{'cases':cases,'identity':{}})
    monkeypatch.setattr(runner.common,'_registration_hash',lambda root:'hash')
    for name in cases:
        (tmp_path/name).mkdir()
        (tmp_path/name/'supervision.json').write_text('{}')
    monkeypatch.setattr(runner,'verify_case',lambda root,name,*args:
        ({'status':'FAILED_EXECUTION'},None) if name=='a' else
        ({'status':'FAILED_NUMERICAL_SCREEN'},None))
    assert runner.adjudicate(tmp_path) is False
    assert runner.read(tmp_path/'adjudication.json')['status']=='FAILED_EXECUTION'


def test_cross_family_screen_does_not_compare_atom_decomposition():
    assert checks.screened_channel('endpoint_atoms/0/1')
    assert not checks.common_channel('endpoint_atoms/0/1')
    assert checks.common_channel('support_wrenches/2/2')
    assert checks.common_channel('fixed_bands/0/total_wrench/2')
    assert not checks.common_channel('root_line_wrench/2')


def synthetic(n):
    from copy import deepcopy
    base={'tip_pose_m':[0.,0.,0.],
          'support_wrenches':[[0.,-1e6,-.5e6],[0.,0.,0.],[0.,0.,0.]],
          'line_quarter_wrenches':np.zeros((4,3)).tolist(),
          'physical_quarter_wrenches':np.zeros((4,3)).tolist(),
          'endpoint_atoms':np.zeros((2,3)).tolist(),
          'endpoint_gaps_m':np.zeros((2,3)).tolist(),
          'physical_line_coefficients':np.zeros((n+1,3)).tolist(),
          'shell_energy_j':0.,'beam_energy_j':0.,'external_work_j':0.,'interface_work_j':0.,
          'gap_l2_m':0.,'gap_rms_m':0.,'motion_rms_m':0.,
          'gap_channel_rms_m':[0.,0.,0.],'motion_channel_rms_m':[0.,0.,0.],
          'combined_dual_norm_N':0.,'balance_scaled':[0.,0.,0.],
          'free_residual_scaled':0.,'weak_gap_scaled':0.,'energy_scaled':0.}
    for key in ('root_elastic_wrench','root_port_wrench','root_load_wrench',
                'root_line_wrench','root_endpoint_wrench'):
        base[key]=[0.,0.,0.]
    base['fixed_bands']=obs.fixed_bands(base['physical_line_coefficients'],base['endpoint_atoms'])
    families={}
    for family in runner.FAMILIES:
        row=deepcopy(base)
        row['stability']={'norm_source':'analytic_h1','norm_identity':{'test':family},
            'auxiliary_status':'PIECEWISE_ANALYTIC_FLOATING',
            'structural_solve_relative_residual':0.,'minimum_beta_diagnostic':1.,
            'generalized_eigenvalues':[1.]*(3*(n+(3 if family=='enriched' else 1)))}
        families[family]=row
    return {'topology':'Q4','mesh':[n,2*n,2*n,n],'halfwidth_m':.05,
            'families':families,'enriched_energy_order_scaled':0.,
            'parent_state_parity_ratio':0.,'parent_observable_parity_ratio':0.}


@pytest.mark.parametrize('mutation',('none','energy','balance','norm','rms','band','spectrum'))
def test_aggregate_adjudication_cannot_hide_contradictory_metrics(mutation):
    data=synthetic(4); row=data['families']['hybrid']
    spec={'topology':'Q4','n_s':4,'n_y':8,'n_beam':8,'n_mortar':4}
    identities={f:{'test':f} for f in runner.FAMILIES}
    if mutation=='energy':row['external_work_j']=1.
    if mutation=='balance':row['support_wrenches'][0][1]+=1.
    if mutation=='norm':row['stability']['auxiliary_squared_norm_change']=0.
    if mutation=='rms':row['gap_rms_m']=1.
    if mutation=='band':row['fixed_bands'][0]['total_wrench'][1]=1.
    if mutation=='spectrum':row['stability']['minimum_beta_diagnostic']=2.
    if mutation=='none':
        assert all(v==0 for v in checks.measurements(data,spec,identities).values())
    else:
        with pytest.raises(ValueError):checks.measurements(data,spec,identities)


def test_trend_decision_includes_gaps_bands_and_family_agreement():
    cases={f'{prefix}_{level}':synthetic(n) for prefix in ('q4','cst_cb')
           for level,n in (('coarse',4),('middle',8),('fine',16))}
    assert checks.refinement_summary(cases)['status']=='PASSED_BOUNDED_TREND_SCREEN'
    row=cases['q4_fine']['families']['P1']
    row['gap_rms_m']=1e-5
    report=checks.refinement_summary(cases)
    assert report['status']=='UNRESOLVED_JOINT_REFINEMENT'
    assert report['q4/P1']['physical_trend_screen']['gaps']['rms_below_one_percent_motion'] is False
    row['gap_rms_m']=0.
    row['fixed_bands'][0]['total_wrench'][1]=100.
    report=checks.refinement_summary(cases)
    assert not report['cross_family/q4']['P1/hybrid']['common_screen_passed']
    assert report['status']=='UNRESOLVED_JOINT_REFINEMENT'


def test_run_once_preserves_failed_case_without_retry_and_consumes_root(tmp_path,monkeypatch):
    root=tmp_path/'evidence'
    monkeypatch.setattr(runner,'CASES',{'a':(), 'b':()})
    monkeypatch.setattr(runner.common,'register',lambda path:path.mkdir())
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'hash')
    calls=[]
    def execute(path,name):
        calls.append(name)
        (path/name).mkdir()
        (path/name/'supervision.json').write_text('{"reason":"child_failure","failure":null}')
        return name=='b'
    monkeypatch.setattr(runner.common,'execute',execute)
    monkeypatch.setattr(runner,'adjudicate',lambda path:False)
    assert runner.run_once(root) is False
    assert calls==['a','b']
    record=runner.read(root/'orchestration.json')
    assert record['inventory_complete']
    assert record['cases'][0]['execution_completed'] is False
    with pytest.raises(FileExistsError):runner.run_once(root)
    assert calls==['a','b']


def test_cancellation_receipt_stops_before_second_scientific_launch(tmp_path,monkeypatch):
    root=tmp_path/'evidence'
    monkeypatch.setattr(runner,'CASES',{'a':(), 'b':()})
    monkeypatch.setattr(runner.common,'register',lambda path:path.mkdir())
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'hash')
    calls=[]
    def execute(path,name):
        calls.append(name)
        (path/name).mkdir()
        (path/name/'supervision.json').write_text(
            '{"reason":"supervisor_failure","failure":"KeyboardInterrupt: cancelled"}')
        return False
    monkeypatch.setattr(runner.common,'execute',execute)
    with pytest.raises(KeyboardInterrupt):runner.run_once(root)
    assert calls==['a']
    assert not runner.read(root/'orchestration.json')['inventory_complete']


def test_launch_budget_does_not_fill_missing_cases_with_fake_receipts(tmp_path,monkeypatch):
    root=tmp_path/'evidence'
    monkeypatch.setattr(runner.common,'register',lambda path:path.mkdir())
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'hash')
    times=iter((0.,2401.,2402.))
    monkeypatch.setattr(runner.time,'monotonic',lambda:next(times))
    with pytest.raises(TimeoutError):runner.run_once(root)
    record=runner.read(root/'orchestration.json')
    assert not record['inventory_complete']
    assert record['cases']==[]


@pytest.mark.parametrize('family',runner.FAMILIES)
def test_changed_recovered_coefficients_cannot_replace_saved_multipliers(family):
    from _b3_e4_f03_trace_dual_exact import dual_gram
    n=4
    row=synthetic(n)['families'][family]
    gram=np.kron(dual_gram(n,family),np.eye(3))
    lam=np.zeros(3*(n+(3 if family=='enriched' else 1)))
    checks.bind_physical_multipliers(row,family,n,lam,gram)
    row['physical_line_coefficients'][1][1]=100.
    row['fixed_bands']=obs.fixed_bands(row['physical_line_coefficients'],row['endpoint_atoms'])
    with pytest.raises(ValueError,match='saved physical multipliers'):
        checks.bind_physical_multipliers(row,family,n,lam,gram)
