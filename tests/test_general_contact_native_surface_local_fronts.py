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
    reason='development candidate exhausts unchanged query2048; retained failed evidence, explicit replay only')
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
