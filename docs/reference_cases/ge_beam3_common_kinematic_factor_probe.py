"""Research-only common-kinematic factor chain of the preserved V5 equations.

Virigin reference states only in this diagnosis. Never silently use this
reference tangent for a loaded/plastic state. No production registration.
"""
import numpy as np
from anysolver._ge_beam3_mixed_ad import Jet2, constant_matrix, matmul, matvec, transpose, so3_exp, so3_log
from anysolver._ge_beam3_p5.compensated import compensated_strain
from anysolver._ge_beam3_centered_mixed import CenteredStationaryBeam
from anysolver._ge_beam3_p5.algebra import HALVES


def reference_chain(element,inner,checkpoint=lambda stage:None):
    core=element.core; reference=core.reference; response=inner['response']
    if (inner['load_parameter']!=0. or np.any(response.moments)
            or not np.array_equal(response.local_rotations,np.tile(np.eye(3),(2,1,1)))
            or not np.array_equal(inner['committed_nodal_rotation_matrices'],np.tile(np.eye(3),(3,1,1)))
            or not np.array_equal(inner['committed_positions'],reference.coordinates)
            or np.any(inner['committed_position_low'])
            or any(h.accumulated!=0. or h.plastic_coordinate!=0. for h in inner['origins'])):
        raise ValueError('virgin reference factor-chain diagnostic only')
    mixed=CenteredStationaryBeam(reference,core.section,position_low=inner['committed_position_low'],
        order=core.order,origins=inner['origins'],line_force=np.zeros(3))
    variables=[Jet2.variable(0.,i,24) for i in range(24)]
    vertices=inner['committed_nodal_rotation_matrices']@reference.nodal_triads
    made_q=[matmul(so3_exp(variables[6*n+3:6*n+6]),constant_matrix(vertices[n],24)) for n in range(3)]
    kinematic=np.zeros((18,24)); rows=[]; coupling=np.zeros((12,6)); compliance=np.zeros((12,12))
    for cell,(left,right) in enumerate(HALVES):
        checkpoint('chain.cell')
        made_u=matmul(so3_exp(variables[18+3*cell:21+3*cell]),constant_matrix(response.local_rotations[cell],24))
        z=compensated_strain(made_u,reference.coordinates,inner['committed_positions'],
            inner['committed_position_low'],variables,left,right)
        kinematic[3*cell:3*cell+3]=np.array([x.gradient for x in z])
        for endpoint,node,sign in ((0,left,-1),(1,right,1)):
            frame=matmul(made_u,constant_matrix(reference.nodal_triads[node],24))
            ell=so3_log(matmul(transpose(frame),made_q[node]))
            kinematic[6+6*cell+3*endpoint:9+6*cell+3*endpoint]=sign*np.array([x.gradient for x in ell])
        for index,t,xi,measure,v,offset,_ in mixed._stations[cell]:
            checkpoint('chain.station')
            gamma=matvec(constant_matrix(v,24),z)
            density=core.section.mixed_response([x.value for x in gamma],np.zeros(3),mixed.origins[cell*core.order+index])
            if density.section.plastic_active: raise ValueError('virgin elastic branch required')
            interpolation=np.zeros((3,12)); interpolation[:,6*cell:6*cell+3]=(1-t)*np.eye(3)
            interpolation[:,6*cell+3:6*cell+6]=t*np.eye(3)
            h=density.hessian
            row=np.zeros((3,18)); row[:,3*cell:3*cell+3]=np.sqrt(measure)*np.linalg.cholesky(h[:3,:3]).T@v
            rows.append(row)
            compliance-=measure*interpolation.T@h[3:,3:]@interpolation
            coupling[:,3*cell:3*cell+3]+=measure*interpolation.T@h[3:,:3]@v
    rows.append(np.linalg.solve(np.linalg.cholesky(compliance),np.column_stack((coupling,np.eye(12)))))
    return np.vstack(rows),kinematic
