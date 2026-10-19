"""One-shot patcher: DC trial-domain rejection + classified no-improvement
failure (SLICE3_FINAL_REPAIR.md). Idempotence is not required; every anchor
must occur exactly once or the patch aborts without writing.
"""
import ast

path = "src/anysolver/nonlinear_static.py"
with open(path, "r", encoding="utf-8", newline="") as fh:
    src = fh.read()


def rep(old, new):
    global src
    count = src.count(old)
    assert count == 1, "anchor found %d times: %r" % (count, old[:80])
    src = src.replace(old, new, 1)


# A. Function-level import of the typed domain error (lazy style matches the
# existing corotational imports in this module).
rep(
    "    def full_u(q_vec: np.ndarray) -> np.ndarray:\r\n",
    "    from .corotational import SO3MeanDomainError\r\n\r\n"
    "    def full_u(q_vec: np.ndarray) -> np.ndarray:\r\n",
)

# B0. Initialize the full-step admissibility flag before the line search.
rep(
    "                        if adaptive_control_subdivision and np.any(delta):\r\n",
    "                        full_step_admissible = False\r\n"
    "                        if adaptive_control_subdivision and np.any(delta):\r\n",
)

# B1. Comment update: describe trial-domain refusal and the classified
# no-improvement failure instead of the unconditional full-step fallback.
rep(
    "                            # retained; without a sufficient decrease the\r\n"
    "                            # full Newton step is kept (unchanged behavior).\r\n",
    "                            # is retained.  A trial whose master rotations\r\n"
    "                            # leave the supported SO(3) chart is refused\r\n"
    "                            # (SO3MeanDomainError) and the search backtracks;\r\n"
    "                            # a refused trial is never committed and never\r\n"
    "                            # mutates constitutive state.  While the control\r\n"
    "                            # row is not yet satisfied the full Newton step is\r\n"
    "                            # kept (unchanged behavior); once the control\r\n"
    "                            # constraint holds, a step with no admissible\r\n"
    "                            # sufficient decrease is not committed: the\r\n"
    "                            # attempt fails with a classified reason and\r\n"
    "                            # bounded subdivision retries, because there the\r\n"
    "                            # committed full step sustains a Newton limit\r\n"
    "                            # cycle (measured period-3 cycle on the direct\r\n"
    "                            # EP route).\r\n",
)

# B2. Line-search state flags.
rep(
    "                            line_search_alpha = 1.0\r\n"
    "                            if merit_current > 0.0:\r\n",
    "                            line_search_alpha = 1.0\r\n"
    "                            line_search_accepted = False\r\n"
    "                            any_trial_admissible = False\r\n"
    "                            if merit_current > 0.0:\r\n",
)

# B3. Trial-domain rejection around the trial kinematics evaluation.
rep(
    "                                    u_trial = full_u(q_trial)\r\n",
    "                                    try:\r\n"
    "                                        u_trial = full_u(q_trial)\r\n"
    "                                    except SO3MeanDomainError:\r\n"
    "                                        # Bounded trial-domain rejection:\r\n"
    "                                        # the trial state left the supported\r\n"
    "                                        # rotation chart.  It is inadmissible:\r\n"
    "                                        # backtrack to the next halving and\r\n"
    "                                        # never commit or assemble it.\r\n"
    "                                        continue\r\n"
    "                                    if line_reduction == 0:\r\n"
    "                                        full_step_admissible = True\r\n"
    "                                    any_trial_admissible = True\r\n",
)

# B4. Record acceptance explicitly.
rep(
    "                                    ) * merit_current:\r\n"
    "                                        line_search_alpha = alpha\r\n"
    "                                        break\r\n",
    "                                    ) * merit_current:\r\n"
    "                                        line_search_alpha = alpha\r\n"
    "                                        line_search_accepted = True\r\n"
    "                                        break\r\n",
)

# B5. Classified failure when no admissible improving step exists.
rep(
    "                            if line_search_alpha < 1.0:\r\n"
    "                                delta = delta * line_search_alpha\r\n"
    "                                control_line_search_reductions += 1\r\n",
    "                            if merit_current > 0.0 and not line_search_accepted:\r\n"
    "                                if not any_trial_admissible:\r\n"
    "                                    failure_reason = 'trial_state_domain_refused'\r\n"
    "                                    break\r\n"
    "                                if constraint_error <= tolerance * target_scale:\r\n"
    "                                    # No admissible improving step exists at a\r\n"
    "                                    # control-satisfied state: committing the\r\n"
    "                                    # full step would sustain the measured\r\n"
    "                                    # Newton limit cycle.  Classify the\r\n"
    "                                    # attempt failed; the rollback below\r\n"
    "                                    # restores the committed state and\r\n"
    "                                    # bounded subdivision retries.\r\n"
    "                                    failure_reason = 'line_search_no_improvement'\r\n"
    "                                    break\r\n"
    "                                # Control row not yet satisfied: keep the\r\n"
    "                                # full Newton step (unchanged behavior).\r\n"
    "                            if line_search_accepted and line_search_alpha < 1.0:\r\n"
    "                                delta = delta * line_search_alpha\r\n"
    "                                control_line_search_reductions += 1\r\n",
)

# B6. Commit guard: never commit an endpoint whose kinematics are refused.
rep(
    "                        from .general_contact.runtime import active_contact_manager\r\n"
    "\r\n"
    "                        contact_manager = active_contact_manager()\r\n"
    "                        if contact_manager is not None:\r\n"
    "                            candidate_u = full_u(q + delta[:-1])\r\n",
    "                        if rotating_mpc_map is not None and not full_step_admissible:\r\n"
    "                            try:\r\n"
    "                                full_u(q + delta[:-1])\r\n"
    "                            except SO3MeanDomainError:\r\n"
    "                                # The step endpoint is outside the supported\r\n"
    "                                # rotation chart: refuse the commit, roll\r\n"
    "                                # back to the attempt start and classify the\r\n"
    "                                # failure instead of aborting the solve from\r\n"
    "                                # an otherwise valid committed state.\r\n"
    "                                failure_reason = 'trial_state_domain_refused'\r\n"
    "                                break\r\n"
    "                        from .general_contact.runtime import active_contact_manager\r\n"
    "\r\n"
    "                        contact_manager = active_contact_manager()\r\n"
    "                        if contact_manager is not None:\r\n"
    "                            candidate_u = full_u(q + delta[:-1])\r\n",
)

# B7. Subdivision eligibility for the two new classified failure reasons.
rep(
    '                        failure_reason == "maximum_iterations_reached"\r\n'
    "                        and adaptive_control_subdivision\r\n"
    "                        and np.isfinite(attempted_control_span)\r\n",
    "                        failure_reason in (\r\n"
    '                            "maximum_iterations_reached",\r\n'
    '                            "line_search_no_improvement",\r\n'
    '                            "trial_state_domain_refused",\r\n'
    "                        )\r\n"
    "                        and adaptive_control_subdivision\r\n"
    "                        and np.isfinite(attempted_control_span)\r\n",
)

ast.parse(src)
with open(path, "w", encoding="utf-8", newline="") as fh:
    fh.write(src)
print("nonlinear_static.py patched OK")
