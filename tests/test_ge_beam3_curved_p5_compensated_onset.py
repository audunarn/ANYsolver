"""Small correctness rehearsals and fail-closed mutations; no 32-element solve."""

import ast
import copy
import json
from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_compensated_onset_wave as wave
from docs.reference_cases import ge_beam3_curved_p5_compensated_onset_inspection as inspection


@pytest.fixture(scope='module')
def small():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(wave.probe.search,'DROPS',(0.,.005,.01))
        cycles = []
        for _ in range(2):
            saved = {};events = []
            def publish(label,raw):
                assert label not in saved
                data = wave.shared.canonical(raw);saved[label] = json.loads(data)
                return {'name':label+'.json','bytes':len(data),'sha256':wave.shared.sha(data)}
            result = wave.probe.records(count=2,progress=lambda *row:events.append(row),publish_raw=publish)
            cycles.append((result,saved,events))
        assert wave.shared.canonical(cycles[0]) == wave.shared.canonical(cycles[1])
        return cycles[0]


def test_small_complete_coordinate_aware_path_and_inspection(small,tmp_path,monkeypatch):
    monkeypatch.setattr(wave.probe.search,'DROPS',(0.,.005,.01))
    result,saved,events = small
    assert len(saved) == 3 and result['schema'] == wave.probe.SCHEMA
    assert result['production_qualified'] is result['first_critical_point_proven'] is False
    assert events[0] == ('INITIALIZATION',None) and events[-1] == ('PROBE_COMPLETE',None)
    assert any(e[0]=='CONTROL' for e in events)
    for name,raw in saved.items(): wave.shared.publish(tmp_path/(name+'.json'),raw)
    write_progress(tmp_path,events)
    packet = {'schema':wave.SCHEMA,'authority':{},'request_id':'a'*32,'request_sha256':'b'*64,'result':result}
    wave.shared.publish(tmp_path/'complete.json',packet)
    assert inspection.inspect_worker(tmp_path,2,{},'a'*32,'b'*64,schema=wave.SCHEMA) == packet
    assert saved['grid-01']['origin_checkpoint_sha256'] == saved['grid-00']['checkpoint_sha256']
    assert saved['grid-00']['origin_checkpoint_sha256'] == inspection.initial_hash(2)
    assert saved['grid-01']['trial']['assembly']['coordinate_schema'] == wave.diagnostic.COORDINATES


@pytest.mark.parametrize('mutation',['schema','low_missing','low_type','normalization','element_low','fixed_low',
    'target_low','policy','station','origin_history','plastic_history','tangent','residual','spectrum',
    'error','target','count','iterations','budget','checkpoint','state_hash','extra'])
def test_raw_mutations_rejected_even_if_container_is_rehashed(small,mutation):
    result,saved,_ = small;raw = copy.deepcopy(saved['grid-01']);a = raw['trial']['assembly'];e = a['response']['elements'][0]
    if mutation=='schema': a['coordinate_schema']='old'
    if mutation=='low_missing': a.pop('position_low')
    if mutation=='low_type': a['position_low'][1][0]=0
    if mutation=='normalization': a['position_low'][1][0]=1.
    if mutation=='element_low': e['position_low'][0][0]=1e-30
    if mutation=='fixed_low': a['position_low'][0][0]=1e-30
    if mutation=='target_low': a['position_low'][2][1]=1e-30
    if mutation=='policy': e['force_accuracy']['limit']*=2
    if mutation=='station': e['stations'].pop()
    if mutation=='origin_history': a['origins'][0][0]['accumulated']=.01
    if mutation=='plastic_history': e['stations'][0]['response']['plastic_active']=True
    if mutation=='tangent': a['response']['tangent'][6][6]+=1.
    if mutation=='residual': a['response']['residual'][6]+=1.
    if mutation=='spectrum': raw['spectra']['out_of_plane']['values'][0]+=1.
    if mutation=='error': raw['state_errors']['equilibrium']=0.
    if mutation=='target': raw['trial']['target']=.09
    if mutation=='count': raw['elements']=True
    if mutation=='iterations': a['iterations']=True
    if mutation=='budget': a['mixed_evaluations']=513
    if mutation=='checkpoint': raw['trial']['checkpoints'][-1]['reaction']=1.
    if mutation=='state_hash': raw['checkpoint_sha256']='a'*64
    if mutation=='extra': a['legacy_high_only']=True
    with pytest.raises((ValueError,KeyError)):
        inspection.check_raw(raw,result['samples'][1],2)


@pytest.mark.parametrize('mutation',['hash','origin','epoch','terminal','extra_file','progress'])
def test_rehashed_origin_and_adjudication_mutations(small,tmp_path,mutation,monkeypatch):
    monkeypatch.setattr(wave.probe.search,'DROPS',(0.,.005,.01))
    result,saved,events = copy.deepcopy(small)
    write_progress(tmp_path,events[:-1] if mutation=='progress' else events)
    if mutation=='origin': saved['grid-01']['origin_checkpoint_sha256']='c'*64
    if mutation=='epoch': saved['grid-01']['trial']['origin_epoch']=0
    if mutation=='terminal': result['production_qualified']=True
    for name,raw in saved.items(): result['raw_bindings'][name]=wave.shared.publish(tmp_path/(name+'.json'),raw)
    if mutation=='hash': result['raw_bindings']['grid-01']['sha256']='b'*64
    if mutation=='extra_file': wave.shared.publish(tmp_path/'extra.json',{})
    wave.shared.publish(tmp_path/'complete.json',{'schema':wave.SCHEMA,'authority':{},'request_id':'a'*32,
        'request_sha256':'b'*64,'result':result})
    with pytest.raises(ValueError): inspection.inspect_worker(tmp_path,2,{},'a'*32,'b'*64,schema=wave.SCHEMA)


def write_progress(folder,events):
    rows = [{'phase':e[0],'id':e[1],'event':e[2] if len(e)==3 else None} for e in events]
    rows.append({'phase':'COMPLETION','id':None,'event':None})
    (folder/'progress.jsonl').write_bytes(b''.join(wave.shared.canonical(r) for r in rows))


@pytest.mark.parametrize('guard',['authority','lease'])
def test_guards_precede_numerics(monkeypatch,tmp_path,guard):
    def denied(*args): raise ValueError('denied')
    monkeypatch.setattr(wave,'authority',denied if guard=='authority' else lambda *a:{})
    monkeypatch.setattr(wave,'lease',denied)
    monkeypatch.setattr(wave.probe,'records',lambda **kw:pytest.fail('early mechanics'))
    with pytest.raises(ValueError,match='denied'): wave.worker(tmp_path,'a'*40,tmp_path)


@pytest.mark.parametrize('mutation',['dirty','head','parent','paths','sibling','environment','preserved'])
def test_freeze_mutations(monkeypatch,tmp_path,mutation):
    def git(repo,*args):
        if args[0]=='status': return 'dirty' if mutation=='dirty' else ''
        if args==('rev-parse','HEAD'):
            if repo==wave.shared.SIBLING: return 'wrong' if mutation=='sibling' else wave.shared.SIBLING_COMMIT
            return 'wrong' if mutation=='head' else 'a'*40
        if args==('rev-parse','HEAD^'): return 'wrong' if mutation=='parent' else wave.BASE
        if args[0]=='diff': return '\n'.join(wave.ALLOWED | ({'src/unsafe.py'} if mutation=='paths' else set()))
        if args==('rev-parse','HEAD^{tree}'): return wave.shared.SIBLING_TREE
        raise AssertionError(args)
    monkeypatch.setattr(wave.shared,'git',git);monkeypatch.setattr(wave.shared,'environment',lambda:{})
    monkeypatch.setattr(wave.shared,'ENVIRONMENT_SHA','wrong' if mutation=='environment' else wave.shared.sha(wave.shared.canonical({})))
    def preserved():
        if mutation=='preserved': raise ValueError('changed history')
        return {}
    monkeypatch.setattr(wave,'preserved',preserved)
    with pytest.raises(ValueError): wave.authority(tmp_path,'a'*40)


def manager_fixture(tmp_path,request_id='b'*32):
    manager=tmp_path/'manager';(manager/'requests').mkdir(parents=True);(manager/'active-lock').mkdir();(manager/'claims').mkdir()
    repo=tmp_path/'repo';repo.mkdir();output=tmp_path/'output'
    data={'request_id':request_id,'repository':str(repo),'command':wave.command(repo,'a'*40,output)}
    wave.shared.publish(manager/'requests'/(request_id+'.json'),data);wave.shared.publish(manager/'active-lock/owner.json',data)
    (manager/'ledger.md').write_text(f'| now | {request_id} | APPROVED | test |\n')
    return manager,repo,output


@pytest.mark.parametrize('request_id',wave.CONSUMED)
def test_consumed_ids_never_reused(tmp_path,request_id):
    manager,repo,output=manager_fixture(tmp_path,request_id)
    with pytest.raises(ValueError): wave.lease(repo,'a'*40,output,manager=manager)


def test_exact_lease_and_cross_namespace_consumption(tmp_path):
    manager,repo,output=manager_fixture(tmp_path)
    assert wave.lease(repo,'a'*40,output,manager=manager)[0]=='b'*32
    with pytest.raises(ValueError): wave.lease(repo,'a'*40,output/'different',manager=manager)
    (manager/'claims'/('other-'+'b'*32)).mkdir()
    with pytest.raises(ValueError): wave.lease(repo,'a'*40,output,manager=manager)


@pytest.mark.parametrize('failure',['exit','timeout','memory','inspection'])
def test_failure_no_retry_or_aggregate(monkeypatch,tmp_path,failure):
    manager,repo,output=manager_fixture(tmp_path);calls=[]
    monkeypatch.setattr(wave,'MANAGER',manager);monkeypatch.setattr(wave,'authority',lambda *a:{})
    monkeypatch.setattr(wave,'lease',lambda *a:('b'*32,'c'*64))
    def child(line,folder,*args,**kwargs):
        calls.append(line)
        assert kwargs=={'timeout':600.,'inactivity':300.,'memory':24*(1<<30)}
        (folder/'partial.log').write_text('preserved')
        if failure in ('timeout','memory'): raise ValueError(failure)
        return {'exit_code':0 if failure=='inspection' else 1}
    def reject(*args,**kwargs): raise ValueError('malformed packet')
    monkeypatch.setattr(wave.shared,'run_child',child);monkeypatch.setattr(wave,'inspect_worker',reject)
    with pytest.raises(ValueError): wave.coordinate(repo,'a'*40,output)
    assert len(calls)==1 and not (output/'aggregate.json').exists()
    assert (output/'blocked-diagnostic.json').exists() and (output/'elements-32/partial.log').read_text()=='preserved'
    with pytest.raises(FileExistsError): wave.coordinate(repo,'a'*40,tmp_path/'again')


def test_preserved_inputs_and_exact_scope():
    bound=wave.preserved()
    assert len(bound['compensated_comparison'])==10 and bound['onset_4_8_16']['bytes']==5160
    assert wave.CASE['meshes']==[32] and wave.CASE['maximum_states']==29
    assert wave.CASE['physical_limit']==1e-11 and wave.CASE['total_local_force_budget']==1e-12
    assert wave.CASE['drops']==list(wave.probe.search.DROPS) and wave.CASE['bracket_width']==1e-7
    assert wave.CASE['child_seconds']==600 and wave.CASE['wave_seconds']==890
    assert len(wave.ALLOWED)==5 and all(p.startswith(('docs/','tests/')) for p in wave.ALLOWED)


def test_no_top_level_numerics_or_old_executor_invocations():
    for module in (wave,wave.probe,inspection):
        tree=ast.parse(Path(module.__file__).read_text())
        top=[ast.unparse(n) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        assert not any('numpy' in t or 'scipy' in t or 'arch_refinement_case' in t for t in top)
    text=Path(wave.__file__).read_text()
    assert 'historical.worker(' not in text and 'historical.coordinate(' not in text
    assert 'diagnostic.capture(' not in text


def test_failed_trial_retains_only_uncommitted_last_evaluation(monkeypatch):
    from docs.reference_cases.ge_beam3_curved_p5_compensated_control import CompensatedDisplacementControlledAssemblyProbe as Control
    from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import DisplacementControlError
    original=Control.trial;saved={}
    def trial(self,target,**kwargs):
        if target != .1: kwargs['max_iterations']=0
        return original(self,target,**kwargs)
    monkeypatch.setattr(Control,'trial',trial)
    def publish(label,raw):
        saved[label]=json.loads(wave.shared.canonical(raw))
        return {'name':label+'.json','bytes':1,'sha256':'a'*64}
    with pytest.raises(DisplacementControlError):
        wave.probe.records(count=2,progress=lambda *a:None,publish_raw=publish)
    assert set(saved)=={'grid-00','grid-01-failed-last'}
    failed=saved['grid-01-failed-last']
    assert failed['disposition']=='UNCOMMITTED_DIAGNOSTIC_ONLY' and failed['replay_verified'] is True
    assert failed['origin_checkpoint_sha256']==saved['grid-00']['checkpoint_sha256']
    assert failed['coordinate_schema']==wave.diagnostic.COORDINATES


def test_comparison_cannot_qualify_or_rewrite_history():
    result=wave.probe.locate(lambda label,drop,origin:{'drop':drop,'load':.03,'lowest':.04612345-drop,
        'uncertainty':1e-12,'negative':int(drop>.04612345),'unresolved':0})
    result['elements']=32
    old=wave.historical.previous();before=wave.shared.canonical(old)
    compared=wave.compare({'result':result},wave.shared.references(),old)
    assert wave.shared.canonical(old)==before
    assert compared['production_qualified'] is compared['accuracy_qualified'] is compared['historical_recomputed'] is False
    assert compared['historical_comparisons']==old['comparisons']
    assert compared['schema']==wave.SCHEMA
