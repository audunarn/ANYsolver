"""Prospective restricted E02 measurements. No solver or qualification authority.

Canonical SI geometry and physical origin are fixed. Input load-derived scales
never depend on displacement. Actual nonzero physical pairing is the work
denominator; characteristic F*L is recorded only, never a substitute for it.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import numpy as np
from scripts.r8_e02_native_rigid_tip import geometry
from scripts.r8_e02_rigid_torque_refinement import geometry80,geometry_identity
from scripts.r8_e02_rigid_precision import build_precision_deck
from scripts.r8_e02_rigid_tip_reference import LOADS

SCHEMA='E02_FIXED_RIGID_REFERENCE_LINEAR_PROPOSAL_V1'
ARTIFACT_KEYS=('native_source','native_wheel','native_site_manifest','external_executable')

def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _hex(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def _nodes(nx,ny):
    return geometry80() if (nx,ny)==(80,32) else geometry(nx,ny)

def registration(load,nx,ny,nz,artifacts,sign=1,reference_mesh=None):
    """Proposal only: exact model/input bytes; formal convergence rule unresolved."""
    if load not in ('Fz','Mx','My') or sign!=1 or (nx,ny) not in ((10,4),(20,8),(40,16),(80,32)) or nz not in (2,4,8):
        raise ValueError('only +offset/+load pure Fz/Mx/My fixed linear refinement family; signed obligations remain open')
    if set(artifacts)!=set(ARTIFACT_KEYS) or not all(_hex(v) for v in artifacts.values()):
        raise ValueError('complete exact source/wheel/site/executable SHA256 binding required')
    reference_mesh=tuple(reference_mesh) if reference_mesh is not None else ((40,16) if nx==80 else (nx,ny))
    nodes,cells,patch,selected,root=_nodes(nx,ny)
    _,base=geometry_identity()
    base['beam_frames']=[np.eye(3).tolist()]*3
    base.update(case=dict(nx=nx,ny=ny,nz=nz,load=load,sign=sign,E_Pa=210e9,nu=.3,thickness_m=.02,
        length_m=1.,width_m=.2,port_m=[.9,0.,.05],offset_sign=1,load_sign=1,
        reference_mesh=list(reference_mesh)),node_ids=list(nodes),coordinates=list(nodes.values()),
        cells=cells,patch_cells=patch,patch_nodes=selected,root_nodes=root)
    deck,candidate=build_precision_deck(*reference_mesh,sign,load,nz=nz)
    wrench=np.array(LOADS[load],dtype=float).ravel()
    length=1.;force=float(np.linalg.norm(np.r_[wrench[:3],wrench[3:]/length]))
    solid=candidate['base']
    solid_nodes={int(n):p for n,p in solid['physical_nodes'].items()}
    result=dict(schema=SCHEMA,status='PROPOSED_NOT_ADOPTED',model=base,model_sha256=identity(base),
        solid_geometry=dict(node_ids=list(solid_nodes),coordinates=list(solid_nodes.values()),
            root_nodes=list(solid['root_nodes']),patch_nodes=list(solid['patch_nodes'])),
        native_input_sha256=identity(base),external_deck_sha256=hashlib.sha256(deck.encode()).hexdigest(),
        artifacts=dict(artifacts),wrench_SI=wrench.tolist(),origin_SI=[0.,0.,0.],
        scales=dict(length_m=length,force_N=force,moment_Nm=force*length,
            translation_m=length,rotation_rad=1.,characteristic_work_J=force*length),
        thresholds=dict(balance=1e-8,physical_work=1e-8,constraint=1e-9,matched_converged_linear=.01),
        convergence=dict(minimum_refinement_levels=3,engineering_convergence_assessment=None,
            applicability_review=None,matched_quantity_registration=None),
        separate_obligations=['negative offset/load signs','normal spin','general six-channel','nonlinear','distributing','BL5','B2'],
        qualification=False)
    result['registration_sha256']=identity(result)
    return result

def _array(value,shape,name):
    a=np.asarray(value,dtype=float)
    if a.shape!=shape or not np.isfinite(a).all():raise ValueError('complete finite '+name+' required')
    return a

def matched_port_work(native_J,reference_J):
    """Provisional 1% comparison; neither last-change nor this is convergence.

    The physical reference work supplies the nonzero relative denominator.
    A reviewed quantity set and independent engineering convergence assessment
    across at least three systematic levels remain missing.
    """
    native_J=float(native_J);reference_J=float(reference_J)
    if not math.isfinite(native_J) or not math.isfinite(reference_J) or reference_J==0:
        raise ValueError('finite matched work and nonzero physical reference required')
    relative=(native_J-reference_J)/abs(reference_J)
    return dict(quantity='physical_port_work_J',native_J=native_J,reference_J=reference_J,
        signed_relative_difference=relative,relative_difference=abs(relative),
        provisional_one_percent_limit_satisfied=abs(relative)<=.01,
        qualification=False,convergence_status='NOT_ADJUDICATED',
        blocker='independent engineering convergence assessment across at least three systematic levels and applicability review missing')

def _transform(record):
    r=_array(record['frame_rotation'],(3,3),'proper frame')
    if not np.allclose(r.T@r,np.eye(3),rtol=0,atol=1e-14) or abs(np.linalg.det(r)-1)>1e-14:
        raise ValueError('proper orthonormal physical frame required')
    origin=_array(record['frame_origin_SI'],(3,),'frame origin')
    units=record['units']
    if set(units)!= {'length_to_m','force_to_N'}:raise ValueError('explicit consistent length/force units required')
    l=float(units['length_to_m']);f=float(units['force_to_N'])
    if not math.isfinite(l*f) or min(l,f)<=0:raise ValueError('positive finite unit conversion required')
    def pose(a):
        return np.c_[l*a[:,:3]@r.T,a[:,3:]@r.T]
    def action(a):
        return np.c_[f*a[:,:3]@r.T,(f*l)*a[:,3:]@r.T]
    return r,origin,l,f,pose,action

def measure(contract,record,native_input,external_deck,artifacts):
    """Evaluate actual observations provisionally; always qualification=False.

    native_input is the exact canonical public-construction record; external_deck
    is original staged text. Frames/units describe observations, not changed laws.
    A producer must retain raw output, actual reaction provenance and energy
    provenance; this kernel cannot certify a self-asserted external field.
    """
    model=contract['model'];case=model['case']
    expected=registration(case['load'],case['nx'],case['ny'],case['nz'],artifacts,case['sign'],case['reference_mesh'])
    if identity(contract)!=identity(expected) or identity(native_input)!=contract['native_input_sha256'] or hashlib.sha256(external_deck.encode()).hexdigest()!=contract['external_deck_sha256']:
        raise ValueError('exact prospective registration/model/input/artifact identity mismatch')
    if record.get('registration_sha256')!=contract['registration_sha256']:
        raise ValueError('observation belongs to another candidate')
    if record.get('status')!='completed' or record.get('reaction_provenance')!='direct-zero-SPC-physical-root':
        raise ValueError('completed physical zero-SPC support reactions required; MPC field not independently admitted')
    if record.get('precision')!='binary64_physical_fields':
        raise ValueError('printed/unknown physical field uncertainty cannot certify 1e-8 work/balance')
    r,o,l,f,pose,action=_transform(record)
    domain=record.get('domain')
    if domain not in ('native','solid'):raise ValueError('explicit physical native or solid observation domain required')
    physical=model if domain=='native' else contract['solid_geometry']
    nodes={n:np.array(p) for n,p in zip(physical['node_ids'],physical['coordinates'])}
    groups={}
    for name in ('root','patch'):
        ids=list(physical[name+'_nodes']);raw=record[name]
        if raw['node_ids']!=ids:raise ValueError('complete exact '+name+' nodes required')
        xyz=_array(raw['coordinates'],(len(ids),3),name+' coordinates')*l@r.T+o
        if not np.allclose(xyz,np.array([nodes[n] for n in ids]),rtol=0,atol=1e-14):
            raise ValueError('physical '+name+' geometry changed beyond coordinate roundoff')
        dofs=6 if domain=='native' else 3
        rawq=_array(raw['poses'],(len(ids),dofs),name+' poses')
        raww=_array(raw['actions'],(len(ids),dofs),name+' actions')
        if domain=='solid':
            rawq=np.c_[rawq,np.zeros_like(rawq)];raww=np.c_[raww,np.zeros_like(raww)]
        q=pose(rawq);w=action(raww)
        groups[name]=(xyz,q,w)
    port=np.array(case['port_m']);pq=pose(_array(record['port_pose'],(1,6),'port pose'))[0]
    if domain=='native':
        beam=_array(record.get('beam_coordinates'),(42,),'native nodal plus retained beam variables')
        if not np.array_equal(beam[:6],np.array(record['port_pose'])[0]):
            raise ValueError('physical port must be actual native beam first six coordinates')
    load=action(_array(record['applied_wrench'],(1,6),'pure applied wrench'))[0]
    if not np.allclose(load,contract['wrench_SI'],rtol=0,atol=1e-14):raise ValueError('pure registered physical load changed')
    def wrench(xyz,w,origin):
        moments=w[:,3:]+np.cross(xyz-origin,w[:,:3])
        return np.array([math.fsum(w[:,j]) for j in range(3)]+[math.fsum(moments[:,j]) for j in range(3)])
    rootx,rootq,rootw=groups['root'];patchx,patchq,patchw=groups['patch']
    reaction=wrench(rootx,rootw,np.array(contract['origin_SI']))
    applied=np.r_[load[:3],load[3:]+np.cross(port,load[:3])]
    residual=reaction+applied
    transferred=wrench(patchx,patchw,port);coefficient=transferred-load
    predicted=np.c_[pq[:3]+np.cross(pq[3:],patchx-port),np.broadcast_to(pq[3:],(len(patchx),3))]
    scales=contract['scales'];F=scales['force_N'];M=scales['moment_Nm'];L=scales['length_m']
    fn=lambda v:float(np.linalg.norm(v))
    patchgap=patchq-predicted
    if domain=='solid':patchgap[:,3:]=0.  # solid has no nodal rotation coordinate
    constraint=max(float(np.max(np.linalg.norm(patchgap[:,:3],axis=1)))/L,
        float(np.max(np.linalg.norm(patchgap[:,3:],axis=1))),
        float(np.max(np.linalg.norm(rootq[:,:3],axis=1)))/L,float(np.max(np.linalg.norm(rootq[:,3:],axis=1))))
    portwork=float(load@pq)
    if not math.isfinite(portwork) or portwork==0:raise ValueError('physical nonzero final work denominator unresolved')
    patchwork=math.fsum(float(a@b) for a,b in zip(patchw,patchq))
    dual_error=abs(patchwork-portwork)/abs(portwork)
    rootwork=math.fsum(float(a@b) for a,b in zip(rootw,rootq))
    support_work_error=abs(rootwork)/abs(portwork)
    energy=record.get('internal_energy_SI_J')
    if domain=='native' and energy is None:
        raise ValueError('native independent internal-operator energy required for diagnostic success')
    energy_gap=None
    if energy is not None:
        if record.get('energy_provenance')!='independent-internal-operator' or not math.isfinite(float(energy)) or float(energy)<=0:
            raise ValueError('independent positive physical energy provenance required; applied-work reconstruction refused')
        energy_gap=abs(2*float(energy)-portwork)/abs(portwork)
    metrics=dict(force_balance=fn(residual[:3])/F,moment_balance=fn(residual[3:])/M,
        work_duality=dual_error,support_work=support_work_error,scaled_constraint=constraint,
        virtual_field_force_coefficient=fn(coefficient[:3])/F,virtual_field_moment_coefficient=fn(coefficient[3:])/M)
    return dict(status='PROVISIONAL_DIAGNOSTICS_ONLY',qualification=False,registration_sha256=contract['registration_sha256'],
        scales=scales,physical_work_denominator_J=abs(portwork),port_work_J=portwork,patch_work_J=patchwork,
        root_support_work_J=rootwork,
        root_wrench_residual_SI=residual.tolist(),patch_wrench_error_SI=coefficient.tolist(),metrics=metrics,
        diagnostic_limits_satisfied=(metrics['force_balance']<=1e-8 and metrics['moment_balance']<=1e-8 and
            metrics['work_duality']<=1e-8 and metrics['scaled_constraint']<=1e-9 and
            metrics['support_work']<=1e-8 and (domain!='native' or energy_gap<=1e-8) and
            metrics['virtual_field_force_coefficient']<=1e-8 and metrics['virtual_field_moment_coefficient']<=1e-8),
        independent_internal_energy_J=energy,energy_work_relative_gap=energy_gap,
        energy_work_diagnostic_limit_satisfied=(energy_gap<=1e-8 if energy_gap is not None else None),
        observation_domain=domain,formal_blockers=['contract not adopted','independent engineering convergence assessment missing',
            'three-level native and external convergence not adjudicated for every registered quantity/load',
            'solid/shell reference applicability and matched quantity set not adopted','independent acceptance outstanding'])
