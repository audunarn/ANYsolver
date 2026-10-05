"""Local stationary-strip support with closed neighboring material."""
from dataclasses import replace
import os
import numpy as np
import pytest
from anysolver.general_contact.native_surface_history import NativeSurfaceHistoryField,NativeSurfaceMotionSegment
from anysolver.general_contact.native_surface_front import stationary_front_angular_cover,stationary_front_angular_envelopes
from anysolver.general_contact.native_surface_support import SupportIntervalBudget,_minimum
from anysolver.general_contact.native_surface_friction_integral import integrate_event_friction_fronts
from test_general_contact_native_surface_support import _field
from test_general_contact_native_surface_friction_integral import _settings


def _mixed(height=.035,slope=.01,rotation=1.1):
    motion=NativeSurfaceMotionSegment(np.zeros((3,3)),np.array(((rotation,0.,0.),(0.,0.,0.))),np.zeros(18))
    field=_field(height=height,rotation=-.8,segments=(motion,),activation_policy='transverse_event_sequence')
    positions=field.initial.positions.copy();positions[:,2]+=slope*positions[:,0]
    return NativeSurfaceHistoryField(field.patch,replace(field.initial,positions=positions),field.segments)


def _three_segment_pulse(initial_height=.036,prefix_height_change=-.001):
    value=_mixed(height=initial_height,rotation=1.6)
    def translation(dz):
        displacement=np.zeros((3,3));displacement[:,2]=dz
        return NativeSurfaceMotionSegment(displacement,np.zeros((2,3)),np.zeros(18))
    return NativeSurfaceHistoryField(value.patch,value.initial,
        (translation(prefix_height_change),value.segments[0],translation(.001)))


def test_whole_angle_stationary_envelope_is_locally_open_with_closed_neighbor():
    value=_mixed();angles=value.patch.rule.definition['angle_range'];budget=SupportIntervalBudget(128)
    cover=stationary_front_angular_cover(value,0,0,angles,budget=budget)
    envelopes=stationary_front_angular_envelopes(value,cover,maximum_axial_uncertainty=1e-7,budget=budget)
    assert len(envelopes)==1
    a,b=envelopes[0]
    # Independent stationary minimum: radius-height=0 at xi=-.5 for all angles.
    assert a<-.5-1e-7<-.5+1e-7<b
    normalframe=value.patch.rule.samples[0].station.reference.nodal_triads[0]
    for pose in (value.initial,value.current):
        gap,padding=_minimum(pose,value.patch.target,normalframe,.03,0,(a,b),angles)
        assert gap>padding
    gap,_=_minimum(value.current,value.patch.target,normalframe,.03,0,(-.8,-.2),angles)
    assert gap<0.
    assert budget.intervals<128
    with pytest.raises(MemoryError,match='cap'):
        stationary_front_angular_envelopes(value,cover,maximum_axial_uncertainty=1e-7,budget=SupportIntervalBudget(1))


@pytest.mark.skipif(os.environ.get('ANYSOLVER_RUN_UNRESOLVED_MIXED_FRONT')!='1',
    reason='bounded expensive development replay; helper tested, native owner/acceptance still incomplete')
def test_mixed_endpoints_integrated_force_and_tangent(tmp_path):
    import json,os
    from pathlib import Path
    from scipy.integrate import quad
    value=_mixed()
    try:
        result=integrate_event_friction_fronts(value,_settings(),maximum_axial_uncertainty=1e-7)
    except Exception as error:
        folder=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
        (folder/'mixed_front_failure.json').write_text(json.dumps({'error':str(error),
            'diagnostics':getattr(error,'integration_diagnostics',None)},indent=2),encoding='utf-8')
        raise
    # All closed points slide in +y. Integrate triangular linear pressure in xi,
    # then integrate its smooth analytic angular dependence independently.
    root=lambda delta:(.03*np.cos(.3+delta)-.035)/.01
    exact=.03*.3*1000*quad(lambda delta:.5*.01*(root(delta)+.8)**2,-.02,.02,epsabs=1e-14)[0]
    derivative=-.03*.3*1000*quad(lambda delta:root(delta)+.8,-.02,.02,epsabs=1e-14)[0]
    y=np.zeros(60);y[[1,7,13]]=1.
    z=np.zeros(60);z[[2,8,14]]=1.
    force=float(y@result.residual);tangent=float(y@result.tangent@z)
    folder=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
    (folder/'mixed_front_result.json').write_text(json.dumps({'force':force,'reference_force':exact,
        'tangent':tangent,'reference_tangent':derivative,'diagnostics':result.diagnostics},indent=2),encoding='utf-8')
    assert force==pytest.approx(exact,rel=1e-5,abs=1e-10)
    assert tangent==pytest.approx(derivative,rel=1e-5,abs=1e-8)
    assert result.dissipated_increment_j>0 and result.stored_energy_j>0
    total=sum((result.residual[6*i:6*i+3] for i in range(3)),np.zeros(3))
    total+=sum((result.residual[42+6*i:45+6*i] for i in range(3)),np.zeros(3))
    np.testing.assert_allclose(total,np.zeros(3),atol=1e-12,rtol=0.)


def test_no_stationary_branch_does_not_discard_closed_material():
    from scipy.integrate import quad
    value=_mixed(height=.024,slope=.001,rotation=.2)
    result=integrate_event_friction_fronts(value,_settings(),maximum_axial_uncertainty=1e-7)
    expected=.03*.3*1000*.6*quad(lambda delta:.03*np.cos(-.6+delta)-.0235,-.02,.02,epsabs=1e-14)[0]
    assert sum(result.residual[6*i+1] for i in range(3))==pytest.approx(expected,rel=1e-5,abs=1e-10)
    assert result.stored_energy_j>0 and result.dissipated_increment_j>0
    assert result.diagnostics['zero_panels_certified']==0


def test_variable_front_route_keeps_closed_no_stationary_surface_force():
    from scipy.integrate import quad
    from anysolver.general_contact.native_surface_friction_integral import integrate_variable_event_friction_fronts
    value=_mixed(height=.024,slope=.001,rotation=.2)
    result=integrate_variable_event_friction_fronts(value,_settings(),maximum_axial_uncertainty=1e-7)
    expected=.03*.3*1000*.6*quad(lambda delta:.03*np.cos(-.6+delta)-.0235,-.02,.02,epsabs=1e-14)[0]
    assert sum(result.residual[6*i+1] for i in range(3))==pytest.approx(expected,rel=1e-5,abs=1e-10)
    assert result.stored_energy_j>0 and result.dissipated_increment_j>0
    assert result.diagnostics['zero_panels_certified']==0
    assert result.diagnostics['open_endpoint_strip_enclosures']==0


def test_multisegment_strip_bound_uses_actual_branch_start():
    from math import acos,sin,cos,fsum
    from anysolver.general_contact.native_surface_path import material_path_pose
    from anysolver.general_contact.native_surface_front_work import open_front_strip_work_bound
    value=_three_segment_pulse();prefix=value.segments[0]
    start=material_path_pose(value.initial,prefix.translations,prefix.angular,prefix.shell_increment,1.)
    middle=NativeSurfaceHistoryField(value.patch,start,(value.segments[1],))
    width=1e-7
    bound=open_front_strip_work_bound(value,0,width,segment_index=1)
    np.testing.assert_array_equal(bound,open_front_strip_work_bound(middle,0,width))
    height=.03-.01*width/2;theta=acos(height/.03)
    elastic=0.;previous=.03*sin(-theta);terms=[]
    for i in range(1,32):
        angle=-theta+2*theta*i/32;y=.03*sin(angle)
        trial=elastic+y-previous;cap=.3*1000*(.03*cos(angle)-height)
        next_elastic=min(trial,cap/1000);terms.append(cap*(trial-next_elastic))
        elastic=next_elastic;previous=y
    assert 0<fsum(terms)<=bound[1]
    assert .5*1000*elastic**2<=bound[2]
    with pytest.raises(ValueError,match='one released-origin segment'):
        open_front_strip_work_bound(value,0,width)
    for invalid in (-1,3,True):
        with pytest.raises(ValueError,match='segment index'):
            open_front_strip_work_bound(value,0,width,segment_index=invalid)


def test_multisegment_front_rejects_closed_prefix_capture():
    # Middle-segment strip is open at its own endpoints, but an earlier
    # captured pose has contact there. Initial penetration remains rejected.
    value=_three_segment_pulse()
    down=np.zeros((3,3));down[:,2]=-.012
    up=np.zeros((3,3));up[:,2]=.011
    value=NativeSurfaceHistoryField(value.patch,value.initial,
        (NativeSurfaceMotionSegment(down,np.zeros((2,3)),np.zeros(18)),
         NativeSurfaceMotionSegment(up,np.zeros((2,3)),np.zeros(18)),*value.segments[1:]))
    with pytest.raises(ValueError,match='unresolved or closed captured endpoint'):
        integrate_event_friction_fronts(value,_settings(),maximum_axial_uncertainty=1e-7)


@pytest.mark.skipif(os.environ.get('ANYSOLVER_RUN_UNRESOLVED_MIXED_FRONT')!='1',
    reason='bounded expensive three-segment development replay; explicit execution only')
def test_multisegment_front_integral_has_independent_cumulative_work(tmp_path):
    from math import acos,sin,cos,fsum
    from scipy.integrate import quad
    import json,os
    from pathlib import Path
    value=_three_segment_pulse()
    folder=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
    try:
        result=integrate_event_friction_fronts(value,_settings(),maximum_axial_uncertainty=1e-7)
    except Exception as error:
        (folder/'multisegment_front_failure.json').write_text(json.dumps(dict(error=str(error),
            diagnostics=getattr(error,'integration_diagnostics',None)),indent=2),encoding='utf-8')
        raise
    def independent_work(xi):
        height=.035+.01*xi
        if height>=.03:return 0.
        theta=acos(height/.03);elastic=0.;previous=.03*sin(-theta);terms=[]
        for i in range(1,32):
            angle=-theta+2*theta*i/32;y=.03*sin(angle)
            trial=elastic+y-previous;cap=.3*1000*(.03*cos(angle)-height)
            next_elastic=min(trial,cap/1000);terms.append(cap*(trial-next_elastic))
            elastic=next_elastic;previous=y
        return fsum(terms)
    # The translated prefix and suffix are strictly open. Only the complete
    # middle pulse contributes cumulative work, independent of angular offset.
    expected=.03*.04*quad(independent_work,-.8,-.5,epsabs=1e-13,epsrel=1e-10)[0]
    (folder/'multisegment_front_result.json').write_text(json.dumps(dict(
        cumulative_work=result.cumulative_dissipation_j,reference=expected,
        stored=result.stored_energy_j,dissipated=result.dissipated_increment_j,
        released=result.released_storage_j,
        diagnostics=result.diagnostics),indent=2),encoding='utf-8')
    assert result.cumulative_dissipation_j==pytest.approx(expected,rel=1e-5,abs=1e-12)
    np.testing.assert_array_equal(result.residual,0.)
    np.testing.assert_array_equal(result.tangent,0.)
    assert result.stored_energy_j==0. and result.dissipated_increment_j==0.
    assert result.released_storage_j==0.


def _saved_local_front_field():
    import json
    from pathlib import Path
    from anysolver.general_contact.native_surface_patch import NativeS3MaterialSurfacePatch
    from anysolver.general_contact.native_surface_quadrature import NativeRoundSurfaceRule
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    from anysolver.general_contact.native_surface_friction_integral import NativeSurfaceFrictionIntegrationSettings
    from test_general_contact_native_surface_replay_owner import _replay_patch
    source=Path(__file__).parents[1]/'docs/d1_review_support/contact_c5_native_surface_point_20261002/replay_owner_second_load_rejected_path.json'
    saved=json.loads(source.read_text());_,bridge=_replay_patch('transverse_event_sequence')
    full=NativeSurfaceHistoryField(bridge.pair,
        NativeS3MaterialConfiguration(**{k:np.asarray(v) for k,v in saved['initial'].items()}),
        tuple(NativeSurfaceMotionSegment(**{k:np.asarray(v) for k,v in s.items()}) for s in saved['segments']),
        maximum_intervals=saved['maximum_intervals'])
    base=full.patch.pairs[0]
    rule=NativeRoundSurfaceRule(base.source.element_id,base.source.reference,base.source.radius,
        xi_range=(.72,.80),angle_range=(3.19,3.20),axial_order=2,angular_order=2)
    patch=NativeS3MaterialSurfacePatch(rule,[full._target_at(s.station) for s in rule.samples],
        normal_stiffness_Pa_per_m=base.normal_stiffness_Pa_per_m,
        friction_coefficient=base.friction_coefficient,
        tangential_stiffness_Pa_per_m=base.tangential_stiffness_Pa_per_m,
        activation_policy='transverse_event_sequence',event_history_substeps=base.event_history_substeps,
        gap_check='straight_patch')
    value=NativeSurfaceHistoryField(patch,full.initial,full.segments,maximum_intervals=full.maximum_intervals)
    settings=NativeSurfaceFrictionIntegrationSettings(**saved['settings'])
    return value,settings,source


@pytest.mark.skipif(os.environ.get('ANYSOLVER_RUN_SAVED_NATIVE_LOCAL_FRONT')!='1',
    reason='named saved-path local discriminator; no fullpatch or coupled run')
def test_saved_second_load_local_front_window(tmp_path):
    import json,os,time
    from dataclasses import asdict
    from pathlib import Path
    from hashlib import sha256
    value,settings,source=_saved_local_front_field()
    folder=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
    record=dict(saved_input_sha256=sha256(source.read_bytes()).hexdigest(),
        selected_xi=(.72,.80),selected_angle=(3.19,3.20),settings=asdict(settings),
        event_policy='transverse_event_sequence',field_identity=value.identity,
        scope='local saved-path integration only, no solve/fullpatch/owner admission')
    (folder/'saved_local_front_preflight.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    start=time.perf_counter()
    try:
        result=integrate_event_friction_fronts(value,settings,maximum_axial_uncertainty=1e-7)
    except Exception as error:
        record.update(elapsed_seconds=time.perf_counter()-start,error_type=type(error).__name__,
            error=str(error),diagnostics=getattr(error,'integration_diagnostics',None))
        (folder/'saved_local_front_failure.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
        raise
    source_force=sum((result.residual[6*i:6*i+3] for i in range(3)),np.zeros(3))
    target_force=sum((result.residual[42+6*i:45+6*i] for i in range(3)),np.zeros(3))
    force_scale=max(np.linalg.norm(source_force),np.linalg.norm(target_force),1e-12)
    record.update(elapsed_seconds=time.perf_counter()-start,diagnostics=result.diagnostics,
        source_force=source_force.tolist(),target_force=target_force.tolist(),
        force_balance_relative=float(np.linalg.norm(source_force+target_force)/force_scale),
        work=dict(stored=result.stored_energy_j,dissipated=result.dissipated_increment_j,
            released=result.released_storage_j,cumulative=result.cumulative_dissipation_j))
    (folder/'saved_local_front_result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    assert result.diagnostics['maximum_scaled_error_estimate']<=1.
    assert record['force_balance_relative']<=1e-6
    assert all(x>=0 for x in record['work'].values())


def test_history_work_cap_covers_inherited_elastic_state_during_unloading():
    from anysolver.general_contact.native_surface_front import prepare_stationary_band
    from anysolver.general_contact.native_surface_front_work import history_front_strip_work_bound
    from anysolver.general_contact.native_surface_history import NativeSurfaceReplayBudget
    original=_mixed(rotation=0.)
    def move(dy,dz):
        translation=np.tile((0.,dy,dz),(3,1))
        return NativeSurfaceMotionSegment(translation,np.zeros((2,3)),np.zeros(18))
    motions=(move(.004,-.011),move(0.,.001))
    value=NativeSurfaceHistoryField(original.patch,original.initial,motions)
    budget=SupportIntervalBudget(128);angles=value.patch.rule.definition['angle_range']
    covers=tuple(stationary_front_angular_cover(value,0,i,angles,budget=budget,
        xi_bounds=(-.8,-.2)) for i in range(2))
    prepared=tuple(prepare_stationary_band(value,cover,budget=budget) for cover in covers)
    envelopes=tuple(stationary_front_angular_envelopes(value,cover,maximum_axial_uncertainty=1e-7,
        budget=budget,prepared=item,_include_endpoints=True) for cover,item in zip(covers,prepared))
    upper=history_front_strip_work_bound(value,0,(-.65,-.55),prepared,envelopes)
    first=NativeSurfaceHistoryField(original.patch,original.initial,motions[:1]).query(-.6,1.5*np.pi,
        budget=NativeSurfaceReplayBudget(16))
    last=value.query(-.6,1.5*np.pi,budget=NativeSurfaceReplayBudget(16))
    trial=last.last_contribution.trial
    actual=np.array((trial.stored_energy_density,trial.dissipated_increment_density,
        trial.released_storage_density,last.history.cumulative_dissipation_density))
    assert first.last_contribution.trial.stored_energy_density>trial.stored_energy_density>0
    assert actual[-1]>actual[1]>0 and np.all(actual<=upper)
    assert np.all(upper>=0)


def test_deferred_directional_controls_match_eager_refined_integral(tmp_path,monkeypatch):
    """Polynomial code probe for evaluation order; no mechanics qualification."""
    import json,os,time
    from pathlib import Path
    from types import SimpleNamespace
    from anysolver.general_contact.native_surface_friction_integral import integrate_material_friction
    value=_mixed(height=.024,slope=.001,rotation=.2)
    # Actual geometry, proof/cache and adaptive integration; replace only the
    # expensive material law with an independent degree-eight polynomial.
    # Gauss4 underintegrates its parent; Gauss8 is exact, as are refined outputs.
    def polynomial_query(self,xi,angle,*,budget):
        q=((xi+.8)/.6)**8
        residual=np.zeros(60);residual[0]=q
        tangent=np.zeros((60,60));tangent[0,0]=q
        point=SimpleNamespace(residual=residual,normal_residual=np.zeros(60),
            spatial_tangent=lambda:tangent,normal_spatial_tangent=lambda:np.zeros((60,60)),
            trial=SimpleNamespace(stored_energy_density=q,dissipated_increment_density=q,
                released_storage_density=q,cumulative_dissipation_density=q))
        return SimpleNamespace(last_contribution=point,history=SimpleNamespace(cumulative_dissipation_density=q))
    monkeypatch.setattr(NativeSurfaceHistoryField,'query',polynomial_query)
    settings=replace(_settings(),force_absolute_tolerance=1e-8,
        tangent_absolute_tolerance=1e-8,energy_absolute_tolerance=1e-8)
    outputs=[];timings=[]
    for eager in (True,False):
        start=time.perf_counter()
        outputs.append(integrate_material_friction(value,settings,_front_uncertainty=1e-7,
            _local_front_strips=True,_eager_directional_controls=eager))
        timings.append(time.perf_counter()-start)
    eager,deferred=outputs
    folder=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
    (folder/'directional_control_parity.json').write_text(json.dumps(dict(
        elapsed_seconds=timings,eager=eager.diagnostics,deferred=deferred.diagnostics),indent=2),encoding='utf-8')
    np.testing.assert_array_equal(deferred.residual,eager.residual)
    np.testing.assert_array_equal(deferred.tangent,eager.tangent)
    for key in ('stored_energy_j','dissipated_increment_j','released_storage_j','cumulative_dissipation_j'):
        assert getattr(deferred,key)==getattr(eager,key)
    for key in ('maximum_scaled_error_estimate','panels','refinement_axes'):
        assert deferred.diagnostics[key]==eager.diagnostics[key]
    refinements=len(deferred.diagnostics['refinement_axes'])
    assert refinements>0
    assert deferred.diagnostics['directional_control_panels']==refinements
    assert deferred.diagnostics['directional_control_panels']<eager.diagnostics['directional_control_panels']
    assert deferred.diagnostics['queries']<eager.diagnostics['queries']
    exact=.03*.6*.04/9.
    assert deferred.residual[0]==pytest.approx(exact,rel=1e-13,abs=1e-16)
    assert deferred.tangent[0,0]==pytest.approx(exact,rel=1e-13,abs=1e-16)
    assert deferred.stored_energy_j==pytest.approx(exact,rel=1e-13,abs=1e-16)
    with pytest.raises(MemoryError,match='material-query/cache cap'):
        integrate_material_friction(value,replace(settings,maximum_queries=1),
            _front_uncertainty=1e-7,_local_front_strips=True)


def test_complete_history_envelopes_bound_boundary_endpoint_and_stored_work():
    from anysolver.general_contact.native_surface_front_boundary import stationary_endpoint_angular_partition
    from anysolver.general_contact.native_surface_front import prepare_stationary_band,axial_contact_front
    from anysolver.general_contact.native_surface_front_work import history_front_strip_work_bound
    from anysolver.general_contact.native_surface_history import NativeSurfaceReplayBudget
    value=_mixed(rotation=.8);budget=SupportIntervalBudget(128)
    partition=stationary_endpoint_angular_partition(value,0,value.patch.rule.definition['angle_range'],budget=budget)
    saw_closed=False
    for left,right,_,_ in partition.bands:
        cover=stationary_front_angular_cover(value,0,0,(left,right),budget=budget,xi_bounds=(-.8,-.2),
            endpoint_partition=partition,_variable_endpoint_branches=True)
        prepared=prepare_stationary_band(value,cover,budget=budget)
        envelopes=stationary_front_angular_envelopes(value,cover,maximum_axial_uncertainty=1e-7,
            budget=budget,prepared=prepared,_include_endpoints=True)
        # Independently evaluated coefficients at actual times must lie inside
        # the union of the endpoint and stationary-extremum envelopes.
        lower=min(a for a,_ in envelopes);upper=max(b for _,b in envelopes)
        for angle in np.linspace(left,right,3):
            for time in np.linspace(0.,1.,13):
                root=axial_contact_front(value,0,0,float(time),float(angle)).axial_coordinate()
                assert lower<=root<=upper
        if not len(cover):continue
        strip=(max(-.8,envelopes[0][0]),min(-.2,envelopes[0][1]))
        density=history_front_strip_work_bound(value,0,strip,(prepared,),(envelopes,))
        # The captured endpoint is genuinely closed at this material point;
        # its nonzero storage is retained and bounded, never replaced by zero.
        angle=(left+right)/2
        xi=axial_contact_front(value,0,0,1.,angle).axial_coordinate()-1e-4
        if not strip[0]<xi<strip[1]:continue
        point=value.query(float(xi),float(angle),budget=NativeSurfaceReplayBudget(16));trial=point.last_contribution.trial
        work=np.array((trial.stored_energy_density,trial.dissipated_increment_density,
            trial.released_storage_density,point.history.cumulative_dissipation_density))
        assert np.all(work>=0) and np.all(work<=density)
        saw_closed=saw_closed or work[0]>0
    assert saw_closed and budget.intervals<=128
    with pytest.raises(ValueError,match='identity/domain'):
        history_front_strip_work_bound(value,0,(-1.,0.),(prepared,),(envelopes,))


@pytest.mark.skipif(os.environ.get('ANYSOLVER_RUN_UNRESOLVED_MIXED_FRONT')!='1',
    reason='bounded actual boundary-ending development integration, not owner admission')
def test_boundary_ending_front_retains_integrated_force_tangent_and_work(tmp_path):
    import json,time
    from pathlib import Path
    from scipy.integrate import quad
    from anysolver.general_contact.native_surface_friction_integral import integrate_variable_event_friction_fronts
    value=_mixed(rotation=.8);folder=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)))
    folder.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    try:
        result=integrate_variable_event_friction_fronts(value,_settings(),maximum_axial_uncertainty=1e-7)
    except Exception as error:
        (folder/'boundary_ending_failure.json').write_text(json.dumps(dict(error_type=type(error).__name__,
            error=str(error),diagnostics=getattr(error,'integration_diagnostics',None),
            elapsed_seconds=time.perf_counter()-start),indent=2),encoding='utf-8')
        raise
    # Final section phase is zero. All closed points slide in +y; independent
    # triangular linear pressure integral uses the physical final cylinder.
    root=lambda delta:(.03*np.cos(delta)-.035)/.01
    exact=.03*.3*1000*quad(lambda delta:.5*.01*(root(delta)+.8)**2,-.02,.02,epsabs=1e-14)[0]
    derivative=-.03*.3*1000*quad(lambda delta:root(delta)+.8,-.02,.02,epsabs=1e-14)[0]
    y=np.zeros(60);y[[1,7,13]]=1.;z=np.zeros(60);z[[2,8,14]]=1.
    force=float(y@result.residual);tangent=float(y@result.tangent@z)
    balance=sum((result.residual[6*i:6*i+3] for i in range(3)),np.zeros(3))
    balance+=sum((result.residual[42+6*i:45+6*i] for i in range(3)),np.zeros(3))
    record=dict(elapsed_seconds=time.perf_counter()-start,diagnostics=result.diagnostics,force=force,
        reference_force=exact,tangent=tangent,reference_tangent=derivative,balance=balance.tolist(),
        work=dict(stored=result.stored_energy_j,dissipated=result.dissipated_increment_j,
            released=result.released_storage_j,cumulative=result.cumulative_dissipation_j))
    (folder/'boundary_ending_result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    assert force==pytest.approx(exact,rel=1e-5,abs=1e-10)
    assert tangent==pytest.approx(derivative,rel=1e-5,abs=1e-8)
    np.testing.assert_allclose(balance,0.,atol=1e-12,rtol=0.)
    assert result.stored_energy_j>0 and result.dissipated_increment_j>0
    assert result.diagnostics['maximum_scaled_error_estimate']<=1.
