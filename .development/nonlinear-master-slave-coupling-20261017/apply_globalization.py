"""One-off exact line edits for the DC line search + lambda recovery (CRLF)."""
import io

PATH = 'src/anysolver/nonlinear_static.py'
src = io.open(PATH, 'r', encoding='utf-8', newline='').read()
lines = src.split('\r\n')


def find_one(text, what):
    hits = [i for i, line in enumerate(lines) if line == text]
    assert len(hits) == 1, (what, hits)
    return hits[0]


def find_startswith(prefix, what):
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    assert len(hits) == 1, (what, hits)
    return hits[0]


# --- signature: new private keyword -----------------------------------------
i_sig = find_one('    initial_load_factor: float = 0.0,', 'signature initial_load_factor')
lines[i_sig + 1:i_sig + 1] = ['    recover_initial_load_factor: bool = False,']

# --- lambda recovery block ---------------------------------------------------
i_prop = find_one(
    '        raise ValueError("Displacement control requires a non-zero proportional load vector")',
    'F_prop_red guard',
)
recovery = [
    '',
    '    if recover_initial_load_factor and rotating_mpc_map is not None:',
    '        # Ordinary supplied initial-state resume without re-equilibration:',
    '        # the copied state is an accepted equilibrium, so recover its load',
    '        # scalar by least squares on the reduced forces as the Newton',
    '        # initial guess.  This is a predictor only: it changes no success',
    '        # criterion and no public contract, and the diagnostic trial',
    '        # assembly below is never committed.',
    '        f_int_initial, _k0, _initial_trial = _assemble_nonlinear_system(',
    '            model,',
    '            initial_u,',
    '            committed_states,',
    '            num_layers,',
    '            tangent=False,',
    '            kinematics=kinematics,',
    '            corotational_tangent=corotational_tangent,',
    '        )',
    '        exact_guard(',
    '            model,',
    '            context="nonlinear static displacement-control initial load recovery",',
    '        )',
    '        _discard_nonlinear_state_candidate(committed_states)',
    '        if follower_active:',
    '            f_const_initial, _unused_k = _weighted_external_load_system(',
    '                model, constant_terms, initial_u, tangent=False,',
    '            )',
    '        else:',
    '            f_const_initial = F_const_static',
    '        f_red_initial = rotating_mpc_map.reduce_force(',
    '            initial_u, f_int_initial - f_const_initial',
    '        )',
    '        _p_norm = float(F_prop_red @ F_prop_red)',
    '        if _p_norm > 0.0:',
    '            lam = float((F_prop_red @ f_red_initial) / _p_norm)',
    '        info["displacement_control_recovered_initial_load_factor"] = float(lam)',
]
lines[i_prop + 1:i_prop + 1] = recovery

# --- line-search counter init ------------------------------------------------
i_cut = find_one('    control_cutbacks_total = 0', 'cutbacks total init')
lines[i_cut + 1:i_cut + 1] = ['    control_line_search_reductions = 0']

# --- line search before applying the Newton update ---------------------------
i_nonfinite = find_one(
    '                        if np.any(~np.isfinite(delta)):',
    'nonfinite delta check',
)
assert lines[i_nonfinite + 1] == '                            failure_reason = "nonfinite_augmented_solution"'
assert lines[i_nonfinite + 2] == '                            break'
line_search = [
    '                        if adaptive_control_subdivision and np.any(delta):',
    '                            # Bounded residual line search on the rotating-MPC',
    '                            # contact-free route: from a converged state the',
    '                            # first postyield Newton step can overshoot the',
    '                            # load factor catastrophically.  Backtrack on the',
    '                            # augmented merit (reduced residual and control',
    '                            # constraint, both normalized like the',
    '                            # convergence criterion).  Every trial evaluation',
    '                            # only replaces the pending state candidate and',
    '                            # is never committed, so committed histories are',
    '                            # retained; without a sufficient decrease the',
    '                            # full Newton step is kept (unchanged behavior).',
    '                            merit_current = (',
    '                                residual_norm / (tolerance * reference)',
    '                                + constraint_error / (tolerance * target_scale)',
    '                            )',
    '                            line_search_alpha = 1.0',
    '                            if merit_current > 0.0:',
    '                                q_line_start = q.copy()',
    '                                lam_line_start = float(lam)',
    '                                for line_reduction in range(8):',
    '                                    alpha = 0.5 ** line_reduction',
    '                                    q_trial = q_line_start + alpha * delta[:-1]',
    '                                    lam_trial = (',
    '                                        lam_line_start + alpha * float(delta[-1])',
    '                                    )',
    '                                    u_trial = full_u(q_trial)',
    '                                    f_int_trial, _k_trial, _s_trial = (',
    '                                        _assemble_nonlinear_system(',
    '                                            model,',
    '                                            u_trial,',
    '                                            committed_states,',
    '                                            num_layers,',
    '                                            tangent=False,',
    '                                            kinematics=kinematics,',
    '                                            corotational_tangent=( ',
    '                                                corotational_tangent',
    '                                            ),',
    '                                        )',
    '                                    )',
    '                                    exact_guard(',
    '                                        model,',
    '                                        context=( ',
    '                                            "nonlinear static displacement-control "',
    '                                            "line search"',
    '                                        ),',
    '                                    )',
    '                                    if follower_active:',
    '                                        f_const_trial, _unused_k = (',
    '                                            _weighted_external_load_system(',
    '                                                model, constant_terms, u_trial,',
    '                                                tangent=False,',
    '                                            )',
    '                                        )',
    '                                        f_prop_trial, _unused_k2 = (',
    '                                            _weighted_external_load_system(',
    '                                                model, [proportional_term],',
    '                                                u_trial, tangent=False,',
    '                                            )',
    '                                        )',
    '                                    else:',
    '                                        f_const_trial = F_const_static',
    '                                        f_prop_trial = F_prop_static',
    '                                    residual_trial = (',
    '                                        rotating_mpc_map.reduce_force(',
    '                                            u_trial,',
    '                                            f_const_trial',
    '                                            + lam_trial * f_prop_trial',
    '                                            - f_int_trial,',
    '                                        )',
    '                                    )',
    '                                    constraint_trial = abs(',
    '                                        target - float(row_full @ u_trial)',
    '                                    )',
    '                                    merit_trial = (',
    '                                        float(np.linalg.norm(residual_trial))',
    '                                        / (tolerance * reference)',
    '                                        + constraint_trial',
    '                                        / (tolerance * target_scale)',
    '                                    )',
    '                                    if merit_trial <= (',
    '                                        1.0 - 1.0e-4 * alpha',
    '                                    ) * merit_current:',
    '                                        line_search_alpha = alpha',
    '                                        break',
    '                            if line_search_alpha < 1.0:',
    '                                delta = delta * line_search_alpha',
    '                                control_line_search_reductions += 1',
]
lines[i_nonfinite + 3:i_nonfinite + 3] = line_search

# --- info adaptation record ---------------------------------------------------
i_info = find_one('            "min_subincrement": float(min_control_subincrement),', 'info min subincrement')
lines[i_info + 1:i_info + 1] = [
    '            "line_search_reductions": int(control_line_search_reductions),',
]

io.open(PATH, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))
print('ok')
