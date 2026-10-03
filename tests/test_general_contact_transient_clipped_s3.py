"""Moving clipped overlap: independent plane/complex-step/Newmark reference.

Reference clipping uses direct target planar barycentrics and a separate complex
analytic polygon integration. No production geometry/pressure kernel is called.
Accepted structural stiffness is input; small-motion structural differences are
bounded by the response check, not independently qualified by this fixture.
"""
from pathlib import Path
import json,os,runpy
import numpy as np
import pytest
from scipy.optimize import root
from anysolver import TransientConfig,solve_transient_contact
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.assembly import assemble_mass_matrix
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.runtime import active_contact_manager
from anysolver.nonlinear_restart import model_configuration_fingerprint

demo=runpy.run_path(str(Path(__file__).parents[1]/'examples/general_contact_deforming_s3_impact_dev.py'))
TARGET_XY=np.array([[-2.,-2.],[.6,-2.],[.6,3.]])
SOURCE_XY=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
INITIAL=np.array([-1.e-4,1.e-4,1.e-4,-1.e-4,0.,0.,0.])
MASS=np.diag(np.r_[20.*demo['SUPPORT'],np.full(3,13./3)])
FACES=((0,1,2),(0,2,3))


def layout(columns):
    xy=np.array([(i/columns,0.) for i in range(columns+1)]
                +[(i/columns,1.) for i in range(columns,-1,-1)])
    faces=[];weights=np.zeros(len(xy))
    for i in range(columns):
        for face in ((i,i+1,2*columns-i),(i,2*columns-i,2*columns+1-i)):
            faces.append(face);weights[list(face)]+=1/(6*columns)
    mass=np.diag(np.r_[20.*weights,np.full(3,13./3)])
    initial=np.r_[2.e-4*xy[:,0]-1.e-4,np.zeros(3)]
    return xy,tuple(faces),mass,initial


def moments(q,columns=1):
    """Original P1 reference moments on direct complex projected polygons."""
    dtype=np.result_type(q,float)
    xy,faces,_,_=layout(columns);count=len(xy)
    source=np.column_stack((xy,np.full(count,.0102))).astype(dtype)
    source[:,2]+=q[:count]
    target=np.column_stack((TARGET_XY,.01+q[count:])).astype(dtype)
    plane=np.linalg.solve(np.column_stack((np.ones(3),TARGET_XY)),target[:,2])
    W=np.zeros(count,dtype=dtype);S=np.zeros(count,dtype=dtype);minimum=[]
    for face in faces:
        ids=np.array(face);nodes=source[ids]
        reference_edges=xy[ids[1:]]-xy[ids[0]]
        reference_jacobian=np.linalg.det(reference_edges)
        n=np.cross(nodes[1]-nodes[0],nodes[2]-nodes[0]);n/=np.sqrt(n@n)
        g=(nodes[:,2]-plane[0]-nodes[:,:2]@plane[1:])/(n[2]-plane[1:]@n[:2])
        projected=nodes-np.outer(g,n)
        local=np.linalg.solve((TARGET_XY[1:]-TARGET_XY[0]).T,
                              (projected[:,:2]-TARGET_XY[0]).T).T
        coefficients=np.column_stack((1-local.sum(axis=1),local))
        polygon=list(np.eye(3,dtype=dtype))
        for edge in range(3):
            if not polygon:break
            output=[];previous=polygon[-1];pv=previous@coefficients[:,edge]
            for current in polygon:
                cv=current@coefficients[:,edge]
                if (pv.real>=0)!=(cv.real>=0):
                    output.append(previous+(current-previous)*pv/(pv-cv))
                if cv.real>=0:output.append(current)
                previous,pv=current,cv
            polygon=output
        for i in range(1,len(polygon)-1):
            shapes=np.array([polygon[0],polygon[i],polygon[i+1]])
            d=shapes[1:,1:]-shapes[0,1:]
            area=.5*(d[0,0]*d[1,1]-d[0,1]*d[1,0])*reference_jacobian
            gv=shapes@g
            S[ids]+=area*shapes.sum(axis=0)/3
            W[ids]+=area*(shapes.sum(axis=0)*gv.sum()+shapes.T@gv)/12
        if polygon:minimum.extend((np.asarray(polygon)@g).real.tolist())
    supported=S.real>0.
    normalized=np.zeros_like(W);normalized[supported]=W[supported]/S[supported]
    return normalized,S,min(minimum)


def response(q,columns=1,normal_stiffness=None):
    q=np.asarray(q,dtype=float);g,S,_=moments(q,columns)
    D=np.zeros((len(g),len(q)))
    if not np.any(g<0.):return np.zeros_like(q),np.zeros((len(q),len(q)))
    for i in range(len(q)):
        value=q.astype(complex);value[i]+=1.e-26j
        D[:,i]=moments(value,columns)[0].imag/1.e-26
    stiffness=demo['KN'] if normal_stiffness is None else normal_stiffness
    return (stiffness*D.T@(S*np.minimum(g,0.)),
            stiffness*D.T@np.diag(S*(g<0.))@D)


def contact_force(q,columns=1,normal_stiffness=None):
    return response(q,columns,normal_stiffness)[0]


def reference(times,K,columns=1,normal_stiffness=None):
    _,_,mass,q=layout(columns);v=np.r_[np.full(len(q)-3,-.1),np.zeros(3)]
    a=np.linalg.solve(mass,-K@q-contact_force(q,columns,normal_stiffness));rows=[(q.copy(),v.copy(),a.copy())]
    for h in np.diff(times):
        beta=.25*h*h;predictor=q+h*v+beta*a
        cached=None;cached_response=None
        def state(value):
            nonlocal cached,cached_response
            position=predictor+beta*value
            if cached is None or not np.array_equal(position,cached):
                cached=position.copy();cached_response=response(position,columns,normal_stiffness)
            return position,cached_response
        def residual(value):
            position,(force,_)=state(value)
            return mass@value+K@position+force
        def jacobian(value):
            _,(_,approximate)=state(value)
            # Only a root preconditioner; full moving-support force remains in
            # every residual and the reference equilibrium criterion is unchanged.
            return mass+beta*(K+approximate)
        solution=root(residual,a,jac=jacobian,method='hybr',options={'xtol':1.e-10})
        assert np.linalg.norm(residual(solution.x))<=1.e-9*max(1.,np.linalg.norm(mass@solution.x))
        next_a=solution.x;q=predictor+beta*next_a
        v+=.5*h*(a+next_a);a=next_a
        rows.append((q.copy(),v.copy(),a.copy()))
    return np.asarray(rows)


def test_clipped_contact_work_and_tangent_match_independent_polygon_oracle():
    model,definition,modes=demo['build_model'](target_xy=TARGET_XY)
    settings=demo['_fixture']['SETTINGS']
    manager=GeneralS3PatchManager(model,definition,settings)
    q=np.array([-.000218,-.000213,-.000215,-.000216,-.000004,-.000003,-.000005])
    force,K,result=manager.evaluate(modes@q,tangent=True)
    g,S,minimum=moments(q)
    np.testing.assert_allclose(result.normalized_weighted_gap_m,g,rtol=0.,atol=2.e-16)
    np.testing.assert_allclose(result.reference_support_m2,S,rtol=0.,atol=2.e-15)
    np.testing.assert_allclose(modes.T@force,contact_force(q),rtol=2.e-10,atol=1.e-6)
    assert abs(result.sampled_overlap_gap-minimum)<2.e-15
    direction=np.array([.1,-.2,.3,-.4,.2,.1,-.2])
    for step in (1.e-8,3.e-8,1.e-7):
        independent=(contact_force(q+step*direction)-contact_force(q-step*direction))/(2*step)
        actual=modes.T@K@modes@direction
        assert np.linalg.norm(actual-independent)/max(1.,np.linalg.norm(independent))<=1.e-5


def test_coarse_pressure_mesh_gap_failure_has_independent_spatial_discriminator():
    model,_,modes=demo['build_model'](target_xy=TARGET_XY)
    K=modes.T@assemble_stiffness_matrix(model)[0]@modes
    times=np.arange(51)*2.5e-5
    trajectory=reference(times,K)
    fields=[moments(q) for q in trajectory[:,0]]
    min_gap=np.array([field[2] for field in fields])
    violation=np.flatnonzero(min_gap<-2.e-5)
    assert violation.size
    first=int(violation[0]);g=fields[first][0]
    record=dict(source_columns=1,first_physical_gap_violation_s=float(times[first]),
        minimum_matched_gap_m=float(min_gap[first]),weighted_pressure_gaps_m=g.tolist(),
        active_pressure_modes=int(np.count_nonzero(g<0.)),gap_budget_m=2.e-5)
    Path(os.environ['RUNNER_TEMP'],'coarse_clipped_gap_discriminator.json').write_text(json.dumps(record,indent=2))
    assert record['active_pressure_modes']==0


def test_refined_clipped_gap_failure_has_independent_enforcement_discriminator():
    """Resolve the remaining hypothesis without replaying a failed owner run."""
    columns=8
    model,_,modes=demo['build_model'](target_xy=TARGET_XY,source_columns=columns)
    K=modes.T@assemble_stiffness_matrix(model)[0]@modes
    times=np.arange(51)*2.5e-5
    trajectory=reference(times,K,columns)
    fields=[moments(q,columns) for q in trajectory[:,0]]
    violation=np.flatnonzero(np.array([field[2] for field in fields])<-2.e-5)
    assert violation.size
    first=int(violation[0]);g,S,minimum=fields[first]
    record=dict(source_columns=columns,normal_stiffness_pa_per_m=demo['KN'],
        first_physical_gap_violation_s=float(times[first]),minimum_matched_gap_m=float(minimum),
        weighted_pressure_gaps_m=g.tolist(),reference_support_m2=S.tolist(),
        active_pressure_modes=int(np.count_nonzero(g<0.)),gap_budget_m=2.e-5,
        normal_coordinates_m=trajectory[first,0].tolist())
    Path(os.environ['RUNNER_TEMP'],'refined_clipped_gap_discriminator.json').write_text(json.dumps(record,indent=2))
    assert record['active_pressure_modes']>0


def test_independent_polygon_reference_measure_is_mesh_invariant():
    """Flat overlap has independently known physical area 0.6*1."""
    areas=[]
    for columns in (1,2,8):
        _,_,_,initial=layout(columns)
        initial[:]=0.
        g,S,minimum=moments(initial,columns)
        areas.append(float(S.sum()))
        np.testing.assert_allclose(g[S>0.],.0002,rtol=0.,atol=5.e-18)
        assert abs(minimum-.0002)<5.e-18
    # Left target edge crosses y=0 at x=-.96 and y=1 at x=-1.48;
    # both are outside the source. Thus the source overlap is exactly [0,.6]x[0,1].
    np.testing.assert_allclose(areas,.6,rtol=0.,atol=4.e-16)


def test_explicit_stiffer_penalty_clipped_reference_preflight():
    columns=8;stiffness=2.e10
    model,_,modes=demo['build_model'](target_xy=TARGET_XY,source_columns=columns,
        normal_stiffness=stiffness)
    K=modes.T@assemble_stiffness_matrix(model)[0]@modes
    times=np.arange(121)*2.5e-5
    trajectory=reference(times,K,columns,stiffness)
    minimum=min(moments(q,columns)[2] for q in trajectory[:,0])
    record=dict(source_columns=columns,normal_stiffness_pa_per_m=stiffness,
        dt_s=2.5e-5,end_s=.003,minimum_matched_gap_m=float(minimum),gap_budget_m=2.e-5)
    Path(os.environ['RUNNER_TEMP'],'stiffer_clipped_reference_preflight.json').write_text(json.dumps(record,indent=2))
    assert minimum>=-2.e-5


def test_moving_clipped_overlap_with_explicit_enforcement_matches_coupled_reference():
    columns=8;stiffness=2.e10;_,_,mass,initial=layout(columns)
    model,definition,modes=demo['build_model'](target_xy=TARGET_XY,source_columns=columns,
        normal_stiffness=stiffness)
    fingerprint=model_configuration_fingerprint(model)
    # Preserve legacy static guard. It rejects a remote Cartesian corner at
    # this open matched pose; the new driver must validate its own actual pose.
    with pytest.raises(ValueError,match='initial penetration'):
        GeneralS3PatchManager(model,definition,demo['_fixture']['SETTINGS'],initial_displacement=modes@initial)
    result=solve_transient_contact(model,definition,
        TransientConfig(2.5e-5,.003,initial_displacement=modes@initial,
            initial_velocity=modes@np.r_[np.full(len(initial)-3,-.1),np.zeros(3)]),
        contact_settings=demo['_fixture']['SETTINGS'],solver_controls=demo['CONTROLS'])
    q,v,a=(np.asarray(values)@modes for values in (result.displacements,result.velocities,result.accelerations))
    K=modes.T@assemble_stiffness_matrix(model)[0]@modes
    np.testing.assert_allclose(modes.T@assemble_mass_matrix(model)[0]@modes,mass,rtol=1.e-14,atol=1.e-14)
    expected=reference(result.times,K,columns,stiffness)
    g=np.asarray([moments(value,columns)[0] for value in q])
    support=np.asarray([moments(value,columns)[1] for value in q])
    gap=np.asarray([moments(value,columns)[2] for value in q])
    observed=np.asarray([row.normalized_weighted_gap_m for row in result.contact])
    record=dict(profile=result.profile,times_s=result.times.tolist(),states=len(result.times),
        source_columns=columns,normal_coordinates=len(initial),
        normal_stiffness_pa_per_m=stiffness,
        initial_normal_coordinates_m=initial.tolist(),target_xy_m=TARGET_XY.tolist(),
        max_displacement_error_m=float(np.max(np.abs(q-expected[:,0]))),
        max_velocity_error_m_s=float(np.max(np.abs(v-expected[:,1]))),
        max_acceleration_error_m_s2=float(np.max(np.abs(a-expected[:,2]))),
        max_pressure_gap_error_m=float(np.max(np.abs(g-observed))),
        reference_overlap_area_range_m2=[float(support.sum(axis=1).min()),float(support.sum(axis=1).max())],
        independent_minimum_gap_m=float(gap.min()),swept_minimum_gap_m=float(min(result.swept_minimum_gaps)),
        maximum_momentum_error_kg_m_s=float(np.max(np.abs(v@np.diag(mass)-v[0]@np.diag(mass)))),
        active_states=sum(row.active_pressure_dofs>0 for row in result.contact),
        localized_events_s=result.localized_contact_event_times,cutbacks=result.cutbacks,
        endpoint_queries=result.event_endpoint_evaluations,stage_evaluations=result.plane_event_stage_evaluations)
    Path(os.environ['RUNNER_TEMP'],'clipped_s3_coupled.json').write_text(json.dumps(record,indent=2))
    assert record['max_displacement_error_m']<=2.e-10
    assert record['max_velocity_error_m_s']<=2.e-6
    assert record['max_acceleration_error_m_s2']<=.02
    assert record['max_pressure_gap_error_m']<=2.e-16
    assert record['reference_overlap_area_range_m2'][1]-record['reference_overlap_area_range_m2'][0]>1.e-9
    assert record['active_states']>0 and record['localized_events_s']
    assert record['independent_minimum_gap_m']>=-2.e-5
    assert record['swept_minimum_gap_m']>=-2.e-5
    assert record['maximum_momentum_error_kg_m_s']<=1.e-9
    assert active_contact_manager() is None and model_configuration_fingerprint(model)==fingerprint


def test_refined_clipped_production_work_matches_reference_measure():
    columns=8;stiffness=2.e10;xy,_,_,q=layout(columns)
    q[:len(xy)]-=.00022
    model,definition,modes=demo['build_model'](target_xy=TARGET_XY,source_columns=columns,
        normal_stiffness=stiffness)
    manager=GeneralS3PatchManager(model,definition,demo['_fixture']['SETTINGS'])
    force,_,result=manager.evaluate(modes@q,tangent=False)
    g,S,_=moments(q,columns)
    np.testing.assert_allclose(result.normalized_weighted_gap_m,g,rtol=0.,atol=3.e-16)
    np.testing.assert_allclose(result.reference_support_m2,S,rtol=0.,atol=2.e-15)
    np.testing.assert_allclose(modes.T@force,contact_force(q,columns,stiffness),rtol=2.e-10,atol=2.e-6)


def test_fresh_matched_penetration_is_rejected_even_within_step_gap_budget():
    model,definition,modes=demo['build_model']()
    initial=modes@np.r_[np.full(4,-.0002001),np.zeros(3)]
    with pytest.raises(ValueError,match='initial matched penetration'):
        solve_transient_contact(model,definition,TransientConfig(2.5e-5,.0001,initial_displacement=initial,
            initial_velocity=np.zeros(modes.shape[0])),
            contact_settings=demo['_fixture']['SETTINGS'],solver_controls=demo['CONTROLS'])
    assert active_contact_manager() is None
