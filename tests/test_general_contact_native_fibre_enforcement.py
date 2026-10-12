"""Bounded enforcement sensitivity of the fixed curved physical-fibre fixture.

Successive penalty responses are development evidence, not an independent
continuum solution or a zero-penetration convergence certificate.
"""
from pathlib import Path
from hashlib import sha256
from math import atan2,ceil,floor,pi,fsum
import json,os
import numpy as np
import pytest
from scipy.optimize import minimize_scalar
from test_general_contact_native_curved_s3_static import _analysis
from test_general_contact_native_surface_bounds import _independent_point
from test_general_contact_native_curved_s3_work import _corners

DATA=Path(__file__).parent/'data'
BASE='general_contact_native_fibre_s3_plastic_active_v1.checkpoint'
CURRENT_ENFORCEMENT_SOURCE='general_contact_native_fibre_s3_plastic_certified_k4e7_v1.checkpoint'
RESPONSE_TARGET=.02


def _gap(owner,state,points):
    """Independent analytic parabola/circle; sampled and bracket-refined xi.

    Angular minima are analytic. This supplements the production whole-patch
    enclosure; sampling/refinement alone is not a conservative global certificate.
    """
    work=owner.pairs[0].work;corners=_corners(work,state.shell_displacement)
    normal=np.cross(corners[1]-corners[0],corners[2]-corners[0]);normal/=np.linalg.norm(normal)
    lo,hi=work.contact.rule.definition['xi_range'];al,ar=work.contact.rule.definition['angle_range']
    radius=.03;p=state.mechanical.positions;low=state.mechanical.position_low;rotations=state.mechanical.cell_rotations[0]
    def angular_minimum(xi):
        point=lambda angle:_independent_point(xi,angle+pi/2,radius,p,low,rotations,False)
        p0,pp,ph=point(0.),point(pi),point(pi/2)
        centre=(p0+pp)/2;A=normal@(centre-corners[0]);B=normal@((p0-pp)/2);C=normal@(ph-centre)
        candidates=[al,ar];phase=atan2(C,B)+pi
        for turn in range(ceil((al-phase)/(2*pi)),floor((ar-phase)/(2*pi))+1):candidates.append(phase+turn*2*pi)
        return min(float(A+B*np.cos(angle)+C*np.sin(angle)) for angle in candidates)
    x=np.linspace(lo,hi,points);values=np.array([angular_minimum(xi) for xi in x]);minimum=float(values.min())
    for i in range(1,len(x)-1):
        if values[i]<=values[i-1] and values[i]<=values[i+1]:
            refined=minimize_scalar(angular_minimum,bounds=(x[i-1],x[i+1]),method='bounded',options={'xatol':1e-12})
            assert refined.success
            minimum=min(minimum,float(refined.fun))
    return minimum


def _quantities(owner,state):
    tip=owner.context.node_ids.index(3)
    target=owner.shell_model.mesh.dof_manager.get_node_dofs(5)[2]
    return dict(contact_force_n=np.asarray(state.contact.contact.beam_force_n),
        contact_moment_nm=np.asarray(state.contact.contact.beam_moment_nm),
        tip_z_m=fsum((state.mechanical.positions[tip,2],state.mechanical.position_low[tip,2],
                     -owner.initial.mechanical.positions[tip,2])),
        target_z_m=float(state.shell_displacement[target]))


def _response_errors(coarse,fine):
    errors={}
    for key in coarse:
        norm=float(np.linalg.norm(fine[key]));assert norm>0.
        errors[key]=float(np.linalg.norm(np.asarray(fine[key])-coarse[key])/norm)
    return errors


def test_enforcement_coarse_independent_gap_and_fixture_preflight():
    raw=(DATA/BASE).read_bytes();owner=_analysis(physical_fibres=True,plastic_fibres=True)
    state,records=owner._restore(raw,sha256(raw).hexdigest())
    values=[_gap(owner,state,n) for n in (65,129)]
    assert abs(values[1]-values[0])<=1e-10
    assert values[1]>=-3e-5
    assert state.contact.contact.minimum_gap_m<=values[1]+1e-10
    assert owner._checkpoint(records)==raw
    quantities=_quantities(owner,state)
    assert all(np.linalg.norm(v)>0 for v in quantities.values())
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:Path(path+'-enforcement-preflight.json').write_text(json.dumps(dict(
        independent_gaps_m=values,production_gap_lower_m=state.contact.contact.minimum_gap_m,
        quantities={k:np.asarray(v).tolist() for k,v in quantities.items()}),indent=2))


@pytest.mark.parametrize('stiffness',(8e7,),ids=('k8e7',))
def test_native_fibre_enforcement_successive_response(stiffness):
    # The earlier 1e7->2e7 and 2e7->4e7 response nonpasses are retained
    # development evidence. This prospective refinement keeps the same
    # geometry, load, materials and 2% gate at the resolved enforcement level.
    _enforcement_case(stiffness,source_checkpoint=(DATA/CURRENT_ENFORCEMENT_SOURCE).read_bytes(),
        integration_budget_policy='certified_active',
        source_integration_budget_policy='certified_active')


def test_native_fibre_enforcement_seeded_successive_response():
    _enforcement_case(8e7,seeded=True,
        source_checkpoint=(DATA/CURRENT_ENFORCEMENT_SOURCE).read_bytes(),
        integration_budget_policy='certified_active',
        source_integration_budget_policy='certified_active')


def test_native_fibre_enforcement_seeded_saved_fine_successive_response():
    path=os.environ.get('CONTACT_ENFORCEMENT_SOURCE_CHECKPOINT')
    digest=os.environ.get('CONTACT_ENFORCEMENT_SOURCE_SHA256')
    if not path or not digest:
        pytest.skip('explicit saved fine checkpoint and hash required')
    raw=Path(path).read_bytes()
    assert sha256(raw).hexdigest()==digest
    _enforcement_case(4e7,seeded=True,source_checkpoint=raw)


def test_native_fibre_enforcement_saved_fine_certified_active():
    path=os.environ.get('CONTACT_ENFORCEMENT_SOURCE_CHECKPOINT')
    digest=os.environ.get('CONTACT_ENFORCEMENT_SOURCE_SHA256')
    if not path or not digest:
        pytest.skip('explicit saved fine checkpoint and hash required')
    raw=Path(path).read_bytes()
    assert sha256(raw).hexdigest()==digest
    _enforcement_case(4e7,seeded=True,source_checkpoint=raw,
        integration_budget_policy='certified_active')


def test_native_fibre_enforcement_saved_active_policy_next_refinement():
    path=os.environ.get('CONTACT_ENFORCEMENT_SOURCE_CHECKPOINT')
    digest=os.environ.get('CONTACT_ENFORCEMENT_SOURCE_SHA256')
    if not path or not digest:
        pytest.skip('explicit saved active-policy checkpoint and hash required')
    raw=Path(path).read_bytes()
    assert sha256(raw).hexdigest()==digest
    _enforcement_case(8e7,seeded=True,source_checkpoint=raw,
        integration_budget_policy='certified_active',source_integration_budget_policy='certified_active')


def _enforcement_case(stiffness,seeded=False,source_checkpoint=None,integration_budget_policy='full_reference',
                      source_integration_budget_policy='full_reference',root_tangent_enclosure_policy='spectral'):
    raw=(DATA/BASE).read_bytes() if source_checkpoint is None else source_checkpoint
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=stiffness,
        integration_budget_policy=integration_budget_policy,root_tangent_enclosure_policy=root_tangent_enclosure_policy)
    output=os.environ.get('CONTACT_APP_RESULT_RECORD')
    guess=None
    if seeded:
        source=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=stiffness/2,
            integration_budget_policy=source_integration_budget_policy)
        guess=owner.make_initial_guess(source,raw,sha256(raw).hexdigest())
        if output:Path(output+'-initial-guess-provenance.json').write_text(json.dumps(dict(
            fingerprint=guess.fingerprint,owner_identity=guess.owner_identity,
            structure_identity=guess.structure_identity,source_owner_identity=guess.source_owner_identity,
            source_checkpoint_sha256=guess.source_checkpoint_sha256),indent=2))
    run=owner.solve(stop_after=1,initial_guess=guess)
    if output:
        Path(output+'-enforcement.checkpoint').write_bytes(run.checkpoint)
        Path(output+'-enforcement-run.json').write_text(json.dumps(dict(stiffness_Pa_per_m=stiffness,seeded=seeded,
            integration_budget_policy=integration_budget_policy,
            source_integration_budget_policy=source_integration_budget_policy,
            root_tangent_enclosure_policy=root_tangent_enclosure_policy,
            status=run.status,failure=run.failure,completed=run.accepted.completed_targets,
            candidates=owner.candidate_evaluations,pair_evaluations=owner.pair_evaluations,
            contact_reuse_hits=owner.contact_reuse_hits,trial_failures=owner.curved_trial_failures),indent=2))
    assert run.status=='paused',run.failure
    assert run.accepted.completed_targets==1
    coarse=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=stiffness/2,
        integration_budget_policy=source_integration_budget_policy)
    state,_=coarse._restore(raw,sha256(raw).hexdigest())
    assert coarse.context.identity==owner.context.identity
    np.testing.assert_array_equal(coarse.shell_stiffness,owner.shell_stiffness)
    independent=_gap(owner,run.accepted,129)
    contact=run.accepted.contact.contact
    errors=_response_errors(_quantities(coarse,state),_quantities(owner,run.accepted))
    report=dict(stiffness_Pa_per_m=stiffness,previous_stiffness_Pa_per_m=stiffness/2,
        response_relative_errors=errors,response_target=RESPONSE_TARGET,
        production_gap_lower_m=contact.minimum_gap_m,independent_sampled_refined_gap_m=independent,
        previous_gap_lower_m=state.contact.contact.minimum_gap_m,
        quantities={k:np.asarray(v).tolist() for k,v in _quantities(owner,run.accepted).items()})
    if output:Path(output+'-enforcement-comparison.json').write_text(json.dumps(report,indent=2))
    assert contact.potential_j>0. and np.linalg.norm(contact.beam_force_n)>0.
    assert np.linalg.norm(contact.beam_force_n+contact.shell_force_n)/.005<=1e-6
    assert np.linalg.norm(contact.beam_moment_nm+contact.shell_moment_nm)/.010<=1e-6
    assert contact.minimum_gap_m>=-3e-5 and independent>=-3e-5
    assert contact.minimum_gap_m<=independent+1e-10
    assert contact.minimum_gap_m>state.contact.contact.minimum_gap_m
    with pytest.raises(ValueError,match='binding'):owner._restore(raw,sha256(raw).hexdigest())
    assert max(errors.values())<=RESPONSE_TARGET
