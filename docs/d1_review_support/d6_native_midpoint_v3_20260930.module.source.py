"""Private single-element elastic native midpoint development owner.

No public finite-speed admission, static codec mutation or physical condensation.
Algebraic nodal-frame velocity slots are inertial placeholders only: stage and
endpoint nodal frames are independent solved coordinates and generally move.
"""
from dataclasses import dataclass
from contextlib import contextmanager
import json
from threading import Lock
import numpy as np

from ._ge_beam3_native_analysis import NativeBeamAnalysis
from ._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from ._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from ._ge_beam3_retained_generalized_state import Context, Program, Mechanical
from ._ge_beam3_native_generalized_loading import DistributedPattern
from ._ge_beam3_native_line_loading import LinePattern
from ._ge_beam3_centered_finite_inertia import (
    evaluate_centered_finite_inertia, PHYSICAL_DOFS, ALGEBRAIC_DOFS)
from ._ge_beam3_p5.algebra import rotation
from ._ge_beam3_p5.chart import exp_chart_terms
from ._ge_beam3_p5.compensated_coordinates import split_sum
from ._ge_beam3_p5_seeded.core import canonical, sha
from ._native_reference_modal import _owned
from .control import cancellation_safe_point

IMPLEMENTATION_ID = 'DEVELOPMENT_C7_SINGLE_CENTERED_NATIVE_MIDPOINT_V1'


@dataclass(frozen=True)
class MidpointState:
    mechanical: Mechanical
    origins: tuple
    histories: tuple
    physical_velocity24: np.ndarray
    physical_acceleration24: np.ndarray
    time: float
    epoch: int
    predecessor_sha256: str
    context_sha256: str


@dataclass(frozen=True)
class StageEvaluation:
    mechanical: Mechanical
    residual: np.ndarray
    jacobian: np.ndarray
    configuration_map: np.ndarray
    physical_velocity24: np.ndarray
    physical_acceleration24: np.ndarray
    structural_residual: np.ndarray
    structural_jacobian: np.ndarray
    inertia: object
    material_sha256: str


@dataclass(frozen=True)
class MidpointCandidate:
    endpoint: MidpointState
    stage: StageEvaluation
    unknown42: np.ndarray
    dt: float
    predecessor_sha256: str
    iterations: int
    backtracks: int
    stage_residual_norm: float
    endpoint_algebraic_norm: float
    endpoint_reaction42: np.ndarray


class MidpointContext:
    """Immutable issued states, ephemeral trials, and atomic accepted replacement.

    Every external operation runs under the exact analysis operation lock. One
    homogeneous six-component clamp on the first native node is admitted here.
    The original static Context deadline remains in force for this context.
    """
    def __init__(self, analysis, *, inertia_order=24, max_iterations=12,
                 max_backtracks=8):
        if type(analysis) is not NativeBeamAnalysis:
            raise ValueError('exact standalone native analysis required')
        if (type(inertia_order) is not int or inertia_order not in (4, 8, 24)
                or type(max_iterations) is not int or not 1 <= max_iterations <= 12
                or type(max_backtracks) is not int or not 0 <= max_backtracks <= 8):
            raise ValueError('bounded exact midpoint settings')
        with analysis._operation():
            elements = analysis._elements
            if (len(elements) != 1 or type(elements[0]) is not NativeGeneralizedStaticElement
                    or type(elements[0].section) is not EllipsoidalGeneralizedSection
                    or len(analysis.model.mesh.nodes) != 3
                    or analysis.model.mesh.dof_manager.total_dofs != 18):
                raise ValueError('one centered generalized element/full 42 order required')
            if analysis._admit_boundaries() != tuple(range(6)):
                raise ValueError('explicit homogeneous full clamp on first ordered node required')
            self.analysis = analysis
            self.element = elements[0]
            self.inertia_order = inertia_order
            self.max_iterations = max_iterations
            self.max_backtracks = max_backtracks
            self._static = Context(analysis.model, Program((0.,),
                DistributedPattern(LinePattern(()), ())))
            if (self._static.count != 42 or self._static.slots != [list(range(42))]
                    or self._static.nodal_count != 18):
                raise ValueError('exact one-element canonical mixed ordering required')
            self.free = np.frombuffer(np.asarray(self._static.free, dtype=int).tobytes(), dtype=int)
            self.physical_free = tuple(i for i in PHYSICAL_DOFS if i in self.free)
            self.algebraic_free = tuple(i for i in ALGEBRAIC_DOFS if i in self.free)
            if len(self.physical_free) != 12 or len(self.algebraic_free) != 24:
                raise ValueError('explicit physical/algebraic supported partition required')
            self._identity = sha(dict(implementation=IMPLEMENTATION_ID,
                analysis=analysis.identity, inertia_order=inertia_order,
                iterations=max_iterations, backtracks=max_backtracks,
                physical=self.physical_free, algebraic=self.algebraic_free, free=self.free,
                static_context=self._static.identity))
            self._current = None
            self._visible_current = None
            self._current_bytes = None
            self._issued = {}
            self._candidates = {}
            self._initial_checks = None
            self._transaction_lock = Lock()

    @property
    def initial_checks(self):
        return None if self._initial_checks is None else json.loads(self._initial_checks)

    @property
    def current(self):
        return self._visible_current

    @contextmanager
    def _atomic_operation(self):
        # The analysis exit guard runs after the operation body. Keep tentative
        # publication private until that guard succeeds; restore all issuance
        # bookkeeping if it fails. A separate nonblocking lock prevents another
        # midpoint operation entering between analysis-lock release and rollback.
        if not self._transaction_lock.acquire(blocking=False):
            raise ValueError('midpoint context is already in use')
        snapshot = None
        try:
            try:
                with self.analysis._operation():
                    snapshot = (self._current, self._visible_current, self._current_bytes,
                        self._issued.copy(), self._candidates.copy(), self._initial_checks)
                    yield
                self._visible_current = self._current
            except BaseException:
                if snapshot is not None:
                    (self._current, self._visible_current, self._current_bytes,
                     self._issued, self._candidates, self._initial_checks) = snapshot
                raise
        finally:
            self._transaction_lock.release()

    def _guard(self, token=None, stage='midpoint.guard'):
        cancellation_safe_point(token, stage)
        self.analysis._guard()
        self._static.guard()
        expected = sha(dict(implementation=IMPLEMENTATION_ID,
            analysis=self.analysis.identity, inertia_order=self.inertia_order,
            iterations=self.max_iterations, backtracks=self.max_backtracks,
            physical=self.physical_free, algebraic=self.algebraic_free, free=self.free,
            static_context=self._static.identity))
        if self._identity != expected or self.analysis._elements != (self.element,):
            raise ValueError('midpoint context definition/settings changed')

    def _require_current(self, state):
        record = self._issued.get(id(state))
        if (type(state) is not MidpointState or state is not self.current
                or record is None or record[0] is not state
                or canonical(state) != record[1] or record[1] != self._current_bytes
                or state.context_sha256 != self._identity):
            raise ValueError('current issued immutable midpoint predecessor required')
        return sha(state)

    def _structural(self, mechanical, origins):
        r, j, _, responses, _ = self._static.assemble(mechanical, 0., origins)
        for response, origin in zip(responses, origins):
            material = json.loads(response.material)
            if canonical(response.history) != canonical(origin):
                raise ValueError('midpoint first slice requires unchanged elastic history')
            if any(row['branch'] != 'ELASTIC'
                   or any(value != 0. for pair in row['dissipation'] for value in pair)
                   for row in material['stations']):
                raise ValueError('midpoint first slice requires strictly elastic stations')
        return r, j, sha([response.material.decode() for response in responses])

    def _inertia(self, mechanical, velocity, acceleration):
        result = evaluate_centered_finite_inertia(self.element.operator.reference,
            self.analysis._inertias[self.element.element_id],
            mechanical.positions, mechanical.position_low,
            mechanical.cell_rotations[0], velocity, acceleration,
            order=self.inertia_order)
        a = list(ALGEBRAIC_DOFS)
        for matrix in (result.mixed_mass, result.mixed_velocity_derivative,
                       result.mixed_configuration_derivative):
            if np.any(matrix[a, :]) or np.any(matrix[:, a]):
                raise ValueError('algebraic inertia derivative must be exactly zero')
        if np.any(result.mixed_inertia[a]) or np.any(result.mixed_generalized_momentum[a]):
            raise ValueError('algebraic inertia must be exactly zero')
        return result

    def _block_checks(self, j, inertia):
        z = list(self.algebraic_free)
        p = list(self.physical_free)
        cz = j[np.ix_(z, z)]
        singular = np.linalg.svd(cz, compute_uv=False)
        tolerance = 64*np.finfo(float).eps*len(z)*singular[0]
        if not np.isfinite(singular).all() or singular[-1] <= tolerance:
            raise ValueError('endpoint algebraic C_z singular: no time step admitted')
        mass = inertia.mixed_mass[np.ix_(p, p)]
        if np.linalg.norm(mass-mass.T) > 64*np.finfo(float).eps*np.linalg.norm(mass):
            raise ValueError('physical mass symmetry contract failed')
        np.linalg.cholesky((mass+mass.T)/2)
        eigenvalues = np.linalg.eigvalsh((mass+mass.T)/2)
        return dict(algebraic_rank=len(z), algebraic_sigma_min=float(singular[-1]),
            algebraic_sigma_max=float(singular[0]),
            algebraic_condition=float(singular[0]/singular[-1]),
            physical_mass_min_eigenvalue=float(eigenvalues[0]),
            physical_mass_max_eigenvalue=float(eigenvalues[-1]),
            physical_mass_condition=float(eigenvalues[-1]/eigenvalues[0]))

    def _norm(self, residual, indices):
        return float(np.linalg.norm((residual/self._static.scale)[list(indices)]))

    def _correction(self, mechanical, step):
        nodal = step[:18].reshape(3, 6)
        return max(float(np.linalg.norm(nodal[:, :3]))/self._static.length,
            float(np.linalg.norm(nodal[:, 3:])), float(np.linalg.norm(step[18:24])),
            float(np.linalg.norm(step[24:]))/max(1., float(np.linalg.norm(mechanical.resultants))))

    def _solve_algebraic(self, mechanical, origins, token):
        z = list(self.algebraic_free)
        for iteration in range(self.max_iterations+1):
            self._guard(token, 'midpoint.algebraic')
            r, j, material = self._structural(mechanical, origins)
            inertia = self._inertia(mechanical, np.zeros(24), np.zeros(24))
            self._block_checks(j, inertia)
            step = np.zeros(42)
            step[z] = np.linalg.solve(j[np.ix_(z, z)], -r[z])
            norm = self._norm(r, z)
            if norm <= 1e-11 and self._correction(mechanical, step) <= 1e-11:
                return mechanical, r, j, norm, material
            if iteration == self.max_iterations:
                raise ValueError('endpoint algebraic iteration limit')
            for cut in range(self.max_backtracks+1):
                self._guard(token, 'midpoint.algebraic.trial')
                proposed = self._static.advance(mechanical, step*(2.**(-cut)))
                rt, _, _ = self._structural(proposed, origins)
                if self._norm(rt, z) < norm:
                    mechanical = proposed
                    break
            else:
                raise ValueError('endpoint algebraic residual backtracking failed')
        raise AssertionError('bounded algebraic loop')

    def _endpoint_acceleration(self, mechanical, origins, velocity):
        r, j, _ = self._structural(mechanical, origins)
        inertia = self._inertia(mechanical, velocity, np.zeros(24))
        checks = self._block_checks(j, inertia)
        p = list(self.physical_free)
        acceleration = np.zeros(24)
        acceleration[p] = np.linalg.solve(inertia.mixed_mass[np.ix_(p, p)],
            -(r+inertia.mixed_inertia)[p])
        dynamic = self._inertia(mechanical, velocity, acceleration)
        reaction = r+dynamic.mixed_inertia
        if self._norm(reaction, p) > 1e-11:
            raise ValueError('endpoint physical acceleration residual failed')
        return _owned(acceleration), _owned(reaction), checks

    def initialize(self, mechanical=None, physical_velocity24=None, *, time=0.,
                   cancellation_token=None):
        with self._atomic_operation():
            self._guard(cancellation_token, 'midpoint.initialize')
            if self.current is not None or type(time) is not float or not np.isfinite(time):
                raise ValueError('one finite typed midpoint initialization required')
            mechanical = self._static.initial.mechanical if mechanical is None else mechanical
            if type(mechanical) is not Mechanical:
                raise ValueError('exact retained mechanical input required')
            mechanical = self._static.make(mechanical.descriptor())
            velocity = np.zeros(24) if physical_velocity24 is None else np.asarray(physical_velocity24)
            if velocity.shape != (24,) or velocity.dtype != np.float64 or not np.isfinite(velocity).all():
                raise ValueError('finite binary64 physical velocity24 required')
            inactive = tuple(i for i in range(24) if i not in self.physical_free)
            if np.any(velocity[list(inactive)]):
                raise ValueError('fixed velocity/algebraic inertial placeholders must be zero')
            velocity = _owned(velocity)
            origins = self._static.initial.histories
            mechanical, _, _, _, _ = self._solve_algebraic(mechanical, origins, cancellation_token)
            acceleration, _, checks = self._endpoint_acceleration(mechanical, origins, velocity)
            state = MidpointState(mechanical, origins, origins, velocity, acceleration,
                time, 0, self._identity, self._identity)
            self._guard(cancellation_token, 'midpoint.initialize.commit')
            self._initial_checks = canonical(checks)
            self._issued[id(state)] = (state, canonical(state))
            self._current = state
            self._current_bytes = canonical(state)
            return state

    def _stage(self, accepted, u, h, token=None):
        self._guard(token, 'midpoint.stage')
        self._require_current(accepted)
        u = np.asarray(u)
        if u.shape != (42,) or u.dtype != np.float64 or not np.isfinite(u).all() or np.any(u[:6]):
            raise ValueError('supported finite binary64 midpoint unknown42 required')
        s = {k: v.copy() for k, v in accepted.mechanical.descriptor().items()}
        a = np.eye(42)
        for node in range(3):
            first = 6*node
            for axis in range(3):
                s['positions'][node, axis], s['position_low'][node, axis] = split_sum((
                    float(s['positions'][node, axis]), float(s['position_low'][node, axis]),
                    .5*float(u[first+axis])))
            a[first:first+3, first:first+3] *= .5
            eta = u[first+3:first+6]
            s['nodal_frames'][node] = rotation(eta)@accepted.mechanical.nodal_frames[node]
            a[first+3:first+6, first+3:first+6] = exp_chart_terms(eta)[0]
        for cell in (0, 1):
            first = 18+3*cell
            half = .5*u[first:first+3]
            s['cell_rotations'][0, cell] = rotation(half)@accepted.mechanical.cell_rotations[0, cell]
            a[first:first+3, first:first+3] = .5*exp_chart_terms(half)[0]
        s['resultants'][0] += u[24:]
        mechanical = self._static.make(s)
        velocity = np.zeros(24)
        p = list(self.physical_free)
        velocity[p] = u[p]/h
        acceleration = np.zeros(24)
        acceleration[p] = 2*(velocity[p]-accepted.physical_velocity24[p])/h
        r, j, material = self._structural(mechanical, accepted.histories)
        inertia = self._inertia(mechanical, velocity, acceleration)
        vmap = np.zeros((42, 42))
        bmap = np.zeros((42, 42))
        vmap[p, p] = 1/h
        bmap[p, p] = 2/h**2
        jacobian = (j+inertia.mixed_configuration_derivative)@a
        jacobian += inertia.mixed_velocity_derivative@vmap+inertia.mixed_mass@bmap
        residual = r+inertia.mixed_inertia
        if not np.isfinite(jacobian).all() or not np.isfinite(residual).all():
            raise ValueError('nonfinite midpoint stage')
        return StageEvaluation(mechanical, _owned(residual), _owned(jacobian), _owned(a),
            _owned(velocity), _owned(acceleration), _owned(r), _owned(j), inertia, material)

    def evaluate_stage(self, accepted, unknown42, *, dt, cancellation_token=None):
        with self._atomic_operation():
            self._time_step(dt)
            return self._stage(accepted, unknown42, dt, cancellation_token)

    @staticmethod
    def _time_step(h):
        if (type(h) is not float or not np.isfinite(h) or h <= 0.
                or h*h == 0. or not np.isfinite(2/(h*h))):
            raise ValueError('positive finite typed midpoint dt required')

    def trial(self, accepted, *, dt, cancellation_token=None):
        with self._atomic_operation():
            self._time_step(dt)
            self._guard(cancellation_token, 'midpoint.trial')
            predecessor = self._require_current(accepted)
            free = list(map(int, self.free))
            p = list(self.physical_free)
            u = np.zeros(42)
            u[p] = dt*accepted.physical_velocity24[p]
            backtracks = 0
            for iteration in range(self.max_iterations+1):
                stage = self._stage(accepted, u, dt, cancellation_token)
                step = np.zeros(42)
                step[free] = np.linalg.solve(stage.jacobian[np.ix_(free, free)], -stage.residual[free])
                norm = self._norm(stage.residual, free)
                if norm <= 1e-11 and self._correction(stage.mechanical, step) <= 1e-11:
                    break
                if iteration == self.max_iterations:
                    raise ValueError('midpoint stage iteration limit')
                for cut in range(self.max_backtracks+1):
                    self._guard(cancellation_token, 'midpoint.stage.trial')
                    proposed = u+2.**(-cut)*step
                    next_stage = self._stage(accepted, proposed, dt, cancellation_token)
                    backtracks += int(cut > 0)
                    if self._norm(next_stage.residual, free) < norm:
                        u = proposed
                        break
                else:
                    raise ValueError('midpoint stage residual backtracking failed')
            endpoint_step = np.zeros(42)
            endpoint_step[p] = u[p]
            endpoint_mechanical = self._static.advance(accepted.mechanical, endpoint_step)
            # Stage algebraics are a starting guess, not accepted endpoint data.
            endpoint_mechanical = self._static.make(dict(
                positions=endpoint_mechanical.positions, position_low=endpoint_mechanical.position_low,
                nodal_frames=stage.mechanical.nodal_frames,
                cell_rotations=endpoint_mechanical.cell_rotations,
                resultants=stage.mechanical.resultants))
            endpoint_mechanical, _, _, alg_norm, _ = self._solve_algebraic(
                endpoint_mechanical, accepted.histories, cancellation_token)
            velocity = np.zeros(24)
            velocity[p] = 2*stage.physical_velocity24[p]-accepted.physical_velocity24[p]
            acceleration, reaction, _ = self._endpoint_acceleration(
                endpoint_mechanical, accepted.histories, velocity)
            if not np.isfinite(accepted.time+dt) or accepted.time+dt <= accepted.time:
                raise ValueError('midpoint time increment is not representable')
            endpoint = MidpointState(endpoint_mechanical, accepted.histories, accepted.histories,
                _owned(velocity), acceleration, accepted.time+dt, accepted.epoch+1,
                predecessor, self._identity)
            candidate = MidpointCandidate(endpoint, stage, _owned(u), dt, predecessor,
                iteration, backtracks, norm, alg_norm, reaction)
            self._guard(cancellation_token, 'midpoint.trial.ready')
            self._require_current(accepted)
            self._candidates[id(candidate)] = (candidate, canonical(candidate))
            return candidate

    def commit(self, candidate, *, cancellation_token=None):
        with self._atomic_operation():
            self._guard(cancellation_token, 'midpoint.before_commit')
            record = self._candidates.get(id(candidate))
            if (type(candidate) is not MidpointCandidate or record is None
                    or record[0] is not candidate or canonical(candidate) != record[1]
                    or candidate.predecessor_sha256 != self._require_current(self.current)
                    or candidate.endpoint.epoch != self.current.epoch+1):
                raise ValueError('issued current-predecessor immutable midpoint candidate required')
            state = candidate.endpoint
            self._issued[id(state)] = (state, canonical(state))
            self._current = state
            self._current_bytes = canonical(state)
            self._candidates.clear()
            return state

    def discard(self, candidate):
        with self._atomic_operation():
            self._guard()
            record = self._candidates.get(id(candidate))
            if record is None or record[0] is not candidate or canonical(candidate) != record[1]:
                raise ValueError('issued immutable midpoint candidate required')
            del self._candidates[id(candidate)]
