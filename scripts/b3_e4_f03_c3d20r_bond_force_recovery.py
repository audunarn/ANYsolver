"""Recover weak bond forces from a saved, linear C3D20R solid solve.

Development diagnostic only.  The shared-node interface action is assembled
from the stiffener elements, less the applied stiffener tip loads.  It is not
a pointwise continuum traction or a qualification of the native line law.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_ccx_solid_bond_screen import parse_nodal_vectors
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


_CORNERS = np.array(((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                     (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)), dtype=float)
_EDGES = ((0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
          (0,4),(1,5),(2,6),(3,7))
_GAUSS = np.array([(a,b,c) for a in (-1/np.sqrt(3),1/np.sqrt(3))
                   for b in (-1/np.sqrt(3),1/np.sqrt(3))
                   for c in (-1/np.sqrt(3),1/np.sqrt(3))])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shape20(local: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Standard Q20 values and local derivatives in deck edge order."""
    x = np.asarray(local, dtype=float)
    values = np.empty(20)
    grad = np.empty((20,3))
    for n, signs in enumerate(_CORNERS):
        a,b,c = signs
        factors = 1 + signs*x
        linear = float(signs@x)-2
        values[n] = np.prod(factors)*linear/8
        for j in range(3):
            other = np.prod(np.delete(factors,j))
            grad[n,j] = signs[j]*other*(linear+factors[j])/8
    for n,(ia,ib) in enumerate(_EDGES,8):
        a,b = _CORNERS[[ia,ib]]
        varying = int(np.flatnonzero(a != b)[0])
        fixed = [j for j in range(3) if j != varying]
        j,k = fixed
        u = varying
        values[n] = .25*(1-x[u]**2)*(1+a[j]*x[j])*(1+a[k]*x[k])
        grad[n,u] = -.5*x[u]*(1+a[j]*x[j])*(1+a[k]*x[k])
        grad[n,j] = .25*a[j]*(1-x[u]**2)*(1+a[k]*x[k])
        grad[n,k] = .25*a[k]*(1-x[u]**2)*(1+a[j]*x[j])
    return values,grad


_N = np.array([shape20(p)[0] for p in _GAUSS])
_D = np.array([shape20(p)[1] for p in _GAUSS])


def element_forces(x: np.ndarray, u: np.ndarray, *, young: float = 210e9,
                   poisson: float = .3) -> tuple[np.ndarray, np.ndarray]:
    """Batched small-strain internal forces; x,u have (element,20,3)."""
    jac = np.einsum('eni,gnj->egij',x,_D)
    det = np.linalg.det(jac)
    if not np.isfinite(det).all() or np.min(det) <= 0:
        raise ValueError('nonpositive or nonfinite C3D20R Jacobian')
    grad = np.einsum('gnj,egji->egni',_D,np.linalg.inv(jac))
    du = np.einsum('eni,egnj->egij',u,grad)
    strain = .5*(du+np.swapaxes(du,-1,-2))
    mu = young/(2*(1+poisson))
    lame = young*poisson/((1+poisson)*(1-2*poisson))
    stress = 2*mu*strain+lame*np.trace(strain,axis1=-2,axis2=-1)[...,None,None]*np.eye(3)
    force = np.einsum('eg,egij,egnj->eni',det,stress,grad)
    return force,det


def affine_patch() -> dict:
    """Independent constant-stress cube face-force and zero-mode check."""
    corners = _CORNERS*.5
    edges = np.array([(corners[a]+corners[b])/2 for a,b in _EDGES])
    x = np.concatenate((corners,edges))[None]
    a = np.array(((.001,.002,-.003),(.004,-.002,.001),
                  (.002,.003,.0005)))
    u = x@a.T + np.array((.3,-.2,.1))
    force,_ = element_forces(x,u,young=1000,poisson=.25)
    strain = .5*(a+a.T)
    stress = 800*strain+400*np.trace(strain)*np.eye(3)
    # The sum of all face nodal forces on a Q20 cube gives σ n A.
    errors = []
    for axis in range(3):
        for sign in (-1,1):
            mask = np.isclose(x[0,:,axis],sign*.5)
            actual = force[0,mask].sum(axis=0)
            errors.append(float(np.linalg.norm(actual-sign*stress[:,axis])))
    rigid,_ = element_forces(x,np.broadcast_to(np.array((.3,-.2,.1)),x.shape),
                             young=1000,poisson=.25)
    error = max(errors)
    if error > 1e-10 or np.max(np.abs(rigid)) > 1e-10:
        raise AssertionError('C3D20R affine/rigid patch failed')
    return {'maximum_face_resultant_error_N':error,
            'maximum_rigid_force_N':float(np.max(np.abs(rigid))),
            'partition_error':float(max(abs(_N.sum(axis=1)-1))),
            'derivative_sum_error':float(max(abs(_D.sum(axis=1)).ravel()))}


def read_deck(path: Path) -> tuple[np.ndarray,dict[str,np.ndarray]]:
    coordinates = {}
    elements: dict[str,list[list[int]]] = {'Plate':[],'Stiffener':[]}
    section = None
    pending = None
    for line in path.open(errors='replace'):
        if line.startswith('*'):
            if pending is not None:
                raise ValueError('incomplete 20-node element')
            head = line.strip().upper()
            section = ('nodes' if head.startswith('*NODE,NSET=ALLNODES') else
                       'Plate' if head.startswith('*ELEMENT,TYPE=C3D20R,ELSET=PLATE') else
                       'Stiffener' if head.startswith('*ELEMENT,TYPE=C3D20R,ELSET=STIFFENER') else None)
            continue
        if section is None or not line.strip():
            continue
        parts = [v.strip() for v in line.split(',') if v.strip()]
        if section == 'nodes':
            coordinates[int(parts[0])] = [float(v) for v in parts[1:]]
        elif pending is None:
            pending = [int(v) for v in parts]
            if len(pending) != 16:
                raise ValueError('unexpected first C3D20R deck line')
        else:
            pending += [int(v) for v in parts]
            if len(pending) != 21:
                raise ValueError('unexpected second C3D20R deck line')
            elements[section].append(pending[1:])
            pending = None
    if set(coordinates) != set(range(1,len(coordinates)+1)):
        raise ValueError('noncontiguous deck node identities')
    return np.array([[0,0,0]]+[coordinates[i] for i in range(1,len(coordinates)+1)]), {
        key:np.asarray(value,dtype=np.int32) for key,value in elements.items()}


def wrench(force: np.ndarray, coordinates: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    f = force[nodes]
    return np.r_[f.sum(axis=0),np.cross(coordinates[nodes],f).sum(axis=0)]


def recover(folder: Path) -> dict:
    model = json.loads((folder/'model.json').read_text())
    if any((model['element_family'] != 'C3D20R',
            model['bond_policy'] != 'terminal',model['contact_policy'] != 'none',
            model['boundary_policy'] != 'left_root')):
        raise ValueError('only saved C1 terminal shared-bond no-contact model admitted')
    stems = list(folder.glob('*.inp'))
    if len(stems) != 1:
        raise ValueError('one saved deck required')
    inp=stems[0]
    frd=inp.with_suffix('.frd')
    dat=inp.with_suffix('.dat')
    x,elements = read_deck(inp)
    if len(x)-1 != model['node_count'] or any(len(elements[k])!=model[f'{k.lower() if k=="Plate" else "bar"}_elements'] for k in elements):
        raise ValueError('saved model/deck inventory mismatch')
    vectors = _read_frd_u(frd)
    if set(vectors) != set(range(1,len(x))):
        raise ValueError('incomplete saved nodal displacement field')
    u = np.array([[0,0,0]]+[vectors[i] for i in range(1,len(x))])
    load = np.zeros_like(x)
    for key,force in model['applied_nodal_forces_N'].items():
        load[int(key)] = force
    fint={k:np.zeros_like(x) for k in elements}
    determinant_min = float('inf')
    for domain,conn in elements.items():
        for start in range(0,len(conn),128):
            ids=conn[start:start+128]
            f,det = element_forces(x[ids],u[ids])
            determinant_min=min(determinant_min,float(det.min()))
            np.add.at(fint[domain],ids.ravel(),f.reshape(-1,3))
    support=np.asarray(model['boundary_node_ids'],dtype=np.int32)
    printed=parse_nodal_vectors(dat.read_text(errors='replace'),set(map(int,support)),
                                'forces','SUPPORTS')
    rf = np.zeros_like(x)
    for node,value in printed.items():
        rf[node]=value
    global_residual=fint['Plate']+fint['Stiffener']-load
    free=np.ones(len(x),bool)
    free[0]=False
    free[support]=False
    seam=np.asarray(model['shared_interface_node_ids'],dtype=np.int32)
    bar_action=fint['Stiffener'][seam]-load[seam]
    plate_action=fint['Plate'][seam]
    plate_nodes=np.asarray(model['plate_boundary_node_ids'],dtype=np.int32)
    bar_nodes=np.asarray(model['beam_root_node_ids'],dtype=np.int32)
    all_nodes=np.arange(1,len(x),dtype=np.int32)
    support_wrench=wrench(global_residual,x,support)
    rf_wrench=wrench(rf,x,support)
    ranked=np.flatnonzero(free)[np.argsort(np.linalg.norm(global_residual[free],axis=1))[-12:]][::-1]
    return {
        'scope':'saved C3D20R small-strain weak shared-node force diagnostic; rounded FRD makes local nodal forces uncertain; printed support RF gives the integrated bond wrench',
        'inputs':{p.name:_sha(p) for p in (inp,frd,dat,folder/'model.json')},
        'inventory':{'nodes':len(x)-1,'plate_elements':len(elements['Plate']),
                     'bar_elements':len(elements['Stiffener']),'shared_nodes':len(seam)},
        'patch':affine_patch(),
        'minimum_jacobian_m3':determinant_min,
        'global':{'free_rms_residual_N':float(np.sqrt(np.mean(global_residual[free]**2))),
                  'free_max_residual_N':float(np.max(np.abs(global_residual[free]))),
                  'support_rms_RF_error_N':float(np.sqrt(np.mean((global_residual[support]-rf[support])**2))),
                  'support_max_RF_error_N':float(np.max(np.abs(global_residual[support]-rf[support]))),
                  'support_wrench_N_Nm':support_wrench.tolist(),
                  'printed_support_wrench_N_Nm':rf_wrench.tolist(),
                  'total_applied_wrench_N_Nm':wrench(load,x,all_nodes).tolist()},
        'largest_free_residuals':[{'node':int(i),'coordinate_m':x[i].tolist(),
                                   'residual_N':global_residual[i].tolist(),
                                   'load_N':load[i].tolist(),
                                   'plate_force_N':fint['Plate'][i].tolist(),
                                   'bar_force_N':fint['Stiffener'][i].tolist()}
                                  for i in ranked],
        'bond':{'bar_on_plate_from_printed_support_N_Nm':(-wrench(rf,x,plate_nodes)).tolist(),
                'bar_on_plate_from_recovered_support_N_Nm':(-wrench(global_residual,x,plate_nodes)).tolist(),
                'bar_side_residual_wrench_N_Nm':wrench(fint['Stiffener']-load,x,seam).tolist(),
                'plate_side_internal_wrench_N_Nm':wrench(fint['Plate'],x,seam).tolist(),
                'seam_rms_mismatch_N':float(np.sqrt(np.mean((bar_action+plate_action)**2))),
                'seam_max_mismatch_N':float(np.max(np.abs(bar_action+plate_action))),
                'bar_side_residual_virtual_work_J':float(np.sum(bar_action*u[seam])),
                'plate_side_internal_virtual_work_J':float(np.sum(plate_action*u[seam]))},
        'support_parts':{'plate_recovered_N_Nm':wrench(global_residual,x,plate_nodes).tolist(),
                         'bar_recovered_N_Nm':wrench(global_residual,x,bar_nodes).tolist(),
                         'plate_printed_N_Nm':wrench(rf,x,plate_nodes).tolist(),
                         'bar_printed_N_Nm':wrench(rf,x,bar_nodes).tolist()}}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=recover(args.folder)
    payload=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == '__main__':
    main()
