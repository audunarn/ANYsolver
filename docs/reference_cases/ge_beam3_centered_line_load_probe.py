"""Research-only load-parameter Schur derivative on the frozen centered core.

No native load API, state commit, public selector or qualification is added.
Local histories remain fixed origins through every evaluation. With L=V-p W,
stationarity gives z_p=H_zz^-1 W_z, g_p=-W_q+H_qz z_p and
Pi_pp=-W_z.z_p. The signed saddle block is solved, never regularized.
"""

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_centered_mixed import CenteredStationaryBeam
from anysolver._ge_beam3_p5.mixed import LocalForceAccuracy
from anysolver._ge_beam3_p5.arrays import _array, _readonly
from anysolver._ge_beam3_p5.arrays import _frames
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum, validate_pair
from anysolver._ge_beam3_p5.compensated import sum_jets
from anysolver._ge_beam3_mixed_ad import Jet2, so3_exp, matmul, constant_matrix


POLICY = 'SPATIAL_DEAD_FORCE_PER_REFERENCE_ARCLENGTH_V1'


@dataclass(frozen=True)
class AugmentedWork:
    work: float
    force: np.ndarray
    hessian: np.ndarray


def load_work(reference, positions, position_low, cells, force, *, order=8):
    """Load-only analytic AD: never subtract two material potentials.

    Use the frozen centered reference evaluator and its load expression,
    independently of the rational-Q2/closed-form derivative oracle.
    """
    x = _array(positions,(3,3),'positions'); low = _array(position_low,(3,3),'position low')
    cells = _frames(cells,2,'cell rotations'); force = _array(force,(3,),'line force')
    if type(order) is not int or order not in (4,8,24): raise ValueError('registered load quadrature required')
    for a,b in zip(x.flat,low.flat): validate_pair(float(a),float(b))
    delta = [Jet2.variable(0.,i,36) for i in range(36)]
    points, weights = np.polynomial.legendre.leggauss(order); terms = []
    for cell in (0,1):
        made_u = matmul(so3_exp(delta[18+3*cell:21+3*cell]),constant_matrix(cells[cell],36))
        for point,weight in zip(points,weights):
            t = float((point+1)/2); xi = cell-1+t
            offset = reference.half_cell_lift(cell,t); measure = weight*reference.jacobian(xi)/2
            for i in range(3):
                position_terms = [(made_u[i][k]-(1 if i == k else 0))*offset[k] for k in range(3)]
                for node,shape in ((cell,1-t),(cell+1,t)):
                    high,tail = split_sum((float(x[node,i]),float(low[node,i]),-float(reference.coordinates[node,i])))
                    position_terms.extend((Jet2.constant(shape*high,36),Jet2.constant(shape*tail,36),shape*delta[6*node+i]))
                terms.append(measure*force[i]*sum_jets(position_terms))
    made = sum_jets(terms)
    if not np.isfinite(made.value) or not np.isfinite(made.gradient).all() or not np.isfinite(made.hessian).all():
        raise ValueError('nonfinite load-only variations')
    return AugmentedWork(float(made.value),_readonly(made.gradient),_readonly(made.hessian))


@dataclass(frozen=True)
class CondensedLoadParameter:
    response: object
    unit_work: float
    augmented_unit_force: np.ndarray
    augmented_unit_work_hessian: np.ndarray
    internal_parameter_derivative: np.ndarray
    residual_parameter_derivative: np.ndarray
    potential_parameter_derivative: float
    potential_parameter_second_derivative: float
    branch: tuple
    policy: str = POLICY


def evaluate(reference, section, positions, position_low, vertex_frames, force,
             parameter, *, order=8, origins=None):
    if type(parameter) is not float or not np.isfinite(parameter):
        raise ValueError('finite explicit load parameter required')
    force = _array(force, (3,), 'unit reference-arclength force')
    def model(value):
        return CenteredStationaryBeam(reference, section, position_low=position_low,
            line_force=value*force, order=order, origins=origins)
    made = model(parameter)
    response = made.solve(positions, vertex_frames, force_accuracy=LocalForceAccuracy(
        1e-12, float(made.reference.regularity.characteristic_length)))
    arguments = (positions, vertex_frames, response.local_rotations, response.moments)
    full = made.evaluate(*arguments)
    unit = load_work(made.reference,positions,position_low,response.local_rotations,force,order=order)
    work, w, w2 = unit.work, unit.force, unit.hessian
    h = full.hessian
    dz = np.linalg.solve(h[18:,18:], w[18:])
    dg = -w[:18]+h[:18,18:]@dz
    pp = -float(w[18:]@dz)
    if not np.isfinite([work,pp]).all() or not all(np.isfinite(v).all() for v in (w,w2,dz,dg)):
        raise ValueError('nonfinite condensed load derivative')
    branch = tuple(station.response.plastic_active for station in response.stations)
    return CondensedLoadParameter(response, float(work), _readonly(w), _readonly(w2),
        _readonly(dz), _readonly(dg), -float(work), pp, branch)
