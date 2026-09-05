"""Small profile/guard/process tests; never launch the refinement campaign."""

import copy
import json
import os
from pathlib import Path
import sys

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_refinement_wave as wave
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from test_ge_beam3_curved_p5_nonlinear_mixed_probe import law,section,A


def test_case_and_geometry_are_identical_to_existing_campaign():
    factor = np.array(wave.CASE['factor'])
    assert np.array_equal(factor.T @ factor,section())
    assert np.array_equal(wave.CASE['direction'],A)
    assert wave.CASE['schedule'] == [.1,.2,.1,0.,-.2,0.]
    for count in (1,2,4,8):
        for expected,made in zip(parabolic_references(.4,count),wave.refined_references(np,count)):
            assert np.array_equal(expected.coordinates,made.coordinates)
            assert np.array_equal(expected.nodal_triads,made.nodal_triads)


def test_explicit_refinement_extent_preserves_default_and_rejects_unbounded_sizes():
    refs = wave.refined_references(np)
    maps = [(2*i,2*i+1,2*i+2) for i in range(16)]
    sections = [law()]*16
    with pytest.raises(ValueError,match='bounded'):
        NonlinearAssemblyHistoryProbe(refs,maps,sections)
    made = NonlinearAssemblyHistoryProbe(refs,maps,sections,extent='REFINEMENT16')
    assert made.committed.positions.shape == (33,3)
    assert sum(len(h) for h in made.committed.histories) == 768
    for extent in ('REFINEMENT32',None,17):
        with pytest.raises(ValueError):
            NonlinearAssemblyHistoryProbe(refs,maps,sections,extent=extent)
    with pytest.raises(ValueError):
        NonlinearAssemblyHistoryProbe(refs+(refs[-1],),maps+[maps[-1]],[law()]*17,extent='REFINEMENT16')


def test_extent_does_not_change_existing_nonlinear_computation():
    refs = wave.refined_references(np,2)
    kwargs = (refs,[(0,1,2),(2,3,4)],[law(),law()])
    baseline = NonlinearAssemblyHistoryProbe(*kwargs,order=8)
    refined = NonlinearAssemblyHistoryProbe(*kwargs,order=8,extent='REFINEMENT16')
    force = np.zeros((5,3));force[-1] = [.01,-.03,.02]
    assert digest(baseline.trial(force)) == digest(refined.trial(force))


def make_lease(tmp_path):
    manager = tmp_path/'manager';manager.mkdir()
    (manager/'requests').mkdir();(manager/'active-lock').mkdir()
    repo = tmp_path/'repo';repo.mkdir()
    output = tmp_path/'output'
    commit,request_id = 'a'*40,'b'*32
    command = wave.command(repo,commit,output)
    row = {'request_id':request_id,'repository':str(repo),'command':command}
    wave.publish(manager/'requests'/(request_id+'.json'),row)
    wave.publish(manager/'active-lock'/'owner.json',row)
    (manager/'ledger.md').write_text(f'| date | {request_id} | APPROVED | test |\n',encoding='utf-8')
    return manager,repo,output,commit,request_id


def test_exact_resource_lease_and_reuse_rejection(tmp_path):
    manager,repo,output,commit,request_id = make_lease(tmp_path)
    assert wave.lease(repo,commit,output,manager=manager)[0] == request_id
    with pytest.raises(wave.RefinementError,match='lease mismatch'):
        wave.lease(repo,commit,tmp_path/'other',manager=manager)
    with (manager/'ledger.md').open('a',encoding='utf-8') as stream:
        stream.write(f'| date | {request_id} | COMPLETED_FAIL | test |\n')
    with pytest.raises(wave.RefinementError,match='unconsumed'):
        wave.lease(repo,commit,output,manager=manager)


def test_missing_approval_and_wrong_lock_rejected(tmp_path):
    manager,repo,output,commit,request_id = make_lease(tmp_path)
    (manager/'ledger.md').write_text('',encoding='utf-8')
    with pytest.raises(wave.RefinementError,match='approval'):
        wave.lease(repo,commit,output,manager=manager)
    owner = manager/'active-lock'/'owner.json'
    record = wave.load(owner);record['command'] = 'different'
    owner.write_bytes(wave.canonical(record))
    with pytest.raises(wave.RefinementError,match='lease mismatch'):
        wave.lease(repo,commit,output,manager=manager)


def test_dirty_authority_and_extent_guard(monkeypatch,tmp_path):
    commit = 'a'*40
    def git(repo,*args):
        if args == ('rev-parse','HEAD'): return commit
        if args[0] == 'status': return ' M production.py'
        raise AssertionError('dirty guard must precede later checks')
    monkeypatch.setattr(wave,'git',git)
    with pytest.raises(wave.RefinementError,match='dirty'):
        wave.authority(tmp_path,commit)
    def extra(repo,*args):
        if args == ('rev-parse','HEAD'): return commit
        if args[0] in ('status','merge-base'): return ''
        if args[0] == 'diff': return '\n'.join(wave.ALLOWED | {'src/changed.py'})
        raise AssertionError('extent guard must precede tree binding')
    monkeypatch.setattr(wave,'git',extra)
    with pytest.raises(wave.RefinementError,match='extent'):
        wave.authority(tmp_path,commit)


def test_worker_guards_precede_numerical_evaluation(monkeypatch,tmp_path):
    def deny(*args): raise wave.RefinementError('denied authority')
    def forbidden(*args): raise AssertionError('numerics must not run')
    monkeypatch.setattr(wave,'authority',deny)
    monkeypatch.setattr(wave,'numerical_records',forbidden)
    with pytest.raises(wave.RefinementError,match='denied'):
        wave.worker(tmp_path,'a'*40,tmp_path,'continuum256')


def packet(tmp_path,kind='continuum256'):
    folder = tmp_path/kind;folder.mkdir()
    rows = []
    count = 513 if kind == 'continuum256' else (256 if kind.endswith('order8') else 768)
    for i,a in enumerate(wave.CASE['schedule']):
        f = [a*v for v in wave.CASE['force_pattern']]
        if kind == 'continuum256':
            raw = {'force':f,'response':{'coordinates':[[2.,2.,3.]]*257,'potential':1.,'tip_moment_residual':0.},
                   'dense_orthogonality_error':0.,'histories':[[0.,0.]]*513,'dissipation_increments':[0.]*513}
        else:
            raw = {'forces':[[0.,0.,0.]]*32+[f],'positions':[[2.,2.,3.]]*33,'residual_norm':0.,
                   'response':{'potential':1.,'elements':[{'local_residual_norm':0.,'stations':[
                       {'response':{'plastic_active':False}}]*(count//16)}]*16}}
        binding = wave.publish(folder/f'step-{i:02}.json',raw)
        rows.append({'step':i,'amplitude':a,'force':f,'tip_displacement':[1.,2.,3.],'potential':1.,
                     'residual':0.,'local_check':0.,'active':0,'stations':count,'raw':binding})
    result = {'schema':wave.SCHEMA,'kind':kind,'authority':{'commit':'c'},'request_id':'b'*32,
              'request_sha256':'d'*64,'production_qualified':False,'records':rows}
    wave.publish(folder/'complete.json',result)
    return folder,result


@pytest.mark.parametrize('mutation', ['count','step','hash','force','summary','raw-rehashed'])
def test_packet_mutations_rejected(tmp_path,mutation):
    folder,record = packet(tmp_path)
    def inspect(): return wave.inspect_worker(folder,'continuum256',{'commit':'c'},'b'*32,'d'*64)
    assert inspect() == record
    if mutation == 'count': record['records'][0]['stations'] = 512
    if mutation == 'step': record['records'][0]['step'] = True
    if mutation == 'hash': record['records'][0]['raw']['sha256'] = '0'*64
    if mutation == 'force': record['records'][0]['force'] = [0.,0.,0.]
    if mutation == 'summary': record['records'][0]['tip_displacement'][0] += .1
    if mutation == 'raw-rehashed':
        raw_path = folder/'step-00.json'
        raw = wave.load(raw_path);raw['response']['coordinates'][-1][0] += .1
        raw_path.write_bytes(wave.canonical(raw))
        record['records'][0]['raw'].update(bytes=raw_path.stat().st_size,sha256=wave.sha(raw_path.read_bytes()))
    (folder/'complete.json').write_bytes(wave.canonical(record))
    with pytest.raises(wave.RefinementError): inspect()


def test_adjudication_retains_above_threshold_and_never_qualifies(tmp_path):
    records = [packet(tmp_path,k)[1] for k in wave.KINDS]
    passed = wave.adjudicate(records)
    assert passed['disposition'] == 'RESEARCH_REFINEMENT_BELOW_2_PERCENT'
    assert passed['production_qualified'] is False
    changed = copy.deepcopy(records);changed[-1]['records'][-1]['tip_displacement'][0] = 2.
    assert wave.adjudicate(changed)['disposition'] == 'RESEARCH_REFINEMENT_ABOVE_2_PERCENT'
    with pytest.raises(wave.RefinementError): wave.adjudicate(records[::-1])


def test_duplicate_nonfinite_and_exclusive_publication(tmp_path,monkeypatch):
    for content in (b'{"x":0,"x":1}\n',b'{"x":NaN}\n',b'{"x":1e400}\n',b' {}\n'):
        path = tmp_path/'bad.json';path.write_bytes(content)
        with pytest.raises(ValueError): wave.load(path)
    output = tmp_path/'complete.json'
    wave.publish(output,{'complete':True})
    original = output.read_bytes()
    with pytest.raises(FileExistsError): wave.publish(output,{'different':True})
    assert output.read_bytes() == original
    def fail(*args): raise OSError('injected publication failure')
    monkeypatch.setattr(os,'link',fail)
    with pytest.raises(OSError): wave.publish(tmp_path/'absent.json',{'value':1})
    assert not (tmp_path/'absent.json').exists()


@pytest.mark.skipif(os.name != 'nt',reason='Windows Job Object controls')
def test_short_contained_child_and_timeout(tmp_path):
    normal = tmp_path/'normal';normal.mkdir()
    result = wave.run_child([sys.executable,'-B','-c','print("unit")'],normal,Path.cwd(),dict(os.environ),timeout=5.,memory=64*(1<<20))
    assert result['exit_code'] == 0 and result['peak_tree_bytes'] <= 64*(1<<20)
    slow = tmp_path/'slow';slow.mkdir()
    with pytest.raises(wave.RefinementError,match='wall'):
        wave.run_child([sys.executable,'-B','-c','import time; time.sleep(20)'],slow,Path.cwd(),dict(os.environ),timeout=.5,memory=64*(1<<20))
    assert not (slow/'complete.json').exists()


@pytest.mark.skipif(os.name != 'nt',reason='Windows Job Object controls')
def test_small_memory_limit_fails_without_scientific_output(tmp_path):
    result = wave.run_child([sys.executable,'-B','-c','x=bytearray(128*1024*1024)'],tmp_path,Path.cwd(),dict(os.environ),timeout=5.,memory=32*(1<<20))
    assert result['exit_code'] != 0
    assert not (tmp_path/'complete.json').exists()


@pytest.mark.skipif(os.name != 'nt',reason='Windows Job Object controls')
def test_timeout_terminates_descendant_as_well_as_root(tmp_path):
    import ctypes
    from ctypes import wintypes
    script = ('import subprocess,sys,time; '
              'p=subprocess.Popen([sys.executable,"-B","-c","import time; time.sleep(20)"]); '
              'print(p.pid,flush=True); time.sleep(20)')
    with pytest.raises(wave.RefinementError,match='wall'):
        wave.run_child([sys.executable,'-B','-c',script],tmp_path,Path.cwd(),dict(os.environ),timeout=1.,memory=64*(1<<20))
    child = int((tmp_path/'stdout.log').read_text().strip())
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000,False,child)
    if handle:
        try:
            code = wintypes.DWORD()
            assert kernel.GetExitCodeProcess(handle,ctypes.byref(code))
            assert code.value != 259
        finally:
            kernel.CloseHandle(handle)


def test_failed_wave_never_publishes_aggregate(monkeypatch,tmp_path):
    manager = tmp_path/'manager';manager.mkdir();(manager/'claims').mkdir()
    repo = tmp_path/'repo';repo.mkdir()
    output = tmp_path/'external'
    monkeypatch.setattr(wave,'MANAGER',manager)
    monkeypatch.setattr(wave,'authority',lambda *args:{'commit':'a'*40})
    monkeypatch.setattr(wave,'lease',lambda *args:('b'*32,'d'*64))
    monkeypatch.setattr(wave,'run_child',lambda *args,**kwargs: {'exit_code':1})
    with pytest.raises(wave.RefinementError,match='failed'):
        wave.coordinate(repo,'a'*40,output)
    assert (output/'blocked-diagnostic.json').exists()
    assert not (output/'aggregate.json').exists()
    with pytest.raises((wave.RefinementError,FileExistsError)):
        wave.coordinate(repo,'a'*40,output)
