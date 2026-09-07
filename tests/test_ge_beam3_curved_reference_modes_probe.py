"""Bounded spectral supervisor mocks; no native spectral solves."""
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_curved_reference_modes_probe as probe


@pytest.mark.parametrize('incident',['success','exit','memory','timeout','inactivity','invalid','cleanup','descendant','mutation'])
def test_spectral_cleanup_and_validation_precede_publication(tmp_path,monkeypatch,incident):
    calls=[]; packet=probe.canonical(dict(development=True))
    ticks=iter([0.,601. if incident=='timeout' else 121. if incident=='inactivity' else 1.,601.])
    monkeypatch.setattr(probe.time,'monotonic',lambda:next(ticks)); monkeypatch.setattr(probe.time,'sleep',lambda _:None)
    monkeypatch.setattr(probe,'guard',lambda _:calls.append('guard'))
    def validate(output,raw,revision):
        calls.append('validate'); assert raw==packet
        if incident=='invalid': raise ValueError('invalid')
    monkeypatch.setattr(probe,'validate',validate)
    class Job:
        def __init__(self,memory): assert memory==24*(1<<30)
        def launch(self,command,*,cwd,env,stdout,stderr):
            assert command[3]=='docs.reference_cases.ge_beam3_curved_reference_modes_probe'
            assert all(env[k]==v for k,v in probe.THREAD_ENVIRONMENT.items()) and 'PYTHONPATH' not in env
            self.root=Path(stdout.name).parent; (self.root/'comparison.pending.json').write_bytes(packet); return self
        def accounting(self): return (0 if incident=='inactivity' else 1,1 if incident=='descendant' else 0,24*(1<<30) if incident=='memory' else 1)
        def poll(self): return 1 if incident=='exit' else 0
        def terminate(self):
            calls.append('terminate')
            if incident=='mutation': (self.root/'comparison.pending.json').write_bytes(packet+b' ')
            return incident!='cleanup'
        def close(self): calls.append('close')
    monkeypatch.setattr(probe,'_ProcessJob',Job); output=tmp_path/'fresh'
    if incident=='success':
        probe.run('1'*40,output)
        assert (output/'comparison.json').read_bytes()==packet
        with pytest.raises(FileExistsError): probe.run('1'*40,output)
    else:
        with pytest.raises((ValueError,RuntimeError)): probe.run('1'*40,output)
        assert not (output/'comparison.json').exists()
    assert calls.count('terminate')==calls.count('close')==1


@pytest.mark.parametrize('raw',[b'',b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b' {"x":1}\n'])
def test_noncanonical_spectral_packets_reject(tmp_path,raw):
    path=tmp_path/'bad.json'; path.write_bytes(raw)
    with pytest.raises(ValueError): probe.read(path)
