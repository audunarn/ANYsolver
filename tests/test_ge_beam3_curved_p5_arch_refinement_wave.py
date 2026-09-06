"""Small correctness and synthetic integrity fixtures; no 16-element solve."""

import ast
import builtins
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_refinement_case as case
from docs.reference_cases import ge_beam3_curved_p5_arch_refinement_wave as wave
from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe


def test_geometry_identity_and_explicit_refinement_extent():
    for count in (2,4,8):
        for old,new in zip(parabolic_references(.1,count),case.references(count)):
            assert np.array_equal(old.coordinates,new.coordinates)
            assert np.array_equal(old.nodal_triads,new.nodal_triads)
    beam,pattern = case.make_beam(16)  # Construction only, no response/solve.
    assert beam.committed.positions.shape==(33,3)
    assert np.count_nonzero(pattern)==1 and pattern[16,1]==-1
    assert sum(map(len,beam.committed.histories))==256
    with pytest.raises(ValueError,match='bounded'):
        NonlinearAssemblyHistoryProbe(beam._references,beam._maps,beam._sections)
    for count in (True,1,3,32):
        with pytest.raises(ValueError): case.references(count)


@pytest.fixture(scope='module')
def small_packet():
    packets,progress = [],[]
    def raw(i,value):
        packets.append(json.loads(wave.canonical(value)))
        return {'name':f'step-{i:02}.json','bytes':1,'sha256':'0'*64}
    rows = case.records(count=2,steps=1,progress=lambda *a:progress.append(a),publish_raw=raw)
    return packets[0],rows[0],progress


def test_small_physical_recovery_and_station_work(small_packet):
    full,row,progress = small_packet
    wave.check_samples(full,row,count=32)
    assert row['stations']==32 and row['stationary_work_error']<1e-11
    assert row['global_balance_error']<1e-11 and row['reference_interpolation_error']<1e-6
    assert row['recovery_energy_norm_error']>.02  # Coarse failure stays visible.
    assert progress==[('STEP_START',0),('STEP_COMPLETE',0)]
    expected = np.array(full['samples']['reference_resultants'])
    assert np.allclose(expected[:,[0,4]],expected[::-1,[0,4]],rtol=0,atol=1e-12)
    assert np.allclose(expected[:,2],-expected[::-1,2],rtol=0,atol=1e-12)


@pytest.mark.parametrize('mutation',['recovery','energy','station','reference','measure','coarser'])
def test_small_rehashed_metric_mutations(small_packet,mutation):
    full,row,_ = copy.deepcopy(small_packet)
    if mutation=='recovery': row['recovery_energy_norm_error']=0.
    if mutation=='energy': full['samples']['physical_energy']+=.01
    if mutation=='station': full['trial']['assembly_trial']['response']['elements'][0]['stations'][0]['response']['strain'][0]+=.01
    if mutation=='reference': full['samples']['reference_resultants'][0][0]+=10
    if mutation=='measure': full['samples']['measures'][0]=-1.
    if mutation=='coarser': full['samples']['coarser_reference_resultants'][0][0]+=10
    with pytest.raises(wave.RefinementError): wave.check_samples(full,row,count=32)


def make_lease(tmp_path):
    manager=tmp_path/'manager';manager.mkdir()
    (manager/'requests').mkdir();(manager/'active-lock').mkdir()
    repo=tmp_path/'repo';repo.mkdir()
    output=tmp_path/'output';commit='a'*40;request_id='b'*32
    record={'request_id':request_id,'repository':str(repo),'command':wave.command(repo,commit,output)}
    wave.publish(manager/'requests'/(request_id+'.json'),record)
    wave.publish(manager/'active-lock'/'owner.json',record)
    (manager/'ledger.md').write_text(f'| date | {request_id} | APPROVED | unit |\n',encoding='utf-8')
    return manager,repo,output,commit,request_id


def test_exact_lease_and_consumed_id(tmp_path):
    manager,repo,output,commit,request_id=make_lease(tmp_path)
    assert wave.lease(repo,commit,output,manager=manager)[0]==request_id
    with pytest.raises(wave.RefinementError,match='mismatch'):
        wave.lease(repo,commit,tmp_path/'changed',manager=manager)
    with (manager/'ledger.md').open('a',encoding='utf-8') as stream:
        stream.write(f'| date | {request_id} | COMPLETED_FAIL | unit |\n')
    with pytest.raises(wave.RefinementError,match='unconsumed'):
        wave.lease(repo,commit,output,manager=manager)


def test_missing_approval(tmp_path):
    manager,repo,output,commit,_=make_lease(tmp_path)
    (manager/'ledger.md').write_text('',encoding='utf-8')
    with pytest.raises(wave.RefinementError,match='approval'):
        wave.lease(repo,commit,output,manager=manager)


@pytest.mark.parametrize('mutation',['dirty','parent','extent','head'])
def test_authority_rejection(monkeypatch,tmp_path,mutation):
    commit='a'*40
    def git(repo,*args):
        if args==('rev-parse','HEAD'): return 'b'*40 if mutation=='head' else commit
        if args[0]=='status': return ' M file' if mutation=='dirty' else ''
        if args==('rev-parse','HEAD^'): return 'b'*40 if mutation=='parent' else wave.BASE
        if args[0]=='diff': return '\n'.join(wave.ALLOWED|({'src/change.py'} if mutation=='extent' else set()))
        raise AssertionError('must reject before tree binding')
    monkeypatch.setattr(wave,'git',git)
    with pytest.raises(wave.RefinementError): wave.authority(tmp_path,commit)


def test_guards_before_numerical_import(monkeypatch,tmp_path):
    original=builtins.__import__
    def guarded(name,*args,**kwargs):
        if name.endswith('arch_refinement_case'): raise AssertionError('numerics imported before guards')
        return original(name,*args,**kwargs)
    def deny(*args): raise wave.RefinementError('denied')
    monkeypatch.setattr(builtins,'__import__',guarded)
    monkeypatch.setattr(wave,'authority',deny)
    with pytest.raises(wave.RefinementError,match='denied'): wave.worker(tmp_path,'a'*40,tmp_path)
    monkeypatch.setattr(wave,'authority',lambda *args:{})
    monkeypatch.setattr(wave,'lease',deny)
    with pytest.raises(wave.RefinementError,match='denied'): wave.worker(tmp_path,'a'*40,tmp_path)
    tree=ast.parse(Path(wave.__file__).read_text())
    imports=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert not any('numpy' in ast.unparse(n) or 'scipy' in ast.unparse(n) or 'arch_refinement_case' in ast.unparse(n) for n in imports)


def synthetic_packet(tmp_path):
    """Explicitly synthetic zero-error data for schema checks, not mechanics."""
    folder=tmp_path/'arch16';folder.mkdir();rows=[]
    for i in range(8):
        row={'step':i,'crown_drop':.1,'load':1.,'reference_load':1.,'relative_load_error':0.,
             'current_load_slope':1. if i==0 else -1.,'minimum_free_eigenvalue':-.1,
             'equilibrium_error':0.,'arc_error':0.,'iterations':1,'mixed_evaluations':16,
             'recovery_energy_norm_error':0.,'physical_energy_relative_error':0.,'stationary_work_error':0.,
             'reference_interpolation_error':0.,'global_balance_error':0.,'stations':256}
        actual=[[1.,0.,0.,0.,0.,0.] for _ in range(256)]
        strains=[[.001,0.,0.,0.,0.,0.] for _ in range(256)]
        forces=[[0.,0.,0.] for _ in range(33)];forces[16][1]=-1.
        stations=[{'response':{'resultants':a,'strain':b}} for a,b in zip(actual,strains)]
        assembly={'positions':[[0.,0.,0.] for _ in range(33)],'forces':forces,'residual_norm':0.,
                  'response':{'potential':.128,'elements':[{'stations':stations[j:j+16]} for j in range(0,256,16)]}}
        raw={'trial':{'assembly_trial':assembly,'parameter':1.,'arc_residual':0.},
             'reference':{'load':1.,'displacement':.1,'profile':'BVP9','strain_energy':.128},
             'samples':{'parameters':[0.]*256,'measures':[1.]*256,'reference_resultants':actual,
                        'coarser_reference_resultants':actual,'actual_resultants':actual,'actual_strains':strains,
                        'physical_energy':.128},'comparison':row}
        rows.append(dict(row,raw=wave.publish(folder/f'step-{i:02}.json',raw)))
    packet={'schema':wave.SCHEMA,'authority':{'commit':'c'},'request_id':'b'*32,'request_sha256':'d'*64,
            'production_qualified':False,'records':rows}
    wave.publish(folder/'complete.json',packet)
    return folder,packet


@pytest.mark.parametrize('mutation',['hash','order','count','raw-force','raw-recovery','raw-energy'])
def test_complete_packet_mutations(tmp_path,mutation):
    folder,packet=synthetic_packet(tmp_path)
    def inspect(): return wave.inspect_worker(folder,{'commit':'c'},'b'*32,'d'*64)
    assert inspect()==packet
    row=packet['records'][0]
    if mutation=='hash': row['raw']['sha256']='0'*64
    if mutation=='order': row['step']=True
    if mutation=='count': row['stations']=255
    if mutation.startswith('raw-'):
        path=folder/'step-00.json';raw=wave.load(path)
        if mutation=='raw-force': raw['trial']['assembly_trial']['forces'][16][1]=0.
        if mutation=='raw-recovery': raw['comparison']['recovery_energy_norm_error']=row['recovery_energy_norm_error']=.01
        if mutation=='raw-energy': raw['samples']['physical_energy']=1.
        path.write_bytes(wave.canonical(raw))
        row['raw'].update(bytes=path.stat().st_size,sha256=wave.sha(path.read_bytes()))
    (folder/'complete.json').write_bytes(wave.canonical(packet))
    with pytest.raises(wave.RefinementError): inspect()


def test_adjudication_does_not_hide_recovery_or_qualify(tmp_path):
    _,packet=synthetic_packet(tmp_path)
    result=wave.adjudicate(packet)
    assert result['disposition']=='RESEARCH_ARCH_COMPARISONS_BELOW_2_PERCENT'
    assert result['production_qualified'] is False
    for error in wave.ERRORS:
        changed=copy.deepcopy(packet);changed['records'][-1][error]=.02
        assert wave.adjudicate(changed)['disposition']=='RESEARCH_ARCH_COMPARISONS_UNRESOLVED'
    packet['records'][-1]['current_load_slope']=1.
    assert wave.adjudicate(packet)['descending_branch_reached'] is False


def test_strict_json_and_exclusive_output(tmp_path):
    for content in (b'{"x":0,"x":1}\n',b'{"x":NaN}\n',b'{"x":1e400}\n',b' {}\n'):
        path=tmp_path/'bad.json';path.write_bytes(content)
        with pytest.raises(ValueError): wave.load(path)
    path=tmp_path/'result.json';wave.publish(path,{'value':1});original=path.read_bytes()
    with pytest.raises(FileExistsError): wave.publish(path,{'value':2})
    assert path.read_bytes()==original


@pytest.mark.parametrize('failure',['exit','timeout','memory'])
def test_process_failure_retains_claim_without_aggregate(monkeypatch,tmp_path,failure):
    manager=tmp_path/'manager';manager.mkdir();(manager/'claims').mkdir()
    repo=tmp_path/'repo';repo.mkdir();output=tmp_path/'external'
    monkeypatch.setattr(wave,'MANAGER',manager)
    monkeypatch.setattr(wave,'authority',lambda *a:{'commit':'a'*40})
    monkeypatch.setattr(wave,'lease',lambda *a:('b'*32,'d'*64))
    def fail(*args,**kwargs):
        assert kwargs=={'timeout':600.,'inactivity':300.,'memory':24*(1<<30)}
        if failure!='exit': raise wave.RefinementError(failure)
        return {'exit_code':1}
    monkeypatch.setattr(wave,'run_child',fail)
    with pytest.raises(wave.RefinementError): wave.coordinate(repo,'a'*40,output)
    assert (output/'blocked-diagnostic.json').exists() and not (output/'aggregate.json').exists()
    assert (manager/'claims'/('ge-beam3-arch-refine16-'+'b'*32)).is_dir()
    with pytest.raises(FileExistsError): wave.coordinate(repo,'a'*40,tmp_path/'other-output')
