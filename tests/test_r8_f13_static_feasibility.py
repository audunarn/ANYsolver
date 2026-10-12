"""One prospectively frozen installed F13 suite; no fixture is imported from history."""
import json,os,traceback
from pathlib import Path
import pytest
from scripts.r8_f13_static_feasibility import DOC,runtime,run_case,GROUPS,write,selected_node_action_parity

@pytest.fixture(scope='session')
def context():
    version=os.environ.get('F13_REGISTRATION_VERSION')
    if version is None:
        pytest.skip('registered F13 runtime marker (F13_REGISTRATION_VERSION) is absent '
                    'in ordinary portable CI; supplied malformed versions still fail')
    if version not in ('v1','v2','v3'):raise ValueError('explicit registered version required')
    registration=json.loads((DOC/('registration-'+version+'.json')).read_text())
    return runtime(registration)

@pytest.mark.parametrize('domain',('point','mixed','physical-footprint'))
@pytest.mark.parametrize('group',GROUPS)
def test_registered_consolidated_case(context,domain,group):
    output=Path(os.environ['F13_CASE_OUTPUT'])/(domain+'--'+group+'.json')
    _record_case(lambda:run_case(context,domain,group),domain+'/'+group,output)

def _record_case(operation,case_id,output):
    """Actual formal caller's failure-preserving record boundary."""
    record=dict(case_id=case_id,status='RUNNING',qualification=False)
    try:
        record['observations']=operation();record['status']='PASS'
        write(output,record)
        assert json.loads(output.read_text())==record,'actual case JSON roundtrip differs'
    except BaseException as exc:
        record.pop('observations',None)
        record.update(status='FAIL',exception=repr(exc),traceback=traceback.format_exc())
        write(output,record);raise

def test_reporting_failure_preserves_actual_caller_record(tmp_path):
    output=tmp_path/'reporting-refusal-scratch.json'
    with pytest.raises(TypeError,match='JSON serializable'):
        _record_case(lambda:dict(nonserializable=object()),'report-only/scratch',output)
    failed=json.loads(output.read_text())
    assert failed['status']=='FAIL' and failed['qualification'] is False
    assert 'observations' not in failed and 'TypeError' in failed['exception']
    assert 'JSON serializable' in failed['traceback']

def test_normalization_actual_full48_helper_keeps_quiet_channels_and_refuses_bad_references(tmp_path):
    import numpy as np
    expected=np.zeros(48);expected[0]=1.
    errors=[]
    for channel in range(1,48):
        actual=expected.copy();actual[channel]=2e-11
        value=selected_node_action_parity(np,actual,expected,1.,1.)
        assert value==pytest.approx(2e-11,rel=1e-14)
        errors.append(value)
        actual[channel]=2e-10
        with pytest.raises(AssertionError,match='parity failed'):selected_node_action_parity(np,actual,expected,1.,1.)
    opposite=expected.copy();opposite[12]=2e-10;opposite[24]=-2e-10
    assert (opposite-expected).sum()==0.
    with pytest.raises(AssertionError,match='parity failed'):selected_node_action_parity(np,opposite,expected,1.,1.)
    for bad in (np.zeros(48),np.full(48,np.nan),np.full(48,np.inf)):
        with pytest.raises(AssertionError):selected_node_action_parity(np,expected,bad,1.,1.)
    with pytest.raises(AssertionError):selected_node_action_parity(np,expected[:-1],expected,1.,1.)
    write(tmp_path/'normalization-refusal-scratch.json',dict(status='PASS',quiet_channels_retained=47,opposite_node_errors_refused=True,
        allzero_nonfinite_reference_refused=True,observed_quiet_channel_errors=errors))
