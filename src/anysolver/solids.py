"""Opt-in linear-static solid blocks; native FEModel numbering is untouched.

Use SolidModel(native_model=...) for mixed models or SolidModel() for all-solid
models. It is deliberately not a FEModel subclass: unsupported native workflows
cannot silently solve only the shell part. Coupling is research-only until its
separate qualification gate is accepted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import sparse

from .control import cancellation_safe_point
from .linalg import FactorizationCache, MatrixClass, factorize_cached
from .solid_residuals import ResidualScales, evaluate_residuals


class SolidModelError(ValueError):
    """Invalid solid model, constraint or numerical result."""


class SolidAnalysisNotSupported(NotImplementedError):
    """The requested workflow has not been implemented/qualified for solids."""


def _array(value: Any, shape: tuple[int, ...], label: str) -> np.ndarray:
    result = np.array(value, dtype=float, copy=True)
    if result.shape != shape or not np.isfinite(result).all():
        raise SolidModelError(f"{label} must be finite with shape {shape}")
    return np.frombuffer(result.tobytes(),dtype=result.dtype).reshape(result.shape)


def _matrix_hash(matrix: sparse.spmatrix) -> str:
    matrix = sparse.csr_matrix(matrix, copy=True)
    matrix.sum_duplicates()
    matrix.sort_indices()
    digest = hashlib.sha256(str(matrix.shape).encode())
    for array in (matrix.indptr, matrix.indices, matrix.data):
        digest.update(array.tobytes())
    return digest.hexdigest()


@dataclass
class SolidRegion:
    name: str
    prepared: Any
    _prescribed: dict[int, float] = field(default_factory=dict, repr=False)
    _loads: dict[str, np.ndarray] = field(default_factory=dict, repr=False)

    @property
    def prescribed(self) -> Mapping[int, float]:
        return MappingProxyType(self._prescribed)

    def prescribe_dofs(self, dofs: Sequence[int], values: Any = 0.0) -> None:
        raw = np.asarray(dofs)
        if raw.ndim != 1 or raw.dtype.kind not in 'iu':
            raise SolidModelError('prescribed DOFs must be an integer vector')
        if np.any(raw < 0) or np.any(raw >= self.prepared.ndof) or len(set(raw.tolist())) != len(raw):
            raise SolidModelError('prescribed DOFs are duplicated or out of range')
        values = np.broadcast_to(np.asarray(values, float), raw.shape)
        if not np.isfinite(values).all():
            raise SolidModelError('prescribed values must be finite')
        proposed = dict(self._prescribed)
        for dof, value in zip(raw, values):
            if int(dof) in proposed and proposed[int(dof)] != float(value):
                raise SolidModelError(f'conflicting prescribed solid DOF {dof}')
            proposed[int(dof)] = float(value)
        self._prescribed = proposed

    def prescribe(self, group: str, values: Any = 0.0,
                  components: Sequence[int] = (0, 1, 2)) -> None:
        dofs = self.prepared.boundary_dofs(group, components=components)
        value = np.asarray(values, float)
        if value.shape == (3,):
            value = value[np.asarray(self.prepared.coefficient_components)[dofs]]
        self.prescribe_dofs(dofs, value)

    def set_load(self, case: str, vector: Any) -> None:
        if not isinstance(case, str) or not case:
            raise SolidModelError('load case needs a nonempty string name')
        self._loads[case] = _array(vector, (self.prepared.ndof,), 'solid load')

    def load(self, case: str) -> np.ndarray:
        return self._loads.get(case, np.zeros(self.prepared.ndof))


@dataclass(frozen=True)
class SolidLayout:
    native_dofs: int
    regions: Mapping[str, slice]
    primary_dofs: int
    multiplier_dofs: int


@dataclass(frozen=True)
class SolidStaticResult:
    coefficients: np.ndarray
    multipliers: np.ndarray
    reactions: np.ndarray
    interface_forces: np.ndarray
    layout: SolidLayout
    cases: tuple[str, ...]
    diagnostics: Mapping[str, Any]

    @property
    def native_displacements(self) -> np.ndarray:
        return self.coefficients[:self.layout.native_dofs]

    def region_coefficients(self, name: str) -> np.ndarray:
        return self.coefficients[self.layout.regions[name]]


class SolidModel:
    """Explicit opt-in model for supported linear statics.

    `research_coupling=True` permits evaluating an unqualified connector. It
    never upgrades the result's qualification status. Direct solid-solid
    connections, native element replacement and one-way submodels are absent.
    """
    _solid_model_protocol = True

    def __init__(self, native_model: Any = None, *, research_coupling: bool = False,
                 residual_scales: Mapping[str, ResidualScales] | None = None):
        self.native_model = native_model
        self.research_coupling = bool(research_coupling)
        self._regions: dict[str, SolidRegion] = {}
        self._interfaces: list[tuple[str, Any]] = []
        self._factorizations = FactorizationCache(name='solid_static', max_entries=2)
        if residual_scales is not None and (not isinstance(residual_scales, Mapping) or
            any(not isinstance(k, str) or not isinstance(v, ResidualScales) for k, v in residual_scales.items())):
            raise SolidModelError('residual_scales must map case names to prospectively registered ResidualScales')
        self._residual_scales = None if residual_scales is None else MappingProxyType(dict(residual_scales))

    @property
    def mesh(self):
        raise SolidAnalysisNotSupported('SolidModel supports linear statics only; use solve_static or solve_linear')

    def apply_boundary_conditions(self):
        raise SolidAnalysisNotSupported('SolidModel must enter the solid linear-static dispatcher')

    @property
    def regions(self) -> Mapping[str, SolidRegion]:
        return MappingProxyType(self._regions)

    def add_region(self, name: str, mesh: Any = None, material: Any = None,
                   *, prepared: Any = None, order: int = 2) -> SolidRegion:
        if not isinstance(name, str) or not name or name in self._regions:
            raise SolidModelError('region name must be nonempty and unique')
        if prepared is not None and (mesh is not None or material is not None):
            raise SolidModelError('provide prepared region OR mesh/material')
        if prepared is None:
            from anysolid import prepare
            prepared = prepare(mesh, material, order=order)
        if not isinstance(prepared.ndof, (int, np.integer)) or prepared.ndof <= 0:
            raise SolidModelError('backend must provide positive coefficient count')
        region = SolidRegion(name, prepared)
        self._regions[name] = region
        return region

    def add_interface(self, region: str, operator: Any, *, diagnostic_strong_tying: bool = False) -> None:
        if region not in self._regions or self.native_model is None:
            raise SolidModelError('interface needs an existing region and native model')
        if not self.research_coupling:
            raise SolidAnalysisNotSupported('weak shell-solid coupling is NO_GO pending numerical qualification; opt into research_coupling explicitly')
        if type(diagnostic_strong_tying) is not bool:
            raise SolidModelError('diagnostic_strong_tying must be an explicit boolean')
        formulation = getattr(operator, 'formulation', None)
        if formulation == 'strong_point_diagnostic_v1':
            if not diagnostic_strong_tying or not getattr(operator, 'metadata', {}).get('diagnostic_only', False):
                raise SolidModelError('strong tying requires explicit diagnostic_strong_tying and a diagnostic operator')
        elif formulation != 'weak_section_moments_v1' or diagnostic_strong_tying:
            raise SolidModelError('only explicit weak research coupling or opted-in strong diagnostic tying is supported')
        if self._interfaces and any(op.formulation != formulation for _,op in self._interfaces):
            raise SolidModelError('do not mix weak integrated and strong point constraint units in one model')
        operator.validate(self.native_model, self._regions[region].prepared)
        self._interfaces.append((region, operator))

    def solve_static(self, cases: Sequence[str] = ('default',), *,
                     native_load_cases: Mapping[str, Any] | None = None,
                     cancellation_token: Any = None,
                     factorization_cache: FactorizationCache | None = None,
                     residual_scales: Mapping[str, ResidualScales] | None = None) -> SolidStaticResult:
        from .assembly import build_constraint_transformation
        from .matrix_assembly import assemble_system

        cancellation_safe_point(cancellation_token, 'solid_static.start')
        cases = tuple(cases)
        if not cases or any(not isinstance(c, str) or not c for c in cases):
            raise SolidModelError('provide at least one named load case')
        if not self._regions:
            raise SolidModelError('SolidModel needs at least one solid region')
        registered = self._residual_scales if residual_scales is None else residual_scales
        references = None
        if registered is not None:
            if not isinstance(registered, Mapping) or any(case not in registered or
                not isinstance(registered[case], ResidualScales) for case in cases):
                raise SolidModelError('provide registered ResidualScales for every requested case before solving')
            references = tuple(registered[case] for case in cases)
        native_load_cases = dict(native_load_cases or {})
        native = self.native_model
        if native is None:
            n_native = 0
            Ksh = sparse.csr_matrix((0, 0))
            Tsh = sparse.csr_matrix((0, 0))
            ush = np.empty(0)
            native_rhs = np.zeros((0, len(cases)))
        else:
            native.apply_boundary_conditions()
            native_vectors = []
            Ksh = Tsh = ush = None
            for case in cases:
                Kcase, fcase, _ = assemble_system(native, native_load_cases.get(case))
                _, _, transform, offset, _, _ = build_constraint_transformation(Kcase, fcase, native)
                if Ksh is not None and (_matrix_hash(Kcase) != _matrix_hash(Ksh) or
                    _matrix_hash(transform) != _matrix_hash(Tsh) or not np.array_equal(offset, ush)):
                    raise SolidModelError('stiffness/supports changed between load cases')
                Ksh, Tsh, ush = Kcase, transform, offset
                native_vectors.append(fcase)
            n_native = Ksh.shape[0]
            native_rhs = np.column_stack(native_vectors)

        blocks = [Ksh]
        transforms = [Tsh]
        offsets = [ush]
        rhs = [native_rhs]
        slices: dict[str, slice] = {}
        cursor = n_native
        for name, region in self._regions.items():
            prepared = region.prepared
            stiffness = sparse.csr_matrix(prepared.assemble_linear(), copy=True)
            if stiffness.shape != (prepared.ndof, prepared.ndof) or not np.isfinite(stiffness.data).all():
                raise SolidModelError(f'invalid backend stiffness for {name}')
            norm = sparse.linalg.norm(stiffness)
            if sparse.linalg.norm(stiffness - stiffness.T) > 1e-10 * max(norm, np.finfo(float).tiny):
                raise SolidModelError(f'backend stiffness for {name} is not symmetric')
            blocks.append(stiffness)
            slices[name] = slice(cursor, cursor + prepared.ndof)
            cursor += int(prepared.ndof)
            fixed = np.array(sorted(region.prescribed), dtype=int)
            if not any(name == key for key, _ in self._interfaces) and hasattr(prepared, 'rigid_modes'):
                rigid = prepared.rigid_modes()
                support_action = rigid[fixed]
                norms = np.linalg.norm(support_action, axis=0)
                if (len(fixed) < rigid.shape[1] or np.any(norms == 0) or
                    np.linalg.matrix_rank(support_action / np.maximum(norms, np.finfo(float).tiny)) < rigid.shape[1]):
                    raise SolidModelError(f'region {name} has unsupported physical rigid modes; free-free solid statics is not enabled')
            free = np.setdiff1d(np.arange(prepared.ndof), fixed)
            transform = sparse.csr_matrix((np.ones(len(free)), (free, np.arange(len(free)))),
                                          shape=(prepared.ndof, len(free)))
            offset = np.zeros(prepared.ndof)
            offset[fixed] = [region.prescribed[int(i)] for i in fixed]
            transforms.append(transform)
            offsets.append(offset)
            rhs.append(np.column_stack([region.load(c) for c in cases]))
        K = sparse.block_diag(blocks, format='csr')
        P = sparse.block_diag(transforms, format='csr')
        u0 = np.concatenate(offsets)
        F = np.vstack(rhs)
        Kred = (P.T @ K @ P).tocsr()
        Fred = np.asarray(P.T @ (F - (K @ u0)[:, None]))

        constraints = []
        affine = []
        for name, operator in self._interfaces:
            operator.validate(native, self._regions[name].prepared)
            row = [sparse.csr_matrix(operator.C_shell)]
            for key, region in self._regions.items():
                row.append(-sparse.csr_matrix(operator.C_solid) if key == name else
                           sparse.csr_matrix((operator.C_shell.shape[0], region.prepared.ndof)))
            constraints.append(sparse.hstack(row, format='csr'))
            affine.append(np.asarray(operator.affine, float))
        C = sparse.vstack(constraints, format='csr') if constraints else sparse.csr_matrix((0, cursor))
        g = np.concatenate(affine) if affine else np.empty(0)
        Cred = (C @ P).tocsr()
        gred = g - C @ u0
        constraint_interfaces = np.concatenate([np.full(op.C_shell.shape[0], i, dtype=int)
            for i, (_, op) in enumerate(self._interfaces)]) if self._interfaces else np.empty(0, dtype=int)
        rotation_dofs = np.array([int(dof) for node in (() if native is None else native.mesh.nodes.values())
                                 for dof in native.mesh.dof_manager.get_node_dofs(node.id)[3:]], dtype=int)
        if references is not None:
            # Validate the new policy's applicability BEFORE factorization.
            # Disjoint-support columns prevent hidden differential MPC modes.
            policy_P = P.copy()
            policy_P.sum_duplicates()
            policy_P.eliminate_zeros()
            if np.any(np.diff(policy_P.indptr) > 1):
                raise SolidAnalysisNotSupported('registered physical residual policy requires disjoint-support reduction; general multi-master MPC scaling is unqualified')
            for reference in references:
                if reference.interface_displacements and len(reference.interface_displacements) != len(self._interfaces):
                    raise SolidModelError('register exactly one displacement scale per physical interface')
        if C.shape[0]:
            row_norm = np.sqrt(np.asarray(Cred.multiply(Cred).sum(axis=1)).ravel())
            if np.any(row_norm <= np.finfo(float).tiny):
                raise SolidModelError('coupling contains a redundant or fully prescribed equation')
            # Row congruence changes multiplier units only, not physical constraints.
            D = sparse.diags(1.0 / row_norm)
            Cs = D @ Cred
            system = sparse.bmat([[Kred, Cs.T], [Cs, None]], format='csr')
            load = np.vstack((Fred, np.repeat((D @ gred)[:, None], len(cases), axis=1)))
            classification = MatrixClass.SYMMETRIC_INDEFINITE
        else:
            D = sparse.csr_matrix((0, 0))
            system, load = Kred, Fred
            classification = MatrixClass.SPD
        cancellation_safe_point(cancellation_token, 'solid_static.before_factorization')
        if system.shape[0]:
            cache = self._factorizations if factorization_cache is None else factorization_cache
            handle = factorize_cached(system, classification, cache=cache,
                                      signature=_matrix_hash(system), options={'backend': 'scipy'})
            if handle.status != 'ok':
                raise SolidModelError(f'singular/unsupported solid system; check supports and interfaces: {handle.failure_reason}')
            solved = handle.solve_many(load)
            diagnostics = handle.diagnostics()
        else:
            solved = np.empty((0, len(cases)))
            diagnostics = {'factorization_count': 0, 'solve_count': 0}
        cancellation_safe_point(cancellation_token, 'solid_static.after_solve')
        for name, operator in self._interfaces:
            operator.validate(native, self._regions[name].prepared)
        reduced = solved[:P.shape[1]]
        multipliers = np.asarray(D @ solved[P.shape[1]:])
        primary = np.asarray(P @ reduced) + u0[:, None]
        interface_forces = np.asarray(C.T @ multipliers)
        reactions = np.asarray(K @ primary) + interface_forces - F
        free_residual = np.asarray(P.T @ reactions)
        scale = np.asarray(abs(P.T) @ (abs(K) @ abs(primary) + abs(interface_forces) + abs(F)))
        equilibrium = float(np.max(abs(free_residual) / np.maximum(scale, np.finfo(float).tiny), initial=0.0))
        cres = np.asarray(C @ primary) - g[:, None]
        cscale = np.asarray(abs(C) @ abs(primary)) + abs(g[:, None])
        constraint_error = float(np.max(abs(cres) / np.maximum(cscale, 1e-14), initial=0.0))
        legacy_equilibrium, legacy_constraint = equilibrium, constraint_error
        report = None
        if references is not None:
            report = evaluate_residuals(K, P, C, primary, multipliers, F, g,
                native_rotation_dofs=rotation_dofs, scales=references,
                constraint_interfaces=constraint_interfaces)
            equilibrium = report['normalized_equilibrium']
            constraint_error = report['normalized_constraint_error']
        if not np.isfinite(primary).all() or equilibrium > 1e-9 or constraint_error > 1e-9:
            failure = SolidModelError(f'solid solve postcheck failed: equilibrium={equilibrium:g}, constraints={constraint_error:g}')
            # Preserve legacy witness data and all registered physical checks.
            failure.diagnostics = {
                'normalized_equilibrium':equilibrium,'normalized_constraint_error':constraint_error,
                'absolute_free_residual_max':float(np.max(abs(free_residual),initial=0.0)),
                'absolute_constraint_residual_max':float(np.max(abs(cres),initial=0.0)),
                'applied_load_max':float(np.max(abs(F),initial=0.0)),
                'displacement_max':float(np.max(abs(primary),initial=0.0)),
                'acceptance':'FAILED_LEGACY_COMPONENTWISE_GATE' if report is None else 'FAILED_REGISTERED_PHYSICAL_V2',
                'legacy_componentwise_equilibrium':legacy_equilibrium,
                'legacy_componentwise_constraint_error':legacy_constraint}
            if report is not None:
                failure.diagnostics['registered_residual_report'] = report
            if cres.size:
                index = np.unravel_index(np.argmax(abs(cres)/np.maximum(cscale,1e-14)),cres.shape)
                row,case_index = (int(v) for v in index)
                witness = C.getrow(row)
                terms = witness.data*primary[witness.indices,case_index]
                failure.diagnostics['controlling_constraint'] = {
                    'row':row,'case':case_index,'raw_residual':float(cres[index]),
                    'raw_scale':float(cscale[index]),'denominator':float(max(cscale[index],1e-14)),
                    'native_term':float(terms[witness.indices<n_native].sum()),
                    'solid_term':float(terms[witness.indices>=n_native].sum()),
                    'affine':float(g[row]),'coefficient_terms':terms.tolist()}
            raise failure
        for array in (primary, multipliers, reactions, interface_forces):
            array.setflags(write=False)
        layout = SolidLayout(n_native, MappingProxyType(slices), cursor, C.shape[0])
        diagnostics.update(normalized_equilibrium=equilibrium, normalized_constraint_error=constraint_error,
                           legacy_componentwise_equilibrium=legacy_equilibrium,
                           legacy_componentwise_constraint_error=legacy_constraint,
                           residual_policy='legacy_componentwise_v1' if report is None else report['policy'],
                           qualification=('diagnostic_only_strong_tying' if any(
                               op.formulation == 'strong_point_diagnostic_v1' for _,op in self._interfaces)
                               else 'research_only' if constraints else 'development_verified_cases_only'),
                           interface_formulations=tuple(op.formulation for _,op in self._interfaces),
                           matrix_class=classification.value, primary_dofs=cursor, multiplier_dofs=C.shape[0])
        if report is not None:
            diagnostics['registered_residual_report'] = report
        return SolidStaticResult(primary, multipliers, reactions, interface_forces, layout, cases,
                                 MappingProxyType(diagnostics))


def solve_solid_linear(model: SolidModel, load_case: Any = None, **options):
    """Compatibility return shape for ANYsolver.solve_linear's solid dispatch."""
    if any(options.get(k) not in (None, False, 'auto', 'transformation', 'direct') for k in
           ('session', 'allow_unbalanced_free_free', 'solver_type', 'constraint_mode')):
        raise SolidAnalysisNotSupported('solid statics currently supports direct constrained solves only')
    name = load_case if isinstance(load_case, str) else getattr(load_case, 'name', 'default')
    result = model.solve_static((name,), native_load_cases={} if isinstance(load_case, str) or load_case is None else {name: load_case},
                                cancellation_token=options.get('cancellation_token'))
    return result.coefficients[:, 0], {'solid_result': result, 'convergence_info': {'status': 'converged'}, **result.diagnostics}


def solve_solid_linear_many(model: SolidModel, load_cases: Sequence[Any], **options):
    if options.get('session') is not None or options.get('allow_unbalanced_free_free') or options.get('constraint_mode', 'auto') not in ('auto', 'transformation'):
        raise SolidAnalysisNotSupported('solid statics currently supports direct constrained solves only')
    names = tuple(c if isinstance(c, str) else getattr(c, 'name', 'default') for c in load_cases)
    native = {}
    semantics = {}
    for name, case in zip(names, load_cases):
        no_native = case is None or isinstance(case, str)
        if name in semantics:
            previous = semantics[name]
            previous_no_native = previous is None or isinstance(previous, str)
            if not (previous is case or (no_native and previous_no_native)):
                raise SolidModelError('distinct native load cases must have distinct names, including implicit cases')
        semantics[name] = case
        if case is not None and not isinstance(case, str):
            if name in native and native[name] is not case:
                raise SolidModelError('distinct native load cases must have distinct names')
            native[name] = case
    result = model.solve_static(names, native_load_cases=native,
                                cancellation_token=options.get('cancellation_token'),
                                factorization_cache=options.get('factorization_cache'))
    return result.coefficients, {'solid_result': result, 'convergence_info': {'status': 'converged'}, **result.diagnostics}
