def _secant_plane_seed_kernel(*, model: 'FEModel', T: sparse.csr_matrix, u0: np.ndarray, F_const: np.ndarray, F_prop: np.ndarray, stage_vectors: Sequence[np.ndarray], load_case: Optional['LoadCase'], constant_load_case: Optional['LoadCase'], load_program: Optional[NonlinearLoadProgram], displacement_control: DisplacementControl, committed_states: Dict[int, Any], num_layers: int, num_steps: int, max_iterations: int, tolerance: float, info: Dict[str, Any], start_time: float, resource_config: Optional[ResourceConfig]=None, kinematics: str='von_karman', corotational_tangent: str='not_applicable', initial_reduced_displacements: Optional[np.ndarray]=None, cancellation_token: Optional[CancellationToken]=None, progress_callback: Optional[ProgressCallback]=None, record_increment_snapshots: bool=False, initial_load_factor: float=0.0, recover_initial_load_factor: bool=False, step_index_offset: int=0, initial_steps: Sequence[NonlinearStaticStep]=(), initial_history: Sequence[Mapping[str, Any]]=(), initial_total_iterations: int=0, restart_analysis_contract: Optional[Mapping[str, Any]]=None, rotating_mpc_map: Optional[Any]=None, _exact_guard: Any=None) -> NonlinearStaticResult:
    """Displacement-control Newton solve with load factor as an unknown."""
    exact_guard = _exact_guard or _EXACT_QUALIFIED_LIFECYCLE_GUARD
    exact_guard(model, context='nonlinear static displacement-control preflight')
    if load_program is not None:
        if len(load_program.stages) == 1:
            constant_terms = [(constant_load_case, 1.0)]
            proportional_term = (load_program.stages[0].load_case, load_program.stages[0].target_factor)
            F_const_static = F_const
            F_prop_static = load_program.stages[0].target_factor * stage_vectors[0]
            active_stage = load_program.stages[0].name
        else:
            constant_terms = [(constant_load_case, 1.0)] + [(stage.load_case, stage.target_factor) for stage in load_program.stages[:-1]]
            proportional_term = (load_program.stages[-1].load_case, load_program.stages[-1].target_factor)
            F_const_static = F_const.copy()
            for stage, vector in zip(load_program.stages[:-1], stage_vectors[:-1]):
                F_const_static += stage.target_factor * vector
            F_prop_static = load_program.stages[-1].target_factor * stage_vectors[-1]
            active_stage = load_program.stages[-1].name
        info['displacement_control_load_split'] = {'constant_stages': [stage.name for stage in load_program.stages[:-1]], 'proportional_stage': active_stage}
    else:
        constant_terms = [(constant_load_case, 1.0)]
        proportional_term = (load_case, 1.0)
        F_const_static = F_const
        F_prop_static = F_prop
        active_stage = 'displacement_control'
    n_red = int(T.shape[1])
    if initial_reduced_displacements is None:
        q = np.zeros(n_red, dtype=float)
    else:
        q = np.asarray(initial_reduced_displacements, dtype=float).reshape(-1).copy()
        if q.size != n_red:
            raise ValueError(f'initial_reduced_displacements has {q.size} entries; expected {n_red}')
    lam = float(initial_load_factor)
    steps: List[NonlinearStaticStep] = list(initial_steps)
    snapshots: List[NonlinearIncrementSnapshot] = []
    history: List[Dict[str, Any]] = copy.deepcopy(list(initial_history))
    status = 'completed'
    failure_reason: Optional[str] = None
    total_iterations = int(initial_total_iterations)
    from .corotational import SO3MeanDomainError

    def full_u(q_vec: np.ndarray) -> np.ndarray:
        u_lin = np.asarray(T @ q_vec + u0, dtype=float).reshape(-1)
        if rotating_mpc_map is not None:
            return rotating_mpc_map.apply_kinematics(u_lin)
        return u_lin
    row_full = displacement_control.full_row(model)
    exact_guard(model, context='nonlinear static displacement-control row')
    row_red = np.asarray(row_full @ T, dtype=float).reshape(-1)
    row_u0 = float(row_full @ u0)
    initial_u = full_u(q)
    if rotating_mpc_map is not None:
        row_jac_initial = np.asarray(row_full @ rotating_mpc_map.jacobian(initial_u), dtype=float).reshape(-1)
        if float(np.linalg.norm(row_jac_initial)) <= 0.0:
            raise ValueError('Displacement control target has a zero control Jacobian at the initial state and cannot be used as an unknown')
    elif float(np.linalg.norm(row_red)) <= 0.0:
        raise ValueError('Displacement control target is fixed or dependent and cannot be used as an unknown')
    follower_active = any((_has_follower_pressure(case, model=model, _exact_guard=exact_guard) for case, _factor in [*constant_terms, proportional_term]))
    if follower_active:
        F_prop_initial, _ = _weighted_external_load_system(model, [proportional_term], initial_u, tangent=False)
        exact_guard(model, context='nonlinear static displacement-control initial load')
    else:
        F_prop_initial = F_prop_static
    F_prop_red = rotating_mpc_map.reduce_force(initial_u, F_prop_initial) if rotating_mpc_map is not None else np.asarray(T.T @ F_prop_initial, dtype=float).reshape(-1)
    if float(np.linalg.norm(F_prop_red)) <= 0.0:
        raise ValueError('Displacement control requires a non-zero proportional load vector')
    if recover_initial_load_factor and rotating_mpc_map is not None:
        f_int_initial, _k0, _initial_trial = _assemble_nonlinear_system(model, initial_u, committed_states, num_layers, tangent=False, kinematics=kinematics, corotational_tangent=corotational_tangent)
        exact_guard(model, context='nonlinear static displacement-control initial load recovery')
        _discard_nonlinear_state_candidate(committed_states)
        if follower_active:
            f_const_initial, _unused_k = _weighted_external_load_system(model, constant_terms, initial_u, tangent=False)
        else:
            f_const_initial = F_const_static
        f_red_initial = rotating_mpc_map.reduce_force(initial_u, f_int_initial - f_const_initial)
        _p_norm = float(F_prop_red @ F_prop_red)
        if _p_norm > 0.0:
            lam = float(F_prop_red @ f_red_initial / _p_norm)
        info['displacement_control_recovered_initial_load_factor'] = float(lam)
    zero_load_tangent = sparse.csr_matrix((model.mesh.dof_manager.total_dofs, model.mesh.dof_manager.total_dofs), dtype=float)
    target_total = float(displacement_control.target_displacement)
    initial_control = float(row_full @ full_u(q)) if rotating_mpc_map is not None else float(row_red @ q + row_u0)
    target_increment = target_total - initial_control
    target_scale = 0.2
    info['displacement_control_initial_value'] = initial_control
    from .general_contact.runtime import active_contact_manager
    contact_manager = active_contact_manager()
    augmented_contact_manager = contact_manager if getattr(contact_manager, 'augmented', False) else None
    moving_tool = bool(contact_manager is not None and hasattr(contact_manager, 'path_translation') and np.any(contact_manager.path_translation))
    motion_factor = 0.0
    if moving_tool:
        if target_total == 0.0:
            raise ValueError('moving rigid-tool displacement control needs a nonzero target')
        motion_factor = initial_control / target_total
        if not -1e-12 <= motion_factor <= 1.0 + 1e-12:
            raise ValueError('initial controlled displacement is outside the rigid-tool path')
        motion_factor = min(1.0, max(0.0, motion_factor))
        contact_manager.set_path_factor(motion_factor)
        initial_contact = contact_manager.evaluate(full_u(q), tangent=False)[2]
        if not initial_contact.gap_tolerance_met:
            raise ValueError('committed moving-tool pose exceeds the contact gap tolerance')
        info['contact_path_parameter'] = 'controlled_displacement_fraction'
    adaptive_control_subdivision = rotating_mpc_map is not None and contact_manager is None
    max_control_cutbacks = 0
    control_attempts_total = 0
    control_cutbacks_total = 0
    control_line_search_reductions = 0
    control_material_event_steps = 0
    control_material_event_evaluations = 0
    min_control_subincrement = abs(target_increment) / max(num_steps, 1) / 2.0 ** max_control_cutbacks
    record_step_index = int(step_index_offset)
    assembly_threads = None if resource_config is None else resource_config.assembly_threads
    with numba_thread_scope(assembly_threads):
        for local_step_index in range(1, num_steps + 1):
            step_index = int(step_index_offset) + local_step_index
            cancellation_safe_point(cancellation_token, f'nonlinear_static.displacement.step:{step_index}')
            exact_guard(model, context='nonlinear static displacement-control step cancellation')
            milestone = initial_control + target_increment * local_step_index / num_steps
            attempt_fraction = 1.0
            attempts_this_step = 0
            cutbacks_this_step = 0
            interval_cutbacks = 0
            accepted_subincrements = 0
            step_iterations = 0
            while True:
                attempts_this_step += 1
                control_attempts_total += 1
                q_attempt_start = q.copy()
                lam_attempt_start = float(lam)
                attempt_start_control = float(row_full @ full_u(q)) if rotating_mpc_map is not None else float(row_red @ q + row_u0)
                target = attempt_start_control + (milestone - attempt_start_control) * attempt_fraction
                residual_norm = float('inf')
                constraint_error = float('inf')
                states_new = committed_states
                assert T.shape == _diagnostic_T.shape and (T != _diagnostic_T).nnz == 0
                q = _diagnostic_q.copy()
                lam = _diagnostic_lam
                next_motion_factor = target / target_total if moving_tool else motion_factor
                if moving_tool:
                    start_u = full_u(q_attempt_start)
                    if not contact_manager.swept_increment_admissible(start_u, start_u, motion_factor, next_motion_factor):
                        failure_reason = 'contact_gap_exceeded'
                        status = 'contact_gap_exceeded'
                        break
                    contact_manager.set_path_factor(next_motion_factor)
                start_normal_multipliers = augmented_contact_manager.normal_multipliers.copy() if augmented_contact_manager is not None else None
                augmentation_limit = augmented_contact_manager.settings.maximum_augmentations if augmented_contact_manager is not None else 1
                augmentation_iterations = 0
                normal_multiplier_change = 0.0
                for augmentation in range(1, augmentation_limit + 1):
                    augmentation_iterations = augmentation
                    for iteration in range(1, max_iterations + 1):
                        cancellation_safe_point(cancellation_token, f'nonlinear_static.displacement.step:{step_index}.iteration:{iteration}')
                        exact_guard(model, context='nonlinear static displacement-control iteration cancellation')
                        total_iterations += 1
                        u = full_u(q)
                        F_int, K_T, trial_states = _assemble_nonlinear_system(model, u, committed_states, num_layers, kinematics=kinematics, corotational_tangent=corotational_tangent)
                        exact_guard(model, context='nonlinear static displacement-control assembly')
                        if follower_active:
                            F_const_current, K_const = _weighted_external_load_system(model, constant_terms, u, tangent=True)
                            F_prop_current, K_prop = _weighted_external_load_system(model, [proportional_term], u, tangent=True)
                            exact_guard(model, context='nonlinear static displacement-control loads')
                        else:
                            F_const_current, F_prop_current = (F_const_static, F_prop_static)
                            K_const = K_prop = zero_load_tangent
                        F_external = F_const_current + lam * F_prop_current
                        if rotating_mpc_map is not None:
                            residual = rotating_mpc_map.reduce_force(u, F_external - F_int)
                            current = float(row_full @ u)
                            ref_vec = rotating_mpc_map.reduce_force(u, F_const_current + max(abs(lam), 1.0) * F_prop_current)
                        else:
                            residual = np.asarray(T.T @ F_external, dtype=float).reshape(-1) - np.asarray(T.T @ F_int, dtype=float).reshape(-1)
                            current = float(row_red @ q + row_u0)
                            ref_vec = np.asarray(T.T @ (F_const_current + max(abs(lam), 1.0) * F_prop_current), dtype=float)
                        residual_norm = float(np.linalg.norm(residual))
                        constraint = target - current
                        constraint_error = abs(constraint)
                        reference = max(float(np.linalg.norm(ref_vec)), 1.0)
                        if residual_norm <= tolerance * reference and constraint_error <= tolerance * target_scale:
                            from .general_contact.runtime import active_contact_manager
                            contact_manager = active_contact_manager()
                            if contact_manager is not None and augmented_contact_manager is None and (not contact_manager.evaluate(u, tangent=False)[2].gap_tolerance_met):
                                failure_reason = 'contact_gap_exceeded'
                                break
                            states_new = trial_states
                            break
                        if rotating_mpc_map is not None:
                            K_ext_total = K_const + lam * K_prop if follower_active else None
                            K_red = rotating_mpc_map.reduce_tangent(u, K_T, F_int - F_external, K_ext_total)
                            F_prop_red = rotating_mpc_map.reduce_force(u, F_prop_current)
                            row_jac = np.asarray(row_full @ rotating_mpc_map.jacobian(u), dtype=float).reshape(-1)
                        else:
                            K_red = (T.T @ K_T @ T - T.T @ K_const @ T - lam * (T.T @ K_prop @ T)).tocsr()
                            F_prop_red = np.asarray(T.T @ F_prop_current, dtype=float).reshape(-1)
                            row_jac = row_red
                        aug = sparse.bmat([[K_red, sparse.csr_matrix((-F_prop_red).reshape(-1, 1))], [sparse.csr_matrix(row_jac.reshape(1, -1)), sparse.csr_matrix((1, 1))]], format='csr')
                        rhs = np.concatenate([residual, np.array([constraint], dtype=float)])
                        try:
                            with np.errstate(all='ignore'):
                                handle = factorize(aug, MatrixClass.GENERAL, signature=f'nonlinear.displacement_control:{step_index}:{iteration}' if augmented_contact_manager is None else f'nonlinear.displacement_control:{step_index}:{augmentation}:{iteration}')
                                delta = np.asarray(handle.solve(rhs), dtype=float).reshape(-1)
                        except Exception:
                            failure_reason = 'singular_augmented_tangent'
                            break
                        if np.any(~np.isfinite(delta)):
                            failure_reason = 'nonfinite_augmented_solution'
                            break
                        full_step_admissible = False
                        if adaptive_control_subdivision and np.any(delta):
                            residual_merit_globalization = any((np.isfinite(value) and value > 0.0 for value in (_max_plastic_strain(committed_states), _max_plastic_strain(trial_states))))
                            merit_current = residual_norm / (tolerance * reference) + constraint_error / (tolerance * target_scale)
                            line_search_alpha = 1.0
                            line_search_accepted = False
                            any_trial_admissible = False
                            event_base = None
                            event_trial_states = None
                            event_trial_alpha = None
                            if residual_merit_globalization and residual_norm * target_scale >= constraint_error * reference:
                                from ._nonlinear_events import material_events
                                event_base = material_events(model, committed_states, trial_states)
                                exact_guard(model, context='nonlinear static material event observation')
                            if merit_current > 0.0:
                                q_line_start = q.copy()
                                lam_line_start = float(lam)
                                alpha = 1.0
                                for line_reduction in range(8):
                                    q_trial = q_line_start + alpha * delta[:-1]
                                    lam_trial = lam_line_start + alpha * float(delta[-1])
                                    try:
                                        u_trial = full_u(q_trial)
                                    except SO3MeanDomainError:
                                        alpha *= 0.5
                                        continue
                                    if line_reduction == 0:
                                        full_step_admissible = True
                                    any_trial_admissible = True
                                    if not residual_merit_globalization:
                                        line_search_alpha = alpha
                                        line_search_accepted = True
                                        break
                                    f_int_trial, _k_trial, _s_trial = _assemble_nonlinear_system(model, u_trial, committed_states, num_layers, tangent=False, kinematics=kinematics, corotational_tangent=corotational_tangent)
                                    exact_guard(model, context='nonlinear static displacement-control line search')
                                    if follower_active:
                                        f_const_trial, _unused_k = _weighted_external_load_system(model, constant_terms, u_trial, tangent=False)
                                        f_prop_trial, _unused_k2 = _weighted_external_load_system(model, [proportional_term], u_trial, tangent=False)
                                    else:
                                        f_const_trial = F_const_static
                                        f_prop_trial = F_prop_static
                                    residual_trial = rotating_mpc_map.reduce_force(u_trial, f_const_trial + lam_trial * f_prop_trial - f_int_trial)
                                    constraint_trial = abs(target - float(row_full @ u_trial))
                                    merit_trial = float(np.linalg.norm(residual_trial)) / (tolerance * reference) + constraint_trial / (tolerance * target_scale)
                                    event_trial_states = _s_trial
                                    event_trial_alpha = alpha
                                    if merit_trial <= (1.0 - 0.0001 * alpha) * merit_current:
                                        line_search_alpha = alpha
                                        line_search_accepted = True
                                        break
                                    denominator = merit_trial - merit_current + alpha * merit_current
                                    if residual_norm * target_scale >= constraint_error * reference and merit_trial >= merit_current:
                                        alpha *= 0.1
                                    elif residual_norm * target_scale >= constraint_error * reference and np.isfinite(denominator) and (denominator > 0.0):
                                        proposed_alpha = 0.5 * alpha * alpha * merit_current / denominator
                                        alpha = float(np.clip(proposed_alpha, 0.1 * alpha, 0.5 * alpha))
                                    else:
                                        alpha *= 0.5
                            if not line_search_accepted and event_base is not None and (event_trial_alpha is not None):
                                from ._nonlinear_events import crossed_material_event
                                event_upper = material_events(model, committed_states, event_trial_states)
                                exact_guard(model, context='nonlinear static material event observation')

                                def evaluate_material_event(event_alpha):
                                    nonlocal control_material_event_evaluations
                                    cancellation_safe_point(cancellation_token, f'nonlinear_static.displacement.material_event:{iteration}')
                                    exact_guard(model, context='nonlinear static material event cancellation')
                                    event_q = q_line_start + event_alpha * delta[:-1]
                                    event_lam = lam_line_start + event_alpha * float(delta[-1])
                                    try:
                                        event_u = full_u(event_q)
                                    except SO3MeanDomainError:
                                        return None
                                    event_f, _event_k, event_states = _assemble_nonlinear_system(model, event_u, committed_states, num_layers, tangent=False, kinematics=kinematics, corotational_tangent=corotational_tangent)
                                    control_material_event_evaluations += 1
                                    exact_guard(model, context='nonlinear static material event trial')
                                    if follower_active:
                                        event_const, _unused_k = _weighted_external_load_system(model, constant_terms, event_u, tangent=False)
                                        event_prop, _unused_k2 = _weighted_external_load_system(model, [proportional_term], event_u, tangent=False)
                                    else:
                                        event_const, event_prop = (F_const_static, F_prop_static)
                                    event_external = event_const + event_lam * event_prop
                                    event_r = rotating_mpc_map.reduce_force(event_u, event_external - event_f)
                                    if not np.all(np.isfinite(event_f)) or not np.all(np.isfinite(event_r)):
                                        return None
                                    event_constraint = abs(target - float(row_full @ event_u))
                                    event_merit = float(np.linalg.norm(event_r)) / (tolerance * reference) + event_constraint / (tolerance * target_scale)
                                    observation = material_events(model, committed_states, event_states)
                                    exact_guard(model, context='nonlinear static material event observation')
                                    return {'events': observation, 'merit': event_merit, 'residual_norm': float(np.linalg.norm(event_r)), 'force_scale': max(float(np.linalg.norm(rotating_mpc_map.reduce_force(event_u, event_f))), float(np.linalg.norm(rotating_mpc_map.reduce_force(event_u, event_external))), 1.0)}
                                event_step = crossed_material_event(event_base, event_upper, event_trial_alpha, q_line_start, delta[:-1], evaluate_material_event)
                                if event_step is not None:
                                    noise_bound = 128.0 * np.finfo(float).eps * max(event_step['force_scale'], residual_norm, reference, 1.0)
                                    if event_step['merit'] <= (1.0 - 0.0001 * event_step['alpha']) * merit_current and residual_norm - event_step['residual_norm'] > noise_bound:
                                        line_search_alpha = event_step['alpha']
                                        line_search_accepted = True
                                        control_material_event_steps += 1
                            if merit_current > 0.0 and (not line_search_accepted):
                                if not any_trial_admissible:
                                    failure_reason = 'trial_state_domain_refused'
                                    break
                                if residual_norm * target_scale >= constraint_error * reference:
                                    failure_reason = 'line_search_no_improvement'
                                    break
                            if line_search_accepted and line_search_alpha < 1.0:
                                delta = delta * line_search_alpha
                                control_line_search_reductions += 1
                        if rotating_mpc_map is not None and (not full_step_admissible):
                            try:
                                full_u(q + delta[:-1])
                            except SO3MeanDomainError:
                                failure_reason = 'trial_state_domain_refused'
                                break
                        from .general_contact.runtime import active_contact_manager
                        contact_manager = active_contact_manager()
                        if contact_manager is not None:
                            candidate_u = full_u(q + delta[:-1])
                            fraction = contact_manager.admissible_step_fraction(u, candidate_u)
                            if fraction <= 1e-12:
                                failure_reason = 'contact_gap_exceeded'
                                break
                            delta *= fraction
                        q += delta[:-1]
                        lam += float(delta[-1])
                    else:
                        failure_reason = 'maximum_iterations_reached'
                    step_iterations += iteration
                    if failure_reason is not None or augmented_contact_manager is None:
                        break
                    candidate_u = full_u(q)
                    certificate = augmented_contact_manager.evaluate(candidate_u, tangent=False)[2]
                    projected = augmented_contact_manager.projected_normal_multipliers(candidate_u)
                    normal_multiplier_change = float(np.max(np.abs(projected - augmented_contact_manager.normal_multipliers)))
                    if normal_multiplier_change <= augmented_contact_manager.settings.pressure_tolerance and certificate.gap_tolerance_met:
                        break
                    augmented_contact_manager.set_normal_multipliers(projected)
                else:
                    failure_reason = 'maximum_augmentations_reached'
                if failure_reason is not None:
                    _discard_nonlinear_state_candidate(committed_states)
                    q = q_attempt_start
                    lam = lam_attempt_start
                    if augmented_contact_manager is not None:
                        augmented_contact_manager.set_normal_multipliers(start_normal_multipliers)
                    if moving_tool:
                        contact_manager.set_path_factor(motion_factor)
                    attempted_control_span = abs(milestone - attempt_start_control) * attempt_fraction
                    if failure_reason in ('maximum_iterations_reached', 'line_search_no_improvement', 'trial_state_domain_refused') and adaptive_control_subdivision and np.isfinite(attempted_control_span) and (attempted_control_span > 0.0) and (attempted_control_span * 0.5 >= min_control_subincrement) and (interval_cutbacks < max_control_cutbacks):
                        failure_reason = None
                        attempt_fraction *= 0.5
                        control_cutbacks_total += 1
                        cutbacks_this_step += 1
                        interval_cutbacks += 1
                        continue
                    if failure_reason == 'maximum_iterations_reached' and adaptive_control_subdivision:
                        failure_reason = 'minimum_control_step_reached'
                    status = 'contact_gap_exceeded' if failure_reason == 'contact_gap_exceeded' else 'stopped_at_limit' if steps else 'diverged'
                    break
                if adaptive_control_subdivision and attempt_fraction < 1.0:
                    accepted_control = float(row_full @ full_u(q))
                    control_progress = accepted_control - attempt_start_control
                    if not np.isfinite(control_progress) or (control_progress <= 0.0 if milestone > attempt_start_control else control_progress >= 0.0) or accepted_subincrements >= 2 ** max_control_cutbacks + 1:
                        _discard_nonlinear_state_candidate(committed_states)
                        q = q_attempt_start
                        lam = lam_attempt_start
                        failure_reason = 'minimum_control_step_reached'
                        status = 'stopped_at_limit' if steps else 'diverged'
                        break
                contact_tool_work_increment = 0.0
                if moving_tool:
                    end_u = full_u(q)
                    start_u = full_u(q_attempt_start)
                    if not contact_manager.swept_increment_admissible(start_u, end_u, motion_factor, next_motion_factor):
                        _discard_nonlinear_state_candidate(committed_states)
                        q = q_attempt_start
                        lam = lam_attempt_start
                        if augmented_contact_manager is not None:
                            augmented_contact_manager.set_normal_multipliers(start_normal_multipliers)
                        contact_manager.set_path_factor(motion_factor)
                        failure_reason = 'contact_gap_exceeded'
                        status = 'contact_gap_exceeded'
                        break
                    contact_tool_work_increment = contact_manager.tool_work_increment(start_u, end_u, motion_factor, next_motion_factor)
                u = full_u(q)
                committed_states = _commit_nonlinear_state_candidate(committed_states, states_new, model=model, accepted_displacements=u)
                motion_factor = next_motion_factor
                current = float(row_full @ u) if rotating_mpc_map is not None else float(row_red @ q + row_u0)
                reaction_internal, _unused, _reaction_states = _assemble_nonlinear_system(model, u, committed_states, num_layers, tangent=False, kinematics=kinematics, corotational_tangent=corotational_tangent, require_full_coordinates=True)
                exact_guard(model, context='nonlinear static displacement-control reaction assembly')
                _discard_nonlinear_state_candidate(committed_states)
                if follower_active:
                    reaction_constant, _unused = _weighted_external_load_system(model, constant_terms, u, tangent=False)
                    reaction_proportional, _unused = _weighted_external_load_system(model, [proportional_term], u, tangent=False)
                    exact_guard(model, context='nonlinear static displacement-control reaction loads')
                else:
                    reaction_constant = F_const_static
                    reaction_proportional = F_prop_static
                reaction_imbalance = reaction_internal - (reaction_constant + lam * reaction_proportional)
                if rotating_mpc_map is not None:
                    reaction_imbalance = rotating_mpc_map.transfer_slave_imbalance_to_masters(u, reaction_imbalance)
                support_reactions = _support_reaction_resultants(model, reaction_imbalance)
                record_step_index += 1
                steps.append(NonlinearStaticStep(step_index=record_step_index, load_factor=float(lam), iterations=step_iterations, residual_norm=residual_norm, displacement_norm=float(np.linalg.norm(u)), max_equivalent_plastic_strain=_max_plastic_strain(committed_states), control_value=current, active_stage=active_stage, support_reactions=support_reactions))
                history.append({'step_index': record_step_index, 'load_factor': float(lam), 'control_value': current, 'target_displacement': target, 'residual_norm': residual_norm, 'constraint_error': constraint_error, 'iterations': step_iterations, **({'control_attempts': attempts_this_step, 'control_cutbacks': cutbacks_this_step} if adaptive_control_subdivision else {}), **({'augmentation_iterations': augmentation_iterations, 'normal_multiplier_change': normal_multiplier_change, 'contact': _augmented_contact_increment_summary(certificate), 'normal_multipliers': augmented_contact_manager.normal_multipliers.tolist()} if augmented_contact_manager is not None else {}), 'active_stage': active_stage, **({'contact_path_factor': motion_factor, 'contact_tool_work_increment': contact_tool_work_increment} if moving_tool else {}), 'support_reactions': {name: list(values) for name, values in support_reactions.items()}})
                if record_increment_snapshots:
                    snapshots.append(_increment_snapshot(record_step_index, lam, u, committed_states, control_value=current))
                if progress_callback is not None:
                    emit_progress(progress_callback, 'nonlinear_static_step', 'nonlinear_static.displacement', completed=local_step_index, total=num_steps, iteration=step_iterations, control='displacement', step_index=int(record_step_index), load_factor=float(lam), control_value=float(current), displacement_norm=float(np.linalg.norm(u)), max_equivalent_plastic_strain=float(_max_plastic_strain(committed_states)), support_reactions={name: list(values) for name, values in support_reactions.items()})
                    exact_guard(model, context='nonlinear static displacement-control progress callback')
                if attempt_fraction >= 1.0:
                    break
                step_iterations = 0
                attempt_fraction = 1.0
                interval_cutbacks = 0
                accepted_subincrements += 1
            if failure_reason is not None:
                break
    u_final = full_u(q)
    if not steps and (not committed_states) and (augmented_contact_manager is not None or any((_qualified_s3_committed_state_validator(element) is not None for element in model.mesh.elements.values()))):
        _initial_force, _initial_tangent, reference_states = _assemble_nonlinear_system(model, u_final, committed_states, num_layers, tangent=False, kinematics=kinematics, corotational_tangent=corotational_tangent)
        committed_states = _commit_nonlinear_state_candidate(committed_states, reference_states, model=model, accepted_displacements=u_final)
    committed_states = _materialize_final_nonlinear_states(committed_states, info)
    committed_states = _finalize_nonlinear_element_states(model, u_final, committed_states, num_layers, kinematics=kinematics)
    committed_states = _seal_final_qualified_q4_states(model, u_final, committed_states, num_layers, info, kinematics=kinematics)
    if adaptive_control_subdivision:
        info['displacement_control_adaptation'] = {'attempts': int(control_attempts_total), 'cutbacks': int(control_cutbacks_total), 'max_cutbacks_per_interval': int(max_control_cutbacks), 'min_subincrement': float(min_control_subincrement), 'line_search_reductions': int(control_line_search_reductions), 'material_event_steps': int(control_material_event_steps), 'material_event_evaluations': int(control_material_event_evaluations), 'applied': control_cutbacks_total > 0}
    info['failure_reason'] = failure_reason
    info['stop_reason'] = 'target_displacement_reached' if failure_reason is None else failure_reason
    info['status_category'] = _nonlinear_status_category(status, failure_reason)
    info['last_converged_load_factor'] = float(lam)
    info['peak_load_factor'] = max((step.load_factor for step in steps), default=float(lam))
    info['force_displacement_history'] = history
    if moving_tool:
        info['contact_path_factor'] = motion_factor
    info['strain_summary'] = _nonlinear_state_summary(committed_states)
    info['total_newton_iterations'] = total_iterations
    info['solve_time'] = time.time() - start_time
    u_postcheck = rotating_mpc_map.to_linear_displacement(u_final) if rotating_mpc_map is not None else u_final
    info['constraint_postcheck'] = constraint_residual_summary(model, u_postcheck)
    if rotating_mpc_map is not None:
        info['constraint_postcheck']['nonlinear_rotating_mpc_count'] = len(rotating_mpc_map.entries)
    exact_guard(model, context='nonlinear static displacement-control constraint postcheck')
    info['result_case'] = make_result_case(name='nonlinear_static_displacement_control', analysis_type='nonlinear_static', load_cases=tuple((stage.load_case for stage in load_program.stages)) if load_program is not None else (), assembly_info={'load': {'vector_type': 'load_program' if load_program is not None else 'load'}, **info}, solver_info={'convergence_info': {'status': status}}, recovery={'displacements': True, 'element_states': True, 'force_displacement_history': True}, settings={'control': 'displacement', 'num_steps': num_steps, 'num_layers': num_layers, 'kinematics': kinematics, 'corotational_tangent': corotational_tangent}).to_dict()
    restart_payload = None
    if restart_analysis_contract is not None:
        restart_payload = create_nonlinear_checkpoint(analysis_kind='static', model=model, analysis_contract=restart_analysis_contract, displacements=u_final, element_states=committed_states, deleted_element_ids=(), path_state=_static_restart_path_payload(control_name='displacement', load_factor=float(lam), step_index=len(steps), total_iterations=total_iterations, steps=steps, force_displacement_history=history, reduced_coordinates=q, terminal_status=status, failure_reason=failure_reason, **{'normal_multipliers': augmented_contact_manager.normal_multipliers.tolist()} if augmented_contact_manager is not None else {}))
        exact_guard(model, context='nonlinear static displacement-control checkpoint output')
    return NonlinearStaticResult(steps, status, u_final, float(lam), committed_states, info, tuple(snapshots), restart_payload)