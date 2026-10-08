"""Independent constrained temporal reference; full spatial K/M are inputs.

No anysolver owner calls. Reuses the reviewed centered-Q2/lifted-line
load/path arithmetic; only algebraic coordinates are Schur eliminated.
"""
from dataclasses import dataclass
import numpy as np
from native_forced_response_reference import (
    owned, line_stations, load_map, path_accounting, positions, position_delta, compare)

FIXED = tuple(range(6))
PHYSICAL = (6, 7, 8, 12, 13, 14, 18, 19, 20, 21, 22, 23)
ALGEBRAIC = (9, 10, 11, 15, 16, 17, *range(24, 42))
ALL_ALGEBRAIC = (3, 4, 5, *ALGEBRAIC)


def reaction_wrench(reaction6, fixed_position, origin):
    """Beam-side support force and moment, with the algebraic-frame couple."""
    r = np.asarray(reaction6)
    assert r.shape == (6,)
    return r[:3], np.cross(np.asarray(fixed_position)-origin, r[:3])+r[3:]


def sine_deficit(x):
    """1-sin(x)/x without subtracting nearly equal values."""
    x = np.asarray(x)
    square = x*x
    series = square*(1./6.-square/120.+square**2/5040.-square**3/362880.)
    direct = 1.-np.sinc(x/np.pi)
    return np.where(abs(x) < .01, series, direct)


@dataclass(frozen=True)
class ConstrainedDescriptor:
    mass: np.ndarray
    stiffness: np.ndarray
    full_stiffness: np.ndarray
    full_mass: np.ndarray
    embedding: np.ndarray
    algebraic_map: np.ndarray
    cholesky: np.ndarray
    modes: np.ndarray
    eigenvalues: np.ndarray
    omega: np.ndarray
    checks: dict

    @classmethod
    def from_full(cls, full_stiffness, full_mass):
        k, m = owned(full_stiffness), owned(full_mass)
        assert k.shape == m.shape == (42, 42)
        assert np.linalg.norm(k-k.T)/np.linalg.norm(k) <= 1e-12
        assert np.linalg.norm(m-m.T)/np.linalg.norm(m) <= 1e-12
        assert np.count_nonzero(m[list(ALL_ALGEBRAIC)]) == 0
        assert np.count_nonzero(m[:, list(ALL_ALGEBRAIC)]) == 0
        p, z = list(PHYSICAL), list(ALGEBRAIC)
        c = k[np.ix_(z, z)]
        singular = np.linalg.svd(c, compute_uv=False)
        threshold = 64.*np.finfo(float).eps*len(z)*singular[0]
        assert singular[-1] > threshold, 'singular constrained algebraic block'
        zz = -np.linalg.solve(c, k[np.ix_(z, p)])
        embedding = np.zeros((42, len(p)))
        embedding[p] = np.eye(len(p)); embedding[z] = zz
        ke = k[np.ix_(p, p)]+k[np.ix_(p, z)]@zz
        symmetry = np.linalg.norm(ke-ke.T)/np.linalg.norm(ke)
        assert symmetry <= 1e-11
        mp = m[np.ix_(p, p)]
        l = np.linalg.cholesky(mp)
        transformed = np.linalg.solve(l, ke)
        transformed = np.linalg.solve(l, transformed.T).T
        transformed_symmetry = np.linalg.norm(transformed-transformed.T)/np.linalg.norm(transformed)
        assert transformed_symmetry <= 1e-11
        # Only a recorded roundoff-sized skew part is removed for symmetric eigh.
        values, u = np.linalg.eigh(.5*(transformed+transformed.T))
        resolution = 64.*np.finfo(float).eps*len(p)*max(1., np.linalg.norm(transformed, 2))
        assert values[0] > resolution, 'unexpected unresolved constrained physical mode'
        modes = np.linalg.solve(l.T, u)
        orthogonality = np.linalg.norm(modes.T@mp@modes-np.eye(len(p)))
        residual = np.linalg.norm(ke@modes-mp@modes@np.diag(values))/(np.linalg.norm(ke)*np.linalg.norm(modes))
        assert orthogonality <= 1e-10 and residual <= 1e-10
        checks = dict(algebraic_rank=len(z), algebraic_singular_values=singular.tolist(),
            algebraic_condition=float(singular[0]/singular[-1]), algebraic_resolution=float(threshold),
            mass_condition=float(np.linalg.cond(mp)), stiffness_symmetry=float(symmetry),
            transformed_symmetry=float(transformed_symmetry), eigenvalue_resolution=float(resolution),
            eigen_residual=float(residual), mode_mass_orthogonality=float(orthogonality))
        return cls(owned(mp), owned(ke), k, m, owned(embedding), owned(zz), owned(l),
                   owned(modes), owned(values), owned(np.sqrt(values)), checks)

    def mass_norm(self, value):
        return float(np.linalg.norm(self.cholesky.T@value))

    def positive_norm(self, value):
        return float(np.linalg.norm(self.modes.T@self.mass@value))

    def trajectory(self, force12, time, *, dt=None, index=None):
        f = self.modes.T@force12
        phase = self.omega*time if dt is None else index*2.*np.arctan(self.omega*dt/2.)
        q = f*2.*np.sin(phase/2.)**2/self.eigenvalues
        v = f*np.sin(phase)/self.omega
        return self.modes@q, self.modes@v

    def reaction(self, force42, q12, a12):
        return (self.full_stiffness@self.embedding@q12
                +self.full_mass[:, list(PHYSICAL)]@a12-np.asarray(force42))[list(FIXED)]

    def continuous_reaction(self, force42, time):
        f = self.modes.T@np.asarray(force42)[list(PHYSICAL)]
        q, _ = self.trajectory(np.asarray(force42)[list(PHYSICAL)], time)
        a = self.modes@(f*np.cos(self.omega*time))
        return self.reaction(force42, q, a)

    def continuous_reaction_integral(self, force42, start, end):
        f = self.modes.T@np.asarray(force42)[list(PHYSICAL)]
        def primitives(time):
            phase = self.omega*time
            iq = self.modes@(f*time*sine_deficit(phase)/self.eigenvalues)
            ia = self.modes@(f*time*np.sinc(phase/np.pi))
            return iq, ia
        q0, a0 = primitives(start); q1, a1 = primitives(end)
        return self.reaction(np.asarray(force42)*(end-start), q1-q0, a1-a0)

    def midpoint_reaction(self, force42, dt, index):
        f = np.asarray(force42)[list(PHYSICAL)]
        before, _ = self.trajectory(f, (index-1)*dt, dt=dt, index=index-1)
        after, _ = self.trajectory(f, index*dt, dt=dt, index=index)
        qmid = .5*(before+after)
        amid = np.linalg.solve(self.mass, f-self.stiffness@qmid)
        return self.reaction(force42, qmid, amid)

    def midpoint_reaction_integral(self, force42, dt, count):
        return dt*sum((self.midpoint_reaction(force42, dt, n) for n in range(1, count+1)), np.zeros(6))

    def scales(self, force12, resultant, length, duration):
        q, v = self.trajectory(force12, duration)
        value = dict(configuration=self.mass_norm(q), velocity=self.mass_norm(v),
            elastic_configuration=self.positive_norm(q), elastic_velocity=self.positive_norm(v),
            energy=float(.5*(q@self.stiffness@q+v@self.mass@v)),
            force=float(np.linalg.norm(resultant)), moment=length*float(np.linalg.norm(resultant)),
            momentum=duration*float(np.linalg.norm(resultant)),
            angular_momentum=length*duration*float(np.linalg.norm(resultant)))
        assert all(np.isfinite(x) and x > 0. for x in value.values())
        return value
