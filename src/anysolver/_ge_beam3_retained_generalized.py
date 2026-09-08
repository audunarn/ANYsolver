"""Private finite-rotation retained generalized ellipsoid beam potential.

Kinematic map ported unchanged from the frozen retained physical-fibre operator.
Pi(q,p;origin)=p.k(q)-Psi*(p;origin). The geometry is the preserved centered
two-cell kinematic map; material comes from the coupled generalized ellipsoid cell.
No history commit, hidden static condensation or public routing occurs here.
"""
from dataclasses import dataclass
from math import fsum
import numpy as np

from ._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
from ._ge_beam3_generalized_cell import GeneralizedCellConjugate, GeneralizedCellHistory
from ._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from ._ge_beam3_mixed_ad import Jet2, constant_matrix, matmul, transpose, so3_exp, so3_log
from ._ge_beam3_p5.compensated import compensated_strain
from ._ge_beam3_p5.compensated_coordinates import validate_pair
from ._ge_beam3_p5.algebra import HALVES
from ._ge_beam3_p5.arrays import _array, _frames
from ._native_reference_modal import _owned
from ._ge_beam3_p5_seeded.core import canonical, sha


POLICY = 'CANDIDATE_GE_BEAM3_RETAINED_GENERALIZED_ELLIPSOID_V1'


@dataclass(frozen=True)
class Evaluation:
    potential: float
    residual: np.ndarray
    hessian: np.ndarray
    hessian_low: np.ndarray
    kinematics: np.ndarray
    history: GeneralizedCellHistory
    material: bytes
    production_qualified: bool = False


class RetainedGeneralizedOperator:
    __slots__ = ('reference', 'section', 'order', 'cell', 'stations', 'identity', '_reference_identity', '_sealed')

    def __setattr__(self, name, value):
        if getattr(self, '_sealed', False): raise AttributeError('retained generalized operator is immutable')
        object.__setattr__(self, name, value)

    def __init__(self, reference, section, *, order):
        if type(reference) is not Reference or type(section) is not EllipsoidalGeneralizedSection:
            raise ValueError('explicit centered reference and native generalized ellipsoid section required')
        if type(order) is not int or order not in (4, 8):
            raise ValueError('private retained generalized entry supports explicit quadrature order 4 or 8')
        self.reference = Reference(reference.coordinates, reference.nodal_triads,
            regularity_relative_tolerance=reference._regularity_relative_tolerance,
            rotation_tolerance=reference._rotation_tolerance, frame_tolerance=reference._frame_tolerance)
        self.section = section; self.order = order
        points, weights = np.polynomial.legendre.leggauss(order)
        data = []; stations = []
        for cell in (0, 1):
            for index, (point, weight) in enumerate(zip(points, weights)):
                t = float((point+1)/2); xi = cell-1+t; jacobian = self.reference.jacobian(xi)
                measure = float(weight*jacobian/2); frame = _owned(self.reference.frame(xi))
                data.append(dict(cell=cell, t=t, weight=measure, v=(frame.T/jacobian).tolist()))
                stations.append((cell, index, xi, measure, frame))
        self.cell = GeneralizedCellConjugate(section, data); self.stations = tuple(stations)
        self._reference_identity = self.reference.fingerprint()
        self.identity = sha(dict(formulation_id=POLICY, section=section.identity,
            reference=self._reference_identity, quadrature=order, cell=self.cell.identity))
        self._sealed = True

    def guard(self):
        self.cell.guard()
        if self.reference.fingerprint() != self._reference_identity:
            raise ValueError('captured retained generalized reference changed')

    def evaluate(self, positions, position_low, vertices, rotations, resultants, *, origin=None, increment=None, check=None):
        self.guard()
        if check is not None: check()
        x = _array(positions, (3, 3), 'generalized positions'); low = _array(position_low, (3, 3), 'generalized low positions')
        for h, l in zip(x.flat, low.flat): validate_pair(float(h), float(l))
        q = _frames(vertices, 3, 'generalized nodal frames'); u = _frames(rotations, 2, 'generalized cell rotations')
        p = _array(resultants, (18,), 'generalized retained resultants')
        delta = np.zeros(42) if increment is None else _array(increment, (42,), 'generalized chart increment')
        angular = [delta[6*n+3:6*n+6] for n in range(3)]+[delta[18+3*c:21+3*c] for c in (0, 1)]
        if max(np.linalg.norm(v) for v in angular) >= .9*np.pi:
            raise ValueError('retained generalized rotation chart requires cutback')
        variables = [Jet2.variable(value, i, 24) for i, value in enumerate(delta[:24])]
        made_q = [matmul(so3_exp(variables[6*n+3:6*n+6]), constant_matrix(q[n], 24)) for n in range(3)]
        z = []; ell = []
        for cell, (left, right) in enumerate(HALVES):
            made_u = matmul(so3_exp(variables[18+3*cell:21+3*cell]), constant_matrix(u[cell], 24))
            z.extend(compensated_strain(made_u, self.reference.coordinates, x, low, variables, left, right))
            for node, sign in ((left, -1), (right, 1)):
                frame = matmul(made_u, constant_matrix(self.reference.nodal_triads[node], 24))
                ell.extend(sign*v for v in so3_log(matmul(transpose(frame), made_q[node])))
        values = z+ell; k = np.array([v.value for v in values]); j = np.array([v.gradient for v in values])
        p = p+delta[24:]
        response = self.cell.response(p.tolist(), origin, check=check)
        gh, gl = response['gradient']
        compatibility = [fsum((float(v), -h, -l)) for v, h, l in zip(k, gh, gl)]
        residual = np.r_[j.T@p, compatibility]
        geometric = sum((v.hessian*force for v, force in zip(values, p)), np.zeros((24, 24)))
        ch = np.array([row[0] for row in response['hessian']]); cl = np.array([row[1] for row in response['hessian']])
        hessian = np.block([[geometric, j.T], [j, -ch]])
        hessian_low = np.zeros((42, 42)); hessian_low[24:, 24:] = -cl
        potential = fsum([*(float(a)*float(b) for a, b in zip(p, k)),
                         -response['potential'][0][0], -response['potential'][1][0]])
        if not np.isfinite(potential): raise ValueError('finite retained generalized potential required')
        self.guard()
        if check is not None: check()
        return Evaluation(potential, _owned(residual), _owned(hessian), _owned(hessian_low), _owned(k),
                          response['history'], canonical(response))

    def recover(self, rotations, resultants, *, origin=None, check=None):
        self.guard(); u = _frames(rotations, 2, 'retained generalized recovery rotations')
        p = _array(resultants, (18,), 'retained generalized recovery resultants')
        response = self.cell.response(p.tolist(), origin, check=check)
        rows = []
        for (cell, index, xi, weight, ref), fields, history in zip(self.stations, response['stations'], response['history'].stations):
            rows.append(dict(cell=cell, station=index, xi=xi, measure=weight,
                strain=_owned(fields['strain'][0]), strain_low=_owned(fields['strain'][1]),
                resultants=_owned(fields['resultants'][0]), resultants_low=_owned(fields['resultants'][1]),
                history=history, reference_frame=ref,
                current_frame=_owned(u[cell]@ref), formulation_id=POLICY,
                recovery_policy='PAIRED_GENERALIZED_RESULTANT_RETAINED_FIELDS_V1'))
        self.guard()
        if check is not None: check()
        return tuple(rows)
