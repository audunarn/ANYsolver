"""Two scoped staged material/lifecycle checks, not aggregate M4/F06 acceptance."""
from copy import deepcopy
from dataclasses import asdict, is_dataclass, replace
import json
import math
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from anysolver import _stiffened_shell_ge_finite_experimental as finite
from anysolver._stiffened_shell_beam_history import arrays as history_arrays
from test_stiffened_shell_native_coupled_material import definition_for

OPTIONS = dict(max_iterations=20, max_backtracks=12)
CONTROL = ss.AdaptiveIncrementControl(4, 64)


def _owner(request, definition):
    owner=ss.create_analysis(definition=definition)
    request.addfinalizer(owner.close)
    return owner


def _plain(v):
    if is_dataclass(v): return _plain(asdict(v))
    if isinstance(v, dict): return {str(k):_plain(x) for k,x in v.items()}
    if isinstance(v, (tuple,list)): return [_plain(x) for x in v]
    if isinstance(v, np.ndarray): return v.tolist()
    if isinstance(v, np.generic): return v.item()
    return v


def _canonical(v):
    return json.dumps(_plain(v),sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _capture(owner,result,path):
    """Record actual accepted origins/frames, never interpolate historical state."""
    path.mkdir(exist_ok=False)
    driver=owner._finite_driver;r=deepcopy(result)
    q=np.array(driver._state.q,copy=True)
    shell_frames=Rotation.from_rotvec(q[:owner._shell_count].reshape(-1,6)[:,3:].copy()).as_matrix()
    if driver._state.shell_anchors is not None:shell_frames=shell_frames@driver._state.shell_anchors
    beam={k:np.array(x,copy=True) for k,x in history_arrays(owner._beam_parts,driver._beam_origins,'accepted')}
    shell=deepcopy(driver._shell_origins);checkpoint=owner.checkpoint()
    (path/'checkpoint.bin').write_bytes(checkpoint)
    (path/'material.json').write_bytes(_canonical({'shell':shell,'beam':driver._beam_origins,'result':r}))
    np.savez_compressed(path/'state.npz',q=q,shell_frames=shell_frames,beam_positions=r.beam_positions,
        beam_frames=r.beam_frames,cell_frames=r.cell_frames,cell_resultants=r.cell_resultants,
        multipliers=r.multipliers,support_reactions=r.support_reactions,applied_dead_load=r.applied_dead_load,**beam)
    return dict(result=r,q=q,shell_frames=shell_frames,beam=beam,shell=shell,checkpoint=checkpoint,
                exact_material=_canonical((shell,driver._beam_origins)),path=path)


def _checks(new,previous,peak,owner):
    r=new['result']
    assert r.status==('completed' if owner._finite_driver._adaptive_state.completed else 'accepted_prefix')
    assert r.free_equilibrium_ratio<=1e-8 and r.constraint_max<=1e-9
    assert r.accepted_factors[-1]==r.load_position and r.load_position>0.
    knots=(0.,peak,peak/4.,-peak/2.,peak)
    j=min(int(r.load_position),3);fraction=r.load_position-j
    force=(1.-fraction)*knots[j]+fraction*knots[j+1]
    assert force!=0.,'no accepted zero-force target is admitted by this fixture'
    expected=np.zeros_like(r.applied_dead_load)
    expected[owner._shell_count+6*owner._beam_index[105]+2]=force
    np.testing.assert_array_equal(r.applied_dead_load,expected)
    shell_positions=np.asarray(owner._definition.shell.coordinates_m)+new['q'][:owner._shell_count].reshape(-1,6)[:,:3]
    positions=np.vstack((shell_positions,r.beam_positions))
    ground=r.support_reactions[:6*len(positions)].reshape(-1,6)
    load_force=np.array((0.,0.,force))
    balance_force=ground[:,:3].sum(axis=0)+load_force
    balance_moment=(ground[:,3:]+np.cross(positions,ground[:,:3])).sum(axis=0)+np.cross(positions[-1],load_force)
    balance={'force_N':balance_force.tolist(),'moment_Nm':balance_moment.tolist(),
             'force_ratio':float(np.linalg.norm(balance_force)/peak),
             'moment_ratio':float(np.linalg.norm(balance_moment)/(2.*peak))}
    (new['path']/'balance.json').write_bytes(_canonical(balance))
    assert balance['force_ratio']<=1e-8 and balance['moment_ratio']<=1e-8
    assert np.all(np.asarray(r.shell_layer_alpha)>=0.)
    for energy in r.beam_fibre_energy:assert math.fsum(energy.incremental_dissipation_j)>=0.
    for (_,element,slots,_),origin in zip(owner._shell_parts,new['shell']):
        if len(slots)==18:
            element.validate_model_bound_nonlinear_state(owner._shell_model.mesh,
                owner._shell_model.get_material('shell'),origin,3)
    if previous is None:return
    old=previous['result']
    for a,b in [(np.asarray(r.shell_layer_alpha),np.asarray(old.shell_layer_alpha)),
                (np.asarray(r.beam_station_accumulated),np.asarray(old.beam_station_accumulated))]:
        assert np.all(a>=b-64.*np.finfo(float).eps*np.maximum(np.abs(a),np.abs(b)))
    # Backward-Euler plastic work density Pa; includes recoverable hardening.
    # Not a fabricated global/cumulative shell dissipation or energy balance.
    for a,b in zip(r.shell_q4_material+r.shell_s3_material,old.shell_q4_material+old.shell_s3_material):
        terms=a.layer_stress*(a.plastic_strain-b.plastic_strain)
        assert np.all(terms.sum(axis=1)>=-64.*np.finfo(float).eps*np.abs(terms).sum(axis=1))


def _material_close(a,b,definition):
    """Full typed tree: only integrity digest is derived; floating leaves SI-scaled."""
    e=definition.shell.young_pa;t=definition.shell.thickness_m;g=e/(2.*(1.+definition.shell.poisson))
    scales={'layer_stress':e,'stress':e,'algorithmic_modulus':e,
        # Explicit1J SI scale for every paired material-energy recovery field.
        'stored_energy_j':1.,'previous_hardening_energy_j':1.,
        'incremental_dissipation_j':1.,'incremental_material_potential_j':1.,
        'strain':np.array((1.,1.,1.,.5,.5,.5)),'strain_low':np.array((1.,1.,1.,.5,.5,.5)),
        'resultants':np.array((e*.01,g*.008,g*.008,g*1.6666666666666667e-5/2.,e*8.333333333333333e-6/2.,e*8.333333333333333e-6/2.)),
        'resultants_low':np.array((e*.01,g*.008,g*.008,g*1.6666666666666667e-5/2.,e*8.333333333333333e-6/2.,e*8.333333333333333e-6/2.)),
        'committed_total_u':np.tile((2.,2.,2.,1.,1.,1.),3),
        'committed_constitutive_u':np.tile((2.,2.,2.,1.,1.,1.),3),
        'station_generalized_strain':np.array((1.,)*3+(.5,)*3+(1.,)*2),
        'station_generalized_resultant':np.array((e*t,)*3+(e*t**3/2.,)*3+(g*t,)*2)}
    def walk(x,y,key=''):
        assert type(x) is type(y)
        if is_dataclass(x):walk(asdict(x),asdict(y),key)
        elif isinstance(x,dict):
            assert x.keys()==y.keys()
            for k in x:
                if k!='state_integrity_sha256':walk(x[k],y[k],k)
        elif isinstance(x,np.ndarray):
            assert x.shape==y.shape and np.isfinite(x).all() and np.isfinite(y).all()
            np.testing.assert_allclose(x/scales.get(key,1.),y/scales.get(key,1.),rtol=0.,atol=1e-9)
        elif isinstance(x,(tuple,list)):
            assert len(x)==len(y)
            # Paired high/low values retain their representation and unit scale.
            if all(isinstance(v,(float,int,np.floating)) for v in x):
                np.testing.assert_allclose(np.asarray(x)/scales.get(key,1.),np.asarray(y)/scales.get(key,1.),rtol=0.,atol=1e-9)
            else:
                for xx,yy in zip(x,y):walk(xx,yy,key)
        elif isinstance(x,(float,np.floating)):
            np.testing.assert_allclose(x/scales.get(key,1.),y/scales.get(key,1.),rtol=0.,atol=1e-9)
        else:assert x==y
    walk(a,b)


def _same(a,b,definition,exact=False):
    x,y=a['result'],b['result']
    assert x.accepted_factors==y.accepted_factors and x.load_position==y.load_position
    assert x.load_programme_identity==y.load_programme_identity
    for field in ('beam_positions','beam_frames','cell_frames','cell_resultants',
                  'multipliers','support_reactions','applied_dead_load'):
        np.testing.assert_allclose(getattr(x,field),getattr(y,field),rtol=1e-8,atol=1e-10)
    np.testing.assert_allclose(a['shell_frames'],b['shell_frames'],rtol=0.,atol=1e-9)
    np.testing.assert_allclose(a['q'][:36].reshape(-1,6)[:,:3],b['q'][:36].reshape(-1,6)[:,:3],rtol=1e-8,atol=1e-10)
    if exact:
        assert a['exact_material']==b['exact_material']
        for field in ('shell_q4_material','shell_s3_material','beam_fibre_material','beam_fibre_energy'):
            assert _canonical(getattr(x,field))==_canonical(getattr(y,field))
    else:
        _material_close(a['shell'],b['shell'],definition);_material_close(a['beam'],b['beam'],definition)
        assert len(x.beam_fibre_material)==len(y.beam_fibre_material)
        for xx,yy in zip(x.beam_fibre_material,y.beam_fibre_material):
            assert (xx.element_id,xx.cell,xx.station)==(yy.element_id,yy.cell,yy.station)
            _material_close(xx,yy,definition)
        for field in ('shell_q4_material','shell_s3_material','beam_fibre_energy'):
            assert len(getattr(x,field))==len(getattr(y,field))
            for xx,yy in zip(getattr(x,field),getattr(y,field)):_material_close(xx,yy,definition)
    assert max(x.free_equilibrium_ratio,y.free_equilibrium_ratio)<=1e-8
    assert max(x.constraint_max,y.constraint_max)<=1e-9


def _run(request,monkeypatch,tmp_path,record_property,triangles):
    definition=definition_for(triangles,triangles);peak=50. if triangles else 1000.
    if not triangles:
        # The physical work/history route selects the independently checked full
        # Q4 map. Historical-corotational behavior remains a distinct identity.
        definition=replace(definition,q4_pullback_policy=ss.Q4_ALGORITHMIC_PULLBACK_V1)
    control=_owner(request,definition)
    endpoints=tuple((ss.NodalAction('beam',105,(0.,0.,f,0.,0.,0.)),) for f in (peak,peak/4.,-peak/2.,peak))
    programme=ss.StagedDeadLoadProgramme(control.preflight()['identity'],endpoints)
    (tmp_path/'input.json').write_bytes(_canonical({'programme':programme.to_payload(),'fixture':'mixed-S3' if triangles else 'Q4',
        'q4_pullback_policy':definition.q4_pullback_policy,
        'peak_N':peak,'max_iterations':20,'max_backtracks':12,'max_cutbacks':4,'max_attempts':64,'targets':(.5,1.,2.,3.,4.)}))
    record_property('raw_state_directory',str(tmp_path));record_property('programme_identity',programme.identity)
    journal=[]
    def observer(owner,label,history):
        def notify(result):
            made=_capture(owner,result,tmp_path/(label+'-'+str(len(history))))
            history.append(made);_checks(made,history[-2] if len(history)>1 else None,peak,owner)
        return notify
    callback=observer(control,'control',journal)
    first=control.solve(programme,(.5,1.),increment_control=CONTROL,on_accepted=callback,**OPTIONS)
    prefix=journal[-1];saved=control.checkpoint()
    if triangles:assert max(max(row) for row in first.shell_layer_alpha)>0.,'S3 J2 plasticity not exercised'
    else:
        fibres=prefix['beam']['accepted_fibres'];assert np.any(fibres[:,2]+fibres[:,3]>0.),'beam-fibre plasticity not exercised'
        assert any(math.fsum(x.incremental_dissipation_j)>0. for x in first.beam_fibre_energy)
    changed=ss.StagedDeadLoadProgramme(control.preflight()['identity'],endpoints[:-1]+
        ((ss.NodalAction('beam',105,(0.,0.,peak+1.,0.,0.,0.)),),))
    with pytest.raises(ValueError,match='programme changed'):control.solve(changed,(2.,),increment_control=CONTROL,**OPTIONS)
    assert control.checkpoint()==saved and control.recover() is first
    token=CancellationToken();original=finite.cancellation_safe_point
    def cancel(token_value,stage):
        if stage=='stiffened-shell.finite.material-publish':token.cancel('plastic candidate before commit')
        return original(token_value,stage)
    count=len(journal)
    with monkeypatch.context() as patch:
        patch.setattr(finite,'cancellation_safe_point',cancel)
        with pytest.raises(SolveCancelled,match='plastic candidate before commit'):
            control.solve(programme,(2.,),increment_control=CONTROL,on_accepted=callback,cancellation_token=token,**OPTIONS)
    assert len(journal)==count and control.checkpoint()==saved and control.recover() is first
    with pytest.raises(ss.FiniteIncrementFailure):control.solve(programme,(2.,),max_iterations=1,max_backtracks=0,on_accepted=callback)
    assert len(journal)==count and control.checkpoint()==saved and control.recover() is first
    rebased=_owner(request,definition);rebased.restore(saved)
    before=_capture(rebased,rebased.recover(),tmp_path/'prefix-restored');_same(prefix,before,definition,True)
    event=rebased.rebase_rotations(expected_generation=rebased.recover().generation)
    after=_capture(rebased,event,tmp_path/'prefix-rebased');_same(before,after,definition,True)
    assert np.any(before['q'][:36].reshape(-1,6)[:,3:]!=0.)
    np.testing.assert_array_equal(after['q'][:36].reshape(-1,6)[:,3:],0.)
    chart=_owner(request,definition);chart.restore(after['checkpoint']);assert chart.checkpoint()==after['checkpoint']
    chart_prefix=_capture(chart,chart.recover(),tmp_path/'chart-restored');_same(after,chart_prefix,definition,True)
    branches={'rebased':[after],'chart-restored':[chart_prefix]};ends={}
    for target in (2.,3.,4.):
        start=len(journal);control.solve(programme,(target,),increment_control=CONTROL,on_accepted=callback,**OPTIONS)
        expected=journal[start:];ends[target]=journal[-1]
        for label,owner in [('rebased',rebased),('chart-restored',chart)]:
            history=branches[label];start=len(history)
            owner.solve(programme,(target,),increment_control=CONTROL,on_accepted=observer(owner,label,history),**OPTIONS)
            actual=history[start:]
            assert [s['result'].load_position for s in actual]==[s['result'].load_position for s in expected]
            for a,b in zip(expected,actual):_same(a,b,definition)
    for position in (2.,3.):
        owner=_owner(request,definition);owner.restore(ends[position]['checkpoint'])
        assert owner.checkpoint()==ends[position]['checkpoint']
        restored=_capture(owner,owner.recover(),tmp_path/('restart-'+str(position)));_same(ends[position],restored,definition,True)
        history=[restored]
        for target in ((3.,4.) if position==2. else (4.,)):
            start=len(history);origin=history[-1]['result'].load_position
            owner.solve(programme,(target,),increment_control=CONTROL,on_accepted=observer(owner,'restart'+str(position),history),**OPTIONS)
            expected=[s for s in journal if origin<s['result'].load_position<=target]
            assert [s['result'].load_position for s in history[start:]]==[s['result'].load_position for s in expected]
            for a,b in zip(expected,history[start:]):_same(a,b,definition)
    assert control.recover().load_programme_complete and control.recover().load_position==4.
    coverage={}
    for domain in ('shell','beam'):
        frames=[s['shell_frames'] if domain=='shell' else s['result'].beam_frames for s in journal]
        frames=[np.tile(np.eye(3),(len(frames[0]),1,1))]+frames
        increments=[b@a.transpose(0,2,1) for a,b in zip(frames,frames[1:])]
        angle=max(float(np.max(Rotation.from_matrix(q).magnitude())) for q in frames)
        comm=max(float(np.max(Rotation.from_matrix(b@a@b.transpose(0,2,1)@a.transpose(0,2,1)).magnitude()))
                 for a,b in zip(increments,increments[1:]))
        coverage[domain]={'rotation_rad':angle,'commutator_rad':comm,'F06_large_elastic_floors_observed_only':angle>=.05 and comm>=1e-5}
    (tmp_path/'coverage.json').write_bytes(_canonical(coverage));record_property('measured_coverage',json.dumps(coverage))


def test_q4_staged_fibre_history_restart_atomicity_and_plastic_rebase(request,monkeypatch,tmp_path,record_property):
    _run(request,monkeypatch,tmp_path,record_property,False)


def test_mixed_s3_staged_j2_history_restart_atomicity_and_plastic_rebase(request,monkeypatch,tmp_path,record_property):
    _run(request,monkeypatch,tmp_path,record_property,True)
