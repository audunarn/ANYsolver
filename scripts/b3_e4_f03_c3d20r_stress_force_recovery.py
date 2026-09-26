"""Assemble C1 F5 stiffener weak forces from printed Gauss-point stress.

This is a bounded development diagnostic. Nodal interface forces are duals
to Q20 displacement interpolation, not pointwise continuum tractions. Their
integrated wrench is checked against the independent plate-support reaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import (
    read_deck, shape20, wrench)
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    parse_nodal_vectors, split_left_root_support_wrenches)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


# Exact C3D20R gauss3d2 point order in CalculiX gauss.f (xi fastest).
_G = np.array([(a,b,c) for c in (-1/np.sqrt(3),1/np.sqrt(3))
               for b in (-1/np.sqrt(3),1/np.sqrt(3))
               for a in (-1/np.sqrt(3),1/np.sqrt(3))])
_D = np.array([shape20(point)[1] for point in _G])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_stress(dat: Path, *, first_element: int,
                element_count: int) -> np.ndarray:
    """Read exactly one ordered STIFFENER Gauss stress block."""
    stress=np.empty((element_count,8,6))
    current=0
    headers=0
    inside=False
    for line in dat.open(errors='replace'):
        if 'stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set STIFFENER' in line:
            headers+=1
            inside=True
            continue
        if not inside:
            continue
        parts=line.split()
        if not parts:
            continue
        if len(parts)!=8 or not parts[0].isdigit():
            raise ValueError('unexpected stiffener stress row')
        element=int(parts[0])
        point=int(parts[1])
        if (element!=first_element+current//8 or
                point!=current%8+1 or current>=element_count*8):
            raise ValueError('incomplete or misordered Gauss stress inventory')
        stress[current//8,current%8]=[float(x) for x in parts[2:]]
        current+=1
    if headers!=1 or current!=element_count*8 or not np.isfinite(stress).all():
        raise ValueError('one finite, complete stiffener stress block required')
    return stress


def integrate(x: np.ndarray, connectivity: np.ndarray,
              stress6: np.ndarray) -> tuple[np.ndarray,float]:
    force=np.zeros_like(x)
    det_min=float('inf')
    for start in range(0,len(connectivity),128):
        conn=connectivity[start:start+128]
        local=x[conn]
        jac=np.einsum('eni,gnj->egij',local,_D)
        det=np.linalg.det(jac)
        if not np.isfinite(det).all() or np.min(det)<=0:
            raise ValueError('invalid C3D20R Jacobian')
        det_min=min(det_min,float(det.min()))
        grad=np.einsum('gnj,egji->egni',_D,np.linalg.inv(jac))
        s6=stress6[start:start+len(conn)]
        stress=np.empty((*s6.shape[:2],3,3))
        stress[...,0,0]=s6[...,0]
        stress[...,1,1]=s6[...,1]
        stress[...,2,2]=s6[...,2]
        stress[...,0,1]=stress[...,1,0]=s6[...,3]
        stress[...,0,2]=stress[...,2,0]=s6[...,4]
        stress[...,1,2]=stress[...,2,1]=s6[...,5]
        local_force=np.einsum('eg,egij,egnj->eni',det,stress,grad)
        np.add.at(force,conn.ravel(),local_force.reshape(-1,3))
    return force,det_min


def recover(folder: Path) -> dict:
    folder=folder.resolve()
    manifest=json.loads((folder/'manifest.json').read_text())
    result=json.loads((folder/'result.json').read_text())
    if result['status']!='COMPLETE_OUTPUT_ONLY_REPLAY' or manifest['omp_threads']!=1:
        raise ValueError('completed, one-thread output-only replay required')
    inp=folder/'solid-5-tip_mx.inp'
    dat=inp.with_suffix('.dat')
    frd=inp.with_suffix('.frd')
    model_path=Path(manifest['source_folder'])/'model.json'
    if not model_path.is_absolute():
        model_path=Path(__file__).resolve().parents[1]/model_path
    archived_frd=model_path.parent/'solid-5-tip_mx.frd'
    model=json.loads(model_path.read_text())
    x,elements=read_deck(inp)
    if len(elements['Plate'])!=model['plate_elements'] or len(elements['Stiffener'])!=model['bar_elements']:
        raise ValueError('replay element inventory mismatch')
    conn=elements['Stiffener']
    stress=read_stress(dat,first_element=len(elements['Plate'])+1,
                       element_count=len(conn))
    fint,minimum_det=integrate(x,conn,stress)
    load=np.zeros_like(x)
    for key,value in model['applied_nodal_forces_N'].items():
        load[int(key)]=value
    support=set(model['boundary_node_ids'])
    rf=parse_nodal_vectors(dat.read_text(errors='replace'),support,
                           'forces','SUPPORTS')
    printed=np.zeros_like(x)
    for node,value in rf.items():
        printed[node]=value
    bar_root=np.asarray(model['beam_root_node_ids'],dtype=np.int32)
    plate_root=np.asarray(model['plate_boundary_node_ids'],dtype=np.int32)
    seam=np.asarray(model['shared_interface_node_ids'],dtype=np.int32)
    bar_nodes=np.unique(conn.ravel())
    free=np.setdiff1d(bar_nodes,np.r_[bar_root,seam])
    residual=fint-load
    bar_on_plate=np.zeros_like(x)
    bar_on_plate[seam]=-residual[seam]
    support_inferred=-wrench(printed,x,plate_root)
    stress_inferred=wrench(bar_on_plate,x,seam)
    bar_root_stress=wrench(residual,x,bar_root)
    bar_root_printed=wrench(printed,x,bar_root)
    u=_read_frd_u(frd)
    if set(u)!=set(range(1,len(x))):
        raise ValueError('incomplete displacement output')
    archived_u=_read_frd_u(archived_frd)
    if set(archived_u)!=set(u):
        raise ValueError('archived and replayed displacement inventories differ')
    max_u_difference=max(float(np.max(np.abs(u[i]-archived_u[i]))) for i in u)
    displacement=np.array([[0,0,0]]+[u[i] for i in range(1,len(x))])
    # x-weighted work-conjugate first moments are low-order transfer
    # descriptors. Raw Q20 nodal signs and pointwise stresses are not.
    shifted=x[seam,0]-.95
    first_moment=np.einsum('n,ni->i',shifted,bar_on_plate[seam])
    integrated_error=stress_inferred-support_inferred
    free_error=float(np.max(np.abs(residual[free])))
    root_error=float(np.max(np.abs(residual[bar_root]-printed[bar_root])))
    if (max_u_difference!=0 or free_error>=1e-3 or root_error>=1e-3 or
            np.max(np.abs(integrated_error))>=1e-3):
        raise ArithmeticError('stress-force or archived-state parity failed')
    source_root=Path(__file__).resolve().parents[1]
    recovery_git=subprocess.run(('git','rev-parse','HEAD'),cwd=source_root,
                                capture_output=True,text=True,check=True).stdout.strip()
    return {
        'classification':'bounded integration-point stress/weak-force diagnostic; not interface qualification',
        'stress_replay_source_git':manifest['source_git'],
        'recovery_source_git':recovery_git,
        'recovery_script_sha256':sha(Path(__file__)),
        'inputs_sha256':{str(p.relative_to(source_root)):sha(p)
                         for p in (inp,dat,frd,model_path,archived_frd)},
        'inventory':{'stiffener_elements':len(conn),'integration_points':len(conn)*8,
                     'shared_bond_nodes':len(seam),'free_stiffener_nodes':len(free)},
        'minimum_jacobian_m3':minimum_det,
        'validation':{'maximum_replay_vs_archived_U_difference_m':max_u_difference,
                      'free_bar_residual_limit_N':1e-3,
                      'bar_root_RF_limit_N':1e-3,
                      'integrated_wrench_limit_N_Nm':1e-3,
                      'status':'PASSED_SAVED_STATE_AND_WEAK_FORCE_CHECKS'},
        'reconstruction':{
            'maximum_free_bar_residual_N':free_error,
            'rms_free_bar_residual_N':float(np.sqrt(np.mean(residual[free]**2))),
            'maximum_bar_root_RF_difference_N':root_error,
            'bar_root_stress_wrench_N_Nm':bar_root_stress.tolist(),
            'bar_root_printed_wrench_N_Nm':bar_root_printed.tolist(),
            'bar_on_plate_stress_wrench_N_Nm':stress_inferred.tolist(),
            'bar_on_plate_support_wrench_N_Nm':support_inferred.tolist(),
            'bar_on_plate_wrench_difference_N_Nm':integrated_error.tolist(),
            'seam_work_on_saved_displacement_J':float(np.sum(bar_on_plate[seam]*displacement[seam])),
            'x_first_moment_about_095_m_Nm':first_moment.tolist()},
        'meaning':'Stresses at gauss3d2 points integrated against Q20 shape gradients yield stiffener internal nodal forces. Minus stiffener residual at shared nodes is bar-on-plate action. Printed plate RF supplies an independent integrated wrench. The first x moment is a low-order dual descriptor; nodal force signs are not physical traction density.',
        'limits':['only stiffener stresses printed; plate-side local stress not reconstructed',
                  'pointwise interface traction and 3D/native pose equivalence not established',
                  'one physical pre-opened combined-load case at F5; no basis selection']}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    data=recover(args.folder)
    payload=json.dumps(data,indent=2,sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__=='__main__':
    main()
