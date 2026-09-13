"""Frozen fifteen-node numerical recovery inventory; bounded runner only.

Every node is self-contained. Reference matrices are reused only inside a node;
no scientific result from a different child is an input to this module.
"""
import ast
from dataclasses import fields, is_dataclass, replace, FrozenInstanceError
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys
from threading import Event, Thread
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'docs/reference_cases'))
from anysolver import _ge_beam3_g3c_affine_q4_recovery as candidate
from anysolver import _ge_beam3_g3c_affine_q4_registry as registry
import ge_beam3_q4_affine_numerical_checker as checker

SCIENTIFIC_RECORDS=[]
CONTRADICTIONS=[]
_FACADES={}
_RESULTS={}
_EXPECTED={}
SOURCES={
 'src/anysolver/e4_pl_element.py':'7fc46a18046e043512a5fb2c3f61ed0b95b834e4dde764f63c500a885e87ea38',
 'src/anysolver/elements.py':'f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37',
 'src/anysolver/_ge_beam3_g3c_local_shell.py':'69d9f27a96ed7e9a5959a42a081eeafbbe72021de6e4da1f91355c5fb3850f10',
 'src/anysolver/_ge_beam3_variational_shell.py':'b0db7a83633f4a835c06e940a6f0de36ab958f7e816c37a23c6ebc16259a2a60',
 'src/anysolver/_ge_beam3_mixed_ad.py':'b299ff765cd2eaae8b33a2ba1d05069f6fe8c39209e1eac75df356a2afb1fe36',
 'src/anysolver/_ge_beam3_pose_joint.py':'69cfb0a71761ab7cad0d62080d81511949e7c920f7f70162bcaba0497b402657',
 'src/anysolver/_ge_beam3_g3c_definition.py':'4b46b870fec010e3378df83c374d763f858d8f25820c14f9704dc6f0a656f0c2',
 'src/anysolver/_ge_beam3_g3c_owner.py':'18b9565d56192e23f192b1a3fbae3cb12ed7ede958c0e4b3e46279a799d1afc5',
 'docs/reference_cases/ge_beam3_g3c_fixtures_v1.json':'d5fecc80c3203ac7d191b4031d64bf35c56d2900066cb01fc1dfa4276d24c006'}


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def array_digest(value):
    a=np.asarray(value,dtype=np.float64)
    assert np.isfinite(a).all()
    return dict(shape=list(a.shape),sha256=sha256(a.astype('<f8',copy=False).tobytes()).hexdigest())


def norm(value):
    a=np.asarray(value,dtype=np.float64)
    assert np.isfinite(a).all()
    largest=float(np.max(np.abs(a))) if a.size else 0.
    return 0. if largest==0. else largest*float(np.linalg.norm(a/largest))


def close(actual,expected,*,scale=None,tolerance=1e-11):
    a=np.asarray(actual,dtype=np.float64);b=np.asarray(expected,dtype=np.float64)
    assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    denominator=norm(b) if scale is None else float(scale)
    assert math.isfinite(denominator) and denominator>=0
    difference=norm(a-b)
    if denominator==0:
        assert difference==0
        return 0.
    ratio=difference/denominator
    assert ratio<=tolerance,(ratio,tolerance,array_digest(a),array_digest(b))
    return ratio


def length(construction):
    X=construction.coordinates
    return max(norm(X[(i+1)%4]-X[i]) for i in range(4))


def scale_vector(construction):
    return np.tile([length(construction)]*3+[1.]*3,4)


def facade(identity):
    if identity not in _FACADES:_FACADES[identity]=candidate.AffineQ4PhysicalRecovery(identity)
    return _FACADES[identity]


def context(identity,pose='MIXED',amplitude=1.):
    return registry.construction(identity),*registry.pose(identity,pose,amplitude)


def evaluate(c,q,accepted):
    key=(c.construction_id,np.asarray(q).tobytes(),np.asarray(accepted).tobytes())
    if key not in _RESULTS:
        print('BEAM CHECKPOINT recovery '+c.construction_id,flush=True)
        _RESULTS[key]=facade(c.construction_id).evaluate(q,accepted)
    return _RESULTS[key]


def independent(c,q,accepted):
    key=(c.construction_id,np.asarray(q).tobytes(),np.asarray(accepted).tobytes())
    if key not in _EXPECTED:
        _EXPECTED[key]=checker.evaluate(c.coordinates,q,accepted,normal=c.normal,
            material_direction=c.material_direction,director_polarity=c.director_polarity)
    return _EXPECTED[key]


def base_contexts():
    for identity in registry.base_ids():
        for pose in registry.POSES:yield identity,pose,*context(identity,pose)


def check_chart(c,trial,expected):
    scales=scale_vector(c);inverse=1/scales
    kin=trial.kinematics
    zero_pose=(np.array_equal(kin.current_positions,c.coordinates)
               and np.array_equal(kin.rotations,np.tile(np.eye(3),(4,1,1))))
    reference_scale=norm((c.coordinates-c.coordinates.mean(axis=0))/length(c))
    return dict(
        d=close(inverse*kin.deformation,inverse*expected['d'],
                scale=reference_scale if zero_pose else norm(inverse*expected['d'])),
        D=close(inverse[:,None]*kin.differential*scales[None,:],inverse[:,None]*expected['D']*scales[None,:]),
        D2=close(inverse[:,None,None]*kin.second*scales[None,:,None]*scales[None,None,:],
                 inverse[:,None,None]*expected['D2']*scales[None,:,None]*scales[None,None,:]),
        R=close(kin.frame,expected['R']),Q=close(kin.rotations,expected['Q']),x=close(kin.current_positions,expected['x']))


def physical_scales(c):
    q,qa=registry.pose(c.construction_id,'ZERO')
    zero=evaluate(c,q,qa);s=scale_vector(c)
    physical=norm(s[:,None]*zero.physical_chart_hessian*s[None,:])
    total=norm(s[:,None]*zero.chart_hessian*s[None,:])
    assert physical>0 and total>0
    return physical,total


def physical_comparison(c,q,qa,predicate,actual,expected):
    """A verified physical mismatch is evidence, never a disguised pytest crash."""
    target=predicate.removeprefix('source_')
    scaled_actual=checker.physical_scaled(target,actual,c.coordinates)
    scaled_expected=checker.physical_scaled(target,expected,c.coordinates)
    error=checker.relative_error(scaled_actual,scaled_expected)
    if error>1e-11:
        directory=Path(os.environ['BEAM_QUALIFICATION_OUTPUT'])
        lease=json.loads((directory.parent/'lease.json').read_text())
        payload=dict(schema='Q4_AFFINE_NUMERICAL_CONTRADICTION_V1',predicate=predicate,
            coordinates=c.coordinates.tolist(),q=np.asarray(q).tolist(),accepted=np.asarray(qa).tolist(),
            normal=c.normal.tolist(),material_direction=c.material_direction.tolist(),director_polarity=c.director_polarity,
            actual=np.asarray(actual).tolist(),tolerance=1e-11,scale_mode='REFERENCE_EDGE_NONDIMENSIONAL_V1',
            source_identity=sha256(canonical(lease['inputs'])).hexdigest(),candidate_identity=lease['candidate']['commit'],
            fixture_identity=c.construction_id)
        # Independently reconstructed expected values and scales, not a caller's
        # fabricated expected operand. The runner verifies again before writing.
        verification=checker.verify_contradiction(payload)
        assert verification['accepted'] is True
        CONTRADICTIONS.append(payload)
    return dict(relative_error=error,passed=error<=1e-11,actual=array_digest(actual))


def check_physical(c,q,qa,trial,expected):
    s=scale_vector(c);zero,_=physical_scales(c)
    zero_pose=not np.any(q) and np.array_equal(qa,np.tile(np.eye(3),(4,1,1)))
    energy_scale=abs(float(expected['physical_energy']))
    if energy_scale==0 or zero_pose:energy_scale=zero
    force=s*expected['physical_force'];force_scale=zero if zero_pose else norm(force) or zero
    hessian=s[:,None]*expected['physical_hessian']*s[None,:]
    return dict(energy=(close(trial.physical_energy,expected['physical_energy'],scale=energy_scale) if zero_pose else
                       physical_comparison(c,q,qa,'physical_energy',trial.physical_energy,expected['physical_energy'])),
        force=(close(s*trial.physical_chart_force,force,scale=force_scale) if zero_pose else
               physical_comparison(c,q,qa,'physical_force',trial.physical_chart_force,expected['physical_force'])),
        hessian=physical_comparison(c,q,qa,'physical_hessian',trial.physical_chart_hessian,expected['physical_hessian']),
        symmetry=close(s[:,None]*trial.physical_chart_hessian*s[None,:],(s[:,None]*trial.physical_chart_hessian*s[None,:]).T),
        spatial_force=close(s*trial.physical_spatial_force,s*expected['physical_spatial_force'],scale=force_scale),
        spatial_tangent=close(s[:,None]*trial.physical_spatial_row_chart_tangent*s[None,:],
                              s[:,None]*expected['physical_spatial_row_tangent']*s[None,:]))


def record(name,**tables):
    for table,rows in tables.items():
        assert rows and len({row['id'] for row in rows})==len(rows),table
    SCIENTIFIC_RECORDS.append(dict(test=name,tables=tables,full_g3c_qualified=False,production_qualified=False))


def test_affine_recovery_definition_and_source_identity():
    hashes={}
    for name,digest in SOURCES.items():
        raw=(ROOT/name).read_bytes().replace(b'\r\n',b'\n');assert sha256(raw).hexdigest()==digest
        hashes[name]=digest
    ids=registry.base_ids()+registry.graph_ids()
    assert len(registry.base_ids())==9 and len(registry.graph_ids())==10 and len(set(ids))==19
    rows=[]
    for identity in ids:
        c=registry.construction(identity);f=facade(identity)
        assert c.recipe_sha256==sha256(c.recipe).hexdigest()
        descriptor=f.descriptor()
        assert not hasattr(f,'commit') and not hasattr(f,'restart')
        rows.append(dict(id=identity,recipe_sha256=c.recipe_sha256,descriptor_sha256=sha256(canonical(descriptor)).hexdigest()))
    lemma_raw=(ROOT/'docs/GE_BEAM3_Q4_AFFINE_RECOVERY_EXTENSION_LEMMA.md').read_bytes().replace(b'\r\n',b'\n')
    assert sha256(lemma_raw).hexdigest()=='156d33ae5a621b953b5d04050218618f6416bac1042f94d3d3fc5c305c9f8762'
    review_raw=(ROOT/'docs/reference_cases/ge_beam3_q4_affine_extension_lemma_review_v1.json').read_bytes()
    lemma=json.loads(review_raw)
    assert set(lemma)=={'decision','findings','reviewer','scope','subject_commit'}
    assert canonical(lemma)==review_raw and not lemma['findings'] and lemma['reviewer']['independent'] is True
    assert lemma['decision']=='ACCEPTED_GE_BEAM3_Q4_AFFINE_EXTENSION_LEMMA'
    assert lemma['scope']['lemma_sha256']==sha256(lemma_raw).hexdigest()
    record('definition_and_source_identity',definitions=rows,source_graph=[dict(id='source_graph',hashes=hashes)],
           extension_lemma=[dict(id='ideal_recipe_extension',lemma_sha256=sha256(lemma_raw).hexdigest(),review_sha256=sha256(review_raw).hexdigest())])


def test_affine_recovery_zero_and_station_constitutive():
    rows=[]
    for identity,pose,c,q,qa in base_contexts():
        trial=evaluate(c,q,qa);expected=independent(c,q,qa);metrics=check_chart(c,trial,expected)
        assert len(trial.stations)==4
        for i,station in enumerate(trial.stations):
            assert station.weight>0
            close(station.resultant,station.constitutive@station.strain,
                  scale=norm(station.resultant) or norm(station.constitutive))
            close(station.weight,expected['weights'][i]);close(station.natural,expected['natural'][i])
            close(station.reference_position,expected['reference_positions'][i]);close(station.current_position,expected['current_positions'][i])
        rows.append(dict(id=identity+'::'+pose,checks=metrics,energy=float(trial.physical_energy),stations=4))
    assert len(rows)==54;record('zero_and_station_constitutive',station=rows)


def test_affine_recovery_independent_material_fields():
    rows=[]
    for identity,pose,c,q,qa in base_contexts():
        trial=evaluate(c,q,qa);expected=independent(c,q,qa);checks=[]
        for i,s in enumerate(trial.stations):
            component_scale=np.array([1.,1.,1.,length(c),length(c),length(c),1.,1.])
            strain_scale=norm(component_scale[:,None]*expected['M'][i]*scale_vector(c)[None,:]) if pose=='ZERO' else norm(component_scale*expected['strains'][i])
            resultant_scale=norm((expected['C']@expected['M'][i])*scale_vector(c)[None,:]/component_scale[:,None]) if pose=='ZERO' else norm(expected['resultants'][i]/component_scale)
            checks.append(dict(M=close(s.mixed_map,expected['M'][i]),
                strain=close(component_scale*s.strain,component_scale*expected['strains'][i],scale=strain_scale),
                resultant=close(s.resultant/component_scale,expected['resultants'][i]/component_scale,scale=resultant_scale),
                frame=close(s.numbered_frame,expected['frame']),constitutive=close(s.constitutive,expected['C'])))
            close(component_scale*s.physical_strain,component_scale*expected['physical_strains'][i],scale=strain_scale)
            close(s.physical_resultant/component_scale,expected['physical_resultants'][i]/component_scale,scale=resultant_scale)
            for prefix in ('reference','current'):
                strain_tensors=np.array([expected[prefix+'_membrane_strain_tensor'][i],expected[prefix+'_curvature_tensor'][i]])
                resultant_tensors=np.array([expected[prefix+'_membrane_resultant_tensor'][i],expected[prefix+'_moment_tensor'][i]])
                scale=np.array([1.,length(c)])[:,None,None]
                close(getattr(s,prefix+'_strain_tensors')*scale,strain_tensors*scale,scale=strain_scale)
                close(getattr(s,prefix+'_resultant_tensors')/scale,resultant_tensors/scale,scale=resultant_scale)
                close(getattr(s,prefix+'_shear_strain'),expected[prefix+'_shear_strain'][i],scale=strain_scale)
                close(getattr(s,prefix+'_shear_resultant'),expected[prefix+'_shear_resultant'][i],scale=resultant_scale)
        close(trial.source_stationary_matrix,expected['Hsource']);close(trial.source_coupling,expected['source_load'])
        close(trial.source_solution,expected['source_solution'])
        rows.append(dict(id=identity+'::'+pose,stations=checks))
    assert len(rows)==54;record('independent_material_fields',independent=rows)


def test_affine_recovery_64_stationarity_and_schur():
    rows=[]
    for identity,pose,c,q,qa in base_contexts():
        trial=evaluate(c,q,qa);expected=independent(c,q,qa)
        block=trial.internal_block64;inverse=trial.internal_inverse64
        assert block.shape==(64,64) and inverse.shape==(64,64)
        close(block@inverse,np.eye(64));close(inverse@block,np.eye(64))
        close(trial.internal_residual64,np.zeros(64),scale=norm(block)*sum(norm(s.strain)+norm(s.resultant) for s in trial.stations) or norm(block))
        schur=trial.direct_chart_hessian-trial.internal_coupling64.T@inverse@trial.internal_coupling64
        close(trial.schur_chart_hessian,schur);close(schur,trial.physical_chart_hessian)
        for i,station in enumerate(trial.stations):
            close(station.internal_block,expected['station_internal'][i]);close(station.internal_inverse,expected['station_inverse'][i])
            close(station.chart_first,expected['station_J'][i]);close(station.chart_second,expected['station_second'][i])
        rows.append(dict(id=identity+'::'+pose,schur=array_digest(schur),full_internal_dimension=64))
    assert len(rows)==54;record('64_stationarity_and_schur',schur=rows)


def test_affine_recovery_actual_chart_work_hessian():
    rows=[]
    for identity,pose,c,q,qa in base_contexts():
        trial=evaluate(c,q,qa);expected=independent(c,q,qa)
        checks=check_physical(c,q,qa,trial,expected)
        zero_pose=not np.any(q) and np.array_equal(qa,np.tile(np.eye(3),(4,1,1)))
        if not zero_pose:
            checks['source_energy']=physical_comparison(c,q,qa,'source_physical_energy',trial.source_physical_energy,expected['physical_energy'])
            checks['source_force']=physical_comparison(c,q,qa,'source_physical_force',trial.source_physical_chart_force,expected['physical_force'])
            checks['source_hessian']=physical_comparison(c,q,qa,'source_physical_hessian',trial.source_physical_chart_hessian,expected['physical_hessian'])
            if any(not checks[key]['passed'] for key in ('source_energy','source_force','source_hessian')):
                rows.append(dict(id=identity+'::'+pose,checks=checks,chart_image_sentinels=False));continue
        D,S=trial.kinematics.differential,trial.kinematics.second
        numerical_force=sum((s.local_force for s in trial.numerical_channels),np.zeros(24))
        numerical_tangent=sum((s.local_tangent for s in trial.numerical_channels),np.zeros((24,24)))
        actual_force=trial.local_force-numerical_force;actual_tangent=trial.local_tangent-numerical_tangent
        close(trial.physical_chart_force,D.T@actual_force,scale=physical_scales(c)[0] if zero_pose else norm(trial.physical_chart_force))
        close(trial.physical_chart_hessian,D.T@actual_tangent@D+np.einsum('i,ijk->jk',actual_force,S))
        local_recovered=sum((s.weight*(s.mixed_map+s.nonlinear_first).T@s.resultant for s in trial.stations),np.zeros(24))
        local_hessian=sum((s.weight*((s.mixed_map+s.nonlinear_first).T@s.constitutive@(s.mixed_map+s.nonlinear_first)+
            np.einsum('a,aij->ij',s.resultant,s.nonlinear_second)) for s in trial.stations),np.zeros((24,24)))
        delta=actual_force-local_recovered;deltaK=actual_tangent-local_hessian
        close(D.T@delta,np.zeros(24),scale=physical_scales(c)[0] if zero_pose else norm(D.T@actual_force))
        close(D.T@deltaK@D+np.einsum('i,ijk->jk',delta,S),np.zeros((24,24)),scale=norm(trial.physical_chart_hessian))
        rows.append(dict(id=identity+'::'+pose,checks=checks,chart_image_sentinels=True))
    assert len(rows)==54;record('actual_chart_work_hessian',work=rows)


def test_affine_recovery_directional_derivatives_all_steps():
    rows=[]
    for identity in registry.base_ids():
        c,q,qa=context(identity);trial=evaluate(c,q,qa);s=scale_vector(c)
        direction=np.sin(np.arange(24)+1);direction/=norm(direction);direction*=s
        for h in (1e-4,1e-5,1e-6):
            plus=evaluate(c,q+h*direction,qa);minus=evaluate(c,q-h*direction,qa)
            work=(plus.physical_energy-minus.physical_energy)/(2*h)
            tangent=(plus.physical_chart_force-minus.physical_chart_force)/(2*h)
            a=close(work,float(trial.physical_chart_force@direction),tolerance=1e-7)
            b=close(s*tangent,s*(trial.physical_chart_hessian@direction),tolerance=1e-7)
            rows.append(dict(id=identity+'::h='+str(h),work=a,tangent=b))
    assert len(rows)==27;record('directional_derivatives_all_steps',directional=rows)


def test_affine_recovery_six_rigid_modes_and_common_motion():
    rigid=[];motion=[]
    for shape in registry.SHAPES:
        identity=shape+'::1';c,q,qa=context(identity,'ZERO');trial=evaluate(c,q,qa);s=scale_vector(c)
        X=c.coordinates-c.coordinates.mean(axis=0);R=np.zeros((24,6))
        for node in range(4):
            R[6*node:6*node+3,:3]=np.eye(3)
            for j in range(3):R[6*node:6*node+3,3+j]=np.cross(np.eye(3)[j],X[node])
            R[6*node+3:6*node+6,3:]=np.eye(3)
        K=s[:,None]*trial.chart_hessian*s[None,:];basis=R/s[:,None]
        close(K@basis,np.zeros((24,6)),scale=norm(K)*norm(basis))
        eigen=np.linalg.eigvalsh(K);threshold=1e-11*norm(K)
        assert np.sum(np.abs(eigen)<=threshold)==6 and np.sum(eigen>threshold)==18
        rigid.append(dict(id=identity,rigid_columns=6,total_positive_modes=18,eigenvalues=array_digest(eigen)))
        c,q,qa=context(identity);base=evaluate(c,q,qa)
        for index in range(4):
            moved,accepted,W=registry.common_motion(q,qa,c.coordinates,index);result=evaluate(c,moved,accepted)
            expected=independent(c,moved,accepted);check_chart(c,result,expected);check_physical(c,moved,accepted,result,expected)
            close(result.physical_energy,base.physical_energy)
            for a,b in zip(result.stations,base.stations):close(a.strain,b.strain);close(a.resultant,b.resultant)
            transformed=(base.physical_spatial_force.reshape(4,6).reshape(4,2,3)@W.T).reshape(24)
            close(result.physical_spatial_force,transformed)
            motion.append(dict(id=identity+'::motion='+str(index),energy=float(result.physical_energy)))
    assert len(rigid)==3 and len(motion)==12;record('six_rigid_modes_and_common_motion',rigid=rigid,common_motion=motion)


def test_affine_recovery_d4_and_director_transports():
    d4=[];director=[]
    for shape in registry.SHAPES:
        base_c,base_q,base_qa=context(shape+'::1');base=evaluate(base_c,base_q,base_qa)
        for k in range(8):
            identity=shape+'::1::D4:'+str(k);c,q,qa=context(identity);trial=evaluate(c,q,qa)
            expected=independent(c,q,qa);check_physical(c,q,qa,trial,expected)
            close(trial.physical_energy,base.physical_energy)
            indices=np.array([6*i+j for i in c.permutation for j in range(6)])
            close(trial.physical_spatial_force,base.physical_spatial_force[indices])
            positions=np.array([s.reference_position for s in base.stations])
            matched=[]
            for station in trial.stations:
                index=int(np.argmin(np.linalg.norm(positions-station.reference_position,axis=1)));assert index not in matched;matched.append(index)
                close(station.reference_position,positions[index])
                close(station.reference_strain_tensors,base.stations[index].reference_strain_tensors)
                close(station.reference_resultant_tensors,base.stations[index].reference_resultant_tensors)
            d4.append(dict(id=identity,station_map=matched))
        for polarity in (-1,1):
            identity=shape+'::1::DIRECTOR:'+str(polarity);c,q,qa=context(identity);trial=evaluate(c,q,qa)
            expected=independent(c,q,qa);check_physical(c,q,qa,trial,expected)
            for station in trial.stations:
                sigma=polarity
                transform=np.diag([1,1,sigma,sigma,sigma,1,sigma,1])
                close(station.physical_strain,transform@station.strain)
                close(station.physical_resultant,transform@station.resultant)
                close(station.physical_strain@station.physical_resultant,station.strain@station.resultant)
            director.append(dict(id=identity,physical_polarity=polarity))
    assert len(d4)==24 and len(director)==6;record('d4_and_director_transports',d4=d4,director=director)


def test_affine_recovery_passive_and_same_pose_rebase():
    passive=[];rebases=[]
    for shape in registry.SHAPES:
        c,q,qa=context(shape+'::1');base=evaluate(c,q,qa)
        transformed,uq,accepted=context(shape+'::1::PASSIVE');trial=evaluate(transformed,uq,accepted)
        expected=independent(transformed,uq,accepted);check_chart(transformed,trial,expected);check_physical(transformed,uq,accepted,trial,expected)
        W=transformed.passive_rotation
        close(trial.physical_energy,base.physical_energy)
        close(trial.physical_spatial_force,(base.physical_spatial_force.reshape(4,2,3)@W.T).reshape(24))
        for a,b in zip(trial.stations,base.stations):
            close(a.reference_strain_tensors,W@b.reference_strain_tensors@W.T)
            close(a.reference_resultant_tensors,W@b.reference_resultant_tensors@W.T)
        passive.append(dict(id=transformed.construction_id,energy=float(trial.physical_energy)))
        rebased,accepted=registry.rebase(q,qa);trial=evaluate(c,rebased,accepted)
        expected=independent(c,rebased,accepted);check_chart(c,trial,expected);check_physical(c,rebased,accepted,trial,expected)
        close(trial.kinematics.deformation,base.kinematics.deformation);close(trial.physical_energy,base.physical_energy)
        close(trial.physical_spatial_force,base.physical_spatial_force)
        rebases.append(dict(id=c.construction_id,energy=float(trial.physical_energy)))
    assert len(passive)==len(rebases)==3;record('passive_and_same_pose_rebase',passive=passive,rebase=rebases)


def test_affine_recovery_all_graph_q4_reference_variants():
    rows=[]
    source=json.loads((ROOT/'docs/reference_cases/ge_beam3_g3c_fixtures_v1.json').read_text())
    for identity in registry.graph_ids():
        graph_id,variant=identity.split('::')
        graph=next(g for g in source['graphs'] if g['id']==graph_id)
        element=next(e for e in graph['elements'] if e['family']=='Q4')
        nodes=dict(graph['nodes']);ids=list(element['nodes']);X=np.array([nodes[i] for i in ids],dtype=np.float64)
        direction=np.array([1.,0.,0.]);normal=np.array(source['definitions']['shell']['reference_normal'],dtype=np.float64)
        if variant=='RENUMBERED':ids=[10000+7*i for i in ids]
        if variant=='CONNECTIVITY_REVERSED':
            ids=[ids[i] for i in (0,3,2,1)];X=X[[0,3,2,1]]
        if variant=='PROPER_GLOBAL_TRANSFORM':
            W=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
            X=X@W.T+np.array([2.,-3.,1.]);normal=W@normal;direction=W@direction
        for pose in ('ZERO','MIXED'):
            c,q,qa=context(identity,pose);trial=evaluate(c,q,qa);expected=independent(c,q,qa)
            assert tuple(ids)==c.node_ids and np.array_equal(X,c.coordinates)
            assert np.array_equal(normal,c.normal) and np.array_equal(direction,c.material_direction)
            check_chart(c,trial,expected);checks=check_physical(c,q,qa,trial,expected)
            assert c.element_id in (11,13,20055,20065)
            close(c.material_direction,c.passive_rotation@np.array([1.,0.,0.]))
            close(c.normal,c.passive_rotation@np.array([0.,0.,1.]))
            rows.append(dict(id=identity+'::'+pose,node_ids=list(c.node_ids),element_id=c.element_id,
                recipe_sha256=c.recipe_sha256,checks=checks))
    assert len(rows)==20;record('all_graph_q4_reference_variants',graph=rows)


def test_affine_recovery_tiny_physical_energy_and_numerical_separation():
    tiny=[];channels=[]
    for shape in registry.SHAPES:
        for amplitude in (1e-6,1e-3):
            c,q,qa=context(shape+'::1',amplitude=amplitude);trial=evaluate(c,q,qa);expected=independent(c,q,qa)
            assert trial.physical_energy>0 and expected['physical_energy']>0
            checks=check_physical(c,q,qa,trial,expected)
            tiny.append(dict(id=c.construction_id+'::amplitude='+str(amplitude),checks=checks,energy=float(trial.physical_energy)))
    for identity,pose,c,q,qa in base_contexts():
        trial=evaluate(c,q,qa);physical=sum(s.weight*.5*(s.strain@s.resultant) for s in trial.stations)
        close(trial.physical_energy,physical,scale=physical_scales(c)[0] if pose=='ZERO' else abs(physical))
        close(trial.energy,physical+sum(s.energy for s in trial.numerical_channels),scale=physical_scales(c)[1] if pose=='ZERO' else abs(trial.energy))
        close(trial.chart_force,trial.physical_chart_force+sum((s.chart_force for s in trial.numerical_channels),np.zeros(24)),
              scale=physical_scales(c)[1] if pose=='ZERO' else norm(trial.chart_force))
        close(trial.chart_hessian,trial.physical_chart_hessian+sum((s.chart_hessian for s in trial.numerical_channels),np.zeros((24,24))))
        assert len(trial.numerical_channels)==2
        channels.append(dict(id=identity+'::'+pose,physical=float(physical),numerical=[dict(name=s.name,energy=float(s.energy)) for s in trial.numerical_channels]))
    assert len(tiny)==6 and len(channels)==54;record('tiny_physical_energy_and_numerical_separation',tiny=tiny,channels=channels)


def test_affine_recovery_definition_observation_races(monkeypatch):
    c,q,qa=context('SQUARE::1');rows=[]
    original_descriptor=candidate.AffineQ4PhysicalRecovery.descriptor
    for route in ('descriptor','displacement_array','accepted_array','cancellation','material_descriptor','cache_array','cache_cancellation'):
        f=candidate.AffineQ4PhysicalRecovery(c.construction_id);other=candidate.AffineQ4PhysicalRecovery('RECTANGLE::1')
        if route.startswith('cache_'):f.evaluate(q,qa)
        entered=[]
        def swap():
            if route.startswith('cache_'):
                altered=replace(f._prepared,constitutive=np.array(f._prepared.constitutive)*2)
                object.__setattr__(f,'_prepared',altered);object.__setattr__(f,'_prepared_seal',candidate._fingerprint(altered))
            else:
                object.__setattr__(f,'_body',other._body);object.__setattr__(f,'_seal',other._seal)
        def forbidden(*args,**kwargs):entered.append(True);raise AssertionError('family entered after definition corruption')
        class Observed:
            def __init__(self,value):self.value=value
            def __array__(self,dtype=None,copy=None):swap();return np.array(self.value,dtype=dtype,copy=True)
        def observed_descriptor(self):
            value=original_descriptor(self)
            if self is f:
                if route=='material_descriptor':value['material_direction']=[0.,1.,0.]
                else:swap()
            return value
        with monkeypatch.context() as patch:
            patch.setattr(candidate,'family_objects',forbidden)
            if route in ('descriptor','material_descriptor'):patch.setattr(candidate.AffineQ4PhysicalRecovery,'descriptor',observed_descriptor)
            options={}
            if route in ('cancellation','cache_cancellation'):options['cancel_check']=lambda:(swap() or False)
            with pytest.raises(ValueError):
                f.evaluate(Observed(q) if route in ('displacement_array','cache_array') else q,
                           Observed(qa) if route=='accepted_array' else qa,**options)
        assert not entered
        rows.append(dict(id=route,rejected_before_family=True))
    record('definition_observation_races',races=rows)


def test_affine_recovery_immutable_detached_results_and_reentry(monkeypatch):
    c,q,qa=context('SQUARE::1');f=candidate.AffineQ4PhysicalRecovery(c.construction_id)
    mutable_q=np.array(q,copy=True);mutable_qa=np.array(qa,copy=True)
    first=f.evaluate(mutable_q,mutable_qa)
    def arrays(value):
        if isinstance(value,np.ndarray):yield value
        elif is_dataclass(value):
            for field in fields(value):yield from arrays(getattr(value,field.name))
        elif isinstance(value,tuple):
            for entry in value:yield from arrays(entry)
        else:assert not isinstance(value,(list,dict))
    snapshots=[array_digest(a) for a in arrays(first)]
    count=0
    for a in arrays(first):
        assert not a.flags.writeable
        with pytest.raises(ValueError):a.setflags(write=True)
        if a.size:
            with pytest.raises(ValueError):a.flat[0]=0
        count+=1
    assert count>30
    with pytest.raises((FrozenInstanceError,AttributeError)):first.physical_energy=0
    mutable_q[:]=0;mutable_qa[:]=0
    assert [array_digest(a) for a in arrays(first)]==snapshots
    again=f.evaluate(q,qa)
    assert [array_digest(a) for a in arrays(again)]==snapshots
    for a,b in zip(arrays(first),arrays(again)):assert not np.shares_memory(a,b) or not a.flags.writeable
    inner=[]
    def reentry():
        with pytest.raises(RuntimeError):f.evaluate(q,qa)
        inner.append(True);return False
    f.evaluate(q,qa,cancel_check=reentry);assert len(inner)==2
    changed=np.array(qa,copy=True);changed[0,0,0]+=1e-3
    with pytest.raises(ValueError):f.evaluate(q,changed)
    assert [array_digest(a) for a in arrays(first)]==snapshots
    entered=Event();release=Event();completed=[];errors=[]
    def pause():entered.set();assert release.wait(20);return False
    def concurrent():
        try:completed.append(f.evaluate(q,qa,cancel_check=pause))
        except BaseException as exc:errors.append(exc)
    thread=Thread(target=concurrent,daemon=True);thread.start()
    try:
        assert entered.wait(20)
        with pytest.raises(RuntimeError):f.evaluate(q,qa)
    finally:release.set();thread.join(30)
    assert not thread.is_alive() and not errors and len(completed)==1
    cached=f._prepared;badweights=np.array(cached.weights,copy=True)*2
    object.__setattr__(f,'_prepared',replace(cached,weights=badweights))
    with pytest.raises(ValueError):f.evaluate(q,qa)
    object.__setattr__(f,'_prepared',cached)
    record('immutable_detached_results_and_reentry',immutability=[dict(id='all_detached_arrays',array_count=count),
        dict(id='caller_arrays_preserved'),dict(id='same_input_repeat'),dict(id='reentry',rejections=len(inner)),
        dict(id='changed_accepted_matrix'),dict(id='concurrent_evaluation'),dict(id='operator_cache_tamper')])


def test_affine_recovery_unsupported_routes_and_cancellation(monkeypatch):
    c,q,qa=context('SQUARE::1');rows=[];entered=[]
    original_family=candidate.family_objects
    def counted(*args,**kwargs):entered.append(True);return original_family(*args,**kwargs)
    nonaffine=np.array(c.coordinates,copy=True);nonaffine[2,0]+=1e-4
    badnormal=np.array(c.normal,copy=True);badnormal[0]=1e-4
    badmaterial=np.array(c.material_direction,copy=True);badmaterial[1]=1e-4
    wrongnodes=tuple(reversed(c.node_ids))
    for name,options in (('nonaffine',{'coordinates':nonaffine}),('director',{'normal':badnormal}),
        ('material_direction',{'material_direction':badmaterial}),('node_ids',{'node_ids':wrongnodes}),
        ('generalized_section',{'generalized_section':np.eye(8)}),('history_section',{'plasticity':True}),
        ('offset',{'offset':.01}),('initial_fields',{'initial_strain':np.ones(8)}),
        ('foreign_policy',{'formulation_id':'GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1'})):
        with monkeypatch.context() as patch:
            patch.setattr(candidate,'family_objects',counted)
            with pytest.raises((ValueError,TypeError)):candidate.AffineQ4PhysicalRecovery(c.construction_id,**options)
        assert not entered;rows.append(dict(id=name,rejected_before_family=True))
    for name in ('GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1','OLD_RETAINED_35_VARIABLE_SYSTEM','FOREIGN'):
        with pytest.raises(ValueError):candidate.AffineQ4PhysicalRecovery(name)
        rows.append(dict(id=name,rejected_before_family=True))
    for label,u,accepted in (('nonfinite_q',np.full(24,np.nan),qa),('nonfinite_accepted',q,np.full((4,3,3),np.inf)),
                             ('wrong_q_shape',q[:18],qa),('wrong_rotation_shape',q,qa[:3])):
        with monkeypatch.context() as patch:
            patch.setattr(candidate,'family_objects',counted)
            with pytest.raises(ValueError):candidate.AffineQ4PhysicalRecovery(c.construction_id).evaluate(u,accepted)
        assert not entered;rows.append(dict(id=label,rejected_before_family=True))
    for phase in ('before_work','before_publication','invalid_callback'):
        f=candidate.AffineQ4PhysicalRecovery(c.construction_id);calls=[];entered.clear()
        def cancellation():
            calls.append(True)
            if phase=='invalid_callback':return 1
            return phase=='before_work' or len(calls)==2
        with monkeypatch.context() as patch:
            patch.setattr(candidate,'family_objects',counted)
            with pytest.raises(ValueError if phase=='invalid_callback' else candidate.AffineRecoveryCancelled):
                f.evaluate(q,qa,cancel_check=cancellation)
        assert bool(entered)==(phase=='before_publication')
        rows.append(dict(id=phase,callbacks=len(calls),family_entries=len(entered),published=False))
    record('unsupported_routes_and_cancellation',rejections=rows)


def test_affine_recovery_actual_mutation_rejection(monkeypatch):
    rows=[]
    for shape in registry.SHAPES:
        c,q,qa=context(shape+'::1');f=facade(c.construction_id);trial=evaluate(c,q,qa);expected=independent(c,q,qa)
        prepared=f._prepared;kin=trial.kinematics
        before=sha256(candidate.canonical(candidate._payload(prepared))).hexdigest()
        def forbidden(*args,**kwargs):raise AssertionError('mutation must not rebuild stationary reference')
        with monkeypatch.context() as protection:
            protection.setattr(candidate,'_prepare_reference',forbidden)
            def station_compare(value):
                stations,g,H=candidate._station_fields(value,kin)
                close(np.array([s.strain for s in stations]),expected['strains'])
                close(np.array([s.resultant for s in stations]),expected['resultants'])
                close(np.array([s.natural for s in stations]),expected['natural'])
                close(np.array([s.reference_position for s in stations]),expected['reference_positions'])
                close(np.array([s.weight for s in stations]),expected['weights'])
                close(np.array([s.numbered_frame for s in stations]),np.array([expected['frame']]*4))
                close(g,expected['physical_force']);close(H,expected['physical_hessian'])
            station_compare(prepared)
            for name in ('station_order','weight','frame','M','resultant'):
                changes={}
                if name=='station_order':changes['natural']=np.array(prepared.natural[::-1],copy=True)
                elif name=='weight':changes['weights']=np.array(prepared.weights)*2
                elif name=='frame':changes['frame']=np.array(prepared.frame)[:,[1,0,2]]
                elif name=='M':
                    value=np.array(prepared.mixed_maps,copy=True);value[0,0,0]+=.1;changes['mixed_maps']=value
                else:changes['constitutive']=np.array(prepared.constitutive)*1.1
                with pytest.raises(AssertionError):station_compare(replace(prepared,**changes))
                rows.append(dict(id=shape+'::'+name,rejection='INDEPENDENT_STATION_COMPARISON'))
            original=candidate._nonlinear_terms
            for mode in ('n','Dn','Hn'):
                def altered(*args,mode=mode):
                    values=list(original(*args));index={'n':0,'Dn':1,'Hn':2}[mode];values[index]=np.zeros_like(values[index]);return tuple(values)
                with monkeypatch.context() as patch:
                    patch.setattr(candidate,'_nonlinear_terms',altered)
                    with pytest.raises(AssertionError):station_compare(prepared)
                rows.append(dict(id=shape+'::'+mode,rejection='INDEPENDENT_STATION_COMPARISON'))
            original_schur=candidate._schur_terms
            def omit_geometric(*args):
                material,geometric=original_schur(*args);return material,np.zeros_like(geometric)
            with monkeypatch.context() as patch:
                patch.setattr(candidate,'_schur_terms',omit_geometric)
                with pytest.raises(AssertionError):station_compare(prepared)
            rows.append(dict(id=shape+'::force_weighted_Hessian',rejection='INDEPENDENT_HESSIAN'))
            badkin=replace(kin,second=np.zeros_like(kin.second))
            _,_,badH=candidate._station_fields(prepared,badkin)
            with pytest.raises(AssertionError):close(badH,expected['physical_hessian'])
            rows.append(dict(id=shape+'::chart_second',rejection='INDEPENDENT_HESSIAN'))
            C=trial.internal_coupling64;inverse=trial.internal_inverse64
            # Actual full station equilibrium catches a coupling sign error.
            badcoupling=-C
            solution=-inverse@C
            with pytest.raises(AssertionError):close(trial.internal_block64@solution,-badcoupling)
            rows.append(dict(id=shape+'::coupling_sign',rejection='STATION_EQUILIBRIUM'))
            badinverse=np.array(inverse,copy=True);badinverse[0,0]+=1
            with pytest.raises(AssertionError):close(trial.internal_block64@badinverse,np.eye(64))
            rows.append(dict(id=shape+'::inverse',rejection='STATION_INVERSE'))
            contaminated=trial.physical_energy+sum(channel.energy for channel in trial.numerical_channels)
            with pytest.raises(AssertionError):close(contaminated,expected['physical_energy'])
            rows.append(dict(id=shape+'::numerical_energy_leak',rejection='MATERIAL_ENERGY'))
        assert sha256(candidate.canonical(candidate._payload(prepared))).hexdigest()==before
    assert len(rows)==39;record('actual_mutation_rejection',mutations=rows)


def test_affine_recovery_smoke_square_station_work():
    rows=[]
    for pose in ('ZERO','MIXED'):
        c,q,qa=context('SQUARE::1',pose);trial=evaluate(c,q,qa);expected=independent(c,q,qa)
        check_chart(c,trial,expected);checks=check_physical(c,q,qa,trial,expected)
        rows.append(dict(id='SQUARE::1::'+pose,checks=checks))
    record('smoke_square_station_work',smoke=rows)
