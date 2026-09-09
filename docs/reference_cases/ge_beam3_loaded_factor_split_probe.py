"""Same-author elastic-material/geometric split of the accepted P5 Hessian.

Research only: caller supplies an already validated native material state.
Not an independent mechanics oracle, eigensolver or public state interface.
Never obtain geometric stiffness by subtracting two large dense tangents.
"""

import numpy as np

from anysolver._ge_beam3_mixed_ad import Jet2, constant_matrix, matmul, matvec, transpose, so3_exp, so3_log
from anysolver._ge_beam3_p5.compensated import compensated_strain
from anysolver._ge_beam3_centered_mixed import CenteredStationaryBeam
from anysolver._ge_beam3_p5.algebra import HALVES


def split_accepted_elastic_operator(element, inner):
    core = element.core; reference = core.reference; response = inner['response']
    mixed = CenteredStationaryBeam(reference, core.section, position_low=inner['committed_position_low'],
        order=core.order, origins=inner['origins'], line_force=inner['load_parameter']*core.line_force)
    variables = [Jet2.variable(0., i, 24) for i in range(24)]
    vertices = inner['committed_nodal_rotation_matrices']@reference.nodal_triads
    made_q = [matmul(so3_exp(variables[6*n+3:6*n+6]), constant_matrix(vertices[n], 24)) for n in range(3)]
    rows = []; coupling = np.zeros((12, 24)); compliance = np.zeros((12, 12)); geometric = np.zeros((24, 24))
    for cell, (left, right) in enumerate(HALVES):
        made_u = matmul(so3_exp(variables[18+3*cell:21+3*cell]), constant_matrix(response.local_rotations[cell], 24))
        z = compensated_strain(made_u, reference.coordinates, inner['committed_positions'],
            inner['committed_position_low'], variables, left, right)
        for endpoint, node, sign in ((0, left, -1), (1, right, 1)):
            frame = matmul(made_u, constant_matrix(reference.nodal_triads[node], 24))
            ell = so3_log(matmul(transpose(frame), made_q[node]))
            for i, value in enumerate(ell):
                coupling[6*cell+3*endpoint+i] += sign*value.gradient
                geometric += sign*response.moments[cell, endpoint, i]*value.hessian
        for index, t, xi, measure, v, offset, _ in mixed._stations[cell]:
            gamma = matvec(constant_matrix(v, 24), z)
            moment = (1-t)*response.moments[cell, 0]+t*response.moments[cell, 1]
            density = core.section.mixed_response([x.value for x in gamma], moment, mixed.origins[cell*core.order+index])
            if density.section.plastic_active:
                raise ValueError('elastic accepted-increment split only')
            jacobian = np.array([x.gradient for x in gamma])
            interpolation = np.zeros((3, 12))
            interpolation[:, 6*cell:6*cell+3] = (1-t)*np.eye(3)
            interpolation[:, 6*cell+3:6*cell+6] = t*np.eye(3)
            h = density.hessian
            rows.append(np.sqrt(measure)*np.linalg.cholesky(h[:3, :3]).T@jacobian)
            compliance -= measure*interpolation.T@h[3:, 3:]@interpolation
            coupling += measure*interpolation.T@h[3:, :3]@jacobian
            for i, value in enumerate(gamma):
                geometric += measure*density.gradient[i]*value.hessian
            # Linear nodal displacement work has zero Hessian. The lifted
            # spatial-dead load contributes only through the cell rotation.
            for i in range(3):
                for k in range(3):
                    geometric -= measure*mixed.line_force[i]*offset[k]*made_u[i][k].hessian
    rows.append(np.linalg.solve(np.linalg.cholesky(compliance), coupling))
    factor = np.vstack(rows)
    if not np.isfinite(factor).all() or not np.isfinite(geometric).all():
        raise ValueError('nonfinite loaded split')
    return factor, geometric
