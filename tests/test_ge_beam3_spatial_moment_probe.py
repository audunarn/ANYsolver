"""Disposable process tests; no native beam or constitutive execution."""
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_spatial_moment_probe as probe


@pytest.mark.parametrize('incident',['success','exit','memory','timeout','inactivity','invalid','cleanup','descendant','changed'])
def test_only_complete_cleaned_process_can_publish(tmp_path,monkeypatch,incident):
    events=[]; clock=iter([0.,601. if incident=='timeout' else 121. if incident=='inactivity' else 1.,601.])
    monkeypatch.setattr(probe.time,'monotonic',lambda:next(clock))
    monkeypatch.setattr(probe.time,'sleep',lambda _:None)
    monkeypatch.setattr(probe,'guard',lambda _:events.append('guard'))
    def summarize(output,revision):
        if incident=='invalid': raise ValueError('incomplete lane')
        return dict(revision=revision,changed=incident=='changed' and 'close' in events)
    monkeypatch.setattr(probe,'summarize',summarize)
    class Job:
        def __init__(self,memory): assert memory==24*(1 << 30)
        def launch(self,command,*,cwd,env,stdout,stderr):
            assert command[3]=='pytest' and all(t in command for t in probe.TESTS)
            assert all(env[k]==v for k,v in probe.THREAD_ENVIRONMENT.items())
            assert 'PYTHONPATH' not in env
            return self
        def accounting(self): return (0 if incident=='inactivity' else 1,1 if incident=='descendant' else 0,24*(1 << 30) if incident=='memory' else 1)
        def poll(self): return 1 if incident=='exit' else 0
        def terminate(self): events.append('terminate'); return incident!='cleanup'
        def close(self): events.append('close')
    monkeypatch.setattr(probe,'_ProcessJob',Job)
    out=tmp_path/'exclusive'
    if incident=='success':
        probe.run('1'*40,out)
        assert (out/'cycle.json').read_bytes()==(out/'cycle.pending.json').read_bytes()
        with pytest.raises(FileExistsError): probe.run('1'*40,out)
    else:
        with pytest.raises((ValueError,RuntimeError)): probe.run('1'*40,out)
        assert not (out/'cycle.json').exists()
    assert events.count('terminate')==events.count('close')==1


@pytest.mark.parametrize('incident',['success','failed','skip','missing','too_many'])
def test_lane_inventory_rejects_incomplete_reports_and_artifacts(tmp_path,incident):
    failures=1 if incident=='failed' else 0; skipped=1 if incident=='skip' else 0
    (tmp_path/'unit.xml').write_text(f'<testsuites><testsuite tests="34" failures="{failures}" errors="0" skipped="{skipped}"/></testsuites>',encoding='utf8')
    folder=tmp_path/'pytest'; folder.mkdir()
    names=probe.ARTIFACTS[:-1] if incident=='missing' else (*probe.ARTIFACTS,'extra.json') if incident=='too_many' else probe.ARTIFACTS
    for name in names:
        path=folder/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b'{}\n')
    if incident=='success': assert probe.summarize(tmp_path,'1'*40)['tests']['tests']==34
    else:
        with pytest.raises(ValueError): probe.summarize(tmp_path,'1'*40)
