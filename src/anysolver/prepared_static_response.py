"""Owned source-response superposition with actual full-state certification."""
from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Mapping, Optional
import numpy as np
from .analysis_session import _immutable_array
from .prepared_static import PreparedStaticEvaluator, _certified_backward_error, _block_norm_data
from .prepared_static_loads import (PreparedStaticError, PreparedStaticCapabilityError,
    ingest_static_case, evaluate_load_vector, load_packet_storage_bytes,
    require_native_source_authority)
from .prepared_static_recovery import (owned_recovery_scope, constraint_force_diagnostics,
    _recover_owned_local, _derived_measure, _ordered_derived, _array_value, _plain_constant,
    _constant_equal, _AFFINITY_RELATIVE_TOLERANCE)
from .prepared_static_measures import PRINCIPAL_COMPONENTS
from . import prepared_static as _prepared_static_module
from .prepared_static_vectorized import (VectorEnvelope, VectorRecovery, build_vector_recovery,
    recover_vector_block, make_metadata_copier, CompiledPressure, c7_ratio)
from .prepared_static_recovery import _OWNED_RECOVERY_SCOPE, ReactionPlan
import copy
from .static_batch import StaticCase
from .control import cancellation_safe_point
from .threading_policy import solver_thread_scope

def _library_storage_bytes(value, seen=None):
    """Count owned containers and array base chains, deduplicating shared buffers."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if type(value) is np.ndarray:
        return size + (0 if value.base is None else _library_storage_bytes(value.base, seen))
    if type(value) is dict:
        return size + sum(_library_storage_bytes(k,seen) + _library_storage_bytes(v,seen)
                          for k,v in value.items())
    if type(value) in (tuple,list):
        return size + sum(_library_storage_bytes(item,seen) for item in value)
    return size

# M16 certified response route (opt-in). See docs/PREPARED_STATIC_M16_CERTIFIED_ROUTE.md.
_STRESS_EXECUTIONS = ('canonical', 'certified_library', 'certified_vectorized')
_SOURCE_AGREEMENT_RELATIVE = 1e-12
# A native authority recheck costs tens of milliseconds; checking every element made
# barge library preparation dominated by safe points (M16 barge timeout). Check the
# token and authority on the first element and then once per stride, outside scopes.
_LIBRARY_SAFE_POINT_STRIDE = 128
_DERIVED_NAMES = frozenset(('von_mises', 'equivalent_stress', 'hill_utilization') + tuple(PRINCIPAL_COMPONENTS))


def _library_schema(element_id, zero):
    """Classify one canonical zero record into affine, constant and derived fields."""
    linear, constants, derived = [], [], []
    for name in zero:
        value = zero[name]
        content = _array_value(value)
        if name in _DERIVED_NAMES:
            if content is None:
                raise PreparedStaticCapabilityError('derived recovery measure is not a float field',
                    diagnostics={'element_id': int(element_id), 'component': str(name)})
            derived.append(name)
            continue
        if content is not None:
            linear.append((name, tuple(int(n) for n in content.shape), type(value) is np.ndarray))
            continue
        try:
            constants.append((name, _plain_constant(value)))
        except ValueError as error:
            raise PreparedStaticCapabilityError('recovery component cannot be represented in a response library',
                diagnostics={'element_id': int(element_id), 'component': str(name)}) from error
    return tuple(zero), tuple(linear), tuple(constants), _ordered_derived(dict.fromkeys(derived))


def _library_vector(record, linear):
    return np.concatenate([np.asarray(record[name], dtype=float).reshape(-1) for name, _shape, _array in linear])         if linear else np.zeros(0)


def _library_fields(values, linear):
    fields, offset = {}, 0
    for name, shape, is_array in linear:
        size = int(np.prod(shape)) if shape else 1
        part = values[offset:offset + size]
        offset += size
        fields[name] = part.reshape(shape).copy() if is_array else float(part[0])
    return fields


def _assemble_library_record(order, linear_values, constants, derived):
    working = dict(linear_values)
    for name, value in constants:
        working[name] = copy.deepcopy(value)
    for name in derived:
        working[name] = _derived_measure(name, working)
    return {name: working[name] for name in order}


def _library_refusal(element_id, message, **extra):
    return PreparedStaticCapabilityError('certified response library: ' + message,
        diagnostics={'stage': 'response element library', 'element_id': int(element_id), **extra})


def _relative_residual(residual, terms):
    scale = max([float(np.linalg.norm(term)) for term in terms] + [1.0])
    return float(np.linalg.norm(residual)) / scale


def _verify_library_element(element_id, recipe, local_size, zero, schema):
    """Random additivity, homogeneity, rigid-offset, constant and derived checks.

    Authority comes from the admitted owned recipe. These probes verify that
    affine superposition and derived recomputation reproduce canonical recovery,
    using the same normwise residual convention as compile_affine_recovery.
    """
    order, linear, constants, derived = schema
    rng = np.random.default_rng(int(element_id) + 16)
    first = rng.uniform(-1.0, 1.0, local_size)
    second = rng.uniform(-1.0, 1.0, local_size)
    rigid = np.zeros(local_size)
    rigid[0::6] = 0.125
    worst = 0.0
    for amplitude in (1e-3, 1.0):
        a, b = first * amplitude, second * amplitude
        records = {key: _recover_owned_local(recipe, vector) for key, vector in
                   (('a', a), ('b', b), ('ab', a + b), ('2a', 2.0 * a), ('t', rigid), ('at', a + rigid))}
        for key, record in records.items():
            if tuple(record) != order:
                raise _library_refusal(element_id, 'recovery component set changed under probes')
            for name, value in constants:
                if not _constant_equal(value, record[name]):
                    raise _library_refusal(element_id, 'recovery constant changed under probes', component=str(name))
            for name, shape, _is_array in linear:
                content = _array_value(record[name])
                if content is None or tuple(content.shape) != shape:
                    raise _library_refusal(element_id, 'recovery field changed type or shape', component=str(name))
        zero_fields = _library_fields(_library_vector(zero, linear), linear)
        fields = {key: _library_fields(_library_vector(record, linear), linear) for key, record in records.items()}
        for name, _shape, _is_array in linear:
            z = np.asarray(zero_fields[name], dtype=float)
            f = {key: np.asarray(values[name], dtype=float) for key, values in fields.items()}
            for label, residual, terms in (
                    ('additivity', f['ab'] - f['a'] - f['b'] + z, (f['ab'], f['a'], f['b'], z)),
                    ('homogeneity', f['2a'] - 2.0 * f['a'] + z, (f['2a'], f['a'], z)),
                    ('rigid_offset', f['at'] - f['a'] - f['t'] + z, (f['at'], f['a'], f['t'], z))):
                relative = _relative_residual(residual, terms)
                if not np.isfinite(relative) or relative > _AFFINITY_RELATIVE_TOLERANCE:
                    raise _library_refusal(element_id, 'recovery field is not affine in displacement',
                                           component=str(name), check=label, relative_residual=relative)
                worst = max(worst, relative)
        for key, record in records.items():
            try:
                built = _assemble_library_record(order, fields[key], constants, derived)
            except KeyError as error:
                raise _library_refusal(element_id, 'derived measure has no reviewed recomputation',
                                       component=str(error)) from error
            for name in derived:
                made, native = np.asarray(built[name], dtype=float), np.asarray(record[name], dtype=float)
                if made.shape != native.shape:
                    raise _library_refusal(element_id, 'derived measure changed shape', component=str(name))
                relative = _relative_residual(made - native, (made, native))
                if not np.isfinite(relative) or relative > _AFFINITY_RELATIVE_TOLERANCE:
                    raise _library_refusal(element_id, 'derived measure does not reproduce canonical recovery',
                                           component=str(name), relative_residual=relative)
                worst = max(worst, relative)
    return worst


@dataclass(frozen=True)
class PatternCase:
    case_id: str
    coefficients: Mapping[str, float]
    time: Optional[float] = None
    canonical_load_case: object = field(default=None, kw_only=True)

@dataclass(frozen=True)
class _PatternPacket:
    indices: np.ndarray
    coefficients: np.ndarray
    canonical: object

class PreparedStaticResponseEvaluator(PreparedStaticEvaluator):
    """Retains one private factor and immutable baseline/homogeneous responses."""
    _fixed_response_packets = True

    def __init__(self, model, patterns, *, baseline_load_case=None, stress_execution='canonical',
                 selected_reaction_diagnostics='full', **kwargs):
        if type(self) is not PreparedStaticResponseEvaluator:
            raise PreparedStaticCapabilityError("source response evaluator subclasses are not admitted")
        if type(stress_execution) is not str or stress_execution not in _STRESS_EXECUTIONS:
            raise PreparedStaticCapabilityError("stress_execution must be 'canonical', 'certified_library' or 'certified_vectorized'")
        if type(selected_reaction_diagnostics) is not str or selected_reaction_diagnostics not in ('full', 'lean'):
            raise PreparedStaticCapabilityError("selected_reaction_diagnostics must be 'full' or 'lean'")
        if selected_reaction_diagnostics == 'lean' and stress_execution != 'certified_vectorized':
            raise PreparedStaticCapabilityError("lean selected reactions require stress_execution='certified_vectorized'")
        self._selected_reaction_diagnostics = selected_reaction_diagnostics
        self._stress_execution = stress_execution
        self._vector = None
        self._vector_bytes = 0
        self._metadata_copies = None
        self._compiled_pressure = None
        self._reaction_plan = None
        self._compiled_pressure_note = 'not prepared'
        self._compiled_pressure_worst_c7 = 0.0
        self._element_library = {}
        self._element_library_numeric_bytes = 0
        self._element_library_verification = 0.0
        self._source_discrepancy_max = 0.0
        self._library_bytes = self._library_numeric_bytes = 0
        self._canonical_matches = {}
        self._response_counts = dict(reconstructed_cases=0, canonical_envelope_cases=0,
                                     certification_fallback_cases=0, direct_cases=0,
                                     preparation_solves=0, reconstructed_element_records=0, canonical_stress_cases=0,
                                     source_agreement_fallback_cases=0, library_stress_cases=0,
                                     element_library_probes=0, vectorized_stress_cases=0,
                                     compiled_load_cases=0, native_load_cases=0,
                                     compiled_disagreement_cases=0, pattern_canonical_solves=0,
                                     native_load_scope_blocks=0, compiled_load_scope_blocks=0)
        super().__init__(model, **kwargs)
        try:
            if type(patterns) is not dict or any(type(k) is not str for k in patterns):
                raise PreparedStaticCapabilityError('patterns must be a plain dict with string names')
            snapshot = self._require_open()
            token = kwargs.get('cancellation_token')
            self._response_safe_point(token, 'prepared_response.before_library')
            # Check the complete retained library plus temporary full/reduced columns
            # before allocating its dense numeric tables. Factor/snapshot already exist.
            m = 1 + len(patterns)
            expected = 8*m*(snapshot.total_dofs*3 + self._operator_matrix.shape[0]*3)
            packet_bytes = load_packet_storage_bytes(StaticCase('baseline', baseline_load_case)) + sum(
                load_packet_storage_bytes(StaticCase(name,value)) for name,value in patterns.items())
            metadata_estimate = (sys.getsizeof(patterns) + sys.getsizeof(()) + 8*len(patterns)
                + sum(sys.getsizeof(name) + sys.getsizeof(i) for i,name in enumerate(patterns)))
            self._check_library_memory(expected + packet_bytes + metadata_estimate)
            self._pattern_names = tuple(patterns)
            self._pattern_lookup = {name:i for i,name in enumerate(self._pattern_names)}
            packets = [ingest_static_case(StaticCase("baseline", baseline_load_case))[2]]
            packets.extend(ingest_static_case(StaticCase(name,value))[2] for name,value in patterns.items())
            with owned_recovery_scope(tuple(snapshot.load_maps.pressure_recipes.values())):
                forces = np.column_stack([evaluate_load_vector(snapshot.load_maps, p)[0] for p in packets])
            rhs = np.asarray(snapshot.transformation.T @ forces)
            rhs[:,0] -= np.asarray(snapshot.transformation.T @ (snapshot.stiffness @ snapshot.prescribed_offset))
            if self._operator_augmented:
                rhs = np.vstack((rhs, np.zeros((snapshot.rigid_modes.shape[1],m))))
            with solver_thread_scope(self._resource_config):
                solved = super()._solve_block(rhs, ())
            for j in range(m):
                operator = self._operator_matrix if self._operator_augmented else snapshot.reduced_stiffness
                error = self._backward_error(operator, solved[:,j], rhs[:,j])
                if not np.isfinite(error) or error > self._backward_error_limit:
                    raise PreparedStaticError('source response library equation failed certification',
                        diagnostics={'column':j, 'relative_backward_error':float(error)})
            self._response_counts['preparation_solves'] = m
            self._force_columns = _immutable_array(forces)
            self._solution_columns = _immutable_array(solved)
            if self._stress_execution == 'certified_library':
                self._build_element_library(snapshot, solved, token, expected + packet_bytes + metadata_estimate)
            if self._stress_execution == 'certified_vectorized' and (self._recovery.include_stresses or snapshot.envelope_plan is not None):
                union = self._library_elements(snapshot)
                # M22 (review F1, F4): build even without elements (node-only envelopes) and
                # check the maps' storage before allocating them.
                self._vector = build_vector_recovery(union, snapshot.envelope_plan,
                    self._recovery.selected_components() if self._recovery.include_stresses else None,
                    lambda stage: self._response_safe_point(token, stage),
                    memory_check=lambda extra: self._check_library_memory(expected + extra))
                self._vector_bytes = self._vector.nbytes()
                self._check_library_memory(expected + self._vector_bytes)
            if self._stress_execution == 'certified_vectorized':
                self._metadata_copies = make_metadata_copier(snapshot.constraint_info, snapshot.nullspace_info)
                self._reaction_plan = ReactionPlan(snapshot.reaction_maps)
                self._prepare_compiled_pressure(snapshot, packets, forces)
            self._library_numeric_bytes = (self._force_columns.nbytes + self._solution_columns.nbytes
                                           + self._element_library_numeric_bytes)
            # Canonical mode keeps the M8 accounting exactly; only the library route owns element columns.
            self._library_bytes = _library_storage_bytes((self._pattern_names,self._pattern_lookup,
                self._force_columns,self._solution_columns) + (
                (self._element_library,) if self._stress_execution == 'certified_library' else ())) + self._vector_bytes
            self._check_library_memory(self._library_bytes)
            self._response_safe_point(token, 'prepared_response.ready')
        except BaseException:
            self.close()
            raise

    def _library_elements(self, snapshot):
        union = {}
        if snapshot.envelope_plan is not None:
            union.update({e.element_id: (e.dof_mapping, e.recipe) for e in snapshot.envelope_plan.elements})
        if self._recovery.include_stresses and snapshot.recovery_compilation is not None:
            union.update({eid: (e.dof_mapping, e.local_recipe) for eid, e in snapshot.recovery_compilation.elements.items()})
        return union

    def _build_element_library(self, snapshot, solved, token, prepared_bytes):
        """Owned verified affine output columns for every recovered element."""
        union = self._library_elements(snapshot)
        if not union:
            return
        n = snapshot.reduced_stiffness.shape[0]
        full = np.asarray(snapshot.transformation @ solved[:n])
        full[:, 0] += snapshot.prescribed_offset
        m = full.shape[1]
        zeros, schemas, outputs = {}, {}, 0
        for index, (eid, (mapping, recipe)) in enumerate(union.items()):
            if index % _LIBRARY_SAFE_POINT_STRIDE == 0:
                self._response_safe_point(token, 'prepared_response.element_schema')
            with owned_recovery_scope((recipe,)):
                zeros[eid] = _recover_owned_local(recipe, np.zeros(mapping.size))
            schemas[eid] = _library_schema(eid, zeros[eid])
            outputs += int(_library_vector(zeros[eid], schemas[eid][1]).size)
        # Retained columns plus one transient column table; checked before allocation.
        self._check_library_memory(prepared_bytes + 2 * 8 * m * outputs + 512 * len(union))
        library, numeric, worst = {}, 0, 0.0
        for index, (eid, (mapping, recipe)) in enumerate(union.items()):
            if index % _LIBRARY_SAFE_POINT_STRIDE == 0:
                self._response_safe_point(token, 'prepared_response.element_library')
            order, linear, constants, derived = schemas[eid]
            with owned_recovery_scope((recipe,)):
                worst = max(worst, _verify_library_element(eid, recipe, int(mapping.size), zeros[eid], schemas[eid]))
                self._response_counts['element_library_probes'] += 12
                zero_vector = _library_vector(zeros[eid], linear)
                columns = np.empty((zero_vector.size, m))
                for j in range(m):
                    record = _recover_owned_local(recipe, full[mapping, j])
                    if tuple(record) != order or any(not _constant_equal(v, record[k]) for k, v in constants):
                        raise _library_refusal(eid, 'recovery schema changed for a library column', column=j)
                    columns[:, j] = _library_vector(record, linear)
                    if j:
                        columns[:, j] -= zero_vector
            if not np.all(np.isfinite(columns)):
                raise _library_refusal(eid, 'nonfinite response library column')
            columns = _immutable_array(columns)
            numeric += columns.nbytes
            library[int(eid)] = (order, linear, constants, derived, columns)
        self._element_library = library
        self._element_library_numeric_bytes = numeric
        self._element_library_verification = worst

    def _prepare_compiled_pressure(self, snapshot, packets, forces):
        """Option 1: compiled pressure loads, enabled only if every pattern column meets C7."""
        self._compiled_pressure = None
        compiled = CompiledPressure(snapshot.load_maps)
        if not compiled.columns:
            self._compiled_pressure_note = 'no compiled pressure bases'
            return
        worst, checked = 0.0, 0
        kinds = frozenset(kind for packet in packets for _eid, (kind, _value) in packet.pressure)
        with owned_recovery_scope(tuple(snapshot.load_maps.pressure_recipes.values())):
            for j, packet in enumerate(packets):
                if not packet.pressure:
                    continue
                made = compiled.evaluate(snapshot.load_maps, packet, kinds=kinds)
                if made is None:
                    self._compiled_pressure_note = f'pattern column {j} has pressure without a compiled basis'
                    return
                load, _info, values, other = made
                worst = max(worst, c7_ratio(load, forces[:, j], compiled.term_scale(values, other)))
                checked += 1
        self._compiled_pressure_worst_c7 = worst
        if not checked:
            self._compiled_pressure_note = 'no pressure pattern columns to verify; native loads'
            return
        if worst > 1.0:
            self._compiled_pressure_note = f'C7 failed at preparation (worst ratio {worst:.3g})'
            return
        compiled.verified_kinds = kinds
        self._compiled_pressure = compiled
        self._vector_bytes += compiled.nbytes()
        self._compiled_pressure_note = f'enabled; {checked} pressure pattern columns meet C7'

    def _source_agrees(self, actual, combined, owned):
        scale = np.abs(self._force_columns[:,0]) + (np.abs(self._force_columns[:,owned.indices]) @ np.abs(owned.coefficients)
                                                    if owned.indices.size else 0.)
        bound = float(np.max(scale, initial=0.))
        discrepancy = float(np.max(np.abs(actual - combined), initial=0.))
        agrees = bool(np.isfinite(bound) and np.isfinite(discrepancy)
                      and discrepancy <= _SOURCE_AGREEMENT_RELATIVE * bound)
        ratio = discrepancy / bound if bound > 0. else (0. if discrepancy == 0. else float('inf'))
        return agrees, discrepancy, bound, ratio

    def _load_scope_recipes(self, snapshot, block):
        """M22 (review S1): no pressure-recipe owners for blocks that never run the native
        pressure kernel; the empty scope still performs the global authority checks at
        entry and exit. A rare compiled disagreement re-evaluates natively and enters
        each element's own scope."""
        compiled = self._compiled_pressure
        if compiled is not None and all(type(packet) is _PatternPacket and (
                packet.canonical is None or not compiled.needs_native_pressure(packet.canonical))
                for _case_id, _time, packet in block):
            self._response_counts['compiled_load_scope_blocks'] += 1
            return ()
        if compiled is not None:
            self._response_counts['native_load_scope_blocks'] += 1
        return super()._load_scope_recipes(snapshot, block)

    def _library_record(self, eid, packet):
        order, linear, constants, derived, columns = self._element_library[eid]
        values = self._combine(columns, packet)
        return _assemble_library_record(order, _library_fields(np.asarray(values, dtype=float), linear),
                                        constants, derived)

    def _response_safe_point(self, token, stage):
        cancellation_safe_point(token, stage)
        self._require_open()
        require_native_source_authority()

    def _check_library_memory(self, extra):
        cfg = self._resource_config
        if cfg is None or cfg.memory_limit_bytes is None:
            return
        from .recovery import MemoryEstimate, ResourcePolicyError
        d = super().diagnostics()
        operator = d['operator_bytes']
        factor = 0 if self._operator_handle is None else self._operator_handle.metadata.get('factor_storage_bytes',operator*4)
        required = self._snapshot.nbytes() + operator + factor + extra + self._snapshot.total_dofs*80
        if self._envelope is not None:
            required += 3*self._envelope.nbytes()
        if required > cfg.memory_limit_bytes:
            fields = dict(self._snapshot.memory_estimate)
            fields['total_bytes_estimate'] = int(required)
            raise ResourcePolicyError('source response library exceeds memory policy', context='prepared_response',
                                      memory_estimate=MemoryEstimate(**fields), resource_config=cfg)

    def _iter_batches_open(self, cases, **kwargs):
        try:
            yield from super()._iter_batches_open(cases, **kwargs)
        finally:
            self._canonical_matches.clear()

    def _response_storage_bytes(self):
        return self._library_bytes

    def _new_envelope(self, plan):
        if getattr(self, '_stress_execution', 'canonical') == 'certified_vectorized':
            return VectorEnvelope(plan)
        return super()._new_envelope(plan)

    def envelope_result(self):
        result = super().envelope_result()
        if result is not None and self._stress_execution == 'certified_library':
            result.diagnostics.update(recovery='certified_response_library_with_canonical_fallback',
                governing_identity_basis='certified_response_values',
                library_stress_cases=self._response_counts['library_stress_cases'])
        return result

    def diagnostics(self):
        result = super().diagnostics()
        result['source_response'] = dict(self._response_counts, library_bytes=self._library_bytes,
            library_numeric_bytes=self._library_numeric_bytes,
            library_metadata_bytes=self._library_bytes-self._library_numeric_bytes,
            pattern_names=list(getattr(self,'_pattern_names',())),
            certificate='actual_full_state_backward_error', envelope_policy='canonical_replay_all',
            compiled_envelope_responses=False, compiled_detailed_responses=False,
            detailed_response_reconstruction_qualified=False,
            detailed_response_execution="canonical_direct_until_component_error_bound",
            reaction_execution="actual_full_Ku_minus_F_diagnostics",
            stress_execution=self._stress_execution,
            max_source_discrepancy_ratio=self._source_discrepancy_max)
        if self._stress_execution == 'certified_library':
            library = self._element_library
            result['source_response'].update(
                contract='certified_response_route_m16',
                source_agreement='max|F_actual-F_c| <= 1e-12 max(|F0|+sum|c_j||F_j|)',
                envelope_policy='certified_response_values',
                governing_identity_basis='certified_response_values',
                compiled_envelope_responses=self._envelope is not None and bool(library),
                compiled_detailed_responses=bool(self._recovery.include_stresses and library),
                detailed_response_execution='certified_response_library',
                element_library_elements=len(library),
                element_library_numeric_bytes=self._element_library_numeric_bytes,
                element_library_worst_verification_residual=self._element_library_verification,
                qualification_record='docs/PREPARED_STATIC_M16_CERTIFIED_ROUTE.md')
        if self._stress_execution == 'certified_vectorized':
            vector = self._vector
            result['source_response'].update(
                contract='certified_vectorized_route_m17',
                source_agreement='max|F_actual-F_c| <= 1e-12 max(|F0|+sum|c_j||F_j|)',
                envelope_policy='certified_response_values',
                governing_identity_basis='certified_response_values',
                detailed_response_execution='certified_vectorized_compiled_affine',
                compiled_envelope_responses=self._envelope is not None and vector is not None,
                compiled_detailed_responses=bool(self._recovery.include_stresses and vector is not None),
                vectorized_elements=0 if vector is None else len(vector.locations),
                vectorized_groups=0 if vector is None else len(vector.groups),
                vectorized_bytes=self._vector_bytes,
                vectorized_probes=0 if vector is None else vector.probes,
                vectorized_worst_verification_residual=0. if vector is None else vector.worst,
                load_execution='compiled_pressure_bases' if self._compiled_pressure is not None else 'native',
                compiled_pressure_note=self._compiled_pressure_note,
                compiled_pressure_worst_c7_ratio=self._compiled_pressure_worst_c7,
                reaction_metadata_copies='pickle_of_plain_snapshot' if self._metadata_copies is not None else 'deepcopy',
                selected_reaction_diagnostics=self._selected_reaction_diagnostics,
                qualification_record='docs/PREPARED_STATIC_M17_VECTORIZED_ROUTE.md')
        return result

    def close(self):
        super().close()
        self._force_columns = self._solution_columns = None
        self._element_library = {}
        self._element_library_numeric_bytes = 0
        self._vector = None
        self._vector_bytes = 0
        self._compiled_pressure = None
        self._metadata_copies = None
        self._reaction_plan = None
        self._canonical_matches.clear()
        self._pattern_names = ()
        self._pattern_lookup = {}
        self._library_bytes = self._library_numeric_bytes = 0

    def _packet_storage_bytes(self, case):
        workspace = 0 if self._vector is None else self._vector.case_workspace_bytes()
        if type(case) is not PatternCase:
            return super()._packet_storage_bytes(case) + workspace
        if type(case.case_id) is not str:
            raise PreparedStaticError("pattern case_id must be a plain string")
        values = case.coefficients
        if type(values) not in (dict,list,tuple,np.ndarray):
            raise PreparedStaticCapabilityError('coefficients require plain named dict or dense numeric vector')
        if type(values) is np.ndarray and (values.ndim != 1 or values.dtype.kind not in 'iuf'):
            raise PreparedStaticCapabilityError('dense coefficients require a one dimensional real array')
        size = 256 + sys.getsizeof(case.case_id) + 64*len(values) + workspace
        if case.canonical_load_case is not None:
            size += load_packet_storage_bytes(StaticCase(case.case_id,case.canonical_load_case,case.time))
        return size

    def _ingest_case(self, case):
        if type(case) is not PatternCase:
            return super()._ingest_case(case)
        # Reuse canonical ID/time validation, and own the optional actual packet.
        case_id,t,canonical = ingest_static_case(StaticCase(case.case_id,case.canonical_load_case,case.time))
        indices,active_values = [],[]
        values = case.coefficients
        if type(values) is dict:
            pairs = values.items()
        elif type(values) in (list,tuple,np.ndarray):
            if len(values) != len(self._pattern_names):
                raise PreparedStaticError('dense coefficient length must equal pattern count')
            pairs = zip(self._pattern_names,values)
        else:
            raise PreparedStaticCapabilityError('coefficients require plain named dict or dense numeric vector')
        for name,value in pairs:
            if type(name) is not str or name not in self._pattern_lookup:
                raise PreparedStaticError('unknown source response pattern', diagnostics={'pattern':str(name)})
            if type(value) not in (float,int,np.float64,np.float32,np.int64,np.int32) or not np.isfinite(value):
                raise PreparedStaticError('pattern coefficients must be finite plain real numbers')
            if value:
                indices.append(self._pattern_lookup[name]+1)
                active_values.append(value)
        return case_id,t,_PatternPacket(np.array(indices,dtype=np.intp),np.array(active_values,dtype=float),
                                       canonical if case.canonical_load_case is not None else None)

    @staticmethod
    def _combine(columns, packet):
        return columns[:,0] + (columns[:,packet.indices] @ packet.coefficients if packet.indices.size else 0.)

    def _load_vector(self, snapshot, owned):
        if type(owned) is not _PatternPacket:
            return super()._load_vector(snapshot,owned)
        scope = _OWNED_RECOVERY_SCOPE.get()
        if scope is None or not scope[0]:
            require_native_source_authority()
        if owned.canonical is not None:
            made = None
            if self._compiled_pressure is not None:
                made = self._compiled_pressure.evaluate(snapshot.load_maps, owned.canonical)
            combined = self._combine(self._force_columns,owned)
            if made is not None and not self._source_agrees(made[0], combined, owned)[0]:
                # M22 (review F2): the compiled path failed the cross-check; the native
                # load decides agreement, certificate, any fallback solve and reactions.
                self._response_counts['compiled_disagreement_cases'] += 1
                made = None
                native_label = 'native_after_compiled_disagreement'
            else:
                native_label = 'native'
            if made is not None:
                actual, info = made[0], made[1]
                self._response_counts['compiled_load_cases'] += 1
            else:
                actual, info = evaluate_load_vector(snapshot.load_maps,owned.canonical)
                if self._stress_execution == 'certified_vectorized':
                    self._response_counts['native_load_cases'] += 1
                    info = dict(info, load_execution=native_label)
            if self._stress_execution != 'canonical':
                agrees, discrepancy, bound, ratio = self._source_agrees(actual, combined, owned)
                self._source_discrepancy_max = max(self._source_discrepancy_max, float(ratio))
                info = dict(info, source_agreement={'max_discrepancy': discrepancy, 'term_scale': bound,
                    'relative': float(ratio), 'agrees': agrees})
            else:
                agrees = bool(np.array_equal(actual, combined))
            self._canonical_matches[id(owned)] = agrees
            return actual, info
        vector = self._combine(self._force_columns,owned)
        if not np.all(np.isfinite(vector)):
            raise PreparedStaticError('source response load overflow')
        return vector, {'method':'owned_source_columns','active_patterns':len(owned.indices)}

    def _solve_block(self, solve_rhs, block):
        library = self._stress_execution != 'canonical'
        if not library and (self._envelope is not None or self._recovery.include_stresses):
            self._reconstructed_block = [False]*len(block)
            made = np.empty_like(solve_rhs)
            for j,(_,_,packet) in enumerate(block):
                source_matches = self._canonical_matches.pop(id(packet),True)
                if type(packet) is _PatternPacket:
                    key = 'canonical_envelope_cases' if self._envelope is not None else 'canonical_stress_cases'
                    if not source_matches:
                        self._response_counts['certification_fallback_cases'] += 1
                else:
                    key = 'direct_cases'
                self._response_counts[key] += 1
                # Match the established one-case replay numerical layout even
                # when ingress and output publication retain multi-case blocks.
                one_rhs = np.array(solve_rhs[:,j:j+1],dtype=float,copy=True,order='C')
                made[:,j:j+1] = super()._solve_block(one_rhs,())
            return made
        made = np.empty_like(solve_rhs)
        self._reconstructed_block = []
        # M31b: the operator norm data is computed at the first certification and
        # again after any canonical solve in between.
        certification_norm = None
        for j,(_,_,packet) in enumerate(block):
            source_matches = self._canonical_matches.pop(id(packet),True)
            reconstruct = type(packet) is _PatternPacket and source_matches
            if type(packet) is _PatternPacket and not source_matches:
                self._response_counts['source_agreement_fallback_cases' if library else 'certification_fallback_cases'] += 1
            if reconstruct:
                made[:,j] = self._combine(self._solution_columns,packet)
                n = self._snapshot.reduced_stiffness.shape[0]
                operator = self._operator_matrix if self._operator_augmented else self._snapshot.reduced_stiffness
                if certification_norm is None:
                    certification_norm = _block_norm_data(operator, self._backward_error)
                error = _certified_backward_error(operator,
                    made[:,j] if self._operator_augmented else made[:n,j],solve_rhs[:,j],certification_norm,
                    self._backward_error)
                if not np.isfinite(error) or error > self._backward_error_limit:
                    reconstruct = False
                    self._response_counts['certification_fallback_cases'] += 1
            if not reconstruct:
                made[:,j:j+1] = super()._solve_block(solve_rhs[:,j:j+1],())
                certification_norm = None
                if type(packet) is _PatternPacket and self._envelope is not None:
                    key = 'canonical_envelope_cases'
                elif type(packet) is _PatternPacket and library:
                    key = 'pattern_canonical_solves'
                else:
                    key = 'direct_cases'
                self._response_counts[key] += 1
            else:
                self._response_counts['reconstructed_cases'] += 1
            self._reconstructed_block.append(reconstruct)
        return made

    def _recover_block(self,snapshot,full,loads,recovery,labels,certified,envelope,block):
        if self._stress_execution == 'certified_vectorized' and self._vector is not None and (
                envelope is not None or recovery.include_stresses):
            flags = tuple(self._reconstructed_block)
            for j,(_,_,packet) in enumerate(block):
                certified[j]['source_response'] = {'reconstructed': flags[j],
                    'stress_execution': 'certified_vectorized',
                    'state': 'reconstructed' if flags[j] else 'canonical_solve',
                    'active_patterns': len(packet.indices) if type(packet) is _PatternPacket else None}
            self._response_counts['vectorized_stress_cases'] += len(block)
            return recover_vector_block(snapshot, full, loads, recovery, labels, certified, envelope,
                                        self._vector, snapshot.recovery_compilation, self._metadata_copies,
                                        self._reaction_plan,
                                        lean_selected=self._selected_reaction_diagnostics == 'lean')
        if self._stress_execution == 'certified_library' and (envelope is not None or recovery.include_stresses):
            flags = tuple(self._reconstructed_block)
            packets = tuple(packet for _,_,packet in block)
            library = self._element_library
            for j,packet in enumerate(packets):
                certified[j]['source_response'] = {'reconstructed': flags[j],
                    'stress_execution': 'certified_library' if flags[j] else 'canonical_fallback',
                    'active_patterns': len(packet.indices) if type(packet) is _PatternPacket else None}
                if flags[j]:
                    self._response_counts['library_stress_cases'] += 1
            def source(eid, column):
                if not flags[column] or eid not in library:
                    return None
                return self._library_record(eid, packets[column])
            results, transaction, stats = _prepared_static_module._SHARED_BINDINGS[0][1](
                snapshot, full, loads, recovery, labels, certified, envelope, record_source=source)
            self._response_counts['reconstructed_element_records'] += stats.get('library_element_records', 0)
            return results, transaction, stats
        if envelope is not None or recovery.include_stresses:
            return super()._recover_block(snapshot,full,loads,recovery,labels,certified,envelope,block)
        from .prepared_static_shared import _selected_reactions
        results = []
        stats = {'physical_element_evaluations':0,'reaction_diagnostic_evaluations':0,
                 'reconstructed_element_records':0}
        for j,(_,_,packet) in enumerate(block):
            if not self._reconstructed_block[j]:
                items,_,counts = super()._recover_block(snapshot,None if full is None else full[:,j:j+1],loads[:,j:j+1],
                    recovery,labels[j:j+1],certified[j:j+1],None,block[j:j+1])
                results.extend(items)
                for key in stats:
                    stats[key] += counts.get(key,0)
                continue
            item = {'status':'converged','solver_info':certified[j], 'node_displacements':{},'element_stresses':{},'reactions':{}}
            certified[j]['source_response'] = {'reconstructed':True,'active_patterns':len(packet.indices)}
            if recovery.include_displacements:
                item['node_displacements'] = {node:full[snapshot.load_maps.node_dofs[node],j].copy() for node in snapshot.selected_node_ids}
            if recovery.include_reactions:
                forces = constraint_force_diagnostics(snapshot.reaction_maps,snapshot.stiffness,snapshot.transformation,
                    snapshot.rigid_modes,full[:,j],loads[:,j],constraint_info=snapshot.constraint_info,nullspace_info=snapshot.nullspace_info)
                _selected_reactions(snapshot,recovery,forces,item)
                stats['reaction_diagnostic_evaluations'] += 1
            results.append(item)
        return results,None,stats

def prepare_static_response_evaluator(model, patterns, *, baseline_load_case=None, **kwargs):
    # stress_execution and selected_reaction_diagnostics (M24) pass through kwargs.
    """Prepare baseline plus homogeneous source responses; existing prepared kwargs apply."""
    return PreparedStaticResponseEvaluator(model,patterns,baseline_load_case=baseline_load_case,**kwargs)

# Pin class methods, global aliases and transitive package helper code before
# any input iterator or progress callback can replace executable authority.
import types as _types
from .boundary import _callable_authority, _callable_authority_matches
from .static_batch import _class_state

def _require_response_authority(owner):
    if type(owner) not in (PreparedStaticEvaluator, PreparedStaticResponseEvaluator):
        raise PreparedStaticCapabilityError("source response evaluator subclasses are not admitted")
    for cls, facts in _RESPONSE_CLASSES:
        if _class_state(cls) != facts:
            raise PreparedStaticCapabilityError('source response class authority changed')
    for function, authority, bindings in _RESPONSE_FUNCTIONS:
        if (not _callable_authority_matches(function,authority) or
            any(function.__globals__.get(name) is not value for name,value in bindings)):
            raise PreparedStaticCapabilityError('source response executable authority changed')
    for name in _RESPONSE_METHOD_NAMES:
        if name in vars(owner):
            raise PreparedStaticCapabilityError('source response instance method authority changed')

def _capture_response_functions():
    records,seen = [],set()
    def visit(function):
        if type(function) is not _types.FunctionType or id(function) in seen:
            return
        seen.add(id(function))
        bindings = tuple((name,function.__globals__[name]) for name in function.__code__.co_names
                         if name in function.__globals__ and not name.startswith('_RESPONSE_'))
        records.append((function,_callable_authority(function),bindings))
        for _,value in bindings:
            if type(value) is _types.FunctionType and value.__module__.startswith('anysolver'):
                visit(value)
    for cls in (PreparedStaticEvaluator,PreparedStaticResponseEvaluator,PatternCase,_PatternPacket,
                VectorEnvelope,VectorRecovery,CompiledPressure,ReactionPlan):
        for value in vars(cls).values():
            visit(value.__func__ if type(value) is staticmethod else value)
    visit(prepare_static_response_evaluator)
    visit(_require_response_authority)
    return tuple(records)

_RESPONSE_CLASSES = tuple((cls,_class_state(cls)) for cls in
    (PreparedStaticResponseEvaluator,PatternCase,_PatternPacket,VectorEnvelope,VectorRecovery,CompiledPressure,ReactionPlan))
_RESPONSE_METHOD_NAMES = tuple({name for cls in (PreparedStaticEvaluator,PreparedStaticResponseEvaluator)
    for name,value in vars(cls).items() if callable(value) or type(value) is staticmethod})
_RESPONSE_FUNCTIONS = _capture_response_functions()
from . import prepared_static as _prepared_module
_prepared_module._RESPONSE_EXECUTION_GUARD = (_require_response_authority,_callable_authority(_require_response_authority))
