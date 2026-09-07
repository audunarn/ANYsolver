"""Loaded spectral containment and immutable-input guards; no actual solves."""
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_loaded_arch_spectra_probe as probe


@pytest.mark.parametrize('incident',['success','exit','memory','timeout','inactivity','invalid','cleanup','descendant','mutation'])
def test_loaded_spectral_cleanup_before_publication(tmp_path,monkeypatch,incident):
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
            assert command[3]=='docs.reference_cases.ge_beam3_loaded_arch_spectra_probe'
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
def test_noncanonical_loaded_packets_reject(raw):
    with pytest.raises(ValueError): probe.parse(raw)


def test_changed_preserved_checkpoint_fails_before_native_construction(tmp_path,monkeypatch):
    from docs.reference_cases import ge_beam3_loaded_arch_spectra as producer
    path=tmp_path/'bad.json'; path.write_bytes(b'{}\n'); monkeypatch.setattr(producer,'INPUT',path)
    def forbidden(*args): raise AssertionError('No native construction after failed input')
    monkeypatch.setattr(producer.family,'model',forbidden)
    with pytest.raises(ValueError,match='identity'): producer.build(forbidden,forbidden)
