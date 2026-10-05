"""Accepted elastic GE/Q4 point buckling, full mixed sparse descriptor.

Lambda scales frozen accepted prestress, not the nonlinear equilibrium load.
No resultant elimination, SPD whitening, mass or symmetry repair is used.
"""
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import pickle

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, eigs, ArpackError

from .control import CancellationToken, SolveCancelled, cancellation_safe_point
from .linalg import MatrixClass, factorize_cached
from ._native_reference_modal import _owned
from ._ge_beam3_pose_joint import _exp_terms
from ._ge_beam3_p5.algebra import skew
from ._ge_beam3_p5_seeded.core import canonical
from ._ge_beam3_retained_generalized import RetainedGeneralizedOperator
from ._stiffened_shell_q4_algorithmic_pullback import POLICY as Q4_POLICY, conservative_components
from ._stiffened_shell_ge_finite_experimental import _position_pair, _State
from ._stiffened_shell_b2_q4_panel_experimental import _modal_scaled_residual

POLICY = 'GE_Q4_POINT_ACCEPTED_CONSERVATIVE_MIXED_BUCKLING_V1_EXPERIMENTAL'
TOLERANCE = 1e-8


@dataclass(frozen=True)
class GEPointBucklingRequest:
    expected_generation: int
    count: int = 3
    shift: float = 1.
    bounds: tuple[float, float] = (0., 1e12)
    max_iterations: int = 600

    def __post_init__(self):
        if (type(self.expected_generation) is not int or self.expected_generation <= 0
                or type(self.count) is not int or self.count <= 0
                or type(self.max_iterations) is not int or self.max_iterations <= 0
                or type(self.shift) not in (float, int) or not np.isfinite(self.shift) or self.shift <= 0
                or type(self.bounds) is not tuple or len(self.bounds) != 2
                or any(type(v) not in (float, int) or not np.isfinite(v) for v in self.bounds)
                or not 0 <= self.bounds[0] < self.bounds[1]):
            raise ValueError('finite positive bounded point-buckling controls and accepted generation required')


@dataclass(frozen=True)
class GEPointBucklingResult:
    status: str
    model_identity: str
    generation: int
    checkpoint_sha256: str
    pencil_identity: str = ''
    prestress_multipliers: tuple = ()
    full_coordinates: tuple = ()
    shell_coordinate_modes: tuple = ()
    shell_spatial_modes: tuple = ()
    beam_modes: tuple = ()
    cell_rotation_modes: tuple = ()
    resultant_modes: tuple = ()
    multiplier_modes: tuple = ()
    coordinate_support_reactions: tuple = ()
    physical_support_wrenches: tuple = ()
    support_provenance: tuple = ()
    equation_residuals: tuple = ()
    constraint_residuals: tuple = ()
    inverse_eigenvalues: tuple = ()
    factorization_count: int = 0
    solve_count: int = 0
    decomposition_error: float = 0.
    symmetry_error: float = 0.
    failure_reason: str | None = None
    policy: str = POLICY
    selection: str = 'finite positive prestress factors nearest shift; completeness unqualified'
    load_factor_interpretation: str = 'frozen accepted prestress scale; not a nonlinear limit load'
    production_qualified: bool = False


@dataclass(frozen=True)
class AcceptedSnapshot:
    generation: int
    checkpoint_sha256: str
    q: np.ndarray
    frames: np.ndarray
    cells: np.ndarray
    resultants: np.ndarray
    multipliers: np.ndarray
    shell_anchors: np.ndarray | None
    applied_dead_load: np.ndarray
    shell_origins: bytes = field(repr=False)
    beam_origins: bytes = field(repr=False)


@dataclass(frozen=True)
class PointBucklingPencil:
    material: object
    geometric: object
    constraints: object
    hessian: object
    shell_geometric: object
    beam_geometric: object
    multiplier_curvature: object
    residual: np.ndarray
    chart: object
    free: tuple
    fixed: tuple
    primal_count: int
    snapshot: AcceptedSnapshot
    identity: str
    decomposition_error: float
    symmetry_error: float


class _Failure(RuntimeError):
    pass


def _freeze(matrix):
    result = matrix.tocsc(copy=True)
    result.sum_duplicates(); result.eliminate_zeros(); result.sort_indices()
    if not np.isfinite(result.data).all():
        raise _Failure('nonfinite sparse conservative block')
    for name in ('data', 'indices', 'indptr'):
        value = getattr(result, name)
        setattr(result, name, np.frombuffer(value.tobytes(), dtype=value.dtype))
    return result


def _matrix_digest(matrices):
    digest = sha256()
    for matrix in matrices:
        digest.update(repr(matrix.shape).encode())
        for value in (matrix.indptr, matrix.indices, matrix.data):
            digest.update(value.tobytes())
    return digest.hexdigest()


def _state_digest(driver):
    return sha256(pickle.dumps((driver._state, driver._shell_origins,
        driver._beam_origins, driver._pattern, driver._applied_load, driver._load_factor), protocol=5)).hexdigest()


def _model_digest(owner):
    # Boundary-only witness, not an inner-loop model scan. Captured definition
    # bytes, actual shell geometry/material and support/scaling provenance bind
    # all data used by this route; local native guards own their kernels.
    geometry = tuple((node, owner._shell_model.mesh.nodes[node].coords()) for node in owner._shell_ids)
    materials = tuple(owner._shell_model.get_material(element.material_name) for _, element, _, _ in owner._shell_parts)
    elements = tuple((eid, tuple(element.node_ids), element.thickness)
                     for eid, element, _, _ in owner._shell_parts)
    return sha256(pickle.dumps((owner._identity, owner._definition, geometry, materials, elements,
        owner._fixed, owner._free, owner._coordinate_scale, owner._constraint_scale), protocol=5)).hexdigest()


def _admit(owner, generation=None):
    owner._require_open()
    d = owner._definition
    driver = owner._finite_driver
    if (driver is None or driver._accepted is None or owner._accepted is not None
            or (generation is not None and generation != owner._generation)):
        raise ValueError('current accepted finite state and matching generation required')
    if (d.q4_pullback_policy != Q4_POLICY or d.shell_reference_policy != 'flat'
            or not d.shell.q4_elements or d.shell.s3_elements or d.shell.j2_curve is not None
            or not d.points or d.lines or d.footprints or d.distributing_footprints
            or d.finite_distributing_footprints or owner._has_physical_fibre
            or driver._external is not None or driver._programme is not None):
        raise ValueError('accepted buckling requires elastic objective flat Q4/generalized GE six-pose points and nodal dead translations')
    if not len(owner._fixed):
        raise ValueError('supported point buckling requires declared fixed coordinates')
    fixed = set(owner._fixed)
    for start, count in ((0, len(owner._shell_ids)), (owner._shell_count, len(owner._beam_ids))):
        for node in range(count):
            flags = [start+6*node+j in fixed for j in (3, 4, 5)]
            if any(flags) and not all(flags):
                raise ValueError('physical rotational supports require full fixed triples')
    applied = driver._applied_load
    if applied is None:
        if driver._pattern is None:
            raise ValueError('accepted dead-load identity is missing')
        applied = driver._load_factor*driver._pattern
    nodal = owner._shell_count+6*len(owner._beam_ids)
    if (not np.isfinite(applied).all() or np.any(applied[nodal:] != 0)
            or np.any(applied[:nodal].reshape(-1, 6)[:, 3:] != 0)):
        raise ValueError('conservative buckling admits nodal dead translations only')
    if driver._accepted.free_equilibrium_ratio > TOLERANCE or driver._accepted.constraint_max > 1e-9:
        raise ValueError('accepted equilibrium/constraint witness is unresolved')
    for element, _, _ in owner._beam_parts:
        if type(element.operator) is not RetainedGeneralizedOperator:
            raise ValueError('full42 generalized retained member required')
    return driver, applied


def capabilities(owner):
    reason = None
    try:
        _admit(owner)
    except (ValueError, RuntimeError) as exc:
        reason = str(exc)
    return dict(policy=POLICY, definition_admitted=reason is None,
        eligible=None if reason is None else False, material_capture_validation_pending=reason is None,
        ineligibility_reason=reason,
        state='accepted elastic objective Q4/generalized GE six-pose-point equilibrium',
        coordinates='all shell, native nodal/cell rotations, eighteen resultants/member and point multipliers',
        loads='conservative nodal dead translations', mass='none',
        material_admission='elastic-interior unchanged-history and yield-margin witness checked during capture, before factorization',
        selection='finite positive factors nearest shift; completeness unqualified',
        multiplier='frozen accepted prestress, not a nonlinear limit load', production_qualified=False)


def _elastic_beam(core, response, origin):
    if canonical(response.history) != canonical(origin):
        raise ValueError('buckling replay must not advance generalized history')
    material = json.loads(response.material)
    with localcontext() as context:
        context.prec = 80
        for station, history in zip(material['stations'], origin.stations, strict=True):
            if station['branch'] != 'ELASTIC':
                raise ValueError('buckling requires elastic-interior generalized material')
            high, low = station['resultants']
            values = [Decimal.from_float(a)+Decimal.from_float(b) for a, b in zip(high, low)]
            radius = Decimal.from_float(core.section.yield_force)+Decimal.from_float(core.section.hardening)*core.section._origin(history)[1]
            q = sum(values[i]*core.section._m[i][j]*values[j] for i in range(6) for j in range(6)).sqrt()
            if radius-q <= Decimal.from_float(64*np.finfo(float).eps)*max(Decimal(1), q, radius):
                raise ValueError('generalized material is on an unresolved yield boundary')


def capture(owner, expected_generation, *, cancellation_token=None):
    """Pure local replay from copied accepted data; no trial-cache publication."""
    driver, applied = _admit(owner, expected_generation)
    initial_state = driver._state
    initial_digest = _state_digest(driver)
    initial_model_digest = _model_digest(owner)
    checkpoint = sha256(driver.checkpoint()).hexdigest()
    snap = AcceptedSnapshot(owner._generation, checkpoint,
        *(_owned(value) for value in (initial_state.q, initial_state.frames, initial_state.cells,
                                     initial_state.resultants, initial_state.multipliers)),
        None if initial_state.shell_anchors is None else _owned(initial_state.shell_anchors),
        _owned(applied), pickle.dumps(driver._shell_origins, protocol=5), pickle.dumps(driver._beam_origins, protocol=5))
    n = owner._K.shape[0]; r = len(snap.multipliers); size = n+r
    terms = {name: ([], [], []) for name in ('material', 'shell', 'beam', 'joint', 'total')}
    forces = [[] for _ in range(size)]
    chart = sparse.eye(size, format='lil')

    def check(stage='capture'):
        cancellation_safe_point(cancellation_token, 'ge_point_buckling.'+stage)
        if (owner._generation != snap.generation or owner._finite_driver is not driver
                or driver._state is not initial_state):
            raise ValueError('accepted state changed during buckling capture/solution')

    def scatter(name, slots, value):
        slots = np.asarray(slots, dtype=int); value = np.asarray(value, dtype=float)
        if value.shape != (len(slots), len(slots)) or not np.isfinite(value).all():
            raise _Failure('finite compatible conservative local block required')
        rows, columns, data = terms[name]
        rows.extend(np.repeat(slots, len(slots))); columns.extend(np.tile(slots, len(slots)))
        data.extend(value.ravel())

    def scatter_force(slots, force):
        for slot, value in zip(slots, force, strict=True):
            forces[int(slot)].append(float(value))

    from math import fsum
    for (_eid, element, slots, _), origin in zip(owner._shell_parts, pickle.loads(snap.shell_origins), strict=True):
        check('shell')
        anchors = None if snap.shell_anchors is None else snap.shell_anchors[slots[::6]//6]
        force, h, km, g, _ = conservative_components(owner._shell_model, element, snap.q[slots], origin, 3,
            rotation_anchors=anchors, prepared_correction=driver._q4_corrections.get(_eid))
        scatter('material', slots, km); scatter('shell', slots, g); scatter('total', slots, h)
        scatter_force(slots, force)
    for node, row in enumerate(snap.q[:owner._shell_count].reshape(-1, 6)):
        start = 6*node+3; p = _exp_terms(row[3:])[1]
        if np.linalg.svd(p, compute_uv=False)[-1] <= 1e-11:
            raise ValueError('singular accepted shell chart requires owner rebase')
        chart[start:start+3, start:start+3] = p
    beam_u = snap.q[owner._shell_count:owner._shell_count+driver._beam_nodal].reshape(-1, 6)[:, :3]
    positions, low = _position_pair(driver._reference_positions, beam_u)
    for index, ((element, slots, _), origin) in enumerate(zip(owner._beam_parts, pickle.loads(snap.beam_origins), strict=True)):
        check('beam')
        nodes = np.array([owner._beam_index[node] for node in element.node_ids])
        response = element.operator.evaluate(positions[nodes], low[nodes], snap.frames[nodes],
            snap.cells[index], snap.resultants[index], origin=origin, check=element.operator.guard)
        _elastic_beam(element.operator, response, origin)
        h = response.hessian+response.hessian_low
        g = np.zeros((42, 42)); g[:24, :24] = h[:24, :24]
        km = np.zeros((42, 42)); km[:24, 24:] = h[:24, 24:]
        km[24:, :24] = h[24:, :24]; km[24:, 24:] = h[24:, 24:]
        global_slots = slots+owner._shell_count
        scatter('material', global_slots, km); scatter('beam', global_slots, g)
        scatter('total', global_slots, h); scatter_force(global_slots, response.residual)
    for index, (joint, slots) in enumerate(zip(owner._connections, owner._joint_slots, strict=True)):
        check('point')
        shell_node = slots[0]//6; beam_node = (slots[6]-owner._shell_count)//6
        x, xl = _position_pair(owner._shell_xyz[shell_node], snap.q[slots[:3]])
        anchors = np.array((np.eye(3) if snap.shell_anchors is None else snap.shell_anchors[shell_node], snap.frames[beam_node]))
        theta = np.zeros((2, 3)); theta[0] = snap.q[slots[3:6]]
        trial = joint.evaluate_ports(np.array((x, positions[beam_node])), anchors, snap.multipliers[6*index:6*index+6],
            rotation_coordinates=theta, charted_ports=(True, False), position_low=np.array((xl, low[beam_node])))
        # evaluate_ports has additive shell rows but spatial beam rows. Complete
        # the beam's zero-Exp covector derivative, never average the matrix.
        h = trial.tangent.copy()
        h[9:12, 9:12] += .5*skew(trial.pose.residual[9:12])
        km = np.zeros((18, 18)); km[:12, 12:] = h[:12, 12:]
        km[12:, :12] = h[12:, :12]
        g = np.zeros((18, 18)); g[:12, :12] = h[:12, :12]
        extended = np.r_[slots, np.arange(n+6*index, n+6*index+6)]
        scatter('material', extended, km); scatter('joint', extended, g)
        scatter('total', extended, h); scatter_force(extended, trial.residual)
    for slot, value in enumerate(snap.applied_dead_load):
        forces[slot].append(-float(value))  # translation dead work has zero Hessian
    matrices = {name: _freeze(sparse.coo_matrix((data, (rows, columns)), shape=(size, size)))
                for name, (rows, columns, data) in terms.items()}
    geometric = _freeze(matrices['shell']+matrices['beam']+matrices['joint'])
    material, hessian = matrices['material'], matrices['total']
    norm = max(1., sparse.linalg.norm(hessian))
    decomposition = float(sparse.linalg.norm(material+geometric-hessian)/norm)
    symmetry = max(float(sparse.linalg.norm(m-m.T)/max(1., sparse.linalg.norm(m)))
                   for m in (material, geometric, hessian))
    if decomposition > 1e-11 or symmetry > 1e-11:
        raise _Failure('conservative split/reconstruction or symmetry witness failed')
    constraints = _freeze(material[n:, :n])
    free = tuple(map(int, owner._free))+tuple(range(n, size)); fixed = tuple(map(int, owner._fixed))
    residual = _owned(np.array([fsum(values) for values in forces]))
    pchart = _freeze(chart.tocsc())
    identity = _matrix_digest((material, geometric, hessian, constraints, pchart,
                               matrices['shell'], matrices['beam'], matrices['joint']))
    packet = PointBucklingPencil(material, geometric, constraints, hessian, matrices['shell'], matrices['beam'],
        matrices['joint'], residual, pchart, free, fixed, n, snap, identity, decomposition, symmetry)
    def guard(stage='guard', *, full=True):
        check(stage)
        if full:
            if _state_digest(driver) != initial_digest:
                raise ValueError('accepted state changed during buckling capture/solution')
            if _model_digest(owner) != initial_model_digest:
                raise ValueError('accepted model/support provenance changed during buckling capture/solution')
            for element, _, _ in owner._beam_parts:
                element.operator.guard()
            if _matrix_digest((packet.material, packet.geometric, packet.hessian, packet.constraints, packet.chart,
                               packet.shell_geometric, packet.beam_geometric, packet.multiplier_curvature)) != identity:
                raise ValueError('immutable accepted buckling pencil changed')
    guard(); return packet, guard


def _scaled_pencil(owner, packet):
    from ._stiffened_shell_ge_experimental import _reference_scales
    _, shell, beam = _reference_scales(owner._shell_xyz, owner._beam_nodes, owner._beam_parts,
        owner._shell_count, owner._beam_count, footprint_retained_roles=True)
    primal = np.r_[shell, beam]
    weighted = sparse.diags(primal)@packet.hessian[:packet.primal_count, :packet.primal_count]@sparse.diags(primal)
    work = float(np.max(np.abs(weighted.data), initial=0.))
    if not np.isfinite(work) or work <= 0:
        raise _Failure('representable positive coordinate work scale required')
    scale = np.r_[primal/np.sqrt(work), np.sqrt(work)/owner._constraint_scale][list(packet.free)]
    if not np.isfinite(scale).all() or np.any(scale <= 0):
        raise _Failure('buckling congruence scale is not representable')
    d = sparse.diags(scale)
    matrices = []
    for source in (packet.material, packet.geometric):
        original = _freeze(source[list(packet.free), :][:, list(packet.free)])
        scaled = _freeze(d@original@d)
        if (original.nnz != scaled.nnz or not np.array_equal(original.indices, scaled.indices)
                or not np.array_equal(original.indptr, scaled.indptr)):
            raise _Failure('buckling congruence lost a matrix entry')
        matrices.append(scaled)
    return matrices[0], matrices[1], scale


def solve(owner, request, *, cancellation_token=None):
    if type(request) is not GEPointBucklingRequest:
        raise ValueError('typed GE point-buckling request required')
    if cancellation_token is not None and not isinstance(cancellation_token, CancellationToken):
        raise ValueError('CancellationToken required')
    _admit(owner, request.expected_generation)
    packet = None; handle = None; raw = ()
    checkpoint = sha256(owner._finite_driver.checkpoint()).hexdigest()
    def finish(status, **kwargs):
        return GEPointBucklingResult(status, owner._identity, owner._generation, checkpoint,
            pencil_identity='' if packet is None else packet.identity,
            decomposition_error=0. if packet is None else packet.decomposition_error,
            symmetry_error=0. if packet is None else packet.symmetry_error,
            inverse_eigenvalues=raw, factorization_count=0 if handle is None else handle.factorization_count,
            solve_count=0 if handle is None else handle.solve_count, **kwargs)
    try:
        packet, guard = capture(owner, request.expected_generation, cancellation_token=cancellation_token)
        if request.count >= len(packet.free)-1:
            raise ValueError('buckling count must leave sparse Arnoldi room')
        a, g, scale = _scaled_pencil(owner, packet)
        guard('before_factorization')
        handle = factorize_cached((a+request.shift*g).tocsc(), MatrixClass.GENERAL)
        if handle.status != 'ok':
            raise _Failure('buckling shift factorization failed: '+str(handle.failure_reason))
        def action(vector):
            guard('iteration', full=False)
            try:
                answer = np.asarray(handle.solve(-g@vector), dtype=float)
            except RuntimeError as exc:
                if str(exc) == 'Sparse solve produced NaN/Inf values' or str(exc).startswith('Cannot solve with failed factorization:'):
                    raise _Failure(str(exc)) from exc
                raise
            if not np.isfinite(answer).all():
                raise _Failure('nonfinite buckling inverse action')
            return answer
        values, vectors = eigs(LinearOperator(a.shape, matvec=action, dtype=float), k=request.count,
            which='LM', tol=1e-10, maxiter=request.max_iterations, v0=np.linspace(1., 2., a.shape[0]))
        raw = tuple(map(complex, values)); pairs = []
        for inverse, vector in zip(values, vectors.T, strict=True):
            guard('pair', full=False)
            if (not np.isfinite(inverse) or inverse.real == 0 or abs(inverse.imag) > TOLERANCE*abs(inverse.real)
                    or np.max(abs(vector.imag)) > TOLERANCE*max(np.max(abs(vector.real)), np.finfo(float).tiny)):
                raise _Failure('singular/infinite/complex or unresolved finite buckling pair')
            multiplier = request.shift+1./float(inverse.real)
            if not np.isfinite(multiplier):
                raise _Failure('nonfinite prestress multiplier')
            if not request.bounds[0] < multiplier <= request.bounds[1]:
                continue
            full = np.zeros(packet.material.shape[0]); full[list(packet.free)] = scale*vector.real
            retained = owner._shell_count+6*len(owner._beam_ids)
            kinematic = np.r_[np.arange(retained), *[np.arange(retained+24*i, retained+24*i+6)
                for i in range(len(owner._beam_parts))]]
            amplitude = float(np.max(abs(full[kinematic]/owner._coordinate_scale[kinematic])))
            if not np.isfinite(amplitude) or amplitude <= 0:
                raise _Failure('nonphysical algebraic-only buckling vector')
            full /= amplitude
            if not np.isfinite(full).all():
                raise _Failure('mixed mode normalization is not representable')
            if full[kinematic[np.argmax(abs(full[kinematic]/owner._coordinate_scale[kinematic]))]] < 0:
                full = -full
            equation = (packet.material+multiplier*packet.geometric)@full
            denominator = (abs(packet.material)+abs(multiplier)*abs(packet.geometric))@abs(full)
            free = np.array(packet.free)
            residual = _modal_scaled_residual(equation[free], denominator[free], scale)
            constraint = packet.constraints@full[:packet.primal_count]
            cscale = abs(packet.constraints)@abs(full[:packet.primal_count])
            gap = _modal_scaled_residual(constraint, cscale, scale[len(owner._free):])
            if residual > TOLERANCE or gap > TOLERANCE or not np.isfinite(residual+gap):
                raise _Failure('original mixed buckling equation/constraint residual witness failed')
            coordinate = np.zeros(packet.primal_count); coordinate[list(packet.fixed)] = equation[list(packet.fixed)]
            # Actual accepted shell chart converts coordinate reaction covectors
            # to spatial support wrenches. Beam Exp charts are centred at zero.
            physical = coordinate.copy()
            for node in range(len(owner._shell_ids)):
                s = slice(6*node+3, 6*node+6)
                physical[s] = np.linalg.solve(packet.chart[s, s].toarray().T, coordinate[s])
            pairs.append((multiplier, _owned(full), _owned(coordinate), _owned(physical), residual, gap))
        pairs.sort(key=lambda pair: pair[0])
        guard('finish')
        if sha256(owner._finite_driver.checkpoint()).hexdigest() != checkpoint:
            raise ValueError('buckling changed accepted checkpoint bytes')
        n = packet.primal_count; beam_start = owner._shell_count
        retained = beam_start+6*len(owner._beam_ids)
        return finish('completed' if pairs else 'no_factors_in_requested_window',
            prestress_multipliers=tuple(p[0] for p in pairs), full_coordinates=tuple(_owned(p[1][:n]) for p in pairs),
            shell_coordinate_modes=tuple(_owned(p[1][:beam_start].reshape(-1, 6)) for p in pairs),
            shell_spatial_modes=tuple(_owned((packet.chart[:beam_start, :beam_start]@p[1][:beam_start]).reshape(-1, 6)) for p in pairs),
            beam_modes=tuple(_owned(p[1][beam_start:n]) for p in pairs),
            cell_rotation_modes=tuple(_owned(np.array([p[1][retained+24*i:retained+24*i+6] for i in range(len(owner._beam_parts))])) for p in pairs),
            resultant_modes=tuple(_owned(np.array([p[1][retained+24*i+6:retained+24*i+24] for i in range(len(owner._beam_parts))])) for p in pairs),
            multiplier_modes=tuple(_owned(p[1][n:]) for p in pairs),
            coordinate_support_reactions=tuple(p[2] for p in pairs), physical_support_wrenches=tuple(p[3] for p in pairs),
            support_provenance=tuple((f.domain, f.node, f.component) for f in owner._definition.fixed),
            equation_residuals=tuple(p[4] for p in pairs), constraint_residuals=tuple(p[5] for p in pairs))
    except SolveCancelled as exc:
        return finish('cancelled', failure_reason=str(exc))
    except (ArpackError, _Failure, np.linalg.LinAlgError) as exc:
        if packet is not None:
            guard('failure')
        return finish('failed', failure_reason=str(exc))
    finally:
        handle = None
