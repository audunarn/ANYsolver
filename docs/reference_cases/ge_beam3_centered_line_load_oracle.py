"""Independent dead-line work reconstruction; no ANYsolver imports.

Reconstruct Q2 interpolation from supplied nodal floats with rational shape
functions. Integrate with the explicitly supplied registered Gauss order, then
differentiate f.(U c) analytically for spatial multiplicative cell rotations.
This verifies the discrete load, not continuum quadrature convergence.
"""

from dataclasses import dataclass
from fractions import Fraction as F
import math

import numpy as np


POLICY = 'SPATIAL_DEAD_FORCE_PER_REFERENCE_ARCLENGTH_V1'


def array(value, shape):
    made = np.array(value, dtype=float, copy=True)
    if made.shape != shape or not np.isfinite(made).all():
        raise ValueError('finite load-oracle data of exact shape required')
    return made


def readonly(value):
    made = np.array(value, copy=True); made.setflags(write=False)
    return made


@dataclass(frozen=True)
class LoadWork:
    work: float
    force: np.ndarray
    hessian: np.ndarray
    nodal_measures: np.ndarray
    cell_lift_integrals: np.ndarray
    policy: str = POLICY


def evaluate(nodes, total_translation, cell_rotations, force, *, order=8):
    nodes = array(nodes, (3,3)); displacement = array(total_translation, (3,3))
    cells = array(cell_rotations, (2,3,3)); force = array(force, (3,))
    if type(order) is not int or order not in (4,8,24):
        raise ValueError('registered load quadrature required')
    for cell in cells:
        if np.linalg.norm(cell.T@cell-np.eye(3)) > 1e-11 or abs(np.linalg.det(cell)-1.) > 1e-11:
            raise ValueError('proper physical cell rotation required')
    rational = [[F(float(v)) for v in row] for row in nodes]
    points, weights = np.polynomial.legendre.leggauss(order)
    nodal = np.zeros(3); lifts = np.zeros((2,3))
    for cell in (0,1):
        for point, weight in zip(points, weights):
            t = F(float((point+1)/2)); xi = F(cell-1)+t
            shapes = (xi*(xi-1)/2, 1-xi*xi, xi*(xi+1)/2)
            derivatives = (xi-F(1,2), -2*xi, xi+F(1,2))
            tangent = [float(sum((derivatives[i]*rational[i][k] for i in range(3)), F())) for k in range(3)]
            jacobian = math.sqrt(math.fsum(v*v for v in tangent))
            if not math.isfinite(jacobian) or jacobian <= 0:
                raise ValueError('positive regular reference measure required')
            measure = float(weight)*jacobian/2
            nodal[cell] += float(1-t)*measure; nodal[cell+1] += float(t)*measure
            for k in range(3):
                position = sum((shapes[i]*rational[i][k] for i in range(3)), F())
                chord = (1-t)*rational[cell][k]+t*rational[cell+1][k]
                lifts[cell,k] += float(position-chord)*measure
    gradient = np.zeros(36); hessian = np.zeros((36,36))
    terms = []
    for node in range(3):
        gradient[6*node:6*node+3] = nodal[node]*force
        terms.append(nodal[node]*float(force@displacement[node]))
    for cell in (0,1):
        d = cells[cell]@lifts[cell]; slot = slice(18+3*cell,21+3*cell)
        terms.append(float(force@((cells[cell]-np.eye(3))@lifts[cell])))
        gradient[slot] = np.cross(d,force)
        hessian[slot,slot] = (np.outer(force,d)+np.outer(d,force))/2-float(force@d)*np.eye(3)
    work = math.fsum(terms)
    if not math.isfinite(work) or not all(np.isfinite(v).all() for v in (gradient,hessian,nodal,lifts)):
        raise ValueError('nonfinite load-work reconstruction')
    return LoadWork(work, readonly(gradient), readonly(hessian), readonly(nodal), readonly(lifts))
