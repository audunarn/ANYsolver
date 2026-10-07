"""Bounded independent static responses for arbitrary ordered load histories."""
from __future__ import annotations

from dataclasses import dataclass, replace
from contextlib import ExitStack, contextmanager
from typing import Any, Iterable, Iterator, Optional
import time as _time
import types

import numpy as np

from .analysis_session import AnalysisSession, _constraint_fingerprints, _immutable_array
from .control import cancellation_safe_point, emit_progress
from .recovery import RecoveryConfig, ResourceConfig, ResourcePolicyError, estimate_model_memory


@dataclass(frozen=True)
class StaticCase:
    case_id: str
    load_case: Any
    time: Optional[float] = None


@dataclass(frozen=True)
class StaticBatch:
    input_indices: tuple[int, ...]
    case_ids: tuple[str, ...]
    times: tuple[Optional[float], ...]
    output_dofs: np.ndarray
    displacements: np.ndarray
    case_results: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]


class StaticBatchError(ValueError):
    """A stream block cannot be certified; earlier yielded blocks remain valid."""
    def __init__(self, message: str, *, diagnostics: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.diagnostics = {} if diagnostics is None else diagnostics


@contextmanager
def _case_failure_boundary(stage: str, case: StaticCase, input_index: int):
    from .control import SolveCancelled
    try:
        yield
    except SolveCancelled:
        raise
    except Exception as error:
        raise StaticBatchError("static case recovery failed", diagnostics={
            "stage": stage, "case_id": case.case_id, "input_index": input_index,
            "error": str(error), "original_exception_type": type(error).__name__}) from error


def _snapshot_plain_load(load: Any) -> tuple[bool, Any]:
    """Own an exact builtin load without conversion or foreign observations."""
    from .boundary import LoadCase, _exact_load_case_instance_namespace, _plain_numeric_array
    if load is None:
        return True, None
    state = _exact_load_case_instance_namespace(load)
    if state is None:
        return False, None
    refused = object()
    def clone(value: Any) -> Any:
        if type(value) in (int, float, bool, str, type(None)):
            return value
        if _plain_numeric_array(value):
            return value.copy()
        if type(value) in (list, tuple):
            made = [clone(v) for v in value]
            return refused if any(v is refused for v in made) else type(value)(made)
        if type(value) is dict and all(type(k) is int for k in value):
            made = {k: clone(v) for k, v in value.items()}
            return refused if any(v is refused for v in made.values()) else made
        return refused
    made = {key: clone(value) for key, value in state.items()}
    if any(value is refused for value in made.values()):
        return False, None
    return True, LoadCase(**made)


def _plain_state(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return (type(value), id(value))
    if type(value) in (str, int, float, bool, type(None)):
        return value
    if type(value) is np.ndarray:
        return (value.shape, value.dtype.str, value.tobytes())
    if type(value) is dict:
        return tuple((_plain_state(k, depth + 1), _plain_state(v, depth + 1)) for k, v in value.items())
    if type(value) in (list, tuple):
        return tuple(_plain_state(v, depth + 1) for v in value)
    namespace = getattr(value, "__dict__", None)
    return (type(value), id(value), _plain_state(namespace, depth + 1))


def _callable_state(function: Any, seen: Optional[set[int]] = None) -> Any:
    if type(function) is not types.FunctionType:
        return (type(function), id(function))
    seen = set() if seen is None else seen
    if id(function) in seen:
        return id(function)
    seen.add(id(function))
    cells = []
    for name, cell in zip(function.__code__.co_freevars, function.__closure__ or ()):
        try:
            value = cell.cell_contents
        except ValueError:
            cells.append("empty")
        else:
            owned_counter = (name == "accepted_generation" and type(value) is int
                and function.__module__ == "anysolver._qualified_authority_epoch"
                and function.__qualname__ in {
                    "_AuthorityEpochManager.bind.<locals>.require",
                    "_AuthorityEpochManager.bind_context.<locals>.require",
                    "_AuthorityEpochManager.bind_argument.<locals>.require"})
            cells.append("owned_epoch_counter" if owned_counter else (
                _callable_state(value, seen) if type(value) is types.FunctionType else id(value)))
    defaults = function.__defaults__
    keywords = function.__kwdefaults__
    return (id(function), function.__code__, id(defaults),
            tuple(id(v) for v in defaults or ()), id(keywords),
            tuple((k, id(v)) for k, v in (keywords or {}).items()), tuple(cells))


def _class_state(cls: type) -> Any:
    result = []
    for base in cls.__mro__:
        for name, value in vars(base).items():
            if type(value) is types.FunctionType:
                state = _callable_state(value)
            elif type(value) is property:
                state = (id(value), _callable_state(value.fget),
                         _callable_state(value.fset), _callable_state(value.fdel))
            elif type(value) in (staticmethod, classmethod):
                state = _callable_state(value.__func__)
            else:
                state = (type(value), id(value))
            result.append((base, name, state))
    return tuple(result)


def _model_state(model: Any) -> Any:
    from .fe_core import _ELEMENT_LOCAL_CACHE_NAMES
    mesh = model.mesh
    token = getattr(mesh, "_qualified_direct_state_token", None)
    activity = mesh.element_activity
    derived = set(_ELEMENT_LOCAL_CACHE_NAMES) | {"_fiber_grid_cache",
        "_qualified_direct_state_token", "_qualified_direct_state_tokens"}
    element_state = tuple((element_id, id(element), _plain_state({k: v for k, v in vars(element).items()
        if k not in derived})) for element_id, element in mesh.elements.items())
    classes = tuple(dict.fromkeys(type(e) for e in mesh.elements.values()))
    revisions = tuple((k, v) for k, v in model.revision_signature().items() if k not in {"load", "result_state"})
    return (id(model), id(mesh), revisions, element_state,
            tuple(_class_state(cls) for cls in classes),
            tuple((node_id, id(node), node.x, node.y, node.z, tuple(node.dofs))
                  for node_id, node in mesh.nodes.items()),
            id(token), None if token is None else int(token[0]),
            _constraint_fingerprints(model), _plain_state(mesh.point_masses),
            _plain_state(model.materials), id(activity),
            None if activity is None else _plain_state(activity))


def iter_linear_batches(
    model: Any, cases: Iterable[StaticCase], *, batch_size: int = 32,
    output_dofs: Optional[Any] = None, recovery_config: Optional[RecoveryConfig] = None,
    resource_config: Optional[ResourceConfig] = None, session: Optional[AnalysisSession] = None,
    constraint_mode: str = "auto", allow_unbalanced_free_free: bool = False,
    cancellation_token: Any = None, progress_callback: Any = None,
) -> Iterator[StaticBatch]:
    """Yield certified static blocks; times label cases and never interpolate loads.

    Every load is independently assembled.  A supplied session stays owned by
    the caller; an internal session closes on exhaustion, error or generator
    close.  Input iteration, progress callbacks and yields hold no authority
    lease.  Model changes across those boundaries terminate the stream.
    """
    from .assembly import (_backward_error, _LINEAR_STATIC_BACKWARD_ERROR_LIMIT,
        _compute_constraint_force_diagnostics_under_lease)
    from .matrix_assembly import _assemble_load_matrix_annotated, LoadMatrixCaseError, assemble_load_vector
    from .recovery import recover_stress_result, filter_reactions
    from .recovery_batches import _run_with_qualified_recovery_runtime_lease
    from .threading_policy import solver_thread_scope
    from .jit_compiler import numba_thread_scope
    from .linalg import backend_operation_counts

    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    cancellation_safe_point(cancellation_token, "static_batch.start")
    model.apply_boundary_conditions()
    owned_session = session is None
    active = AnalysisSession(model) if owned_session else session
    iterator = None
    primary_failure = None
    try:
        active._require_model(model)
        recovery = RecoveryConfig(include_displacements=False, include_stresses=False,
                                  include_reactions=False) if recovery_config is None else recovery_config
        n = int(model.mesh.dof_manager.total_dofs)
        dofs = np.arange(n, dtype=np.intp) if output_dofs is None else np.asarray(output_dofs, dtype=np.intp).reshape(-1).copy()
        if np.any(dofs < 0) or np.any(dofs >= n):
            if owned_session:
                active.close()
            raise ValueError("output_dofs contains an out-of-range DOF")
        dofs = _immutable_array(dofs)
        frozen = _model_state(model)

        def unchanged(stage: str) -> None:
            if _model_state(model) != frozen:
                raise StaticBatchError("model changed during static stream", diagnostics={"stage": stage})
            active._require_model(model)


        iterator = iter(cases)
        unchanged("input iterator creation")
        try:
            first_case = next(iterator)
        except StopIteration:
            unchanged("empty input")
            return
        unchanged("first input observation")
        if type(first_case) is not StaticCase or type(first_case.case_id) is not str:
            raise StaticBatchError("cases must be StaticCase records with string case_id")
        first_time = None if first_case.time is None else float(first_case.time)
        if first_time is not None and not np.isfinite(first_time):
            raise StaticBatchError("case time must be finite when supplied")
        first_plain, first_snapshot = _snapshot_plain_load(first_case.load_case)
        unchanged("first load snapshot observation")
        first_case = StaticCase(first_case.case_id,
            first_snapshot if first_plain else first_case.load_case, first_time)
        estimate = estimate_model_memory(model, num_rhs=0, recovery_config=recovery)
        selected_elements = len(recovery.selected_element_ids(model)) if recovery.include_stresses else 0
        # Account for simultaneous load/reduced/solution/reconstruction blocks
        # and conservative per-element result arrays; native factor storage is
        # estimated separately from the assembled sparse matrix.
        base_bytes = int(estimate.total_bytes_estimate * 4)
        per_case_bytes = int((n * 10 + len(dofs)) * 8 + selected_elements * 512 * 8)
        effective = batch_size
        limit = None if resource_config is None else resource_config.memory_limit_bytes
        if limit is not None:
            available = int(limit) - base_bytes
            effective = min(batch_size, available // max(per_case_bytes, 1))
            if effective < 1:
                memory = replace(estimate, total_bytes_estimate=base_bytes + per_case_bytes,
                    notes=estimate.notes + ("static block and native factor storage estimated",))
                raise ResourcePolicyError("one static case exceeds configured memory estimate limit",
                    context="iter_linear_batches", memory_estimate=memory, resource_config=resource_config)
        unchanged("memory preflight")
        assembly_threads = None if resource_config is None else resource_config.assembly_threads
        first_eager = None
        if not first_plain:
            try:
                with solver_thread_scope(resource_config), numba_thread_scope(assembly_threads):
                    vector, info = assemble_load_vector(model, first_case.load_case)
            except Exception as error:
                from .control import SolveCancelled
                if isinstance(error, SolveCancelled):
                    raise
                raise StaticBatchError("load assembly failed", diagnostics={"stage": "load assembly",
                    "case_id": first_case.case_id, "input_index": 0,
                    "error": str(error), "original_exception_type": type(error).__name__}) from error
            unchanged("first immediate load assembly")
            first_eager = (np.array(vector, copy=True), info)
            first_case = StaticCase(first_case.case_id, None, first_time)
        before = backend_operation_counts()
        prepare_start = _time.perf_counter()
        with solver_thread_scope(resource_config):
            with numba_thread_scope(assembly_threads):
                active.stiffness_plan()
            operator = active.static_operator_plan(constraint_mode=constraint_mode, model=model)
        unchanged("operator preparation")
        constraint = operator.constraint
        K = active.stiffness_plan().matrix
        output = active.output_selection_plan(dofs, constraint)
        if operator.handle is not None and operator.handle.status != "ok":
            raise StaticBatchError("static factorization failed", diagnostics=operator.handle.diagnostics())
        prepare_seconds = _time.perf_counter() - prepare_start
        pending_first = True
        next_index = 0
        exhausted = False
        while not exhausted:
            block_started = _time.perf_counter()
            cancellation_safe_point(cancellation_token, "static_batch.before_input")
            unchanged("before input")
            block = []
            indices = []
            eager_vectors = {}
            eager_infos = {}
            if first_eager is not None:
                eager_vectors[0], eager_infos[0] = first_eager
                first_eager = None
            eager_seconds = 0.0
            for _ in range(effective):
                try:
                    if pending_first:
                        case, first_case, pending_first = first_case, None, False
                    else:
                        case = next(iterator)
                except StopIteration:
                    exhausted = True
                    unchanged("input exhaustion")
                    break
                unchanged("input observation")
                if type(case) is not StaticCase or type(case.case_id) is not str:
                    raise StaticBatchError("cases must be StaticCase records with string case_id")
                case_time = None if case.time is None else float(case.time)
                if case_time is not None and not np.isfinite(case_time):
                    raise StaticBatchError("case time must be finite when supplied")
                unchanged("case record observation")
                plain, snapshot = _snapshot_plain_load(case.load_case)
                unchanged("load snapshot observation")
                if not plain:
                    eager_started = _time.perf_counter()
                    try:
                        with solver_thread_scope(resource_config), numba_thread_scope(assembly_threads):
                            vector, info = assemble_load_vector(model, case.load_case)
                    except Exception as error:
                        from .control import SolveCancelled
                        if isinstance(error, SolveCancelled):
                            raise
                        raise StaticBatchError("load assembly failed", diagnostics={"stage": "load assembly",
                            "case_id": case.case_id, "input_index": next_index,
                            "error": str(error), "original_exception_type": type(error).__name__}) from error
                    unchanged("immediate load assembly")
                    eager_vectors[len(block)], eager_infos[len(block)] = np.array(vector, copy=True), info
                    eager_seconds += _time.perf_counter() - eager_started
                block.append(StaticCase(case.case_id, snapshot, case_time))
                indices.append(next_index)
                next_index += 1
                cancellation_safe_point(cancellation_token, "static_batch.after_input")
            if not block:
                break
            start = _time.perf_counter()
            phases = {"operator_preparation": prepare_seconds,
                "input_and_snapshot": start - block_started - eager_seconds}
            prepare_seconds = 0.0
            pending = [index for index in range(len(block)) if index not in eager_vectors]
            try:
                with solver_thread_scope(resource_config), numba_thread_scope(assembly_threads):
                    pending_F, pending_info = _assemble_load_matrix_annotated(model,
                        tuple(block[index].load_case for index in pending))
            except LoadMatrixCaseError as error:
                position = pending[error.case_index]
                raise StaticBatchError("load assembly failed", diagnostics={"stage": "load assembly",
                    "case_id": block[position].case_id, "input_index": indices[position],
                    "error": str(error), "original_exception_type": type(error.__cause__).__name__}) from error.__cause__
            vectors = dict(eager_vectors)
            infos = dict(eager_infos)
            for column, position in enumerate(pending):
                vectors[position] = pending_F[:, column]
                infos[position] = pending_info["columns"][column]
            F = np.column_stack([vectors[index] for index in range(len(block))])
            load_info = {"columns": [infos[index] for index in range(len(block))]}
            del pending_F, pending_info, vectors, infos, eager_vectors, eager_infos
            unchanged("load assembly")
            phases["load_assembly"] = _time.perf_counter() - start + eager_seconds
            phase_start = _time.perf_counter()
            rhs = np.asarray(constraint.T.T @ (F - (K @ constraint.u0)[:, None]), dtype=float)
            r = operator.rigid_modes.shape[1]
            compatibility = []
            for j, case in enumerate(block):
                components = np.asarray(operator.rigid_modes.T @ rhs[:, j]).reshape(-1)
                imbalance = float(np.linalg.norm(components))
                relative = imbalance / max(float(np.linalg.norm(rhs[:, j])), 1.0)
                warnings = []
                if operator.augmented and relative > 1e-7:
                    message = "The external load vector has a non-zero rigid-body component. For a physical free-free static solution, use self-equilibrated loads."
                    if not allow_unbalanced_free_free:
                        raise StaticBatchError(message, diagnostics={"status": "incompatible_free_free_load",
                            "case_id": case.case_id, "input_index": indices[j],
                            "relative_rigid_body_load_imbalance": relative})
                    warnings.append(message + " The nullspace solve returned a gauged displacement field and balancing generalized reactions.")
                compatibility.append({"rigid_body_load_components": components.tolist(),
                    "rigid_body_load_imbalance_norm": imbalance,
                    "relative_rigid_body_load_imbalance": relative, "warnings": warnings})
            solve_rhs = np.vstack((rhs, np.zeros((r, len(block))))) if operator.augmented else rhs
            phases["load_reduction_and_compatibility"] = _time.perf_counter() - phase_start
            phase_start = _time.perf_counter()
            cancellation_safe_point(cancellation_token, "static_batch.before_solve")
            try:
                with solver_thread_scope(resource_config):
                    solved = np.zeros_like(solve_rhs) if operator.handle is None else (
                        operator.scaling[:, None] * operator.handle.solve_many(operator.scaling[:, None] * solve_rhs))
            except Exception as error:
                from .control import SolveCancelled
                if isinstance(error, SolveCancelled):
                    raise
                raise StaticBatchError("static backend solve failed", diagnostics={"stage": "solve",
                    "case_ids": tuple(case.case_id for case in block), "error": str(error)}) from error
            unchanged("backend solve")
            cancellation_safe_point(cancellation_token, "static_batch.after_solve")
            phases["solve"] = _time.perf_counter() - phase_start
            phase_start = _time.perf_counter()
            q = solved[:rhs.shape[0]]
            values = output.reconstruct(q)
            need_full = recovery.include_stresses or recovery.include_reactions or recovery.include_displacements
            full = np.asarray(constraint.T @ q + constraint.u0[:, None]) if need_full else None
            phases["output_reconstruction"] = _time.perf_counter() - phase_start
            phases["certification"] = 0.0
            phases["recovery"] = 0.0
            certified = []
            for j, case in enumerate(block):
                phase_start = _time.perf_counter()
                error = (_backward_error(operator.matrix, solved[:, j], solve_rhs[:, j])
                    if operator.augmented else _backward_error(constraint.K_red, q[:, j], rhs[:, j]))
                if not np.isfinite(error) or error > _LINEAR_STATIC_BACKWARD_ERROR_LIMIT:
                    raise StaticBatchError("static case exceeded certified backward-error limit",
                        diagnostics={"case_id": case.case_id,
                            "input_index": indices[j],
                            "relative_backward_error": error if np.isfinite(error) else None,
                            "relative_backward_error_disposition": "LIMIT_EXCEEDED" if np.isfinite(error) else "NONFINITE_OR_OVERFLOW"})
                info = {"status": "converged", "case_id": case.case_id,
                    "input_index": indices[j], "relative_backward_error": error,
                    "relative_backward_error_limit": _LINEAR_STATIC_BACKWARD_ERROR_LIMIT,
                    "relative_backward_error_disposition": "CERTIFIED", "load": load_info["columns"][j],
                    "backend": {} if operator.handle is None else operator.handle.diagnostics(),
                    **dict(operator.info), **compatibility[j]}
                if operator.augmented:
                    info.update(method="rigid_body_nullspace_augmented", nullspace_rank=r,
                        rigid_body_lagrange_multipliers=solved[rhs.shape[0]:, j].tolist(),
                        gauge_residual_norm=float(np.linalg.norm(operator.rigid_modes.T @ q[:, j])),
                        augmented_residual_norm=float(np.linalg.norm(constraint.K_red @ q[:, j]
                            + operator.rigid_modes @ solved[rhs.shape[0]:, j] - rhs[:, j])))
                phases["certification"] += _time.perf_counter() - phase_start
                certified.append(info)
            results = []
            # The block is already acquired and every recovery call below is
            # package owned, so one solver thread scope covers the whole block
            # instead of re-entering native pool coordination per case.  The
            # scope still restores before input iteration, callbacks, yields
            # and every error or close path, and each case keeps its own
            # failure boundary and mutation check.
            with ExitStack() as block_scopes:
                if recovery.include_stresses or recovery.include_reactions:
                    block_scopes.enter_context(solver_thread_scope(resource_config))
                for j, case in enumerate(block):
                    phase_start = _time.perf_counter()
                    info = certified[j]
                    item = {"status": "converged", "solver_info": info,
                        "node_displacements": {}, "element_stresses": {}, "reactions": {}}
                    if recovery.include_displacements:
                        for node_id in recovery.selected_node_ids(model):
                            item["node_displacements"][node_id] = full[np.asarray(model.mesh.nodes[node_id].dofs), j].copy()
                    if recovery.include_stresses:
                        with _case_failure_boundary("stress recovery", case, indices[j]):
                            recovered = recover_stress_result(model, full[:, j], recovery,
                                resource_config=resource_config)
                        item["element_stresses"] = recovered.element_stresses
                        info["stress_recovery"] = recovered.provenance_dict()
                        info["recovery"] = recovered.execution_report.to_dict()
                    if recovery.include_reactions:
                        with _case_failure_boundary("reaction recovery", case, indices[j]):
                            forces = _run_with_qualified_recovery_runtime_lease(model, context="static batch prepared reactions",
                                operation=lambda guard, j=j: _compute_constraint_force_diagnostics_under_lease(
                                    model, full[:, j], qualified_runtime_guard=guard,
                                    prepared_system=(K, F[:, j], constraint, operator.rigid_modes, operator.info["nullspace_info"])))
                        combined = {}
                        for bucket in ("support_reactions", "mpc_slave_forces"):
                            for node_id, force in forces[bucket].items():
                                combined.setdefault(node_id, np.zeros(6))
                                combined[node_id] += force
                        item["reactions"] = filter_reactions(combined, recovery, model)
                        item["reaction_node_ids"] = recovery.selected_node_ids(model)
                        if recovery.node_ids is not None:
                            selected = set(item["reaction_node_ids"])
                            forces = {key: value for key, value in forces.items() if key != "residual"}
                            for bucket in ("support_reactions", "mpc_slave_forces", "mpc_master_equivalent_forces"):
                                forces[bucket] = {node: value for node, value in forces[bucket].items() if node in selected}
                        item["constraint_forces"] = forces
                    unchanged("case recovery")
                    phases["recovery"] += _time.perf_counter() - phase_start
                    results.append(item)
            after = backend_operation_counts()
            diagnostics = {"status": "converged", "batch_size": len(block), "requested_batch_size": batch_size,
                "effective_batch_size": effective, "estimated_block_bytes": base_bytes + per_case_bytes * len(block),
                "process_wide_backend_operation_counts": after,
                "process_wide_backend_operation_deltas": {k: after[k] - before.get(k, 0) for k in after},
                "analysis_session": active.diagnostics(), "elapsed_seconds": _time.perf_counter() - block_started,
                "phase_timings_seconds": phases,
                "full_reconstruction": need_full, "prepared_reactions": bool(recovery.include_reactions)}
            emit_progress(progress_callback, "static_batch_complete", "static_batch.complete",
                          completed=next_index, num_cases=len(block))
            unchanged("progress callback")
            cancellation_safe_point(cancellation_token, "static_batch.before_yield")
            values.setflags(write=False)
            dofs.setflags(write=False)
            yield StaticBatch(tuple(indices), tuple(c.case_id for c in block), tuple(c.time for c in block),
                              dofs, values, tuple(results), diagnostics)
            # Drop all prior block ownership before requesting more input.
            del F, rhs, solve_rhs, solved, q, values, full, results, certified, block
            unchanged("consumer return")
            before = after
    except BaseException as error:
        primary_failure = error
        raise
    finally:
        try:
            if iterator is not None:
                try:
                    close = getattr(iterator, "close", None)
                    if callable(close):
                        close()
                except BaseException as cleanup_error:
                    if primary_failure is None:
                        primary_failure = cleanup_error
                        raise
                    BaseException.add_note(primary_failure, "source iterator cleanup failed: " + repr(cleanup_error))
        finally:
            if owned_session:
                try:
                    active.close()
                except BaseException as cleanup_error:
                    if primary_failure is None:
                        raise
                    BaseException.add_note(primary_failure, "analysis session cleanup failed: " + repr(cleanup_error))
