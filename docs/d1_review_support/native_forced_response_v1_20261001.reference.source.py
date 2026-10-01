"""Independent temporal/load reference; accepted spatial matrices are inputs.

No anysolver imports, production load/inertia evaluations or eigensolve. The
original centered Q2 curve and two P1 lifted cells are integrated explicitly.
All fifteen frozen physical modes, including six rigid modes, are retained.
"""
from dataclasses import dataclass
from fractions import Fraction
import numpy as np


def owned(value):
    array = np.asarray(value, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError('finite reference input required')
    return np.frombuffer(array.tobytes(), dtype=float).reshape(array.shape)


def line_stations(coordinates, order=4):
    x = np.asarray(coordinates)
    assert x.shape == (3, 3) and order == 4
    a, b = (x[2]-x[0])/2., x[0]-2*x[1]+x[2]
    points, weights = np.polynomial.legendre.leggauss(order)
    rows = []
    for cell in (0, 1):
        for point, weight in zip(points, weights):
            t = float((point+1.)/2.)
            xi = cell-1.+t
            rows.append(dict(cell=cell, left=cell, right=cell+1, t=t,
                measure=float(weight*np.linalg.norm(a+xi*b)/2.),
                lift0=owned(.5*t*(t-1.)*b)))
    return rows


def load_map(points, cells, rows, force, reference_points):
    """F_i=integral N_i f, F_cell=integral (Uc0)x f; algebraic rows zero."""
    load, tangent = np.zeros(42), np.zeros((42, 42))
    resultant, moment, potential = np.zeros(3), np.zeros(3), 0.
    for row in rows:
        cell, left, right, t, w = (row[k] for k in ('cell', 'left', 'right', 't', 'measure'))
        lift = cells[cell]@row['lift0']
        point = (1.-t)*points[left]+t*points[right]+lift
        displacement = ((1.-t)*(points[left]-reference_points[left])
                        +t*(points[right]-reference_points[right])+lift-row['lift0'])
        load[6*left:6*left+3] += w*(1.-t)*force
        load[6*right:6*right+3] += w*t*force
        first = 18+3*cell
        load[first:first+3] += w*np.cross(lift, force)
        tangent[first:first+3, first:first+3] += w*(np.outer(lift, force)-(lift@force)*np.eye(3))
        resultant += w*force
        moment += w*np.cross(point, force)
        potential += w*float(force@displacement)
    return dict(load42=load, tangent42=tangent, force=resultant, moment=moment, potential=potential)


def average_rotation(phi):
    a, b, c = phi
    skew = np.array(((0., -c, b), (c, 0., -a), (-b, a, 0.)))
    square = float(phi@phi)
    if square < 1e-4:
        first = .5-square/24.+square**2/720.-square**3/40320.
        second = 1./6.-square/120.+square**2/5040.-square**3/362880.
    else:
        angle = np.sqrt(square)
        first, second = (1.-np.cos(angle))/square, (angle-np.sin(angle))/(square*angle)
    return np.eye(3)+first*skew+second*(skew@skew)


def positions(mechanical):
    return np.array([[float(Fraction(float(h))+Fraction(float(l))) for h, l in zip(row, low)]
        for row, low in zip(mechanical.positions, mechanical.position_low)])


def position_delta(now, before):
    return np.array([[float(Fraction(float(h))+Fraction(float(l))-
                           Fraction(float(h0))-Fraction(float(l0)))
        for h, l, h0, l0 in zip(row, low, row0, low0)]
        for row, low, row0, low0 in zip(now.positions, now.position_low,
                                      before.positions, before.position_low)])


def path_accounting(before, candidate, rows, force, reference_points):
    after = candidate.endpoint.mechanical
    delta = position_delta(after, before)
    phi = candidate.unknown42[18:24].reshape(2, 3)
    average_cells = np.array([average_rotation(phi[c])@before.cell_rotations[0, c] for c in (0, 1)])
    average = load_map(positions(before)+.5*delta, average_cells, rows, force, reference_points)
    work = 0.
    for row in rows:
        c, left, right, t, w = (row[k] for k in ('cell', 'left', 'right', 't', 'measure'))
        displacement = ((1.-t)*delta[left]+t*delta[right]
            +(after.cell_rotations[0, c]-before.cell_rotations[0, c])@row['lift0'])
        work += w*float(force@displacement)
    return dict(exact_work=float(work), linear_impulse=candidate.dt*average['force'],
                angular_impulse=candidate.dt*average['moment'], phi=phi)


@dataclass(frozen=True)
class Descriptor:
    mass: np.ndarray
    stiffness: np.ndarray
    cholesky: np.ndarray
    modes: np.ndarray
    eigenvalues: np.ndarray
    omega: np.ndarray

    @classmethod
    def from_saved(cls, saved):
        m, k = owned(saved['M15']), owned(saved['Ke15'])
        assert m.shape == k.shape == (15, 15)
        l = np.linalg.cholesky(m)
        values = np.asarray(saved['eigenvalues'])
        assert values.shape == (15,)
        assert np.all(abs(values[:6]) <= saved['eigenvalue_resolution'])
        assert np.all(values[6:] > saved['eigenvalue_resolution'])
        q = np.linalg.solve(l.T, np.asarray(saved['transformed_eigenvectors']))
        assert np.linalg.norm(q.T@m@q-np.eye(15)) <= 1e-10
        assert np.linalg.norm(k@q-m@q@np.diag(values))/(np.linalg.norm(k)*np.linalg.norm(q)) <= 1e-10
        omega = np.r_[np.zeros(6), np.sqrt(values[6:])]
        return cls(m, k, owned(l), owned(q), owned(values), owned(omega))

    def mass_norm(self, vector):
        return float(np.linalg.norm(self.cholesky.T@vector))

    def positive_norm(self, vector):
        return float(np.linalg.norm(self.modes[:, 6:].T@self.mass@vector))

    def trajectory(self, force15, time, *, dt=None, index=None):
        f = self.modes.T@force15
        z, velocity = .5*f*time*time, f*time
        phase = self.omega[6:]*time if dt is None else index*2.*np.arctan(self.omega[6:]*dt/2.)
        z[6:] = f[6:]*2.*np.sin(phase/2.)**2/self.eigenvalues[6:]
        velocity[6:] = f[6:]*np.sin(phase)/self.omega[6:]
        return self.modes@z, self.modes@velocity

    def scales(self, force15, resultant, length, duration):
        q, v = self.trajectory(force15, duration)
        energy = float(.5*(q@self.stiffness@q+v@self.mass@v))
        value = dict(configuration=self.mass_norm(q), velocity=self.mass_norm(v),
            elastic_configuration=self.positive_norm(q), elastic_velocity=self.positive_norm(v),
            energy=energy, force=float(np.linalg.norm(resultant)),
            moment=length*float(np.linalg.norm(resultant)),
            momentum=duration*float(np.linalg.norm(resultant)),
            angular_momentum=length*duration*float(np.linalg.norm(resultant)))
        assert all(np.isfinite(x) and x > 0. for x in value.values())
        return value


def compare(coarse, fine, floor, ratio):
    if coarse <= floor:
        return dict(coarse=coarse, fine=fine, passes=fine <= floor,
                    disposition='resolution limited' if fine <= floor else 'unresolved NONPASS', ratio=None)
    return dict(coarse=coarse, fine=fine, passes=fine <= ratio*coarse,
                disposition='resolved comparison', ratio=fine/coarse)
