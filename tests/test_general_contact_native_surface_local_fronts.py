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
