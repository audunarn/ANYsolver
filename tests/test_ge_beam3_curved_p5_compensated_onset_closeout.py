"""Static frozen-output checks; no mechanics or spectral recomputation."""

from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_compensated_onset_wave as wave


ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-compensated-onset32-20260906-70e8742b5e6a4013b68c9d44d8f2ad19')
FILES = {
    'aggregate.json':(12186,'9fe362d7d92386d58ccfa64c88561d5dd340344443ac10eb0b9d302c7cf8a22b'),
    'inputs.json':(7919,'ce4bab98fb9d98a98c18371e4c9b31da39608f5ab939157d0c66925ef29ffe60'),
    'elements-32/complete.json':(13336,'e612ab9daff1ef7be46dbb394e6a8a6b4ce75c0c11e7e15ca790caa0d3809533'),
    'elements-32/process-start.json':(385,'7ebd437b150fdff8ce198d636cc14c1472dfe62f78290d282e47da70175a7d86'),
    'elements-32/process.json':(100,'d69306790f854cd369a8d5e173dfe16341318ca3bff579e00a7025e3984bb183'),
    'elements-32/progress.jsonl':(87220,'1f8dbcb7ba0c91a2c9823bd928dd423ef362fa3340401549b11d51a293207ec7'),
    'elements-32/stdout.log':(0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'elements-32/stderr.log':(0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
}


@pytest.fixture(scope='module')
def records():
    def verify(name,size,digest):
        data=wave.shared.ordinary(ROOT/name)
        assert len(data)==size and wave.shared.sha(data)==digest
    for name,(size,digest) in FILES.items(): verify(name,size,digest)
    packet=wave.shared.load(ROOT/'elements-32/complete.json')
    bindings=packet['result']['raw_bindings'];raws={}
    for name,b in bindings.items():
        assert b['name']==name+'.json'
        verify('elements-32/'+b['name'],b['bytes'],b['sha256'])
        raws[name]=wave.shared.load(ROOT/'elements-32'/b['name'])
    expected=set(FILES)|{'elements-32/'+b['name'] for b in bindings.values()}
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==expected
    assert len(expected)==27
    assert sum(s for s,_ in FILES.values())+sum(b['bytes'] for b in bindings.values())==23257908
    return packet,raws,wave.shared.load(ROOT/'aggregate.json')


def test_complete_authority_graph_preserved_without_rerun(records):
    packet,_,aggregate=records;inputs=wave.shared.load(ROOT/'inputs.json');authority=inputs['authority']
    assert inputs['case']==wave.CASE
    assert authority==packet['authority']==aggregate['authority']
    assert authority['commit']=='15ce810d1adb23d1ea20d3bab74e9d69db26f26f'
    assert authority['tree']=='7104a314c35fa20178d25bd9388b8ac8a812d0b1'
    assert wave.shared.sha(wave.shared.canonical(authority))=='d18c9d9bb487f3ce4e0101e7f337b24f9b60beec55cdcf93b347152c9460e362'
    assert authority['preserved']==wave.preserved()
    assert packet['request_id']==aggregate['request_id']=='b632bbec2d8c41f3b2f490278ef9e46b'
    assert packet['request_sha256']==aggregate['request_sha256']=='83efe3a430c1ad6d12e1d9ec5a70bd23069d1edc4f3d55b4efd929241c9bd887'
    assert aggregate['worker_sha256']==FILES['elements-32/complete.json'][1]
    assert aggregate['progress_sha256']==FILES['elements-32/progress.jsonl'][1]


def test_numerical_uncertainty_is_preserved_not_zero_or_qualification(records):
    packet,_,aggregate=records;result=packet['result'];samples=result['samples'];last=samples[-1]
    assert len(samples)==19 and len([s for s in samples if s['id'].startswith('grid-')])==13
    assert result['disposition']==aggregate['current']['disposition']=='MIDPOINT_LATERAL_SIGN_UNRESOLVED'
    assert last['sign']==0 and last['lowest']==1.1083452621194213e-8 != 0.
    assert last['uncertainty']==2.5258869382013487e-7 > abs(last['lowest'])
    assert result['bracket']['width']==0.0001562500000000036 > wave.probe.search.WIDTH
    assert aggregate['production_qualified'] is aggregate['accuracy_qualified'] is aggregate['first_critical_point_proven'] is False
    assert aggregate['historical_recomputed'] is False
    assert aggregate['restriction']=='NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'


def test_endpoint_comparisons_are_within_two_percent_only(records):
    _,_,aggregate=records
    expected=wave.compare(records[0],wave.shared.references(),wave.historical.previous())
    assert aggregate['current']==expected['current']
    assert aggregate['historical_comparisons']==expected['historical_comparisons']
    for sides in aggregate['current']['comparison']['continuum'].values():
        for side in sides.values():
            assert max(abs(v) for v in side['discrete_endpoint_relative_drop_errors'])<.02
            assert max(abs(v) for v in side['discrete_endpoint_relative_load_errors'])<.02


def test_all_accepted_states_and_resource_limits(records):
    _,raws,_=records
    assert max(r['trial']['assembly']['residual_norm'] for r in raws.values())==5.506791506773546e-12<1e-11
    assert max(r['trial']['assembly']['iterations'] for r in raws.values())==3
    assert max(r['trial']['assembly']['mixed_evaluations'] for r in raws.values())==510<8192
    assert sum(len(e['stations']) for r in raws.values() for e in r['trial']['assembly']['response']['elements'])==9728
    for r in raws.values():
        a=r['trial']['assembly']
        wave.diagnostic.check_accuracy(a['response'],32);wave.diagnostic.check_coordinates(a,32)
        assert len(a['positions'])==len(a['position_low'])==65
    process=wave.shared.load(ROOT/'elements-32/process.json')
    assert process['exit_code']==0 and 0<process['wall_seconds']==168.8295971999978<600
    assert process['cpu_100ns']==1682187500 and process['peak_tree_bytes']==220176384<24*(1<<30)
