"""Continuous development reference for the frozen two-mode oblique fixture.

No solver or material package is imported. Pressure modes have support 1/2;
their gaps differ from physical corner gaps. The membrane is uniform pure
deviatoric strain with perfect plasticity on the DNV first plateau, alpha<.005.
There is no hardening, general shell deformation or engineering acceptance.

Each fixed branch is affine. Matrix exponentials advance it; a Taylor/Bernstein
enclosure checks branch departure and excludes unresolved hidden excursions.
These enclosures concern the represented affine matrix and have an explicit
floating arithmetic allowance. Exponential/ODE propagation and event errors
are separately assessed by tighter controls and independent DOP853 arithmetic.
"""

from dataclasses import dataclass
from math import comb, exp, factorial
from time import perf_counter
from types import MappingProxyType

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm

E, NU, H, RHO = 1.e9, .3, .05, 1.e4
G, YIELD, KN, GAP = E/2.6, .2, 4.e11, .0008
NORMAL = np.array([np.sin(2.e-5), 0., np.cos(2.e-5)])
MASS = np.array([RHO*H/6., RHO*H])
TAU_Y = YIELD/np.sqrt(3.)
D = np.array([[-NORMAL[0]/6., NORMAL[2]], [NORMAL[0]/6., NORMAL[2]]])
B = D[:, 0]+NORMAL[2]*GAP
STATE_SCALES = np.array([1.e-8, 1.e-3, 1.e-5, 1., 1.e-8, 1.e-8])
_MATRIX_SCALES = np.array([1.e-8, 1.e-3, 1.e-3, 1., 1.e-8, 1.e-8, 1.])
_ORDER = 24
_BERNSTEIN = np.array([[comb(j, k)/comb(_ORDER, k) if k <= j else 0.
                        for k in range(_ORDER+1)] for j in range(_ORDER+1)])
_EPS = np.finfo(float).eps
for _constant in (NORMAL, MASS, D, B, STATE_SCALES, _MATRIX_SCALES, _BERNSTEIN):
    _constant.setflags(write=False)


class ReferenceResolutionError(ValueError):
    """Bounded reference cannot resolve this branch/event or plateau domain."""


@dataclass(frozen=True)
class ReferenceEvent:
    time: float
    kind: str
    indices: tuple[int, ...] = ()


@dataclass(frozen=True)
class ContinuousReference:
    times: np.ndarray
    q: np.ndarray
    v: np.ndarray
    p: np.ndarray
    alpha: np.ndarray
    tau: np.ndarray
    events: tuple[ReferenceEvent, ...]
    pressure_active: np.ndarray
    material_branch: np.ndarray
    kinetic_energy: np.ndarray
    elastic_energy: np.ndarray
    contact_energy: np.ndarray
    plastic_dissipation: np.ndarray
    diagnostics: object


def _owned(value, dtype=float):
    result = np.array(value, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


def _matrix(active, branch, enabled):
    matrix = np.zeros((7, 7))
    matrix[0, 2] = matrix[1, 3] = 1.
    support = .5*np.asarray(active, dtype=float) if enabled else np.zeros(2)
    stiffness = KN*D.T @ (support[:, None]*D)
    constant = KN*D.T @ (support*B)
    if branch == 0:
        stiffness[0, 0] += 4*G*H
        matrix[2, 4] = 4*G*H/MASS[0]
    else:
        constant[0] += branch*2*H*TAU_Y
        matrix[4, 2] = 1.
        matrix[5, 2] = 2*branch/np.sqrt(3.)
    matrix[2:4, :2] = -stiffness/MASS[:, None]
    matrix[2:4, 6] = -constant/MASS
    return matrix*_MATRIX_SCALES[None, :]/_MATRIX_SCALES[:, None]


def _functions(active, branch, enabled):
    rows = []
    if enabled:
        for index in range(2):
            orientation = -1. if active[index] else 1.
            row = np.zeros(7)
            row[:2], row[-1] = orientation*D[index], orientation*B[index]
            rows.append((row*_MATRIX_SCALES,
                         'contact_release' if active[index] else 'contact_closure', index, 1.e-14))
    if branch == 0:
        for sign in (-1, 1):
            row = np.zeros(7)
            row[0], row[4], row[-1] = -sign*2*G, sign*2*G, TAU_Y
            rows.append((row*_MATRIX_SCALES,
                         'yield_negative' if sign < 0 else 'yield_positive', sign, 1.e-10))
    else:
        row = np.zeros(7)
        row[2] = branch
        rows.append((row*_MATRIX_SCALES, 'unloading', branch, 1.e-16))
    return rows


def _taylor(matrix, z, h):
    terms = [z]
    errors = [0.]
    norm = float(np.linalg.norm(matrix, ord=np.inf))*(1.+16*_EPS)
    gamma = 8*_EPS/(1.-8*_EPS)
    for k in range(1, _ORDER+1):
        term = (matrix @ terms[-1])*(h/k)
        error = (norm*errors[-1]+gamma*norm*np.max(np.abs(terms[-1])))*(h/k)
        error += 2*_EPS*np.max(np.abs(term))
        terms.append(term)
        errors.append(error)
    x = norm*h
    remainder = np.max(np.abs(z))*exp(x)*x**(_ORDER+1)/factorial(_ORDER+1)
    return np.asarray(terms), np.asarray(errors), remainder


def _range(row, terms, errors, remainder):
    coefficients = terms @ row
    controls = _BERNSTEIN @ coefficients
    row_norm = np.sum(np.abs(row))*(1.+16*_EPS)
    allowance = row_norm*(np.sum(errors)+remainder)
    allowance += 16*_EPS*row_norm*np.sum(np.max(np.abs(terms), axis=1))
    allowance += 32*_EPS*np.sum(np.abs(coefficients))
    allowance = float(np.nextafter(allowance, np.inf))
    return float(np.min(controls)-allowance), float(np.max(controls)+allowance), allowance


def _check_grouped_residuals(selected, event_z):
    """Every time-near proposal must also fit its own dimensional gap budget."""
    largest_ratio = 0.
    for _, row, kind, index, tolerance, arithmetic_allowance in selected:
        residual = abs(float(row @ event_z))
        limit = tolerance+arithmetic_allowance
        if not np.isfinite(residual) or residual > limit:
            raise ReferenceResolutionError(
                'grouped continuous event residual exceeds its tolerance and arithmetic allowance')
        largest_ratio = max(largest_ratio, residual/limit)
    return largest_ratio


def continuous_reference(times, *, method='exponential', maximum_step=1.e-6,
                         relative_tolerance=2.e-12, absolute_tolerance=2.e-14,
                         event_time_tolerance=1.e-14, maximum_intervals=20000,
                         maximum_event_iterations=80, contact_enabled=True,
                         initial_q=(0., 0.), initial_v=(0., -1.),
                         initial_p=0., initial_alpha=0.):
    """States at requested times, with an incoming/tolerance branch convention.

    ODE tolerances are dimensionless after division by STATE_SCALES; they are
    not scalar absolute tolerances applied to tiny physical strain components.
    No state reset, projection or return-map history replacement is performed.
    An output exactly at a boundary can retain the incoming phase when its
    endpoint violation fits the declared branch tolerance. The phase switches
    on a subsequently resolved departure; right continuity is not promised.
    Exponential and DOP853 methods share the event and branch checking logic.
    """
    started = perf_counter()
    times = np.asarray(times, dtype=float)
    if (times.ndim != 1 or not times.size or not np.all(np.isfinite(times))
            or times[0] < 0. or np.any(np.diff(times) <= 0.) or times[-1] > .01
            or method not in ('exponential', 'dop853')
            or type(contact_enabled) is not bool
            or any(not np.isfinite(value) or value <= 0. for value in
                   (maximum_step, relative_tolerance, absolute_tolerance, event_time_tolerance))
            or maximum_step > 2.e-6
            or type(maximum_intervals) is not int or maximum_intervals < 1
            or type(maximum_event_iterations) is not int or maximum_event_iterations < 1):
        raise ValueError('invalid bounded continuous-reference controls or times')
    q0, v0 = np.asarray(initial_q, dtype=float), np.asarray(initial_v, dtype=float)
    if (q0.shape != (2,) or v0.shape != (2,) or not np.all(np.isfinite(q0))
            or not np.all(np.isfinite(v0)) or not np.isfinite(initial_p)
            or not np.isfinite(initial_alpha) or initial_alpha < 0.
            or initial_alpha >= .005 or abs(initial_p)*2/np.sqrt(3.) > initial_alpha+1.e-20):
        raise ValueError('invalid continuous-reference initial state')
    y = np.r_[q0, v0, initial_p, initial_alpha]
    tau0 = 2*G*(y[0]-y[4])
    if abs(tau0) > TAU_Y+1.e-10:
        raise ValueError('initial state lies outside the elastic/plateau domain')
    branch = int(np.sign(tau0)) if abs(tau0) >= TAU_Y-1.e-10 and tau0*y[2] > 0. else 0
    gaps0, rates0 = B+D@y[:2], D@y[2:4]
    active = ((gaps0 < 0.) | ((gaps0 == 0.) & (rates0 < 0.))) if contact_enabled else np.zeros(2, bool)
    events, saved, phases = [], [], []
    diagnostics = dict(method=method, maximum_step=maximum_step,
        relative_tolerance=relative_tolerance, dimensionless_absolute_tolerance=absolute_tolerance,
        state_scales=STATE_SCALES.tolist(), event_time_tolerance=event_time_tolerance,
        maximum_intervals=maximum_intervals, maximum_event_iterations=maximum_event_iterations,
        branch_gap_tolerance_m=1.e-14, branch_stress_tolerance_pa=1.e-10,
        branch_velocity_tolerance_per_s=1.e-16,
        intervals=0, exponential_evaluations=0, ode_function_evaluations=0,
        event_iterations=0, enclosure_halvings=0, zero_duration_events=0,
        maximum_gap_enclosure_allowance=0., maximum_stress_enclosure_allowance=0.,
        maximum_velocity_enclosure_allowance=0., maximum_yield_event_residual_pa=0.,
        maximum_contact_event_gap_residual_m=0., maximum_unloading_event_velocity_residual_per_s=0.,
        maximum_grouped_event_residual_ratio=0.,
        output_phase_convention='incoming phase may persist at a boundary within branch tolerance',
        scope='development reference, not accepted; pure-deviatoric uniform membrane, '
              'two normalized pressure groups, perfect plateau alpha<.005; '
              'no physical-corner penetration or generalized shell certificate')
    current = 0.
    cluster = set()

    for target in times:
        while current < target:
            diagnostics['intervals'] += 1
            if diagnostics['intervals'] > maximum_intervals:
                raise ReferenceResolutionError('continuous-reference interval budget exhausted')
            matrix = _matrix(active, branch, contact_enabled)
            z = np.r_[y, 1.]/_MATRIX_SCALES
            functions = _functions(active, branch, contact_enabled)
            cache = {0.: y.copy()}

            def propagate(h):
                if h not in cache:
                    if method == 'exponential':
                        diagnostics['exponential_evaluations'] += 1
                        cache[h] = (expm(matrix*h) @ z)[:6]*_MATRIX_SCALES[:6]
                    else:
                        # Independent physical-force evaluation, not matrix multiplication.
                        def rhs(t, scaled):
                            state = scaled*STATE_SCALES
                            strain, normal, ve, vw, p, alpha = state
                            tau = 2*G*(strain-p) if branch == 0 else branch*TAU_Y
                            force = np.array([2*H*tau, 0.])
                            if contact_enabled:
                                force += KN*D.T @ (.5*active*(B+D@state[:2]))
                            pdot = ve if branch else 0.
                            adot = 2*branch*ve/np.sqrt(3.) if branch else 0.
                            return np.r_[ve, vw, -force/MASS, pdot, adot]/STATE_SCALES
                        solution = solve_ivp(rhs, (0., h), y/STATE_SCALES, method='DOP853',
                            rtol=relative_tolerance, atol=absolute_tolerance, max_step=h)
                        diagnostics['ode_function_evaluations'] += solution.nfev
                        if not solution.success:
                            raise ReferenceResolutionError('independent DOP853 stage failed')
                        cache[h] = solution.y[:, -1]*STATE_SCALES
                    if not np.all(np.isfinite(cache[h])):
                        raise ReferenceResolutionError('nonfinite continuous-reference stage')
                return cache[h]

            h = min(maximum_step, target-current)
            while True:
                end = propagate(h)
                end_z = np.r_[end, 1.]/_MATRIX_SCALES
                terms, errors, remainder = _taylor(matrix, z, h)
                crossings, uncertain = [], False
                for row, kind, index, tolerance in functions:
                    low, high, error = _range(row, terms, errors, remainder)
                    dlow, dhigh, derror = _range(row @ matrix, terms, errors, remainder)
                    label = 'gap' if kind.startswith('contact') else 'velocity' if kind == 'unloading' else 'stress'
                    key = 'maximum_'+label+'_enclosure_allowance'
                    diagnostics[key] = max(diagnostics[key], error)
                    first, last = float(row @ z), float(row @ end_z)
                    allowance = tolerance+error
                    if first < -allowance:
                        raise ReferenceResolutionError('selected continuous branch is inconsistent at its origin')
                    if last < -tolerance:
                        if dhigh >= 0.:
                            uncertain = True
                        else:
                            crossings.append((row, kind, index, tolerance, error))
                    elif low < -allowance and not (dlow > 0. and first >= -allowance):
                        uncertain = True
                if not uncertain:
                    break
                diagnostics['enclosure_halvings'] += 1
                h *= .5
                if h < event_time_tolerance or current+h == current:
                    raise ReferenceResolutionError('unresolved hidden excursion or grazing continuous event')

            proposed = []
            for row, kind, index, tolerance, arithmetic_allowance in crossings:
                left, right = 0., h
                fleft = float(row @ z)
                if fleft <= 0.:
                    proposed.append((0., row, kind, index, tolerance, arithmetic_allowance))
                    continue
                for iteration in range(maximum_event_iterations):
                    diagnostics['event_iterations'] += 1
                    middle = left+.5*(right-left)
                    middle_state = np.r_[propagate(middle), 1.]/_MATRIX_SCALES
                    value = float(row @ middle_state)
                    if value > 0.:
                        left = middle
                    else:
                        right = middle
                    root = left+.5*(right-left)
                    residual = abs(float(row @ (np.r_[propagate(root), 1.]/_MATRIX_SCALES)))
                    if right-left <= event_time_tolerance and residual <= tolerance:
                        proposed.append((root, row, kind, index, tolerance, arithmetic_allowance))
                        break
                else:
                    raise ReferenceResolutionError('continuous event root budget exhausted')

            if proposed:
                advance = min(item[0] for item in proposed)
                event_state = propagate(advance).copy()
                selected = [item for item in proposed if abs(item[0]-advance) <= event_time_tolerance]
                ratio = _check_grouped_residuals(selected, np.r_[event_state, 1.]/_MATRIX_SCALES)
                diagnostics['maximum_grouped_event_residual_ratio'] = max(
                    diagnostics['maximum_grouped_event_residual_ratio'], ratio)
                y = event_state
                if advance > 0.:
                    current += advance
                    cluster.clear()
                else:
                    diagnostics['zero_duration_events'] += 1
                for _, row, kind, index, tolerance, arithmetic_allowance in selected:
                    identity = (kind, index)
                    if identity in cluster or len(cluster) >= 6:
                        raise ReferenceResolutionError('zero-time continuous event cluster stalled')
                    cluster.add(identity)
                    if kind.startswith('contact'):
                        diagnostics['maximum_contact_event_gap_residual_m'] = max(
                            diagnostics['maximum_contact_event_gap_residual_m'], abs((B+D@y[:2])[index]))
                        active[index] = kind == 'contact_closure'
                        events.append(ReferenceEvent(float(current), kind, (index,)))
                    elif kind == 'unloading':
                        diagnostics['maximum_unloading_event_velocity_residual_per_s'] = max(
                            diagnostics['maximum_unloading_event_velocity_residual_per_s'], abs(y[2]))
                        branch = 0
                        events.append(ReferenceEvent(float(current), kind))
                    else:
                        branch = index
                        diagnostics['maximum_yield_event_residual_pa'] = max(
                            diagnostics['maximum_yield_event_residual_pa'], abs(2*G*(y[0]-y[4])-index*TAU_Y))
                        events.append(ReferenceEvent(float(current), kind))
            else:
                y = end.copy()
                current = float(target) if h == target-current else current+h
                cluster.clear()
            if y[5] >= .005:
                raise ReferenceResolutionError('continuous reference left the supported first plateau')
        saved.append(y.copy())
        phases.append((active.copy(), branch))

    saved = np.asarray(saved)
    q, v, p, alpha = saved[:, :2], saved[:, 2:4], saved[:, 4], saved[:, 5]
    tau = 2*G*(q[:, 0]-p)
    kinetic = .5*np.sum(MASS*v*v, axis=1)
    elastic = 2*G*H*(q[:, 0]-p)**2
    contact = (.25*KN*np.sum(np.minimum(B+q@D.T, 0.)**2, axis=1)
               if contact_enabled else np.zeros(len(times)))
    dissipation = H*YIELD*(alpha-initial_alpha)
    initial_energy = (.5*np.sum(MASS*v0*v0)+2*G*H*(q0[0]-initial_p)**2
                      +(.25*KN*np.sum(np.minimum(gaps0, 0.)**2) if contact_enabled else 0.))
    diagnostics.update(elapsed_seconds=perf_counter()-started,
        maximum_energy_balance_error_j=float(np.max(np.abs(kinetic+elastic+contact+dissipation-initial_energy))),
        initial_energy_j=float(initial_energy),
        maximum_alpha=float(np.max(alpha)), event_count=len(events))
    return ContinuousReference(_owned(times), _owned(q), _owned(v), _owned(p), _owned(alpha),
        _owned(tau), tuple(events), _owned([phase[0] for phase in phases], bool),
        _owned([phase[1] for phase in phases], int), _owned(kinetic), _owned(elastic),
        _owned(contact), _owned(dissipation), MappingProxyType(diagnostics))
