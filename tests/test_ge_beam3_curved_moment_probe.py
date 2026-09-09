"""Disposable guard tests; no native solve or old campaign rerun."""
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_curved_moment_probe as probe
from docs.reference_cases.ge_beam3_curved_moment_comparison import sample_indices,metrics


@pytest.mark.parametrize('incident',['success','exit','memory','timeout','inactivity','invalid',
    'cleanup','descendant','mutation'])
def test_cleanup_and_validation_precede_publication(tmp_path,monkeypatch,incident):
    calls=[]; packet=probe.canonical(dict(development=True))
    ticks=iter([0.,601. if incident=='timeout' else 121. if incident=='inactivity' else 1.,601.])
    monkeypatch.setattr(probe.time,'monotonic',lambda:next(ticks))
    monkeypatch.setattr(probe.time,'sleep',lambda _:None)
    monkeypatch.setattr(probe,'guard',lambda _:calls.append('guard'))
    def summary(output,revision):
        calls.append('summary')
        if incident=='invalid': raise ValueError('invalid')
        return dict(development=True)
    monkeypatch.setattr(probe,'summary',summary)
    class Job:
        def __init__(self,memory): assert memory==24*(1<<30)
        def launch(self,command,*,cwd,env,stdout,stderr):
            assert command[3]=='docs.reference_cases.ge_beam3_curved_moment_probe'
            assert all(env[k]==v for k,v in probe.THREAD_ENVIRONMENT.items())
            assert 'PYTHONPATH' not in env
            self.root=Path(stdout.name).parent
            (self.root/'comparison.pending.json').write_bytes(packet)
            return self
        def accounting(self): return (0 if incident=='inactivity' else 1,1 if incident=='descendant' else 0,24*(1<<30) if incident=='memory' else 1)
        def poll(self): return 1 if incident=='exit' else 0
        def terminate(self):
            calls.append('terminate')
            if incident=='mutation': (self.root/'comparison.pending.json').write_bytes(packet+b' ')
            return incident!='cleanup'
        def close(self): calls.append('close')
    monkeypatch.setattr(probe,'_ProcessJob',Job)
    output=tmp_path/'fresh'
    if incident=='success':
        probe.run('1'*40,output)
        assert (output/'comparison.json').read_bytes()==packet
        with pytest.raises(FileExistsError): probe.run('1'*40,output)
    else:
        with pytest.raises((ValueError,RuntimeError)): probe.run('1'*40,output)
        assert not (output/'comparison.json').exists()
    assert calls.count('terminate')==calls.count('close')==1


@pytest.mark.parametrize('raw',[b'',b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b' {"x":1}\n'])
def test_noncanonical_or_nonfinite_packets_reject(tmp_path,raw):
    path=tmp_path/'bad.json'; path.write_bytes(raw)
    with pytest.raises(ValueError): probe.read(path)


def test_explicit_sampling_rejects_missing_duplicate_nonfinite():
    assert sample_indices([-1.,0.,1.],[1.,-1.])==[2,0]
    for samples,points in [([-1.,0.,1.],[.1]),([-1.,0.,0.,1.],[0.]),([-1.,float('nan'),1.],[1.])]:
        with pytest.raises(ValueError): sample_indices(samples,points)


def test_metrics_exact_match_and_perturbed_station():
    q=np.eye(3).tolist(); strain=[0.,0.,0.,0.,0.,1.]
    record=dict(mechanical=dict(positions=[[-1.,0.,0.],[1.,0.,0.]],position_low=np.zeros((2,3)).tolist(),nodal_frames=[q,q]),
        residual=[0.,0.,0.,0.,0.,-1.]+[0.]*6,metrics=[0.,0.])
    fine=dict(parameter=[-1.,1.],profile='IVP13',production_qualified=False,frames=[q,q],strains=[strain,strain],
        positions=[[-1.,0.,0.],[1.,0.,0.]],section=np.eye(6).tolist(),moment=[0.,0.,1.],strain_energy=1.)
    coarse={**fine,'profile':'IVP9'}
    station=dict(strain=strain,strain_low=[0.]*6,resultants=strain,resultants_low=[0.]*6,current_frame=q,measure=2.)
    recovery=[dict(stations=[station])]
    value=metrics(record,recovery,[-1.],[-1.,1.],fine,coarse)
    for key in ('strain_energy_norm_relative_error','spatial_force_max_absolute_error','spatial_moment_max_relative_error',
            'integrated_energy_relative_error','reaction_moment_absolute_error'): assert value[key]==0.
    station['strain']=[0.,0.,0.,0.,0.,2.]
    changed=metrics(record,recovery,[-1.],[-1.,1.],fine,coarse)
    assert changed['strain_energy_norm_relative_error']==1.
