"""Literal current producer input/admission controls, no physical solve."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from scripts.r8_e02_rigid_principal_current import admitted,binding,prepare,staged,observation,accurate_rigid_fit,parse_current_solid,ordinary_rigid_observation,read_double_output
from scripts.r8_e02_rigid_precision import build_precision_deck,root_elimination_proof
from scripts.r8_e02_rigid_tip_reference import LOADS
from scripts.r8_e02_rigid_acceptance import identity,measure

@pytest.mark.parametrize('load',['Fz','My'])
def test_principal_actual_saved_caller_serializes_and_keeps_print_flags(tmp_path,load):
    from scripts.r8_e02_rigid_principal_current import solid
    case=Path(__file__).resolve().parents[1]/'.development/e02-rigid-principal-current-20261009-v1/cases'/load
    if load=='My':
        with pytest.raises(RuntimeError,match='physical guard failure'):
            solid(load,case,principal_observation=True,output_path=tmp_path)
    else:solid(load,case,principal_observation=True,output_path=tmp_path)
    parsed=json.loads((tmp_path/'solid-parse.json').read_text())
    metrics=json.loads((tmp_path/'solid-metrics.json').read_text())
    assert metrics['diagnostic_limits_satisfied']==(load=='Fz')
    if load=='My':assert metrics['metrics']['force_balance']>1e-8
    assert len(parsed['six_component_print_comparison'])==6
    failed=[x['component'] for x in parsed['six_component_print_comparison'] if not x['accurate_pass']]
    assert failed==(['thetaX'] if load=='My' else [])
    assert parsed['supporting_print_interval_status']==('FAILED' if load=='My' else 'PASSED')
    assert all(type(x) is bool for x in parsed['ordinary_port']['dual_checks_passed'])

@pytest.mark.parametrize('tamper',['loadcontrol','unloadedcontrol','multiple','binary','energy','stdout','geometry'])
def test_principal_observation_retains_loaded_control_and_structural_refusals(tamper):
    args=saved_fz();case=Path(__file__).resolve().parents[1]/'.development/e02-rigid-principal-current-20261009-v1/cases/My'
    args.update(data=(case/'reference.frd').read_bytes(),dat=(case/'reference.dat').read_text(),
        stdout=(case/'stdout.txt').read_text(),deck=(case/'reference.inp').read_text(),manifest=json.loads((case/'candidate.json').read_text()))
    if tamper=='loadcontrol':args['dat']=args['dat'].replace('2.807432E-05','3.807432E-05')
    elif tamper=='unloadedcontrol':args['dat']=args['dat'].replace('-8.859593E-15','-8.859593E-10')
    elif tamper=='multiple':args['dat']=args['dat'].replace('5.475376E-16','5.475376E-10')
    elif tamper=='binary':args['data']=args['data'][:-28]
    elif tamper=='energy':args['dat']=args['dat'].replace('internal energy (element, energy)','unsupported energy (element, energy)')
    elif tamper=='stdout':args['stdout']+='\n*ERROR: manufactured failure\n'
    else:args['manifest']['base']['nx']=20
    with pytest.raises(ValueError):parse_current_solid(**args,principal_observation=True)

def saved_fz():
    case=Path(__file__).resolve().parents[1]/'.development/e02-rigid-principal-current-20261009-v1/cases/Fz'
    return dict(data=(case/'reference.frd').read_bytes(),dat=(case/'reference.dat').read_text(),
        stdout=(case/'stdout.txt').read_text(),deck=(case/'reference.inp').read_text(),
        manifest=json.loads((case/'candidate.json').read_text()))

def test_accurate_rigid_fit_recovers_manufactured_pose_and_refuses_nonrigid_or_degenerate():
    p=np.array([[x,y,z] for x in (.8,.9,1.) for y in (-.1,.1) for z in (-.01,.01)])
    port=np.array([.9,0.,.05]);v=np.array([1e-6,-3e-15,8e-5]);theta=np.array([5e-14,-1e-4,-1e-15])
    u=v+np.cross(theta,p-port);r=accurate_rigid_fit(p,u,port)
    assert r['translation_m']==pytest.approx(v,abs=1e-20)
    assert r['theta_rad']==pytest.approx(theta,abs=1e-19)
    u[0,2]+=1e-6
    with pytest.raises(ValueError):accurate_rigid_fit(p,u,port)
    with pytest.raises(ValueError):accurate_rigid_fit(np.array([[0,0,0],[1,0,0],[2,0,0]]),np.zeros((3,3)),port)
    with pytest.raises(ValueError):accurate_rigid_fit(p,np.full_like(p,np.nan),port)

def test_saved_fz_accurate_pose_preserves_all_original_print_intervals_and_old_failure():
    r=parse_current_solid(**saved_fz())
    assert not r['ordinary_strict_comparison_passed']
    assert [v['component'] for v in r['six_component_print_comparison'] if not v['ordinary_pass']]==['Uy','thetaX']
    assert all(v['accurate_pass'] for v in r['six_component_print_comparison'])
    assert r['root_displacement_max_m']==0. and r['root_binary_field_is_reaction']
    assert r['port']['rigid_mapping_max_gap_m']<1e-18
    assert not r['can_certify_energy_work_1e_minus_8']

def test_saved_my_accurate_dual_retains_historical_failed_diagnostic():
    args=saved_fz();case=Path(__file__).resolve().parents[1]/'.development/e02-rigid-principal-current-20261009-v1/cases/My'
    args.update(data=(case/'reference.frd').read_bytes(),dat=(case/'reference.dat').read_text(),
        stdout=(case/'stdout.txt').read_text(),deck=(case/'reference.inp').read_text(),
        manifest=json.loads((case/'candidate.json').read_text()))
    base=args['manifest']['base'];u,rf=read_double_output(args['data'],base)
    physical={int(n):p for n,p in base['physical_nodes'].items()};ids=base['patch_nodes']
    values=([physical[n] for n in ids],[u[n] for n in ids],base['control_nodes'][str(base['controls']['patch_ref'])],base['applied_force_N'],base['applied_moment_Nm'])
    assert ordinary_rigid_observation(*values)['dual_checks_passed']==[False,True,True]
    assert accurate_rigid_fit(*values)['dual_checks_passed']==[True]*3
    # Corrected arithmetic must still refuse the saved My control mismatch.
    with pytest.raises(ValueError,match='original printed control rounding'):parse_current_solid(**args)
    args['data']=args['data'][:-28]
    with pytest.raises(ValueError):parse_current_solid(**args)

def test_accurate_dual_manufactured_work_and_refusals():
    p=np.array([[x,y,z] for x in (.8,.9,1.) for y in (-.1,.1) for z in (-.01,.01)])
    port=np.array([.9,0.,.05]);v=np.array([2e-5,-3e-6,8e-5]);theta=np.array([3e-5,-1e-4,2e-6])
    u=v+np.cross(theta,p-port);F=np.array([0.,0.,10.]);M=np.array([0.,1.,0.])
    r=accurate_rigid_fit(p,u,port,F,M)
    assert r['external_final_pairing_J']==pytest.approx(F@v+M@theta,rel=1e-14)
    assert r['load_resultant_N']==pytest.approx(F,abs=1e-70)
    assert r['load_moment_about_port_Nm']==pytest.approx(M,abs=1e-70)
    assert r['dual_checks_passed']==[True]*3
    for f,m in ((F,None),(F,[np.nan,0.,0.]),([0.,10.],M)):
        with pytest.raises(ValueError):accurate_rigid_fit(p,u,port,f,m)
    u[0,1]+=1e-4
    with pytest.raises(ValueError):accurate_rigid_fit(p,u,port,F,M)

@pytest.mark.parametrize('tamper',['control','energy','binary','stdout','geometry'])
def test_saved_fz_accurate_parser_keeps_structural_and_print_refusals(tamper):
    args=saved_fz()
    if tamper=='control':args['dat']=args['dat'].replace('-3.204015E-15','-4.204015E-15')
    elif tamper=='energy':args['dat']=args['dat'].replace('internal energy (element, energy)','unsupported energy (element, energy)')
    elif tamper=='binary':args['data']=args['data'][:-28]
    elif tamper=='stdout':args['stdout']+='\n*ERROR: manufactured fatal diagnostic\n'
    else:args['manifest']['base']['nx']=20
    with pytest.raises(ValueError):parse_current_solid(**args)

@pytest.mark.parametrize('load',['Fz','My'])
def test_actual_current_load_full_geometry_and_artifact_inputs(tmp_path,load):
    c,d,m,a=prepare(load,tmp_path/load)
    assert c['wrench_SI']==np.array(LOADS[load]).ravel().tolist()
    assert c['model']['case']['port_m']==[.9,0.,.05]
    assert c['model']['beam_frames']==[np.eye(3).tolist()]*3
    assert len(c['model']['node_ids'])==697 and len(c['model']['cells'])==640
    assert len(c['solid_geometry']['node_ids'])==7493
    assert c['solid_geometry']['root_nodes']==m['base']['root_nodes']
    assert d==build_precision_deck(40,16,1,load,nz=2)[0]
    assert staged(load,tmp_path/load)==(json.loads(json.dumps(c)),d,json.loads(json.dumps(m)),a)
    proof=root_elimination_proof(m['base'])
    assert proof['both_directions_proved']
    record=observation(c,'solid');assert record['domain']=='solid' and record['applied_wrench']==[c['wrench_SI']]
    assert not c['qualification']

@pytest.mark.parametrize('load',['Mx','mixed','Fz-','My-negative-offset'])
def test_no_mx_mixed_or_new_sign_case(load):
    with pytest.raises(ValueError):admitted(load)

@pytest.mark.parametrize('field',['contract','native-input','candidate','reference'])
def test_staging_bytes_and_semantics_tamper_refusal(tmp_path,field):
    prepare('Fz',tmp_path/'Fz')
    path=tmp_path/'Fz'/('reference.inp' if field=='reference' else field+'.json')
    if field=='reference':path.write_text(path.read_text()+'\n')
    else:
        value=json.loads(path.read_text());value['tamper']=True;path.write_text(json.dumps(value))
    with pytest.raises(ValueError):staged('Fz',tmp_path/'Fz')

def test_geometry_and_load_identity_are_independent(tmp_path):
    f,d,_,_=prepare('Fz',tmp_path/'Fz');m,e,_,_=prepare('My',tmp_path/'My')
    assert f['native_input_sha256']!=m['native_input_sha256'] and d!=e
    assert f['artifacts']==m['artifacts']

@pytest.mark.parametrize('load',['Fz','My'])
def test_actual_prepare_save_staged_to_measure_roundtrip(tmp_path,load):
    prepare(load,tmp_path/load);c,d,m,a=staged(load,tmp_path/load)
    nodes=dict(zip(c['model']['node_ids'],c['model']['coordinates']));W=np.array(c['wrench_SI'])
    pq=W*1e-5;port=np.array(c['model']['case']['port_m']);record=observation(c,'native')
    record.update(port_pose=[pq.tolist()],beam_coordinates=pq.tolist()+[0.]*36,
        internal_energy_SI_J=.5*float(W@pq),energy_provenance='independent-internal-operator')
    for name in ('root','patch'):
        ids=c['model'][name+'_nodes'];xyz=np.array([nodes[n] for n in ids]);n=len(ids)
        if name=='patch':
            poses=np.c_[pq[:3]+np.cross(pq[3:],xyz-port),np.broadcast_to(pq[3:],(n,3))]
            actions=np.broadcast_to(W/n,(n,6)).copy();actions[:,3:]-=np.cross(xyz-port,actions[:,:3])
        else:
            poses=np.zeros((n,6));target=np.r_[-W[:3],-W[3:]-np.cross(port,W[:3])]
            actions=np.broadcast_to(target/n,(n,6)).copy();actions[:,3:]-=np.cross(xyz,actions[:,:3])
        record[name]=dict(node_ids=ids,coordinates=xyz.tolist(),poses=poses.tolist(),actions=actions.tolist())
    assert measure(c,record,c['model'],d,a)['diagnostic_limits_satisfied']
    c['unregistered']='tamper'
    with pytest.raises(ValueError):measure(c,record,c['model'],d,a)
