"""Manufactured physical maps/unit covariance/refusals; no equilibrium runs."""
import copy
import json
import numpy as np
import pytest
from scripts.r8_e02_rigid_acceptance import ARTIFACT_KEYS,measure,registration,matched_port_work
from scripts.r8_e02_rigid_precision import build_precision_deck

ARTIFACTS={name:('1234567890abcdef'*4) for name in ARTIFACT_KEYS}

def test_exact_registration_survives_json_tuple_list_roundtrip_without_admitting_extra_fields():
    c,r,m,d=fixture()
    c,r,m=json.loads(json.dumps([c,r,m]))
    assert measure(c,r,m,d,ARTIFACTS)['diagnostic_limits_satisfied']
    c['extra']='unregistered'
    with pytest.raises(ValueError,match='identity'):measure(c,r,m,d,ARTIFACTS)

def test_last_change_or_small_reference_gap_cannot_supply_convergence():
    r=matched_port_work(1.7445002169677598e-5,1.744681305259499e-5)
    assert r['provisional_one_percent_limit_satisfied'] and not r['qualification']
    assert r['convergence_status']=='NOT_ADJUDICATED'
    with pytest.raises(ValueError):matched_port_work(0.,0.)

def test_root_support_work_cannot_hide_behind_balanced_resultants_and_small_gaps():
    c,r,m,d=fixture('Mx')
    for index,sign in ((0,1),(-1,-1)):
        r['root']['poses'][index][1]=sign*1e-10
        r['root']['actions'][index][1]+=sign*1.
    result=measure(c,r,m,d,ARTIFACTS)
    assert result['metrics']['force_balance']<1e-14 and result['metrics']['moment_balance']<1e-14
    assert result['metrics']['scaled_constraint']<1e-9
    assert result['root_support_work_J']==pytest.approx(2e-10,abs=1e-24)
    assert result['metrics']['support_work']==pytest.approx(2e-5)
    assert not result['diagnostic_limits_satisfied']

def test_native_energy_is_mandatory_and_inconsistent_energy_fails_aggregate():
    c,r,m,d=fixture();r.pop('internal_energy_SI_J')
    with pytest.raises(ValueError,match='energy required'):measure(c,r,m,d,ARTIFACTS)
    c,r,m,d=fixture();r['internal_energy_SI_J']*=1.01
    result=measure(c,r,m,d,ARTIFACTS)
    assert not result['energy_work_diagnostic_limit_satisfied'] and not result['diagnostic_limits_satisfied']

@pytest.mark.parametrize('nz',[4,8])
def test_thickness_only20x8_solid_admission_and_independent_native_grid(nz):
    assert registration('Mx',80,32,nz,ARTIFACTS,reference_mesh=(20,8))['model']['case']['reference_mesh']==[20,8]
    for mesh in ((10,4),(40,16)):
        with pytest.raises(ValueError):registration('Mx',80,32,nz,ARTIFACTS,reference_mesh=mesh)

def fixture(load='Mx'):
    c=registration(load,20,8,2,ARTIFACTS)
    m=c['model'];nodes=dict(zip(m['node_ids'],m['coordinates']));W=np.array(c['wrench_SI'])
    pq=W*1e-5;port=np.array(m['case']['port_m'])
    r=dict(registration_sha256=c['registration_sha256'],status='completed',domain='native',
        reaction_provenance='direct-zero-SPC-physical-root',precision='binary64_physical_fields',frame_rotation=np.eye(3).tolist(),
        frame_origin_SI=[0.,0.,0.],units=dict(length_to_m=1.,force_to_N=1.),
        port_pose=[pq.tolist()],applied_wrench=[W.tolist()],internal_energy_SI_J=.5*float(W@pq),
        energy_provenance='independent-internal-operator',beam_coordinates=pq.tolist()+[0.]*36)
    for group in ('root','patch'):
        ids=list(m[group+'_nodes']);xyz=np.array([nodes[n] for n in ids]);n=len(ids)
        if group=='patch':
            pose=np.c_[pq[:3]+np.cross(pq[3:],xyz-port),np.broadcast_to(pq[3:],(n,3))]
            action=np.broadcast_to(W/n,(n,6)).copy()
            # Forces applied at off-port vertices have a total lever-arm moment;
            # compensate with the physical nodal moment map, without changing W.
            action[:,3:]-=np.cross(xyz-port,action[:,:3])
        else:
            pose=np.zeros((n,6));reaction=np.r_[-W[:3],-W[3:]-np.cross(port,W[:3])]
            action=np.broadcast_to(reaction/n,(n,6)).copy()
            action[:,3:]-=np.cross(xyz,action[:,:3])
        r[group]=dict(node_ids=ids,coordinates=xyz.tolist(),poses=pose.tolist(),actions=action.tolist())
    deck,_=build_precision_deck(20,8,1,load,nz=2)
    return c,r,m,deck

def evaluate(parts):return measure(*parts,ARTIFACTS)

@pytest.mark.parametrize('load',['Fz','Mx','My'])
def test_complete_manufactured_balance_pose_virtualwork_and_not_qualification(load):
    c,r,m,d=fixture(load);result=measure(c,r,m,d,ARTIFACTS)
    assert result['diagnostic_limits_satisfied']
    assert not result['qualification'] and c['convergence']['engineering_convergence_assessment'] is None
    assert result['physical_work_denominator_J']==pytest.approx(np.array(c['wrench_SI'])@np.array(r['port_pose'])[0])
    assert result['energy_work_relative_gap']==pytest.approx(0.)
    assert max(result['metrics'].values())<1e-14

def transform(r,R,o,length_unit,force_unit):
    r=copy.deepcopy(r);r['frame_rotation']=R.tolist();r['frame_origin_SI']=o.tolist()
    r['units']=dict(length_to_m=length_unit,force_to_N=force_unit)
    for name in ('root','patch'):
        v=r[name];v['coordinates']=((np.array(v['coordinates'])-o)@R/length_unit).tolist()
        q=np.array(v['poses']);q[:,:3]=q[:,:3]@R/length_unit;q[:,3:]=q[:,3:]@R;v['poses']=q.tolist()
        w=np.array(v['actions']);w[:,:3]=w[:,:3]@R/force_unit;w[:,3:]=w[:,3:]@R/(force_unit*length_unit);v['actions']=w.tolist()
    for name,is_pose in [('port_pose',True),('applied_wrench',False)]:
        a=np.array(r[name]);a[:,:3]=a[:,:3]@R/(length_unit if is_pose else force_unit)
        a[:,3:]=a[:,3:]@R/(1 if is_pose else force_unit*length_unit);r[name]=a.tolist()
    r['beam_coordinates'][:6]=r['port_pose'][0]
    return r

@pytest.mark.parametrize('load',['Fz','Mx','My'])
def test_equivalent_mm_kN_and_changed_proper_frame_origin(load):
    c,r,m,d=fixture(load)
    R=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    moved=transform(r,R,np.array([2.,-3.,.7]),.001,1000.)
    a=measure(c,r,m,d,ARTIFACTS);b=measure(c,moved,m,d,ARTIFACTS)
    assert b['diagnostic_limits_satisfied']
    assert b['port_work_J']==pytest.approx(a['port_work_J'],rel=1e-14)
    assert b['patch_work_J']==pytest.approx(a['patch_work_J'],rel=1e-14)
    assert b['root_wrench_residual_SI']==pytest.approx(a['root_wrench_residual_SI'],abs=1e-14)
    assert b['scales']==a['scales']

def test_unloaded_channel_and_wrong_sign_lever_arm_are_not_masked():
    c,r,m,d=fixture('Fz');r['root']['actions'][0][0]+=2e-7
    a=measure(c,r,m,d,ARTIFACTS)
    assert a['metrics']['force_balance']>=2e-8 and not a['diagnostic_limits_satisfied']
    c,r,m,d=fixture('Fz');r['root']['actions'][0][4]*=-1
    assert not measure(c,r,m,d,ARTIFACTS)['diagnostic_limits_satisfied']

def test_actual_work_denominator_not_characteristic_one_joule_floor():
    c,r,m,d=fixture();q=1e-12
    r['port_pose']=(np.array(r['port_pose'])*q).tolist()
    r['beam_coordinates'][:6]=r['port_pose'][0]
    r['patch']['poses']=(np.array(r['patch']['poses'])*q).tolist()
    r['internal_energy_SI_J']*=q;r['patch']['actions'][0][3]*=1.01
    a=measure(c,r,m,d,ARTIFACTS)
    assert a['physical_work_denominator_J']==pytest.approx(1e-17,abs=1e-30)
    assert a['metrics']['work_duality']>1e-5 and not a['diagnostic_limits_satisfied']

@pytest.mark.parametrize('mutation',[
    lambda c,r,m,d:c['thresholds'].update(balance=1e-7),
    lambda c,r,m,d:r.update(registration_sha256='0'*64),
    lambda c,r,m,d:r.update(reaction_provenance='rigid-MPC-FORC'),
    lambda c,r,m,d:r['root']['node_ids'].pop(),
    lambda c,r,m,d:r['patch']['node_ids'].pop(),
    lambda c,r,m,d:r['port_pose'][0].__setitem__(3,0.),
    lambda c,r,m,d:r.update(energy_provenance='applied_work_divided_by_two'),
    lambda c,r,m,d:r['frame_rotation'][0].__setitem__(0,-1.),
    lambda c,r,m,d:m['coordinates'][0].__setitem__(0,.01) if isinstance(m['coordinates'][0],list) else m.update(fixed='nonzero'),
    lambda c,r,m,d:r['patch']['poses'][0].__setitem__(0,float('nan')),
    lambda c,r,m,d:r['applied_wrench'][0].__setitem__(2,1.),
    lambda c,r,m,d:r.update(precision='printed-seven-digit'),
    lambda c,r,m,d:r.update(beam_coordinates=[0.]*18),
])
def test_strict_refusals(mutation):
    c,r,m,d=fixture();m=copy.deepcopy(m);mutation(c,r,m,d)
    with pytest.raises(ValueError):measure(c,r,m,d,ARTIFACTS)

@pytest.mark.parametrize('load',['Fz','Mx','My'])
@pytest.mark.parametrize('pair',[(10,4,10,4),(20,8,20,8),(40,16,40,16),(80,32,40,16)])
def test_literal_native_solid_load_geometry_axes_and_input_grid_identity(load,pair):
    nx,ny,rx,ry=pair;c=registration(load,nx,ny,2,ARTIFACTS,reference_mesh=(rx,ry))
    deck,candidate=build_precision_deck(rx,ry,1,load,nz=2);b=candidate['base']
    assert (c['model']['case']['nx'],c['model']['case']['ny'])==(nx,ny)
    assert c['model']['case']['reference_mesh']==[rx,ry]
    assert c['wrench_SI']==list(b['applied_force_N'])+list(b['applied_moment_Nm'])
    assert c['model']['case']['port_m']==list(b['control_nodes'][b['controls']['patch_ref']])
    assert c['model']['beam_positions']==[[.9,0.,.05],[.95,0.,.05],[1.,0.,.05]]
    assert c['model']['fixed']=='all six root coordinates zero'
    assert c['model']['case']['offset_sign']==1 and c['model']['case']['load_sign']==1
    assert c['model']['beam_frames']==[np.eye(3).tolist()]*3
    assert c['solid_geometry']['node_ids']==list(b['physical_nodes'])
    with pytest.raises(ValueError):registration(load,nx,ny,2,ARTIFACTS,sign=-1,reference_mesh=(rx,ry))

def test_input_and_artifact_tamper_refused_and_reference_mesh_explicit():
    c,r,m,d=fixture()
    with pytest.raises(ValueError):measure(c,r,m,d+'\n',ARTIFACTS)
    with pytest.raises(ValueError):measure(c,r,m,d,dict(ARTIFACTS,native_wheel='0'*64))
    with pytest.raises(ValueError):registration('mixed',40,16,2,ARTIFACTS)
    fine=registration('My',80,32,2,ARTIFACTS)
    assert fine['model']['case']['nx']==80 and fine['model']['case']['reference_mesh']==[40,16]
    assert registration('My',80,32,8,ARTIFACTS,reference_mesh=(20,8))['model']['case']['nz']==8

def test_bad_rotation_gap_zero_finalpair_and_unit_metadata_refused():
    c,r,m,d=fixture();r['patch']['poses'][0][4]=2e-9
    assert not measure(c,r,m,d,ARTIFACTS)['diagnostic_limits_satisfied']
    c,r,m,d=fixture();r['units']['rotation_scale']=.5
    with pytest.raises(ValueError):measure(c,r,m,d,ARTIFACTS)

@pytest.mark.parametrize('load',['Fz','Mx','My'])
def test_full_solid_volume_patch_root_force_couples_without_invented_nodal_directors(load):
    c,r,m,d=fixture(load);r['domain']='solid';solid=c['solid_geometry']
    nodes=dict(zip(solid['node_ids'],solid['coordinates']));port=np.array(m['case']['port_m'])
    W=np.array(c['wrench_SI']);pq=np.array(r['port_pose'])[0]
    for name in ('patch','root'):
        ids=solid[name+'_nodes'];xyz=np.array([nodes[n] for n in ids]);n=len(ids)
        origin=port if name=='patch' else np.zeros(3)
        arms=xyz-origin;B=np.zeros((6,3*n));B[:3]=np.tile(np.eye(3),(1,n))
        for i,(x,y,z) in enumerate(arms):B[3:,3*i:3*i+3]=[[0,-z,y],[z,0,-x],[-y,x,0]]
        target=W if name=='patch' else np.r_[-W[:3],-W[3:]-np.cross(port,W[:3])]
        force=(B.T@np.linalg.solve(B@B.T,target)).reshape(n,3)
        q=pq[:3]+np.cross(pq[3:],xyz-port) if name=='patch' else np.zeros((n,3))
        r[name]=dict(node_ids=ids,coordinates=xyz.tolist(),poses=q.tolist(),actions=force.tolist())
    r.pop('internal_energy_SI_J')  # actual solid energy is optional corroboration
    result=measure(c,r,m,d,ARTIFACTS)
    assert result['diagnostic_limits_satisfied'] and result['observation_domain']=='solid'
    assert result['metrics']['work_duality']<1e-12
    # Physical midside/thickness coverage is mandatory, not merely corner samples.
    r['root']['node_ids']=r['root']['node_ids'][::2]
    with pytest.raises(ValueError):measure(c,r,m,d,ARTIFACTS)
