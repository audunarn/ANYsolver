"""Independent polynomial checks for saved-state multiplier postprocessing."""

from pathlib import Path
import copy
import json
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_area_axis_report as report


@pytest.mark.parametrize('left,right',((0.,1.),(.031,.819),(0.,1/32)))
def test_p1_subband_force_and_origin_moment_against_polynomial_integral(left,right):
    n=8
    nodes=np.linspace(0.,1.,n+1)
    lam=np.column_stack((2+3*nodes,-4+5*nodes,6-7*nodes)).ravel()
    h=right-left
    s2=(right**2-left**2)/2
    s3=(right**3-left**3)/3
    expected=(2*h+3*s2,-4*h+5*s2,
              -4*s2+5*s3+report.original.YAW_LENGTH*(6*h-7*s2))
    np.testing.assert_allclose(report.multiplier_wrench(lam,n,left,right),
                               expected,rtol=2e-14,atol=2e-15)


@pytest.mark.parametrize('n_mortar,n_beam',((2,8),(8,2),(8,16)))
def test_hermite_root_weight_against_exact_linear_density_moments(n_mortar,n_beam):
    lam=np.zeros((n_mortar+1,3))
    lam[:,1]=-3+5*np.linspace(0.,1.,n_mortar+1)
    h=1/n_beam
    assert report.root_port_force(lam.ravel(),n_mortar,n_beam)==pytest.approx(
        -3*h/2+5*3*h*h/20,rel=2e-14,abs=2e-15)


def test_invalid_multiplier_field_rejected():
    with pytest.raises(ValueError):
        report.multiplier_wrench(np.zeros(5),2,0.,.2)
    with pytest.raises(ValueError):
        report.root_port_force(np.zeros(9),2,0)


def test_adjudication_must_bind_source_and_complete_passed_inventory():
    registration={'identity':{'head':'candidate'},'cases':{'case':{}}}
    accepted={'identity':{'head':'candidate'},
              'cases':{'case':{'status':'PASSED_ALGEBRAIC_SCREEN'}}}
    report._validate_adjudication(registration,accepted)
    for changed in (
            {**accepted,'identity':{'head':'other'}},
            {**accepted,'cases':{}},
            {**accepted,'cases':{'case':{'status':'FAILED'}}}):
        with pytest.raises(ValueError,match='accepted algebraic'):
            report._validate_adjudication(registration,changed)


@pytest.fixture
def accepted_receipt(tmp_path):
    (tmp_path/'observables.json').write_text('{"result":1}',encoding='utf-8')
    (tmp_path/'solved_state.npz').write_bytes(b'snapshot receipt fixture')
    observed=report._sha(tmp_path/'observables.json')
    state=report._sha(tmp_path/'solved_state.npz')
    registration={'identity':{'head':'candidate'},
                  'limits':{'seconds_per_case':10,'rss_bytes_per_case':1000},
                  'parity_reference':{'case':observed}}
    events=[{'phase':'identity','case':'case','identity':registration['identity'],
             'registration_sha256':'registration',
             'threadpools':[{'num_threads':1}]},
            {'phase':'observables','case':'case','sha256':observed,
             'state_sha256':state}]
    receipt={'reason':'completed','exit_code':0,'failure':None,
             'registration_sha256':'registration','phases':['identity','observables'],
             'observables_sha256':observed,'elapsed_seconds':2.,
             'sampled_peak_rss_bytes':500}

    def write(current_events=events,current_receipt=receipt):
        (tmp_path/'stdout.jsonl').write_text(
            '\n'.join(json.dumps(e) for e in current_events),encoding='utf-8')
        (tmp_path/'supervision.json').write_text(
            json.dumps(current_receipt),encoding='utf-8')

    write()
    return tmp_path,registration,events,receipt,write


def test_complete_receipt_and_matching_frozen_baseline_are_accepted(accepted_receipt):
    directory,registration,_,_,_=accepted_receipt
    report._validate_receipt(directory,'case',registration,'registration')


@pytest.mark.parametrize('key,value',(
    ('reason','timeout'),('exit_code',1),('failure','backend error'),
    ('registration_sha256','other'),('phases',['identity']),
    ('observables_sha256','other'),('elapsed_seconds',11.),
    ('elapsed_seconds',float('nan')),('sampled_peak_rss_bytes',1001)))
def test_failed_or_inconsistent_supervisor_receipt_is_rejected(accepted_receipt,key,value):
    directory,registration,events,receipt,write=accepted_receipt
    write(events,{**receipt,key:value})
    with pytest.raises(ValueError,match='supervision receipt'):
        report._validate_receipt(directory,'case',registration,'registration')


@pytest.mark.parametrize('mutation',('source','threads','state','malformed'))
def test_unbound_child_events_are_rejected(accepted_receipt,mutation):
    directory,registration,events,receipt,write=accepted_receipt
    changed=copy.deepcopy(events)
    if mutation=='source':
        changed[0]['identity']={'head':'other'}
    elif mutation=='threads':
        changed[0]['threadpools'][0]['num_threads']=2
    elif mutation=='state':
        changed[1]['state_sha256']='other'
    else:
        changed[0]=[]
    write(changed,receipt)
    with pytest.raises(ValueError,match='identity mismatch'):
        report._validate_receipt(directory,'case',registration,'registration')


def test_changed_baseline_observable_is_rejected(accepted_receipt):
    directory,registration,_,_,_=accepted_receipt
    registration['parity_reference']['case']='different frozen result'
    with pytest.raises(ValueError,match='baseline parity mismatch'):
        report._validate_receipt(directory,'case',registration,'registration')
