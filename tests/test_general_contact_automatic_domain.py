"""Declared-domain precedence/role/refusal and actual ordinary restart checks."""
from dataclasses import replace,asdict
import json,os
from pathlib import Path
import numpy as np
import pytest

from anysolver import FEModel,BoundaryCondition,create_shell_element
from anysolver.general_contact import (ContactSurface,ContactInteraction,RigidContactBody,ContactSolverSettings,
    AutomaticContactParticipant as Participant,AutomaticContactDefaults as Defaults,
    AutomaticContactDomain as Domain,AutomaticContactDomainError,
    resolve_automatic_contact_domain as resolve,verify_automatic_contact_resolution as verify)
from examples.general_contact_automatic_domain import build,solve


def shell_pair(*,size_a=2.,size_b=1.):
    model=FEModel('role-reference')
    model.add_material('elastic',1e5,.3,density=1.)
    for face,(size,z) in enumerate(((size_a,.1),(size_b,0.))):
        nodes=[]
        for local,(x,y) in enumerate(((0.,0.),(size,0.),(size,size),(0.,size))):
            node=4*face+local+1;nodes.append(node);model.add_node(node,x,y,z)
        model.add_element(face+1,create_shell_element(face+1,nodes,'elastic',thickness=.01))
    model.add_boundary_condition(BoundaryCondition('guides',tuple(range(1,9)),
        {name:0. for name in ('ux','uy','rx','ry','rz')}))
    domain=Domain('two-shells',(
        Participant(ContactSurface('a',(1,),side='bottom'),'body-a'),
        Participant(ContactSurface('b',(2,),side='top'),'body-b')),Defaults(1e5,.001))
    return model,domain,ContactSolverSettings()


def test_complete_pairing_precedence_permutation_and_identity():
    model,_,domain,settings,baseline=build()
    assert len(baseline.definition.interactions)==2
    assert [r.disposition for r in baseline.selections].count('outside_family')==1
    assert all(pair.surface=='skin' for pair in baseline.definition.interactions)
    assert all(baseline.identity in pair.name for pair in baseline.definition.interactions)
    reversed_domain=replace(domain,participants=tuple(reversed(domain.participants)))
    assert resolve(model,reversed_domain,settings)==baseline
    explicit=ContactInteraction('user-name','skin','floor',2e6,2e-6)
    overridden=resolve(model,replace(domain,pair_overrides=(explicit,)),settings,explicit_pairs=(explicit,))
    row=next(row for row in overridden.selections if row.target=='floor')
    assert row.original_interaction_name=='user-name'
    pair=next(pair for pair in overridden.definition.interactions if pair.target=='floor')
    assert pair.normal_stiffness==2e6 and pair.gap_tolerance==2e-6
    excluded=resolve(model,replace(domain,excluded_pairs=(('floor','skin'),),pair_overrides=(explicit,)),settings)
    assert len(excluded.definition.interactions)==1
    assert next(row for row in excluded.selections if row.participants==('floor','skin')).disposition=='excluded'
    assert len(resolve(model,domain,settings).definition.interactions)==2  # complete even initially open/inactive
    with pytest.raises(AutomaticContactDomainError,match='conflict'):
        resolve(model,replace(domain,pair_overrides=(explicit,replace(explicit,normal_stiffness=3e6))),settings)
    # Exclusion suppresses even conflicting mechanical overrides, whose full
    # input provenance remains hashed; unknown declarations still refuse.
    suppressed=replace(domain,excluded_pairs=(('floor','skin'),),pair_overrides=(explicit,replace(explicit,normal_stiffness=3e6)))
    assert len(resolve(model,suppressed,settings).definition.interactions)==1
    with pytest.raises(AutomaticContactDomainError,match='no pairs dropped'):
        resolve(model,replace(domain,maximum_pairs=1),settings)
    for changed in (replace(domain,name='changed'),replace(domain,defaults=Defaults(2e6,1e-6))):
        assert resolve(model,changed,settings).identity!=baseline.identity
    assert resolve(model,domain,replace(settings,maximum_candidate_pairs=200)).identity!=baseline.identity


def test_coarser_median_reference_role_and_stable_tie():
    model,domain,settings=shell_pair()
    result=resolve(model,domain,settings)
    row=result.selections[0]
    assert (row.source,row.target)==('a','b')
    assert row.source_reference_median_area_m2==pytest.approx(4.)
    assert row.target_reference_median_area_m2==pytest.approx(1.)
    # Explicit orientation is never reversed to recover an executable profile.
    explicit=ContactInteraction('explicit','b','a',1e5,.001)
    result=resolve(model,domain,settings,explicit_pairs=(explicit,))
    assert result.definition.interactions[0].surface=='b'
    model,domain,settings=shell_pair(size_a=1.,size_b=1.)
    result=resolve(model,replace(domain,participants=tuple(reversed(domain.participants))),settings)
    assert result.definition.interactions[0].surface=='a'


def test_q4_bilinear_area_is_not_diagonal_area():
    from anysolver.general_contact.automatic_domain import _face_area
    corners=np.array(((0.,0.,0.),(1.,0.,0.),(1.,1.,.3),(0.,1.,0.)))
    # Independent graph z=.3*x*y on unit square, high-order 1D quadrature product.
    nodes,weights=np.polynomial.legendre.leggauss(40);x=(nodes+1)/2
    expected=sum(wx*wy*np.sqrt(1+.09*(a*a+b*b)) for a,wx in zip(x,weights/2) for b,wy in zip(x,weights/2))
    diagonal=.5*np.linalg.norm(np.cross(corners[1]-corners[0],corners[2]-corners[0]))+.5*np.linalg.norm(np.cross(corners[2]-corners[0],corners[3]-corners[0]))
    assert _face_area(corners)==pytest.approx(expected,rel=1e-12)
    assert abs(expected-diagonal)>1e-3


def test_exact_equal_q4_s3_area_role_and_rigid_transform():
    from anysolver.general_contact.automatic_domain import _face_area,_coarser_source
    q4=np.array(((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)))
    s3=np.array(((0.,0.,0.),(2.,0.,0.),(0.,1.,0.)))
    rotation=np.array(((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)))
    for r,shift in ((np.eye(3),np.zeros(3)),(rotation,np.array((7.,-4.,2.)))):
        areas={'a-s3':_face_area(s3@r.T+shift),'z-q4':_face_area(q4@r.T+shift)}
        assert areas['a-s3']==areas['z-q4']==1.
        assert _coarser_source(('z-q4','a-s3'),areas)=='a-s3'


def test_reference_fold_nonfinite_and_degenerate_refusal():
    from anysolver.general_contact.automatic_domain import _face_area
    for corners in (
        ((0.,0.,0.),(1.,1.,0.),(1.,0.,0.),(0.,1.,0.)),
        ((0.,0.,0.),(1.,0.,0.),(2.,0.,0.),(3.,0.,0.)),
        ((0.,0.,0.),(1.,0.,0.),(1.,float('nan'),0.),(0.,1.,0.)),
        ((0.,0.,0.),(1.,0.,0.),(2.,0.,0.))):
        with pytest.raises(AutomaticContactDomainError):_face_area(corners)


def test_s3_formulation_owned_selected_skin_offset():
    model=FEModel('s3-reference-offset');model.add_material('elastic',1e5,.3,density=1.)
    for node,point in enumerate(((0.,0.,.035),(1.,0.,.035),(0.,1.,.035)),1):model.add_node(node,*point)
    model.add_element(1,create_shell_element(1,(1,2,3),'elastic',formulation='e4-pl-s3-v2d',thickness=.05,
                          reference_normal=(0.,0.,1.),reference_surface_offset=.01))
    domain=Domain('s3-floor',(
        Participant(ContactSurface('selected',(1,),side='bottom'),'s3-body'),
        Participant(RigidContactBody('floor','plane',(0.,0.,0.),(0.,0.,1.)),'tool-body')),Defaults(1e6,1e-6))
    result=resolve(model,domain)
    row=next(r for r in json.loads(result.reference_json) if r['name']=='selected')
    assert row['faces'][0]['reference_positions_m'][0][2]==pytest.approx(.035-.025-.01)
    assert row['faces'][0]['reference_area_m2']==pytest.approx(.5)


def test_physical_skin_binding_median_and_persistence():
    from anysolver.general_contact.automatic_domain import _reference,_coarser_source
    model=FEModel('median-not-total');model.add_material('elastic',1e5,.3,density=1.)
    participants=[];eid=0
    for name,count,area,z in (('many-fine',2,.5,.1),('one-coarse',1,.75,0.)):
        ids=[]
        for face in range(count):
            eid+=1;side=np.sqrt(area);nodes=[]
            for local,(x,y) in enumerate(((0.,0.),(side,0.),(side,side),(0.,side))):
                node=4*(eid-1)+local+1;nodes.append(node);model.add_node(node,x+face,y,z)
            model.add_element(eid,create_shell_element(eid,nodes,'elastic',thickness=.05));ids.append(eid)
        participants.append(Participant(ContactSurface(name,tuple(ids),side='bottom'),name+'-body'))
    rows,areas=_reference(model,tuple(participants))
    assert _coarser_source(tuple(areas),areas)=='one-coarse'
    assert sum(face['reference_area_m2'] for face in rows[0]['faces'])>sum(face['reference_area_m2'] for face in rows[1]['faces'])
    assert rows[0]['faces'][0]['reference_positions_m'][0][2]==pytest.approx(.075)
    model,_,domain,settings,result=build()
    assert Domain.from_dict(json.loads(json.dumps(domain.to_dict())))==domain
    malformed=domain.to_dict();malformed['unknown']=1
    with pytest.raises(AutomaticContactDomainError):Domain.from_dict(malformed)
    explicit=tuple(ContactInteraction('original-'+target,'skin',target,2e6,2e-6) for target in ('floor','second-floor'))
    all_explicit=replace(domain,pair_overrides=explicit)
    baseline=resolve(model,all_explicit,settings)
    changed=resolve(model,replace(all_explicit,defaults=Defaults(3e6,2e-6)),settings)
    assert baseline.identity!=changed.identity
    assert [asdict(p)|{'name':''} for p in baseline.definition.interactions]==[asdict(p)|{'name':''} for p in changed.definition.interactions]
    with pytest.raises(AutomaticContactDomainError):verify(model,replace(all_explicit,pair_overrides=()),baseline,settings)
    changed_definition=replace(result.definition,interactions=(replace(result.definition.interactions[0],normal_stiffness=2e6),*result.definition.interactions[1:]))
    poisoned=replace(result,definition=changed_definition,definition_json=json.dumps(asdict(changed_definition),sort_keys=True,separators=(',',':')))
    with pytest.raises(AutomaticContactDomainError):verify(model,domain,poisoned,settings)
    poisoned=replace(result,selections=tuple(replace(row,reason='changed') for row in result.selections))
    with pytest.raises(AutomaticContactDomainError):verify(model,domain,poisoned,settings)
    with pytest.raises(AutomaticContactDomainError):resolve(model,replace(domain,excluded_pairs=(('floor','second-floor'),)),settings)


def test_refusals_and_fixed_reference_binding():
    model,_,domain,settings,result=build()
    assert verify(model,domain,result,settings)==result.definition
    with pytest.raises(AutomaticContactDomainError):
        replace(domain,excluded_pairs=(('unknown','skin'),))
    with pytest.raises(AutomaticContactDomainError):
        replace(domain,participants=domain.participants+(domain.participants[0],))
    with pytest.raises(AutomaticContactDomainError):
        resolve(model,domain,settings,explicit_pairs=(ContactInteraction('bad','floor','skin',1e5,.001),))
    with pytest.raises(AutomaticContactDomainError):
        resolve(model,domain,settings,explicit_pairs=(ContactInteraction('bad','skin','unknown',1e5,.001),))
    with pytest.raises(AutomaticContactDomainError):
        verify(model,replace(domain,defaults=Defaults(2e6,1e-6)),result,settings)
    with pytest.raises(AutomaticContactDomainError):
        verify(model,domain,result,replace(settings,maximum_candidate_pairs=200))
    model.mesh.nodes[3].x+=.01
    with pytest.raises(AutomaticContactDomainError,match='changed'):
        verify(model,domain,result,settings)
    model,domain,settings=shell_pair()
    same=replace(domain,participants=tuple(replace(p,body_id='one-body') for p in domain.participants))
    with pytest.raises(AutomaticContactDomainError,match='self-contact'):
        resolve(model,same,settings)
    with pytest.raises(AutomaticContactDomainError,match='no executable'):
        resolve(model,replace(same,excluded_pairs=(('a','b'),)),settings)
    beam=replace(domain,participants=(replace(domain.participants[0],participant=ContactSurface('a',(1,),beam_radius=.01)),domain.participants[1]))
    with pytest.raises(AutomaticContactDomainError,match='beam/native'):
        resolve(model,beam,settings)


def test_actual_nonlinear_static_restart_and_provenance_refusal():
    model,load,domain,settings,resolution=build()
    half=solve(model,load,domain,settings,resolution,max_load_factor=.5,emit_restart_checkpoint=True)
    assert half.status=='completed',half.failure_reason
    capsule=half.to_restart_checkpoint()
    resumed=solve(model,load,domain,settings,resolution,restart_checkpoint=capsule,emit_restart_checkpoint=True)
    full=solve(model,load,domain,settings,resolution,emit_restart_checkpoint=True)
    report=dict(identity=resolution.identity,half_status=half.status,resumed_status=resumed.status,full_status=full.status,
                contact=resumed.info.get('general_contact'),checkpoint=capsule)
    mapping={row.compiled_interaction_name:row.target for row in resolution.selections if row.disposition=='resolved'}
    pair_errors={}
    for pair in resumed.info['general_contact']['pairs']:
        target=mapping[pair['interaction']];contact=pair['contact']
        force=.25 if target=='floor' else .15
        expected_force=np.array((0.,0.,force));expected_moment=np.array((.5*force,-.5*force,0.))
        errors=dict(shell_force=float(np.linalg.norm(np.array(contact['shell_force'])-expected_force)/.4),
                    rigid_force=float(np.linalg.norm(np.array(contact['rigid_force'])+expected_force)/.4),
                    shell_moment=float(np.linalg.norm(np.array(contact['shell_moment'])-expected_moment)/.4),
                    rigid_moment=float(np.linalg.norm(np.array(contact['rigid_moment'])+expected_moment)/.4))
        pair_errors[target]=dict(compiled_name=pair['interaction'],expected_force_n=expected_force,
                                expected_moment_nm=expected_moment,normalized_errors=errors,
                                actual={name:contact[name] for name in ('shell_force','rigid_force','shell_moment','rigid_moment')})
    report['pair_resultants_about_global_origin']=pair_errors
    if os.environ.get('AUTOMATIC_DOMAIN_RESULT'):
        Path(os.environ['AUTOMATIC_DOMAIN_RESULT']).write_text(json.dumps(report,indent=2,default=lambda x:x.tolist()),encoding='utf-8')
    assert resumed.status==full.status=='completed'
    assert set(pair_errors)=={'floor','second-floor'}
    assert max(error for row in pair_errors.values() for error in row['normalized_errors'].values())<=1e-6
    assert resumed.info['general_contact']['penalty_energy']>0
    assert resumed.info['general_contact']['gap_tolerance_met']
    # Two distinct parallel tools separated by1e-7m: their pressure difference
    # k*delta=0.1N; total prescribed force0.4N gives resultants0.25N/0.15N.
    assert resumed.info['general_contact']['shell_force'][2]==pytest.approx(.4,abs=1e-8)
    expected_gap=-(.4+1e6*1e-7)/(2e6)
    assert resumed.info['general_contact']['minimum_gap']==pytest.approx(expected_gap,abs=1e-10)
    np.testing.assert_allclose(resumed.displacements,full.displacements,rtol=1e-8,atol=1e-10)
    changed=replace(domain,name='new-provenance')
    changed_resolution=resolve(model,changed,settings)
    with pytest.raises(ValueError,match='incompatible'):
        solve(model,load,changed,settings,changed_resolution,restart_checkpoint=capsule)


def test_oblique_rigid_component_persistence_is_bit_exact():
    model,_,domain,settings,_=build()
    for kind in ('plane','cylinder'):
        body=RigidContactBody('oblique',kind,(0.,0.,-.025),(1.,1.,0.),radius=.2 if kind=='cylinder' else None)
        selected=replace(domain,participants=(domain.participants[-1],Participant(body,'oblique-body')))
        stored=selected.to_dict()
        restored=Domain.from_dict(json.loads(json.dumps(stored)))
        assert restored.to_dict()==stored
        assert restored==selected
        if kind=='plane':
            resolution=resolve(model,restored,settings)
            assert resolution.identity==resolve(model,selected,settings).identity
            assert verify(model,restored,resolution,settings)==resolution.definition
        for invalid in ((2.,2.,0.),(float('nan'),1.,0.),('1',0.,0.),(1.,0.)):
            malformed=json.loads(json.dumps(stored))
            rigid=next(row for row in malformed['participants'] if row['kind']=='rigid')
            rigid['participant']['normal']=invalid
            with pytest.raises(AutomaticContactDomainError):Domain.from_dict(malformed)
