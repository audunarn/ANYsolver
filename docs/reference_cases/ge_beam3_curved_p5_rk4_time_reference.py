"""Separate bounded time reference; SHARED elastic and inertia mechanics.

RK4 and algebraic trace Newton are separately implemented here. This is not
an independent mechanics oracle, production integrator or qualification.
"""

from dataclasses import dataclass
import time

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, skew
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import CurvedFiniteProbe, _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_finite_inertia_probe import FiniteInertiaProbe


SCHEMA = 'GE_BEAM3_P5_SEPARATE_RK4_TIME_REFERENCE_V1'
PHYSICAL = np.array([0,1,2,6,7,8,12,13,14,18,19,20,21,22,23])
TRACES = np.array([3,4,5,9,10,11,15,16,17])


class TimeReferenceError(RuntimeError):
    """Bounded reference calculation failed; no canonical result exists."""


def inverse_left_jacobian(beta):
    beta = _array(beta,(3,),'temporary rotation coordinate')
    theta = float(np.linalg.norm(beta))
    if theta >= .9*np.pi: raise ValueError('temporary reference chart exhausted')
    k = skew(beta)
    if theta < 1e-3:
        coefficient = 1/12+theta**2/720+theta**4/30240
    else:
        coefficient = (1-.5*theta/np.tan(.5*theta))/theta**2
    return np.eye(3)-.5*k+coefficient*(k@k)


@dataclass(frozen=True)
class TimePoint:
    positions: np.ndarray
    vertex_frames: np.ndarray
    cell_rotations: np.ndarray
    nodal_velocity: np.ndarray
    cell_angular_velocity: np.ndarray


@dataclass(frozen=True)
class TimeObservation:
    point: TimePoint
    acceleration: np.ndarray
    energy: float
    linear_momentum: np.ndarray
    angular_momentum: np.ndarray
    trace_residual_norm: float
    physical_residual_norm: float


class SeparateTimeReference:
    """Free elastic macrocell only; no loads, clamps, history or restart."""

    def __init__(self, reference, section, section_mass, *, order=8):
        self.elastic = CurvedFiniteProbe(reference,section,order=order)
        self.kinetic = FiniteInertiaProbe(reference,section_mass,order=order)
        self.length = max(np.linalg.norm(a-b) for a in reference.coordinates for b in reference.coordinates)

    def _traces(self, x, cells, guard):
        # Start afresh from frozen reference traces; no integration-history cache.
        q = self.elastic.frames.copy(); count = 0

        def value(frames):
            nonlocal count
            guard()
            if count >= 64: raise TimeReferenceError('reference trace evaluation bound')
            count += 1
            jet = self.elastic._jet(x,frames,cells,external=True)
            norm = float(np.linalg.norm(jet.gradient[TRACES])/self.length)
            if not np.isfinite(norm): raise TimeReferenceError('nonfinite reference trace residual')
            return jet,norm

        jet,norm = value(q)
        for iteration in range(11):
            if norm <= 1e-11: return q,jet,norm
            if iteration == 10: raise TimeReferenceError('reference trace update bound')
            # Energy-Newton Hessian in a freshly based spatial chart. This
            # differs from the midpoint endpoint force-Jacobian iteration.
            hessian = jet.hessian[np.ix_(TRACES,TRACES)]
            np.linalg.cholesky(hessian)
            update = np.linalg.solve(hessian,-jet.gradient[TRACES]).reshape(3,3)
            for backtrack in range(10):
                spin = update*(.5**backtrack)
                if max(np.linalg.norm(v) for v in spin) >= .9*np.pi: continue
                candidate = np.array([rotation(v)@base for v,base in zip(spin,q)])
                new,new_norm = value(candidate)
                if new_norm < norm:
                    q,jet,norm = candidate,new,new_norm
                    break
            else: raise TimeReferenceError('reference trace line search failed')
        raise AssertionError('unreachable')

    def observe(self, positions, cells, nodal_velocity, cell_velocity, *, guard=lambda: None):
        guard()
        x = _array(positions,(3,3),'reference positions');u = _frames(cells,2,'reference cell rotations')
        v = _array(nodal_velocity,(3,3),'reference nodal velocities')
        w = _array(cell_velocity,(2,3),'reference angular velocities')
        q,elastic,trace_norm = self._traces(x,u,guard)
        velocity = np.zeros(24)
        for node in range(3): velocity[6*node:6*node+3] = v[node]
        velocity[18:] = w.ravel()
        kinetic = self.kinetic.evaluate(x,u,velocity,np.zeros(24))
        mass = kinetic.mass[np.ix_(PHYSICAL,PHYSICAL)]
        np.linalg.cholesky(mass)
        acceleration = np.zeros(24)
        acceleration[PHYSICAL] = np.linalg.solve(mass,-(elastic.gradient+kinetic.inertia)[PHYSICAL])
        balance = kinetic.mass@acceleration+kinetic.inertia+elastic.gradient
        norm = float(np.linalg.norm(balance[PHYSICAL]))
        if not np.isfinite(norm) or norm > 1e-11*max(1.,np.linalg.norm(elastic.gradient)):
            raise TimeReferenceError('reference physical acceleration residual')
        point = TimePoint(*(_readonly(a) for a in (x,q,u,v,w)))
        return TimeObservation(point,_readonly(acceleration),float(elastic.value+kinetic.kinetic_energy),
            kinetic.linear_momentum,kinetic.angular_momentum,trace_norm,norm)

    def integrate(self, initial, duration, steps):
        if type(initial) is not TimePoint: raise ValueError('reference TimePoint required')
        if type(duration) is not float or not np.isfinite(duration) or not 0 < duration <= .1:
            raise ValueError('short positive reference duration required')
        if type(steps) is not int or steps not in (4,8,16,32): raise ValueError('bounded RK4 partition required')
        _frames(initial.vertex_frames,3,'initial traces')
        start = time.monotonic(); count = 0

        def guard():
            if time.monotonic()-start > 600: raise TimeReferenceError('reference wall limit')

        origin = self.observe(initial.positions,initial.cell_rotations,initial.nodal_velocity,
                              initial.cell_angular_velocity,guard=guard)
        if np.linalg.norm(origin.point.vertex_frames-initial.vertex_frames)>1e-11:
            raise ValueError('initial algebraic trace state is inconsistent')
        base_cells = initial.cell_rotations.copy()
        y = np.r_[initial.positions.ravel(),np.zeros(6),initial.nodal_velocity.ravel(),initial.cell_angular_velocity.ravel()]

        def fields(value):
            value = _array(value,(30,),'reference ODE coordinates')
            beta = value[9:15].reshape(2,3)
            for b in beta: inverse_left_jacobian(b)
            cells = np.array([rotation(b)@base for b,base in zip(beta,base_cells)])
            return value[:9].reshape(3,3),cells,value[15:24].reshape(3,3),value[24:].reshape(2,3),beta

        def rhs(value):
            nonlocal count
            guard()
            if count >= 128: raise TimeReferenceError('reference RHS bound')
            count += 1
            x,cells,v,w,beta = fields(value)
            made = self.observe(x,cells,v,w,guard=guard)
            a = made.acceleration
            beta_dot = np.array([inverse_left_jacobian(b)@omega for b,omega in zip(beta,w)])
            return np.r_[v.ravel(),beta_dot.ravel(),a[:18].reshape(3,6)[:,:3].ravel(),a[18:]]

        h = duration/steps
        for _ in range(steps):
            k1 = rhs(y); k2 = rhs(y+h*k1/2); k3 = rhs(y+h*k2/2); k4 = rhs(y+h*k3)
            y = y+h*(k1+2*k2+2*k3+k4)/6
        x,cells,v,w,_ = fields(y)
        final = self.observe(x,cells,v,w,guard=guard);guard()
        return final,count


def state_distance(a,b,length,duration):
    """Scaled physical-state distance; excludes algebraic trace coordinates."""
    if (type(length) not in (int,float,np.float64) or type(duration) not in (int,float,np.float64)
            or not np.isfinite([length,duration]).all() or length<=0 or duration<=0):
        raise ValueError('positive finite comparison scales required')
    for point in (a,b):
        _array(point.positions,(3,3),'comparison positions')
        _frames(point.cell_rotations,2,'comparison cells')
        _array(point.nodal_velocity,(3,3),'comparison velocity')
        _array(point.cell_angular_velocity,(2,3),'comparison angular velocity')
    parts = ((a.positions-b.positions)/length,
             (a.cell_rotations-b.cell_rotations)/np.sqrt(2),
             (a.nodal_velocity-b.nodal_velocity)*duration/length,
             (a.cell_angular_velocity-b.cell_angular_velocity)*duration)
    return float(np.sqrt(sum(np.sum(part**2) for part in parts)))
